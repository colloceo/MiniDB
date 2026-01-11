from minidb import MiniDB
import os
import shutil

def test_disk_index():
    data_dir = "test_index_data"
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
        
    db = MiniDB(data_dir=data_dir)
    db.execute_query("CREATE TABLE users (id int, name str, email str)")
    
    # Insert some data
    print("Inserting rows...")
    db.execute_query("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')")
    db.execute_query("INSERT INTO users VALUES (3, 'Charlie', 'charlie@example.com')")
    db.execute_query("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com')")
    
    print("\nVerifying Index lookups (O(log N) path)...")
    
    # Check Bob (ID 2)
    res = db.execute_query("SELECT * FROM users WHERE id = 2")
    print(f"ID 2 Result: {res}")
    assert len(res) == 1
    assert res[0]['name'] == 'Bob'
    
    # Check Alice (ID 1)
    res = db.execute_query("SELECT * FROM users WHERE id = 1")
    print(f"ID 1 Result: {res}")
    assert len(res) == 1
    assert res[0]['name'] == 'Alice'
    
    # Check Non-existent
    res = db.execute_query("SELECT * FROM users WHERE id = 99")
    print(f"ID 99 Result: {res}")
    assert len(res) == 0
    
    # Verify index file exists
    idx_path = os.path.join(data_dir, "users.idx")
    assert os.path.exists(idx_path)
    idx_size = os.path.getsize(idx_path)
    print(f"Index file size: {idx_size} bytes (Expected 24 for 3 entries)")
    assert idx_size == 24
    
    # Re-initialize to test rebuild and loading
    print("\nRe-initializing database (testing index persistence)...")
    db2 = MiniDB(data_dir=data_dir)
    res = db2.execute_query("SELECT * FROM users WHERE id = 3")
    print(f"ID 3 Result from new instance: {res}")
    assert len(res) == 1
    assert res[0]['name'] == 'Charlie'

    print("\nAll Disk-Based Index tests passed!")
    
    # Cleanup
    shutil.rmtree(data_dir)

if __name__ == "__main__":
    test_disk_index()
