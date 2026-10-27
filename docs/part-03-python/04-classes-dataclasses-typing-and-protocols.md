---
id: "c03-04"
title: "3.4 Classes, dataclasses, typing and protocols"
sidebar_label: "3.4 Classes, dataclasses, typing and protocols"
sidebar_position: 4
description: "Classes and OOP for infrastructure code: attributes, methods, inheritance and MRO, composition, data class builders, type hints, protocols, ABCs, pydantic validation, operator overloading and design"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.4 Classes, dataclasses, typing and protocols

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Any machine with Python 3.11+; `pip install mypy pyright pydantic` |
| Part | Part 3: Python for infrastructure |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Infrastructure scripts grow into software: a Redfish client with a session and retry policy, a Slurm wrapper with typed job records, a provider interface hiding GCP, AWS and on-prem differences, a configuration model validated from YAML, an exporter holding metric state. Object-oriented design, data classes, and type hints are how that growth stays maintainable: they make state explicit, interfaces enforceable and errors catchable before production. Modern Python also leans on typing at runtime (pydantic models validate API input, FastAPI builds documentation from annotations, dataclasses generate boilerplate), so understanding the machinery matters. This chapter covers classes and the object model, inheritance and composition, data class builders (`namedtuple`, `NamedTuple`, `dataclass`, `attrs`, pydantic), type hints and static checking (`mypy`, `pyright`), protocols and ABCs, generics, operator overloading, and design guidance for infrastructure code.

## Prerequisites and outcomes

You should know functions and the data model (chapters 3.1 and 3.3).

After this chapter you can:

- Write classes with instance and class attributes, methods, `@classmethod`, `@staticmethod`, `@property`, `__slots__`, and explain attribute lookup and bound methods.
- Use inheritance (single and multiple), `super()`, the MRO (C3), mixins, and know when to prefer composition; design abstract interfaces with `abc.ABC` and `typing.Protocol`.
- Build data classes with `namedtuple`/`NamedTuple`, `@dataclass` (fields, defaults, `field(default_factory=...)`, `frozen`, `slots`, `kw_only`, `__post_init__`, ordering), `attrs`, and pydantic; choose among them.
- Add type hints to functions, variables and classes; use `Optional`/`|`, `list[str]`, `dict[str, int]`, `Callable`, `TypedDict`, `Literal`, `Final`, `Annotated`, `TypeVar`, generics, `ParamSpec`, `overload`, `Self`; run mypy/pyright in CI and configure strictness.
- Implement operator overloading and rich comparisons properly (`total_ordering`, NotImplemented).
- Validate configuration and API data with pydantic; manage secrets and settings.
- Apply design principles: composition over inheritance, dependency injection, small interfaces, immutability, explicit errors.

## 1. Classes and objects

### Class definition and instances

```python
class Node:
    """A compute node in the cluster."""
    cluster = "ai-prod"                      # class attribute: shared by all instances
    _count = 0

    def __init__(self, name: str, gpus: int = 8) -> None:
        self.name = name                      # instance attributes live in the instance __dict__
        self.gpus = gpus
        self._state = "unknown"               # leading underscore: "internal" by convention
        Node._count += 1

    def __repr__(self) -> str:
        return f"Node(name={self.name!r}, gpus={self.gpus})"

    def drain(self) -> None:                  # instance method: first parameter is self
        self._state = "draining"

    @property
    def state(self) -> str:                   # read-only computed attribute, accessed as node.state
        return self._state

    @state.setter
    def state(self, value: str) -> None:      # validation on assignment
        if value not in {"ready", "draining", "down", "unknown"}:
            raise ValueError(f"bad state {value!r}")
        self._state = value

    @classmethod
    def from_dict(cls, d: dict) -> "Node":    # alternative constructor; cls supports subclasses
        return cls(d["name"], d.get("gpus", 8))

    @staticmethod
    def valid_name(name: str) -> bool:        # utility namespaced in the class; no self/cls
        return name.isidentifier() or "-" in name
```

Key facts:

