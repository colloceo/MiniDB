import os
import json
from .table import Table
from .parser import SQLParser
from .exceptions import DBError, TableNotFoundError

class MiniDB:
    def __init__(self, data_dir="data", metadata_file="metadata.json"):
        self.data_dir = data_dir
        self.metadata_path = os.path.join(self.data_dir, metadata_file)
        self.tables = {}
        self.parser = SQLParser()
        
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
                return self.get_tables()

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

            table_name = parsed.get('table')
            if not table_name:
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
                table.insert_row(row_dict)
                return f"Row inserted into '{table_name}'."
            
            if cmd_type == 'SELECT':
                condition = parsed.get('condition')
                if condition:
                    return table.select_where(condition['column'], condition['operator'], condition['value'])
                return table.select_all()
            
            if cmd_type == 'DELETE':
                condition = parsed['condition']
                count = table.delete_where(condition['column'], condition['operator'], condition['value'])
                return f"Deleted {count} row(s) from '{table_name}'."
            
            if cmd_type == 'UPDATE':
                condition = parsed['condition']
                count = table.update_where(
                    condition['column'], 
                    condition['operator'],
                    condition['value'], 
                    parsed['target_column'], 
                    parsed['target_value']
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
            
        # Probe Phase: Iterate through the larger table and check for matches
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
