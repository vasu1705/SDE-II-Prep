# LLD 6 — Logging Framework

[← Back to LLD](../README.md) · Status: ☐ not started

## Requirements
- Log levels (`TRACE < DEBUG < INFO < WARN < ERROR`); a logger drops messages below its configured level.
- Multiple **sinks/appenders**: console, file, and **async** (non-blocking) delivery.
- Pluggable **formatters** (plain text, JSON); per-logger configuration; thread-safe.

## Entities
`Logger`, `LogLevel` (enum), `LogRecord(level, message, timestamp, thread, throwable)`, `Appender` interface (`ConsoleAppender`, `FileAppender`, `AsyncAppender`), `Formatter`, `LoggerFactory`/registry.

## Patterns to apply
- **Singleton / registry** for the logger factory (and why static singletons hurt tests), **Chain of Responsibility** for level filtering across appenders, **Strategy** for formatters, **Decorator** for `AsyncAppender` wrapping another appender, **Observer** for fan-out to several appenders.

## Concurrency (the interesting part)
- Async logging: producers push to a bounded `BlockingQueue`, one consumer thread writes. Decide the **overflow policy** (block, drop oldest, drop newest) and what happens on shutdown (**drain** the queue).
- Ordering guarantees, file-writer thread-safety, and rolling files by size/time.
- Links: [producer–consumer with `BlockingQueue`](../../02-languages/java/02-collections/05-concurrent-collections.md), [executors](../../02-languages/java/03-concurrency/01-executors-thread-pools.md).

## Extension questions
Structured/MDC context, sampling, log rotation, remote sinks with retry, dynamic level changes at runtime.

## Test checklist
- [ ] Level filtering at each threshold
- [ ] Two appenders receive the same record
- [ ] Async appender: no loss with a slow sink when policy = block; shutdown drains pending records

## Solution
_(add `src/` and links here)_
