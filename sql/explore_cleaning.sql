-- 1. Before -> after: see each messy value and what it becomes
SELECT
    payment_method                      AS raw_value,
    LENGTH(payment_method)              AS raw_length,
    UPPER(TRIM(payment_method))         AS trimmed_upper,
    CASE UPPER(TRIM(payment_method))
        WHEN 'CASH'        THEN 'Cash'
        WHEN 'CREDIT CARD' THEN 'Credit Card'
        WHEN 'DEBIT CARD'  THEN 'Debit Card'
        WHEN 'MOBILE PAY'  THEN 'Mobile Pay'
        ELSE 'Unknown'
    END                                 AS clean_value,
    COUNT(*)                            AS row_count
FROM sales_raw
GROUP BY 1, 2, 3, 4
ORDER BY clean_value, raw_value;

-- 2. After cleaning: how many distinct payment methods are left?
SELECT payment_method, COUNT(*) AS row_count
FROM sales_clean
GROUP BY payment_method
ORDER BY row_count DESC;