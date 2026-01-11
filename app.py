from flask import Flask, request, render_template, redirect, url_for
from minidb import MiniDB

app = Flask(__name__)
db = MiniDB()

# Ensure system tables exist for the demo with strict typing
db.execute_query("CREATE TABLE students (id int, name str, course_id int)")
db.execute_query("CREATE TABLE courses (id int, title str)")

# Seed data if tables are empty
if not db.execute_query("SELECT * FROM courses"):
    db.execute_query("INSERT INTO courses VALUES (1, 'Computer Science')")
    db.execute_query("INSERT INTO courses VALUES (2, 'Electrical Eng')")
    
if not db.execute_query("SELECT * FROM students"):
    db.execute_query("INSERT INTO students VALUES (101, 'Collins', 1)")
    db.execute_query("INSERT INTO students VALUES (102, 'John', 2)")

@app.route("/report")
def report():
    """Relational report demo using JOIN."""
    query = "SELECT * FROM students JOIN courses ON students.course_id = courses.id"
    results = db.execute_query(query)
    return render_template("report.html", results=results)

@app.context_processor
def inject_metadata():
    """Injects table list into all templates for the sidebar."""
    return dict(tables=db.get_tables())

@app.route("/")
def dashboard():
    """Main dashboard showing system stats."""
    return render_template("dashboard.html")

@app.route("/sql-console", methods=["GET", "POST"])
def console():
    """Interactive SQL Console."""
    result_type = None
    result_data = None
    last_query = None
    
    if request.method == "POST":
        last_query = request.form.get("query")
        res = db.execute_query(last_query)
        
        if isinstance(res, list):
            result_type = 'table'
            result_data = res
        elif isinstance(res, str):
            if res.startswith("Error"):
                result_type = 'error'
            else:
                result_type = 'message'
            result_data = res
            
    return render_template("console.html", 
                           result_type=result_type, 
                           result_data=result_data, 
                           last_query=last_query)

@app.route("/table/<table_name>", methods=["GET", "POST"])
def view_table(table_name):
    """Generic table view for any table."""
    msg = request.args.get("msg")
    view = request.args.get("view", "browse") # 'browse' or 'structure'
    
    # Handle student insertion (Legacy support)
    if request.method == "POST" and table_name == "students":
        sid = request.form.get("id")
        name = request.form.get("name")
        grade = request.form.get("grade")
        
        query = f"INSERT INTO students VALUES ({sid}, '{name}', '{grade}')"
        msg = db.execute_query(query)
        
    desc = db.execute_query(f"DESCRIBE {table_name}")
    if isinstance(desc, str) and "Error" in desc:
        return f"Table {table_name} not found.", 404
        
    results = db.execute_query(f"SELECT * FROM {table_name}")
    rows = results if isinstance(results, list) else []
    
    return render_template("browse_table.html", 
                           rows=rows, 
                           columns=desc['columns'], 
                           primary_key=desc['primary_key'],
                           table_name=table_name,
                           active_table=table_name,
                           msg=msg,
                           view=view)

@app.route("/delete/<table_name>/<pk_value>")
def delete_record(table_name, pk_value):
    """Delete a specific record from a table."""
    desc = db.execute_query(f"DESCRIBE {table_name}")
    if isinstance(desc, str) and "Error" in desc:
        return f"Table {table_name} not found.", 404
        
    pk_col = desc['primary_key']
    # Execute the delete query
    query = f"DELETE FROM {table_name} WHERE {pk_col} = {pk_value}"
    msg = db.execute_query(query)
    
    return redirect(url_for("view_table", table_name=table_name, msg=msg))

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
        else:
            msg = "Error: Column name is required"
    
    # Get table description
    desc = db.execute_query(f"DESCRIBE {table_name}")
    if isinstance(desc, str) and "Error" in desc:
        return f"Table {table_name} not found.", 404
    
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
                          active_table=table_name,
                          columns=column_info,
                          msg=msg)

@app.route("/api/table/<table_name>/columns")
def get_table_columns(table_name):
    """API endpoint to get columns of a table for foreign key dropdowns."""
    desc = db.execute_query(f"DESCRIBE {table_name}")
    if isinstance(desc, dict):
        return {"columns": desc['columns']}
    return {"columns": []}, 404

@app.route("/create_table", methods=["GET", "POST"])
def create_table():
    """Visual table designer with foreign key support."""
    if request.method == "POST":
        # Get JSON data from request
        data = request.get_json()
        
        # Extract table name
        table_name = data.get('table_name', '').strip()
        if not table_name:
            return {"success": False, "error": "Table name is required"}, 400
        
        # Build SQL query
        columns_sql = []
        foreign_keys_sql = []
        
        # Process columns
        for col in data.get('columns', []):
            col_name = col.get('name', '').strip()
            col_type = col.get('type', 'str').lower()
            is_primary = col.get('is_primary', False)
            is_unique = col.get('is_unique', False)
            
            if not col_name:
                continue
            
            # Build column definition
            col_def = f"{col_name} {col_type}"
            if is_unique and not is_primary:
                col_def += " UNIQUE"
            
            columns_sql.append(col_def)
        
        # Process foreign keys
        for fk in data.get('foreign_keys', []):
            local_col = fk.get('local_column', '').strip()
            ref_table = fk.get('ref_table', '').strip()
            ref_col = fk.get('ref_column', '').strip()
            
            if local_col and ref_table and ref_col:
                fk_def = f"FOREIGN KEY ({local_col}) REFERENCES {ref_table}({ref_col})"
                foreign_keys_sql.append(fk_def)
        
        # Combine all parts
        all_parts = columns_sql + foreign_keys_sql
        sql_query = f"CREATE TABLE {table_name} ({', '.join(all_parts)})"
        
        # Execute query
        result = db.execute_query(sql_query)
        
        if isinstance(result, str) and "Error" not in result:
            return {"success": True, "message": result, "sql": sql_query}
        else:
            return {"success": False, "error": result, "sql": sql_query}, 400
    
    # GET request - show form
    return render_template("create_table.html")

if __name__ == "__main__":
    print("MiniDB Admin Dashboard starting at http://127.0.0.1:5000")
    app.run(debug=True)
