---
name: vendor-selection
description: Rank and recommend vendors on quality, reliability, lead time, price and terms, optionally for a specific SKU. Use for "best vendor", "who should supply SKU012", "compare vendors", "vendor risk", "backup suppliers".
---

# Vendor Selection

## Inputs
- `sku` (optional). If given, compare its current vendor with alternatives.

## Steps
1. If `sku` given, get the product and current vendor:
   ```sql
   SELECT i.sku, i.name, i.category, i.region, i.qty, i.unit_cost, i.vendor_id, v.name AS vendor
   FROM inventory i LEFT JOIN vendors v ON i.vendor_id = v.vendor_id WHERE i.sku = '<SKU>';
   ```
2. Rank vendors:
   ```sql
   SELECT vendor_id, name, quality_score, reliability_rating, on_time_delivery_rate,
          lead_time_days, avg_delay_days, unit_price, bulk_discount_percent,
          payment_terms_days, min_order_qty, return_acceptance_rate
   FROM vendors
   ORDER BY quality_score DESC,
            CASE reliability_rating WHEN 'good' THEN 3 WHEN 'average' THEN 2 ELSE 1 END DESC,
            lead_time_days ASC
   LIMIT 10;
   ```
3. Compute a simple score for each of the 10 (show it, so the ranking is transparent):
   `score = quality_score×20 + on_time_delivery_rate×0.3 + reliability(good=10, average=5, poor=0) − lead_time_days − avg_delay_days×2`
4. Effective price = `unit_price × (1 − bulk_discount_percent/100)`.

## Output format
1. **Best overall vendor** — name, ID and why (2 bullet facts).
2. **Backup options** — 2 vendors, each with the scenario they suit (faster, cheaper, better terms).
3. **Comparison table** — Vendor | Score | Quality | Reliability | On-time % | Lead time | Eff. price | Min order
4. **Trade-offs** between quality, lead time and price (2–3 bullets).
5. **Risk mitigation** — e.g. dual-sourcing, buffer stock for long lead times, avoid `poor` reliability vendors.

If `sku` was given, start with: "Current vendor for <SKU>: <vendor> — keep / switch to <vendor>" and why.
