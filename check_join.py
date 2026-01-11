from minidb import MiniDB

db = MiniDB()
query = "SELECT * FROM students JOIN courses ON students.course_id = courses.id"
results = db.execute_query(query)
print(f"Join Results Type: {type(results)}")
print(f"Results: {results}")

# Check if data exists
print("\nStudents Table:")
print(db.execute_query("SELECT * FROM students"))
print("\nCourses Table:")
print(db.execute_query("SELECT * FROM courses"))
