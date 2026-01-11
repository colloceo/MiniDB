import json
import os
from typing import List, Dict, Any, Optional, Generator, Union
from .exceptions import DBError, ValidationError
from .lock_manager import LockManager
from .indexer import Indexer

class Table:
    """Represents a database table with streaming storage and indexing.

    Attributes:
        table_name (str): Name of the table.
        columns (List[str]): List of column names.
        primary_key (Optional[str]): Name of the primary key column.
        column_types (Dict[str, str]): Mapping of column names to their types (e.g., 'int', 'str').
        unique_columns (List[str]): List of columns with unique constraints.
        foreign_keys (Dict[str, str]): Mapping of local columns to 'table.column' references.
        data_dir (str): Directory where table data is stored.
        file_path (str): Path to the .jsonl data file.
        index_path (str): Path to the .idx index file.
        data (List[Dict[str, Any]]): In-memory cache of table rows (maintained for backward compatibility).
        indexer (Indexer): Manager for disk-based primary key lookup.
        lock_manager (LockManager): Manager for concurrency control.
    """

    def __init__(self, table_name: str, columns: List[str], primary_key: Optional[str] = None, 
                 column_types: Optional[Dict[str, str]] = None, unique_columns: Optional[List[str]] = None, 
                 foreign_keys: Optional[Dict[str, str]] = None, data_dir: str = "data") -> None:
        """Initializes the table schema and loads existing data.

        Args:
            table_name: Name of the table.
            columns: List of column names.
            primary_key: Optional primary key column name.
            column_types: Optional dictionary of column types.
            unique_columns: Optional list of unique columns.
            foreign_keys: Optional dictionary of foreign key constraints.
            data_dir: Directory for data storage.
        """
        self.table_name = table_name
        self.columns = columns
        # Default primary key is the first column if not specified
        self.primary_key = primary_key if primary_key else (columns[0] if columns else None)
        self.column_types = column_types or {}
        self.unique_columns = unique_columns or []
        self.foreign_keys = foreign_keys or {}
        self.data_dir = data_dir
        self.file_path = os.path.join(self.data_dir, f"{table_name}.jsonl")
        self.index_path = os.path.join(self.data_dir, f"{table_name}.idx")
        self.data = []
        self.indexer = Indexer(self.index_path)
        
        # Initialize lock manager for concurrency control
        self.lock_manager = LockManager(data_dir=data_dir)
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.load_data()

    def load_rows(self) -> Generator[Dict[str, Any], None, None]:
        """Generator to yield rows one by one from the .jsonl file.

        Yields:
            Dict[str, Any]: A single row as a dictionary.
        """
        if not os.path.exists(self.file_path):
            return
        
        with open(self.file_path, "r") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)

    def _rebuild_index(self) -> None:
        """Rebuilds the disk-based binary index from the .jsonl file."""
        if not self.primary_key or not os.path.exists(self.file_path):
            return
            
        pk_offset_pairs = []
        with open(self.file_path, "r") as f:
            while True:
                offset = f.tell()
                line = f.readline()
                if not line:
                    break
                if line.strip():
                    try:
                        row = json.loads(line)
                        pk_val = row.get(self.primary_key)
                        if pk_val is not None and isinstance(pk_val, int):
                            pk_offset_pairs.append((pk_val, offset))
                    except json.JSONDecodeError:
                        pass
        
        self.indexer.rebuild(pk_offset_pairs)

    def get_row_by_id(self, pk_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a specific row by its primary key using the disk index.
        
        Args:
            pk_id: The primary key value.
            
        Returns:
            Optional[Dict[str, Any]]: The row data if found, else None.
        """
        offset = self.indexer.find(pk_id)
        if offset is None:
            return None
            
        try:
            with open(self.file_path, "r") as f:
                f.seek(offset)
                line = f.readline()
                if line:
                    return json.loads(line)
        except (IOError, json.JSONDecodeError):
            return None
        return None

    def load_data(self) -> None:
        """Reads data from the local .jsonl file and builds index.

        Raises:
            DBError: If loading from disk fails.
        """
        if not os.path.exists(self.file_path):
            self.data = []
            return
        
        # Acquire lock before reading
        self.lock_manager.acquire_lock(self.table_name)
        
        try:
            self.data = []
            for row in self.load_rows():
                self.data.append(row)
            self._rebuild_index()
        except (json.JSONDecodeError, IOError) as e:
            raise DBError(f"Failed to load data for table '{self.table_name}': {e}")
        finally:
            # Always release lock, even if an error occurs
            self.lock_manager.release_lock(self.table_name)

    def save_data(self) -> None:
        """Writes the current data list to the .jsonl file line by line atomically.

        Raises:
            DBError: If saving to disk fails.
        """
        # Acquire lock before writing
        self.lock_manager.acquire_lock(self.table_name)
        
        temp_path = f"{self.file_path}.tmp"
        try:
            with open(temp_path, "w") as f:
                for row in self.data:
                    f.write(json.dumps(row) + "\n")
                f.flush()
                # os.fsync requires a file descriptor
                os.fsync(f.fileno())
            
            # Atomic swap
            os.replace(temp_path, self.file_path)
            
            # Rebuild index since offsets have changed
            self._rebuild_index()
        except (IOError, OSError) as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise DBError(f"Failed to save data for table '{self.table_name}': {e}")
        finally:
            # Always release lock, even if an error occurs
            self.lock_manager.release_lock(self.table_name)

    def append_row(self, row_data: Dict[str, Any]) -> int:
        """Appends a single row to the .jsonl file and returns its offset.

        Args:
            row_data: The row dictionary to append.

        Returns:
            int: The file offset where the row was written.

        Raises:
            DBError: If the append operation fails.
        """
        self.lock_manager.acquire_lock(self.table_name)
        try:
            # Open in append mode, but we need to know the offset
            # One way is to check size before appending
            current_offset = os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0
            with open(self.file_path, "a") as f:
                f.write(json.dumps(row_data) + "\n")
                f.flush()
                os.fsync(f.fileno())
            return current_offset
        except (IOError, OSError) as e:
            raise DBError(f"Failed to append data to table '{self.table_name}': {e}")
        finally:
            self.lock_manager.release_lock(self.table_name)

    def insert_row(self, row_data: Dict[str, Any]) -> None:
        """Validates and appends a row, updating the index and file.

        Args:
            row_data: The row dictionary to insert.

        Raises:
            ValidationError: If row contents do not match the schema.
            TypeError: If column value types mismatch.
            DuplicateKeyError: If primary key uniqueness is violated.
            UniqueConstraintError: If unique constraints are violated.
        """
        if not isinstance(row_data, dict):
            raise ValidationError("Row data must be a dictionary.")
        
        # Validate columns
        row_keys = set(row_data.keys())
        expected_keys = set(self.columns)
        
        if row_keys != expected_keys:
            missing = expected_keys - row_keys
            extra = row_keys - expected_keys
            error_msg = f"Data validation failed for table '{self.table_name}'."
            if missing:
                error_msg += f" Missing columns: {missing}."
            if extra:
                error_msg += f" Unexpected columns: {extra}."
            raise ValidationError(error_msg)
        
        # Type Enforcement
        for col, expected_type in self.column_types.items():
            val = row_data.get(col)
            if expected_type == 'int':
                if not isinstance(val, int):
                    raise TypeError(f"Type mismatch for column '{col}': expected int, got {type(val).__name__}.")
            elif expected_type == 'str':
                if not isinstance(val, str):
                    raise TypeError(f"Type mismatch for column '{col}': expected str, got {type(val).__name__}.")

        # Check primary key uniqueness using disk index
        pk_val = row_data.get(self.primary_key)
        if isinstance(pk_val, int) and self.indexer.find(pk_val) is not None:
            from .exceptions import DuplicateKeyError
            raise DuplicateKeyError(f"Duplicate primary key '{pk_val}' for table '{self.table_name}'.")

        # Check secondary unique constraints
        for col in self.unique_columns:
            if col == self.primary_key: continue # Already checked
            val = row_data.get(col)
            # Scan file for unique constraint
            for r in self.load_rows():
                if r.get(col) == val:
                    from .exceptions import UniqueConstraintError
                    raise UniqueConstraintError(f"Unique constraint violation: value '{val}' already exists in column '{col}'.")

        self.data.append(row_data)
        
        # Append to file and update index
        offset = self.append_row(row_data)
        if self.primary_key and isinstance(pk_val, int):
            self.indexer.append(pk_val, offset)

    def select_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns all rows (list, but loaded via generator).

        Args:
            limit: Maximum number of rows to return.

        Returns:
            List[Dict[str, Any]]: List of matching row dictionaries.
        """
        results = []
        for row in self.load_rows():
            results.append(row)
            if limit and len(results) >= limit:
                break
        return results

    def select_where(self, column: str, operator: str, value: Any, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns rows matching the condition. Uses index for '=' on primary key.

        Args:
            column: Name of the column to filter on.
            operator: Comparison operator (e.g., '=', '>', 'IN').
            value: Value to compare against.
            limit: Maximum number of rows to return.

        Returns:
            List[Dict[str, Any]]: List of matching row dictionaries.
        """
        if column == self.primary_key and operator == '=':
            if isinstance(value, int):
                row = self.get_row_by_id(value)
                return [row] if row else []
            # If not int, fallback to scan (index only supports int PKs for now)
        
        # Fallback to streaming scan for non-indexed columns or complex operators
        results = []
        for row in self.load_rows():
            if self._evaluate_condition(row.get(column), operator, value):
                results.append(row)
                if limit and len(results) >= limit:
                    break
        return results

    def delete_where(self, column: str, operator: str, value: Any) -> int:
        """Removes rows matching the condition and saves data.

        Args:
            column: Name of the column to filter on.
            operator: Comparison operator.
            value: Value to compare against.

        Returns:
            int: Number of rows deleted.
        """
        original_count = len(self.data)
        self.data = [row for row in self.data if not self._evaluate_condition(row.get(column), operator, value)]
        deleted_count = original_count - len(self.data)
        
        if deleted_count > 0:
            self.save_data()
        return deleted_count

    def update_where(self, condition_col: str, condition_op: str, condition_val: Any, 
                     target_col: str, target_val: Any) -> int:
        """Updates matching rows and saves data.

        Args:
            condition_col: Column for condition.
            condition_op: Operator for condition.
            condition_val: Value for condition.
            target_col: Column to update.
            target_val: New value for column.

        Returns:
            int: Number of rows updated.
        """
        updated_count = 0
        needs_index_rebuild = (target_col == self.primary_key)
        
        for row in self.data:
            if self._evaluate_condition(row.get(condition_col), condition_op, condition_val):
                row[target_col] = target_val
                updated_count += 1
        
        if updated_count > 0:
            self.save_data()
        return updated_count

    def _evaluate_condition(self, row_value: Any, operator: str, target_value: Any) -> bool:
        """Helper to decide if a row matches the condition, handling type comparisons.

        Args:
            row_value: The value from the row.
            operator: Comparison operator.
            target_value: The target value from the query.

        Returns:
            bool: True if condition matches, False otherwise.
        """
        if row_value is None:
            return False
        
        # Standardize for comparison if possible
        try:
            if isinstance(target_value, (int, float)) and not isinstance(row_value, (int, float)):
                row_value = float(row_value) if isinstance(target_value, float) else int(row_value)
            elif isinstance(row_value, (int, float)) and not isinstance(target_value, (int, float)):
                target_value = float(target_value) if isinstance(row_value, float) else int(target_value)
        except (ValueError, TypeError):
            pass

        if operator == '=': return row_value == target_value
        if operator == '!=': return row_value != target_value
        if operator == '>': return row_value > target_value
        if operator == '<': return row_value < target_value
        if operator == '>=': return row_value >= target_value
        if operator == '<=': return row_value <= target_value
        if operator == 'IN':
            if isinstance(target_value, list):
                return row_value in target_value
            return row_value == target_value
        
        return False

    def project_columns(self, rows: List[Dict[str, Any]], columns_str: str) -> List[Dict[str, Any]]:
        """Helper to return only specific columns from a list of rows.

        Args:
            rows: List of row dictionaries.
            columns_str: Comma-separated list of columns, or '*'.

        Returns:
            List[Dict[str, Any]]: Projected row dictionaries.
        """
        if columns_str == '*':
            return rows
        
        cols = [c.strip() for c in columns_str.split(',')]
        result = []
        for row in rows:
            new_row = {k: row[k] for k in cols if k in row}
            result.append(new_row)
        return result

    def add_column(self, column_name: str, column_type: Optional[str] = None) -> str:
        """Adds a new column to the table schema and updates all existing rows.

        Args:
            column_name: Name of the new column.
            column_type: Type of the new column (e.g., 'int', 'str').

        Returns:
            str: Success message.

        Raises:
            ValidationError: If column already exists.
        """
        # Check if column already exists
        if column_name in self.columns:
            raise ValidationError(f"Column '{column_name}' already exists in table '{self.table_name}'.")
        
        # Update schema
        self.columns.append(column_name)
        if column_type:
            self.column_types[column_name] = column_type
        
        # Determine default value based on type
        if column_type == 'int':
            default_value = 0
        elif column_type == 'str':
            default_value = ''
        else:
            default_value = None
        
        # Add column to all existing rows
        for row in self.data:
            row[column_name] = default_value
        
        # Atomic save
        self.save_data()
        
        return f"Column '{column_name}' added to table '{self.table_name}'."
    
    def _validate_row(self, row_data: Dict[str, Any]) -> None:
        """Validate a row without inserting it (for transaction support).

        Args:
            row_data: Row dictionary to validate.

        Raises:
            ValidationError: If validation fails.
        """
        if not isinstance(row_data, dict):
            raise ValidationError("Row data must be a dictionary.")
        
        # Validate columns
        row_keys = set(row_data.keys())
        expected_keys = set(self.columns)
        
        if row_keys != expected_keys:
            missing = expected_keys - row_keys
            extra = row_keys - expected_keys
            error_msg = f"Data validation failed for table '{self.table_name}'."
            if missing:
                error_msg += f" Missing columns: {missing}."
            if extra:
                error_msg += f" Extra columns: {extra}."
            raise ValidationError(error_msg)
        
        # Validate types
        for col, expected_type in self.column_types.items():
            value = row_data.get(col)
            if value is not None:
                if expected_type == 'int' and not isinstance(value, int):
                    raise ValidationError(f"Column '{col}' expects type 'int', got '{type(value).__name__}'.")
                elif expected_type == 'str' and not isinstance(value, str):
                    raise ValidationError(f"Column '{col}' expects type 'str', got '{type(value).__name__}'.")
    
    def _matches_condition(self, row: Dict[str, Any], column: str, operator: str, value: Any) -> bool:
        """Check if a row matches a WHERE condition.

        Args:
            row: Row dictionary.
            column: Filter column.
            operator: Filter operator.
            value: Filter value.

        Returns:
            bool: True if matches.
        """
        row_value = row.get(column)
        
        if operator == '=':
            return row_value == value
        elif operator == '!=':
            return row_value != value
        elif operator == '>':
            return row_value > value
        elif operator == '<':
            return row_value < value
        elif operator == '>=':
            return row_value >= value
        elif operator == '<=':
            return row_value <= value
        
        return False
    
    def drop_column(self, column_name: str) -> str:
        """Drops a column from the table.
        
        Args:
            column_name: Name of the column to drop.
            
        Returns:
            str: Success message.

        Raises:
            SchemaError: If attempting to drop primary key column.
            ValidationError: If column doesn't exist.
        """
        from .exceptions import SchemaError
        
        # Safety check: Cannot drop primary key
        if column_name == self.primary_key:
            raise SchemaError(
                f"Cannot drop column '{column_name}': it is the primary key. "
                f"Remove primary key constraint first or choose a different primary key."
            )
        
        # Check if column exists
        if column_name not in self.columns:
            raise ValidationError(f"Column '{column_name}' does not exist in table '{self.table_name}'.")
        
        # Remove from schema
        self.columns.remove(column_name)
        
        # Remove from column_types if present
        if column_name in self.column_types:
            del self.column_types[column_name]
        
        # Remove from unique_columns if present
        if column_name in self.unique_columns:
            self.unique_columns.remove(column_name)
        
        # Remove from foreign_keys if present
        if column_name in self.foreign_keys:
            del self.foreign_keys[column_name]
        
        # Remove column from all rows
        for row in self.data:
            if column_name in row:
                del row[column_name]
        
        # Rebuild index (in case it was affected)
        self._rebuild_index()
        
        # Atomic save
        self.save_data()
        
        return f"Column '{column_name}' dropped from table '{self.table_name}'."
    
    def rename_column(self, old_name: str, new_name: str) -> str:
        """Renames a column in the table.
        
        Args:
            old_name: Current name of the column.
            new_name: New name for the column.
            
        Returns:
            str: Success message.

        Raises:
            ValidationError: If old column doesn't exist or new name already exists.
        """
        # Check if old column exists
        if old_name not in self.columns:
            raise ValidationError(f"Column '{old_name}' does not exist in table '{self.table_name}'.")
        
        # Check if new name already exists
        if new_name in self.columns:
            raise ValidationError(f"Column '{new_name}' already exists in table '{self.table_name}'.")
        
        # Update columns list
        column_index = self.columns.index(old_name)
        self.columns[column_index] = new_name
        
        # Update column_types
        if old_name in self.column_types:
            self.column_types[new_name] = self.column_types.pop(old_name)
        
        # Update unique_columns
        if old_name in self.unique_columns:
            unique_index = self.unique_columns.index(old_name)
            self.unique_columns[unique_index] = new_name
        
        # Update foreign_keys
        if old_name in self.foreign_keys:
            self.foreign_keys[new_name] = self.foreign_keys.pop(old_name)
        
        # Update primary_key if it's being renamed
        if self.primary_key == old_name:
            self.primary_key = new_name
        
        # Rename column in all rows
        for row in self.data:
            if old_name in row:
                row[new_name] = row.pop(old_name)
        
        # Rebuild index (primary key might have been renamed)
        self._rebuild_index()
        
        # Atomic save
        self.save_data()
        
        return f"Column '{old_name}' renamed to '{new_name}' in table '{self.table_name}'."
