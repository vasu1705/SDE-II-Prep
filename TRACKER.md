# Revision Tracker

Single place to see what is **written** (✅), **partly covered** (🟡) and **still to write** (⏳), mapped to the five tracks.
Tick the box when *you* have revised a topic (not just when the note exists).

Legend: ✅ note exists and code is verified · 🟡 touched inside another note · ⏳ planned

---

## 1. Concurrency & multithreading — *highest priority*

| Done | Topic | Status | Where |
|---|---|---|---|
| - [ ] | `volatile` (visibility ≠ atomicity), `synchronized`, `ReentrantLock`, atomics, deadlock | ✅ | [Locks, volatile & deadlocks](02-languages/java/03-concurrency/04-locks-volatile-deadlock.md) |
| - [ ] | Executors, `ThreadPoolExecutor` internals, sizing, rejection, `submit` vs `execute` | ✅ | [Executors & thread pools](02-languages/java/03-concurrency/01-executors-thread-pools.md) |
| - [ ] | `Callable` / `Future` / `CompletableFuture` composition | ✅ | [CompletableFuture](02-languages/java/03-concurrency/02-completablefuture.md) |
| - [ ] | **Async error handling**, `try/catch/finally` in async code, HTTP client, `IOException` vs custom exceptions, retries, timeouts | ✅ | [Async error handling & HTTP calls](02-languages/java/03-concurrency/03-async-error-handling-http.md) |
| - [ ] | Virtual threads (Java 21) vs platform threads | ✅ | [Virtual threads](02-languages/java/03-concurrency/05-virtual-threads.md) |
| - [ ] | `ConcurrentHashMap` (CAS + per-bin lock), blocking queues, copy-on-write | ✅ | [Concurrent collections](02-languages/java/02-collections/05-concurrent-collections.md) |
| - [ ] | Java Memory Model / happens-before in depth, `ThreadLocal` | 🟡 | basics in the locks note; `ThreadLocal` leak in [Memory model](02-languages/java/01-java-basics/01-memory-model.md) |

## 2. JVM internals & garbage collection

| Done | Topic | Status | Where |
|---|---|---|---|
| - [ ] | Heap layout: Eden/Survivor/Old, Metaspace, TLAB, GC roots, reachability | ✅ | [Memory model](02-languages/java/01-java-basics/01-memory-model.md) |
| - [ ] | Memory-leak patterns (static maps, unclosed resources, `ThreadLocal`, mutated keys) | ✅ | [Memory model §6](02-languages/java/01-java-basics/01-memory-model.md), [equals & hashCode](02-languages/java/02-collections/02-equals-hashcode.md) |
| - [ ] | Collectors compared: Serial / Parallel / **G1** / **ZGC** / Shenandoah, pauses, reading GC logs | ⏳ | planned: `04-jvm-internals/` |
| - [ ] | Class loading, JIT & tiered compilation, escape analysis | ⏳ | |
| - [ ] | Heap dumps, thread dumps, JFR, diagnosing leaks and high CPU | ⏳ | |

## 3. Spring Boot internals & JPA

> Spring notes are **lean and not executed** (written from standard Boot 3.x behaviour); run key claims before relying on them.

| Done | Topic | Status | Where |
|---|---|---|---|
| - [ ] | IoC container, DI styles, scopes, bean lifecycle, auto-configuration, config | ✅ | [IoC, DI & auto-configuration](02-languages/java/06-spring-boot/01-ioc-di-and-auto-configuration.md) |
| - [ ] | Proxies & AOP: why `@Transactional`/`@Async`/`@Cacheable` fail on self-invocation & private methods; rollback rules, propagation, isolation | ✅ | [Proxies, transactions & async](02-languages/java/06-spring-boot/02-proxies-transactions-async.md) |
| - [ ] | JPA/Hibernate: N+1 (`JOIN FETCH`, `@EntityGraph`), LAZY vs EAGER, open-in-view, locking | ✅ | [JPA & Hibernate](02-languages/java/06-spring-boot/03-jpa-hibernate.md) |
| - [ ] | `@RestControllerAdvice`, `@Valid`, Spring Security filter chain + JWT, test slices, Actuator | ✅ | [REST, errors, security & testing](02-languages/java/06-spring-boot/04-rest-errors-security-testing.md) |
| - [ ] | Spring Boot interview Q&A (45 + 8 scenarios) | ✅ | [Q&A sheet](02-languages/java/06-spring-boot/05-spring-boot-interview-qa.md) |
| - [ ] | Runnable, verified Spring example projects | ⏳ | |
| - [ ] | Maven / Gradle packaging & dependency management (*not in this repo yet*) | ⏳ | |

## 4. Modern Java (8 → 21)

