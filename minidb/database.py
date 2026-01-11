import os
import json
import uuid
import copy
from .table import Table
from .parser import SQLParser
from .exceptions import DBError, TableNotFoundError

class TransactionManager:
    """Manages database transactions with BEGIN, COMMIT, and ROLLBACK support."""
    
    def __init__(self):
        self.session_id = None
        self.in_transaction = False
        self.staging_area = {}  # {table_name: {'data': [...], 'modified': True}}
        
    def begin(self):
        """Start a new transaction."""
        if self.in_transaction:
            raise DBError("Transaction already in progress. COMMIT or ROLLBACK first.")
        
        self.session_id = str(uuid.uuid4())
        self.in_transaction = True
        self.staging_area = {}
        return f"Transaction started (Session: {self.session_id[:8]})"
    
    def commit(self, tables):
        """Commit all staged changes to disk."""
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
    
    def rollback(self):
        """Discard all staged changes."""
        if not self.in_transaction:
            raise DBError("No active transaction to rollback.")
        
        discarded_tables = list(self.staging_area.keys())
        self._clear()
        return f"Transaction rolled back. Discarded changes to: {discarded_tables if discarded_tables else 'none'}"
    
    def _clear(self):
        """Clear transaction state."""
        self.session_id = None
        self.in_transaction = False
        self.staging_area = {}
    
    def stage_table(self, table_name, table_data):
        """Stage a table's data for modification."""
        if table_name not in self.staging_area:
            # Create a deep copy of the table data
            self.staging_area[table_name] = {
                'data': copy.deepcopy(table_data),
                'modified': False
            }
        return self.staging_area[table_name]['data']
    
    def mark_modified(self, table_name):
        """Mark a table as modified in the current transaction."""
        if table_name in self.staging_area:
            self.staging_area[table_name]['modified'] = True

class MiniDB:
    def __init__(self, data_dir="data", metadata_file="metadata.json"):
        self.data_dir = data_dir
        self.metadata_path = os.path.join(self.data_dir, metadata_file)
        self.tables = {}
        self.parser = SQLParser()
        self.transaction = TransactionManager()  # Transaction manager
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self._load_metadata()

    def _load_metadata(self):
        """Loads table definitions from metadata.json."""
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

    def _save_metadata(self):
        """Saves current table definitions to metadata.json."""
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

    def execute_query(self, query_string):
        """Parses and executes a SQL query."""
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
                # SELECT always reads from current state
                if self.transaction.in_transaction and table_name in self.transaction.staging_area:
                    # Read from staging area if modified in transaction
                    staged_data = self.transaction.staging_area[table_name]['data']
                    condition = parsed.get('condition')
                    if condition:
                        # Apply WHERE filter to staged data
                        return [row for row in staged_data 
                                if table._matches_condition(row, condition['column'], 
                                                           condition['operator'], condition['value'])]
                    return staged_data
                else:
                    # Read from disk
                    condition = parsed.get('condition')
                    if condition:
                        return table.select_where(condition['column'], condition['operator'], condition['value'])
                    return table.select_all()
            
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
                new_file_path = os.path.join(self.data_dir, f"{new_name}.json")
                
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

    def get_tables(self):
        """Returns a list of all table names."""
        return list(self.tables.keys())

    def _nested_loop_join(self, left_rows, right_rows, left_on, right_on):
        """Simple Nested Loop Join implementation."""
        result = []
        l_table, l_col = left_on
        r_table, r_col = right_on
        
        for l_row in left_rows:
            for r_row in right_rows:
                if l_row.get(l_col) == r_row.get(r_col):
                    result.append(self._merge_rows(l_row, r_row, r_table))
        return result

    def _hash_join(self, left_rows, right_rows, left_on, right_on):
        """Optimized Hash Join implementation O(N+M)."""
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
            
        hash_map = {}
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

    def _merge_rows(self, left_row, right_row, r_table_name):
        """Helper to merge two rows and handle column name collisions."""
        merged = left_row.copy()
        for k, v in right_row.items():
            if k in merged:
                merged[f"{r_table_name}_{k}"] = v
            else:
                merged[k] = v
        return merged

    def _create_table(self, name, columns, column_types=None, unique_columns=None, foreign_keys=None):
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
