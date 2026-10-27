"""Chapter 3.4 model: Classes, OOP inheritance and composition (LP Ch. 26-32
FirstClass/SecondClass/ThirdClass, Person/Manager/Department & AttrDisplay,
Super/Inheritor/Replacer/Extender/Provider specialize.py, classtree.py,
SkipObject multi-scan iterable, Commuter5 __add__/__radd__, PizzaShop/streams
composition, pseudoprivate __X name mangling, bound methods, C3 MRO diamond),
Fluent Python Vector2d & N-dimensional Vector (__bytes__, frombytes, polar/
hyper-spherical __format__, slice-aware __getitem__, dynamic x/y/z/t __getattr__
& __setattr__, XOR __hash__, zip_longest __add__, dot product @ __matmul__),
Data Class Builders (City namedtuple, HackerClubMember @dataclass),
Interfaces/Protocols/ABCs (Tombola, BingoCage, LottoBlower), and
UpperCaseMixin cooperative MRO.
"""
from abc import ABC, abstractmethod
from array import array
import collections
from dataclasses import dataclass, field
import functools
import itertools
import math
import operator
import reprlib
from typing import ClassVar, Iterable, Iterator, List, Protocol, Sequence, Tuple, TypeVar, Generic, runtime_checkable


# 1. LP Ch. 27 & 28: FirstClass/SecondClass/ThirdClass & Person/Manager/AttrDisplay
class FirstClass:
    def setdata(self, value) -> None:
        self.data = value

    def display(self):
        return self.data


class SecondClass(FirstClass):
    def display(self):
        return f'Current value = "{self.data}"'


class ThirdClass(SecondClass):
    def __init__(self, value) -> None:
        self.data = value

    def __add__(self, other) -> "ThirdClass":
        return ThirdClass(self.data + other)

    def __str__(self) -> str:
        return f"[ThirdClass: {self.data}]"

    def mul(self, other) -> None:
        self.data *= other


class AttrDisplay:
    """LP Ch. 28 Example 28-13 classtools.py: generic display mixin showing instance __dict__."""

    def gatherAttrs(self) -> str:
        return ", ".join(f"{k}={getattr(self, k)}" for k in sorted(self.__dict__))

    def __repr__(self) -> str:
        return f"[{self.__class__.__name__}: {self.gatherAttrs()}]"


class Person(AttrDisplay):
    """LP Ch. 28 Example 28-14 person_14.py."""

    def __init__(self, name: str, job: str | None = None, pay: int = 0) -> None:
        self.name = name
        self.job = job
        self.pay = pay

    def lastName(self) -> str:
        return self.name.split()[-1]

    def giveRaise(self, percent: float) -> None:
        self.pay = int(self.pay * (1 + percent))


class Manager(Person):
    """LP Ch. 28 Manager customizing giveRaise by augmenting Person.giveRaise."""

    def __init__(self, name: str, pay: int) -> None:
        Person.__init__(self, name, "mgr", pay)

    def giveRaise(self, percent: float, bonus: float = 0.10) -> None:
        Person.giveRaise(self, percent + bonus)


# 2. LP Ch. 29 specialize.py & Ch. 30 SkipObject & Commuter5 & Ch. 31 pseudoprivate
class Super:
    def method(self) -> str:
        return "in Super.method"

    def delegate(self) -> str:
        return self.action()

    def action(self) -> str:
        raise NotImplementedError("action must be defined")


class Inheritor(Super):
    pass


class Replacer(Super):
    def method(self) -> str:
        return "in Replacer.method"


class Extender(Super):
    def method(self) -> str:
        return "starting Extender.method -> " + Super.method(self) + " -> ending Extender.method"


class Provider(Super):
    def action(self) -> str:
        return "in Provider.action"


class SkipObject:
    """LP Ch. 30 Example 30-3/30-7: Multi-scan iterable yielding every second item."""

    def __init__(self, wrapped: Sequence) -> None:
        self.wrapped = wrapped

    def __iter__(self) -> Iterator:
        offset = 0
        while offset < len(self.wrapped):
            item = self.wrapped[offset]
            offset += 2
            yield item


class Commuter5:
    """LP Ch. 30 Example 30-14: Commutative + returning Commuter5 without nested wrapping."""

    def __init__(self, val: int) -> None:
        self.val = val

    def __add__(self, other) -> "Commuter5":
        if isinstance(other, Commuter5):
            other = other.val
        return Commuter5(self.val + other)

    def __radd__(self, other) -> "Commuter5":
        return Commuter5(other + self.val)

    def __repr__(self) -> str:
        return f"Commuter5({self.val})"


