# Multithreading From Scratch (Start Here)

> **Level:** SDE-I → SDE-II · **Area:** Java · **Read first, then:** [Executors](01-executors-thread-pools.md) · [CompletableFuture](02-completablefuture.md) · [Async errors & HTTP](03-async-error-handling-http.md) · [Locks & volatile](04-locks-volatile-deadlock.md) · [Virtual threads](05-virtual-threads.md)

The deeper notes are precise but dense. This one builds the picture slowly, with one analogy you can keep reusing.

> The counter results in Step 2 and Step 3 were run on JDK 21 (the lost-update total changes each run). The other snippets are short illustrations, not verified programs.

## The one picture to keep in your head

Imagine a **shared kitchen** in a restaurant.

| Restaurant | Programming |
|---|---|
| Cooks working at the same time | **threads** |
| One order for one cook | a **task** (a `Runnable` or `Callable`) |
| The shared fridge, the shared till | **shared mutable data** (fields, a `HashMap`, a counter) |
| The recipe card for a dish | the code inside a method |
| Two cooks reaching into the same fridge at once | a **race condition** |
| A key that lets only one cook into the fridge | a **lock** (`synchronized`) |
| A whiteboard everyone must check, not a memo they copied earlier | **`volatile`** (visibility) |
| A fixed team of cooks plus an order rail | a **thread pool** (`ExecutorService`) |
| The receipt you get for an order you'll collect later | a **`Future`** |
| "Ring me when it's ready" instead of standing at the counter | a **`CompletableFuture`** |

Every concurrency problem is one of these:

1. **Two threads change the same data at the same time** → wrong results (race).
2. **One thread doesn't see another thread's change** → stale values (visibility).
3. **Threads wait on each other forever** → deadlock.

Everything else in the notes is a tool for one of those three.

---

## Step 1 — A thread is just "another worker running my code"

Normally your program runs one line after another on the `main` thread. A second thread lets two pieces of code run **at the same time**.

```java
Thread t = new Thread(() -> System.out.println("hello from " + Thread.currentThread().getName()));
t.start();                 // starts a NEW worker; it runs in parallel with main
System.out.println("main keeps going");
t.join();                  // main waits here until t finishes
```

- `start()` starts a new thread. Calling `run()` directly does **not** start a thread; it just runs the code on the current one. This is a common mistake.
- The order of the two printed lines is **not guaranteed**. Parallel means you can't predict which line comes first.

---

## Step 2 — The problem: two workers, one counter

Here is the smallest program that goes wrong:

```java
static int counter = 0;

Runnable work = () -> {
    for (int i = 0; i < 100_000; i++) counter++;   // looks like one step...
};
Thread a = new Thread(work), b = new Thread(work);
a.start(); b.start(); a.join(); b.join();
System.out.println(counter);                       // expected 200000
```

`counter++` is actually **three steps**:

```text
1. read counter   (say it's 5)
2. add 1          (6)
3. write it back  (6)
```

Two threads can interleave like this:

```text
Thread A reads 5
Thread B reads 5          <- both saw 5
Thread A writes 6
Thread B writes 6         <- one increment is LOST
```

**Verified on JDK 21 in one run: the total was 106,119 instead of 200,000.** The exact number changes every run, which is what makes race bugs hard to catch: the program usually "works" in a quick test and fails in production.

> The fix is not "make it faster" or "add a sleep". The fix is to make the three steps **indivisible** (atomic). Step 3 shows how.

---

## Step 3 — Fix it with a lock (`synchronized`)

A lock is a key: only the thread holding it may enter the block.

```java
static final Object lock = new Object();
static int counter = 0;

Runnable work = () -> {
    for (int i = 0; i < 100_000; i++) {
        synchronized (lock) {          // take the key
            counter++;                 // only one thread can be here at a time
        }                              // give the key back (automatic)
    }
};
```

**Verified: the total is exactly 200,000.**

Rules of thumb:
- Lock the **same object** everywhere you touch the shared data. Locking two different objects protects nothing.
- Keep the locked part **short**. Never call the network or sleep while holding a lock; others queue behind you.
- Using a lock makes things *correct*, but everyone queues, so it is slower. For a simple counter, `AtomicInteger` (a hardware-level "set only if unchanged" operation) is the cleaner choice:

```java
AtomicInteger counter = new AtomicInteger();
counter.incrementAndGet();    // one indivisible step, no lock to write
```

---

## Step 4 — `volatile`: the whiteboard rule

Sometimes the problem isn't the math, it's **visibility**. Each cook may copy the whiteboard onto a notepad and keep reading the notepad.

```java
static volatile boolean running = true;   // "always read the real whiteboard"

// thread 1
while (running) { doWork(); }

// thread 2
running = false;                          // thread 1 is guaranteed to see this
```

What `volatile` gives you:
- **Visibility:** a write is seen by the next read in any thread.
- **Ordering:** the compiler and CPU won't reorder around it.

