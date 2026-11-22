# Modern Java (11 → 21): Records, Sealed Types, Pattern Matching

> **Level:** SDE-II / SDE-III · **Area:** Java · **Prev:** [Lambdas, streams & Optional](07-lambdas-streams-optional.md) · **Baseline:** Java 21 (LTS)

## TL;DR

Modern Java lets you model data as **immutable records**, restrict hierarchies with **sealed types**, and take them apart with **pattern matching** in `switch` — the compiler then checks you covered every case. Together they replace most Visitor-pattern boilerplate and `instanceof`-cast chains.

| Feature | Since | One-liner |
|---|---|---|
| `var` (local inference) | 10 | `var map = new HashMap<String,Integer>();` |
| Switch expressions | 14 | `int n = switch (day) { case MON, TUE -> 1; default -> 0; };` |
| Helpful `NullPointerException` messages | 14 | tells you *which* variable/call was null |
| Text blocks | 15 | multi-line strings with `"""` |
| Records | 16 | immutable data carrier |
| Pattern matching for `instanceof` | 16 | `if (o instanceof String s)` |
| `Stream.toList()` | 16 | unmodifiable list |
| Sealed classes/interfaces | 17 | closed hierarchies |
| Pattern matching for `switch`, record patterns | 21 | deconstruct in `switch` |
| Virtual threads | 21 | cheap threads for blocking I/O |
| Sequenced collections | 21 | `getFirst()`, `getLast()`, `reversed()` |

## The analogy: a restaurant menu that can't be ordered off-menu

- A **record** is a *printed menu item*: name, price, description — fixed once printed.
- A **sealed interface** is the *menu itself*: only these dishes exist (`Starter`, `Main`, `Dessert`).
- **Pattern-matching `switch`** is the *waiter*: for every dish on the menu they know what to do, and the manager (compiler) checks that **no dish is forgotten** — add a new dish and every waiter script that doesn't handle it fails to compile.

## 1. Records

```java
public record Point(int x, int y) { }
// Generates: private final fields, canonical constructor, accessors x() / y(),
//            equals, hashCode, toString:  Point[x=1, y=2]
```

What you can do:

- **Compact constructor** for validation/normalisation (assign to parameters, no `this.x = x` needed).
- Add methods, static factories, static fields, implement interfaces, nested records.
- Override accessors / `toString` / `equals`.

What you can't: extend another class (implicitly extend `java.lang.Record`), declare extra instance fields, be extended (implicitly `final`).

```java
// Run: RecordDemo.java
import java.util.*;

public class RecordDemo {
    record Range(int lo, int hi) {
        Range {                                            // compact canonical constructor
            if (lo > hi) throw new IllegalArgumentException("lo > hi: " + lo + " > " + hi);
        }
        int length() { return hi - lo; }
        static Range of(int lo, int hi) { return new Range(lo, hi); }
    }

    // Shallow immutability trap: a record holding a mutable List
    record LeakyTeam(List<String> members) { }
    record SafeTeam(List<String> members) {
        SafeTeam { members = List.copyOf(members); }       // defensive copy -> truly immutable
    }

    public static void main(String[] args) {
        var r = Range.of(2, 7);
        System.out.println(r + " length=" + r.length());           // Range[lo=2, hi=7] length=5
        System.out.println(r.equals(new Range(2, 7)));              // true
        try { new Range(5, 1); } catch (IllegalArgumentException e) { System.out.println(e.getMessage()); }

        List<String> src = new ArrayList<>(List.of("a"));
        LeakyTeam leaky = new LeakyTeam(src);
        SafeTeam safe = new SafeTeam(src);
        src.add("b");
        System.out.println(leaky.members() + " vs " + safe.members());   // [a, b] vs [a]
    }
}
```

```text
Range[lo=2, hi=7] length=5
true
lo > hi: 5 > 1
[a, b] vs [a]
```

> [!WARNING]
> Records are **shallowly** immutable: the *references* are final, the objects they point to may not be. Copy mutable components (`List.copyOf`, `.clone()`) in the compact constructor. Records are great as DTOs, map keys, tuples, and value objects — **not** as JPA entities (need no-arg constructor/mutability) — though they work as Spring/Jackson DTOs and in projections.

