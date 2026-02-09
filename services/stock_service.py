from __future__ import annotations

import sqlite3
from typing import Dict, Iterable, List, Optional, Tuple

from database import get_connection


def list_categories() -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    finally:
        conn.close()


def add_category(name: str, description: str = "") -> bool:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (name, description),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_category(category_id: int, name: str, description: str = "") -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE categories SET name=?, description=? WHERE id=?",
            (name, description, category_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_category(category_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM categories WHERE id=?", (category_id,))
        conn.commit()
    finally:
        conn.close()


def list_products(search: Optional[str] = None) -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        if search:
            like = f"%{search}%"
            return conn.execute(
                """
                SELECT p.*, c.name AS category_name
                FROM products p
                LEFT JOIN categories c ON c.id = p.category_id
                WHERE p.name LIKE ? OR p.sku LIKE ?
                ORDER BY p.name
                """,
                (like, like),
            ).fetchall()
        return conn.execute(
            """
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            ORDER BY p.name
            """
        ).fetchall()
    finally:
        conn.close()


def add_product(
    name: str,
    sku: str,
    category_id: Optional[int],
    description: str,
    purchase_price: float,
    selling_price: float,
    quantity: int,
    min_quantity: int,
) -> bool:
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO products (
                name, sku, category_id, description,
                purchase_price, selling_price, quantity, min_quantity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                sku,
                category_id,
                description,
                purchase_price,
                selling_price,
                quantity,
                min_quantity,
            ),
        )
        conn.commit()
        if quantity:
            _log_movement(conn, conn.execute("SELECT last_insert_rowid()").fetchone()[0], quantity, "IN", "Initial stock")
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_product(
    product_id: int,
    name: str,
    sku: str,
    category_id: Optional[int],
    description: str,
    purchase_price: float,
    selling_price: float,
    quantity: int,
    min_quantity: int,
) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE products SET
                name=?, sku=?, category_id=?, description=?,
                purchase_price=?, selling_price=?, quantity=?, min_quantity=?
            WHERE id=?
            """,
            (
                name,
                sku,
                category_id,
                description,
                purchase_price,
                selling_price,
                quantity,
                min_quantity,
                product_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def delete_product(product_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
    finally:
        conn.close()


def list_suppliers() -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    finally:
        conn.close()


def add_supplier(name: str, phone: str, email: str, address: str, company: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO suppliers (name, phone, email, address, company) VALUES (?, ?, ?, ?, ?)",
            (name, phone, email, address, company),
        )
        conn.commit()
    finally:
        conn.close()


def list_customers() -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
    finally:
        conn.close()


def add_customer(name: str, phone: str, email: str, address: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO customers (name, phone, email, address) VALUES (?, ?, ?, ?)",
            (name, phone, email, address),
        )
        conn.commit()
    finally:
        conn.close()


def _log_movement(conn: sqlite3.Connection, product_id: int, quantity: int, movement_type: str, note: str) -> None:
    conn.execute(
        "INSERT INTO stock_movements (product_id, quantity, movement_type, note) VALUES (?, ?, ?, ?)",
        (product_id, quantity, movement_type, note),
    )


def adjust_stock(product_id: int, quantity_delta: int, note: str = "Manual adjust") -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE products SET quantity = quantity + ? WHERE id=?",
            (quantity_delta, product_id),
        )
        _log_movement(conn, product_id, quantity_delta, "ADJUST", note)
        conn.commit()
    finally:
        conn.close()


def record_purchase(
    supplier_id: Optional[int],
    items: Iterable[Tuple[int, int, float]],
) -> int:
    """Items: iterable of (product_id, qty, price). Returns purchase id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO purchases (supplier_id) VALUES (?)",
            (supplier_id,),
        )
        purchase_id = cursor.lastrowid
        total = 0.0
        for product_id, qty, price in items:
            cursor.execute(
                "INSERT INTO purchase_lines (purchase_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (purchase_id, product_id, qty, price),
            )
            cursor.execute(
                "UPDATE products SET quantity = quantity + ?, purchase_price = ? WHERE id=?",
                (qty, price, product_id),
            )
            _log_movement(conn, product_id, qty, "IN", f"Purchase #{purchase_id}")
            total += qty * price
        cursor.execute("UPDATE purchases SET total_amount=? WHERE id=?", (total, purchase_id))
        conn.commit()
        return purchase_id
    finally:
        conn.close()


