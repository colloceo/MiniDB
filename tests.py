import os
import subprocess
import sys

def run_test_file(filename):
    print(f"Running {filename}...")
    try:
        # Run the test as a subprocess
        result = subprocess.run([sys.executable, filename], capture_output=True, text=True)
        
        # Print output regardless of success for logs
        print(result.stdout)
        if result.stderr:
            print(f"Error Output:\n{result.stderr}", file=sys.stderr)
            
        # Check if the process exited with non-zero
        if result.returncode != 0:
            return False
            
        # Check output for failure patterns like '[x]'
        if "[x]" in result.stdout:
            return False
            
        return True
    except Exception as e:
        print(f"Failed to execute {filename}: {e}", file=sys.stderr)
        return False

def main():
    # List of core tests to run for CI validation
    core_tests = [
        "test_parser.py",
        "test_engine.py",
        "test_storage.py",
        "test_crud.py",
        "test_join.py",
        "test_metadata.py",
        "test_transactions.py",
        "test_alter_table.py",
        "test_column_management.py"
    ]
    
    passed_all = True
    for test in core_tests:
        if not os.path.exists(test):
            print(f"Warning: Test file {test} not found, skipping.")
            continue
            
        if not run_test_file(test):
            print(f"FAILED: {test}")
            passed_all = False
        else:
            print(f"PASSED: {test}")
        print("-" * 40)
        
    if not passed_all:
        print("Final Result: FAIL")
        sys.exit(1)
    else:
        print("Final Result: ALL TESTS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
