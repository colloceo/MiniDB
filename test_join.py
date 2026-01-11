from minidb import MiniDB
import os
import shutil

def test_joins_and_uniqueness():
    print("--- Testing MiniDB Joins & Uniqueness ---")
    
    test_dir = "test_join_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    db = MiniDB(data_dir=test_dir)
    
    # Setup tables
    db.execute_query("CREATE TABLE users (id, name)")
    db.execute_query("CREATE TABLE orders (order_id, user_id, amount)")
    
    # 1. Test Uniqueness (DuplicateKeyError)
    print("Inserting user 1...")
    db.execute_query("INSERT INTO users VALUES (1, 'Alice')")
    print("Inserting user 1 again (should fail)...")
    res = db.execute_query("INSERT INTO users VALUES (1, 'Bob')")
    print(f"Result: {res}")
    
    # 2. Test Join
    db.execute_query("INSERT INTO users VALUES (2, 'Bob')")
    db.execute_query("INSERT INTO orders VALUES (101, 1, 50.0)")
    db.execute_query("INSERT INTO orders VALUES (102, 1, 75.0)")
    db.execute_query("INSERT INTO orders VALUES (103, 2, 20.0)")
    
    print("\nExecuting Join: SELECT * FROM users JOIN orders ON users.id = orders.user_id")
    join_res = db.execute_query("SELECT * FROM users JOIN orders ON users.id = orders.user_id")
    
    print(f"Found {len(join_res)} joined rows:")
    for row in join_res:
        print(f"  {row}")

    # Verify counts
    if len(join_res) == 3:
        print("[v] Join results look correct.")
    else:
        print(f"[x] Expected 3 rows, got {len(join_res)}")

    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    print("--- Testing Complete ---")

if __name__ == "__main__":
    test_joins_and_uniqueness()
