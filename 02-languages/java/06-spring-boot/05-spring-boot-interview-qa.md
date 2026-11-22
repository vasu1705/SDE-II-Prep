# Spring Boot — Interview Rapid-Fire & Scenario Questions

> **Level:** SDE-II / SDE-III · **Area:** Spring Boot 3.x · **Prev:** [REST, errors, security & testing](04-rest-errors-security-testing.md)

Short answers (2–4 lines) with a link to the deeper note. Read the answer aloud before expanding the details. Unverified-by-execution notice from the other Spring notes applies here too.

## A. Core / IoC / Boot

<details><summary><b>1.</b> What does <code>@SpringBootApplication</code> do?</summary>

Combines `@SpringBootConfiguration`, `@EnableAutoConfiguration` and `@ComponentScan` (scans the main class's package and below). → [note 01](01-ioc-di-and-auto-configuration.md#6-auto-configuration-how-boot-just-works)
</details>

<details><summary><b>2.</b> Constructor vs field injection?</summary>

Constructor: immutable, required, testable, cycles fail fast. Field: hidden dependencies, needs reflection to test. Use constructor. → [01](01-ioc-di-and-auto-configuration.md#1-di-styles)
</details>

<details><summary><b>3.</b> Spring singleton vs GoF singleton? Thread safety?</summary>

One per container, not per JVM; shared by all threads so must be stateless/thread-safe. → [01](01-ioc-di-and-auto-configuration.md#3-scopes)
</details>

<details><summary><b>4.</b> Bean lifecycle order?</summary>

Constructor → injection → Aware → BPP before → `@PostConstruct` → `afterPropertiesSet` → init-method → BPP after (proxies) → … → `@PreDestroy` → `destroy`. → [01](01-ioc-di-and-auto-configuration.md#4-bean-lifecycle--the-order-you-must-know)
</details>

<details><summary><b>5.</b> How does auto-configuration back off?</summary>

`@ConditionalOnMissingBean` (and other conditions) — your own bean suppresses the default. See why with `--debug`. → [01](01-ioc-di-and-auto-configuration.md#6-auto-configuration-how-boot-just-works)
</details>

<details><summary><b>6.</b> Config precedence and profiles?</summary>

Command-line > system props > env vars > profile files > `application.yml` > defaults. `spring.profiles.active`, `@Profile`. → [01](01-ioc-di-and-auto-configuration.md#7-externalized-configuration)
</details>

<details><summary><b>7.</b> <code>@ConfigurationProperties</code> vs <code>@Value</code>?</summary>

Typed, grouped, validated, relaxed-binding vs single scattered values. Prefer `@ConfigurationProperties` (records work in Boot 3).
</details>

<details><summary><b>8.</b> How do you handle circular dependencies?</summary>

Redesign (extract a third bean / events); `@Lazy` as a workaround; Boot 2.6+ forbids them by default. → [01](01-ioc-di-and-auto-configuration.md#5-circular-dependencies)
</details>

<details><summary><b>9.</b> Prototype bean inside a singleton?</summary>

Injected once. Use `ObjectProvider`, `@Lookup` or a scoped proxy.
</details>

<details><summary><b>10.</b> What is a starter?</summary>

A dependency bundle (e.g. `spring-boot-starter-web`); the auto-configuration module reacts to what's on the classpath.
</details>

## B. Proxies, AOP, async, caching

<details><summary><b>11.</b> How does Spring implement <code>@Transactional</code>?</summary>

A proxy (CGLIB by default) with a `TransactionInterceptor` begins/commits/rolls back around the call. → [02](02-proxies-transactions-async.md#1-how-the-proxy-is-built-and-called)
</details>

<details><summary><b>12.</b> Why does <code>@Transactional</code>/<code>@Async</code>/<code>@Cacheable</code> not work on <code>this.method()</code>?</summary>

The call bypasses the proxy. Move to another bean or restructure. → [02](02-proxies-transactions-async.md#2-what-the-proxy-cant-see-and-the-fixes)
</details>

<details><summary><b>13.</b> JDK vs CGLIB proxy?</summary>

Interface-based vs subclass-based; Boot defaults to CGLIB — no `final` classes/methods.
</details>

<details><summary><b>14.</b> Name the AOP terms.</summary>

Aspect, join point (method execution in Spring AOP), pointcut, advice (`@Before/@After/@Around…`), weaving (runtime proxies). → [02](02-proxies-transactions-async.md#3-aop-vocabulary--writing-your-own-aspect)
</details>

<details><summary><b>15.</b> How do you handle exceptions in <code>@Async</code>?</summary>

Return `CompletableFuture` (handle on it) or register an `AsyncUncaughtExceptionHandler` for `void`. → [02](02-proxies-transactions-async.md#5-async)
</details>

<details><summary><b>16.</b> What's the default executor for <code>@Async</code> and the risk?</summary>

Boot's `applicationTaskExecutor` (core 8, unbounded queue). Configure a bounded, named executor; consider virtual threads.
</details>

<details><summary><b>17.</b> <code>@Scheduled</code> gotchas?</summary>

Single-thread scheduler by default; runs on every instance (use ShedLock/Quartz); exceptions are logged and the schedule continues.
</details>

<details><summary><b>18.</b> <code>@Cacheable</code> gotchas?</summary>

Proxy rules; default cache has no TTL/size bound; need Caffeine/Redis; cache stampede → `sync = true`.
</details>

## C. Transactions

<details><summary><b>19.</b> Default rollback behaviour?</summary>

Unchecked exceptions and `Error` roll back; checked commit unless `rollbackFor`. → [02](02-proxies-transactions-async.md#41-rollback-rules-the-1-interview-trap)
</details>

<details><summary><b>20.</b> REQUIRED vs REQUIRES_NEW vs NESTED?</summary>

Join / suspend-and-start-new (own connection, independent commit) / savepoint within the same transaction.
</details>

<details><summary><b>21.</b> What is <code>UnexpectedRollbackException</code>?</summary>

Inner participant marked the transaction rollback-only, outer swallowed the exception and tried to commit.
</details>

<details><summary><b>22.</b> Isolation levels and the default?</summary>

READ_UNCOMMITTED < READ_COMMITTED < REPEATABLE_READ < SERIALIZABLE; `DEFAULT` = the DB's default (READ COMMITTED on Postgres/Oracle/SQL Server, REPEATABLE READ on MySQL InnoDB). → [02](02-proxies-transactions-async.md#43-isolation)
</details>

<details><summary><b>23.</b> What does <code>readOnly=true</code> do?</summary>

Hint: no dirty-check flush, possible replica routing; not a write guard.
</details>

<details><summary><b>24.</b> Why avoid HTTP calls inside a transaction?</summary>

Holds a DB connection/locks during remote latency → pool exhaustion. Use outbox/after-commit.
</details>

<details><summary><b>25.</b> What is the dual-write problem?</summary>

DB write + message publish can't be atomic; fix with the transactional outbox or after-commit events.
</details>

## D. JPA / Hibernate

<details><summary><b>26.</b> What is the persistence context / dirty checking?</summary>

Per-transaction cache of managed entities; changes flushed at commit without `save()`. → [03](03-jpa-hibernate.md#2-entity-states-and-dirty-checking)
</details>

<details><summary><b>27.</b> N+1 — cause, detection, fixes?</summary>

Lazy association per parent. Detect via SQL logs/statistics; fix with fetch join, `@EntityGraph`, batch size, DTO projection. → [03](03-jpa-hibernate.md#4-the-n1-problem-and-its-fixes)
</details>

<details><summary><b>28.</b> LAZY vs EAGER defaults?</summary>

To-one eager, to-many lazy. Make all lazy; fetch explicitly.
</details>

<details><summary><b>29.</b> <code>LazyInitializationException</code>?</summary>

Lazy access outside a session. Fetch in the query or map to DTOs inside the transaction. → [03](03-jpa-hibernate.md#lazyinitializationexception)
</details>

<details><summary><b>30.</b> open-in-view?</summary>

Default true; keeps session through the web layer, hides N+1, holds connections. Turn off. → [03](03-jpa-hibernate.md#6-open-session-in-view-springjpaopen-in-view)
</details>

<details><summary><b>31.</b> Optimistic vs pessimistic locking?</summary>

`@Version` + retry vs `SELECT … FOR UPDATE`. → [03](03-jpa-hibernate.md#7-locking-and-concurrency)
</details>

<details><summary><b>32.</b> Fetch join with pagination?</summary>

In-memory pagination (HHH90003004). Paginate ids first or use batch fetching.
</details>

<details><summary><b>33.</b> Why not expose entities from controllers?</summary>

Lazy proxies, cycles, leaking/over-posting fields, coupling API to schema. Use DTOs/records.
</details>

<details><summary><b>34.</b> <code>Page</code> vs <code>Slice</code>?</summary>

Page runs an extra COUNT; Slice only knows "has next". Deep offsets are slow → keyset pagination.
</details>

<details><summary><b>35.</b> IDENTITY vs SEQUENCE?</summary>

IDENTITY disables insert batching; SEQUENCE (allocation size) allows it.
</details>

## E. REST / Security / Testing / Production

<details><summary><b>36.</b> Global exception handling?</summary>

`@RestControllerAdvice` + `ProblemDetail`; log details, return safe messages. → [04](04-rest-errors-security-testing.md#3-global-error-handling-with-problemdetail)
</details>

<details><summary><b>37.</b> <code>@Valid</code> vs <code>@Validated</code>?</summary>

`@Valid` triggers/cascades; `@Validated` adds groups and method-level validation.
</details>

<details><summary><b>38.</b> Status codes for upstream failure?</summary>

Timeout 504; upstream failure 502/503; never 500 for expected upstream errors.
</details>

<details><summary><b>39.</b> 401 vs 403?</summary>

401 = not authenticated; 403 = authenticated but not allowed.
</details>

<details><summary><b>40.</b> How does JWT auth work in Spring?</summary>

Resource server: bearer-token filter decodes/verifies the JWT, builds `JwtAuthenticationToken` with authorities, authorisation rules run on it. → [04](04-rest-errors-security-testing.md#stateless-api-with-jwt-resource-server)
</details>

<details><summary><b>41.</b> CSRF vs CORS?</summary>

CSRF: forged cookie-authenticated requests (disable for header-token APIs). CORS: browser rule about cross-origin reads.
</details>

<details><summary><b>42.</b> <code>SecurityContext</code> and threads?</summary>

Thread-local; doesn't propagate to `@Async`/new threads without delegating wrappers.
</details>

<details><summary><b>43.</b> Test slices?</summary>

`@WebMvcTest`, `@DataJpaTest`, `@JsonTest`, `@RestClientTest`; `@SpringBootTest` for end-to-end; `@MockitoBean` for mocks. → [04](04-rest-errors-security-testing.md#6-testing-with-slices)
</details>

<details><summary><b>44.</b> Actuator probes?</summary>

`/actuator/health/liveness` (restart) and `/readiness` (traffic); secure other endpoints. → [04](04-rest-errors-security-testing.md#7-production-readiness-checklist)
</details>

<details><summary><b>45.</b> Graceful shutdown?</summary>

`server.shutdown=graceful` + `spring.lifecycle.timeout-per-shutdown-phase`.
</details>

## F. Scenario questions

<details><summary><b>S1.</b> An endpoint is slow only under load. What do you check?</summary>

1. Metrics: p95/p99 latency, error rate, thread-pool and **Hikari pool** usage (`HikariPool.getConnection` waits). 2. Count **SQL statements per request** (N+1) and slow queries. 3. Thread dump: blocked/waiting threads, lock contention. 4. External calls: timeouts missing? serial instead of parallel? 5. GC logs/heap (pauses, allocation rate). 6. Transaction length (external calls inside tx, open-in-view). 7. Reproduce with a load test, change one thing at a time. → [JPA note](03-jpa-hibernate.md), [thread dumps & deadlocks](../03-concurrency/04-locks-volatile-deadlock.md#6-deadlock-livelock-starvation).
</details>

<details><summary><b>S2.</b> <code>@Transactional</code> isn't rolling back. List suspects.</summary>

Checked exception without `rollbackFor`; exception swallowed; self-invocation/private/`new`; different thread; rollback-only/`UnexpectedRollbackException`; test-managed transaction; non-transactional resource. → [02](02-proxies-transactions-async.md#my-transactional-isnt-rolling-back--suspect-list)
</details>

<details><summary><b>S3.</b> N+1 in production — find and fix?</summary>

Turn on SQL logging/statistics (or a datasource proxy) for the endpoint, count statements, identify the lazy association, fix with `@EntityGraph`/fetch join/batch size/DTO, then add a regression test asserting the statement count. → [03](03-jpa-hibernate.md#4-the-n1-problem-and-its-fixes)
</details>

<details><summary><b>S4.</b> <code>LazyInitializationException</code> in the controller — options and trade-offs?</summary>

Best: map to DTO within a `@Transactional` service/fetch what's needed. OK: entity graph/fetch join. Bad: EAGER everywhere, open-in-view. → [03](03-jpa-hibernate.md#lazyinitializationexception)
</details>

<details><summary><b>S5.</b> Make a call to an external API resilient.</summary>

Shared `RestClient` with connect/read timeouts; translate errors into a domain exception with `retriable`; bounded retries with backoff+jitter for idempotent calls; circuit breaker + bulkhead; fallback; metrics; map failures to 502/503/504. → [04](04-rest-errors-security-testing.md#4-calling-other-services-restclient), [async error handling](../03-concurrency/03-async-error-handling-http.md)
</details>

<details><summary><b>S6.</b> Secure service-to-service calls inside the cluster.</summary>

OAuth2 client-credentials tokens (short-lived JWT, validated by each service as a resource server), mTLS between services/service mesh, least-privilege scopes, network policies, no shared static API keys, rotate secrets, audit logging.
</details>

<details><summary><b>S7.</b> Startup fails with a circular dependency / <code>NoUniqueBeanDefinitionException</code>. What now?</summary>

Read the cycle path in the error; break the cycle (extract a bean, use events). For ambiguity use `@Primary`/`@Qualifier` or inject `List<T>`. → [01](01-ioc-di-and-auto-configuration.md)
</details>

<details><summary><b>S8.</b> You need an email sent after the order is saved, without risking "email sent but order rolled back".</summary>

`@TransactionalEventListener(AFTER_COMMIT)` (or the outbox pattern for guaranteed delivery), with the send performed asynchronously on a bounded executor and failures handled/retried. → [02](02-proxies-transactions-async.md#44-other-attributes-and-rules)
</details>

---
[↑ Back to Spring Boot index](README.md)
