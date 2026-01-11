"""
Transaction Management Demo
Interactive demonstration of BEGIN, COMMIT, and ROLLBACK
"""
from minidb import MiniDB
import os
import shutil

# Clean start
if os.path.exists("data"):
    shutil.rmtree("data")

print("\n" + "="*70)
print("MINIDB TRANSACTION MANAGEMENT DEMONSTRATION")
print("="*70)

db = MiniDB()

# Setup: Create banking tables
print("\n📋 Step 1: Setting up Banking Database")
print("-"*70)
db.execute_query("CREATE TABLE accounts (id INT, name STR, balance INT)")
db.execute_query("CREATE TABLE transactions (id INT, from_account INT, to_account INT, amount INT)")
print("[v] Created tables: accounts, transactions")

# Insert initial data
db.execute_query("INSERT INTO accounts VALUES (1, 'Alice', 1000)")
db.execute_query("INSERT INTO accounts VALUES (2, 'Bob', 500)")
db.execute_query("INSERT INTO accounts VALUES (3, 'Charlie', 750)")
print("[v] Inserted initial account data")

accounts = db.execute_query("SELECT * FROM accounts")
print("\nInitial Balances:")
for acc in accounts:
    print(f"  {acc['name']}: ${acc['balance']}")

# Demo 1: Successful Money Transfer with COMMIT
print("\n📋 Step 2: Money Transfer (Alice → Bob: $200)")
print("-"*70)

print("Starting transaction...")
result = db.execute_query("BEGIN TRANSACTION")
print(f"  {result}")

print("\nTransferring $200 from Alice to Bob...")
db.execute_query("UPDATE accounts SET balance = 800 WHERE id = 1")  # Alice -200
db.execute_query("UPDATE accounts SET balance = 700 WHERE id = 2")  # Bob +200
db.execute_query("INSERT INTO transactions VALUES (1, 1, 2, 200)")
print("  [v] Changes staged in transaction")

print("\nBalances in transaction (before commit):")
accounts_in_tx = db.execute_query("SELECT * FROM accounts")
for acc in accounts_in_tx:
    print(f"  {acc['name']}: ${acc['balance']}")

print("\nCommitting transaction...")
commit_result = db.execute_query("COMMIT")
print(f"  {commit_result}")

print("\nBalances after commit:")
accounts_after = db.execute_query("SELECT * FROM accounts")
for acc in accounts_after:
    print(f"  {acc['name']}: ${acc['balance']}")

# Demo 2: Failed Transfer with ROLLBACK
print("\n📋 Step 3: Failed Transfer (Bob → Charlie: $1000) - ROLLBACK")
print("-"*70)

print("Starting transaction...")
db.execute_query("BEGIN")

print("\nAttempting to transfer $1000 from Bob to Charlie...")
print("  (Bob only has $700, but we'll try anyway)")
db.execute_query("UPDATE accounts SET balance = -300 WHERE id = 2")  # Bob -1000 (negative!)
db.execute_query("UPDATE accounts SET balance = 1750 WHERE id = 3")  # Charlie +1000
print("  [v] Changes staged")

print("\nBalances in transaction (invalid state):")
accounts_invalid = db.execute_query("SELECT * FROM accounts")
for acc in accounts_invalid:
    status = " ⚠️ NEGATIVE!" if acc['balance'] < 0 else ""
    print(f"  {acc['name']}: ${acc['balance']}{status}")

print("\n[FAIL] Detected invalid state! Rolling back transaction...")
rollback_result = db.execute_query("ROLLBACK")
print(f"  {rollback_result}")

print("\nBalances after rollback (restored):")
accounts_restored = db.execute_query("SELECT * FROM accounts")
for acc in accounts_restored:
    print(f"  {acc['name']}: ${acc['balance']}")

# Demo 3: Multi-step Transaction
print("\n📋 Step 4: Multi-step Transaction (Multiple Transfers)")
print("-"*70)

print("Starting transaction...")
db.execute_query("BEGIN TRANSACTION")

print("\nExecuting multiple transfers:")
print("  1. Alice → Charlie: $100")
db.execute_query("UPDATE accounts SET balance = 700 WHERE id = 1")
db.execute_query("UPDATE accounts SET balance = 800 WHERE id = 3")
db.execute_query("INSERT INTO transactions VALUES (2, 1, 3, 100)")

print("  2. Bob → Alice: $50")
db.execute_query("UPDATE accounts SET balance = 750 WHERE id = 1")
db.execute_query("UPDATE accounts SET balance = 650 WHERE id = 2")
db.execute_query("INSERT INTO transactions VALUES (3, 2, 1, 50)")

print("  3. Charlie → Bob: $75")
db.execute_query("UPDATE accounts SET balance = 725 WHERE id = 2")
db.execute_query("UPDATE accounts SET balance = 725 WHERE id = 3")
db.execute_query("INSERT INTO transactions VALUES (4, 3, 2, 75)")

print("\nBalances in transaction:")
accounts_multi = db.execute_query("SELECT * FROM accounts")
for acc in accounts_multi:
    print(f"  {acc['name']}: ${acc['balance']}")

print("\nCommitting all transfers...")
db.execute_query("COMMIT")

print("\nFinal balances:")
final_accounts = db.execute_query("SELECT * FROM accounts")
for acc in final_accounts:
    print(f"  {acc['name']}: ${acc['balance']}")

print("\nTransaction log:")
txs = db.execute_query("SELECT * FROM transactions")
for tx in txs:
    print(f"  TX #{tx['id']}: Account {tx['from_account']} → Account {tx['to_account']}: ${tx['amount']}")

# Demo 4: Auto-commit Mode
print("\n📋 Step 5: Auto-commit Mode (No Transaction)")
print("-"*70)

print("Direct INSERT without transaction...")
db.execute_query("INSERT INTO accounts VALUES (4, 'David', 1000)")
print("  [v] Immediately committed to disk")

print("\nDirect UPDATE without transaction...")
db.execute_query("UPDATE accounts SET balance = 1100 WHERE id = 4")
print("  [v] Immediately committed to disk")

accounts_final = db.execute_query("SELECT * FROM accounts")
print("\nAll accounts:")
for acc in accounts_final:
    print(f"  {acc['name']}: ${acc['balance']}")

# Summary
print("\n" + "="*70)
print("[PASS] TRANSACTION DEMONSTRATION COMPLETE")
print("="*70)

print("\nFeatures Demonstrated:")
print("  [v] BEGIN TRANSACTION - Start isolated transaction")
print("  [v] COMMIT - Save all changes atomically")
print("  [v] ROLLBACK - Discard invalid changes")
print("  [v] Multi-table transactions - Accounts + Transactions")
print("  [v] Multi-step transactions - Multiple operations")
print("  [v] Transaction isolation - Changes visible only in transaction")
print("  [v] Auto-commit mode - Direct operations without transaction")

print("\nUse Cases Shown:")
print("  [v] Money transfers (atomicity)")
print("  [v] Error recovery (rollback)")
print("  [v] Batch operations (multiple transfers)")
print("  [v] Data consistency (all or nothing)")

print("\n" + "="*70 + "\n")
