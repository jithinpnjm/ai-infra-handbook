"""Chapter 3.3 model: Python data model (NodeInventory & drain_order, Vector),
sequence slicing and bytecode puzzle (t[0] += [3]), dict __missing__
(StrKeyDict0), weak references and HauntedBus/TwilightBus mutability traps,
first-class function Strategy pattern & promo registry, closures/freevars &
singledispatch, comprehensions & matrix operations, and generator functions
(scramble1/2, permute1/2, mymap, myzip, mymapPad, ArithmeticProgression,
yield from tree, and classic averaging coroutine).

Sources modeled:
- Luciano Ramalho, Fluent Python, 2nd ed. (fluent-python-2nd-edition, FP):
  * Chapter 1 ("The Python Data Model"): Node namedtuple, NodeInventory (__len__,
    __getitem__), drain_order ranking (0 to 51), and Vector (__repr__, __abs__,
    __bool__, __add__, __mul__).
  * Chapter 2 ("An Array of Sequences"): listcomps vs map/filter, Cartesian
    products, tuple records & nested unpacking (metro_areas), named slices,
    t = (1, 2, [30, 40]); t[2] += [50, 60] TypeError + in-place mutation,
    bisect, deque, array, and memoryview.
  * Chapter 3 ("Dictionaries and Sets"): dict comprehensions (dial_codes),
    setdefault vs defaultdict, __missing__ and StrKeyDict0, ChainMap, Counter,
    MappingProxyType, dict views & set algebra.
  * Chapter 6 ("Object References, Mutability, and Recycling"): Bus shallow vs
    deep copy, HauntedBus mutable defaultpassengers=[], TwilightBus aliasing
    caller list, and weakref.finalize.
  * Chapter 7 ("Functions as First-Class Objects"): higher-order functions,
    BingoCage (__call__), tag keyword-only arguments, itemgetter, attrgetter,
    methodcaller, and functools.partial.
  * Chapter 9 ("Decorators and Closures"): registration execution at import
    time, Averager class vs make_averager closure (__code__.co_freevars and
    __closure__ vs nonlocal count/total), clock decorator, functools.cache,
    and @singledispatch.
  * Chapter 10 ("Design Patterns with First-Class Functions"): refactoring
    Classic Strategy (Order, Customer, LineItem, FidelityPromo 5% >=1000 pts,
    BulkItemPromo 10% >=20 units, LargeOrderPromo 7% >=10 distinct items) to
    first-class functions and @promotion registry with best_promo.
  * Chapter 17 ("Iterators, Generators, and Classic Coroutines"): Sentence
    iterator vs generator vs lazy re.finditer, ArithmeticProgression, itertools
    (accumulate, groupby, tee, product), yield from subgenerator delegation &
    class hierarchy tree(cls), and classic averaging coroutine with send() and
    return Result(count, average).
- Mark Lutz, Learning Python, 6th ed. (learning-python-6th-edition, LP):
  * Chapters 14 & 20 ("Iterations and Comprehensions", "Comprehensions and
    Generations"): single-pass vs multiple-pass iterables, matrix comprehensions,
    comprehension scope vs := leakage, generator send/yield from, scramble1/2,
    permute1/2 (N! vs N), mymap, myzip, and mymapPad.
- volume-02/01-python-core-oop-masterclass.md.
"""
import collections
from decimal import Decimal
from typing import Callable, Dict, Iterable, Iterator, List, NamedTuple, Optional, Sequence, Tuple

Node = collections.namedtuple("Node", ["slot", "rack"])


class NodeInventory:
    """A rack inventory as a sequence: it only implements __len__ and __getitem__."""

    slots = [f"{n:02d}" for n in range(1, 14)]
    racks = "r1 r2 r3 r4".split()

    def __init__(self) -> None:
        self._nodes = [Node(slot, rack) for rack in self.racks for slot in self.slots]

    def __len__(self) -> int:
        return len(self._nodes)

    def __getitem__(self, position):
        return self._nodes[position]


RACK_PRIORITY = dict(r4=3, r3=2, r2=1, r1=0)


def drain_order(node: Node) -> int:
    """Rank returning 0 for slot 01 in rack r1 and 51 for slot 13 in rack r4."""
    slot_value = NodeInventory.slots.index(node.slot)
    return slot_value * len(RACK_PRIORITY) + RACK_PRIORITY[node.rack]


def demonstrate_tuple_inplace_add_puzzle() -> Tuple[bool, Tuple[object, ...]]:
    """FP Ch. 2 Example 2-17: t = (1, 2, [30, 40]); t[2] += [50, 60] mutates the
    inner list in place via __iadd__ and then raises TypeError on tuple __setitem__.
    """
    t = (1, 2, [30, 40])
    raised_type_error = False
    try:
        t[2] += [50, 60]  # type: ignore[index]
    except TypeError:
        raised_type_error = True
    return raised_type_error, t


