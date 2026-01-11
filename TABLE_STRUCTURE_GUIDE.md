# Table Structure View - Implementation Guide

## ✅ Feature Complete: Table Structure Management

### Overview

MiniDB now includes a **dedicated Table Structure View** that allows you to inspect existing table schemas and dynamically add new columns without writing SQL. This complements the Table Designer for complete schema management.

---

## 🎨 Features

### Core Functionality
- ✅ **Schema Inspection**: View all columns with types and constraints
- ✅ **Key Indicators**: Visual badges for PRIMARY, UNIQUE, and FOREIGN keys
- ✅ **Foreign Key References**: See which tables/columns are referenced
- ✅ **Add Columns**: Inline form to add new columns via ALTER TABLE
- ✅ **Real-time SQL Preview**: See generated ALTER TABLE command
- ✅ **Default Value Info**: Clear explanation of default values
- ✅ **Seamless Navigation**: Easy switching between Browse and Structure views

### UI/UX Features
- ✅ **Beautiful Design**: Modern gradient header with purple theme
- ✅ **Color-coded Badges**: Visual distinction for different key types
- ✅ **Responsive Layout**: Works on all screen sizes
- ✅ **Hover Effects**: Interactive table rows
- ✅ **Confirmation Dialogs**: Prevents accidental schema changes
- ✅ **Auto-focus**: Column name input focused on page load

---

## 🚀 How to Access

### From Web Interface

1. **Navigate to any table:**
   ```
   http://127.0.0.1:5000/table/<table_name>
   ```

2. **Click the "Structure" tab** at the top

3. **Or directly access:**
   ```
   http://127.0.0.1:5000/table/<table_name>/structure
   ```

---

## 📋 User Guide

### Viewing Table Structure

**The structure view displays:**

1. **Column List Table:**
   - **#** - Column position
   - **Column Name** - Name of the column
   - **Data Type** - INT, STR, or FLOAT
   - **Key** - Constraint type:
     - `PRI` (Yellow badge) - Primary Key
     - `UNI` (Green badge) - Unique constraint
     - `MUL` (Blue badge) - Foreign Key
   - **Details** - Foreign key references (if applicable)

2. **Summary Footer:**
   - Total number of columns

### Adding a New Column

**Step-by-Step:**

1. **Scroll to "Add New Column" section**

2. **Enter Column Name:**
   - Type a descriptive name (e.g., `email`, `age`, `status`)
   - Lowercase with underscores recommended

3. **Select Data Type:**
   - `INT` - Integer numbers
   - `STR` - Text/strings (default)
   - `FLOAT` - Decimal numbers

4. **Preview SQL:**
   - The SQL command updates in real-time as you type
   - Shows: `ALTER TABLE table_name ADD column_name TYPE`

5. **Click "Add Column":**
   - Confirmation dialog appears
   - Confirms you want to add the column
   - Warns about default values

6. **Success:**
   - Column is added to table
   - All existing rows updated with default values
   - Page refreshes to show updated structure

---

## 🎯 Example Usage

### Scenario: Adding Email to Users Table

**Initial Structure:**
```
users table:
- id (INT) - PRI
- name (STR)
```

**Steps:**

1. Navigate to `/table/users/structure`

2. In "Add New Column" form:
   - Column Name: `email`
   - Data Type: `STR`

3. SQL Preview shows:
   ```sql
   ALTER TABLE users ADD email STR
   ```

4. Click "Add Column"

5. Confirm the action

6. **Result:**
   ```
   users table:
   - id (INT) - PRI
   - name (STR)
   - email (STR)  ← NEW!
   ```

**All existing rows now have:**
```json
{"id": 1, "name": "Alice", "email": ""}
{"id": 2, "name": "Bob", "email": ""}
```

---

## 🔧 Technical Implementation

### Backend Route

**File:** `app.py`

```python
@app.route("/table/<table_name>/structure", methods=["GET", "POST"])
def table_structure(table_name):
    """View and modify table structure (schema)."""
    msg = None
    
    # Handle adding new column
    if request.method == "POST":
        col_name = request.form.get("column_name", "").strip()
        col_type = request.form.get("column_type", "str").lower()
        
        if col_name:
            query = f"ALTER TABLE {table_name} ADD {col_name} {col_type}"
            result = db.execute_query(query)
            msg = result
    
    # Get table description
    desc = db.execute_query(f"DESCRIBE {table_name}")
    
    # Prepare column info with key indicators
    column_info = []
    for col in desc['columns']:
        key_type = ""
        if col == desc['primary_key']:
            key_type = "PRI"
        elif col in desc.get('unique_columns', []):
            key_type = "UNI"
        elif col in desc.get('foreign_keys', {}):
            key_type = "MUL"
        
        column_info.append({
            'name': col,
            'type': desc['column_types'].get(col, 'unknown').upper(),
            'key': key_type,
            'is_fk': col in desc.get('foreign_keys', {}),
            'fk_ref': desc.get('foreign_keys', {}).get(col, '')
        })
    
    return render_template("structure.html",
                          table_name=table_name,
                          columns=column_info,
                          msg=msg)
```

### Frontend Template

**File:** `templates/structure.html`

**Key Components:**

1. **Header Section:**
   - Table name with icon
   - Navigation buttons (Browse Data, SQL Console)

2. **Column List Table:**
   - Responsive table with hover effects
   - Color-coded badges for key types
   - Foreign key reference display

