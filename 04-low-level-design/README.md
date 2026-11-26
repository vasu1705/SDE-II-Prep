# 04 — Low-Level Design (OOD & Machine Coding)

[← Back to book](../README.md)

Each problem gets its own folder with a task README now (requirements, entities, patterns, concurrency concerns, test checklist) and the solution later. Implement in **Java 21** with **SOLID**, the patterns named below, and **JUnit 5 tests**.

| # | Problem | Main pattern(s) | Core challenge | Priority |
|---|---------|-----------------|----------------|----------|
| 1 | [Inventory Management System](01-inventory-management/README.md) | Repository, Strategy, Observer | stock **reservation** + concurrency safety | ⭐ focus |
| 2 | [Shopping Cart with discount/coupon rules](02-shopping-cart-discounts/README.md) | Strategy, Chain of Responsibility, Specification | **composable** rules, money maths | ⭐ focus |
| 3 | [Vending Machine](03-vending-machine/README.md) | **State** | clean transitions, change-making | |
| 4 | [Library Management System](04-library-management/README.md) | entity modelling, Strategy (fines) | borrowing limits, fines, reservations | |
| 5 | [Food Delivery Order State Machine](05-food-delivery-order-state-machine/README.md) | State, Observer | strict transitions, cancellation rules, event hooks | ⭐ focus |
| 6 | [Logging Framework](06-logging-framework/README.md) | Singleton, Chain of Responsibility, Strategy | levels, multiple sinks, async logging | |
| 7 | [Hit Counter](07-hit-counter/README.md) | time-bucketed circular buffer | high-concurrency writes, scaling to millions RPS | ⭐ focus |
| 8 | [Keyboard Auto-Complete Engine](08-keyboard-autocomplete/README.md) | Trie | memory optimisation, weighted ranking | |

Priority note: the source list says to spend most time on the **Hit Counter, Inventory System, Shopping Cart and Order State Machine**.

## Approach for a 35-minute machine-coding round
1. **Clarify** (3 min): scope, what is out of scope, concurrency expectations, in-memory only?
2. **Entities & relationships** (5 min): nouns → classes; enums for fixed sets; decide immutable value objects vs entities.
3. **APIs** (3 min): the public interface first; hide implementation behind interfaces.
4. **Patterns** (5 min): name where you will use State/Strategy/etc. and *why*; do not add patterns "for show".
5. **Code** (15 min): core path first, compile often, small classes.
6. **Test & extend** (4 min): happy path + two edge cases; say how you'd add the next requirement.

## Conventions in this section
- One folder per problem: `README.md` (task) → later `src/` (code) + `Main.java` demo + tests.
- Use the [LLD problem template](../templates/lld-problem-template.md) for the write-up.
- Single-file runnable demos use the `// Run: ClassName.java` convention used across the repo.

## Revision checklist
- [ ] Draw a class diagram for each problem in ≤ 5 minutes
- [ ] Explain every pattern you used and its alternative
- [ ] Show the concurrency strategy (lock, atomic, immutable) for problems 1, 6, 7