def record_sale(
    customer_id: Optional[int],
    payment_method: str,
    items: Iterable[Tuple[int, int, float]],
) -> int:
    """Items: iterable of (product_id, qty, price). Returns sale id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # ensure stock availability
        for product_id, qty, _ in items:
            row = cursor.execute(
                "SELECT quantity FROM products WHERE id=?", (product_id,)
            ).fetchone()
            if not row or row["quantity"] < qty:
                raise ValueError("Insufficient stock for product id %s" % product_id)
        cursor.execute(
            "INSERT INTO sales (customer_id, payment_method) VALUES (?, ?)",
            (customer_id, payment_method),
        )
        sale_id = cursor.lastrowid
        total = 0.0
        for product_id, qty, price in items:
            cursor.execute(
                "INSERT INTO sale_lines (sale_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (sale_id, product_id, qty, price),
            )
            cursor.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id=?",
                (qty, product_id),
            )
            _log_movement(conn, product_id, -qty, "OUT", f"Sale #{sale_id}")
            total += qty * price
        cursor.execute("UPDATE sales SET total_amount=? WHERE id=?", (total, sale_id))
        conn.commit()
        return sale_id
    finally:
        conn.close()


def list_stock_movements(limit: int = 200) -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT sm.*, p.name AS product_name
            FROM stock_movements sm
            JOIN products p ON p.id = sm.product_id
            ORDER BY sm.created_at DESC, sm.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()


def metrics() -> Dict[str, float]:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM products) AS products,
                (SELECT COUNT(*) FROM suppliers) AS suppliers,
                (SELECT COUNT(*) FROM customers) AS customers,
                (SELECT COALESCE(SUM(total_amount),0) FROM sales) AS revenue,
                (SELECT COALESCE(SUM(total_amount),0) FROM purchases) AS purchases
            """
        )
        row = cur.fetchone()
        return {
            "products": row["products"],
            "suppliers": row["suppliers"],
            "customers": row["customers"],
            "revenue": row["revenue"],
            "purchases": row["purchases"],
        }
    finally:
        conn.close()


def low_stock() -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM products WHERE quantity <= min_quantity ORDER BY quantity"
        ).fetchall()
    finally:
        conn.close()


def sales_totals(days: int = 14) -> List[Tuple[str, float]]:
    """Return daily sales totals for the last N days (date string, total)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT DATE(date) AS d, COALESCE(SUM(total_amount), 0) AS total
            FROM sales
            WHERE DATE(date) >= DATE('now', ?)
            GROUP BY DATE(date)
            ORDER BY DATE(date)
            """,
            (f"-{days} day",),
        ).fetchall()
        return [(r["d"], float(r["total"])) for r in rows]
    finally:
        conn.close()


def purchase_totals(days: int = 14) -> List[Tuple[str, float]]:
    """Return daily purchase totals for the last N days (date string, total)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT DATE(date) AS d, COALESCE(SUM(total_amount), 0) AS total
            FROM purchases
            WHERE DATE(date) >= DATE('now', ?)
            GROUP BY DATE(date)
            ORDER BY DATE(date)
            """,
            (f"-{days} day",),
        ).fetchall()
        return [(r["d"], float(r["total"])) for r in rows]
    finally:
        conn.close()


def category_choices() -> List[Tuple[int, str]]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, name FROM categories ORDER BY name").fetchall()
        return [(r["id"], r["name"]) for r in rows]
    finally:
        conn.close()


def product_choices() -> List[Tuple[int, str]]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, name, sku FROM products ORDER BY name").fetchall()
        return [(r["id"], f"{r['name']} ({r['sku']})" if r["sku"] else r["name"]) for r in rows]
    finally:
        conn.close()


def supplier_choices() -> List[Tuple[int, str]]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, name, company FROM suppliers ORDER BY name").fetchall()
        return [(r["id"], f"{r['name']} - {r['company']}" if r["company"] else r["name"]) for r in rows]
    finally:
        conn.close()


def customer_choices() -> List[Tuple[int, str]]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, name FROM customers ORDER BY name").fetchall()
        return [(r["id"], r["name"]) for r in rows]
    finally:
        conn.close()
