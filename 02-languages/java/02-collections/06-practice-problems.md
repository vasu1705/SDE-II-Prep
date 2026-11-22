# Collections — Practice Problems

> **Level:** SDE-II / SDE-III · **Area:** Java · **Covers:** notes 01–05 of this section

Two parts: **A. Predict the output** (tests whether you *really* know the behaviour) and **B. Coding problems** (frequently asked, with the collection choice explained). Try before you expand.

---

## A. Predict the output

<details>
<summary><b>A1.</b> Fixed-size list</summary>

```java
List<Integer> l = Arrays.asList(1, 2, 3);
l.set(0, 9);
l.add(4);
```

`set` works, **`add` throws `UnsupportedOperationException`** — `Arrays.asList` is a fixed-size list backed by the array.
</details>

<details>
<summary><b>A2.</b> <code>remove(int)</code> vs <code>remove(Object)</code></summary>

```java
List<Integer> l = new ArrayList<>(List.of(3, 0, 1));
l.remove(1);
l.remove(Integer.valueOf(1));
System.out.println(l);
```

**`[3]`**. `remove(1)` picks the `remove(int index)` overload → removes the element at index 1 (the `0`) → `[3, 1]`. `remove(Integer.valueOf(1))` picks `remove(Object)` → removes the *value* 1 → `[3]`.
</details>

<details>
<summary><b>A3.</b> Priority queue printing</summary>

```java
PriorityQueue<Integer> pq = new PriorityQueue<>();
for (int x : new int[] {5, 1, 4, 2, 3}) pq.add(x);
System.out.println(pq);
```

**`[1, 2, 4, 5, 3]`** — that's the **heap array**, not sorted order. Only `poll()` is guaranteed to return elements in order.
</details>

<details>
<summary><b>A4.</b> Null keys</summary>

```java
Map<String,String> h = new HashMap<>();
h.put(null, "x");
System.out.println(h.get(null));
Map<String,String> c = new ConcurrentHashMap<>();
c.put(null, "x");
```

`HashMap` prints **`x`** (null key lives in bucket 0). `ConcurrentHashMap.put(null, …)` throws **`NullPointerException`**.
</details>

<details>
<summary><b>A5.</b> Mutable list as a key</summary>

```java
List<Integer> key = new ArrayList<>(List.of(1));
Map<List<Integer>, String> m = new HashMap<>();
m.put(key, "v");
key.add(2);
System.out.println(m.get(key) + " " + m.get(List.of(1, 2)) + " " + m.get(List.of(1)) + " " + m.size());
```

**`null null null 1`**. The entry was filed under the hash of `[1]`. Looking up `[1,2]` computes another hash (miss); looking up `[1]` finds the right bucket but `[1].equals([1,2])` is false (miss). The entry is a ghost: size is still 1.
</details>

<details>
<summary><b>A6.</b> <code>Arrays.asList</code> and primitive arrays</summary>

```java
System.out.println(Arrays.asList(new int[] {1, 2, 3}).size());
System.out.println(Arrays.asList(new Integer[] {1, 2, 3}).size());
```

**`1` then `3`**. `int[]` is a single object, so you get `List<int[]>`. `Integer[]` is an `Object[]`, so it's spread as the varargs.
</details>

<details>
<summary><b>A7.</b> Recursive memoisation with <code>computeIfAbsent</code></summary>

```java
static Map<Integer,Long> memo = new HashMap<>();
static long fib(int n) {
    if (n < 2) return n;
    return memo.computeIfAbsent(n, k -> fib(k - 1) + fib(k - 2));
}
// fib(10)
```

Throws **`ConcurrentModificationException`** (Java 9+). The mapping function modifies the same map. Fix: check `memo.get(n)` first, compute, then `put`, or use an array/DP.
</details>

<details>
<summary><b>A8.</b> The <code>Set&lt;Short&gt;</code> puzzle</summary>

