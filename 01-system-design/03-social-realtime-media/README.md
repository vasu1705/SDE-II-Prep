# HLD — Social, Real-Time & Media

[← Back to System Design](../README.md)

| Done | System | Hardest part (deep dive) | Key concepts to cover |
|---|---|---|---|
| ☐ | Chat application (WhatsApp/Slack) | delivery guarantees and presence at scale | **WebSockets**, connection servers + routing table, message ids/ordering, offline storage & delivery, read receipts, group fan-out, end-to-end encryption overview |
| ☐ | Social media feed (Twitter/Instagram) | building a timeline fast | **fan-out on write vs fan-out on read** (and the hybrid for celebrities), feed cache, ranking, pagination, media via CDN |
| ☐ | Ride-hailing (Uber/Ola) | matching riders and drivers in real time | **geospatial indexing** (Quadtree / Geohash / S2), location update stream, matching, ETA, surge pricing, trip state machine |
| ☐ | Google Docs (collaborative editing) | concurrent edits converge | **OT vs CRDT**, operation log, cursors/presence, version history, offline merge |
| ☐ | Video streaming | smooth playback on any network | upload pipeline & transcoding, **HLS/DASH adaptive bitrate**, chunking, CDN, thumbnails/metadata |
| ☐ | Recommendation system | personalised results at low latency | candidate generation + ranking, offline training vs online serving, feature store, cold start, feedback loop |

## Checklist of concepts
- [ ] Push vs pull and when each wins  - [ ] Fan-out strategies and the celebrity problem
- [ ] Geohash vs Quadtree  - [ ] CRDT vs OT  - [ ] Adaptive bitrate streaming

## Links in this repo
[Virtual threads for many connections](../../02-languages/java/03-concurrency/05-virtual-threads.md) · [Notification system](../02-core-distributed-infra/README.md)
