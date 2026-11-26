# 05 — Databases & SQL

[← Back to book](../README.md)

Four topics that backend deep-dive rounds probe (especially for Java/Spring roles). Each becomes its own note later; this page is the task list with starting hints.

| # | Topic | Status |
|---|-------|--------|
| 1 | [Order Management System schema](#1-order-management-system-schema) | ☐ |
| 2 | [Clustered vs non-clustered indexes](#2-clustered-vs-non-clustered-indexes) | ☐ |
| 3 | [Inventory consistency under concurrent orders](#3-inventory-consistency-under-concurrent-orders) | ☐ |
| 4 | [ACID with a concrete example](#4-acid-with-a-concrete-example) | ☐ |

## 1. Order Management System schema
**Task:** design a normalised schema and justify it.

- Tables to start from: `customers`, `addresses`, `products`, `categories`, `orders`, `order_items`, `payments`, `inventory`, `order_status_history`.
- Normalise to **3NF**, then say where you deliberately **denormalise** (copy the unit price and product name into `order_items` so old orders don't change when prices change).
- Keys & constraints: PK/FK, `CHECK (quantity > 0)`, unique constraints, money as `DECIMAL(p,s)` (never float), status as an enum/lookup table.
- Indexes from **access patterns**: orders by customer and date, order items by order, lookups by SKU.
- Discuss: soft delete vs archive, partitioning orders by date, multi-currency.
- [ ] Draw the ER diagram  - [ ] Write the DDL  - [ ] List the 5 queries it must serve and their indexes

## 2. Clustered vs non-clustered indexes
**Task:** explain storage layout, lookup cost and write overhead.

| | Clustered | Non-clustered (secondary) |
|---|---|---|
| What it is | the table rows are **stored in the index order**; leaf pages *are* the data | a separate B-tree whose leaves hold the key plus a **pointer** (row id or the clustered key) |
| How many per table | **one** | many |
| Lookup | one tree descent to the row | descend, then **one more hop** to fetch the row (a *bookmark/key lookup*), unless the index is **covering** |
| Write cost | inserts out of key order cause page splits | every secondary index must be updated on each write |

- **MySQL/InnoDB:** the table is clustered by the primary key, and secondary indexes store the PK (so a wide or random PK, e.g. random UUID, bloats every index).
- **PostgreSQL:** tables are heaps; B-tree indexes are all "secondary"; `CLUSTER` reorders once but doesn't maintain it.
- **SQL Server:** you choose a clustered index explicitly (default is the primary key).
- Also cover: covering indexes, composite index column order (leftmost prefix), selectivity, and `EXPLAIN` to prove an index is used.
- [ ] Explain with a diagram  - [ ] Show an `EXPLAIN` before/after

## 3. Inventory consistency under concurrent orders
**Task:** prevent overselling when many buyers target the same SKU.

```sql
-- (a) Atomic conditional update: no read-then-write race. Check the affected row count (0 = out of stock).
UPDATE inventory SET stock = stock - :qty WHERE sku = :sku AND stock >= :qty;

-- (b) Optimistic locking: version column; retry if 0 rows updated.
UPDATE inventory SET stock = stock - :qty, version = version + 1
 WHERE sku = :sku AND version = :seenVersion AND stock >= :qty;

-- (c) Pessimistic locking: lock the row for the transaction.
SELECT stock FROM inventory WHERE sku = :sku FOR UPDATE;
```

- Compare (a)/(b)/(c): throughput under contention, deadlock risk (lock several SKUs in a consistent order), retry cost.
- **Isolation levels:** what READ COMMITTED vs REPEATABLE READ vs SERIALIZABLE do about lost updates and **write skew**.
- **Beyond one DB:** Redis atomic `DECR`/Lua for the hot path, with a reservation table and TTL; reconcile with the DB.
- Links: [JPA optimistic/pessimistic locking](../02-languages/java/06-spring-boot/03-jpa-hibernate.md#7-locking-and-concurrency), [isolation levels](../02-languages/java/06-spring-boot/02-proxies-transactions-async.md#43-isolation), [LLD inventory](../04-low-level-design/01-inventory-management/README.md), [HLD flash sale](../01-system-design/01-ecommerce-and-fintech/README.md).
- [ ] Reproduce the race with two sessions  - [ ] Show each fix  - [ ] State the trade-offs

## 4. ACID with a concrete example
**Task:** explain each property using one real transaction, e.g. *placing an order* (create order + deduct stock + record payment).

- **Atomicity:** all three steps commit or none do (rollback on failure).
- **Consistency:** constraints hold before and after (`stock >= 0`, FK validity, totals match items).
- **Isolation:** two buyers of the last item don't both succeed (see topic 3).
- **Durability:** once committed it survives a crash (write-ahead log, fsync).
- Add the counter-example: what breaks without each property.
- [ ] Walk through it out loud in 2 minutes
