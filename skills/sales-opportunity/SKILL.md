---
name: sales-opportunity
description: Find upcoming sales opportunities by combining the 5-day weather forecast with historical weather-driven demand and current stock. Use for "where are the sales opportunities", "what will sell this week", "weather impact on demand", "which categories to push".
---

# Sales Opportunity

## Inputs
- `category` (optional), `region` (optional), `days` forecast horizon (default 5, the max the weather API gives).

## Steps
1. **Recent performance** (last 30 days of data):
   ```sql
   SELECT i.category, s.region, SUM(s.qty) AS units, ROUND(SUM(s.revenue), 2) AS revenue
   FROM sales s JOIN inventory i ON s.sku = i.sku
   WHERE s.date >= date((SELECT MAX(date) FROM sales), '-30 days')
   GROUP BY i.category, s.region ORDER BY revenue DESC;
   ```
2. **Weather**: call `get_weather` for each of the 5 regions (or just the requested one).
   Classify each region's dominant condition for the period (Clear / Clouds / Rain / Thunderstorm …) and temperature band.
3. **Weather-demand lift** per category (all history):
   ```sql
   SELECT i.category, s.weather_condition,
          ROUND(AVG(s.qty), 2) AS avg_units,
          ROUND(AVG(s.revenue), 2) AS avg_revenue,
          COUNT(*) AS n
   FROM sales s JOIN inventory i ON s.sku = i.sku
   GROUP BY i.category, s.weather_condition;
   ```
   Lift % = (avg_units under forecast condition / overall avg_units for the category − 1) × 100.
   Ignore combinations with n < 20.
4. **Stock check** for the categories with the best lift in the regions where that weather is coming:
   ```sql
   SELECT category, region, SUM(qty) AS units, SUM(qty <= reorder_threshold) AS low_stock_skus
   FROM inventory WHERE category IN (<cats>) GROUP BY category, region;
   ```
5. **Expected revenue impact** (label clearly as an estimate):
   recent daily revenue for that category+region × lift % × forecast days.

## Output format
```
SALES OPPORTUNITIES — next N days
```
1. Top opportunities table: Region | Forecast weather | Category | Demand lift | Stock position | Est. extra revenue
2. Categories likely to see increased demand (and which will soften)
3. Recommended inventory adjustments (move stock between regions, or reorder → offer `reorder-recommendation`)
4. One-line caveat if weather was unavailable (then base the answer on seasonality only)
