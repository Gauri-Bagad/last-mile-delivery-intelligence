USE delivery_db;

-- ===== 0. HEADLINE KPIs =====
SELECT COUNT(*)                           AS total_orders,
       ROUND(AVG(is_late)*100, 1)         AS sla_breach_pct,
       ROUND(AVG(actual_delivery_days),1) AS avg_delivery_days,
       ROUND(AVG(warehouse_handover_days),1) AS avg_warehouse_days,
       ROUND(AVG(transit_days),1)         AS avg_transit_days
FROM deliveries;

-- ===== 1. WORST WAREHOUSES =====
SELECT seller_id, seller_state,
       COUNT(*)                           AS total_orders,
       ROUND(AVG(is_late)*100, 1)         AS late_rate_pct,
       ROUND(AVG(warehouse_handover_days),1) AS avg_warehouse_days
FROM deliveries
GROUP BY seller_id, seller_state
HAVING COUNT(*) >= 50
ORDER BY late_rate_pct DESC
LIMIT 10;

-- ===== 2. WORST LANES (courier proxy) —  CONCAT instead of || =====
SELECT CONCAT(seller_state, ' -> ', customer_state) AS lane,
       COUNT(*)                           AS total_orders,
       ROUND(AVG(is_late)*100, 1)         AS late_rate_pct,
       ROUND(AVG(actual_delivery_days),1) AS avg_delivery_days
FROM deliveries
GROUP BY lane
HAVING COUNT(*) >= 100
ORDER BY late_rate_pct DESC
LIMIT 10;

-- ===== 3. CITY BOTTLENECKS =====
SELECT customer_city, customer_state,
       COUNT(*)                           AS total_orders,
       ROUND(AVG(is_late)*100, 1)         AS late_rate_pct,
       ROUND(AVG(actual_delivery_days),1) AS avg_delivery_days
FROM deliveries
GROUP BY customer_city, customer_state
HAVING COUNT(*) >= 100
ORDER BY late_rate_pct DESC
LIMIT 10;

-- ===== 4. ROOT CAUSE (warehouse vs road) =====
SELECT route_type,
       COUNT(*)                           AS total_orders,
       ROUND(AVG(is_late)*100, 1)         AS late_rate_pct,
       ROUND(AVG(warehouse_handover_days),1) AS avg_warehouse_days,
       ROUND(AVG(transit_days),1)         AS avg_transit_days
FROM deliveries
GROUP BY route_type;

-- ===== 5. DELAY TREND OVER TIME =====
SELECT order_month,
       COUNT(*)                           AS total_orders,
       ROUND(AVG(is_late)*100, 1)         AS late_rate_pct
FROM deliveries
GROUP BY order_month
ORDER BY order_month;

-- ===== 6. SLA-RISK SEGMENTS =====
SELECT route_type,
       CASE WHEN warehouse_handover_days > 3
            THEN 'Slow dispatch (>3d)' ELSE 'Fast dispatch (<=3d)' END AS dispatch_speed,
       COUNT(*)                           AS total_orders,
       ROUND(AVG(is_late)*100, 1)         AS late_rate_pct
FROM deliveries
GROUP BY route_type, dispatch_speed
ORDER BY late_rate_pct DESC;