---
id: "c03-03"
title: "3.3 Idiomatic Python: the data model, comprehensions, generators"
sidebar_label: "3.3 Idiomatic Python: the data model, comprehensions, generators"
sidebar_position: 3
description: "The Python data model and special methods, sequences, mappings and sets, text vs bytes, references, functions as objects, comprehensions, iterators, generators, itertools and lazy pipelines"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.3 Idiomatic Python: the data model, comprehensions, generators

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Any machine with Python 3.11 or newer |
| Part | Part 3: Python for infrastructure |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

"Pythonic" is not decoration; it is how the language and its libraries expect you to behave, and the reason frameworks (pandas, PyTorch, FastAPI, Kubernetes clients) feel consistent. The **data model** (special methods such as `__len__`, `__getitem__`, `__iter__`, `__enter__`) is what makes your own objects work with `len()`, `for`, `with`, `sorted` and slicing. **Comprehensions and generators** are how infrastructure scripts stream gigabytes of logs, paginate cloud APIs, and transform metrics without exhausting memory. Getting them right turns a 40-line loop with a bug into a three-line pipeline you can test. This chapter covers the data model, the sequence/mapping/set types in depth, comprehensions, the iterator protocol, generators and coroutine-style generators, `itertools`/`functools`/`operator`, text vs bytes, object references, and design patterns with first-class functions.

## Prerequisites and outcomes

You should know the core language (chapter 3.1) and modules (3.2).

After this chapter you can:

- Explain the data model: special (dunder) methods, how built-ins and syntax dispatch to them, and implement a small class that behaves like a sequence, mapping, context manager, or numeric type.
- Choose and use sequence types (list, tuple, deque, array, memoryview), slicing and unpacking, sorting and key functions, bisect; mapping and set types (dict, defaultdict, Counter, OrderedDict, ChainMap, MappingProxyType, set operations), and understand hash and equality contracts.
- Write list/dict/set comprehensions and generator expressions, know when not to, and handle scoping rules and the walrus operator in comprehensions.
- Explain iterables, iterators and the iterator protocol; write generator functions, `yield from`, generator pipelines, infinite generators, and send/throw/close semantics; use `itertools` recipes.
- Handle text vs bytes, encodings and normalisation; understand references, aliasing, weak references, and object lifecycle.
- Use first-class functions for patterns (strategy, command, registry, callbacks) instead of class hierarchies.
- Process large inputs in constant memory and paginate APIs lazily.

## 1. The Python data model

The data model defines how objects interact with the language. When you write `len(x)`, `x[i]`, `for a in x`, `x + y`, `with x:` or `print(x)`, Python calls **special methods** on the object's type: `type(x).__len__(x)`, `__getitem__`, `__iter__`, `__add__`, `__enter__`/`__exit__`, `__str__`. Implementing them lets your classes participate in built-in behaviour. You should rarely call dunder methods directly (call `len(x)`, not `x.__len__()`), and you should not invent new ones.

```python
from collections import abc
import math

class Vector:
    """2D vector demonstrating the data model."""
    __slots__ = ("x", "y")                       # fixed attributes: smaller, faster objects

    def __init__(self, x=0.0, y=0.0):
        self.x, self.y = float(x), float(y)

    def __repr__(self):                          # unambiguous, for developers/logs: eval-like
        return f"Vector({self.x!r}, {self.y!r})"
    def __str__(self):                           # for humans
        return f"({self.x}, {self.y})"
    def __eq__(self, other):
        if not isinstance(other, Vector): return NotImplemented     # let Python try the reflected operation
        return (self.x, self.y) == (other.x, other.y)
    def __hash__(self):                          # must agree with __eq__ if instances are used in sets/dict keys
        return hash((self.x, self.y))
    def __abs__(self):  return math.hypot(self.x, self.y)
    def __bool__(self): return bool(abs(self))
    def __add__(self, other):
        if not isinstance(other, Vector): return NotImplemented
        return Vector(self.x + other.x, self.y + other.y)
    def __mul__(self, k):
        if not isinstance(k, (int, float)): return NotImplemented
        return Vector(self.x * k, self.y * k)
    __rmul__ = __mul__                           # 3 * v
    def __iter__(self):                          # unpacking: x, y = v
        yield self.x; yield self.y
```

### Categories of special methods

