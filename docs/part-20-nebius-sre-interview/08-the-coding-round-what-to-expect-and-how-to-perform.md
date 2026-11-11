---
id: "c20-08"
title: "20.8 The coding round: what to expect and how to perform"
sidebar_label: "20.8 The coding round"
sidebar_position: 8
description: "How to handle the coding task in a Nebius SRE interview: the 60-minute structure, thinking aloud, writing code that runs first time in a plain editor, hand testing with edge-case checklists, the Python standard-library tools worth knowing with verified behaviours, Go equivalents, common pitfalls and a four-week practice routine, with a tested harness and edge-case examples."
status: "drafted"
tier: "1"
level: "I"
lab_venue: "Laptop / Docker"
---

# 20.8 The coding round: what to expect and how to perform

## What the interviewer is testing

You get a problem statement and an empty editor. The interviewer says: "Take your time, talk me through it." Nothing is hidden about the format, but a lot is hidden inside it. This chapter serves the coding part of the first technical interview. Nebius's interview page says the technical interviews include "at least one practical coding / algorithms / data-structures task". That is the plan's wording, taken from the official page.

The same page says you must write working, testable code in a language of your choice, with Python or Go named as examples. It lists classical algorithms and data structures as the topic. It also lists the behaviours that are graded. You should say your thinking aloud, ask for hints, review your code for errors before you submit, offer alternatives, and adapt when the parameters change.

Candidate reports are anecdotes, and they vary. One candidate reported two LeetCode easy or medium problems in one hour. A secondary source reported medium to hard problems, sometimes in a plain editor and without running the code. A report from a Senior SRE software-engineer interview mentions a string compression question. Nebius has not published its problem list. So prepare for the harder version and treat an easy round as a gift.

A realistic question in the interviewer's voice: "Given a stream of request logs, return the k endpoints with the most errors. Write it so I can run it, and tell me what changes if the logs no longer fit in memory."

## The core ideas

### 1. The coding round grades a process, and the code is only the last step

Picture two candidates. One goes silent for six minutes and types a correct solution. The other talks for six minutes, asks two questions, writes a slower solution, and fixes a bug before the interviewer sees it. The second candidate usually scores higher, because the interviewer cannot grade thinking they never heard.

Nebius states what it wants: say your reasoning aloud, ask for hints, review the code before submitting, offer alternatives and adapt if parameters change. That is a list of behaviours, not a list of algorithms. Each behaviour is cheap to practise and each one is visible to the interviewer. A candidate who does all five and writes a slightly clumsy solution beats one who writes an elegant solution in silence.

As an SRE you already do this in incidents. You state a hypothesis, test it, and say what you ruled out. The Systems Performance book, chapter 2, calls the weak alternative the streetlight anti-method. You try the tool you already know, not the one the problem needs. In a coding round the same trap is reaching for the first pattern you remember. **Treat the interview as a short incident: state the problem, form a hypothesis, test it, and narrate.**

### 2. The 60-minute structure

An hour with one or two problems leaves little slack. If there are two problems, you have about 25 minutes each plus a buffer. If there is one problem, the interviewer will probably add a follow-up. Use the same seven steps every time, so you never wonder what to do next.

```mermaid
flowchart LR
  A["1 Clarify<br/>2 min"] --> B["2 Examples<br/>3 min"]
  B --> C["3 Brute force<br/>3 min"]
  C --> D["4 Optimise<br/>5 min"]
  D --> E["5 Code<br/>10 min"]
  E --> F["6 Test by hand<br/>5 min"]
  F --> G["7 Complexity<br/>2 min"]
  F -.->|"bug found"| E
  D -.->|"stuck"| C
```

Clarify means asking about input size, input type, duplicates, empty input, and what to return when there is no answer. Examples means writing two small cases and one edge case on the screen, with the expected output. Brute force means saying the obvious solution and its cost, even if you will not code it. Optimise means asking what the brute force repeats, then removing that repetition with a hash map, a sort, a heap or a window.

Code, test and complexity come last. The times above are my planning figures for a 25-minute problem, not Nebius requirements. If you spend 15 minutes before the first line of code, you will be rushed. If you spend none, you will rewrite. **Say the brute force out loud before you try to be clever, because it proves you can solve the problem and gives you a baseline to improve.**

### 3. Clarify and use examples as a specification

An interviewer says: "Compress a string." That is not a specification. Does "aabcccccaaa" become "a2b1c5a3" or "a2bc5a3"? What if the result is longer than the input? Is the input only lowercase letters? These questions are not stalling. The string compression question reported by one candidate has at least three valid readings, and each one gives a different function.

Ask three kinds of question. Ask about the input: size, type, range, sorted or not, duplicates, can it be empty. Ask about the output: what to return when nothing matches, whether order matters, whether ties need a rule. Ask about the environment: does it fit in memory, is it called once or many times, can I use the standard library.

