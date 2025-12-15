# Home Decor Inventory Management System

MySQL schema + Streamlit frontend implementing products, categories/subcategories, suppliers, customers, users, purchases, sales, and stock.

## Setup
1) Create your `.env` from `.env.example` (adjust values if needed):
```bash
cp .env.example .env
```

2) Load schema/sample data into MySQL (uses values from `.env`):
```bash
mysql -u u230499416_in -p -h srv1915.hstgr.io u230499416_in < schema.sql
```

3) Configure DB connection by editing `.env` if you need different credentials.

4) Install Python requirements:
```bash
pip install -r requirements.txt
```

5) Run the app:
```bash
streamlit run app.py
```
The app will open in your browser (default http://localhost:8501).
