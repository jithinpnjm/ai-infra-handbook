#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.20: Terraform modules and reusable infrastructure."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from terraform_modules_validator import (
    detect_inline_vs_separate_sg_conflict,
    parse_git_module_source,
    validate_gke_gpu_pool_inputs,
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
    # 1. Section 2 & 5: gke-gpu-pool validation & precondition checks (.tftest.hcl equivalent)
    ok_valid, _ = validate_gke_gpu_pool_inputs(
        {"name": "h100-pool", "gpu_count": 8, "gpu_type": "nvidia-h100-80gb"}
    )
    ok_bad_cnt, errs_cnt = validate_gke_gpu_pool_inputs(
        {"name": "h100-pool", "gpu_count": 3, "gpu_type": "nvidia-h100-80gb"}
    )
    ok_no_type, errs_type = validate_gke_gpu_pool_inputs(
        {"name": "h100-pool", "gpu_count": 8, "gpu_type": None}
    )
    check(
        "gke-gpu-pool accepts valid 8xH100 pool and rejects gpu_count=3 and missing gpu_type when gpu_count>0",
        ok_valid is True
        and ok_bad_cnt is False
        and "gpu_count must be 0, 1, 2, 4 or 8." in errs_cnt
        and ok_no_type is False
        and "gpu_type is required when gpu_count > 0." in errs_type,
    )

    # 2. Section 4 & TUR Ch. 4: Git module `source` double-slash `//` subdir and `?ref=` pin check
    pinned = parse_git_module_source(
        "git::https://git.example.com/platform/terraform-modules.git//gke-gpu-pool?ref=v2.3.1"
    )
    unpinned = parse_git_module_source(
        "github.com/foo/modules//services/webserver-cluster?ref=main"
    )
    check(
        "parse_git_module_source extracts repo, //subdir, and flags ?ref=v2.3.1 as pinned vs ?ref=main as unpinned",
        pinned["subdir"] == "gke-gpu-pool"
        and pinned["ref"] == "v2.3.1"
        and pinned["is_pinned"] is True
        and unpinned["subdir"] == "services/webserver-cluster"
        and unpinned["is_pinned"] is False,
    )

    # 3. TUR Ch. 4 Gotcha #2: Inline vs separate security-group rule conflict
    check(
        "detect_inline_vs_separate_sg_conflict flags conflict when inline ingress and external aws_security_group_rule mix",
        detect_inline_vs_separate_sg_conflict(True, True) is True
        and detect_inline_vs_separate_sg_conflict(False, True) is False,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
