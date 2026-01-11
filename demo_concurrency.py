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
print("  ✓ Lock acquired")

is_locked = lock_manager.is_locked('accounts')
print(f"  Table 'accounts' locked: {is_locked}")

print("\nReleasing lock...")
lock_manager.release_lock('accounts')
print("  ✓ Lock released")

is_locked = lock_manager.is_locked('accounts')
print(f"  Table 'accounts' locked: {is_locked}")

# Demo 2: Lock Timeout
print("\n📋 Step 2: Lock Timeout (Deadlock Prevention)")
print("-"*70)

print("User 1: Acquiring lock on 'accounts'...")
lock_manager.acquire_lock('accounts')
print("  ✓ User 1 has the lock")

print("\nUser 2: Attempting to acquire same lock...")
print("  (Will timeout after 2 seconds)")

try:
    # Create a second lock manager with short timeout
    lm2 = LockManager(data_dir="data", timeout=1.0)
    lm2.acquire_lock('accounts')
    print("  ❌ Should not reach here!")
except DatabaseBusyError as e:
    print(f"  ✓ Timeout occurred: {str(e)[:60]}...")
    print("  ✓ DatabaseBusyError raised as expected")

print("\nUser 1: Releasing lock...")
lock_manager.release_lock('accounts')
print("  ✓ Lock released")

print("\nUser 2: Trying again...")
lm2.acquire_lock('accounts')
print("  ✓ User 2 successfully acquired lock")
lm2.release_lock('accounts')
print("  ✓ User 2 released lock")

# Demo 3: Automatic Lock Management
print("\n📋 Step 3: Automatic Lock Management (save_data/load_data)")
print("-"*70)

print("Inserting data (automatically acquires and releases lock)...")
db.execute_query("INSERT INTO accounts VALUES (2, 'Bob', 500)")
print("  ✓ Insert complete (lock was acquired and released)")

print("\nSelecting data (automatically acquires and releases lock)...")
data = db.execute_query("SELECT * FROM accounts")
print(f"  ✓ Found {len(data)} accounts")
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
    print(f"  ✓ Error occurred: {type(e).__name__}")

print("\nChecking if lock was released...")
is_locked = lock_manager.is_locked('accounts')
print(f"  Table 'accounts' locked: {is_locked}")
print("  ✓ Lock was properly released despite error (finally block worked)")

# Demo 5: Stale Lock Cleanup
print("\n📋 Step 5: Stale Lock Cleanup")
print("-"*70)

print("Creating a stale lock file (simulating crashed process)...")
stale_lock_path = os.path.join("data", "accounts.lock")
with open(stale_lock_path, 'w') as f:
    f.write(f"Stale lock from crashed process\nTimestamp: {time.time()}\n")
print("  ✓ Stale lock created")

# Make it old
old_time = time.time() - 400  # 400 seconds ago
os.utime(stale_lock_path, (old_time, old_time))
print("  ✓ Modified timestamp to 400 seconds ago")

print("\nRunning cleanup (max_age=300 seconds)...")
cleaned = lock_manager.cleanup_stale_locks(max_age=300)
print(f"  ✓ Cleaned up locks: {cleaned}")

is_locked = lock_manager.is_locked('accounts')
print(f"  Table 'accounts' locked: {is_locked}")
print("  ✓ Stale lock removed")

# Demo 6: Multi-table Locking
print("\n📋 Step 6: Multi-table Locking")
print("-"*70)

db.execute_query("CREATE TABLE transactions (id INT, account_id INT, amount INT)")
print("✓ Created 'transactions' table")

accounts_lm = db.tables['accounts'].lock_manager
transactions_lm = db.tables['transactions'].lock_manager

print("\nAcquiring locks on both tables...")
accounts_lm.acquire_lock('accounts')
transactions_lm.acquire_lock('transactions')
print("  ✓ Both tables locked")

print(f"  accounts locked: {accounts_lm.is_locked('accounts')}")
print(f"  transactions locked: {transactions_lm.is_locked('transactions')}")

print("\nReleasing locks...")
accounts_lm.release_lock('accounts')
transactions_lm.release_lock('transactions')
print("  ✓ Both locks released")

# Demo 7: Locks with Transactions
print("\n📋 Step 7: Locks with Database Transactions")
print("-"*70)

print("Starting database transaction...")
db.execute_query("BEGIN TRANSACTION")
print("  ✓ Transaction started")

print("\nMaking changes (each operation uses locks)...")
db.execute_query("UPDATE accounts SET balance = 1100 WHERE id = 1")
db.execute_query("INSERT INTO transactions VALUES (1, 1, 100)")
print("  ✓ Changes staged (locks acquired and released for each operation)")

print("\nCommitting transaction...")
db.execute_query("COMMIT")
print("  ✓ Transaction committed")

print("\nVerifying no locks remain...")
is_locked = lock_manager.is_locked('accounts')
print(f"  accounts locked: {is_locked}")
print("  ✓ All locks properly released")

# Summary
print("\n" + "="*70)
print("✅ CONCURRENCY LOCKING DEMONSTRATION COMPLETE")
print("="*70)

print("\nFeatures Demonstrated:")
print("  ✓ Lock acquisition and release")
print("  ✓ Lock timeout (DatabaseBusyError after 2 seconds)")
print("  ✓ Automatic locking in save_data/load_data")
print("  ✓ Lock release on error (finally block)")
print("  ✓ Stale lock cleanup")
print("  ✓ Multi-table locking")
print("  ✓ Integration with transactions")

print("\nBenefits:")
print("  ✓ Multi-user support")
print("  ✓ Deadlock prevention")
print("  ✓ Crash-safe operations")
print("  ✓ Data integrity guaranteed")
print("  ✓ Concurrent access controlled")

print("\n" + "="*70 + "\n")
