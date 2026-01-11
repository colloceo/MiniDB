import time
from minidb import MiniDB

def benchmark():
    db = MiniDB()
    
    print("--- MiniDB Hash Join Benchmark ---")
    print("Dataset: 5000 Students x 50 Courses")
    
    # Warm up / Load tables
    db.execute_query("SELECT * FROM large_students LIMIT 1")
    db.execute_query("SELECT * FROM large_courses LIMIT 1")
    
    print("\nExecuting: SELECT * FROM large_students JOIN large_courses ON large_students.course_id = large_courses.id")
    
    start_time = time.time()
    results = db.execute_query("SELECT * FROM large_students JOIN large_courses ON large_students.course_id = large_courses.id")
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Join complete: {len(results)} rows returned.")
    print(f"Execution Time: {duration:.4f} seconds.")
    
    if duration < 0.1:
        print("\n[v] Performance is EXCELLENT (Sub-100ms for 5000 records).")
    elif duration < 0.5:
        print("\n[v] Performance is GOOD.")
    else:
        print("\n[!] Performance could be improved.")

if __name__ == "__main__":
    benchmark()