```java
Set<Short> s = new HashSet<>();
for (short i = 0; i < 5; i++) { s.add(i); s.remove(i - 1); }
System.out.println(s.size());
```

**`5`**. `i - 1` is an `int`, so it autoboxes to `Integer`; `remove(Object)` never finds a `Short` equal to an `Integer`. (`Short.equals(Integer)` is always `false`.)
</details>

<details>
<summary><b>A9.</b> Case-insensitive <code>TreeMap</code></summary>

```java
Map<String,Integer> m = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
m.put("A", 1); m.put("a", 2);
System.out.println(m);
```

**`{A=2}`** — the comparator says `"A"` and `"a"` are the same key; the **first key object is kept**, the value is overwritten.
</details>

<details>
<summary><b>A10.</b> Removing while iterating</summary>

```java
List<Integer> l = new ArrayList<>(List.of(1, 2, 3, 4));
for (Integer x : l) if (x == 3) l.remove(x);   // (a)
```

(a) **Does not throw** — removing the *second-to-last* element makes `hasNext()` return `false` (`cursor == size`), so `next()` (where the check lives) is never called. Remove `2` or `4` instead and you get `ConcurrentModificationException`. Moral: it's a bug either way; use `removeIf`.
</details>

---

## B. Coding problems

### 1. LRU cache from scratch

*Constraint:* O(1) `get`/`put`, and "you may not use `LinkedHashMap`".

**Idea:** `HashMap<K, Node>` for O(1) lookup + **doubly linked list** ordered by recency. Sentinel `head`/`tail` nodes remove all null-edge cases.

```java
// Run: LruFromScratch.java
import java.util.*;

public class LruFromScratch {
    static class LRU<K, V> {
        private class Node { K key; V val; Node prev, next; Node(K k, V v) { key = k; val = v; } }

        private final int capacity;
        private final Map<K, Node> index = new HashMap<>();
        private final Node head = new Node(null, null), tail = new Node(null, null); // sentinels

        LRU(int capacity) { this.capacity = capacity; head.next = tail; tail.prev = head; }

        V get(K key) {
            Node n = index.get(key);
            if (n == null) return null;
            unlink(n); addFirst(n);                    // now most-recent
            return n.val;
        }

        void put(K key, V val) {
            Node n = index.get(key);
            if (n != null) { n.val = val; unlink(n); addFirst(n); return; }
            if (index.size() == capacity) {            // evict least-recent = node before tail
                Node lru = tail.prev;
                unlink(lru); index.remove(lru.key);
            }
            n = new Node(key, val);
            index.put(key, n); addFirst(n);
        }

        private void unlink(Node n) { n.prev.next = n.next; n.next.prev = n.prev; }
        private void addFirst(Node n) { n.next = head.next; n.prev = head; head.next.prev = n; head.next = n; }

        @Override public String toString() {           // most -> least recent
            StringBuilder sb = new StringBuilder("[");
            for (Node n = head.next; n != tail; n = n.next) sb.append(n.key).append(n.next != tail ? ", " : "");
            return sb.append("]").toString();
        }
    }

    public static void main(String[] args) {
        LRU<String,Integer> c = new LRU<>(2);
        c.put("a", 1); c.put("b", 2);
        System.out.println(c.get("a"));    // 1  (a is now most recent)
        c.put("c", 3);                     // evicts b
        System.out.println(c.get("b"));    // null
        System.out.println(c);             // [c, a]
    }
}
```

Follow-ups: thread safety (lock per cache vs striped), TTL (store expiry; lazy eviction on read), LFU (frequency buckets: `Map<Integer, LinkedHashSet<K>>` + `minFreq`).

### 2. Implement `HashMap` (separate chaining)

*The interviewer wants:* hash spreading, index mask, chain search with `hash` then `equals`, resize with rehash, `null` key handling.

