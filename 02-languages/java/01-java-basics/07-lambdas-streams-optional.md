# Lambdas, Streams & `Optional`

> **Level:** SDE-II / SDE-III · **Area:** Java · **Prev:** [Generics](06-generics.md) · **Next:** [Modern Java](08-modern-java.md)

## TL;DR

- A **lambda** is a short implementation of a **functional interface** (one abstract method). Captured locals must be **effectively final**.
- A **stream** is a *pipeline description*: **intermediate** operations (`filter`, `map`…) are **lazy**; nothing runs until a **terminal** operation (`collect`, `count`, `forEach`…). A stream can be consumed **once**.
- Streams are great for transformation/aggregation; keep lambdas **pure** (no shared mutable state) — especially with `parallel()`.
- **`Optional`** models "maybe a value" for **return types**; not for fields, parameters or collections.

## The analogy: a factory conveyor belt

A stream is a **conveyor belt with stations** (filter, convert, pack). Setting up the stations does **nothing**; only pressing the **"start" button (terminal operation)** moves items along. Items travel through *all* stations one at a time (not station-by-station), and if the last station says *"I only need the first item"* the belt stops early (**short-circuit**). Once the belt has run, it's empty — you can't run the same belt twice.

## 1. Functional interfaces

| Interface | Shape | Example |
|---|---|---|
| `Function<T,R>` | `T → R` | `s -> s.length()` |
| `BiFunction<T,U,R>` | `(T,U) → R` | `(a, b) -> a + b` |
| `UnaryOperator<T>` / `BinaryOperator<T>` | `T → T` / `(T,T) → T` | `String::trim`, `Integer::sum` |
| `Predicate<T>` | `T → boolean` | `s -> s.isEmpty()` |
| `Supplier<T>` | `() → T` | `ArrayList::new` |
| `Consumer<T>` | `T → void` | `System.out::println` |
| `Runnable` / `Callable<V>` | `() → void` / `() → V` (throws) | tasks |
| `Comparator<T>` | `(T,T) → int` | `Comparator.comparing(Person::name)` |
| Primitive variants | `IntFunction`, `ToIntFunction`, `IntPredicate`… | avoid boxing |

**Method references** (4 kinds): static `Integer::parseInt` · bound instance `System.out::println` · unbound instance `String::length` (first arg is the receiver) · constructor `ArrayList::new`.

### Lambda vs anonymous class

| | Lambda | Anonymous class |
|---|---|---|
| `this` | the **enclosing** instance | the anonymous object itself |
| Compiled to | `invokedynamic` + synthetic method (no extra `.class` file) | separate `Outer$1.class` |
| Can implement | functional interfaces only | any interface/abstract class |
| Captures | effectively-final locals, `this` | same, plus can hold own state |

**Why effectively final?** Captured locals are *copied* into the lambda; a mutable shared local would give two threads two different "truths". Use an `AtomicInteger`/array holder, or better, restructure with `reduce`.

## 2. Stream pipelines: lazy, one element at a time

```java
// Run: StreamLaziness.java
import java.util.*;
import java.util.stream.*;

public class StreamLaziness {
    public static void main(String[] args) {
        List<String> names = List.of("alice", "bob", "carol", "dave");

        // 1. No terminal operation -> nothing executes
        names.stream().peek(n -> System.out.println("never printed: " + n)).map(String::length);

        // 2. Elements flow vertically through the whole pipeline; findFirst short-circuits
        Optional<String> r = names.stream()
            .peek(n -> System.out.println("filter sees " + n))
            .filter(n -> n.length() > 3)
            .peek(n -> System.out.println("map sees    " + n))
            .map(String::toUpperCase)
            .findFirst();
        System.out.println("result = " + r.get());

        // 3. A stream is single-use
        Stream<String> s = names.stream();
        s.count();
        try { s.count(); }
        catch (IllegalStateException e) { System.out.println("ISE: " + e.getMessage()); }

        // 4. Stream.toList() is unmodifiable; Collectors.toList() gives an ArrayList (not guaranteed, but mutable in practice)
        try { names.stream().toList().add("x"); }
        catch (UnsupportedOperationException e) { System.out.println("toList() is unmodifiable"); }

        // 5. Infinite streams need a limit / short-circuit
        System.out.println(Stream.iterate(1, x -> x * 2).limit(6).toList());   // [1, 2, 4, 8, 16, 32]
    }
}
```

```text
filter sees alice
map sees    alice
result = ALICE
ISE: stream has already been operated upon or closed
toList() is unmodifiable
[1, 2, 4, 8, 16, 32]
```

Only **`alice`** was ever examined — `bob`, `carol`, `dave` never entered the pipeline.

**Stateless vs stateful intermediate ops:** `filter/map/flatMap/peek` are stateless; `sorted/distinct/limit/skip` are stateful (`sorted` is a *barrier*: it must see everything before emitting).

