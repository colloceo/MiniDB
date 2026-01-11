# MiniDB: A Custom RDBMS from First Principles

**MiniDB** is a lightweight, relational database engine built from scratch in Python. It was designed to demonstrate core database internals—including B-Tree indexing concepts, Hash Joins, and Atomic Persistence—without relying on external database libraries like SQLite.

> **Note:** This project was built for the **Pesapal Junior Dev Challenge '26**.

## 🎥 Demo Video
[Click here to watch the 2-minute System Demo]

## 🏗️ Architecture Overview

The system is organized into four modular layers, designed to mimic a production RDBMS:

```mermaid
graph TD
    UI[UI Layer: Web Dashboard] -->|HTTP POST| API[Flask Routes]
    API -->|SQL String| P[SQL Parser]
    P -->|Command Object| E[Execution Engine]
    E -->|Read/Write| S[Storage Layer]
    S -->|JSONL & Fsync| D[(Data Files)]
    E -.->|O(1) Lookups| H{Hash Index}
```

- **UI Layer**: A Flask-based Admin Dashboard (`app.py`) for visual schema management, data entry, and SQL execution.
- **SQL Parser**: A regex-based engine (`parser.py`) that translates SQL into command objects. Supports `CREATE`, `INSERT`, `SELECT` (with specific columns & nested subqueries), `UPDATE`, `DELETE`, and `JOIN`.
- **Database Engine**: The query coordinator (`database.py`). It replaces naive $O(N^2)$ loops with $O(N)$ Hash Joins and supports recursive subquery resolution.
- **Storage Layer**: Handles data persistence (`table.py`). Uses **JSON Lines (.jsonl)** for streaming I/O and implements Atomic Writes & File Locking.

## 🧠 Key Engineering Decisions

### 1. Scalability: JSON Lines (.jsonl) Storage
Unlike standard JSON arrays which require loading the entire file into memory, MiniDB uses JSON Lines:
- **Streaming Scans**: Rows are yielded one-by-one using Python generators, keeping memory usage constant even for million-row tables.
- **O(1) Persistence**: New records are appended to the end of the file instead of rewriting the entire dataset.
- **Fast Lookups**: The engine uses the file stream to validate unique constraints and perform subquery filters without bulk loading.

### 2. Performance: Hash Joins over Nested Loops
Naive database implementations use Nested Loop Joins ($O(N \times M)$). MiniDB implements a Hash Join algorithm:
- **Build Phase**: Constructs an in-memory Hash Map of the smaller table.
- **Probe Phase**: Scans the larger table and performs $O(1)$ lookups against the map.
- **Result**: Reduces query time from linear growth to near-constant time for lookups.

### 3. Intelligence: Nested Subqueries & Projection
MiniDB supports advanced SQL features usually found in mature engines:
- **Recursive Execution**: Subqueries in `WHERE col IN (...)` clauses are resolved recursively before the outer query runs.
- **Column Projection**: Reduces data transfer by only returning requested columns (e.g., `SELECT name FROM users`) rather than full records.
- **Depth-Limited Scans**: The `LIMIT` clause short-circuits the storage generator, stopping disk reads as soon as the quota is met.

### 4. Reliability: Atomic Writes (Crash Safety)
To prevent data corruption during power failures, MiniDB uses an atomic save strategy:
1. Writes data to a temporary file (`table.tmp`).
2. Forces a hardware flush using `os.fsync`.
3. Performs an atomic swap using `os.replace`.
- **Result**: The database is never in a "half-written" state.

### 5. Consistency: ACID Transactions
MiniDB implements a robust Transaction Manager within the engine:
- **Staging Area**: Changes during a transaction are kept in a session-specific buffer.
- **Atomicity**: Supports `BEGIN`, `COMMIT`, and `ROLLBACK` for multi-statement workflows.
- **Integrity**: Ensures that if a process crashes mid-transaction, no partial data is committed to disk.

### 6. Concurrency: Multi-Process File Locking
To support multiple users/processes, MiniDB implements a global `LockManager`:
- **Pessimistic Locking**: Leverages file-based locks (`.lock` files) to prevent race conditions during write operations.
- **Timeout & Retry**: Includes a retry mechanism with configurable timeouts for busy database scenarios.
- **Stale Lock Cleanup**: Includes logic to detect and remove "dead" locks left behind by crashed processes.

## 🚀 How to Run

### Prerequisites
- Python 3.10+
- Flask (for the web dashboard)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/collins-odhiambo/minidb.git
   cd minidb
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App
1. Start the Web Admin Dashboard:
   ```bash
   python app.py
   ```
   Visit `http://127.0.0.1:5000` to access the UI.

2. To use the CLI (REPL) mode:
   ```bash
   python main.py
   ```

### 🐳 Run with Docker
If you have Docker installed, you can spin up the entire system with a single command:
```bash
docker-compose up --build
```
- **Web UI**: Access at `http://localhost:5000`
- **Persistence**: Database files are automatically mapped to the `./data` folder on your host machine.

## ⚠️ Known Limitations (Prototype Scope)
- **SQL Breadth**: Supports a subset of SQL syntax. Complex multi-level aggregate functions (SUM, AVG) are not yet implemented.
- **Memory Residency**: While storage is streaming, the primary key index is kept in-memory for $O(1)$ speed. Extremely large keyspace may require a B-Tree file-baked index.

## 🙏 Acknowledgements & AI Usage
This project was built as part of the Pesapal Junior Dev Challenge '26.
- **Architecture & Logic**: Designed by Collins Odhiambo.
- **Code Generation**: Boilerplate regex parsing and Flask templates generated by AI (Gemini 2.0).
- **Algorithm Optimization**: AI assisted in refactoring the Join algorithm, implementing the concurrency lock manager, and the JSONL storage migration.
- **Verification**: All code was manually reviewed, tested, and integrated by the author.

Built with code, sweat, and Python.
