---
name: sales-analysis
description: Analyse historical sales — units, revenue, daily averages, top days, regional performance and how weather conditions affected demand. Use for "sales trends", "how did SKU042 sell", "sales by region", "revenue last 90 days".
---

# Sales Analysis

## Inputs
- `days` (default 365), `sku` (optional), `region` (optional), `category` (optional).

## Period
Data is historical. Anchor the window to the last date in the table:
`s.date >= date((SELECT MAX(date) FROM sales), '-<days> days')`.
Use alias `s` for sales and join `inventory i ON s.sku = i.sku` for names/categories.
Add the sku / region / category filters to every query when given.

## Steps
1. Totals:
   ```sql
   SELECT MIN(s.date) AS from_date, MAX(s.date) AS to_date,
          SUM(s.qty) AS units, ROUND(SUM(s.revenue), 2) AS revenue, COUNT(*) AS orders
   FROM sales s WHERE s.date >= date((SELECT MAX(date) FROM sales), '-365 days');
   ```
   Average daily sales = `units / days`.
2. By region (revenue, units), ordered by revenue DESC.
3. Weather impact — units and average units per order by `weather_condition`:
   ```sql
   SELECT s.weather_condition, SUM(s.qty) AS units, ROUND(AVG(s.qty), 2) AS avg_units_per_order
   FROM sales s WHERE <period> GROUP BY s.weather_condition ORDER BY units DESC;
   ```
4. Top 5 selling days: `SELECT s.date, s.sku, i.name, s.qty ... ORDER BY s.qty DESC LIMIT 5`.
5. If no `sku` given: top 5 products by revenue (`GROUP BY s.sku`).
6. If the result set is empty, say "No sales data found for that filter" and show the available date range
   (`SELECT MIN(date), MAX(date) FROM sales`).

## Output format
```
SALES ANALYSIS (<from_date> to <to_date>)
Units: N | Revenue: Rs X | Avg daily: N.N units | Orders: N
```
Then tables for region performance, weather impact and top products, followed by 2–3 bullet insights
(e.g. which weather lifts demand, which region leads).