Then write the examples as the interviewer's contract. In the harness later in this chapter, an example is a pair of arguments and expected value, so your examples become tests with no extra typing. If you wrote "aaa goes to a3" and "abc stays abc", you have also settled the rule for results that are not shorter. **State your assumptions as examples, and let the interviewer correct them in the first three minutes instead of the last three.**

### 4. How to think aloud without rambling

Thinking aloud is a skill with a shape. Use short, structured sentences with a fixed vocabulary. "My first idea is a double loop, which is quadratic. The repeated work is looking up a complement, so a dictionary should make that constant time. I will check with the example." That takes ten seconds and it gives the interviewer three things to react to.

Avoid two failure modes. The first is silence. The second is narrating every keystroke, which buries the useful parts. Speak at decisions: choosing a structure, choosing a loop bound, handling an edge case. While you type routine lines such as a loop header, silence is fine.

Use these sentence starters until they feel natural. "The input could be..." for clarifying. "The brute force is..., which costs..." for the baseline. "What repeats here is..." for optimising. "I will name this because..." for code. "Let me trace the example." for testing. "If the input no longer fits in memory, then..." for follow-ups.

**Narrate decisions, not keystrokes.**

### 5. Recovering when you are stuck

Every candidate gets stuck. The interviewer is watching what you do next. Nebius's page tells you to ask for hints, which means asking is expected and not a failure. A good request is specific: "I have the sliding window idea but I am not sure when to move the left pointer. Can you confirm the window must contain no repeats?"

Use a fixed checklist when your mind goes blank. First, go back to your smallest example and trace it by hand, writing the state of each variable. Second, say the brute force and its cost, then ask what it recomputes. Third, ask whether sorting the input or using a hash map removes the repeated work. Fourth, solve a smaller version: a shorter input, one fewer constraint. Fifth, ask for a hint, saying what you tried.

If time is nearly gone, deliver something correct and say what is missing. A working brute force with a clear statement of "this is quadratic, and here is the improvement I would make" scores better than half a clever solution that does not run. Switching to the brute force is not giving up. It is the same decision you make in an incident when you roll back instead of debugging live.

**When stuck, shrink the example, never the silence.**

### 6. Writing code that runs first time in a plain editor

A secondary source says some rounds use a plain editor and do not let you run the code. Assume the worst. In that case, the main danger is not the algorithm. It is a typo, an off-by-one error, or a variable that was never defined. The defence is writing in a style that is easy to read back.

Four habits do most of the work. Use names that say what the thing is: `last_seen`, not `d`; `run_len`, not `c`. Write small functions, each doing one job, so you can test them in your head. Prefer a plain loop over a clever one-liner, because a loop can be traced line by line. Handle the empty input first, with an early return, because that is where most bugs live.

Avoid tricks you cannot explain. A nested comprehension with a conditional and two function calls will take you longer to check than three plain lines. Avoid reusing one variable for two meanings. Avoid mutating the input unless the interviewer asks for it. Also write the function signature and a one-line docstring first, because the docstring is a written contract you can test against.

Here is the string compression function from the practice code. Read it as a model of the style: one pass, named state, early return for empty input, and a documented assumption.

```python
def compress(s):
    """'aabcccccaaa' -> 'a2b1c5a3'. Return s if the result is not shorter.

    Ask first: should a single letter keep its '1'? Here it does.
    """
    if not s:
        return s
    parts = []
    run_char, run_len = s[0], 1
    for ch in s[1:]:
        if ch == run_char:
            run_len += 1
        else:
            parts.append(run_char + str(run_len))
            run_char, run_len = ch, 1
    parts.append(run_char + str(run_len))
    packed = "".join(parts)
    return packed if len(packed) < len(s) else s
```

The line after the loop is the classic bug. The last run is never closed inside the loop, so you must append it after. Many first attempts forget this. Building a list and joining at the end also matters. Python strings cannot change, so repeated `+=` can copy the string each time. The Python 3.12 FAQ says the total cost of concatenating many strings is quadratic in the total length in the general case, and recommends a list and `str.join`. CPython sometimes grows a plain local variable in place, so the slowdown does not always show. In a test on 2026-11-09, 200,000 appends took 0.007 s in a plain local loop but about 0.37 s once a second name referred to the string. The list and join version took 0.0035 s. Do not rely on the in-place shortcut in an interview.

**Write the plain version, trace it once, and only then consider whether it needs to be shorter.**

### 7. Testing by hand with edge-case checklists

The interviewer asked you to "review code for errors before submitting", in the official page's words. Do it in a fixed order. Trace the example you wrote at the start. Then trace the smallest input. Then trace one input that hits the special branch, such as a repeat at the end of the string. Say the values of the variables as you go.

An edge-case checklist saves you from inventing cases under pressure. Keep one per input type and run through it every time. The practice code stores them in `EDGE_CHECKLISTS`.

