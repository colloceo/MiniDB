import time
import os
import shutil
from minidb import MiniDB

def run_benchmark():
    test_dir = "benchmark_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    db = MiniDB(data_dir=test_dir)
    
    # 1. Setup tables
    db.execute_query("CREATE TABLE users (id, name)")
    db.execute_query("CREATE TABLE orders (order_id, user_id, amount)")
    
    # 2. Insert data
    NUM_USERS = 500
    NUM_ORDERS = 1000
    
    print(f"Inserting {NUM_USERS} users and {NUM_ORDERS} orders...")
    for i in range(NUM_USERS):
        db.execute_query(f"INSERT INTO users VALUES ({i}, 'User {i}')")
    
    for i in range(NUM_ORDERS):
        user_id = i % NUM_USERS
        db.execute_query(f"INSERT INTO orders VALUES ({i}, {user_id}, {i*10.5})")
    
    # query
    query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
    
    # Benchmark Hash Join (current implementation)
    start_time = time.time()
    results_hash = db.execute_query(query)
    hash_duration = time.time() - start_time
    print(f"Hash Join took: {hash_duration:.4f} seconds (found {len(results_hash)} rows)")
    
    # Temporarily force Nested Loop Join to compare
    orig_hash_join = db._hash_join
    db._hash_join = db._nested_loop_join
    
    start_time = time.time()
    results_nl = db.execute_query(query)
    nl_duration = time.time() - start_time
    print(f"Nested Loop Join took: {nl_duration:.4f} seconds (found {len(results_nl)} rows)")
    
    # Verify results are same
    if len(results_hash) == len(results_nl):
        print("[v] Success: Both algorithms returned the same number of rows.")
    else:
        print(f"[x] Error: Row count mismatch! Hash: {len(results_hash)}, NL: {len(results_nl)}")

    # Summary
    speedup = nl_duration / hash_duration if hash_duration > 0 else float('inf')
    print(f"\nSpeedup: {speedup:.2f}x faster with Hash Join!")

    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    run_benchmark()
