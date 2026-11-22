---
name: ticket-management
description: View, create, approve, reject or complete reorder tickets and show ticket statistics. Use for "show tickets", "pending tickets", "raise a ticket for SKU023", "create tickets for the reorder plan", "approve ticket 4".
---

# Ticket Management

Statuses: `pending` → `approved` / `rejected` → `completed`. Priorities: `high`, `medium`, `low`.

## View tickets / stats
1. Stats:
   ```sql
   SELECT status, COUNT(*) AS n FROM tickets GROUP BY status;
   SELECT priority, COUNT(*) AS n FROM tickets WHERE status='pending' GROUP BY priority;
   SELECT ROUND(COALESCE(SUM(t.recommended_qty * v.unit_price), 0), 2) AS pending_value
   FROM tickets t JOIN vendors v ON t.vendor_id = v.vendor_id WHERE t.status='pending';
   ```
2. List (default `pending`, max 10, or the status the user asked for):
   ```sql
   SELECT t.id, t.sku, i.name AS product, t.recommended_qty, v.name AS vendor,
          t.priority, t.status, t.created_at, t.reason
   FROM tickets t
   LEFT JOIN inventory i ON t.sku = i.sku
   LEFT JOIN vendors v ON t.vendor_id = v.vendor_id
   WHERE t.status = 'pending'
   ORDER BY CASE t.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, t.created_at DESC
   LIMIT 10;
   ```
Output: `TICKET STATUS — Pending: N | Value: Rs X`, then a table: # | SKU | Product | Qty | Vendor | Priority.
If there are none: "No pending tickets."

## Create tickets
1. You need, per ticket: `sku`, `reason`, `recommended_qty`, `vendor_id`, `priority`.
   - Coming from a reorder plan earlier in this conversation → reuse those values.
   - User names a single SKU without details → use the `reorder-recommendation` rules for qty and vendor.
2. Check the SKU and vendor exist (`SELECT sku FROM inventory WHERE sku=...`, same for vendors),
   and skip SKUs that already have a pending ticket:
   `SELECT id FROM tickets WHERE sku='<SKU>' AND status='pending';`
3. **Show the list of tickets you are about to create and ask the user to confirm.** Do not write before a "yes".
4. One `write_db` per ticket:
   ```sql
   INSERT INTO tickets (sku, reason, recommended_qty, vendor_id, priority, status)
   VALUES ('<SKU>', '<reason>', <qty>, '<VENDOR_ID>', '<priority>', 'pending');
   ```
5. Report created ticket IDs (from `last id`), any skipped and why, and the total value.

## Update a ticket
1. Fetch it first (`SELECT ... WHERE t.id = <id>`); if missing say "Ticket #<id> not found".
2. Confirm the change with the user, then:
   `UPDATE tickets SET status = '<approved|rejected|completed>' WHERE id = <id>;`
3. Reply: "Ticket #<id> updated to <status>."
