# MiniDB SQL Syntax Guide

## Quick Reference

This guide shows the correct SQL syntax for MiniDB commands.

---

## ✅ Supported Commands

### 1. **SHOW TABLES**
List all tables in the database.

```sql
SHOW TABLES
```

**Example:**
```
minidb> SHOW TABLES
['students', 'courses', 'users']
```

---

### 2. **DESCRIBE / DESC**
Show table structure (columns, types, constraints).

```sql
DESCRIBE table_name
DESC table_name          -- Shorthand alias
```

**Example:**
```
minidb> DESC students
{'columns': ['id', 'name', 'course_id'], 'primary_key': 'id', 'column_types': {'id': 'int', 'name': 'str', 'course_id': 'int'}, 'unique_columns': []}

minidb> DESCRIBE courses
{'columns': ['id', 'title'], 'primary_key': 'id', 'column_types': {'id': 'int', 'title': 'str'}, 'unique_columns': []}
```

---

### 3. **CREATE TABLE**
Create a new table with columns and optional types/constraints.

```sql
CREATE TABLE table_name (col1 [type] [UNIQUE], col2 [type], ...)
```

**Types:** `int`, `str`  
**Constraints:** `UNIQUE`

**Examples:**
```sql
-- Basic table
CREATE TABLE users (id, name, email)

-- With types
CREATE TABLE students (id int, name str, course_id int)

-- With unique constraint
CREATE TABLE accounts (id int, email str UNIQUE, username str UNIQUE)
```

---

### 4. **INSERT INTO**
Insert a new row into a table.

```sql
INSERT INTO table_name VALUES (value1, value2, ...)
```

**Examples:**
```sql
-- String values need quotes
INSERT INTO students VALUES (101, 'Collins', 1)

-- Numbers don't need quotes
INSERT INTO courses VALUES (1, 'Computer Science')

-- Mixed types
INSERT INTO users VALUES (5, 'John Doe', 'john@example.com')
```

---

### 5. **SELECT**
Retrieve data from a table.

#### **Select All Rows:**
```sql
SELECT * FROM table_name
```

#### **Select with WHERE Clause:**
```sql
SELECT * FROM table_name WHERE column operator value
```

**Operators:** `=`, `!=`, `>`, `<`, `>=`, `<=`

**Examples:**
```sql
-- All students
SELECT * FROM students

-- Specific student by ID
SELECT * FROM students WHERE id = 101

-- Students with course_id greater than 1
SELECT * FROM students WHERE course_id > 1

-- Students not in course 2
SELECT * FROM students WHERE course_id != 2

-- String comparison
SELECT * FROM students WHERE name = 'Collins'
```

**⚠️ IMPORTANT:** You **MUST** use the `WHERE` keyword!

❌ **WRONG:**
```sql
SELECT id=102 FROM students          -- Missing WHERE keyword
SELECT * FROM students id=101        -- Missing WHERE keyword
```

✅ **CORRECT:**
```sql
SELECT * FROM students WHERE id = 102
SELECT * FROM students WHERE id = 101
```

---

### 6. **SELECT with JOIN**
Combine data from two tables based on a related column.

```sql
SELECT * FROM table1 JOIN table2 ON table1.column = table2.column
```

**Example:**
```sql
-- Get student names with their course titles
SELECT * FROM students JOIN courses ON students.course_id = courses.id
```

**Result:**
```
id  | name    | course_id | title
----|---------|-----------|------------------
101 | Collins | 1         | Computer Science
102 | John    | 2         | Electrical Eng
```

---

### 7. **UPDATE**
Modify existing rows in a table.

```sql
UPDATE table_name SET column = value WHERE condition_column operator condition_value
```

**Examples:**
```sql
-- Update student name
UPDATE students SET name = 'Collins Jr.' WHERE id = 101

-- Update course title
UPDATE courses SET title = 'Advanced CS' WHERE id = 1

-- Update with numeric value
UPDATE students SET course_id = 2 WHERE id = 101
```

