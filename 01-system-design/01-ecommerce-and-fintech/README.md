# HLD — E-commerce & Fintech

[← Back to System Design](../README.md)

Shared theme: **money and stock must be correct** — so idempotency, atomic reservation and an auditable ledger matter more than raw speed.

| Done | System | Hardest part (deep dive) | Key concepts to cover |
|---|---|---|---|
| ☐ ⭐ | **E-commerce checkout & flash sale** | selling limited stock to a spike without overselling | inventory **reservation with TTL**, atomic decrement (Redis Lua / DB conditional update), **queue-based admission control** (virtual waiting room), idempotency keys, rate limiting, payment timeout → release stock, eventual vs strong consistency |
| ☐ | **Payment / wallet ledger** (Razorpay/Stripe-style) | never lose or double-count money | **double-entry ledger** (every debit has a matching credit), immutable append-only entries, **idempotency keys**, exactly-once *effects* over at-least-once delivery, reconciliation with banks, state machine for payment (created → authorised → captured → refunded), webhooks with retries/signature |
| ☐ | Product catalog & search | fast, fresh search over a large catalog | search index (Elasticsearch/OpenSearch), CDC from DB to index, denormalised read models, caching, relevance & facets |
| ☐ | Order tracking & delivery | real-time status for millions of orders | event-driven state machine, event streaming, push (WebSocket/SSE) vs poll, location updates, notification fan-out |

## Building blocks reused here
Idempotency keys · distributed locks (and why they are tricky: lease/TTL, fencing tokens) · transactional outbox + Saga · optimistic vs pessimistic locking · rate limiting · queues for back-pressure.

## Links in this repo
- Code-level inventory & concurrency: [LLD Inventory Management](../../04-low-level-design/01-inventory-management/README.md), [Databases: inventory consistency](../../05-databases/README.md)
- Transactions, outbox, dual-write: [transactions note](../../02-languages/java/06-spring-boot/02-proxies-transactions-async.md#44-other-attributes-and-rules)
- Resilient external calls (payment gateway): [async error handling](../../02-languages/java/03-concurrency/03-async-error-handling-http.md)

## Per-system checklist (copy into each write-up)
- [ ] Requirements & estimation  - [ ] API & data model  - [ ] Core flow diagram
- [ ] Deep dive on the hardest part  - [ ] Failure modes (timeouts, retries, duplicates)
- [ ] Consistency choice and why  - [ ] Scaling plan (shard, cache, queue)
