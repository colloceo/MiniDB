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
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    # Print rows
    for row in data:
        line = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        print(line)
    
    print("-" * len(header))
    print(f"({len(data)} rows in set)")

def main():
    db = MiniDB()
    print("Welcome to MiniDB. Type 'exit' to quit.")
    
    while True:
        try:
            query = input("minidb> ").strip()
            
            if not query:
                continue
                
            if query.lower() in ('exit', 'quit', '.exit'):
                print("Goodbye!")
                break
                
            result = db.execute_query(query)
            
            if isinstance(result, list):
                print_table(result)
            else:
                print(result)
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
