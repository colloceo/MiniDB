import os
import shutil
from minidb import MiniDB

def test_sql_injection():
    data_dir = "test_security_data"
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
        
    db = MiniDB(data_dir=data_dir)
    
    # 1. Setup tables
    db.execute_query("CREATE TABLE students (id int, name str)")
    db.execute_query("INSERT INTO students VALUES (1, 'Alice')")
    
    print("Initial state: students table exists.")
    
    # 2. Attempt SQL Injection
    # The payload tries to close the current statement and drop the table
    # In MiniDB, since the parser is regex based, a classic injection might look like this
    # to confuse the regex or the subsequent execution logic.
    injection_payload = "Hacker'); DROP TABLE students; --"
    
    print(f"\nAttempting injection with payload: {injection_payload}")
    
    # Using parameterized query (The safe way)
    query = "INSERT INTO students VALUES (?, ?)"
    params = (2, injection_payload)
    
    try:
        msg = db.execute_query(query, params)
        print(f"Server response: {msg}")
    except Exception as e:
        print(f"Error during execution: {e}")
        
    # 3. Verify if students table still exists
    tables = db.get_tables()
    print(f"\nCurrent tables: {tables}")
    
    if 'students' in tables:
        print("✅ SUCCESS: 'students' table still exists. System is protected.")
    else:
        print("❌ FAILURE: 'students' table was DROPPED! System is VULNERABLE.")
        # Cleanup before exit
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
        return
        
    # 4. Verify the data was inserted literally
    res = db.execute_query("SELECT * FROM students WHERE id = 2")
    if res and res[0]['name'] == injection_payload:
        print(f"✅ SUCCESS: Payload was stored literally as: {res[0]['name']}")
    else:
        # MiniDB's INSERT regex might split on commas, let's see how it handled the payload
        print(f"Current data for ID 2: {res}")
        if res and injection_payload in str(res[0]['name']):
             print("✅ SUCCESS: Payload was stored safely (escaping quotes worked).")
        else:
             print("❌ FAILURE: Payload handling error.")

    # Cleanup
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)

if __name__ == "__main__":
    test_sql_injection()
