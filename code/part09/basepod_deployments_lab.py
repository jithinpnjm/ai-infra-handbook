#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.10: BasePOD and smaller deployments."""

from __future__ import annotations

import sys

from basepod_deployments import (
    evaluate_six_stage_acceptance,
    select_deployment_archetype,
    select_gpu_sharing_mechanism,
    size_128gpu_training_pod_blueprint,
)


def run_checks() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label} -- {detail}")

    print("=== Chapter 9.10 Lab: BasePOD and Smaller Deployments ===")

    # 1. Three Deployment Archetypes checks (Module 4 Q14 & V21 Ch 2/13)
    d_single = select_deployment_archetype(1)
    check(
        "1-node deployment maps to Single-Node DGX (8 GPUs, internal NVSwitch only)",
        d_single["archetype"] == "Single-Node DGX" and d_single["gpu_count"] == 8,
    )

    d_base4 = select_deployment_archetype(4)
    d_base16 = select_deployment_archetype(16)
    check(
        "4-node (32 GPU) and 16-node (128 GPU) air-cooled pods map to BasePOD / Leaf-Only Pod",
        d_base4["archetype"] == "BasePOD / Leaf-Only Pod"
        and d_base4["gpu_count"] == 32
        and d_base16["archetype"] == "BasePOD / Leaf-Only Pod"
        and d_base16["gpu_count"] == 128,
    )

    d_super = select_deployment_archetype(32)
    d_liq = select_deployment_archetype(8, requires_liquid_cooling=True)
    check(
        "32-node cluster or liquid-cooled deployment maps to SuperPOD (multi-tier Clos + facility CDU)",
        d_super["archetype"] == "SuperPOD" and d_liq["archetype"] == "SuperPOD",
    )

    try:
        select_deployment_archetype(0)
        check("Rejects node_count <= 0", False)
    except ValueError:
        check("Rejects node_count <= 0", True)

    # 2. GPU Sharing & Isolation (MIG vs MPS vs Time-Slicing) checks
    mig_sec = select_gpu_sharing_mechanism(
        multi_tenant_untrusted=True, classified_data=True, need_hardware_fault_isolation=True
    )
    check(
        "Untrusted multi-tenant / classified workload selects MIG (7 slices, hardware memory + fault isolation)",
        mig_sec["mechanism"] == "MIG"
        and mig_sec["max_instances_per_gpu"] == 7
        and mig_sec["hardware_memory_isolation"] is True
        and mig_sec["fault_isolation"] is True
        and mig_sec["dedicated_l2_and_bw"] is True,
    )

    mps_single = select_gpu_sharing_mechanism(
        multi_tenant_untrusted=False,
        classified_data=False,
        need_hardware_fault_isolation=False,
        concurrent_small_kernels_single_tenant=True,
    )
    check(
        "Single-tenant concurrent small kernels selects MPS (spatial sharing, no hardware fault isolation)",
        mps_single["mechanism"] == "MPS"
        and mps_single["hardware_memory_isolation"] is False
        and mps_single["fault_isolation"] is False,
    )

    ts_dev = select_gpu_sharing_mechanism(
        multi_tenant_untrusted=False,
        classified_data=False,
        need_hardware_fault_isolation=False,
        concurrent_small_kernels_single_tenant=False,
    )
    check(
        "Low-priority single-tenant dev notebooks select Time-Slicing",
        ts_dev["mechanism"] == "Time-Slicing" and ts_dev["fault_isolation"] is False,
    )

    # 3. V21 Ch 13 16-Node (128-GPU H100) Training Pod Blueprint checks
    pod128 = size_128gpu_training_pod_blueprint()
    check(
        "V21 Ch13: 16 nodes * 8 H100 == 128 GPUs across 4 racks (40.8 kW/rack, 163.2 kW total IT load)",
        pod128["total_gpus"] == 128
        and pod128["compute_racks"] == 4
        and pod128["rack_power_kw"] == 40.8
        and pod128["total_it_power_kw"] == 163.2,
        f"got {pod128}",
    )
    check(
        "V21 Ch13: Leaf-only rail-optimized NDR fabric uses 8 rail leaves with 16 downlinks each",
        pod128["rail_leaf_switches"] == 8 and pod128["downlinks_per_rail_leaf"] == 16,
    )
    check(
        "V21 Ch13: CAPEX is $4.56M compute + $0.9M infra == $5.46M (~$43K/GPU, ~$43/BF16 TFLOP)",
        pod128["compute_capex_usd"] == 4_560_000
        and pod128["total_capex_usd"] == 5_460_000
        and pod128["cost_per_gpu_usd"] == 42656
        and pod128["cost_per_bf16_tflop_usd"] == 43,
        f"got {pod128}",
    )

    try:
        size_128gpu_training_pod_blueprint(nodes=0)
        check("Rejects nodes <= 0 in pod sizer", False)
    except ValueError:
        check("Rejects nodes <= 0 in pod sizer", True)

    # 4. V21 Lab 01 Multi-Pool Startup Sizing math checks (70B on 100B tokens, 500 QPS inference)
    flops_70b_100b = 6.0 * 70e9 * 100e9
    sustained_flops_128h100_40mfu = 128.0 * 989e12 * 0.40
    days_to_train = round((flops_70b_100b / sustained_flops_128h100_40mfu) / 86400.0, 1)
    check(
        "V21 Lab 01: 70B model on 100B tokens (4.2e22 FLOPs) at 40% MFU on 128 H100s takes 9.6 days",
        flops_70b_100b == 4.2e22 and days_to_train == 9.6,
        f"got days={days_to_train}",
    )
    check(
        "V21 Lab 01: 9 inference nodes (72 GPUs = 36 2-GPU replicas at 15.2 QPS) deliver 547.2 QPS (>500 QPS target)",
        round(36 * 15.2, 1) == 547.2,
    )

    # 5. V21 Ch 13 Six-Stage Commissioning & Acceptance Auditor checks
    all_pass_stages = {
        "breaker_headroom_pct": 25.0,
        "max_inlet_temp_c": 24.0,
        "optics_and_cables_clean": True,
        "all_bmcs_reachable": True,
        "zero_firmware_drift": True,
        "topo_m_matches_fleet": True,
        "nvlink_all_active": True,
        "ibstat_all_active": True,
        "lldp_matches_diagram": True,
        "min_rail_bw_pct_of_line_rate": 94.0,
        "zero_pfc_pause_storms": True,
        "aggregate_seq_bw_mbps_per_gpu": 150.0,
        "mdtest_passed": True,
        "checkpoint_save_restore_timed": True,
        "hpl_linpack_passed": True,
        "clusterkit_passed": True,
        "burn_in_hours": 48,
        "burn_in_node_drops": 0,
        "proxy_workload_passed": True,
        "live_alert_fire_verified": True,
        "cmdb_reconciled": True,
        "live_rollback_executed": True,
        "external_runbooks_and_support_verified": True,
    }
    res_acc = evaluate_six_stage_acceptance(all_pass_stages)
    check(
        "V21 Ch13: Cluster passing all 6 acceptance stages is approved for production handoff",
        res_acc["accepted_for_production"] is True and len(res_acc["failed_stages"]) == 0,
    )

    s1_fail = dict(all_pass_stages, max_inlet_temp_c=34.0)  # Node 7 missing blanking panel example
    check(
        "V21 Ch13 Stage 1 Triage: 34C inlet temp (missing blanking panel recirculation) fails Stage 1 Physical",
        "stage1_physical_acceptance" in evaluate_six_stage_acceptance(s1_fail)["failed_stages"],
    )

    s1_pdu_fail = dict(all_pass_stages, breaker_headroom_pct=15.0)
    check(
        "V21 Ch13 Stage 1: PDU breaker headroom <= 20% fails Stage 1 Physical",
        "stage1_physical_acceptance" in evaluate_six_stage_acceptance(s1_pdu_fail)["failed_stages"],
    )

    s2_fail = dict(all_pass_stages, topo_m_matches_fleet=False)  # Post-RMA slot swap example
    check(
        "V21 Ch13 Stage 2 Triage: Mismatched nvidia-smi topo -m after RMA fails Stage 2 Server",
        "stage2_server_acceptance" in evaluate_six_stage_acceptance(s2_fail)["failed_stages"],
    )

    s2_fw_fail = dict(all_pass_stages, zero_firmware_drift=False)
    check(
        "V21 Ch13 Stage 2: Firmware drift across nodes fails Stage 2 Server",
        "stage2_server_acceptance" in evaluate_six_stage_acceptance(s2_fw_fail)["failed_stages"],
    )

    s3_fail = dict(all_pass_stages, min_rail_bw_pct_of_line_rate=85.0)  # 1 rail 15% slower example
    check(
        "V21 Ch13 Stage 3 Triage: Degraded rail at 85% line rate (<90% threshold) fails Stage 3 Network",
        "stage3_network_acceptance" in evaluate_six_stage_acceptance(s3_fail)["failed_stages"],
    )

    s4_fail = dict(all_pass_stages, aggregate_seq_bw_mbps_per_gpu=60.0)
    check(
        "V21 Ch13 Stage 4 Triage: Concurrent storage read < 100 MB/s/GPU fails Stage 4 Storage",
        "stage4_storage_acceptance" in evaluate_six_stage_acceptance(s4_fail)["failed_stages"],
    )

    s5_xid79 = dict(all_pass_stages, burn_in_hours=48, burn_in_node_drops=1)
    check(
        "V21 Ch13 Stage 5 Triage: Node drop (Xid 79) at hour 48 of burn-in fails Stage 5 Cluster",
        "stage5_cluster_acceptance" in evaluate_six_stage_acceptance(s5_xid79)["failed_stages"],
    )

    s5_short = dict(all_pass_stages, burn_in_hours=4)
    check(
        "V21 Ch13 Stage 5: Burn-in shorter than 24 hours fails Stage 5 Cluster",
        "stage5_cluster_acceptance" in evaluate_six_stage_acceptance(s5_short)["failed_stages"],
    )

    s6_alert = dict(all_pass_stages, live_alert_fire_verified=False)  # DCGM metric name mismatch example
    check(
        "V21 Ch13 Stage 6 Triage: Unverified/silent GPU temp alert fails Stage 6 Operational",
        "stage6_operational_acceptance" in evaluate_six_stage_acceptance(s6_alert)["failed_stages"],
    )

    s6_rollback = dict(all_pass_stages, live_rollback_executed=False)
    check(
        "V21 Ch13 Stage 6: Paper-only rollback (not executed live) fails Stage 6 Operational",
        "stage6_operational_acceptance" in evaluate_six_stage_acceptance(s6_rollback)["failed_stages"],
    )

    s3_pfc = dict(all_pass_stages, zero_pfc_pause_storms=False)
    check(
        "V21 Ch13 Stage 3: PFC pause storm during all-to-all test fails Stage 3 Network",
        "stage3_network_acceptance" in evaluate_six_stage_acceptance(s3_pfc)["failed_stages"],
    )

    s4_md = dict(all_pass_stages, mdtest_passed=False)
    check(
        "V21 Ch13 Stage 4: Failed mdtest small-file metadata rate fails Stage 4 Storage",
        "stage4_storage_acceptance" in evaluate_six_stage_acceptance(s4_md)["failed_stages"],
    )

    s5_ck = dict(all_pass_stages, clusterkit_passed=False)
    check(
        "V21 Ch13 Stage 5: Failed ClusterKit multi-node sweep fails Stage 5 Cluster",
        "stage5_cluster_acceptance" in evaluate_six_stage_acceptance(s5_ck)["failed_stages"],
    )

    s6_cmdb = dict(all_pass_stages, cmdb_reconciled=False)
    check(
        "V21 Ch13 Stage 6: Unreconciled CMDB serials/rack slots fails Stage 6 Operational",
        "stage6_operational_acceptance" in evaluate_six_stage_acceptance(s6_cmdb)["failed_stages"],
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
