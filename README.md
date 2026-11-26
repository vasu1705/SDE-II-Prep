# SDE-II / SDE-III Prep — Revision Book

A personal revision guide for SDE-II/III interviews: system design, Java, Python, Node.js, and DSA.
Every note is plain Markdown and renders directly on GitHub (use the **☰ outline** button at the top-right of any file for its table of contents).

## How to use this book

1. Go through sections in order, or jump to a weak area.
2. Every topic follows [the same template](templates/topic-template.md): *Concept → Why it matters → Example → Pitfalls → Interview Q&A → Further reading*.
3. Interview Q&A answers are hidden in collapsible blocks. Try answering first, then expand.
4. Tick the checklists below as topics are written and revised.

## Contents

| # | Section | What's inside |
|---|---------|---------------|
| 1 | [System Design](01-system-design/README.md) | Fundamentals, building blocks, classic case studies |
| 2 | [Languages](02-languages/README.md) | [Java](02-languages/java/README.md) (✅ [Basics](02-languages/java/01-java-basics/README.md), ✅ [Collections](02-languages/java/02-collections/README.md)) · [Python](02-languages/python/README.md) · [Node.js](02-languages/node/README.md) |
| 3 | [DSA](03-dsa/README.md) | Patterns, ⭐ priority overlaps, problem lists by pattern |
| 4 | [Low-Level Design](04-low-level-design/README.md) | 8 machine-coding problems (Inventory, Cart, Vending Machine, Hit Counter, …) |
| 5 | [Databases & SQL](05-databases/README.md) | Order schema, clustered vs non-clustered indexes, inventory consistency, ACID |
| 6 | [Behavioral](06-behavioral/README.md) | STAR template and story bank |

📅 **[Study plan (6 weeks + "one week left" version)](STUDY-PLAN.md)** · ✅ **[Revision tracker](TRACKER.md)**

## Progress

Detailed topic-by-topic progress lives in the **[Revision Tracker](TRACKER.md)** (concurrency, JVM, Spring Boot/JPA, modern Java, DSA patterns).

- [ ] System Design
- [ ] Java — ✅ basics, ✅ collections, ✅ concurrency & async, ✅ [Spring Boot](02-languages/java/06-spring-boot/README.md) (lean, unexecuted) · ⏳ JVM/GC, ⏳ Maven/Gradle
- [ ] Python
- [ ] Node.js
- [ ] DSA

## How to run the code samples ("runnable" defined)

A Java code block is **runnable** when its **first line** is `// Run: ClassName.java`. It is then a complete, single-file program: one public class `ClassName` with a `main` method and no third-party libraries. To run it:

1. Copy the block into a file named `ClassName.java`.
2. Run `java ClassName.java` (needs **JDK 21**; Java 11+ can launch a single source file directly, no `javac` step).
3. Some blocks need JVM flags, shown as `// Run: ClassName.java  (needs: java --some-flag ClassName.java)`; use those flags.

Other points:
- Blocks **without** the `// Run:` marker are **illustrations** (fragments, config, or multi-file code such as the Spring samples). They are not meant to be run as-is.
- The output printed under a runnable block was captured from a real run on JDK 21. Results that depend on timing or threads (race-condition counters, speed comparisons) differ from run to run; the note says when.
- **Not executed:** the [Spring Boot notes](02-languages/java/06-spring-boot/README.md) and some short snippets in the concurrency primer are marked as unexecuted.
- To run every runnable block in a note at once, use [`tools/run-java-blocks.py`](tools/run-java-blocks.py). It reports only failures, and a couple of blocks fail on purpose (an `OutOfMemoryError` demo and a `System.exit` demo).

## Conventions

- Folders and files are numbered (`01-`, `02-`) so they sort in study order.
- Every folder has a `README.md` index.
- Diagrams use [Mermaid](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams) so they render on GitHub.
- Callouts use GitHub alerts: `> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`.