| Input type | Probes to try |
|---|---|
| String | empty, one character, two equal characters, all same, mixed case, spaces |
| List | empty, one item, duplicates, all equal, negatives, already sorted, reverse sorted |
| Two lists | both empty, one empty, same length, different lengths |
| Intervals | empty, one, touching ends, one inside another, out of order |
| Number | 0, 1, -1, a very large value, a float such as 0.1 + 0.2 |

For anything with state, add three more probes: first call, repeat call, and call after reset. For anything with a window, probe a window larger than the input. For anything with a limit, probe exactly the limit, one under and one over.

Two further techniques help. A **stress test** compares your fast solution with an obvious slow one on many small random inputs. You can run it only when code runs, but it catches the bugs that hand tracing misses, so use it in your practice. The other technique is to deep-copy the input before each call, so that a function that changes its input cannot hide a bug in the next case. Both are in the harness below.

**Run the checklist for the input type before you say "I think it works".**

### 8. A reusable harness for practice

Practice should feel like the interview. This harness is small enough to retype from memory in a plain editor. It takes a function and a list of cases, runs each case on a deep copy of the arguments, catches exceptions, compares in exact, unordered or tolerance mode, and prints a line per case with the time. `stress` compares a fast and a brute solution on random inputs.

```python
# code/part20/c08_check.py
"""A tiny testing harness for the coding round (chapter 20.8).

Paste the part you need into a plain editor. It uses only the standard library.
"""
import copy
import math
import random
import time


def _same(got, want, unordered, tol):
    if unordered:
        try:
            got, want = sorted(got), sorted(want)
        except TypeError:
            pass
    if tol is not None and isinstance(got, float) and isinstance(want, float):
        return math.isclose(got, want, rel_tol=tol, abs_tol=tol)
    return got == want


def check(fn, cases, unordered=False, tol=None, verbose=True):
    """Run fn on (args, expected) pairs. Return the list of failures.

    Each call gets a deep copy of args, so a function that changes its
    input cannot hide a bug in the next case. An exception counts as a failure.
    """
    failures = []
    for i, (args, want) in enumerate(cases):
        if not isinstance(args, tuple):
            args = (args,)
        start = time.perf_counter()
        try:
            got = fn(*copy.deepcopy(args))
        except Exception as exc:  # report, do not stop
            got = "raised %s: %s" % (type(exc).__name__, exc)
            ok = False
        else:
            ok = _same(got, want, unordered, tol)
        ms = (time.perf_counter() - start) * 1000
        if verbose:
            print("%-4s case %d args=%r got=%r want=%r (%.2f ms)"
                  % ("ok" if ok else "FAIL", i, args, got, want, ms))
        if not ok:
            failures.append((i, args, got, want))
    if verbose:
        print("%d of %d passed" % (len(cases) - len(failures), len(cases)))
    return failures


def stress(fast, brute, make_input, runs=300, seed=0):
    """Compare a fast solution with a slow obvious one on random small input.

    Returns the first input where they differ, or None.
    """
    rng = random.Random(seed)
    for _ in range(runs):
        args = make_input(rng)
        if fast(*copy.deepcopy(args)) != brute(*copy.deepcopy(args)):
            return args
    return None
```

Use it like this. Each case is a pair of arguments and the expected result. Pass a tuple for several arguments.

```python
from c08_check import check
from c08_edge_cases import compress

check(compress, [("", ""), ("aaa", "a3"), ("abc", "abc")])
```

The file `code/part20/c08_edge_cases.py` holds six solved problems with the checklists as a dictionary. Its tests in `test_c08_edge_cases.py` run each function against its edge cases. Reading the tests is the fastest way to see what a good checklist looks like. The functions are `compress`, `two_sum`, `top_k_frequent`, `merge_intervals`, `valid_brackets` and `longest_unique_window`. Their patterns, such as windows and heaps, are taught in c20-09 and the larger set of problems is in c20-11.

The tests in `test_c08_check.py` check the harness itself, including the case where a function mutates its input and the case where a faulty fast solution is caught by `stress`. A harness you do not trust is worse than none.

**Retype the harness once a week until you can write it in five minutes.**

### 9. Python tools that save time

You are strong in Python, so the point here is to know exact behaviours, because the interviewer will ask "what does that return?" Every result below was produced by running `code/part20/c08_stdlib_tour.py` under Python 3.12.7 on 2026-11-09. The Fluent Python book, chapter 3, says that dict keeps insertion order since Python 3.6, which matters later.

