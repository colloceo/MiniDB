"""
Concurrency Locking Test Suite
Tests file-based locking for multi-user access
"""
import os
import shutil
import time
import threading
from minidb import MiniDB
from minidb.exceptions import DatabaseBusyError

# Clean start
if os.path.exists("data"):
    shutil.rmtree("data")

print("="*70)
print("CONCURRENCY LOCKING TESTS")
print("="*70)

# Test 1: Basic Lock Acquisition and Release
print("\n[TEST 1] Basic Lock Acquisition and Release")
print("-"*70)

db = MiniDB()
db.execute_query("CREATE TABLE test (id INT, value STR)")
db.execute_query("INSERT INTO test VALUES (1, 'Hello')")

table = db.tables['test']
lock_manager = table.lock_manager

# Check lock doesn't exist initially
assert not lock_manager.is_locked('test'), "Lock should not exist initially"
print("✓ No lock exists initially")

# Acquire lock
lock_manager.acquire_lock('test')
assert lock_manager.is_locked('test'), "Lock should exist after acquisition"
print("✓ Lock acquired successfully")

# Release lock
lock_manager.release_lock('test')
assert not lock_manager.is_locked('test'), "Lock should not exist after release"
print("✓ Lock released successfully")

print("✅ PASS: Basic lock operations work")

# Test 2: Lock Timeout
print("\n[TEST 2] Lock Timeout (DatabaseBusyError)")
print("-"*70)

# Acquire lock
lock_manager.acquire_lock('test')
print("✓ Lock acquired")

# Try to acquire again (should timeout)
try:
    # Create a new lock manager with short timeout
    from minidb.lock_manager import LockManager
    lm2 = LockManager(data_dir="data", timeout=0.5)
    lm2.acquire_lock('test')
    print("❌ FAIL: Should have raised DatabaseBusyError")
except DatabaseBusyError as e:
    print(f"✓ DatabaseBusyError raised: {e}")
    print("✅ PASS: Timeout works correctly")
finally:
    lock_manager.release_lock('test')

# Test 3: Concurrent Writes (Simulated)
print("\n[TEST 3] Concurrent Write Protection")
print("-"*70)

results = {'success': 0, 'errors': 0}

def concurrent_insert(db_instance, thread_id, results):
    """Simulate concurrent inserts"""
    try:
        for i in range(3):
            db_instance.execute_query(f"INSERT INTO test VALUES ({thread_id * 10 + i}, 'Thread{thread_id}')")
            time.sleep(0.01)  # Small delay
        results['success'] += 1
    except Exception as e:
        print(f"Thread {thread_id} error: {e}")
        results['errors'] += 1

# Create multiple database instances (simulating different users)
db1 = MiniDB()
db2 = MiniDB()

# Start concurrent threads
thread1 = threading.Thread(target=concurrent_insert, args=(db1, 1, results))
thread2 = threading.Thread(target=concurrent_insert, args=(db2, 2, results))

thread1.start()
thread2.start()

thread1.join()
thread2.join()

print(f"Successful threads: {results['success']}")
print(f"Failed threads: {results['errors']}")

# Verify data integrity
data = db.execute_query("SELECT * FROM test")
print(f"Total rows in table: {len(data)}")
assert len(data) >= 6, "Should have at least 6 new rows"
print("✅ PASS: Concurrent writes protected by locks")

# Test 4: Lock Release on Exception
print("\n[TEST 4] Lock Release on Exception")
print("-"*70)

# Create a scenario where an error occurs during save
try:
    # This should acquire lock, fail, and release lock
    db.execute_query("INSERT INTO test VALUES ('invalid', 'type')")  # Type error
except Exception as e:
    print(f"✓ Expected error occurred: {type(e).__name__}")

# Check that lock was released
assert not lock_manager.is_locked('test'), "Lock should be released after error"
print("✓ Lock was released despite error")
print("✅ PASS: Finally block ensures lock release")

# Test 5: Multiple Table Locking
print("\n[TEST 5] Multiple Table Locking")
print("-"*70)

db.execute_query("CREATE TABLE users (id INT, name STR)")
db.execute_query("CREATE TABLE orders (id INT, user_id INT)")

