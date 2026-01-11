"""
Test Foreign Key Support
"""
from minidb import MiniDB
import os
import shutil

# Clean slate
if os.path.exists("data"):
    shutil.rmtree("data")

db = MiniDB()

print("=" * 70)
print("FOREIGN KEY SUPPORT - TEST")
print("=" * 70)

# Test 1: Create table with foreign key
print("\n[TEST 1] Creating table with FOREIGN KEY constraint")
print("-" * 70)

query1 = "CREATE TABLE courses (id int, title str)"
result1 = db.execute_query(query1)
print(f"Query: {query1}")
print(f"Result: {result1}")

query2 = "CREATE TABLE students (id int, name str, course_id int, FOREIGN KEY (course_id) REFERENCES courses(id))"
result2 = db.execute_query(query2)
print(f"\nQuery: {query2}")
print(f"Result: {result2}")

# Test 2: Verify foreign key is stored in metadata
print("\n[TEST 2] Verifying foreign key in table metadata")
print("-" * 70)

desc = db.execute_query("DESCRIBE students")
print(f"DESCRIBE students:")
print(f"  Columns: {desc['columns']}")
print(f"  Column Types: {desc['column_types']}")
print(f"  Foreign Keys: {desc['foreign_keys']}")

if desc['foreign_keys'] == {'course_id': 'courses.id'}:
    print("\n✓ PASS: Foreign key correctly stored!")
else:
    print(f"\n✗ FAIL: Expected {{'course_id': 'courses.id'}}, got {desc['foreign_keys']}")

# Test 3: Verify metadata persistence
print("\n[TEST 3] Testing metadata persistence")
print("-" * 70)

# Reload database
db2 = MiniDB()
desc2 = db2.execute_query("DESCRIBE students")
print(f"After reload - Foreign Keys: {desc2['foreign_keys']}")

if desc2['foreign_keys'] == {'course_id': 'courses.id'}:
    print("✓ PASS: Foreign key persisted across database reload!")
else:
    print(f"✗ FAIL: Foreign key not persisted correctly")

# Test 4: Multiple foreign keys
print("\n[TEST 4] Table with multiple foreign keys")
print("-" * 70)

query3 = "CREATE TABLE enrollments (id int, student_id int, course_id int, FOREIGN KEY (student_id) REFERENCES students(id), FOREIGN KEY (course_id) REFERENCES courses(id))"
result3 = db.execute_query(query3)
print(f"Query: {query3}")
print(f"Result: {result3}")

desc3 = db.execute_query("DESCRIBE enrollments")
print(f"\nForeign Keys: {desc3['foreign_keys']}")

expected_fks = {
    'student_id': 'students.id',
    'course_id': 'courses.id'
}

if desc3['foreign_keys'] == expected_fks:
    print("✓ PASS: Multiple foreign keys correctly stored!")
else:
    print(f"✗ FAIL: Expected {expected_fks}, got {desc3['foreign_keys']}")

# Test 5: Parser test - verify correct extraction
print("\n[TEST 5] Parser extraction test")
print("-" * 70)

from minidb.parser import SQLParser
parser = SQLParser()

test_query = "CREATE TABLE test (id int, ref_id int, FOREIGN KEY (ref_id) REFERENCES other(id))"
parsed = parser.parse(test_query)

print(f"Query: {test_query}")
print(f"Parsed columns: {parsed['columns']}")
print(f"Parsed foreign_keys: {parsed['foreign_keys']}")

if parsed['foreign_keys'] == {'ref_id': 'other.id'}:
    print("✓ PASS: Parser correctly extracts foreign key!")
else:
    print(f"✗ FAIL: Parser extraction failed")

print("\n" + "=" * 70)
print("FOREIGN KEY TESTS COMPLETE")
print("=" * 70)