| Tool | Exact behaviour verified |
|---|---|
| `Counter("abracadabra").most_common(2)` | `[('a', 5), ('b', 2)]` |
| `Counter()["z"]` for a missing key | `0`, and the key is not added |
| `Counter("ab") + Counter("bc")` | `Counter({'b': 2, 'a': 1, 'c': 1})` |
| `defaultdict(list)` after only reading `d["missing"]` | the key now exists with `[]` |
| `deque([1,2,3], maxlen=3)` then `append(4)` then `appendleft(0)` | `[0, 2, 3]`, items fall off the other end |
| `heapq.heapify` then `heappop` on `[5,1,4]` | pops `1`, so it is a min-heap |
| `heapq.nlargest(2, [5,1,4,9])` | `[9, 5]` |
| `bisect_left` and `bisect_right` for 2 in `[1,2,2,2,5]` | `1` and `4` |
| `bisect_left` for 3 in the same list | `4`, the insertion point |
| `accumulate([1,2,3,4])` | `[1, 3, 6, 10]` |
| `pairwise("abcd")` | `[('a','b'), ('b','c'), ('c','d')]` |
| `groupby("aabbbc")` run lengths | `[('a',2), ('b',3), ('c',1)]` |
| `len(list(product("ab", repeat=3)))` | `8` |
| `fib(30)` with `lru_cache`, then `cache_info().misses` | `832040` and `31` |
| `statistics.median([1,2,3,4])` | `2.5` |
| `statistics.quantiles([1,2,3,4,100], n=4)` | `[1.5, 3.0, 52.0]` |
| `statistics.mean([1,2,3,4,100])` against `median` | `22` against `3` |

Several of these are answers to follow-up questions. A max-heap does not exist in `heapq`, so negate the values on the way in and out. `bisect_left` finds the first position where you could insert and keep order, so it is the lower bound. `groupby` only groups neighbouring equal keys, so you must sort first, as the pitfalls below show. `pairwise` needs Python 3.10 or newer.

A dataclass with `order=True` compares fields in order, and `field(compare=False)` removes a field from comparison. In the tour, `Job(1, "x") == Job(1, "y")` is `True` for that reason. This is useful for putting jobs on a heap. A regular expression with named groups gives readable log parsing, and the tour parses `10.0.0.7 - GET /v1/chat 503 12ms` into the address, status and latency. The mean of 22 against the median of 3 is the one-line reason that SREs quote percentiles and not averages.

The Learning Python book, chapter 16 onwards, and Fluent Python give the language-level background. The handbook's own Python chapters cover it in depth: [idiomatic Python, the data model, comprehensions and generators](../part-03-python/03-idiomatic-python-the-data-model-comprehensions-generators.md) and [functions, scopes and arguments](../part-03-python/14-functions-scopes-and-arguments-in-depth.md). Do not re-read them for the round. Use them to fill the gaps the harness shows you.

**Know the five or six tools by exact behaviour, and say which one you chose and why.**

### 10. Go equivalents, briefly

Nebius names Go as an acceptable language. If you are weaker in Go than Python, use Python, because the interview grades problem solving and not language choice. If you do use Go, know that it has no built-in counter, no heap function and no ordered-set type. The standard library gives you `map`, `container/heap`, `sort.Slice`, `sort.SliceStable` and `sort.SearchInts`.

The file below was run with Go 1.23.2. `go vet` and `go test` both passed. The Go test file has to end in `_test.go`, which is why it does not follow the `test_c08_` prefix.

```go
# code/part20/c08_go/c08_toolkit.go
// code/part20/c08_go/c08_toolkit.go
// Go equivalents of the Python toolkit in chapter 20.8.
package c08toolkit

import (
	"container/heap"
	"sort"
)

// Count is Counter: a map with a zero default for missing keys.
func Count(s string) map[rune]int {
	m := map[rune]int{}
	for _, r := range s {
		m[r]++
	}
	return m
}

// intHeap is a min-heap of ints, the shape heapq gives you for free in Python.
type intHeap []int

func (h intHeap) Len() int           { return len(h) }
func (h intHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h intHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *intHeap) Push(x any)        { *h = append(*h, x.(int)) }
func (h *intHeap) Pop() any {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[:n-1]
	return x
}

// TopK returns the k largest values, largest first, using a size-k min-heap.
func TopK(nums []int, k int) []int {
	h := &intHeap{}
	for _, v := range nums {
		heap.Push(h, v)
		if h.Len() > k {
			heap.Pop(h)
		}
	}
	out := make([]int, h.Len())
	for i := len(out) - 1; i >= 0; i-- {
		out[i] = heap.Pop(h).(int)
	}
	return out
}

// LowerBound is bisect_left: first index whose value is >= x.
func LowerBound(a []int, x int) int { return sort.SearchInts(a, x) }

// Pair is a row used to show that SliceStable keeps equal keys in input order.
type Pair struct {
	Name string
	Rank int
}

func SortByRank(p []Pair) []Pair {
	out := append([]Pair(nil), p...)
	sort.SliceStable(out, func(i, j int) bool { return out[i].Rank < out[j].Rank })
	return out
}

// MergeIntervals merges closed intervals; touching intervals merge.
func MergeIntervals(in [][2]int) [][2]int {
	a := append([][2]int(nil), in...)
	sort.Slice(a, func(i, j int) bool { return a[i][0] < a[j][0] })
	var out [][2]int
	for _, iv := range a {
		if n := len(out); n > 0 && iv[0] <= out[n-1][1] {
			if iv[1] > out[n-1][1] {
				out[n-1][1] = iv[1]
			}
		} else {
			out = append(out, iv)
		}
	}
	return out
}
```

