# Java — Collections

[← Back to Java](../README.md)

Read in order. Each note has: analogy → mechanism → runnable code → pitfalls → interview Q&A → predict-the-output.

| # | Note | You will learn |
|---|------|----------------|
| 1 | [Framework overview](01-framework-overview.md) | Hierarchy, complexity table, decision tree, immutable vs unmodifiable, Java 21 sequenced collections |
| 2 | [`equals()` & `hashCode()`](02-equals-hashcode.md) | The contract, what breaks (with proof), records, JPA traps, `compareTo` consistency |
| 3 | [`HashMap` internals](03-hashmap-internals.md) | put/get step by step, bit-spreading, resize split, treeification (verified by reflection), fail-fast, `merge`/`compute` |
| 4 | [Ordered maps & LRU](04-ordered-maps-lru.md) | `LinkedHashMap` access-order LRU, `TreeMap` navigation, comparator traps |
| 5 | [Concurrent collections](05-concurrent-collections.md) | Lost updates demo, `ConcurrentHashMap` design, blocking queues, copy-on-write |
| 6 | [Practice problems](06-practice-problems.md) | 10 predict-the-output puzzles + 6 coding problems (LRU, HashMap from scratch, Top-K, …) |

## Revision checklist

- [ ] Can explain the `equals`/`hashCode` contract and what each violation breaks
- [ ] Can draw `HashMap.put()` from memory (hash → index → chain → treeify → resize)
- [ ] Know when resize vs treeify happens (≥ 9th node **and** table ≥ 64)
- [ ] Can write an LRU cache two ways
- [ ] Can explain why `ConcurrentHashMap` forbids nulls and how it locks
- [ ] Solved all of the practice problems without looking
