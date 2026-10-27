#!/usr/bin/env python3
"""Self-checking lab for Chapter 3.4: Classes, dataclasses, typing and protocols."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from python_classes_typing_protocols import (
    Commuter5,
    Extender,
    HackerClubMember,
    Inheritor,
    LottoBlower,
    Manager,
    Person,
    Provider,
    PseudoprivateC3,
    Replacer,
    SkipObject,
    SupportsLessThan,
    ThirdClass,
    UpperDict,
    Vector,
    Vector2d,
    top,
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
    # 1. LP Ch. 27 & 28: ThirdClass, Person, Manager, and AttrDisplay
    a = ThirdClass("abc")
    b = a + "xyz"
    a.mul(3)
    sue = Person("Sue Jones", job="dev", pay=100000)
    sue.giveRaise(0.10)
    pat = Manager("Pat Jones", 50000)
    pat.giveRaise(0.10)
    check(
        "ThirdClass overloads +/mul/__str__, and Manager.giveRaise augments Person.giveRaise with 10% bonus (50000 -> 60000)",
        str(b) == "[ThirdClass: abcxyz]"
        and a.data == "abcabcabc"
        and sue.lastName() == "Jones"
        and sue.pay == 110000
        and pat.pay == 60000
        and repr(pat) == "[Manager: job=mgr, name=Pat Jones, pay=60000]",
    )

    # 2. LP Ch. 29-31: specialize.py, SkipObject multi-scan, Commuter5, and pseudoprivate __X mangling
    skipper = SkipObject("abcdef")
    pairs = [x + y for x in skipper for y in skipper]
    c_x = Commuter5(88)
    c_y = Commuter5(99)
    c3 = PseudoprivateC3()
    c3.meth1()
    c3.metha()
    check(
        "specialize.py classes, SkipObject 9 nested pairs, Commuter5(88)+Commuter5(99)==187, and _C1__X/_C2__X mangling",
        Inheritor().method() == "in Super.method"
        and Replacer().method() == "in Replacer.method"
        and "starting Extender.method" in Extender().method()
        and Provider().delegate() == "in Provider.action"
        and len(pairs) == 9
        and pairs[0] == "aa"
        and pairs[-1] == "ee"
        and repr(c_x + c_y) == "Commuter5(187)"
        and repr(1 + c_y) == "Commuter5(100)"
        and c3.__dict__ == {"_C1__X": 88, "_C2__X": 99}
        and (c3.meth2(), c3.methb()) == (88, 99),
    )

    # 3. FP Ch. 11: Vector2d (__bytes__, frombytes, polar format 'p', __slots__, __hash__)
    v2d = Vector2d(3, 4)
    v2d_clone = Vector2d.frombytes(bytes(v2d))
    check(
        "Vector2d round-trips via bytes(), formats Cartesian & polar ('0.5fp'), hashes, and omits __dict__ via __slots__",
        v2d == v2d_clone
        and abs(v2d) == 5.0
        and format(v2d, ".2f") == "(3.00, 4.00)"
        and format(Vector2d(1, 1), "0.5fp") == "<1.41421, 0.78540>"
        and not hasattr(v2d, "__dict__")
        and isinstance(hash(v2d), int),
    )

    # 4. FP Ch. 12 & 16: N-dimensional Vector (slicing, dynamic x/y/z/t, zip_longest +, scalar *, dot product @)
    v = Vector([3.0, 4.0, 5.0])
    v_sum = v + (10, 20)
    v_rsum = (10, 20) + v
    v_mul = 10 * v
    dot = Vector([1, 2, 3]) @ Vector([4, 5, 6])
    check(
        "N-dim Vector slices into Vector, resolves v.x/v.y/v.z, computes zip_longest +, scalar *, and @ dot product (32.0)",
        isinstance(v[1:], Vector)
        and (v.x, v.y, v.z) == (3.0, 4.0, 5.0)
        and v_sum == Vector([13.0, 24.0, 5.0])
        and v_rsum == v_sum
        and v_mul == Vector([30.0, 40.0, 50.0])
        and dot == 32.0,
    )

    # 5. FP Ch. 5: HackerClubMember dataclass with ClassVar and __post_init__ validation
    HackerClubMember.all_handles.clear()
    leo = HackerClubMember("Leo Rochael")
    leo2 = HackerClubMember("Leo DaVinci", handle="Neo")
    dup_raised = False
    try:
        HackerClubMember("Leo Smith")
    except ValueError:
        dup_raised = True
    check(
        "HackerClubMember derives default handle='Leo', tracks ClassVar all_handles, and rejects duplicate handles",
        leo.handle == "Leo"
        and leo2.handle == "Neo"
        and dup_raised is True
        and HackerClubMember.all_handles == {"Leo", "Neo"},
    )

    # 6. FP Ch. 8, 13, 14, 15: LottoBlower[int] ABC/Generic, SupportsLessThan Protocol top(), and UpperDict Mixin
    machine = LottoBlower[int]([10, 20, 30])
    first = machine.pick()
    remain = machine.inspect()
    ud = UpperDict([("a", "letter A"), (2, "digit two")])
    ud["b"] = "letter B"
    check(
        "LottoBlower[int] picks/inspects, top() sorts SupportsLessThan, and UpperDict normalizes string keys to uppercase",
        first == 10
        and remain == (20, 30)
        and top([4, 1, 9, 2], 2) == [9, 4]
        and isinstance(5, SupportsLessThan)
        and ud["a"] == "letter A"
        and ud.get("b") == "letter B"
        and ("b" in ud) is True
        and list(ud.keys()) == ["A", 2, "B"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
