# Diagnosing Production Issues: High CPU, Leaks, Latency, Hangs, OOM

> **Level:** SDE-II / SDE-III · **Area:** Java · **Prev:** [Garbage collectors](02-garbage-collectors.md) · **Prereqs:** [Memory model](../01-java-basics/01-memory-model.md), [Locks & deadlocks](../03-concurrency/04-locks-volatile-deadlock.md) · **Next:** Maven/Gradle (note not written yet, see the [tracker](../../../TRACKER.md))

## TL;DR

- Production debugging is a **loop**: *symptom → cheapest tool that tells you which of 4 buckets it is (CPU / memory / blocked threads / GC) → evidence → hypothesis → one fix → verify.* Don't guess, don't restart before you have taken a **thread dump and heap histogram** (a restart destroys the evidence).
- **One tool covers 90%: `jcmd <pid> <command>`** (thread dump, heap info, class histogram, heap dump, flags, JFR start/stop). `jstack`, `jmap`, `jstat` are older single-purpose siblings.
- **Thread dumps** answer "what is every thread doing *right now*?". Take **3 dumps, 5-10 s apart**: one dump is a photo, three are a movie. Threads that appear in the same place in all three are your suspects.
- **Heap histograms** (`GC.class_histogram`) taken twice show **what is growing**; a **heap dump** + Eclipse MAT shows **who holds it** (dominator tree → path to GC roots).
- **JFR** (Java Flight Recorder) is the always-available, low-overhead black box: CPU samples, allocation, GC, locks, I/O. Enable it permanently in prod.
- Always run with the "seatbelts": `-XX:+HeapDumpOnOutOfMemoryError`, GC logging (`-Xlog:gc*`), `-XX:+ExitOnOutOfMemoryError` and, in containers, `-XX:MaxRAMPercentage`.

## The analogy: a hospital triage

A patient arrives with "feels bad" (the symptom: slow, down, big bill). Triage asks four fast questions in order, each with a cheap instrument: **pulse** (CPU: is a core pegged?), **blood pressure** (memory/GC: is heap climbing?), **can they move?** (threads: are they all stuck waiting?), **ECG over time** (JFR: record and review). Only when triage points to an organ do you order the **MRI** (heap dump + MAT) or the **surgery** (a code fix). And you never "discharge" (restart) the patient before taking samples, or you lose the evidence.

## 1. The toolbox

| Tool | What it gives you | Cost / risk |
|---|---|---|
| `jcmd <pid> help` | list of diagnostic commands for that JVM | none |
| `jcmd <pid> Thread.print` (= `jstack`) | all thread stacks, states, locks held/awaited, **deadlock report**, per-thread `cpu=` | brief safepoint, cheap |
| `jcmd <pid> GC.class_histogram` (= `jmap -histo:live`) | instances and bytes **per class** | **forces a full GC first** (unless you pass `-all`): visible pause |
| `jcmd <pid> GC.heap_info` | heap/region/metaspace usage right now | cheap |
| `jcmd <pid> GC.heap_dump <file>` (= `jmap -dump`) | full `.hprof` snapshot | **STW pause, file ≈ size of live heap** (120 MB in the demo below) |
| `jcmd <pid> VM.flags`, `VM.command_line`, `VM.uptime`, `VM.system_properties` | exactly how the JVM was started (what *really* got applied) | none |
| `jstat -gcutil <pid> 1000 5` | rolling GC numbers (Eden/Old/Metaspace %, GC counts and times) | very cheap, no logging needed |
| `jcmd <pid> JFR.start/dump/stop`, `-XX:StartFlightRecording` | the flight recorder | low overhead by design; safe for production |
| `jfr summary/print/view` | read a `.jfr` file offline | offline |
| `jcmd <pid> VM.native_memory summary` | off-heap breakdown (needs `-XX:NativeMemoryTracking=summary` at start) | small overhead when enabled |
| `jcmd <pid> Thread.dump_to_file -format=json <file>` | thread dump that **includes virtual threads** (`jstack`-style dumps omit them) | cheap (command listed by `jcmd help` on JDK 21) |
| Eclipse **MAT** / VisualVM / IntelliJ profiler | analyse `.hprof` offline | needs RAM ≈ dump size |
| **async-profiler** (flame graphs) | low-overhead CPU / allocation / lock profiling, including native frames and kernel time | external tool; *not run locally* |
| `top -H -p <pid>`, `ps`, `vmstat`, `iostat`, `ss`, `kubectl top` | OS view: which thread, swap, I/O wait, connections | none |

`jcmd` needs to run **as the same OS user** as the target JVM, and from the same container if the JVM is containerised (`kubectl exec -it pod -- jcmd 1 Thread.print`; the app is usually PID 1).

## 2. Reading a thread dump