| Purpose | Methods | Triggered by |
|---|---|---|
| Representation | `__repr__`, `__str__`, `__format__`, `__bytes__` | `repr()`, `print`, f-strings, `bytes()` |
| Truthiness/size | `__bool__`, `__len__` | `if x`, `len(x)` |
| Comparison/hash | `__eq__`, `__lt__`, `__le__`... `__hash__` | `==`, `<`, `sorted`, sets, dict keys; `functools.total_ordering` fills in the rest |
| Arithmetic | `__add__`, `__sub__`, `__mul__`, `__truediv__`, `__floordiv__`, `__mod__`, `__pow__`, `__neg__`, `__abs__` plus reflected `__radd__` and in-place `__iadd__` | operators |
| Container | `__getitem__`, `__setitem__`, `__delitem__`, `__contains__`, `__iter__`, `__reversed__`, `__missing__` | `x[i]`, `in`, `for`, `reversed` |
| Iteration | `__iter__`, `__next__` | `iter()`, `next()` |
| Context managers | `__enter__`, `__exit__` | `with` |
| Callable | `__call__` | `x()` |
| Attribute access | `__getattr__`, `__getattribute__`, `__setattr__`, `__delattr__`, `__dir__`, descriptors `__get__`/`__set__` | `x.a` (chapter 3.11) |
| Lifecycle | `__new__`, `__init__`, `__del__`, `__init_subclass__`, `__class_getitem__` | construction, destruction, subclassing |
| Async | `__aiter__`, `__anext__`, `__aenter__`, `__aexit__`, `__await__` | `async for`, `async with`, `await` (chapter 3.6) |

Design rules: return `NotImplemented` (not raise) for unsupported operand types so Python can try the other operand; keep `__eq__` and `__hash__` consistent (equal objects must hash equal; mutable objects should not be hashable); make `__repr__` always useful (include the identifying fields); prefer composition and the abstract collection base classes (`collections.abc.Sequence`, `Mapping`, `MutableMapping`) which supply many methods once you implement a few.

### A sequence by protocol

```python
class Fleet(abc.Sequence):
    """Immutable ordered collection of host names; gets index, count, iteration, 'in', reversed for free."""
    def __init__(self, hosts): self._hosts = list(hosts)
    def __len__(self): return len(self._hosts)
    def __getitem__(self, i):
        if isinstance(i, slice): return Fleet(self._hosts[i])      # slicing returns the same type
        return self._hosts[i]
    def __repr__(self): return f"Fleet({self._hosts!r})"

f = Fleet(["gpu01", "gpu02", "gpu03"])
len(f), f[0], f[-1], f[1:], "gpu02" in f, list(reversed(f)), f.index("gpu03")
```

Only `__len__` and `__getitem__` were needed. This is the essence of **duck typing with protocols**: anything with the right methods plugs in.

### Context managers

```python
from contextlib import contextmanager
import time

class Timer:
    def __enter__(self): self.t0 = time.perf_counter(); return self
    def __exit__(self, exc_type, exc, tb):
        self.elapsed = time.perf_counter() - self.t0
        return False                                  # do not swallow exceptions

@contextmanager
def drained(node):
    cordon(node); drain(node)
    try:
        yield node                                    # body of the with statement runs here
    finally:
        uncordon(node)                                # always executes, even on errors
with drained("gpu07") as n: upgrade(n)
```

`contextlib` also provides `suppress`, `closing`, `redirect_stdout`, `ExitStack` (manage a dynamic number of resources), `nullcontext`, `chdir` (3.11), and `asynccontextmanager`. Use `with` for files, locks, sockets, temporary directories, DB transactions, timers, and any acquire/release pair.

## 2. Sequences

### The sequence family

Container sequences hold references to objects (list, tuple, `collections.deque`); flat sequences hold values of one type contiguously (`str`, `bytes`, `bytearray`, `memoryview`, `array.array`). Mutable: list, deque, bytearray, array; immutable: tuple, str, bytes.

```python
# slicing: seq[start:stop:step]; half-open; negative indices; slice objects are first class
data = list(range(10))
data[2:7:2], data[::-1], data[-3:], data[:0]
data[2:5] = ["a", "b"]           # slice assignment (lists): replaces and can change length
del data[::2]
s = slice(0, 4); data[s]

# unpacking
first, *middle, last = data
(a, b), c = (1, 2), 3
for host, (cpu, mem) in {"a": (8, 64), "b": (16, 128)}.items(): ...
def f(a, b, c): ...
f(*[1, 2, 3]); f(**{"a": 1, "b": 2, "c": 3})

# sorting
nodes.sort(key=lambda n: (n.rack, -n.gpus, n.name))      # stable, multi-key, descending on one key
from operator import itemgetter, attrgetter
sorted(rows, key=itemgetter("rack", "name")); sorted(objs, key=attrgetter("rack", "name"))
import bisect; i = bisect.bisect_left(sorted_list, x); bisect.insort(sorted_list, x)
heapq.nlargest(5, items, key=...)      # top-k without full sort
```

Notes: `sort()` sorts in place and returns `None`; `sorted()` returns a new list. Python's sort (Timsort) is stable and O(n log n) with O(n) best case on partially ordered data. Use `key=` instead of `cmp`. **Tuple comparison** is lexicographic. **`list.insert(0, x)` and `list.pop(0)` are O(n)**: use `collections.deque` (`appendleft`, `popleft`, `maxlen=N` ring buffers, ideal for recent-N windows of metrics or log lines).

