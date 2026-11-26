# LLD 7 — Hit Counter

[← Back to LLD](../README.md) · Status: ☐ not started · Priority: ⭐

## Requirements
- `hit(timestamp)` records a hit; `getHits(now)` returns hits in the last **N seconds** (classic: 300 s).
- High-concurrency writes; **memory must not grow with traffic**.
- Follow-up: scale to millions of requests per second with acceptable accuracy across machines.

## Approaches to compare
| Approach | Memory | `hit` | `getHits` | Notes |
|---|---|---|---|---|
| Queue of timestamps | O(hits in window) | O(1) | O(expired) | simple; memory grows with traffic ✗ |
| **Circular buffer of N one-second buckets** | **O(N)** (fixed) | O(1) | O(N) | each slot stores `(second, count)`; reset a stale slot when its second differs |
| Sliding window with finer buckets | O(N/granularity) | O(1) | O(buckets) | trade accuracy for memory |

## Concurrency design
- Per-slot atomic counters (`AtomicLongArray`) or `LongAdder` per slot to reduce contention; handle the **stale-slot reset race** (two threads resetting the same slot) with a CAS on the slot's timestamp or a lock striped per slot.
- Time source: inject `Clock` for tests; beware clock skew.
- Links: [atomics & `LongAdder`](../../02-languages/java/03-concurrency/04-locks-volatile-deadlock.md#5-atomics-and-cas); related reference: the [rate limiter worked solution](../../02-languages/java/07-design-patterns-and-lld/03-lld-interview-problems.md#2-rate-limiter-token-bucket-sliding-window-fixed-window) (sliding window).

## Scaling follow-up (distributed)
- Per-node counters + periodic aggregation (approximate, eventually consistent); or a sharded counter service; or Redis (`INCR` on per-second keys with TTL, or sorted-set sliding window).
- Accuracy vs cost: exact global counts need coordination; most systems accept small error. See [HLD: distributed hit counter](../../01-system-design/02-core-distributed-infra/README.md).

## Test checklist
- [ ] Hits older than the window are not counted (boundary: exactly N seconds)
- [ ] Multiple hits in the same second; gaps longer than the window (all slots stale)
- [ ] 1M concurrent `hit` calls from many threads give the exact total (single node)

## Solution
_(add `src/` and links here)_