```java
// Run: MyHashMapDemo.java
import java.util.*;

public class MyHashMapDemo {
    static class MyHashMap<K, V> {
        private static class Node<K, V> {
            final int hash; final K key; V value; Node<K, V> next;
            Node(int hash, K key, V value, Node<K, V> next) { this.hash = hash; this.key = key; this.value = value; this.next = next; }
        }
        private Node<K, V>[] table;
        private int size;

        @SuppressWarnings("unchecked")
        MyHashMap() { table = (Node<K, V>[]) new Node[16]; }

        private static int hash(Object k) { int h = (k == null) ? 0 : k.hashCode(); return h ^ (h >>> 16); }

        V put(K key, V value) {
            int h = hash(key), i = (table.length - 1) & h;
            for (Node<K, V> n = table[i]; n != null; n = n.next)
                if (n.hash == h && Objects.equals(n.key, key)) { V old = n.value; n.value = value; return old; }
            table[i] = new Node<>(h, key, value, table[i]);          // insert at head of the chain
            if (++size > table.length * 0.75) resize();
            return null;
        }

        V get(Object key) {
            int h = hash(key);
            for (Node<K, V> n = table[(table.length - 1) & h]; n != null; n = n.next)
                if (n.hash == h && Objects.equals(n.key, key)) return n.value;
            return null;
        }

        V remove(Object key) {
            int h = hash(key), i = (table.length - 1) & h;
            Node<K, V> prev = null;
            for (Node<K, V> n = table[i]; n != null; prev = n, n = n.next) {
                if (n.hash == h && Objects.equals(n.key, key)) {
                    if (prev == null) table[i] = n.next; else prev.next = n.next;
                    size--; return n.value;
                }
            }
            return null;
        }

        @SuppressWarnings("unchecked")
        private void resize() {
            Node<K, V>[] old = table;
            table = (Node<K, V>[]) new Node[old.length * 2];
            for (Node<K, V> head : old)
                for (Node<K, V> n = head; n != null; ) {
                    Node<K, V> next = n.next;
                    int i = (table.length - 1) & n.hash;             // hash is cached: no recomputation
                    n.next = table[i]; table[i] = n;
                    n = next;
                }
        }
        int size() { return size; }
        int capacity() { return table.length; }
    }

    public static void main(String[] args) {
        MyHashMap<Object, Integer> m = new MyHashMap<>();
        for (int i = 0; i < 1000; i++) m.put("k" + i, i);
        m.put(null, -1);
        System.out.println("size=" + m.size() + " capacity=" + m.capacity());   // size=1001 capacity=2048
        System.out.println(m.get("k500") + " " + m.get(null) + " " + m.get("nope"));
        for (int i = 0; i < 500; i++) m.remove("k" + i);
        System.out.println("size after removing 500 = " + m.size());
    }
}
```

Discussion points: treeification (not implemented), iteration, `Iterable` + fail-fast `modCount`, thread safety, why `final int hash`.

### 3. Group anagrams

*Collection choice:* `Map<String, List<String>>`, key = canonical form. Use `LinkedHashMap` if the output order matters.

```java
// Run: GroupAnagrams.java
import java.util.*;

public class GroupAnagrams {
    static List<List<String>> group(String[] words) {
        Map<String, List<String>> groups = new LinkedHashMap<>();
        for (String w : words) {
            char[] cs = w.toCharArray();
            Arrays.sort(cs);                                    // O(k log k) key
            groups.computeIfAbsent(new String(cs), k -> new ArrayList<>()).add(w);
        }
        return new ArrayList<>(groups.values());
    }

    public static void main(String[] args) {
        System.out.println(group(new String[] {"eat", "tea", "tan", "ate", "nat", "bat"}));
        // [[eat, tea, ate], [tan, nat], [bat]]
    }
}
```

Optimisation to mention: build the key from a 26-int frequency array (`Arrays.toString(counts)` or a `#`-joined string) → `O(n·k)` instead of `O(n·k log k)`. Never use `char[]` as a key directly (identity `hashCode`).

### 4. Top-K frequent elements

*Collection choice:* `HashMap` for counts + **min-heap of size k** (`PriorityQueue`) → `O(n log k)`.

