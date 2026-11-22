# Primitives, Wrappers, Autoboxing & Equality

> **Level:** SDE-II / SDE-III · **Area:** Java · **Prev:** [Memory model](01-memory-model.md) · **Next:** [Strings](03-strings.md)

## TL;DR

- **Primitives** hold raw values (fast, never `null`). **Wrappers** are objects (needed by generics/collections, can be `null`).
- **Autoboxing** converts silently between them — convenient, but hides **`NullPointerException`**, **identity-vs-value bugs** (`==`) and **allocation cost**.
- `==` compares **values for primitives**, **references for objects**. Use `.equals()` for content.
- Floating-point and integer arithmetic have well-defined (and surprising) edge cases: overflow wraps, `0.1 + 0.2 != 0.3`, `NaN != NaN`.

## The analogy: cash vs a gift card in an envelope

A primitive is **cash in your pocket**: it *is* the value. A wrapper is **an envelope containing the cash**: you can pass the envelope around, label it, or hand over an *empty* envelope (`null`) — and comparing two envelopes with `==` asks *"is this literally the same envelope?"*, not *"is the same amount inside?"*.

## 1. The primitives

| Type | Size | Range / notes | Wrapper |
|---|---|---|---|
| `byte` | 8 bit | −128 … 127 | `Byte` |
| `short` | 16 bit | −32,768 … 32,767 | `Short` |
| `char` | 16 bit | unsigned 0 … 65,535 (UTF-16 code unit) | `Character` |
| `int` | 32 bit | −2³¹ … 2³¹−1 (≈ ±2.1 billion) | `Integer` |
| `long` | 64 bit | −2⁶³ … 2⁶³−1 | `Long` |
| `float` | 32 bit | IEEE-754, ~7 decimal digits | `Float` |
| `double` | 64 bit | IEEE-754, ~15–16 decimal digits | `Double` |
| `boolean` | JVM-defined (1 byte in arrays) | `true`/`false` | `Boolean` |

Defaults: numeric `0`, `boolean` `false`, `char` `'\u0000'`, references `null` (applies to **fields and array elements** — *local variables have no default*; reading an unassigned local is a compile error).

## 2. Autoboxing and unboxing

```java
Integer a = 5;          // autobox:   Integer.valueOf(5)
int b = a;              // unbox:     a.intValue()
List<Integer> l = new ArrayList<>();
l.add(1);               // autobox
int first = l.get(0);   // unbox
```

Costs: each boxing may allocate (except small cached values); unboxing a `null` throws NPE; arithmetic on wrappers unboxes then reboxes — **a `Long sum` accumulator in a hot loop allocates on nearly every iteration and is typically several times slower than `long sum`** (the JIT sometimes eliminates it, so measure with JMH).

### 2.1 The Integer cache — the famous `==` trap

`Integer.valueOf` (used by autoboxing) returns **cached instances for −128…127**. Same for `Short`, `Long`, `Byte`, `Character` (0…127), `Boolean`. **Not** `Float`/`Double`.

```java
// Run: IntegerCache.java
public class IntegerCache {
    public static void main(String[] args) {
        Integer a = 127, b = 127;
        Integer c = 128, d = 128;
        System.out.println("127 == 127 : " + (a == b));        // true  (same cached object)
        System.out.println("128 == 128 : " + (c == d));        // false (two different objects)
        System.out.println("128 equals : " + c.equals(d));     // true

        Long l = 1L;
        System.out.println("Long(1).equals(1)  : " + l.equals(1));    // false: 1 is an Integer
        System.out.println("Long(1).equals(1L) : " + l.equals(1L));   // true
        System.out.println("new Integer vs valueOf: " + (Integer.valueOf(5) == Integer.valueOf(5)));  // true
    }
}
```

Lesson: **never compare wrapper objects with `==`**; use `equals` (or `Integer.compare`, or unbox deliberately). The cache upper bound can be raised with `-XX:AutoBoxCacheMax=<n>` — so code that "works" with `==` is **environment-dependent**. `new Integer(5)` is deprecated for removal.

### 2.2 Unboxing NPE hiding in the ternary operator

```java
Integer count = null;
int x = condition ? count : 0;   // NPE! The ternary's type is int, so `count` is unboxed.
Integer y = condition ? count : Integer.valueOf(0);  // OK: both operands are Integer
```