The differences to remember are these. A missing map key returns the zero value, so `m[r]++` works without a default dictionary. A heap needs five methods because it is an interface. `sort.Slice` is not stable, so use `sort.SliceStable` if equal keys must keep their order. A string is a byte sequence, and ranging over it yields runes. This costs a candidate who treats a string as an array of characters.

**Pick the language you can write without looking things up, and say why.**

### 11. Pitfalls that cost points

These are the errors that wreck a correct idea. All of them are in `code/part20/c08_pitfalls.py`, with tests. The outputs below were run on Python 3.12.7.

A mutable default is shared between calls. Fluent Python, chapter 6, shows it with a bus class and says the fix is `None` as the default. Learning Python, chapter 18, warns the same way. Calling `append_bad(1)` and then `append_bad(2)` returns the same list object both times, holding `[1, 2]`. The good version, which creates the list inside the function, returns `[1]` then `[2]`.

Integer division differs from float division. Python gives `7 / 2` as `3.5` and `7 // 2` as `3`. Floor division rounds toward minus infinity, so `-7 // 2` is `-4`, and `-7 % 3` is `2`. This matters in binary search midpoints and in modular arithmetic on negative numbers.

Multiplying a list copies references. The grid `[[0] * 2] * 2` holds the same row twice, so setting one cell changes both rows: `[[1, 0], [1, 0]]`. Build the grid with a comprehension instead and you get `[[1, 0], [0, 0]]`.

Slicing makes a copy. `data[1:4]` is a new list, and changing it does not change `data`. On a list of one million items, I measured `a[1:]` at about 2.7 ms on this Mac. So a loop that slices on every step, such as `s[1:]` in a recursion, turns a linear algorithm into a quadratic one. Pass indexes instead. Similarly `list.pop(0)` moves every other item. On a 100,000-item list I measured about 14 microseconds per `pop(0)` and `append`, against about 0.05 for a `deque` doing `popleft` and `append`. These are single measurements on my machine, so trust the ratio and not the digits. The Systems Performance book, chapter 2, gives a time-scale table that is the right mental model: a copy goes through memory, so cost scales with size.

The recursion limit is 1000 by default. `sys.getrecursionlimit()` returned `1000`, and recursing 5000 deep raised `RecursionError`. For a depth that large, write the loop or use an explicit stack. Raising the limit is a risky answer. The Python 3.12 documentation for `sys.setrecursionlimit` says a too-high limit can lead to a crash, because the limit exists to protect the C stack. In my test on Python 3.12.7, a pure Python function recursed 5,000,000 deep after raising the limit without crashing, so the risk depends on the version and on recursion through C code. Treat the crash as a documented risk and not as something you can reproduce on demand.

Dictionary order is insertion order, and Fluent Python, chapter 3, confirms it. In the run, adding `z` then `a` gave the key list `['z', 'a']`. Two dicts with the same items but different insertion order still compare equal. So you can rely on order for output, but not for equality.

Sorting is stable. Sorting `[("b",1),("a",1),("c",0)]` by the second field gave `[('c',0),('b',1),('a',1)]`, and the two items with rank 1 kept their input order. In Go, use `SliceStable` for the same promise.

Floats do not compare exactly. `0.1 + 0.2 == 0.3` is `False` and `math.isclose(0.1 + 0.2, 0.3)` is `True`. Use integers for money and counts, and use a tolerance for measurements.

Changing a list while looping over it skips items. Removing the even numbers from `[2, 4, 6, 8]` inside a `for` loop left `[4, 8]`. Build a new list, or loop over a copy.

`itertools.groupby` groups only neighbours. Running it on the unsorted string "aabaa" gave `[('a', 2), ('b', 1), ('a', 2)]`, so `a` appears twice. Sort first, or use a `Counter`.

**Before you submit, scan your code for each of these ten, and say that you did.**

### 12. Follow-ups: when the parameters change

Nebius lists "adapt if parameters change". Expect the interviewer to say: "Now the input has a billion lines." Or: "Now it must be thread-safe." Or: "Now the list is sorted." These are not traps. They test whether you understand why your solution works.

Prepare standard answers. If the data does not fit in memory, process it as a stream and keep only counters, or use a bounded heap of size k. If it must be thread-safe, say which operations need a lock and where. If the input is already sorted, say what you can now skip, such as the sort or the hash map. If the time limit is tight, say what you would trade, such as memory for speed.

