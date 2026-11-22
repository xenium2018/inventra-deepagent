---
name: financial-report
description: Financial summary and health check — total sales, purchases, net profit, margin, by region and product, with recommendations to improve margins. Use for "financial report", "profit", "margin in West region", "financial health", "top revenue products".
---

# Financial Report

## Inputs
- `region` (optional), `days` (default 365; use 90 for a "health check" unless the user says otherwise).

## Period
Anchor to the latest finance date: `date >= date((SELECT MAX(date) FROM finance), '-<days> days')`.
If that returns no rows, use all-time data and say so.

## Steps
1. Summary:
   ```sql
   SELECT MIN(date) AS from_date, MAX(date) AS to_date,
          ROUND(SUM(CASE WHEN type='sale' THEN amount ELSE 0 END), 2) AS total_sales,
          ROUND(SUM(CASE WHEN type='purchase' THEN amount ELSE 0 END), 2) AS total_purchases,
          COUNT(*) AS transactions, ROUND(AVG(amount), 2) AS avg_transaction
   FROM finance WHERE <period> [AND region = '<Region>'];
   ```
   - Net profit = total_sales − total_purchases
   - Profit margin % = net_profit / total_sales × 100 (0 if no sales)
2. By region (only if no region filter): same sums `GROUP BY region`, with margin per region.
3. Top 5 revenue products:
   ```sql
   SELECT f.sku, i.name, i.category, ROUND(SUM(f.amount), 2) AS revenue
   FROM finance f LEFT JOIN inventory i ON f.sku = i.sku
   WHERE f.type = 'sale' AND <period> GROUP BY f.sku ORDER BY revenue DESC LIMIT 5;
   ```
4. Margin by category (sales minus purchases, joined to inventory) to spot loss-making categories.

## Output format
```
FINANCIAL SUMMARY (<from> to <to>) [for <Region> region]
Total sales: Rs X | Total purchases: Rs Y | Net profit: Rs Z | Margin: N.N%
```
Then region table, top products table.

If the user asked for **analysis / health / advice**, add:
1. Health assessment (one line: healthy / watch / concern, and why)
2. Profitability insights (which regions/categories drive or drag margin)
3. 2–3 specific actions to improve margin (cost, pricing, mix)
4. Cost optimisation and revenue-growth ideas tied to the numbers above
