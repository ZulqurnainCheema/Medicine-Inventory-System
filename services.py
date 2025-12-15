from datetime import date, timedelta

from db import fetch_all, fetch_one, run_query


# CATEGORIES
def list_categories(parent_id=None):
    if parent_id is None:
        return fetch_all("SELECT * FROM categories WHERE parent_category_id IS NULL AND is_deleted = 0")
    return fetch_all(
        "SELECT * FROM categories WHERE parent_category_id = %s AND is_deleted = 0",
        (parent_id,),
    )


def list_all_categories():
    return fetch_all(
        """
        SELECT c.*, parent.name AS parent_name
        FROM categories c
        LEFT JOIN categories parent ON c.parent_category_id = parent.category_id
        WHERE c.is_deleted = 0
        ORDER BY COALESCE(parent.name, c.name), c.name
        """
    )


def add_category(name, parent_category_id=None):
    return run_query(
        "INSERT INTO categories (name, parent_category_id) VALUES (%s, %s)",
        (name, parent_category_id),
        return_lastrowid=True,
    )


def update_category(category_id, name=None, parent_category_id=None):
    fields = []
    params = []
    if name is not None:
        fields.append("name = %s")
        params.append(name)
    if parent_category_id is not None:
        fields.append("parent_category_id = %s")
        params.append(parent_category_id)
    if not fields:
        return 0
    params.append(category_id)
    return run_query(
        f"UPDATE categories SET {', '.join(fields)} WHERE category_id = %s AND is_deleted = 0",
        params,
    )


def delete_category(category_id):
    return run_query(
        "UPDATE categories SET is_deleted = 1 WHERE category_id = %s", (category_id,)
    )


# PRODUCTS
def list_products():
    return fetch_all(
        """
        SELECT p.*, cat.name AS category_name, subcat.name AS subcategory_name
        FROM products p
        LEFT JOIN categories cat ON p.category_id = cat.category_id AND cat.is_deleted = 0
        LEFT JOIN categories subcat ON p.subcategory_id = subcat.category_id AND subcat.is_deleted = 0
        WHERE p.is_deleted = 0
        """
    )


def add_product(name, category_id, subcategory_id, price):
    return run_query(
        "INSERT INTO products (name, category_id, subcategory_id, price) VALUES (%s, %s, %s, %s)",
        (name, category_id, subcategory_id, price),
        return_lastrowid=True,
    )


def update_product(product_id, name=None, category_id=None, subcategory_id=None, price=None):
    fields = []
    params = []
    if name is not None:
        fields.append("name = %s")
        params.append(name)
    if category_id is not None:
        fields.append("category_id = %s")
        params.append(category_id)
    if subcategory_id is not None:
        fields.append("subcategory_id = %s")
        params.append(subcategory_id)
    if price is not None:
        fields.append("price = %s")
        params.append(price)
    if not fields:
        return 0
    params.append(product_id)
    return run_query(
        f"UPDATE products SET {', '.join(fields)} WHERE product_id = %s AND is_deleted = 0",
        params,
    )


def delete_product(product_id):
    return run_query(
        "UPDATE products SET is_deleted = 1 WHERE product_id = %s", (product_id,)
    )


def get_product(product_id):
    return fetch_one(
        "SELECT * FROM products WHERE product_id = %s AND is_deleted = 0",
        (product_id,),
    )


# SUPPLIERS
def list_suppliers():
    return fetch_all("SELECT * FROM suppliers WHERE is_deleted = 0")


def add_supplier(name, contact_info):
    return run_query(
        "INSERT INTO suppliers (name, contact_info) VALUES (%s, %s)",
        (name, contact_info),
        return_lastrowid=True,
    )


def update_supplier(supplier_id, name=None, contact_info=None):
    fields = []
    params = []
    if name is not None:
        fields.append("name = %s")
        params.append(name)
    if contact_info is not None:
        fields.append("contact_info = %s")
        params.append(contact_info)
    if not fields:
        return 0
    params.append(supplier_id)
    return run_query(
        f"UPDATE suppliers SET {', '.join(fields)} WHERE supplier_id = %s AND is_deleted = 0",
        params,
    )