## 3. Collectors you should know cold

```java
// Run: CollectorsDemo.java
import java.util.*;
import java.util.function.BinaryOperator;
import java.util.stream.*;

public class CollectorsDemo {
    record Emp(String name, String dept, int salary) {}

    public static void main(String[] args) {
        List<Emp> emps = List.of(
            new Emp("Asha", "ENG", 120), new Emp("Ben", "ENG", 100),
            new Emp("Cy", "OPS", 80),    new Emp("Di", "OPS", 90), new Emp("Eli", "HR", 70));

        // group + count (TreeMap for stable order)
        Map<String, Long> countByDept =
            emps.stream().collect(Collectors.groupingBy(Emp::dept, TreeMap::new, Collectors.counting()));
        System.out.println(countByDept);                                    // {ENG=2, HR=1, OPS=2}

        // group + average
        Map<String, Double> avgByDept =
            emps.stream().collect(Collectors.groupingBy(Emp::dept, TreeMap::new, Collectors.averagingInt(Emp::salary)));
        System.out.println(avgByDept);                                      // {ENG=110.0, HR=70.0, OPS=85.0}

        // group + map names
        Map<String, String> namesByDept = emps.stream().collect(
            Collectors.groupingBy(Emp::dept, TreeMap::new, Collectors.mapping(Emp::name, Collectors.joining("/"))));
        System.out.println(namesByDept);                                    // {ENG=Asha/Ben, HR=Eli, OPS=Cy/Di}

        // top earner per department (toMap with a merge function)
        Map<String, Emp> topByDept = emps.stream().collect(Collectors.toMap(
            Emp::dept, e -> e, BinaryOperator.maxBy(Comparator.comparingInt(Emp::salary)), TreeMap::new));
        System.out.println(topByDept.values().stream().map(Emp::name).toList());   // [Asha, Eli, Di]

        // partition in two
        Map<Boolean, List<String>> byPay = emps.stream().collect(Collectors.partitioningBy(
            e -> e.salary() >= 90, Collectors.mapping(Emp::name, Collectors.toList())));
        System.out.println(byPay);                                          // {false=[Cy, Eli], true=[Asha, Ben, Di]}

        // toMap without a merge function throws on duplicate keys!
        try { emps.stream().collect(Collectors.toMap(Emp::dept, Emp::name)); }
        catch (IllegalStateException e) { System.out.println("ISE: " + e.getMessage()); }

        // flatMap, distinct, sorted, reduce
        List<List<Integer>> nested = List.of(List.of(3, 1), List.of(2, 3), List.of());
        System.out.println(nested.stream().flatMap(List::stream).distinct().sorted().toList());       // [1, 2, 3]
        System.out.println(emps.stream().mapToInt(Emp::salary).sum());                                // 460
        System.out.println(emps.stream().map(Emp::salary).reduce(0, Integer::sum));                   // 460

        // multi-key sort: dept asc, salary desc
        System.out.println(emps.stream()
            .sorted(Comparator.comparing(Emp::dept).thenComparing(Emp::salary, Comparator.reverseOrder()))
            .map(Emp::name).toList());                                                                // [Asha, Ben, Eli, Di, Cy]
    }
}
```

Use primitive streams (`mapToInt`, `IntStream.range`, `summaryStatistics()`) to avoid boxing.

## 4. Parallel streams — when *not* to use them

```java
list.parallelStream().map(...).collect(...)   // splits work across the common ForkJoinPool
```

Use only if **all** hold: large data set (≈ >10⁴ elements) · CPU-bound, **non-blocking** per-element work · easily splittable source (`ArrayList`, arrays, `IntStream.range`; **not** `LinkedList`, `Stream.iterate`) · **stateless, side-effect-free, associative** operations.

Pitfalls:

- **Shared mutable state** → data races: `parallelStream().forEach(list::add)` into an `ArrayList` loses elements or throws.
- **Blocking I/O** inside a task starves the *shared* common pool used by everything else in the JVM.
- `forEach` is unordered under parallel; use `forEachOrdered` (kills parallelism benefits) if order matters.
- `reduce` needs an **associative** op and a proper identity; `collect` with a proper combiner.
- Overhead often outweighs gains for small/cheap work. **Measure with JMH.**

## 5. `Optional`

```java
// Run: OptionalDemo.java
import java.util.*;

public class OptionalDemo {
    static String expensive() { System.out.println("  expensive() called"); return "fallback"; }

    public static void main(String[] args) {
        Optional<String> present = Optional.of("value");

        System.out.println("orElse:");     present.orElse(expensive());          // argument evaluated EAGERLY even though unused
        System.out.println("orElseGet:");  present.orElseGet(OptionalDemo::expensive);   // lazy: not called

        Optional<String> empty = Optional.empty();
        System.out.println(empty.map(String::toUpperCase).orElse("none"));               // none
        System.out.println(present.filter(s -> s.startsWith("v")).isPresent());          // true
        System.out.println(Optional.ofNullable((String) null).or(() -> Optional.of("alt")).get());  // alt (Java 9)

        try { empty.orElseThrow(() -> new NoSuchElementException("no value")); }
        catch (NoSuchElementException e) { System.out.println(e.getMessage()); }
    }
}
```

