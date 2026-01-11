from minidb import MiniDB
import os
import shutil
import time

def test_engine():
    print("--- Testing MiniDB Engine & Indexing ---")
    
    test_dir = "test_engine_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    db = MiniDB(data_dir=test_dir)
    
    # 1. Create Table
    print(db.execute_query("CREATE TABLE users (id, name, email)"))
    
    # 2. Insert Data
    db.execute_query("INSERT INTO users VALUES (1, 'Alice', 'alice@test.com')")
    db.execute_query("INSERT INTO users VALUES (2, 'Bob', 'bob@test.com')")
    db.execute_query("INSERT INTO users VALUES (3, 'Charlie', 'charlie@test.com')")
    
    # 3. Select All
    all_users = db.execute_query("SELECT * FROM users")
    print(f"All users: {len(all_users)}")
    
    # 4. Select by Primary Key (id=1) - O(1) Internal test
    print("Testing O(1) Index Lookup for id=2...")
    start_time = time.perf_counter()
    alice = db.execute_query("SELECT * FROM users WHERE id=2")
    end_time = time.perf_counter()
    print(f"Result: {alice}")
    print(f"Lookup took: {end_time - start_time:.6f}s")
    
    # 5. Persistence Check
    print("\nRestarting DB...")
    db2 = MiniDB(data_dir=test_dir)
    bob = db2.execute_query("SELECT * FROM users WHERE id=2")
    if bob and bob[0]['name'] == 'Bob':
        print("[v] Persistence verified after restart.")
    else:
        print(f"[x] Persistence failed: {bob}")

    # 6. Duplicate PK Check
    res = db2.execute_query("INSERT INTO users VALUES (1, 'Clone', 'clone@test.com')")
    if "Error" in res:
        print(f"[v] Duplicate PK caught: {res}")
    else:
        print("[x] Failed to catch duplicate PK.")

    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    print("--- Testing Complete ---")

if __name__ == "__main__":
    test_engine()
