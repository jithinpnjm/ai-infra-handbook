---
id: "c20-09"
title: "20.9 Algorithm patterns for SRE-flavoured problems"
sidebar_label: "20.9 Algorithm patterns for SRE problems"
sidebar_position: 9
description: "Sixteen algorithm patterns that appear in SRE coding rounds, each with the idea in plain words, a tested Python template, its complexity measured where practical, the operations situation it models, the variations an interviewer adds and the bug that sinks candidates."
status: "drafted"
tier: "1"
level: "I"
lab_venue: "Laptop / Docker"
---

# 20.9 Algorithm patterns for SRE-flavoured problems

## What the interviewer is testing

The interviewer pastes a link to a shared editor and says: "Here is a log file with a few million lines. Tell me which endpoints are slowest, and which ones have been failing in the last five minutes." Picture the cursor blinking in an empty file. The log is too big to open in an editor, the clock is running, and you need a method before you need a line of code. This chapter serves the coding round. Nebius states that the process includes at least one practical coding, algorithms or data-structures task. It also says you may use any language, should say your reasoning aloud, ask for hints and review your code before submitting.

One candidate reported two LeetCode easy-to-medium problems in a one-hour round. Nebius has not published its problems, so this chapter does not guess a list. It teaches the patterns behind most easy and medium problems, framed as SRE situations. The point is not to memorise every answer. The point is to recognise the shape of a problem quickly and to know the template that fits it.

A realistic question in the interviewer's voice: "Implement a rate limiter that allows 100 requests per minute per API key. Then tell me what happens at the window boundary, and how you would change it to allow bursts."



## The core ideas

Every section below has the same parts. First the situation, then the idea in plain words, then a template you can type from memory. After the template come its cost, the SRE setting, the follow-up an interviewer adds, and the bug that most often sinks the answer. Read the situation first, because it tells you which question the interviewer is really asking. All code is in `code/part20/` with the prefix `c09_`, and the blocks here are exact copies of the files. The tests carry the prefix `test_c09_`.

![The core ideas](./img/m20-09-1.svg)

*Figure 20.9.1. The core ideas, as a diagram.*



| Pattern | Typical cost | SRE setting |
|---|---|---|
| Hash-map aggregation | O(n) time, O(distinct keys) memory | Log analysis, cardinality |
| Sliding window with deque | O(n) time, O(window) memory | Rolling error rate, peak in window |
| Two pointers | O(n) time, O(1) memory | Merging sorted logs, pairing values |
| Heap top-k | O(n log k) time, O(k) memory | Slowest endpoints, merging streams |
| Interval merge and sweep | O(n log n) time | Maintenance windows, GPU reservations |
| Rate limiters | O(1) per request for three of four | API quotas |
| LRU cache | O(1) per operation | Prefix and metadata caches |
| Consistent hashing | O(log N) lookup with N ring points | Sticky routing, sharding |
| Backoff with jitter | O(1) per retry | Client resilience |
| Topological sort | O(V + E) | Start order, Terraform-like plans |
| BFS and DFS | O(V + E) | Blast radius, network paths |
| Union-find | near O(1) per operation, amortised | Clusters of failing nodes |
| Binary search on the answer | O(log range) checks | Capacity and timeout tuning |
| Streaming percentiles | O(1) or O(buckets) memory | Latency SLIs |

### 1. Log parsing and aggregation with hash maps

A service writes one line per request. Your manager wants error rate and total time per endpoint from a file too large to load. The idea is a single pass. Read one line at a time, update a dictionary keyed by endpoint, and never keep the lines. Learning Python, chapter 14, explains why: iterating over a file object reads one line at a time and avoids the memory problem of loading everything with `readlines`. The file stays on disk, and only the running totals stay in memory.

Walk through the first pass in your head. The loop takes one line, asks the parser for a record, and either counts it as bad or adds it to the running totals for its endpoint. Then the loop moves on, and the earlier line is gone from memory. The only thing that grows is the dictionary, and it grows with endpoints, which is the number you want to stay small.

Two details matter. Real logs contain garbage, so the parser returns `None` for a bad line and the caller counts it instead of crashing. A crash in the middle of a large file loses the work already done, while a counted bad line costs one increment. And counts need a default, which `defaultdict` or `Counter` supplies, as Fluent Python, chapter 3, shows. Without the default, the first time you see a new endpoint the code would fail, and that failure would only show up on the busy path.

```python
"""Log parsing and aggregation with hash maps."""
from collections import Counter, defaultdict


def parse_line(line):
    """Parse 'ts method path status latency_ms'. Return a dict or None if malformed."""
    parts = line.split()
    if len(parts) != 5:
        return None
    ts, method, path, status, ms = parts
    try:
        return {"ts": int(ts), "method": method, "path": path,
                "status": int(status), "ms": float(ms)}
    except ValueError:
        return None


def aggregate(lines):
    """One pass. Return (stats per path, number of malformed lines)."""
    stats = defaultdict(lambda: {"n": 0, "errors": 0, "ms_total": 0.0})
    bad = 0
    for line in lines:
        rec = parse_line(line)
        if rec is None:
            bad += 1
            continue
        s = stats[rec["path"]]
        s["n"] += 1
        s["errors"] += rec["status"] >= 500
        s["ms_total"] += rec["ms"]
    return dict(stats), bad


def error_rate(stat):
    return stat["errors"] / stat["n"] if stat["n"] else 0.0


def top_paths(lines, k):
    """The k most frequent paths, ties broken by path name so output is stable."""
    counts = Counter(rec["path"] for rec in map(parse_line, lines) if rec)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]


def first_duplicate_request_id(ids):
    """Return the first id that was already seen, else None. O(n) with a set."""
    seen = set()
    for i in ids:
        if i in seen:
            return i
        seen.add(i)
    return None
```

The cost is O(n) time and memory proportional to the number of distinct paths, not lines. That second part is where the SRE angle lives. If you key by raw URL and the URL contains a user id, the dictionary grows without bound. Each new user adds a new key, and memory grows with the user base instead of with the handful of routes your service really has. Chapter 20.15 covers the same problem as metric cardinality. The helper `collapse_ids` in the strings section shows the usual fix, which is to replace the ids with a placeholder before you use the path as a key.

A concrete case makes the risk clear. Suppose the service puts a customer id in the path, and every customer makes a few requests a day. After a month the dictionary holds one entry per customer, not one per route, and every report has to scan all of them. Collapsing the ids keeps the dictionary the size the product actually needs.





Decide: if the question says "per" something, reach for a dictionary first and say what the key is. The key is the answer to "per what", and naming it out loud shows the interviewer you understood the question before you wrote any code.

### 2. Sliding windows: rolling error rate and the maximum in a window

![A deque of indexes in decreasing value order where a new value pops all smaller values from the back, the front index leaves when it falls out of the window, and the front is the maximum.](./img/p3-2009-monotonic-deque.svg)

*Figure 20.9.2. Each index is appended once and removed once, so the work is O(n) even though there is a loop inside a loop.*

![A rolling window keeps recent events in a deque, appending on the right and evicting old events from the left.](./img/x09-sliding-window-eviction.svg)

*Figure 20.9.3. A sliding window appends new events on one end and evicts old events from the other end, so each event enters and leaves once.*

An alert should fire when the error rate over the last five minutes exceeds one percent. Events arrive in time order, and the alert runs all day. The naive approach recounts the window on every event, which is wasteful when most events are the same as the last check. The better idea is to keep the events in a queue, add the new one on the right, and drop the old ones from the left, adjusting a running total as you go. The window slides along the stream, which is where the name comes from.

Use `collections.deque` for the queue. Fluent Python, chapter 2, says a deque is the more efficient first-in first-out structure than a list, because popping from the front of a list shifts every element. A deque removes from either end without moving the rest, so the eviction step stays cheap no matter how long the window grows.

The reason the deque matters is easy to see with a small picture. A list stores its items side by side, so removing the first one means sliding every other item one place along. A deque is built so that both ends are cheap, and the sliding never happens.

```python
"""Sliding windows: rolling error rate and max in a window, both with a deque."""
from collections import deque


class RollingErrorRate:
    """Error rate over the last `window_s` seconds. Events must arrive in time order."""

    def __init__(self, window_s):
        self.window_s = window_s
        self.events = deque()   # (timestamp, is_error)
        self.errors = 0

    def _evict(self, now):
        # Keep events with now - window_s < ts, so the window is half-open.
        while self.events and self.events[0][0] <= now - self.window_s:
            _, was_error = self.events.popleft()
            self.errors -= was_error

    def add(self, ts, is_error):
        self.events.append((ts, bool(is_error)))
        self.errors += bool(is_error)
        self._evict(ts)

    def rate(self, now):
        self._evict(now)
        return self.errors / len(self.events) if self.events else 0.0


def sliding_max(values, k):
    """Maximum of every window of k values. The deque holds indexes of decreasing values."""
    if k <= 0:
        raise ValueError("k must be positive")
    dq, out = deque(), []
    for i, v in enumerate(values):
        while dq and values[dq[-1]] <= v:
            dq.pop()                    # smaller older values can never be a max again
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()                # front index fell out of the window
        if i >= k - 1:
            out.append(values[dq[0]])
    return out


def sliding_max_naive(values, k):
    return [max(values[i:i + k]) for i in range(len(values) - k + 1)]


def longest_run_below(values, limit):
    """Longest stretch whose sum stays <= limit (all values >= 0). Variable window."""
    best = left = total = 0
    for right, v in enumerate(values):
        total += v
        while total > limit:
            total -= values[left]
            left += 1
        best = max(best, right - left + 1)
    return best
```

The second function is the classic follow-up: the maximum of every window of k values. The deque stores indexes of values in decreasing order. When a new value arrives, every smaller value at the back can never be the maximum again, so you pop them. Each index enters and leaves once, so the work is O(n) even though there is a loop inside a loop. Picture a line of people waiting for a lift, where anyone shorter than a newcomer will never be the tallest while the newcomer stays in the window.

