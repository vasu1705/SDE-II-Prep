# Locks, `volatile`, Atomics & Deadlocks

> **Level:** SDE-II / SDE-III · **Area:** Java · **Prev:** [Async error handling](03-async-error-handling-http.md) · **Next:** [Virtual threads](05-virtual-threads.md)

## TL;DR

Shared mutable state breaks in three ways — **atomicity** (a read-modify-write interleaves), **visibility** (one thread doesn't see another's write), **ordering** (the JIT/CPU reorder operations). Tools:

| Problem | Tool |
|---|---|
| Visibility + ordering only (a flag, a safely-published reference) | **`volatile`** |
| Atomic single-variable update | **`AtomicInteger/Long/Reference`**, **`LongAdder`** (high contention) |
| Multi-step invariant / critical section | **`synchronized`** or **`ReentrantLock`** |
| Many readers, rare writers | `ReentrantReadWriteLock` / `StampedLock` |
| Avoid the problem | **immutable objects**, confinement (one thread), thread-safe collections |

**`volatile` gives visibility, not atomicity: `volatile int count; count++` is still a race.**

## The analogy: a shared kitchen

- **Visibility** — a whiteboard in the kitchen. Without `volatile`, each cook may be reading a **photocopy** they made earlier (a CPU cache / register) and never notice the board changed. `volatile` = *"always read the real board, and write straight to it."*
- **Atomicity** — "read the egg count, add one, write it back" is **three steps**; two cooks can both read 5 and both write 6. `volatile` doesn't make three steps one. A **lock** (one key to the pantry) or an **atomic** (a "compare-and-swap" button: *"set to 6 only if it's still 5, otherwise tell me"*) does.
- **Deadlock** — Cook A holds the knife and waits for the board; Cook B holds the board and waits for the knife. Nobody can ever proceed.

## 1. The Java Memory Model in one page

Without synchronisation the JVM, JIT and CPU may **reorder** and **cache** — a thread can legally see stale or out-of-order values. The JMM defines **happens-before (HB)** edges; if action A happens-before B, B sees A's effects.

| HB edge | Meaning |
|---|---|
| **Program order** | within a thread, earlier statements HB later ones |
| **Monitor** | `unlock(m)` HB every later `lock(m)` (end of a `synchronized` block → start of the next on the same object) |
| **Volatile** | a **write** of a volatile variable HB every later **read** of it |
| **Thread start/join** | `thread.start()` HB everything in that thread; everything in the thread HB `join()` returning |
| **Executor / Future / CF / BlockingQueue** | submitting HB the task's run; the task HB `get()`; `put` HB the matching `take` |
| **`final` fields** | correctly constructed objects publish their `final` fields safely to any thread |
| Transitivity | A HB B and B HB C ⇒ A HB C |

If two threads touch the same variable, at least one writes, and there's **no HB edge** between them, you have a **data race** — behaviour is undefined (practically: stale reads, torn updates, infinite loops).

## 2. `volatile`: visibility yes, atomicity no

```java
// Run: CounterRace.java
import java.util.concurrent.atomic.*;
import java.util.concurrent.locks.*;

public class CounterRace {
    static final int THREADS = 4, N = 250_000, EXPECTED = THREADS * N;

    static int plain;                                  // no protection
    static volatile int vol;                           // visible, but ++ is read-modify-write
    static int synced;                                 // protected by synchronized
    static int locked;                                 // protected by ReentrantLock
    static final AtomicInteger atomic = new AtomicInteger();
    static final LongAdder adder = new LongAdder();
    static final Object monitor = new Object();
    static final ReentrantLock lock = new ReentrantLock();

    static void runConcurrently(Runnable r) throws Exception {
        Thread[] ts = new Thread[THREADS];
        for (int i = 0; i < THREADS; i++) { ts[i] = new Thread(r); ts[i].start(); }
        for (Thread t : ts) t.join();
    }

    public static void main(String[] args) throws Exception {
        runConcurrently(() -> { for (int i = 0; i < N; i++) plain++; });
        runConcurrently(() -> { for (int i = 0; i < N; i++) vol++; });
        runConcurrently(() -> { for (int i = 0; i < N; i++) synchronized (monitor) { synced++; } });
        runConcurrently(() -> { for (int i = 0; i < N; i++) { lock.lock(); try { locked++; } finally { lock.unlock(); } } });
        runConcurrently(() -> { for (int i = 0; i < N; i++) atomic.incrementAndGet(); });
        runConcurrently(() -> { for (int i = 0; i < N; i++) adder.increment(); });

        System.out.println("expected                = " + EXPECTED);
        System.out.println("plain int               = " + plain  + "   correct? " + (plain == EXPECTED));
        System.out.println("volatile int            = " + vol    + "   correct? " + (vol == EXPECTED));
        System.out.println("synchronized            = " + synced + "   correct? " + (synced == EXPECTED));
        System.out.println("ReentrantLock           = " + locked + "   correct? " + (locked == EXPECTED));
        System.out.println("AtomicInteger           = " + atomic.get() + "   correct? " + (atomic.get() == EXPECTED));
        System.out.println("LongAdder               = " + adder.sum() + "   correct? " + (adder.sum() == EXPECTED));
    }
}
```