## 2. Sealed types + pattern-matching `switch`

```java
// Run: ShapeDemo.java
public class ShapeDemo {
    sealed interface Shape permits Circle, Rect, Tri { }
    record Circle(double r) implements Shape { }
    record Rect(double w, double h) implements Shape { }
    record Tri(double base, double height) implements Shape { }

    // No default branch: the compiler proves all permitted subtypes are covered.
    static double area(Shape s) {
        return switch (s) {
            case Circle c                      -> Math.PI * c.r() * c.r();
            case Rect(double w, double h)      -> w * h;                       // record pattern: deconstruct
            case Tri(double b, double h)       -> 0.5 * b * h;
        };
    }

    // Guards with `when`, plus null handling in the switch itself
    static String describe(Object o) {
        return switch (o) {
            case null                          -> "null!";
            case Integer i when i > 100        -> "big int " + i;
            case Integer i                     -> "int " + i;
            case String str when str.isBlank() -> "blank string";
            case String str                    -> "string of length " + str.length();
            case Circle(double r)              -> "circle r=" + r;
            default                            -> "something else: " + o;
        };
    }

    public static void main(String[] args) {
        System.out.printf("%.2f %.1f %.1f%n", area(new Circle(1)), area(new Rect(2, 3)), area(new Tri(4, 5)));
        for (Object o : new Object[] { null, 7, 500, " ", "hey", new Circle(2), 3.5 })
            System.out.println(describe(o));
    }
}
```

```text
3.14 6.0 10.0
null!
int 7
big int 500
blank string
string of length 3
circle r=2.0
something else: 3.5
```

Why this beats the old way:

| Old (Visitor / `instanceof` chain) | New (sealed + switch patterns) |
|---|---|
| Add a subtype → silently falls through to a default/`else` | Add a subtype → **every non-exhaustive `switch` fails to compile** |
| `if (s instanceof Circle) { Circle c = (Circle) s; … }` | `case Circle c ->` (binding is already typed) |
| Visitor needs `accept` methods in every class | Data and behaviour stay separate (functional style) |

Rules: `permits` subclasses must be in the same module/package and each must be `final`, `sealed` or `non-sealed`. Dominance: a more general `case` before a specific one is a compile error. Order matters; `when` guards are tested top to bottom.

### Pattern matching for `instanceof` (Java 16)

```java
if (obj instanceof String s && s.length() > 3) {   // s is in scope only where the match is certain
    System.out.println(s.toUpperCase());
}
// Typical use in equals():
@Override public boolean equals(Object o) { return o instanceof Point p && p.x == x && p.y == y; }
```

## 3. Smaller but frequent additions

```java
// Run: SmallFeatures.java
import java.util.*;
import java.util.stream.*;

public class SmallFeatures {
    enum Day { MON, TUE, SAT, SUN }

    public static void main(String[] args) throws Exception {
        // var: local variable type inference (still statically typed!)
        var list = new ArrayList<Map<String, Integer>>();
        list.add(Map.of("a", 1));
        System.out.println(list);

        // switch expression: arrow form, no fall-through, exhaustive for enums, can yield a value
        Day d = Day.SAT;
        String kind = switch (d) {
            case SAT, SUN -> "weekend";
            case MON, TUE -> {
                String tmp = "week";
                yield tmp + "day";                         // yield returns from a block branch
            }
        };
        System.out.println(kind);

        // Sequenced collections (Java 21)
        List<Integer> nums = new ArrayList<>(List.of(1, 2, 3));
        System.out.println(nums.getFirst() + " " + nums.getLast() + " " + nums.reversed());   // 1 3 [3, 2, 1]
        nums.addFirst(0);
        LinkedHashMap<String, Integer> lhm = new LinkedHashMap<>();
        lhm.put("x", 1); lhm.put("y", 2);
        System.out.println(nums + " " + lhm.firstEntry() + " " + lhm.lastEntry());

        // Virtual threads (Java 21): cheap, one per task, block freely
        Thread vt = Thread.ofVirtual().name("vt-1").start(() ->
            System.out.println("virtual? " + Thread.currentThread().isVirtual()));
        vt.join();

        // Pre-sized map (Java 19)
        Map<String, Integer> m = HashMap.newHashMap(100);
        m.put("k", 1);
        System.out.println(m);
    }
}
```

