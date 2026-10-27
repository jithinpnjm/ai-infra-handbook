#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.11: Ansible roles and collections."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_roles_collections import (
    resolve_role_dependency_order,
    role_file_search_candidates,
    validate_role_argument_spec,
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
    # 1. Section 1 meta/argument_specs.yml validation (defaults, choices, type checks)
    spec = {
        "gpu_driver_branch": {"type": "str", "default": "550", "choices": ["535", "550", "555"]},
        "gpu_driver_persistence_mode": {"type": "bool", "default": True},
        "gpu_driver_validate_gpu_count": {"type": "int", "default": 0},
    }
    ok1, errs1, eff1 = validate_role_argument_spec(spec, {"gpu_driver_validate_gpu_count": 8})
    ok2, errs2, _ = validate_role_argument_spec(spec, {"gpu_driver_branch": "470", "gpu_driver_validate_gpu_count": True})
    check(
        "argument_specs applies default branch='550', accepts count=8, and rejects invalid branch '470' and bool-for-int",
        ok1 is True
        and eff1 == {
            "gpu_driver_branch": "550",
            "gpu_driver_persistence_mode": True,
            "gpu_driver_validate_gpu_count": 8,
        }
        and ok2 is False
        and len(errs2) == 2,
    )

    # 2. Section 1 & AUR Ch. 9 Role dependency execution order & deduplication
    deps = {
        "gpu_driver": ["common_base"],
        "dcgm": ["common_base", "gpu_driver"],
    }
    order_dedup = resolve_role_dependency_order(["gpu_driver", "dcgm"], deps)
    order_dups = resolve_role_dependency_order(["gpu_driver", "dcgm"], deps, allow_duplicates={"common_base": True})
    check(
        "role dependencies run before dependents and deduplicate common_base (['common_base', 'gpu_driver', 'dcgm']) unless allow_duplicates",
        order_dedup == ["common_base", "gpu_driver", "dcgm"]
        and order_dups.count("common_base") == 2,
    )

    # 3. AUR Ch. 9 Role relative file search order
    cands = role_file_search_candidates("database", "pg_hba.conf", "files")
    check(
        "role file lookup checks ./roles/database/files/pg_hba.conf first before falling back to playbook ./files/pg_hba.conf",
        cands[0] == "./roles/database/files/pg_hba.conf" and cands[-2] == "./files/pg_hba.conf",
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
