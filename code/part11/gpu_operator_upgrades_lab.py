"""Chapter 11.5 Lab — GPU Operator installation, configuration and upgrades.

Run with:
    python3 code/part11/gpu_operator_upgrades_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gpu_operator_upgrades import (
    PoolAcceptanceEvidence,
    UpgradeAndRollbackState,
    diagnose_installation_or_upgrade_symptom,
    evaluate_pool_acceptance,
    evaluate_upgrade_or_rollback_gate,
    plan_canary_and_progressive_batches,
)


def _check(condition: bool, label: str, passed: list[str], failed: list[str]) -> None:
    if condition:
        passed.append(label)
        print(f"  [PASS] {label}")
    else:
        failed.append(label)
        print(f"  [ERR]  {label}")


def main() -> int:
    passed: list[str] = []
    failed: list[str] = []

    print("=== Chapter 11.5 Lab: GPU Operator Installation, Configuration & Upgrades ===")

    # 1. 7-Criterion Production Installation Acceptance (V10 Ch 10)
    # Case A: Helm says deployed on 6-node canary, but clusterpolicy is notReady (gpu-node-04 driver CrashLoopBackOff)
    ev_canary_driver_broken = PoolAcceptanceEvidence(
        helm_status="deployed",
        cluster_policy_state="notReady",
        total_canary_nodes=6,
        driver_ready_nodes=5,
        capacity_gpus=8,
        allocatable_gpus=0,
        labels_and_taints_verified=True,
        validation_pod_marker="",
        validation_pod_uuid="",
        dcgm_metric_series_count=0,
        dcgm_metric_uuid="",
        drain_reboot_return_passed=False,
    )
    res_broken = evaluate_pool_acceptance(ev_canary_driver_broken)
    _check(
        res_broken["helm_deployed"] is True and res_broken["pool_accepted"] is False,
        "Helm status='deployed' with clusterpolicy='notReady' (5/6 nodes ready) is rejected by acceptance gate",
        passed,
        failed,
    )
    _check(
        "1_driver_and_operands_ready" in res_broken["failed_gates"]
        and "3_allocatable_matches_capacity" in res_broken["failed_gates"],
        "Acceptance gate flags 1_driver_and_operands_ready and 3_allocatable_matches_capacity on gpu-node-04",
        passed,
        failed,
    )

    # Case B: All 6 canary nodes pass driver, allocatable=8, CUDA_VALIDATED, and UUID-matched DCGM (97%)
    ev_healthy = PoolAcceptanceEvidence(
        helm_status="deployed",
        cluster_policy_state="ready",
        total_canary_nodes=6,
        driver_ready_nodes=6,
        capacity_gpus=8,
        allocatable_gpus=8,
        labels_and_taints_verified=True,
        validation_pod_marker="CUDA_VALIDATED",
        validation_pod_uuid="GPU-3a91",
        dcgm_metric_series_count=8,
        dcgm_metric_uuid="GPU-3a91",
        drain_reboot_return_passed=True,
    )
    res_healthy = evaluate_pool_acceptance(ev_healthy)
    _check(
        res_healthy["pool_accepted"] is True and len(res_healthy["failed_gates"]) == 0,
        "All 7 acceptance criteria pass when 6/6 nodes, 8/8 allocatable, CUDA_VALIDATED, and UUID GPU-3a91 match",
        passed,
        failed,
    )

    # Case C: UUID mismatch between workload Pod and DCGM Exporter series
    ev_uuid_mismatch = PoolAcceptanceEvidence(
        helm_status="deployed",
        cluster_policy_state="ready",
        total_canary_nodes=6,
        driver_ready_nodes=6,
        capacity_gpus=8,
        allocatable_gpus=8,
        labels_and_taints_verified=True,
        validation_pod_marker="CUDA_VALIDATED",
        validation_pod_uuid="GPU-3a91",
        dcgm_metric_series_count=8,
        dcgm_metric_uuid="GPU-9999",
        drain_reboot_return_passed=True,
    )
    res_uuid_mismatch = evaluate_pool_acceptance(ev_uuid_mismatch)
    _check(
        res_uuid_mismatch["pool_accepted"] is False
        and res_uuid_mismatch["failed_gates"] == ["6_dcgm_telemetry_uuid_matched"],
        "Acceptance gate rejects pool when DCGM metric UUID does not match validation Pod UUID",
        passed,
        failed,
    )

    # Case D: Missing DCGM metrics (0 series on port 9400) while workload passes
    ev_no_metrics = PoolAcceptanceEvidence(
        helm_status="deployed",
        cluster_policy_state="ready",
        total_canary_nodes=6,
        driver_ready_nodes=6,
        capacity_gpus=8,
        allocatable_gpus=8,
        labels_and_taints_verified=True,
        validation_pod_marker="CUDA_VALIDATED",
        validation_pod_uuid="GPU-3a91",
        dcgm_metric_series_count=0,
        dcgm_metric_uuid="GPU-3a91",
        drain_reboot_return_passed=True,
    )
    res_no_metrics = evaluate_pool_acceptance(ev_no_metrics)
    _check(
        res_no_metrics["pool_accepted"] is False
        and "6_dcgm_telemetry_uuid_matched" in res_no_metrics["failed_gates"],
        "Acceptance gate rejects pool when dcgm-exporter returns 0 DCGM_FI_DEV_GPU_UTIL series",
        passed,
        failed,
    )

    # 2. 120-Node Fleet Canary & Progressive Batch Sizing (V10 Ch 11)
    plan = plan_canary_and_progressive_batches(
        total_nodes=120,
        hardware_batches=4,
        canary_nodes_per_hw_batch=2,
        first_rollout_pct=10.0,
        gpus_per_node=8,
    )
    _check(
        plan["nodes_per_hw_batch"] == 30,
        "120-node fleet across 4 hardware procurement batches has 30 nodes per batch",
        passed,
        failed,
    )
    _check(
        plan["canary_nodes"] == 8 and plan["canary_pct_rounded"] == 7,
        "2 canary nodes per hardware batch = 8 canary nodes (~7% of 120-node fleet)",
        passed,
        failed,
    )
    _check(
        plan["wave_schedule_nodes"] == [8, 12, 24, 76]
        and sum(plan["wave_schedule_nodes"]) == 120,
        "Progressive rollout waves are 8 (canary) -> 12 (10%) -> 24 (doubled) -> 76 (remaining) = 120 nodes",
        passed,
        failed,
    )
    _check(
        plan["batch1_remaining_serving_pct"] == 90.0,
        "First post-canary batch of 12 nodes leaves 90.0% of fleet capacity serving traffic",
        passed,
        failed,
    )
    _check(
        plan["total_fleet_gpus"] == 960
        and plan["batch2_gpus_at_risk"] == 192
        and plan["batch2_blast_radius_pct"] == 20.0,
        "Fault caught at the 24-node batch affects 24 x 8 = 192 GPUs out of 960 total GPUs (20.0% blast radius)",
        passed,
        failed,
    )

    # 3. Controlled Upgrade & Rollback `Recheck` Gate (Lab 04: 24.6.0 rev 1 -> 24.9.1 rev 2)
    up_ok = evaluate_upgrade_or_rollback_gate(
        UpgradeAndRollbackState(
            prior_revision=1,
            prior_chart="gpu-operator-24.6.0",
            target_revision=2,
            target_chart="gpu-operator-24.9.1",
            baseline_allocatable=8,
            post_upgrade_allocatable=8,
            post_upgrade_workload_ok=True,
            post_upgrade_dcgm_ok=True,
            new_xid_or_kernel_errors=False,
        )
    )
    _check(
        up_ok["upgrade_gate"] == "pass"
        and up_ok["action"] == "uncordon_canary_and_proceed_to_staged_rollout",
        "Upgrade from 24.6.0 (rev 1) to 24.9.1 (rev 2) passes gate when allocatable=8, workload OK, DCGM OK, 0 Xids",
        passed,
        failed,
    )

    up_xid_fail = evaluate_upgrade_or_rollback_gate(
        UpgradeAndRollbackState(
            baseline_allocatable=8,
            post_upgrade_allocatable=8,
            post_upgrade_workload_ok=True,
            post_upgrade_dcgm_ok=True,
            new_xid_or_kernel_errors=True,
            helm_rollback_succeeded=False,
        )
    )
    _check(
        up_xid_fail["upgrade_gate"] == "fail"
        and up_xid_fail["action"] == "trigger_helm_rollback_to_revision_1",
        "New Xid or kernel errors trigger upgrade_gate='fail' even when validation Pod succeeded",
        passed,
        failed,
    )

    # Lab 04 Step 16: `helm rollback gpu-operator 1` succeeds, but `allocatable` stays 0!
    rb_diverged = evaluate_upgrade_or_rollback_gate(
        UpgradeAndRollbackState(
            baseline_allocatable=8,
            post_upgrade_allocatable=0,
            post_upgrade_workload_ok=False,
            helm_rollback_succeeded=True,
            post_rollback_allocatable=0,
            post_rollback_workload_ok=False,
        )
    )
    _check(
        rb_diverged["rollback_recheck_gate"] == "fail_host_state_diverged"
        and "keep_node_cordoned" in str(rb_diverged["action"]),
        "When helm rollback 1 succeeds but allocatable stays 0, Recheck catches host-state divergence and keeps node cordoned",
        passed,
        failed,
    )

    rb_clean = evaluate_upgrade_or_rollback_gate(
        UpgradeAndRollbackState(
            baseline_allocatable=8,
            post_upgrade_allocatable=0,
            post_upgrade_workload_ok=False,
            helm_rollback_succeeded=True,
            post_rollback_allocatable=8,
            post_rollback_workload_ok=True,
        )
    )
    _check(
        rb_clean["rollback_recheck_gate"] == "pass",
        "When rollback restores allocatable=8 and validation workload passes, Recheck gate passes",
        passed,
        failed,
    )

    # 4. Troubleshooting Classifier (V10 Ch 10 & Ch 11)
    d_mok = diagnose_installation_or_upgrade_symptom(
        "modprobe: ERROR: could not insert 'nvidia': Key was rejected by service",
        "",
        8,
        8,
    )
    d_start = diagnose_installation_or_upgrade_symptom(
        "",
        "OCI runtime create failed: (open /run/nvidia/driver/dev/nvidia0: no such file or directory): unknown",
        8,
        8,
    )
    d_alloc = diagnose_installation_or_upgrade_symptom("", "", 0, 8)
    d_dcgm = diagnose_installation_or_upgrade_symptom("", "", 8, 0)
    d_ok = diagnose_installation_or_upgrade_symptom("", "", 8, 8)

    _check(
        d_mok["boundary"] == "secure_boot_mok_signing",
        "Classifier routes 'Key was rejected by service' on gpu-node-04 to secure_boot_mok_signing",
        passed,
        failed,
    )
    _check(
        d_start["boundary"] == "pod_start_runtime_injection",
        "Classifier routes missing /run/nvidia/driver/dev/nvidia0 OCI error on gpu-node-07 to pod_start_runtime_injection",
        passed,
        failed,
    )
    _check(
        d_alloc["boundary"] == "device_plugin_or_kubelet_registration",
        "Classifier routes allocatable=0 (gpu-node-11 vs gpu-node-12=8) to device_plugin_or_kubelet_registration",
        passed,
        failed,
    )
    _check(
        d_dcgm["boundary"] == "observability_dcgm_scrape_path",
        "Classifier routes 0 DCGM_FI_DEV_GPU_UTIL series on port 9400 to observability_dcgm_scrape_path",
        passed,
        failed,
    )
    _check(
        d_ok["boundary"] == "healthy",
        "Classifier reports healthy when driver, runtime, allocatable=8, and DCGM series>0 all pass",
        passed,
        failed,
    )

    # 5. Additional verification checks on Lab 04 drain & version parameters
    _check(
        UpgradeAndRollbackState().prior_chart == "gpu-operator-24.6.0"
        and UpgradeAndRollbackState().target_chart == "gpu-operator-24.9.1",
        "Lab 04 revision history tracks gpu-operator-24.6.0 (rev 1) -> gpu-operator-24.9.1 (rev 2)",
        passed,
        failed,
    )
    _check(
        len(res_healthy["criteria"]) == 7,
        "Pool acceptance contract evaluates all 7 criteria independently",
        passed,
        failed,
    )
    _check(
        plan["canary_nodes"] * 8 == 64,
        "8-node canary pool across 4 hardware batches tests 64 GPUs before Batch 1",
        passed,
        failed,
    )
    _check(
        plan["wave_schedule_nodes"][1] * 8 == 96,
        "12-node Batch 1 (10% of 120-node fleet) tests 96 GPUs",
        passed,
        failed,
    )
    _check(
        plan["wave_schedule_nodes"][3] * 8 == 608,
        "Final 76-node wave covers the remaining 608 GPUs after 3 clean observation windows",
        passed,
        failed,
    )
    _check(
        64 + 96 + 192 + 608 == 960,
        "Sum of GPUs across waves (64 + 96 + 192 + 608) equals total fleet capacity of 960 GPUs",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
