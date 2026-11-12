#!/usr/bin/env python3
"""Self-checking lab for Chapter 3.3: Idiomatic Python: the data model, comprehensions, generators."""
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from python_idiomatic_data_model import (
    Node,
    Customer,
    NodeInventory,
    LineItem,
    Order,
    Result,
    StrKeyDict0,
    best_promo,
    bulk_item_promo,
    delegate_averager,
    demonstrate_tuple_inplace_add_puzzle,
    fidelity_promo,
    large_order_promo,
    make_averager,
    mymap_pad_gen,
    myzip_gen,
    permute1,
    permute2,
    scramble1,
    drain_order,
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
    # 1. NodeInventory (__len__, __getitem__, slicing, drain_order)
    deck = NodeInventory()
    aces = deck[12::13]
    ranked = sorted(deck, key=drain_order)
    check(
        "NodeInventory has 52 nodes, deck[12::13] slices slot 13 of all 4 racks, and drain_order ranks slot 01 of r1 (0) to slot 13 of r4 (51)",
        len(deck) == 52
        and len(aces) == 4
        and all(c.slot == "13" for c in aces)
        and ranked[0] == Node("01", "r1")
        and ranked[-1] == Node("13", "r4")
        and drain_order(Node("01", "r1")) == 0
        and drain_order(Node("13", "r4")) == 51,
    )

    # 2. FP Ch. 2 t = (1, 2, [30, 40]); t[2] += [50, 60] puzzle
    raised, mutated_tuple = demonstrate_tuple_inplace_add_puzzle()
    check(
        "t[2] += [50, 60] raises TypeError on tuple assignment AFTER mutating the inner list to [30, 40, 50, 60]",
        raised is True and mutated_tuple == (1, 2, [30, 40, 50, 60]),
    )

    # 3. FP Ch. 3 StrKeyDict0 (__missing__, get, __contains__)
    skd = StrKeyDict0([("2", "two"), ("4", "four")])
    check(
        "StrKeyDict0 converts int keys via __missing__ (skd[2] == 'two', 2 in skd, skd.get(1, 'N/A') == 'N/A')",
        skd["2"] == "two"
        and skd[4] == "four"
        and (2 in skd) is True
        and (1 in skd) is False
        and skd.get(1, "N/A") == "N/A",
    )

    # 4. FP Ch. 9 make_averager closure (__code__.co_freevars and nonlocal)
    avg = make_averager()
    check(
        "make_averager closure tracks count/total via nonlocal (10 -> 10.0, 11 -> 10.5, 12 -> 11.0)",
        avg(10) == 10.0
        and avg(11) == 10.5
        and avg(12) == 11.0
        and set(avg.__code__.co_freevars) == {"count", "total"},
    )

    # 5. FP Ch. 10 First-class function Strategy pattern & @promotion registry
    joe = Customer("John Doe", 0)
    ann = Customer("Ann Smith", 1100)
    cart = (
        LineItem("banana", 4, Decimal("0.5")),
        LineItem("apple", 10, Decimal("1.5")),
        LineItem("watermelon", 5, Decimal(5)),
    )
    banana_cart = (
        LineItem("banana", 30, Decimal("0.5")),
        LineItem("apple", 10, Decimal("1.5")),
    )
    long_cart = tuple(LineItem(str(sku), 1, Decimal(1)) for sku in range(10))
    check(
        "Order strategy functions compute fidelity (42.00 -> 39.90), bulk (30.00 -> 28.50), large order (10.00 -> 9.30), and best_promo",
        Order(joe, cart, fidelity_promo).due() == Decimal("42.00")
        and Order(ann, cart, fidelity_promo).due() == Decimal("39.90")
        and Order(joe, banana_cart, bulk_item_promo).due() == Decimal("28.50")
        and Order(joe, long_cart, large_order_promo).due() == Decimal("9.30")
        and Order(ann, cart, best_promo).due() == Decimal("39.90"),
    )

    # 6. LP Ch. 20 scramble1 vs permute1/permute2 (N=4 rotations vs N!=24 permutations)
    scr = list(scramble1("hack"))
    p1 = permute1("hack")
    p2 = list(permute2("hack"))
    check(
        "scramble1('hack') yields 4 rotations while permute1/permute2('hack') yield all 24 (4!) permutations",
        scr == ["hack", "ackh", "ckha", "khac"]
        and len(p1) == 24
        and p1 == p2,
    )

    # 7. LP Ch. 20 myzip_gen and mymap_pad_gen
    z = list(myzip_gen("abc", "xyz123"))
    mp = list(mymap_pad_gen("abc", "xyz123", pad=99))
    check(
        "myzip_gen truncates to shortest ('abc') while mymap_pad_gen pads missing items with pad=99",
        z == [("a", "x"), ("b", "y"), ("c", "z")]
        and mp == [("a", "x"), ("b", "y"), ("c", "z"), (99, "1"), (99, "2"), (99, "3")],
    )

    # 8. FP Ch. 17 yield from coroutine delegation & StopIteration return value capture
    coro_res = delegate_averager([10.0, 20.0, 30.0])
    check(
        "yield from averager_coro() sends values and captures Result(count=3, average=20.0)",
        coro_res == Result(count=3, average=20.0),
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