3. **Add Column Form:**
   - Column name input
   - Data type dropdown
   - Submit button
   - Info alert about default values

4. **SQL Preview:**
   - Dark code block
   - Real-time updates via JavaScript
   - Shows generated ALTER TABLE command

**JavaScript Features:**

```javascript
// Real-time SQL preview
function updateSQLPreview() {
    const colName = document.getElementById('column_name').value.trim();
    const colType = document.getElementById('column_type').value.toUpperCase();
    const tableName = "{{ table_name }}";
    
    if (colName) {
        preview.textContent = `ALTER TABLE ${tableName} ADD ${colName} ${colType}`;
    }
}

// Confirmation before submission
form.addEventListener('submit', function(e) {
    const confirmed = confirm(
        `Are you sure you want to add column '${colName}' (${colType})?`
    );
    if (!confirmed) {
        e.preventDefault();
    }
});
```

---

## 📊 Key Indicators

### Badge Colors

| Key Type | Badge Color | Icon | Meaning |
|----------|-------------|------|---------|
| **PRI** | Yellow | 🔑 | Primary Key - Unique identifier |
| **UNI** | Green | 🛡️ | Unique Constraint - No duplicates |
| **MUL** | Blue | 🔗 | Foreign Key - References another table |

### Foreign Key Display

When a column is a foreign key, the Details column shows:
```
→ References: table_name.column_name
```

Example:
```
dept_id → References: departments.id
```

---

## ✅ Features Checklist

### Display Features
- [x] Column list with position numbers
- [x] Column names
- [x] Data types (INT, STR, FLOAT)
- [x] Key type badges (PRI, UNI, MUL)
- [x] Foreign key references
- [x] Total column count
- [x] Responsive table layout
- [x] Hover effects

### Add Column Features
- [x] Column name input
- [x] Data type dropdown
- [x] Real-time SQL preview
- [x] Form validation
- [x] Confirmation dialog
- [x] Success/error messages
- [x] Default value information
- [x] Auto-focus on input

### Navigation Features
- [x] Tab navigation (Browse ↔ Structure)
- [x] Breadcrumb links
- [x] Quick access to SQL Console
- [x] Active tab highlighting

---

## 🎨 Design Highlights

### Color Scheme

- **Header Gradient**: Purple gradient (`#667eea` → `#764ba2`)
- **Primary Actions**: Bootstrap blue (`#0d6efd`)
- **Success**: Green (`#198754`)
- **Warning**: Yellow (`#ffc107`)
- **Info**: Light blue (`#0dcaf0`)
- **Code Block**: Dark gray (`#1e1e1e`)

### Visual Effects

- **Card Hover**: Subtle lift and shadow
- **Row Hover**: Light blue background
- **Badge Design**: Rounded with icons
- **Smooth Transitions**: 0.2s ease on all interactions

---

## 🚀 Advanced Usage

### Example: Building a Complete Schema

**Starting with basic table:**
```sql
CREATE TABLE products (id INT, name STR)
```

**Adding columns via Structure View:**

1. Add `price` (FLOAT):
   - Result: All rows get `price: 0.0`

2. Add `description` (STR):
   - Result: All rows get `description: ""`

3. Add `stock` (INT):
   - Result: All rows get `stock: 0`

4. Add `category_id` (INT):
   - Result: All rows get `category_id: 0`
   - Later add foreign key via Table Designer

**Final Structure:**
```
products:
- id (INT) - PRI
- name (STR)
- price (FLOAT)
- description (STR)
- stock (INT)
- category_id (INT) - MUL → categories.id
```

---

## 🎯 Best Practices

### When to Use Structure View

✅ **Good for:**
- Inspecting existing table schemas
- Adding simple columns to existing tables
- Viewing foreign key relationships
- Quick schema modifications

❌ **Not ideal for:**
- Creating new tables (use Table Designer)
- Adding foreign keys (use Table Designer)
- Complex schema changes (use SQL Console)

### Column Naming

- ✅ Use lowercase
- ✅ Use underscores for multi-word names
- ✅ Be descriptive but concise
- ✅ Follow existing naming patterns

### Data Type Selection

- **INT**: IDs, counts, quantities, ages
- **STR**: Names, emails, descriptions, statuses
- **FLOAT**: Prices, percentages, measurements

---

## 📁 File Structure

```
MiniDB/
├── app.py                          # Flask route: table_structure()
├── templates/
│   ├── base.html                   # Navigation (unchanged)
│   ├── browse_table.html           # Updated with Structure tab
│   └── structure.html              # New structure view template
└── minidb/
    ├── parser.py                   # ALTER TABLE parsing
    ├── database.py                 # Query execution
    └── table.py                    # add_column() method
```

---

## 🎉 Summary

The **Table Structure View** provides a complete interface for schema inspection and modification. It features:

✅ **Visual Schema Display** - See all columns, types, and constraints  
✅ **Key Indicators** - Color-coded badges for easy identification  
✅ **Foreign Key Info** - See table relationships at a glance  
✅ **Inline Column Addition** - Add columns without SQL  
✅ **Real-time Preview** - See SQL before execution  
✅ **Beautiful Design** - Modern, responsive interface  

**Access it now:**
```
http://127.0.0.1:5000/table/<table_name>/structure
```

---

*Table Structure View implemented for MiniDB - Pesapal Junior Dev Challenge '26*
