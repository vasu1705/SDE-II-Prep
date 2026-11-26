# Puzzlers & "What Happens If…"

> **Level:** SDE-II / SDE-III · **Area:** Java · **Prev:** [Gotchas index](README.md) · **Next:** `java.time`, I/O & misc (note not written yet, see the [tracker](../../../TRACKER.md))

## TL;DR

- Every puzzler is a **rule you half-know meeting an edge case**: lazy class initialisation, compile-time constants, `int` promotion, overload phases, views vs copies, `scale` in `BigDecimal`.
- Interviewers ask "what happens if…" to see whether you reason from the **language rules** (JLS) or guess. Say the rule first, then the result.
- Everything below was **compiled and run on JDK 21**; outputs are real. Items already covered in depth elsewhere are linked, not repeated: [Integer cache / overflow / floats](../01-java-basics/02-primitives-wrappers-equality.md), [String pool](../01-java-basics/03-strings.md), [overload/override/init order](../01-java-basics/04-oop-polymorphism.md), [exceptions/finally](../01-java-basics/05-exceptions.md), [generics/erasure](../01-java-basics/06-generics.md), [`equals`/`hashCode`](../02-collections/02-equals-hashcode.md), [`HashMap`](../02-collections/03-hashmap-internals.md).

## The analogy: the highway code and its exceptions

"Stop at a red light" is the rule everybody knows. The **puzzlers are the footnotes**: *unless a police officer waves you through*, *unless you are turning right on red where signed*. The compiler and the JVM follow the footnotes literally, with no sense of humour. This note is the list of footnotes that actually cause production bugs and interview rejections.

How to use it: cover the answer, say the **rule**, then the **result**. Sections group the puzzles by theme; fully runnable programs have a `// Run:` marker (`java ClassName.java`), small ones sit in collapsed `<details>` blocks.

---

## 1. Class initialisation & the JVM lifecycle

### 1.1 When does a class actually initialise? (static init order, constants, `main`)

A class is initialised **lazily, on first active use**: `new`, calling a static method, reading/writing a static field that is **not a compile-time constant**. Superclass first. Things that do **not** trigger it: a class literal (`Lazy.class`), creating an *array* of the type, reading a `static final` **constant variable** (primitive/`String` initialised with a constant expression — javac copies the value into the caller), and reading a static field *through a subclass* (only the class that **declares** the field initialises).

```java
// Run: StaticInit.java
public class StaticInit {
    public static void main(String[] args) {
        System.out.println("1. main starts");
        System.out.println("2. Const.NAME  = " + Const.NAME);          // constant variable: NO init of Const
        System.out.println("3. Const.TIME  = " + Const.NOT_CONST);     // not a constant expression: triggers init
        System.out.println("4. Const.NAME  = " + Const.NAME);
        Child[] arr = new Child[1];                                   // array creation: no init
        System.out.println("5. array of Child created, length " + arr.length);
        System.out.println("6. Child.parentField = " + Child.parentField);  // declared in Parent: only Parent initialised
        System.out.println("7. new Child()");
        new Child();
        System.out.println("8. Lazy.class literal");
        Class<?> c = Lazy.class;                                      // class literal: no init
        System.out.println("9. got " + c.getSimpleName());
        System.out.println("10. Lazy.INSTANCE touched");
        Object o = Lazy.INSTANCE;
    }

    static class Const {
        static final String NAME = "inlined";                         // compile-time constant
        static final String NOT_CONST = new String("runtime");        // not a constant
        static { System.out.println("   [Const.<clinit>]"); }
    }
    static class Parent {
        static int parentField = 42;
        static { System.out.println("   [Parent.<clinit>]"); }
        { System.out.println("   [Parent instance init]"); }
        Parent() { System.out.println("   [Parent ctor]"); }
    }
    static class Child extends Parent {
        static { System.out.println("   [Child.<clinit>]"); }
        { System.out.println("   [Child instance init]"); }
        Child() { System.out.println("   [Child ctor]"); }
    }
    static class Lazy {
        static final Lazy INSTANCE = new Lazy();
        static { System.out.println("   [Lazy.<clinit>]"); }
    }
}
```

```text
1. main starts
2. Const.NAME  = inlined
   [Const.<clinit>]
3. Const.TIME  = runtime
4. Const.NAME  = inlined
5. array of Child created, length 1
   [Parent.<clinit>]
6. Child.parentField = 42
7. new Child()
   [Child.<clinit>]
   [Parent instance init]
   [Parent ctor]
   [Child instance init]
   [Child ctor]
8. Lazy.class literal
9. got Lazy
10. Lazy.INSTANCE touched
   [Lazy.<clinit>]
```

Reading it line by line:

- Line 2: `Const.NAME` printed *without* `[Const.<clinit>]` — it was **inlined by javac**. Line 3 touched a non-constant, so the initialiser ran.
- Line 6: `Child.parentField` initialised only `Parent` (the declaring class), never `Child`.
- Lines 7–: `new Child()` runs `Child.<clinit>` **once**, then for every instance: `Parent` instance initialisers → `Parent` ctor → `Child` instance initialisers → `Child` ctor (full detail in [OOP note §3](../01-java-basics/04-oop-polymorphism.md)).
- `Lazy.INSTANCE` shows `<clinit>` running at the moment of first use. This is also **why the "initialisation-on-demand holder" singleton is thread-safe** with no `synchronized`: the JVM guarantees class initialisation runs once, under a lock.

**Proof that the constant is inlined** — the bytecode of `main` contains the literal; there is no `getstatic` for `NAME` (output of `javap -c -p` on the compiled class above, filtered, whitespace condensed):

```text
 3: ldc  #13  // String 1. main starts
11: ldc  #23  // String 2. Const.NAME  = inlined
33: ldc  #33  // String 4. Const.NAME  = inlined
```

**Practical consequence (a real production bug):** if library `A` has `public static final int MAX = 10` and your app `B` is compiled against it, `B` carries a **copy of 10**. Release `A` with `MAX = 20`, drop in the new jar *without recompiling B*, and `B` still uses 10. Use a non-constant (`static final Integer MAX = 10`, or a method) for values that may change between releases. (Explained by the JLS rule above; the two-jar scenario itself was not run locally.)

### 1.2 What happens if a static initialiser throws?

```java
// Run: InitFailure.java
public class InitFailure {
    static class Broken {
        static int value = compute();
        static int compute() { throw new IllegalStateException("config missing"); }
        static void hello() { System.out.println("never printed"); }
    }
    static int a = getB();      // forward use through a method: legal, sees default 0
    static int b = 5;
    static int getB() { return b; }

    public static void main(String[] args) {
        System.out.println("a = " + a + ", b = " + b);
        for (int i = 1; i <= 2; i++) {
            try {
                Broken.hello();
            } catch (Throwable t) {
                System.out.println("attempt " + i + ": " + t);
                if (t.getCause() != null) System.out.println("   cause: " + t.getCause());
            }
        }
    }
}
```

```text
a = 0, b = 5
attempt 1: java.lang.ExceptionInInitializerError
   cause: java.lang.IllegalStateException: config missing
attempt 2: java.lang.NoClassDefFoundError: Could not initialize class InitFailure$Broken
   cause: java.lang.ExceptionInInitializerError: Exception java.lang.IllegalStateException: config missing [in thread "main"]
```

- First touch: **`ExceptionInInitializerError`** wrapping your exception. The class is now permanently marked **erroneous**.
- Every later touch in that classloader: **`NoClassDefFoundError: Could not initialize class …`** — a confusing error that hides the real cause in the *first* log line you probably never saw. When you meet a `NoClassDefFoundError` for a class that is on the classpath, search the logs for the earlier `ExceptionInInitializerError`.
- `static int a = getB(); static int b = 5;` printed `a = 0`: static initialisers run **top to bottom**, and calling a method that reads `b` early sees its default. Writing `static int a = b + 1;` directly is rejected by the compiler:

```text
C8.java:1: error: illegal forward reference
public class C8 { static int a = b + 1; static int b = 2; ...
                                 ^
```

### 1.3 What happens if `main` throws, another thread throws, or you call `System.exit`?

```java
// Run: ExitDemo.java
public class ExitDemo {
    public static void main(String[] args) throws Exception {
        String mode = args.length > 0 ? args[0] : "exit";
        Runtime.getRuntime().addShutdownHook(new Thread(() -> System.out.println("  [hook] shutdown hook ran")));
        try {
            System.out.println("mode = " + mode);
            switch (mode) {
                case "exit"  -> System.exit(3);
                case "halt"  -> Runtime.getRuntime().halt(4);
                case "throw" -> throw new IllegalStateException("boom from main");
                case "thread" -> {
                    Thread t = new Thread(() -> { throw new RuntimeException("boom in worker"); }, "worker-1");
                    t.start(); t.join();
                    System.out.println("main finished normally");
                }
                case "nondaemon" -> {
                    new Thread(() -> {
                        try { Thread.sleep(300); } catch (InterruptedException e) {}
                        System.out.println("  non-daemon thread finishing");
                    }).start();
                    throw new IllegalStateException("main dies first");
                }
            }
        } finally {
            System.out.println("finally block");
        }
    }
}
```

Run once per mode (`java ExitDemo.java <mode>`; no argument means `exit`). Real results, stdout and stderr merged:

**`exit`** (`System.exit(3)` inside `try`):

```text
mode = exit
  [hook] shutdown hook ran
[exit code: 3]
```

**`halt`** (`Runtime.halt(4)`):

```text
mode = halt
[exit code: 4]
```

**`throw`** (uncaught exception in `main`):

```text
mode = throw
finally block
Exception in thread "main" java.lang.IllegalStateException: boom from main
	at ExitDemo.main(ExitDemo.java:11)
  [hook] shutdown hook ran
[exit code: 1]
```

**`thread`** (exception in a worker thread, `main` finishes normally):

```text
mode = thread
Exception in thread "worker-1" java.lang.RuntimeException: boom in worker
	at ExitDemo.lambda$main$1(ExitDemo.java:13)
	at java.base/java.lang.Thread.run(Thread.java:1583)
main finished normally
finally block
  [hook] shutdown hook ran
[exit code: 0]
```

**`nondaemon`** (`main` throws while a non-daemon thread is still sleeping):

```text
mode = nondaemon
finally block
Exception in thread "main" java.lang.IllegalStateException: main dies first
	at ExitDemo.main(ExitDemo.java:22)
  non-daemon thread finishing
  [hook] shutdown hook ran
[exit code: 1]
```

What each teaches:

| Case | Rule |
|---|---|
| `System.exit(3)` inside `try` | **`finally` does NOT run** (no "finally block" line); shutdown hooks **do** run; exit code 3. |
| `Runtime.halt(4)` | Terminates immediately: **no shutdown hooks, no finalisers, no `finally`**. Last resort (e.g. a corrupted state you must not flush). |
| uncaught exception in `main` | `finally` runs, trace printed by the default handler, hooks run, **exit code 1**. |
| exception in another thread | Printed by the thread's handler; the JVM keeps going; exit code stays **0** if `main` ends normally. Install `Thread.setDefaultUncaughtExceptionHandler` to log/alert. |
| `main` dies but a **non-daemon** thread is alive | JVM waits for that thread (`non-daemon thread finishing` printed *after* the trace), then exits with code **1**. |

Shutdown hooks (`Runtime.addShutdownHook`) run on `SIGTERM`/`SIGINT`/normal exit/`System.exit`, **not** on `SIGKILL` (`kill -9`), power loss or `halt`. Multiple hooks start **concurrently in unspecified order** — never rely on ordering between them, and never call `System.exit` from a hook (it blocks forever, per the Javadoc; not run locally). Keep hooks short and idempotent; Spring Boot's graceful shutdown is built on exactly this.

### 1.4 `finalize()` vs `Cleaner` vs `try-with-resources`

- `Object.finalize()` is **deprecated for removal** (JEP 421, Java 18). It runs at an unpredictable time (maybe never), can **resurrect** the object, slows GC, and an exception inside it is silently swallowed. `java --finalization=disabled` (Java 18+) turns it off entirely to test your code.
- The replacement for a **safety net** is `java.lang.ref.Cleaner`; the replacement for **deterministic release** is `AutoCloseable` + try-with-resources. Use both: close explicitly, with a `Cleaner` as backup.

