import time
import random
from faker import Faker
from minidb import MiniDB

def seed_data():
    fake = Faker()
    db = MiniDB()
    
    print("--- MiniDB Data Seeding ---")
    
    # 1. Cleanup existing tables if they exist
    print("Preparing tables...")
    db.execute_query("DROP TABLE large_students")
    db.execute_query("DROP TABLE large_courses")
    
    # 2. Create tables
    db.execute_query("CREATE TABLE large_courses (id INT, title STR, faculty STR)")
    db.execute_query("CREATE TABLE large_students (id INT, name STR, email STR, course_id INT)")
    
    start_time = time.time()
    
    # 3. Seed Courses (50)
    print("Generating 50 courses...")
    course_ids = []
    for i in range(1, 51):
        title = fake.job() + " Science"
        faculty = "Faculty of " + fake.word().capitalize()
        db.execute_query(f"INSERT INTO large_courses VALUES ({i}, '{title}', '{faculty}')")
        course_ids.append(i)
        
    # 4. Seed Students (5000)
    print("Generating 5000 students...")
    # Using transactions for much faster seeding if supported, 
    # but the prompt says 'Batch Insert' which usually implies loops in our context.
    # Actually, our insert_row saves after every insert unless in a transaction.
    # To be fast, we SHOULD use a transaction.
    
    db.execute_query("BEGIN")
    for i in range(1, 5001):
        name = fake.name().replace("'", "") # Avoid SQL syntax errors with names like O'Connell
        email = fake.email()
        course_id = random.choice(course_ids)
        db.execute_query(f"INSERT INTO large_students VALUES ({i}, '{name}', '{email}', {course_id})")
        
        if i % 1000 == 0:
            print(f"  Inserted {i} records...")
            
    db.execute_query("COMMIT")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nSeeding complete: 5000 records generated in {duration:.2f} seconds.")

if __name__ == "__main__":
    # Ensure faker is installed for the script to run locally
    try:
        import faker
    except ImportError:
        print("Installing faker library...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "faker"])
        
    seed_data()