Typical output (the two broken counters differ on every run):

```text
expected                = 1000000
plain int               = 318244   correct? false
volatile int            = 402917   correct? false
synchronized            = 1000000   correct? true
ReentrantLock           = 1000000   correct? true
AtomicInteger           = 1000000   correct? true
LongAdder               = 1000000   correct? true
```

`volatile` fixed *nothing* here, because `vol++` is `read → add → write` and two threads interleave between the steps.

### What `volatile` *is* good for

```java
// 1. A stop/ready FLAG written by one thread, read by others
private volatile boolean running = true;
void stop() { running = false; }
void loop() { while (running) { work(); } }

// 2. Publishing an immutable object by replacing a reference
private volatile Config config = new Config(...);   // readers always see a fully-built Config
void reload() { config = loadFromDisk(); }          // safe: single write of a reference

// 3. Double-checked locking singleton — volatile is REQUIRED
private static volatile Holder instance;
static Holder get() {
    Holder h = instance;
    if (h == null) {
        synchronized (Holder.class) {
            h = instance;
            if (h == null) instance = h = new Holder();
        }
    }
    return h;               // (simpler & also safe: initialization-on-demand holder class, or an enum singleton)
}
```

Without `volatile` in (3), another thread could see a non-null `instance` whose fields are not yet initialised (reordering of construction vs publication).

### Visibility bug in action

```java
// Run: Visibility.java
public class Visibility {
    static boolean stopPlain = false;                   // NOT volatile
    static volatile boolean stopVolatile = false;

    public static void main(String[] args) throws Exception {
        Thread a = new Thread(() -> { long n = 0; while (!stopPlain) n++; });       // JIT may hoist the read out of the loop
        Thread b = new Thread(() -> { long n = 0; while (!stopVolatile) n++; });
        a.setDaemon(true); b.setDaemon(true);          // so a stuck thread can't keep the JVM alive
        a.start(); b.start();

        Thread.sleep(500);
        stopPlain = true; stopVolatile = true;         // both flags set at the same moment
        a.join(1000); b.join(1000);

        System.out.println("thread watching the plain flag stopped?    " + !a.isAlive());
        System.out.println("thread watching the volatile flag stopped? " + !b.isAlive());
    }
}
```

```text
thread watching the plain flag stopped?    false
thread watching the volatile flag stopped? true
```

> [!NOTE]
> The plain-flag result is *permitted*, not *guaranteed*: on HotSpot the compiled loop usually caches the flag in a register and spins forever, but with different JIT timing it may happen to stop. "Works on my machine" proves nothing about a data race.

## 3. `synchronized`

```java
public synchronized void deposit(long amt) { balance += amt; }      // locks `this`
public static synchronized void reset() { … }                        // locks the Class object
synchronized (lockObject) { … }                                      // locks any object: prefer a private final lock
```

- Provides **mutual exclusion** *and* the monitor HB edge (visibility of everything done inside).
- **Reentrant**: a thread holding the lock can enter again.
- Released automatically on exception or normal exit — no `finally` needed.
- Use a **`private final Object lock`** rather than `this` so outside code can't lock your monitor.
- **Never call alien/overridable code or do blocking I/O while holding a lock** (deadlock and latency risk).
- `wait()/notify()` require holding the monitor; always `wait` in a `while (!condition)` loop (spurious wakeups). Prefer `BlockingQueue`/`Condition`.
- **Java 21 virtual threads:** blocking inside `synchronized` *pins* the carrier thread (fixed in JDK 24) — see [Virtual threads](05-virtual-threads.md).

## 4. `ReentrantLock` — when `synchronized` isn't enough

```java
private final ReentrantLock lock = new ReentrantLock();

public void transfer() {
    lock.lock();
    try {                       // ALWAYS try/finally — nothing unlocks for you
        // critical section
    } finally {
        lock.unlock();
    }
}

if (lock.tryLock(200, TimeUnit.MILLISECONDS)) {       // don't wait forever
    try { … } finally { lock.unlock(); }
} else {
    // couldn't get it: back off, retry, or fail — this is how you AVOID deadlock
}
```

