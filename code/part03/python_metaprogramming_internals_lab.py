#!/usr/bin/env python3
"""Self-checking lab for Chapter 3.11: Python under the hood: decorators, descriptors and metaprogramming."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from python_metaprogramming_internals import (
    CardHolder,
    FrozenJSON,
    LineItem,
    ToyModule,
    ToyParameter,
    rangetest,
    record_factory,
    trace_class_creation_order,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. FP Ch. 22 FrozenJSON (__new__ + __getattr__ + keyword.iskeyword 'class' -> 'class_')
    feed = FrozenJSON(
        {
            "Schedule": {
                "events": [{"serial": 33950, "name": "There *Will* Be Bugs"}],
                "speakers": [{"name": "Anna Martelli Ravenscroft", "class": 2024}],
            }
        }
    )
    check(
        "FrozenJSON traverses nested dicts/lists via attributes and appends '_' to Python keywords ('class_')",
        feed.Schedule.events[0].name == "There *Will* Be Bugs"
        and feed.Schedule.speakers[0].class_ == 2024,
    )

    # 2. FP Ch. 23 LineItem with Validated, Quantity, and NonBlank descriptors (__set_name__)
    item = LineItem("  Moluccan nutmeg  ", 8, 13.95)
    blank_err = False
    neg_err = False
    try:
        LineItem("   ", 5, 10.0)
    except ValueError:
        blank_err = True
    try:
        item.weight = 0
    except ValueError:
        neg_err = True
    check(
        "LineItem descriptors strip NonBlank description, compute subtotal, and reject blank/non-positive values",
        item.description == "Moluccan nutmeg"
        and round(item.subtotal(), 2) == 111.60
        and blank_err is True
        and neg_err is True,
    )

    # 3. LP Ch. 38 CardHolder per-instance descriptor state (bob does not morph into sue!)
    bob = CardHolder("1234-5678", "Bob Smith", 40, "123 main st")
    sue = CardHolder("5678-1234", "Sue Jones", 35, "124 main st")
    check(
        "CardHolder per-instance descriptors isolate bob ('bob_smith', 22.5) from sue ('sue_jones', 27.5)",
        bob.name == "bob_smith"
        and bob.acct == "12345***"
        and bob.remain == 22.5
        and sue.name == "sue_jones"
        and sue.acct == "56781***"
        and sue.remain == 27.5,
    )

    # 4. LP Ch. 39 @rangetest(**argchecks) validating positional, keyword, and defaulted arguments
    @rangetest(age=(0, 120), M=(1, 12), D=(1, 31))
    def profile_entry(name: str, age: int, M: int = 8, D: int = 31) -> str:
        return f"{name}:{age}:{M}/{D}"

    ok_call = profile_entry("Pat", age=40, M=8)
    range_err = False
    try:
        profile_entry("Pat", 150)
    except TypeError:
        range_err = True
    check(
        "@rangetest validates positional and keyword arguments and preserves __name__ via @wraps",
        ok_call == "Pat:40:8/31"
        and range_err is True
        and profile_entry.__name__ == "profile_entry",
    )

    # 5. FP Ch. 24 record_factory dynamic class creation via type() & class-creation hook sequence
    Dog = record_factory("Dog", "name weight owner")
    rex = Dog("Rex", 30, owner="Bob")
    order = trace_class_creation_order()
    check(
        "record_factory creates slotted Dog class dynamically via type(), and class creation fires hooks in exact order 1..6",
        repr(rex) == "Dog(name='Rex', weight=30, owner='Bob')"
        and tuple(rex) == ("Rex", 30, "Bob")
        and order
        == [
            "1.__prepare__:Sub",
            "2.body:Sub",
            "3.__new__:Sub",
            "4.__set_name__:Sub.field",
            "5.__init_subclass__:Sub",
            "6.__init__:Sub",
        ],
    )

    # 6. Section 3.5 & 9.10 ToyModule.__setattr__ registering ToyParameter and child ToyModule (vs plain list)
    class Block(ToyModule):
        def __init__(self) -> None:
            super().__init__()
            self.w1 = ToyParameter("w1", (16, 16))

    class Net(ToyModule):
        def __init__(self) -> None:
            super().__init__()
            self.embed = ToyParameter("embed", (100, 16))
            self.block = Block()
            self.unregistered_list = [ToyParameter("lost", (4, 4))]

    net = Net()
    param_names = [p.name for p in net.parameters()]
    check(
        "ToyModule.__setattr__ registers direct and nested parameters ('embed', 'w1') while plain list parameters are skipped",
        param_names == ["embed", "w1"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
