#!/usr/bin/env python3
"""Self-checking lab for Chapter 3.1: Python core: types, control flow, functions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from python_core_fundamentals import (
    add_node_safe,
    compare_floor_vs_trunc,
    demonstrate_shallow_vs_deep_copy,
    make_nonlocal_counter,
    sanitize_and_render_host_template,
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
    # 1. Floor division (//, math.floor) vs truncation (math.trunc, int) (Section 3, LP Ch. 5)
    pos = compare_floor_vs_trunc(5, 2)
    neg = compare_floor_vs_trunc(5, -2)
    check("for +5/2 (2.5), floor (2) and truncation (2) agree",
          pos["floor_div_op"] == 2 and pos["math_trunc"] == 2)
    check("for 5/-2 (-2.5), floor division rounds down to -3 while math.trunc/int truncate toward zero to -2",
          neg["floor_div_op"] == -3
          and neg["math_floor"] == -3
          and neg["math_trunc"] == -2
          and neg["int_trunc"] == -2)

    # 2. Shallow vs deep copy of nested mutable structures (Section 2, FP Ch. 6)
    cp = demonstrate_shallow_vs_deep_copy()
    check("mutating inner list affects alias (len 3) and shallow copy (len 3), but NOT deepcopy (len 2)",
          cp["alias_len"] == 3
          and cp["shallow_len"] == 3
          and cp["deep_len"] == 2
          and cp["shallow_shares_inner_list"] is True
          and cp["deep_shares_inner_list"] is False)

    # 3. str.maketrans/translate and string.Template (Section 4, LP Ch. 7)
    st = sanitize_and_render_host_template("gpu-01: (rack-2)", "node1", 8)
    check("str.translate converts 'gpu-01: (rack-2)' to 'gpu_01_rack_2' and Template renders 'node1 has 8 GPUs'",
          st["normalized_label"] == "gpu_01_rack_2"
          and st["rendered"] == "node1 has 8 GPUs"
          and st["safe_partial"] == "node1 has ${gpus} GPUs")

    # 4. Safe default argument idiom vs mutable default trap (Section 8)
    c1 = add_node_safe("10.0.0.1")
    c2 = add_node_safe("10.0.0.2")
    check("add_node_safe(ip, nodes=None) creates independent lists across calls",
          c1 == ["10.0.0.1"] and c2 == ["10.0.0.2"] and (c1 is not c2))

    # 5. LEGB closure with nonlocal state (Section 8)
    counter = make_nonlocal_counter(0)
    check("closure with nonlocal increments state across calls (1, 2, 3)",
          [counter(), counter(), counter()] == [1, 2, 3])

    # 6. Additional provenance checks from chapter text
    check("3,840,755,982,336 bytes is 3577.0 GiB (1024**3)",
          round(3_840_755_982_336 / (1024 ** 3), 1) == 3577.0)
    check("round() uses round-half-to-even: round(2.5) == 2 and round(3.5) == 4",
          round(2.5) == 2 and round(3.5) == 4)
    check("compare_floor_vs_trunc raises ZeroDivisionError on 0 denominator",
          _raises_zero(lambda: compare_floor_vs_trunc(5, 0)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises_zero(fn) -> bool:
    try:
        fn()
        return False
    except ZeroDivisionError:
        return True


if __name__ == "__main__":
    main()