For the top-k errors question at the start, the answer has three layers. The simple version counts with a `Counter` and takes `most_common(k)`. The memory-bounded version keeps a heap of size k over the counts. When the number of distinct endpoints is itself too large, you split the input by a hash of the endpoint so each worker holds only its share of keys, then merge the per-worker top-k lists. The last step is my reasoning and not a Nebius answer.

**When the parameters change, say what assumption in your solution just broke.**

### 13. A four-week practice routine

The plan fits a person with a job. It is my suggestion and not a Nebius requirement. Budget about five hours a week. The problem set is in c20-11 and the patterns are in c20-09.

| Week | Focus | Time budget |
|---|---|---|
| 1 | Language basics: dicts, counters, sorting, strings, the harness. Do 6 easy problems in plain-editor mode with no running code, then run the harness. | 5 sessions of 1 hour |
| 2 | Core patterns: hash maps, two pointers, sliding window, stacks. Do 8 problems, each 25 minutes, narrating aloud. | 4 sessions of 75 minutes |
| 3 | Heaps, intervals, binary search, graphs. Do 6 problems, plus the stress test for each. Add one Go solution per session if you plan to use Go. | 4 sessions of 75 minutes |
| 4 | Full mock rounds: two problems in 60 minutes, once with a friend who changes the parameters at the end, once recorded. Review pitfalls and complexity. | 3 mocks of 90 minutes, plus review |

Keep a log with the problem, minutes taken, bugs found by hand, bugs found by the harness, and the one thing you would do differently. The harness-found bugs are what to practise on. When the number of harness-found bugs falls to zero for three problems in a row, you are ready for the plain-editor round.

**Practise the process under time pressure, because knowing the answer is not the skill being graded.**

## How to answer out loud

### The first two minutes of any problem

Say: "Let me restate the problem to check I understand it." Restate it in one sentence. Then ask three questions: size of the input, what to return on empty or impossible input, and whether I can use the standard library. Write two examples and one edge example. Then say: "Is that what you meant?"

Expect the interviewer to refine the problem here. Do not take it as a sign that you did something wrong. If they say "use your judgment", write the assumption down on the screen and move on.

### Presenting brute force and the improvement

Say: "The brute force is this, and it costs this much. What it repeats is this. So I will use this structure, and the cost becomes this." Always give cost in both time and extra memory. A sample: "Two nested loops is quadratic time with constant memory. The repeated work is searching for the complement. A dictionary makes that lookup constant on average, so the total is linear time with linear extra memory."

The follow-up to expect is "can you do it in constant memory?" Have a sentence ready on the trade-off, even if you cannot solve it.

### Before running or submitting

Say: "I will trace the first example, then an empty input, then the case where the pattern is at the end." Do it aloud with variable values. When you find a bug, say what it was and why. This is a point-scoring moment, not an embarrassing one.

The follow-up to expect is "what is the complexity?" Give time and space, name the dominant term, and say which step dominates. For `top_k_frequent`, counting is linear in n and the heap step is about n log k in the worst case.

### When the interviewer changes the problem

Say: "That breaks my assumption that the input is small. Let me think about what stays valid." Then name the part of the solution that survives and the part that needs to change. Do not start again from nothing.

### When you do not know

Say: "I do not remember the exact function name. I would look it up, and here is what it does." Then describe the behaviour and write a short version yourself. This is fine in an SRE interview, since the job does not require memorising an API. Guessing a name and presenting it as certain is not fine.

## Worked scenarios

### Scenario 1: string compression, start to finish

Problem: "Compress a string: replace each run of equal characters with the character and the run length."

Clarify. Ask about single characters and results that are longer. Say the assumption: a single letter keeps its 1, and the function returns the original if the result is not shorter.

Examples. `"aabcccccaaa"` gives `"a2b1c5a3"`. `"abc"` gives `"abc"`, because `"a1b1c1"` is longer. `""` gives `""`.

Brute force. Count runs with nested loops, which is quadratic if you rescan. The improvement: one pass with a counter for the current run, and a list of pieces joined at the end. That is linear time and linear extra memory.

Code. The `compress` function earlier. Test by hand. Trace `"aaa"`: `run_char` is `a`, `run_len` becomes 3, the loop ends, the last run is appended, giving `"a3"`, which is shorter than `"aaa"`, so it returns `"a3"`. Trace `"aa"`: the packed form is `"a2"`, which has length 2, not shorter than 2, so it returns `"aa"`. That check is why the comparison is `<` and not `<=`. The unit tests cover these cases and pass.

Follow-up: "What if I want the output in place, in a list of characters?" That needs two pointers, a reader and a writer, and a rule for writing counts above 9 as several characters. I did not implement this variant. Say it is a different function with the same pattern.

### Scenario 2: top error endpoints from a log