| Feature | `synchronized` | `ReentrantLock` |
|---|---|---|
| Release | automatic | manual `finally { unlock() }` |
| Try without blocking / with timeout | no | `tryLock()`, `tryLock(t)` |
| Interruptible wait | no | `lockInterruptibly()` |
| Fairness option | no | `new ReentrantLock(true)` (slower, avoids starvation) |
| Multiple wait-sets | one per monitor | many `Condition`s per lock |
| Introspection | limited | `isLocked`, `getQueueLength`… |
| Virtual-thread friendly (Java 21) | pins on blocking | yes (preferred) |

Default to `synchronized` for simple cases; use `ReentrantLock` when you need `tryLock`, timeouts, interruptibility, or conditions.

**Read/write locks:** `ReentrantReadWriteLock` (many readers **or** one writer) pays off only when reads dominate and the critical section is non-trivial; **`StampedLock`** adds optimistic reads (read without locking, then `validate(stamp)`), not reentrant.

## 5. Atomics and CAS

`AtomicInteger.incrementAndGet()` uses a CPU **compare-and-swap**: *"set to `new` only if the current value is still `expected`"* — lock-free, retry-on-conflict:

```java
int prev, next;
do { prev = value.get(); next = prev + 1; }
while (!value.compareAndSet(prev, next));    // retry if another thread changed it in between
```

- **`LongAdder`/`LongAccumulator`**: spread updates over cells to avoid CAS contention — much faster than `AtomicLong` for counters hit by many threads, but `sum()` isn't an atomic snapshot.
- **`AtomicReference<T>`** for lock-free immutable-state swaps.
- **ABA problem:** a value goes A → B → A and a CAS wrongly succeeds; `AtomicStampedReference` adds a version stamp.
- Atomics make **one variable** atomic. Two atomics updated together are **not** atomic as a pair — use a lock, or put both values in one immutable object held by an `AtomicReference`.

## 6. Deadlock, livelock, starvation

**Deadlock needs all four (Coffman) conditions:** mutual exclusion · hold-and-wait · no preemption · circular wait. Break any one to prevent it.

```java
// Run: DeadlockDemo.java
import java.lang.management.*;
import java.util.*;

public class DeadlockDemo {
    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }

    static Thread locker(String name, Object first, Object second) {
        Thread t = new Thread(() -> {
            synchronized (first) { sleep(100); synchronized (second) { /* work */ } }
        }, name);
        t.setDaemon(true);                                   // so the demo JVM can exit
        return t;
    }

    public static void main(String[] args) throws Exception {
        // 1. Opposite lock order -> circular wait
        Object a = new Object(), b = new Object();
        Thread t1 = locker("T1", a, b), t2 = locker("T2", b, a);
        t1.start(); t2.start();
        Thread.sleep(500);

        ThreadMXBean mx = ManagementFactory.getThreadMXBean();
        long[] ids = mx.findDeadlockedThreads();             // what jstack / monitoring tools do
        System.out.println("deadlocked threads: " + (ids == null ? 0 : ids.length));
        List<String> lines = new ArrayList<>();
        for (ThreadInfo ti : mx.getThreadInfo(ids)) lines.add("  " + ti.getThreadName() + " is " + ti.getThreadState() + ", waiting for a lock held by " + ti.getLockOwnerName());
        Collections.sort(lines);
        lines.forEach(System.out::println);

        // 2. The fix: every thread takes the locks in the SAME global order
        Object c = new Object(), d = new Object();
        Thread o1 = locker("O1", c, d), o2 = locker("O2", c, d);
        o1.start(); o2.start();
        o1.join(2000); o2.join(2000);
        System.out.println("consistent lock ordering -> both finished: " + (!o1.isAlive() && !o2.isAlive()));
    }
}
```

```text
deadlocked threads: 2
  T1 is BLOCKED, waiting for a lock held by T2
  T2 is BLOCKED, waiting for a lock held by T1
consistent lock ordering -> both finished: true
```

**Prevention toolbox**

| Technique | How |
|---|---|
| **Global lock ordering** | always acquire in a fixed order (e.g. by account id: `lock(min(a,b))` then `lock(max(a,b))`) |
| **`tryLock` with timeout** | give up and retry/back off instead of waiting forever |
| **Lock less** | avoid nested locks; keep critical sections tiny; no I/O or callbacks while locked |
| **Prefer higher-level tools** | `ConcurrentHashMap.merge`, `BlockingQueue`, immutability, message passing |
| **Detect** | `jstack <pid>` / `jcmd <pid> Thread.print` print "Found one Java-level deadlock"; `ThreadMXBean.findDeadlockedThreads()` |

