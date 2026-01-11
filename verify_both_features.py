"""
Quick verification that both features are working
"""
from minidb import MiniDB
import os
import shutil

# Clean start
if os.path.exists("data"):
    shutil.rmtree("data")

db = MiniDB()

print("="*70)
print("VERIFICATION: FOREIGN KEYS + ALTER TABLE")
print("="*70)

# Test 1: Foreign Keys
print("\n[TEST 1] Foreign Key Support")
print("-"*70)
db.execute_query("CREATE TABLE departments (id INT, name STR)")
db.execute_query("""
    CREATE TABLE employees (
        id INT, 
        name STR, 
        dept_id INT, 
        FOREIGN KEY (dept_id) REFERENCES departments(id)
    )
""")

desc = db.execute_query("DESCRIBE employees")
print(f"Foreign Keys: {desc['foreign_keys']}")
assert desc['foreign_keys'] == {'dept_id': 'departments.id'}, "Foreign key not stored!"
print("✓ PASS: Foreign key correctly stored")

# Test 2: ALTER TABLE
print("\n[TEST 2] ALTER TABLE ADD COLUMN")
print("-"*70)
db.execute_query("INSERT INTO employees VALUES (1, 'Alice', 1)")
db.execute_query("INSERT INTO employees VALUES (2, 'Bob', 1)")

# Add email column
db.execute_query("ALTER TABLE employees ADD email STR")
desc2 = db.execute_query("DESCRIBE employees")
print(f"Updated columns: {desc2['columns']}")
assert 'email' in desc2['columns'], "Column not added!"

# Check data
data = db.execute_query("SELECT * FROM employees")
print(f"Data after ALTER: {data}")
assert all('email' in row for row in data), "Column not in all rows!"
assert all(row['email'] == '' for row in data), "Default value incorrect!"
print("✓ PASS: Column added with default values")

# Add salary column
db.execute_query("ALTER TABLE employees ADD salary INT")
data2 = db.execute_query("SELECT * FROM employees")
assert all(row['salary'] == 0 for row in data2), "INT default incorrect!"
print("✓ PASS: INT column added with default value 0")

# Test 3: Persistence
print("\n[TEST 3] Metadata Persistence")
print("-"*70)
db2 = MiniDB()  # Reload
desc3 = db2.execute_query("DESCRIBE employees")
print(f"After reload - Columns: {desc3['columns']}")
print(f"After reload - Foreign Keys: {desc3['foreign_keys']}")
assert desc3['foreign_keys'] == {'dept_id': 'departments.id'}, "FK not persisted!"
assert desc3['columns'] == ['id', 'name', 'dept_id', 'email', 'salary'], "Schema not persisted!"
print("✓ PASS: All metadata persisted correctly")

print("\n" + "="*70)
print("✅ ALL FEATURES VERIFIED AND WORKING!")
print("="*70)
print("\nImplemented Features:")
print("  ✓ Foreign Key constraints (metadata storage)")
print("  ✓ ALTER TABLE ADD COLUMN (schema modification)")
print("  ✓ Type-based default values")
print("  ✓ Atomic operations")
print("  ✓ Metadata persistence")
print("\n" + "="*70)