| Done | Topic | Status | Where |
|---|---|---|---|
| - [ ] | Functional interfaces, `map` vs `flatMap`, `groupingBy`, when *not* to use `parallelStream()` | ✅ | [Lambdas, streams & Optional](02-languages/java/01-java-basics/07-lambdas-streams-optional.md) |
| - [ ] | `Optional`: `orElse` vs `orElseGet`, don't use as field/parameter | ✅ | same note |
| - [ ] | Records, sealed types, pattern-matching `switch`, text blocks, sequenced collections | ✅ | [Modern Java](02-languages/java/01-java-basics/08-modern-java.md) |
| - [ ] | **Which feature to use when** (records vs classes, streams vs loops, collections, `Optional` vs exceptions vs `Result`) | ✅ | [Choosing the right tool](02-languages/java/01-java-basics/09-choosing-the-right-tool.md) |

## 5. DSA patterns (applied in Java)

| Done | Topic | Status | Where |
|---|---|---|---|
| - [ ] | Collections ↔ DSA pairing (HashMap counting, prefix sums, Top-K heap, LRU) | 🟡 | [Collections practice problems](02-languages/java/02-collections/06-practice-problems.md) |
| - [ ] | Two pointers & sliding window | ⏳ | [DSA index](03-dsa/README.md) |
| - [ ] | Monotonic stack/queue (`ArrayDeque`) | ⏳ | |
| - [ ] | Heaps: Top-K, Merge-K (`PriorityQueue`) | 🟡 | Top-K done; Merge-K ⏳ |
| - [ ] | Trees & graphs: BFS/DFS, topological sort, Dijkstra | ⏳ | |
| - [ ] | Binary search on answer, 1D/2D DP | ⏳ | |

## 6. Target interview checklist (from the shared posts)

Task lists exist for every item; solutions come later, one at a time. Plan: [STUDY-PLAN.md](STUDY-PLAN.md).

| Pillar | Item | Status | Where |
|---|---|---|---|
| **DSA ⭐** | LRU / LFU | 🟡 LRU reference exists; LFU ⏳ | [data structure design](03-dsa/06-data-structure-design/README.md) |
| DSA ⭐ | Trapping Rain Water | ⏳ | [arrays & two pointers](03-dsa/01-arrays-sliding-window-two-pointers/README.md) |
| DSA ⭐ | Kth Largest in a Stream | ⏳ | [heaps & streams](03-dsa/02-heaps-and-streams/README.md) |
| DSA ⭐ | Word Break (DP + Trie) | ⏳ | [DP & tries](03-dsa/05-dp-and-tries/README.md) |
| DSA ⭐ | Clone Graph (+ random pointers) | ⏳ | [graphs & trees](03-dsa/04-graphs-and-trees/README.md) |
| DSA ⭐ | Median of Two Sorted Arrays | ⏳ | [binary search](03-dsa/03-binary-search/README.md) |
| DSA | Remaining pattern problems (sliding window, heaps, binary search on answer, graphs, LIS, autocomplete) | ⏳ | [DSA index](03-dsa/README.md) |
| **LLD** | Inventory, Shopping Cart, Vending Machine, Library, Order State Machine, Logging, Hit Counter, Autocomplete | ⏳ task READMEs | [LLD](04-low-level-design/README.md) |
| **HLD** | E-commerce/fintech, core infra, social/real-time, storage/search, SSH key rotation | ⏳ task READMEs | [System design](01-system-design/README.md) |
| **SQL** | Order schema, clustered vs non-clustered, inventory consistency, ACID | ⏳ task README (JPA locking/isolation 🟡 in Spring notes) | [Databases](05-databases/README.md) |
| **Concurrency/JVM** | Race conditions, synchronization, `happens-before` | ✅ | [locks note](02-languages/java/03-concurrency/04-locks-volatile-deadlock.md) |
| Concurrency/JVM | Thread lifecycle (states) | 🟡 | [primer](02-languages/java/03-concurrency/00-concurrency-from-scratch.md) |
| Concurrency/JVM | Prevent overselling under concurrent requests | ⏳ | planned Java note |
| Concurrency/JVM | `CompletableFuture` vs `ExecutorService` | 🟡 covered in two notes; one-page comparison ⏳ | [executors](02-languages/java/03-concurrency/01-executors-thread-pools.md), [CompletableFuture](02-languages/java/03-concurrency/02-completablefuture.md) |
| Concurrency/JVM | JVM tuning for a checkout service (heap, G1/ZGC, GC logs) | ⏳ | planned |
| **Behavioral** | 4 STAR stories | ⏳ templates | [Behavioral](06-behavioral/README.md) |

## Already finished (from the original list)

- ✅ Core essentials — [Java Basics](02-languages/java/01-java-basics/README.md)
- ✅ Collections — [Collections](02-languages/java/02-collections/README.md)
- ✅ `HashMap` internals — [HashMap internals](02-languages/java/02-collections/03-hashmap-internals.md)

> **Note on Maven/Gradle:** the earlier discussion mentioned bundling as done, but there is no Maven/Gradle note in this repo yet, so it is tracked as ⏳ above. Skip it if you have your own notes elsewhere.
