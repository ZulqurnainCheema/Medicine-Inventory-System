-- Medical Inventory Management System Schema
-- Drop tables in FK-safe order
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS purchases;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS medicines;

-- Create base entities
CREATE TABLE medicines (
    medicine_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    is_deleted TINYINT(1) NOT NULL DEFAULT 0
);

CREATE TABLE suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_info VARCHAR(255) NOT NULL,
    is_deleted TINYINT(1) NOT NULL DEFAULT 0
);

CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_deleted TINYINT(1) NOT NULL DEFAULT 0
);

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE purchases (
    purchase_id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    supplier_id INT NOT NULL,
    quantity INT NOT NULL,
    purchase_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT fk_purchases_medicine FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON UPDATE CASCADE,
    CONSTRAINT fk_purchases_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON UPDATE CASCADE
);

CREATE TABLE sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    customer_id INT NOT NULL,
    quantity INT NOT NULL,
    sale_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT fk_sales_medicine FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON UPDATE CASCADE,
    CONSTRAINT fk_sales_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON UPDATE CASCADE
);

-- Stock associative entity links medicines and suppliers; one stock row per batch
CREATE TABLE stock (
    medicine_id INT NOT NULL,
    supplier_id INT NOT NULL,
    quantity INT NOT NULL,
    expiry_date DATE NOT NULL,
    PRIMARY KEY (medicine_id, supplier_id, expiry_date),
    CONSTRAINT fk_stock_medicine FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON UPDATE CASCADE,
    CONSTRAINT fk_stock_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON UPDATE CASCADE
);

-- Helpful indexes for lookups
CREATE INDEX idx_purchases_medicine ON purchases(medicine_id);
CREATE INDEX idx_purchases_supplier ON purchases(supplier_id);
CREATE INDEX idx_sales_medicine ON sales(medicine_id);
CREATE INDEX idx_sales_customer ON sales(customer_id);
CREATE INDEX idx_stock_expiry ON stock(expiry_date);

-- Sample data
INSERT INTO medicines (name, category, price) VALUES
('Paracetamol 500mg', 'Analgesic', 2.50),
('Amoxicillin 250mg', 'Antibiotic', 8.75),
('Ibuprofen 200mg', 'Anti-inflammatory', 3.20),
('Cetirizine 10mg', 'Antihistamine', 1.80),
('Insulin Glargine', 'Hormone', 45.00);

INSERT INTO suppliers (name, contact_info) VALUES
('HealthSource Pharma', 'healthsource@example.com | +1-555-1122'),
('Medico Supplies', 'medico@example.com | +1-555-3344'),
('WellCare Distributors', 'wellcare@example.com | +1-555-5566');

INSERT INTO customers (name) VALUES
('City Clinic'),
('Sunrise Hospital'),
('Community Health Center');

INSERT INTO users (username, password) VALUES
('admin', 'adminpass'),
('pharmacist', 'pharmacistpass');

-- Purchases representing incoming stock batches
INSERT INTO purchases (medicine_id, supplier_id, quantity, purchase_date) VALUES
(1, 1, 100, '2024-01-10'),  -- Paracetamol initial batch
(2, 2, 23,  '2024-02-05'),  -- Amoxicillin batch
(3, 2, 10,  '2023-09-15'),  -- Ibuprofen batch
(4, 3, 5,   '2024-01-28'),  -- Cetirizine batch
(5, 1, 40,  '2024-03-02');  -- Insulin batch

-- Stock entries (one expired, one near-expiry, one low stock)
INSERT INTO stock (medicine_id, supplier_id, quantity, expiry_date) VALUES
(1, 1, 95, '2025-12-31'),          -- Paracetamol, quantity after sale deduction
(2, 2, 20, '2024-07-15'),          -- Near expiry batch for Amoxicillin
(3, 2, 10, '2023-12-31'),          -- Expired Ibuprofen batch
(4, 3, 3, '2024-03-01'),           -- Low stock Cetirizine
(5, 1, 40, '2026-05-20');          -- Insulin ample stock

-- Sales referencing medicines and customers
INSERT INTO sales (medicine_id, customer_id, quantity, sale_date) VALUES
(1, 1, 5, '2024-02-20'),  -- Paracetamol sold 5, leaves 95 in stock
(2, 2, 3, '2024-03-01'),  -- Amoxicillin sold 3, leaves 20 in stock
(4, 3, 2, '2024-03-05');  -- Cetirizine sold 2, leaves 3 in stock

-- Reflect stock deduction from the Paracetamol sale (already applied above)
-- For transparency, the initial purchase batch was 100 units, reduced by 5 sold to City Clinic
-- UPDATE stock SET quantity = quantity - 5 WHERE medicine_id = 1 AND supplier_id = 1 AND expiry_date = '2025-12-31';