- `class` is an **executable statement** creating a class object (an instance of `type`). Calling the class creates an instance: `__new__` allocates, `__init__` initialises.
- `self` is just the conventional name for the instance; methods are functions stored on the class that become **bound methods** when accessed through an instance (`node.drain` is a bound method object carrying `node`).
- **Attribute lookup (`object.attr`) and inheritance search**: every `object.attr` expression triggers a bottom-up search of a tree of linked namespace objects—looking first in the **instance** object (`self`, via `self.__dict__`), then in its **class** (`self.__class__`), and then in all higher **superclasses** in the class tree from bottom to top and left to right (linearised as `self.__class__.__mro__`), returning the first `attr` found (with data descriptors such as `@property` or `__slots__` on the class taking precedence over the instance `__dict__`, and `__getattr__` called as a fallback if nothing is found). Because lower definitions in the tree are found first, subclasses override superclass attributes simply by redefining them. Assignment (`obj.attr = v`), by contrast, does not climb the inheritance tree: it writes directly to the target object's namespace (`obj.__dict__`, or invokes a data descriptor setter). Class attributes are shared; assigning via an instance **shadows** rather than modifying them (`node.cluster = "x"` creates an instance attribute on `node`).
- **Classes are not enclosing (`E`) scopes in LEGB**: while a `class` body executes in its own local namespace dictionary (which becomes the class's attribute dictionary), a `class` statement **never acts as an enclosing (`E`) scope** for `def` methods or nested classes inside it under the `LEGB` rule (lookup is `LEGB`, not `LCEGB`). Unqualified names inside a method skip the enclosing `class` and resolve in enclosing `def` functions, the module global (`G`) scope, or built-ins (`B`). Methods must always qualify class attributes via `self.attr` (inheritance search) or `ClassName.attr`:

```python
# In the book's classscope3.py example (untested here):
X = 1
def nester():
    X = 2                        # enclosing function scope (E)
    class C:
        X = 3                    # class attribute C.X (not in LEGB for methods)
        def method1(self):
            print(X)             # prints 2 (from nester's E scope, NOT 3 in class C)
            print(self.X)        # prints 3 (via inheritance on self -> C.X)
```

- **Mutable class attributes** (a list or dict at class level) are shared by all instances: a common bug source. Create per-instance mutable state in `__init__`.
- **Privacy** is by convention: `_name` (internal), `__name` (name-mangled to `_Class__name` to avoid subclass clashes, not true privacy). Python trusts programmers; document the public API.
- **`@property`** exposes methods as attributes: start with plain attributes and add properties later without changing callers. Use for validation, derived values, lazy computation (`functools.cached_property`), and read-only fields.
- **`__slots__` and its inheritance rules**: assigning a sequence of attribute name strings to `__slots__` reserves fixed per-instance storage managed by class-level descriptors instead of allocating a per-instance `__dict__` (and `__weakref__`), saving memory when millions of instances exist. However, `__slots__` has strict inheritance rules:
  - **Every class in the hierarchy must define `__slots__`:** if a subclass defines `__slots__` but a superclass does not (or a superclass defines `__slots__` and a subclass does not), the class without `__slots__` still creates an instance `__dict__` on every instance, negating the memory savings (in the book's example, `class C: pass; class D(C): __slots__ = ['a']` still gives `D()` an instance `__dict__`). Subclasses that add no new attributes must still declare `__slots__ = ()`.
  - **Do not repeat slot names in subclasses:** instances inherit the union of all `__slots__` along the MRO; repeating a superclass slot name in a subclass hides the superclass slot descriptor and wastes space.
  - **No class-level defaults of the same name and single non-empty base:** because each slot name is a class-level descriptor on the class, assigning a class attribute with the same name (`class C: __slots__ = ['a']; a = 99`) raises `ValueError: 'a' in __slots__ conflicts with class variable`. In multiple inheritance, at most one base class may have a non-empty `__slots__` (mixing two classes with non-empty `__slots__` raises `TypeError: multiple bases have instance lay-out conflict`; mixins should use `__slots__ = ()`).
  - **Generic attribute inspection:** because slotted instances lack `__dict__` (unless `'__dict__'` is explicitly included in `__slots__`) and `obj.__slots__` shows only the lowest class's list rather than the union across superclasses, generic tools should use `dir(obj)` and `getattr(obj, name)` rather than indexing `obj.__dict__`.
- **`__init__` must not do heavy IO** (network calls, file reads) when avoidable: prefer explicit factory classmethods or lazy connection, so objects are cheap to construct and test.

### Object lifecycle and identity

`__new__` (rarely overridden; used for singletons, immutables), `__init__`, `__del__` (avoid), `__enter__/__exit__` for deterministic cleanup. Equality and hashing by value need explicit methods (or dataclasses). `copy.copy(obj)` and `copy.deepcopy(obj)` customise via `__copy__`/`__deepcopy__`. Pickling (`pickle`, `__getstate__`) is unsafe for untrusted data and brittle across versions: serialise to JSON/YAML/protobuf instead.

## 2. Inheritance, composition and protocols

### Inheritance and `super()`

```python
class Resource:
    def __init__(self, name):
        self.name = name
    def describe(self): return f"{type(self).__name__}({self.name})"

class GpuNode(Resource):
    def __init__(self, name, gpus):
        super().__init__(name)         # cooperative: delegates to the next class in the MRO
        self.gpus = gpus
    def describe(self):                 # override and extend
        return super().describe() + f" gpus={self.gpus}"
```

- `super()` returns a proxy that delegates to the **next class in the instance's MRO** (`self.__class__.__mro__` past the class containing the `super()` call), not necessarily the direct parent; this is what makes cooperative multiple inheritance work, provided the class hierarchy satisfies three cooperative `super()` call-chain rules:
  1. **Universal deployment:** every class in the MRO that implements the method before the anchor must call `super().method()`. The first class that omits `super()` stops the chain (in the book's example, if `class C(B, A)` calls `super().act()` and `B.act` does not call `super().act()`, `A.act` is never reached).
  2. **Call-chain anchors:** the MRO chain must end at an anchor class that defines the method without calling `super()` again. For `__init__`, the built-in root `object` provides an anchor (`object.__init__(self)`), but for custom methods such as `act(self)`, calling `super().act()` in the last class before `object` raises `AttributeError: 'super' object has no attribute 'act'` unless a common base/anchor class (such as `class X: def act(self): ...`) precedes `object` on the MRO.
  3. **Compatible argument signatures:** because a class's next neighbor on `self.__class__.__mro__` depends on the subclass's inheritance graph, all cooperative implementations of a method across the tree must accept compatible signatures (or consume their own keyword arguments and forward `**kwargs`), and `object.__init__()` at the end of an `__init__` chain accepts no extra arguments beyond `self` (`TypeError: object.__init__() takes exactly one argument`).
- **Method Resolution Order**: Python linearises the class hierarchy using the **C3 algorithm**: children before parents, parents in the declared order, and each class appears once; `Class.__mro__` or `Class.mro()` shows it. In diamond inheritance, the shared base is reached once, after all its subclasses.

```python
class A: 
    def f(self): return "A"
class B(A): 
    def f(self): return "B>" + super().f()
class C(A): 
    def f(self): return "C>" + super().f()
class D(B, C): 
    def f(self): return "D>" + super().f()
D().f()        # 'D>B>C>A'
D.__mro__      # (D, B, C, A, object)
```

- **Mixins**: small classes adding one capability (logging, tagging, serialisation) to be combined via multiple inheritance; keep them stateless or with minimal state, with no `__init__` requirements, and name them `...Mixin`.
- **`isinstance(x, Base)`** and **`issubclass`** respect inheritance; `type(x) is T` checks exact types (rarely wanted).
- **Liskov substitution principle**: subclasses must honour the base class contract (accept at least what the base accepts, return no less than promised, not raise new surprising exceptions).

### Composition over inheritance

"Has-a" beats "is-a" for most infrastructure code: inheritance couples subclasses to parent implementation and creates deep, fragile hierarchies. Prefer holding collaborators as attributes and delegating:

```python
class RedfishClient:
    def __init__(self, session, retry_policy, logger):      # dependencies injected
        self._session, self._retry, self._log = session, retry_policy, logger
    def get_power(self, host): return self._retry(lambda: self._session.get(f"https://{host}/redfish/v1/Chassis/1/Power"))
```

Benefits: dependencies are explicit and swappable (pass a fake session in tests), classes stay small, behaviours combine freely. **Dependency injection** is simply passing collaborators in rather than constructing them inside (no framework needed).

### Abstract base classes

```python
from abc import ABC, abstractmethod

class Provider(ABC):
    """Contract for cloud/on-prem providers."""
    @abstractmethod
    def create_vm(self, name: str, cpus: int) -> str: ...
    @abstractmethod
    def delete_vm(self, vm_id: str) -> None: ...
    def ensure_vm(self, name: str, cpus: int) -> str:       # concrete template method built on abstract ones
        return self.find(name) or self.create_vm(name, cpus)
    @abstractmethod
    def find(self, name: str) -> str | None: ...

class Gcp(Provider): ...         # must implement all abstract methods or instantiation raises TypeError
```

ABCs enforce that subclasses implement required methods at instantiation time, and provide **virtual subclassing** (`Provider.register(Third)`); `collections.abc` supplies container ABCs (`Iterable`, `Sequence`, `Mapping`, `Callable`) for `isinstance` checks. Use an ABC when you want shared concrete behaviour plus enforced abstract methods and runtime checks.

### Protocols (structural typing)

A `typing.Protocol` describes an interface by the methods an object has, with no inheritance required: "if it quacks like a duck." Static checkers verify conformance; `@runtime_checkable` allows `isinstance` checks (method presence only).

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class SupportsClose(Protocol):
    def close(self) -> None: ...

class Sink(Protocol):
    def write(self, data: bytes) -> int: ...

def flush_to(sink: Sink, data: bytes) -> int:        # accepts files, sockets, BytesIO, your own classes
    return sink.write(data)
```

Choose: **Protocol** for interfaces at boundaries where implementers are third-party or unrelated (loose coupling, test fakes); **ABC** when you control the hierarchy and want runtime enforcement and shared code.

## 3. Data class builders

Plain classes need boilerplate (`__init__`, `__repr__`, `__eq__`). Data class builders generate it.

| Builder | Mutable? | Typing | Validation | Notes |
|---|---|---|---|---|
| `collections.namedtuple("P", "x y")` | No (tuple) | Untyped | None | Lightweight, tuple behaviour (unpack, index, hashable) |
| `typing.NamedTuple` | No | Typed fields | None | Class syntax, defaults, methods |
| `@dataclasses.dataclass` | Yes (or `frozen=True`) | Typed annotations (not enforced) | Via `__post_init__` | Standard library; most common |
| `attrs` (`@define`) | Yes/frozen | Optional | Validators/converters | Third party; predates dataclasses; richer |
| `pydantic.BaseModel` | Yes/frozen | Enforced at runtime (coercion/validation) | Strong, with errors | Parsing external data, settings, FastAPI |
| `TypedDict` | A dict | Static only | None | Typing JSON-like dicts; no runtime class |

```python
from dataclasses import dataclass, field, asdict, replace
from typing import ClassVar

@dataclass(order=True, frozen=True, slots=True, kw_only=True)
class GpuNode:
    name: str
    rack: str
    gpus: int = 8
    tags: tuple[str, ...] = ()
    MAX_GPUS: ClassVar[int] = 16                        # class variable, not a field

    def __post_init__(self):                              # validation hook
        if not 0 < self.gpus <= self.MAX_GPUS:
            raise ValueError(f"gpus out of range: {self.gpus}")

@dataclass
class Cluster:
    name: str
    nodes: list[GpuNode] = field(default_factory=list)   # NEVER default=[]: dataclasses reject mutable defaults
    meta: dict[str, str] = field(default_factory=dict)

n = GpuNode(name="gpu01", rack="r1")
n2 = replace(n, gpus=4)                  # frozen: create modified copies
asdict(n)                                # to dict (recursive), for JSON
sorted([n2, n])                          # order=True generates comparisons from field order
```

Options: `frozen=True` (immutable, hashable with `eq`), `order=True`, `slots=True` (3.10+), `kw_only=True`, `eq=True`, `unsafe_hash`, `repr=False`; field options `field(default_factory, repr=False, compare=False, init=False, metadata={...})`; `InitVar` for init-only parameters; `dataclasses.fields(obj)` for introspection. Inheritance works, but field ordering rules (non-default after default) can bite; `kw_only` helps.

**Pitfalls:** annotations are not enforced (`GpuNode(name=5)` succeeds); validate in `__post_init__` or use pydantic at boundaries. `frozen` dataclasses are shallowly immutable (a list inside can still be mutated; use tuples/frozenset). Dataclass equality compares all fields (use `compare=False` for volatile ones).

### Pydantic

Pydantic models validate and coerce input at runtime and are the standard for parsing external data (YAML/JSON configs, API requests, environment variables).

```python
from pydantic import BaseModel, Field, field_validator, ValidationError, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from ipaddress import IPv4Address
from typing import Literal

class NodeSpec(BaseModel):
    model_config = {"extra": "forbid", "frozen": True}     # reject unknown keys: catches typos in config files
    name: str = Field(pattern=r"^[a-z0-9-]+$", max_length=63)
    ip: IPv4Address
    gpus: int = Field(8, ge=1, le=16)
    role: Literal["compute", "login", "storage"] = "compute"

    @field_validator("name")
    @classmethod
    def no_reserved(cls, v):
        if v in {"localhost", "admin"}: raise ValueError("reserved name")
        return v

try:
    spec = NodeSpec.model_validate({"name": "gpu01", "ip": "10.0.0.5", "gpus": "8"})     # "8" coerced to int 8
except ValidationError as e:
    print(e.errors())                    # structured list of errors with locations

spec.model_dump(), spec.model_dump_json(), NodeSpec.model_json_schema()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MYOPS_", env_file=".env")
    api_url: str
    api_token: SecretStr                 # repr shows '**********'; use .get_secret_value() deliberately
    timeout: float = 10.0
```

Notes: pydantic v2 (Rust core) is fast; v1 has a different API; models can be nested, generic, discriminated unions (`Field(discriminator="type")`), computed fields; FastAPI uses them for request/response schemas (chapter 3.7). Validate **at the boundary** (config load, API ingress), then pass trusted, typed objects internally (parse, don't validate repeatedly).

## 4. Type hints and static checking

Type hints (PEP 484 and successors) annotate intent. **CPython ignores them at runtime** (stored in `__annotations__`); tools enforce them: `mypy`, `pyright`/Pylance, `pyre`, `pytype`, and IDEs. Libraries like pydantic and FastAPI read them at runtime.

```python
from collections.abc import Iterable, Iterator, Mapping, Sequence, Callable
from typing import Any, Final, Literal, TypedDict, TypeVar, Generic, overload, Self, TypeAlias, NewType, Annotated

def parse_size(s: str) -> int: ...
def first_up(nodes: Iterable[Node]) -> Node | None: ...                  # 3.10+ union syntax (Optional[Node] before)
def group(nodes: Sequence[Node]) -> dict[str, list[Node]]: ...           # builtin generics (3.9+): list[int], dict[str, int], tuple[int, ...]
def retry(fn: Callable[[], T], attempts: int = 3) -> T: ...
Port = NewType("Port", int)                                               # distinct type for the checker
MAX_RETRIES: Final = 5                                                    # constant
Mode = Literal["dry-run", "apply"]
class Event(TypedDict, total=False):                                      # shape of a dict
    type: str
    node: str
JsonScalar: TypeAlias = str | int | float | bool | None
```

Essentials:

- **Parameters accept general types, return specific types**: take `Iterable`/`Sequence`/`Mapping`, return `list`/`dict`. Don't annotate with `list` when any iterable will do.
- **`Optional[X]` is `X | None`**: the checker forces you to handle `None`. Narrowing: `if x is not None:`; `isinstance`; `assert x`; early returns.
- **`Any`** disables checking for that value (escape hatch, spreads silently); prefer `object` or a Protocol; use `# type: ignore[code]` sparingly with justification.
- **Generics**: `TypeVar("T")` for functions preserving types; `class Stack(Generic[T])` or the 3.12 syntax `class Stack[T]:` / `def first[T](xs: Sequence[T]) -> T:`; bounded `TypeVar("T", bound=Comparable)`; `ParamSpec`/`Concatenate` for decorators preserving signatures (chapter 3.11); `Self` for fluent methods/classmethods returning the same class.
- **`@overload`** to express return type depending on argument type/literal.
- **Callable** types: `Callable[[int, str], bool]`; for keyword/complex signatures use a Protocol with `__call__`.
- **Variance**: `Sequence` is covariant (a `Sequence[Dog]` is a `Sequence[Animal]`), `list` invariant (a `list[Dog]` is not a `list[Animal]`) because lists are mutable.
- **`TYPE_CHECKING`** blocks for imports used only in annotations (avoid cycles/cost): `if TYPE_CHECKING: from .models import Node`; with `from __future__ import annotations` (or 3.14 deferred evaluation) annotations become lazily evaluated strings.
- **`Annotated[int, Field(ge=0)]`** attaches metadata used by pydantic/FastAPI.
- **`typing.Protocol`, `TypedDict`, `NamedTuple`, `dataclass_transform`** support framework authors.
- **Gradual typing**: annotate public APIs first; enable strictness progressively (`mypy --strict`, per-module overrides, `pyright` basic vs strict); keep the type-check job in CI (chapter 3.9) and treat new errors as build failures.

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true
[[tool.mypy.overrides]]
module = ["redfish.*", "paramiko.*"]
ignore_missing_imports = true
```

```bash
mypy src/ ; pyright ; python -m mypy --install-types ; stubgen -p thirdparty   # stubs for untyped libraries (types-requests, types-PyYAML packages)
```

Typing for infrastructure code is high value at **boundaries** (API clients, config models, plugin interfaces) and in code with many `None`/Optional cases; it catches wrong argument order, missing awaits, and forgotten error paths.

## 5. Operator overloading and comparison

Overload operators only when the meaning is natural (vectors, sizes, versions, durations), return new objects (value semantics), return `NotImplemented` for unknown operand types, and keep `__eq__`/`__hash__`/ordering consistent.

```python
from functools import total_ordering

@total_ordering                      # supply __eq__ and one of <, <=, >, >=; others are generated
class Version:
    def __init__(self, s: str): self.parts = tuple(int(p) for p in s.split("."))
    def __eq__(self, o): return NotImplemented if not isinstance(o, Version) else self.parts == o.parts
    def __lt__(self, o): return NotImplemented if not isinstance(o, Version) else self.parts < o.parts
    def __hash__(self): return hash(self.parts)
    def __repr__(self): return f"Version({'.'.join(map(str, self.parts))!r})"

class Bytes(int):                    # subclass a builtin for a domain type
    def __str__(self):
        n, units = float(self), ["B", "KiB", "MiB", "GiB", "TiB"]
        for u in units:
            if n < 1024 or u == units[-1]: return f"{n:.1f} {u}"
            n /= 1024
```

For real version handling use `packaging.version.Version`; for IP addresses `ipaddress`; for durations `datetime.timedelta`. Also: reflected (`__radd__`), in-place (`__iadd__` should mutate and return `self`), unary (`__neg__`), bitwise, `__matmul__` for matrix multiplication, `__contains__`, `__call__`, `__format__` for custom format specs.

## 6. Design guidance for infrastructure code

1. **Use functions until state or polymorphism appears.** A module of functions is often the best design. Use a class when you have state that travels together (a session and its credentials), an interface with multiple implementations, or a lifecycle (open/close).
2. **Separate IO from logic.** Pure functions that transform data (parse, decide, format) are easy to test; thin IO shells call them. This is the "functional core, imperative shell" pattern and makes tools testable without clusters (chapter 3.9).
3. **Make illegal states unrepresentable**: use enums/Literals for states, frozen dataclasses for values, validation at construction.
4. **Small, explicit interfaces**: depend on a Protocol with two methods rather than a concrete client with fifty; inject it.
5. **Immutability by default** for configuration and value objects.
6. **Errors as part of the API**: define a small exception hierarchy (`class MyOpsError(Exception)`; `class NodeNotFound(MyOpsError)`), raise specific errors, document them; don't return `None`/magic values to signal failure when an exception is clearer (chapter 3.5).
7. **Avoid deep inheritance**; keep to one or two levels; prefer composition and mixins sparingly.
8. **Enums** for fixed choices: `class State(enum.StrEnum): READY = "ready"; DOWN = "down"` (3.11 `StrEnum`), `enum.auto()`, `Flag` for bit flags; they serialise cleanly and prevent typos.
9. **Logging and repr**: give every domain object a useful `__repr__`; log with `%r`.
10. **Avoid global mutable singletons**; pass objects explicitly or use a clearly scoped context (a `Settings` instance).
11. **Document behaviour with docstrings and types**, and keep public APIs stable (deprecate with `warnings.warn(..., DeprecationWarning)`).
12. **SOLID in practice**: single responsibility (a class changes for one reason), open/closed via registries/plugins, Liskov via contracts, interface segregation via Protocols, dependency inversion via injection.

### Example: a typed provider layer

```python
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

class State(StrEnum):
    PENDING = "pending"; RUNNING = "running"; STOPPED = "stopped"

@dataclass(frozen=True, slots=True)
class Instance:
    id: str
    name: str
    state: State
    ip: str | None = None

class Compute(Protocol):
    def list_instances(self, project: str) -> list[Instance]: ...
    def start(self, project: str, instance_id: str) -> None: ...

def ensure_running(c: Compute, project: str, names: set[str]) -> list[str]:
    started = []
    for inst in c.list_instances(project):
        if inst.name in names and inst.state is not State.RUNNING:
            c.start(project, inst.id)
            started.append(inst.name)
    return started

class FakeCompute:                                      # test double satisfying the Protocol, no inheritance
    def __init__(self, instances): self.instances, self.started = instances, []
    def list_instances(self, project): return self.instances
    def start(self, project, instance_id): self.started.append(instance_id)

def test_ensure_running():
    fake = FakeCompute([Instance("1", "a", State.STOPPED), Instance("2", "b", State.RUNNING)])
    assert ensure_running(fake, "p", {"a", "b"}) == ["a"] and fake.started == ["1"]
```

## 7. Lab (untested)

1. **Class basics**: build `Node` with properties, class/static methods and `__slots__`; show instance vs class attribute shadowing; reproduce the shared mutable class attribute bug and fix it; view bound methods, `__dict__`, `vars()`, `dir()`.
2. **Inheritance and MRO**: implement the diamond (A, B, C, D) with cooperative `super()`; print `__mro__`; break it by omitting a `super()` call and explain; build a mixin (`TaggableMixin`) and a composition-based alternative; compare.
3. **ABC vs Protocol**: define `Provider` as an ABC (instantiation error for missing methods) and `Compute` as a Protocol; implement a fake satisfying the Protocol without inheritance; run mypy to see conformance errors; use `@runtime_checkable`.
4. **Data classes**: model the cluster with `namedtuple`, `NamedTuple`, `dataclass` (frozen, slots, order), and `pydantic`; compare memory (`sys.getsizeof`/`tracemalloc`), speed of creation (`timeit`), and behaviour with bad input; show the mutable default error; use `replace` and `asdict`.
5. **Pydantic**: load a YAML cluster definition into nested models with `extra="forbid"`; produce clear error messages for typos and wrong types; generate a JSON schema; use `BaseSettings` with environment variables and `SecretStr`.
6. **Typing**: annotate a small module (API client, parser, scheduler); run `mypy --strict` and fix errors; introduce `Optional` bugs and see them caught; write generic `first[T]` and a `Protocol` with `__call__`; use `TypedDict` for a JSON payload; add `py.typed` marker to a package.
7. **Operator overloading**: implement `Version` with `total_ordering`, a `Size` class (add, compare, format) and `Money` using `Decimal`; test mixed-type behaviour and `NotImplemented`.
8. **Refactor**: take a script with global state and dict-shaped data; refactor into a functional core (pure functions on dataclasses) and an IO shell; write tests with fakes.
9. **Enums**: replace string constants with `StrEnum` and `Flag`; serialise to JSON; show invalid-value errors.
10. **Clean up.**

Mark tested only after execution.

## 8. Common mistakes

- Mutable class attributes and mutable default arguments; forgetting `default_factory` in dataclasses.
- Deep inheritance hierarchies; calling `super().__init__` inconsistently (breaking cooperative inheritance); overriding methods with different signatures.
- Using classes as namespaces for functions (use modules) or singletons (use module-level objects).
- Assuming type hints enforce anything at runtime; sprinkling `Any`; unchecked `# type: ignore`.
- Validating the same data repeatedly (or never) instead of at the boundary.
- Exposing mutable internals (returning the internal list) instead of copies/tuples.
- Overloading operators with surprising semantics; defining `__eq__` without `__hash__`.
- Doing IO in `__init__`; catching exceptions in constructors and leaving half-initialised objects.
- Pickling untrusted data; relying on `__del__`.
- Storing secrets in `repr`-visible attributes (use `SecretStr`).

## 9. Interview angles

- "What is the difference between a class attribute and an instance attribute? What bug can class-level lists cause?"
- "Explain MRO and `super()`. What is C3 linearisation? Resolve this diamond."
- "Composition vs inheritance: examples where you chose each."
- "ABC vs Protocol?"
- "Dataclass vs namedtuple vs pydantic vs plain class?"
- "Do type hints affect runtime? How do you enforce them in CI?"
- "How would you design a multi-cloud provisioning tool in Python?" (Interface, factory, injected clients, typed models, errors, tests.)
- "What does `@property` give you? `@classmethod` vs `@staticmethod`?"
- "What is `__slots__` and when would you use it?"
- "How do you make a class hashable and sortable correctly?"

## 10. Checkpoint questions (40)

1. What creates an instance? **A:** Calling the class: `__new__` then `__init__`.
2. What is `self`? **A:** The instance, passed as the first parameter by binding.
3. Instance vs class attribute? **A:** Per object vs shared by all instances.
4. What does assigning via instance do to a class attribute? **A:** Creates a shadowing instance attribute.
5. What is `@property` for? **A:** Attribute-style access to computed/validated values.
6. `@classmethod` vs `@staticmethod`? **A:** Receives the class vs receives nothing.
7. What does `__slots__` do, and what happens if a subclass defines `__slots__` while its superclass does not? **A:** `__slots__` fixes instance attributes and omits the per-instance `__dict__` to save memory, but if any class in the inheritance hierarchy omits `__slots__`, that class still creates an instance `__dict__`, negating the memory savings unless every class in the hierarchy defines `__slots__` (using `__slots__ = ()` when adding no new attributes).
8. What is name mangling? **A:** `__x` becomes `_Class__x` to avoid subclass clashes.
9. What does `super()` do? **A:** Delegates to the next class in the MRO.
10. What algorithm builds the MRO? **A:** C3 linearisation.
11. How to see the MRO? **A:** `Class.__mro__`.
12. What is a mixin? **A:** A small class adding one capability via multiple inheritance.
13. Composition over inheritance means? **A:** Hold collaborators instead of subclassing.
14. What is dependency injection? **A:** Passing collaborators into objects.
15. What do ABCs enforce? **A:** Abstract methods must be implemented to instantiate.
16. What is a Protocol? **A:** Structural interface satisfied by method presence.
17. When prefer Protocol? **A:** Loose coupling with unrelated/third-party implementers.
18. What does `@dataclass` generate? **A:** `__init__`, `__repr__`, `__eq__` (and more).
19. Why `default_factory`? **A:** Avoid shared mutable defaults.
20. What does `frozen=True` do? **A:** Prevents attribute assignment; enables hashing.
21. What does `slots=True` do? **A:** Uses `__slots__` for the dataclass.
22. `order=True` effect? **A:** Generates comparison methods by field order.
23. What is `__post_init__`? **A:** Hook after generated init for validation/derived fields.
24. Does a dataclass validate types? **A:** No.
25. What does pydantic add? **A:** Runtime validation/coercion and JSON schema.
26. What does `extra="forbid"` do? **A:** Rejects unknown fields.
27. Why `SecretStr`? **A:** Prevents accidental secret exposure in logs/repr.
28. Do type hints run at runtime? **A:** No (stored but ignored by CPython).
29. What is `X | None`? **A:** Optional type.
30. Why accept `Iterable` but return `list`? **A:** Flexible inputs, concrete outputs.
31. What is `TypedDict`? **A:** Static typing for dict shapes.
32. What is `Literal` used for? **A:** Restrict to specific values.
33. What is a `TypeVar`? **A:** A placeholder for generic functions/classes.
34. List invariance example? **A:** `list[Dog]` is not a `list[Animal]`.
35. What is `NewType` for? **A:** Distinct types for the checker at no runtime cost.
36. Why return `NotImplemented`? **A:** Let Python try the other operand/reflected method.
37. What does `total_ordering` do? **A:** Derives other comparisons from `__eq__` and one ordering.
38. Functional core, imperative shell? **A:** Pure logic separated from IO.
39. Why exception hierarchies? **A:** Specific, catchable, documented failures.
40. Why avoid IO in `__init__`? **A:** Hard to test, slow construction, partial initialisation.

## 11. Sources and review notes

**Written in original words.** Principal sources:

- Luciano Ramalho, *Fluent Python*, 2nd ed.: chapter 5 (data class builders), chapter 8 (type hints in functions), chapter 11 (a Pythonic object), chapter 13 (interfaces, protocols and ABCs), chapter 14 (inheritance: for better or for worse), chapter 15 (more about type hints), chapter 16 (operator overloading).
- Mark Lutz, *Learning Python*, 6th ed. (`learning-python-6th-edition`, part VI: classes and OOP—with `Chapter 26. OOP: The Big Picture`, `Chapter 29. Class Coding Details`, and `Chapter 32. Class Odds and Ends` read in full for this chapter—covering the big picture, `object.attr` inheritance tree search, class coding basics, a more realistic example, class coding details, why `class` is not an enclosing `E` scope in `LEGB`, operator overloading, designing with classes, `__slots__` inheritance rules, cooperative `super()` call-chain rules, and class odds and ends).
- The author's `nvidia-devops` repository, volume 02: advanced OOP and design patterns (ABC provider interfaces, factories, MRO and multiple inheritance, class vs instance variables, dataclasses, pydantic configuration validation and secrets).
- Examples are the author's constructions.

**Flagged for verification before publishing:** version-specific features (`StrEnum` 3.11, `Self` 3.11, PEP 695 generics syntax 3.12, dataclass `slots`/`kw_only` 3.10), pydantic v2 API names, mypy/pyright option names, and every code listing; all labs are **untested**.
