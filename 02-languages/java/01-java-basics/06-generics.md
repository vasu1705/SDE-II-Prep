# Generics: Type Erasure, Wildcards & PECS

> **Level:** SDE-II / SDE-III · **Area:** Java · **Prev:** [Exceptions](05-exceptions.md) · **Next:** [Lambdas, streams & Optional](07-lambdas-streams-optional.md)

## TL;DR

- Generics give **compile-time type safety** and remove casts. They are implemented by **type erasure**: the compiler checks, then erases `T` to its bound (usually `Object`) and inserts casts. At run time a `List<String>` is just a `List`.
- Consequences: no `new T()`, no `new T[n]`, no `instanceof List<String>`, no primitives as type arguments, **no overloads that differ only by type argument**.
- Generics are **invariant** (`List<Integer>` is *not* a `List<Number>`); arrays are **covariant** (and unsafe).
- **PECS:** *Producer `extends`, Consumer `super`.*

## The analogy: labelled moving boxes

Writing **"Books"** on a box helps *the movers (compiler)* stop you from putting a kettle in it. Once the truck leaves (runtime), the label is **peeled off** — the box is just a box. If someone smuggled a kettle in through a side door (raw types), you only find out when you open it and grab a "book" (`ClassCastException`).

## 1. Basics

```java
class Box<T> {                          // generic class
    private T value;
    void set(T v) { value = v; }
    T get() { return value; }
}

static <T extends Comparable<T>> T max(T a, T b) {   // generic method with a bound
    return a.compareTo(b) >= 0 ? a : b;
}

Box<String> b = new Box<>();            // diamond: inferred type argument
String s = b.get();                     // no cast needed
```

- A bound `T extends A & B` allows multiple interface bounds (class first).
- **Raw types** (`List` without `<>`) disable checking — only exist for legacy compatibility. Never use them.

## 1.5 The diamond operator `<>`

The diamond tells the compiler: *"infer the type arguments for me."* It saves you from repeating the type on the right side.

```java
List<String> names = new ArrayList<>();        // Java 7+: String inferred from the LEFT side
printAll(new ArrayList<>());                    // Java 8+: inferred from the PARAMETER type List<String>
Comparator<String> c = new Comparator<>() {     // Java 9+: diamond also works with anonymous classes
    public int compare(String a, String b) { return Integer.compare(a.length(), b.length()); }
};
```

Verified on JDK 21 (`printAll` receives an empty list; the comparator returns `1` for `"aa"` vs `"b"`).

| Situation | What the compiler infers | Result |
|---|---|---|
| `List<String> x = new ArrayList<>()` | from the declared type | `ArrayList<String>` |
| `printAll(new ArrayList<>())` | from the method parameter | `ArrayList<String>` |
| `var x = new ArrayList<>()` | **nothing to infer from** | `ArrayList<Object>` ⚠️ |
| `var x = new ArrayList<String>()` | explicit | `ArrayList<String>` ✅ |

> [!WARNING]
> `var` plus a diamond is the trap: `var list = new ArrayList<>(); list.add(42);` compiles and silently makes a list of `Object`. Write the type argument when you use `var` with a constructor.

**Limits to know**

- Diamond only infers; **erasure still happens**. `new ArrayList<>()` at runtime is just an `ArrayList`.
- You cannot use primitives: `new ArrayList<int>()` is a compile error (use `Integer`).
- The "type token" trick (`new TypeRef<List<String>>() {}`) needs the type to be *visible in the source*. A diamond can keep it only when the target type supplies it: `TypeRef<Map<String, List<Integer>>> t = new TypeRef<>() {};` works (verified), but `var t = new TypeRef<>() {};` infers `Object` and the runtime type information is lost.
- Diamond with an anonymous class needs Java 9+.

### Interview Q&A — diamond

<details>
<summary><b>Q1.</b> What does <code>&lt;&gt;</code> do?</summary>

