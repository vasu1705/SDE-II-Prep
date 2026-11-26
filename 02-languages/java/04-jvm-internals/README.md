# Java — JVM Internals & Performance

[← Back to Java](../README.md)

> [!NOTE]
> **Status:** drafted by background writers. The runnable code blocks (`// Run:`) were executed on JDK 21 (all passed except the deliberate OOM demo, which is meant to throw `OutOfMemoryError`). The notes are long and have **not been read line by line**; treat the prose as a draft and report anything that looks wrong.

| # | Note | You will learn |
|---|------|----------------|
| 1 | [Class loading & the JIT](01-class-loading-and-jit.md) | class lifecycle and lazy initialisation (with proof), loader hierarchy and parent delegation, loader leaks, interpreter → C1 → C2, why naive benchmarks lie, CDS/native-image overview |
| 2 | [Garbage collectors](02-garbage-collectors.md) | what a GC must do, Serial/Parallel/**G1**/**ZGC**/Shenandoah compared, key flags, **reading real GC logs**, the whole `OutOfMemoryError` family reproduced, a tuning workflow |
| 3 | [Diagnosing production issues](03-diagnosing-production-issues.md) | `jcmd`/`jstack`/JFR toolbox, reading a thread dump, finding a leak with histogram snapshots, a playbook per symptom, container tips, "first 10 minutes" checklist |

Related: [Memory model basics](../01-java-basics/01-memory-model.md) · [Locks & deadlocks](../03-concurrency/04-locks-volatile-deadlock.md)

## Revision checklist
- [ ] Explain when a class is initialised and give three triggers
- [ ] Explain tiered compilation and why you warm up before measuring
- [ ] Compare G1 and ZGC and pick one for a latency-sensitive service
- [ ] Read a GC log line (before → after, pause time) and say what it means
- [ ] Walk through "high CPU / memory leak / hang" triage in order
- [ ] Say what `-XX:MaxRAMPercentage` does in a container