```python
from collections import deque
recent = deque(maxlen=1000)           # keeps only the last 1000 entries
recent.append(sample)
from array import array
temps = array("f", [71.0, 72.5])      # compact numeric storage (4 bytes each) vs list of float objects (~32 bytes each)
mv = memoryview(bytearray(1024)); chunk = mv[100:200]     # zero-copy views over binary buffers (sockets, mmap, NumPy)
```

**Augmented assignment** on mutable sequences mutates in place (`a += [1]` extends the shared list); on tuples/strings it rebinds. The famous puzzle `t = ([1], 2); t[0] += [3]` raises `TypeError` *and* mutates the list, because the in-place add succeeds before the failed item assignment. **Named tuples** (`collections.namedtuple`, `typing.NamedTuple`) give tuple semantics with named fields (chapter 3.4 compares them to dataclasses).

### Memory and performance notes

- Lists store pointers (8 bytes each on 64-bit) to separate objects: a list of one million floats costs about 32 MB plus the objects; use NumPy arrays or `array` for numeric bulk data (chapter 3.10).
- Prefer comprehensions and built-ins (`sum`, `max`, `any`, `all`, `join`) over manual loops for speed and clarity.
- `x in list` is linear; convert to a `set` for repeated membership tests.
- `copy.copy`, slicing and `list()` make shallow copies.

## 3. Mappings and sets

```python
d = {"gpu01": 8, "gpu02": 8}
d["gpu03"] = 4; d.get("x", 0); d.pop("gpu01"); d.setdefault("gpu04", 8); d |= {"gpu05": 2}; dict(zip(keys, values))
{k: v for k, v in d.items() if v >= 8}; sorted(d.items(), key=lambda kv: kv[1], reverse=True)
for k in list(d):                       # iterate over a copy of keys if you delete
    if d[k] == 0: del d[k]
```

- **Hashing contract**: keys must be hashable (hash never changes, `a == b` implies `hash(a) == hash(b)`). Dict and set lookups are O(1) on average because of hashing; many collisions degrade to O(n).
- **Ordering**: dicts preserve insertion order (guaranteed since 3.7); `OrderedDict` adds `move_to_end` (useful for LRU caches) and order-sensitive equality.
- **`defaultdict(factory)`** creates missing values on access (`defaultdict(list)` to group, `defaultdict(int)` to count); `__missing__` lets subclasses of `dict` customise missing-key behaviour.
- **`Counter`**: multiset with `most_common`, arithmetic (`c1 + c2`, `c1 - c2`), `update`.
- **`ChainMap`**: layered lookups without copying: configuration precedence (`ChainMap(cli_args, os.environ, file_cfg, defaults)`).
- **`types.MappingProxyType(d)`** read-only view; `dict.keys()/items()` are live views supporting set operations.
- **Sets**: `{1, 2}`, `set(iterable)`, `|`, `&`, `-`, `^`, `<=` (subset), `isdisjoint`; elements must be hashable; `frozenset` for hashable sets. Great for diffing desired vs actual state, deduplication (note: unordered; for ordered dedupe use `dict.fromkeys(items)`).
- **Equality of different containers**: `{1: "a"} == {1: "a"}` True regardless of order; lists compare order-sensitively; `1 == 1.0 == True` and they hash equal, so `{1, 1.0, True}` has one element.
- **Nested defaults**: `defaultdict(lambda: defaultdict(list))` for two-level grouping; for deeply nested configuration prefer typed models (chapter 3.4).
- **Merging**: `a | b`, `{**a, **b}`, `ChainMap`; deep merges require recursion.

```python
from collections import defaultdict, Counter, ChainMap
by_rack = defaultdict(list)
for n in nodes: by_rack[n["rack"]].append(n["name"])
errors = Counter(e["code"] for e in events)
cfg = ChainMap({"retries": 5}, {"retries": 3, "timeout": 10})        # first mapping wins
cfg["timeout"], cfg["retries"]
```

## 4. Text versus bytes

(Expanded in chapter 3.5; the essentials here.)

- **`str`** is Unicode text (sequence of code points); **`bytes`** is binary data. Convert only at the boundaries: decode bytes to text on input (`data.decode("utf-8")`), encode text to bytes on output (`s.encode("utf-8")`).
- **Encodings**: UTF-8 is the default for new work; ASCII subset; Latin-1 maps bytes 1:1 to code points 0 to 255 (useful to carry arbitrary bytes through text APIs); `errors="replace"|"ignore"|"surrogateescape"|"backslashreplace"|"strict"` control failures. `locale.getpreferredencoding()` varies by environment (containers with `LANG=C` surprise people); always pass `encoding="utf-8"` to `open()`.
- **Unicode pitfalls**: the same visible text can have different code point sequences (`é` as one code point or `e` + combining accent): normalise with `unicodedata.normalize("NFC", s)` before comparing; `str.casefold()` for caseless matching; `len()` counts code points, not bytes or visual characters (graphemes); sorting is by code point (use `locale.strxfrm` or ICU for human order).
- **Bytes API**: `bytes` indexing returns ints; `b"abc"[0] == 97`; `bytes.hex()`, `bytes.fromhex`, `int.from_bytes`, `struct.pack/unpack` for binary protocols, `base64`, `hashlib` (bytes in, bytes out).
- Subprocess output, socket reads and file reads in binary mode are bytes; JSON/YAML/regex operate on text.

