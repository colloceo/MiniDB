import sys
try:
    import readline
except ImportError:
    # Readline not available (e.g., Windows)
    pass

from minidb import MiniDB

def print_table(data):
    """Simple standard-library implementation to print results as a table."""
    if not data or not isinstance(data, list):
        if isinstance(data, dict):
            # Special case for DESCRIBE output or single dictionary
            print_dict_as_table(data)
        else:
            print(data)
        return

    if len(data) == 0:
        print("Empty set (0 rows)")
        return

    # Get all unique columns across all rows
    columns = []
    for row in data:
        for k in row.keys():
            if k not in columns:
                columns.append(k)

    # Determine column widths
    widths = {col: len(col) for col in columns}
    for row in data:
        for col in columns:
            val = str(row.get(col, ""))
            widths[col] = max(widths[col], len(val))

    # Print header
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    _print_divider(header)
    print(header)
    _print_divider(header)

    # Print rows
    for row in data:
        line = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        print(line)
    
    _print_divider(header)
    print(f"({len(data)} rows in set)")

def print_dict_as_table(data):
    """Converts a dictionary (like DESCRIBE results) into a readable table."""
    # Special handling for DESCRIBE results which have specific structure
    if 'columns' in data and 'column_types' in data:
        print(f"\nSchema Information for Table:")
        rows = []
        for col in data['columns']:
            rows.append({
                'Column': col,
                'Type': data['column_types'].get(col, 'UNKNOWN'),
                'Key': 'PRI' if col == data.get('primary_key') else 'UNI' if col in data.get('unique_columns', []) else 'MUL' if col in data.get('foreign_keys', {}) else '',
                'Details': f"Ref: {data['foreign_keys'][col]}" if col in data.get('foreign_keys', {}) else '—'
            })
        print_table(rows)
    else:
        # Fallback for generic dict
        for k, v in data.items():
            print(f"{k}: {v}")

def _print_divider(header_line):
    print("-" * len(header_line))

def main():
    db = MiniDB()
    print("Welcome to MiniDB CLI.")
    print("Enter SQL commands. Use ';' to separate or terminate statements.")
    print("Tip: If you forget the ';', just press Enter on an empty line to execute.")
    print("Type 'exit' or 'quit' to logout.")
    
    buffer = ""
    while True:
        try:
            prompt = "minidb> " if not buffer else "      -> "
            line = input(prompt)
            
            # Exit check (immediate)
            if not buffer and line.strip().lower() in ('exit', 'quit', '.exit'):
                print("Goodbye!")
                break

            # Handle empty line as execution trigger for existing buffer
            if not line.strip() and buffer.strip():
                # User pressed Enter on empty line - execute what we have
                pass
            elif not line.strip() and not buffer.strip():
                continue
            else:
                buffer += " " + line
                # If it doesn't end in a semicolon, keep buffering
                if not buffer.strip().endswith(';'):
                    continue
                
            # Split and execute statements
            # We treat the buffer as a single block if no semicolon, 
            # or multiple blocks if semicolons exist.
            raw_buffer = buffer.strip()
            if not raw_buffer:
                continue
                
            statements = [s.strip() for s in raw_buffer.split(';') if s.strip()]
            if not statements and raw_buffer:
                statements = [raw_buffer] # Fallback for no semicolon execution
                
            buffer = "" # Reset buffer
            
            for stmt in statements:
                if len(statements) > 1:
                    print(f"\nExecuting: {stmt}")
                
                try:
                    results = db.execute_query(stmt)
                    
                    if isinstance(results, list):
                        print_table(results)
                    elif isinstance(results, dict):
                        print_dict_as_table(results)
                    else:
                        print(results)
                except Exception as stmt_error:
                    print(f"Statement Error: {stmt_error}")
                
        except KeyboardInterrupt:
            if buffer:
                buffer = ""
                print("\nBuffer cleared.")
                continue
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"CLI Error: {e}")

if __name__ == "__main__":
    main()
