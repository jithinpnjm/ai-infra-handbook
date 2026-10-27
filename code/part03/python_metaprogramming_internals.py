"""Chapter 3.11 model: Decorators, descriptors, dynamic attributes, and class
metaprogramming (how Python frameworks work under the hood).

Sources modeled:
- Luciano Ramalho, Fluent Python, 2nd ed. (fluent-python-2nd-edition, FP):
  * Chapter 22 ("Dynamic Attributes and Properties"): FrozenJSON (__new__ +
    __getattr__ + keyword.iskeyword), LineItem quantity() property factory,
    and cached_property / @property deleter (BlackKnight).
  * Chapter 23 ("Attribute Descriptors"): Validated ABC + Quantity and NonBlank
    overriding (data) descriptors with __set_name__, and overriding vs
    non-overriding (non-data) descriptor lookup precedence (Managed).
  * Chapter 24 ("Class Metaprogramming"): record_factory(cls_name, field_names)
    using type(cls_name, (object,), cls_attrs), Checked base class with
    __init_subclass__, @checked class decorator, and MetaBunch metaclass /
    class-creation execution order (__prepare__ -> body -> __new__ -> __init__
    -> __set_name__ -> __init_subclass__).
- Mark Lutz, Learning Python, 6th ed. (learning-python-6th-edition, LP):
  * Chapter 38 ("Managed Attributes"): CardHolder implemented 4 ways (properties,
    per-instance descriptors validate_descriptors2.py vs buggy shared-descriptor-state
    validate_descriptors1.py, __getattr__, and __getattribute__), and
    GetAttr vs GetAttribute interception.
  * Chapter 39 ("Decorators"): function & class decorators, @tracer (why a
    class-based decorator without __get__ fails on methods vs nonlocal function
    decorator), @timer(label=..., trace=...), Public/Private class decorator
    access control, and @rangetest(**argchecks) validating positional, keyword,
    and default arguments via __code__.co_varnames.
  * Chapter 40 ("Metaclasses and Inheritance"): type(classname, supers, classdict),
    MetaOne/MetaTwo (__new__ and __init__), metaclass vs class decorator
    augmentation (decorating all methods with tracer), and the two-tree
    inheritance algorithm (instance -> class MRO vs class -> metaclass MRO, and
    why built-in operations skip the instance/class step).
- volume-02/05-advanced-oop-design-masterclass.md.
"""
from abc import ABC, abstractmethod
from collections import abc
import functools
import inspect
import keyword
from typing import Any, Callable, Dict, Iterable, List, Tuple


# 1. FP Ch. 22 Example 22-5/22-6: FrozenJSON navigating nested dicts/lists via __new__ & __getattr__
class FrozenJSON:
    """FP Ch. 22: Read-only facade for navigating nested JSON mappings using attribute notation."""

    def __new__(cls, arg):
        if isinstance(arg, abc.Mapping):
            return super().__new__(cls)
        if isinstance(arg, abc.MutableSequence):
            return [cls(item) for item in arg]
        return arg

    def __init__(self, mapping: abc.Mapping) -> None:
        self.__data = {}
        for key, value in mapping.items():
            if keyword.iskeyword(key):
                key += "_"
            self.__data[key] = value

    def __getattr__(self, name: str) -> Any:
        try:
            return getattr(self.__data, name)
        except AttributeError:
            try:
                return FrozenJSON(self.__data[name])
            except KeyError as exc:
                raise AttributeError(name) from exc

    def __dir__(self) -> List[str]:
        return list(self.__data.keys())


# 2. FP Ch. 23 Examples 23-5 to 23-7: Validated ABC, Quantity, NonBlank descriptors with __set_name__
class Validated(ABC):
    def __set_name__(self, owner: type, name: str) -> None:
        self.storage_name = name

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        if instance is None:
            return self
        return instance.__dict__[self.storage_name]

    def __set__(self, instance: Any, value: Any) -> None:
        value = self.validate(self.storage_name, value)
        instance.__dict__[self.storage_name] = value

    @abstractmethod
    def validate(self, name: str, value: Any) -> Any:
        """Return validated value or raise ValueError."""


class Quantity(Validated):
    """A number greater than zero."""

    def validate(self, name: str, value: Any) -> Any:
        if value <= 0:
            raise ValueError(f"{name} must be > 0")
        return value


class NonBlank(Validated):
    """A string with at least one non-space character."""

    def validate(self, name: str, value: Any) -> Any:
        value = value.strip()
        if not value:
            raise ValueError(f"{name} cannot be blank")
        return value


class LineItem:
    """FP Ch. 23 Example 23-7 bulkfood_v5.py."""

    description = NonBlank()
    weight = Quantity()
    price = Quantity()

    def __init__(self, description: str, weight: float, price: float) -> None:
        self.description = description
        self.weight = weight
        self.price = price

    def subtotal(self) -> float:
        return self.weight * self.price


