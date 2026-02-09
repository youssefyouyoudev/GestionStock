# Gestion de Stock – Python & SQLite

## 1. Project Overview
Gestion de Stock is a desktop or web-based inventory management system built with Python and SQLite. It manages products, suppliers, customers, purchases, sales, and stock levels in real time. Target users include small and medium businesses, shops, warehouses, pharmacies, restaurants, and freelancers.

## 2. Tech Stack
| Layer          | Technology                         |
| -------------- | ---------------------------------- |
| Language       | Python 3.10+                       |
| Database       | SQLite                             |
| UI (optional)  | Tkinter / PyQt / Streamlit / Flask |
| ORM (optional) | SQLAlchemy                         |
| Reports        | Pandas + Matplotlib                |
| Export         | Excel / PDF                        |
| Architecture   | MVC / Clean Architecture           |

## 3. Core Modules

### Products Module
Fields: id, name, reference (SKU), category, description, purchase_price, selling_price, quantity, minimum_quantity, barcode, created_at.

Features: add/edit/delete, search by name or barcode, low-stock alerts, price update, import/export CSV.

### Categories Module
Fields: id, name, description.

### Suppliers Module
Fields: id, name, phone, email, address, company.

### Customers Module
Fields: id, name, phone, email, address.

### Purchases Module (Stock In)
Fields: id, supplier_id, date, total_amount.

Purchase lines: product_id, quantity, price. Stock updates automatically.

### Sales Module (Stock Out)
Fields: id, customer_id, date, total_amount, payment_method.

### Stock Movements
Types: IN (purchase), OUT (sale), ADJUST (manual correction).

## 4. Database Design (SQLite)

### products table
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    sku TEXT UNIQUE,
    category_id INTEGER,
    purchase_price REAL,
    selling_price REAL,
    quantity INTEGER,
    min_quantity INTEGER
);
```

### purchases
```sql
CREATE TABLE purchases (
    id INTEGER PRIMARY KEY,
    supplier_id INTEGER,
    date TEXT
);
```

### sales
```sql
CREATE TABLE sales (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    date TEXT
);
```

## 5. Python Project Structure
```bash
gestion_stock/
├── database.py
├── models/
│   ├── product.py
│   ├── supplier.py
│   └── sale.py
├── services/
│   ├── stock_service.py
│   └── report_service.py
├── ui/
│   └── app.py
└── main.py
```

## 6. Example Python Code

### Database connection
```python
import sqlite3

def get_db():
    return sqlite3.connect("stock.db")
```

### Add product
```python
def add_product(name, price, qty):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO products (name, selling_price, quantity) VALUES (?, ?, ?)",
        (name, price, qty)
    )
    db.commit()
```

### Sell product
```python
def sell_product(product_id, qty):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT quantity FROM products WHERE id=?", (product_id,))
    stock = cursor.fetchone()[0]

    if stock >= qty:
        cursor.execute(
            "UPDATE products SET quantity = quantity - ? WHERE id=?",
            (qty, product_id)
        )
        db.commit()
```

## 7. Reports and Analytics
Reports: stock (current inventory), sales (daily/monthly), profit (revenue - cost), low stock (below minimum), best sellers (top products).

Using Pandas:
```python
import pandas as pd

df = pd.read_sql("SELECT * FROM products", db)
print(df)
```

## 8. Advanced Features (Pro Version)
Authentication with roles, password hashing, barcode scanning (e.g., webcam), email alerts on low stock, automatic backups to cloud, and multi-warehouse support.

## 9. Real Business Workflow
1) Admin adds products. 2) Purchases increase stock. 3) Sales decrease stock. 4) Reports show profit. 5) Alerts notify low stock.

## 10. UI Options
Desktop: Tkinter (simple), PyQt (professional). Web: Flask + Bootstrap, Django + Tailwind. Mobile: Kivy or a Flutter frontend.

## 11. Security and Data Integrity
Use foreign keys to prevent invalid data, transactions to avoid stock corruption, logs for audit trail, and validation to prevent negative stock.

## 12. Performance
SQLite handles 100k+ products and 1M+ records, suitable for local apps. For scaling, switch to PostgreSQL or MySQL.

## 13. Monetizable SaaS Version
Sell as a subscription, per-shop license, or cloud version. Add multi-tenant support, API (FastAPI), and Stripe payments.

## 14. Portfolio Title
SmartStock – Python Inventory Management System.

## 15. Skills Demonstrated
Real business logic, SQL mastery, Python architecture, CRUD systems, data analysis, and SaaS mindset.

## Final Summary
A real-world inventory system that is buildable in 7–14 days, fits freelance client needs, shines in a portfolio, and can evolve into a SaaS.

## Running the Tkinter app (this repo)
1) Install Python 3.10+.
2) From the project root, run `python -m venv .venv` then activate it.
3) Install requirements (only stdlib used; optional: `pip install pandas matplotlib` if you extend reports).
4) Start the app: `python main.py`. Default login: admin / admin.
5) Data is stored in `stock.db` (SQLite). Exports are written to `exports/`.
"# GestionStock" 
