-- 1. Load raw CSVs into tables
CREATE OR REPLACE TABLE stores   AS SELECT * FROM read_csv_auto('data/raw/stores.csv');
CREATE OR REPLACE TABLE products AS SELECT * FROM read_csv_auto('data/raw/products.csv');
CREATE OR REPLACE TABLE sales_raw AS
SELECT * FROM read_csv('data/raw/sales_transactions.csv', header = true,
                       types = {'order_date': 'VARCHAR'});

-- 2. Data quality report: what needs fixing?
SELECT
    COUNT(*)                                            AS total_rows,
    COUNT(*) - COUNT(DISTINCT order_id)                 AS duplicate_rows,
    SUM(CASE WHEN discount_pct   IS NULL THEN 1 ELSE 0 END) AS missing_discount,
    SUM(CASE WHEN payment_method IS NULL THEN 1 ELSE 0 END) AS missing_payment,
    SUM(CASE WHEN quantity < 0           THEN 1 ELSE 0 END) AS return_rows,
    SUM(CASE WHEN order_date LIKE '%/%'  THEN 1 ELSE 0 END) AS wrong_date_format
FROM sales_raw;

-- 3. Inconsistent text values
SELECT payment_method, COUNT(*) AS row_count
FROM sales_raw
GROUP BY payment_method
ORDER BY row_count DESC;
