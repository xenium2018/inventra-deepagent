---
name: reorder-recommendation
description: Weather-aware reorder plan for low-stock items — what to reorder, how many units, from which vendor, and in what priority; records the forecast. Use for "what should I reorder", "reorder plan for South", "restock recommendations", "should we stock up before the monsoon".
---

# Reorder Recommendation

## Inputs
- `region` (optional). If none given, cover all regions.

## Steps
1. **Low-stock items** with their current vendor:
   ```sql
   SELECT i.sku, i.name, i.category, i.region, i.qty, i.reorder_threshold, i.unit_cost,
          v.vendor_id, v.name AS vendor, v.lead_time_days, v.quality_score,
          v.reliability_rating, v.min_order_qty, v.unit_price
   FROM inventory i LEFT JOIN vendors v ON i.vendor_id = v.vendor_id
   WHERE i.qty <= i.reorder_threshold [AND i.region = '<Region>']
   ORDER BY CAST(i.qty AS REAL) / i.reorder_threshold;
   ```
   If none: say all items are adequately stocked and stop.

2. **Base reorder quantity** for each item:
   `reorder_qty = max(0, 2 × reorder_threshold − qty)`
   If `reorder_qty` is below the vendor's `min_order_qty`, raise it to `min_order_qty` and note it.

3. **Weather**: call `get_weather` once for each distinct region in the list.
   Summarise each region as hot / rainy / humid / mild for the next 5 days.

4. **Historical weather sensitivity** for the affected categories:
   ```sql
   SELECT i.category, s.weather_condition, ROUND(AVG(s.qty), 2) AS avg_units
   FROM sales s JOIN inventory i ON s.sku = i.sku
   WHERE i.category IN (<categories>) GROUP BY i.category, s.weather_condition;
   ```
   If a category's average under the forecast condition is ≥ 15% above its overall average,
   add a weather buffer of +20% to `reorder_qty` (round up). Explain it in one phrase.

5. **Vendor choice**: keep the current vendor unless it is `poor` reliability or quality_score < 3.5.
   Otherwise pick an alternative from:
   ```sql
   SELECT vendor_id, name, quality_score, reliability_rating, lead_time_days, unit_price, min_order_qty
   FROM vendors
   ORDER BY quality_score DESC,
            CASE reliability_rating WHEN 'good' THEN 3 WHEN 'average' THEN 2 ELSE 1 END DESC,
            lead_time_days ASC LIMIT 5;
   ```

6. **Priority**
   - `high`: qty ≤ 50% of threshold, OR weather buffer applied, OR vendor lead time > 7 days
   - `medium`: other low-stock items
   - `low`: qty is exactly at threshold and no weather pressure

7. **Record forecasts** — one `write_db` call per item (this is tracking, no confirmation needed):
   ```sql
   INSERT INTO forecasts (forecast_date, sku, predicted_demand, predicted_weather, recommendation)
   VALUES (date('now'), '<SKU>', <reorder_qty>, '<condition or Unknown>', 'Reorder <qty> units from <vendor_id>: <short reason>');
   ```

## Output format
```
REORDER PLAN [for <Region>] — N items need action
```
Table: Priority | SKU | Product | Region | Stock/Threshold | Reorder qty | Vendor | Lead time | Est. cost (qty × unit_price)
Then: total estimated spend, a 1-line weather summary per region, and key reasons for the high-priority items.

End with: *"Shall I raise reorder tickets for these?"* If yes → follow the `ticket-management` skill.