It asks the compiler to infer the generic type arguments from the context: the declared variable type, the method parameter, or the return type. It doesn't change runtime behaviour.
</details>

<details>
<summary><b>Q2.</b> What is <code>var x = new HashMap&lt;&gt;()</code> and why is it a problem?</summary>

With `var` there is no declared type to infer from, so the map becomes `HashMap<Object, Object>`. Put the types in explicitly: `var x = new HashMap<String, Integer>()`.
</details>

---

## 2. Type erasure — what the JVM actually sees

```java
// Run: ErasureDemo.java
import java.lang.reflect.*;
import java.util.*;

public class ErasureDemo {
    // Anonymous-subclass trick: the generic superclass IS retained in class metadata.
    static abstract class TypeRef<T> {
        final Type type = ((ParameterizedType) getClass().getGenericSuperclass()).getActualTypeArguments()[0];
    }

    static class Name implements Comparable<Name> {
        final String v; Name(String v) { this.v = v; }
        @Override public int compareTo(Name o) { return v.compareTo(o.v); }
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    public static void main(String[] args) {
        // 1. Same runtime class
        List<String> strings = new ArrayList<>();
        List<Integer> ints = new ArrayList<>();
        System.out.println("same class? " + (strings.getClass() == ints.getClass()));       // true

        // 2. Heap pollution via a raw type: the compiler is silenced, failure is delayed
        List raw = strings;
        raw.add(42);                                    // compiles with a warning; erased add(Object)
        try {
            String s = strings.get(0);                  // compiler-inserted cast (String) -> CCE here
        } catch (ClassCastException e) {
            System.out.println("ClassCastException at the READ site, not where 42 was added");
        }

        // 3. Arrays are covariant and reified -> runtime check; generics are invariant -> compile check
        Object[] objs = new String[1];
        try { objs[0] = 1; }                            // compiles!
        catch (ArrayStoreException e) { System.out.println("ArrayStoreException: " + e.getMessage()); }
        // List<Object> lo = new ArrayList<String>();   // does not compile: invariance

        // 4. instanceof with generics: only the unbounded wildcard is allowed
        Object o = strings;
        System.out.println("instanceof List<?> : " + (o instanceof List<?>));
        // o instanceof List<String>                    // compile error: cannot check at runtime

        // 5. Bridge methods: how erasure keeps overriding working
        for (Method m : Name.class.getDeclaredMethods())
            if (m.getName().equals("compareTo"))
                System.out.println(m.getName() + "(" + m.getParameterTypes()[0].getSimpleName() + ") bridge=" + m.isBridge());

        // 6. Retrieving a generic type at runtime using a TypeRef (what Gson/Jackson/Spring do)
        System.out.println(new TypeRef<Map<String, List<Integer>>>() {}.type);
    }
}
```

Output (the two `compareTo` lines may print in either order):

```text
same class? true
ClassCastException at the READ site, not where 42 was added
ArrayStoreException: java.lang.Integer
instanceof List<?> : true
compareTo(Name) bridge=false
compareTo(Object) bridge=true
java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>
```

> [!NOTE]
> The `instanceof` rule: you can't test `instanceof List<String>`, but `instanceof List<?>` is fine (and so is `instanceof List`). Reifiable types are those whose full type is available at runtime: primitives, non-generic classes, raw types, and types with unbounded wildcards.

### What erasure forbids (and the workaround)

| Not allowed | Why | Workaround |
|---|---|---|
| `new T()` | `T` is `Object` at run time | pass a `Supplier<T>` or `Class<T>` |
| `new T[10]` | arrays need the real element type | `(T[]) new Object[10]` (unchecked), `List<T>`, or `Array.newInstance(cls, n)` |
| `T.class`, `x instanceof T` | no runtime `T` | pass a `Class<T>` (a *type token*) |
| `static T field` | one static per class, not per `T` | – |
| `new List<String>[3]` | generic arrays are unsafe | `List<List<String>>` |
| `catch (T e)` / `class X<T> extends Exception` | exceptions can't be generic | – |
| `List<int>` | type args must be reference types | `List<Integer>`, `IntStream`, primitive collections |
| `void f(List<String>)` + `void f(List<Integer>)` | same erasure → name clash | rename |