Also: `Map<String,Integer> m; int v = m.get("missing");` → NPE. Use `getOrDefault`.

## 3. Arithmetic traps in one runnable file

```java
// Run: ArithmeticTraps.java
import java.math.BigDecimal;

public class ArithmeticTraps {
    public static void main(String[] args) {
        // 1. Overflow wraps silently
        System.out.println(Integer.MAX_VALUE + 1);                    // -2147483648
        System.out.println(1000 * 60 * 60 * 24 * 365);                // int overflow -> garbage
        System.out.println(1000L * 60 * 60 * 24 * 365);               // 31536000000 (long arithmetic)
        try { Math.addExact(Integer.MAX_VALUE, 1); }
        catch (ArithmeticException e) { System.out.println("addExact -> " + e.getMessage()); }

        // 2. abs(MIN_VALUE) is still negative
        System.out.println(Math.abs(Integer.MIN_VALUE));              // -2147483648

        // 3. Integer division & modulo (truncate toward zero)
        System.out.println(5 / 2 + " " + -5 / 2 + " " + -5 % 2 + " " + Math.floorMod(-5, 2));   // 2 -2 -1 1

        // 4. Floating point
        System.out.println(0.1 + 0.2);                                // 0.30000000000000004
        System.out.println(0.1 + 0.2 == 0.3);                         // false
        System.out.println(new BigDecimal(0.1));                      // 0.1000000000000000055511151231257827...
        System.out.println(new BigDecimal("0.1").add(new BigDecimal("0.2")));   // 0.3
        System.out.println(BigDecimal.valueOf(0.1));                  // 0.1  (uses Double.toString)

        // 5. NaN and signed zero
        System.out.println((Double.NaN == Double.NaN) + " " + Double.valueOf(Double.NaN).equals(Double.NaN));   // false true
        System.out.println((0.0 == -0.0) + " " + Double.valueOf(0.0).equals(-0.0));                              // true false
        System.out.println(1.0 / 0);                                  // Infinity (no exception for doubles)
        // System.out.println(1 / 0);                                 // ArithmeticException for ints

        // 6. Narrowing casts
        System.out.println((int) 3.99 + " " + (int) -3.99 + " " + Math.round(-2.5) + " " + (byte) 200);   // 3 -3 -2 -56

        // 7. char is numeric
        char c = 'a';
        System.out.println(c + 1);                                    // 98 (int)
        System.out.println((char) (c + 1));                           // b
        c += 1;                                                       // compound assignment has an implicit cast
        System.out.println(c);                                        // b

        // 8. Compound assignment hides a cast
        short s = 1;
        s += 1;                                                       // OK
        // s = s + 1;                                                 // compile error: int cannot be assigned to short
        System.out.println(s);

        // 9. i = i++
        int i = 5;
        i = i++;
        System.out.println(i);                                        // 5 (old value assigned back)
    }
}
```

Output:

```text
-2147483648
1471228928
31536000000
addExact -> integer overflow
-2147483648
2 -2 -1 1
0.30000000000000004
false
0.1000000000000000055511151231257827021181583404541015625
0.3
0.1
false true
true false
Infinity
3 -3 -2 -56
98
b
b
2
5
```

**Money:** never `double`. Use `BigDecimal` (constructed from `String` or `BigDecimal.valueOf`) with an explicit `RoundingMode`, or store **integer minor units** (`long cents`).

## 4. Equality cheat sheet

| Expression | Compares | Notes |
|---|---|---|
| `int == int` | values | |
| `Integer == int` | **unboxes** → values | NPE if `null` |
| `Integer == Integer` | **references** | cached −128…127 only! |
| `String == String` | references | pooled literals may match; never rely on it ([Strings](03-strings.md)) |
| `a.equals(b)` | logical equality | default = `==`; override for value types |
| `Objects.equals(a, b)` | null-safe `equals` | |
| `Double.compare(a, b)` | total order (`NaN` largest, `-0.0 < 0.0`) | use in comparators/`equals` |
| `Arrays.equals` / `deepEquals` | array contents | `arr1.equals(arr2)` is identity! |

## 5. Interview Q&A