A timing on a Mac with Python 3.12.7 and window size 1,000 shows the claim. The deque version took 0.0012, 0.0028 and 0.0052 seconds for 10,000, 20,000 and 40,000 values. The naive version took 0.0567, 0.1184 and 0.2495 seconds. Doubling n doubles both, as it should for fixed k, but the naive one pays a factor of about k. That is a timing on one machine, not a guarantee, and the ratio is the part worth remembering.

When you read a timing like this, look for the ratio and the trend, and forget the exact digits. The trend says the naive method slows down in step with the window size, while the deque method does not. That is the claim the interviewer will care about, and a timing on your own machine will show the same shape with different digits.



The common bugs are off-by-one on the boundary and the empty window. In the test file the event exactly ten seconds old is out of a ten-second window, and the rate of an empty window is zero. Say your boundary choice aloud: "I treat the window as half-open, so an event exactly W seconds old is dropped." A half-open window includes its start and excludes its end, and that one sentence tells the interviewer you have thought about the edge.

Decide: if the question is about "the last N items" or "the last T seconds", it is a window, and your first sentence is whether it is half-open. Half-open or closed is the first question a careful engineer asks about any time range.

### 3. Two pointers

![Two pointers move inward over a sorted list, moving one pointer depending on whether the pair sum is too big or too small.](./img/p2-2009-two-pointers.svg)

*Figure 20.9.4. Two pointers walk inward over a sorted list, moving the pointer that the sum comparison says can help.*

Two sorted lists of timestamps come from two servers, and you want one merged timeline. Or you want two values in a sorted list of latencies that sum to a budget. The idea is to put one pointer at each relevant position and move the one that the comparison tells you to move. Sortedness is what makes the move safe, because it tells you which pointer can never help again. Picture two people walking up a staircase from opposite ends, each stepping only when the step they stand on is the wrong one.

```python
"""Two pointers on sorted data."""


def two_sum_sorted(a, target):
    """Indexes (i, j), i < j, with a[i] + a[j] == target in sorted a, else None."""
    i, j = 0, len(a) - 1
    while i < j:
        s = a[i] + a[j]
        if s == target:
            return i, j
        if s < target:
            i += 1
        else:
            j -= 1
    return None


def merge_sorted(a, b):
    """Merge two sorted lists, stable: on ties the element from a goes first."""
    out, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i]); i += 1
        else:
            out.append(b[j]); j += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out


def dedupe_in_place(a):
    """Remove duplicates from sorted list a in place. Return the new length."""
    if not a:
        return 0
    write = 1
    for read in range(1, len(a)):
        if a[read] != a[write - 1]:
            a[write] = a[read]
            write += 1
    del a[write:]
    return write


def common_sorted(a, b):
    """Sorted list of values present in both sorted lists, each value once."""
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] < b[j]:
            i += 1
        elif a[i] > b[j]:
            j += 1
        else:
            if not out or out[-1] != a[i]:
                out.append(a[i])
            i += 1
            j += 1
    return out
```

Every function is O(n) time and O(1) extra memory, apart from the output. The in-place dedupe uses a read pointer and a write pointer and finishes with a `del` of the tail. The pattern shows up in SRE work whenever data is already sorted and you want to avoid building a second copy of it.



Decide: if the input is sorted and you are about to write a nested loop, stop and ask whether two pointers remove the inner loop. A nested loop over sorted data is usually the first sign that the sort is being wasted.

### 4. Heaps and top-k

![A min-heap of size k holds the current top k slowest samples with the fastest of them at the root, and each new sample either replaces the root or is dropped.](./img/p3-2009-heap-topk.svg)

*Figure 20.9.5. The heap never holds more than k items however long the stream runs, so memory stays at O(k).*

The question is "which ten endpoints are slowest" over ten million samples. Sorting everything costs O(n log n) and holds everything in memory. The idea is a min-heap of size k. The root is the weakest member of the current top k. A new sample either beats the root and replaces it, or is ignored. The heap never holds more than k items, however long the stream runs.

Picture the heap during a run. The first ten samples fill it, and the root holds the fastest of them. Each later sample is compared with the root. A slow sample pushes out the fastest one in the heap, and a fast sample is dropped at once. At the end, the heap holds the ten slowest, and sorting those ten is cheap.

```python
"""Heaps: top-k and merging k sorted streams."""
import heapq


def top_k_slowest(samples, k):
    """samples: iterable of (endpoint, ms). Return the k slowest, slowest first.

    Keeps a min-heap of size k, so memory is O(k) and time is O(n log k).
    """
    if k <= 0:
        return []
    heap = []  # (ms, endpoint): the root is the fastest of the current top k
    for endpoint, ms in samples:
        item = (ms, endpoint)
        if len(heap) < k:
            heapq.heappush(heap, item)
        elif item > heap[0]:
            heapq.heapreplace(heap, item)
    return [(e, ms) for ms, e in sorted(heap, reverse=True)]


def merge_k_sorted(streams):
    """Merge k sorted iterables lazily. Heap entries carry the stream index as tiebreak."""
    heap = []
    iters = [iter(s) for s in streams]
    for idx, it in enumerate(iters):
        for first in it:
            heap.append((first, idx))
            break
    heapq.heapify(heap)
    while heap:
        value, idx = heap[0]
        yield value
        nxt = next(iters[idx], heap)     # sentinel: the heap itself
        if nxt is heap:
            heapq.heappop(heap)
        else:
            heapq.heapreplace(heap, (nxt, idx))


class RunningMedian:
    """Median of a stream with two heaps. O(log n) add, O(1) read."""

    def __init__(self):
        self.low = []    # max-heap by negation
        self.high = []   # min-heap

    def add(self, x):
        heapq.heappush(self.low, -x)
        heapq.heappush(self.high, -heapq.heappop(self.low))
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def median(self):
        if not self.low:
            raise ValueError("empty")
        if len(self.low) > len(self.high):
            return float(-self.low[0])
        return (-self.low[0] + self.high[0]) / 2
```

Time is O(n log k) and memory O(k). A measurement with k equal to 10 gives this. The heap took 0.0045 seconds for 100,000 samples and 0.0185 for 400,000. Sorting and slicing took 0.0154 and 0.0735. So the heap was three to four times faster here, but both grew linearly with n. Do not claim a dramatic speedup. The honest claim is the memory: the heap never holds more than k items, which matters on a stream that never ends.

The second function merges k sorted streams, such as the logs from k servers, lazily. The heap holds one head per stream. Pop the smallest, refill from the same stream. The stream index in the tuple is the tiebreaker, because Python compares tuples element by element and would otherwise try to compare two payloads that may not be comparable. The test proves laziness with an endless generator, because an eager merge would never return. Lazy means the function hands back one value at a time, so the merged log never has to fit in memory.





Decide: "best k" or "merge sorted inputs" means a heap, and you must say which end of the heap holds what. In a min-heap the root is the smallest value, and for a top-k problem that root is the one to compare against and replace.

### 5. Interval merging and scheduling

![A timeline comparison showing how taking the maximum end time prevents nested intervals from shrinking merged ranges, and how a cursor identifies free gaps between busy intervals.](./img/p4-2009-interval-merge.svg)

*Figure 20.0.0. Interval merging requires taking the maximum of the end boundaries so nested intervals do not truncate the merged range, while free slot detection advances a cursor through sorted gaps.*

Platform teams book maintenance windows and GPU reservations. Two questions follow. Which windows overlap, and how many nodes do we need if each reservation needs a whole node? The idea is to sort by start time and sweep once, keeping only what you must remember about the past. Think of a single list of bookings on a shared whiteboard, read from the top, with a note of which rooms are still in use.

A useful way to say the sweep is "I walk the timeline from left to right, and at each point I know how many things are running." That sentence is short, it names the state you keep, and it describes the sweep without any code.

```python
"""Interval merging and scheduling."""
import heapq


def merge_intervals(intervals):
    """Merge overlapping or touching [start, end] intervals."""
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)   # max: the new one may sit inside the old one
        else:
            out.append([s, e])
    return [tuple(x) for x in out]


def free_slots(busy, day_start, day_end):
    """Gaps inside [day_start, day_end] not covered by any busy interval."""
    gaps, cursor = [], day_start
    for s, e in merge_intervals(busy):
        if s > cursor:
            gaps.append((cursor, min(s, day_end)))
        cursor = max(cursor, e)
        if cursor >= day_end:
            break
    if cursor < day_end:
        gaps.append((cursor, day_end))
    return [g for g in gaps if g[0] < g[1]]


def min_gpu_nodes(reservations):
    """Fewest nodes so that no two overlapping reservations share one.

    Half-open [start, end): a job ending at 10 frees its node for one starting at 10.
    """
    ends = []  # min-heap of end times of reservations currently holding a node
    for s, e in sorted(reservations):
        if ends and ends[0] <= s:
            heapq.heapreplace(ends, e)
        else:
            heapq.heappush(ends, e)
    return len(ends)


def max_overlap_sweep(reservations):
    """Same answer with an event sweep. Ends sort before starts at the same time."""
    events = []
    for s, e in reservations:
        events.append((s, 1))
        events.append((e, -1))
    events.sort()                 # (t, -1) < (t, +1)
    cur = best = 0
    for _, d in events:
        cur += d
        best = max(best, cur)
    return best


def fits_window(existing, new):
    """True if the half-open interval `new` overlaps none of `existing`."""
    ns, ne = new
    return all(ne <= s or e <= ns for s, e in existing)
```

Merging is O(n log n) for the sort and O(n) for the sweep. The bug that fails most candidates is writing `out[-1][1] = e` instead of `max(out[-1][1], e)`. An interval fully inside the previous one would then shrink it. The test `merge_intervals([(1, 10), (2, 3)])` is there for that. The example is small, and that is the point: the bug only shows when one interval sits inside another.

The node-count function uses a min-heap of end times. If the earliest end is at or before the next start, that node is free, so reuse it. Otherwise open a new node. The sweep version reaches the same answer by turning each interval into a plus event and a minus event, and sorting so that minus comes before plus at the same instant. The test cross-checks both against a brute-force count of overlaps at every integer time, which gives you two independent answers that must agree.

