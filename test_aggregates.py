from minidb import MiniDB
import os

def test_aggregates():
    db = MiniDB(data_dir="test_data")
    
    # Setup
    db.execute_query("DROP TABLE employees")
    db.execute_query("CREATE TABLE employees (id int, name str, salary int, score float)")
    db.execute_query("INSERT INTO employees VALUES (1, 'Alice', 50000, 85.5)")
    db.execute_query("INSERT INTO employees VALUES (2, 'Bob', 60000, 92.0)")
    db.execute_query("INSERT INTO employees VALUES (3, 'Charlie', 55000, 78.5)")
    
    print("--- Testing Aggregates ---")
    
    # Test AVG and MAX
    res = db.execute_query("SELECT AVG(salary), MAX(score) FROM employees")
    print(f"AVG/MAX Result: {res}")
    # Alice=50k, Bob=60k, Charlie=55k. AVG = 55000. MAX score = 92.0
    assert res[0]['AVG(salary)'] == 55000.0
    assert res[0]['MAX(score)'] == 92.0
    
    # Test COUNT(*) and SUM
    res = db.execute_query("SELECT COUNT(*), SUM(salary) FROM employees WHERE salary > 50000")
    print(f"COUNT/SUM Result: {res}")
    # Bob=60k, Charlie=55k. COUNT=2, SUM=115000
    assert res[0]['COUNT(*)'] == 2
    assert res[0]['SUM(salary)'] == 115000
    
    # Test MIN
    res = db.execute_query("SELECT MIN(salary) FROM employees")
    print(f"MIN Result: {res}")
    assert res[0]['MIN(salary)'] == 50000
    
    # Test Task 3: ValueError on SUM of STR
    print("\nTesting validation (Error on SUM of STR)...")
    res = db.execute_query("SELECT SUM(name) FROM employees")
    print(f"Error Result: {res}")
    assert "Error: Cannot compute SUM on non-numeric column 'name'" in res

    print("\nAll aggregate tests passed!")

if __name__ == "__main__":
    if not os.path.exists("test_data"):
        os.makedirs("test_data")
    try:
        test_aggregates()
    finally:
        # Cleanup
        if os.path.exists("test_data"):
            import shutil
            shutil.rmtree("test_data")
