#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.6: Environment modules, Spack and EasyBuild."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modules_spack import (
    compare_module_versions_tcl_vs_lmod,
    parse_spack_spec,
    simulate_lmod_compiler_swap,
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
    # 1. Section 2: Lmod compiler swap inactive-marking and automatic reload (SCL Ch. 21)
    tree = {
        "gcc/15.1.0": ["openmpi/5.0.7"],
        "intel/2025.0": ["openmpi/5.0.7"],
        "clang/18.0": [],
    }
    swap_ok = simulate_lmod_compiler_swap(tree, "gcc/15.1.0", "openmpi/5.0.7", "intel/2025.0")
    swap_inact = simulate_lmod_compiler_swap(tree, "gcc/15.1.0", "openmpi/5.0.7", "clang/18.0")
    check(
        "simulate_lmod_compiler_swap reloads openmpi/5.0.7 under intel/2025.0 and marks it inactive under clang/18.0",
        swap_ok["active_modules"] == ["intel/2025.0", "openmpi/5.0.7"]
        and swap_inact["inactive_modules"] == ["openmpi/5.0.7"]
        and swap_inact["mpi_status"] == "inactive",
    )

    # 2. Section 2: Tcl string version sort ('mkl/4.0' > 'mkl/11.0') vs Lmod numeric version sort ('mkl/11.0' > 'mkl/4.0')
    cmp_res = compare_module_versions_tcl_vs_lmod(["mkl/4.0", "mkl/11.0"])
    check(
        "compare_module_versions_tcl_vs_lmod reproduces SCL Ch. 21 trap: Tcl string sort picks mkl/4.0 while Lmod picks mkl/11.0",
        cmp_res["tcl_string_highest"] == "mkl/4.0" and cmp_res["lmod_numeric_highest"] == "mkl/11.0",
    )

    # 3. Section 3: Spack spec parser (@version, +variant, %compiler, key=val, ^dependency)
    sp = parse_spack_spec("petsc@3.21 +cuda %gcc@13.3.0 cuda_arch=90 ^openmpi@5.0.7")
    check(
        "parse_spack_spec extracts package=petsc, version=3.21, compiler=gcc@13.3.0, +cuda, cuda_arch=90, and ^openmpi@5.0.7",
        sp["package"] == "petsc"
        and sp["version"] == "3.21"
        and sp["compiler"] == "gcc@13.3.0"
        and sp["variants_on"] == ["cuda"]
        and sp["kv_variants"] == {"cuda_arch": "90"}
        and sp["dependencies"] == ["openmpi@5.0.7"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
