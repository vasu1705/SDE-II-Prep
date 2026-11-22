# OOP: Polymorphism, Interfaces, Initialisation Order

> **Level:** SDE-II / SDE-III · **Area:** Java · **Prev:** [Strings](03-strings.md) · **Next:** [Exceptions](05-exceptions.md)

## TL;DR

- **Overloading** = same name, different parameters, chosen at **compile time** from the *declared* (static) types.
- **Overriding** = subclass replaces an instance method, chosen at **run time** from the *actual* object type (virtual dispatch).
- Only **instance methods** are virtual. **Fields, static methods and private methods are not** — they're resolved by the declared type.
- Interface = a *capability/contract* (many allowed, `default` methods). Abstract class = *shared state + partial implementation* (one only).
- Don't call overridable methods from constructors; know the init order.

## The analogy: a universal remote

Pressing **"Play"** (a method call) on a *universal remote* (the reference type `Device`) does whatever the **actual device** in front of it does — TV, DVD, speaker. That's **overriding / runtime polymorphism**.
**Overloading** is different: it's like the remote having a "Play" button *and* a "Play(episode number)" button — the **button you press** (compile-time signature) is chosen by what you typed, not by what's behind it.

## 1. Overload vs override — and the dispatch rule

```java
// Run: DispatchDemo.java
public class DispatchDemo {
    static class Animal {
        String name = "animal";                       // field
        String sound() { return "..."; }              // instance method (virtual)
        static String kind() { return "Animal"; }     // static (hidden, not overridden)
    }
    static class Dog extends Animal {
        String name = "dog";                          // HIDES the field
        @Override String sound() { return "Woof"; }
        static String kind() { return "Dog"; }        // hides
    }

    static void speak(Animal a) { System.out.println("speak(Animal)"); }
    static void speak(Dog d)    { System.out.println("speak(Dog)"); }
    static void show(Object o)  { System.out.println("show(Object)"); }
    static void show(String s)  { System.out.println("show(String)"); }

    public static void main(String[] args) {
        Animal a = new Dog();                         // static type Animal, runtime type Dog

        System.out.println(a.sound());                // Woof        <- OVERRIDING: runtime type
        System.out.println(a.name);                   // animal      <- fields: static type
        System.out.println(((Dog) a).name);           // dog
        System.out.println(a.kind());                 // Animal      <- static method: static type

        speak(a);                                     // speak(Animal) <- OVERLOADING: static type of the argument
        speak(new Dog());                             // speak(Dog)

        Object o = "text";
        show(o);                                      // show(Object)  <- chosen at compile time
        show("text");                                 // show(String)
        show((Object) "text");                        // show(Object)
        show(null);                                   // show(String)  <- most specific applicable wins
    }
}
```

Output:

```text
Woof
animal
dog
Animal
speak(Animal)
speak(Dog)
show(Object)
show(String)
show(Object)
show(String)
```

**Override rules to remember**

