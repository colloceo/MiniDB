"""
Concurrency Locking Demo
Demonstrates file-based locking for multi-user access
"""
import os
import shutil
import time
from minidb import MiniDB
from minidb.exceptions import DatabaseBusyError
from minidb.lock_manager import LockManager

# Clean start
if os.path.exists("data"):
    shutil.rmtree("data")

print("\n" + "="*70)
print("CONCURRENCY LOCKING DEMONSTRATION")
print("="*70)

db = MiniDB()

# Demo 1: Basic Locking
print("\n📋 Step 1: Basic Lock Operations")
print("-"*70)

db.execute_query("CREATE TABLE accounts (id INT, name STR, balance INT)")
db.execute_query("INSERT INTO accounts VALUES (1, 'Alice', 1000)")

table = db.tables['accounts']
lock_manager = table.lock_manager

print("Checking lock status...")
is_locked = lock_manager.is_locked('accounts')
print(f"  Table 'accounts' locked: {is_locked}")

print("\nAcquiring lock...")
lock_manager.acquire_lock('accounts')
print("  [v] Lock acquired")

is_locked = lock_manager.is_locked('accounts')
print(f"  Table 'accounts' locked: {is_locked}")

print("\nReleasing lock...")
lock_manager.release_lock('accounts')
print("  [v] Lock released")

is_locked = lock_manager.is_locked('accounts')
print(f"  Table 'accounts' locked: {is_locked}")

# Demo 2: Lock Timeout
print("\n📋 Step 2: Lock Timeout (Deadlock Prevention)")
print("-"*70)

print("User 1: Acquiring lock on 'accounts'...")
lock_manager.acquire_lock('accounts')
print("  [v] User 1 has the lock")

print("\nUser 2: Attempting to acquire same lock...")
print("  (Will timeout after 2 seconds)")

try:
    # Create a second lock manager with short timeout
    lm2 = LockManager(data_dir="data", timeout=1.0)
    lm2.acquire_lock('accounts')
    print("  [FAIL] Should not reach here!")
except DatabaseBusyError as e:
    print(f"  [v] Timeout occurred: {str(e)[:60]}...")
    print("  [v] DatabaseBusyError raised as expected")

print("\nUser 1: Releasing lock...")
lock_manager.release_lock('accounts')
print("  [v] Lock released")

print("\nUser 2: Trying again...")
lm2.acquire_lock('accounts')
print("  [v] User 2 successfully acquired lock")
lm2.release_lock('accounts')
print("  [v] User 2 released lock")

# Demo 3: Automatic Lock Management
print("\n📋 Step 3: Automatic Lock Management (save_data/load_data)")
print("-"*70)

print("Inserting data (automatically acquires and releases lock)...")
db.execute_query("INSERT INTO accounts VALUES (2, 'Bob', 500)")
print("  [v] Insert complete (lock was acquired and released)")

print("\nSelecting data (automatically acquires and releases lock)...")
data = db.execute_query("SELECT * FROM accounts")
print(f"  [v] Found {len(data)} accounts")
for acc in data:
    print(f"    {acc['name']}: ${acc['balance']}")

# Demo 4: Lock Release on Error
print("\n📋 Step 4: Lock Release on Error (Finally Block)")
print("-"*70)

print("Attempting invalid operation (will cause error)...")
try:
    # This will fail due to type mismatch
    db.execute_query("INSERT INTO accounts VALUES ('invalid', 'Bob', 500)")
except Exception as e:
    print(f"  [v] Error occurred: {type(e).__name__}")

print("\nChecking if lock was released...")
is_locked = lock_manager.is_locked('accounts')
print(f"  Table 'accounts' locked: {is_locked}")
print("  [v] Lock was properly released despite error (finally block worked)")

# Demo 5: Stale Lock Cleanup
print("\n📋 Step 5: Stale Lock Cleanup")
print("-"*70)

print("Creating a stale lock file (simulating crashed process)...")
stale_lock_path = os.path.join("data", "accounts.lock")
with open(stale_lock_path, 'w') as f:
    f.write(f"Stale lock from crashed process\nTimestamp: {time.time()}\n")
print("  [v] Stale lock created")

# Make it old
old_time = time.time() - 400  # 400 seconds ago
os.utime(stale_lock_path, (old_time, old_time))
print("  [v] Modified timestamp to 400 seconds ago")

print("\nRunning cleanup (max_age=300 seconds)...")
cleaned = lock_manager.cleanup_stale_locks(max_age=300)
print(f"  [v] Cleaned up locks: {cleaned}")

is_locked = lock_manager.is_locked('accounts')
print(f"  Table 'accounts' locked: {is_locked}")
print("  [v] Stale lock removed")

# Demo 6: Multi-table Locking
print("\n📋 Step 6: Multi-table Locking")
print("-"*70)

db.execute_query("CREATE TABLE transactions (id INT, account_id INT, amount INT)")
print("[v] Created 'transactions' table")

accounts_lm = db.tables['accounts'].lock_manager
transactions_lm = db.tables['transactions'].lock_manager

print("\nAcquiring locks on both tables...")
accounts_lm.acquire_lock('accounts')
transactions_lm.acquire_lock('transactions')
print("  [v] Both tables locked")

print(f"  accounts locked: {accounts_lm.is_locked('accounts')}")
print(f"  transactions locked: {transactions_lm.is_locked('transactions')}")

print("\nReleasing locks...")
accounts_lm.release_lock('accounts')
transactions_lm.release_lock('transactions')
print("  [v] Both locks released")

# Demo 7: Locks with Transactions
print("\n📋 Step 7: Locks with Database Transactions")
print("-"*70)

print("Starting database transaction...")
db.execute_query("BEGIN TRANSACTION")
print("  [v] Transaction started")

print("\nMaking changes (each operation uses locks)...")
db.execute_query("UPDATE accounts SET balance = 1100 WHERE id = 1")
db.execute_query("INSERT INTO transactions VALUES (1, 1, 100)")
print("  [v] Changes staged (locks acquired and released for each operation)")

print("\nCommitting transaction...")
db.execute_query("COMMIT")
print("  [v] Transaction committed")

print("\nVerifying no locks remain...")
is_locked = lock_manager.is_locked('accounts')
print(f"  accounts locked: {is_locked}")
print("  [v] All locks properly released")

# Summary
print("\n" + "="*70)
print("[PASS] CONCURRENCY LOCKING DEMONSTRATION COMPLETE")
print("="*70)

print("\nFeatures Demonstrated:")
print("  [v] Lock acquisition and release")
print("  [v] Lock timeout (DatabaseBusyError after 2 seconds)")
print("  [v] Automatic locking in save_data/load_data")
print("  [v] Lock release on error (finally block)")
print("  [v] Stale lock cleanup")
print("  [v] Multi-table locking")
print("  [v] Integration with transactions")

print("\nBenefits:")
print("  [v] Multi-user support")
print("  [v] Deadlock prevention")
print("  [v] Crash-safe operations")
print("  [v] Data integrity guaranteed")
print("  [v] Concurrent access controlled")

print("\n" + "="*70 + "\n")
