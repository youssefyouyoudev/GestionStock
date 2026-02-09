import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
from typing import List, Tuple

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:  # matplotlib optional
    MATPLOTLIB_AVAILABLE = False

import database
from services import auth_service, report_service, stock_service


BG_COLOR = "#f7f5fb"
PANEL_COLOR = "#ffffff"
ACCENT = "#6b5b95"
ACCENT_DARK = "#594a7a"
TEXT_COLOR = "#2f2a3d"
SUCCESS = "#3c9d9b"


def apply_theme(root: tk.Tk) -> ttk.Style:
    style = ttk.Style()
    style.theme_use("clam")

    # Base backgrounds
    root.configure(background=BG_COLOR)
    style.configure("TFrame", background=BG_COLOR)
    style.configure("Card.TFrame", background=PANEL_COLOR)
    style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=("Segoe UI", 10))
    style.configure("Card.TLabel", background=PANEL_COLOR, foreground=TEXT_COLOR, font=("Segoe UI", 10, "bold"))

    # Buttons
    style.configure(
        "Accent.TButton",
        background=ACCENT,
        foreground="white",
        padding=8,
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "Accent.TButton",
        background=[("active", ACCENT_DARK)],
        foreground=[("disabled", "#d6d6d6")],
    )

    style.configure(
        "TButton",
        padding=6,
        font=("Segoe UI", 10),
    )

    # Notebook
    style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        padding=(14, 8),
        font=("Segoe UI", 10, "bold"),
    )
    style.map("TNotebook.Tab", background=[("selected", PANEL_COLOR)], foreground=[("selected", TEXT_COLOR)])

    # LabelFrame / cards
    style.configure("TLabelframe", background=PANEL_COLOR, bordercolor="#e3dff2", relief="solid")
    style.configure("TLabelframe.Label", background=PANEL_COLOR, foreground=TEXT_COLOR, font=("Segoe UI", 10, "bold"))

    # Treeview
    style.configure(
        "Mauve.Treeview",
        background="white",
        fieldbackground="white",
        foreground=TEXT_COLOR,
        rowheight=24,
        bordercolor="#e0ddee",
        borderwidth=1,
    )
    style.map("Mauve.Treeview", background=[("selected", ACCENT)], foreground=[("selected", "white")])
    style.configure("Mauve.Treeview.Heading", background=ACCENT, foreground="white", font=("Segoe UI", 10, "bold"))

    return style


class LoginWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Gestion de Stock - Login")
        self.geometry("320x180")
        self.resizable(False, False)

        apply_theme(self)

        container = ttk.Frame(self, padding=16, style="Card.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        ttk.Label(container, text="Welcome", style="Card.TLabel", font=("Segoe UI", 12, "bold")).pack(pady=(0, 8))
        ttk.Label(container, text="Username").pack(pady=(4, 0), anchor="w")
        self.username_entry = ttk.Entry(container, width=28)
        self.username_entry.pack()

        ttk.Label(container, text="Password").pack(pady=(10, 0), anchor="w")
        self.password_entry = ttk.Entry(container, show="*", width=28)
        self.password_entry.pack()

        ttk.Button(container, text="Login", style="Accent.TButton", command=self.login).pack(pady=12, fill=tk.X)
        self.bind("<Return>", lambda _: self.login())
        self.username_entry.focus()

    def login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if auth_service.verify_user(username, password):
            self.destroy()
            app = MainApp(username)
            app.mainloop()
        else:
            messagebox.showerror("Login failed", "Invalid credentials")


class MainApp(tk.Tk):
    def __init__(self, username: str) -> None:
        super().__init__()
        self.title(f"Gestion de Stock - {username}")
        self.geometry("1100x720")
        self.username = username

        self.style = apply_theme(self)

        self.category_choices: List[Tuple[int, str]] = []
        self.product_choices: List[Tuple[int, str]] = []
        self.supplier_choices: List[Tuple[int, str]] = []
        self.customer_choices: List[Tuple[int, str]] = []

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.dashboard_frame = ttk.Frame(notebook)
        self.products_frame = ttk.Frame(notebook)
        self.categories_frame = ttk.Frame(notebook)
        self.suppliers_frame = ttk.Frame(notebook)
        self.customers_frame = ttk.Frame(notebook)
        self.purchases_frame = ttk.Frame(notebook)
        self.sales_frame = ttk.Frame(notebook)
        self.movements_frame = ttk.Frame(notebook)
        self.reports_frame = ttk.Frame(notebook)

        notebook.add(self.dashboard_frame, text="Dashboard")
        notebook.add(self.products_frame, text="Products")
        notebook.add(self.categories_frame, text="Categories")
        notebook.add(self.suppliers_frame, text="Suppliers")
        notebook.add(self.customers_frame, text="Customers")
        notebook.add(self.purchases_frame, text="Purchases")
        notebook.add(self.sales_frame, text="Sales")
        notebook.add(self.movements_frame, text="Stock Movements")
        notebook.add(self.reports_frame, text="Reports")

        self._build_dashboard()
        self._build_categories()
        self._build_products()
        self._build_suppliers()
        self._build_customers()
        self._build_purchases()
        self._build_sales()
        self._build_movements()
        self._build_reports()
        self._refresh_all_choices()

    # Dashboard
    def _build_dashboard(self) -> None:
        stats_frame = ttk.LabelFrame(self.dashboard_frame, text="Stats", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)

        self.stats_vars = {name: tk.StringVar(value="0") for name in ["products", "suppliers", "customers", "revenue", "purchases"]}
        row = 0
        for label, key in [
            ("Products", "products"),
            ("Suppliers", "suppliers"),
            ("Customers", "customers"),
            ("Revenue", "revenue"),
            ("Purchases", "purchases"),
        ]:
            ttk.Label(stats_frame, text=label + ":", width=12).grid(row=row, column=0, sticky="w", padx=5, pady=4)
            ttk.Label(stats_frame, textvariable=self.stats_vars[key]).grid(row=row, column=1, sticky="w", padx=5, pady=4)
            row += 1

        charts_frame = ttk.LabelFrame(self.dashboard_frame, text="Performance", padding=10)
        charts_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10, ipady=4)

        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(8, 3), dpi=100)
            self.axes = self.figure.add_subplot(111)
            self.chart_canvas = FigureCanvasTkAgg(self.figure, master=charts_frame)
            self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            ttk.Label(
                charts_frame,
                text="Install matplotlib to see sales/purchase charts (pip install matplotlib)",
                foreground=ACCENT,
            ).pack(pady=4)

        low_stock_frame = ttk.LabelFrame(self.dashboard_frame, text="Low stock", padding=10)
        low_stock_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        columns = ("id", "name", "qty", "min")
        self.low_tree = ttk.Treeview(low_stock_frame, columns=columns, show="headings", height=8, style="Mauve.Treeview")
        for col, title in zip(columns, ["ID", "Name", "Qty", "Min"]):
            self.low_tree.heading(col, text=title)
            self.low_tree.column(col, width=120 if col == "name" else 80)
        self.low_tree.pack(fill=tk.BOTH, expand=True)
        ttk.Button(self.dashboard_frame, text="Refresh", style="Accent.TButton", command=self.refresh_dashboard).pack(pady=5)
        self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        stats = stock_service.metrics()
        for key, val in stats.items():
            if key in ["revenue", "purchases"]:
                self.stats_vars[key].set(f"{val:.2f}")
            else:
                self.stats_vars[key].set(str(val))
        for i in self.low_tree.get_children():
            self.low_tree.delete(i)
        for r in stock_service.low_stock():
            self.low_tree.insert("", tk.END, values=(r["id"], r["name"], r["quantity"], r["min_quantity"]))
        if MATPLOTLIB_AVAILABLE:
            self.render_charts()

    # Categories
    def _build_categories(self) -> None:
        form = ttk.LabelFrame(self.categories_frame, text="Add category", padding=10)
        form.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(form, text="Name").grid(row=0, column=0, padx=5, pady=5)
        self.cat_name = ttk.Entry(form, width=30)
        self.cat_name.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(form, text="Description").grid(row=1, column=0, padx=5, pady=5)
        self.cat_desc = ttk.Entry(form, width=30)
        self.cat_desc.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(form, text="Add", command=self.add_category).grid(row=0, column=2, rowspan=2, padx=10)

        columns = ("id", "name", "description")
        self.cat_tree = ttk.Treeview(self.categories_frame, columns=columns, show="headings", style="Mauve.Treeview")
        for col in columns:
            self.cat_tree.heading(col, text=col.title())
        self.cat_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.refresh_categories()

    def add_category(self) -> None:
        if not self.cat_name.get():
            messagebox.showwarning("Missing", "Name is required")
            return
        ok = stock_service.add_category(self.cat_name.get(), self.cat_desc.get())
        if not ok:
            messagebox.showerror("Error", "Category already exists")
        self.cat_name.delete(0, tk.END)
        self.cat_desc.delete(0, tk.END)
        self.refresh_categories()

    def refresh_categories(self) -> None:
        for i in self.cat_tree.get_children():
            self.cat_tree.delete(i)
        for r in stock_service.list_categories():
            self.cat_tree.insert("", tk.END, values=(r["id"], r["name"], r["description"]))
        self.refresh_products_categories()

    # Products
    def _build_products(self) -> None:
        form = ttk.LabelFrame(self.products_frame, text="Add / Update", padding=10)
        form.pack(fill=tk.X, padx=10, pady=10)
        labels = ["Name", "SKU", "Description", "Purchase Price", "Selling Price", "Quantity", "Min Qty"]
        self.product_entries = {}
        for idx, label in enumerate(labels):
            ttk.Label(form, text=label).grid(row=idx, column=0, padx=5, pady=3, sticky="w")
            entry = ttk.Entry(form, width=32)
            entry.grid(row=idx, column=1, padx=5, pady=3)
            self.product_entries[label] = entry

        ttk.Label(form, text="Category").grid(row=7, column=0, padx=5, pady=3, sticky="w")
        self.product_category = ttk.Combobox(form, width=30, state="readonly")
        self.product_category.grid(row=7, column=1, padx=5, pady=3)

        ttk.Button(form, text="Add Product", style="Accent.TButton", command=self.add_product).grid(row=0, column=2, rowspan=2, padx=10, pady=4, sticky="n")

        columns = ("id", "name", "sku", "category", "qty", "min", "sell", "buy")
        self.prod_tree = ttk.Treeview(self.products_frame, columns=columns, show="headings", style="Mauve.Treeview")
        for col, title in zip(columns, ["ID", "Name", "SKU", "Category", "Qty", "Min", "Sell", "Buy"]):
            self.prod_tree.heading(col, text=title)
            self.prod_tree.column(col, width=110)
        self.prod_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.refresh_products()

    def refresh_products_categories(self) -> None:
        self._refresh_all_choices()

    def add_product(self) -> None:
        try:
            name = self.product_entries["Name"].get()
            if not name:
                raise ValueError("Name is required")
            sku = self.product_entries["SKU"].get()
            cat_idx = self.product_category.current()
            category_id = self.category_choices[cat_idx][0] if cat_idx != -1 and self.category_choices else None
            description = self.product_entries["Description"].get()
            purchase_price = float(self.product_entries["Purchase Price"].get() or 0)
            selling_price = float(self.product_entries["Selling Price"].get() or 0)
            qty = int(self.product_entries["Quantity"].get() or 0)
            min_qty = int(self.product_entries["Min Qty"].get() or 0)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return
        ok = stock_service.add_product(
            name,
            sku,
            category_id,
            description,
            purchase_price,
            selling_price,
            qty,
            min_qty,
        )
        if not ok:
            messagebox.showerror("Error", "Product name or SKU already exists")
        for entry in self.product_entries.values():
            entry.delete(0, tk.END)
        self.product_category.set("")
        self.refresh_products()

    def refresh_products(self) -> None:
        for i in self.prod_tree.get_children():
            self.prod_tree.delete(i)
        for r in stock_service.list_products():
            self.prod_tree.insert(
                "",
                tk.END,
                values=(
                    r["id"],
                    r["name"],
                    r["sku"],
                    r["category_name"],
                    r["quantity"],
                    r["min_quantity"],
                    r["selling_price"],
                    r["purchase_price"],
                ),
            )
        self.refresh_dashboard()
        self._refresh_all_choices()

    # Suppliers
    def _build_suppliers(self) -> None:
        form = ttk.LabelFrame(self.suppliers_frame, text="Add supplier", padding=10)
        form.pack(fill=tk.X, padx=10, pady=10)
        labels = ["Name", "Phone", "Email", "Address", "Company"]
        self.supplier_entries = {}
        for idx, label in enumerate(labels):
            ttk.Label(form, text=label).grid(row=idx, column=0, padx=5, pady=3, sticky="w")
            entry = ttk.Entry(form, width=30)
            entry.grid(row=idx, column=1, padx=5, pady=3)
            self.supplier_entries[label] = entry
        ttk.Button(form, text="Add", command=self.add_supplier).grid(row=0, column=2, rowspan=2, padx=10)

        columns = ("id", "name", "phone", "email", "address", "company")
        self.sup_tree = ttk.Treeview(self.suppliers_frame, columns=columns, show="headings", style="Mauve.Treeview")
        for col in columns:
            self.sup_tree.heading(col, text=col.title())
            self.sup_tree.column(col, width=140 if col == "name" else 120)
        self.sup_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.refresh_suppliers()

    def add_supplier(self) -> None:
        vals = {k: e.get() for k, e in self.supplier_entries.items()}
        if not vals["Name"]:
            messagebox.showerror("Missing", "Name is required")
            return
        stock_service.add_supplier(
            vals["Name"], vals["Phone"], vals["Email"], vals["Address"], vals["Company"]
        )
        for e in self.supplier_entries.values():
            e.delete(0, tk.END)
        self.refresh_suppliers()
        self._refresh_all_choices()

    def refresh_suppliers(self) -> None:
        for i in self.sup_tree.get_children():
            self.sup_tree.delete(i)
        for r in stock_service.list_suppliers():
            self.sup_tree.insert(
                "",
                tk.END,
                values=(r["id"], r["name"], r["phone"], r["email"], r["address"], r["company"]),
            )

    # Customers
    def _build_customers(self) -> None:
        form = ttk.LabelFrame(self.customers_frame, text="Add customer", padding=10)
        form.pack(fill=tk.X, padx=10, pady=10)
        labels = ["Name", "Phone", "Email", "Address"]
        self.customer_entries = {}
        for idx, label in enumerate(labels):
            ttk.Label(form, text=label).grid(row=idx, column=0, padx=5, pady=3, sticky="w")
            entry = ttk.Entry(form, width=30)
            entry.grid(row=idx, column=1, padx=5, pady=3)
            self.customer_entries[label] = entry
        ttk.Button(form, text="Add", command=self.add_customer).grid(row=0, column=2, rowspan=2, padx=10)

        columns = ("id", "name", "phone", "email", "address")
        self.cust_tree = ttk.Treeview(self.customers_frame, columns=columns, show="headings", style="Mauve.Treeview")
        for col in columns:
            self.cust_tree.heading(col, text=col.title())
        self.cust_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.refresh_customers()

    def add_customer(self) -> None:
        vals = {k: e.get() for k, e in self.customer_entries.items()}
        if not vals["Name"]:
            messagebox.showerror("Missing", "Name is required")
            return
        stock_service.add_customer(vals["Name"], vals["Phone"], vals["Email"], vals["Address"])
        for e in self.customer_entries.values():
            e.delete(0, tk.END)
        self.refresh_customers()
        self._refresh_all_choices()

    def refresh_customers(self) -> None:
        for i in self.cust_tree.get_children():
            self.cust_tree.delete(i)
        for r in stock_service.list_customers():
            self.cust_tree.insert(
                "",
                tk.END,
                values=(r["id"], r["name"], r["phone"], r["email"], r["address"]),
            )

    # Purchases
    def _build_purchases(self) -> None:
        form = ttk.LabelFrame(self.purchases_frame, text="Record purchase", padding=10)
        form.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(form, text="Supplier").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.purchase_supplier = ttk.Combobox(form, width=30, state="readonly")
        self.purchase_supplier.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(form, text="Product").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.purchase_product = ttk.Combobox(form, width=30, state="readonly")
        self.purchase_product.grid(row=1, column=1, padx=5, pady=3)

        ttk.Label(form, text="Quantity").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.purchase_qty = ttk.Entry(form, width=12)
        self.purchase_qty.grid(row=2, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(form, text="Price").grid(row=3, column=0, padx=5, pady=3, sticky="w")
        self.purchase_price = ttk.Entry(form, width=12)
        self.purchase_price.grid(row=3, column=1, padx=5, pady=3, sticky="w")

        ttk.Button(form, text="Add line", style="Accent.TButton", command=self.add_purchase_line).grid(row=0, column=2, rowspan=2, padx=10, pady=4)
        ttk.Button(form, text="Commit purchase", command=self.commit_purchase).grid(row=2, column=2, rowspan=2, padx=10, pady=4)

        self.purchase_lines: list[tuple[int, int, float, str]] = []

        columns = ("product", "qty", "price")
        self.purchase_tree = ttk.Treeview(self.purchases_frame, columns=columns, show="headings", height=6, style="Mauve.Treeview")
        for col in columns:
            self.purchase_tree.heading(col, text=col.title())
        self.purchase_tree.pack(fill=tk.X, padx=10, pady=10)

        self.purchase_log = tk.Text(self.purchases_frame, height=10, bg=PANEL_COLOR, fg=TEXT_COLOR, relief="flat")
        self.purchase_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def add_purchase_line(self) -> None:
        product_idx = self.purchase_product.current()
        if product_idx == -1 or not self.product_choices:
            messagebox.showerror("Missing", "Select a product")
            return
        try:
            qty = int(self.purchase_qty.get())
            price = float(self.purchase_price.get())
        except ValueError:
            messagebox.showerror("Invalid", "Quantity and price are required")
            return
        product_id, product_label = self.product_choices[product_idx]
        self.purchase_lines.append((product_id, qty, price, product_label))
        self.purchase_tree.insert("", tk.END, values=(product_label, qty, price))
        self.purchase_product.set("")
        self.purchase_qty.delete(0, tk.END)
        self.purchase_price.delete(0, tk.END)

    def commit_purchase(self) -> None:
        if not self.purchase_lines:
            messagebox.showwarning("Empty", "Add at least one line")
            return
        supplier_idx = self.purchase_supplier.current()
        supplier_id = self.supplier_choices[supplier_idx][0] if supplier_idx != -1 and self.supplier_choices else None
        items_for_db = [(pid, qty, price) for pid, qty, price, _ in self.purchase_lines]
        purchase_id = stock_service.record_purchase(supplier_id, items_for_db)
        self.purchase_log.insert(tk.END, f"Recorded purchase #{purchase_id}\n")
        self.purchase_lines.clear()
        for i in self.purchase_tree.get_children():
            self.purchase_tree.delete(i)
        self.purchase_supplier.set("")
        self.refresh_products()

    # Sales
    def _build_sales(self) -> None:
        form = ttk.LabelFrame(self.sales_frame, text="Record sale", padding=10)
        form.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(form, text="Customer").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.sale_customer = ttk.Combobox(form, width=30, state="readonly")
        self.sale_customer.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(form, text="Product").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.sale_product = ttk.Combobox(form, width=30, state="readonly")
        self.sale_product.grid(row=1, column=1, padx=5, pady=3)

        ttk.Label(form, text="Quantity").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.sale_qty = ttk.Entry(form, width=12)
        self.sale_qty.grid(row=2, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(form, text="Price").grid(row=3, column=0, padx=5, pady=3, sticky="w")
        self.sale_price = ttk.Entry(form, width=12)
        self.sale_price.grid(row=3, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(form, text="Payment").grid(row=4, column=0, padx=5, pady=3, sticky="w")
        self.sale_payment = ttk.Combobox(form, width=20, state="readonly", values=["cash", "card", "transfer"])
        self.sale_payment.grid(row=4, column=1, padx=5, pady=3, sticky="w")
        self.sale_payment.set("cash")

        ttk.Button(form, text="Add line", style="Accent.TButton", command=self.add_sale_line).grid(row=0, column=2, rowspan=2, padx=10, pady=4)
        ttk.Button(form, text="Commit sale", command=self.commit_sale).grid(row=2, column=2, rowspan=2, padx=10, pady=4)

        self.sale_lines: list[tuple[int, int, float, str]] = []

        columns = ("product", "qty", "price")
        self.sale_tree = ttk.Treeview(self.sales_frame, columns=columns, show="headings", height=6, style="Mauve.Treeview")
        for col in columns:
            self.sale_tree.heading(col, text=col.title())
        self.sale_tree.pack(fill=tk.X, padx=10, pady=10)

        self.sale_log = tk.Text(self.sales_frame, height=10, bg=PANEL_COLOR, fg=TEXT_COLOR, relief="flat")
        self.sale_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def add_sale_line(self) -> None:
        product_idx = self.sale_product.current()
        if product_idx == -1 or not self.product_choices:
            messagebox.showerror("Missing", "Select a product")
            return
        try:
            qty = int(self.sale_qty.get())
            price = float(self.sale_price.get())
        except ValueError:
            messagebox.showerror("Invalid", "Quantity and price are required")
            return
        product_id, product_label = self.product_choices[product_idx]
        self.sale_lines.append((product_id, qty, price, product_label))
        self.sale_tree.insert("", tk.END, values=(product_label, qty, price))
        self.sale_product.set("")
        self.sale_qty.delete(0, tk.END)
        self.sale_price.delete(0, tk.END)

    def commit_sale(self) -> None:
        if not self.sale_lines:
            messagebox.showwarning("Empty", "Add at least one line")
            return
        customer_idx = self.sale_customer.current()
        customer_id = self.customer_choices[customer_idx][0] if customer_idx != -1 and self.customer_choices else None
        payment_method = self.sale_payment.get() or "cash"
        try:
            sale_id = stock_service.record_sale(customer_id, payment_method, [(pid, qty, price) for pid, qty, price, _ in self.sale_lines])
        except ValueError as exc:
            messagebox.showerror("Stock error", str(exc))
            return
        self.sale_log.insert(tk.END, f"Recorded sale #{sale_id}\n")
        self.sale_lines.clear()
        for i in self.sale_tree.get_children():
            self.sale_tree.delete(i)
        self.sale_customer.set("")
        self.refresh_products()

    # Movements
    def _build_movements(self) -> None:
        ttk.Button(self.movements_frame, text="Refresh", style="Accent.TButton", command=self.refresh_movements).pack(pady=5)
        columns = ("id", "product", "qty", "type", "note", "created")
        self.move_tree = ttk.Treeview(self.movements_frame, columns=columns, show="headings", style="Mauve.Treeview")
        for col, title in zip(columns, ["ID", "Product", "Qty", "Type", "Note", "Created"]):
            self.move_tree.heading(col, text=title)
            self.move_tree.column(col, width=140 if col == "note" else 90)
        self.move_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.refresh_movements()

    def refresh_movements(self) -> None:
        for i in self.move_tree.get_children():
            self.move_tree.delete(i)
        for r in stock_service.list_stock_movements():
            self.move_tree.insert(
                "",
                tk.END,
                values=(r["id"], r["product_name"], r["quantity"], r["movement_type"], r["note"], r["created_at"]),
            )

    def render_charts(self) -> None:
        sales = stock_service.sales_totals(14)
        purchases = stock_service.purchase_totals(14)
        # merge dates
        dates = sorted({d for d, _ in sales} | {d for d, _ in purchases})
        if not dates:
            self.axes.clear()
            self.axes.text(0.5, 0.5, "No data yet", ha="center", va="center", color=TEXT_COLOR)
            self.axes.set_xticks([])
            self.axes.set_yticks([])
            self.figure.tight_layout()
            self.chart_canvas.draw_idle()
            return
        sales_map = {d: v for d, v in sales}
        purchase_map = {d: v for d, v in purchases}
        sales_vals = [sales_map.get(d, 0) for d in dates]
        purchase_vals = [purchase_map.get(d, 0) for d in dates]

        x = range(len(dates))
        width = 0.35
        self.axes.clear()
        self.axes.bar([i - width / 2 for i in x], sales_vals, width=width, color=ACCENT, label="Sales")
        self.axes.bar([i + width / 2 for i in x], purchase_vals, width=width, color=SUCCESS, label="Purchases")
        self.axes.set_xticks(list(x))
        self.axes.set_xticklabels(dates, rotation=30, ha="right", fontsize=8)
        self.axes.set_ylabel("Amount")
        self.axes.set_title("Last 14 days")
        self.axes.legend()
        self.figure.tight_layout()
        self.chart_canvas.draw_idle()

    # Reports
    def _build_reports(self) -> None:
        ttk.Label(self.reports_frame, text="Exports go to ./exports/").pack(pady=10)
        ttk.Button(self.reports_frame, text="Export products CSV", style="Accent.TButton", command=self.export_products).pack(pady=5)
        ttk.Button(self.reports_frame, text="Export sales CSV", command=self.export_sales).pack(pady=5)

    def export_products(self) -> None:
        target = Path("exports/products.csv")
        report_service.export_products_csv(target)
        messagebox.showinfo("Exported", f"Saved to {target}")

    def export_sales(self) -> None:
        target = Path("exports/sales.csv")
        report_service.export_sales_csv(target)
        messagebox.showinfo("Exported", f"Saved to {target}")

    def _refresh_all_choices(self) -> None:
        self.category_choices = stock_service.category_choices()
        if hasattr(self, "product_category"):
            self.product_category["values"] = [f"{name} (#{cid})" for cid, name in self.category_choices]
            self.product_category.set("")

        self.product_choices = stock_service.product_choices()
        product_labels = [label for _, label in self.product_choices]
        if hasattr(self, "purchase_product"):
            self.purchase_product["values"] = product_labels
        if hasattr(self, "sale_product"):
            self.sale_product["values"] = product_labels

        self.supplier_choices = stock_service.supplier_choices()
        supplier_labels = [label for _, label in self.supplier_choices]
        if hasattr(self, "purchase_supplier"):
            self.purchase_supplier["values"] = supplier_labels

        self.customer_choices = stock_service.customer_choices()
        customer_labels = [label for _, label in self.customer_choices]
        if hasattr(self, "sale_customer"):
            self.sale_customer["values"] = customer_labels


def run_app() -> None:
    database.init_db()
    LoginWindow().mainloop()


if __name__ == "__main__":
    run_app()
