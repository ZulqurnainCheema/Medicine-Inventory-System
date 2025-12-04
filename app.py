from datetime import date

import pandas as pd
import streamlit as st

import services


st.set_page_config(page_title="Medical Inventory System", layout="wide")

LOW_STOCK_THRESHOLD = 5


def ensure_auth():
    if "auth_user" not in st.session_state:
        st.session_state["auth_user"] = None


def login_page():
    st.title("Medical Inventory Login")
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
    medicines = services.list_medicines()
    suppliers = services.list_suppliers()
    customers = services.list_customers()
    stock = services.get_current_stock()
    low_stock = services.get_low_stock(LOW_STOCK_THRESHOLD)
    expired = services.get_expired()

    total_stock_qty = sum(item["quantity"] for item in stock) if stock else 0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        kpi_card("Medicines", len(medicines))
    with col2:
        kpi_card("Suppliers", len(suppliers))
    with col3:
        kpi_card("Customers", len(customers))
    with col4:
        kpi_card("Total Stock", total_stock_qty)
    with col5:
        kpi_card("Low Stock", len(low_stock))
    with col6:
        kpi_card("Expired Batches", len(expired))

    if stock:
        stock_df = pd.DataFrame(stock)
        grouped = stock_df.groupby("medicine_name")["quantity"].sum().reset_index()
        st.subheader("Stock by Medicine")
        st.bar_chart(grouped, x="medicine_name", y="quantity")

    st.subheader("Low Stock")
    st.dataframe(pd.DataFrame(low_stock) if low_stock else pd.DataFrame())

    st.subheader("Near Expiry (next 30 days)")
    near = services.get_near_expiry(30)
    st.dataframe(pd.DataFrame(near) if near else pd.DataFrame())

    st.subheader("Expired Medicines")
    st.dataframe(pd.DataFrame(expired) if expired else pd.DataFrame())


