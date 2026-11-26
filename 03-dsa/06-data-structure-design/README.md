# Data Structure Design

[← Back to DSA](../README.md)

**Pattern recap:** combine two structures so every operation is O(1): a hash map for lookup plus a list/bucket structure for ordering.

| Done | Problem | LeetCode | Difficulty | Key idea / hint | Solution |
|---|---|---|---|---|---|
| 🟡 ⭐ | **LRU Cache** from scratch | 146 | Medium | `HashMap<K, Node>` + doubly linked list with sentinel head/tail; move to front on access, evict the tail | Reference implementation (two ways, including `LinkedHashMap`): [LRU from scratch](../../02-languages/java/02-collections/06-practice-problems.md#1-lru-cache-from-scratch), [LinkedHashMap LRU](../../02-languages/java/02-collections/04-ordered-maps-lru.md). Still to do: write it again from memory and add tests |
| ☐ ⭐ | **LFU Cache** from scratch | 460 | Hard | `Map<K, Node>` + `Map<Integer, LinkedHashSet<K>>` (frequency buckets) + a `minFreq` variable; evict the oldest key in the `minFreq` bucket; O(1) per op | |

## Follow-ups interviewers ask
Thread safety (single lock vs striping vs a library such as Caffeine), TTL expiry, size in bytes instead of entry count, write-through vs write-back, distributed cache (consistent hashing; see [system design](../../01-system-design/02-core-distributed-infra/README.md)).

## Checklist
- [ ] Write LRU with a manual doubly linked list in ≤ 20 min
- [ ] Explain why LFU needs `minFreq` and how it is updated
- [ ] Discuss tie-breaking in LFU (least frequent, then least recent)