class StrKeyDict0(dict):
    """FP Ch. 3 Example 3-8: StrKeyDict0 converts non-str keys to str on lookup."""

    def __missing__(self, key):
        if isinstance(key, str):
            raise KeyError(key)
        return self[str(key)]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key) -> bool:
        return key in self.keys() or str(key) in self.keys()


class Customer(NamedTuple):
    name: str
    fidelity: int


class LineItem(NamedTuple):
    product: str
    quantity: int
    price: Decimal

    def total(self) -> Decimal:
        return self.price * self.quantity


class Order(NamedTuple):
    """FP Ch. 10 Example 10-3: Order Context with pluggable function Strategy."""

    customer: Customer
    cart: Sequence[LineItem]
    promotion: Optional[Callable[["Order"], Decimal]] = None

    def total(self) -> Decimal:
        return sum((item.total() for item in self.cart), start=Decimal(0))

    def due(self) -> Decimal:
        discount = Decimal(0) if self.promotion is None else self.promotion(self)
        return self.total() - discount


PROMOS: List[Callable[[Order], Decimal]] = []


def promotion(promo_fn: Callable[[Order], Decimal]) -> Callable[[Order], Decimal]:
    """FP Ch. 10 Example 10-9: Registration decorator for promotion strategies."""
    PROMOS.append(promo_fn)
    return promo_fn


@promotion
def fidelity_promo(order: Order) -> Decimal:
    """5% discount for customers with 1000 or more fidelity points."""
    if order.customer.fidelity >= 1000:
        return order.total() * Decimal("0.05")
    return Decimal(0)


@promotion
def bulk_item_promo(order: Order) -> Decimal:
    """10% discount for each LineItem with 20 or more units."""
    discount = Decimal(0)
    for item in order.cart:
        if item.quantity >= 20:
            discount += item.total() * Decimal("0.1")
    return discount


@promotion
def large_order_promo(order: Order) -> Decimal:
    """7% discount for orders with 10 or more distinct items."""
    distinct_items = {item.product for item in order.cart}
    if len(distinct_items) >= 10:
        return order.total() * Decimal("0.07")
    return Decimal(0)


def best_promo(order: Order) -> Decimal:
    """FP Ch. 10 Example 10-6: Compute the largest discount across registered promos."""
    return max(promo(order) for promo in PROMOS)


def make_averager() -> Callable[[float], float]:
    """FP Ch. 9 Example 9-14: Efficient closure averager using nonlocal count and total."""
    count = 0
    total = 0.0

    def averager(new_value: float) -> float:
        nonlocal count, total
        count += 1
        total += new_value
        return total / count

    return averager


def scramble1(seq: Sequence) -> Iterator[Sequence]:
    """LP Ch. 20 Example 20-1: Generate N rotations of a sequence lazily."""
    for i in range(len(seq)):
        yield seq[i:] + seq[:i]


def permute1(seq: Sequence) -> List[Sequence]:
    """LP Ch. 20 Example 20-2: Compute all N! permutations eagerly in a list."""
    if not seq:
        return [seq]
    res: List[Sequence] = []
    for i in range(len(seq)):
        rest = seq[:i] + seq[i + 1 :]
        for x in permute1(rest):
            res.append(seq[i : i + 1] + x)
    return res


def permute2(seq: Sequence) -> Iterator[Sequence]:
    """LP Ch. 20 Example 20-2: Yield all N! permutations lazily via recursive generator."""
    if not seq:
        yield seq
    else:
        for i in range(len(seq)):
            rest = seq[:i] + seq[i + 1 :]
            for x in permute2(rest):
                yield seq[i : i + 1] + x


def myzip_gen(*seqs: Iterable) -> Iterator[Tuple[object, ...]]:
    """LP Ch. 20 Example 20-6: Emulate truncating zip as a generator."""
    lists = [list(s) for s in seqs]
    while all(lists):
        yield tuple(s.pop(0) for s in lists)


def mymap_pad_gen(*seqs: Iterable, pad: object = None) -> Iterator[Tuple[object, ...]]:
    """LP Ch. 20 Example 20-6: Emulate padding map/zip_longest as a generator."""
    lists = [list(s) for s in seqs]
    while any(lists):
        yield tuple((s.pop(0) if s else pad) for s in lists)


class Result(NamedTuple):
    count: int
    average: float


def averager_coro() -> Iterator[None]:
    """FP Ch. 17 Example 17-37: Classic coroutine returning Result via StopIteration.value."""
    total = 0.0
    count = 0
    average = 0.0
    while True:
        term = yield
        if term is None:
            break
        total += term
        count += 1
        average = total / count
    return Result(count, average)


def delegate_averager(values: Sequence[float]) -> Result:
    """Drive averager_coro() using `result = yield from averager_coro()`."""
    res_holder: List[Result] = []

    def grouper():
        res = yield from averager_coro()
        res_holder.append(res)
        yield res

    g = grouper()
    next(g)  # prime coroutine
    for v in values:
        g.send(v)
    g.send(None)  # terminate subgenerator and capture return value
    return res_holder[0]
