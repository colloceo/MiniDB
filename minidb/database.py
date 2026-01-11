import os
import json
import uuid
import copy
from typing import List, Dict, Any, Optional, Union, Tuple
from .table import Table
from .parser import SQLParser
from .exceptions import DBError, TableNotFoundError

class TransactionManager:
    """Manages database transactions with BEGIN, COMMIT, and ROLLBACK support.
    
    Attributes:
        session_id (Optional[str]): Unique ID for the current transaction session.
        in_transaction (bool): True if a transaction is currently active.
        staging_area (Dict[str, Dict[str, Any]]): Buffer for uncommitted changes.
    """
    
    def __init__(self) -> None:
        """Initializes the transaction manager in an idle state."""
        self.session_id: Optional[str] = None
        self.in_transaction: bool = False
        self.staging_area: Dict[str, Dict[str, Any]] = {}  # {table_name: {'data': [...], 'modified': True}}
        
    def begin(self) -> str:
        """Starts a new transaction.
        
        Returns:
            str: Confirmation message with session ID.
            
        Raises:
            DBError: If a transaction is already in progress.
        """
        if self.in_transaction:
            raise DBError("Transaction already in progress. COMMIT or ROLLBACK first.")
        
        self.session_id = str(uuid.uuid4())
        self.in_transaction = True
        self.staging_area = {}
        return f"Transaction started (Session: {self.session_id[:8]})"
    
    def commit(self, tables: Dict[str, Table]) -> str:
        """Commits all staged changes to disk.
        
        Args:
            tables: Dictionary of table objects to update.
            
        Returns:
            str: Summary of the commit operation.
            
        Raises:
            DBError: If no transaction is active or commit fails.
        """
        if not self.in_transaction:
            raise DBError("No active transaction to commit.")
        
        committed_tables = []
        try:
            # Write all staged changes to disk
            for table_name, staged_data in self.staging_area.items():
                if staged_data.get('modified'):
                    table = tables.get(table_name)
                    if table:
                        # Apply staged data to table
                        table.data = staged_data['data']
                        table._rebuild_index()
                        table.save_data()
                        committed_tables.append(table_name)
            
            # Clear transaction state
            self._clear()
            return f"Transaction committed. Modified tables: {committed_tables if committed_tables else 'none'}"
        
        except Exception as e:
            # If commit fails, keep transaction open for retry or rollback
            raise DBError(f"Commit failed: {e}. Transaction still active.")
    
    def rollback(self) -> str:
        """Discards all staged changes.
        
        Returns:
            str: Summary of the rollback operation.
            
        Raises:
            DBError: If no active transaction exists.
        """
        if not self.in_transaction:
            raise DBError("No active transaction to rollback.")
        
        discarded_tables = list(self.staging_area.keys())
        self._clear()
        return f"Transaction rolled back. Discarded changes to: {discarded_tables if discarded_tables else 'none'}"
    
    def _clear(self) -> None:
        """Internal helper to reset the transaction state."""
        self.session_id = None
        self.in_transaction = False
        self.staging_area = {}
    
    def stage_table(self, table_name: str, table_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stages a table's data for modification within a transaction.
        
        Args:
            table_name: Name of the table to stage.
            table_data: The current in-memory rows of the table.
            
        Returns:
            List[Dict[str, Any]]: A deep copy of the row data for staging.
        """
        if table_name not in self.staging_area:
            # Create a deep copy of the table data
            self.staging_area[table_name] = {
                'data': copy.deepcopy(table_data),
                'modified': False
            }
        return self.staging_area[table_name]['data']
    
    def mark_modified(self, table_name: str) -> None:
        """Marks a staged table as modified so it can be committed.
        
        Args:
            table_name: Name of the table to mark.
        """
        if table_name in self.staging_area:
            self.staging_area[table_name]['modified'] = True

class MiniDB:
    """The central engine for managing multiple tables and executing queries.
    
    Attributes:
        data_dir (str): Directory where all data and metadata files are stored.
        metadata_path (str): Full path to the metadata.json file.
        tables (Dict[str, Table]): Map of table names to Table objects.
        parser (SQLParser): The SQL command parser.
        transaction (TransactionManager): Manager for atomic operations.
    """
    
    def __init__(self, data_dir: str = "data", metadata_file: str = "metadata.json") -> None:
        """Initializes the database engine and loads metadata.
        
        Args:
            data_dir: Base directory for storage.
            metadata_file: Filename for schema persistence.
        """
        self.data_dir = data_dir
        self.metadata_path = os.path.join(self.data_dir, metadata_file)
        self.tables: Dict[str, Table] = {}
        self.parser = SQLParser()
        self.transaction = TransactionManager()
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Internal method to load table schemas from metadata.json."""
        if not os.path.exists(self.metadata_path):
            return
        
        try:
            with open(self.metadata_path, "r") as f:
                metadata = json.load(f)
                for table_name, info in metadata.items():
                    self.tables[table_name] = Table(
                        table_name, 
                        info['columns'], 
                        primary_key=info.get('primary_key'),
                        column_types=info.get('column_types'),
                        unique_columns=info.get('unique_columns'),
                        foreign_keys=info.get('foreign_keys'),
                        data_dir=self.data_dir
                    )
        except Exception as e:
            print(f"Warning: Failed to load metadata: {e}")

    def _save_metadata(self) -> None:
        """Internal method to persist current table schemas to metadata.json.
        
        Raises:
            DBError: If saving fails.
        """
        metadata = {}
        for name, table in self.tables.items():
            metadata[name] = {
                'columns': table.columns,
                'primary_key': table.primary_key,
                'column_types': table.column_types,
                'unique_columns': table.unique_columns,
                'foreign_keys': table.foreign_keys
            }
        
        try:
            with open(self.metadata_path, "w") as f:
                json.dump(metadata, f, indent=4)
        except IOError as e:
            raise DBError(f"Failed to save metadata: {e}")

    def execute_query(self, query_string: str) -> Any:
        """Parses and executes a SQL query on the system.
        
        Args:
            query_string: The raw SQL string to execute.
            
        Returns:
            Any: The result of the query (list of rows, success message, or error string).
        """
        try:
            parsed = self.parser.parse(query_string)
            cmd_type = parsed['type']
            
            if cmd_type == 'SHOW_TABLES':
                table_list = self.get_tables()
                return [{'table_name': name} for name in table_list]

            # Transaction commands
            if cmd_type == 'BEGIN':
                return self.transaction.begin()
            
            if cmd_type == 'COMMIT':
                return self.transaction.commit(self.tables)
            
            if cmd_type == 'ROLLBACK':
                return self.transaction.rollback()

            if cmd_type == 'JOIN':
                table1_name = parsed['table1']
                table2_name = parsed['table2']
                if table1_name not in self.tables:
                    raise TableNotFoundError(f"Table '{table1_name}' does not exist.")
                if table2_name not in self.tables:
                    raise TableNotFoundError(f"Table '{table2_name}' does not exist.")
                
                table1 = self.tables[table1_name]
                table2 = self.tables[table2_name]
                
                return self._hash_join(
                    table1.select_all(), 
                    table2.select_all(), 
                    parsed['left_on'], 
                    parsed['right_on']
                )

            # Commands that require a target table
            table_name = parsed.get('table')
            if not table_name and cmd_type not in ['BEGIN', 'COMMIT', 'ROLLBACK', 'SHOW_TABLES', 'JOIN']:
                 raise DBError(f"Missing table name for command type {cmd_type}")

            if cmd_type == 'CREATE':
                return self._create_table(
                    table_name, 
                    parsed['columns'], 
                    column_types=parsed.get('column_types'),
                    unique_columns=parsed.get('unique_columns'),
                    foreign_keys=parsed.get('foreign_keys')
                )
            
            if table_name not in self.tables:
                raise TableNotFoundError(f"Table '{table_name}' does not exist.")
            
            table = self.tables[table_name]
            
            if cmd_type == 'INSERT':
                # Convert list of values to dict based on table columns
                row_dict = dict(zip(table.columns, parsed['values']))
                
                if self.transaction.in_transaction:
                    # In transaction: modify staging area only
                    staged_data = self.transaction.stage_table(table_name, table.data)
                    
                    # Validate and add row to staged data
                    table._validate_row(row_dict)  # Validate first
                    staged_data.append(row_dict)
                    self.transaction.mark_modified(table_name)
                    
                    return f"Row staged for insert into '{table_name}' (Transaction active)."
                else:
                    # Auto-commit mode: write to disk immediately
                    table.insert_row(row_dict)
                    return f"Row inserted into '{table_name}'."
            
            if cmd_type == 'SELECT':
                limit = parsed.get('limit')
                condition = parsed.get('condition')
                columns = parsed.get('columns', '*')
                
                # Handle nested subquery in WHERE clause
                if condition and isinstance(condition['value'], str) and condition['value'].startswith('(') and 'SELECT' in condition['value'].upper():
                    sub_sql = condition['value'][1:-1].strip()
                    sub_res = self.execute_query(sub_sql)
                    
                    if isinstance(sub_res, list):
                        # Flatten subquery result to a simple list of values
                        if sub_res and isinstance(sub_res[0], dict):
                            flattened = []
                            for row in sub_res:
                                flattened.extend(row.values())
                            condition['value'] = flattened
                        else:
                            condition['value'] = sub_res

                # Execution Logic
                if self.transaction.in_transaction and table_name in self.transaction.staging_area:
                    # Read from staging area if modified in transaction
                    staged_data = self.transaction.staging_area[table_name]['data']
                    res = staged_data
                    if condition:
                        res = [row for row in staged_data 
                                if table._matches_condition(row, condition['column'], 
                                                           condition['operator'], condition['value'])]
                    if limit:
                        res = res[:limit]
                else:
                    # Read from disk
                    if condition:
                        res = table.select_where(condition['column'], condition['operator'], condition['value'], limit=limit)
                    else:
                        res = table.select_all(limit=limit)
                
                # Apply column projection
                return table.project_columns(res, columns)
            
            if cmd_type == 'DELETE':
                condition = parsed['condition']
                
                if self.transaction.in_transaction:
                    # In transaction: modify staging area only
                    staged_data = self.transaction.stage_table(table_name, table.data)
                    
                    # Filter out rows that match the condition
                    original_count = len(staged_data)
                    staged_data[:] = [row for row in staged_data 
                                     if not table._matches_condition(row, condition['column'], 
                                                                    condition['operator'], condition['value'])]
                    count = original_count - len(staged_data)
                    
                    if count > 0:
                        self.transaction.mark_modified(table_name)
                    
                    return f"Staged deletion of {count} row(s) from '{table_name}' (Transaction active)."
                else:
                    # Auto-commit mode: write to disk immediately
                    count = table.delete_where(condition['column'], condition['operator'], condition['value'])
                    return f"Deleted {count} row(s) from '{table_name}'."
            
            if cmd_type == 'UPDATE':
                condition = parsed['condition']
                target_column = parsed['target_column']
                target_value = parsed['target_value']
                
                if self.transaction.in_transaction:
                    # In transaction: modify staging area only
                    staged_data = self.transaction.stage_table(table_name, table.data)
                    
                    # Update rows that match the condition
                    count = 0
                    for row in staged_data:
                        if table._matches_condition(row, condition['column'], 
                                                   condition['operator'], condition['value']):
                            row[target_column] = target_value
                            count += 1
                    
                    if count > 0:
                        self.transaction.mark_modified(table_name)
                    
                    return f"Staged update of {count} row(s) in '{table_name}' (Transaction active)."
                else:
                    # Auto-commit mode: write to disk immediately
                    count = table.update_where(
                        condition['column'], 
                        condition['operator'],
                        condition['value'], 
                        target_column, 
                        target_value
                    )
                    return f"Updated {count} row(s) in '{table_name}'."
            
            if cmd_type == 'ALTER_TABLE':
                # Add column to table
                result = table.add_column(
                    parsed['column_name'],
                    parsed.get('column_type')
                )
                # Update metadata after schema change
                self._save_metadata()
                return result
            
            if cmd_type == 'DROP_COLUMN':
                # Drop column from table
                result = table.drop_column(parsed['column_name'])
                # Update metadata after schema change
                self._save_metadata()
                return result
            
            if cmd_type == 'RENAME_COLUMN':
                # Rename column in table
                result = table.rename_column(parsed['old_name'], parsed['new_name'])
                # Update metadata after schema change
                self._save_metadata()
                return result
            
            if cmd_type == 'DROP_TABLE':
                # Drop entire table
                table_name = parsed['table']
                if table_name not in self.tables:
                    raise TableNotFoundError(f"Table '{table_name}' does not exist.")
                
                table = self.tables[table_name]
                
                # Delete the JSON file
                if os.path.exists(table.file_path):
                    os.remove(table.file_path)
                
                # Remove from tables dict
                del self.tables[table_name]
                
                # Update metadata
                self._save_metadata()
                
                return f"Table '{table_name}' dropped successfully."
            
            if cmd_type == 'RENAME_TABLE':
                # Rename entire table
                old_name = parsed['table']
                new_name = parsed['new_name']
                
                if old_name not in self.tables:
                    raise TableNotFoundError(f"Table '{old_name}' does not exist.")
                
                if new_name in self.tables:
                    raise DBError(f"Table '{new_name}' already exists.")
                
                table = self.tables[old_name]
                old_file_path = table.file_path
                new_file_path = os.path.join(self.data_dir, f"{new_name}.jsonl")
                
                # Rename the JSON file
                if os.path.exists(old_file_path):
                    os.rename(old_file_path, new_file_path)
                
                # Update table object
                table.table_name = new_name
                table.file_path = new_file_path
                
                # Update tables dict
                self.tables[new_name] = table
                del self.tables[old_name]
                
                # Update metadata
                self._save_metadata()
                
                return f"Table '{old_name}' renamed to '{new_name}' successfully."
            
            if cmd_type == 'DESCRIBE':
                return {
                    'columns': table.columns,
                    'primary_key': table.primary_key or 'id',
                    'column_types': table.column_types,
                    'unique_columns': table.unique_columns,
                    'foreign_keys': table.foreign_keys
                }
            
                
        except (DBError, TypeError) as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Unexpected Error: {e}"

    def get_tables(self) -> List[str]:
        """Returns a list of all table names currently registered in the database.
        
        Returns:
            List[str]: List of table names.
        """
        return list(self.tables.keys())

    def _nested_loop_join(self, left_rows: List[Dict[str, Any]], right_rows: List[Dict[str, Any]], 
                          left_on: Tuple[str, str], right_on: Tuple[str, str]) -> List[Dict[str, Any]]:
        """Performs a simple Nested Loop Join. Complexity: O(N*M).
        
        Args:
            left_rows: Rows from the left table.
            right_rows: Rows from the right table.
            left_on: (table_name, column_name) for left join condition.
            right_on: (table_name, column_name) for right join condition.
            
        Returns:
            List[Dict[str, Any]]: Joined results.
        """
        result = []
        l_table, l_col = left_on
        r_table, r_col = right_on
        
        for l_row in left_rows:
            for r_row in right_rows:
                if l_row.get(l_col) == r_row.get(r_col):
                    result.append(self._merge_rows(l_row, r_row, r_table))
        return result

    def _hash_join(self, left_rows: List[Dict[str, Any]], right_rows: List[Dict[str, Any]], 
                   left_on: Tuple[str, str], right_on: Tuple[str, str]) -> List[Dict[str, Any]]:
        """Performs an optimized Hash Join. Complexity: O(N+M).
        
        Args:
            left_rows: Rows from the left table.
            right_rows: Rows from the right table.
            left_on: (table_name, column_name) for left condition.
            right_on: (table_name, column_name) for right condition.
            
        Returns:
            List[Dict[str, Any]]: Joined results.
        """
        result = []
        l_table, l_col = left_on
        r_table, r_col = right_on
        
        # Build Phase: Identify the smaller table and build a hash map
        build_rows, probe_rows = left_rows, right_rows
        build_col, probe_col = l_col, r_col
        build_table, probe_table = l_table, r_table
        swapped = False
        
        if len(right_rows) < len(left_rows):
            build_rows, probe_rows = right_rows, left_rows
            build_col, probe_col = r_col, l_col
            build_table, probe_table = r_table, l_table
            swapped = True
            
        hash_map: Dict[Any, List[Dict[str, Any]]] = {}
        for row in build_rows:
            key = row.get(build_col)
            if key not in hash_map:
                hash_map[key] = []
            hash_map[key].append(row)
        
        for p_row in probe_rows:
            key = p_row.get(probe_col)
            if key in hash_map:
                for b_row in hash_map[key]:
                    if swapped:
                        # left=probe, right=build
                        result.append(self._merge_rows(p_row, b_row, build_table))
                    else:
                        # left=build, right=probe
                        result.append(self._merge_rows(b_row, p_row, probe_table))
        return result

    def _merge_rows(self, left_row: Dict[str, Any], right_row: Dict[str, Any], r_table_name: str) -> Dict[str, Any]:
        """Helper to merge two rows and handle column name collisions.
        
        Args:
            left_row: Row from the left table.
            right_row: Row from the right table.
            r_table_name: Name of the right table for prefixing collisions.
            
        Returns:
            Dict[str, Any]: Merged row dictionary.
        """
        merged = left_row.copy()
        for k, v in right_row.items():
            if k in merged:
                merged[f"{r_table_name}_{k}"] = v
            else:
                merged[k] = v
        return merged

    def _create_table(self, name: str, columns: List[str], column_types: Optional[Dict[str, str]] = None, 
                      unique_columns: Optional[List[str]] = None, foreign_keys: Optional[Dict[str, str]] = None) -> str:
        """Internal method to create and initialize a new table.
        
        Args:
            name: Table name.
            columns: List of column names.
            column_types: Map of col -> type.
            unique_columns: List of columns with uniqueness constraints.
            foreign_keys: Reference map.
            
        Returns:
            str: Status message.
        """
        if name in self.tables:
            return f"Error: Table '{name}' already exists."
        
        self.tables[name] = Table(
            name, columns, 
            column_types=column_types, 
            unique_columns=unique_columns,
            foreign_keys=foreign_keys,
            data_dir=self.data_dir
        )
        self._save_metadata()
        return f"Table '{name}' created with columns {columns}."
