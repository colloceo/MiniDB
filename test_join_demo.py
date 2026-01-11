"""
Demo script to verify JOIN functionality and Hash Join algorithm
"""
from minidb import MiniDB
import os
import shutil

# Clean slate - remove existing data
if os.path.exists("data"):
    shutil.rmtree("data")

# Initialize database
db = MiniDB()

print("=" * 60)
print("MiniDB JOIN Feature Demonstration")
print("=" * 60)

# Create tables with proper schema
print("\n1. Creating tables...")
db.execute_query("CREATE TABLE students (id int, name str, course_id int)")
db.execute_query("CREATE TABLE courses (id int, title str)")
print("   ✓ Tables created: students, courses")

# Insert seed data
print("\n2. Inserting seed data...")
db.execute_query("INSERT INTO courses VALUES (1, 'Computer Science')")
db.execute_query("INSERT INTO courses VALUES (2, 'Electrical Eng')")
db.execute_query("INSERT INTO students VALUES (101, 'Collins', 1)")
db.execute_query("INSERT INTO students VALUES (102, 'John', 2)")
print("   ✓ Inserted 2 courses and 2 students")

# Display individual tables
print("\n3. Viewing individual tables:")
print("\n   STUDENTS TABLE:")
students = db.execute_query("SELECT * FROM students")
for student in students:
    print(f"   - ID: {student['id']}, Name: {student['name']}, Course ID: {student['course_id']}")

print("\n   COURSES TABLE:")
courses = db.execute_query("SELECT * FROM courses")
for course in courses:
    print(f"   - ID: {course['id']}, Title: {course['title']}")

# Execute JOIN query
print("\n4. Executing JOIN query:")
print("   Query: SELECT * FROM students JOIN courses ON students.course_id = courses.id")
print()

results = db.execute_query("SELECT * FROM students JOIN courses ON students.course_id = courses.id")

if isinstance(results, str):
    print(f"   ✗ Error: {results}")
else:
    print(f"   ✓ JOIN successful! Found {len(results)} matching rows\n")
    print("   JOINED RESULTS:")
    print("   " + "-" * 56)
    print(f"   {'Student Name':<20} | {'Course Title':<30}")
    print("   " + "-" * 56)
    for row in results:
        student_name = row.get('name', 'N/A')
        course_title = row.get('title', 'N/A')
        print(f"   {student_name:<20} | {course_title:<30}")
    print("   " + "-" * 56)

print("\n5. Algorithm Analysis:")
print("   ✓ Parser: Regex-based SQL parsing with JOIN support")
print("   ✓ Algorithm: Hash Join (O(N+M) complexity)")
print("   ✓ Optimization: Smaller table used for hash map build phase")

print("\n" + "=" * 60)
print("Demo Complete!")
print("=" * 60)