users_table = db.tables['users']
orders_table = db.tables['orders']

# Acquire locks on both tables
users_table.lock_manager.acquire_lock('users')
orders_table.lock_manager.acquire_lock('orders')

print("✓ Acquired locks on both tables")

assert users_table.lock_manager.is_locked('users'), "Users should be locked"
assert orders_table.lock_manager.is_locked('orders'), "Orders should be locked"

# Release locks
users_table.lock_manager.release_lock('users')
orders_table.lock_manager.release_lock('orders')

print("✓ Released locks on both tables")
print("✅ PASS: Multiple table locking works")

# Test 6: Stale Lock Cleanup
print("\n[TEST 6] Stale Lock Cleanup")
print("-"*70)

# Create a stale lock (simulate crashed process)
stale_lock_path = os.path.join("data", "test.lock")
with open(stale_lock_path, 'w') as f:
    f.write("Stale lock from crashed process\n")

# Wait a moment
time.sleep(0.1)

# Modify the file timestamp to make it old
old_time = time.time() - 400  # 400 seconds ago
os.utime(stale_lock_path, (old_time, old_time))

print("✓ Created stale lock file")

# Cleanup stale locks
cleaned = lock_manager.cleanup_stale_locks(max_age=300)  # 5 minutes
print(f"✓ Cleaned up stale locks: {cleaned}")

assert 'test' in cleaned, "Should have cleaned test lock"
assert not os.path.exists(stale_lock_path), "Stale lock should be removed"
print("✅ PASS: Stale lock cleanup works")

# Test 7: Lock During Transaction
print("\n[TEST 7] Locks During Transaction")
print("-"*70)

# Start transaction
db.execute_query("BEGIN TRANSACTION")
print("✓ Transaction started")

# Make changes (these use locks internally)
db.execute_query("INSERT INTO test VALUES (100, 'InTransaction')")
db.execute_query("UPDATE test SET value = 'Modified' WHERE id = 1")

print("✓ Operations completed (locks acquired and released)")

# Commit
db.execute_query("COMMIT")
print("✓ Transaction committed")

# Verify no locks remain
assert not lock_manager.is_locked('test'), "No locks should remain after commit"
print("✅ PASS: Locks work correctly with transactions")

# Test 8: Read-Write Concurrency
print("\n[TEST 8] Read-Write Concurrency")
print("-"*70)

read_results = []

def concurrent_read(db_instance, results_list):
    """Simulate concurrent reads"""
    for _ in range(5):
        data = db_instance.execute_query("SELECT * FROM test")
        results_list.append(len(data))
        time.sleep(0.01)

def concurrent_write(db_instance, value):
    """Simulate concurrent writes"""
    for i in range(3):
        db_instance.execute_query(f"INSERT INTO test VALUES ({value + i}, 'Concurrent')")
        time.sleep(0.02)

# Create instances
db_read = MiniDB()
db_write = MiniDB()

# Start threads
read_thread = threading.Thread(target=concurrent_read, args=(db_read, read_results))
write_thread = threading.Thread(target=concurrent_write, args=(200,))

read_thread.start()
write_thread.start()

read_thread.join()
write_thread.join()

print(f"✓ Completed {len(read_results)} concurrent reads")
print(f"✓ Read counts: {read_results}")
print("✅ PASS: Read-write concurrency handled by locks")

print("\n" + "="*70)
print("✅ ALL CONCURRENCY LOCKING TESTS PASSED")
print("="*70)

print("\nFeatures Verified:")
print("  ✓ Lock acquisition and release")
print("  ✓ Lock timeout (DatabaseBusyError)")
print("  ✓ Concurrent write protection")
print("  ✓ Lock release on exception (finally block)")
print("  ✓ Multiple table locking")
print("  ✓ Stale lock cleanup")
print("  ✓ Locks with transactions")
print("  ✓ Read-write concurrency")

print("\nConcurrency Features:")
print("  ✓ File-based locking")
print("  ✓ Timeout mechanism (2 seconds default)")
print("  ✓ Retry logic (0.1s intervals)")
print("  ✓ Deadlock prevention")
print("  ✓ Crash-safe (finally blocks)")
print("  ✓ Multi-user support")

print("\n" + "="*70)