```java
// Run: TopK.java
import java.util.*;

public class TopK {
    static List<Integer> topK(int[] nums, int k) {
        Map<Integer, Integer> freq = new HashMap<>();
        for (int n : nums) freq.merge(n, 1, Integer::sum);

        PriorityQueue<Map.Entry<Integer, Integer>> heap =
            new PriorityQueue<>(Comparator.comparingInt(Map.Entry::getValue));   // min-heap by count
        for (Map.Entry<Integer, Integer> e : freq.entrySet()) {
            heap.offer(e);
            if (heap.size() > k) heap.poll();                  // drop the least frequent so far
        }
        List<Integer> out = new ArrayList<>();
        while (!heap.isEmpty()) out.add(heap.poll().getKey()); // ascending frequency
        Collections.reverse(out);
        return out;
    }

    public static void main(String[] args) {
        System.out.println(topK(new int[] {1, 1, 1, 2, 2, 3}, 2));   // [1, 2]
    }
}
```

Alternatives: bucket sort by frequency `O(n)`; quickselect average `O(n)`.

### 5. First non-repeating character

*Collection choice:* `LinkedHashMap` keeps first-seen order; the first entry with count 1 wins.

```java
// Run: FirstUnique.java
import java.util.*;

public class FirstUnique {
    static int firstUniqueIndex(String s) {
        Map<Character, Integer> counts = new LinkedHashMap<>();
        for (char c : s.toCharArray()) counts.merge(c, 1, Integer::sum);
        for (Map.Entry<Character, Integer> e : counts.entrySet())
            if (e.getValue() == 1) return s.indexOf(e.getKey());
        return -1;
    }

    public static void main(String[] args) {
        System.out.println(firstUniqueIndex("leetcode"));      // 0 (l)
        System.out.println(firstUniqueIndex("loveleetcode"));  // 2 (v)
        System.out.println(firstUniqueIndex("aabb"));          // -1
    }
}
```

For ASCII-only input an `int[26]`/`int[128]` is faster and simpler — mention it, then explain why the map is the general solution (Unicode).

### 6. Subarray sum equals K (prefix-sum + HashMap)

*Insight:* `sum(i..j) = prefix[j] - prefix[i-1]`. We need earlier prefixes equal to `prefix[j] - k`. Count how often each prefix appeared.

```java
// Run: SubarraySumK.java
import java.util.*;

public class SubarraySumK {
    static int count(int[] nums, int k) {
        Map<Integer, Integer> seen = new HashMap<>();
        seen.put(0, 1);                       // empty prefix
        int prefix = 0, ans = 0;
        for (int n : nums) {
            prefix += n;
            ans += seen.getOrDefault(prefix - k, 0);
            seen.merge(prefix, 1, Integer::sum);
        }
        return ans;
    }

    public static void main(String[] args) {
        System.out.println(count(new int[] {1, 2, 3}, 3));      // 2  -> [1,2], [3]
        System.out.println(count(new int[] {1, -1, 0}, 0));     // 3  -> [1,-1], [0], [1,-1,0]
    }
}
```

`O(n)` time, `O(n)` space. Sliding window does **not** work here because of negative numbers.

---

## C. Rapid-fire (answer out loud)

- Why is `HashMap` capacity a power of two?
- What's the cost of `new ArrayList<>(list)` vs `new LinkedList<>(list)`?
- How would you get a sorted view of a `HashMap`'s keys? (`new TreeMap<>(map)` / `stream().sorted()`; cost `O(n log n)`.)
- What's the difference between `Iterator` and `ListIterator`? (bidirectional, `set`, `add`, indices.)
- Which collection would you use for: a task scheduler by deadline? (`PriorityQueue`) · a sliding-window maximum? (`ArrayDeque` as monotonic deque) · de-duplicating while preserving order? (`LinkedHashSet`) · counting enum occurrences? (`EnumMap`) · an interval/booking lookup? (`TreeMap`).

---
[↑ Back to Collections index](README.md)
