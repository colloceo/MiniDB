import os
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
    msg = request.args.get("msg")
    
    # Get all tables
    tables = db.get_tables()
    total_tables = len(tables)
    
    # Calculate total records
    total_records = 0
    for table_name in tables:
        try:
            data = db.execute_query(f"SELECT * FROM {table_name}")
            if isinstance(data, list):
                total_records += len(data)
        except:
            pass
    
    # Calculate storage size
    total_size_bytes = 0
    last_modified = 0
    
    if os.path.exists(db.data_dir):
        for filename in os.listdir(db.data_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(db.data_dir, filename)
                try:
                    # Get file size
                    total_size_bytes += os.path.getsize(file_path)
                    # Get last modified time
                    mod_time = os.path.getmtime(file_path)
                    if mod_time > last_modified:
                        last_modified = mod_time
                except:
                    pass
    
    # Convert bytes to KB
    total_size_kb = round(total_size_bytes / 1024, 2)
    
    # Format last active time
    if last_modified > 0:
        from datetime import datetime
        last_active = datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')
    else:
        last_active = "Never"
    
    return render_template("dashboard.html",
                          total_tables=total_tables,
                          total_records=total_records,
                          disk_usage=total_size_kb,
                          last_active=last_active,
                          msg=msg)

@app.route("/sql-console", methods=["GET", "POST"])
def console():
    """Interactive SQL Console."""
    result_type = None
    result_data = None
    last_query = None
    execution_results = []  # Track results of multiple statements
    
    if request.method == "POST":
        last_query = request.form.get("query", "").strip()
        
        # Split by semicolon to support multiple statements
        statements = [stmt.strip() for stmt in last_query.split(';') if stmt.strip()]
        
        if len(statements) == 0:
            result_type = 'error'
            result_data = "Error: No SQL statement provided"
        elif len(statements) == 1:
            # Single statement - original behavior
            res = db.execute_query(statements[0])
            
            if isinstance(res, list):
                result_type = 'table'
                result_data = res
            elif isinstance(res, str):
                if res.startswith("Error") or "Error" in res:
                    result_type = 'error'
                else:
                    result_type = 'message'
                result_data = res
            elif isinstance(res, dict):
                # DESCRIBE returns dict
                result_type = 'dict'
                result_data = res
        else:
            # Multiple statements - execute sequentially
            for i, stmt in enumerate(statements, 1):
                try:
                    res = db.execute_query(stmt)
                    
                    # Track each result
                    execution_results.append({
                        'number': i,
                        'statement': stmt,
                        'result': res,
                        'type': 'table' if isinstance(res, list) else 'message' if isinstance(res, str) else 'dict'
                    })
                except Exception as e:
                    execution_results.append({
                        'number': i,
                        'statement': stmt,
                        'result': f"Error: {e}",
                        'type': 'error'
                    })
                    # Continue executing remaining statements
            
            result_type = 'multi'
            result_data = execution_results
            
    return render_template("console.html", 
                           result_type=result_type, 
                           result_data=result_data, 
                           last_query=last_query,
                           execution_results=execution_results)

@app.route("/table/<table_name>", methods=["GET"])
def view_table(table_name):
    """Generic table view for any table."""
    msg = request.args.get("msg")
    view = request.args.get("view", "browse") # 'browse' or 'structure'
    
    desc = db.execute_query(f"DESCRIBE {table_name}")
    if isinstance(desc, str) and "Error" in desc:
        return f"Table {table_name} not found.", 404
        
    results = db.execute_query(f"SELECT * FROM {table_name}")
    rows = results if isinstance(results, list) else []
    
    # Enrich column info with types
    column_defs = []
    for col in desc['columns']:
        column_defs.append({
            'name': col,
            'type': desc['column_types'].get(col, 'str').upper()
        })
    
    return render_template("browse_table.html", 
                           rows=rows, 
                           columns=desc['columns'], 
                           column_defs=column_defs,
                           primary_key=desc['primary_key'],
                           table_name=table_name,
                           active_table=table_name,
                           msg=msg,
                           view=view)

@app.route("/table/<table_name>/insert", methods=["POST"])
def insert_record(table_name):
    """Insert a new record into a table."""
    desc = db.execute_query(f"DESCRIBE {table_name}")
    if isinstance(desc, str) and "Error" in desc:
        return f"Table {table_name} not found.", 404
        
    columns = []
    params = []
    
    for col in desc['columns']:
        val = request.form.get(col)
        if val is not None and val != "":
            columns.append(col)
            # Handle types for parameters
            col_type = desc['column_types'].get(col, 'str').lower()
            if col_type == 'int':
                try: params.append(int(val))
                except: params.append(0)
            elif col_type == 'float':
                try: params.append(float(val))
                except: params.append(0.0)
            else:
                params.append(val)
    
    if not columns:
        return redirect(url_for("view_table", table_name=table_name, msg="Error: No data provided"))
        
    placeholders = ", ".join(["?" for _ in range(len(params))])
    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    msg = db.execute_query(query, tuple(params))
    
    return redirect(url_for("view_table", table_name=table_name, msg=msg))

@app.route("/table/<table_name>/update", methods=["POST"])
def update_record(table_name):
    """Update an existing record in a table."""
    desc = db.execute_query(f"DESCRIBE {table_name}")
    if isinstance(desc, str) and "Error" in desc:
        return f"Table {table_name} not found.", 404
        
    pk_col = desc['primary_key']
    pk_val = request.form.get(pk_col)
    
    if not pk_val:
        return redirect(url_for("view_table", table_name=table_name, msg="Error: Primary key missing"))
        
    updates = []
    params = []
    for col in desc['columns']:
        if col == pk_col:
            continue
            
        val = request.form.get(col)
        if val is not None:
            col_type = desc['column_types'].get(col, 'str').lower()
            updates.append(f"{col} = ?")
            if val == "":
                if col_type == 'int': params.append(0)
                elif col_type == 'float': params.append(0.0)
                else: params.append("")
            else:
                if col_type == 'int': 
                    try: params.append(int(val))
                    except: params.append(0)
                elif col_type == 'float':
                    try: params.append(float(val))
                    except: params.append(0.0)
                else: 
                    params.append(val)
    
    if not updates:
        return redirect(url_for("view_table", table_name=table_name, msg="No changes made"))
        
    # Build where clause with PK
    pk_type = desc['column_types'].get(pk_col, 'int').lower()
    try:
        pk_val_typed = int(pk_val) if pk_type in ['int', 'float'] else pk_val
    except:
        pk_val_typed = pk_val

    query = f"UPDATE {table_name} SET {', '.join(updates)} WHERE {pk_col} = ?"
    params.append(pk_val_typed)
    
    msg = db.execute_query(query, tuple(params))
    
    return redirect(url_for("view_table", table_name=table_name, msg=msg))

@app.route("/delete/<table_name>/<pk_value>")
def delete_record(table_name, pk_value):
    """Delete a specific record from a table."""
    desc = db.execute_query(f"DESCRIBE {table_name}")
    if isinstance(desc, str) and "Error" in desc:
        return f"Table {table_name} not found.", 404
        
    pk_col = desc['primary_key']
    pk_type = desc['column_types'].get(pk_col, 'int').lower()
    
    try:
        pk_val_typed = int(pk_value) if pk_type in ['int', 'float'] else pk_value
    except:
        pk_val_typed = pk_value

    # Execute the delete query using parameters
    query = f"DELETE FROM {table_name} WHERE {pk_col} = ?"
    msg = db.execute_query(query, (pk_val_typed,))
    
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
    return {" columns": []}, 404

@app.route("/table/<table_name>/drop_column", methods=["POST"])
def drop_column(table_name):
    """Drop a column from a table."""
    column_name = request.form.get("column_name")
    
    try:
        result = db.execute_query(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
        
        if "Error" in str(result):
            msg = f"Error: {result}"
        else:
            msg = f"Success: {result}"
    except Exception as e:
        msg = f"Error: {e}"
    
    return redirect(url_for('table_structure', table_name=table_name, msg=msg))

@app.route("/table/<table_name>/rename_column", methods=["POST"])
def rename_column(table_name):
    """Rename a column in a table."""
    old_name = request.form.get("old_name")
    new_name = request.form.get("new_name")
    
    try:
        result = db.execute_query(f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}")
        
        if "Error" in str(result):
            msg = f"Error: {result}"
        else:
            msg = f"Success: {result}"
    except Exception as e:
        msg = f"Error: {e}"
    
    return redirect(url_for('table_structure', table_name=table_name, msg=msg))

@app.route("/table/<table_name>/operations")
def table_operations(table_name):
    """Table operations page (rename, delete)."""
    msg = request.args.get("msg")
    
    # Get table info
    desc = db.execute_query(f"DESCRIBE {table_name}")
    data = db.execute_query(f"SELECT * FROM {table_name}")
    
    column_count = len(desc['columns']) if isinstance(desc, dict) else 0
    row_count = len(data) if isinstance(data, list) else 0
    primary_key = desc.get('primary_key', 'id') if isinstance(desc, dict) else 'id'
    
    return render_template("operations.html",
                          table_name=table_name,
                          active_table=table_name,
                          column_count=column_count,
                          row_count=row_count,
                          primary_key=primary_key,
                          msg=msg)

@app.route("/table/<table_name>/rename", methods=["POST"])
def rename_table(table_name):
    """Rename a table."""
    new_name = request.form.get("new_name")
    
    try:
        result = db.execute_query(f"ALTER TABLE {table_name} RENAME TO {new_name}")
        
        if "Error" in str(result):
            msg = f"Error: {result}"
            return redirect(url_for('table_operations', table_name=table_name, msg=msg))
        else:
            msg = f"Success: {result}"
            # Redirect to the new table name
            return redirect(url_for('view_table', table_name=new_name, msg=msg))
    except Exception as e:
        msg = f"Error: {e}"
        return redirect(url_for('table_operations', table_name=table_name, msg=msg))

@app.route("/table/<table_name>/delete", methods=["POST"])
def delete_table(table_name):
    """Delete a table."""
    try:
        result = db.execute_query(f"DROP TABLE {table_name}")
        
        if "Error" in str(result):
            msg = f"Error: {result}"
            return redirect(url_for('table_operations', table_name=table_name, msg=msg))
        else:
            msg = f"Success: {result}"
            # Redirect to dashboard after deletion
            return redirect(url_for('dashboard', msg=msg))
    except Exception as e:
        msg = f"Error: {e}"
        return redirect(url_for('dashboard', msg=msg))

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

@app.route("/documentation")
def documentation():
    """Documentation page with SQL reference and examples."""
    return render_template("documentation.html")

if __name__ == "__main__":
    print("MiniDB Admin Dashboard starting at http://127.0.0.1:5000")
    app.run(debug=True)
