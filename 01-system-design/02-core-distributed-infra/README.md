# HLD — Core Distributed Infrastructure

[← Back to System Design](../README.md)

These are the **reusable building blocks** behind the other designs. Learn them first.

| Done | System | Hardest part (deep dive) | Key concepts to cover |
|---|---|---|---|
| ☐ | URL shortener | unique short codes at scale + redirect latency | base62 encoding, ID generation (counter vs hash vs Snowflake), cache for hot links, 301 vs 302, analytics off the hot path |
| ☐ | **API rate limiter** | accurate limits across many nodes | token bucket, leaky bucket, fixed vs **sliding window**, Redis atomic ops (Lua), per-user/IP/key limits, fail-open vs fail-closed |
| ☐ | Distributed cache (Redis-style) | partitioning and failure handling | **consistent hashing** + virtual nodes, replication, eviction (LRU/LFU), cache-aside vs write-through, stampede protection, hot keys |
| ☐ | CDN | serving content near users | edge caching, cache invalidation/TTL, origin shield, push vs pull, anycast/DNS routing |
| ☐ | Distributed notification system | reliable fan-out to many channels | queues per channel, retries + dead-letter queue, de-duplication, user preferences, **back-pressure**, rate limits per provider, templating |
| ☐ | Distributed job scheduler | run each job exactly once (effectively) | leader election/leases, sharded timers, persistent job store, retries with backoff, idempotent jobs, missed-run handling |
| ☐ | Distributed ID generator | unique, roughly time-ordered ids without coordination | **Snowflake** layout (timestamp + machine id + sequence), **clock skew** handling, ULID/UUIDv7, ticket servers |
| ☐ | Distributed hit counter | high write rate with bounded accuracy | sharded counters, local aggregation then flush, approximate counting, windowed buckets; companion to the [LLD hit counter](../../04-low-level-design/07-hit-counter/README.md) |

## Checklist of concepts
- [ ] Consistent hashing (why virtual nodes) - [ ] Token bucket vs sliding window - [ ] Snowflake bit layout
- [ ] Fan-out queues & back-pressure - [ ] Clock skew and why wall clocks lie
- [ ] Idempotent consumers & dead-letter queues

## Links in this repo
[Concurrent collections](../../02-languages/java/02-collections/05-concurrent-collections.md) · [LRU/LFU](../../03-dsa/06-data-structure-design/README.md) · [Resilience patterns](../../02-languages/java/03-concurrency/03-async-error-handling-http.md)
