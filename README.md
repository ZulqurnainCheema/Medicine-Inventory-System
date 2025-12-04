# Medical Inventory Management System

MySQL schema + Streamlit frontend implementing the ERD for medicines, suppliers, customers, users, purchases, sales, and stock.

## Setup
1) Create MySQL database and load schema/sample data:
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS medical_inventory;"
mysql -u root -p medical_inventory < schema.sql
```

2) Configure DB connection: rename `config_example.py` to `config.py` and update credentials.

3) Install Python requirements:
```bash
pip install -r requirements.txt
```

4) Run the app:
```bash
streamlit run app.py
```
The app will open in your browser (default http://localhost:8501).
