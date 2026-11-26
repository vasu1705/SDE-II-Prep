# Arrays, Sliding Window & Two Pointers

[← Back to DSA](../README.md)

**Pattern recap:** *two pointers* shrink a search space using order or symmetry; *sliding window* keeps a running summary of a contiguous range; *prefix/running state* (Kadane) turns "best over all subarrays" into one pass. Ask first: **is the input sorted, and do I need a contiguous range?**

| Done | Problem | LeetCode | Difficulty | Key idea / hint | Solution |
|---|---|---|---|---|---|
| ☐ ⭐ | **Trapping Rain Water** | 42 | Hard | Water above `i` = `min(maxLeft, maxRight) - h[i]`. Two pointers with running `leftMax`/`rightMax` (O(n) time, O(1) space); alternative: monotonic stack | |
| ☐ | Two Sum (HashMap) | 1 | Easy | Store `value → index`; look up the complement as you go | |
| ☐ | Two Sum II (sorted array) | 167 | Medium | Two pointers from both ends | |
| ☐ | 3Sum / 4Sum / K-Sum | 15, 18 | Medium | Sort, fix one (or more), two pointers for the rest; skip duplicates; generalise with recursion | |
| ☐ | Maximum Subarray (Kadane) | 53 | Medium | `best = max(x, best + x)`; variations: return the indices, circular array (918) | |
| ☐ | Maximum Product Subarray | 152 | Medium | Track both running **max and min** (a negative flips them) | |
| ☐ | Longest Substring Without Repeating Characters | 3 | Medium | Sliding window + last-seen index map; move `left` to `lastSeen + 1` | |
| ☐ | Minimum Window Substring | 76 | Hard | Window with `need`/`have` counts and a `formed` counter; expand right, shrink left while valid | |

## Edge cases to rehearse
Empty array, single element, all negatives (Kadane), duplicates (K-Sum), integer overflow in sums/products, window larger than the input.

## Checklist
- [ ] Explain why Trapping Rain Water two-pointer is correct (the smaller side is the binding side)
- [ ] State when sliding window fails (negative numbers in "sum ≥ K" problems)
- [ ] Solve every row above in ≤ 25 min
