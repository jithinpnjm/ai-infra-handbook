#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.23: Autoscaling: HPA, VPA, KEDA and the cluster autoscaler."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autoscaling_hpa_ca_simulator import (
    compute_hpa_desired_replicas,
    evaluate_ca_node_scale_down,
    simulate_overprovisioning_pause_pods,
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
    # 1. Section 2 & PK Ch. 13: HPA tolerance band, scale-up rate cap, and scale-down stabilization window
    # Within 10% tolerance (ratio 1.08 -> stays at 4)
    r_tol = compute_hpa_desired_replicas(current_replicas=4, metric_ratios=[1.08])
    # Spike ratio 5.0 (raw=20), capped by max(4+4=8, 4*2=8) -> 8
    r_up = compute_hpa_desired_replicas(current_replicas=4, metric_ratios=[0.5, 5.0], max_scale_up_percent=100, max_scale_up_pods=4)
    # Drop ratio 0.25 on 8 replicas (raw=2), but stabilization window has recent recommendation of 6 -> holds at 6!
    r_down = compute_hpa_desired_replicas(
        current_replicas=8,
        metric_ratios=[0.25],
        recent_scale_down_recommendations=[5, 6, 4],
    )
    check(
        "compute_hpa_desired_replicas ignores 1.08 ratio within 10% tolerance, caps 5x spike from 4 to 8 replicas, and holds scale-down at window max 6",
        r_tol == 4 and r_up == 8 and r_down == 6,
    )

    # 2. Section 5: Cluster Autoscaler scale-down blockers
    blocked_ok, blockers = evaluate_ca_node_scale_down(
        node_utilization_ratio=0.30,
        unneeded_minutes=15.0,
        pods_on_node=[
            {"name": "scratch-pod", "has_controller": True, "has_local_storage": True, "pdb_disruptions_allowed": 1},
            {"name": "locked-pod", "has_controller": True, "has_local_storage": False, "pdb_disruptions_allowed": 0},
        ],
    )
    can_scale_down, _ = evaluate_ca_node_scale_down(
        node_utilization_ratio=0.30,
        unneeded_minutes=15.0,
        pods_on_node=[
            {"name": "annotated-pod", "has_controller": True, "has_local_storage": True, "safe_to_evict": True, "pdb_disruptions_allowed": 1},
        ],
    )
    check(
        "evaluate_ca_node_scale_down flags unannotated emptyDir and PDB=0 blockers, and permits scale-down when safe_to_evict=True",
        blocked_ok is False and len(blockers) == 2 and can_scale_down is True,
    )

    # 3. Section 5 & PK Ch. 13: Cluster Overprovisioning with negative-priority pause pods
    overprov = simulate_overprovisioning_pause_pods(
        ready_gpu_nodes=4,
        pause_pods_running=2,
        incoming_high_prio_gpu_pods=2,
    )
    check(
        "simulate_overprovisioning_pause_pods schedules 2 burst GPU pods in 0s by preempting 2 pause pods and requests 2 replacement nodes in background",
        overprov["instantly_scheduled_high_prio"] == 2
        and overprov["waiting_for_cold_node"] == 0
        and overprov["ca_background_nodes_requested"] == 2
        and overprov["target_total_nodes"] == 6,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
