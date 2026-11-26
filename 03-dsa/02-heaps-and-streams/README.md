# Heaps, Streams & Priority Queues

[← Back to DSA](../README.md)

**Pattern recap:** a heap gives the min/max in O(1) and updates in O(log n). *Top-K* uses a heap of size K (a **min**-heap for the K largest). *Streaming median* uses two heaps. *Merge K* keeps one candidate per list in a heap. Java: `PriorityQueue` with a `Comparator` (see [collections overview](../../02-languages/java/02-collections/01-framework-overview.md)).

| Done | Problem | LeetCode | Difficulty | Key idea / hint | Solution |
|---|---|---|---|---|---|
| ☐ ⭐ | **Kth Largest Element in a Stream** | 703 | Easy | Min-heap of size K; the root is the answer; `add` is O(log K) | |
| ☐ | Find Median from Data Stream | 295 | Hard | Max-heap for the lower half, min-heap for the upper half; keep sizes within 1 | |
| ☐ | Merge K Sorted Lists | 23 | Hard | Min-heap of list heads, O(N log k); or divide and conquer | |
| 🟡 | Top K Frequent Elements | 347 | Medium | Counts in a `HashMap`, then heap (O(n log k)) or **bucket sort** (O(n)). Heap version exists in [collections practice](../../02-languages/java/02-collections/06-practice-problems.md); add the bucket-sort version | |
| ☐ | Find K Closest Points to Origin | 973 | Medium | Max-heap of size K by distance (no `sqrt` needed); or quickselect (average O(n)) | |
| ☐ | Design a Scheduler with Task Priorities | — (design) | Medium | `PriorityQueue` ordered by (priority, sequence number for FIFO ties); delayed tasks via timestamp; then thread-safety (`PriorityBlockingQueue`) and starvation (aging) | |

## Edge cases to rehearse
K larger than the stream so far, duplicates, ties in priority, negative numbers, comparator overflow (never subtract), concurrent producers.

## Checklist
- [ ] Explain why the K *largest* uses a **min**-heap
- [ ] Explain the two-heap invariant for the median
- [ ] Compare heap vs quickselect vs bucket sort for Top-K (time, space, streaming support)
