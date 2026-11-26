# Dynamic Programming & Tries

[← Back to DSA](../README.md)

**Pattern recap:** DP = overlapping subproblems + optimal substructure; define `dp[i]` precisely first, then the transition, then the base case. A **Trie** stores strings by shared prefixes, giving O(length) lookups and prefix queries; combine it with DP when a dictionary lookup is the inner step.

| Done | Problem | LeetCode | Difficulty | Key idea / hint | Solution |
|---|---|---|---|---|---|
| ☐ ⭐ | **Word Break** | 139 | Medium | `dp[i]` = prefix of length `i` is breakable; try each split `j < i` with `dp[j] && dict.contains(s[j..i))`; **Trie** speeds up the inner check; follow-up: Word Break II (140) with memoised DFS | |
| ☐ | Longest Increasing Subsequence | 300 | Medium | O(n²) DP first; then **patience sorting**: keep `tails[]` and binary-search the insert position for O(n log n) | |
| ☐ ⭐ | **Word Auto-Complete with a Trie** (frequency/weight ranking) | 642 | Hard | Trie where each node keeps a count; return the top K by (frequency desc, lexicographic). Memory optimisation: radix/compressed trie, store top-K per node, cap depth. Same problem as the [LLD autocomplete engine](../../04-low-level-design/08-keyboard-autocomplete/README.md) and the [HLD search autocomplete](../../01-system-design/04-storage-and-search/README.md) | |

## Related warm-up (optional)
Implement Trie (LeetCode 208) before the autocomplete problem.

## Edge cases to rehearse
Empty string, dictionary with repeated or overlapping words, very long strings (use a `HashSet` of word lengths to bound the inner loop), ties in frequency, unicode vs lowercase-only alphabet (array of 26 vs `HashMap` children).

## Checklist
- [ ] State `dp[i]` in words before writing any code
- [ ] Explain LIS patience sorting and why `tails` stays sorted
- [ ] Explain Trie memory trade-offs (array children vs map vs compressed)