```java
// Run: CleanerDemo.java
import java.lang.ref.Cleaner;

public class CleanerDemo {
    private static final Cleaner CLEANER = Cleaner.create();

    static class Resource implements AutoCloseable {
        // The cleaning action must NOT reference the Resource (or it can never become unreachable).
        private static class State implements Runnable {
            final String name;
            State(String name) { this.name = name; }
            public void run() { System.out.println("  [cleaner] released native handle of " + name); }
        }
        private final Cleaner.Cleanable cleanable;
        Resource(String name) { cleanable = CLEANER.register(this, new State(name)); }
        @Override public void close() { cleanable.clean(); }            // idempotent: runs the action once
    }

    public static void main(String[] args) throws Exception {
        try (Resource r = new Resource("A")) {
            System.out.println("using A");
        }                                                               // closed deterministically
        System.out.println("A closed");

        new Resource("B");                                              // leaked: forgot close()
        for (int i = 0; i < 5; i++) { System.gc(); Thread.sleep(100); }
        System.out.println("end of main (B's cleaner may or may not have run: GC timing is not guaranteed)");
    }
}
```

```text
using A
  [cleaner] released native handle of A
A closed
  [cleaner] released native handle of B
end of main (B's cleaner may or may not have run: GC timing is not guaranteed)
```

Rules: the cleaning action must **not capture the object it cleans** (here the static nested `State` holds only the name) or the object can never become unreachable; `clean()` is idempotent, so `close()` + GC both calling it is safe. Resource B's cleaner ran only because `System.gc()` happened to collect it: **that timing is not guaranteed**, which is exactly why you never rely on it for correctness (locks, transactions, file handles).

---

## 2. Inner, anonymous & lambda `this`

```java
// Run: InnerClassTraps.java
import java.io.*;
import java.lang.reflect.Field;

public class InnerClassTraps {
    private final byte[] bigPayload = new byte[10_000_000];   // 10 MB held by the outer instance
    private final String id = "outer-1";

    class Inner implements Serializable {                      // non-static: holds a hidden InnerClassTraps.this
        int x = 7;
    }
    class Plain { }                                            // non-serializable inner that never touches the outer
    static class Nested implements Serializable {              // static: no hidden reference
        int x = 7;
    }

    Runnable anonymousTask() {
        return new Runnable() {                                // anonymous class in an instance method: captures this
            @Override public void run() { System.out.println("run, id from outer = " + id); }
            @Override public String toString() { return "anon.this=" + this.getClass().getName() + ", outer=" + InnerClassTraps.this.id; }
        };
    }
    Runnable lambdaTask() {
        return () -> System.out.println("lambda this = " + this.id);   // lambda: `this` is the OUTER instance
    }
    static Runnable staticFactoryTask() {
        return new Runnable() { public void run() { } };       // static context: no outer instance
    }

    static void listFields(Class<?> c) {
        if (c.getDeclaredFields().length == 0) System.out.println("  " + c.getName() + " : no fields");
        for (Field f : c.getDeclaredFields())
            System.out.println("  " + c.getName() + " field: " + f.getName() + " : " + f.getType().getSimpleName()
                    + (f.isSynthetic() ? "  (synthetic)" : ""));
    }

    static byte[] serialize(Object o) throws IOException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(bos)) { oos.writeObject(o); }
        return bos.toByteArray();
    }

    public static void main(String[] args) throws Exception {
        InnerClassTraps outer = new InnerClassTraps();
        Inner inner = outer.new Inner();

        System.out.println("-- hidden fields");
        listFields(Inner.class);
        listFields(Plain.class);
        listFields(Nested.class);
        listFields(staticFactoryTask().getClass());
        listFields(outer.anonymousTask().getClass());

        System.out.println("-- serializing a static nested instance");
        System.out.println("  bytes = " + serialize(new Nested()).length);

        System.out.println("-- serializing an inner instance (drags the outer along)");
        try {
            serialize(inner);
        } catch (NotSerializableException e) {
            System.out.println("  NotSerializableException: " + e.getMessage());
        }

        System.out.println("-- this inside anonymous class / lambda");
        Runnable a = outer.anonymousTask();
        a.run();
        System.out.println("  " + a);
        outer.lambdaTask().run();

        System.out.println("-- a tiny inner object keeps the 10 MB outer reachable");
        Field f = Inner.class.getDeclaredField("this$0");
        f.setAccessible(true);
        InnerClassTraps captured = (InnerClassTraps) f.get(inner);
        System.out.println("  inner.this$0 == outer ? " + (captured == outer) + ", payload bytes reachable = " + captured.bigPayload.length);
    }
}
```

```text
-- hidden fields
  InnerClassTraps$Inner field: x : int
  InnerClassTraps$Inner field: this$0 : InnerClassTraps  (synthetic)
  InnerClassTraps$Plain : no fields
  InnerClassTraps$Nested field: x : int
  InnerClassTraps$2 : no fields
  InnerClassTraps$1 field: this$0 : InnerClassTraps  (synthetic)
-- serializing a static nested instance
  bytes = 51
-- serializing an inner instance (drags the outer along)
  NotSerializableException: InnerClassTraps
-- this inside anonymous class / lambda
run, id from outer = outer-1
  anon.this=InnerClassTraps$1, outer=outer-1
lambda this = outer-1
-- a tiny inner object keeps the 10 MB outer reachable
  inner.this$0 == outer ? true, payload bytes reachable = 10000000
```

What the output proves:

1. A **non-static inner class** carries a hidden `this$0` field pointing at the outer instance. A tiny `Inner` therefore keeps the whole outer object (here a 10 MB array) reachable: a classic **memory leak** when inner/anonymous objects are stored in long-lived collections, caches or listeners registered with a static registry.
2. **Serialising** an inner instance serialises `this$0` too; the outer is not `Serializable`, so you get `NotSerializableException: InnerClassTraps`. A `static` nested class has no such field (51 bytes, fine).
3. **JDK nuance (verified):** since JDK 18 `javac` **omits `this$0` when the inner class never uses it** — `Plain` has no fields — *except* for `Serializable` classes (`Inner` keeps it, because it must stay stable for serialisation). Do not rely on this; default to `static` nested classes.
4. **Anonymous classes** declared in an instance method capture the outer `this` (`$1` has `this$0`); declared in a **static** context (`$2`) they do not.
5. `this` inside an anonymous class is the **anonymous instance** (`InnerClassTraps$1`); you reach the outer one with `Outer.this`. Inside a **lambda**, `this` is simply the enclosing instance — lambdas are not new scopes for `this`, and they don't create `this$0` fields (they capture only what they use).

> [!WARNING]
> Double-brace initialisation (`new ArrayList<>() {{ add("x"); }}`) creates an anonymous subclass that captures `this`, breaks `equals` symmetry (`getClass()` differs) and leaks the outer. Use `List.of(..)`.

---

## 3. Enum quirks

```java
// Run: EnumQuirks.java
import java.util.*;

public class EnumQuirks {
    enum Op {
        ADD("+") { int apply(int a, int b) { return a + b; } },
        MUL("*") { int apply(int a, int b) { return a * b; } };
        final String sym;
        Op(String sym) { this.sym = sym; }
        abstract int apply(int a, int b);
    }
    enum Level { LOW, MID, HIGH }                             // ordinal 0,1,2 : do not persist ordinal()!
    enum Singleton { INSTANCE; int hits; int hit() { return ++hits; } }

    enum Registry {
        A, B;
        // static final Map<String,Registry> BY_NAME = new HashMap<>();
        // Registry() { BY_NAME.put(name(), this); }          // compile error: illegal reference to static field from initializer
        static final Map<String, Registry> BY_NAME = new HashMap<>();
        static { for (Registry r : values()) BY_NAME.put(r.name(), r); }   // correct place
    }

    public static void main(String[] args) throws Exception {
        System.out.println("-- values() returns a fresh clone each call");
        Level[] v1 = Level.values(), v2 = Level.values();
        System.out.println("  same array? " + (v1 == v2) + ", same elements? " + (v1[0] == v2[0]));
        v1[0] = null;                                         // harmless: only our copy changed
        System.out.println("  Level.values()[0] still " + Level.values()[0]);

        System.out.println("-- constant-specific bodies are anonymous subclasses");
        System.out.println("  Op.ADD.getClass()          = " + Op.ADD.getClass());
        System.out.println("  Op.ADD.getDeclaringClass() = " + Op.ADD.getDeclaringClass());
        System.out.println("  " + Op.ADD.apply(3, 4) + " " + Op.MUL.apply(3, 4) + " " + Op.MUL.sym);

        System.out.println("-- valueOf / switch / EnumMap");
        try { Level.valueOf("low"); } catch (IllegalArgumentException e) { System.out.println("  " + e.getMessage()); }
        Level lv = Level.MID;
        switch (lv) { case LOW -> System.out.println("  low"); case MID -> System.out.println("  mid (case label is unqualified)"); default -> {} }
        Level nul = null;
        try { switch (nul) { case LOW -> {} default -> {} } } catch (NullPointerException e) { System.out.println("  switch(null enum) -> NPE"); }
        EnumMap<Level, Integer> em = new EnumMap<>(Level.class);
        em.put(Level.HIGH, 3); em.put(Level.LOW, 1);
        System.out.println("  EnumMap iterates in ordinal order: " + em);

        System.out.println("-- singleton, equality, compareTo");
        Singleton.INSTANCE.hit(); Singleton.INSTANCE.hit();
        System.out.println("  hits = " + Singleton.INSTANCE.hits + ", == works: " + (Level.valueOf("LOW") == Level.LOW));
        System.out.println("  compareTo uses ordinal: " + Level.LOW.compareTo(Level.HIGH));

        System.out.println("-- ordinal() is fragile");
        System.out.println("  " + Level.HIGH.ordinal() + " (insert a constant above HIGH and every stored ordinal silently changes meaning)");

        System.out.println("-- static registry must be filled in a static block");
        System.out.println("  " + Registry.BY_NAME.get("B"));

        System.out.println("-- cannot be instantiated reflectively");
        try { Level.class.getDeclaredConstructors()[0].newInstance("X", 9); }
        catch (Exception e) { System.out.println("  " + e.getClass().getSimpleName() + ": " + e.getMessage()); }
    }
}
```

```text
-- values() returns a fresh clone each call
  same array? false, same elements? true
  Level.values()[0] still LOW
-- constant-specific bodies are anonymous subclasses
  Op.ADD.getClass()          = class EnumQuirks$Op$1
  Op.ADD.getDeclaringClass() = class EnumQuirks$Op
  7 12 *
-- valueOf / switch / EnumMap
  No enum constant EnumQuirks.Level.low
  mid (case label is unqualified)
  switch(null enum) -> NPE
  EnumMap iterates in ordinal order: {LOW=1, HIGH=3}
-- singleton, equality, compareTo
  hits = 2, == works: true
  compareTo uses ordinal: -2
-- ordinal() is fragile
  2 (insert a constant above HIGH and every stored ordinal silently changes meaning)
-- static registry must be filled in a static block
  B
-- cannot be instantiated reflectively
  IllegalArgumentException: Cannot reflectively create enum objects
```

Take-aways:

- `values()` returns a **new array every call** (defensive clone): cache it in a `private static final` array if you call it in a hot path, and never expect mutation of it to stick.
- Constants with bodies are **anonymous subclasses** (`EnumQuirks$Op$1`); use **`getDeclaringClass()`**, not `getClass()`, in generic code (`EnumMap` and `Enum.compareTo` do).
- `==` is correct and null-safe for enums; `switch` on a `null` enum throws **NPE** (unlike `Objects.equals`); `valueOf` is case-sensitive and throws `IllegalArgumentException`.
- `EnumMap`/`EnumSet` are array/bit-vector backed: fastest keyed collections, **iterate in ordinal (declaration) order**.
- **Never persist `ordinal()`** (DB column, wire format): reordering or inserting a constant silently re-maps old data. Persist `name()` or an explicit code field.
- An enum constructor **cannot touch a static field** (compile error `illegal reference to static field from initializer`): constants are created *before* static initialisers run. Fill lookup maps in a `static {}` block, as shown.
- Enum singleton (`Singleton.INSTANCE`) is the only singleton form that survives **serialisation, reflection** (`Cannot reflectively create enum objects`) and cloning for free.

