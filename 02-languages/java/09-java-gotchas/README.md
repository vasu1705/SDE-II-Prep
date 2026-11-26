# Java — Gotchas & "What Happens If…"

[← Back to Java](../README.md)

> [!NOTE]
> **Status:** drafted by a background writer. 14 of 15 runnable blocks passed on JDK 21; the 15th calls `System.exit`/`halt` on purpose to show exit codes. The note is very long (~96 KB) and has **not been read line by line**.

| # | Note | You will learn |
|---|------|----------------|
| 1 | [Puzzlers and "what happens if…"](01-puzzlers-and-what-happens-if.md) | class initialisation & JVM exit/shutdown hooks, inner/anonymous/lambda `this`, enum quirks, interface default/static/private methods, casting, arrays, typing & operators, overload resolution & varargs, `final`/immutability/copying, `Optional`, collection and comparator traps, numbers & `BigDecimal` |

Not written yet: `java.time`, I/O, serialization, regex, reflection and a cross-topic rapid-fire sheet (see the [tracker](../../../TRACKER.md)).

Already covered elsewhere: [wrappers & `==`](../01-java-basics/02-primitives-wrappers-equality.md), [strings](../01-java-basics/03-strings.md), [OOP & init order](../01-java-basics/04-oop-polymorphism.md), [exceptions](../01-java-basics/05-exceptions.md), [generics](../01-java-basics/06-generics.md).

## Revision checklist
- [ ] Predict static/instance initialisation order across a class hierarchy
- [ ] Explain what a shutdown hook can and can't do
- [ ] Explain overload resolution with boxing and varargs
- [ ] List five comparator/collection traps and their fixes
