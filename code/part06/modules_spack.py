#!/usr/bin/env python3
"""Lmod hierarchy state simulator, Spack spec parser, and Tcl vs Lmod version comparator for Chapter 6.6."""
import re


def simulate_lmod_compiler_swap(
    core_compilers: dict[str, list[str]],
    initial_compiler: str,
    initial_mpi: str,
    target_compiler: str,
) -> dict[str, list[str] | str]:
    """Simulate Lmod dynamic MODULEPATH hierarchy swap (SCL Chapter 21).

    - Loading initial_compiler exposes its MPI list and loads initial_mpi.
    - Unloading initial_compiler marks initial_mpi 'inactive' (removed from PATH/LD_LIBRARY_PATH).
    - Loading target_compiler automatically reloads initial_mpi if available under target_compiler.
    """
    available_under_target = core_compilers.get(target_compiler, [])
    if initial_mpi in available_under_target:
        active_modules = [target_compiler, initial_mpi]
        inactive_modules: list[str] = []
        mpi_status = f"reloaded_for_{target_compiler}"
    else:
        active_modules = [target_compiler]
        inactive_modules = [initial_mpi]
        mpi_status = "inactive"
    return {
        "active_modules": active_modules,
        "inactive_modules": inactive_modules,
        "mpi_status": mpi_status,
    }


def compare_module_versions_tcl_vs_lmod(versions: list[str]) -> dict[str, str]:
    """Compare lexicographical string sorting (classic Tcl Modules 3.2.10) vs numeric version sorting (Lmod).

    SCL Chapter 21 example: ['mkl/4.0', 'mkl/11.0'] -> Tcl picks 'mkl/4.0' ('4' > '1'), Lmod picks 'mkl/11.0' (11 > 4).
    """
    tcl_highest = max(versions)  # Pure ASCII string sort

    def numeric_key(v: str) -> tuple[int, ...]:
        nums = [int(x) for x in re.findall(r"\d+", v)]
        return tuple(nums)

    lmod_highest = max(versions, key=numeric_key)
    return {
        "tcl_string_highest": tcl_highest,
        "lmod_numeric_highest": lmod_highest,
    }


def parse_spack_spec(spec_str: str) -> dict[str, object]:
    """Parse a compact Spack spec string into root package, version, compiler, variants, and dependencies."""
    parts = spec_str.strip().split()
    root = parts[0]
    pkg, ver = (root.split("@", 1) + [""])[:2] if "@" in root else (root, "")
    compiler = ""
    variants_on: list[str] = []
    kv_variants: dict[str, str] = {}
    deps: list[str] = []
    for tok in parts[1:]:
        if tok.startswith("%"):
            compiler = tok[1:]
        elif tok.startswith("^"):
            deps.append(tok[1:])
        elif tok.startswith("+"):
            variants_on.append(tok[1:])
        elif "=" in tok:
            k, v = tok.split("=", 1)
            kv_variants[k] = v
    return {
        "package": pkg,
        "version": ver,
        "compiler": compiler,
        "variants_on": variants_on,
        "kv_variants": kv_variants,
        "dependencies": deps,
    }


if __name__ == "__main__":
    tree = {"gcc/15.1.0": ["openmpi/5.0.7"], "intel/2025.0": ["openmpi/5.0.7"]}
    print("Lmod swap gcc -> intel:", simulate_lmod_compiler_swap(tree, "gcc/15.1.0", "openmpi/5.0.7", "intel/2025.0"))
    print("Tcl vs Lmod mkl sort:", compare_module_versions_tcl_vs_lmod(["mkl/4.0", "mkl/11.0"]))
    print("Spack spec:", parse_spack_spec("petsc@3.21 +cuda %gcc@13.3.0 cuda_arch=90 ^openmpi@5.0.7"))
