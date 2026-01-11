"""
Test ALTER TABLE ADD COLUMN functionality
"""
from minidb import MiniDB
import os
import shutil

# Clean slate
if os.path.exists("data"):
    shutil.rmtree("data")

db = MiniDB()

print("=" * 70)
print("ALTER TABLE ADD COLUMN - TEST")
print("=" * 70)

# Test 1: Create table and add data
print("\n[TEST 1] Creating table and inserting data")
print("-" * 70)

db.execute_query("CREATE TABLE users (id INT, name STR)")
db.execute_query("INSERT INTO users VALUES (1, 'Alice')")
db.execute_query("INSERT INTO users VALUES (2, 'Bob')")

print("Table created with columns: id, name")
print("Inserted 2 rows")

# Verify initial data
data = db.execute_query("SELECT * FROM users")
print("\nInitial data:")
for row in data:
    print(f"  {row}")

# Test 2: Add new column
print("\n[TEST 2] Adding new column 'email' (STR)")
print("-" * 70)

result = db.execute_query("ALTER TABLE users ADD email STR")
print(f"Result: {result}")

# Verify schema updated
desc = db.execute_query("DESCRIBE users")
print(f"\nUpdated schema:")
print(f"  Columns: {desc['columns']}")
print(f"  Column Types: {desc['column_types']}")

# Verify data updated with default values
data = db.execute_query("SELECT * FROM users")
print(f"\nData after adding column:")
for row in data:
    print(f"  {row}")

# Check default value
if all(row.get('email') == '' for row in data):
    print("[v] PASS: Default value (empty string) added to all rows")
else:
    print("[x] FAIL: Default value not correctly applied")

# Test 3: Add INT column
print("\n[TEST 3] Adding new column 'age' (INT)")
print("-" * 70)

result2 = db.execute_query("ALTER TABLE users ADD age INT")
print(f"Result: {result2}")

data2 = db.execute_query("SELECT * FROM users")
print(f"\nData after adding 'age' column:")
for row in data2:
    print(f"  {row}")

# Check default value for INT
if all(row.get('age') == 0 for row in data2):
    print("[v] PASS: Default value (0) added to all rows")
else:
    print("[x] FAIL: Default value not correctly applied")

# Test 4: Verify metadata persistence
print("\n[TEST 4] Testing metadata persistence")
print("-" * 70)

# Reload database
db2 = MiniDB()
desc2 = db2.execute_query("DESCRIBE users")
print(f"After reload - Columns: {desc2['columns']}")
print(f"After reload - Column Types: {desc2['column_types']}")

expected_columns = ['id', 'name', 'email', 'age']
if desc2['columns'] == expected_columns:
    print("[v] PASS: Schema persisted correctly")
else:
    print(f"[x] FAIL: Expected {expected_columns}, got {desc2['columns']}")

# Test 5: Insert data with new columns
print("\n[TEST 5] Inserting data with new columns")
print("-" * 70)

db.execute_query("INSERT INTO users VALUES (3, 'Charlie', 'charlie@example.com', 25)")
data3 = db.execute_query("SELECT * FROM users")
print("All data:")
for row in data3:
    print(f"  {row}")

# Test 6: Update existing rows with new column values
print("\n[TEST 6] Updating new column values")
print("-" * 70)

db.execute_query("UPDATE users SET email = 'alice@example.com' WHERE id = 1")
db.execute_query("UPDATE users SET age = 30 WHERE id = 1")

data4 = db.execute_query("SELECT * FROM users WHERE id = 1")
print(f"Updated row: {data4[0]}")

if data4[0]['email'] == 'alice@example.com' and data4[0]['age'] == 30:
    print("[v] PASS: New columns can be updated")
else:
    print("[x] FAIL: Update failed")

# Test 7: Try to add duplicate column (should fail)
print("\n[TEST 7] Attempting to add duplicate column (should fail)")
print("-" * 70)

result_dup = db.execute_query("ALTER TABLE users ADD name STR")
print(f"Result: {result_dup}")

if "Error" in result_dup or "already exists" in result_dup:
    print("[v] PASS: Duplicate column rejected")
else:
    print("[x] FAIL: Duplicate column should have been rejected")

# Test 8: Verify data file structure
print("\n[TEST 8] Verifying data file structure")
print("-" * 70)

import json
file_data = []
with open("data/users.jsonl", "r") as f:
    for line in f:
        if line.strip():
            file_data.append(json.loads(line))

print(f"Data file contains {len(file_data)} rows")
if file_data:
    print(f"First row keys: {list(file_data[0].keys())}")

expected_keys = {'id', 'name', 'email', 'age'}
if file_data and set(file_data[0].keys()) == expected_keys:
    print("[v] PASS: Data file structure correct")
else:
    print(f"[x] FAIL: Expected keys {expected_keys}, got {set(file_data[0].keys()) if file_data else 'None'}")

print("\n" + "=" * 70)
print("ALTER TABLE TESTS COMPLETE")
print("=" * 70)
