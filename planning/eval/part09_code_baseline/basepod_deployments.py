#!/usr/bin/env python3
"""Part 9, Chapter 9.10: BasePOD and smaller deployments model.

Models the three deployment archetypes (Single DGX Node vs BasePOD/Single-Pod vs
SuperPOD), GPU sharing isolation modes (MIG vs MPS vs Time-Slicing), the 16-node
(128-GPU) leaf-only pod blueprint, the $20M multi-pool startup design from
Volume 21 Lab 01, and the Six-Stage Commissioning & Acceptance Auditor.

Sources:
- nvidia-devops Volume 21 Chapters 2 and 13 & Lab 01
- nvidia-devops-core-interview Module 4 Q14 ("DGX vs BasePOD vs SuperPOD Onboarding")
- nvidia-devops-legacy-v09 ("01 - Hardware & Ecosystem Gauntlet", "03 - Security")
"""

from __future__ import annotations

from typing import Dict, List


def select_deployment_archetype(node_count: int, requires_liquid_cooling: bool = False) -> Dict[str, object]:
    """Classify a deployment into Single-Node DGX, BasePOD (Leaf-Only Pod), or SuperPOD.

    Sources:
    - nvidia-devops-core-interview Module 4 Q14 (1 node vs 2-8 node BasePOD vs 32+ node SuperPOD)
    - nvidia-devops Volume 21 Chapter 2 Part 3.1 & Chapter 13 (8-16 node leaf-only pod = 64-128 GPUs)
    My inference: Treats 2..16 nodes (16..128 GPUs) without liquid cooling as the practical
    BasePOD / leaf-only single-pod range before transitioning to a multi-tier SuperPOD.
    """
    if node_count <= 0:
        raise ValueError("node_count must be >= 1.")

    if node_count == 1 and not requires_liquid_cooling:
        return {
            "archetype": "Single-Node DGX",
            "gpu_count": 8,
            "network_topology": "Internal NVSwitch only (no external compute fabric required)",
            "storage_architecture": "Internal 30 TB NVMe (/raid) + enterprise NAS",
            "primary_focus": "DGX OS, NGC containers, Jupyter, and MIG/MPS single-node utilization",
        }

    if 2 <= node_count <= 16 and not requires_liquid_cooling:
        return {
            "archetype": "BasePOD / Leaf-Only Pod",
            "gpu_count": node_count * 8,
            "network_topology": "Single-tier (Leaf-Only) Rail-Optimized IB NDR or RoCEv2 (1 hop intra-rail, 0 spines)",
            "storage_architecture": "Centralized certified flash storage (WEKA, VAST, NetApp) over 100-400G RoCE/IB",
            "primary_focus": "3-fabric separation (Compute/Storage/Mgmt), BCM golden images, Slurm/K8s + GPU/Network Operator",
        }

    return {
        "archetype": "SuperPOD",
        "gpu_count": node_count * 8,
        "network_topology": "Multi-tier non-blocking Fat-Tree/Clos (Leaf + Spine) with UFM Enterprise & NMX-M",
        "storage_architecture": "Dedicated High-Performance Storage (90-280 GB/s/SU) + NFS User Storage",
        "primary_focus": "Facility-level power/CDU liquid cooling, rail alignment, UFM telemetry, Mission Control autonomous recovery",
    }


