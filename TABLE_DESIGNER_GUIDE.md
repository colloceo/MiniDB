# Table Designer UI - Implementation Guide

## ✅ Feature Complete: Visual Table Designer

### Overview

MiniDB now includes a **beautiful, interactive Table Designer** that allows you to visually create database tables with columns, data types, constraints, and foreign key relationships—all through an intuitive web interface.

---

## 🎨 Features

### Core Functionality
- ✅ **Visual Table Creation**: No SQL knowledge required
- ✅ **Dynamic Column Management**: Add/remove columns on the fly
- ✅ **Data Type Selection**: INT, STR, FLOAT support
- ✅ **Constraint Management**: PRIMARY KEY and UNIQUE checkboxes
- ✅ **Foreign Key Relationships**: Visual relationship builder
- ✅ **Real-time SQL Preview**: See generated SQL before execution
- ✅ **Auto-navigation**: Redirects to new table after creation

### UI/UX Features
- ✅ **Modern Bootstrap Design**: Clean, professional interface
- ✅ **Responsive Layout**: Works on desktop and mobile
- ✅ **Interactive Elements**: Smooth animations and transitions
- ✅ **Color-coded Sections**: Visual distinction between columns and FKs
- ✅ **Real-time Validation**: Instant feedback on errors
- ✅ **Copy SQL**: One-click SQL copying to clipboard

---

## 🚀 How to Access

### From Web Interface

1. **Start the Flask app:**
   ```bash
   python app.py
   ```

2. **Navigate to:**
   ```
   http://127.0.0.1:5000/create_table
   ```

3. **Or click:**
   - Sidebar → "Table Designer" (under Analysis section)

---

## 📋 User Guide

### Step 1: Enter Table Name

1. Click on the **Table Name** input field
2. Enter a descriptive name (e.g., `employees`, `products`)
3. Lowercase names are recommended

### Step 2: Add Columns

1. Click **"Add Column"** button (starts with 1 column by default)
2. For each column:
   - **Name**: Enter column name (e.g., `id`, `email`, `salary`)
   - **Type**: Select from dropdown:
     - `INT` - Integer numbers
     - `STR` - Text/strings
     - `FLOAT` - Decimal numbers
   - **Attributes**:
     - ☑️ **Primary Key**: Check for primary key (only one allowed)
     - ☑️ **Unique**: Check to enforce uniqueness

3. Click **trash icon** to remove unwanted columns

### Step 3: Add Foreign Keys (Optional)

1. Click **"Add Relationship"** button
2. For each foreign key:
   - **Local Column**: Select column from your new table
   - **References Table**: Select existing table
   - **References Column**: Select column from referenced table

3. Click **trash icon** to remove relationships

### Step 4: Preview & Create

1. Click **"Preview SQL"** to see generated SQL
2. Click **"Create Table"** to execute
3. Success! You'll be redirected to the new table

---

## 🎯 Example Walkthrough

### Creating an Employees Table with Foreign Key

**Scenario:** Create an `employees` table that references a `departments` table.

#### Step-by-Step:

1. **Table Name:** `employees`

2. **Add Columns:**
   - Column 1:
     - Name: `id`
     - Type: `INT`
     - ✅ Primary Key
   
   - Column 2:
     - Name: `name`
     - Type: `STR`
   
   - Column 3:
     - Name: `email`
     - Type: `STR`
     - ✅ Unique
   
   - Column 4:
     - Name: `dept_id`
     - Type: `INT`

3. **Add Foreign Key:**
   - Local Column: `dept_id`
   - References Table: `departments`
   - References Column: `id`

4. **Generated SQL:**
   ```sql
   CREATE TABLE employees (
       id INT, 
       name STR, 
       email STR UNIQUE, 
       dept_id INT, 
       FOREIGN KEY (dept_id) REFERENCES departments(id)
   )
   ```

5. **Click "Create Table"** ✅

---

## 🔧 Technical Implementation

### Backend (Flask Route)

**File:** `app.py`

```python
@app.route("/create_table", methods=["GET", "POST"])
def create_table():
    """Visual table designer with foreign key support."""
    if request.method == "POST":
        data = request.get_json()
        
        # Extract table name
        table_name = data.get('table_name', '').strip()
        
        # Build SQL from columns
        columns_sql = []
        for col in data.get('columns', []):
            col_def = f"{col['name']} {col['type']}"
            if col.get('is_unique') and not col.get('is_primary'):
                col_def += " UNIQUE"
            columns_sql.append(col_def)
        
        # Build SQL from foreign keys
        foreign_keys_sql = []
        for fk in data.get('foreign_keys', []):
            fk_def = f"FOREIGN KEY ({fk['local_column']}) REFERENCES {fk['ref_table']}({fk['ref_column']})"
            foreign_keys_sql.append(fk_def)
        
        # Combine and execute
        sql_query = f"CREATE TABLE {table_name} ({', '.join(columns_sql + foreign_keys_sql)})"
        result = db.execute_query(sql_query)
        
        return {"success": True, "message": result, "sql": sql_query}
    
    return render_template("create_table.html")
```

### Frontend (JavaScript)

**File:** `templates/create_table.html`

**Key Functions:**

1. **`addColumn()`** - Dynamically adds column input row
2. **`addForeignKey()`** - Dynamically adds FK relationship row
3. **`buildSQL()`** - Constructs SQL string from form data
4. **`createTable()`** - Sends JSON to server via fetch API
5. **`showSQLPreview()`** - Displays SQL in modal
6. **`updateRefColumns()`** - Fetches columns from selected table