def medicines_page():
    st.title("Medicines")
    with st.form("add_medicine"):
        st.subheader("Add Medicine")
        name = st.text_input("Name")
        category = st.text_input("Category")
        price = st.number_input("Price", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Add")
        if submitted:
            services.add_medicine(name, category, price)
            st.success("Medicine added")

    meds = services.list_medicines()
    st.subheader("Manage Medicines")
    if meds:
        meds_df = pd.DataFrame(meds)
        st.dataframe(meds_df)
        ids = {f'{m["name"]} (ID {m["medicine_id"]})': m for m in meds}
        selected_label = st.selectbox("Select medicine to edit", list(ids.keys()))
        selected = ids[selected_label]
        new_name = st.text_input(
            "Edit name",
            value=selected["name"],
            key=f"edit_name_{selected['medicine_id']}",
        )
        new_cat = st.text_input(
            "Edit category",
            value=str(selected["category"]),
            key=f"edit_category_{selected['medicine_id']}",
        )
        new_price = st.number_input(
            "Edit price",
            min_value=0.0,
            value=float(selected["price"]),
            format="%.2f",
            key=f"edit_price_{selected['medicine_id']}",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Medicine"):
                services.update_medicine(
                    selected["medicine_id"], new_name, new_cat, new_price
                )
                st.success("Updated")
                st.rerun()
        with col2:
            if st.button("Delete Medicine"):
                services.delete_medicine(selected["medicine_id"])
                st.warning("Deleted")
                st.rerun()
    else:
        st.info("No medicines found.")


def suppliers_page():
    st.title("Suppliers")
    with st.form("add_supplier"):
        st.subheader("Add Supplier")
        name = st.text_input("Supplier name")
        contact = st.text_input("Contact info")
        if st.form_submit_button("Add"):
            services.add_supplier(name, contact)
            st.success("Supplier added")

    sups = services.list_suppliers()
    st.subheader("Manage Suppliers")
    if sups:
        st.dataframe(pd.DataFrame(sups))
        ids = {f'{s["name"]} (ID {s["supplier_id"]})': s for s in sups}
        selected_label = st.selectbox("Select supplier to edit", list(ids.keys()))
        selected = ids[selected_label]
        new_name = st.text_input(
            "Edit name",
            value=selected["name"],
            key=f"sup_edit_name_{selected['supplier_id']}",
        )
        new_contact = st.text_input(
            "Edit contact",
            value=selected["contact_info"],
            key=f"sup_edit_contact_{selected['supplier_id']}",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Supplier"):
                services.update_supplier(
                    selected["supplier_id"], new_name, new_contact
                )
                st.success("Updated")
                st.rerun()
        with col2:
            if st.button("Delete Supplier"):
                services.delete_supplier(selected["supplier_id"])
                st.warning("Deleted")
                st.rerun()
    else:
        st.info("No suppliers found.")


def customers_page():
    st.title("Customers")
    with st.form("add_customer"):
        st.subheader("Add Customer")
        name = st.text_input("Customer name")
        if st.form_submit_button("Add"):
            services.add_customer(name)
            st.success("Customer added")

    customers = services.list_customers()
    st.subheader("Manage Customers")
    if customers:
        st.dataframe(pd.DataFrame(customers))
        ids = {f'{c["name"]} (ID {c["customer_id"]})': c for c in customers}
        selected_label = st.selectbox("Select customer to edit", list(ids.keys()))
        selected = ids[selected_label]
        new_name = st.text_input(
            "Edit name",
            value=selected["name"],
            key=f"cust_edit_name_{selected['customer_id']}",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Customer"):
                services.update_customer(selected["customer_id"], new_name)
                st.success("Updated")
                st.rerun()
        with col2:
            if st.button("Delete Customer"):
                services.delete_customer(selected["customer_id"])
                st.warning("Deleted")
                st.rerun()
    else:
        st.info("No customers found.")


def purchase_page():
    st.title("Record Purchase")
    meds = services.list_medicines()
    sups = services.list_suppliers()
    if not meds or not sups:
        st.warning("Add medicines and suppliers first.")
        return
    med_option = st.selectbox(
        "Medicine", [f'{m["name"]} (ID {m["medicine_id"]})' for m in meds]
    )
    sup_option = st.selectbox(
        "Supplier", [f'{s["name"]} (ID {s["supplier_id"]})' for s in sups]
    )
    quantity = st.number_input("Quantity", min_value=1, value=1)
    expiry = st.date_input("Expiry date", value=date.today())
    purchase_date = st.date_input("Purchase date", value=date.today())
    if st.button("Save Purchase"):
        med_id = int(med_option.split("ID")[1].strip(") "))
        sup_id = int(sup_option.split("ID")[1].strip(") "))
        services.add_purchase(med_id, sup_id, int(quantity), expiry, purchase_date)
        st.success("Purchase recorded and stock updated.")


def sales_page():
    st.title("Record Sale")
    meds = services.list_medicines()
    customers = services.list_customers()
    if not meds or not customers:
        st.warning("Add medicines and customers first.")
        return
    med_option = st.selectbox(
        "Medicine", [f'{m["name"]} (ID {m["medicine_id"]})' for m in meds]
    )
    cust_option = st.selectbox(
        "Customer", [f'{c["name"]} (ID {c["customer_id"]})' for c in customers]
    )
    quantity = st.number_input("Quantity", min_value=1, value=1)
    sale_date = st.date_input("Sale date", value=date.today())
    if st.button("Save Sale"):
        med_id = int(med_option.split("ID")[1].strip(") "))
        cust_id = int(cust_option.split("ID")[1].strip(") "))
        try:
            services.add_sale(med_id, cust_id, int(quantity), sale_date)
            st.success("Sale recorded and stock reduced.")
        except ValueError as exc:
            st.error(str(exc))


def reports_page():
    st.title("Reports")
    tabs = st.tabs(
        [
            "Current Stock",
            "Low Stock",
            "Expired",
            "Near Expiry",
            "Purchases",
            "Sales",
        ]
    )
    with tabs[0]:
        st.dataframe(pd.DataFrame(services.get_current_stock()))
    with tabs[1]:
        st.dataframe(pd.DataFrame(services.get_low_stock(LOW_STOCK_THRESHOLD)))
    with tabs[2]:
        st.dataframe(pd.DataFrame(services.get_expired()))
    with tabs[3]:
        st.dataframe(pd.DataFrame(services.get_near_expiry(30)))
    with tabs[4]:
        st.dataframe(pd.DataFrame(services.get_purchase_report()))
    with tabs[5]:
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
            "Medicines",
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
    elif page == "Medicines":
        medicines_page()
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
