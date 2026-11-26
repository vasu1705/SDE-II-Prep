# Java — Design Patterns & LLD

[← Back to Java](../README.md)

> [!NOTE]
> **Status:** drafted by background writers. All 31 runnable code blocks (`// Run:`) were executed on JDK 21 and passed. The notes are very long (up to ~87 KB) and have **not been read line by line**. For the practice problems with task lists, see [04-low-level-design](../../../04-low-level-design/README.md).

| # | Note | You will learn |
|---|------|----------------|
| 1 | [SOLID & OOP design](01-solid-and-oop-design.md) | each SOLID principle as *violation → refactor*, composition over inheritance, coupling/cohesion, DI by hand vs Spring, tell-don't-ask, immutability, how modern Java changes classic patterns, code smells to critique |
| 2 | [Design patterns](02-design-patterns.md) | Singleton, Factory, Builder, Strategy, Observer, Template Method, Chain of Responsibility, Command, State, Iterator, Visitor vs sealed + `switch`, Null Object, Decorator, Adapter, Facade, Proxy (runnable JDK proxy), DI, Retry & Circuit Breaker, plus a pattern → intent → JDK/Spring cheat sheet and scenario questions |
| 3 | [LLD interview problems](03-lld-interview-problems.md) | the 35-minute approach plus worked **Parking Lot, Rate Limiter, Vending Machine, thread-safe LRU + TTL cache** |

## Reference solutions for the LLD task folders
- Vending Machine → [worked solution](03-lld-interview-problems.md#3-vending-machine-state-pattern) · task: [LLD 3](../../../04-low-level-design/03-vending-machine/README.md)
- Rate limiter (token bucket, sliding window) → [worked solution](03-lld-interview-problems.md#2-rate-limiter-token-bucket-sliding-window-fixed-window) · related: [Hit Counter](../../../04-low-level-design/07-hit-counter/README.md), [HLD rate limiter](../../../01-system-design/02-core-distributed-infra/README.md)
- Thread-safe LRU + TTL → [worked solution](03-lld-interview-problems.md#4-thread-safe-lru--ttl-cache) · related: [LRU/LFU](../../../03-dsa/06-data-structure-design/README.md)

## Revision checklist
- [ ] Give a violation and a fix for each SOLID letter
- [ ] Implement Strategy with a lambda and State with a sealed interface
- [ ] Explain Singleton pitfalls (double-checked locking, tests)
- [ ] Explain JDK proxies vs Spring AOP proxies
- [ ] Run a 35-minute LLD round on one problem end to end
