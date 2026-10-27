"""Chapter 2.29 model: Ansible serial batch and max_fail_percentage rollout
simulator, idempotent configuration diff and compliance drift detector, and
5-stage network CI/CD pipeline gate evaluator.

Sources modeled:
- Christian Adell, Scott S. Lowe, Jason Edelman, and Matt Oswalt, Network
  Programmability and Automation, 2nd ed. (network-programmability-and-automation-2nd-edition,
  NPA), Chapters 12, 13, and 14 (Ansible, Nornir, Terraform, 5 CI pipeline
  components, 6 network automation architecture components, Source of Truth).
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 26 ("The Case for Network Automation": automation and complexity,
  on-box automation, controllers, from automation to auto) and Chapter 27
  ("Virtualized Network Functions": VNFs, service chaining, intent-based
  networking, DPDK/SR-IOV/DPU trade-offs).
"""
from typing import Dict, List


def simulate_serial_batch_rollout(
    devices: List[str],
    serial_pct: int,
    failing_devices: List[str],
    max_fail_percentage: int = 0,
) -> Dict[str, object]:
    """Simulate an Ansible rolling playbook execution with serial='25%' and max_fail_percentage."""
    if not devices or not (1 <= serial_pct <= 100) or not (0 <= max_fail_percentage <= 100):
        raise ValueError("Invalid rollout parameters")
    batch_size = max(1, (len(devices) * serial_pct) // 100)
    batches: List[List[str]] = [devices[i : i + batch_size] for i in range(0, len(devices), batch_size)]
    completed_batches: List[List[str]] = []
    halted = False
    for b in batches:
        failed_in_batch = [d for d in b if d in failing_devices]
        fail_pct = (100.0 * len(failed_in_batch)) / float(len(b))
        completed_batches.append(b)
        if fail_pct > max_fail_percentage:
            halted = True
            break
    return {
        "batch_size": batch_size,
        "batches_executed": len(completed_batches),
        "total_batches": len(batches),
        "halted_early": halted,
    }


def compute_idempotent_config_diff(
    running_lines: List[str],
    intended_lines: List[str],
) -> Dict[str, object]:
    """Compute idempotent delta between running and intended config lines (changed=False if identical)."""
    run_set = [line.strip() for line in running_lines if line.strip()]
    int_set = [line.strip() for line in intended_lines if line.strip()]
    to_add = [line for line in int_set if line not in run_set]
    to_remove = [line for line in run_set if line not in int_set]
    changed = len(to_add) > 0 or len(to_remove) > 0
    return {
        "changed": changed,
        "lines_to_add": to_add,
        "lines_to_remove": to_remove,
    }


def evaluate_network_ci_pipeline(
    pr_approved: bool,
    lint_and_schema_ok: bool,
    emulation_deployed_ok: bool,
    validation_assertions_ok: bool,
) -> Dict[str, object]:
    """Evaluate the 5-stage network CI pipeline before allowing canary/production deployment."""
    stages = [
        ("peer_review", pr_approved),
        ("build_lint_schema", lint_and_schema_ok),
        ("emulation_lab", emulation_deployed_ok),
        ("deployment_validation", validation_assertions_ok),
    ]
    for stage_name, ok in stages:
        if not ok:
            return {"deploy_allowed": False, "blocked_at_stage": stage_name}
    return {"deploy_allowed": True, "blocked_at_stage": None}