---

## 4. Interfaces: default, static, private

```java
// Run: InterfaceRules.java
public class InterfaceRules {
    interface Walker { default String move() { return "walk"; } }
    interface Swimmer { default String move() { return "swim"; } }
    static class Duck implements Walker, Swimmer {
        // without this override: compile error "types Walker and Swimmer are incompatible"
        @Override public String move() { return Walker.super.move() + "+" + Swimmer.super.move(); }
    }

    interface Greeter {
        String name();
        default String greet() { return decorate("Hello " + name()); }
        private String decorate(String s) { return "*" + s + "*"; }      // private helper (Java 9)
        static Greeter of(String n) { return () -> n; }                  // static factory on the interface
    }

    static class Base { public String who() { return "Base class"; } }
    interface Who { default String who() { return "Who interface"; } }
    static class Mixed extends Base implements Who { }                   // "class wins" rule

    interface Constants { int LIMIT = 10; }                              // implicitly public static final

    public static void main(String[] args) {
        System.out.println(new Duck().move());
        System.out.println(Greeter.of("Ada").greet());
        System.out.println(new Mixed().who());
        System.out.println(Constants.LIMIT);
        // Duck.of("x") would NOT compile: static interface methods are not inherited; write Greeter.of(...)
        // `default String toString()` in an interface -> compile error: a default method cannot override Object's methods
    }
}
```

```text
walk+swim
*Hello Ada*
Base class
10
```

Rules of conflict resolution (JLS 8.4.8): **(1) class wins** — a method inherited from a superclass beats an interface default (`Mixed` printed `Base class`); **(2) the most specific interface wins** if one extends the other; **(3) otherwise you must override** and may delegate with `Interface.super.method()`. Without the override in `Duck`, javac says:

```text
C6.java:1: error: types A and B are incompatible;
  class C inherits unrelated defaults for m() from types A and B
```

Other facts: interface **static methods are not inherited** (call them as `Greeter.of(..)`); **private** interface methods (Java 9) share code between defaults; interface fields are implicitly `public static final`; a default method **cannot override `Object` methods** (`toString`, `equals`, `hashCode`), because the class-wins rule would always shadow it.

---

## 5. Casting & `instanceof`: compile error or `ClassCastException`?