def delete_supplier(supplier_id):
    return run_query(
        "UPDATE suppliers SET is_deleted = 1 WHERE supplier_id = %s", (supplier_id,)
    )


# CUSTOMERS
def list_customers():
    return fetch_all("SELECT * FROM customers WHERE is_deleted = 0")


def add_customer(name):
    return run_query(
        "INSERT INTO customers (name) VALUES (%s)", (name,), return_lastrowid=True
    )


def update_customer(customer_id, name=None):
    if name is None:
        return 0
    return run_query(
        "UPDATE customers SET name = %s WHERE customer_id = %s AND is_deleted = 0",
        (name, customer_id),
    )


def delete_customer(customer_id):
    return run_query(
        "UPDATE customers SET is_deleted = 1 WHERE customer_id = %s", (customer_id,)
    )


# AUTHENTICATION
def validate_user(username, password):
    user = fetch_one(
        "SELECT * FROM users WHERE username = %s AND password = %s",
        (username, password),
    )
    return user is not None


# PURCHASES
def add_purchase(product_id, supplier_id, quantity, expiry_date=None, purchase_date=None, purchase_price=0.0):
    if purchase_date is None:
        purchase_date = date.today()
    # If no expiry provided, align with purchase_date to satisfy NOT NULL constraint.
    if expiry_date is None:
        expiry_date = purchase_date
    purchase_id = run_query(
        "INSERT INTO purchases (product_id, supplier_id, quantity, purchase_date, purchase_price) VALUES (%s, %s, %s, %s, %s)",
        (product_id, supplier_id, quantity, purchase_date, purchase_price),
        return_lastrowid=True,
    )
    upsert_stock(product_id, supplier_id, quantity, expiry_date)
    return purchase_id


# SALES
def add_sale(product_id, customer_id, quantity, sale_date=None, sale_price=0.0):
    if sale_date is None:
        sale_date = date.today()
    deduct_stock(product_id, quantity)
    sale_id = run_query(
        "INSERT INTO sales (product_id, customer_id, quantity, sale_date, sale_price) VALUES (%s, %s, %s, %s, %s)",
        (product_id, customer_id, quantity, sale_date, sale_price),
        return_lastrowid=True,
    )
    return sale_id


# STOCK HELPERS
def upsert_stock(product_id, supplier_id, quantity, expiry_date):
    query = """
        INSERT INTO stock (product_id, supplier_id, quantity, expiry_date)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
    """
    run_query(query, (product_id, supplier_id, quantity, expiry_date))


def deduct_stock(product_id, quantity):
    remaining = quantity
    batches = fetch_all(
        """
        SELECT product_id, supplier_id, quantity, expiry_date
        FROM stock
        WHERE product_id = %s AND quantity > 0
        ORDER BY expiry_date ASC
        """,
        (product_id,),
    )
    for batch in batches:
        if remaining <= 0:
            break
        to_remove = min(batch["quantity"], remaining)
        run_query(
            "UPDATE stock SET quantity = quantity - %s WHERE product_id = %s AND supplier_id = %s AND expiry_date = %s",
            (to_remove, batch["product_id"], batch["supplier_id"], batch["expiry_date"]),
        )
        remaining -= to_remove
    if remaining > 0:
        raise ValueError("Insufficient stock to fulfill sale")


# REPORTS
def get_current_stock():
    return fetch_all(
        """
        SELECT s.product_id,
               m.name AS product_name,
               m.category_id,
               m.subcategory_id,
               cat.name AS category_name,
               subcat.name AS subcategory_name,
               s.supplier_id,
               sup.name AS supplier_name,
               s.quantity,
               s.expiry_date
        FROM stock s
        JOIN products m ON s.product_id = m.product_id AND m.is_deleted = 0
        LEFT JOIN categories cat ON m.category_id = cat.category_id AND cat.is_deleted = 0
        LEFT JOIN categories subcat ON m.subcategory_id = subcat.category_id AND subcat.is_deleted = 0
        JOIN suppliers sup ON s.supplier_id = sup.supplier_id AND sup.is_deleted = 0
        ORDER BY s.expiry_date ASC
        """
    )