## 5. Object references, mutability and recycling

- **Variables are labels**; assignment binds; function arguments are passed by "object reference" (the callee gets a new name bound to the caller's object): mutating a mutable argument is visible to the caller; rebinding is not.
- **Identity, equality, interning, small-int caching** (chapter 3.1); `del` removes a name, not an object; the object disappears when its reference count hits zero.
- **Weak references**: `weakref.ref(obj)`, `WeakValueDictionary`, `WeakSet` allow caches and registries that do not keep objects alive.
- **Copy semantics in APIs**: functions should not mutate arguments unless documented; return new objects for pure functions; use tuples/frozen dataclasses for values.
- **`__del__`** is unreliable for cleanup; use context managers, `try/finally`, or `weakref.finalize`.
- **Garbage collector**: `gc.collect()`, `gc.get_stats()`, `gc.freeze()` before forking workers (reduces copy-on-write memory growth in preforking servers, relevant to inference and data-loader workers).

## 6. Functions as objects and patterns

Functions are instances of `function`, with attributes (`__name__`, `__doc__`, `__defaults__`, `__code__`, `__annotations__`), callable, passable and returnable.

```python
def apply(fn, items): return [fn(i) for i in items]
callable(apply); apply.__name__; apply.__defaults__
```

Patterns that replace class hierarchies:

- **Strategy**: pass the function (`sort(key=...)`, `retry(fn)`), or a dict of functions: `ACTIONS = {"start": start, "stop": stop}; ACTIONS[cmd](*args)`.
- **Registry via decorator**: 

```python
HANDLERS = {}
def handler(event_type):
    def register(fn):
        HANDLERS[event_type] = fn
        return fn
    return register

@handler("node_down")
def on_node_down(ev): ...
HANDLERS[ev["type"]](ev)
```

- **Command objects**: `functools.partial(deploy, app="api", env="prod")` creates a pre-bound callable you can queue or schedule.
- **Callbacks and hooks**: pass functions to libraries (signal handlers, `atexit.register`, progress callbacks).
- **Callable objects** (`__call__`) hold state (a rate limiter instance) while behaving like functions.
- **`functools`**: `lru_cache(maxsize=...)`/`cache` memoise pure functions (arguments must be hashable; watch memory and staleness for functions depending on external state); `cached_property`; `singledispatch` (overload by first argument type); `total_ordering`; `reduce`; `wraps` (preserve metadata in decorators; chapter 3.11).
- **`operator`** module: `itemgetter`, `attrgetter`, `methodcaller`, `add`, `mul` replace trivial lambdas.
- **Higher-order built-ins**: `map`, `filter`, `sorted(key=)`, `min/max(key=)`, `any/all`, `sum`.

## 7. Comprehensions

Comprehensions build collections declaratively from iterables, in one expression, usually faster and more readable than the equivalent loop.

```python
squares   = [n * n for n in range(10)]
evens     = [n for n in range(20) if n % 2 == 0]
labels    = ["even" if n % 2 == 0 else "odd" for n in range(5)]          # conditional expression goes BEFORE 'for'
pairs     = [(r, n) for r in racks for n in nodes_in(r)]                 # nested loops: read left to right like nested for statements
matrix_t  = [[row[i] for row in matrix] for i in range(len(matrix[0]))]  # transpose
flat      = [x for sub in nested for x in sub]
by_name   = {n.name: n for n in nodes}                                    # dict comprehension
inverse   = {v: k for k, v in mapping.items()}
racks     = {n.rack for n in nodes}                                       # set comprehension
lazy      = (len(line) for line in lines)                                 # generator expression: no list built
total     = sum(n.gpus for n in nodes)                                    # generator expression as sole argument: no extra parentheses
```

Rules and gotchas:

- **Scope**: in all comprehension forms (list, set, dict, and generator expressions), the `for` loop variable lives in the comprehension's own nested scope and does not leak into or overwrite names in the enclosing scope (unlike a regular `for` loop statement). However, a named assignment expression (`:=`) inside a comprehension **does** leak out and binds its target variable in the **enclosing scope** (and `yield` inside a comprehension is forbidden):

```python
# In the book's examples (untested here):
X = 99
[X for X in range(5)]                                  # [0, 1, 2, 3, 4]; outer X is still 99
for X in range(5): pass                                # regular for statement changes outer X to 4

S = 'hack'
[(temp := S[i]) + temp.upper() for i in range(len(S))] # ['hH', 'aA', 'cC', 'kK']
# temp == 'k' in the enclosing scope, whereas i raises NameError: name 'i' is not defined
```

- **Walrus** avoids recomputation: `[y for x in data if (y := expensive(x)) is not None]`.
- **Readability limit**: more than two `for`/`if` clauses, or side effects, belong in a loop. Do not use comprehensions for side effects (`[print(x) for x in xs]` builds a useless list).
- **Memory**: list comprehensions materialise everything; use generator expressions to feed `sum`, `any`, `all`, `max`, `sorted`, `",".join`, `set(...)`, `tuple(...)` when you don't need the list.
- **Filtering and mapping combined** is where they shine; `map`/`filter` with named functions are fine when the function exists already.
- **Performance**: comprehensions avoid repeated attribute lookups (`list.append`) and are typically 20 to 50% faster than equivalent loops; but algorithmic choices (set vs list) matter far more.
- **Pitfalls**: modifying the source while comprehending; building lists of lists with shared references (use the comprehension form `[[0]*c for _ in range(r)]`); catching exceptions inside (not possible: wrap in a function).

```python
# Parse "key=value" pairs from an environment-style file, ignoring comments and blanks
env = {
    k.strip(): v.strip()
    for line in Path("/etc/default/myapp").read_text().splitlines()
    if (line := line.strip()) and not line.startswith("#") and "=" in line
    for k, _, v in [line.partition("=")]
}
```

## 8. Iterables, iterators and generators

### The iterator protocol

- An **iterable** has `__iter__()` returning an iterator (lists, dicts, files, strings, sockets' makefile, generators...).
- An **iterator** has `__next__()` (returns the next item or raises `StopIteration`) and `__iter__()` returning itself. Iterators are **single pass** and stateful.
- `for x in obj:` is `it = iter(obj)` then `while True: x = next(it)` until `StopIteration`. Unpacking, `list()`, `sum()`, `in`, `zip`, `enumerate`, comprehension all consume iterables the same way.
- `iter(callable, sentinel)` builds an iterator from a function until it returns the sentinel: `for block in iter(lambda: f.read(65536), b""):` reads a file in chunks.
- **Reuse bug**: iterating a generator or `map`/`filter`/`zip` object twice yields nothing the second time. Convert to a list/tuple if you need two passes, or recreate the iterator; use `itertools.tee` carefully (it buffers).

```python
class Countdown:
    """Iterable producing a fresh iterator each time (restartable)."""
    def __init__(self, n): self.n = n
    def __iter__(self):
        n = self.n
        while n > 0:
            yield n
            n -= 1
list(Countdown(3)), list(Countdown(3))
```

### Generator functions

A function containing `yield` returns a **generator iterator** when called; its body runs lazily, suspending at each `yield` and resuming on the next `next()`, preserving local state. When the function returns, `StopIteration` is raised.

```python
def fib():
    a, b = 0, 1
    while True:                 # infinite generator: safe because consumption is lazy
        yield a
        a, b = b, a + b
from itertools import islice
list(islice(fib(), 10))

def read_chunks(path, size=1 << 20):
    with open(path, "rb") as f:
        while chunk := f.read(size):
            yield chunk

def tail_lines(path):
    """Follow a file like tail -f."""
    with open(path, encoding="utf-8", errors="replace") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5); continue
            yield line.rstrip("\n")
```

Properties:

- Generators are **lazy and memory-efficient**: only the current state is held; they are ideal for large files, database cursors, API pagination, directory walks, and streaming transformations.
- A generator's `with` blocks and `try/finally` clean up when the generator is exhausted, closed (`gen.close()` raises `GeneratorExit` inside), or garbage collected: always consume fully or close explicitly when holding resources.
- **`yield from subgen`** delegates to a sub-iterator and passes through `send`/`throw`; it also captures the sub-generator's return value (`result = yield from sub()`).
- **`send()`, `throw()`, `close()`** make generators usable as coroutines (the pre-`async` model: `x = yield value` receives values). Modern code uses `async def` (chapter 3.6), but this explains how asyncio is built.
- **Generator expressions** `(f(x) for x in xs)` are anonymous one-shot generators.
- **Exceptions inside generators** propagate to the consumer; `StopIteration` raised inside a generator is converted to `RuntimeError` (PEP 479): use `return`.

### Pipelines

Chain generators so each stage processes one item at a time; the whole pipeline runs in constant memory and is easy to test per stage:

```python
import gzip, re, json
from pathlib import Path
from collections import Counter

def files(root, pattern="*.log.gz"): yield from Path(root).rglob(pattern)
def lines(paths):
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
            yield from f
def parse(lines):
    rx = re.compile(r'(?P<ip>\S+) \S+ \S+ \[(?P<ts>[^\]]+)\] "(?P<req>[^"]*)" (?P<status>\d{3}) (?P<size>\d+|-)')
    for l in lines:
        if m := rx.match(l): yield m.groupdict()
def errors(records): return (r for r in records if r["status"].startswith("5"))

top = Counter(r["ip"] for r in errors(parse(lines(files("/var/log/nginx"))))).most_common(10)
```

Paginating an API lazily:

```python
def list_instances(client, project):
    token = None
    while True:
        resp = client.list(project=project, page_token=token, page_size=500)
        yield from resp["items"]
        token = resp.get("nextPageToken")
        if not token: break
running = (i for i in list_instances(c, "p") if i["status"] == "RUNNING")
```

Batching:

```python
from itertools import islice
def batched(iterable, n):
    it = iter(iterable)
    while batch := list(islice(it, n)):
        yield batch
# Python 3.12+: itertools.batched(iterable, n) yields tuples
for ids in batched(all_instance_ids, 100): client.bulk_delete(ids)       # API limits of 100 per call
```

### `itertools`, `functools`, `operator`

| Tool | Purpose |
|---|---|
| `islice(it, start, stop, step)` | Lazy slicing |
| `chain(a, b)` / `chain.from_iterable(xs)` | Concatenate iterables lazily |
| `zip_longest`, `zip(strict=True)` | Pairwise combine |
| `groupby(sorted_items, key)` | Group **consecutive** equal keys (sort first) |
| `accumulate(xs, func)` | Running totals (cumulative sums, max) |
| `takewhile`, `dropwhile` | Take/drop by predicate |
| `product`, `permutations`, `combinations`, `combinations_with_replacement` | Combinatorics (test matrices, parameter sweeps) |
| `cycle`, `repeat`, `count` | Infinite iterators (round robin: `cycle(backends)`) |
| `tee(it, n)` | n independent iterators over one (buffers) |
| `starmap(f, tuples)` | Apply f(*args) |
| `pairwise(xs)` (3.10) | Adjacent pairs (deltas of counters) |
| `batched(xs, n)` (3.12) | Chunks |
| `functools.reduce`, `partial`, `lru_cache` | Folding, partial application, memoisation |

```python
from itertools import groupby, accumulate, pairwise, product, chain
rows = sorted(nodes, key=lambda n: n["rack"])
for rack, grp in groupby(rows, key=lambda n: n["rack"]): print(rack, [n["name"] for n in grp])
rates = [b - a for a, b in pairwise(counter_samples)]                # per-interval deltas
matrix = list(product(["bf16", "fp8"], [1, 8, 64], [128, 2048]))      # benchmark parameter grid
```

## 9. Idioms for clarity and correctness

- **EAFP vs LBYL**: "easier to ask forgiveness than permission": `try: value = d[key] except KeyError: ...` often beats `if key in d:` (and is race-free for files: `try: open(...)`, not `if os.path.exists`). Use LBYL where the check is cheap and failure rare.
- **Truthiness**: `if items:`; but use `is None` when None is distinct.
- **Enumerate, zip, reversed, sorted** instead of index arithmetic; `for i, x in enumerate(xs, 1)`.
- **Unpacking**: `a, b = b, a`; `head, *tail = xs`; ignore with `_`.
- **`with`** for resources; **`pathlib`** for paths.
- **`str.join`** for concatenation; **f-strings** for formatting; `!r` in log messages.
- **`any()` / `all()`** over generator expressions short-circuit.
- **`dict.get`/`setdefault`/`defaultdict`/`Counter`** instead of manual key checks.
- **`next(iter_, default)`** to get the first match: `first_up = next((n for n in nodes if n.up), None)`.
- **`sorted(set(xs))`, `dict.fromkeys`** for dedupe.
- **`enumerate` over `range(len())`**, **`min/max(key=)`**.
- **`isinstance(x, (list, tuple))`** with ABCs (`collections.abc.Mapping`) rather than exact type checks; accept the most general useful type (a `Sequence`/`Iterable`) and return a concrete one.
- **Avoid**: bare `except:`, mutable defaults, `from x import *`, `global` state, `eval`/`exec` on external input, `type(x) == T`, building SQL/shell by formatting, shadowing built-ins, overusing lambdas, deeply nested comprehensions, premature optimisation.
- **Zen of Python** (`import this`): explicit is better than implicit; readability counts; errors should never pass silently; flat is better than nested.

## 10. Infrastructure examples

### LRU cache of expensive lookups

```python
from functools import lru_cache
import socket

@lru_cache(maxsize=4096)
def reverse_dns(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except OSError:
        return ip
reverse_dns.cache_info(); reverse_dns.cache_clear()
```

### Sliding-window rate / anomaly detector

```python
from collections import deque
from statistics import mean, pstdev

class Window:
    def __init__(self, n=60): self.v = deque(maxlen=n)
    def add(self, x): self.v.append(x)
    def anomalous(self, x, k=3.0):
        if len(self.v) < self.v.maxlen: return False
        m, s = mean(self.v), pstdev(self.v) or 1e-9
        return abs(x - m) > k * s
```

### Merging layered configuration

```python
from collections import ChainMap
import os, json
def load_config(cli: dict) -> ChainMap:
    env = {k[6:].lower(): v for k, v in os.environ.items() if k.startswith("MYOPS_")}
    file_cfg = json.load(open("/etc/myops.json")) if os.path.exists("/etc/myops.json") else {}
    return ChainMap({k: v for k, v in cli.items() if v is not None}, env, file_cfg, {"retries": 3, "timeout": 30})
```

### A resource pool as a context manager

```python
from contextlib import contextmanager
from queue import Queue
class Pool:
    def __init__(self, make, n): self._q = Queue(); [self._q.put(make()) for _ in range(n)]
    @contextmanager
    def acquire(self):
        c = self._q.get()
        try: yield c
        finally: self._q.put(c)
```

## 11. Lab (untested)

1. **Data model**: implement `Vector`, then `Fleet` (a `Sequence`), then `Config` (a `MutableMapping` with dotted-key access and layering), verifying `len`, iteration, `in`, slicing, `repr`, equality, hashing, sorting, and `sorted(set(...))` behaviour. Use `collections.abc` to see which methods you got for free. Write tests with plain `assert`.
2. **Special-method puzzles**: show `NotImplemented` vs raising; `__eq__` without `__hash__` makes instances unhashable; `__radd__`; `__bool__` vs `__len__`; the `t[0] += [3]` puzzle; explain each result.
3. **Comprehensions**: rewrite five loops as comprehensions, then rewrite two over-nested ones back into functions; benchmark loop vs list comprehension vs generator expression for sum with `timeit` and memory with `tracemalloc`.
4. **Iterators and generators**: implement `Countdown` as iterator class and generator function; demonstrate single-pass behaviour; write `read_chunks`, `tail_lines`, `batched`, `window(iterable, n)`; implement `yield from` delegation; use `send()` to build a running-average coroutine; show `close()` triggering `finally`.
5. **Pipelines**: generate 5 million synthetic log lines to gzip files; implement the pipeline above; compare memory (`/usr/bin/time -v`) against a `readlines()` version; add a `dedupe` stage using a bounded set or Bloom-filter-like structure.
6. **itertools**: use `groupby`, `accumulate`, `pairwise`, `product`, `chain.from_iterable`, `islice`; build a benchmark parameter sweep generator and a round-robin backend selector with `cycle`.
7. **Text vs bytes**: round-trip strings with different encodings; reproduce a `UnicodeDecodeError` and fix it with `errors="replace"` and `surrogateescape`; normalise composed/decomposed Unicode; compute byte vs code point lengths.
8. **Memoisation and weak refs**: implement an `lru_cache` function with expensive IO simulated; measure; demonstrate staleness bug; replace with TTL cache; show a `WeakValueDictionary` cache.
9. **Patterns**: implement a command dispatcher using a registry decorator; a retry decorator is deferred to 3.11; implement `partial`-based pre-bound commands.
10. **Review**: take a script of your own (or a provided one) and refactor it to idiomatic form; list each change and the principle behind it.
11. **Clean up.**

Mark tested only after execution.

## 12. Common mistakes

- Reaching for index loops (`range(len(x))`) instead of iteration helpers.
- Consuming an iterator twice; returning a generator when callers expect a list (and vice versa) without documenting it.
- Modifying a collection during iteration; mutating arguments unexpectedly.
- Defining `__eq__` but not `__hash__` (or hashing mutable objects).
- Treating `str` as bytes (or the reverse); relying on the default locale encoding.
- Overusing comprehensions for side effects or deeply nested logic; unreadable one-liners.
- Using `list` for queues (`pop(0)`) or `in` on big lists.
- Unbounded caches (`lru_cache(maxsize=None)`) in long-running services.
- Holding file handles open in a half-consumed generator.
- `except Exception: pass` inside generator pipelines, hiding data loss.

## 13. Interview angles

- "What is the Python data model? Implement a class that works with `len`, indexing and `for`."
- "Iterable vs iterator vs generator?"
- "How would you process a 200 GB log file for the top 10 IPs by 5xx errors with 100 MB of RAM?"
- "Generator expression vs list comprehension: when does it matter?"
- "What does `yield from` do? How do `send` and `close` work?"
- "What are the `__eq__`/`__hash__` rules?"
- "Why is `deque` better than `list` for queues? When is a list better?"
- "What is EAFP?"
- "What does `lru_cache` require of its arguments? What are its risks in a service?"
- "Explain `sorted` stability and multi-key sorting with `key`."
- "How do `defaultdict`, `Counter` and `ChainMap` simplify code?"

## 14. Checkpoint questions (40)

1. What is a special method? **A:** A dunder method Python calls to implement syntax/built-ins.
2. Why call `len(x)` not `x.__len__()`? **A:** Built-ins do extra checks/fast paths; idiom.
3. `__repr__` vs `__str__`? **A:** Developer-unambiguous vs human-friendly.
4. What should binary operators return for unsupported types? **A:** `NotImplemented`.
5. `__eq__` and `__hash__` rule? **A:** Equal objects must have equal hashes; mutable objects shouldn't be hashable.
6. What does `__radd__` do? **A:** Handles `other + obj` when `other` can't.
7. Minimum to make a Sequence via ABC? **A:** `__len__` and `__getitem__`.
8. What makes a context manager? **A:** `__enter__` and `__exit__` (or `@contextmanager`).
9. What does returning True from `__exit__` do? **A:** Suppresses the exception.
10. Why deque over list for queues? **A:** O(1) at both ends.
11. What does `maxlen` do on deque? **A:** Ring buffer of the last N items.
12. List vs array.array memory? **A:** Pointers to objects vs compact typed values.
13. `memoryview` use? **A:** Zero-copy slices of binary buffers.
14. Is `sort()` stable? **A:** Yes.
15. `key=` vs `cmp`? **A:** Key function; cmp removed.
16. What is `defaultdict`? **A:** Dict that creates missing values via a factory.
17. What is `ChainMap` good for? **A:** Layered config lookup without copying.
18. Dict ordering guarantee? **A:** Insertion order since 3.7.
19. Why must dict keys be hashable? **A:** Lookup uses the hash.
20. How to dedupe preserving order? **A:** `dict.fromkeys(items)`.
21. Where does the conditional expression go in a comprehension? **A:** Before `for` for if/else; filter `if` after.
22. Does a comprehension variable leak into the enclosing scope, and how does `:=` behave inside a comprehension? **A:** The `for` loop target is local to the comprehension and does not leak, but a `:=` named assignment inside a comprehension binds its target in the enclosing scope (and `yield` inside a comprehension is forbidden).
23. When to use a generator expression? **A:** When you only iterate once/feed a reducer.
24. Walrus in comprehensions? **A:** Avoid recomputation of a value used in filter and output.
25. Iterable vs iterator? **A:** Provides an iterator vs produces items and is single-pass.
26. What does `for` call? **A:** `iter()` then `next()` until `StopIteration`.
27. What does `iter(callable, sentinel)` do? **A:** Calls until the sentinel is returned.
28. What is a generator function? **A:** A function with `yield` returning a lazy iterator.
29. What does `yield from` do? **A:** Delegates to a sub-iterator and returns its result.
30. What happens on `gen.close()`? **A:** `GeneratorExit` raised at the yield; finally blocks run.
31. Why are generators memory-efficient? **A:** Only current state is kept.
32. `groupby` requirement? **A:** Input sorted by the key (groups consecutive keys).
33. What does `pairwise` give? **A:** Adjacent pairs.
34. `str` vs `bytes` conversion? **A:** `encode`/`decode` at I/O boundaries.
35. Why normalise Unicode? **A:** Equivalent text can have different code points.
36. What is EAFP? **A:** Try the operation and handle the exception.
37. `lru_cache` argument requirement? **A:** Hashable arguments.
38. What is a weak reference for? **A:** Referencing without keeping the object alive.
39. Why `gc.freeze()` before forking? **A:** Reduce copy-on-write growth in workers.
40. How to read a file in chunks idiomatically? **A:** `while chunk := f.read(n)` or `iter(lambda: f.read(n), b"")`.

## 15. Sources and review notes

**Written in original words.** Principal sources:

- Luciano Ramalho, *Fluent Python*, 2nd ed.: chapter 1 (the Python data model), chapter 2 (an array of sequences), chapter 3 (dictionaries and sets), chapter 4 (Unicode text versus bytes), chapter 6 (object references, mutability and recycling), chapter 7 (functions as first-class objects), chapter 10 (design patterns with first-class functions), chapter 12 (special methods for sequences), chapter 17 (iterators, generators and classic coroutines).
- Mark Lutz, *Learning Python*, 6th ed. (`learning-python-6th-edition`; chapters 14 and 20—with `Chapter 20. Comprehensions and Generations` read in full for this chapter—and the function chapters).
- The author's `nvidia-devops` repository, volume 02 (Python core and OOP masterclass): choosing data structures by problem, lists versus sets for membership, generators for log streaming.
- Examples are the author's constructions.

**Flagged for verification before publishing:** version-specific features (`itertools.batched` in 3.12, `pairwise` in 3.10, `contextlib.chdir` in 3.11), memory-size figures (CPython-version dependent), and every code listing; all labs are **untested**.
