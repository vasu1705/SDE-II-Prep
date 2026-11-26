# 03 — Data Structures & Algorithms

[← Back to book](../README.md)

Problems are grouped **by pattern**, not by company, so one technique unlocks many questions. Each folder has a task README with the problem list, a one-line hint per problem, and a status column. Solutions come later, one at a time.

## ⭐ Highest-priority overlaps (do these first)

These appear across several interview reports, so they have the best return on time:

| ⭐ | Problem | Folder |
|---|---|---|
| ☐ | **LRU / LFU cache** from scratch | [data-structure design](06-data-structure-design/README.md) |
| ☐ | **Trapping Rain Water** (stack + two pointers) | [arrays & two pointers](01-arrays-sliding-window-two-pointers/README.md) |
| ☐ | **Kth Largest Element in a Stream** | [heaps & streams](02-heaps-and-streams/README.md) |
| ☐ | **Word Break** (DP + Trie) | [DP & tries](05-dp-and-tries/README.md) |
| ☐ | **Clone Graph** (and the random-pointer variation) | [graphs & trees](04-graphs-and-trees/README.md) |
| ☐ | **Median of Two Sorted Arrays** | [binary search](03-binary-search/README.md) |
| ☐ | **Search / keyboard autocomplete** (Trie + design) | [DP & tries](05-dp-and-tries/README.md), [LLD](../04-low-level-design/08-keyboard-autocomplete/README.md), [HLD](../01-system-design/04-storage-and-search/README.md) |

## Pattern folders

| # | Folder | Problems |
|---|--------|----------|
| 1 | [Arrays, sliding window & two pointers](01-arrays-sliding-window-two-pointers/README.md) | Trapping Rain Water, Two Sum family, Kadane, Max Product Subarray, Longest Substring, Min Window Substring |
| 2 | [Heaps, streams & priority queues](02-heaps-and-streams/README.md) | Kth Largest in Stream, Median from Stream, Merge K Lists, Top K Frequent, K Closest Points, Priority Scheduler |
| 3 | [Binary search](03-binary-search/README.md) | Search on answer (capacity/days/weights), Median of Two Sorted Arrays |
| 4 | [Graphs & trees](04-graphs-and-trees/README.md) | Clone Graph, Cycle in directed graph, Course Schedule, Word Ladder, Serialize/Deserialize tree |
| 5 | [DP & tries](05-dp-and-tries/README.md) | Word Break, LIS, Autocomplete with a Trie |
| 6 | [Data structure design](06-data-structure-design/README.md) | LRU, LFU |

## How we will solve each problem

1. Create `<pattern folder>/<problem-name>.md` from the [DSA problem template](../templates/dsa-problem-template.md): problem, approach, complexity, edge cases, code, tests.
2. Code is **Java 21**, single file, with a `// Run: ClassName.java` first line and a `main` that checks the examples. (Python is fine as an extra.)
3. Time-box: **25 minutes** to a working solution, then write down what you missed.
4. Flip the status in the folder README from ☐ to ✅ and add the link.

Complexity discipline: always state **time and space**, then name the edge cases (empty input, one element, duplicates, negatives, overflow).

## Foundations (revision checklist)
- [ ] Big-O cheat sheet & amortized analysis
- [ ] Arrays, strings, hashing
- [ ] Linked lists, stacks, queues, monotonic stack/queue
- [ ] Heaps / priority queues
- [ ] Trees, BST, tries
- [ ] Graphs: BFS, DFS, topological sort, union-find
- [ ] Shortest paths: Dijkstra, Bellman-Ford
- [ ] Backtracking, greedy, bit manipulation
- [ ] Segment tree / Fenwick tree (advanced)

## Already solved elsewhere in the repo
- LRU cache (two ways), Top-K frequent, first non-repeating character, subarray sum = K: [Collections practice problems](../02-languages/java/02-collections/06-practice-problems.md).

## Practice log
| Problem | Pattern | Difficulty | Status | Notes |
|---------|---------|------------|--------|-------|
|         |         |            |        |       |