```text
[{a=1}]
weekend
1 3 [3, 2, 1]
[0, 1, 2, 3] x=1 y=2
virtual? true
{k=1}
```

**Helpful NPE messages (Java 14+, on by default since 15):** instead of a bare `NullPointerException`, you get e.g. `Cannot invoke "String.length()" because "user.name" is null` (local variable names show only if compiled with `-g`; otherwise `"<local1>"`).

**Virtual threads (Project Loom)** — covered properly in the concurrency section: millions of cheap, JVM-scheduled threads for blocking-style code; don't pool them; avoid `synchronized` pinning around blocking calls (Java 21), prefer `ReentrantLock`.

**What came after 21** (know the names): unnamed variables/patterns `_` (22), stream gatherers (24), scoped values and structured concurrency (preview), string templates (withdrawn/redesigned). Java 25 is the next LTS after 21.

## 4. Interview Q&A

<details>
<summary><b>Q1.</b> What is a record, and what does the compiler generate?</summary>

A concise, shallowly immutable data class. The compiler generates private final fields, a canonical constructor, accessor methods named after the components, and `equals`/`hashCode`/`toString` based on all components. Records are implicitly final and extend `java.lang.Record`.
</details>

<details>
<summary><b>Q2.</b> How do you validate or normalise record fields?</summary>

A **compact canonical constructor**: `Range { if (lo > hi) throw …; }` — parameters can be reassigned (e.g. defensive copy) and are then assigned to the fields automatically.
</details>

<details>
<summary><b>Q3.</b> What problem do sealed classes solve?</summary>

They restrict which classes may extend a type, so the set of subtypes is known and closed. The compiler can then check `switch` exhaustiveness, enabling algebraic-data-type modelling without a `default` that hides missing cases.
</details>

<details>
<summary><b>Q4.</b> <code>var</code> — is Java now dynamically typed?</summary>

No. `var` only infers the *compile-time* type from the initialiser; it's local-only (not fields/parameters/returns), can't be `null`-initialised, and the type is still fixed. Use it when the type is obvious from the right-hand side.
</details>

<details>
<summary><b>Q5.</b> Switch expression vs statement?</summary>

Expressions produce a value, use `->` (no fall-through) or `yield`, and must be exhaustive. Statements with `:` labels fall through unless you `break`.
</details>

<details>
<summary><b>Q6.</b> Are records good JPA entities?</summary>

No — entities need a no-arg constructor, mutable state for dirty checking and proxying, and non-final classes. Use records for DTOs, projections, value objects and map keys.
</details>

<details>
<summary><b>Q7.</b> What are virtual threads and when would you not use them?</summary>

User-mode threads scheduled by the JVM on a small pool of carrier threads, ideal for large numbers of blocking I/O tasks. Not helpful for CPU-bound work (no more cores), and be careful with pinning (`synchronized` + blocking in Java 21) and heavy `ThreadLocal` use.
</details>

## 5. Predict the output / compile

<details>
<summary><b>P1.</b> Does this compile? What does it print?</summary>

```java
record P(int x) { P { x = Math.abs(x); } }
System.out.println(new P(-5));
```

Compiles; prints **`P[x=5]`** — the compact constructor reassigns the *parameter*, which then initialises the field.
</details>

<details>
<summary><b>P2.</b> Does this compile?</summary>

```java
sealed interface S permits A, B {}
record A() implements S {}
record B() implements S {}
static int f(S s) { return switch (s) { case A a -> 1; }; }
```

**No** — the `switch` is not exhaustive (`B` missing). Add `case B b -> 2` (no `default` needed).
</details>

<details>
<summary><b>P3.</b> Does this compile?</summary>

```java
Object o = 5;
String r = switch (o) {
    case Number n -> "number";
    case Integer i -> "integer";
    default -> "other";
};
```

**No** — `case Integer i` is *dominated* by the earlier, more general `case Number n` (unreachable). Put the specific case first.
</details>

---
[↑ Back to Java Basics index](README.md)
