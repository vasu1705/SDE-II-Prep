# Binary Search

[← Back to DSA](../README.md)

**Pattern recap:** binary search works on any **monotonic predicate**, not just sorted arrays. *Search on answer:* guess a value, test "is it feasible?" in O(n), and the feasible values form a boundary. *Partition search* (median of two arrays) binary-searches a **cut position**, not a value.

| Done | Problem | LeetCode | Difficulty | Key idea / hint | Solution |
|---|---|---|---|---|---|
| ☐ ⭐ | **Median of Two Sorted Arrays** | 4 | Hard | Binary search the partition on the **smaller** array so left halves have `(m+n+1)/2` elements and `maxLeft ≤ minRight` on both sides; O(log(min(m,n))) | |
| ☐ | Capacity to Ship Packages Within D Days (search on answer) | 1011 | Medium | Range `[max(weights), sum(weights)]`; feasibility = greedy day count ≤ D | |
| ☐ | Koko Eating Bananas (search on answer) | 875 | Medium | Range `[1, max(pile)]`; feasibility = sum of `ceil(pile/speed)` ≤ H | |
| ☐ | Split Array Largest Sum (search on answer) | 410 | Hard | Same shape as shipping packages: minimise the maximum segment sum | |

## Template to memorise
```text
lo, hi = smallest possible answer, largest possible answer
while lo < hi:
    mid = lo + (hi - lo) / 2          # avoid overflow
    if feasible(mid): hi = mid        # answer is mid or smaller
    else:             lo = mid + 1
return lo
```

## Edge cases to rehearse
Empty or one-element arrays, one array empty (median), duplicates, even vs odd total length, `int` overflow in `lo + hi`, infinite loop from the wrong `mid` rounding.

## Checklist
- [ ] Explain why the feasibility predicate must be monotonic
- [ ] Write the lower-bound and upper-bound variants without looking
- [ ] Explain why partitioning on the smaller array avoids out-of-bounds
