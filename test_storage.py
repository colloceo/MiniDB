from minidb import Table, ValidationError, DBError
import os
import shutil

def test_storage():
    print("--- Testing MiniDB Storage Layer ---")
    
    # Setup: Ensure a clean environment for testing
    test_data_dir = "test_data"
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)
    
    table_name = "users"
    columns = ["id", "name", "email"]
    
    # 1. Initialization
    try:
        users = Table(table_name, columns, data_dir=test_data_dir)
        print("[v] Table initialization successful.")
    except Exception as e:
        print(f"[x] Table initialization failed: {e}")
        return

    # 2. Insert Valid Row
    try:
        users.insert_row({"id": 1, "name": "Alice", "email": "alice@example.com"})
        print("[v] Row insertion successful.")
    except Exception as e:
        print(f"[x] Row insertion failed: {e}")

    # 3. Persistence Check (Reload)
    try:
        users_reloaded = Table(table_name, columns, data_dir=test_data_dir)
        data = users_reloaded.select_all()
        if len(data) == 1 and data[0]["name"] == "Alice":
            print("[v] Data persistence verified.")
        else:
            print(f"[x] Data persistence failed. Data: {data}")
    except Exception as e:
        print(f"[x] Reload failed: {e}")

    # 4. Validation Check (Invalid Columns)
    try:
        users.insert_row({"id": 2, "name": "Bob"}) # Missing 'email'
        print("[x] Validation failed: Accepted row with missing columns.")
    except ValidationError as e:
        print(f"[v] Validation successfully caught missing column: {e}")

    # 5. Validation Check (Extra Columns)
    try:
        users.insert_row({"id": 2, "name": "Bob", "email": "bob@example.com", "age": 30})
        print("[x] Validation failed: Accepted row with extra columns.")
    except ValidationError as e:
        print(f"[v] Validation successfully caught extra column: {e}")

    # Cleanup
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)
    print("--- Testing Complete ---")

if __name__ == "__main__":
    test_storage()