Say your boundary convention before you code. Are intervals closed or half-open? A reservation that ends at 10:00 and one that starts at 10:00 can share a node under the half-open reading. Under the closed reading they conflict. The code above merges touching intervals and treats reservations as half-open, and the docstrings say so. That is a decision you should state, not hide, because the interviewer may have a different rule in mind for their system.



Decide: if time ranges appear, sort by start, then say whether the ends are inclusive. The inclusive question is the one that decides whether two touching ranges collide.

### 6. Rate limiters: four algorithms and their trade-offs

![A token bucket refills at a steady rate up to a cap, a burst can spend the saved tokens at once, and after that the client can only send as fast as the bucket refills.](./img/p3-2009-token-bucket.svg)

*Figure 20.9.6. The token bucket enforces the long-run rate and permits a burst up to the bucket size, and refill is computed lazily so no background thread is needed.*

![A fixed window limit of 10 per second lets 20 requests through within 10 milliseconds when they straddle the window reset.](./img/x09-fixed-window-boundary-burst.svg)

*Figure 20.9.7. A fixed window resets its counter at the boundary, so a client can send the full limit just before and just after it.*

An API key should get 100 requests a minute. An attacker or a buggy client sends 1,000. The limiter must say yes or no in microseconds, using little memory per key. There are four standard answers, and each one trades accuracy, memory and burst behaviour differently. The question is not which algorithm is best in general. The question is which one fits the promise you made to the customer.

The fixed window counts requests per clock minute and resets at the boundary. The sliding log stores a timestamp for every accepted request. The token bucket holds tokens that refill at a steady rate up to a cap. The leaky bucket is a queue that drains at a fixed rate. A fifth, the sliding window counter, is the usual compromise between accuracy and memory. Picture each one as a different kind of ticket office: one counts sales per hour, one keeps every receipt, one hands out tokens that accumulate, and one lines people up and lets them through at a fixed pace.

The fixed window is the easiest to build and the easiest to explain, which is why it appears in so many first answers. Its weakness is the boundary, and the boundary is what the interviewer will test. Knowing the weakness by heart is worth more than knowing the code by heart.

```python
"""Four rate limiters. The clock is always passed in, so tests never sleep.

Each allow(now) returns True or False. Callers must pass non-decreasing times.
For a token bucket that counts LLM tokens and keeps per-tenant state, see
gw13_token_bucket.py in chapter 20.13.
"""
from collections import deque


class FixedWindow:
    """Count requests per window of `window_s`. Cheapest, but allows a 2x burst at the edge."""

    def __init__(self, limit, window_s):
        self.limit, self.window_s = limit, window_s
        self.window_id, self.count = None, 0

    def allow(self, now):
        wid = int(now // self.window_s)
        if wid != self.window_id:
            self.window_id, self.count = wid, 0
        if self.count < self.limit:
            self.count += 1
            return True
        return False


class SlidingLog:
    """Remember every accepted timestamp. Exact, but memory is O(limit) per key."""

    def __init__(self, limit, window_s):
        self.limit, self.window_s = limit, window_s
        self.log = deque()

    def allow(self, now):
        while self.log and self.log[0] <= now - self.window_s:
            self.log.popleft()
        if len(self.log) < self.limit:
            self.log.append(now)
            return True
        return False


class SlidingCounter:
    """Two fixed windows blended by overlap. O(1) memory, approximate."""

    def __init__(self, limit, window_s):
        self.limit, self.window_s = limit, window_s
        self.wid, self.cur, self.prev = None, 0, 0

    def allow(self, now):
        wid = int(now // self.window_s)
        if self.wid is None:
            self.wid = wid
        elif wid == self.wid + 1:
            self.prev, self.cur, self.wid = self.cur, 0, wid
        elif wid > self.wid + 1:
            self.prev, self.cur, self.wid = 0, 0, wid
        frac_prev = 1 - (now % self.window_s) / self.window_s
        if self.prev * frac_prev + self.cur + 1 <= self.limit:
            self.cur += 1
            return True
        return False


class TokenBucket:
    """Refill at `rate` per second up to `burst`. Allows bursts, enforces the long-run rate."""

    def __init__(self, rate, burst):
        self.rate, self.burst = rate, burst
        self.level, self.last = float(burst), None

    def allow(self, now, cost=1):
        if self.last is not None:
            self.level = min(self.burst, self.level + (now - self.last) * self.rate)
        self.last = now
        if self.level >= cost:
            self.level -= cost
            return True
        return False


class LeakyBucket:
    """Meter version: a queue that drains at `rate`; a request is refused if it would overflow.

    Output is smooth, so unlike the token bucket it does not let a burst through.
    """

    def __init__(self, rate, capacity):
        self.rate, self.capacity = rate, capacity
        self.water, self.last = 0.0, None

    def allow(self, now):
        if self.last is not None:
            self.water = max(0.0, self.water - (now - self.last) * self.rate)
        self.last = now
        if self.water + 1 <= self.capacity:
            self.water += 1
            return True
        return False
```

Chapter 20.13 already contains a production-flavoured token bucket in `gw13_token_bucket.py` that counts LLM tokens and tracks tenants. The versions here are the interview-sized ones. The clock is an argument, so tests never sleep, and that keeps the tests fast and repeatable. If you move the code into a service, the clock should still come from the caller.

| Algorithm | Memory per key | Burst behaviour | Weakness |
|---|---|---|---|
| Fixed window | One counter | Up to 2x the limit across a boundary | The boundary burst |
| Sliding log | One timestamp per accepted request | Exact | Memory grows with the limit |
| Sliding window counter | Two counters | Approximate, close to exact | Assumes even spread in the previous window |
| Token bucket | Level and last time | Allows a burst up to the bucket size | Burst may hurt a weak backend |
| Leaky bucket | Level and last time | None, output is smooth | Rejects short bursts a backend could take |

The tests demonstrate the numbers. With a limit of 10 per second, 10 requests at 0.99 and 10 at 1.0 all pass the fixed window, so 20 requests arrive within 10 milliseconds. The sliding log lets exactly 10 through. The sliding counter lets at most 11 through in the test. The table below sums up the trade-offs, and the boundary burst is the one to be ready to explain.

The token bucket is the answer to say first for an API, because it enforces the long-run rate and permits a burst. The test offers 100 requests a second for 60 seconds to a bucket with rate 5 and burst 10 and checks that between 300 and 310 pass. Refill is computed lazily from the elapsed time on each call, so no background thread is needed. A bucket that refills while nobody is calling costs nothing, which is why it suits many keys at once.

Think of the bucket as a savings account for requests. Each second adds a few tokens, up to a cap. A client can spend the saved tokens in one quick burst, and then it can only send as fast as the account refills. That is exactly the behaviour a healthy API wants, and it is why the token bucket is the usual first answer.



Decide: say "token bucket" for APIs and name the boundary burst of the fixed window as the reason not to use it. The short version is that the fixed window lets a client send the full limit twice in a row across the boundary.

### 7. LRU cache

![An LRU cache built from a hash map that points at nodes of a doubly linked list, with sentinels at both ends and the least recent node evicted first.](./img/p2-2009-lru-links.svg)

*Figure 20.9.8. An LRU cache pairs a hash map for lookup with a doubly linked list that keeps the most recent entry at the front and evicts from the back.*

A router caches which replica holds a prompt prefix, and the table must not grow forever. When it is full, throw away the entry used longest ago. Systems Performance, chapter 2, defines LRU as an eviction policy that removes the least recently used object when space is needed. Picture a small desk with room for only a few open files. When a new file arrives, you put away the one you have not touched for the longest time.

The idea needs two things at once. Lookup by key in constant time needs a hash map. Finding and moving the oldest or newest entry in constant time needs an ordered list. The interview version asks you to write it, first with `OrderedDict`, which does both, and then from scratch with a doubly linked list. Knowing why each structure is there is worth more than typing either one from memory.

```python
"""LRU cache two ways: OrderedDict, and a hash map plus a doubly linked list."""
from collections import OrderedDict


class LRUOrdered:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.d = OrderedDict()

    def get(self, key, default=None):
        if key not in self.d:
            return default
        self.d.move_to_end(key)          # most recent goes to the right end
        return self.d[key]

    def put(self, key, value):
        if key in self.d:
            self.d.move_to_end(key)
        self.d[key] = value
        if len(self.d) > self.capacity:
            self.d.popitem(last=False)   # evict from the left: least recently used

    def keys_oldest_first(self):
        return list(self.d)


class _Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=None, value=None):
        self.key, self.value, self.prev, self.next = key, value, None, None


class LRUList:
    """Head side is most recent, tail side is least recent. Sentinels remove edge cases."""

    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.map = {}
        self.head, self.tail = _Node(), _Node()
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, n):
        n.prev.next, n.next.prev = n.next, n.prev

    def _push_front(self, n):
        n.next, n.prev = self.head.next, self.head
        self.head.next.prev = n
        self.head.next = n

    def get(self, key, default=None):
        n = self.map.get(key)
        if n is None:
            return default
        self._unlink(n)
        self._push_front(n)
        return n.value

    def put(self, key, value):
        n = self.map.get(key)
        if n is not None:
            n.value = value
            self._unlink(n)
            self._push_front(n)
            return
        if len(self.map) >= self.capacity:
            lru = self.tail.prev
            self._unlink(lru)
            del self.map[lru.key]       # the node must remember its key for this line
        n = _Node(key, value)
        self.map[key] = n
        self._push_front(n)

    def keys_oldest_first(self):
        out, n = [], self.tail.prev
        while n is not self.head:
            out.append(n.key)
            n = n.prev
        return out
```

In `LRUOrdered`, `move_to_end` marks a key as most recent and `popitem(last=False)` drops the oldest. Fluent Python, chapter 3, lists both methods. In `LRUList`, the map goes from key to node. The sentinels at each end remove every special case for an empty list, so the code does not need an if statement before each change. Each node stores its key, and that is not decoration. When you evict the tail node, you must know which dictionary key to delete.

