# HLD — Storage & Search

[← Back to System Design](../README.md)

| Done | System | Hardest part (deep dive) | Key concepts to cover |
|---|---|---|---|
| ☐ | File storage (Dropbox/Google Drive) | efficient sync of large files | **chunking** and content hashing, **deduplication**, metadata DB vs blob store, delta sync, resumable uploads, versioning, sharing/permissions, conflict resolution |
| ☐ ⭐ | **Search autocomplete (Google)** | sub-100 ms suggestions for billions of queries | **distributed Trie** (or prefix index), top-K per prefix, **caching hot prefixes**, offline aggregation of query logs, sharding by prefix, freshness vs cost, personalisation and filtering |

## Search autocomplete — one problem, three levels
- DSA: [Word Auto-Complete with a Trie](../../03-dsa/05-dp-and-tries/README.md)
- LLD: [Keyboard Auto-Complete Engine](../../04-low-level-design/08-keyboard-autocomplete/README.md)
- HLD: this folder (scale, sharding, caching, data pipeline)

## Checklist of concepts
- [ ] Chunking + dedup (content-addressed storage)  - [ ] Metadata vs blob separation
- [ ] Trie sharding and hot-prefix cache  - [ ] Offline pipeline for query aggregation
