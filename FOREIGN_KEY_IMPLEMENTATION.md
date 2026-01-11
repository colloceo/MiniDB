# Foreign Key Support - Implementation Guide

## ✅ Task 1 Complete: Foreign Key Parsing & Metadata Storage

### Overview

MiniDB now supports **FOREIGN KEY** constraints in `CREATE TABLE` statements. Foreign keys are parsed, stored in table metadata, and persisted across database restarts.

---

## 📝 Syntax

### Basic Foreign Key

```sql
CREATE TABLE students (
    id INT, 
    name STR, 
    course_id INT, 
    FOREIGN KEY (course_id) REFERENCES courses(id)
)
```

### Multiple Foreign Keys

```sql
CREATE TABLE enrollments (
    id INT,
    student_id INT,
    course_id INT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
)
```

### Combined with Other Constraints

```sql
CREATE TABLE users (
    id INT,
    email STR UNIQUE,
    department_id INT,
    FOREIGN KEY (department_id) REFERENCES departments(id)
)
```

---

## 🔧 Implementation Details

### 1. Parser Enhancement (`parser.py`)

**Pattern Matching:**
```python
fk_match = re.match(
    r'FOREIGN\s+KEY\s*\((\w+)\)\s+REFERENCES\s+(\w+)\s*\((\w+)\)', 
    part, 
    re.IGNORECASE
)
```

**Extraction:**
- **Group 1**: Local column name (e.g., `course_id`)
- **Group 2**: Referenced table name (e.g., `courses`)
- **Group 3**: Referenced column name (e.g., `id`)

**Storage Format:**
```python
foreign_keys = {
    'course_id': 'courses.id',
    'student_id': 'students.id'
}
```

---

### 2. Table Class Update (`table.py`)

**Constructor Signature:**
```python
def __init__(self, table_name, columns, primary_key=None, 
             column_types=None, unique_columns=None, 
             foreign_keys=None, data_dir="data"):
    # ...
    self.foreign_keys = foreign_keys or {}
```

**Metadata Storage:**
```python
{
    'columns': ['id', 'name', 'course_id'],
    'primary_key': 'id',
    'column_types': {'id': 'int', 'name': 'str', 'course_id': 'int'},
    'unique_columns': [],
    'foreign_keys': {'course_id': 'courses.id'}
}
```

---

### 3. Database Engine Update (`database.py`)

**Metadata Persistence:**
```python
def _save_metadata(self):
    metadata = {}
    for name, table in self.tables.items():
        metadata[name] = {
            'columns': table.columns,
            'primary_key': table.primary_key,
            'column_types': table.column_types,
            'unique_columns': table.unique_columns,
            'foreign_keys': table.foreign_keys  # ✅ Added
        }
```

**Metadata Loading:**
```python
def _load_metadata(self):
    # ...
    self.tables[table_name] = Table(
        table_name, 
        info['columns'], 
        primary_key=info.get('primary_key'),
        column_types=info.get('column_types'),
        unique_columns=info.get('unique_columns'),
        foreign_keys=info.get('foreign_keys'),  # ✅ Added
        data_dir=self.data_dir
    )
```

**CREATE TABLE Execution:**
```python
if cmd_type == 'CREATE':
    return self._create_table(
        table_name, 
        parsed['columns'], 
        column_types=parsed.get('column_types'),
        unique_columns=parsed.get('unique_columns'),
        foreign_keys=parsed.get('foreign_keys')  # ✅ Added
    )
```

---

## 🧪 Testing

### Test 1: Basic Foreign Key

```python
from minidb import MiniDB

db = MiniDB()

# Create parent table
db.execute_query("CREATE TABLE courses (id INT, title STR)")

# Create child table with foreign key
db.execute_query("""
    CREATE TABLE students (
        id INT, 
        name STR, 
        course_id INT, 
        FOREIGN KEY (course_id) REFERENCES courses(id)
    )
""")

# Verify foreign key
desc = db.execute_query("DESCRIBE students")
print(desc['foreign_keys'])
# Output: {'course_id': 'courses.id'}
```

### Test 2: Multiple Foreign Keys

```python
db.execute_query("""
    CREATE TABLE enrollments (
        id INT,
        student_id INT,
        course_id INT,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (course_id) REFERENCES courses(id)
    )
""")

desc = db.execute_query("DESCRIBE enrollments")
print(desc['foreign_keys'])
# Output: {'student_id': 'students.id', 'course_id': 'courses.id'}
```

### Test 3: Persistence