## 3. Invariance & wildcards — PECS

`Integer` is a `Number`, but **`List<Integer>` is not a `List<Number>`**. If it were, you could add a `Double` to a list of `Integer`s through the `Number` view.

Wildcards express variance at *use sites*:

| Syntax | Reads as | Can read as | Can write |
|---|---|---|---|
| `List<? extends Number>` | "a list of some subtype of Number" | `Number` | **nothing** (except `null`) |
| `List<? super Integer>` | "a list of some supertype of Integer" | `Object` only | `Integer` (and subtypes) |
| `List<?>` | "list of unknown" | `Object` | nothing (except `null`) |

**PECS — Producer Extends, Consumer Super:** if the collection *produces* values you read → `? extends T`; if it *consumes* values you write → `? super T`.

```java
// Run: PecsDemo.java
import java.util.*;

public class PecsDemo {
    // src PRODUCES numbers for us -> extends
    static double sum(Collection<? extends Number> src) {
        double total = 0;
        for (Number n : src) total += n.doubleValue();
        return total;
    }

    // dst CONSUMES integers from us -> super
    static void fillWithInts(Collection<? super Integer> dst) {
        for (int i = 1; i <= 3; i++) dst.add(i);
    }

    // The canonical signature (java.util.Collections.copy): read from src (extends), write to dst (super)
    static <T> void copy(List<? super T> dst, List<? extends T> src) {
        for (T t : src) dst.add(t);
    }

    // Comparable<? super T>: a type may compare via a SUPERCLASS's compareTo (e.g. java.sql.Timestamp vs Date)
    static <T extends Comparable<? super T>> T max(Collection<? extends T> c) {
        Iterator<? extends T> it = c.iterator();
        T best = it.next();
        while (it.hasNext()) { T x = it.next(); if (x.compareTo(best) > 0) best = x; }
        return best;
    }

    public static void main(String[] args) {
        System.out.println(sum(List.of(1, 2, 3)));                    // 6.0   (List<Integer> is accepted)
        System.out.println(sum(List.of(1.5, 2.5)));                   // 4.0   (List<Double> too)

        List<Number> numbers = new ArrayList<>();
        List<Object> objects = new ArrayList<>();
        fillWithInts(numbers);                                        // List<Number> accepted
        fillWithInts(objects);                                        // List<Object> accepted
        System.out.println(numbers + " " + objects);                  // [1, 2, 3] [1, 2, 3]

        List<Object> out = new ArrayList<>();
        copy(out, List.of("a", "b"));
        System.out.println(out);                                      // [a, b]

        System.out.println(max(List.of(3, 9, 4)));                    // 9
    }
}
```

```text
6.0
4.0
[1, 2, 3] [1, 2, 3]
[a, b]
9
```

Mnemonic: *"`extends` = read-only box of Ts-or-subtypes, `super` = write-only box accepting Ts."* If you both read and write, use plain `T`. If you neither care about the type, use `?`.

## 4. Advanced notes

- **Bridge methods:** when a class overrides a generic method with a concrete type (`compareTo(Name)`), the compiler adds a synthetic `compareTo(Object)` that casts and delegates, so overriding still works after erasure (shown above).
- **Heap pollution & `@SafeVarargs`:** a generic varargs `T...` creates a `T[]` (erased `Object[]`) — unsafe; `@SafeVarargs` on `static`/`final`/`private` methods asserts you don't expose or write to the array (`List.of`, `Arrays.asList` do).
- **Recursive bound:** `<T extends Comparable<T>>` / `Enum<E extends Enum<E>>` — "T is comparable to itself".
- **Generic method type inference:** `Collections.<String>emptyList()` is rarely needed; target typing infers it.
- **Why erasure?** Backward compatibility with pre-5 code and no JVM change. Project Valhalla is working toward specialised generics over value types.
- **Super type tokens** (`TypeRef`, Jackson `TypeReference`, Spring `ParameterizedTypeReference`) use the one place where generics survive: the generic *superclass* signature of an (anonymous) subclass.