What it does **not** give you:
- **Atomicity.** `volatile int count; count++;` is still broken (it's still three steps). Use `AtomicInteger` or a lock for that.

Use `volatile` for simple flags like "stop" or "config reloaded", where one thread writes and others read.

---

## Step 5 — Thread pools: don't hire a new cook per order

Creating a `Thread` costs real memory and time, and an unlimited number of threads will crash the JVM. A **pool** keeps a fixed team of workers and an order queue.

```java
ExecutorService pool = Executors.newFixedThreadPool(4);   // 4 cooks
for (int i = 0; i < 100; i++) {
    int orderId = i;
    pool.submit(() -> System.out.println("cooking order " + orderId));  // queued, then picked up
}
pool.shutdown();                                           // no new orders; finish the queue
pool.awaitTermination(10, TimeUnit.SECONDS);
```

Three things to remember:
- **Always shut the pool down**, or the JVM may never exit.
- **`submit` hides exceptions** inside the returned `Future` unless someone calls `get()`. A failed task can disappear silently. ([Details](01-executors-thread-pools.md#5-submit-vs-execute--where-do-exceptions-go))
- `newFixedThreadPool` has an **unlimited queue**, so a traffic spike piles up work in memory. Production code uses a bounded queue.

---

## Step 6 — `Future`: the receipt

`submit` returns a `Future`, which is a receipt. You can check it or wait for it:

```java
Future<Integer> receipt = pool.submit(() -> expensiveCalculation());

// later...
Integer result = receipt.get();                          // BLOCKS until ready
Integer safer = receipt.get(2, TimeUnit.SECONDS);        // blocks at most 2s, then throws TimeoutException
```

The limitation: `get()` makes you **stand at the counter**. You can't say "when it's ready, do X" and you can't easily chain steps. That's what `CompletableFuture` is for.

---

## Step 7 — `CompletableFuture`: "ring me when it's ready"

```java
CompletableFuture
    .supplyAsync(() -> fetchUser(7))                 // step 1: runs on another thread
    .thenApply(user -> user.name())                  // step 2: when step 1 finishes, transform
    .thenAccept(name -> System.out.println(name))    // step 3: consume
    .exceptionally(ex -> { System.out.println("failed: " + ex); return null; });   // errors land here
```

Read it as a sentence: *"fetch the user, then take the name, then print it; if anything fails, print the failure."* Nothing blocks the main thread.

| You want… | Method |
|---|---|
| Transform the result (no new async work) | `thenApply` |
| The next step is itself async | `thenCompose` |
| Two independent async calls, combine them | `thenCombine` |
| Wait for all of several | `allOf` |
| Handle failure | `exceptionally` / `handle` |

Two beginner traps:
- **Don't block inside it.** Calling `get()` or `join()` inside a chain can freeze the threads it needs.
- **Use your own executor for blocking I/O.** Without one it uses a small shared pool meant for CPU work. ([Details](02-completablefuture.md))

---

## Step 8 — Deadlock: two people, two chopsticks

Thread A holds lock 1 and waits for lock 2. Thread B holds lock 2 and waits for lock 1. Nobody moves.

```java
// Thread A                       // Thread B
synchronized (lockA) {            synchronized (lockB) {
    synchronized (lockB) { … }        synchronized (lockA) { … }
}                                 }
```

The fix that almost always works: **every thread takes the locks in the same order** (for example, always `lockA` before `lockB`). Also, `tryLock(timeout)` lets a thread give up instead of waiting forever. ([Demo](04-locks-volatile-deadlock.md#6-deadlock-livelock-starvation))

---

## Step 9 — Virtual threads (Java 21): cheap cooks

A platform thread is an operating-system thread: expensive, so you pool a few hundred. A **virtual thread** is a JVM-managed thread that costs very little. When it waits for the network, it steps aside and lets another virtual thread use the CPU.

```java
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 10_000; i++) {
        executor.submit(() -> callSlowService());   // plain blocking code, one thread per task
    }
}   // close() waits for all tasks
```

- Write ordinary blocking code (`try/catch`, straight-line calls); it scales like async code.
- Don't pool virtual threads. Limit how many talk to a downstream service with a `Semaphore`.
- They don't make **CPU** work faster: you still have only as many cores as you have.

---

## Cheat sheet: "I want to… → use…"

| I want to… | Use |
|---|---|
| Run work in the background | `ExecutorService` (a pool, not `new Thread`) |
| Count something from many threads | `AtomicInteger` / `LongAdder` |
| Protect several fields that must change together | `synchronized` or `ReentrantLock` |
| Share a simple on/off flag | `volatile boolean` |
| Get a result later | `Future` (blocking) or `CompletableFuture` (chainable) |
| Chain steps and handle errors without blocking | `CompletableFuture` |
| Many simultaneous network calls, simple code | virtual threads (Java 21) |
| A thread-safe map | `ConcurrentHashMap` (use `merge`, not get-then-put) |

## Quick self-check (answer before opening)

<details>
<summary><b>1.</b> Why does <code>counter++</code> from two threads give a wrong total?</summary>

It's read, add, write. The threads can interleave so one update overwrites the other.
</details>

<details>
<summary><b>2.</b> Does <code>volatile</code> fix <code>counter++</code>?</summary>

No. `volatile` gives visibility and ordering. It does not make the read-add-write atomic. Use `AtomicInteger` or a lock.
</details>

<details>
<summary><b>3.</b> What does <code>thread.run()</code> do versus <code>thread.start()</code>?</summary>

`start()` creates a new thread that runs the code in parallel. `run()` just runs it on the current thread, so nothing is concurrent.
</details>

<details>
<summary><b>4.</b> Why use a pool instead of <code>new Thread</code> per task?</summary>

Thread creation is costly and unlimited threads can exhaust memory. A pool reuses a fixed set of workers and queues the rest.
</details>

<details>
<summary><b>5.</b> A task submitted with <code>submit()</code> failed, and nothing was logged. Why?</summary>

The exception is stored in the `Future`. Nobody called `get()`, so it was never seen.
</details>

<details>
<summary><b>6.</b> How do two threads deadlock, and how do you prevent it?</summary>

Each holds one lock and waits for the other's. Prevent it by always taking locks in the same order, or by using `tryLock` with a timeout.
</details>

---
[↑ Back to Concurrency index](README.md)
