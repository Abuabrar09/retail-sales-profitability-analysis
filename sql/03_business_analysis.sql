-- Q1. Overall business KPIs (2024-2025)
-- Business question: How much did we sell, how much did discounts cost us,
-- and what share of revenue do we keep as gross profit?
SELECT
    COUNT(*)                                              AS transactions,
    ROUND(SUM(gross_sales), 2)                            AS gross_sales,
    ROUND(SUM(discount_amount), 2)                        AS discounts,
    ROUND(SUM(net_revenue), 2)                            AS net_revenue,
    ROUND(SUM(cogs), 2)                                   AS cogs,
    ROUND(SUM(gross_profit), 2)                           AS gross_profit,
    ROUND(SUM(gross_profit) / SUM(net_revenue) * 100, 2)  AS gross_margin_pct,
    ROUND(SUM(discount_amount) / SUM(gross_profit) * 100, 1) AS discount_as_pct_of_profit
FROM sales_enriched;

-- Q2a. Yearly comparison
-- Business question: Did the business grow from 2024 to 2025?
SELECT
    YEAR(order_date)                                      AS year,
    ROUND(SUM(net_revenue), 0)                            AS net_revenue,
    ROUND(SUM(gross_profit), 0)                           AS gross_profit,
    ROUND(SUM(gross_profit) / SUM(net_revenue) * 100, 1)  AS margin_pct
FROM sales_enriched
GROUP BY YEAR(order_date)
ORDER BY year;

-- Q2b. Monthly trend with year-over-year growth
-- Business question: Which months are strongest, and is each month
-- growing compared with the same month last year?
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', order_date) AS month,
        SUM(net_revenue)                AS revenue,
        SUM(gross_profit)               AS profit
    FROM sales_enriched
    GROUP BY DATE_TRUNC('month', order_date)
)
SELECT
    STRFTIME(month, '%Y-%m')                              AS month,
    ROUND(revenue, 0)                                     AS revenue,
    ROUND(profit, 0)                                      AS profit,
    ROUND(profit / revenue * 100, 1)                      AS margin_pct,
    ROUND(LAG(revenue, 12) OVER (ORDER BY month), 0)      AS revenue_same_month_last_year,
    ROUND((revenue - LAG(revenue, 12) OVER (ORDER BY month))
          / LAG(revenue, 12) OVER (ORDER BY month) * 100, 1) AS yoy_growth_pct
FROM monthly
ORDER BY month;

-- Q3a. Regional performance
-- Business question: Which regions drive the business?
SELECT
    region,
    COUNT(DISTINCT store_id)                                  AS stores,
    ROUND(SUM(net_revenue), 0)                                AS revenue,
    ROUND(SUM(net_revenue) * 100.0 / (SELECT SUM(net_revenue) FROM sales_enriched), 1) AS revenue_share_pct,
    ROUND(SUM(gross_profit), 0)                               AS gross_profit,
    ROUND(SUM(gross_profit) / SUM(net_revenue) * 100, 1)      AS gross_margin_pct
FROM sales_enriched
GROUP BY region
ORDER BY revenue DESC;

-- Q3b. Store ranking by operating profit (after store running costs)
-- Business question: Which stores actually make money, and which lose it?
WITH store_perf AS (
    SELECT
        store_id, store_name, region, store_format,
        SUM(gross_sales)      AS gross_sales,
        SUM(discount_amount)  AS discounts,
        SUM(net_revenue)      AS revenue,
        SUM(gross_profit)     AS gross_profit
    FROM sales_enriched
    GROUP BY store_id, store_name, region, store_format
)
SELECT
    sp.store_id,
    sp.store_name,
    sp.region,
    sp.store_format                                               AS format,
    ROUND(sp.revenue, 0)                                          AS revenue,
    ROUND(sp.gross_profit / sp.revenue * 100, 1)                  AS gross_margin_pct,
    ROUND(sp.discounts / sp.gross_sales * 100, 1)                 AS discount_rate_pct,
    ROUND(s.monthly_operating_cost * 24, 0)                       AS operating_costs,
    ROUND(sp.gross_profit - s.monthly_operating_cost * 24, 0)     AS operating_profit,
    ROUND((sp.gross_profit - s.monthly_operating_cost * 24) / sp.revenue * 100, 1) AS operating_margin_pct,
    CASE
        WHEN sp.gross_profit - s.monthly_operating_cost * 24 < 0           THEN 'LOSS-MAKING'
        WHEN (sp.gross_profit - s.monthly_operating_cost * 24) / sp.revenue < 0.01 THEN 'At risk'
        ELSE 'Healthy'
    END                                                           AS status
FROM store_perf sp
JOIN stores s ON sp.store_id = s.store_id
ORDER BY operating_profit;

-- Q3c. Performance by store format
-- Business question: Is one type of store the problem?
WITH store_perf AS (
    SELECT store_id, store_format,
           SUM(net_revenue) AS revenue, SUM(gross_profit) AS gross_profit
    FROM sales_enriched
    GROUP BY store_id, store_format
)
SELECT
    sp.store_format                                                AS format,
    COUNT(*)                                                       AS stores,
    ROUND(SUM(sp.revenue), 0)                                      AS revenue,
    ROUND(SUM(sp.gross_profit - s.monthly_operating_cost * 24), 0) AS operating_profit,
    ROUND(SUM(sp.gross_profit - s.monthly_operating_cost * 24) / SUM(sp.revenue) * 100, 1) AS operating_margin_pct
FROM store_perf sp
JOIN stores s ON sp.store_id = s.store_id
GROUP BY sp.store_format
ORDER BY operating_margin_pct;