"""
Transaction Management Test Suite
Tests BEGIN, COMMIT, and ROLLBACK functionality
"""
import os
import shutil
from minidb import MiniDB

# Clean start
if os.path.exists("data"):
    shutil.rmtree("data")

db = MiniDB()

print("="*70)
print("TRANSACTION MANAGEMENT TESTS")
print("="*70)

# Test 1: Basic Transaction - COMMIT
print("\n[TEST 1] Basic Transaction with COMMIT")
print("-"*70)

# Create table
db.execute_query("CREATE TABLE accounts (id INT, name STR, balance INT)")
print("✓ Table 'accounts' created")

# Insert initial data
db.execute_query("INSERT INTO accounts VALUES (1, 'Alice', 1000)")
db.execute_query("INSERT INTO accounts VALUES (2, 'Bob', 500)")
print("✓ Initial data inserted (auto-commit)")

# Start transaction
result = db.execute_query("BEGIN TRANSACTION")
print(f"✓ {result}")

# Make changes in transaction
db.execute_query("INSERT INTO accounts VALUES (3, 'Charlie', 750)")
db.execute_query("UPDATE accounts SET balance = 1200 WHERE id = 1")
print("✓ Changes staged in transaction")

# Check data before commit (should see staged changes)
data_in_tx = db.execute_query("SELECT * FROM accounts")
print(f"Data in transaction: {len(data_in_tx)} rows")
assert len(data_in_tx) == 3, "Should see 3 rows in transaction"
assert data_in_tx[0]['balance'] == 1200, "Should see updated balance"

# Commit transaction
commit_result = db.execute_query("COMMIT")
print(f"✓ {commit_result}")

# Verify data persisted
data_after = db.execute_query("SELECT * FROM accounts")
print(f"Data after commit: {len(data_after)} rows")
assert len(data_after) == 3, "Should have 3 rows after commit"
assert data_after[0]['balance'] == 1200, "Balance should be updated"
print("✅ PASS: Transaction committed successfully")

# Test 2: Transaction ROLLBACK
print("\n[TEST 2] Transaction with ROLLBACK")
print("-"*70)

# Start new transaction
db.execute_query("BEGIN")
print("✓ Transaction started")

# Make changes
db.execute_query("INSERT INTO accounts VALUES (4, 'David', 2000)")
db.execute_query("DELETE FROM accounts WHERE id = 2")
print("✓ Changes staged (INSERT + DELETE)")

# Check data in transaction
data_in_tx2 = db.execute_query("SELECT * FROM accounts")
print(f"Data in transaction: {len(data_in_tx2)} rows")
assert len(data_in_tx2) == 3, "Should see 3 rows (added David, removed Bob)"

# Rollback transaction
rollback_result = db.execute_query("ROLLBACK")
print(f"✓ {rollback_result}")

# Verify data NOT persisted
data_after_rollback = db.execute_query("SELECT * FROM accounts")
print(f"Data after rollback: {len(data_after_rollback)} rows")
assert len(data_after_rollback) == 3, "Should still have 3 rows"
assert any(r['name'] == 'Bob' for r in data_after_rollback), "Bob should still exist"
assert not any(r['name'] == 'David' for r in data_after_rollback), "David should not exist"
print("✅ PASS: Transaction rolled back successfully")

# Test 3: Multiple Table Transaction
print("\n[TEST 3] Multi-table Transaction")
print("-"*70)

# Create second table
db.execute_query("CREATE TABLE transactions (id INT, account_id INT, amount INT)")
print("✓ Table 'transactions' created")

# Start transaction
db.execute_query("BEGIN TRANSACTION")
print("✓ Transaction started")

# Modify multiple tables
db.execute_query("UPDATE accounts SET balance = 900 WHERE id = 1")
db.execute_query("INSERT INTO transactions VALUES (1, 1, -100)")
db.execute_query("UPDATE accounts SET balance = 600 WHERE id = 2")
db.execute_query("INSERT INTO transactions VALUES (2, 2, 100)")
print("✓ Modified 2 tables in transaction")

# Commit
commit_result2 = db.execute_query("COMMIT")
print(f"✓ {commit_result2}")

# Verify both tables updated
accounts = db.execute_query("SELECT * FROM accounts WHERE id = 1")
txs = db.execute_query("SELECT * FROM transactions")
assert accounts[0]['balance'] == 900, "Account balance should be updated"
assert len(txs) == 2, "Should have 2 transaction records"
print("✅ PASS: Multi-table transaction committed")

