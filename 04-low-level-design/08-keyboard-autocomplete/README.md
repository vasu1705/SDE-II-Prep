# LLD 8 — Keyboard Auto-Complete Engine

[← Back to LLD](../README.md) · Status: ☐ not started

## Requirements
- `insert(word)` / `record(word)` increments usage; `suggest(prefix, k)` returns the top-K completions.
- **Ranking** by frequency/weight (ties broken alphabetically or by recency).
- Memory-conscious for a large dictionary; safe under concurrent reads and occasional writes.

## Design choices to compare
| Choice | Idea | Trade-off |
|---|---|---|
| Plain Trie, collect all words under the prefix, then sort | simplest | slow for popular prefixes |
| **Store top-K at every node** | `suggest` is O(prefix length) | more memory, updates must refresh ancestors |
| Compressed (radix) Trie | merge single-child chains | far less memory, more complex insert |
| Child storage: `array[26]` vs `HashMap` vs sorted list | speed vs memory | array wastes space on sparse nodes |

## Same problem, three levels
- DSA version: [Word Auto-Complete with a Trie](../../03-dsa/05-dp-and-tries/README.md)
- LLD version (this folder): clean classes, ranking strategy, thread-safety
- HLD version: [Search autocomplete at scale](../../01-system-design/04-storage-and-search/README.md) (cache hot prefixes, offline aggregation, sharding)

## Patterns & concurrency
- **Strategy** for ranking (frequency, recency, personalisation); immutable snapshots (copy-on-write trie) for lock-free reads vs a read-write lock.

## Test checklist
- [ ] Prefix with no matches; prefix equal to a whole word; empty prefix
- [ ] Ranking order and tie-breaks; K larger than the matches
- [ ] Frequency update changes the order of suggestions

## Solution
_(add `src/` and links here)_
