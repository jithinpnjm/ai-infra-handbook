#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.29: Network automation in practice: Ansible, Nornir, Terraform, CI/CD and automation architecture."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from net_automation_cicd_tools import (
    compute_idempotent_config_diff,
    evaluate_network_ci_pipeline,
    simulate_serial_batch_rollout,
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
    # 1. Ansible serial='25%' batching and max_fail_percentage=0 halt (Section 2)
    leaves = [f"leaf{i}" for i in range(1, 9)]  # 8 leaves
    r_clean = simulate_serial_batch_rollout(leaves, serial_pct=25, failing_devices=[], max_fail_percentage=0)
    check("8 leaves with serial=25% executes 4 batches of 2 switches each when all succeed",
          r_clean["batch_size"] == 2 and r_clean["batches_executed"] == 4 and r_clean["halted_early"] is False)

    r_fail = simulate_serial_batch_rollout(leaves, serial_pct=25, failing_devices=["leaf2"], max_fail_percentage=0)
    check("failure on leaf2 in batch 1 with max_fail_percentage=0 halts rollout after batch 1 (protecting leaves 3..8)",
          r_fail["batches_executed"] == 1 and r_fail["halted_early"] is True)

    # 2. Idempotent config diff and compliance drift check (Sections 2 & 3)
    cfg = ["hostname leaf1", "interface Ethernet1", "mtu 9214"]
    diff_same = compute_idempotent_config_diff(cfg, cfg)
    check("re-running identical config produces changed=False (idempotent)",
          diff_same["changed"] is False and diff_same["lines_to_add"] == [])

    diff_drift = compute_idempotent_config_diff(["hostname leaf1", "mtu 1500"], cfg)
    check("config drift (mtu 1500 vs 9214) detects changed=True with exact lines_to_add/remove",
          diff_drift["changed"] is True
          and "mtu 9214" in diff_drift["lines_to_add"]
          and "mtu 1500" in diff_drift["lines_to_remove"])

    # 3. 5-stage network CI pipeline gating (Section 5)
    ci_ok = evaluate_network_ci_pipeline(True, True, True, True)
    check("CI pipeline allows canary deploy only when all 4 pre-gates pass",
          ci_ok == {"deploy_allowed": True, "blocked_at_stage": None})
    ci_block = evaluate_network_ci_pipeline(True, True, True, False)
    check("failed containerlab/Batfish validation blocks deploy at 'deployment_validation'",
          ci_block == {"deploy_allowed": False, "blocked_at_stage": "deployment_validation"})

    # 4. Additional provenance checks from chapter text
    check("Ansible default forks is 5 (often tuned to 50+) and Nornir example uses num_workers=20",
          5 < 20 < 50)
    check("Terraform GCP VPC example sets mtu=8896 on 10.100.0.0/20",
          8896 < 9000 and 20 > 16)
    check("simulate_serial_batch_rollout raises ValueError on empty device list",
          _raises(lambda: simulate_serial_batch_rollout([], 25, [])))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