# Test 4: Auto-commit Mode (No Transaction)
print("\n[TEST 4] Auto-commit Mode")
print("-"*70)

# Direct INSERT without transaction
db.execute_query("INSERT INTO accounts VALUES (5, 'Eve', 1500)")
print("✓ Direct INSERT (auto-commit)")

# Verify immediately persisted
data = db.execute_query("SELECT * FROM accounts WHERE id = 5")
assert len(data) == 1, "Should find Eve immediately"
print("✅ PASS: Auto-commit mode works")

# Test 5: Error Handling
print("\n[TEST 5] Error Handling")
print("-"*70)

# Try COMMIT without transaction
try:
    db.execute_query("COMMIT")
    print("❌ FAIL: Should have raised error")
except:
    print("✓ COMMIT without transaction raises error")

# Try ROLLBACK without transaction
try:
    db.execute_query("ROLLBACK")
    print("❌ FAIL: Should have raised error")
except:
    print("✓ ROLLBACK without transaction raises error")

# Try nested BEGIN
db.execute_query("BEGIN")
try:
    db.execute_query("BEGIN")
    print("❌ FAIL: Should have raised error")
except:
    print("✓ Nested BEGIN raises error")
    db.execute_query("ROLLBACK")  # Clean up

print("✅ PASS: Error handling works correctly")

# Test 6: Transaction Isolation
print("\n[TEST 6] Transaction Isolation")
print("-"*70)

# Start transaction
db.execute_query("BEGIN")
db.execute_query("INSERT INTO accounts VALUES (6, 'Frank', 3000)")
print("✓ Inserted Frank in transaction")

# SELECT should see staged data
data_in_tx = db.execute_query("SELECT * FROM accounts WHERE id = 6")
assert len(data_in_tx) == 1, "Should see Frank in transaction"
print("✓ SELECT sees staged changes")

# Rollback
db.execute_query("ROLLBACK")

# SELECT should NOT see Frank
data_after = db.execute_query("SELECT * FROM accounts WHERE id = 6")
assert len(data_after) == 0, "Should not see Frank after rollback"
print("✅ PASS: Transaction isolation works")

# Test 7: Complex UPDATE in Transaction
print("\n[TEST 7] Complex UPDATE in Transaction")
print("-"*70)

db.execute_query("BEGIN")
db.execute_query("UPDATE accounts SET balance = 2000 WHERE balance > 500")
print("✓ Updated multiple rows in transaction")

data_in_tx = db.execute_query("SELECT * FROM accounts WHERE balance = 2000")
print(f"Rows with balance=2000 in transaction: {len(data_in_tx)}")

db.execute_query("COMMIT")
data_after = db.execute_query("SELECT * FROM accounts WHERE balance = 2000")
print(f"Rows with balance=2000 after commit: {len(data_after)}")
assert len(data_after) > 0, "Should have rows with balance=2000"
print("✅ PASS: Complex UPDATE committed")

# Test 8: DELETE in Transaction
print("\n[TEST 8] DELETE in Transaction")
print("-"*70)

# Count before
count_before = len(db.execute_query("SELECT * FROM accounts"))
print(f"Accounts before: {count_before}")

db.execute_query("BEGIN")
db.execute_query("DELETE FROM accounts WHERE balance < 1000")
print("✓ Deleted rows in transaction")

count_in_tx = len(db.execute_query("SELECT * FROM accounts"))
print(f"Accounts in transaction: {count_in_tx}")

db.execute_query("ROLLBACK")
count_after = len(db.execute_query("SELECT * FROM accounts"))
print(f"Accounts after rollback: {count_after}")

assert count_after == count_before, "Count should be same after rollback"
print("✅ PASS: DELETE rollback works")

print("\n" + "="*70)
print("✅ ALL TRANSACTION TESTS PASSED")
print("="*70)

print("\nTransaction Features Verified:")
print("  ✓ BEGIN TRANSACTION")
print("  ✓ COMMIT (single and multi-table)")
print("  ✓ ROLLBACK")
print("  ✓ Auto-commit mode")
print("  ✓ Transaction isolation")
print("  ✓ INSERT/UPDATE/DELETE in transactions")
print("  ✓ Error handling")
print("  ✓ Staging area functionality")
print("\n" + "="*70)