Problem: given lines like `10.0.0.7 - GET /v1/chat 503 12ms`, return the three endpoints with the most 5xx responses.

Clarify. Ask whether ties need a rule and what a malformed line should do. Assume ties go to the alphabetically smaller endpoint, and skip malformed lines. State both.

Approach. Parse with a regular expression that has named groups, as in the tour. Count 5xx by endpoint with a `Counter`. Take the top k with `heapq.nsmallest` and a key of negative count then name, which is how `top_k_frequent` gets a deterministic tie-break. Python's `most_common` gives equal counts in first-seen order, which is stable but is not the rule you stated.

Edge cases. An empty log. A line with no status code. All counts equal. `k` larger than the number of endpoints, which `top_k_frequent("ab", 5)` handles by returning both. Test these with the harness.

Follow-up: memory. If the endpoint set is bounded, a `Counter` is fine at any log size, because memory depends on distinct endpoints and not lines. Say that. If the distinct set is huge, shard by hash as described before.

### Scenario 3: you are stuck on merge intervals

Problem: merge overlapping intervals. You have drawn two examples and cannot see the algorithm.

Step one: write the brute force aloud. "For each interval, compare with every other and merge if they overlap, repeat until nothing changes." That is at least quadratic.

Step two: ask what makes the comparison hard. Intervals are in any order, so any pair might overlap. What if they were sorted by start? Then an interval can only overlap the one right before it, since the previous merged interval has the largest end so far.

Step three: write it. Sort, keep a merged list, and for each interval either extend the last merged interval or append. The key line is `start <= merged[-1][1]`, and the `<=` encodes the rule that touching intervals merge. Ask the interviewer if touching intervals should merge, because that is the common ambiguity.

Step four: test. `[(1,2),(2,3)]` gives `[(1,3)]`. `[(1,5),(2,3)]` gives `[(1,5)]`, which tests the `max`. `[(3,4),(1,2)]` tests the sort. The complexity is dominated by the sort, so it is n log n. The Go version in the toolkit passes the same cases.

## Hands-on lab

You will set up the harness and run everything. This took about five minutes on a laptop. I ran steps 1 to 4 on 2026-11-09 with Python 3.12.7, pytest 8.3.5 and Go 1.23.2.

1. Change into the repository root and run the Python tests: `cd code/part20 && python3 -m pytest -q test_c08_*.py`. Expected result: 30 passed. I ran this and saw 30 passed.
2. Run the Go tests: `cd code/part20/c08_go && go vet ./... && go test ./...`. Expected result: `ok  c08toolkit`. I ran this and it passed.
3. Open a Python shell in `code/part20` and run `import c08_stdlib_tour as t; t.statistics_demo()`. Expected result: `(22, 3, 2.5, [1.5, 3.0, 52.0])`. I ran this.
4. Break a function on purpose. In a scratch copy, change `<` to `<=` in `compress`, then run `python3 -m pytest -q test_c08_edge_cases.py`. Expected result: at least one failure on `"aa"`. I did not run this exact mutation, so treat the result as the expected shape. The point is to see the harness catch a boundary bug.
5. Timed drill, which you do alone. Pick one problem from the practice set in c20-11, set a 25-minute timer, open a plain text editor with no autocomplete, and talk aloud while you work. Then run the harness. Count the bugs it finds that you did not find by hand. That count is your real score.

## Drill questions

<details><summary>1. What does Nebius say it wants to see in the coding task?</summary>

Working, testable code in a language of your choice, with Python or Go named as examples. Also that you say your thinking aloud, ask for hints, review the code before submitting, offer alternatives and adapt if parameters change. The topic is classical algorithms and data structures.
</details>

<details><summary>2. What are the seven steps for a problem?</summary>

Clarify, examples, brute force, optimise, code, test by hand, and state the complexity. If testing finds a bug you go back to code, and if you are stuck you go back to the brute force.
</details>

<details><summary>3. Why say the brute force aloud?</summary>

It shows you can solve the problem, it gives a baseline cost, and it shows what repeats, which is where the improvement comes from. It is also a safe answer if time runs out.
</details>

<details><summary>4. You are stuck. What do you do, in order?</summary>

Trace the smallest example by hand. Say the brute force and what it recomputes. Ask whether a sort or a hash map removes that work. Solve a smaller version. Ask for a specific hint and say what you already tried.
</details>

<details><summary>5. What does `heapq.heapify` build, and how do you get a max-heap?</summary>

A min-heap in place, so `heappop` returns the smallest. For a max-heap, push negated values and negate again when you pop.
</details>

<details><summary>6. What do `bisect_left` and `bisect_right` return for 2 in `[1,2,2,2,5]`?</summary>

`1` and `4`. The left one is the first position where 2 could go, and the right one is after the last 2.
</details>

<details><summary>7. Why does `groupby("aabaa")` give three groups?</summary>

