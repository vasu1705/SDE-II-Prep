# Java

[← Back to languages](../README.md)

Baseline: **Java 21 (LTS)**. All runnable code in these notes was compiled and run on JDK 21.
Each note follows the same shape: *analogy → mechanism → runnable code → pitfalls → interview Q&A → predict-the-output*.

## Sections

| # | Section | Status | Highlights |
|---|---------|--------|------------|
| 1 | [Java Basics](01-java-basics/README.md) | ✅ 8 notes | memory model, wrappers & `==`, strings, OOP dispatch & init order, exceptions, generics & PECS, streams, records/sealed/pattern matching |
| 2 | [Collections](02-collections/README.md) | ✅ 6 notes | `equals`/`hashCode`, `HashMap` internals, LRU/`TreeMap`, concurrent collections, 16 practice problems |
| 3 | Concurrency | ⏳ planned | see checklist below |
| 4 | JVM internals & performance | ⏳ planned | see checklist below |
| 5 | Spring Boot | ⏳ planned | see checklist below |
| 6 | Design patterns & SOLID in Java | ⏳ planned | |
| 7 | Testing (JUnit 5, Mockito) | ⏳ planned | |
| 8 | Miscellaneous problems & gotchas | ⏳ planned | puzzlers, "what happens if…" |

## Planned: Concurrency
- [ ] Java Memory Model, happens-before, `volatile`
- [ ] `synchronized`, `ReentrantLock`, `ReadWriteLock`, `StampedLock`
- [ ] Atomics, CAS, `LongAdder`
- [ ] Executors, thread pools sizing, `ThreadPoolExecutor` internals, rejection policies
- [ ] `CompletableFuture` composition & error handling
- [ ] Deadlock / livelock / starvation, detecting with thread dumps
- [ ] Virtual threads (Loom), structured concurrency
- [ ] Producer–consumer, rate limiter, thread-safe cache — coding problems

## Planned: JVM internals & performance
- [ ] Class loading & class-loader hierarchy
- [ ] Garbage collectors: Serial, Parallel, G1, ZGC, Shenandoah; reading GC logs
- [ ] JIT, tiered compilation, escape analysis, inlining
- [ ] Heap/thread dumps, JFR, async-profiler; diagnosing leaks & high CPU
- [ ] JVM flags that matter in containers

## Planned: Spring Boot
- [ ] IoC container, DI styles, bean scopes & lifecycle, `@Configuration` proxying
- [ ] Auto-configuration: how `@SpringBootApplication` works, conditions, writing a starter
- [ ] `@Transactional`: proxies, propagation, isolation, self-invocation & checked-exception pitfalls
- [ ] REST: controllers, validation, `@ControllerAdvice`, `ProblemDetail`, pagination, idempotency
- [ ] Data: Spring Data JPA, N+1 problem, lazy loading, `open-in-view`, optimistic locking
- [ ] Security: filter chain, JWT/OAuth2 resource server, method security, CSRF/CORS
- [ ] Configuration: profiles, `@ConfigurationProperties`, externalised config, secrets
- [ ] Observability: Actuator, Micrometer, structured logging, tracing
- [ ] Caching, scheduling, async, events, AOP
- [ ] Testing slices: `@WebMvcTest`, `@DataJpaTest`, Testcontainers
- [ ] MVC vs WebFlux; Kafka/RabbitMQ with Spring
- [ ] Production readiness: graceful shutdown, health probes, connection pools (HikariCP)
