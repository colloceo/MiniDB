import os
import shutil
from minidb import MiniDB

def test_operators():
    test_dir = "test_op_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    db = MiniDB(data_dir=test_dir)
    db.execute_query("CREATE TABLE scores (id, student, grade)")
    
    # Setup data
    db.execute_query("INSERT INTO scores VALUES (1, 'Alice', 95)")
    db.execute_query("INSERT INTO scores VALUES (2, 'Bob', 85)")
    db.execute_query("INSERT INTO scores VALUES (3, 'Charlie', 70)")
    db.execute_query("INSERT INTO scores VALUES (4, 'Dave', 60)")
    
    # 1. Test '>' operator
    print("Executing SELECT: SELECT * FROM scores WHERE grade > 80")
    res = db.execute_query("SELECT * FROM scores WHERE grade > 80")
    print(f"Result (Should be Alice and Bob): {len(res)} rows found.")
    if len(res) == 2:
        print("[v] '>' operator works correctly.")
    else:
        print(f"[x] '>' operator failed: {res}")

    # 2. Test '<=' operator
    print("\nExecuting SELECT: SELECT * FROM scores WHERE grade <= 70")
    res = db.execute_query("SELECT * FROM scores WHERE grade <= 70")
    print(f"Result (Should be Charlie and Dave): {len(res)} rows found.")
    if len(res) == 2:
        print("[v] '<=' operator works correctly.")
    else:
        print(f"[x] '<=' operator failed: {res}")

    # 3. Test '!=' operator
    print("\nExecuting DELETE: DELETE FROM scores WHERE grade != 95")
    db.execute_query("DELETE FROM scores WHERE grade != 95")
    res = db.execute_query("SELECT * FROM scores")
    print(f"Result (Should be only Alice): {len(res)} rows remained.")
    if len(res) == 1 and res[0]['student'] == 'Alice':
        print("[v] '!=' operator works correctly for DELETE.")
    else:
        print(f"[x] '!=' operator failed for DELETE: {res}")

    # 4. Test '>=' operator with UPDATE
    db.execute_query("INSERT INTO scores VALUES (5, 'Eve', 50)")
    print("\nExecuting UPDATE: UPDATE scores SET student = 'Super Alice' WHERE grade >= 95")
    res_update = db.execute_query("UPDATE scores SET student = 'Super Alice' WHERE grade >= 95")
    print(f"Update Result: {res_update}")
    
    res = db.execute_query("SELECT * FROM scores WHERE id = 1")
    print(f"Final Student Record: {res}")
    if res and res[0]['student'] == 'Super Alice':
        print("[v] '>=' operator works correctly for UPDATE.")
    else:
        print(f"[x] '>=' operator failed for UPDATE. Expected student 'Super Alice', got '{res[0]['student'] if res else 'None'}'")

    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    print("\n--- Operator Verification Complete ---")

if __name__ == "__main__":
    test_operators()
