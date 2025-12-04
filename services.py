from datetime import date, timedelta

from db import fetch_all, fetch_one, run_query


# MEDICINES
def list_medicines():
    return fetch_all("SELECT * FROM medicines WHERE is_deleted = 0")


def add_medicine(name, category, price):
    return run_query(
        "INSERT INTO medicines (name, category, price) VALUES (%s, %s, %s)",
        (name, category, price),
        return_lastrowid=True,
    )


def update_medicine(medicine_id, name=None, category=None, price=None):
    fields = []
    params = []
    if name is not None:
        fields.append("name = %s")
        params.append(name)
    if category is not None:
        fields.append("category = %s")
        params.append(category)
    if price is not None:
        fields.append("price = %s")
        params.append(price)
    if not fields:
        return 0
    params.append(medicine_id)
    return run_query(
        f"UPDATE medicines SET {', '.join(fields)} WHERE medicine_id = %s AND is_deleted = 0",
        params,
    )


def delete_medicine(medicine_id):
    return run_query(
        "UPDATE medicines SET is_deleted = 1 WHERE medicine_id = %s", (medicine_id,)
    )


def get_medicine(medicine_id):
    return fetch_one(
        "SELECT * FROM medicines WHERE medicine_id = %s AND is_deleted = 0",
        (medicine_id,),
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
def add_purchase(medicine_id, supplier_id, quantity, expiry_date, purchase_date=None):
    if purchase_date is None:
        purchase_date = date.today()
    purchase_id = run_query(
        "INSERT INTO purchases (medicine_id, supplier_id, quantity, purchase_date) VALUES (%s, %s, %s, %s)",
        (medicine_id, supplier_id, quantity, purchase_date),
        return_lastrowid=True,
    )
    upsert_stock(medicine_id, supplier_id, quantity, expiry_date)
    return purchase_id


# SALES
def add_sale(medicine_id, customer_id, quantity, sale_date=None):
    if sale_date is None:
        sale_date = date.today()
    deduct_stock(medicine_id, quantity)
    sale_id = run_query(
        "INSERT INTO sales (medicine_id, customer_id, quantity, sale_date) VALUES (%s, %s, %s, %s)",
        (medicine_id, customer_id, quantity, sale_date),
        return_lastrowid=True,
    )
    return sale_id


# STOCK HELPERS
def upsert_stock(medicine_id, supplier_id, quantity, expiry_date):
    query = """
        INSERT INTO stock (medicine_id, supplier_id, quantity, expiry_date)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
    """
    run_query(query, (medicine_id, supplier_id, quantity, expiry_date))


def deduct_stock(medicine_id, quantity):
    remaining = quantity
    batches = fetch_all(
        """
        SELECT medicine_id, supplier_id, quantity, expiry_date
        FROM stock
        WHERE medicine_id = %s AND quantity > 0
        ORDER BY expiry_date ASC
        """,
        (medicine_id,),
    )
    for batch in batches:
        if remaining <= 0:
            break
        to_remove = min(batch["quantity"], remaining)
        run_query(
            "UPDATE stock SET quantity = quantity - %s WHERE medicine_id = %s AND supplier_id = %s AND expiry_date = %s",
            (to_remove, batch["medicine_id"], batch["supplier_id"], batch["expiry_date"]),
        )
        remaining -= to_remove
    if remaining > 0:
        raise ValueError("Insufficient stock to fulfill sale")


# REPORTS
def get_current_stock():
    return fetch_all(
        """
        SELECT s.medicine_id,
               m.name AS medicine_name,
               s.supplier_id,
               sup.name AS supplier_name,
               s.quantity,
               s.expiry_date
        FROM stock s
        JOIN medicines m ON s.medicine_id = m.medicine_id AND m.is_deleted = 0
        JOIN suppliers sup ON s.supplier_id = sup.supplier_id AND sup.is_deleted = 0
        ORDER BY s.expiry_date ASC
        """
    )


def get_low_stock(threshold):
    return fetch_all(
        """
        SELECT s.medicine_id,
               m.name AS medicine_name,
               SUM(s.quantity) AS total_quantity
        FROM stock s
        JOIN medicines m ON s.medicine_id = m.medicine_id AND m.is_deleted = 0
        GROUP BY s.medicine_id, m.name
        HAVING total_quantity <= %s
        """,
        (threshold,),
    )


def get_near_expiry(days=30):
    today = date.today()
    cutoff = today + timedelta(days=days)
    return fetch_all(
        """
        SELECT s.*, m.name AS medicine_name, sup.name AS supplier_name
        FROM stock s
        JOIN medicines m ON s.medicine_id = m.medicine_id AND m.is_deleted = 0
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
        SELECT s.*, m.name AS medicine_name, sup.name AS supplier_name
        FROM stock s
        JOIN medicines m ON s.medicine_id = m.medicine_id AND m.is_deleted = 0
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
               sa.medicine_id,
               m.name AS medicine_name,
               sa.customer_id,
               c.name AS customer_name,
               sa.quantity,
               sa.sale_date
        FROM sales sa
        JOIN medicines m ON sa.medicine_id = m.medicine_id AND m.is_deleted = 0
        JOIN customers c ON sa.customer_id = c.customer_id AND c.is_deleted = 0
        ORDER BY sa.sale_id DESC
        """
    )


def get_purchase_report():
    return fetch_all(
        """
        SELECT p.purchase_id,
               p.medicine_id,
               m.name AS medicine_name,
               p.supplier_id,
               sup.name AS supplier_name,
               p.quantity,
               p.purchase_date
        FROM purchases p
        JOIN medicines m ON p.medicine_id = m.medicine_id AND m.is_deleted = 0
        JOIN suppliers sup ON p.supplier_id = sup.supplier_id AND sup.is_deleted = 0
        ORDER BY p.purchase_id DESC
        """
    )
