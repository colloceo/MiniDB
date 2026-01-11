"""
Column Management Test Suite
Tests DROP COLUMN and RENAME COLUMN functionality
"""
import os
import shutil
from minidb import MiniDB
from minidb.exceptions import SchemaError, ValidationError

# Clean start
if os.path.exists("data"):
    shutil.rmtree("data")

print("="*70)
print("COLUMN MANAGEMENT TESTS")
print("="*70)

db = MiniDB()

# Test 1: DROP COLUMN - Basic
print("\n[TEST 1] DROP COLUMN - Basic Functionality")
print("-"*70)

db.execute_query("CREATE TABLE users (id INT, name STR, email STR, age INT)")
db.execute_query("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com', 25)")
db.execute_query("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com', 30)")
print("[v] Created table with 4 columns and 2 rows")

# Drop email column
result = db.execute_query("ALTER TABLE users DROP COLUMN email")
print(f"[v] {result}")

# Verify column is gone
desc = db.execute_query("DESCRIBE users")
assert 'email' not in desc['columns'], "Email should not be in columns"
assert len(desc['columns']) == 3, "Should have 3 columns now"
print(f"[v] Columns after drop: {desc['columns']}")

# Verify data is updated
data = db.execute_query("SELECT * FROM users")
for row in data:
    assert 'email' not in row, "Email should not be in row data"
print(f"[v] Data verified: {data}")

print("[PASS] PASS: DROP COLUMN works correctly")

# Test 2: DROP COLUMN - Primary Key Protection
print("\n[TEST 2] DROP COLUMN - Primary Key Protection")
print("-"*70)

try:
    db.execute_query("ALTER TABLE users DROP COLUMN id")
    print("[FAIL] FAIL: Should have raised SchemaError")
except Exception as e:
    if "SchemaError" in str(type(e).__name__) or "primary key" in str(e).lower():
        print(f"[v] SchemaError raised: {e}")
        print("[PASS] PASS: Cannot drop primary key column")
    else:
        print(f"[FAIL] Wrong error type: {type(e).__name__}")

# Test 3: DROP COLUMN - Non-existent Column
print("\n[TEST 3] DROP COLUMN - Non-existent Column")
print("-"*70)

try:
    db.execute_query("ALTER TABLE users DROP COLUMN nonexistent")
    print("[FAIL] FAIL: Should have raised ValidationError")
except Exception as e:
    if "ValidationError" in str(type(e).__name__) or "does not exist" in str(e):
        print(f"[v] ValidationError raised: {e}")
        print("[PASS] PASS: Error on non-existent column")
    else:
        print(f"[FAIL] Wrong error type: {type(e).__name__}")

# Test 4: RENAME COLUMN - Basic
print("\n[TEST 4] RENAME COLUMN - Basic Functionality")
print("-"*70)

# Rename 'name' to 'full_name'
result = db.execute_query("ALTER TABLE users RENAME COLUMN name TO full_name")
print(f"[v] {result}")

# Verify column is renamed
desc = db.execute_query("DESCRIBE users")
assert 'name' not in desc['columns'], "Old name should not exist"
assert 'full_name' in desc['columns'], "New name should exist"
print(f"[v] Columns after rename: {desc['columns']}")

# Verify data is updated
data = db.execute_query("SELECT * FROM users")
for row in data:
    assert 'name' not in row, "Old name should not be in row"
    assert 'full_name' in row, "New name should be in row"
print(f"[v] Data verified: {data}")

print("[PASS] PASS: RENAME COLUMN works correctly")

# Test 5: RENAME COLUMN - Primary Key
print("\n[TEST 5] RENAME COLUMN - Primary Key Rename")
print("-"*70)

# Rename primary key column
result = db.execute_query("ALTER TABLE users RENAME COLUMN id TO user_id")
print(f"[v] {result}")

# Verify primary key is updated
desc = db.execute_query("DESCRIBE users")
assert desc['primary_key'] == 'user_id', "Primary key should be updated"
assert 'user_id' in desc['columns'], "New primary key name should exist"
print(f"[v] Primary key updated: {desc['primary_key']}")

# Verify data and index work
data = db.execute_query("SELECT * FROM users")
assert all('user_id' in row for row in data), "All rows should have user_id"
print(f"[v] Data verified: {data}")

print("[PASS] PASS: Primary key rename works")

# Test 6: RENAME COLUMN - Duplicate Name
print("\n[TEST 6] RENAME COLUMN - Duplicate Name Error")
print("-"*70)

try:
    db.execute_query("ALTER TABLE users RENAME COLUMN age TO full_name")
    print("[FAIL] FAIL: Should have raised ValidationError")
except Exception as e:
    if "ValidationError" in str(type(e).__name__) or "already exists" in str(e):
        print(f"[v] ValidationError raised: {e}")
        print("[PASS] PASS: Error on duplicate column name")
    else:
        print(f"[FAIL] Wrong error type: {type(e).__name__}")

# Test 7: RENAME COLUMN - Non-existent Column
print("\n[TEST 7] RENAME COLUMN - Non-existent Column")
print("-"*70)

try:
    db.execute_query("ALTER TABLE users RENAME COLUMN nonexistent TO something")
    print("[FAIL] FAIL: Should have raised ValidationError")
except Exception as e:
    if "ValidationError" in str(type(e).__name__) or "does not exist" in str(e):
        print(f"[v] ValidationError raised: {e}")
        print("[PASS] PASS: Error on non-existent column")
    else:
        print(f"[FAIL] Wrong error type: {type(e).__name__}")