```python
# Create database and table
db1 = MiniDB()
db1.execute_query("CREATE TABLE courses (id INT, title STR)")
db1.execute_query("""
    CREATE TABLE students (
        id INT, 
        name STR, 
        course_id INT, 
        FOREIGN KEY (course_id) REFERENCES courses(id)
    )
""")

# Reload database
db2 = MiniDB()
desc = db2.execute_query("DESCRIBE students")
print(desc['foreign_keys'])
# Output: {'course_id': 'courses.id'}  ✅ Persisted!
```

---

## 📊 Current Status

### ✅ Completed Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Parser Support** | ✅ Complete | Regex pattern matches `FOREIGN KEY (col) REFERENCES table(col)` |
| **Metadata Storage** | ✅ Complete | Foreign keys stored in `self.foreign_keys` dictionary |
| **Persistence** | ✅ Complete | Foreign keys saved to and loaded from `metadata.json` |
| **DESCRIBE Output** | ✅ Complete | `DESCRIBE table` shows foreign key relationships |
| **Multiple FKs** | ✅ Complete | Tables can have multiple foreign key constraints |

### 🚧 Pending Features (Future Tasks)

| Feature | Status | Description |
|---------|--------|-------------|
| **Referential Integrity** | 🔜 Pending | Validate foreign key values on INSERT/UPDATE |
| **Cascade Operations** | 🔜 Pending | ON DELETE CASCADE, ON UPDATE CASCADE |
| **FK Validation** | 🔜 Pending | Check that referenced table/column exists |
| **Schema Modification** | 🔜 Pending | ALTER TABLE to add/drop foreign keys |

---

## 📁 File Changes

### Modified Files

1. **`minidb/parser.py`**
   - Added foreign key regex matching
   - Extract local column, referenced table, and referenced column
   - Return `foreign_keys` in parsed result

2. **`minidb/table.py`**
   - Added `foreign_keys` parameter to `__init__`
   - Store foreign keys as instance variable

3. **`minidb/database.py`**
   - Updated `_save_metadata()` to persist foreign keys
   - Updated `_load_metadata()` to load foreign keys
   - Updated `execute_query()` to pass foreign keys on CREATE
   - Updated `_create_table()` to accept foreign keys parameter
   - Updated DESCRIBE output to include foreign keys

### New Files

4. **`test_foreign_keys.py`**
   - Comprehensive test suite for foreign key functionality
   - Tests parsing, storage, persistence, and multiple FKs

---

## 🎯 Example Usage

### Complete Example

```python
from minidb import MiniDB

# Initialize database
db = MiniDB()

# Create schema with foreign keys
db.execute_query("CREATE TABLE departments (id INT, name STR)")
db.execute_query("CREATE TABLE courses (id INT, title STR, dept_id INT, FOREIGN KEY (dept_id) REFERENCES departments(id))")
db.execute_query("CREATE TABLE students (id INT, name STR, course_id INT, FOREIGN KEY (course_id) REFERENCES courses(id))")

# Insert data
db.execute_query("INSERT INTO departments VALUES (1, 'Computer Science')")
db.execute_query("INSERT INTO courses VALUES (1, 'Database Systems', 1)")
db.execute_query("INSERT INTO students VALUES (101, 'Collins', 1)")

# Inspect schema
print(db.execute_query("DESCRIBE courses"))
# Output includes: 'foreign_keys': {'dept_id': 'departments.id'}

print(db.execute_query("DESCRIBE students"))
# Output includes: 'foreign_keys': {'course_id': 'courses.id'}

# Query with JOIN (foreign keys help document relationships)
results = db.execute_query("SELECT * FROM students JOIN courses ON students.course_id = courses.id")
print(results)
```

---

## 🔍 Metadata Example

**`data/metadata.json`:**
```json
{
    "courses": {
        "columns": ["id", "title"],
        "primary_key": "id",
        "column_types": {"id": "int", "title": "str"},
        "unique_columns": [],
        "foreign_keys": {}
    },
    "students": {
        "columns": ["id", "name", "course_id"],
        "primary_key": "id",
        "column_types": {"id": "int", "name": "str", "course_id": "int"},
        "unique_columns": [],
        "foreign_keys": {"course_id": "courses.id"}
    }
}
```

---

## ✅ Task 1 Summary

**Objective**: Update parser to handle FOREIGN KEY syntax and store relationships in table metadata.

**Status**: ✅ **COMPLETE**

**Deliverables**:
1. ✅ Parser extracts `FOREIGN KEY (col) REFERENCES table(col)`
2. ✅ Metadata stored in `self.foreign_keys = {'col': 'table.col'}`
3. ✅ Foreign keys persisted in `metadata.json`
4. ✅ DESCRIBE command shows foreign keys
5. ✅ Comprehensive test suite created

**Next Steps**: Implement referential integrity enforcement (Task 2)

---

*Foreign Key Support implemented for MiniDB - Pesapal Junior Dev Challenge '26*
