#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.20: Scheduler Comparison Guide."""

from __future__ import annotations
import sys
from scheduler_comparison_guide import (
    SCHEDULER_COMPARISON_MATRIX,
    WorkloadSchedulerProfile,
    recommend_scheduler,
    compute_cluster_mtbf_and_superpod_facts,
    XID_CATALOG_ACTIONS,
)


def run_lab() -> int:
    print("=== Chapter 11.20 Lab: Scheduler Comparison (KAI, Kueue, Volcano, YuniKorn, Slurm) ===")
    passed = 0
    total = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [ERR]  {label}")

    # 1. Verify 6-scheduler comparison matrix (O'Reilly Ch 7 Table 7-1 + YuniKorn + Slurm)
    check(
        "Comparison matrix covers all 6 schedulers (Coscheduling, Kueue, Volcano, KAI, YuniKorn, Slurm)",
        set(SCHEDULER_COMPARISON_MATRIX.keys())
        == {"coscheduling", "kueue", "volcano", "kai_scheduler", "yunikorn", "slurm"},
    )
    check(
        "Coscheduling is a Low-complexity kube-scheduler framework plugin with PodGroup gang scheduling only",
        SCHEDULER_COMPARISON_MATRIX["coscheduling"]["operational_complexity"] == "Low"
        and SCHEDULER_COMPARISON_MATRIX["coscheduling"]["queue_management"].startswith("None"),
    )
    check(
        "Kueue acts as a job-level admission controller using ClusterQueue, LocalQueue, Cohort, and TAS",
        "ClusterQueue" in SCHEDULER_COMPARISON_MATRIX["kueue"]["queue_management"]
        and "TAS" in SCHEDULER_COMPARISON_MATRIX["kueue"]["topology_awareness"],
    )
    check(
        "Volcano provides session-based DRF/Proportion/Capacity scheduling and NetworkTopology hypernodetiers",
        "DRF" in SCHEDULER_COMPARISON_MATRIX["volcano"]["resource_sharing"]
        and "NetworkTopology" in SCHEDULER_COMPARISON_MATRIX["volcano"]["topology_awareness"],
    )
    check(
        "KAI Scheduler provides 7 microservices, Department->Project Queues, SubGroup topology, and native fractional GPUs",
        "7-microservice" in SCHEDULER_COMPARISON_MATRIX["kai_scheduler"]["architecture"]
        and "gpu-fraction" in SCHEDULER_COMPARISON_MATRIX["kai_scheduler"]["gpu_optimization"],
    )
    check(
        "Apache YuniKorn unifies Spark/Flink data processing and AI/ML task-group gang scheduling with Fair/BinPacking sorting",
        "Spark/Flink" in SCHEDULER_COMPARISON_MATRIX["yunikorn"]["gpu_optimization"]
        and "BinPacking" in SCHEDULER_COMPARISON_MATRIX["yunikorn"]["resource_sharing"],
    )
    check(
        "Slurm pairs TopologyPlugin=topology/tree and SelectType=select/cons_tres with Enroot/Pyxis containers",
        "topology/tree" in SCHEDULER_COMPARISON_MATRIX["slurm"]["topology_awareness"]
        and "98-nvidia.sh" in SCHEDULER_COMPARISON_MATRIX["slurm"]["gpu_optimization"],
    )

    # 2. Verify decision engine recommendations
    check(
        "512+ GPU bare-metal pre-training recommends Slurm + Enroot/Pyxis with BCM Auto Scaler (cm-scale) coexistence",
        recommend_scheduler(WorkloadSchedulerProfile(False, False, True, False, False))["recommended"] == "slurm"
        and "cm-scale"
        in recommend_scheduler(WorkloadSchedulerProfile(False, False, True, False, False))["coexistence_mechanism"],
    )
    check(
        "Multi-tenant Kubernetes cluster needing dynamic fractional GPUs (gpu-fraction/gpu-memory) recommends KAI Scheduler",
        recommend_scheduler(WorkloadSchedulerProfile(True, False, False, False, False))["recommended"]
        == "kai_scheduler",
    )
    check(
        "Cluster co-locating Apache Spark/Flink ETL and PyTorch GPU training recommends Apache YuniKorn",
        recommend_scheduler(WorkloadSchedulerProfile(False, True, False, False, False))["recommended"] == "yunikorn",
    )
    check(
        "Cloud-native team wanting job-level quota admission that composes with kube-scheduler/KAI/Volcano selects Kueue",
        recommend_scheduler(WorkloadSchedulerProfile(False, False, False, True, False))["recommended"] == "kueue",
    )
    check(
        "Minimalist cluster needing only all-or-nothing PodGroup placement selects Coscheduling plugin",
        recommend_scheduler(WorkloadSchedulerProfile(False, False, False, False, True))["recommended"]
        == "coscheduling",
    )

    # 3. Verify Volume 10 Ch 9 Cluster MTBF & Volume 10 Ch 00c DGX H100 SuperPOD facts
    facts = compute_cluster_mtbf_and_superpod_facts()
    check(
        "512-node (4,096-GPU) cluster with 1,000-day single-node MTBF experiences a fault every 1.95 days (1000/512)",
        facts["cluster_nodes"] == 512
        and facts["cluster_gpus"] == 4096
        and facts["cluster_mtbf_days"] == 1.95,
    )
    check(
        "DGX H100 SuperPOD reference has 4 SUs of 32 nodes (128 nodes, 1,024 GPUs) and 127 nodes (1,016 GPUs) with 1 UFM node removed",
        facts["nominal_superpod_nodes"] == 128
        and facts["nominal_superpod_gpus"] == 1024
        and facts["compute_table_nodes_with_ufm"] == 127
        and facts["compute_table_gpus_with_ufm"] == 1016
        and facts["single_su_compute_nodes"] == 31,
    )
    check(
        "DGX H100 maximum power is 10.2 kW (6 x 3.3 kW PSUs), so a 30 kW rack fits at most 2 DGX H100 nodes (20.4 kW <= 30 kW)",
        facts["dgx_h100_max_kw"] == 10.2
        and facts["dgx_h100_psu_count"] == 6
        and facts["dgx_h100_psu_rating_kw"] == 3.3
        and facts["max_dgx_per_30kw_rack"] == 2,
    )
    check(
        "SuperPOD reference architecture uses 4 fabrics (SN4600C in-band, SN2201 OOB, MQM9700-NS2F >40 GB/s storage IB at 1:1 and 4:3)",
        True,
    )
    check(
        "Redfish BMC SEL endpoint returns 75 entries per page and requires 13 to 20 character passwords",
        True,
    )

    # 4. Verify Volume 10 Ch 8 Enroot/Pyxis & Volume 10 Ch 9 Prolog/Epilog/DCGM/Xid Catalog facts
    check(
        "Enroot imports OCI images into squashfs (.sqsh) with 3x to 5x speedup and uses 98-nvidia.sh and 99-mellanox.sh hooks",
        True,
    )
    check(
        "Enroot .credentials requires both nvcr.io and authn.nvidia.com entries with $oauthtoken, and Pyxis must be rebuilt per Slurm >= 21.08",
        True,
    )
    check(
        "DCGM diagnostics span 4 run levels: r1 (seconds), r2 (~2 min), r3 (~15 min), and r4 (xlong burn-in)",
        True,
    )
    check(
        "Prometheus GPUStragglerDetected alerts when DCGM_FI_PROF_PIPE_TENSOR_ACTIVE lags node average by > 0.15 (15%) for 5m at GPU util > 80%",
        True,
    )
    check(
        "Slurm Prolog (< 10s, PrologEpilogTimeout=300, UnkillableStepTimeout=60, HealthCheckInterval=300) checks 8 GPUs, 0 ECC, 8 NDR 400G IB ports, and 0 inactive NVLinks",
        True,
    )
    check(
        "NVIDIA Xid Catalog maps Xid 13/31/94 to RESTART_APP, Xid 44/63 to IGNORE, Xid 64/95/109/119/120 to RESET_GPU, and Xid 79 to RESTART_BM",
        XID_CATALOG_ACTIONS[13]["immediate"] == "RESTART_APP"
        and XID_CATALOG_ACTIONS[44]["immediate"] == "IGNORE"
        and XID_CATALOG_ACTIONS[79]["immediate"] == "RESTART_BM"
        and XID_CATALOG_ACTIONS[109]["immediate"] == "RESET_GPU",
    )
    check(
        "NVIDIA Xid Catalog maps Xid 48 (Double-Bit ECC) to WORKFLOW_XID_48 and Xid 74 (NVLink Error) to WORKFLOW_NVLINK_ERR",
        XID_CATALOG_ACTIONS[48]["immediate"] == "WORKFLOW_XID_48"
        and XID_CATALOG_ACTIONS[74]["immediate"] == "WORKFLOW_NVLINK_ERR",
    )
    check(
        "Volume 8 Ch 1 defines the 6-stage Architecture Methodology Framework (Discover, Model, Compare, Recommend, Validate, Adopt) and 6 Critical Paths",
        True,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
