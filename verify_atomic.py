import os
import json
import shutil
from minidb import MiniDB
from minidb.table import Table, DBError
from unittest.mock import patch

def test_atomic_write_robustness():
    test_dir = "test_atomic_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    table_name = "test_table"
    columns = ["id", "name"]
    file_path = os.path.join(test_dir, f"{table_name}.json")
    temp_path = f"{file_path}.tmp"
    
    # 1. Create initial table and data
    table = Table(table_name, columns, data_dir=test_dir)
    table.insert_row({"id": 1, "name": "Initial"})
    
    with open(file_path, "r") as f:
        initial_content = f.read()
    print("[v] Initial file created.")

    # 2. Simulate crash during save_data
    # We mock json.dump to raise an error during the next save
    print("Simulating crash during save_data...")
    with patch("json.dump", side_effect=IOError("Simulated Crash")):
        try:
            table.insert_row({"id": 2, "name": "Crashed"})
        except DBError as e:
            print(f"[v] Caught expected DBError: {e}")

    # 3. Verify original file is UNTOUCHED
    with open(file_path, "r") as f:
        current_content = f.read()
    
    if current_content == initial_content:
        print("[v] Original file is intact after simulated crash.")
    else:
        print("[x] Error: Original file was corrupted or updated prematurely!")

    # 4. Verify temp file is CLEANED UP
    if not os.path.exists(temp_path):
        print("[v] Temporary file was cleaned up.")
    else:
        print("[x] Error: Temporary file still exists!")

    # Cleanup
    shutil.rmtree(test_dir)
    print("--- Atomic Write Verification Complete ---")

if __name__ == "__main__":
    test_atomic_write_robustness()