| Rule | Detail |
|---|---|
| Same signature | name + parameter types |
| Return type | same or a **covariant** subtype |
| Access | same or **wider** (can't narrow `public` → `protected`) |
| Checked exceptions | may throw the same, narrower, or none — never *broader* new checked ones |
| `static`, `private`, `final` | not overridable (static/private are *hidden*; `final` forbidden) |
| `@Override` | always use it — the compiler catches typos and `equals(MyType)` mistakes |

**Overload resolution order:** exact/widening primitive → boxing → varargs. `void f(long)` beats `void f(Integer)` for `f(5)`.

## 2. Interface vs abstract class

| | Interface | Abstract class |
|---|---|---|
| State (instance fields) | no (only `static final` constants) | yes |
| Constructors | no | yes |
| Inheritance | a class can implement **many** | **one** superclass |
| Methods | abstract, `default`, `static`, `private` | abstract + concrete, any visibility |
| Models | **can-do** (`Comparable`, `Runnable`) | **is-a with shared code** (`AbstractList`) |
| Evolve without breaking implementors | add a `default` method | add a concrete method |

```java
// Run: DefaultDiamond.java
public class DefaultDiamond {
    interface Walker { default String move() { return "walk"; } }
    interface Swimmer { default String move() { return "swim"; } }

    // Two defaults with the same signature -> the class MUST resolve the conflict.
    static class Duck implements Walker, Swimmer {
        @Override public String move() { return Walker.super.move() + "+" + Swimmer.super.move(); }
    }

    public static void main(String[] args) {
        System.out.println(new Duck().move());      // walk+swim
    }
}
```

Resolution rules for default-method conflicts: **(1)** a class method (even inherited) always wins over interface defaults; **(2)** otherwise the **most specific** interface wins; **(3)** otherwise the compiler forces you to override and pick with `X.super.m()`.

Design guidance: *program to interfaces*; use abstract classes for template-method skeletons; **prefer composition over inheritance** (inheritance breaks encapsulation — see the `Point`/`ColorPoint` `equals` problem in [equals & hashCode](../02-collections/02-equals-hashcode.md)).

## 3. Initialisation order (a favourite trick question)

```java
// Run: InitOrder.java
public class InitOrder {
    static class Parent {
        static { System.out.println("1. Parent static block"); }
        { System.out.println("3. Parent instance block"); }
        Parent() { System.out.println("4. Parent constructor"); describe(); }
        void describe() { System.out.println("   Parent.describe"); }
    }

    static class Child extends Parent {
        static { System.out.println("2. Child static block"); }
        private String label = "ready";                     // initialised AFTER the Parent constructor body
        { System.out.println("5. Child instance block"); }
        Child() { super(); System.out.println("6. Child constructor, label=" + label); }
        @Override void describe() { System.out.println("   Child.describe, label=" + label); }
    }

    public static void main(String[] args) {
        System.out.println("-- first new Child()");
        new Child();
        System.out.println("-- second new Child()");
        new Child();                                          // static blocks do NOT run again
    }
}
```

Output:

```text
-- first new Child()
1. Parent static block
2. Child static block
3. Parent instance block
4. Parent constructor
   Child.describe, label=null
5. Child instance block
6. Child constructor, label=ready
-- second new Child()
3. Parent instance block
4. Parent constructor
   Child.describe, label=null
5. Child instance block
6. Child constructor, label=ready
```

**Order:** class loading → *static initialisers, parent first* (once per class) → for each `new`: *parent* instance initialisers + constructor, then *child* field initialisers/instance blocks + constructor body.

> [!WARNING]
> **The constructor trap:** the `Parent` constructor called the overridden `describe()` **before** `Child.label` was assigned → it saw `null`. **Never call overridable methods from a constructor** (make them `final`/`private`, or use a factory/`init()` method).

## 4. Other pillars, in practice

- **Encapsulation** — `private` fields, expose behaviour not data; immutable value objects (`record`).
- **Abstraction** — depend on interfaces (`List`), not implementations (`ArrayList`).
- **Inheritance** — `is-a`; use sparingly; mark classes `final` unless designed for extension; Java 17 `sealed` restricts who may extend.
- **Polymorphism** — subtype (override), parametric (generics), ad-hoc (overloading).
- **SOLID in one line each:** **S**ingle responsibility · **O**pen/closed (extend by adding classes, not editing) · **L**iskov (subtypes must honour the base contract) · **I**nterface segregation (small, focused interfaces) · **D**ependency inversion (depend on abstractions; this is what Spring DI automates).
- **`Object` methods:** `equals`, `hashCode`, `toString`, `getClass`, `clone` (avoid; use copy constructors), `finalize` (deprecated for removal).
- **`instanceof` patterns (Java 16):** `if (shape instanceof Circle c && c.r() > 0) { … }`.

## 5. Interview Q&A

<details>
<summary><b>Q1.</b> Compile-time vs runtime polymorphism?</summary>

Compile-time = overloading (resolved by the compiler from static types of arguments). Runtime = overriding (the JVM picks the implementation from the object's actual class via the virtual method table / `invokevirtual`).
</details>

<details>
<summary><b>Q2.</b> Can we override static or private methods? Fields?</summary>

No. `static` and `private` methods are resolved at compile time by the declared type — redeclaring them in a subclass *hides* them. Fields are never polymorphic; a same-named subclass field *hides* the parent's.
</details>

<details>
<summary><b>Q3.</b> Interface or abstract class? Why did <code>default</code> methods appear?</summary>

Use an interface for a capability that unrelated classes can have; an abstract class when subclasses share state or constructor logic. `default` methods let APIs evolve (e.g. `Collection.stream()`, `List.sort`) without breaking existing implementations.
</details>

<details>
<summary><b>Q4.</b> What happens if two interfaces provide the same <code>default</code> method?</summary>

Compile error unless the implementing class overrides it; inside it you may delegate with `A.super.m()`. A concrete class method always beats a default.
</details>

<details>
<summary><b>Q5.</b> Can a constructor be overridden/inherited? Can it be <code>private</code>?</summary>

Not inherited, so not overridden. Private constructors are used for singletons, utility classes, static factories, builders.
</details>

<details>
<summary><b>Q6.</b> What is covariant return type?</summary>

An overriding method may return a subtype of the parent's return type (`Animal copy()` → `Dog copy()`). The compiler adds a synthetic *bridge method* to keep binary compatibility.
</details>

<details>
<summary><b>Q7.</b> Why is "composition over inheritance" advised?</summary>

Inheritance couples a subclass to the parent's implementation details (fragile base class: e.g. `HashSet.addAll` calling `add`, which the subclass counts twice). Composition + delegation gives flexibility and testability.
</details>

<details>
<summary><b>Q8.</b> What is the difference between <code>abstract</code> class and <code>final</code> class? <code>sealed</code>?</summary>

`abstract`: can't instantiate, meant to be extended. `final`: can't be extended. `sealed` (Java 17): extendable only by the listed `permits` subclasses — gives you closed hierarchies the compiler can exhaustively check in `switch`.
</details>

## 6. Predict the output

<details>
<summary><b>P1.</b></summary>

```java
class A { void f(Object o) { System.out.println("A.Object"); } }
class B extends A { void f(String s) { System.out.println("B.String"); } }
A x = new B();
x.f("hi");
```

**`A.Object`** — `B.f(String)` *overloads*, it doesn't override. The compiler looks only at `A`'s methods for `x`, finds `f(Object)`, and the runtime type doesn't change that.
</details>

<details>
<summary><b>P2.</b></summary>

```java
class P { static void hi() { System.out.println("P"); } }
class C extends P { static void hi() { System.out.println("C"); } }
P p = new C();
p.hi();
```

**`P`** — static methods are bound to the declared type.
</details>

<details>
<summary><b>P3.</b></summary>

```java
class P { int x = 1; int get() { return x; } }
class C extends P { int x = 2; @Override int get() { return x; } }
P p = new C();
System.out.println(p.x + " " + p.get());
```

**`1 2`** — field access uses `P`; `get()` is virtual and returns `C.x`.
</details>

---
[↑ Back to Java Basics index](README.md)