def get_low_stock(threshold):
    return fetch_all(
        """
        SELECT s.product_id,
               m.name AS product_name,
               cat.name AS category_name,
               subcat.name AS subcategory_name,
               SUM(s.quantity) AS total_quantity
        FROM stock s
        JOIN products m ON s.product_id = m.product_id AND m.is_deleted = 0
        LEFT JOIN categories cat ON m.category_id = cat.category_id AND cat.is_deleted = 0
        LEFT JOIN categories subcat ON m.subcategory_id = subcat.category_id AND subcat.is_deleted = 0
        GROUP BY s.product_id, m.name, cat.name, subcat.name
        HAVING total_quantity <= %s
        """,
        (threshold,),
    )


def get_near_expiry(days=30):
    today = date.today()
    cutoff = today + timedelta(days=days)
    return fetch_all(
        """
        SELECT s.*, m.name AS product_name, sup.name AS supplier_name, cat.name AS category_name, subcat.name AS subcategory_name
        FROM stock s
        JOIN products m ON s.product_id = m.product_id AND m.is_deleted = 0
        LEFT JOIN categories cat ON m.category_id = cat.category_id AND cat.is_deleted = 0
        LEFT JOIN categories subcat ON m.subcategory_id = subcat.category_id AND subcat.is_deleted = 0
        JOIN suppliers sup ON s.supplier_id = sup.supplier_id AND sup.is_deleted = 0
        WHERE s.expiry_date BETWEEN %s AND %s
        ORDER BY s.expiry_date ASC
        """,
        (today, cutoff),
    )


def get_expired():
    today = date.today()
    return fetch_all(
        """
        SELECT s.*, m.name AS product_name, sup.name AS supplier_name, cat.name AS category_name, subcat.name AS subcategory_name
        FROM stock s
        JOIN products m ON s.product_id = m.product_id AND m.is_deleted = 0
        LEFT JOIN categories cat ON m.category_id = cat.category_id AND cat.is_deleted = 0
        LEFT JOIN categories subcat ON m.subcategory_id = subcat.category_id AND subcat.is_deleted = 0
        JOIN suppliers sup ON s.supplier_id = sup.supplier_id AND sup.is_deleted = 0
        WHERE s.expiry_date < %s
        ORDER BY s.expiry_date ASC
        """,
        (today,),
    )


def get_sales_report():
    return fetch_all(
        """
        SELECT sa.sale_id,
               sa.product_id,
               m.name AS product_name,
               cat.name AS category_name,
               subcat.name AS subcategory_name,
               sa.customer_id,
               cust.name AS customer_name,
               sa.quantity,
               sa.sale_date,
               sa.sale_price
        FROM sales sa
        JOIN products m ON sa.product_id = m.product_id AND m.is_deleted = 0
        LEFT JOIN categories cat ON m.category_id = cat.category_id AND cat.is_deleted = 0
        LEFT JOIN categories subcat ON m.subcategory_id = subcat.category_id AND subcat.is_deleted = 0
        JOIN customers cust ON sa.customer_id = cust.customer_id AND cust.is_deleted = 0
        ORDER BY sa.sale_id DESC
        """
    )


def get_purchase_report():
    return fetch_all(
        """
        SELECT p.purchase_id,
               p.product_id,
               m.name AS product_name,
               cat.name AS category_name,
               subcat.name AS subcategory_name,
               p.supplier_id,
               sup.name AS supplier_name,
               p.quantity,
               p.purchase_date,
               p.purchase_price
        FROM purchases p
        JOIN products m ON p.product_id = m.product_id AND m.is_deleted = 0
        LEFT JOIN categories cat ON m.category_id = cat.category_id AND cat.is_deleted = 0
        LEFT JOIN categories subcat ON m.subcategory_id = subcat.category_id AND subcat.is_deleted = 0
        JOIN suppliers sup ON p.supplier_id = sup.supplier_id AND sup.is_deleted = 0
        ORDER BY p.purchase_id DESC
        """
    )
