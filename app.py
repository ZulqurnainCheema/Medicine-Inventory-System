from datetime import date

import pandas as pd
import streamlit as st

import services


st.set_page_config(page_title="Home Decor Inventory", layout="wide")

LOW_STOCK_THRESHOLD = 5


def ensure_auth():
    if "auth_user" not in st.session_state:
        st.session_state["auth_user"] = None


def login_page():
    st.title("Home Decor Inventory Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if services.validate_user(username, password):
            st.session_state["auth_user"] = username
            st.success("Login successful. Loading dashboard...")
            st.rerun()
        else:
            st.error("Invalid credentials")


def kpi_card(label, value):
    st.metric(label, value)


def dashboard_page():
    st.title("Dashboard")
    products = services.list_products()
    suppliers = services.list_suppliers()
    customers = services.list_customers()
    stock = services.get_current_stock()
    low_stock = services.get_low_stock(LOW_STOCK_THRESHOLD)
    purchases = services.get_purchase_report()
    sales = services.get_sales_report()

    total_stock_qty = sum(item["quantity"] for item in stock) if stock else 0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        kpi_card("Products", len(products))
    with col2:
        kpi_card("Suppliers", len(suppliers))
    with col3:
        kpi_card("Customers", len(customers))
    with col4:
        kpi_card("Total Stock", total_stock_qty)
    with col5:
        kpi_card("Low Stock", len(low_stock))
    with col6:
        kpi_card("Expired Batches", len(services.get_expired()))

    if stock:
        stock_df = pd.DataFrame(stock)
        grouped = stock_df.groupby("product_name")["quantity"].sum().reset_index()
        st.subheader("Stock by Product")
        st.bar_chart(grouped, x="product_name", y="quantity")

        cat_grouped = (
            stock_df.groupby("category_name")["quantity"].sum().reset_index().fillna("Unassigned")
        )
        st.subheader("Stock by Category")
        st.bar_chart(cat_grouped, x="category_name", y="quantity")

    st.subheader("Low Stock")
    st.dataframe(pd.DataFrame(low_stock) if low_stock else pd.DataFrame())


    st.subheader("Recent Purchases")
    st.dataframe(pd.DataFrame(purchases) if purchases else pd.DataFrame())

    st.subheader("Recent Sales")
    st.dataframe(pd.DataFrame(sales) if sales else pd.DataFrame())


def products_page():
    st.title("Products")
    root_categories = services.list_categories()
    if not root_categories:
        st.warning("Add categories first.")
        return

    st.subheader("Add Product")
    name = st.text_input("Name", key="add_product_name")
    category_options = {c["name"]: c["category_id"] for c in root_categories}
    category_label = st.selectbox(
        "Category",
        list(category_options.keys()),
        key="add_product_category",
    )
    selected_category_id = category_options[category_label]
    subcategories = services.list_categories(selected_category_id)
    sub_opts = {"(None)": None}
    sub_opts.update({sc["name"]: sc["category_id"] for sc in subcategories})
    sub_label = st.selectbox(
        "Subcategory",
        list(sub_opts.keys()),
        key=f"add_subcat_{selected_category_id}",
    )
    selected_sub_id = sub_opts[sub_label]
    price = st.number_input("Price", min_value=0.0, format="%.2f", key="add_product_price")
    if st.button("Add Product"):
        services.add_product(name, selected_category_id, selected_sub_id, price)
        st.success("Product added")

    products = services.list_products()
    st.subheader("Manage Products")
    if products:
        search_term = st.text_input("Search products", key="product_search")
        filtered = [
            p
            for p in products
            if search_term.lower() in p["name"].lower()
            or search_term.lower() in str(p.get("category_name", "")).lower()
            or search_term.lower() in str(p.get("subcategory_name", "")).lower()
        ]
        st.dataframe(pd.DataFrame(filtered))

        if filtered:
            options = {f"{p['name']} (ID {p['product_id']})": p for p in filtered}
            selected_label = st.selectbox("Select product to edit", list(options.keys()))
            selected = options[selected_label]

            category_options = {c["name"]: c["category_id"] for c in root_categories}
            selected_category_label = next(
                (name for name, cid in category_options.items() if cid == selected["category_id"]),
                list(category_options.keys())[0],
            )
            cat_label = st.selectbox(
                "Category",
                list(category_options.keys()),
                index=list(category_options.keys()).index(selected_category_label),
                key=f"edit_cat_{selected['product_id']}",
            )
            selected_category_id = category_options[cat_label]
            subcategories = services.list_categories(selected_category_id)
            sub_opts = {"(None)": None}
            sub_opts.update({sc["name"]: sc["category_id"] for sc in subcategories})
            default_sub_label = "(None)"
            for name, cid in sub_opts.items():
                if cid == selected.get("subcategory_id"):
                    default_sub_label = name
                    break
            sub_label = st.selectbox(
                "Subcategory",
                list(sub_opts.keys()),
                index=list(sub_opts.keys()).index(default_sub_label),
                key=f"edit_subcat_{selected['product_id']}_{selected_category_id}",
            )
            selected_sub_id = sub_opts[sub_label]

            new_name = st.text_input("Name", value=selected["name"], key=f"edit_name_{selected['product_id']}")
            new_price = st.number_input(
                "Price",
                min_value=0.0,
                value=float(selected["price"]),
                format="%.2f",
                key=f"edit_price_{selected['product_id']}",
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update", key=f"btn_save_prod_{selected['product_id']}"):
                    services.update_product(
                        selected["product_id"],
                        new_name,
                        selected_category_id,
                        selected_sub_id,
                        new_price,
                    )
                    st.success("Updated")
                    st.rerun()
            with col2:
                if st.button("Delete", key=f"btn_delete_prod_{selected['product_id']}"):
                    services.delete_product(selected["product_id"])
                    st.warning("Deleted")
                    st.rerun()
    else:
        st.info("No products found.")


def categories_page():
    st.title("Categories")
    root_categories = services.list_categories()

    with st.form("add_root_category"):
        st.subheader("Add Root Category")
        name = st.text_input("Category name")
        if st.form_submit_button("Add Category"):
            services.add_category(name)
            st.success("Category added")
            st.rerun()

    with st.form("add_subcategory"):
        st.subheader("Add Subcategory")
        if root_categories:
            parent_map = {c["name"]: c["category_id"] for c in root_categories}
            parent_label = st.selectbox("Parent category", list(parent_map.keys()))
            parent_id = parent_map[parent_label]
            sub_name = st.text_input("Subcategory name")
            if st.form_submit_button("Add Subcategory"):
                services.add_category(sub_name, parent_id)
                st.success("Subcategory added")
                st.rerun()
        else:
            st.info("Add a root category first.")

    all_cats = services.list_all_categories()
    st.subheader("Manage Categories")
    if all_cats:
        display = []
        for cat in all_cats:
            display.append(
                {
                    "category_id": cat["category_id"],
                    "name": cat["name"],
                    "parent": cat.get("parent_name"),
                }
            )
        st.dataframe(pd.DataFrame(display))
        options = {
            (f"{cat['parent_name']} -> {cat['name']}" if cat.get("parent_name") else cat["name"]): cat
            for cat in all_cats
        }
        selected_label = st.selectbox("Select category to edit", list(options.keys()))
        selected = options[selected_label]

        new_name = st.text_input(
            "Name", value=selected["name"], key=f"cat_edit_name_{selected['category_id']}"
        )
        parent_choices = {"(None)": None}
        parent_choices.update({c["name"]: c["category_id"] for c in root_categories})
        current_parent_label = "(None)"
        for name, cid in parent_choices.items():
            if cid == selected.get("parent_category_id"):
                current_parent_label = name
                break
        new_parent_label = st.selectbox(
            "Parent category",
            list(parent_choices.keys()),
            index=list(parent_choices.keys()).index(current_parent_label),
            key=f"cat_edit_parent_{selected['category_id']}",
        )
        new_parent_id = parent_choices[new_parent_label]
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Category", key=f"btn_update_cat_{selected['category_id']}"):
                services.update_category(selected["category_id"], new_name, new_parent_id)
                st.success("Updated")
                st.rerun()
        with col2:
            if st.button("Delete Category", key=f"btn_delete_cat_{selected['category_id']}"):
                services.delete_category(selected["category_id"])
                st.warning("Deleted")
                st.rerun()
    else:
        st.info("No categories found.")


def suppliers_page():
    st.title("Suppliers")
    st.subheader("Add Supplier")
    name = st.text_input("Supplier name", key="add_supplier_name")
    contact = st.text_input("Contact info", key="add_supplier_contact")
    if st.button("Add Supplier"):
        services.add_supplier(name, contact)
        st.success("Supplier added")

    sups = services.list_suppliers()
    st.subheader("Manage Suppliers")
    if sups:
        st.dataframe(pd.DataFrame(sups))
        options = {f"{s['name']} (ID {s['supplier_id']})": s for s in sups}
        selected_label = st.selectbox("Select supplier to edit", list(options.keys()))
        sup = options[selected_label]
        new_name = st.text_input("Name", value=sup["name"], key=f"sup_edit_name_{sup['supplier_id']}")
        new_contact = st.text_input(
            "Contact", value=sup["contact_info"], key=f"sup_edit_contact_{sup['supplier_id']}"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Supplier", key=f"btn_sup_update_{sup['supplier_id']}"):
                services.update_supplier(sup["supplier_id"], new_name, new_contact)
                st.success("Updated")
                st.rerun()
        with col2:
            if st.button("Delete Supplier", key=f"btn_sup_delete_{sup['supplier_id']}"):
                services.delete_supplier(sup["supplier_id"])
                st.warning("Deleted")
                st.rerun()
    else:
        st.info("No suppliers found.")


def customers_page():
    st.title("Customers")
    st.subheader("Add Customer")
    name = st.text_input("Customer name", key="add_customer_name")
    if st.button("Add Customer"):
        services.add_customer(name)
        st.success("Customer added")

    customers = services.list_customers()
    st.subheader("Manage Customers")
    if customers:
        st.dataframe(pd.DataFrame(customers))
        options = {f"{c['name']} (ID {c['customer_id']})": c for c in customers}
        selected_label = st.selectbox("Select customer to edit", list(options.keys()))
        selected = options[selected_label]
        new_name = st.text_input("Name", value=selected["name"], key=f"cust_edit_name_{selected['customer_id']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Customer", key=f"btn_cust_update_{selected['customer_id']}"):
                services.update_customer(selected["customer_id"], new_name)
                st.success("Updated")
                st.rerun()
        with col2:
            if st.button("Delete Customer", key=f"btn_cust_delete_{selected['customer_id']}"):
                services.delete_customer(selected["customer_id"])
                st.warning("Deleted")
                st.rerun()
    else:
        st.info("No customers found.")


def purchase_page():
    st.title("Record Purchase")
    products = services.list_products()
    sups = services.list_suppliers()
    if not products or not sups:
        st.warning("Add products and suppliers first.")
        return
    product_option = st.selectbox(
        "Product", [f'{m["name"]} (ID {m["product_id"]})' for m in products]
    )
    sup_option = st.selectbox(
        "Supplier", [f'{s["name"]} (ID {s["supplier_id"]})' for s in sups]
    )
    quantity = st.number_input("Quantity", min_value=1, value=1)
    purchase_date = st.date_input("Purchase date", value=date.today())
    if st.button("Save Purchase"):
        product_id = int(product_option.split("ID")[1].strip(") "))
        sup_id = int(sup_option.split("ID")[1].strip(") "))
        services.add_purchase(product_id, sup_id, int(quantity), None, purchase_date)
        st.success("Purchase recorded and stock updated.")

    st.subheader("Purchase History")
    purchases = services.get_purchase_report()
    st.dataframe(pd.DataFrame(purchases) if purchases else pd.DataFrame())


def sales_page():
    st.title("Record Sale")
    products = services.list_products()
    customers = services.list_customers()
    if not products or not customers:
        st.warning("Add products and customers first.")
        return
    product_option = st.selectbox(
        "Product", [f'{m["name"]} (ID {m["product_id"]})' for m in products]
    )
    cust_option = st.selectbox(
        "Customer", [f'{c["name"]} (ID {c["customer_id"]})' for c in customers]
    )
    quantity = st.number_input("Quantity", min_value=1, value=1)
    sale_date = st.date_input("Sale date", value=date.today())
    if st.button("Save Sale"):
        product_id = int(product_option.split("ID")[1].strip(") "))
        cust_id = int(cust_option.split("ID")[1].strip(") "))
        try:
            services.add_sale(product_id, cust_id, int(quantity), sale_date)
            st.success("Sale recorded and stock reduced.")
        except ValueError as exc:
            st.error(str(exc))

    st.subheader("Sales History")
    sales = services.get_sales_report()
    st.dataframe(pd.DataFrame(sales) if sales else pd.DataFrame())


def reports_page():
    st.title("Reports")
    tabs = st.tabs(
        [
            "Current Stock",
            "Low Stock",
            "Purchases",
            "Sales",
        ]
    )
    with tabs[0]:
        st.dataframe(pd.DataFrame(services.get_current_stock()))
    with tabs[1]:
        st.dataframe(pd.DataFrame(services.get_low_stock(LOW_STOCK_THRESHOLD)))
    with tabs[2]:
        st.dataframe(pd.DataFrame(services.get_purchase_report()))
    with tabs[3]:
        st.dataframe(pd.DataFrame(services.get_sales_report()))


def main():
    ensure_auth()
    if st.session_state["auth_user"] is None:
        login_page()
        return

    st.sidebar.title(f"Welcome, {st.session_state['auth_user']}")
    page = st.sidebar.radio(
        "Navigate",
        (
            "Dashboard",
            "Categories",
            "Products",
            "Suppliers",
            "Customers",
            "Purchase Entry",
            "Sales Entry",
            "Reports",
        ),
    )
    if st.sidebar.button("Logout"):
        st.session_state["auth_user"] = None
        st.experimental_rerun()

    if page == "Dashboard":
        dashboard_page()
    elif page == "Categories":
        categories_page()
    elif page == "Products":
        products_page()
    elif page == "Suppliers":
        suppliers_page()
    elif page == "Customers":
        customers_page()
    elif page == "Purchase Entry":
        purchase_page()
    elif page == "Sales Entry":
        sales_page()
    elif page == "Reports":
        reports_page()


if __name__ == "__main__":
    main()
