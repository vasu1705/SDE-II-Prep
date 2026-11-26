# 01 — System Design

[← Back to book](../README.md)

Prepare by **category**, so you reuse the same building blocks (idempotency, queues, caching, consistent hashing, sharding) instead of memorising 20 separate designs.

## Case-study categories

| # | Category | Systems | Key concepts |
|---|----------|---------|--------------|
| 1 | [E-commerce & fintech](01-ecommerce-and-fintech/README.md) | Checkout & flash sale, payment/wallet ledger, product catalog & search, order tracking & delivery | distributed locks, idempotency keys, double-entry ledger, inventory reservation, consistency |
| 2 | [Core distributed infrastructure](02-core-distributed-infra/README.md) | URL shortener, API rate limiter, distributed cache, CDN, notification system, job scheduler, ID generator, hit counter | consistent hashing, token bucket/sliding window, Snowflake IDs, fan-out queues, back-pressure, clock skew |
| 3 | [Social, real-time & media](03-social-realtime-media/README.md) | Chat, social feed, ride-hailing, collaborative docs, video streaming, recommendations | WebSockets, fan-out on write vs read, geospatial indexing, CRDT/OT, adaptive bitrate |
| 4 | [Storage & search](04-storage-and-search/README.md) | File storage (Dropbox/Drive), search autocomplete | chunking & dedup, metadata vs blob, distributed tries, hot-prefix caching |
| 5 | [Systems & ops logic](05-systems-and-ops/README.md) | Zero-downtime SSH key rotation (master–slave) | dual-key overlap, verification, rollback safety |

## Answer framework (use for every design)
1. **Requirements:** functional, non-functional (latency, availability, consistency), scale, out of scope.
2. **Estimation:** users, QPS (average and peak), storage, bandwidth.
3. **API & data model:** the 3–5 key endpoints; the entities and access patterns.
4. **High-level design:** boxes and arrows; sync vs async paths.
5. **Deep dives:** the 2 hardest parts (the "interesting" bottleneck for that system).
6. **Failure & scale:** what breaks, retries, idempotency, replication, sharding, hot keys.
7. **Trade-offs:** say what you chose *and what you gave up*.

## Fundamentals (revision checklist)
- [ ] Requirements gathering & back-of-envelope estimation
- [ ] Latency, throughput, availability, reliability
- [ ] CAP theorem & PACELC
- [ ] Consistency models (strong, eventual, causal)
- [ ] Scaling: vertical vs horizontal, stateless services

## Building blocks (revision checklist)
- [ ] Load balancing (L4/L7, algorithms)
- [ ] Caching (strategies, eviction, invalidation, stampede)
- [ ] Databases: SQL vs NoSQL, indexing, replication, sharding — see [Databases](../05-databases/README.md)
- [ ] Message queues & streaming (Kafka, SQS, RabbitMQ)
- [ ] CDN & object storage
- [ ] API design (REST, gRPC, GraphQL), pagination, **idempotency**
- [ ] Rate limiting
- [ ] Consistent hashing
- [ ] Service discovery & API gateway

## Reliability & distributed systems (revision checklist)
- [ ] Replication & leader election
- [ ] Consensus (Raft/Paxos at a high level)
- [ ] Distributed transactions: 2PC, Saga, transactional outbox (see [transactions note](../02-languages/java/06-spring-boot/02-proxies-transactions-async.md#44-other-attributes-and-rules))
- [ ] Retries, backoff, circuit breakers, bulkheads ([async error handling](../02-languages/java/03-concurrency/03-async-error-handling-http.md))
- [ ] Observability: logs, metrics, traces