## 5. Interview Q&A

<details>
<summary><b>Q1.</b> What is type erasure?</summary>

At compile time generics are checked, then type parameters are replaced by their bound (`Object` if unbounded), casts are inserted where needed, and bridge methods are generated. At run time `List<String>` and `List<Integer>` are the same class.
</details>

<details>
<summary><b>Q2.</b> Why can't you create a generic array (<code>new T[]</code>)?</summary>

Arrays are reified and covariant — they check element types at runtime — but `T` isn't known at runtime, so the check would be impossible and covariance + generics would defeat type safety. Use `ArrayList<T>` or `(T[]) new Object[n]` carefully.
</details>

<details>
<summary><b>Q3.</b> Is <code>List&lt;Object&gt; l = new ArrayList&lt;String&gt;();</code> legal? Why/why not?</summary>

No. Generics are invariant; otherwise `l.add(42)` would put an `Integer` into a list of `String`s. Use `List<? extends Object>`/`List<?>` for read-only polymorphism.
</details>

<details>
<summary><b>Q4.</b> Explain PECS with an example.</summary>

`Collections.copy(List<? super T> dest, List<? extends T> src)`: `src` produces `T`s (extends), `dest` consumes them (super). `Collection<? extends Number>` can be read as `Number` but not added to; `Collection<? super Integer>` can be added `Integer`s but only read as `Object`.
</details>

<details>
<summary><b>Q5.</b> <code>List&lt;?&gt;</code> vs <code>List&lt;Object&gt;</code> vs raw <code>List</code>?</summary>

`List<Object>` is a list you may add any object to (but only accepts exactly `List<Object>`). `List<?>` is a list of *some unknown* type — you can read `Object`s, add only `null`, and it accepts any `List<X>`. Raw `List` turns off all checks.
</details>

<details>
<summary><b>Q6.</b> What's a bridge method?</summary>

A compiler-generated synthetic method that preserves polymorphism after erasure, e.g. `compareTo(Object)` forwarding to `compareTo(Name)`; also used for covariant return types.
</details>

<details>
<summary><b>Q7.</b> How can you obtain generic type info at runtime?</summary>

Only from declarations: fields, method signatures, and superclass/interface signatures (`getGenericSuperclass`, `getGenericReturnType`). Libraries exploit this with type tokens (an anonymous subclass `new TypeReference<List<Foo>>(){}`).
</details>

<details>
<summary><b>Q8.</b> Why does <code>&lt;T extends Comparable&lt;? super T&gt;&gt;</code> appear in <code>Collections.max</code>?</summary>

So types that inherit their `compareTo` from a superclass still qualify (a `Timestamp` is comparable via `Date`'s `Comparable<Date>`). `Comparable` is a *consumer* of `T`, hence `super`.
</details>

## 6. Predict the output

<details>
<summary><b>P1.</b> Does it compile? What happens?</summary>

```java
List<String> a = new ArrayList<>();
List<Integer> b = new ArrayList<>();
System.out.println(a.getClass() == b.getClass());
```

Compiles; prints **`true`** (erasure).
</details>

<details>
<summary><b>P2.</b> Does it compile?</summary>

```java
void f(List<String> l) { }
void f(List<Integer> l) { }
```

**No** — "name clash: same erasure". Both become `f(List)`.
</details>

<details>
<summary><b>P3.</b> Does it compile?</summary>

```java
List<? extends Number> l = new ArrayList<Integer>();
l.add(5);
Number n = l.get(0);
```

`l.add(5)` **fails to compile** (the actual element type is unknown: could be `Double`). `l.get(0)` as `Number` is fine.
</details>

---
[↑ Back to Java Basics index](README.md)