Every operation is O(1). A timing of 200,000 get-or-put operations with capacity 1,000 shows this. The `OrderedDict` took 0.030 seconds and the hand-built list 0.053. Both are constant per operation. The built-in structure is simply written in C, which is why it is a little faster, and that is a fact about the implementation and not about the algorithm.

The test runs both caches against a reference model through 2,000 random operations, comparing the full recency order after every step. It also stores a value of 0, since the classic bug is treating a falsy value as a miss. A cache that returns "not found" for a stored zero is correct in the sense of never crashing, and wrong in the sense of quietly losing data.



Decide: start with `OrderedDict`, say it is enough in production, and then offer to build the linked list if the interviewer wants the mechanism. The order of those three moves shows you know both the tool and the reason for it.

### 8. Consistent hashing with virtual nodes

![A hash ring where keys move clockwise to the first node, adding a node moves only one arc, and many virtual points flatten the load.](./img/p2-2009-hash-ring.svg)

*Figure 20.9.9. On a consistent hash ring, a key belongs to the first node clockwise, and virtual points flatten load from a ratio of 1.935 to 1.035.*

You want requests with the same session to land on the same replica, so its cache is warm. Taking the hash modulo the number of replicas works until you add one replica, and then almost every key moves. Distributed AI Systems, chapter 9, applies consistent hashing of the user id to give the same user the same model variant. This is the generic mechanism. Nebius has not published its router algorithm, so do not describe it as theirs.

The idea: put both nodes and keys on a circle by hashing them. A key belongs to the first node clockwise from it. Adding a node steals only the arc just before it, so roughly one in N keys moves. With few points the arcs have very uneven lengths, so each node gets many virtual points spread around the circle. Picture a clock face with a few hands, where each hand covers a slice, and where a slice is split into many thin pieces so that no single hand covers much more than its share.

```python
"""Consistent hashing with virtual nodes, plus the balance and movement measurements."""
import bisect
import hashlib
from collections import Counter


def h(s):
    """Stable 64-bit hash. Python's built-in hash() changes between processes, so never use it."""
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], "big")


class Ring:
    def __init__(self, nodes=(), vnodes=100):
        self.vnodes = vnodes
        self.points = []     # sorted hashes
        self.owner = {}      # hash -> node
        for n in nodes:
            self.add(n)

    def add(self, node):
        for i in range(self.vnodes):
            p = h(f"{node}#{i}")
            if p not in self.owner:
                bisect.insort(self.points, p)
                self.owner[p] = node

    def remove(self, node):
        keep = [p for p in self.points if self.owner[p] != node]
        self.owner = {p: self.owner[p] for p in keep}
        self.points = keep

    def lookup(self, key):
        if not self.points:
            raise LookupError("empty ring")
        i = bisect.bisect_right(self.points, h(key))
        return self.owner[self.points[i % len(self.points)]]   # wrap around the circle


def balance(ring, keys):
    """Return (max load / mean load, counts per node)."""
    counts = Counter(ring.lookup(k) for k in keys)
    mean = len(keys) / len(counts)
    return max(counts.values()) / mean, counts


def moved_fraction(before, after, keys):
    return sum(before.lookup(k) != after.lookup(k) for k in keys) / len(keys)


def modulo_moved_fraction(n_before, n_after, keys):
    return sum(h(k) % n_before != h(k) % n_after for k in keys) / len(keys)
```

The built-in `hash` for strings changes between Python processes, so the ring uses a SHA-256 prefix. That is the first thing to say when asked why you did not just call `hash()`. A router that restarts with a different hash would send every session to a different replica, and the caches would go cold all at once.

Lookup is a binary search on the sorted points, and the modulo wraps the circle. Balance here is the highest node load divided by the mean, for 10 nodes and 100,000 keys. With 1 point per node the ratio was 1.935. With 10 points it was 1.573, with 100 it was 1.106 and with 1,000 it was 1.035. The lookup cost rose only from 0.054 to 0.074 seconds per 100,000 lookups when the number of ring points went from 200 to 20,000, which fits O(log N). More points cost a little memory and a little lookup time, and they buy a much flatter load.

A simple way to explain the ring to a colleague is to picture a list of hash values in sorted order, with a wrap at the end. To find the owner of a key, you find where the key's hash would sit in the list, then take the next point. If the key is past the last point, you wrap to the first one. The binary search makes that lookup take a few steps even with thousands of points.

The tests check the movement claim. Adding an eleventh node to ten moved between 5 and 15 percent of 20,000 keys on the ring, against over 85 percent for modulo hashing. Removing a node moved only that node's keys. That last property is the one that matters in an outage, because the keys that stayed put keep their warm caches.



Decide: always quote the balance number you measured as the reason for virtual nodes, not a remembered rule of thumb. A number from your own run is evidence, and a rule of thumb is only a guess.

### 9. Retry with exponential backoff and jitter

![Clients that retry at the same instants create a spike, while full jitter spreads their retries across the wait window.](./img/x09-retry-jitter-herd.svg)

*Figure 20.9.10. Full jitter chooses each retry delay at random up to the current ceiling, so clients that failed together do not all retry together.*

A dependency returns 503 for ten seconds. Ten thousand clients retry immediately, again and again, and the dependency cannot recover. Picture a shop with a closed door, where every customer knocks at the same moment, every second, and nobody can get in while the door is shut. The idea is to wait longer after each failure, and to randomise the wait so that clients do not retry in lockstep.

Full jitter means the delay is a uniform random number between zero and the current ceiling. The ceiling doubles each attempt and is capped. The randomness is what spreads the retries across time, so a thousand clients that failed together do not all come back together.

Without jitter, a thousand clients that all failed at the same moment would wait the same amount and retry at the same moment, and the dependency would see the same spike again. With full jitter, the retries spread out across the whole wait window, and the load arrives as a smooth slope instead of a wall.

```python
"""Retry with exponential backoff and jitter. Sleep and randomness are injected.

The herd simulation and the retry-budget maths live in c21_backoff_math.py (chapter 20.21).
"""
import random


def backoff_delay(attempt, base=0.1, cap=5.0, rng=random.random):
    """Full jitter: uniform between 0 and min(cap, base * 2**attempt). attempt starts at 0."""
    ceiling = min(cap, base * (2 ** attempt))
    return rng() * ceiling


class RetryableError(Exception):
    pass


def call_with_retry(fn, max_attempts=5, base=0.1, cap=5.0, deadline_s=None,
                    sleep=None, rng=random.random, clock=None):
    """Call fn(); retry RetryableError with full jitter. Other exceptions propagate at once.

    deadline_s bounds the total time. We never sleep past it.
    """
    import time
    sleep = sleep or time.sleep
    clock = clock or time.monotonic
    start = clock()
    for attempt in range(max_attempts):
        try:
            return fn()
        except RetryableError:
            if attempt == max_attempts - 1:
                raise
            delay = backoff_delay(attempt, base, cap, rng)
            if deadline_s is not None and clock() - start + delay >= deadline_s:
                raise
            sleep(delay)
```

The herd simulation and the retry-budget arithmetic are in `c21_backoff_math.py` and chapter 20.21. Here you need only the template and the discipline around it. Randomness and sleep are injected, so the tests assert exact delays without waiting: with the random value fixed at 1, attempts 0 and 3 wait 0.1 and 0.8 seconds, and attempt 30 is capped at 5. Injecting the sleep and the randomness is what makes a retry loop testable at all.

Three rules make the answer senior. Retry only errors that are safe to retry, which in the code is a dedicated exception type, and let everything else propagate at once. Bound the total time with a deadline and never sleep past it. And only retry operations that are idempotent, or carry an idempotency key. An idempotent operation gives the same result when it runs twice, so a retry cannot charge a customer twice.

A common way to present the three rules is to name them in order, safe errors first, then the deadline, then idempotence. Each rule closes a different way that a retry can make an outage worse, so naming all three shows you have thought about the failure, not only the timing.



Decide: say "capped exponential backoff with full jitter, a deadline and a retry budget" as one phrase. The phrase names every part of the answer, so the interviewer hears the whole design in one breath.

### 10. Topological sort and cycle detection

