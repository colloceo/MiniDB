from minidb import SQLParser, DBError

def test_parser():
    print("--- Testing MiniDB SQL Parser ---")
    parser = SQLParser()
    
    test_cases = [
        ("CREATE TABLE students (id, name, grade)", "CREATE"),
        ("INSERT INTO students VALUES (1, 'Alice', 95.5)", "INSERT"),
        ("SELECT * FROM students", "SELECT"),
        ("DROP TABLE students", "DROP_TABLE"),
        ("ALTER TABLE students RENAME TO pupils", "RENAME_TABLE"),
        ("ALTER TABLE students ADD age INT", "ALTER_TABLE"),
        ("ALTER TABLE students DROP COLUMN age", "DROP_COLUMN"),
        ("ALTER TABLE students RENAME COLUMN name TO full_name", "RENAME_COLUMN"),
        ("SHOW TABLES", "SHOW_TABLES"),
        ("DESCRIBE students", "DESCRIBE")
    ]
    
    success_count = 0
    for sql, expected_type in test_cases:
        try:
            result = parser.parse(sql)
            print(f"[v] Parsed: '{sql}' -> {result['type']}")
            if result['type'] != expected_type:
                print(f"[x] Error: Expected type {expected_type}, got {result['type']}")
            else:
                success_count += 1
        except DBError as e:
            print(f"[x] Failed to parse '{sql}': {e}")

    # Test real error case (invalid syntax)
    try:
        parser.parse("INVALID COMMAND students")
        print("[x] Error: Should have failed on invalid syntax")
    except DBError as e:
        print(f"[v] Successfully caught invalid syntax: {e}")
        success_count += 1

    print(f"--- Testing Complete: {success_count}/{len(test_cases) + 1} passed ---")
    
    if success_count < (len(test_cases) + 1):
        exit(1)

if __name__ == "__main__":
    test_parser()