```java
// Run: HangDemo.java  (needs: java -XX:StartFlightRecording=duration=6s,filename=hang.jfr HangDemo.java 8)
import java.util.concurrent.*;

public class HangDemo {
    static final Object CONFIG_LOCK = new Object();
    static final Object LOCK_A = new Object(), LOCK_B = new Object();

    static long spin() {                                   // pure CPU: shows up as RUNNABLE + high cpu= in a dump
        long x = 1;
        while (!Thread.currentThread().isInterrupted()) x = x * 31 + System.nanoTime() % 7;
        return x;
    }

    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }

    public static void main(String[] args) throws Exception {
        int seconds = args.length > 0 ? Integer.parseInt(args[0]) : 8;
        System.out.println("pid=" + ProcessHandle.current().pid());

        daemon("cpu-burner", HangDemo::spin);                                       // RUNNABLE, burning a core

        daemon("config-holder", () -> { synchronized (CONFIG_LOCK) { sleep(60_000); } });   // TIMED_WAITING while HOLDING a lock
        sleep(200);
        daemon("blocked-worker", () -> { synchronized (CONFIG_LOCK) { System.out.println("never printed"); } });  // BLOCKED

        BlockingQueue<String> q = new LinkedBlockingQueue<>();
        daemon("idle-consumer", () -> { try { q.take(); } catch (InterruptedException ignored) { } });          // WAITING

        daemon("dl-1", () -> { synchronized (LOCK_A) { sleep(300); synchronized (LOCK_B) { } } });             // classic deadlock
        daemon("dl-2", () -> { synchronized (LOCK_B) { sleep(300); synchronized (LOCK_A) { } } });

        sleep(seconds * 1000L);
        System.out.println("exiting");
        System.exit(0);
    }

    static void daemon(String name, Runnable r) { Thread t = new Thread(r, name); t.setDaemon(true); t.start(); }
}
```

While it runs, from another terminal: `jcmd <pid> Thread.print > dump.txt` (the same output as `jstack <pid>`). The interesting threads, from a real dump on JDK 21 (trimmed):

```text
"cpu-burner" #32 [14788] daemon prio=5 os_prio=0 cpu=3765.62ms elapsed=3.96s tid=0x0000019b6ddcffc0 nid=14788 runnable  [0x0000004c215fe000]
   java.lang.Thread.State: RUNNABLE
	at HangDemo.spin(HangDemo.java:10)
	at HangDemo$$Lambda/0x0000019b011c0208.run(Unknown Source)
	at java.lang.Thread.runWith(java.base@21.0.13.1/Thread.java:1596)
	at java.lang.Thread.run(java.base@21.0.13.1/Thread.java:1583)

"config-holder" #33 [8744] daemon prio=5 os_prio=0 cpu=0.00ms elapsed=3.96s ... waiting on condition  [0x0000004c216fe000]
   java.lang.Thread.State: TIMED_WAITING (sleeping)
	at java.lang.Thread.sleep0(java.base@21.0.13.1/Native Method)
	at java.lang.Thread.sleep(java.base@21.0.13.1/Thread.java:509)
	at HangDemo.sleep(HangDemo.java:14)
	at HangDemo.lambda$main$0(HangDemo.java:22)
	- locked <0x0000000711a057f0> (a java.lang.Object)

"blocked-worker" #34 [12600] daemon prio=5 os_prio=0 cpu=0.00ms elapsed=3.75s ... waiting for monitor entry  [0x0000004c217ff000]
   java.lang.Thread.State: BLOCKED (on object monitor)
	at HangDemo.lambda$main$1(HangDemo.java:24)
	- waiting to lock <0x0000000711a057f0> (a java.lang.Object)

"idle-consumer" #35 [17308] daemon prio=5 os_prio=0 cpu=0.00ms elapsed=3.75s ... waiting on condition  [0x0000004c218fe000]
   java.lang.Thread.State: WAITING (parking)
	at jdk.internal.misc.Unsafe.park(java.base@21.0.13.1/Native Method)
	- parking to wait for  <0x0000000711a42618> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)
	at java.util.concurrent.locks.LockSupport.park(java.base@21.0.13.1/LockSupport.java:371)
	...

Found one Java-level deadlock:
=============================
"dl-1":
  waiting to lock monitor 0x0000019b6e3ac500 (object 0x0000000711a05810, a java.lang.Object),
  which is held by "dl-2"

"dl-2":
  waiting to lock monitor 0x0000019b6e3abb60 (object 0x0000000711a05800, a java.lang.Object),
  which is held by "dl-1"

Java stack information for the threads listed above:
===================================================
"dl-1":
	at HangDemo.lambda$main$3(HangDemo.java:29)
	- waiting to lock <0x0000000711a05810> (a java.lang.Object)
	- locked <0x0000000711a05800> (a java.lang.Object)
"dl-2":
	at HangDemo.lambda$main$4(HangDemo.java:30)
	- waiting to lock <0x0000000711a05800> (a java.lang.Object)
	- locked <0x0000000711a05810> (a java.lang.Object)
```

**Anatomy of a thread header**: `"name" #javaId [osTid] daemon prio=5 cpu=…ms elapsed=…s tid=… nid=… <state hint> [stack pointer]`.

