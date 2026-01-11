from minidb import SQLParser, DBError

def test_parser():
    print("--- Testing MiniDB SQL Parser ---")
    parser = SQLParser()
    
    test_cases = [
        ("CREATE TABLE students (id, name, grade)", "CREATE"),
        ("INSERT INTO students VALUES (1, 'Alice', 95.5)", "INSERT"),
        ("SELECT * FROM students", "SELECT")
    ]
    
    for sql, expected_type in test_cases:
        try:
            result = parser.parse(sql)
            print(f"[v] Parsed: '{sql}' -> {result}")
            if result['type'] != expected_type:
                print(f"[x] Error: Expected type {expected_type}, got {result['type']}")
        except DBError as e:
            print(f"[x] Failed to parse '{sql}': {e}")

    # Test error case
    try:
        parser.parse("DROP TABLE students")
        print("[x] Error: Should have failed on unsupported command 'DROP'")
    except DBError as e:
        print(f"[v] Successfully caught unsupported command: {e}")

    print("--- Testing Complete ---")

if __name__ == "__main__":
    test_parser()