- **Livelock:** threads keep reacting to each other and make no progress (two people stepping aside in a corridor). Fix with randomised backoff.
- **Starvation:** a thread never gets the lock/CPU (unfair locks, low priority). Fair locks, bounded queues.
- **Thread-pool starvation deadlock:** see [Executors](01-executors-thread-pools.md#8-rules-for-tasks-that-run-in-pools).

## 7. Immutability and safe publication — the best "lock" is no lock

- **Immutable objects** (all fields `final`, no escaping `this`, defensive copies) are thread-safe by construction and safely shareable: `String`, `record`s, `List.of`.
- **Safe publication** of a mutable object needs an HB edge: put it in a `volatile`/`final` field, publish via a lock, or hand it over through a concurrent collection/executor.
- **Thread confinement:** keep state inside one thread (local variables, `ThreadLocal`, actor/queue-per-entity). **`ThreadLocal`** pitfalls: leak in pools (call `remove()`), inheritance, and heavy use with virtual threads.
- `SimpleDateFormat` is **not** thread-safe — use `java.time.DateTimeFormatter` (immutable).

## 8. Interview Q&A

<details>
<summary><b>Q1.</b> What does <code>volatile</code> guarantee? Is <code>count++</code> on a volatile int thread-safe?</summary>

Visibility (a write is seen by later reads in other threads) and ordering (no reordering across the volatile access, HB edge). It does **not** make compound actions atomic, so `count++` (read-modify-write) is not safe — use `AtomicInteger`, a lock, or `LongAdder`.
</details>

<details>
<summary><b>Q2.</b> <code>synchronized</code> vs <code>ReentrantLock</code>?</summary>

Both are reentrant mutual-exclusion with HB guarantees. `synchronized` is simpler and auto-releases; `ReentrantLock` adds `tryLock`/timeouts, interruptible acquisition, fairness, multiple `Condition`s and works better with virtual threads (no pinning), at the cost of manual `try/finally unlock`.
</details>

<details>
<summary><b>Q3.</b> What is happens-before?</summary>

The JMM's visibility/ordering guarantee between actions: if A HB B then B sees A's writes. Created by program order, monitor unlock→lock, volatile write→read, thread start/join, executor submission→task, and transitivity. Without an HB edge between a write and a read you have a data race.
</details>

<details>
<summary><b>Q4.</b> How do you detect and prevent a deadlock?</summary>

Detect: thread dumps (`jstack`, `jcmd Thread.print`), `ThreadMXBean.findDeadlockedThreads`. Prevent: consistent global lock ordering, `tryLock` with timeouts, narrow lock scopes, avoid calling external code under lock, use higher-level concurrency utilities.
</details>

<details>
<summary><b>Q5.</b> What is CAS and what are its drawbacks?</summary>

A hardware compare-and-swap: update a variable only if it still holds the expected value, retrying on failure — lock-free and fast at low contention. Drawbacks: spinning under high contention (use `LongAdder`), only one variable at a time, and the ABA problem.
</details>

<details>
<summary><b>Q6.</b> Why is double-checked locking broken without <code>volatile</code>?</summary>

The write of the reference can be reordered before the constructor's field writes, so another thread can see a non-null but partially constructed object. `volatile` forbids that reordering (Java 5+). Alternatives: holder class idiom, enum singleton.
</details>

<details>
<summary><b>Q7.</b> <code>AtomicLong</code> vs <code>LongAdder</code>?</summary>

`AtomicLong` = a single CAS-contended cell with exact `get()`. `LongAdder` stripes updates across cells, so write throughput scales under contention, but `sum()` is only a point-in-time estimate under concurrent updates. Use `LongAdder` for metrics/counters, `AtomicLong` when you need exact atomic read-modify-write semantics (IDs, compare-and-set).
</details>

<details>
<summary><b>Q8.</b> Why call <code>wait()</code> in a loop?</summary>

Spurious wakeups and "stolen" notifications mean the condition may be false when the thread resumes; re-check with `while (!condition) wait();`. Better: use `BlockingQueue`/`Condition`.
</details>

## 9. Predict the output

<details>
<summary><b>P1.</b></summary>

```java
static volatile int n;
// 2 threads each run: for (int i = 0; i < 100_000; i++) n++;
// after joining both:
System.out.println(n == 200_000);
```

**`false` (almost always)** — `volatile` doesn't make `n++` atomic.
</details>

<details>
<summary><b>P2.</b></summary>

```java
Object lock = new Object();
synchronized (lock) {
    synchronized (lock) {
        System.out.println("inside");
    }
}
```

Prints **`inside`** — intrinsic locks are reentrant. (`ReentrantLock` too.)
</details>

<details>
<summary><b>P3.</b> Is this safe?</summary>

```java
Map<String,Integer> m = new ConcurrentHashMap<>();
// many threads:
Integer v = m.get(k);
m.put(k, v == null ? 1 : v + 1);
```

**No** — check-then-act race across two calls. Use `m.merge(k, 1, Integer::sum)`.
</details>

---
[↑ Back to Concurrency index](README.md)
