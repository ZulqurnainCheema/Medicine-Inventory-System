# Home Decor Inventory Management System

MySQL schema + Streamlit frontend implementing products, categories/subcategories, suppliers, customers, users, purchases, sales, and stock.

## Setup
1) Load schema/sample data into MySQL (uses `u230499416_in` in `config.py`):
```bash
mysql -u u230499416_in -p -h srv1915.hstgr.io u230499416_in < schema.sql
```

2) Configure DB connection: edit `config.py` if you need different credentials.

3) Install Python requirements:
```bash
pip install -r requirements.txt
```

4) Run the app:
```bash
streamlit run app.py
```
The app will open in your browser (default http://localhost:8501).
