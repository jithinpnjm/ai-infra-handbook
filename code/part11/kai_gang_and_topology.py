"""Chapter 11.16 — KAI gang scheduling and topology-aware placement.

Deterministic models for:
1. KAI Scheduler multi-level `Topology` tree (`Rack / IB Leaf Switch` -> `Node /
   NVSwitch Domain` -> `NUMA / NVLink Island`) and gang + topology scorer:
   - Prefers single-node `NVSwitch` (`900 GB/s`) over same-rack `InfiniBand`
     (`200-400 Gbps`), which beats cross-rack `Spine` or `Ethernet` (`10-100 Gbps`).
2. Volume 02 Lab 04 `4`-GPU H100 (`81559 MiB`) dual-socket placement verifier:
   - Group A (`NUMA 0`, CPUs `0-15`, `257698 MB` RAM): `GPU0` (`0000:1b:00.0`)
     & `GPU1` (`0000:3d:00.0`) (`NV4`) + `NIC0` (`0000:18:00.0`, `PIX`).
   - Group B (`NUMA 1`, CPUs `16-31`, `258043 MB` RAM): `GPU2` (`0000:9a:00.0`)
     & `GPU3` (`0000:c3:00.0`) (`NV4`) + `NIC1` (`0000:9d:00.0`, `PIX`).
   - Degraded NVLink detector (`nvidia-smi nvlink --status`: `3 x 26.562 GB/s` +
     `1 x 0.000 GB/s` = `79.686 / 106.248 GB/s` = `75.0%` active bandwidth).
3. Volume 24 Project 10 `50B`-model training throughput & topology calculator:
   - `256 * 2048 = 524,288` tokens/step, `2 * 50B = 100` GFLOP/token.
   - `1000` TFLOPS achieved -> `3.6e18` FLOP/hr -> `36M` tokens/hr/GPU.
   - `90` H100 GPUs at `80%` availability -> `22.7T` tokens/year vs `100T` target
     (`4.4x` shortfall, needing `~396` GPUs / `~$16M` GPU CapEx vs `$5M` budget).
   - `100ms` compute + `50ms` ring AllReduce = `150ms < 300ms` step target;
     `600 GB` checkpoint (`200 GB` weights + `400 GB` optimizer).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class CandidateNodeTopology:
    """Topology state of a candidate GPU node in a KAI scheduling session."""

    node_name: str
    rack_or_leaf_switch: str
    free_gpus_numa0: int
    free_gpus_numa1: int
    has_nvswitch_full_mesh: bool
    inter_node_fabric: str  # "infiniband" or "ethernet"

    @property
    def total_free_gpus(self) -> int:
        return self.free_gpus_numa0 + self.free_gpus_numa1


def select_kai_gang_topology_placement(
    pods_in_gang: int,
    gpus_per_pod: int,
    topology_constraint: str,  # "single-numa", "single-node-nvswitch", "same-rack-ib", "any"
    nodes: List[CandidateNodeTopology],
) -> Dict[str, object]:
    """Simulate KAI Scheduler atomic gang + hierarchical topology placement."""
    total_gpus_needed = pods_in_gang * gpus_per_pod

    # 1. Check single-NUMA constraint (all pods fit inside one NUMA island on one node)
    if topology_constraint == "single-numa":
        for n in nodes:
            if n.free_gpus_numa0 >= total_gpus_needed:
                return {
                    "scheduled": True,
                    "domain": "single_numa_island",
                    "nodes": [n.node_name],
                    "numa_node": 0,
                    "bottleneck_link": "NV4 / PIX (900 GB/s / 64 GB/s)",
                }
            if n.free_gpus_numa1 >= total_gpus_needed:
                return {
                    "scheduled": True,
                    "domain": "single_numa_island",
                    "nodes": [n.node_name],
                    "numa_node": 1,
                    "bottleneck_link": "NV4 / PIX (900 GB/s / 64 GB/s)",
                }
        return {"scheduled": False, "domain": None, "nodes": [], "bottleneck_link": None}

    # 2. Check single-node NVSwitch full-mesh constraint (e.g., 8 GPUs on 1 NVSwitch node)
    if topology_constraint in ("single-node-nvswitch", "same-rack-ib", "any"):
        for n in nodes:
            if n.has_nvswitch_full_mesh and n.total_free_gpus >= total_gpus_needed:
                return {
                    "scheduled": True,
                    "domain": "single_node_nvswitch",
                    "nodes": [n.node_name],
                    "bottleneck_link": "NVSwitch Full Mesh (900 GB/s per GPU)",
                }
        if topology_constraint == "single-node-nvswitch":
            return {"scheduled": False, "domain": None, "nodes": [], "bottleneck_link": None}

    # 3. Check same-rack InfiniBand leaf switch across multiple nodes
    by_rack: Dict[str, List[CandidateNodeTopology]] = {}
    for n in nodes:
        if n.inter_node_fabric == "infiniband" and n.total_free_gpus >= gpus_per_pod:
            by_rack.setdefault(n.rack_or_leaf_switch, []).append(n)

    for rack_id, rack_nodes in sorted(by_rack.items()):
        placeable_pods = sum(rn.total_free_gpus // gpus_per_pod for rn in rack_nodes)
        if placeable_pods >= pods_in_gang:
            chosen_nodes: List[str] = []
            rem = pods_in_gang
            for rn in rack_nodes:
                fit = min(rem, rn.total_free_gpus // gpus_per_pod)
                chosen_nodes.extend([rn.node_name] * fit)
                rem -= fit
                if rem == 0:
                    break
            return {
                "scheduled": True,
                "domain": f"same_rack_ib ({rack_id})",
                "nodes": chosen_nodes,
                "bottleneck_link": "InfiniBand Leaf Switch (200-400 Gbps)",
            }

    if topology_constraint == "same-rack-ib":
        return {"scheduled": False, "domain": None, "nodes": [], "bottleneck_link": None}

    # 4. Fallback (`any`): scatter across any available nodes
    all_eligible = [n for n in nodes if n.total_free_gpus >= gpus_per_pod]
    if sum(n.total_free_gpus // gpus_per_pod for n in all_eligible) >= pods_in_gang:
        return {
            "scheduled": True,
            "domain": "cross_rack_or_ethernet",
            "nodes": [n.node_name for n in all_eligible[:pods_in_gang]],
            "bottleneck_link": "Cross-Rack / Standard Ethernet (10-100 Gbps)",
        }
    return {"scheduled": False, "domain": None, "nodes": [], "bottleneck_link": None}


def verify_lab04_host_placement_and_nvlink(
    selected_gpus: Tuple[int, int],
    selected_nic: int,
    nvlink_speeds_gbs: Tuple[float, ...] = (26.562, 26.562, 0.000, 26.562),
    expected_per_link_gbs: float = 26.562,
) -> Dict[str, object]:
    """Verify Volume 02 Lab 04 2-GPU + 1-NIC placement and NVLink sub-link health."""
    # Group 0: GPUs (0, 1) + NIC 0 on NUMA 0; Group 1: GPUs (2, 3) + NIC 1 on NUMA 1
    gpu_numa = {0: 0, 1: 0, 2: 1, 3: 1}
    nic_numa = {0: 0, 1: 1}

    g0, g1 = selected_gpus
    same_numa_gpus = gpu_numa[g0] == gpu_numa[g1]
    local_nic = nic_numa[selected_nic] == gpu_numa[g0] and same_numa_gpus
    peer_path = "NV4" if same_numa_gpus else "SYS"
    nic_path = "PIX" if local_nic else "SYS"

    active_links = sum(1 for s in nvlink_speeds_gbs if s > 0.0)
    total_links = len(nvlink_speeds_gbs)
    actual_bw = round(sum(nvlink_speeds_gbs), 3)
    expected_bw = round(total_links * expected_per_link_gbs, 3)
    bw_health_pct = round((actual_bw / expected_bw) * 100.0, 2)

    return {
        "same_numa_gpus": same_numa_gpus,
        "local_nic": local_nic,
        "gpu_peer_path": peer_path,
        "gpu_to_nic_path": nic_path,
        "placement_optimal": same_numa_gpus and local_nic,
        "active_nvlinks": active_links,
        "total_nvlinks": total_links,
        "actual_nvlink_bw_gbs": actual_bw,
        "expected_nvlink_bw_gbs": expected_bw,
        "nvlink_health_pct": bw_health_pct,
    }


def evaluate_50b_training_cluster_design(
    model_params_b: float = 50.0,
    batch_size: int = 256,
    seq_length: int = 2048,
    achieved_tflops_per_gpu: float = 1000.0,
    cluster_gpus: int = 90,
    availability_fraction: float = 0.80,
    target_tokens_trillion_per_yr: float = 100.0,
) -> Dict[str, float]:
    """Evaluate Volume 24 Project 10 50B LLM throughput, step latency, and budget gap."""
    tokens_per_step = batch_size * seq_length  # 524,288
    gflops_per_token = 2.0 * model_params_b  # 100 GFLOP/token
    eflops_per_hour_per_gpu = (achieved_tflops_per_gpu * 3600.0) / 1e6  # 3.6 EFLOP/hr
    tokens_millions_per_hr_per_gpu = (
        (achieved_tflops_per_gpu * 1e12 * 3600.0) / (gflops_per_token * 1e9)
    ) / 1e6  # 36.0M

    cluster_tokens_billions_per_hr = (
        cluster_gpus * tokens_millions_per_hr_per_gpu
    ) / 1000.0  # 3.24B
    achievable_trillion_per_yr = (
        cluster_tokens_billions_per_hr * 24.0 * 365.0 * availability_fraction
    ) / 1000.0  # 22.70592 -> ~22.7T

    shortfall_ratio = target_tokens_trillion_per_yr / achievable_trillion_per_yr
    gpus_needed_for_target = round(cluster_gpus * shortfall_ratio)  # ~396

    return {
        "tokens_per_step": float(tokens_per_step),
        "gflops_per_token": round(gflops_per_token, 2),
        "eflops_per_hour_per_gpu": round(eflops_per_hour_per_gpu, 2),
        "tokens_millions_per_hr_per_gpu": round(tokens_millions_per_hr_per_gpu, 2),
        "cluster_tokens_billions_per_hr": round(cluster_tokens_billions_per_hr, 2),
        "achievable_trillion_per_yr": round(achievable_trillion_per_yr, 1),
        "shortfall_ratio": round(shortfall_ratio, 1),
        "gpus_needed_for_100t": float(gpus_needed_for_target),
    }