**Data Flow:**
```
User Input → JavaScript Collection → JSON Payload → Flask Route → SQL Execution → Response → UI Update
```

---

## 📊 JSON Payload Structure

### Request Format

```json
{
    "table_name": "employees",
    "columns": [
        {
            "name": "id",
            "type": "int",
            "is_primary": true,
            "is_unique": false
        },
        {
            "name": "email",
            "type": "str",
            "is_primary": false,
            "is_unique": true
        }
    ],
    "foreign_keys": [
        {
            "local_column": "dept_id",
            "ref_table": "departments",
            "ref_column": "id"
        }
    ]
}
```

### Response Format

**Success:**
```json
{
    "success": true,
    "message": "Table 'employees' created with columns ['id', 'email', 'dept_id'].",
    "sql": "CREATE TABLE employees (id INT, email STR UNIQUE, dept_id INT, FOREIGN KEY (dept_id) REFERENCES departments(id))"
}
```

**Error:**
```json
{
    "success": false,
    "error": "Error: Table 'employees' already exists.",
    "sql": "CREATE TABLE employees (...)"
}
```

---

## 🎨 UI Components

### Color Scheme

- **Primary Blue** (`#0d6efd`) - Primary actions, headers
- **Success Green** (`#198754`) - Column section
- **Warning Yellow** (`#ffc107`) - Foreign key section
- **Danger Red** (`#dc3545`) - Delete actions
- **Dark Gray** (`#212529`) - Code preview

### Visual Indicators

- **Column Rows**: Light gray background, blue left border
- **FK Rows**: Light yellow background, yellow left border
- **Hover Effects**: Subtle shadow and background change
- **Icons**: Bootstrap Icons for visual clarity

---

## ✅ Features Checklist

### Input Features
- [x] Table name input with validation
- [x] Dynamic column addition/removal
- [x] Column name input
- [x] Data type dropdown (INT, STR, FLOAT)
- [x] Primary key checkbox (single selection enforced)
- [x] Unique constraint checkbox
- [x] Dynamic foreign key addition/removal
- [x] Local column dropdown (auto-populated)
- [x] Reference table dropdown (from existing tables)
- [x] Reference column dropdown (fetched via API)

### UI Features
- [x] Modern Bootstrap 5 design
- [x] Responsive layout
- [x] Smooth animations
- [x] Color-coded sections
- [x] Icon-based navigation
- [x] Real-time SQL preview modal
- [x] Copy SQL to clipboard
- [x] Success/error alerts
- [x] Form reset functionality
- [x] Auto-redirect after creation

### Backend Features
- [x] GET route for form display
- [x] POST route for table creation
- [x] JSON request handling
- [x] SQL query construction
- [x] Database execution
- [x] Error handling
- [x] API endpoint for column fetching

---

## 🚀 Advanced Usage

### Creating Complex Tables

**Example: E-commerce Order System**

```javascript
// Orders table with multiple foreign keys
{
    "table_name": "orders",
    "columns": [
        {"name": "id", "type": "int", "is_primary": true},
        {"name": "order_number", "type": "str", "is_unique": true},
        {"name": "customer_id", "type": "int"},
        {"name": "product_id", "type": "int"},
        {"name": "quantity", "type": "int"},
        {"name": "total_price", "type": "float"}
    ],
    "foreign_keys": [
        {"local_column": "customer_id", "ref_table": "customers", "ref_column": "id"},
        {"local_column": "product_id", "ref_table": "products", "ref_column": "id"}
    ]
}
```

**Generated SQL:**
```sql
CREATE TABLE orders (
    id INT,
    order_number STR UNIQUE,
    customer_id INT,
    product_id INT,
    quantity INT,
    total_price FLOAT,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)
```

---

## 🎯 Best Practices

### Naming Conventions
- ✅ Use lowercase for table names
- ✅ Use snake_case for multi-word names (e.g., `order_items`)
- ✅ Use singular or plural consistently
- ✅ Keep names descriptive but concise

### Column Design
- ✅ Always define a primary key
- ✅ Use appropriate data types
- ✅ Add UNIQUE constraints where needed
- ✅ Name foreign key columns clearly (e.g., `user_id`, `product_id`)

### Foreign Keys
- ✅ Ensure referenced table exists first
- ✅ Reference primary keys when possible
- ✅ Use consistent naming (e.g., `table_id` format)

---

## 📁 File Structure

```
MiniDB/
├── app.py                          # Flask routes (create_table, API)
├── templates/
│   ├── base.html                   # Updated with Table Designer link
│   └── create_table.html           # Table Designer UI
└── minidb/
    ├── parser.py                   # SQL parsing (CREATE TABLE)
    ├── database.py                 # Query execution
    └── table.py                    # Table storage
```

---

## 🎉 Summary

The **Table Designer** provides a complete visual interface for creating database tables without writing SQL. It features:

✅ **Intuitive UI** - Easy to use, no SQL knowledge required  
✅ **Full Feature Support** - Columns, types, constraints, foreign keys  
✅ **Real-time Preview** - See SQL before execution  
✅ **Modern Design** - Beautiful, responsive interface  
✅ **Seamless Integration** - Works with existing MiniDB features  

**Access it now at:** `http://127.0.0.1:5000/create_table`

---

*Table Designer UI implemented for MiniDB - Pesapal Junior Dev Challenge '26*