```text
orElse:
  expensive() called
orElseGet:
none
true
alt
no value
```

**Do / don't**

| Do | Don't |
|---|---|
| Return `Optional<T>` from methods that may have no result | Use as a **field**, a method **parameter**, or in a **collection/DTO** (not `Serializable`, adds allocation) |
| Chain `map` / `flatMap` / `filter` / `orElseGet` / `orElseThrow` | Call `get()` without checking (use `orElseThrow()` Java 10+) |
| `Optional.ofNullable(x)` when `x` may be null | `Optional.of(null)` → NPE |
| Return an **empty collection**, not `Optional<List<T>>` | `if (opt.isPresent()) return opt.get(); else …` — use `map/orElse` |
| Use primitive variants `OptionalInt` etc. when relevant | Return `null` from a method that returns `Optional` |

## 6. Interview Q&A

<details>
<summary><b>Q1.</b> What is a functional interface? Is <code>@FunctionalInterface</code> required?</summary>

An interface with exactly one abstract method (it can have default/static methods and re-declare `Object` methods like `equals`). The annotation is optional but makes the compiler enforce the rule.
</details>

<details>
<summary><b>Q2.</b> Why must local variables used in a lambda be effectively final?</summary>

They're captured by value (copied). Allowing mutation would make the copy and original diverge and create thread-safety hazards, since the lambda may outlive the stack frame or run on another thread.
</details>

<details>
<summary><b>Q3.</b> Intermediate vs terminal operations; what does "lazy" mean?</summary>

Intermediate ops return a stream and only describe work; terminal ops (`collect`, `forEach`, `reduce`, `count`, `findFirst`, `anyMatch`) trigger it. Laziness enables fusing stages into a single pass and short-circuiting (`limit`, `findFirst`, `anyMatch`).
</details>

<details>
<summary><b>Q4.</b> <code>map</code> vs <code>flatMap</code>?</summary>

`map` is 1→1 (each element becomes one value); `flatMap` is 1→many (each element becomes a stream, which is then flattened). e.g. lists of words per line → one stream of words.
</details>

<details>
<summary><b>Q5.</b> When would you not use a stream?</summary>

Simple loops with early exit/complex control flow, checked exceptions, mutating several variables, or performance-critical hot paths on primitives where an indexed loop is clearer. Debugging stack traces are also harder.
</details>

<details>
<summary><b>Q6.</b> Why does <code>Collectors.toMap</code> throw, and how do you fix it?</summary>

Duplicate keys → `IllegalStateException: Duplicate key`. Supply a merge function `(a,b) -> a` or use `groupingBy`. Also, `toMap` rejects `null` *values*.
</details>

<details>
<summary><b>Q7.</b> <code>orElse</code> vs <code>orElseGet</code>?</summary>

`orElse(x)` evaluates `x` always (even if the Optional has a value); `orElseGet(supplier)` only calls the supplier when empty. Use `orElseGet` for anything costly or with side effects.
</details>

<details>
<summary><b>Q8.</b> When is a parallel stream slower than sequential?</summary>

Small data, cheap per-element work, poor splitting (`LinkedList`, `iterate`), boxing-heavy ops, contention on shared state, blocking calls on the common pool, or a busy machine/container with few cores.
</details>

## 7. Predict the output

<details>
<summary><b>P1.</b></summary>

```java
Stream<Integer> s = Stream.of(1, 2, 3);
s.map(x -> x * 2);
s.forEach(System.out::println);
```

**`IllegalStateException: stream has already been operated upon or closed`** — calling `map` already "used up" `s` (it returned a new stream; the result was discarded, and nothing printed).
</details>

<details>
<summary><b>P2.</b></summary>

```java
List<Integer> r = Stream.of(5, 3, 8, 1).sorted().limit(2).toList();
System.out.println(r);
```

**`[1, 3]`**
</details>

<details>
<summary><b>P3.</b></summary>

```java
int[] counter = {0};
List.of(1, 2, 3).forEach(x -> counter[0] += x);
System.out.println(counter[0]);
```

**`6`** — legal (array reference is effectively final, contents mutable), but prefer `sum()`; this breaks under parallel streams.
</details>

<details>
<summary><b>P4.</b></summary>

```java
System.out.println(Stream.of("a", "bb", "ccc").collect(Collectors.toMap(String::length, s -> s)).get(2));
```

**`bb`**.
</details>

---
[↑ Back to Java Basics index](README.md)
