import json
import os
from .exceptions import DBError, ValidationError

class Table:
    def __init__(self, table_name, columns, primary_key=None, column_types=None, unique_columns=None, foreign_keys=None, data_dir="data"):
        self.table_name = table_name
        self.columns = columns
        # Default primary key is the first column if not specified
        self.primary_key = primary_key if primary_key else (columns[0] if columns else None)
        self.column_types = column_types or {} # dict: {col: type_name}
        self.unique_columns = unique_columns or [] # list: [col, col]
        self.foreign_keys = foreign_keys or {} # dict: {local_col: 'ref_table.ref_col'}
        self.data_dir = data_dir
        self.file_path = os.path.join(self.data_dir, f"{table_name}.json")
        self.data = []
        self.index = {} # Primary Key -> Row Data mapping
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.load_data()

    def _rebuild_index(self):
        """Rebuilds the hash map index from the in-memory data."""
        self.index = {}
        if not self.primary_key:
            return
        for row in self.data:
            pk_val = row.get(self.primary_key)
            if pk_val is not None:
                self.index[pk_val] = row

    def load_data(self):
        """Reads data from the local JSON file and builds index."""
        if not os.path.exists(self.file_path):
            self.data = []
            self.index = {}
            return
        
        try:
            with open(self.file_path, "r") as f:
                self.data = json.load(f)
            self._rebuild_index()
        except (json.JSONDecodeError, IOError) as e:
            raise DBError(f"Failed to load data for table '{self.table_name}': {e}")

    def save_data(self):
        """Writes the current data list to the JSON file atomically."""
        temp_path = f"{self.file_path}.tmp"
        try:
            with open(temp_path, "w") as f:
                json.dump(self.data, f, indent=4)
                f.flush()
                # os.fsync requires a file descriptor
                os.fsync(f.fileno())
            
            # Atomic swap
            os.replace(temp_path, self.file_path)
        except (IOError, OSError) as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise DBError(f"Failed to save data for table '{self.table_name}': {e}")

    def insert_row(self, row_data):
        """Validates and appends a row, updating the index and file."""
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

        # Check primary key uniqueness
        pk_val = row_data.get(self.primary_key)
        if pk_val in self.index:
            from .exceptions import DuplicateKeyError
            raise DuplicateKeyError(f"Duplicate primary key '{pk_val}' for table '{self.table_name}'.")

        # Check secondary unique constraints
        for col in self.unique_columns:
            if col == self.primary_key: continue # Already checked
            val = row_data.get(col)
            if any(r.get(col) == val for r in self.data):
                from .exceptions import UniqueConstraintError
                raise UniqueConstraintError(f"Unique constraint violation: value '{val}' already exists in column '{col}'.")

        self.data.append(row_data)
        if self.primary_key:
            self.index[pk_val] = row_data
        self.save_data()

    def select_all(self):
        """Returns all rows (copy)."""
        return list(self.data)

    def select_where(self, column, operator, value):
        """Returns rows matching the condition. Uses index for '=' on primary key."""
        if column == self.primary_key and operator == '=':
            row = self.index.get(value)
            return [row] if row else []
        
        # Fallback to full scan for non-indexed columns or complex operators
        return [row for row in self.data if self._evaluate_condition(row.get(column), operator, value)]

    def delete_where(self, column, operator, value):
        """Removes rows matching the condition and saves data."""
        original_count = len(self.data)
        self.data = [row for row in self.data if not self._evaluate_condition(row.get(column), operator, value)]
        deleted_count = original_count - len(self.data)
        
        if deleted_count > 0:
            self._rebuild_index()
            self.save_data()
        return deleted_count

    def update_where(self, condition_col, condition_op, condition_val, target_col, target_val):
        """Updates matching rows and saves data."""
        updated_count = 0
        needs_index_rebuild = (target_col == self.primary_key)
        
        for row in self.data:
            if self._evaluate_condition(row.get(condition_col), condition_op, condition_val):
                row[target_col] = target_val
                updated_count += 1
        
        if updated_count > 0:
            if needs_index_rebuild:
                self._rebuild_index()
            self.save_data()
        return updated_count

    def _evaluate_condition(self, row_value, operator, target_value):
        """Helper to decide if a row matches the condition, handling type comparisons."""
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
        
        return False

    def add_column(self, column_name, column_type=None):
        """Adds a new column to the table schema and updates all existing rows."""
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