def select_gpu_sharing_mechanism(
    multi_tenant_untrusted: bool,
    classified_data: bool,
    need_hardware_fault_isolation: bool,
    concurrent_small_kernels_single_tenant: bool = False,
) -> Dict[str, object]:
    """Recommend MIG, MPS, or Time-Slicing for smaller/shared GPU deployments.

    Sources:
    - nvidia-devops-legacy-v09 ("01 - Hardware & Ecosystem Gauntlet", Module 1.1)
    - nvidia-devops-legacy-v09 ("03 - Security Governance Masterclass")
    Rules:
    - MIG (Multi-Instance GPU): physical hardware partitioning (up to 7 instances on A100/H100/B200)
      with dedicated SMs, L2 cache, and memory controllers. Mandatory for untrusted multi-tenancy,
      classified data, or strict QoS / hardware fault isolation.
    - MPS (Multi-Process Service): spatial sharing of SMs for a SINGLE tenant running multiple small
      concurrent kernels; shares L2 cache and VRAM with ZERO hardware fault isolation.
    - Time-Slicing: temporal context switching on shared VRAM; highest latency jitter and zero
      memory isolation (only for low-priority single-tenant dev notebooks).
    """
    if multi_tenant_untrusted or classified_data or need_hardware_fault_isolation:
        return {
            "mechanism": "MIG",
            "max_instances_per_gpu": 7,
            "hardware_memory_isolation": True,
            "fault_isolation": True,
            "dedicated_l2_and_bw": True,
        }
    if concurrent_small_kernels_single_tenant:
        return {
            "mechanism": "MPS",
            "max_instances_per_gpu": 48,
            "hardware_memory_isolation": False,
            "fault_isolation": False,
            "dedicated_l2_and_bw": False,
        }
    return {
        "mechanism": "Time-Slicing",
        "max_instances_per_gpu": 16,
        "hardware_memory_isolation": False,
        "fault_isolation": False,
        "dedicated_l2_and_bw": False,
    }


def size_128gpu_training_pod_blueprint(
    nodes: int = 16,
    gpus_per_node: int = 8,
    node_power_kw: float = 10.2,
    nodes_per_rack: int = 4,
    node_unit_cost_usd: int = 285_000,
    ib_fabric_cost_usd: int = 400_000,
    storage_cost_usd: int = 200_000,
    racks_pdus_cooling_cost_usd: int = 200_000,
    install_cost_usd: int = 100_000,
) -> Dict[str, object]:
    """Reproduce the Volume 21 Chapter 13 16-Node (128-GPU H100) Training Pod Blueprint.

    Source: nvidia-devops Volume 21 Chapter 13 ("Cluster Specification" & "Hardware Cost Breakdown"):
    - 16 nodes * 8 H100 SXM5 = 128 GPUs (128 * 989 = 126,592 BF16 TFLOPS).
    - 8 NDR leaf switches (1 per rail), 16 downlinks per switch.
    - 16 * 10.2 kW = 163.2 kW (~163 kW) IT load across 4 racks (4 nodes/rack = 40.8 kW/rack).
    - CAPEX: 16 * $285K ($4.56M) + $400K IB + $200K storage + $200K racks/cooling + $100K install
      = $5,460,000 (~$5.46M / ~$5.5M), or ~$42,656 (~$43K) per GPU and ~$43.13 (~$43) per BF16 TFLOP.
    """
    if nodes <= 0 or gpus_per_node <= 0 or nodes_per_rack <= 0:
        raise ValueError("Node and rack counts must be positive.")

    total_gpus = nodes * gpus_per_node
    total_bf16_tflops = total_gpus * 989.0
    compute_racks = (nodes + nodes_per_rack - 1) // nodes_per_rack
    rack_power_kw = round(nodes_per_rack * node_power_kw, 1)
    total_it_power_kw = round(nodes * node_power_kw, 1)

    compute_capex = nodes * node_unit_cost_usd
    total_capex = (
        compute_capex
        + ib_fabric_cost_usd
        + storage_cost_usd
        + racks_pdus_cooling_cost_usd
        + install_cost_usd
    )
    cost_per_gpu = round(total_capex / float(total_gpus))
    cost_per_bf16_tflop = round(total_capex / total_bf16_tflops)

    return {
        "nodes": nodes,
        "total_gpus": total_gpus,
        "compute_racks": compute_racks,
        "rack_power_kw": rack_power_kw,
        "total_it_power_kw": total_it_power_kw,
        "rail_leaf_switches": 8,
        "downlinks_per_rail_leaf": nodes,
        "compute_capex_usd": compute_capex,
        "total_capex_usd": total_capex,
        "cost_per_gpu_usd": cost_per_gpu,
        "cost_per_bf16_tflop_usd": cost_per_bf16_tflop,
    }


