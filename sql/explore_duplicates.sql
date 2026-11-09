-- After cleaning: are any duplicates left?
SELECT
    COUNT(*)                  AS total_rows,
    COUNT(DISTINCT order_id)  AS unique_orders,
    COUNT(*) - COUNT(DISTINCT order_id) AS duplicates_left
FROM sales_clean;