Rule of thumb: the **compiler** rejects a cast only when the two *static* types can **provably never** relate (unrelated classes; a `final` class that doesn't implement the interface). Everything else compiles and is checked **at run time** (`ClassCastException`).

```java
// Run: CastingRules.java
import java.util.*;

public class CastingRules {
    interface Flyer { }
    static class Animal { }
    static class Dog extends Animal { }
    static final class Rock { }

    static void attempt(String label, Runnable r) {
        try { r.run(); System.out.println(label + " -> ok"); }
        catch (ClassCastException e) { System.out.println(label + " -> ClassCastException"); }
    }

    public static void main(String[] args) {
        Object o = "text";
        attempt("(Integer) obj holding a String", () -> { Integer i = (Integer) o; });

        Animal animal = new Animal();
        attempt("(Dog) new Animal()            ", () -> { Dog d = (Dog) animal; });
        attempt("(Flyer) new Animal()          ", () -> { Flyer f = (Flyer) animal; });  // compiles: a subclass could implement Flyer
        // Rock r = new Rock(); Flyer f2 = (Flyer) r;     // COMPILE error: Rock is final and does not implement Flyer
        // Integer n = (Integer) "text";                  // COMPILE error: incompatible types
        // Dog d2 = (Dog) new Rock();                     // COMPILE error: unrelated classes

        Object nul = null;
        System.out.println("(String) null          -> " + (String) nul);                  // casting null always succeeds
        System.out.println("null instanceof Object -> " + (nul instanceof Object));       // always false

        List<String> strings = new ArrayList<>();
        @SuppressWarnings({"unchecked", "rawtypes"})
        List<Integer> sneaky = (List) strings;                 // unchecked: erasure means no runtime check
        sneaky.add(42);                                        // heap pollution
        System.out.println("size via sneaky = " + strings.size());
        try { String s = strings.get(0); }                     // the compiler-inserted checkcast fails HERE
        catch (ClassCastException e) { System.out.println("later, at the read site -> ClassCastException"); }

        Object x = 42;
        if (x instanceof Integer n && n > 40) System.out.println("pattern variable n = " + n);

        System.out.println("(int) (1L << 40) = " + (int) (1L << 40) + ", (int) 3_000_000_000L = " + (int) 3_000_000_000L);
        Object boxed = 5;                                      // an Integer
        try { long l = (Long) boxed; } catch (ClassCastException e) { System.out.println("(Long) obj holding Integer -> CCE"); }
        long ok = (Integer) boxed;                             // cast to Integer, unbox, widen: fine
        System.out.println("(Integer) then widen -> " + ok);
    }
}
```

```text
(Integer) obj holding a String -> ClassCastException
(Dog) new Animal()             -> ClassCastException
(Flyer) new Animal()           -> ClassCastException
(String) null          -> null
null instanceof Object -> false
size via sneaky = 1
later, at the read site -> ClassCastException
pattern variable n = 42
(int) (1L << 40) = 0, (int) 3_000_000_000L = -1294967296
(Long) obj holding Integer -> CCE
(Integer) then widen -> 5
```

Compile-time rejections (real `javac` output):

```text
C1.java:1: error: incompatible types: Rock cannot be converted to Flyer     // final class Rock, interface Flyer
C2.java:1: error: incompatible types: String cannot be converted to Integer  // (Integer) "text"
```

Notes: `null` can be cast to anything and is `instanceof` nothing; `(Flyer) animal` compiled because *a subclass of `Animal` might implement `Flyer`*; the **unchecked** generic cast produced heap pollution that exploded **later and elsewhere** (at the read site) — the reason for the [PECS/erasure rules](../01-java-basics/06-generics.md); casting `Object`→`Long` when it holds an `Integer` fails, but `(Integer)` then widening works; narrowing `long→int` silently keeps the low 32 bits.

---

## 6. Arrays

<details>
<summary><b>Puzzle 1.</b> Covariance: what does this do?</summary>

```java
Object[] objs = new String[1];
objs[0] = 1;
```

**`ArrayStoreException: java.lang.Integer`** (at run time, compiles fine). Arrays are **covariant and reified**: a `String[]` is an `Object[]` for the compiler, but the array object remembers its real element type and checks every store. Generics are invariant and erased, so `List<Object> l = new ArrayList<String>()` is a compile error instead. This is why you can't create `new T[n]` or `new List<String>[n]`.
</details>

<details>
<summary><b>Puzzle 2.</b> Size of the list?</summary>

```java
int[] prim = {1, 2, 3};
Integer[] boxed = {1, 2, 3};
System.out.println(Arrays.asList(prim).size() + " " + Arrays.asList(boxed).size());
```

**`1 3`**. `asList(T...)` needs `T[]`; an `int[]` is not a `T[]`, so the whole array becomes **one element** of a `List<int[]>`. Use `Arrays.stream(prim).boxed().toList()` or `IntStream`.
</details>

<details>
<summary><b>Puzzle 3.</b> Is <code>Arrays.asList</code> mutable?</summary>

```java
Integer[] arr = {1, 2, 3};
List<Integer> view = Arrays.asList(arr);
view.set(0, 99);
System.out.println(arr[0]);
view.add(4);
```

Prints **`99`**, then `add` throws **`UnsupportedOperationException`**. `Arrays.asList` is a **fixed-size write-through view** of the array: `set` writes the array, `add`/`remove` are unsupported. Wrap in `new ArrayList<>(Arrays.asList(..))` for a real list, or use `List.of` for an immutable one.
</details>

<details>
<summary><b>Puzzle 4.</b> Shared rows</summary>

```java
int[][] rows = new int[3][];
Arrays.fill(rows, new int[2]);
rows[0][0] = 7;
System.out.println(Arrays.deepToString(rows));
```

**`[[7, 0], [7, 0], [7, 0]]`** — `fill` stores the *same* `int[2]` reference in all three slots. Build rows in a loop (`rows[i] = new int[2]`) or `new int[3][2]`.
</details>

<details>
<summary><b>Puzzle 5.</b> <code>clone()</code> of a 2-D array</summary>

```java
int[][] a = {{1, 2}, {3, 4}};
int[][] b = a.clone();
b[0][0] = 99;
b[1] = new int[]{0, 0};
System.out.println(Arrays.deepToString(a));
```

**`[[99, 2], [3, 4]]`**. `clone()` copies the **outer** array only (shallow): the inner arrays are shared, so `b[0][0] = 99` is visible through `a`, while replacing `b[1]` is not. Deep copy: `Arrays.stream(a).map(int[]::clone).toArray(int[][]::new)`.
</details>

<details>
<summary><b>Puzzle 6.</b> Printing a <code>char[]</code></summary>

```java
char[] cs = {'h', 'i'};
System.out.println(cs);
System.out.println(("" + cs).startsWith("[C@"));
System.out.println(String.valueOf(cs));
```

**`hi`, `true`, `hi`**. `PrintStream.println(char[])` is a dedicated overload that prints the characters; string concatenation calls `toString()` → `[C@<hash>`. (And `System.out.println(null)` doesn't compile: *"reference to println is ambiguous: both `println(char[])` and `println(String)` match"*.)
</details>

<details>
<summary><b>Puzzle 7.</b> Array equality</summary>

```java
int[] x = {1, 2}, y = {1, 2};
System.out.println(x.equals(y) + " " + Arrays.equals(x, y) + " "
        + (x.hashCode() == y.hashCode()) + " " + (Arrays.hashCode(x) == Arrays.hashCode(y)));
```

**`false true false true`**. Arrays inherit identity `equals`/`hashCode` from `Object`. Use `Arrays.equals`/`hashCode` (or `deepEquals`/`deepHashCode` for nested). Consequently an array as a `HashMap` key or in a `record` component compares by **reference** — wrap it in a `List` or compare manually.
</details>

---

## 7. Typing, operators & control flow

<details>
<summary><b>Puzzle 8.</b> Ternary typing: what do these print?</summary>

```java
char c = 'x'; int i = 0;
System.out.println(true ? c : 0);
System.out.println(true ? c : i);
System.out.println(false ? 1 : 'a');
```

**`x`, `120`, `a`**. If one operand is `char` and the other an `int` **constant that fits in `char`**, the type is `char`. With a non-constant `int` variable, binary numeric promotion gives `int`, so the `char` prints as its code `120`. Rule of thumb: the ternary's type is decided **statically** from both branches, not from the branch taken.
</details>

<details>
<summary><b>Puzzle 9.</b> Ternary with boxed and primitive operands</summary>

```java
Object o  = true ? 1 : 2.0;
Object o2 = true ? (Object) 1 : 2.0;
Integer n = null;
Integer r = true ? n : Integer.valueOf(0);
System.out.println(o + " " + o2 + " " + r);
```

**`1.0 1 null`**. `1 : 2.0` promotes to `double` before boxing → `1.0`. Casting one side to `Object` makes it a reference conditional → stays `Integer 1`. With both operands `Integer` there is no unboxing, so `null` passes; with `true ? n : 0` (int) it would **NPE** (see [wrappers note §2.2](../01-java-basics/02-primitives-wrappers-equality.md)).
</details>

<details>
<summary><b>Puzzle 10.</b> Concatenation vs addition</summary>

```java
System.out.println(1 + 2 + "3" + 4 + 5);
System.out.println("" + 1 + 2 + '3' + (char) 52);
```

**`3345`** and **`1234`**. `+` is left-associative: `1 + 2` is `int` addition → `3`; once a `String` appears everything after is concatenation. `(char) 52` is the character `'4'`.
</details>

<details>
<summary><b>Puzzle 11.</b> Side effects in one expression</summary>

```java
int a = 1; a += a++ + ++a; System.out.println(a);
int x = 5; x = x++ + ++x;  System.out.println(x);
```

**`5`** and **`12`**. Java evaluates **left to right** and `a += e` is `a = a + e` with the **old** `a` saved first: `1 + (1 + 3) = 5` (`a++` yields 1 and makes `a` 2; `++a` makes it 3). `x++ + ++x` = `5 + 7`. Never write these; but know the order is *defined* (unlike C).
</details>

<details>
<summary><b>Puzzle 12.</b> Precedence</summary>

```java
System.out.println(1 + 2 << 3);
System.out.println(true || false && false);
System.out.println(-1 >>> 1 == Integer.MAX_VALUE);
```

**`24`, `true`, `true`**. `+` binds tighter than `<<` → `3 << 3`; `&&` binds tighter than `||`; shifts bind tighter than `==`. And the famous `if (x & 1 == 0)` does not compile because `==` binds tighter than `&`:

```text
C7.java:1: error: bad operand types for binary operator '&'
  first type:  int   second type: boolean
```

Write `(x & 1) == 0`.
</details>

<details>
<summary><b>Puzzle 13.</b> <code>&</code> vs <code>&&</code>, and assignment in a condition</summary>

```java
String s = null;
if (s != null & s.length() > 0) { }        // (A)
if (s != null && s.length() > 0) { }       // (B)
boolean b = false;
if (b = true) System.out.println("b is now " + b);
```

(A) throws **NPE**: the non-short-circuit `&` evaluates both sides. (B) is safe. The last line **assigns** `true` and then tests it: prints `b is now true` (compiles because `boolean = boolean` is a boolean expression; with `int` it would not compile — one reason to prefer `if (flag)` over `if (flag == true)`).
</details>

<details>
<summary><b>Puzzle 14.</b> The infinite <code>double</code> loop</summary>

```java
int count = 0;
for (double d = 0; d != 1.0 && count < 15; d += 0.1) count++;
System.out.println(count);
```

**`15`** (the guard stopped it). `0.1` summed ten times is `0.9999999999999999`, never exactly `1.0`, so `d != 1.0` never becomes false. Never use `==`/`!=` on floating point as a loop condition; use `<` with a tolerance or an integer counter.
</details>

<details>
<summary><b>Puzzle 15.</b> A static method on a <code>null</code> reference</summary>

```java
static class Util { static String hi() { return "static call on a null reference works"; } }
Util u = null;
System.out.println(u.hi());
```

Prints **`static call on a null reference works`**. Static methods are bound to the **declared type**; the reference is never dereferenced. (Instance calls on `null` NPE; so does `switch` on a `null` String/enum.) Static analysers flag this: call `Util.hi()`.
</details>

<details>
<summary><b>Puzzle 16.</b> Switch fall-through with <code>default</code> in the middle</summary>

```java
switch (3) {
    case 1: System.out.print("one ");
    default: System.out.print("default ");
    case 2: System.out.print("two "); break;
    case 4: System.out.print("four ");
}
```

**`default two `**. No case matches 3 → jump to `default`, then **fall through** into `case 2` (placement of `default` doesn't matter for matching, but does for fall-through), `break` stops. Arrow-form `case X ->` (Java 14+) never falls through.
</details>

<details>
<summary><b>Puzzle 17.</b> <code>switch</code> expression, <code>yield</code>, and <code>char</code> vs <code>int</code> labels</summary>

```java
String s = switch ("b") { case "a" -> "A"; case "b" -> { String t = "B"; yield t + t; } default -> "?"; };
char c = 'b';
switch (c) { case 'a' -> System.out.println("a"); case 98 -> System.out.println("98 matched 'b'"); default -> System.out.println("none"); }
System.out.println(s);
```

Prints **`98 matched 'b'`** then **`BB`**. A `switch` expression must be exhaustive and uses `yield` inside a block. `case 98` is allowed for a `char` selector because the constant is assignable to `char`; labels must be constants, and **duplicates after conversion are a compile error**. `switch` on a `String` uses `hashCode` + `equals` and NPEs on `null`.
</details>

<details>
<summary><b>Puzzle 18.</b> Labelled <code>break</code> / <code>continue</code></summary>

```java
outer:
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        if (j == 2) continue outer;
        if (i == 2) break outer;
        System.out.print(i + "" + j + " ");
    }
}
```

**`00 01 10 11 `**. `continue outer` abandons the inner loop and moves to the next `i`; `break outer` leaves **both** loops (at `i == 2, j == 0`). Labels are legit for matrix searches, but extracting a method with `return` is usually clearer.
</details>

### 7.1 Unicode escapes are translated before the lexer

```java
// Run: UnicodeEscape.java
public class UnicodeEscape {
    public static void main(String[] args) {
        // Is this line a comment? \u000a System.out.println("I was inside a comment!");
        System.out.println("main continues");
        char c = 'A';                                    // unicode escapes are translated BEFORE lexing
        System.out.println(c);
        String s = "tab\there";                               // \t is an ordinary escape sequence, handled later
        System.out.println(s);
    }
}
```

```text
I was inside a comment!
main continues
A
tab	here
```

`\u000a` is a **line feed** inserted into the source *before* tokenising, so the "comment" ended and the `println` after it became real code. (The reverse also bites: writing `"\u%04x"` in source fails with `illegal unicode escape` — I hit this while writing the demo; write `"\\u%04x"`.) Since Java 15 text blocks and `\s`/`\<newline>` escapes exist, but Unicode pre-translation is unchanged.

---

## 8. Overload resolution & varargs

Three phases, always in this order: **(1) subtyping/widening only, no boxing; (2) boxing/unboxing allowed; (3) varargs.** The first phase that finds *any* applicable method wins; among those, the **most specific** is picked. Static (declared) types decide, never the runtime type.

```java
// Run: OverloadResolution.java
public class OverloadResolution {
    static void f(long x)      { System.out.println("f(long)"); }
    static void f(Integer x)   { System.out.println("f(Integer)"); }
    static void f(Object x)    { System.out.println("f(Object)"); }
    static void f(int... x)    { System.out.println("f(int...)"); }

    static void g(Object x)    { System.out.println("g(Object)"); }
    static void g(String x)    { System.out.println("g(String)"); }

    static void h(Object... xs) { System.out.println("h: xs = " + (xs == null ? "null array" : xs.length + " element(s)")); }

    static void k(double d)    { System.out.println("k(double)"); }
    static void k(Object o)    { System.out.println("k(Object)"); }

    public static void main(String[] args) {
        System.out.println("-- widening beats boxing beats varargs");
        f(1);                    // phase 1 (no boxing): f(long) via widening
        f(Integer.valueOf(1));   // phase 1: f(Integer) is an exact match
        f('a');                  // char widens to long
        f("s");                  // only f(Object) applies
        f();                     // only varargs applies

        System.out.println("-- most specific wins");
        g("s");
        g(null);                 // String is more specific than Object
        g((Object) "s");         // static type decides, not runtime type

        System.out.println("-- varargs and null");
        h();                     // empty array
        h(1, 2);
        h((Object) null);        // one element: null
        h((Object[]) null);      // the array itself is null
        h(new String[]{"a", "b"});   // String[] IS an Object[] -> spread into 2 elements
        h(new int[]{1, 2});          // int[] is not an Object[] -> ONE element

        System.out.println("-- boxing vs widening");
        k(1);                    // int -> double is a widening: preferred over boxing to Integer -> Object
        k(Integer.valueOf(1));   // phase 1: Integer -> Object (subtyping) beats unboxing+widening
    }
}
```

```text
-- widening beats boxing beats varargs
f(long)
f(Integer)
f(long)
f(Object)
f(int...)
-- most specific wins
g(String)
g(String)
g(Object)
-- varargs and null
h: xs = 0 element(s)
h: xs = 2 element(s)
h: xs = 1 element(s)
h: xs = null array
h: xs = 2 element(s)
h: xs = 1 element(s)
-- boxing vs widening
k(double)
k(Object)
```

(`javac` also prints a *warning* for `h(new String[]{...})`: "non-varargs call of varargs method with inexact argument type" — precisely because that call spreads the array. Cast to `Object` for one element or `Object[]` to silence it deliberately.)

Highlights:

- `f(1)` → `f(long)` (widening, phase 1) **beats** `f(Integer)` (boxing, phase 2).
- `g(null)` → `g(String)`: most specific. With `g(String)` and `g(Integer)` it is **ambiguous**, a compile error. Likewise `f(int...)` vs `f(Integer...)` called with `f(1)`:

```text
C5.java:1: error: reference to g is ambiguous
  both method g(String) in C5 and method g(Integer) in C5 match
C4.java:1: error: reference to f is ambiguous
  both method f(int...) in C4 and method f(Integer...) in C4 match
```

- `h((Object[]) null)` passes a **null array**: `for (Object o : xs)` NPEs. `h((Object) null)` passes one `null` element. `h(new int[]{1,2})` is **one** element (an `int[]` is not an `Object[]`).
- Overloading varargs with non-varargs of the same prefix is a trap; prefer distinct method names.

---

## 9. `final`, effectively final, immutability & copying

```java
// Run: CloneAndFinal.java
import java.util.*;
import java.util.function.Supplier;

public class CloneAndFinal {
    // ---- Cloneable: shallow by default ----
    static class Team implements Cloneable {
        String name;
        List<String> members = new ArrayList<>();
        Team(String name) { this.name = name; }
        @Override public Team clone() {                       // covariant return, public, no checked exception
            try {
                Team copy = (Team) super.clone();             // bitwise copy: `members` still points at the SAME list
                return copy;
            } catch (CloneNotSupportedException e) { throw new AssertionError(e); }
        }
        Team deepClone() {
            Team copy = clone();
            copy.members = new ArrayList<>(members);          // you must remember every mutable field
            return copy;
        }
    }

    // ---- Copy constructor / record: the modern alternative ----
    static class Point {
        final int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }
        Point(Point other) { this(other.x, other.y); }        // no Cloneable, no casts, final fields allowed
    }
    record Order(String id, List<String> items) {
        Order { items = List.copyOf(items); }                 // defensive copy: immutable inside the record
    }

    static class NoClone { Object tryClone() throws CloneNotSupportedException { return super.clone(); } }

    // ---- final vs effectively final vs immutable ----
    static int counter = 0;                                   // statics and fields CAN be mutated from lambdas

    public static void main(String[] args) throws Exception {
        System.out.println("-- clone is shallow");
        Team a = new Team("A");
        a.members.add("ann");
        Team shallow = a.clone();
        shallow.members.add("bob");
        System.out.println("  original members after adding to the shallow clone: " + a.members + "  (shared list!)");
        Team deep = a.deepClone();
        deep.members.add("cat");
        System.out.println("  after the deep clone changes: original=" + a.members + " deep=" + deep.members);

        System.out.println("-- Cloneable has no clone() method; Object.clone() is protected");
        try { new NoClone().tryClone(); } catch (CloneNotSupportedException e) { System.out.println("  CloneNotSupportedException: " + e.getMessage()); }
        int[] arr = {1, 2, 3};
        System.out.println("  arrays have a public clone(): " + Arrays.toString(arr.clone()) + ", same object? " + (arr.clone() == arr));

        System.out.println("-- copy constructor and defensive copies");
        Point p = new Point(1, 2), q = new Point(p);
        System.out.println("  copy: " + q.x + "," + q.y + ", same object? " + (p == q));
        List<String> items = new ArrayList<>(List.of("pen"));
        Order o = new Order("o1", items);
        items.add("sneaky");
        System.out.println("  record keeps its own copy: " + o.items());
        try { o.items().add("x"); } catch (UnsupportedOperationException e) { System.out.println("  and it is immutable -> UnsupportedOperationException"); }

        System.out.println("-- final reference != immutable object");
        final List<String> fixed = new ArrayList<>();
        fixed.add("still mutable");
        System.out.println("  " + fixed);
        // fixed = new ArrayList<>();                         // compile error: cannot assign a value to final variable

        System.out.println("-- effectively final");
        int base = 10;                                        // never reassigned -> effectively final
        Supplier<Integer> s1 = () -> base + 1;
        // base++;                                            // un-commenting this breaks the lambda above:
                                                              // "local variables referenced from a lambda expression must be final or effectively final"
        System.out.println("  " + s1.get());
        int[] box = {0};                                      // the 'array of one' workaround: reference is final, contents are not
        Runnable inc = () -> box[0]++;
        inc.run(); inc.run();
        Runnable incStatic = () -> counter++;                 // static/instance fields need no workaround (and no thread-safety)
        incStatic.run();
        System.out.println("  box[0] = " + box[0] + ", counter = " + counter + "  (a shared mutable counter in a parallel stream would be a data race)");

        System.out.println("-- final fields and safe publication");
        System.out.println("  final fields are guaranteed visible after construction; non-final fields are not (JMM) -> see 03-concurrency/04");

        System.out.println("-- final on a method/class means different things");
        System.out.println("  final method: cannot override | final class: cannot extend | final param/local: cannot reassign | final field: assigned once");
    }
}
```

```text
-- clone is shallow
  original members after adding to the shallow clone: [ann, bob]  (shared list!)
  after the deep clone changes: original=[ann, bob] deep=[ann, bob, cat]
-- Cloneable has no clone() method; Object.clone() is protected
  CloneNotSupportedException: CloneAndFinal$NoClone
  arrays have a public clone(): [1, 2, 3], same object? false
-- copy constructor and defensive copies
  copy: 1,2, same object? false
  record keeps its own copy: [pen]
  and it is immutable -> UnsupportedOperationException
-- final reference != immutable object
  [still mutable]
-- effectively final
  11
  box[0] = 2, counter = 1  (a shared mutable counter in a parallel stream would be a data race)
-- final fields and safe publication
  final fields are guaranteed visible after construction; non-final fields are not (JMM) -> see 03-concurrency/04
-- final on a method/class means different things
  final method: cannot override | final class: cannot extend | final param/local: cannot reassign | final field: assigned once
```

- `Object.clone()` is `protected`, `Cloneable` is an empty **marker** interface (the method isn't on it), the default is a **shallow bitwise copy**, it bypasses constructors (so `final` fields can't be re-assigned), and it throws a checked exception. Josh Bloch's verdict (Effective Java Item 13): **prefer copy constructors/factories**, or records with defensive `List.copyOf`. The one good use: arrays (`arr.clone()`).
- `final` on a reference means *the variable can't be reassigned*, **not** that the object is immutable. Immutable class recipe: `final` class, `private final` fields, no setters, defensive copies in and out, no `this` escape in the constructor.
- A lambda/anonymous class can capture locals only if **effectively final** (never reassigned). Reassigning breaks compilation:

```text
C9.java:1: error: local variables referenced from a lambda expression must be final or effectively final
```

  The `int[1]`-box trick compiles but is a thread-safety smell — prefer `AtomicInteger`, a `reduce`, or a plain loop.

---

## 10. Object contract, `hashCode` helpers & `Optional`

<details>
<summary><b>Puzzle 19.</b> Default <code>toString</code> and <code>hashCode</code></summary>

```java
Object o = new Object();
String s = o.toString();
System.out.println(s.startsWith("java.lang.Object@") + " " + s.equals("java.lang.Object@" + Integer.toHexString(o.hashCode())));
```

**`true true`**. Default `toString` = `getClass().getName() + "@" + Integer.toHexString(hashCode())`; default `hashCode` is an **identity hash** (not a memory address you can rely on, stable for the object's life, and stored in the header). If you override `equals`, override `hashCode` ([contract](../02-collections/02-equals-hashcode.md)).
</details>

<details>
<summary><b>Puzzle 20.</b> <code>Objects.hash</code> vs <code>hashCode</code></summary>

```java
System.out.println(Objects.hash(1) + " " + Integer.valueOf(1).hashCode() + " "
        + Objects.hash(1, 2) + " " + Arrays.asList(1, 2).hashCode());
System.out.println(Objects.hash() + " " + Arrays.hashCode(new int[0]) + " " + List.of().hashCode()
        + " " + Objects.hashCode(null) + " " + Objects.hash((Object) null));
```

**`32 1 994 994`** and **`1 1 1 0 31`**. `Objects.hash(a, b…)` is `Arrays.hashCode(Object[])`: start at **1**, then `31*h + e.hashCode()`. So a *single* element gives `31 + hash`, **not** the element's hash; an empty call gives 1; `Objects.hash(a,b)` equals the `List.of(a,b)` hash by construction. It also **boxes** primitives and allocates a varargs array per call — in a hot `hashCode()` prefer a hand-rolled `31 * h + ...` chain or a `record`.
</details>

<details>
<summary><b>Puzzle 21.</b> Known hash values</summary>

```java
System.out.println(List.of(1, 2, 3).hashCode() + " " + Set.of(1, 2, 3).hashCode() + " " + Map.of(1, 2).hashCode()
        + " " + "ab".hashCode() + " " + Boolean.hashCode(true) + " " + Long.hashCode(1L << 32)
        + " " + Double.hashCode(0.0) + " " + Double.hashCode(-0.0));
```

**`30817 6 3 3105 1231 1 0 -2147483648`**. List: order-sensitive polynomial (31). Set: **sum** of element hashes (order-free). Map: sum of `keyHash ^ valueHash` (`1 ^ 2 = 3`). `String`: `s[0]*31^(n-1) + …` (`"ab"` = 97*31 + 98). `Boolean` 1231/1237. `Long`: `(int)(v ^ (v >>> 32))`. `Double.hashCode(-0.0)` differs from `0.0` (bit pattern) — consistent with `Double.equals` ([wrappers note](../01-java-basics/02-primitives-wrappers-equality.md)).
</details>

<details>
<summary><b>Puzzle 22.</b> <code>Objects.hash</code> with an array argument</summary>

```java
String[] sa = {"a", "b"};
System.out.println(Objects.hash(sa) == Objects.hash("a", "b"));
System.out.println(Objects.hash((Object) sa) == Objects.hash("a", "b"));
int[] ia = {1, 2};
System.out.println(Objects.hash(ia) == Objects.hash(1, 2));
```

**`true false false`**. A `String[]` *is* an `Object[]`, so it is spread as the varargs array. Cast to `Object` → one element, hashed by identity. An `int[]` is always one element (identity hash). Same family of traps as `Arrays.asList(int[])` (Puzzle 2).
</details>

<details>
<summary><b>Puzzle 23.</b> <code>orElse</code> vs <code>orElseGet</code></summary>

```java
static int sideEffects = 0;
static String expensive() { sideEffects++; return "computed"; }
// ...
Optional<String> o = Optional.of("x");
String a = o.orElse(expensive());
System.out.println(sideEffects + " " + a);
String b = o.orElseGet(() -> expensive());
System.out.println(sideEffects + " " + b);
```

**`1 x`** then **`1 x`**. `orElse(expensive())` evaluates its **argument eagerly** even though the Optional is present (a DB call or object creation you pay for every time!). `orElseGet(supplier)` is lazy. Also: `Optional.of(null)` → NPE (`ofNullable` for maybe-null); `Optional.ofNullable(null).equals(Optional.empty())` is `true`. Misuse list: `Optional` as a field, method **parameter**, collection element, or `isPresent()`+`get()` instead of `map/orElseThrow` ([design guidance](../01-java-basics/07-lambdas-streams-optional.md)); never `==` compare Optionals; they are not `Serializable`.
</details>

<details>
<summary><b>Puzzle 24.</b> <code>List.remove(int)</code> vs <code>remove(Object)</code></summary>

```java
List<Integer> list = new ArrayList<>(List.of(10, 20, 30, 1));
list.remove(1);
System.out.println(list);
list.remove(Integer.valueOf(1));
System.out.println(list);
```

**`[10, 30, 1]`** then **`[10, 30]`**. `remove(1)` picks the exact-match `remove(int index)` (phase 1, no boxing); only an `Integer` argument selects `remove(Object)`.
</details>

---

## 11. Collections & comparator traps

```java
// Run: CollectionTraps.java
import java.util.*;

public class CollectionTraps {
    public static void main(String[] args) {
        System.out.println("-- 1. remove inside for-each");
        List<String> list = new ArrayList<>(List.of("a", "b", "c", "d"));
        try { for (String s : list) if (s.equals("b")) list.remove(s); }
        catch (ConcurrentModificationException e) { System.out.println("  removing \"b\" -> CME"); }

        List<String> second2last = new ArrayList<>(List.of("a", "b", "c", "d"));
        for (String s : second2last) if (s.equals("c")) second2last.remove(s);   // 2nd-to-last: hasNext() is false -> loop just ends
        System.out.println("  removing \"c\" (second to last) -> no exception, result " + second2last);

        System.out.println("-- 2. the three safe ways");
        List<Integer> nums = new ArrayList<>(List.of(1, 2, 3, 4, 5, 6));
        nums.removeIf(n -> n % 2 == 0);
        System.out.println("  removeIf       : " + nums);
        for (Iterator<Integer> it = nums.iterator(); it.hasNext(); ) if (it.next() == 3) it.remove();
        System.out.println("  Iterator.remove: " + nums);
        List<Integer> copy = new ArrayList<>(nums);
        for (Integer n : copy) nums.remove(n);                                    // iterate a snapshot
        System.out.println("  iterate a copy : " + nums);

        System.out.println("-- 3. remove(int) vs remove(Object)");
        List<Integer> l = new ArrayList<>(List.of(10, 20, 30, 1));
        l.remove(1);                       // index 1
        System.out.println("  remove(1)                  -> " + l);
        l.remove(Integer.valueOf(1));      // value 1
        System.out.println("  remove(Integer.valueOf(1)) -> " + l);

        System.out.println("-- 4. views vs copies");
        List<String> src = new ArrayList<>(List.of("x", "y"));
        List<String> view = Collections.unmodifiableList(src);
        List<String> snap = List.copyOf(src);
        src.add("z");
        System.out.println("  unmodifiableList sees later change: " + view);
        System.out.println("  List.copyOf does not              : " + snap);
        try { view.add("w"); } catch (UnsupportedOperationException e) { System.out.println("  view.add -> UnsupportedOperationException"); }
        List<Integer> big = new ArrayList<>(List.of(1, 2, 3, 4, 5));
        big.subList(1, 3).clear();
        System.out.println("  subList(1,3).clear() wrote through: " + big);

        System.out.println("-- 5. Arrays.asList / List.of");
        List<String> fixed = Arrays.asList("a", "b");
        fixed.set(0, "A");
        try { fixed.add("c"); } catch (UnsupportedOperationException e) { System.out.println("  Arrays.asList: set ok, add -> UOE, " + fixed); }
        try { List.of("a").contains(null); } catch (NullPointerException e) { System.out.println("  List.of(..).contains(null) -> NPE (ArrayList would say false)"); }
        try { List.of("a", null); } catch (NullPointerException e) { System.out.println("  List.of(\"a\", null) -> NPE"); }
        System.out.println("  Arrays.asList tolerates null: " + Arrays.asList("a", null) + ", new ArrayList contains(null) = " + new ArrayList<>(List.of("a")).contains(null));
        try { Map.of("k", 1, "k", 2); } catch (IllegalArgumentException e) { System.out.println("  Map.of duplicate key -> " + e.getMessage()); }

        System.out.println("-- 6. iteration order is not a contract (Set.of / Map.of)");
        System.out.println("  Set.of is randomised per JVM run: do not depend on its order. TreeSet / LinkedHashSet are ordered by contract.");

        System.out.println("-- 7. Collections.emptyList vs mutable result");
        List<String> empty = Collections.emptyList();
        try { empty.add("x"); } catch (UnsupportedOperationException e) { System.out.println("  emptyList().add -> UOE"); }

        System.out.println("-- 8. equals across list types");
        System.out.println("  ArrayList.equals(LinkedList) = " + new ArrayList<>(List.of(1, 2)).equals(new LinkedList<>(List.of(1, 2)))
                + ", Arrays.asList.equals(List.of) = " + Arrays.asList(1, 2).equals(List.of(1, 2))
                + ", HashSet.equals(TreeSet) = " + new HashSet<>(List.of(1, 2)).equals(new TreeSet<>(List.of(2, 1))));
    }
}
```

```text
-- 1. remove inside for-each
  removing "b" -> CME
  removing "c" (second to last) -> no exception, result [a, b, d]
-- 2. the three safe ways
  removeIf       : [1, 3, 5]
  Iterator.remove: [1, 5]
  iterate a copy : []
-- 3. remove(int) vs remove(Object)
  remove(1)                  -> [10, 30, 1]
  remove(Integer.valueOf(1)) -> [10, 30]
-- 4. views vs copies
  unmodifiableList sees later change: [x, y, z]
  List.copyOf does not              : [x, y]
  view.add -> UnsupportedOperationException
  subList(1,3).clear() wrote through: [1, 4, 5]
-- 5. Arrays.asList / List.of
  Arrays.asList: set ok, add -> UOE, [A, b]
  List.of(..).contains(null) -> NPE (ArrayList would say false)
  List.of("a", null) -> NPE
  Arrays.asList tolerates null: [a, null], new ArrayList contains(null) = false
  Map.of duplicate key -> duplicate key: k
-- 6. iteration order is not a contract (Set.of / Map.of)
  Set.of is randomised per JVM run: do not depend on its order. TreeSet / LinkedHashSet are ordered by contract.
-- 7. Collections.emptyList vs mutable result
  emptyList().add -> UOE
-- 8. equals across list types
  ArrayList.equals(LinkedList) = true, Arrays.asList.equals(List.of) = true, HashSet.equals(TreeSet) = true
```

- The fail-fast `ConcurrentModificationException` is **best-effort** and checked in `next()`: removing the **second-to-last** element makes `hasNext()` return `false` (cursor == size) so the loop silently ends — you "got away with it" *and skipped the last element*. Use `removeIf`, `Iterator.remove`, or iterate a copy.
- `unmodifiableList` is a **read-only view** (later changes show through); `List.copyOf`/`List.of` are **immutable snapshots**. `subList` is a **view**: `clear()` on it deletes from the parent; structurally modifying the parent invalidates it.
- `List.of`/`Set.of`/`Map.of` reject `null` — **even in `contains(null)`** — and `Map.of`/`Set.of` reject duplicates. `Arrays.asList` and `ArrayList` allow nulls.
- `Set.of`/`Map.of` iteration order is deliberately **unspecified and varies between JVM runs** (salted); code that depends on it passes locally and fails in CI.

```java
// Run: ComparatorTraps.java
import java.math.BigDecimal;
import java.util.*;

public class ComparatorTraps {
    record Person(String name, int age) { }

    public static void main(String[] args) {
        System.out.println("-- 1. subtraction comparator overflows");
        Comparator<Integer> broken = (a, b) -> a - b;
        System.out.println("  compare(Integer.MIN_VALUE, 1) = " + broken.compare(Integer.MIN_VALUE, 1) + "  (positive: says MIN_VALUE > 1)");
        System.out.println("  Integer.compare(...)          = " + Integer.compare(Integer.MIN_VALUE, 1));

        System.out.println("-- 2. compareTo inconsistent with equals: BigDecimal");
        BigDecimal a = new BigDecimal("1.0"), b = new BigDecimal("1.00");
        System.out.println("  equals = " + a.equals(b) + ", compareTo = " + a.compareTo(b));
        Set<BigDecimal> hash = new HashSet<>(List.of(a, b));
        Set<BigDecimal> tree = new TreeSet<>(List.of(a, b));
        System.out.println("  HashSet size = " + hash.size() + ", TreeSet size = " + tree.size());

        System.out.println("-- 3. TreeSet/TreeMap use the comparator as equality");
        TreeSet<String> ci = new TreeSet<>(String.CASE_INSENSITIVE_ORDER);
        ci.add("Java"); ci.add("JAVA"); ci.add("java");
        System.out.println("  " + ci + " contains(\"jAvA\") = " + ci.contains("jAvA"));

        System.out.println("-- 4. sort is stable (List.sort / Collections.sort / Stream.sorted on objects)");
        List<Person> people = new ArrayList<>(List.of(new Person("Zed", 30), new Person("Amy", 25), new Person("Bob", 30), new Person("Cat", 25)));
        people.sort(Comparator.comparingInt(Person::age));
        System.out.println("  by age only keeps input order inside ties: " + people.stream().map(Person::name).toList());
        people.sort(Comparator.comparingInt(Person::age).reversed().thenComparing(Person::name));
        System.out.println("  age desc, name asc: " + people.stream().map(Person::name).toList());

        System.out.println("-- 5. nulls");
        List<String> withNull = new ArrayList<>(Arrays.asList("b", null, "a"));
        try { Collections.sort(withNull); } catch (NullPointerException e) { System.out.println("  natural order + null -> NPE"); }
        withNull.sort(Comparator.nullsFirst(Comparator.naturalOrder()));
        System.out.println("  nullsFirst: " + withNull);

        System.out.println("-- 6. reversed() binds to the whole chain built so far");
        Comparator<Person> c1 = Comparator.comparing(Person::name).reversed().thenComparingInt(Person::age);
        Comparator<Person> c2 = Comparator.comparing(Person::name).thenComparingInt(Person::age).reversed();
        List<Person> ties = List.of(new Person("A", 1), new Person("A", 2));
        System.out.println("  name desc then age asc : " + ties.stream().sorted(c1).map(Person::age).toList());
        System.out.println("  whole chain reversed   : " + ties.stream().sorted(c2).map(Person::age).toList());

        System.out.println("-- 7. a comparator that never returns 0 for equal elements violates the contract");
        Random rnd = new Random(1);
        List<Integer> nums = new ArrayList<>();
        for (int i = 0; i < 1000; i++) nums.add(rnd.nextInt(10));            // many duplicates
        try { nums.sort((x, y) -> x < y ? -1 : 1); System.out.println("  no exception (detection is best-effort)"); }
        catch (IllegalArgumentException e) { System.out.println("  IllegalArgumentException: " + e.getMessage()); }
    }
}
```

```text
-- 1. subtraction comparator overflows
  compare(Integer.MIN_VALUE, 1) = 2147483647  (positive: says MIN_VALUE > 1)
  Integer.compare(...)          = -1
-- 2. compareTo inconsistent with equals: BigDecimal
  equals = false, compareTo = 0
  HashSet size = 2, TreeSet size = 1
-- 3. TreeSet/TreeMap use the comparator as equality
  [Java] contains("jAvA") = true
-- 4. sort is stable (List.sort / Collections.sort / Stream.sorted on objects)
  by age only keeps input order inside ties: [Amy, Cat, Zed, Bob]
  age desc, name asc: [Bob, Zed, Amy, Cat]
-- 5. nulls
  natural order + null -> NPE
  nullsFirst: [null, a, b]
-- 6. reversed() binds to the whole chain built so far
  name desc then age asc : [1, 2]
  whole chain reversed   : [2, 1]
-- 7. a comparator that never returns 0 for equal elements violates the contract
  IllegalArgumentException: Comparison method violates its general contract!
```

- `(a, b) -> a - b` **overflows**; always `Integer.compare`/`Comparator.comparingInt`.
- A `TreeSet`/`TreeMap` uses the comparator (not `equals`) for identity: case-insensitive set kept only `Java`; `BigDecimal("1.0")` and `("1.00")` collapse in a `TreeSet` but are two elements in a `HashSet` ([`compareTo` consistent with `equals`](../02-collections/02-equals-hashcode.md)).
- `List.sort`, `Collections.sort`, `Arrays.sort(Object[])` and `Stream.sorted()` are **stable** (TimSort/merge); `Arrays.sort(int[])` is not stable but that's unobservable for primitives. Multi-key sorts: chain `thenComparing`.
- `reversed()` applies to the **comparator built so far**: `comparing(name).reversed().thenComparing(age)` ≠ `comparing(name).thenComparing(age).reversed()`.
- A comparator violating its contract (here: never returning 0 for equals) can make TimSort throw `Comparison method violates its general contract!` — detection is **best-effort and size-dependent**, so the bug can lurk until the data grows.

---

## 12. Numbers: parsing, `StringBuilder`, `Math`, shifts, `BigDecimal`

```java
// Run: NumberTraps.java
public class NumberTraps {
    static void parse(String s) {
        String shown = s == null ? "null" : "\"" + s.chars().mapToObj(c -> c < 128 ? String.valueOf((char) c) : String.format("\\u%04x", c)).reduce("", String::concat) + "\"";
        try { System.out.println("  parseInt(" + shown + ") = " + Integer.parseInt(s)); }
        catch (NumberFormatException e) { System.out.println("  parseInt(" + shown + ") -> NFE: " + e.getMessage()); }
    }

    public static void main(String[] args) {
        System.out.println("-- Integer.parseInt edge cases");
        parse("+5"); parse("-0"); parse(" 5"); parse("5 "); parse(""); parse(null);
        parse("2147483647"); parse("2147483648"); parse("0x10"); parse("1_000"); parse("1e3"); parse("08");
        parse("٣٤");                                                   // Arabic-Indic digits 3 and 4
        System.out.println("  decode(\"0x10\") = " + Integer.decode("0x10") + ", decode(\"010\") = " + Integer.decode("010")
                + ", parseInt(\"ff\", 16) = " + Integer.parseInt("ff", 16) + ", parseUnsignedInt(\"4294967295\") = " + Integer.parseUnsignedInt("4294967295"));
        System.out.println("  literal 010 = " + 010 + " (octal!), Integer.valueOf(\"010\") = " + Integer.valueOf("010"));
        System.out.println("  Double.parseDouble(\" 1.5 \") = " + Double.parseDouble(" 1.5 ") + " (trims whitespace, unlike parseInt), Boolean.parseBoolean(\"yes\") = " + Boolean.parseBoolean("yes"));

        System.out.println("-- StringBuilder capacity");
        StringBuilder sb = new StringBuilder();
        System.out.println("  new StringBuilder().capacity()        = " + sb.capacity());
        sb.append("0123456789ABCDEFG");
        System.out.println("  after 17 chars                        = " + sb.capacity() + "  ((16 + 1) * 2 = 34 : old*2+2)");
        System.out.println("  new StringBuilder(\"abc\").capacity()   = " + new StringBuilder("abc").capacity() + "  (16 + length)");
        StringBuilder trap = new StringBuilder('a');                              // char -> int overload: capacity 97, content empty!
        System.out.println("  new StringBuilder('a') -> length " + trap.length() + ", capacity " + trap.capacity() + ", content \"" + trap + "\"");
        sb.setLength(0);
        System.out.println("  setLength(0) keeps capacity           = " + sb.capacity());
        sb.trimToSize();
        System.out.println("  trimToSize()                          = " + sb.capacity());
        System.out.println("  reverse / insert / deleteCharAt: " + new StringBuilder("abc").reverse().insert(0, "[").deleteCharAt(1).append(']'));

        System.out.println("-- Math: round, floorDiv, floorMod, rint");
        System.out.println("  round(2.5)=" + Math.round(2.5) + " round(-2.5)=" + Math.round(-2.5) + " round(-2.51)=" + Math.round(-2.51) + " rint(2.5)=" + Math.rint(2.5) + " rint(3.5)=" + Math.rint(3.5));
        System.out.println("  round(0.49999999999999994)=" + Math.round(0.49999999999999994) + " round(Float.NaN)=" + Math.round(Float.NaN) + " round(1e20)=" + Math.round(1e20));
        System.out.println("  -7 / 2 = " + (-7 / 2) + ", -7 % 2 = " + (-7 % 2) + ", floorDiv(-7,2) = " + Math.floorDiv(-7, 2) + ", floorMod(-7,2) = " + Math.floorMod(-7, 2));
        System.out.println("  floorMod(7,-3) = " + Math.floorMod(7, -3) + "  (sign follows the divisor), 7 % -3 = " + (7 % -3));
        System.out.println("  ceil(-0.5) = " + Math.ceil(-0.5) + ", (int) Math.ceil(7 / 2) = " + (int) Math.ceil(7 / 2) + " (int division first!), Math.ceilDiv(7,2) = " + Math.ceilDiv(7, 2));
        System.out.println("  array index bucket: (hash % n) can be negative: " + (-5 % 4) + " vs floorMod " + Math.floorMod(-5, 4));
        System.out.println("  Math.sqrt(-1) = " + Math.sqrt(-1) + ", 5 % 0.0 = " + (5 % 0.0) + ", 0.0 / 0 = " + (0.0 / 0));
        try { int z = 0; System.out.println(5 % z); } catch (ArithmeticException e) { System.out.println("  5 % 0 (int) -> " + e.getMessage()); }

        System.out.println("-- shifts");
        System.out.println("  1 << 32 = " + (1 << 32) + ", 1L << 32 = " + (1L << 32) + ", 1 << 33 = " + (1 << 33) + ", 1 << -1 = " + (1 << -1));
        System.out.println("  -16 >> 2 = " + (-16 >> 2) + ", -16 >>> 2 = " + (-16 >>> 2) + ", -16L >>> 2 = " + (-16L >>> 2));
        byte b = (byte) 0xF0;                                                     // -16
        System.out.println("  (byte) 0xF0 >>> 4 = " + (b >>> 4) + "  (promoted to int first), (b & 0xFF) >>> 4 = " + ((b & 0xFF) >>> 4));
        byte b2 = (byte) 0xF0; b2 >>>= 4;
        System.out.println("  b2 >>>= 4 then stored back in a byte = " + b2);
        int lo = Integer.MAX_VALUE - 1, hi = Integer.MAX_VALUE;
        System.out.println("  (lo + hi) / 2 = " + ((lo + hi) / 2) + ", (lo + hi) >>> 1 = " + ((lo + hi) >>> 1) + ", lo + (hi - lo) / 2 = " + (lo + (hi - lo) / 2));

        System.out.println("-- bit tricks");
        int n = 40;                                                                // 0b101000
        System.out.println("  n & (n-1) clears lowest set bit: " + Integer.toBinaryString(n) + " -> " + Integer.toBinaryString(n & (n - 1)));
        System.out.println("  n & -n isolates lowest set bit : " + (n & -n));
        System.out.println("  power of two (x>0 && (x&(x-1))==0): 64 -> " + (64 > 0 && (64 & 63) == 0) + ", 40 -> " + (40 > 0 && (40 & 39) == 0));
        System.out.println("  bitCount(255)=" + Integer.bitCount(255) + " highestOneBit(40)=" + Integer.highestOneBit(40) + " numberOfTrailingZeros(40)=" + Integer.numberOfTrailingZeros(40) + " numberOfLeadingZeros(1)=" + Integer.numberOfLeadingZeros(1));
        int x = 5, y = 9; x ^= y; y ^= x; x ^= y;
        System.out.println("  xor swap: x=" + x + " y=" + y);
        System.out.println("  set bit 3: " + (1 | (1 << 3)) + ", test bit: " + ((9 >> 3 & 1) == 1) + ", toggle: " + (9 ^ (1 << 3)) + ", clear: " + (9 & ~(1 << 3)));
        System.out.println("  Integer.toBinaryString(-1).length() = " + Integer.toBinaryString(-1).length() + ", Integer.toHexString(-1) = " + Integer.toHexString(-1));
        System.out.println("  Integer.MIN_VALUE == -Integer.MIN_VALUE : " + (Integer.MIN_VALUE == -Integer.MIN_VALUE));
        System.out.println("  Long.MAX_VALUE + 1 == Long.MIN_VALUE    : " + (Long.MAX_VALUE + 1 == Long.MIN_VALUE));
    }
}
```

```text
-- Integer.parseInt edge cases
  parseInt("+5") = 5
  parseInt("-0") = 0
  parseInt(" 5") -> NFE: For input string: " 5"
  parseInt("5 ") -> NFE: For input string: "5 "
  parseInt("") -> NFE: For input string: ""
  parseInt(null) -> NFE: Cannot parse null string
  parseInt("2147483647") = 2147483647
  parseInt("2147483648") -> NFE: For input string: "2147483648"
  parseInt("0x10") -> NFE: For input string: "0x10"
  parseInt("1_000") -> NFE: For input string: "1_000"
  parseInt("1e3") -> NFE: For input string: "1e3"
  parseInt("08") = 8
  parseInt("\u0663\u0664") = 34
  decode("0x10") = 16, decode("010") = 8, parseInt("ff", 16) = 255, parseUnsignedInt("4294967295") = -1
  literal 010 = 8 (octal!), Integer.valueOf("010") = 10
  Double.parseDouble(" 1.5 ") = 1.5 (trims whitespace, unlike parseInt), Boolean.parseBoolean("yes") = false
-- StringBuilder capacity
  new StringBuilder().capacity()        = 16
  after 17 chars                        = 34  ((16 + 1) * 2 = 34 : old*2+2)
  new StringBuilder("abc").capacity()   = 19  (16 + length)
  new StringBuilder('a') -> length 0, capacity 97, content ""
  setLength(0) keeps capacity           = 34
  trimToSize()                          = 0
  reverse / insert / deleteCharAt: [ba]
-- Math: round, floorDiv, floorMod, rint
  round(2.5)=3 round(-2.5)=-2 round(-2.51)=-3 rint(2.5)=2.0 rint(3.5)=4.0
  round(0.49999999999999994)=0 round(Float.NaN)=0 round(1e20)=9223372036854775807
  -7 / 2 = -3, -7 % 2 = -1, floorDiv(-7,2) = -4, floorMod(-7,2) = 1
  floorMod(7,-3) = -2  (sign follows the divisor), 7 % -3 = 1
  ceil(-0.5) = -0.0, (int) Math.ceil(7 / 2) = 3 (int division first!), Math.ceilDiv(7,2) = 4
  array index bucket: (hash % n) can be negative: -1 vs floorMod 3
  Math.sqrt(-1) = NaN, 5 % 0.0 = NaN, 0.0 / 0 = NaN
  5 % 0 (int) -> / by zero
-- shifts
  1 << 32 = 1, 1L << 32 = 4294967296, 1 << 33 = 2, 1 << -1 = -2147483648
  -16 >> 2 = -4, -16 >>> 2 = 1073741820, -16L >>> 2 = 4611686018427387900
  (byte) 0xF0 >>> 4 = 268435455  (promoted to int first), (b & 0xFF) >>> 4 = 15
  b2 >>>= 4 then stored back in a byte = -1
  (lo + hi) / 2 = -1, (lo + hi) >>> 1 = 2147483646, lo + (hi - lo) / 2 = 2147483646
-- bit tricks
  n & (n-1) clears lowest set bit: 101000 -> 100000
  n & -n isolates lowest set bit : 8
  power of two (x>0 && (x&(x-1))==0): 64 -> true, 40 -> false
  bitCount(255)=8 highestOneBit(40)=32 numberOfTrailingZeros(40)=3 numberOfLeadingZeros(1)=31
  xor swap: x=9 y=5
  set bit 3: 9, test bit: true, toggle: 1, clear: 1
  Integer.toBinaryString(-1).length() = 32, Integer.toHexString(-1) = ffffffff
  Integer.MIN_VALUE == -Integer.MIN_VALUE : true
  Long.MAX_VALUE + 1 == Long.MIN_VALUE    : true
```

Points worth saying aloud:

- `parseInt` accepts a leading `+`/`-`, but **no whitespace, underscores, hex prefix or exponent**; leading zeros are fine and decimal (`"08"` = 8) whereas a **source literal** `010` is **octal** (8). It also accepts **non-ASCII Unicode digits** (`٣٤` = 34) — a validation/injection footgun; validate with a regex like `[0-9]+` first if input is untrusted. `parseInt(null)` gives `NumberFormatException: Cannot parse null string`, not NPE.
- `new StringBuilder('a')` picks `StringBuilder(int capacity)` (char widens to int 97): **empty builder with capacity 97**. Growth is `(old + 1) * 2` → `old*2+2`. `setLength(0)` reuses the buffer.
- `Math.round` = `floor(x + 0.5)` (ties go toward **positive** infinity: `-2.5 → -2`), NaN → 0, saturates at `Long.MAX_VALUE`; `Math.rint` is banker's (ties to even). `%` takes the sign of the **dividend**; `floorMod` takes the sign of the **divisor** — use it for array/bucket indices (`-5 % 4 = -1`).
- `(int) Math.ceil(7 / 2)` is `3`: the integer division happens first. `Math.ceilDiv` (Java 18) does it right.
- Shift distances are **masked** (`& 31` for `int`, `& 63` for `long`): `1 << 32 == 1`, `1 << -1 == MIN_VALUE`. `>>` keeps the sign, `>>>` fills with zeros. `byte`/`short` are promoted to `int` **before** shifting, so `b >>> 4` on `(byte) 0xF0` yields `0x0FFFFFFF`; mask with `& 0xFF` first.
- Midpoint overflow (`(lo + hi) / 2` → `-1`) is the famous binary-search bug; use `lo + (hi - lo) / 2` or `(lo + hi) >>> 1`.
- Bit tricks interviewers expect: `n & (n-1)` clears the lowest set bit (so `n & (n-1) == 0` ⇒ power of two for `n > 0`), `n & -n` isolates it, `Integer.bitCount`, `numberOfTrailingZeros`, `highestOneBit`, XOR swap.

```java
// Run: BigDecimalTraps.java
import java.math.*;
import java.util.*;

public class BigDecimalTraps {
    public static void main(String[] args) {
        System.out.println("-- equals vs compareTo (scale matters)");
        BigDecimal a = new BigDecimal("2.0"), b = new BigDecimal("2.00");
        System.out.println("  equals=" + a.equals(b) + " compareTo=" + a.compareTo(b) + " hash equal=" + (a.hashCode() == b.hashCode()));
        System.out.println("  stripTrailingZeros: " + a.stripTrailingZeros().equals(b.stripTrailingZeros()));
        BigDecimal hundred = new BigDecimal("100").stripTrailingZeros();
        System.out.println("  100 stripped -> " + hundred + " (scale " + hundred.scale() + "), toPlainString -> " + hundred.toPlainString());
        System.out.println("  new BigDecimal(\"1E+2\") = " + new BigDecimal("1E+2") + ", unscaled=" + new BigDecimal("1E+2").unscaledValue() + ", scale=" + new BigDecimal("1E+2").scale());
        System.out.println("  zero: " + new BigDecimal("0.0").equals(BigDecimal.ZERO) + " / compareTo " + new BigDecimal("0.0").compareTo(BigDecimal.ZERO) + " / signum " + new BigDecimal("0.0").signum());

        System.out.println("-- constructors");
        System.out.println("  new BigDecimal(0.1)         = " + new BigDecimal(0.1));
        System.out.println("  new BigDecimal(\"0.1\")       = " + new BigDecimal("0.1"));
        System.out.println("  BigDecimal.valueOf(0.1)     = " + BigDecimal.valueOf(0.1));
        System.out.println("  BigDecimal.valueOf(2.50)    = " + BigDecimal.valueOf(2.50) + "  (double loses the trailing zero)");
        System.out.println("  BigDecimal.valueOf(5, 2)    = " + BigDecimal.valueOf(5, 2) + "  (unscaled 5, scale 2)");

        System.out.println("-- scale of results");
        BigDecimal x = new BigDecimal("1.10"), y = new BigDecimal("2.205");
        System.out.println("  add scale = max      : " + x.add(y) + " (scale " + x.add(y).scale() + ")");
        System.out.println("  multiply scale = sum : " + x.multiply(y) + " (scale " + x.multiply(y).scale() + ")");
        try { BigDecimal.ONE.divide(new BigDecimal(3)); }
        catch (ArithmeticException e) { System.out.println("  1/3 without rounding -> ArithmeticException: " + e.getMessage()); }
        System.out.println("  1/4 exact terminates : " + BigDecimal.ONE.divide(new BigDecimal(4)));
        System.out.println("  1/3 scale 4 HALF_UP  : " + BigDecimal.ONE.divide(new BigDecimal(3), 4, RoundingMode.HALF_UP));
        System.out.println("  1/3 MathContext(5)   : " + BigDecimal.ONE.divide(new BigDecimal(3), new MathContext(5)) + "  (5 significant digits)");

        System.out.println("-- rounding modes on setScale(0)");
        System.out.printf("  %-6s %6s %6s %6s %6s%n", "mode", "2.5", "1.5", "-2.5", "2.4");
        for (RoundingMode m : new RoundingMode[]{RoundingMode.UP, RoundingMode.DOWN, RoundingMode.CEILING, RoundingMode.FLOOR, RoundingMode.HALF_UP, RoundingMode.HALF_DOWN, RoundingMode.HALF_EVEN}) {
            System.out.printf("  %-9s %6s %6s %6s %6s%n", m,
                    new BigDecimal("2.5").setScale(0, m), new BigDecimal("1.5").setScale(0, m), new BigDecimal("-2.5").setScale(0, m), new BigDecimal("2.4").setScale(0, m));
        }
        try { new BigDecimal("2.5").setScale(0); } catch (ArithmeticException e) { System.out.println("  setScale(0) with no mode on 2.5 -> " + e.getMessage()); }

        System.out.println("-- money: 3 items at 0.333 each, tax 8.25%");
        BigDecimal unit = new BigDecimal("0.333"), qty = new BigDecimal("3"), tax = new BigDecimal("0.0825");
        BigDecimal net = unit.multiply(qty);
        BigDecimal gross = net.add(net.multiply(tax)).setScale(2, RoundingMode.HALF_EVEN);
        System.out.println("  net=" + net + " gross(2dp, HALF_EVEN)=" + gross);
        System.out.println("  double version: " + (0.333 * 3 * 1.0825) + "  (don't)");
        System.out.println("  Set<BigDecimal> {2.0, 2.00} sizes: HashSet=" + new HashSet<>(List.of(a, b)).size() + ", TreeSet=" + new TreeSet<>(List.of(a, b)).size());
    }
}
```

```text
-- equals vs compareTo (scale matters)
  equals=false compareTo=0 hash equal=false
  stripTrailingZeros: true
  100 stripped -> 1E+2 (scale -2), toPlainString -> 100
  new BigDecimal("1E+2") = 1E+2, unscaled=1, scale=-2
  zero: false / compareTo 0 / signum 0
-- constructors
  new BigDecimal(0.1)         = 0.1000000000000000055511151231257827021181583404541015625
  new BigDecimal("0.1")       = 0.1
  BigDecimal.valueOf(0.1)     = 0.1
  BigDecimal.valueOf(2.50)    = 2.5  (double loses the trailing zero)
  BigDecimal.valueOf(5, 2)    = 0.05  (unscaled 5, scale 2)
-- scale of results
  add scale = max      : 3.305 (scale 3)
  multiply scale = sum : 2.42550 (scale 5)
  1/3 without rounding -> ArithmeticException: Non-terminating decimal expansion; no exact representable decimal result.
  1/4 exact terminates : 0.25
  1/3 scale 4 HALF_UP  : 0.3333
  1/3 MathContext(5)   : 0.33333  (5 significant digits)
-- rounding modes on setScale(0)
  mode      2.5    1.5   -2.5    2.4
  UP             3      2     -3      3
  DOWN           2      1     -2      2
  CEILING        3      2     -2      3
  FLOOR          2      1     -3      2
  HALF_UP        3      2     -3      2
  HALF_DOWN      2      1     -2      2
  HALF_EVEN      2      2     -2      2
  setScale(0) with no mode on 2.5 -> Rounding necessary
-- money: 3 items at 0.333 each, tax 8.25%
  net=0.999 gross(2dp, HALF_EVEN)=1.08
  double version: 1.0814175000000001  (don't)
  Set<BigDecimal> {2.0, 2.00} sizes: HashSet=2, TreeSet=1
```

- **`equals` compares value *and scale*** (`2.0 ≠ 2.00`), so it breaks `HashSet`/`HashMap` keys; **`compareTo` ignores scale**. Normalise with `stripTrailingZeros()` (careful: `100` becomes `1E+2` — use `toPlainString()` for display) or compare with `compareTo(..) == 0`. `BigDecimal.ZERO.equals(new BigDecimal("0.0"))` is `false`.
- Construct from **`String`** (or `valueOf(long, scale)`); `new BigDecimal(0.1)` captures the binary error; `valueOf(double)` goes via `Double.toString`.
- Result scale: add/subtract → `max(scale)`; multiply → `sum(scale)`; divide needs a **rounding mode or `MathContext`**, else a non-terminating expansion throws `ArithmeticException`. `setScale(n)` without a mode throws `Rounding necessary` if digits would be lost.
- Rounding table (observed): `HALF_UP` is "school" rounding (2.5→3, −2.5→−3); `HALF_EVEN` is banker's rounding (2.5→2, 1.5→2) and the standard for money aggregation; `CEILING`/`FLOOR` follow the number line; `UP`/`DOWN` are away-from/toward zero. Pick one per domain rule and test negative numbers.
- Round **once, at the end** of a calculation (the tax example); rounding each step compounds error.

---

## 13. Pitfalls checklist

> [!WARNING]
> The traps that cause real incidents, in rough order of frequency:
> 1. Mutating a collection while iterating it; confusing a **view** with a **copy**.
> 2. Boxed `==`, `Integer` unboxing NPE, `remove(int)` vs `remove(Object)`.
> 3. `NoClassDefFoundError` that is really a failed **static initialiser**.
> 4. Inner/anonymous classes pinning big outer objects (and listeners never removed).
> 5. `System.exit`/`halt` skipping `finally`, or relying on shutdown hooks being ordered or running at all.
> 6. `BigDecimal.equals`, `double` money, `a - b` comparators, `(lo + hi) / 2`.
> 7. `Arrays.asList(int[])`, `Arrays.fill` with one shared row, `clone()` on nested arrays.
> 8. Relying on `Set.of`/`HashMap` iteration order or on `ordinal()`.
> 9. `Optional.orElse(expensiveCall())`, `Optional` fields/parameters.
> 10. Public `static final` constants recompiled into every client (inlined).

---

## 14. Interview Q&A

<details>
<summary><b>Q1.</b> When exactly is a class initialised, and why does it matter?</summary>

On first active use: instance creation, static method call, non-constant static field read/write, subclass initialisation (superclass first), or `Class.forName`. Not on a class literal, an array of the type, or a compile-time-constant read. It matters for startup order bugs, lazy singletons (holder idiom), `ExceptionInInitializerError`/`NoClassDefFoundError`, and for **deadlocks between two classes whose `<clinit>`s reference each other from different threads**.
</details>

<details>
<summary><b>Q2.</b> <code>System.exit</code> vs <code>Runtime.halt</code> vs returning from <code>main</code>?</summary>

`exit` runs shutdown hooks (and does not run pending `finally` blocks of other frames); `halt` skips everything; returning from `main` waits for non-daemon threads. Exit code 0 = success; uncaught exception in `main` = 1; `kill -9` runs nothing.
</details>

<details>
<summary><b>Q3.</b> Why is <code>finalize()</code> bad and what replaces it?</summary>

Unpredictable timing, may never run, resurrection risk, GC overhead, exceptions ignored, security attacks via finalizer. Deprecated for removal (Java 18, JEP 421). Use try-with-resources for deterministic release and `Cleaner` (or `PhantomReference`) as a safety net.
</details>

<details>
<summary><b>Q4.</b> Why can an inner-class instance cause a memory leak or a serialisation failure?</summary>

It holds `this$0`, a strong reference to the outer instance, so the outer can't be collected while the inner lives, and serialisation drags the outer into the stream. Fix: `static` nested class, pass only needed data, or use a lambda that captures only what it needs (and never store it in a long-lived registry without deregistration).
</details>

<details>
<summary><b>Q5.</b> Compile error or <code>ClassCastException</code>?</summary>

If the static types can *never* be related (unrelated classes, final class vs. interface it doesn't implement) → compile error. If a runtime subtype *could* satisfy it (down-casts, cast to an interface from a non-final class) → compiles, runtime check. Unchecked generic casts compile with a warning and fail later.
</details>

<details>
<summary><b>Q6.</b> What are the three overload-resolution phases?</summary>

1. Strict invocation (subtyping, primitive widening); 2. loose invocation (boxing/unboxing); 3. variable-arity. First phase with any applicable candidate wins; then most-specific; ambiguity is a compile error.
</details>

<details>
<summary><b>Q7.</b> Why is <code>Cloneable</code> considered broken?</summary>

Marker interface with no `clone()`, protected `Object.clone()`, shallow by default, skips constructors, incompatible with `final` fields holding mutable state, checked exception, and subclass contracts are fragile. Prefer copy constructors, static factories or records; arrays are the exception.
</details>

<details>
<summary><b>Q8.</b> <code>BigDecimal.equals</code> vs <code>compareTo</code>, and how do you store money?</summary>

`equals` includes scale; `compareTo` doesn't. Store money as `BigDecimal` with a fixed scale (and currency) or as integer minor units (`long cents`); round once with an explicit `RoundingMode`; column type `NUMERIC(19,4)`-style, never `double`/`float`.
</details>

<details>
<summary><b>Q9.</b> Why shouldn't you persist <code>ordinal()</code>?</summary>

It is the declaration position; reordering or inserting constants changes the meaning of stored data. Persist `name()` (renames still break) or an explicit immutable code.
</details>

<details>
<summary><b>Q10.</b> Which <code>java.util</code> sorts are stable?</summary>

`Collections.sort`, `List.sort`, `Arrays.sort(T[])`, `Stream.sorted()` on ordered streams (TimSort / merge-sort variants) are stable. `Arrays.sort` on primitives (dual-pivot quicksort) is not, but stability is not observable there.
</details>

---

## 15. Predict the output

All of these were run; each answer is the observed output.

<details>
<summary><b>P1.</b></summary>

```java
System.out.println((int) 'A' + 1 + "" + (char) ('A' + 1));
```

**`66B`** — `65 + 1 = 66` (int), then concatenated with `""` and `'B'`.
</details>

<details>
<summary><b>P2.</b></summary>

```java
long x = Integer.MAX_VALUE; x++;
System.out.println(x);
System.out.println(Integer.MAX_VALUE + 1 < Integer.MAX_VALUE);
```

**`2147483648`** then **`true`** — `x` is a `long`, no overflow; the `int` expression wraps to `MIN_VALUE`.
</details>

<details>
<summary><b>P3.</b></summary>

```java
char c = 65; c += 1.7;
System.out.println(c);
byte b = 10; b *= 30;
System.out.println(b);
```

**`B`** then **`44`** — compound assignment casts back: `(char) 66.7 = 'B'`; `300` narrowed to a byte is `44`.
</details>

<details>
<summary><b>P4.</b></summary>

```java
System.out.println("5" + 5 * 2 + 5);
System.out.println(1 / 2 * 2.0 + 1 / 2.0 * 2);
System.out.println(010 + 0x10 + 0b10);
System.out.println('a' + 'b' + "c" + 'd' + 'e');
```

**`5105`**, **`1.0`**, **`26`** (8 + 16 + 2), **`195cde`**. Integer division `1/2` is `0`, `1/2.0` is `0.5`; `'a' + 'b'` is `int` 195 before the first `String`.
</details>

<details>
<summary><b>P5.</b></summary>

```java
int[] a = {1, 2, 3}; int i = 0;
a[i] = i = 2;
System.out.println(Arrays.toString(a) + " " + i);
```

**`[2, 2, 3] 2`** — the array **index** `a[i]` (with `i == 0`) is evaluated **before** the right-hand side runs.
</details>

<details>
<summary><b>P6.</b></summary>

```java
int i = 0; i = i++ + i++;      System.out.println(i);
int j = 0; j = ++j + j++;      System.out.println(j);
```

**`1`** and **`2`** — `0 + 1`, and `1 + 1`.
</details>

<details>
<summary><b>P7.</b></summary>

```java
float f = 1.1f; double d = 1.1;
System.out.println((f == d) + " " + (f == 1.1f) + " " + ((double) f));
System.out.println(Math.min(-0.0, 0.0) + " " + (0.0 == -0.0));
System.out.println((short) 40000);
String s = null; System.out.println(s + "x");
```

**`false true 1.100000023841858`**, **`-0.0 true`**, **`-25536`**, **`nullx`**. `f` widened to `double` carries the float's rounding error; `Math.min` orders `-0.0 < 0.0` while `==` doesn't; `40000 - 65536 = -25536`; concatenating `null` appends the text `null`.
</details>

<details>
<summary><b>P8.</b></summary>

```java
StringBuilder a = new StringBuilder("a"), b = new StringBuilder("a");
System.out.println(a.equals(b) + " " + a.compareTo(b) + " " + a.toString().equals(b.toString()));
Integer i1 = 1000; int i2 = 1000; Integer i3 = 1000;
System.out.println((i1 == i2) + " " + (i1 == i3));
```

**`false 0 true`** and **`true false`**. `StringBuilder` doesn't override `equals` (but implements `Comparable` since Java 11); `Integer == int` unboxes (value compare), `Integer == Integer` compares references (1000 is outside the cache).
</details>

---
[↑ Back to Gotchas index](README.md)