class _C1:
    def meth1(self) -> None:
        self.__X = 88

    def meth2(self) -> int:
        return self.__X


class _C2:
    def metha(self) -> None:
        self.__X = 99

    def methb(self) -> int:
        return self.__X


class PseudoprivateC3(_C1, _C2):
    """LP Ch. 31 pseudoprivate.py: __X mangles to _C1__X and _C2__X without collision."""


# 3. FP Ch. 11, 12, 16: Vector2d and N-dimensional Vector
class Vector2d:
    """FP Ch. 11 Example 11-11 vector2d_v3.py with __slots__, bytes, and polar format 'p'."""

    __match_args__ = ("x", "y")
    __slots__ = ("__x", "__y")
    typecode = "d"

    def __init__(self, x: float, y: float) -> None:
        self.__x = float(x)
        self.__y = float(y)

    @property
    def x(self) -> float:
        return self.__x

    @property
    def y(self) -> float:
        return self.__y

    def __iter__(self) -> Iterator[float]:
        return (i for i in (self.x, self.y))

    def __repr__(self) -> str:
        class_name = type(self).__name__
        return "{}({!r}, {!r})".format(class_name, *self)

    def __str__(self) -> str:
        return str(tuple(self))

    def __bytes__(self) -> bytes:
        return bytes([ord(self.typecode)]) + bytes(array(self.typecode, self))

    @classmethod
    def frombytes(cls, octets: bytes) -> "Vector2d":
        typecode = chr(octets[0])
        memv = memoryview(octets[1:]).cast(typecode)
        return cls(*memv)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector2d):
            return NotImplemented
        return tuple(self) == tuple(other)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __abs__(self) -> float:
        return math.hypot(self.x, self.y)

    def __bool__(self) -> bool:
        return bool(abs(self))

    def angle(self) -> float:
        return math.atan2(self.y, self.x)

    def __format__(self, fmt_spec: str = "") -> str:
        if fmt_spec.endswith("p"):
            fmt_spec = fmt_spec[:-1]
            coords: Tuple[float, ...] = (abs(self), self.angle())
            outer_fmt = "<{}, {}>"
        else:
            coords = tuple(self)
            outer_fmt = "({}, {})"
        components = (format(c, fmt_spec) for c in coords)
        return outer_fmt.format(*components)


