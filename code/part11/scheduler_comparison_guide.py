#!/usr/bin/env python3
"""Chapter 11.20 model: Scheduler Comparison Guide (KAI, Kueue, Volcano, YuniKorn, Coscheduling & Slurm).

Models:
1. O'Reilly Generative AI on Kubernetes Chapter 7 Table 7-1 + Apache YuniKorn + Slurm
   comparison matrix across 9 architectural dimensions.
2. Workload-to-Scheduler Decision Engine (evaluating GPU fractional sharing, Spark/Flink
   co-location, bare-metal multi-hundred-node MPI/NCCL training, and cloud-native
   admission queueing).
3. Volume 10 Chapter 9 Cluster MTBF & 3-Tier Health Gate Calculator (512 nodes / 4,096 GPUs
   with 1,000-day single-node MTBF -> 1.95 days cluster MTBF; NVIDIA Xid Catalog buckets).
4. Volume 10 Chapter 00c DGX H100 SuperPOD Reference Sizing (4 SUs = 128 nodes / 1,024 GPUs
   vs 127 nodes / 1,016 GPUs with 1 UFM node; 31 vs 32 nodes per SU; 10.2 kW max per DGX H100
   with 6x 3.3 kW PSUs; BCM Auto Scaler cm-scale Slurm/Kubernetes node repurposing).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


SCHEDULER_COMPARISON_MATRIX: Dict[str, Dict[str, str]] = {
    "coscheduling": {
        "architecture": "kube-scheduler framework plugin",
        "gang_scheduling": "PodGroup CRD (all-or-nothing pod placement)",
        "queue_management": "None (relies on external queue or PriorityClass)",
        "resource_sharing": "None",
        "topology_awareness": "None (uses default NodeResourcesFit / TopologyManager)",
        "gpu_optimization": "Integer extended resources only (nvidia.com/gpu)",
        "operational_complexity": "Low",
    },
    "kueue": {
        "architecture": "Job-level admission controller (delegates pod binding to kube-scheduler or secondary scheduler)",
        "gang_scheduling": "All-or-nothing job-level Workload admission via suspend flag",
        "queue_management": "ClusterQueue, LocalQueue, Cohort borrowing & lending",
        "resource_sharing": "Cohort fair sharing with flavor-level borrowing limits",
        "topology_awareness": "Topology-Aware Scheduling (TAS) via Topology & ResourceFlavor CRDs",
        "gpu_optimization": "Flavor-based heterogeneous GPU and MIG quota accounting",
        "operational_complexity": "Medium",
    },
    "volcano": {
        "architecture": "Full replacement batch scheduler (Session: Open -> Action -> Plugin -> Close)",
        "gang_scheduling": "PodGroup CRD (minMember, minTaskMember, minResources)",
        "queue_management": "Hierarchical Queues with capability, weight, and deserved",
        "resource_sharing": "Dominant Resource Fairness (DRF), Proportion, Capacity plugins",
        "topology_awareness": "NetworkTopology CRD (hypernodetiers) & binpack plugin",
        "gpu_optimization": "GPU sharing / MIG / vGPU scheduler plugins",
        "operational_complexity": "Medium-High",
    },
    "kai_scheduler": {
        "architecture": "7-microservice GPU-native scheduler (operator, kai-scheduler, pod-grouper, binder, queue-controller, admission, pod-group-controller)",
        "gang_scheduling": "PodGroup with hierarchical SubGroup / PodSet gang & topology constraints",
        "queue_management": "Two-level hierarchical Queue (Department -> Project) with quota, limit, overQuotaWeight",
        "resource_sharing": "Guaranteed quota + weighted over-quota borrowing + staleness reclamation",
        "topology_awareness": "Topology CRD + SubGroup rack/leaf/NVLink domain placement",
        "gpu_optimization": "Native fractional GPUs (gpu-fraction, gpu-memory) via binder reservation pods + MIG consolidation",
        "operational_complexity": "Medium",
    },
    "yunikorn": {
        "architecture": "Unified batch + streaming replacement scheduler (Apache YuniKorn)",
        "gang_scheduling": "Task-group gang scheduling via placeholder pods",
        "queue_management": "Hierarchical queues with guaranteed and max capacities",
        "resource_sharing": "Fair (spread) and BinPacking node sorting + dynamic resource quotas",
        "topology_awareness": "Node sorting and rack/zone placement rules",
        "gpu_optimization": "Converges Apache Spark/Flink data prep + GPU AI/ML jobs on one scheduler",
        "operational_complexity": "Medium",
    },
    "slurm": {
        "architecture": "Bare-metal HPC workload manager (slurmctld, slurmd, slurmdbd, slurmrestd) + Enroot/Pyxis",
        "gang_scheduling": "Native millisecond-synchronized whole-job gang allocation (sbatch / srun)",
        "queue_management": "Multi-factor Fair-Share Tree (Account -> User) + QoS + Partitions",
        "resource_sharing": "Exclusive node/GRES allocation, cgroups v2 ConstrainDevices=yes, or static GRES/MIG/MPS",
        "topology_awareness": "TopologyPlugin=topology/tree (spine-leaf switch hop minimization) + SelectType=select/cons_tres",
        "gpu_optimization": "AutoDetect=nvml GRES, zero-overhead bare-metal InfiniBand/NVLink, Enroot 98-nvidia.sh & 99-mellanox.sh hooks",
        "operational_complexity": "High for microservice teams; gold standard for bare-metal HPC",
    },
}


@dataclass(frozen=True)
class WorkloadSchedulerProfile:
    needs_fractional_gpu_memory: bool
    co_locates_spark_flink_and_ml: bool
    is_bare_metal_512_plus_gpu_pretraining: bool
    wants_lightweight_k8s_job_admission_only: bool
    wants_minimal_podgroup_plugin_only: bool


def recommend_scheduler(profile: WorkloadSchedulerProfile) -> Dict[str, str]:
    """Selects the optimal scheduler based on Chapter 11.20 decision criteria."""
    if profile.is_bare_metal_512_plus_gpu_pretraining:
        return {
            "recommended": "slurm",
            "container_runtime": "Enroot + Pyxis (--container-image=/shared/containers/pytorch.sqsh)",
            "coexistence_mechanism": "BCM Auto Scaler (cm-scale) configuration overlays",
        }
    if profile.needs_fractional_gpu_memory:
        return {
            "recommended": "kai_scheduler",
            "container_runtime": "containerd + NVIDIA Container Toolkit (CDI)",
            "coexistence_mechanism": "Can pair with Kueue admission or Run:ai Control Plane",
        }
    if profile.co_locates_spark_flink_and_ml:
        return {
            "recommended": "yunikorn",
            "container_runtime": "containerd + NVIDIA Container Toolkit",
            "coexistence_mechanism": "Unified hierarchical queues for Spark/Flink + PyTorch",
        }
    if profile.wants_lightweight_k8s_job_admission_only:
        return {
            "recommended": "kueue",
            "container_runtime": "containerd + NVIDIA Container Toolkit",
            "coexistence_mechanism": "Composes with kube-scheduler, KAI Scheduler, or Volcano",
        }
    if profile.wants_minimal_podgroup_plugin_only:
        return {
            "recommended": "coscheduling",
            "container_runtime": "containerd + NVIDIA Container Toolkit",
            "coexistence_mechanism": "In-process kube-scheduler plugin",
        }
    return {
        "recommended": "volcano",
        "container_runtime": "containerd + NVIDIA Container Toolkit",
        "coexistence_mechanism": "Standalone session-based Kubernetes batch scheduler",
    }


def compute_cluster_mtbf_and_superpod_facts(
    num_nodes: int = 512,
    gpus_per_node: int = 8,
    single_node_mtbf_days: float = 1000.0,
    superpod_sus: int = 4,
    nodes_per_su: int = 32,
    ufm_reserved_nodes: int = 1,
    dgx_h100_max_kw: float = 10.2,
    rack_power_limit_kw: float = 30.0,
) -> Dict[str, object]:
    """Computes Volume 10 Ch 9 Cluster MTBF and Volume 10 Ch 00c DGX H100 SuperPOD facts."""
    total_gpus = num_nodes * gpus_per_node
    cluster_mtbf_days = round(single_node_mtbf_days / num_nodes, 2)

    nominal_superpod_nodes = superpods_nodes = superpod_sus * nodes_per_su
    nominal_superpod_gpus = superpods_nodes * gpus_per_node
    compute_table_nodes = nominal_superpod_nodes - ufm_reserved_nodes
    compute_table_gpus = compute_table_nodes * gpus_per_node
    single_su_compute_nodes = nodes_per_su - ufm_reserved_nodes

    max_dgx_per_30kw_rack = int(rack_power_limit_kw // dgx_h100_max_kw)

    return {
        "cluster_nodes": num_nodes,
        "cluster_gpus": total_gpus,
        "single_node_mtbf_days": single_node_mtbf_days,
        "cluster_mtbf_days": cluster_mtbf_days,
        "nominal_superpod_nodes": nominal_superpod_nodes,
        "nominal_superpod_gpus": nominal_superpod_gpus,
        "compute_table_nodes_with_ufm": compute_table_nodes,
        "compute_table_gpus_with_ufm": compute_table_gpus,
        "single_su_compute_nodes": single_su_compute_nodes,
        "dgx_h100_max_kw": dgx_h100_max_kw,
        "dgx_h100_psu_count": 6,
        "dgx_h100_psu_rating_kw": 3.3,
        "max_dgx_per_30kw_rack": max_dgx_per_30kw_rack,
    }


XID_CATALOG_ACTIONS: Dict[int, Dict[str, str]] = {
    13: {"description": "Graphics Engine Exception", "immediate": "RESTART_APP", "investigatory": "WORKFLOW_XID_13"},
    31: {"description": "GPU memory page fault", "immediate": "RESTART_APP", "investigatory": "WORKFLOW_XID_31"},
    44: {"description": "Graphics Engine fault during context switch", "immediate": "IGNORE", "investigatory": "CONTACT_SUPPORT"},
    48: {"description": "Double Bit ECC Error", "immediate": "WORKFLOW_XID_48", "investigatory": "WORKFLOW_XID_48"},
    63: {"description": "GPU memory remapping event", "immediate": "IGNORE", "investigatory": "IGNORE"},
    64: {"description": "GPU memory remapping failure", "immediate": "RESET_GPU", "investigatory": "CONTACT_SUPPORT"},
    74: {"description": "NVLINK Error", "immediate": "WORKFLOW_NVLINK_ERR", "investigatory": "CONTACT_SUPPORT"},
    79: {"description": "GPU has fallen off the bus", "immediate": "RESTART_BM", "investigatory": "CONTACT_SUPPORT"},
    94: {"description": "Contained memory error", "immediate": "RESTART_APP", "investigatory": "IGNORE (sympathetic)"},
    95: {"description": "Uncontained memory error", "immediate": "RESET_GPU", "investigatory": "IGNORE (sympathetic)"},
    109: {"description": "Context Switch Timeout Error", "immediate": "RESET_GPU", "investigatory": "CONTACT_SUPPORT"},
    119: {"description": "GSP RPC Timeout", "immediate": "RESET_GPU", "investigatory": "INVESTIGATE_SW"},
    120: {"description": "GSP Error", "immediate": "RESET_GPU", "investigatory": "INVESTIGATE_SW"},
}
