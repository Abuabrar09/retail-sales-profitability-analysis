-- Clean sales: remove duplicates, fix dates, fill missing values, standardise text
CREATE OR REPLACE TABLE sales_clean AS
WITH dedup AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) AS rn
    FROM sales_raw
)
SELECT
    order_id,
    COALESCE(TRY_STRPTIME(order_date, '%Y-%m-%d'),
             TRY_STRPTIME(order_date, '%m/%d/%Y'))::DATE AS order_date,
    store_id,
    product_id,
    quantity,
    unit_price,
    COALESCE(discount_pct, 0) AS discount_pct,
    CASE UPPER(TRIM(payment_method))
        WHEN 'CASH'        THEN 'Cash'
        WHEN 'CREDIT CARD' THEN 'Credit Card'
        WHEN 'DEBIT CARD'  THEN 'Debit Card'
        WHEN 'MOBILE PAY'  THEN 'Mobile Pay'
        ELSE 'Unknown'
    END AS payment_method,
    customer_type,
    quantity < 0 AS is_return
FROM dedup
WHERE rn = 1;

-- Enriched view: join store + product info and calculate financials
CREATE OR REPLACE VIEW sales_enriched AS
SELECT
    s.*,
    p.product_name, p.category, p.subcategory, p.unit_cost,
    st.store_name, st.region, st.store_format,
    s.quantity * s.unit_price                         AS gross_sales,
    s.quantity * s.unit_price * s.discount_pct        AS discount_amount,
    s.quantity * s.unit_price * (1 - s.discount_pct)  AS net_revenue,
    s.quantity * p.unit_cost                          AS cogs,
    s.quantity * s.unit_price * (1 - s.discount_pct)
      - s.quantity * p.unit_cost                      AS gross_profit
FROM sales_clean s
JOIN products p  ON s.product_id = p.product_id
JOIN stores   st ON s.store_id   = st.store_id;

-- Verify
SELECT COUNT(*) AS clean_rows,
       SUM(CASE WHEN order_date IS NULL THEN 1 ELSE 0 END) AS bad_dates
FROM sales_clean;
