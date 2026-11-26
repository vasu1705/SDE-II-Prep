# Graphs & Trees

[← Back to DSA](../README.md)

**Pattern recap:** BFS finds shortest paths in *unweighted* graphs; DFS explores structure and detects cycles; topological sort orders a DAG (Kahn's algorithm with in-degrees, or DFS finish order). Copying a graph needs an **old → new map** so shared and cyclic nodes are copied once. Java: `ArrayDeque` for BFS, recursion or an explicit stack for DFS.

| Done | Problem | LeetCode | Difficulty | Key idea / hint | Solution |
|---|---|---|---|---|---|
| ☐ ⭐ | **Clone Graph** | 133 | Medium | DFS/BFS with `HashMap<Node, Node>` (old → new); create the clone before recursing so cycles terminate | |
| ☐ ⭐ | Clone with random pointers (variation) | 138 | Medium | *Copy List with Random Pointer*: map old → new, or interleave copies in the list (O(1) space). (Interpretation of "random pointers variation": confirm with the original post) | |
| ☐ | Detect a Cycle in a Directed Graph | core of 207 | Medium | DFS with three colours (white/grey/black): a back edge to a grey node is a cycle; or Kahn's algorithm (processed count < n) | |
| ☐ | Course Schedule (and II: return the order) | 207, 210 | Medium | Build adjacency list + in-degrees; Kahn's BFS; cycle means impossible | |
| ☐ | Word Ladder | 127 | Hard | BFS over words; neighbours via wildcard buckets (`h*t`); **bidirectional BFS** to cut the frontier | |
| ☐ | Serialize and Deserialize a Binary Tree | 297 | Hard | Preorder with null markers (and a delimiter), or level-order; deserialize with an index/queue | |

## Edge cases to rehearse
Null/empty graph, a single node, self-loops, disconnected components, duplicate edges, a very deep tree (recursion depth), `null` markers in serialization, word not in dictionary.

## Checklist
- [ ] Explain why BFS (not DFS) gives the shortest path in Word Ladder
- [ ] Detect a cycle two ways (colours and Kahn's) and say when each is simpler
- [ ] Write an iterative DFS for a deep tree