# 3. LP Ch. 38 Examples 38-21 & 38-23: CardHolder with per-client-instance descriptor state
class CardHolder:
    """LP Ch. 38 validate_descriptors2.py: Per-instance descriptor state (so bob != sue)."""

    acctlen = 8
    retireage = 62.5

    def __init__(self, acct: str, name: str, age: float, addr: str) -> None:
        self.acct = acct
        self.name = name
        self.age = age
        self.addr = addr

    class Name:
        def __get__(self, instance, owner):
            return self if instance is None else instance.__name

        def __set__(self, instance, value: str):
            instance.__name = value.lower().replace(" ", "_")

    name = Name()

    class Age:
        def __get__(self, instance, owner):
            return self if instance is None else instance.__age

        def __set__(self, instance, value: float):
            if value < 0 or value > 150:
                raise ValueError("invalid age")
            instance.__age = value

    age = Age()

    class Acct:
        def __get__(self, instance, owner):
            return self if instance is None else instance.__acct[:-3] + "***"

        def __set__(self, instance, value: str):
            value = value.replace("-", "")
            if len(value) != instance.acctlen:
                raise TypeError("invalid acct number")
            instance.__acct = value

    acct = Acct()

    class Remain:
        def __get__(self, instance, owner):
            return self if instance is None else instance.retireage - instance.age

        def __set__(self, instance, value):
            raise TypeError("cannot set remain")

    remain = Remain()


# 4. LP Ch. 39 Example 39-25: @rangetest(**argchecks) decorator for positional & keyword args
def rangetest(**argchecks: Tuple[float, float]) -> Callable:
    """LP Ch. 39 Example 39-25: Validate argument ranges for positional and keyword calls."""

    def onDecorator(func: Callable) -> Callable:
        code = func.__code__
        allargs = code.co_varnames[: code.co_argcount]
        funcname = func.__name__

        @functools.wraps(func)
        def onCall(*pargs, **kargs):
            expected = list(allargs)
            positionals = expected[: len(pargs)]
            for (argname, (low, high)) in argchecks.items():
                if argname in kargs:
                    if kargs[argname] < low or kargs[argname] > high:
                        raise TypeError(f'{funcname} argument "{argname}" not in {low}..{high}')
                elif argname in positionals:
                    position = positionals.index(argname)
                    if pargs[position] < low or pargs[position] > high:
                        raise TypeError(f'{funcname} argument "{argname}" not in {low}..{high}')
            return func(*pargs, **kargs)

        return onCall

    return onDecorator


# 5. FP Ch. 24 Example 24-2: record_factory(cls_name, field_names) dynamic class builder via type()
def record_factory(cls_name: str, field_names: str | Iterable[str]) -> type:
    """FP Ch. 24 Example 24-2: Create a slotted record class dynamically with type()."""
    if isinstance(field_names, str):
        field_names = field_names.replace(",", " ").split()
    field_names_tuple = tuple(field_names)

    def __init__(self, *args, **kwargs) -> None:
        attrs = dict(zip(self.__slots__, args))
        attrs.update(kwargs)
        for name, value in attrs.items():
            setattr(self, name, value)

    def __iter__(self):
        for name in self.__slots__:
            yield getattr(self, name)

    def __repr__(self) -> str:
        values = ", ".join(f"{name}={value!r}" for name, value in zip(self.__slots__, self))
        return f"{self.__class__.__name__}({values})"

    cls_attrs = dict(
        __slots__=field_names_tuple,
        __init__=__init__,
        __iter__=__iter__,
        __repr__=__repr__,
    )
    return type(cls_name, (object,), cls_attrs)


# 6. FP Ch. 24 & LP Ch. 40: Class creation hook order & toy PyTorch nn.Module.__setattr__
def trace_class_creation_order() -> List[str]:
    events: List[str] = []

    class TraceMeta(type):
        @classmethod
        def __prepare__(mcs, name, bases, **kw):
            events.append(f"1.__prepare__:{name}")
            return {}

        def __new__(mcs, name, bases, ns, **kw):
            events.append(f"3.__new__:{name}")
            return super().__new__(mcs, name, bases, ns)

        def __init__(cls, name, bases, ns, **kw):
            events.append(f"6.__init__:{name}")
            super().__init__(name, bases, ns)

    class TraceDesc:
        def __set_name__(self, owner, name):
            events.append(f"4.__set_name__:{owner.__name__}.{name}")

    class Base(metaclass=TraceMeta):
        def __init_subclass__(cls, **kw):
            super().__init_subclass__(**kw)
            events.append(f"5.__init_subclass__:{cls.__name__}")

    events.clear()

    class Sub(Base):
        events.append("2.body:Sub")
        field = TraceDesc()

    _ = Sub
    return events


class ToyParameter:
    def __init__(self, name: str, shape: Tuple[int, ...]) -> None:
        self.name = name
        self.shape = shape


class ToyModule:
    """Section 3.5 & 9.10: Demonstrate how PyTorch nn.Module.__setattr__ registers
    ToyParameter and child ToyModule instances automatically.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "_parameters", {})
        object.__setattr__(self, "_modules", {})

    def __setattr__(self, name: str, value: Any) -> None:
        if isinstance(value, ToyParameter):
            self._parameters[name] = value
        elif isinstance(value, ToyModule):
            self._modules[name] = value
        object.__setattr__(self, name, value)

    def parameters(self) -> List[ToyParameter]:
        params = list(self._parameters.values())
        for mod in self._modules.values():
            params.extend(mod.parameters())
        return params