![Kahn's algorithm orders services so each starts after its dependencies, and leftover nodes reveal a cycle.](./img/x09-kahn-start-order.svg)

*Figure 20.9.11. Kahn's algorithm starts services with no open dependencies and unlocks others as each one finishes, so any leftover node signals a cycle.*

You must start services in an order where each service's dependencies are up first. Or a Terraform-like tool must apply resources in dependency order. The graph has an edge from each service to the things it needs. A valid order exists exactly when there is no cycle. Picture a set of building blocks where each one rests on others, and you must place the base pieces before the pieces that rest on them.

Kahn's algorithm: count how many unmet dependencies each node has, start with those at zero, and each time you finish a node, reduce the count of the nodes that waited on it. If nodes remain at the end, they are on a cycle or blocked by one. The method is a queue of ready work, and each finished item unlocks the items that were waiting for it.

Here is the method in plain steps. Count the open dependencies of each service. Put every service with no open dependencies into a queue. Take one from the queue and write it to the output. For each service that was waiting on it, subtract one open dependency, and queue it if the count reaches zero. Repeat until the queue is empty.

```python
"""Dependency graphs: topological order, cycle detection, BFS shortest path."""
from collections import deque


def topo_order(deps):
    """deps maps node -> list of nodes it depends on (they must come first).

    Kahn's algorithm. Returns (order, cycle_nodes). cycle_nodes is empty when the
    graph is acyclic. Otherwise it holds every node that is on a cycle or blocked by one.
    Ties are broken alphabetically so the order is deterministic.
    """
    nodes = set(deps)
    for ds in deps.values():
        nodes.update(ds)
    indeg = {n: 0 for n in nodes}
    dependents = {n: [] for n in nodes}
    for n, ds in deps.items():
        for d in set(ds):
            indeg[n] += 1
            dependents[d].append(n)
    ready = sorted(n for n in nodes if indeg[n] == 0)
    queue, order = deque(ready), []
    while queue:
        n = queue.popleft()
        order.append(n)
        newly = []
        for m in dependents[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                newly.append(m)
        queue.extend(sorted(newly))
    stuck = sorted(nodes - set(order))
    return order, stuck


def find_cycle(deps):
    """Return one cycle as a list [a, b, ..., a] following dependency edges, or None. DFS colours."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {}
    stack_path = []

    def visit(n):
        colour[n] = GREY
        stack_path.append(n)
        for d in sorted(set(deps.get(n, ()))):
            c = colour.get(d, WHITE)
            if c == GREY:
                return stack_path[stack_path.index(d):] + [d]
            if c == WHITE:
                found = visit(d)
                if found:
                    return found
        stack_path.pop()
        colour[n] = BLACK
        return None

    for n in sorted(deps):
        if colour.get(n, WHITE) == WHITE:
            found = visit(n)
            if found:
                return found
    return None


def shortest_path(graph, src, dst):
    """BFS on an unweighted graph. Return the node list or None. Mark nodes when enqueued."""
    if src == dst:
        return [src]
    parent = {src: None}
    queue = deque([src])
    while queue:
        n = queue.popleft()
        for m in graph.get(n, ()):
            if m not in parent:
                parent[m] = n
                if m == dst:
                    path = [m]
                    while parent[path[-1]] is not None:
                        path.append(parent[path[-1]])
                    return path[::-1]
                queue.append(m)
    return None


def reachable(graph, src):
    """Iterative DFS. Recursion would hit Python's limit on a long chain of services."""
    seen, stack = {src}, [src]
    while stack:
        n = stack.pop()
        for m in graph.get(n, ()):
            if m not in seen:
                seen.add(m)
                stack.append(m)
    return seen


def blast_radius(deps, failed):
    """Services that transitively depend on `failed`."""
    rev = {}
    for n, ds in deps.items():
        for d in ds:
            rev.setdefault(d, []).append(n)
    return reachable(rev, failed) - {failed}
```

Cost is O(V + E). The function returns the order plus the stuck nodes, which gives cycle detection for free. For a precise report, `find_cycle` walks depth-first with three colours and returns the actual loop. A grey node found again means you came back to something on the current path. The test cross-checks the two methods against each other on random graphs, so the two answers must match.

Chapter 20.24 shows a plan ordering resources. This is the general algorithm, not a description of Terraform internals. If the interviewer asks how a real tool orders its work, say that the algorithm is the general idea and that you would check the tool's documentation for its details.



Decide: ask "what should happen on a cycle", because the answer is an error naming the cycle, not an empty result. An empty result looks like success, and a silent success is the worst outcome for a deploy.

### 11. BFS, DFS and shortest path on a service graph

![Reversing dependency edges from a failed network component exposes the blast radius through breadth-first search rings, marking nodes on enqueue to prevent duplicate processing.](./img/p4-2009-blast-radius-bfs.svg)

*Figure 20.0.0. Reversing service dependency edges turns an inward dependency graph into an outward blast radius search where breadth-first search identifies all downstream affected services.*

A database fails. Which services are affected? Or: what is the fewest hops between two network devices? Breadth-first search explores in rings of increasing distance, so the first time it reaches the target is the shortest route when every edge costs the same. Depth-first search follows one path as far as it goes and is the natural tool for "what is reachable". Both answers matter during an incident, and the question you are asked tells you which search to reach for.

During an incident, the two questions often come one after another. First, what breaks. Second, what is the fastest safe route back. The first is a reachability question, and the second is an ordering question. Saying so out loud helps the interviewer see that you are solving the right problem at each moment.

The code above has all three. `shortest_path` marks a node as seen when it is added to the queue, not when it is removed. Marking late lets the same node enter the queue many times and can make the search exponential on dense graphs. `reachable` is iterative with a stack, and the test builds a chain of 50,000 services to show that a recursive version would hit Python's recursion limit. `blast_radius` reverses the edges and reuses `reachable`, so one function answers the question "who depends on this" by walking the graph backwards.

The cost is O(V + E). Each node is visited once and each edge is looked at once, so the total work grows with the size of the map of services. That is why the same code handles a small dependency graph and a large one without changing shape.



Decide: if edges are unweighted and you want the fewest hops, say BFS. If they have costs, say Dijkstra. The question about costs is the one that decides which algorithm you need.

### 12. Union-find

![Union by size attaches smaller root trees under larger ones, while path compression flattens deep parent pointers directly to the root during find operations.](./img/p4-2009-union-find.svg)

*Figure 20.0.0. Union by size keeps disjoint trees shallow by attaching smaller clusters under larger roots, while path compression flattens parent chains directly to the root on each lookup.*

Fifty nodes report errors. Some pairs are linked, for example by sharing a switch. How many separate failure clusters are there? Union-find answers "are these two in the same group" and "merge these two groups" in near-constant time. Each group has a root, `find` follows parents up to the root, and `union` points one root at the other. Think of it as a set of small teams, where each team has a leader and a merge means one leader reports to the other.

Picture a small map of racks, where a line between two racks means they share a switch. If both racks are failing and they share a switch, they probably belong to one incident. Union-find lets you walk the list of links once and collect the racks into clusters, without building the full map first.

```python
"""Union-find with path compression and union by size."""


class UnionFind:
    def __init__(self, items=()):
        self.parent, self.size = {}, {}
        self.components = 0
        for x in items:
            self.add(x)

    def add(self, x):
        if x not in self.parent:
            self.parent[x], self.size[x] = x, 1
            self.components += 1

    def find(self, x):
        self.add(x)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:       # path compression, iterative
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.components -= 1
        return True

    def groups(self):
        out = {}
        for x in self.parent:
            out.setdefault(self.find(x), set()).add(x)
        return list(out.values())


def failing_clusters(failing_nodes, links):
    """Groups of failing nodes that are connected by links between failing nodes."""
    bad = set(failing_nodes)
    uf = UnionFind(bad)
    for a, b in links:
        if a in bad and b in bad:
            uf.union(a, b)
    return sorted(sorted(g) for g in uf.groups())
```

Two optimisations make it fast. Path compression flattens the tree during `find`, so the next lookup goes straight to the root. Union by size attaches the smaller tree under the larger, which keeps the trees shallow in the first place. Together they give an amortised cost treated as constant. Amortised means that a single slow call can happen, but the average over many calls stays small.

The test compares the component count against a brute-force merge of sets on random edge lists. The `failing_clusters` function is the SRE form: only links between two failing nodes count, so a healthy switch does not join clusters. In the interview, ask whether a shared healthy switch should connect them, because the answer depends on whether the switch is a real path for the fault.



Decide: for a stream of "these two are connected" facts, use union-find. For a one-time traversal of a graph you already hold, BFS is fine. Union-find is for facts that arrive over time, and BFS is for a graph that is already in memory.

### 13. Binary search on the answer

![A row of timeout values that go no, no, no, yes, yes, yes with the search halving the range until it finds the first yes, and returning hi plus 1 if nothing passes.](./img/p3-2009-binary-search-answer.svg)

*Figure 20.9.12. When a bigger value never makes the check worse, the answers flip once and binary search finds the flip in a handful of checks.*

You do not know the right timeout. You do have a yes-or-no test: with this timeout, do at least 99 percent of requests succeed? Because a larger timeout can only help, the answers go no, no, no, yes, yes, yes. Binary search finds the flip point in a handful of checks, even if each check is expensive. The search does not need to know the shape of the curve, only that the answer flips once.

Picture a team that must choose a timeout for a client library. Too short, and healthy requests fail. Too long, and a stuck request holds a connection for a long time. The search asks only one question at each step: at this timeout, is the target met? Each answer narrows the range by half.

```python
"""Binary search on the answer: find the smallest value for which a monotonic check passes."""
import math


def first_true(lo, hi, ok):
    """Smallest x in [lo, hi] with ok(x) True, assuming ok is False...False True...True.

    Returns hi + 1 if ok is never True. Integer search, so it always terminates.
    """
    while lo <= hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid - 1
        else:
            lo = mid + 1
    return lo


def min_replicas(peak_rps, per_replica_rps_fn, max_replicas=10_000):
    """Fewest replicas whose total capacity covers peak_rps, when per-replica
    capacity falls as replicas are added (shared-state overhead). Monotonic in n.
    """
    def ok(n):
        return n * per_replica_rps_fn(n) >= peak_rps
    n = first_true(1, max_replicas, ok)
    return None if n > max_replicas else n


def min_timeout_ms(latencies_ms, target_success):
    """Smallest integer timeout that lets at least target_success of requests finish."""
    n = len(latencies_ms)
    ok = lambda t: sum(x <= t for x in latencies_ms) >= math.ceil(target_success * n)
    return first_true(0, int(max(latencies_ms)) + 1, ok)


def min_window_hours(job_hours, nodes):
    """Smallest maintenance window (hours per node) so that jobs, run in the given order
    and split into at most `nodes` contiguous groups, each fit in the window.
    This is the classic 'split array largest sum' form of the pattern.
    """
    def ok(cap):
        groups, load = 1, 0
        for j in job_hours:
            if load + j > cap:
                groups += 1
                load = 0
            load += j
        return groups <= nodes

    return first_true(max(job_hours), sum(job_hours), ok)


def float_search(lo, hi, ok, iterations=60):
    """Binary search on reals: fixed iteration count, never `while lo != hi`."""
    for _ in range(iterations):
        mid = (lo + hi) / 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi
```

The template `first_true` is the one to memorise. It returns `hi + 1` when nothing passes, so the caller must test for that. Forgetting that last check is the most common bug in this pattern, and the function's docstring says it on purpose.

The examples are the SRE forms. `min_replicas` finds the fewest replicas that cover peak traffic when per-replica capacity falls as replicas are added, so you cannot just divide. The test compares it to a linear scan. `min_timeout_ms` returns the smallest integer timeout that lets a target fraction finish. `min_window_hours` is the classic split-array problem, framed as the shortest maintenance window that lets a fixed job order run on a given number of nodes. The test compares it to brute force on 100 random inputs. `float_search` uses a fixed number of iterations because a real-valued loop that tests equality may never end.

The cost is O(log range) calls to the check, so the total is that times the cost of one check. State both, because a cheap check that runs many times and an expensive check that runs a few times can have very different bills.



Decide: whenever a problem asks for "the minimum X such that something holds", and bigger X never makes it worse, search on X. The phrase "bigger never hurts" is the test that tells you the pattern applies.

### 14. Streaming percentiles, and why you never average percentiles

![Three ways to keep a p99 for a stream, exact, a reservoir sample, and a bucket histogram, with measured bucket counts and errors against an exact p99 of 551.79.](./img/p3-2009-histogram-tradeoff.svg)

*Figure 20.9.13. A finer bucket ratio costs more memory and gives a smaller error, and histograms from many servers add bucket by bucket.*

![Averaging the p99 of a quiet server and a busy server gives 55 ms, while merging their requests gives a true p99 of 12 ms.](./img/x09-averaged-p99-trap.svg)

*Figure 20.9.14. Averaging per-server percentiles weights small servers as heavily as large ones, so the fleet percentile must come from merged samples or histograms.*

The latency SLI is p99. Servers handle millions of requests, so you cannot store every latency. Systems Performance, chapter 2, lists latency as an average or a percentile, and the percentile is the one that reveals the tail users feel. Three ideas follow, and each one answers a different part of the problem: what the percentile means, how to keep a sample of it, and how to keep a histogram of it.

First, the exact definition. The nearest-rank percentile is the smallest value with at least p percent of the samples at or below it. That is what `percentile` computes, and the tests include a single-element list and an empty list, because those are the two cases that break careless code.

Picture a list of response times written out in order, with the smallest on the left. The p95 is the value that most of the list sits at or below, with only the slowest few above it. Writing the list out first is the easiest way to check the function against a small example.

Second, a reservoir sample keeps k values chosen uniformly from a stream of unknown length. After the first k, item number n replaces a random slot with probability k over n. The effect is that every item seen so far has the same chance of being in the sample, however long the stream has run.

Third, a fixed-bucket histogram counts how many samples fall in each of a set of buckets with geometric spacing. This is the idea behind a Prometheus histogram. Its memory depends on the number of buckets, not on the traffic, and histograms from many servers add bucket by bucket. The Prometheus histogram guide says the error is limited by the width of the bucket the quantile falls in. The error depends on the bucket ratio. I measured it on 200,000 lognormal samples. The exact p99 was 551.79. A ratio of 1.1 with 123 buckets gave 593.35, and a ratio of 1.02 with 584 buckets gave 553.93. Finer buckets, smaller error. The trade is memory for accuracy, and you can choose the point on that curve.

```python
"""Streaming percentiles: exact, reservoir sample, fixed-bucket histogram, and the averaging trap."""
import bisect
import math
import random


def percentile(sorted_vals, p):
    """Nearest-rank percentile, p in (0, 100]. The smallest value with at least p% at or below it."""
    if not sorted_vals:
        raise ValueError("empty")
    if not 0 < p <= 100:
        raise ValueError("p must be in (0, 100]")
    rank = math.ceil(p / 100 * len(sorted_vals))
    return sorted_vals[rank - 1]


class Reservoir:
    """Algorithm R: a uniform random sample of k items from a stream of unknown length."""

    def __init__(self, k, rng=None):
        self.k, self.n, self.items = k, 0, []
        self.rng = rng or random.Random()

    def add(self, x):
        self.n += 1
        if len(self.items) < self.k:
            self.items.append(x)
        else:
            j = self.rng.randrange(self.n)      # 0 .. n-1 inclusive
            if j < self.k:
                self.items[j] = x

    def percentile(self, p):
        return percentile(sorted(self.items), p)


class LogHistogram:
    """Fixed buckets with geometric boundaries, like a Prometheus histogram.

    Memory is the number of buckets. Error is bounded by the bucket ratio.
    Histograms from many servers can be added bucket by bucket.
    """

    def __init__(self, lo=1.0, hi=100_000.0, ratio=1.1):
        self.bounds = []
        b = lo
        while b < hi * ratio:
            self.bounds.append(b)
            b *= ratio
        self.counts = [0] * (len(self.bounds) + 1)   # last bucket: above every bound

    def add(self, x):
        self.counts[bisect.bisect_left(self.bounds, x)] += 1

    def merge(self, other):
        assert self.bounds == other.bounds
        for i, c in enumerate(other.counts):
            self.counts[i] += c

    def quantile(self, q):
        """Upper bound of the bucket holding the q-th quantile, q in (0, 1]."""
        total = sum(self.counts)
        target = math.ceil(q * total)
        seen = 0
        for i, c in enumerate(self.counts):
            seen += c
            if seen >= target:
                return self.bounds[min(i, len(self.bounds) - 1)]
        raise ValueError("empty")


def average_of_p99s(groups):
    """The wrong way to get a fleet p99: average each server's p99."""
    return sum(percentile(sorted(g), 99) for g in groups) / len(groups)


def true_p99(groups):
    return percentile(sorted(x for g in groups for x in g), 99)
```

A t-digest is a more advanced sketch. At a high level it keeps a small set of clusters, each with a mean and a count, with very small clusters at the tails so extreme percentiles stay accurate, and two digests can be merged. It is not implemented in the code folder. If asked, describe that idea and say a library is the right choice in practice, because a well-tested library beats a quick implementation under pressure.

The trap in the last two functions is the one to remember. If a quiet server has 1,000 requests with p99 of 10 and a busy one has 10 requests with p99 of 100, the average of the two p99s is 55. The true p99 across all 1,010 requests is 12. The test asserts exactly those numbers. Averaging percentiles weights a server with ten requests as much as one with a thousand. **To combine servers, merge the histograms or the raw samples, then take the percentile.** The same rule explains why a Prometheus query for a fleet p99 uses `histogram_quantile` over summed bucket rates and not an average of per-instance quantiles. The Prometheus histogram guide shows `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))` as the good form. It says averaging quantiles gives statistically nonsensical values, and it adds that this works only while the bucket boundaries match across instances.



Decide: say "I would never average percentiles, I would merge histograms" before the interviewer has to ask. Saying it first shows that you know the trap and that you avoid it by design.

### 15. String compression and parsing

The last two small patterns are text. A support engineer pastes a log line with a quoted message and asks what the fields are, or asks for a compressed form of a repeated string. Run-length encoding replaces a run of the same character by its count and the character. A tokeniser turns a line like `level=info msg="hello world"` into fields while respecting quotes.

A short way to say the tokeniser idea is "I read one character at a time, and I change state when I see a quote." That sentence names the approach, and it prepares you for the edge cases that follow.

```python
"""String compression and parsing: run-length encoding and a quote-aware tokeniser."""
import re


def rle_encode(s):
    out, i = [], 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(f"{j - i}{s[i]}")
        i = j
    return "".join(out)


def rle_decode(s):
    """Decode '3a2b' style text. The input must not contain digits as data characters."""
    out, num = [], ""
    for ch in s:
        if ch.isdigit():
            num += ch
        else:
            if not num:
                raise ValueError("missing count before %r" % ch)
            out.append(ch * int(num))
            num = ""
    if num:
        raise ValueError("trailing count")
    return "".join(out)


def tokenize(line):
    """Parse logfmt text (key=value pairs, values may be quoted with backslash escapes) into a dict."""
    out, i, n = {}, 0, len(line)
    while i < n:
        while i < n and line[i] == " ":
            i += 1
        if i >= n:
            break
        j = i
        while j < n and line[j] not in "= ":
            j += 1
        key = line[i:j]
        if j >= n or line[j] == " ":
            out[key] = ""
            i = j
            continue
        j += 1  # skip '='
        if j < n and line[j] == '"':
            j += 1
            buf = []
            while j < n and line[j] != '"':
                if line[j] == "\\" and j + 1 < n:
                    j += 1
                buf.append(line[j])
                j += 1
            if j >= n:
                raise ValueError("unterminated quote")
            out[key] = "".join(buf)
            i = j + 1
        else:
            k = j
            while k < n and line[k] != " ":
                k += 1
            out[key] = line[j:k]
            i = k
    return out


def collapse_ids(path):
    """Normalise URL paths for metrics labels: /users/123/jobs/9f2c... -> /users/:n/jobs/:hex"""
    path = re.sub(r"/\d+(?=/|$)", "/:n", path)
    return re.sub(r"/[0-9a-f]{8,}(?=/|$)", "/:hex", path)
```

Both are O(n). Run-length encoding has two classic traps. When the count has more than one digit, decoding must read all the digits, and the test uses a run of 25. And the format is ambiguous when the data itself contains digits, so the decoder documents that restriction and rejects a missing count. A round-trip test over random strings proves the pair is consistent, which means encoding and then decoding gives back the original.

The tokeniser reads one character at a time with a small state machine. Inside quotes a backslash escapes the next character, and an unterminated quote raises an error. Python's `str.split` would break `"hello world"` apart, and that is the point of the exercise. The `collapse_ids` helper turns `/users/123/jobs/9f2c4a1b88` into a stable label, tying back to cardinality, which is why the same helper appears in the first section.



Decide: for any parser, write the three bad inputs first: empty, truncated, and the character that has a special meaning. Writing the bad inputs first gives the parser its shape before you write it.

### 16. Basic concurrency: queues, counters and asyncio

![A fetch_all coroutine runs several calls concurrently, each with its own timeout so a slow call fails alone, and an overall timeout that cancels whatever is still running.](./img/p3-2009-asyncio-two-timeouts.svg)

*Figure 20.9.15. Wrap each call so it never raises, give it its own timeout, and put an overall timeout around the whole gather.*

![Two threads each read the same counter value, add one and write back the same result, so two increments leave the count one lower, while a lock makes read, add and write one unit.](./img/p3-2009-lost-update.svg)

*Figure 20.9.16. The increment is three steps, read, add and write, so without the lock two threads can overwrite each other.*

An ingest service has a fast reader and slow writers. A counter is updated from many threads. A fan-out call asks five backends and must not wait for the slowest forever. These are the three concurrency questions an SRE round asks, and each one has a standard answer that is short to say and easy to get wrong.

```python
"""Basic concurrency: producer/consumer, a thread-safe counter, asyncio gather with timeouts."""
import asyncio
import queue
import threading

SENTINEL = object()


def run_pipeline(items, n_workers, work):
    """Producer puts items on a bounded queue. n_workers consumers apply work().

    Each worker gets one sentinel so it knows when to stop. Returns results in completion order.
    """
    q = queue.Queue(maxsize=10)          # bounded: a slow consumer slows the producer
    results, lock = [], threading.Lock()

    def worker():
        while True:
            item = q.get()
            if item is SENTINEL:
                return
            r = work(item)
            with lock:
                results.append(r)

    threads = [threading.Thread(target=worker) for _ in range(n_workers)]
    for t in threads:
        t.start()
    for it in items:
        q.put(it)
    for _ in threads:
        q.put(SENTINEL)
    for t in threads:
        t.join()
    return results


class Counter:
    """`self.n += 1` is read, add, write: three steps. Without the lock updates can be lost."""

    def __init__(self):
        self.n = 0
        self._lock = threading.Lock()

    def inc(self):
        with self._lock:
            self.n += 1


class UnsafeCounter:
    def __init__(self):
        self.n = 0

    def inc(self):
        self.n += 1


def hammer(counter, threads=8, per_thread=20_000):
    ts = [threading.Thread(target=lambda: [counter.inc() for _ in range(per_thread)])
          for _ in range(threads)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return counter.n


async def fetch_all(fns, per_call_timeout, overall_timeout):
    """Run coroutine functions concurrently. Return a list of ('ok', value) or ('err', name).

    A slow call times out alone. The overall budget cancels whatever is still running.
    """
    async def one(fn):
        try:
            return ("ok", await asyncio.wait_for(fn(), per_call_timeout))
        except asyncio.TimeoutError:
            return ("err", "timeout")
        except Exception as e:
            return ("err", type(e).__name__)

    try:
        return await asyncio.wait_for(asyncio.gather(*(one(f) for f in fns)), overall_timeout)
    except asyncio.TimeoutError:
        return [("err", "overall_timeout")] * len(fns)
```

Producer and consumer. A bounded `queue.Queue` connects them, so a slow consumer slows the producer instead of letting memory grow. This is the same idea as the bounded request queue that Distributed AI Systems, chapter 9, recommends, with 503 as the overflow response. The producer sends one sentinel per worker so each worker knows when to stop. Without the sentinel, the workers would wait on the queue forever.

Picture a conveyor belt with a fixed length. The producer can only add items while there is room on the belt, and the workers take items off as they finish. When the belt is full, the producer waits, which is exactly the backpressure you want in a service under load.

The thread-safe counter. The Python FAQ for 3.12 says that `i = i+1` is not atomic and that, when in doubt, you should use a mutex. So the locked `Counter` is correct and `UnsafeCounter` is wrong by specification. Running the unsafe counter with 8 threads and 200,000 increments each on Python 3.12.7 reported exactly 1,600,000, so the race did not appear. That does not make it safe. The scheduler may switch between the bytecodes of the read, the add and the write, and other interpreter versions or other operations can lose updates. Never offer "it worked when I ran it" as a proof. Systems Performance, chapter 5, describes mutexes as making other threads block and wait off the CPU.

A simple way to remember the lesson is that the lock turns three steps into one. Without the lock, two threads can each read the same value, each add one, and each write back the same result. Two increments then leave the count one lower than it should be. The lock makes the read, add and write happen as one unit.

Asyncio. Fluent Python, chapter 21, shows `asyncio.gather` waiting for all awaitables and returning results in the order they were submitted. The 3.12 documentation adds that if one raises and `return_exceptions` is false, the exception propagates immediately and the other awaitables keep running. Our `fetch_all` therefore wraps each call so it never raises, gives each call its own timeout with `wait_for`, and puts an overall timeout around the whole gather. The tests show three different outcomes for a fast, a slow and a failing call, and that the overall timeout cancels everything. Python 3.11 added `asyncio.timeout` and `asyncio.TaskGroup` as the modern alternatives.

A simple mental model is a set of waiters in a restaurant. Each call is a table, and the gather is the host waiting for every table to finish. The per-call timeout is a rule that a slow table is cleared alone, and the overall timeout is a rule that the whole room closes at a fixed time.

For CPU-bound work, threads do not help in standard CPython because of the global interpreter lock, so use processes. For I/O-bound fan-out, threads or asyncio work. The question to ask is where the time goes: waiting on the network or computing on the processor.



Decide: name the bottleneck first, I/O or CPU, because the right tool follows from it. Naming the bottleneck is the step that turns a vague concurrency question into a concrete design.

## How to answer out loud

The rhythm for every coding question is the same. Restate the problem and ask two clarifying questions. Name the pattern. Say the plan and the complexity. Write the code, test it on a tiny example, then on edge cases. Finish with the follow-up you would expect. Five short questions follow, one for each of the patterns most often asked, and each answer is written as you might say it in the room.

Keep the rhythm in your head as a checklist of five short moves. Restate, pick the pattern, state the cost, write and test, then name the follow-up. A candidate who follows the same five moves each time sounds calm, and calm is what the interviewer hears first.

**Question 1. "Implement a rate limiter for 100 requests a minute per key."** Ask per key or global, one process or many, bursts or not. Name the four options, then choose the token bucket. Write `allow(now)` with a lazy refill. Say the memory is two numbers per key. Name the boundary burst of the fixed window, which is up to twice the limit, as the reason you rejected the simpler option. Expect follow-ups on idle-key eviction and a shared store, and say that a shared store is a different design with its own failure modes.

**Question 2. "Find the slowest ten endpoints in a huge log."** Say you will stream the file, not load it. Aggregate with a dictionary keyed by endpoint, then take the top ten with a size-ten heap. State O(n) for the pass and O(m log 10) for the heap over m endpoints. Ask whether slowest means the mean or p99. If p99, say you cannot keep every sample and would use a histogram per endpoint.

**Question 3. "Design an LRU cache."** Begin with the pair of needs: lookup by key and removal of the oldest. Offer `OrderedDict` in five lines. Then, if asked, draw the hash map pointing at nodes of a doubly linked list with sentinels, and walk through a get and an eviction. State O(1). Mention the zero-value trap, because it is the one most often missed in a live round.

**Question 4. "Given service dependencies, give a start order."** Say topological sort and Kahn's algorithm. Explain the in-degree counting in two sentences. Leftover nodes mean a cycle. State O(V + E). If the interviewer adds a cycle to the graph, name the cycle rather than returning an empty list.

**Question 5. "Retries: how would you write them?"** Say capped exponential backoff with full jitter, a total deadline, retries only for safe errors and idempotent calls, and a retry budget so a partial outage does not multiply load. Point to chapter 20.21 for the layered-amplification arithmetic. Expect the follow-up "why jitter", and answer that without it every client retries at the same instants.



## Worked scenarios

### Scenario 1. A rolling error-rate alert with a quiet-period guard

A tired on-call engineer wakes up to a page that fires for a single failed request in the middle of the night. Problem. The on-call wants an alert when the five-minute error rate exceeds one percent. At 03:00 traffic is so low that one failed request out of two is a 50 percent rate. How do you build it, so that the page means something?

Reasoning. The window pattern gives the rate. The empty or tiny window gives a noisy result. So the alert needs a minimum number of requests as well as a rate threshold. A rate on its own is misleading when there is almost no traffic, and the minimum volume is what stops the noise from paging anyone.

Steps. Feed events into `RollingErrorRate`. Before alerting, read `len(r.events)` and require at least a stated minimum. Choose the minimum from the traffic: with 100 requests in the window, a single error is already one percent, so a minimum of a few hundred keeps one stray failure from paging anyone. That figure is an example, not a Nebius standard. Pick the number that matches your own traffic, and write it down with the reason.

Think of the minimum as a guard rail rather than a threshold. It does not say whether the service is healthy. It says whether the number is big enough to be worth reading at all, and that is a separate question that the interviewer may ask.

Answer. Window rate plus a volume floor. Memory is the number of events in the window, so at 10,000 requests a second and a 300-second window the deque would hold three million tuples. Say that this is too much and switch to per-second buckets of two counters, which is 300 entries. This bucket trick is the same window pattern with a coarser unit, and it trades a little precision for a large drop in memory.

### Scenario 2. Fitting a maintenance job into GPU reservations

![Three reservations from 0 to 4, 2 to 6 and 8 to 10 hours on a timeline need two nodes because the first two overlap during hours 2 to 4, and the third reuses a node.](./img/p3-2009-gpu-sweep.svg)

*Figure 20.9.17. Sort by start and keep a min-heap of end times; if the earliest end is at or before the next start, reuse that node, otherwise open a new one.*

A planner has two nodes, a stack of reservations and a job that must fit somewhere before a deadline. Problem. A node has reservations `(0, 4)` and `(2, 6)` hours, and a second node has `(8, 10)`. All are half-open. How many nodes do you need for all three, and where can a two-hour job run?

Reasoning. The first two overlap during hours 2 to 4, so they need separate nodes, and `(8, 10)` can reuse either. `min_gpu_nodes` returns 2. For the job, `free_slots` on the first node, after merging to `(0, 6)`, leaves `(6, 8)` and `(8, 10)` free. Walk the timeline on paper before you trust the function, because the picture makes the gaps obvious.

Answer. Two nodes, and the job fits at hours 6 to 8 on the first. Your first reply to a real request should be whether reservations are per node or pooled, because that answer changes the whole model.

### Scenario 3. Which services break, and what starts first

A network outage has just been announced, and the team asks which services will break and in what order to bring them back. Problem. The dependency map is `api -> db, cache`, `cache -> net`, `db -> net`, and `web -> api`. The network layer goes down. What is the blast radius, and in what order do you bring things back?

Reasoning. Blast radius is every service that transitively depends on `net`. `blast_radius(deps, "net")` reverses the edges and walks. It returns `cache`, `db`, `api` and `web`. Recovery order is the topological order, with `net` first, then `cache` and `db`, then `api`, then `web`. The order is deterministic because ties are broken alphabetically, which means the team gets the same plan every time they run it.

A useful habit is to read the reversed edges aloud. If the network depends on nothing, every line that starts at the network leads to a service that is affected. That sentence explains the reverse walk without a diagram.

Answer. Everything except `net` is affected, and the start order is `net, cache, db, api, web`. The tests assert the blast radius and a topological order for a graph of this shape. If someone later adds `net -> web`, the graph has a cycle, and `topo_order` returns the stuck nodes and `find_cycle` names the loop. The correct behaviour is to refuse to proceed and print the cycle, so that the team fixes the map before they restart anything.

## Hands-on lab

All of this lab ran on this Mac with Python 3.12.7 and pytest 8.3.5. Nothing needs a container, so you can run it on any laptop with the same versions, and the steps below are in the order the chapter needs them.

1. Run the tests from the repository root. The command below runs all four test files together, and it should finish quickly.

```bash
python3 -m pytest code/part20/test_c09_logs_windows.py code/part20/test_c09_heaps_intervals.py code/part20/test_c09_ratelimit_lru_ring.py code/part20/test_c09_rest.py -q
```

Expected result: 65 passed.

2. Measure the complexity claims. The script prints timings for the window and ring examples, so you can compare them with the numbers in this chapter.

```bash
python3 code/part20/c09_measure.py
```

Expected shape: the deque column grows about twice when n doubles, the naive column grows about twice as well but is roughly fifty times larger at k equal to 1,000, ring balance falls from about 1.9 to about 1.04 as virtual nodes rise from 1 to 1,000, and the unsafe counter probably prints 1,600,000. The numbers in this chapter came from that run. Yours will differ in the digits, but the shape should match.

```text
sliding max, k=1000: deque vs naive (seconds)
  n= 10000 deque=0.0012 naive=0.0567
  n= 40000 deque=0.0052 naive=0.2495
ring balance (max load / mean) 10 nodes, 100k keys
  vnodes=    1 ratio=1.935
  vnodes= 1000 ratio=1.035
```

3. Break the code on purpose. In `c09_intervals.py`, replace `max(out[-1][1], e)` with `e`, and rerun the second test file. Expected result: `test_merge_intervals` fails. Restore the line. Then in `c09_lru.py`, delete the `move_to_end` call in `get` and watch the random cross-check fail. These mutations show what the tests guard, and they are the quickest way to learn which line matters.

These lab steps were not run in a container, and the mutation steps were not run. The test and measurement steps are the ones that ran.

## Drill questions

1. What does a deque buy you over a list in a sliding window?

<details><summary>Answer</summary>

Removing from the front of a deque is constant time. On a list it shifts every other element.

</details>

2. In the maximum-of-window algorithm, why is the work O(n) when there is a loop inside the loop?

<details><summary>Answer</summary>

Each index is appended once and removed once. The inner loop only removes, so the total number of removals across the whole run is at most n.

</details>

3. Why does a fixed-window limiter allow twice the limit, and which algorithms avoid it?

<details><summary>Answer</summary>

The counter resets at the boundary, so a client can send the full limit just before it and again just after. The sliding log avoids it exactly, the sliding counter approximately, and the buckets through continuous refill.

</details>

4. Token bucket or leaky bucket for protecting a GPU endpoint that tolerates short bursts?

<details><summary>Answer</summary>

Token bucket. It passes a burst up to the bucket size and enforces the long-run rate. The leaky bucket smooths output and rejects bursts the backend could take.

</details>

5. What goes wrong if an LRU node does not store its key?

<details><summary>Answer</summary>

When you evict the tail node, you must delete its entry from the hash map. Without the key in the node, you cannot find which map entry to delete, and the map keeps a stale pointer.

</details>

6. Why use virtual nodes, and what did the measurement show?

<details><summary>Answer</summary>

With one point per node the arcs are uneven. In my run the busiest of 10 nodes had 1.935 times the mean load with 1 point and 1.035 times with 1,000.

</details>

7. Why is modulo hashing a poor choice when replicas change?

<details><summary>Answer</summary>

Changing the divisor changes the owner of almost every key. In the test, going from 10 to 11 nodes moved over 85 percent of keys with modulo and between 5 and 15 percent with the ring, close to one in eleven.

</details>

8. What are the three parts of a senior retry answer beyond "backoff"?

<details><summary>Answer</summary>

Full jitter, a total deadline, and retrying only safe errors on idempotent operations. A retry budget is the fourth, in chapter 20.21.

</details>

9. How does Kahn's algorithm tell you there is a cycle?

<details><summary>Answer</summary>

It removes nodes whose dependencies are done. If nodes are left over, they are on a cycle or wait on one.

</details>

10. A quiet server has p99 of 10 ms over 1,000 requests and a busy one p99 of 100 ms over 10 requests. What is the fleet p99, and why is the average wrong?

<details><summary>Answer</summary>

In the test the true p99 over all 1,010 requests is 12 ms, while the average of the two p99s is 55 ms. The average gives a server with ten requests as much weight as one with a thousand. Merge histograms or samples first, then compute the percentile.

</details>

## Common mistakes and weak answers

| Weak answer | What loses points | Say instead |
|---|---|---|
| Starts typing at once | The interviewer cannot hear your reasoning | "I will restate, pick the pattern, give the cost, then code" |
| Loads the whole log into a list | Fails on large input | "I will iterate the file line by line and aggregate" |
| Fixed-window limiter with no comment | Misses the boundary burst | "This allows up to 2x at the edge, so I prefer a token bucket" |
| Uses `hash()` for a ring | Not stable between processes | "A stable hash such as SHA-256" |
| Averages p99 values | Statistically wrong | "I merge histograms, then take the quantile" |
| Retries with no jitter or deadline | Creates herds, outlives the caller | "Capped backoff, full jitter, a deadline, a budget" |
| Recursive DFS on a long chain | Hits the recursion limit | "Iterative with an explicit stack" |
| "It worked when I ran it" on a race | Proves nothing | "The docs say it is not atomic, so I use a lock" |
| A default of `[]` for a mutable argument | Learning Python, chapter 17, notes defaults keep state between calls | Use `None` and create the list inside |
| Claims a speedup without measuring | Unsupported | "O(n log k) versus O(n log n), and I would measure" |



## Connections to the rest of the handbook

The coding round connects to several other chapters, so this list shows where to go next when a part of this one is still shaky.

- 20.8 What to expect (`c20-08`), 20.10 Complexity and latency numbers (`c20-10`) and 20.11 Practice set (`c20-11`) are the rest of the coding round.
- 20.13 Design: multi-tenant LLM API (`c20-13`) contains the production-style token bucket and a router simulation.
- 20.15 Observability pipeline (`c20-15`) covers metric cardinality. 20.18 How LLM serving fails (`c20-18`) covers retry amplification and bounded queues.
- 20.19 SLIs, SLOs and alerts (`c20-19`) builds on the percentile and rolling-window sections.
- 20.21 Routing, retries and overload control (`c20-21`) has the herd simulation and retry-budget arithmetic.
- 20.24 Terraform for resilient GPU clusters (`c20-24`) shows a plan graph where topological ordering applies.

## Sources and review notes

Sources, all read on 2026-11-09:

- Fluent Python, 2nd edition: chapter 2 "An Array of Sequences" for deque as the efficient first-in first-out structure and for `bisect`; chapter 3 "Dictionaries and Sets" for `defaultdict`, `OrderedDict` and `move_to_end`; chapter 21 "Asynchronous Programming" for `asyncio.gather` behaviour and `asyncio.run`.
- Learning Python, 6th edition: chapter 14 "Iterations and Comprehensions" for line-by-line file iteration and the memory problem of `readlines`; chapter 8 "Lists and Dictionaries" for mutability; chapter 17 "Scopes" for state retained in mutable default arguments.
- Distributed AI Systems, chapter 9 "Production LLM Serving Stack": bounded request queue with an immediate 503, consistent hashing of the user id for variant assignment, and rate limiting in the API gateway.
- Systems Performance, 2nd edition: chapter 2 "Methodologies" for LRU as an eviction policy and for latency as an average or percentile; chapter 5 "Applications" for the big-O table and the locking primitives.
- Python 3.12 documentation, FAQ "What kinds of global value mutation are thread-safe?", and the asyncio Tasks page for `gather`, `timeout` and `TaskGroup`, fetched from docs.python.org.
- Nebius interview process and candidate reports, from `planning/VOLUME_20_NEBIUS_SRE_PLAN.md` section 1.

Code and tests: `code/part20/c09_*.py` and `code/part20/test_c09_*.py`. All 65 tests passed on Python 3.12.7 with pytest 8.3.5. `python3 tools/check_code_files.py code/part20` reported 264 files and 0 problems. Code blocks were copied from the files by script, not with the sync tool.

Explicitly labelled inferences:

- The minimum request count in scenario 1 is an illustration, not a standard.
- The near-constant amortised cost of union-find is a textbook result I did not measure.
- The t-digest description is a high-level idea, and I did not implement or measure it.

Not verified:

- The thread race in `UnsafeCounter` did not reproduce on Python 3.12.7, so I have no observed lost update.
- Timings are one run on one Mac and will vary.
- The lab mutation steps were not run.

### Verification log

Fetched 2026-11-09: prometheus.io/docs/practices/histograms and the Python 3.12 asyncio Tasks page. Claims checked: 6. Confirmed: 5 (`histogram_quantile` with `sum by (le)`, error bounded by bucket width, averaging quantiles is invalid, `gather` leaves other awaitables running after one raises, `TaskGroup` and `timeout` added in 3.11). Corrected: 0. Removed: 1 (the "general practice" disclaimer, replaced by the citation). Still unverified: 2. They are the near-constant amortised cost of union-find and the t-digest description. No gem book in the local library mentions either, so I kept them as labelled textbook claims. The `UnsafeCounter` race still did not reproduce.