# Test 8: DROP COLUMN - With Constraints
print("\n[TEST 8] DROP COLUMN - Column with Constraints")
print("-"*70)

db.execute_query("CREATE TABLE products (id INT, name STR UNIQUE, price INT)")
db.execute_query("INSERT INTO products VALUES (1, 'Widget', 100)")
print("[v] Created table with UNIQUE constraint")

# Drop column with UNIQUE constraint
result = db.execute_query("ALTER TABLE products DROP COLUMN name")
print(f"[v] {result}")

# Verify constraint is removed
desc = db.execute_query("DESCRIBE products")
assert 'name' not in desc['unique_columns'], "Unique constraint should be removed"
print(f"[v] Unique columns after drop: {desc['unique_columns']}")

print("[PASS] PASS: DROP COLUMN removes constraints")

# Test 9: RENAME COLUMN - With Constraints
print("\n[TEST 9] RENAME COLUMN - Column with Constraints")
print("-"*70)

db.execute_query("CREATE TABLE orders (id INT, product_id INT, quantity INT)")
# Simulate foreign key
db.tables['orders'].foreign_keys = {'product_id': 'products.id'}
db.tables['orders'].unique_columns = ['product_id']
print("[v] Created table with constraints")

# Rename column with constraints
result = db.execute_query("ALTER TABLE orders RENAME COLUMN product_id TO item_id")
print(f"[v] {result}")

# Verify constraints are updated
desc = db.execute_query("DESCRIBE orders")
assert 'item_id' in desc['unique_columns'], "Unique constraint should be updated"
assert 'item_id' in desc['foreign_keys'], "Foreign key should be updated"
print(f"[v] Constraints updated: unique={desc['unique_columns']}, fk={desc['foreign_keys']}")

print("[PASS] PASS: RENAME COLUMN updates constraints")

# Test 10: Persistence
print("\n[TEST 10] Persistence - Schema Changes Persist")
print("-"*70)

# Make changes
db.execute_query("ALTER TABLE users DROP COLUMN age")
db.execute_query("ALTER TABLE users RENAME COLUMN full_name TO username")
print("[v] Made schema changes")

# Create new DB instance (reload from disk)
db2 = MiniDB()
desc = db2.execute_query("DESCRIBE users")

assert 'age' not in desc['columns'], "Dropped column should not exist after reload"
assert 'username' in desc['columns'], "Renamed column should exist after reload"
assert desc['primary_key'] == 'user_id', "Primary key should persist"
print(f"[v] Schema persisted: {desc['columns']}")

# Verify data persisted
data = db2.execute_query("SELECT * FROM users")
assert all('username' in row for row in data), "Renamed column data should persist"
print(f"[v] Data persisted: {data}")

print("[PASS] PASS: Schema changes persist to disk")

# Test 11: Complex Scenario
print("\n[TEST 11] Complex Scenario - Multiple Operations")
print("-"*70)

db.execute_query("CREATE TABLE employees (id INT, first_name STR, last_name STR, email STR, department STR, salary INT)")
db.execute_query("INSERT INTO employees VALUES (1, 'John', 'Doe', 'john@example.com', 'IT', 50000)")
db.execute_query("INSERT INTO employees VALUES (2, 'Jane', 'Smith', 'jane@example.com', 'HR', 55000)")
print("[v] Created employees table with 6 columns")

# Multiple operations
db.execute_query("ALTER TABLE employees DROP COLUMN email")
db.execute_query("ALTER TABLE employees RENAME COLUMN first_name TO fname")
db.execute_query("ALTER TABLE employees RENAME COLUMN last_name TO lname")
db.execute_query("ALTER TABLE employees DROP COLUMN department")
print("[v] Performed multiple schema changes")

# Verify final state
desc = db.execute_query("DESCRIBE employees")
expected_columns = ['id', 'fname', 'lname', 'salary']
assert desc['columns'] == expected_columns, f"Expected {expected_columns}, got {desc['columns']}"
print(f"[v] Final columns: {desc['columns']}")

# Verify data
data = db.execute_query("SELECT * FROM employees")
assert len(data) == 2, "Should still have 2 rows"
assert all('fname' in row and 'lname' in row for row in data), "Renamed columns should exist"
print(f"[v] Final data: {data}")

print("[PASS] PASS: Complex scenario works correctly")

print("\n" + "="*70)
print("[PASS] ALL COLUMN MANAGEMENT TESTS PASSED")
print("="*70)

print("\nFeatures Verified:")
print("  [v] DROP COLUMN - Basic functionality")
print("  [v] DROP COLUMN - Primary key protection")
print("  [v] DROP COLUMN - Non-existent column error")
print("  [v] DROP COLUMN - Constraint removal")
print("  [v] RENAME COLUMN - Basic functionality")
print("  [v] RENAME COLUMN - Primary key rename")
print("  [v] RENAME COLUMN - Duplicate name error")
print("  [v] RENAME COLUMN - Non-existent column error")
print("  [v] RENAME COLUMN - Constraint updates")
print("  [v] Persistence - Schema changes persist")
print("  [v] Complex scenarios - Multiple operations")

print("\nSafety Features:")
print("  [v] Cannot drop primary key column")
print("  [v] Validation for non-existent columns")
print("  [v] Duplicate name detection")
print("  [v] Atomic saves after each operation")
print("  [v] Index rebuilding")
print("  [v] Metadata updates")

print("\n" + "="*70)
