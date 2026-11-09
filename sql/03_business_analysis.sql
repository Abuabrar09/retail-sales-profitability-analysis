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