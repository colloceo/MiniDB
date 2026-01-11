from minidb import MiniDB
import os
import shutil

def test_metadata():
    test_dir = "test_metadata_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    db = MiniDB(data_dir=test_dir)
    db.execute_query("CREATE TABLE users (id, username)")
    db.execute_query("CREATE TABLE posts (id, title, author_id)")
    
    # 1. Test SHOW TABLES
    print("Executing SHOW TABLES...")
    res = db.execute_query("SHOW TABLES")
    print(f"Result: {res}")
    if set(res) == {"users", "posts"}:
        print("[v] SHOW TABLES works correctly.")
    else:
        print(f"[x] SHOW TABLES failed: {res}")

    # 2. Test get_tables() method
    print("\nCalling db.get_tables()...")
    res_method = db.get_tables()
    print(f"Result: {res_method}")
    if set(res_method) == {"users", "posts"}:
        print("[v] get_tables() method works correctly.")
    else:
        print(f"[x] get_tables() method failed: {res_method}")

    # 3. Test DESCRIBE (regression)
    print("\nExecuting DESCRIBE users...")
    res_desc = db.execute_query("DESCRIBE users")
    print(f"Result: {res_desc}")
    if res_desc['columns'] == ['id', 'username']:
        print("[v] DESCRIBE users still works.")
    else:
        print(f"[x] DESCRIBE users failed: {res_desc}")

    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    print("\n--- Metadata Verification Complete ---")

if __name__ == "__main__":
    test_metadata()