---

### 8. **DELETE**
Remove rows from a table.

```sql
DELETE FROM table_name WHERE column operator value
```

**Examples:**
```sql
-- Delete specific student
DELETE FROM students WHERE id = 101

-- Delete all students in course 1
DELETE FROM students WHERE course_id = 1

-- Delete by name
DELETE FROM students WHERE name = 'John'
```

---

### 9. **ALTER TABLE**
Modify table schema by adding new columns.

```sql
ALTER TABLE table_name ADD column_name data_type
```

**Supported Types:** `INT`, `STR`

**Behavior:**
- Adds column to table schema
- Updates all existing rows with default values:
  - `INT` → `0`
  - `STR` → `''` (empty string)
- Changes persist across database restarts

**Examples:**
```sql
-- Add email column
ALTER TABLE users ADD email STR

-- Add age column
ALTER TABLE users ADD age INT

-- Add multiple columns (run separately)
ALTER TABLE products ADD price INT
ALTER TABLE products ADD description STR
```

**After ALTER TABLE:**
```sql
-- Existing rows have default values
SELECT * FROM users
-- Output: [{'id': 1, 'name': 'Alice', 'email': ''}]

-- Update new column
UPDATE users SET email = 'alice@example.com' WHERE id = 1

-- Insert with new columns
INSERT INTO users VALUES (2, 'Bob', 'bob@example.com')
```

---

## 🚫 Common Mistakes

### Mistake 1: Missing WHERE keyword
❌ `SELECT id=102 FROM students`  
✅ `SELECT * FROM students WHERE id = 102`

### Mistake 2: Wrong DESCRIBE syntax
❌ `decribe users` (typo)  
✅ `DESCRIBE users` or `DESC users`

### Mistake 3: Case sensitivity in table names
❌ `DESCRIBE Users` (if table is 'users')  
✅ `DESCRIBE users`

### Mistake 4: Missing quotes for strings
❌ `INSERT INTO students VALUES (101, Collins, 1)`  
✅ `INSERT INTO students VALUES (101, 'Collins', 1)`

### Mistake 5: Typos in keywords
❌ `fronm` instead of `from`  
✅ `SELECT * FROM students`

---

## 💡 Tips

1. **Commands are case-insensitive:** `SELECT`, `select`, and `SeLeCt` all work
2. **Table names are case-sensitive:** `students` ≠ `Students`
3. **Use DESC for quick table inspection:** `DESC table_name`
4. **String values need quotes:** Use single quotes `'value'` or double quotes `"value"`
5. **Numbers don't need quotes:** `101`, `3.14`, etc.
6. **WHERE is required for conditions:** Always use `WHERE column = value`

---

## 📚 Full Example Session

```sql
minidb> SHOW TABLES
['students', 'courses']

minidb> DESC students
{'columns': ['id', 'name', 'course_id'], 'primary_key': 'id', ...}

minidb> SELECT * FROM students
id  | name    | course_id
----|---------|----------
101 | Collins | 1
102 | John    | 2

minidb> SELECT * FROM students WHERE id = 101
id  | name    | course_id
----|---------|----------
101 | Collins | 1

minidb> SELECT * FROM students JOIN courses ON students.course_id = courses.id
id  | name    | course_id | title
----|---------|-----------|------------------
101 | Collins | 1         | Computer Science
102 | John    | 2         | Electrical Eng

minidb> UPDATE students SET name = 'Collins Smith' WHERE id = 101
Updated 1 row(s) in 'students'.

minidb> DELETE FROM students WHERE id = 102
Deleted 1 row(s) from 'students'.
```

---

## 🎯 Need Help?

- Type `SHOW TABLES` to see available tables
- Type `DESC table_name` to see table structure
- Type `exit` or `quit` to leave the REPL

For more information, see the README.md file.
