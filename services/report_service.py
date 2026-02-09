import csv
from pathlib import Path
from typing import Iterable

from database import get_connection


def export_products_csv(path: Path) -> Path:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, sku, quantity, min_quantity, selling_price, purchase_price FROM products ORDER BY name"
        ).fetchall()
    finally:
        conn.close()

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["id", "name", "sku", "quantity", "min_quantity", "selling_price", "purchase_price"]
        )
        for r in rows:
            writer.writerow([r["id"], r["name"], r["sku"], r["quantity"], r["min_quantity"], r["selling_price"], r["purchase_price"]])
    return path


def export_sales_csv(path: Path) -> Path:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT s.id, s.date, s.total_amount, s.payment_method,
                   c.name AS customer
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            ORDER BY s.date DESC
            """
        ).fetchall()
    finally:
        conn.close()

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "date", "total_amount", "payment_method", "customer"])
        for r in rows:
            writer.writerow([r["id"], r["date"], r["total_amount"], r["payment_method"], r["customer"]])
    return path
