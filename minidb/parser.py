import re
from typing import Any, Dict, Optional, Union
from .exceptions import DBError

class SQLParser:
    """A regex-based parser for translating SQL strings into execution payloads.
    
    Attributes:
        patterns (Dict[str, re.Pattern]): Map of command types to compiled regex patterns.
    """
    
    def __init__(self) -> None:
        """Initializes the parser with predefined SQL regex patterns."""
        self.patterns: Dict[str, re.Pattern] = {
            'CREATE': re.compile(r"CREATE\s+TABLE\s+(\w+)\s*\((.*)\)", re.IGNORECASE),
            'INSERT': re.compile(r"INSERT\s+INTO\s+(\w+)\s+VALUES\s*\((.*)\)", re.IGNORECASE),
            'SELECT_JOIN': re.compile(r"SELECT\s+\*\s+FROM\s+(\w+)\s+JOIN\s+(\w+)\s+ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)", re.IGNORECASE),
            'SELECT': re.compile(r"SELECT\s+(\*|[\w,\s]+)\s+FROM\s+(\w+)(?:\s+WHERE\s+(\w+)\s*(>=|<=|!=|>|<|=|\s+IN\s+)\s*(.*?))?(?:\s+LIMIT\s+(\d+))?$", re.IGNORECASE),
            'DELETE': re.compile(r"DELETE\s+FROM\s+(\w+)\s+WHERE\s+(\w+)\s*(>=|<=|!=|>|<|=)\s*(.*)", re.IGNORECASE),
            'UPDATE': re.compile(r"UPDATE\s+(\w+)\s+SET\s+(\w+)\s*=\s*(.*)\s+WHERE\s+(\w+)\s*(>=|<=|!=|>|<|=)\s*(.*)", re.IGNORECASE),
            'ALTER_TABLE': re.compile(r"ALTER\s+TABLE\s+(\w+)\s+ADD\s+(\w+)\s+(\w+)", re.IGNORECASE),
            'DROP_COLUMN': re.compile(r"ALTER\s+TABLE\s+(\w+)\s+DROP\s+COLUMN\s+(\w+)", re.IGNORECASE),
            'RENAME_COLUMN': re.compile(r"ALTER\s+TABLE\s+(\w+)\s+RENAME\s+COLUMN\s+(\w+)\s+TO\s+(\w+)", re.IGNORECASE),
            'DROP_TABLE': re.compile(r"DROP\s+TABLE\s+(\w+)", re.IGNORECASE),
            'RENAME_TABLE': re.compile(r"ALTER\s+TABLE\s+(\w+)\s+RENAME\s+TO\s+(\w+)", re.IGNORECASE),
            'BEGIN': re.compile(r"BEGIN\s+TRANSACTION|BEGIN", re.IGNORECASE),
            'COMMIT': re.compile(r"COMMIT", re.IGNORECASE),
            'ROLLBACK': re.compile(r"ROLLBACK", re.IGNORECASE),
            'DESCRIBE': re.compile(r"(?:DESCRIBE|DESC)\s+(\w+)", re.IGNORECASE),
            'SHOW_TABLES': re.compile(r"SHOW\s+TABLES", re.IGNORECASE)
        }

    def parse(self, sql_string: str) -> Dict[str, Any]:
        """Parses a SQL string and returns a structured dictionary.
        
        Args:
            sql_string: The raw SQL string.
            
        Returns:
            Dict[str, Any]: Structured representation of the SQL command.
            
        Raises:
            DBError: If the command syntax is unrecognized.
        """
        sql_string = sql_string.strip()
        
        for cmd_type, pattern in self.patterns.items():
            match = pattern.match(sql_string)
            if match:
                return self._process_match(cmd_type, match)
        
        raise DBError(f"Syntax Error: Could not parse command '{sql_string}'")

    def _process_match(self, cmd_type: str, match: re.Match) -> Dict[str, Any]:
        """Processes regex matches into structured payloads.
        
        Args:
            cmd_type: The identified command type (e.g., 'SELECT', 'CREATE').
            match: The regex match object.
            
        Returns:
            Dict[str, Any]: A payload dictionary specific to the command type.
        """
        if cmd_type == 'CREATE':
            table_name = match.group(1)
            raw_cols = [c.strip() for c in match.group(2).split(',')]
            
            columns = []
            column_types = {}
            unique_columns = []
            foreign_keys = {}  # {local_col: 'ref_table.ref_col'}
            
            for part in raw_cols:
                # Check if this is a FOREIGN KEY constraint
                fk_match = re.match(r'FOREIGN\s+KEY\s*\((\w+)\)\s+REFERENCES\s+(\w+)\s*\((\w+)\)', part, re.IGNORECASE)
                if fk_match:
                    local_col = fk_match.group(1)
                    ref_table = fk_match.group(2)
                    ref_col = fk_match.group(3)
                    foreign_keys[local_col] = f"{ref_table}.{ref_col}"
                    continue
                
                # Regular column definition: name [type] [UNIQUE]
                parts = part.split()
                if not parts: continue
                col_name = parts[0]
                columns.append(col_name)
                
                # Detect type
                for p in parts[1:]:
                    low_p = p.lower()
                    if low_p in ['int', 'str']:
                        column_types[col_name] = low_p
                    if low_p == 'unique':
                        unique_columns.append(col_name)
            
            return {
                'type': 'CREATE',
                'table': table_name,
                'columns': columns,
                'column_types': column_types,
                'unique_columns': unique_columns,
                'foreign_keys': foreign_keys
            }
        
        elif cmd_type == 'INSERT':
            table_name = match.group(1)
            raw_values = [v.strip() for v in match.group(2).split(',')]
            processed_values = [self._infer_type(v) for v in raw_values]
            return {
                'type': 'INSERT',
                'table': table_name,
                'values': processed_values
            }
        
        elif cmd_type == 'SELECT':
            columns = match.group(1).strip()
            table_name = match.group(2)
            condition = None
            if match.group(3) and match.group(4) and match.group(5):
                condition = {
                    'column': match.group(3),
                    'operator': match.group(4).strip().upper(),
                    'value': self._infer_type(match.group(5).strip())
                }
            return {
                'type': 'SELECT',
                'columns': columns,
                'table': table_name,
                'condition': condition,
                'limit': int(match.group(6)) if len(match.groups()) >= 6 and match.group(6) else None
            }
        
        elif cmd_type == 'SELECT_JOIN':
            return {
                'type': 'JOIN',
                'table1': match.group(1),
                'table2': match.group(2),
                'left_on': (match.group(3).strip(), match.group(4).strip()),
                'right_on': (match.group(5).strip(), match.group(6).strip())
            }
        
        elif cmd_type == 'DELETE':
            return {
                'type': 'DELETE',
                'table': match.group(1),
                'condition': {
                    'column': match.group(2),
                    'operator': match.group(3),
                    'value': self._infer_type(match.group(4).strip())
                }
            }
        
        elif cmd_type == 'UPDATE':
            return {
                'type': 'UPDATE',
                'table': match.group(1),
                'target_column': match.group(2),
                'target_value': self._infer_type(match.group(3).strip()),
                'condition': {
                    'column': match.group(4),
                    'operator': match.group(5),
                    'value': self._infer_type(match.group(6).strip())
                }
            }
        
        elif cmd_type == 'ALTER_TABLE':
            return {
                'type': 'ALTER_TABLE',
                'table': match.group(1),
                'column_name': match.group(2),
                'column_type': match.group(3).lower()
            }
        
        elif cmd_type == 'DROP_COLUMN':
            return {
                'type': 'DROP_COLUMN',
                'table': match.group(1),
                'column_name': match.group(2)
            }
        
        elif cmd_type == 'RENAME_COLUMN':
            return {
                'type': 'RENAME_COLUMN',
                'table': match.group(1),
                'old_name': match.group(2),
                'new_name': match.group(3)
            }
        
        elif cmd_type == 'DROP_TABLE':
            return {
                'type': 'DROP_TABLE',
                'table': match.group(1)
            }
        
        elif cmd_type == 'RENAME_TABLE':
            return {
                'type': 'RENAME_TABLE',
                'table': match.group(1),
                'new_name': match.group(2)
            }
        
        elif cmd_type == 'DESCRIBE':
            return {
                'type': 'DESCRIBE',
                'table': match.group(1)
            }
        
        elif cmd_type == 'BEGIN':
            return {'type': 'BEGIN', 'table': None}
        
        elif cmd_type == 'COMMIT':
            return {'type': 'COMMIT', 'table': None}
        
        elif cmd_type == 'ROLLBACK':
            return {'type': 'ROLLBACK', 'table': None}
        
        elif cmd_type == 'SHOW_TABLES':
            return {'type': 'SHOW_TABLES', 'table': None}
        
        return {}

    def _infer_type(self, value: str) -> Union[int, float, str]:
        """Helper to convert string values from SQL to appropriate Python types.
        
        Args:
            value: The string value from the SQL command.
            
        Returns:
            Union[int, float, str]: The converted value.
        """
        # Remove quotes if present
        if (value.startswith("'") and value.endswith("'")) or \
           (value.startswith('"') and value.endswith('"')):
            return value[1:-1]
        
        # Try numeric types
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            return value