It groups only neighbouring equal keys. The two `a` runs are separated by `b`, so you get `a` twice. Sort first or use a `Counter`.
</details>

<details><summary>8. What is wrong with `def f(x, bucket=[])`?</summary>

The default list is created once when the function is defined and is shared by every call that omits it. Use `None` as the default and create the list inside the function.
</details>

<details><summary>9. Why is `s[1:]` inside a recursion a problem?</summary>

Slicing copies, so each step costs time proportional to the remaining length, and the total becomes quadratic. Pass indexes instead. I measured about 2.7 ms for one slice of a million-item list on my laptop.
</details>

<details><summary>10. The interviewer says the log no longer fits in memory. What do you say?</summary>

Process it as a stream. Keep counters for distinct keys, or a heap of size k if you want only the top k. If the distinct keys are too many, shard them by hash across workers and merge the top-k lists. Name the assumption that broke.
</details>

## Common mistakes and weak answers

- Silence for several minutes. Say what you are considering, even if it is only the brute force.
- Coding before examples. Write two examples first. They are your tests, and they settle ambiguity.
- A clever one-liner you cannot trace. Say "I will write the plain version first".
- Forgetting empty input. Say "empty input returns X" before the loop.
- Saying "I think it works" without a trace. Trace an example, an empty input and an end-of-input case aloud.
- Treating a hint as a failure. The official page tells you to ask for hints, so ask a specific one.
- Claiming a complexity you did not work out. Count the loops and the sort, then say time and space.
- Presenting a guessed API name as certain. Say what the function does and write it yourself.
- Over-optimising a problem the interviewer did not ask to optimise. Get a correct solution first, then ask whether to improve it.


## Connections to the rest of the handbook

- c20-09 teaches the SRE-flavoured patterns: log parsing, sliding windows, heaps, intervals, rate limiters and retry with jitter.
- c20-10 covers complexity, latency numbers and how to test your own code aloud.
- c20-11 is the larger practice set with reference solutions.
- c20-07 is the Linux console lab set, the other practical round.
- c20-03 shows the same hypothesis and test method for a sick Linux box.
- The Part 3 chapters on [idiomatic Python](../part-03-python/03-idiomatic-python-the-data-model-comprehensions-generators.md), [functions and arguments](../part-03-python/14-functions-scopes-and-arguments-in-depth.md) and [objects and data structures](../part-03-python/12-objects-types-and-data-structures-in-depth.md) give the language depth.

## Sources and review notes

Sources and dates:

- Nebius SRE interview page, nebius.com/careers/interviews/sre, as recorded in `planning/VOLUME_20_NEBIUS_SRE_PLAN.md` section 1 on 2026-11-09. I did not refetch it. It is tagged official.
- Candidate reports as recorded in the plan, tagged report: two LeetCode easy or medium problems in one hour; a secondary source reporting medium to hard problems and plain editors; one Senior SRE software-engineer report with a string compression question. These are anecdotes.
- Fluent Python, 2nd edition, chapter 3 "Dictionaries and Sets" for insertion order, and chapter 6 "Object References, Mutability, and Recycling" for mutable parameter defaults.
- Learning Python, 6th edition, chapter 18 "Arguments" for mutable defaults.
- Systems Performance, 2nd edition, chapter 2 "Methodologies" for the streetlight anti-method and the time-scale table.
- Code run on 2026-11-09: Python 3.12.7, pytest 8.3.5, Go 1.23.2 on macOS. All behaviours in the tables and pitfalls come from running `c08_stdlib_tour.py` and `c08_pitfalls.py`.

Explicitly labelled inferences:

- The time allocations in the seven-step diagram, the practice routine and the answer outlines are my reasoning.
- The sharding answer to the log follow-up is my reasoning. Nebius has not published its coding problems.
- The advice that Python is safer than Go for a candidate who is stronger in Python is my judgement.

Not verified:

- I did not run the `<` to `<=` mutation in the lab. I did not implement the in-place compression variant.
- The timing figures for slicing and `pop(0)` are single runs on one laptop.
- I could not crash CPython 3.12.7 with a raised recursion limit. The crash claim rests on the documentation only.

### Verification log

Fetched 2026-11-09 from docs.python.org/3.12: the sys page, the programming FAQ and the collections page. Claims checked: 6. Confirmed: 4 (string concatenation cost and `str.join`, recursion limit crash warning, deque against `list.pop(0)` cost, default limit 1000 and `RecursionError` by running). Corrected: 2 (the `+=` claim is now sourced and measured, and the crash claim is now documented with the failed reproduction stated). Removed: 0. Still unverified: 0 factual claims. The sharding answer and the time allocations remain my labelled reasoning, and the laptop timings stay single runs.
- No `chain_gate`, lint or Mermaid gate result is claimed unless stated in the report to the supervisor.
