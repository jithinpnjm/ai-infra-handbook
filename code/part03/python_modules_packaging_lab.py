#!/usr/bin/env python3
"""Self-checking lab for Chapter 3.2: Modules, packages, virtual environments and packaging."""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from python_modules_packaging import (
    build_dynamic_getattr_module,
    compare_dunder_import_vs_import_module,
    filter_from_star_exports,
    list_module_namespace,
    resolve_four_step_import_search,
    simulate_import_vs_from_and_reload,
    transitive_reload_recursive,
    transitive_reload_stack,
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
    # 1. import vs from reference copying, shared mutables, and reload() (LP Ch. 23 & 25)
    sim = simulate_import_vs_from_and_reload()
    check(
        "from share import x, y rebinds local x only while mutating y[0] in place; reload updates share.x",
        sim["share_x_before_reload"] == 1
        and sim["share_y_before_reload"] == ["hack", 2]
        and sim["copied_x_stale_after_reload"] == "hack"
        and sim["qualified_x_after_reload"] == "After editing"
        and sim["qualified_y_after_reload"] == [10, 20],
    )

    # 2. Four-step import search algorithm: regular package vs simple module vs PEP 420 namespace package (LP Ch. 24)
    cand = ["/ns/part1", "/ns/part2"]
    ns_fs = {"/ns/part1/sub", "/ns/part2/sub"}
    kind_ns, paths_ns = resolve_four_step_import_search(cand, ns_fs, "sub")
    check(
        "PEP 420 namespace package concatenates bare directories across candidate path entries",
        kind_ns == "namespace_package" and paths_ns == ["/ns/part1/sub", "/ns/part2/sub"],
    )

    # Adding __init__.py in /ns/part2/sub gives regular package precedence over earlier bare dir /ns/part1/sub!
    reg_fs = {"/ns/part1/sub", "/ns/part2/sub", "/ns/part2/sub/__init__.py"}
    kind_reg, paths_reg = resolve_four_step_import_search(cand, reg_fs, "sub")
    check(
        "regular package (__init__.py) in later sys.path entry beats bare namespace directory in earlier entry",
        kind_reg == "regular_package" and paths_reg == ["/ns/part2/sub/__init__.py"],
    )

    # Simple module in later sys.path entry also beats bare namespace directory in earlier entry
    mod_fs = {"/ns/part1/sub", "/ns/part2/sub.py"}
    kind_mod, paths_mod = resolve_four_step_import_search(cand, mod_fs, "sub")
    check(
        "simple module (sub.py) in later sys.path entry beats bare namespace directory in earlier entry",
        kind_mod == "simple_module" and paths_mod == ["/ns/part2/sub.py"],
    )

    # 3. Data hiding: _X vs __all__ precedence (LP Ch. 25 unders.py & alls.py)
    unders = {"a": 1, "b": 2, "_c": 3, "_d": 4}
    alls = {"__all__": ["a", "_c"], "a": 1, "b": 2, "_c": 3, "_d": 4}
    check(
        "without __all__, from * skips _X names; with __all__, __all__ overrides _X (exports ['a', '_c'])",
        filter_from_star_exports(unders) == ["a", "b"]
        and filter_from_star_exports(alls) == ["a", "_c"],
    )

    # 4. Module-level __getattr__ and __dir__ hooks (LP Ch. 25 gamod.py)
    gamod = build_dynamic_getattr_module()
    check(
        "gamod.py returns real attr var=2, computes virtual 'test'->'testtest' and 'hack'->'HACK', and customizes dir()",
        gamod.var == 2
        and gamod.test == "testtest"
        and gamod.hack == "HACK"
        and gamod.code == "CODE"
        and dir(gamod) == ["code", "hack", "test", "var"],
    )

    # 5. __import__ vs importlib.import_module on dotted package paths (LP Ch. 25)
    imp_cmp = compare_dunder_import_vs_import_module("email.message")
    check(
        "__import__('email.message') returns 'email' while importlib.import_module('email.message') returns 'email.message'",
        imp_cmp["dunder_import_name"] == "email"
        and imp_cmp["import_module_name"] == "email.message",
    )

    # 6. Module introspection (mydir.py) and transitive reloaders (reloadall2.py vs reloadall3.py) (LP Ch. 25)
    rc = types.ModuleType("rc")
    rc.Z = 3
    rb = types.ModuleType("rb")
    rb.Y = 2
    rb.rc = rc
    ra = types.ModuleType("ra")
    ra.X = 1
    ra.rb = rb
    ra.rc = rc  # diamond / duplicate reference

    rec_order = transitive_reload_recursive(ra)
    stk_order = transitive_reload_stack(ra)
    ns_items = list_module_namespace(ra, include_dunders=False)
    check(
        "recursive and explicit-stack transitive reloaders visit the exact same module set without duplicates",
        rec_order == ["ra", "rb", "rc"]
        and set(rec_order) == set(stk_order)
        and [k for k, _ in ns_items] == ["X", "rb", "rc"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