class Vector:
    """FP Ch. 12 & 16 N-dimensional Vector supporting slicing, dynamic x/y/z/t,
    XOR hash, zip_longest +, scalar *, and dot-product @.
    """

    typecode = "d"
    __match_args__ = ("x", "y", "z", "t")

    def __init__(self, components: Iterable[float]) -> None:
        self._components = array(self.typecode, components)

    def __iter__(self) -> Iterator[float]:
        return iter(self._components)

    def __repr__(self) -> str:
        components = reprlib.repr(self._components)
        components = components[components.find("[") : -1]
        return f"Vector({components})"

    def __str__(self) -> str:
        return str(tuple(self))

    def __bytes__(self) -> bytes:
        return bytes([ord(self.typecode)]) + bytes(self._components)

    @classmethod
    def frombytes(cls, octets: bytes) -> "Vector":
        typecode = chr(octets[0])
        memv = memoryview(octets[1:]).cast(typecode)
        return cls(memv)

    def __len__(self) -> int:
        return len(self._components)

    def __getitem__(self, key):
        if isinstance(key, slice):
            cls = type(self)
            return cls(self._components[key])
        index = operator.index(key)
        return self._components[index]

    def __getattr__(self, name: str) -> float:
        cls = type(self)
        try:
            pos = cls.__match_args__.index(name)
        except ValueError:
            pos = -1
        if 0 <= pos < len(self._components):
            return self._components[pos]
        raise AttributeError(f"{cls.__name__!r} object has no attribute {name!r}")

    def __setattr__(self, name: str, value: object) -> None:
        cls = type(self)
        if len(name) == 1:
            if name in cls.__match_args__:
                error = "readonly attribute {attr_name!r}"
            elif name.islower():
                error = "can't set attributes 'a' to 'z' in {cls_name!r}"
            else:
                error = ""
            if error:
                raise AttributeError(error.format(cls_name=cls.__name__, attr_name=name))
        super().__setattr__(name, value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return len(self) == len(other) and all(a == b for a, b in zip(self, other))

    def __hash__(self) -> int:
        hashes = (hash(x) for x in self)
        return functools.reduce(operator.xor, hashes, 0)

    def __abs__(self) -> float:
        return math.hypot(*self)

    def __bool__(self) -> bool:
        return bool(abs(self))

    def __add__(self, other: object) -> "Vector":
        try:
            pairs = itertools.zip_longest(self, other, fillvalue=0.0)  # type: ignore[arg-type]
            return Vector(a + b for a, b in pairs)
        except TypeError:
            return NotImplemented

    __radd__ = __add__

    def __mul__(self, scalar: object) -> "Vector":
        try:
            factor = float(scalar)  # type: ignore[arg-type]
        except TypeError:
            return NotImplemented
        return Vector(n * factor for n in self)

    def __rmul__(self, scalar: object) -> "Vector":
        return self * scalar

    def __matmul__(self, other: object) -> float:
        if isinstance(other, collections.abc.Sized) and isinstance(other, collections.abc.Iterable):
            if len(self) == len(other):
                return sum(a * b for a, b in zip(self, other))
            raise ValueError("@ requires vectors of equal length.")
        return NotImplemented

    def __rmatmul__(self, other: object) -> float:
        return self @ other


# 4. FP Ch. 5: ClubMember and HackerClubMember dataclass with ClassVar and __post_init__
@dataclass
class ClubMember:
    name: str
    guests: list[str] = field(default_factory=list)


@dataclass
class HackerClubMember(ClubMember):
    all_handles: ClassVar[set[str]] = set()
    handle: str = ""

    def __post_init__(self) -> None:
        cls = self.__class__
        if self.handle == "":
            self.handle = self.name.split()[0]
        if self.handle in cls.all_handles:
            raise ValueError(f"handle {self.handle!r} already exists.")
        cls.all_handles.add(self.handle)


# 5. FP Ch. 13 & 15: Tombola ABC & Generic LottoBlower[T] & SupportsLessThan Protocol
class Tombola(ABC):
    @abstractmethod
    def load(self, iterable: Iterable) -> None:
        """Add items from an iterable."""

    @abstractmethod
    def pick(self):
        """Remove item at random, returning it. Raise LookupError if empty."""

    def loaded(self) -> bool:
        return bool(self.inspect())

    def inspect(self) -> Tuple:
        items = []
        while True:
            try:
                items.append(self.pick())
            except LookupError:
                break
        self.load(items)
        return tuple(items)


T = TypeVar("T")


class LottoBlower(Tombola, Generic[T]):
    """FP Ch. 13 & 15: Generic Tombola implementation."""

    def __init__(self, iterable: Iterable[T]) -> None:
        self._balls = list(iterable)

    def load(self, iterable: Iterable[T]) -> None:
        self._balls.extend(iterable)

    def pick(self) -> T:
        try:
            return self._balls.pop(0)  # deterministic pop for repeatable testing
        except IndexError:
            raise LookupError("pick from empty LottoBlower")

    def loaded(self) -> bool:
        return bool(self._balls)

    def inspect(self) -> Tuple[T, ...]:
        return tuple(self._balls)


@runtime_checkable
class SupportsLessThan(Protocol):
    def __lt__(self, other: object) -> bool: ...


LT = TypeVar("LT", bound=SupportsLessThan)


def top(series: Iterable[LT], length: int) -> List[LT]:
    """FP Ch. 8 Example 8-18: Return top `length` items using bounded TypeVar."""
    ordered = sorted(series, reverse=True)
    return ordered[:length]


# 6. FP Ch. 14: UpperCaseMixin cooperative multiple inheritance
def _upper(key):
    try:
        return key.upper()
    except AttributeError:
        return key


class UpperCaseMixin:
    def __setitem__(self, key, item) -> None:
        super().__setitem__(_upper(key), item)  # type: ignore[misc]

    def __getitem__(self, key):
        return super().__getitem__(_upper(key))  # type: ignore[misc]

    def get(self, key, default=None):
        return super().get(_upper(key), default)  # type: ignore[misc]

    def __contains__(self, key) -> bool:
        return super().__contains__(_upper(key))  # type: ignore[misc]


class UpperDict(UpperCaseMixin, collections.UserDict):
    pass
