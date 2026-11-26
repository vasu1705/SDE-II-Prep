# Java

[← Back to languages](../README.md)

Baseline: **Java 21 (LTS)**. All runnable code in these notes was compiled and run on JDK 21 (what "runnable" means and how to run it: [root README](../../README.md#how-to-run-the-code-samples-runnable-defined); Spring notes are the exception and are unexecuted).
Each note follows the same shape: *analogy → mechanism → runnable code → pitfalls → interview Q&A → predict-the-output*.

## Sections

| # | Section | Status | Highlights |
|---|---------|--------|------------|
| 1 | [Java Basics](01-java-basics/README.md) | ✅ 9 notes | memory model, wrappers & `==`, strings, OOP dispatch & init order, exceptions, generics & PECS, streams, records/sealed/pattern matching, **which feature to use when** |
| 2 | [Collections](02-collections/README.md) | ✅ 6 notes | `equals`/`hashCode`, `HashMap` internals, LRU/`TreeMap`, concurrent collections, 16 practice problems |
| 3 | [Concurrency & Async](03-concurrency/README.md) | ✅ 5 notes | executors, `CompletableFuture`, **async error handling & HTTP calls**, locks/`volatile`/deadlocks, virtual threads |
| 4 | [JVM internals & performance](04-jvm-internals/README.md) | ✅ 3 notes (drafted; code run, prose not reviewed line by line) | class loading & JIT, G1/ZGC & real GC logs, production diagnosis playbook |
| 5 | [Spring Boot](06-spring-boot/README.md) | ✅ 5 notes (lean; **not executed**, see note) | IoC & lifecycle, proxies/`@Transactional`/`@Async` traps, JPA & N+1, REST errors/Security/JWT/testing, 45+8 Q&A |
| 6 | [Design patterns & SOLID in Java](07-design-patterns-and-lld/README.md) | ✅ 3 notes (drafted; code run, prose not reviewed line by line) | SOLID, 18 patterns, worked LLD problems |
| 7 | Testing (JUnit 5, Mockito) | ⏳ planned | |
| 8 | [Miscellaneous problems & gotchas](09-java-gotchas/README.md) | 🟡 1 note (drafted); `java.time`/IO/regex and a rapid-fire sheet still to write | puzzlers, "what happens if…" |

Progress across all tracks: see the [Revision Tracker](../../TRACKER.md).

## Still to write in Concurrency
- [ ] `ThreadLocal` in depth, `ReadWriteLock`/`StampedLock` worked examples
- [ ] Producer–consumer, rate limiter, thread-safe cache — coding problems
- [ ] Structured concurrency (`StructuredTaskScope`) once it leaves preview

## Planned: JVM internals & performance
- [ ] Class loading & class-loader hierarchy
- [ ] Garbage collectors: Serial, Parallel, G1, ZGC, Shenandoah; reading GC logs
- [ ] JIT, tiered compilation, escape analysis, inlining
- [ ] Heap/thread dumps, JFR, async-profiler; diagnosing leaks & high CPU
- [ ] JVM flags that matter in containers

## Interview checklist items still needing a Java note
- [x] Thread lifecycle (states and transitions): [Runnable, Callable & threads §8](03-concurrency/00-runnable-callable-and-threads.md#8-thread-lifecycle-the-states)
- [ ] Preventing overselling under concurrent requests (app lock, Redis Lua/atomic decrement, DB row lock)
- [ ] `CompletableFuture` vs `ExecutorService` one-page comparison
- [ ] JVM tuning for a high-throughput checkout service (heap sizing, G1 vs ZGC, pause targets, GC logs)

## Spring Boot — what's left
- [ ] Verified, runnable example projects for the Spring demos (Maven + H2 + MockMvc)
- [ ] MVC vs WebFlux; Kafka/RabbitMQ with Spring
- [ ] Spring Boot 4 / Framework 7 migration notes
