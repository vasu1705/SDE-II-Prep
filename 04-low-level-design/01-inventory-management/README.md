# LLD 1 — Inventory Management System

[← Back to LLD](../README.md) · Status: ☐ not started · Priority: ⭐

## Requirements
- Maintain stock per **SKU** per warehouse/location; add stock, remove stock, query availability.
- **Reserve** stock for an order (hold), then **confirm** (deduct) or **release** (cancel or expire after a TTL).
- Never oversell under concurrent requests.
- Low-stock alerts; audit trail of every stock movement.

## Entities (starting point)
`Sku`, `Product`, `Warehouse`, `StockLevel(onHand, reserved)`, `Reservation(id, items, status, expiresAt)`, `StockMovement` (audit), `Order` reference by id only.
Derived: `available = onHand - reserved`.

## Patterns to apply
- **Repository** for storage, **Strategy** for allocation (nearest warehouse, FIFO batch), **Observer** for low-stock alerts, **State** for `Reservation` (HELD → CONFIRMED / RELEASED / EXPIRED).

## Concurrency (the heart of this problem)
- Atomic conditional update: reserve only if `available ≥ qty` (compare-and-set, or a per-SKU lock).
- Compare **optimistic** (version number, retry) vs **pessimistic** (lock per SKU) vs a single atomic decrement; discuss lock ordering when reserving several SKUs.
- Expiry: scheduled sweeper vs lazy expiry on read.
- Links: [locks & atomics](../../02-languages/java/03-concurrency/04-locks-volatile-deadlock.md), [JPA locking](../../02-languages/java/06-spring-boot/03-jpa-hibernate.md#7-locking-and-concurrency), [database inventory consistency](../../05-databases/README.md).

## Extension questions
Multiple warehouses, backorders, batch/expiry dates, bundles (kits), distributed deployment (move to DB/Redis).

## Test checklist
- [ ] Reserve → confirm → stock decreases once
- [ ] Reserve → release/expire → stock returns
- [ ] 100 threads reserve the last 10 units → exactly 10 succeed
- [ ] Reserving several SKUs is all-or-nothing

## Solution
_(add `src/` and links here)_
