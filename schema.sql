-- Medical Inventory Management System Schema
-- Drop tables in FK-safe order
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS purchases;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;

-- Create base entities
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_category_id INT NULL,
    is_deleted TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT fk_categories_parent FOREIGN KEY (parent_category_id) REFERENCES categories(category_id) ON UPDATE CASCADE
);

CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id INT NOT NULL,
    subcategory_id INT NULL,
    price DECIMAL(10,2) NOT NULL,
    is_deleted TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(category_id) ON UPDATE CASCADE,
    CONSTRAINT fk_products_subcategory FOREIGN KEY (subcategory_id) REFERENCES categories(category_id) ON UPDATE CASCADE
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
    product_id INT NOT NULL,
    supplier_id INT NOT NULL,
    quantity INT NOT NULL,
    purchase_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    purchase_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT fk_purchases_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON UPDATE CASCADE,
    CONSTRAINT fk_purchases_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON UPDATE CASCADE
);

CREATE TABLE sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    customer_id INT NOT NULL,
    quantity INT NOT NULL,
    sale_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    sale_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT fk_sales_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON UPDATE CASCADE,
    CONSTRAINT fk_sales_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON UPDATE CASCADE
);

-- Stock associative entity links products and suppliers; one stock row per batch
CREATE TABLE stock (
    product_id INT NOT NULL,
    supplier_id INT NOT NULL,
    quantity INT NOT NULL,
    expiry_date DATE NOT NULL,
    PRIMARY KEY (product_id, supplier_id, expiry_date),
    CONSTRAINT fk_stock_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON UPDATE CASCADE,
    CONSTRAINT fk_stock_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON UPDATE CASCADE
);

-- Helpful indexes for lookups
CREATE INDEX idx_purchases_product ON purchases(product_id);
CREATE INDEX idx_purchases_supplier ON purchases(supplier_id);
CREATE INDEX idx_sales_product ON sales(product_id);
CREATE INDEX idx_sales_customer ON sales(customer_id);
CREATE INDEX idx_stock_expiry ON stock(expiry_date);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_subcategory ON products(subcategory_id);

-- Sample data
-- Categories and subcategories
INSERT INTO categories (name, parent_category_id) VALUES
('Furniture', NULL),        -- 1
('Lighting', NULL),         -- 2
('Textiles', NULL),         -- 3
('Decor', NULL),            -- 4
('Tables', 1),              -- 5 sub of Furniture
('Seating', 1),             -- 6 sub of Furniture
('Table Lamps', 2),         -- 7 sub of Lighting
('Wall Lights', 2),         -- 8 sub of Lighting
('Rugs', 3),                -- 9 sub of Textiles
('Pillows', 3),             -- 10 sub of Textiles
('Wall Art', 4),            -- 11 sub of Decor
('Vases', 4);               -- 12 sub of Decor

INSERT INTO products (name, category_id, subcategory_id, price) VALUES
('Oak Coffee Table', 1, 5, 220.00),
('Velvet Accent Chair', 1, 6, 350.00),
('Ceramic Table Lamp', 2, 7, 120.00),
('Handwoven Jute Rug', 3, 9, 180.00),
('Abstract Canvas Art', 4, 11, 95.00);

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
INSERT INTO purchases (product_id, supplier_id, quantity, purchase_date, purchase_price) VALUES
(1, 1, 20, '2024-01-10', 180.00),   -- Oak Coffee Table stock
(2, 2, 15, '2024-02-05', 250.00),   -- Velvet Accent Chair stock
(3, 2, 25, '2023-09-15', 80.00),    -- Ceramic Table Lamp stock
(4, 3, 30, '2024-01-28', 140.00),   -- Handwoven Jute Rug stock
(5, 1, 40, '2024-03-02', 60.00);    -- Abstract Canvas Art stock

-- Stock entries (one expired, one near-expiry, one low stock)
INSERT INTO stock (product_id, supplier_id, quantity, expiry_date) VALUES
(1, 1, 18, '2025-12-31'),          -- Oak Coffee Table, quantity after sale deduction
(2, 2, 12, '2024-07-15'),          -- Velvet Accent Chair near expiry placeholder date
(3, 2, 5,  '2023-12-31'),          -- Ceramic Table Lamp expired placeholder date
(4, 3, 4,  '2024-03-01'),          -- Handwoven Jute Rug low stock
(5, 1, 35, '2026-05-20');          -- Abstract Canvas Art ample stock

-- Sales referencing products and customers
INSERT INTO sales (product_id, customer_id, quantity, sale_date, sale_price) VALUES
(1, 1, 2, '2024-02-20', 220.00),  -- Oak Coffee Table sold 2, leaves 18 in stock
(2, 2, 3, '2024-03-01', 350.00),  -- Velvet Accent Chair sold 3, leaves 12 in stock
(4, 3, 1, '2024-03-05', 180.00);  -- Handwoven Jute Rug sold 1, leaves 4 in stock

-- Reflect stock deduction from the Paracetamol sale (already applied above)
-- For transparency, the initial purchase batch was 100 units, reduced by 5 sold to City Clinic
-- UPDATE stock SET quantity = quantity - 5 WHERE product_id = 1 AND supplier_id = 1 AND expiry_date = '2025-12-31';