<details>
<summary><b>Q1.</b> What's the output of <code>Integer a=127,b=127,c=128,d=128; (a==b)+" "+(c==d)</code>?</summary>

`true false`. Autoboxing calls `Integer.valueOf`, which caches −128…127. 128 creates two distinct objects. Always use `equals`.
</details>

<details>
<summary><b>Q2.</b> When does autoboxing cause performance problems?</summary>

Boxed accumulators in loops (`Long total = 0L; total += x;` allocates a new `Long` each iteration beyond the cache), generic collections of primitives (`List<Integer>` ≈ 4× the memory of `int[]` plus pointer chasing), and `Map<Integer,Integer>` counters. Use primitive arrays, `IntStream`, or specialised collections.
</details>

<details>
<summary><b>Q3.</b> Why can unboxing throw an NPE and how do you spot it?</summary>

Unboxing is an implicit `x.intValue()` call. If the wrapper is `null` → NPE. Common sources: `map.get()` returning `null`, ternary with mixed `Integer`/`int`, database nullable columns mapped to `int`. Since Java 14, helpful NPE messages name the null variable.
</details>

<details>
<summary><b>Q4.</b> Why is <code>0.1 + 0.2 != 0.3</code>?</summary>

0.1 and 0.2 have no exact binary representation (like 1/3 in decimal). Their approximations add to 0.30000000000000004. Compare with a tolerance (`Math.abs(a-b) < 1e-9`) or use `BigDecimal` for exact decimal arithmetic.
</details>

<details>
<summary><b>Q5.</b> <code>new BigDecimal(0.1)</code> vs <code>new BigDecimal("0.1")</code> vs <code>BigDecimal.valueOf(0.1)</code>?</summary>

The `double` constructor captures the *binary* approximation (0.1000000000000000055…). The `String` constructor is exact. `valueOf(double)` uses `Double.toString`, giving `0.1` — convenient but still starts from a double. Prefer `String`.
</details>

<details>
<summary><b>Q6.</b> What's the difference between <code>int</code> and <code>Integer</code>?</summary>

`int` is a 32-bit value type (default `0`, no methods, fast, can't be generic). `Integer` is an immutable object (nullable, usable in generics/collections, has utility methods, ~16 B on heap, cached for small values).
</details>

<details>
<summary><b>Q7.</b> Why does <code>Math.abs(Integer.MIN_VALUE)</code> return a negative number?</summary>

Two's complement has one more negative value than positive; +2³¹ doesn't fit in an `int`, so negation overflows back to MIN_VALUE. Use `Math.absExact` to get an exception, or widen to `long`.
</details>

<details>
<summary><b>Q8.</b> How does <code>Double.equals</code> differ from <code>==</code> on doubles?</summary>

`Double.equals` compares the bit patterns after canonicalising NaN: `NaN.equals(NaN)` is `true` and `0.0.equals(-0.0)` is `false`. `==` on primitives follows IEEE-754: `NaN == NaN` false, `0.0 == -0.0` true. That's why using a `Double` key in a `HashMap` behaves slightly differently from `==` intuition.
</details>

## 6. Predict the output

<details>
<summary><b>P1.</b></summary>

```java
Long a = 127L, b = 127L;
System.out.println((a == b) + " " + a.equals(127));
```

**`true false`** — 127 is within the `Long` cache; `a.equals(127)` receives an `Integer`.
</details>

<details>
<summary><b>P2.</b></summary>

```java
byte b = (byte) 130;
System.out.println(b);
System.out.println(b & 0xFF);
```

**`-126` then `130`** — narrowing keeps the low 8 bits (`10000010`) → negative as signed; masking with `0xFF` recovers the unsigned value.
</details>

<details>
<summary><b>P3.</b></summary>

```java
System.out.println('a' + 'b');
System.out.println("" + 'a' + 'b');
System.out.println((char) ('a' + 1));
```

**`195`, `ab`, `b`** — `char + char` is `int` arithmetic; string concatenation changes the meaning.
</details>

<details>
<summary><b>P4.</b></summary>

```java
long big = 2147483647 + 1;
System.out.println(big);
```

**`-2147483648`** — the addition is done in `int` *before* widening to `long`. Write `2147483647L + 1`.
</details>

---
[↑ Back to Java Basics index](README.md)
