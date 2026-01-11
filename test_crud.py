import os
import shutil
from minidb import MiniDB

def test_crud_operations():
    test_dir = "test_crud_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    db = MiniDB(data_dir=test_dir)
    db.execute_query("CREATE TABLE students (id, name, grade)")
    
    # 1. Test INSERT
    db.execute_query("INSERT INTO students VALUES (1, 'Alice', 'A')")
    db.execute_query("INSERT INTO students VALUES (2, 'Bob', 'B')")
    db.execute_query("INSERT INTO students VALUES (3, 'Charlie', 'C')")
    
    # 2. Test UPDATE
    print("Executing UPDATE: UPDATE students SET grade = 'A+' WHERE id = 2")
    res = db.execute_query("UPDATE students SET grade = 'A+' WHERE id = 2")
    print(f"Result: {res}")
    
    # Verify Update
    records = db.execute_query("SELECT * FROM students WHERE id = 2")
    if records and records[0]['grade'] == 'A+':
        print("[v] Update successful: Bob's grade is now A+.")
    else:
        print(f"[x] Update failed: {records}")

    # 3. Test DELETE
    print("\nExecuting DELETE: DELETE FROM students WHERE id = 3")
    res = db.execute_query("DELETE FROM students WHERE id = 3")
    print(f"Result: {res}")
    
    # Verify Delete
    records = db.execute_query("SELECT * FROM students WHERE id = 3")
    if not records:
        print("[v] Delete successful: Charlie is gone.")
    else:
        print(f"[x] Delete failed: {records}")

    # 4. Test Multi-Row Update
    db.execute_query("INSERT INTO students VALUES (4, 'Dave', 'B')")
    print("\nExecuting Multi-UPDATE: UPDATE students SET grade = 'Pass' WHERE grade = 'B'")
    db.execute_query("UPDATE students SET grade = 'Pass' WHERE grade = 'B'")
    
    records = db.execute_query("SELECT * FROM students WHERE grade = 'Pass'")
    if len(records) == 1: # Dave (id=4) should be 'Pass', Bob was already updated to 'A+'
        print("[v] Multi-Update successful.")
    else:
        print(f"[x] Multi-Update result count mismatch: {len(records)}")

    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    print("\n--- CRUD Verification Complete ---")

if __name__ == "__main__":
    test_crud_operations()
