import sqlite3
from pathlib import Path
from typing import Callable

DB_PATH = Path(__file__).resolve().parent / "stock.db"


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with foreign keys enforced."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def run_with_connection(fn: Callable[[sqlite3.Connection], None]) -> None:
    """Utility to run a callback with a managed connection and commit."""
    conn = get_connection()
    try:
        fn(conn)
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not exist and seed an admin user."""
    schema_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT UNIQUE,
        category_id INTEGER,
        description TEXT,
        purchase_price REAL DEFAULT 0,
        selling_price REAL DEFAULT 0,
        quantity INTEGER DEFAULT 0,
        min_quantity INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );

    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT,
        company TEXT
    );

    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT
    );

    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER,
        date TEXT DEFAULT CURRENT_TIMESTAMP,
        total_amount REAL DEFAULT 0,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
    );

    CREATE TABLE IF NOT EXISTS purchase_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        date TEXT DEFAULT CURRENT_TIMESTAMP,
        total_amount REAL DEFAULT 0,
        payment_method TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    );

    CREATE TABLE IF NOT EXISTS sale_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    CREATE TABLE IF NOT EXISTS stock_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        movement_type TEXT NOT NULL,
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    """

    def _init(conn: sqlite3.Connection) -> None:
        conn.executescript(schema_sql)
        # seed admin user if missing
        cur = conn.execute("SELECT COUNT(*) AS c FROM users WHERE username=?", ("admin",))
        if cur.fetchone()[0] == 0:
            # default password: admin
            import hashlib

            pw_hash = hashlib.sha256("admin".encode()).hexdigest()
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                ("admin", pw_hash),
            )

    run_with_connection(_init)


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")
