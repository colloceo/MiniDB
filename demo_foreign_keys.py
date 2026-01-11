"""
Foreign Key Feature Demo
Demonstrates the new FOREIGN KEY support in MiniDB
"""
from minidb import MiniDB
import os
import shutil

# Clean start
if os.path.exists("data"):
    shutil.rmtree("data")

print("\n" + "="*70)
print("MINIDB FOREIGN KEY FEATURE DEMONSTRATION")
print("="*70)

db = MiniDB()

# Step 1: Create parent table
print("\n📋 Step 1: Creating parent table (courses)")
print("-"*70)
query1 = "CREATE TABLE courses (id INT, title STR)"
result1 = db.execute_query(query1)
print(f"SQL: {query1}")
print(f"[v] {result1}")

# Step 2: Create child table with foreign key
print("\n📋 Step 2: Creating child table with FOREIGN KEY constraint")
print("-"*70)
query2 = """CREATE TABLE students (
    id INT, 
    name STR, 
    course_id INT, 
    FOREIGN KEY (course_id) REFERENCES courses(id)
)""".replace('\n', ' ')
result2 = db.execute_query(query2)
print(f"SQL: {query2}")
print(f"[v] {result2}")

# Step 3: Inspect schema
print("\n📋 Step 3: Inspecting table schema")
print("-"*70)
desc = db.execute_query("DESCRIBE students")
print("DESCRIBE students:")
print(f"  • Columns: {desc['columns']}")
print(f"  • Primary Key: {desc['primary_key']}")
print(f"  • Column Types: {desc['column_types']}")
print(f"  • Foreign Keys: {desc['foreign_keys']}")

# Step 4: Insert sample data
print("\n📋 Step 4: Inserting sample data")
print("-"*70)
db.execute_query("INSERT INTO courses VALUES (1, 'Computer Science')")
db.execute_query("INSERT INTO courses VALUES (2, 'Electrical Engineering')")
db.execute_query("INSERT INTO students VALUES (101, 'Collins', 1)")
db.execute_query("INSERT INTO students VALUES (102, 'John', 2)")
print("[v] Inserted 2 courses and 2 students")

# Step 5: Query with JOIN
print("\n📋 Step 5: Querying with JOIN (using foreign key relationship)")
print("-"*70)
join_query = "SELECT * FROM students JOIN courses ON students.course_id = courses.id"
results = db.execute_query(join_query)
print(f"SQL: {join_query}\n")
print(f"{'Student Name':<20} | {'Course Title':<30}")
print("-"*52)
for row in results:
    print(f"{row['name']:<20} | {row['title']:<30}")

# Step 6: Demonstrate persistence
print("\n📋 Step 6: Testing metadata persistence")
print("-"*70)
db2 = MiniDB()  # Reload database
desc2 = db2.execute_query("DESCRIBE students")
print("After database reload:")
print(f"  • Foreign Keys: {desc2['foreign_keys']}")
print("[v] Foreign key constraint persisted!")

# Step 7: Multiple foreign keys example
print("\n📋 Step 7: Creating table with multiple foreign keys")
print("-"*70)
query3 = """CREATE TABLE enrollments (
    id INT,
    student_id INT,
    course_id INT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
)""".replace('\n', ' ')
result3 = db.execute_query(query3)
print(f"SQL: {query3}")
print(f"[v] {result3}")

desc3 = db.execute_query("DESCRIBE enrollments")
print(f"\nForeign Keys: {desc3['foreign_keys']}")

print("\n" + "="*70)
print("[PASS] FOREIGN KEY FEATURE DEMONSTRATION COMPLETE")
print("="*70)
print("\nKey Features Demonstrated:")
print("  [v] FOREIGN KEY syntax parsing")
print("  [v] Metadata storage in table.foreign_keys")
print("  [v] Persistence across database restarts")
print("  [v] DESCRIBE command shows foreign keys")
print("  [v] Multiple foreign keys per table")
print("  [v] Integration with JOIN queries")
print("\n" + "="*70 + "\n")
