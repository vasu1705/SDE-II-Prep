# Study Plan

How the six preparation pillars fit together, with links to where each lives in this repo. Pillars: **DSA** and **System Design** (the bulk of most rounds), then **LLD**, **SQL**, **Java concurrency/JVM**, and **Behavioral**.

> Status legend: ✅ written · 🟡 partly covered · ⏳ task list only (solutions to come). Track details in the [Revision Tracker](TRACKER.md).

## 6-week plan

| Week | Focus | Do | Where |
|---|---|---|---|
| **1** | **Overlaps & core internals** | Solve the 6 overlapping DSA problems; revise SQL + concurrency/JVM topics in depth | [DSA ⭐ list](03-dsa/README.md), [Databases](05-databases/README.md), [Concurrency](02-languages/java/03-concurrency/README.md) |
| **2** | Remaining DSA patterns | Sliding window, heaps/streams, binary search — 2 problems/day, 25-minute timer | [Arrays](03-dsa/01-arrays-sliding-window-two-pointers/README.md), [Heaps](03-dsa/02-heaps-and-streams/README.md), [Binary search](03-dsa/03-binary-search/README.md) |
| **3** | Graphs, trees, DP, tries | Remaining graph/tree/DP problems + weighted Trie autocomplete | [Graphs & trees](03-dsa/04-graphs-and-trees/README.md), [DP & tries](03-dsa/05-dp-and-tries/README.md) |
| **4** | **LLD sprint** | Code all 8 problems in the IDE with unit tests; heavy focus on Hit Counter, Inventory, Shopping Cart, Order State Machine | [LLD](04-low-level-design/README.md) |
| **5** | **HLD: core infra & e-commerce** | Whiteboard E-commerce/Payments, Core infra, and the SSH key rotation scenario | [HLD categories 1, 2, 5](01-system-design/README.md) |
| **6** | **HLD real-time + behavioral polish** | Whiteboard Social/Real-time/Storage designs; rehearse 4 behavioral/project narratives aloud | [HLD categories 3, 4](01-system-design/README.md), [Behavioral](06-behavioral/README.md) |

## Week 1 in detail (the highest-ROI week)
1. **DSA (6 problems):** LRU/LFU, Trapping Rain Water, Kth Largest in a Stream, Word Break, Clone Graph, Median of Two Sorted Arrays (plus the Trie autocomplete if time allows).
2. **SQL (4 topics):** Order schema, clustered vs non-clustered indexes, inventory consistency, ACID — [Databases](05-databases/README.md).
3. **Concurrency/JVM (5 topics):**
   - Thread lifecycle, race conditions, synchronization — [primer](02-languages/java/03-concurrency/00-concurrency-from-scratch.md), [Runnable, Callable & thread states](02-languages/java/03-concurrency/00-runnable-callable-and-threads.md), [locks note](02-languages/java/03-concurrency/04-locks-volatile-deadlock.md)
   - Preventing overselling under concurrent requests — ⏳ planned note (see [tracker](TRACKER.md))
   - `CompletableFuture` vs `ExecutorService` — [executors](02-languages/java/03-concurrency/01-executors-thread-pools.md), [CompletableFuture](02-languages/java/03-concurrency/02-completablefuture.md) (a one-page comparison is ⏳)
   - JVM tuning for a high-throughput checkout service — [GC note](02-languages/java/04-jvm-internals/02-garbage-collectors.md) (heap sizing, G1 vs ZGC, GC logs) and [diagnosis playbook](02-languages/java/04-jvm-internals/03-diagnosing-production-issues.md); a checkout-specific summary is ⏳
   - `happens-before` — [locks note §1](02-languages/java/03-concurrency/04-locks-volatile-deadlock.md#1-the-java-memory-model-in-one-page)

## If you only have about a week
Priority order (most interview value per hour):
1. Week-1 list above (overlap DSA + SQL + concurrency/JVM).
2. [Spring Boot Q&A sheet](02-languages/java/06-spring-boot/05-spring-boot-interview-qa.md) and the [async error-handling note](02-languages/java/03-concurrency/03-async-error-handling-http.md).
3. One LLD problem end to end (Inventory or Hit Counter) and one HLD (checkout/flash sale).
4. Write the 4 behavioral stories.

## Daily rhythm that works
- 2 problems under a 25-minute timer (write down what you missed).
- 1 concept from the checklist explained aloud without notes.
- End of week: re-solve two problems you failed earlier.
