# Java — Basics

[← Back to Java](../README.md)

Read in order. Every note: analogy → mechanism → runnable code (verified on JDK 21) → pitfalls → interview Q&A → predict-the-output.

| # | Note | You will learn |
|---|------|----------------|
| 1 | [Memory model](01-memory-model.md) | Stack vs heap, pass-by-value, object layout, GC roots, leaks, `StackOverflowError` vs OOM |
| 2 | [Primitives, wrappers & equality](02-primitives-wrappers-equality.md) | Integer cache, autoboxing NPEs, overflow, floating point, `BigDecimal`, `==` vs `equals` |
| 3 | [Strings](03-strings.md) | Immutability, pool & `intern`, concatenation cost, `split`/`strip`/text blocks, Unicode |
| 4 | [OOP & polymorphism](04-oop-polymorphism.md) | Overload vs override dispatch, field hiding, interfaces vs abstract classes, init order, constructor trap |
| 5 | [Exceptions](05-exceptions.md) | Checked vs unchecked, `finally` traps, try-with-resources & suppressed, performance |
| 6 | [Generics](06-generics.md) | Erasure, bridge methods, invariance, wildcards & PECS, type tokens |
| 7 | [Lambdas, streams & Optional](07-lambdas-streams-optional.md) | Lazy pipelines, collectors, parallel pitfalls, `Optional` rules |
| 8 | [Modern Java 11→21](08-modern-java.md) | Records, sealed types, pattern-matching `switch`, sequenced collections, virtual threads |
| 9 | [Choosing the right tool](09-choosing-the-right-tool.md) | Records vs classes vs enums vs sealed, streams vs loops, which collection, `Optional` vs exceptions vs a `Result` type, which async tool, what to adopt first |

## Revision checklist

- [ ] Explain pass-by-value using the `swap` example
- [ ] Predict `Integer` `==` results around 127/128
- [ ] Explain why `String` is immutable (4 reasons) and what `new String("a")` creates
- [ ] Draw the dispatch rules: overload (static type) vs override (runtime type) vs fields/static (static type)
- [ ] State the init order for a parent/child pair
- [ ] Explain `finally` + `return` and suppressed exceptions
- [ ] Explain erasure and PECS with `Collections.copy`
- [ ] Explain why streams are lazy and single-use
- [ ] Model a closed hierarchy with `sealed` + `record` + `switch`
