#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.21: Terraform loops, conditionals, lifecycle and gotchas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from terraform_loops_lifecycle import (
    evaluate_one_concat_conditional,
    flatten_team_namespaces,
    simulate_count_vs_for_each_removal,
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
    # 1. Section 1, 2 & TUR Ch. 5: Removing "trinity" from ["neo", "trinity", "morpheus"] under count vs for_each
    diff = simulate_count_vs_for_each_removal(["neo", "trinity", "morpheus"], ["neo", "morpheus"])
    check(
        "Removing 'trinity' under count mutates [1] (trinity->morpheus) and destroys [2] (morpheus), whereas for_each only destroys ['trinity']",
        diff["count_actions"] == ["modify/replace [1] (trinity -> morpheus)", "destroy [2] (morpheus)"]
        and diff["for_each_actions"] == ["destroy ['trinity']"],
    )

    # 2. Section 5 & TUR Ch. 5: one(concat(...)) safe conditional output selector
    check(
        "evaluate_one_concat_conditional selects full_arn when True and read_only_arn when False without [0] index errors",
        evaluate_one_concat_conditional(True, "arn:full", "arn:ro") == "arn:full"
        and evaluate_one_concat_conditional(False, "arn:full", "arn:ro") == "arn:ro",
    )

    # 3. Section 9: Flattening nested (team, namespace) maps for for_each
    teams = {
        "nlp": {"gpu_quota": 16, "namespaces": ["nlp-train", "nlp-eval"]},
        "vision": {"gpu_quota": 8, "namespaces": ["vis-train"]},
    }
    flat = flatten_team_namespaces(teams)
    check(
        "flatten_team_namespaces produces 3 stable 'team/ns' keys with propagated gpu_quota",
        list(flat.keys()) == ["nlp/nlp-train", "nlp/nlp-eval", "vision/vis-train"]
        and flat["nlp/nlp-eval"]["quota"] == 16
        and flat["vision/vis-train"]["quota"] == 8,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