- **`cpu=3765.62ms elapsed=3.96s`**: this thread consumed ~3.8 s of CPU in ~4 s of life = one fully busy core. Every other thread shows `cpu=0.00ms`. **That's how you find the hot thread without `top -H`**: sort by `cpu=`, or compare two dumps. (On Linux you can also match `top -H -p <pid>`'s thread id, converted to hex, against `nid=0x…`; on Linux `nid` is printed in hex, here on Windows it was decimal. Linux: not run locally.)
- **Thread states** (`java.lang.Thread.State`):

| State in dump | Meaning | Typical interpretation |
|---|---|---|
| `RUNNABLE` | running **or** ready to run **or** in a native call (including *blocked in socket read*; the JVM can't tell) | busy loop, regex, serialization... **or** just waiting on I/O: look at the top frame (`SocketInputStream.read`, `epollWait` = idle) |
| `BLOCKED (on object monitor)` | waiting to **enter** a `synchronized` block; line `- waiting to lock <0x…>` | **lock contention**. Find who holds `<0x…>` (`- locked <0x…>` in another thread, e.g. `config-holder` above) |
| `WAITING (parking)` / `(on object monitor)` | waiting **indefinitely** for a signal: `LockSupport.park` (`ReentrantLock`, `BlockingQueue.take`, `Future.get`), or `Object.wait()` | normal for idle pool workers (`take`); a problem if *every* request thread is here waiting for something that never comes |
| `TIMED_WAITING` | same but with a timeout: `sleep`, `wait(ms)`, `poll(timeout)`, `parkNanos` | timers, retry back-off, `sleep` **while holding a lock** (as `config-holder`: the root cause of `blocked-worker`) |
| `NEW` / `TERMINATED` | not started / finished | rarely in dumps |

- **Deadlock**: the JVM detects **monitor and `java.util.concurrent` lock** cycles and prints **`Found one Java-level deadlock:`** at the end of the dump (use `Thread.print -l` to include `ReentrantLock` ownership). The cycle: `dl-1` holds A and waits for B; `dl-2` holds B and waits for A. Fix by consistent lock ordering or `tryLock` with timeout. A *livelock* or a "pool exhaustion" hang is **not** reported: you see it as many threads `WAITING` on the same condition/future.
- **Pool-exhaustion hang** pattern: all `http-nio-…-exec-N` threads `WAITING` in `Future.get`/`CompletableFuture.join`, while the pool that should complete those futures has **no free thread**: tasks wait for tasks in the same pool.
- Threads with identical stacks in all three dumps and `cpu=` growing = hot code. Identical stack and `cpu=` flat = stuck/waiting on something external (DB, HTTP call without timeout).
- Virtual threads don't appear in a normal `jstack` dump (there may be millions); use `jcmd <pid> Thread.dump_to_file -format=json file` (see [virtual threads](../03-concurrency/05-virtual-threads.md)).

## 3. Memory leak: histogram snapshots (real run)

```java
// Run: LeakDemo.java  (needs: java -Xmx512m LeakDemo.java 12)
import java.util.*;

public class LeakDemo {
    static final List<Payload> AUDIT_TRAIL = new ArrayList<>();      // the leak: static, never trimmed

    record Payload(long id, String user, byte[] body) {}

    static void handleRequest(long id) {
        AUDIT_TRAIL.add(new Payload(id, "user-" + (id % 100), new byte[1024]));   // "log every request for debugging"
    }

    public static void main(String[] args) throws Exception {
        int seconds = args.length > 0 ? Integer.parseInt(args[0]) : 12;
        System.out.println("pid=" + ProcessHandle.current().pid() + "  (attach with: jcmd <pid> GC.class_histogram)");
        long id = 0, end = System.currentTimeMillis() + seconds * 1000L;
        while (System.currentTimeMillis() < end) {
            for (int i = 0; i < 2_000; i++) handleRequest(id++);       // ~2 MB per 100 ms
            Thread.sleep(100);
        }
        System.out.println("requests handled: " + id + ", retained payloads: " + AUDIT_TRAIL.size());
    }
}
```

Start it with `java -Xmx512m LeakDemo.java 14`, then, ~4 seconds apart, run `jcmd <pid> GC.class_histogram | head`. The histogram counts only **live** objects (it forces a GC first), so growth between two snapshots is **retained** memory, not allocation churn.

```text
--- snapshot 1                                         --- snapshot 2 (about 4 s later)
 num     #instances         #bytes  class name          num     #instances         #bytes  class name
   1:        163942       81798472  [B                    1:        323942      166918472  [B
   2:         76000        2432000  LeakDemo$Payload      2:        156000        4992000  LeakDemo$Payload
   3:         87855        2108520  java.lang.String      3:        167855        4028520  java.lang.String
```

Reading it:

- `[B` is `byte[]` (JVM notation: `[` = array, `B` = byte; `[I` int[], `[C` char[], `[Ljava.lang.Object;` Object[]). It is always at the top in real apps; it tells you little by itself.
- **Compare snapshots, not absolute numbers**: `LeakDemo$Payload` went 76,000 → 156,000, `String` 87,855 → 167,855, `byte[]` +160,000 (the extra `byte[]` are the 1 KB bodies and the strings' internal arrays). All three grow **in lockstep**, which means they are one retained structure. The *application* class (`Payload`) is the one to chase; JDK types (`byte[]`, `String`, `HashMap$Node`) are usually just contents.
- Other quick views while it ran: `jcmd <pid> GC.heap_info` showed `garbage-first heap total 306176K, used 188073K` (and Metaspace `used 10257K`: not the problem); `jstat -gcutil <pid> 1000 3` showed the **Old** column climbing between samples:

```text
  S0     S1     E      O      M     CCS    YGC     YGCT     FGC    FGCT     CGC    CGCT       GCT
     - 100.00 103.12  11.93  97.55  90.87      2     0.016     0     0.000     0     0.000     0.016
     - 100.00  56.25  27.91  97.55  90.87      3     0.031     0     0.000     0     0.000     0.031
     - 100.00  15.38  44.71  97.61  90.87      4     0.047     0     0.000     0     0.000     0.047
```

  (`E`/`O`/`M` are **% used** of Eden/Old/Metaspace; `YGC/FGC` counts and `…T` seconds. Old: 11.9% → 27.9% → 44.7% while young GCs happen every second = **objects survive and get promoted: a leak signature**. With a healthy app Old oscillates and comes back down after mixed/full GCs.)
- `jcmd <pid> GC.heap_dump <file>` wrote a **120,369,763-byte** `.hprof` in 0.1 s for ~100k live payloads (the dump is of the **live** heap, roughly its size; the app was paused while writing).

**What to do next**: open the `.hprof` in **Eclipse MAT** (*not run locally*; concepts only):

| MAT concept | Meaning |
|---|---|
| **Shallow size** | memory of the object itself (header + fields), *not* what it references. A `byte[1024]` has shallow size ≈ 1 KB; an `ArrayList` object has ~24-32 bytes shallow. |
| **Retained size** | memory that would be **freed if this object were garbage-collected**: the object plus everything reachable *only* through it. This is the number to sort by. |
| **Dominator tree** | A object *dominates* B if every path from a GC root to B goes through A. The tree sorted by retained size shows "the 3 objects that hold 80% of the heap": here the static `ArrayList AUDIT_TRAIL`. |
| **Path to GC Roots** (exclude weak/soft refs) | for a suspicious instance: the chain of references from a GC root (static field, thread stack, JNI) that keeps it alive: *the answer to "why isn't this collected?"* |
| **Leak Suspects report** | automatic summary of dominators holding a large fraction of the heap |
| **Histogram / OQL / compare two dumps** | per-class counts, query objects, diff two dumps for growth |

Typical culprits found this way: static/`ConcurrentHashMap` caches without eviction (use Caffeine/size-bounded), unbounded queues, listeners never deregistered, `ThreadLocal`s on pool threads, sessions, class loaders (see [class-loading note](01-class-loading-and-jit.md#4-class-loader-leaks)), and per-request objects stored in a long-lived structure (as here).

## 4. JFR: the flight recorder (real run)

Start at JVM launch: `-XX:StartFlightRecording=duration=6s,filename=hang.jfr` (for production: `-XX:StartFlightRecording=disk=true,maxage=6h,maxsize=500m,dumponexit=true,filename=...`), or **on a running process**: `jcmd <pid> JFR.start name=r1 settings=profile duration=60s filename=/tmp/r1.jfr`, `jcmd <pid> JFR.dump name=r1 filename=...`, `JFR.stop`. `settings=profile` samples more often than the default `default` profile. Overhead is designed to be low enough to leave a recording running in production.

On the `HangDemo` run above (6 s):

```text
$ jfr summary hang.jfr
 Version: 2.1
 Chunks: 1
 Start: 2026-11-22 18:15:40 (UTC)
 Duration: 6 s

 Event Type                              Count  Size (bytes)
=============================================================
 jdk.BooleanFlag                           499         15207
 jdk.ActiveSetting                         360         10410
 jdk.SystemProcess                         329         18682
 ...
 jdk.ObjectAllocationSample                 73          1021
 jdk.NativeMethodSample                     42           420
 jdk.ThreadAllocationStatistics             35           337
 jdk.Deoptimization                         23           531
 jdk.ExecutionSample                        23           230
 ...
```

`jfr summary` is the table of contents: what events exist and how many. Then read the ones you care about:

```text
$ jfr view hot-methods hang.jfr
                             Java Methods that Executes the Most

Method                                                                        Samples Percent
----------------------------------------------------------------------------- ------- -------
HangDemo.spin()                                                                    21  91.30%
sun.net.www.ParseUtil.encodePath(String, boolean)                                   1   4.35%
com.sun.tools.javac.comp.DeferredAttr$FilterScanner.lambda$new$0(Set, JCTree)       1   4.35%

$ jfr print --events jdk.ExecutionSample hang.jfr      (one record)
jdk.ExecutionSample {
  startTime = 23:45:40.795 (2026-11-22)
  sampledThread = "cpu-burner" (javaThreadId = 32)
  state = "STATE_RUNNABLE"
  stackTrace = [
    HangDemo.spin() line: 10
    java.lang.Thread.run() line: 1583
  ]
}
```

91% of the CPU samples are in `HangDemo.spin()`: the "high CPU" answer in one command (the other two samples are the `java File.java` source launcher compiling our program). The sample count is small because this is a 6 s recording; use `settings=profile` and 30-60 s on a real service.

Useful JFR events: `jdk.ExecutionSample` (CPU hot methods), `jdk.ObjectAllocationSample` (who allocates: allocation hot spots), `jdk.GarbageCollection` / `jdk.GCPhasePause` (pauses), `jdk.JavaMonitorEnter` / `jdk.ThreadPark` (lock contention, with duration threshold), `jdk.SocketRead` / `jdk.FileRead` (I/O latency), `jdk.ClassLoad`, `jdk.OldObjectSample` (leak candidates; enable with `path-to-gc-roots=true`). Open the `.jfr` in **JDK Mission Control** or IntelliJ for a UI. (`jfr view` and `jcmd … JFR.view` exist in JDK 21; older JDKs need `jfr print` or JMC.)

**async-profiler / flame graphs** (*not run locally*): samples stacks with low overhead without safepoint bias, **CPU, wall-clock, allocation, lock** modes; renders a **flame graph**: x-axis = share of samples (width), y-axis = stack depth; the **wide plateaus at the top** are where time is spent. Use **wall-clock** mode for "slow but CPU is idle" (blocked on I/O/locks), **CPU** mode for "burning CPU", **alloc** mode for allocation pressure. JFR gives the same *shape* of answer with no extra install.

## 5. Playbook per symptom

### 5.1 High CPU

1. `top`/`kubectl top`: is it the **Java process** and is it **user** (our code/GC) or **system/iowait** CPU?
2. **GC or app?** `jstat -gcutil <pid> 1000` / GC log: many GCs and high `GCT` growth → memory problem in disguise (go to 5.2). Else...
3. **Hot threads**: 3 thread dumps, 5 s apart; look at `cpu=` and `RUNNABLE` threads with the same stack. Or JFR/async-profiler `hot-methods`.
4. Usual suspects: runaway/regex backtracking, tight loop, unbounded retry loop, JSON (de)serialisation of huge payloads, `HashMap` misuse under concurrency (infinite loop in Java 7), logging at DEBUG, JIT compiler threads right after deploy (warm-up: see [JIT](01-class-loading-and-jit.md#6-warm-up-and-why-naive-microbenchmarks-lie)), a GC thread storm.

### 5.2 Memory leak / heap growth

1. GC log or `jstat`: look at heap **after** GCs. **Rising floor** = leak (or growing cache); sawtooth with flat floor = healthy.
2. Two `GC.class_histogram` snapshots minutes apart → which application class grows (section 3).
3. `GC.heap_dump` → MAT: dominator tree, path to GC roots → find the structure holding it.
4. Fix (bound/evict, deregister, `remove()` ThreadLocal, close resources); redeploy; verify the floor is flat.
5. **Off-heap leak** (RSS grows but heap doesn't): `-XX:NativeMemoryTracking=summary` + `jcmd <pid> VM.native_memory summary` (verified: output starts `Total: reserved=… committed=…` with `Java Heap`, `Class`, `Thread`, … sections); direct `ByteBuffer`s (Netty), thread stacks, Metaspace/class loaders, JNI, glibc malloc arenas.

### 5.3 Latency spikes (p99 up, average fine)

1. **Correlate timestamps** of spikes with: GC pauses (GC log), thread-dump patterns (many `BLOCKED`), downstream latency (DB/HTTP: missing timeouts), connection-pool exhaustion (threads `WAITING` in `HikariPool.getConnection`), CPU throttling in containers (cgroup `cpu.stat` `nr_throttled`: *not run locally*), safepoint pauses (`-Xlog:safepoint`), noisy neighbours.
2. **GC pauses**: `Pause Full`, `Evacuation Failure`, `Humongous Allocation`, long `Evacuate Collection Set` (see [GC note](02-garbage-collectors.md#4-reading-gc-logs-real-runs)).
3. **Lock contention**: JFR `jdk.JavaMonitorEnter` / `jdk.ThreadPark` events, or dumps with many `BLOCKED` on one `<0x…>` and one thread `RUNNABLE`/`TIMED_WAITING` holding it (as `config-holder` above).
4. JIT: deoptimisation storms after a rare code path (`-Xlog:deoptimization=debug`), code-cache full.
5. Percentiles hide **coordinated omission** in load tests; measure with a tool that corrects for it (e.g. HdrHistogram-based, wrk2).

### 5.4 Hang / unresponsive

1. `jcmd <pid> Thread.print -l` ×3. First scroll to the bottom: **`Found one Java-level deadlock`**? (shown above) → fix lock order.
2. No deadlock: look for the **same stack in all request threads**: `WAITING` in `Future.get` (pool starvation), `BLOCKED` on one monitor (lock held across I/O), `RUNNABLE` in `SocketInputStream.read` / `epollWait` on a call **without timeout** (hung downstream).
3. Check pools: is the executor's queue unbounded? Are all `exec` threads busy? Is the DB connection pool exhausted?
4. If the JVM doesn't answer `jcmd` at all: it may be in a long GC/safepoint (look at the GC log), or the process is swapping/OOM-killed (check `dmesg`/pod events).

### 5.5 OutOfMemoryError

1. Read the **message** (see the [OOM table](02-garbage-collectors.md#5-the-outofmemoryerror-family-all-reproduced)): heap space / Metaspace / native thread / direct buffer / GC overhead.
2. Heap space → the heap dump written by `-XX:+HeapDumpOnOutOfMemoryError` → MAT *Leak Suspects*.
3. Metaspace → class loader count, class histogram, recent redeploys/dynamic proxies.
4. Native thread → count threads (`Thread.print | grep -c '^"'`: 26 in the demo process), find what spawns them.
5. Killed with **exit code 137 and no Java stack trace** → the *kernel* OOM-killed the process: container limit < heap + non-heap (see [GC note, container rules](02-garbage-collectors.md#3-key-flags)).

## 6. Containers and Kubernetes tips

*Container behaviour is standard but was **not run locally** (this is a Windows host); flags and `jcmd` commands above were run.*

- JVM is **cgroup-aware** (JDK 10+/8u191+ on Linux): default heap = 25% of the container memory limit, CPU count from the CPU limit. Set `-XX:MaxRAMPercentage=70` (not 100) and `-Xms` = `-Xmx` for services; leave room for Metaspace, code cache, thread stacks (`-Xss`), direct buffers.
- Pin down what the JVM *actually* decided: `jcmd 1 VM.flags` and `jcmd 1 VM.command_line`, `java -XX:+PrintFlagsFinal -version | grep -E 'MaxHeapSize|ActiveProcessorCount'`; and inspect `Runtime.availableProcessors()` in a debug endpoint.
- **CPU limit** too low → fewer GC/compiler threads and **throttling** (latency spikes with low reported CPU). Prefer requests without tight limits, or size limits generously.
- **Write dumps somewhere that survives the pod restart**: `-XX:HeapDumpPath=/dumps` on a mounted volume sized above the heap (or use an ephemeral debug container/sidecar and `kubectl cp`). Add `-XX:+ExitOnOutOfMemoryError` so Kubernetes restarts a *clean* pod.
- Distroless/JRE-only images often lack `jcmd`/`jstack`: use a **JDK** image, or `kubectl debug` with an ephemeral container sharing the process namespace (and the same user).
- Export metrics continuously (Micrometer / Actuator: `jvm.memory.used`, `jvm.gc.pause`, `jvm.threads.states`, `process.cpu.usage`) and alert on **heap-after-GC trend** rather than raw heap use; use `/actuator/heapdump` and `/actuator/threaddump` only if secured (they leak secrets).
- Enable always-on **JFR** (`dumponexit`, bounded `maxsize`/`maxage`) so a post-mortem has data.

## 7. The first 10 minutes checklist

1. **Don't restart yet.** If you must (outage), first capture: `jcmd <pid> Thread.print > td1.txt`, `jcmd <pid> GC.class_histogram > h1.txt`, `jcmd <pid> VM.flags`, the last GC log, and (if safe) `GC.heap_dump`.
2. **Scope it**: when did it start (deploy? traffic? config?), which instances, which endpoints. Check dashboards: CPU, heap-after-GC, GC pause, thread count, connection pools, downstream latency, error rate.
3. **Which bucket?** CPU high → 5.1. Heap floor rising / GC frantic → 5.2. Threads stuck / no CPU → 5.4. Spikes → 5.3. `OutOfMemoryError` / exit 137 → 5.5.
4. **Three thread dumps**, 5-10 s apart. Search for `Found one Java-level deadlock`, group threads by identical top frames, sort by `cpu=`.
5. **`jstat -gcutil <pid> 1000 10`** (or the GC log): Old% trend, Full GC count, GC time %.
6. **Start a JFR recording** (`jcmd <pid> JFR.start duration=60s settings=profile filename=/tmp/r.jfr`) and look at `jfr view hot-methods` / allocation / locks.
7. **Form one hypothesis, change one thing** (roll back the deploy, raise a pool limit, add a timeout, restart one instance with `-Xlog`/NMT enabled): measure again.
8. **Write down** timeline, evidence and fix; add the missing alert/timeout/bound so it can't recur silently.

## 8. Pitfalls

> [!WARNING]
> - **Restarting first** (evidence gone) or taking **one** thread dump (can't tell stuck from busy).
> - **`jmap -histo:live` / `GC.class_histogram` / heap dump on a struggling prod JVM** force a full GC or STW pause: take them on **one** instance (drained from the load balancer if possible), not all.
> - **Heap dump contains secrets** (passwords, tokens, PII). Treat `.hprof` as sensitive data; don't attach it to tickets.
> - **A `RUNNABLE` thread is not necessarily using CPU** (it may be blocked in a native socket read). Use `cpu=` growth, not the state alone.
> - **Reading the histogram as absolute**: `[B`/`String` are always big. Compare two snapshots and look for *application* classes.
> - **Blaming GC for everything**: GC is often the symptom of a leak or a high allocation rate. Fix those first.
> - **Profiling only at safepoints** (naive sampling profilers) shows misleading hot spots. JFR and async-profiler avoid that bias.
> - **No timeouts on outbound calls** → "hangs" that are just threads parked in `read()` forever. See [async error handling](../03-concurrency/03-async-error-handling-http.md).
> - **Debug flags left on** (e.g. `-Xlog:gc*=debug` at high volume, NMT `detail`, `-XX:+PrintCompilation`): they cost CPU/disk.

## 9. Interview Q&A

<details>
<summary><b>Q1.</b> Production CPU is at 100%. Walk me through what you do.</summary>

Confirm it's the Java process and user CPU. Rule out GC (`jstat -gcutil`/GC log: if GC time is huge, treat it as a memory problem). Otherwise take 3 thread dumps 5 s apart (`jcmd <pid> Thread.print`), find `RUNNABLE` threads whose stack stays the same and whose `cpu=` grows (or use `top -H` + hex `nid` on Linux), and confirm with a JFR/async-profiler CPU profile (`jfr view hot-methods`). Then fix the code path (regex, loop, serialisation...) and verify.
</details>

<details>
<summary><b>Q2.</b> How do you find a memory leak in a running service?</summary>

See whether heap **after GC** keeps rising (GC log, `jstat`). Take two `GC.class_histogram` snapshots minutes apart to see which application classes grow. Take a heap dump (`GC.heap_dump`) and open it in MAT: the **dominator tree** (sorted by *retained size*) shows what holds the memory and **Path to GC Roots** shows *why* it isn't collected (static collection, ThreadLocal, listener, class loader...). Fix, then verify the floor is flat.
</details>

<details>
<summary><b>Q3.</b> Shallow size vs retained size?</summary>

Shallow = memory occupied by the object itself (header + fields). Retained = memory that would be freed if that object were collected: itself plus everything reachable only through it. Retained size (via the dominator tree) is what identifies the real memory hogs; a tiny `ArrayList` object can have a huge retained size.
</details>

<details>
<summary><b>Q4.</b> What do the thread states in a thread dump mean, and which indicate trouble?</summary>

`RUNNABLE` (running/ready/in native code, including blocked socket reads), `BLOCKED` (waiting for a monitor: contention), `WAITING` (indefinite `park`/`wait`/`join`), `TIMED_WAITING` (`sleep`/timeouts). Trouble: many `BLOCKED` on one monitor; all request threads `WAITING` for the same future/lock/connection; `RUNNABLE` in a long CPU loop. Idle pool workers `WAITING` on the queue are normal.
</details>

<details>
<summary><b>Q5.</b> How do you detect and fix a deadlock in production?</summary>

`jcmd <pid> Thread.print -l` (or `jstack`): the JVM prints `Found one Java-level deadlock` with the cycle of threads, locks and stack lines. Programmatically `ThreadMXBean.findDeadlockedThreads()`. Fix with a global lock ordering, shorter critical sections, or `tryLock` with timeout; avoid calling alien code while holding a lock.
</details>

<details>
<summary><b>Q6.</b> <code>jstack</code> vs <code>jcmd</code> vs <code>jmap</code> vs <code>jstat</code>?</summary>

`jcmd` is the all-in-one front end to the JVM's diagnostic commands (thread print, heap info, histogram, heap dump, flags, JFR). `jstack` ≈ `jcmd Thread.print`, `jmap` ≈ `jcmd GC.class_histogram / GC.heap_dump`, `jstat` is a lightweight sampler of GC/class-loading/compilation counters. Prefer `jcmd`.
</details>

<details>
<summary><b>Q7.</b> What is JFR and why use it in production?</summary>

Flight Recorder is built into the JVM and records events (CPU samples, allocation samples, GC, lock waits, I/O, exceptions) into a ring buffer/file with overhead low enough to be always on. After an incident you `jcmd JFR.dump` or read the `dumponexit` file with `jfr print/view/summary` or JDK Mission Control, with no need to reproduce the issue.
</details>

<details>
<summary><b>Q8.</b> The pod restarts with exit code 137 and logs show no <code>OutOfMemoryError</code>. What happened?</summary>

137 = SIGKILL: the **kernel/orchestrator OOM-killed** the container because total process memory (heap + Metaspace + code cache + thread stacks + direct buffers + native) exceeded the limit; the JVM never had a chance to throw. Check `kubectl describe pod` (OOMKilled), lower the heap (`MaxRAMPercentage` ~70), use NMT to see non-heap growth, and raise the limit if the legitimate footprint is bigger.
</details>

<details>
<summary><b>Q9.</b> Latency is bad but CPU is low. Where do you look?</summary>

Threads are *waiting*, not computing: thread dumps (`BLOCKED`/`WAITING`/`RUNNABLE` in socket read), lock contention (JFR monitor events), connection pool exhaustion, a slow downstream without timeouts, GC pauses or safepoints (GC log, `-Xlog:safepoint`), CPU throttling in cgroups. Use **wall-clock** profiling (async-profiler `-e wall`) since CPU profiling doesn't see waiting.
</details>

<details>
<summary><b>Q10.</b> How do you analyse an <code>OutOfMemoryError: Java heap space</code> after it happened?</summary>

If `-XX:+HeapDumpOnOutOfMemoryError` was set, open the `.hprof` in MAT: Leak Suspects → dominator tree → path to GC roots. Compare with GC logs (when did the post-GC floor start rising and what changed?). If it isn't a leak but the working set is simply bigger than `-Xmx` (e.g. loading a 1 GB file), fix the algorithm (stream/page) or size the heap and container accordingly.
</details>

<details>
<summary><b>Q11.</b> What's a flame graph and how do you read it?</summary>

An aggregation of sampled stack traces: each box is a method, width = share of samples including its callees, stack grows upward (callers at the bottom). Look for **wide boxes near the top** (self time) and unexpectedly wide callers. CPU mode shows computation, wall mode shows waiting, alloc mode shows who allocates. Produced by async-profiler or from JFR data.
</details>

## 10. Predict the output / Spot the bug

<details>
<summary><b>P1.</b> What <code>Thread.State</code> does each thread report? (<code>holder</code> sleeps 2 s inside <code>synchronized(M)</code>; <code>blocked</code> wants <code>M</code>; <code>waiter</code> does <code>M3.wait()</code> inside <code>synchronized(M3)</code>; <code>timed</code> does <code>M2.wait(2000)</code>; <code>parked</code> calls <code>LockSupport.park()</code>; <code>lockWaiter</code> calls <code>ReentrantLock.lock()</code> on a lock the main thread holds.)</summary>

Run result (about 0.5 s after starting all of them):

```text
new      : NEW
holder (sleep inside synchronized): TIMED_WAITING
blocked (wants M)                 : BLOCKED
waiter (Object.wait())            : WAITING
timed (Object.wait(2000))         : TIMED_WAITING
parked (LockSupport.park)         : WAITING
lockWaiter (ReentrantLock.lock)   : WAITING
holder after finishing            : TERMINATED
```

Key points: `sleep` inside `synchronized` is `TIMED_WAITING` **while still holding the monitor** (that's why others are `BLOCKED`); only waiting to **enter a monitor** is `BLOCKED`: waiting for a `ReentrantLock` is `WAITING` (parked), not `BLOCKED`. (Had `waiter` called `wait()` on an object it doesn't hold the monitor of, it would have died with `IllegalMonitorStateException` and shown `TERMINATED`: I hit exactly that mistake in my first draft of this quiz.)
</details>

<details>
<summary><b>P2.</b> Two histogram snapshots 5 minutes apart. Which class do you chase first?</summary>

| class | snapshot 1 | snapshot 2 |
|---|---:|---:|
| `[B` | 163,942 | 323,942 |
| `java.lang.String` | 87,855 | 167,855 |
| `LeakDemo$Payload` | 76,000 | 156,000 |
| `java.lang.Class` | 2,902 | 2,902 |

`LeakDemo$Payload` (the application class). `byte[]` and `String` grow too but are its contents: they all grew by the same ~80,000 (`Payload` +80,000, `String` +80,000, `byte[]` +160,000: one body array plus one string array per payload). `java.lang.Class` is flat, so **not** a class-loader/Metaspace leak. Then take a heap dump and use *Path to GC Roots* on a `Payload` to find the static list. (Numbers are from the real snapshots above except the `Class` count, which in the real output was `2,902` in snapshot 1 and was not displayed in the second excerpt.)
</details>

<details>
<summary><b>P3. Spot the bug.</b> Service hangs under load; every <code>http-exec-N</code> thread shows <code>WAITING (parking) at CompletableFuture.join</code>. CPU is near 0. What's wrong?</summary>

```java
ExecutorService pool = Executors.newFixedThreadPool(8);          // shared by controller work AND the inner tasks
CompletableFuture<String> outer = CompletableFuture.supplyAsync(() -> {
    CompletableFuture<String> inner = CompletableFuture.supplyAsync(() -> fetch(), pool);
    return inner.join();                                          // a pool thread blocks waiting for another task in the SAME pool
}, pool);
```

**Pool starvation (thread-pool deadlock)**: with 8 concurrent outer tasks all 8 threads are blocked in `join()` waiting for inner tasks that sit in the queue with no free thread to run them. The JVM reports **no deadlock** (it isn't a lock cycle), only many `WAITING` threads with the same stack. Fix: don't block inside pool tasks (`thenCompose` instead of `join`), use separate pools for different layers, or use virtual threads. (Reasoned from the dump pattern; not run locally.)
</details>

<details>
<summary><b>P4. Spot the bug.</b> A heap dump taken at 3 a.m. is attached to a public Jira ticket for the team to look at. What's wrong?</summary>

An `.hprof` contains **every object in memory**: DB passwords, API tokens, session IDs, customer PII. It must be handled as sensitive data (restricted storage, access control, deleted afterwards, or analysed in place); share MAT's *leak suspects* summary instead.
</details>

---
[↑ Back to JVM internals index](README.md)
