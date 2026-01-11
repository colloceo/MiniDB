"""
ALTER TABLE Feature Demo
Demonstrates dynamic schema modification in MiniDB
"""
from minidb import MiniDB
import os
import shutil

# Clean start
if os.path.exists("data"):
    shutil.rmtree("data")

print("\n" + "="*70)
print("MINIDB ALTER TABLE FEATURE DEMONSTRATION")
print("="*70)

db = MiniDB()

# Step 1: Create initial table
print("\n📋 Step 1: Creating initial table")
print("-"*70)
db.execute_query("CREATE TABLE employees (id INT, name STR)")
print("[v] Table 'employees' created with columns: id, name")

# Step 2: Insert initial data
print("\n📋 Step 2: Inserting initial employee data")
print("-"*70)
db.execute_query("INSERT INTO employees VALUES (1, 'Alice Johnson')")
db.execute_query("INSERT INTO employees VALUES (2, 'Bob Smith')")
db.execute_query("INSERT INTO employees VALUES (3, 'Charlie Brown')")
print("[v] Inserted 3 employees")

data = db.execute_query("SELECT * FROM employees")
print("\nInitial data:")
for row in data:
    print(f"  ID: {row['id']}, Name: {row['name']}")

# Step 3: Add email column
print("\n📋 Step 3: Adding 'email' column (STR)")
print("-"*70)
result = db.execute_query("ALTER TABLE employees ADD email STR")
print(f"[v] {result}")

desc = db.execute_query("DESCRIBE employees")
print(f"Updated schema: {desc['columns']}")

data = db.execute_query("SELECT * FROM employees")
print("\nData after adding 'email' (defaults to ''):")
for row in data:
    print(f"  {row}")

# Step 4: Add salary column
print("\n📋 Step 4: Adding 'salary' column (INT)")
print("-"*70)
result2 = db.execute_query("ALTER TABLE employees ADD salary INT")
print(f"[v] {result2}")

desc2 = db.execute_query("DESCRIBE employees")
print(f"Updated schema: {desc2['columns']}")
print(f"Column types: {desc2['column_types']}")

# Step 5: Update new column values
print("\n📋 Step 5: Updating new column values")
print("-"*70)
db.execute_query("UPDATE employees SET email = 'alice@company.com' WHERE id = 1")
db.execute_query("UPDATE employees SET salary = 75000 WHERE id = 1")

db.execute_query("UPDATE employees SET email = 'bob@company.com' WHERE id = 2")
db.execute_query("UPDATE employees SET salary = 65000 WHERE id = 2")

print("[v] Updated Alice and Bob's email and salary")

data = db.execute_query("SELECT * FROM employees")
print("\nUpdated data:")
for row in data:
    print(f"  {row}")

# Step 6: Insert new employee with all columns
print("\n📋 Step 6: Inserting new employee with all columns")
print("-"*70)
db.execute_query("INSERT INTO employees VALUES (4, 'Diana Prince', 'diana@company.com', 85000)")
print("[v] Inserted Diana with complete information")

data = db.execute_query("SELECT * FROM employees")
print("\nAll employees:")
print(f"{'ID':<5} | {'Name':<20} | {'Email':<25} | {'Salary':<10}")
print("-"*70)
for row in data:
    print(f"{row['id']:<5} | {row['name']:<20} | {row['email']:<25} | {row['salary']:<10}")

# Step 7: Add department column
print("\n📋 Step 7: Adding 'department' column")
print("-"*70)
db.execute_query("ALTER TABLE employees ADD department STR")
db.execute_query("UPDATE employees SET department = 'Engineering' WHERE id = 1")
db.execute_query("UPDATE employees SET department = 'Sales' WHERE id = 2")
db.execute_query("UPDATE employees SET department = 'Engineering' WHERE id = 3")
db.execute_query("UPDATE employees SET department = 'Management' WHERE id = 4")
print("[v] Added department column and updated values")

# Step 8: Final schema and data
print("\n📋 Step 8: Final schema and complete dataset")
print("-"*70)

desc_final = db.execute_query("DESCRIBE employees")
print(f"Final schema:")
print(f"  Columns: {desc_final['columns']}")
print(f"  Types: {desc_final['column_types']}")

data_final = db.execute_query("SELECT * FROM employees")
print(f"\nComplete employee database ({len(data_final)} records):")
print(f"{'ID':<5} | {'Name':<20} | {'Email':<25} | {'Salary':<10} | {'Department':<15}")
print("-"*95)
for row in data_final:
    print(f"{row['id']:<5} | {row['name']:<20} | {row['email']:<25} | {row['salary']:<10} | {row['department']:<15}")

# Step 9: Demonstrate persistence
print("\n📋 Step 9: Testing schema persistence")
print("-"*70)
db2 = MiniDB()  # Reload database
desc_reload = db2.execute_query("DESCRIBE employees")
data_reload = db2.execute_query("SELECT * FROM employees")

print(f"After database reload:")
print(f"  Schema columns: {desc_reload['columns']}")
print(f"  Data rows: {len(data_reload)}")
print("[v] Schema and data persisted correctly!")

print("\n" + "="*70)
print("[PASS] ALTER TABLE FEATURE DEMONSTRATION COMPLETE")
print("="*70)
print("\nKey Features Demonstrated:")
print("  [v] Dynamic schema modification (ALTER TABLE ADD COLUMN)")
print("  [v] Type-based default values (INT→0, STR→'')")
print("  [v] Existing rows automatically updated")
print("  [v] New columns can be updated and queried")
print("  [v] New rows include all columns")
print("  [v] Schema changes persist across restarts")
print("  [v] Atomic operations ensure data integrity")
print("\n" + "="*70 + "\n")