def evaluate_six_stage_acceptance(stages: Dict[str, object]) -> Dict[str, object]:
    """Validate the Volume 21 Chapter 13 Six-Stage AI Factory Commissioning & Acceptance Gate.

    Source: nvidia-devops Volume 21 Chapter 13 ("AI Factory Commissioning and Acceptance", lines 152-360):
    1. Stage 1 Physical: breaker_headroom_pct > 20.0, max_inlet_temp_c < 27.0, optics_clean, bmc_reachable.
    2. Stage 2 Server: zero_firmware_drift, topo_m_matches_fleet, nvlink_all_active, ibstat_all_active.
    3. Stage 3 Network: lldp_matches_diagram, per_rail_bw_pct_of_line_rate >= 90.0, zero_pfc_pause_storms.
    4. Stage 4 Storage: aggregate_seq_bw_mbps_per_gpu >= 100.0, mdtest_passed, checkpoint_save_restore_timed.
    5. Stage 5 Cluster: hpl_linpack_passed, clusterkit_passed, burn_in_hours >= 24 and burn_in_node_drops == 0,
       proxy_workload_passed.
    6. Stage 6 Operational: live_alert_fire_verified, cmdb_reconciled, live_rollback_executed,
       external_runbooks_and_support_verified.
    """
    failed_stages: List[str] = []

    # Stage 1: Physical Acceptance
    if (
        float(stages.get("breaker_headroom_pct", 0.0)) <= 20.0
        or float(stages.get("max_inlet_temp_c", 99.0)) >= 27.0
        or not bool(stages.get("optics_and_cables_clean", False))
        or not bool(stages.get("all_bmcs_reachable", False))
    ):
        failed_stages.append("stage1_physical_acceptance")

    # Stage 2: Server Acceptance
    if (
        not bool(stages.get("zero_firmware_drift", False))
        or not bool(stages.get("topo_m_matches_fleet", False))
        or not bool(stages.get("nvlink_all_active", False))
        or not bool(stages.get("ibstat_all_active", False))
    ):
        failed_stages.append("stage2_server_acceptance")

    # Stage 3: Network Acceptance
    if (
        not bool(stages.get("lldp_matches_diagram", False))
        or float(stages.get("min_rail_bw_pct_of_line_rate", 0.0)) < 90.0
        or not bool(stages.get("zero_pfc_pause_storms", False))
    ):
        failed_stages.append("stage3_network_acceptance")

    # Stage 4: Storage Acceptance
    if (
        float(stages.get("aggregate_seq_bw_mbps_per_gpu", 0.0)) < 100.0
        or not bool(stages.get("mdtest_passed", False))
        or not bool(stages.get("checkpoint_save_restore_timed", False))
    ):
        failed_stages.append("stage4_storage_acceptance")

    # Stage 5: Cluster Acceptance
    if (
        not bool(stages.get("hpl_linpack_passed", False))
        or not bool(stages.get("clusterkit_passed", False))
        or int(stages.get("burn_in_hours", 0)) < 24
        or int(stages.get("burn_in_node_drops", 1)) > 0
        or not bool(stages.get("proxy_workload_passed", False))
    ):
        failed_stages.append("stage5_cluster_acceptance")

    # Stage 6: Operational Acceptance
    if (
        not bool(stages.get("live_alert_fire_verified", False))
        or not bool(stages.get("cmdb_reconciled", False))
        or not bool(stages.get("live_rollback_executed", False))
        or not bool(stages.get("external_runbooks_and_support_verified", False))
    ):
        failed_stages.append("stage6_operational_acceptance")

    return {
        "accepted_for_production": len(failed_stages) == 0,
        "failed_stages": failed_stages,
    }
