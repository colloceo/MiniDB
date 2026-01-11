from minidb import MiniDB
import os
import shutil

def test_describe():
    test_dir = "test_describe_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    db = MiniDB(data_dir=test_dir)
    db.execute_query("CREATE TABLE students (id, name, grade)")
    
    # Test DESCRIBE
    print("Executing DESCRIBE students...")
    res = db.execute_query("DESCRIBE students")
    print(f"Result: {res}")
    
    expected = {'columns': ['id', 'name', 'grade'], 'primary_key': 'id'}
    if res == expected:
        print("[v] DESCRIBE command works correctly.")
    else:
        print(f"[x] DESCRIBE command failed. Expected {expected}, got {res}")

    # Test DESCRIBE non-existent table
    print("\nExecuting DESCRIBE non_existent...")
    res = db.execute_query("DESCRIBE non_existent")
    print(f"Result: {res}")
    if "Error" in res:
        print("[v] DESCRIBE non-existent table correctly returns an error.")
    else:
        print(f"[x] DESCRIBE non-existent table failed to return an error: {res}")

    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    print("\n--- DESCRIBE Verification Complete ---")

if __name__ == "__main__":
    test_describe()
