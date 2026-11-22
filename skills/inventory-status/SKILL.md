---
name: inventory-status
description: Show current stock levels, totals by category and region, and low-stock alerts. Use for questions like "inventory status", "what's low on stock", "stock in North region", "how many units of X do we have".
---

# Inventory Status

## Inputs
- `region` (optional): North / South / East / West / Central.
- `category` or `sku` (optional) if the user names one.

Add `WHERE region = '<Region>'` (and/or category/sku filters) to every query below when given.

## Steps
1. Headline counts:
   ```sql
   SELECT COUNT(*) AS total_items,
          SUM(qty <= reorder_threshold) AS low_stock_count,
          SUM(qty) AS total_units,
          ROUND(SUM(qty * unit_cost), 2) AS stock_value
   FROM inventory;
   ```
2. Units by category:
   ```sql
   SELECT category, SUM(qty) AS units, COUNT(*) AS skus
   FROM inventory GROUP BY category ORDER BY category;
   ```
3. Units by region — **only when no region filter** was given:
   ```sql
   SELECT region, SUM(qty) AS units FROM inventory GROUP BY region ORDER BY region;
   ```
4. Low-stock items, most critical first (top 10):
   ```sql
   SELECT sku, name, category, region, qty, reorder_threshold
   FROM inventory WHERE qty <= reorder_threshold
   ORDER BY CAST(qty AS REAL) / reorder_threshold ASC LIMIT 10;
   ```
5. For a single SKU question, also join its vendor:
   ```sql
   SELECT i.*, v.name AS vendor_name, v.lead_time_days, v.quality_score
   FROM inventory i LEFT JOIN vendors v ON i.vendor_id = v.vendor_id WHERE i.sku = '<SKU>';
   ```

## Output format
```
INVENTORY STATUS [in <Region> region]
Total items: N | Low-stock alerts: N | Stock value: Rs X

By category: table (category | units | SKUs)
By region:   table (only if no region filter)
Low-stock items: table (SKU | name | region | qty | threshold)
```
If there are no low-stock items, say "All items adequately stocked."
If there are low-stock items, end with: *"Want a reorder plan for these?"* (→ `reorder-recommendation` skill).
