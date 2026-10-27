#!/usr/bin/env python3
"""Chapter 14.10 model: Multi-node Training Architecture.

Models:
1. Rank Mapping & Process Group Rendezvous (`c10d`, `env://`, `tcp://`, `TCPStore`, SLURM):
   - Global rank formula: `RANK = NODE_RANK * GPUS_PER_NODE + LOCAL_RANK`.
   - SLURM launcher patterns:
     * Pattern A (`--ntasks-per-node=1` + `torchrun --nproc_per_node=G`): 1 `torchrun` supervisor per node
       (`SLURM_NTASKS == SLURM_NNODES`, `SLURM_PROCID == SLURM_NODEID`, `SLURM_LOCALID == 0`), spawning
       `G` local worker processes (`WORLD_SIZE = SLURM_NNODES * G`).
     * Pattern B (`--ntasks-per-node=G` + `srun python train.py` with `init_method="env://"`): SLURM
       directly spawns `G` tasks per node (`SLURM_NTASKS == WORLD_SIZE`, `SLURM_PROCID == RANK`,
       `SLURM_LOCALID == LOCAL_RANK`).
   - Misconfiguration detection: `--ntasks-per-node=8` combined with `torchrun --nproc_per_node=8`
     spawns `8 * 8 = 64` processes per node (`8x` GPU oversubscription); setting `MASTER_ADDR=127.0.0.1`
     on a multi-node job causes split-brain single-node process groups.
2. Multi-Dimensional 3D/4D Process-Group Rank Grid Generator `(DP, PP, TP)` & `(DP, PP, CP, TP)`:
   - Standard Megatron-LM / TorchTitan rank ordering `[DP, PP, CP, TP]` (inner-most `TP` contiguous
     within a node's `NVLink` domain; `PP` across neighboring leaf switches/rails; `DP`/`FSDP` across
     the cluster fabric) vs anti-pattern `[TP, PP, DP]` (`TP-across-nodes` crossing `50 GB/s` IB
     instead of `900 GB/s` NVLink, causing `18x` bandwidth drop and `16.7x` step-time slowdown).
3. Rail-Optimized Fabric & Multi-Node Scaling Efficiency (`16` to `16,384` GPUs):
   - Per-GPU cross-node bandwidth (`400 Gbps` NDR IB = `50 GB/s`; `8` NICs = `400 GB/s` node aggregate;
     `800 Gbps` XDR IB = `100 GB/s` per GPU / `800 GB/s` node aggregate) vs intra-node `NVLink 4`
     (`900 GB/s` per GPU, `18x` ratio) and `NVLink 5` (`1,800 GB/s` per GPU).
   - Ring vs Tree collective latency and bandwidth scaling from `8` GPUs (`49.0 GB` in `~54 ms` on
     `900 GB/s` NVLink) to `512` GPUs (`55.9 GB` in `~2.2 s` on `25 GB/s` IB, `512` ring hops vs
     `9` tree hops) and compute-to-communication scaling efficiency across `16` to `16,384` GPUs.
4. Host CPU / NUMA / PCIe / NIC Affinity Binding Verifier:
   - Dual-socket `8`-GPU HGX topology (`GPUs 0..3` on `NUMA 0` paired 1:1 with `mlx5_0..mlx5_3` on
     dedicated PCIe switches `PIX`; `GPUs 4..7` on `NUMA 1` paired 1:1 with `mlx5_4..mlx5_7`).
   - Detects QPI/UPI cross-socket traversal (`SYS`) when `GPU 0` uses `NIC 3` or wrong NUMA cores
     (`40 GB/s` vs `300 GB/s` in `nccl-tests`, `7.5x` degradation).
5. Storage / Checkpoint / Network Co-Design & Preemption Recovery:
   - Megatron-LM `8.03B` distributed checkpoint sizing (`16.06 GB` `BF16` weights + `64.24 GB` `FP32`
     `Adam` states = `80.30 GB` theoretical, `108.0 GB` actual across `4 x 27.0 GB` `.distcp` shards)
     and burst parallel filesystem write bandwidth + SLURM `SIGUSR1@90` / `SIGTERM` preemption handling.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class SlurmRendezvousConfig:
    num_nodes: int
    gpus_per_node: int
    ntasks_per_node: int
    launcher: str  # "torchrun" or "srun_direct"
    nproc_per_node: int = 8
    master_addr: str = "dgx-001"
    master_port: int = 29500


def map_global_rank(node_rank: int, local_rank: int, gpus_per_node: int = 8) -> int:
    """Computes global rank from node_rank and local_rank: RANK = NODE_RANK * GPUS_PER_NODE + LOCAL_RANK."""
    if node_rank < 0 or local_rank < 0 or local_rank >= gpus_per_node:
        raise ValueError(f"Invalid node_rank={node_rank} or local_rank={local_rank} for gpus_per_node={gpus_per_node}")
    return node_rank * gpus_per_node + local_rank


def invert_global_rank(global_rank: int, gpus_per_node: int = 8) -> Tuple[int, int]:
    """Recovers (node_rank, local_rank) from global_rank."""
    if global_rank < 0 or gpus_per_node <= 0:
        raise ValueError("global_rank must be >= 0 and gpus_per_node > 0")
    return global_rank // gpus_per_node, global_rank % gpus_per_node


def validate_slurm_rendezvous(cfg: SlurmRendezvousConfig) -> Dict[str, int | str | bool]:
    """Validates SLURM + PyTorch c10d rendezvous configuration and detects launch anti-patterns."""
    expected_world_size = cfg.num_nodes * cfg.gpus_per_node
    split_brain_loopback = cfg.num_nodes > 1 and cfg.master_addr in ("127.0.0.1", "localhost", "::1")

    if cfg.launcher == "torchrun":
        spawned_per_node = cfg.ntasks_per_node * cfg.nproc_per_node
        slurm_ntasks = cfg.num_nodes * cfg.ntasks_per_node
        oversubscription_factor = spawned_per_node // cfg.gpus_per_node
        valid_task_layout = (cfg.ntasks_per_node == 1) and (cfg.nproc_per_node == cfg.gpus_per_node)
    elif cfg.launcher == "srun_direct":
        spawned_per_node = cfg.ntasks_per_node
        slurm_ntasks = cfg.num_nodes * cfg.ntasks_per_node
        oversubscription_factor = spawned_per_node // cfg.gpus_per_node
        valid_task_layout = cfg.ntasks_per_node == cfg.gpus_per_node
    else:
        raise ValueError(f"Unknown launcher: {cfg.launcher}")

    actual_world_size = cfg.num_nodes * spawned_per_node
    is_valid = valid_task_layout and not split_brain_loopback and (1024 <= cfg.master_port <= 65535)

    return {
        "expected_world_size": expected_world_size,
        "actual_world_size": actual_world_size,
        "slurm_ntasks": slurm_ntasks,
        "spawned_per_node": spawned_per_node,
        "oversubscription_factor": oversubscription_factor,
        "valid_task_layout": valid_task_layout,
        "split_brain_loopback": split_brain_loopback,
        "is_valid": is_valid,
        "c10d_endpoint": f"{cfg.master_addr}:{cfg.master_port}",
    }


def generate_4d_parallel_groups(
    dp_size: int,
    pp_size: int,
    cp_size: int,
    tp_size: int,
    gpus_per_node: int = 8,
    order: str = "tp-cp-pp-dp",
) -> Dict[str, object]:
    """Generates 3D/4D process groups (TP, CP, PP, DP) and analyzes NVLink vs InfiniBand rail locality.

    - `order="tp-cp-pp-dp"` (standard): TP is inner-most (stride 1), then CP, then PP, then DP (outer-most).
      `global_rank = (((dp * pp_size + pp) * cp_size + cp) * tp_size + tp)`
    - `order="dp-pp-cp-tp"` (misconfigured TP-outer): DP is inner-most (stride 1) and TP is outer-most,
      forcing TP groups across nodes over slower InfiniBand links.
    """
    world_size = dp_size * pp_size * cp_size * tp_size
    tp_groups: List[List[int]] = []
    cp_groups: List[List[int]] = []
    pp_groups: List[List[int]] = []
    dp_groups: List[List[int]] = []

    def rank_of(dp: int, pp: int, cp: int, tp: int) -> int:
        if order == "tp-cp-pp-dp":
            return ((dp * pp_size + pp) * cp_size + cp) * tp_size + tp
        if order == "dp-pp-cp-tp":
            return ((tp * pp_size + pp) * cp_size + cp) * dp_size + dp
        raise ValueError(f"Unsupported order: {order}")

    for dp in range(dp_size):
        for pp in range(pp_size):
            for cp in range(cp_size):
                tp_groups.append([rank_of(dp, pp, cp, tp) for tp in range(tp_size)])

    for dp in range(dp_size):
        for pp in range(pp_size):
            for tp in range(tp_size):
                cp_groups.append([rank_of(dp, pp, cp, tp) for cp in range(cp_size)])

    for dp in range(dp_size):
        for cp in range(cp_size):
            for tp in range(tp_size):
                pp_groups.append([rank_of(dp, pp, cp, tp) for pp in range(pp_size)])

    for pp in range(pp_size):
        for cp in range(cp_size):
            for tp in range(tp_size):
                dp_groups.append([rank_of(dp, pp, cp, tp) for dp in range(dp_size)])

    # Check whether every TP group stays inside a single node's NVLink domain
    tp_intra_node = all(
        len({r // gpus_per_node for r in group}) == 1 for group in tp_groups
    )
    # Check whether PP and DP hops preserve rail alignment (same local_rank / NIC index across nodes)
    pp_same_rail = all(
        len({r % gpus_per_node for r in group}) == 1 for group in pp_groups
    )
    dp_same_rail = all(
        len({r % gpus_per_node for r in group}) == 1 for group in dp_groups
    )

    return {
        "world_size": world_size,
        "num_nodes": world_size // gpus_per_node,
        "tp_groups": tp_groups,
        "cp_groups": cp_groups,
        "pp_groups": pp_groups,
        "dp_groups": dp_groups,
        "tp_intra_node": tp_intra_node,
        "pp_same_rail": pp_same_rail,
        "dp_same_rail": dp_same_rail,
    }


def evaluate_rail_fabric_and_collectives(
    gpus_per_node: int = 8,
    nic_gbps: float = 400.0,
    nvlink_bw_gbps_per_gpu: float = 900.0,
    grad_tensor_gb: float = 28.0,
    large_cluster_gpus: int = 512,
    effective_ib_gbps_per_gpu: float = 25.0,
) -> Dict[str, float]:
    """Computes rail-optimized cross-node vs intra-node bandwidth and Ring vs Tree collective costs."""
    per_gpu_ib_gbps = nic_gbps * 0.125  # 400 Gbps * 0.125 = 50.0 GB/s
    node_aggregate_ib_gbps = gpus_per_node * per_gpu_ib_gbps  # 8 * 50.0 = 400.0 GB/s
    nvlink_to_ib_ratio = round(nvlink_bw_gbps_per_gpu / per_gpu_ib_gbps, 2)  # 900 / 50 = 18.0x

    # Case A: 8 GPUs on single node NVLink (900 GB/s), 28 GB FP32 gradients (49 GB / 900 GB/s = 0.0544 s ~ 54 ms)
    ring_bytes_8gpu_gb = 2.0 * ((gpus_per_node - 1) / gpus_per_node) * grad_tensor_gb  # 49.0 GB
    ring_time_8gpu_s = 0.0544
    ring_time_8gpu_ms = round((ring_bytes_8gpu_gb / nvlink_bw_gbps_per_gpu) * 1000.0, 1)  # 54.4 ms (~54 ms)

    # Case B: 512 GPUs (64 nodes) over IB (25 GB/s effective), 28 GB FP32 gradients
    ring_bytes_512gpu_gb = round(
        2.0 * ((large_cluster_gpus - 1) / large_cluster_gpus) * grad_tensor_gb, 4
    )  # 55.8906 GB (~55.9 GB)
    ring_time_512gpu_s = round(ring_bytes_512gpu_gb / effective_ib_gbps_per_gpu, 2)  # 2.24 s (~2.2 s)
    ring_hops_512 = large_cluster_gpus  # 512 hops
    tree_hops_512 = int(large_cluster_gpus).bit_length() - 1  # log2(512) = 9 hops

    return {
        "per_gpu_ib_gbps": per_gpu_ib_gbps,
        "node_aggregate_ib_gbps": node_aggregate_ib_gbps,
        "nvlink_bw_gbps_per_gpu": nvlink_bw_gbps_per_gpu,
        "nvlink_to_ib_ratio": nvlink_to_ib_ratio,
        "ring_bytes_8gpu_gb": ring_bytes_8gpu_gb,
        "ring_time_8gpu_s": ring_time_8gpu_s,
        "ring_time_8gpu_ms": ring_time_8gpu_ms,
        "ring_bytes_512gpu_gb": ring_bytes_512gpu_gb,
        "ring_time_512gpu_s": ring_time_512gpu_s,
        "ring_hops_512": float(ring_hops_512),
        "tree_hops_512": float(tree_hops_512),
    }


SCALING_CURVE_REFERENCE_TABLE: List[Dict[str, float | int | str]] = [
    {"num_gpus": 16, "num_nodes": 2, "tree_hops": 1, "ar_bytes_gb": 17.50, "raw_comm_time_s": 0.3519, "exposed_comm_time_s": 0.0894, "step_time_s": 4.0894, "compute_to_comm_ratio": 11.37, "scaling_efficiency_pct": "97.81%"},
    {"num_gpus": 64, "num_nodes": 8, "tree_hops": 3, "ar_bytes_gb": 30.625, "raw_comm_time_s": 0.6204, "exposed_comm_time_s": 0.1610, "step_time_s": 4.1610, "compute_to_comm_ratio": 6.45, "scaling_efficiency_pct": "96.13%"},
    {"num_gpus": 256, "num_nodes": 32, "tree_hops": 5, "ar_bytes_gb": 33.906, "raw_comm_time_s": 0.6950, "exposed_comm_time_s": 0.1864, "step_time_s": 4.1864, "compute_to_comm_ratio": 5.76, "scaling_efficiency_pct": "95.55%"},
    {"num_gpus": 1024, "num_nodes": 128, "tree_hops": 7, "ar_bytes_gb": 34.727, "raw_comm_time_s": 0.7234, "exposed_comm_time_s": 0.2025, "step_time_s": 4.2025, "compute_to_comm_ratio": 5.53, "scaling_efficiency_pct": "95.18%"},
    {"num_gpus": 4096, "num_nodes": 512, "tree_hops": 9, "ar_bytes_gb": 34.932, "raw_comm_time_s": 0.7425, "exposed_comm_time_s": 0.2185, "step_time_s": 4.2185, "compute_to_comm_ratio": 5.39, "scaling_efficiency_pct": "94.82%"},
    {"num_gpus": 16384, "num_nodes": 2048, "tree_hops": 11, "ar_bytes_gb": 34.983, "raw_comm_time_s": 0.7615, "exposed_comm_time_s": 0.2367, "step_time_s": 4.2367, "compute_to_comm_ratio": 5.25, "scaling_efficiency_pct": "94.41%"},
]


def compute_multinode_scaling_curve(
    gpu_counts: List[int] | None = None,
    base_compute_time_s: float = 4.0,
    dp_grad_gb_per_replica: float = 17.5,
    inter_node_bw_gbps: float = 50.0,
    per_hop_tree_latency_ms: float = 1.5,
    overlap_fraction: float = 0.75,
) -> List[Dict[str, float | int]]:
    """Models compute-to-communication ratio and scaling efficiency from 16 to 16,384 GPUs.

    Assumes 3D/HSDP-style scaling where intra-node TP/FSDP size is 8 GPUs (`17.5 GB` gradient shard
    per GPU for a 70B FP16 model) and DP replicas scale across `N / 8` nodes.
    As cluster size grows under fixed or moderately scaled global batch, exposed collective latency
    plus pipeline/straggler overhead increases the communication tax.
    """
    if gpu_counts is None:
        gpu_counts = [16, 64, 256, 1024, 4096, 16384]

    results: List[Dict[str, float | int]] = []
    for n_gpus in gpu_counts:
        num_nodes = max(1, n_gpus // 8)
        tree_hops = max(1, num_nodes.bit_length() - 1)
        # AllReduce bytes across `num_nodes` DP ranks for a 17.5 GB shard
        ar_bytes_gb = 2.0 * ((num_nodes - 1) / num_nodes) * dp_grad_gb_per_replica
        bw_time_s = ar_bytes_gb / inter_node_bw_gbps
        latency_straggler_s = (tree_hops * per_hop_tree_latency_ms) / 1000.0 * (1.0 + 0.25 * tree_hops)
        raw_comm_time_s = bw_time_s + latency_straggler_s
        exposed_comm_time_s = (1.0 - overlap_fraction) * bw_time_s + latency_straggler_s
        step_time_s = base_compute_time_s + exposed_comm_time_s
        scaling_efficiency = round(base_compute_time_s / step_time_s, 4)
        compute_to_comm_ratio = round(base_compute_time_s / raw_comm_time_s, 2)
        results.append(
            {
                "num_gpus": n_gpus,
                "num_nodes": num_nodes,
                "tree_hops": tree_hops,
                "ar_bytes_gb": round(ar_bytes_gb, 4),
                "raw_comm_time_s": round(raw_comm_time_s, 4),
                "exposed_comm_time_s": round(exposed_comm_time_s, 4),
                "step_time_s": round(step_time_s, 4),
                "scaling_efficiency": scaling_efficiency,
                "compute_to_comm_ratio": compute_to_comm_ratio,
            }
        )
    return results


def verify_node_numa_nic_binding(
    total_cores: int = 128,
    gpus_per_node: int = 8,
    custom_nic_map: Dict[int, str] | None = None,
) -> Dict[str, object]:
    """Generates and validates per-rank CPU core, NUMA node, PCIe switch, and RDMA NIC bindings.

    Standard dual-socket 8-GPU HGX node:
    - Socket/NUMA 0 (cores 0..63): GPUs 0..3 paired 1:1 with mlx5_0..mlx5_3 (PIX)
    - Socket/NUMA 1 (cores 64..127): GPUs 4..7 paired 1:1 with mlx5_4..mlx5_7 (PIX)
    """
    cores_per_gpu = total_cores // gpus_per_node
    bindings: List[Dict[str, object]] = []
    all_optimal = True

    for local_rank in range(gpus_per_node):
        expected_numa = 0 if local_rank < (gpus_per_node // 2) else 1
        expected_nic = f"mlx5_{local_rank}"
        actual_nic = custom_nic_map.get(local_rank, expected_nic) if custom_nic_map else expected_nic
        actual_nic_idx = int(actual_nic.split("_")[1])
        nic_numa = 0 if actual_nic_idx < (gpus_per_node // 2) else 1

        core_start = local_rank * cores_per_gpu
        core_end = core_start + cores_per_gpu - 1
        same_pcie_switch = actual_nic_idx == local_rank
        same_numa = nic_numa == expected_numa
        path_type = "PIX" if same_pcie_switch else ("PXB/NODE" if same_numa else "SYS")

        if not same_pcie_switch:
            all_optimal = False

        bindings.append(
            {
                "local_rank": local_rank,
                "gpu": f"cuda:{local_rank}",
                "numa_node": expected_numa,
                "cpu_cores": f"{core_start}-{core_end}",
                "expected_nic": expected_nic,
                "actual_nic": actual_nic,
                "path_type": path_type,
                "gdr_optimal": same_pcie_switch,
            }
        )

    return {
        "cores_per_gpu": cores_per_gpu,
        "all_optimal": all_optimal,
        "expected_nccl_busbw_gbps": 300.0 if all_optimal else 40.0,
        "bindings": bindings,
    }


def evaluate_storage_checkpoint_codesign(
    params_billion: float = 8.03,
    num_shards: int = 4,
    shard_file_gb: float = 27.0,
    cluster_Aggregate_write_gbps: float = 25.0,
    slurm_signal_lead_s: int = 90,
) -> Dict[str, float | bool]:
    """Computes Megatron-LM distributed checkpoint footprint and validates SLURM preemption grace window."""
    bf16_weights_gb = round(params_billion * 2.0, 2)  # 8.03 * 2 = 16.06 GB
    fp32_adam_gb = round(params_billion * 8.0, 2)  # 8.03 * 8 = 64.24 GB
    theoretical_state_gb = round(bf16_weights_gb + fp32_adam_gb, 2)  # 80.30 GB
    actual_distcp_total_gb = round(num_shards * shard_file_gb, 2)  # 4 * 27.0 = 108.0 GB
    metadata_overhead_gb = round(actual_distcp_total_gb - theoretical_state_gb, 2)  # 27.70 GB
    write_duration_s = round(actual_distcp_total_gb / cluster_Aggregate_write_gbps, 2)  # 108 / 25 = 4.32 s
    fits_in_signal_window = write_duration_s < slurm_signal_lead_s

    return {
        "bf16_weights_gb": bf16_weights_gb,
        "fp32_adam_gb": fp32_adam_gb,
        "theoretical_state_gb": theoretical_state_gb,
        "actual_distcp_total_gb": actual_distcp_total_gb,
        "metadata_overhead_gb": metadata_overhead_gb,
        "write_duration_s": write_duration_s,
        "slurm_signal_lead_s": float(slurm_signal_lead_s),
        "fits_in_signal_window": fits_in_signal_window,
    }


if __name__ == "__main__":
    rdzv = validate_slurm_rendezvous(SlurmRendezvousConfig(4, 8, 1, "torchrun", 8, "dgx-012", 29500))
    print("Rendezvous (4x8 torchrun):", rdzv)
    grid = generate_4d_parallel_groups(dp_size=2, pp_size=2, cp_size=1, tp_size=8, gpus_per_node=8)
    print("4D Grid (DP=2, PP=2, CP=1, TP=8):", {k: v for k, v in grid.items() if not k.endswith("_groups")})
    fabric = evaluate_rail_fabric_and_collectives()
    print("Rail Fabric & Collectives:", fabric)
    curve = compute_multinode_scaling_curve()
    print("Scaling Curve (16..16384 GPUs):", [(r["num_gpus"], r["scaling_efficiency"]) for r in curve])
    affinity = verify_node_numa_nic_binding()
    print("Affinity Optimal:", affinity["all_optimal"], "Cores/GPU:", affinity["cores_per_gpu"])
    ckpt = evaluate_storage_checkpoint_codesign()
    print("Checkpoint Co-design (8.03B):", ckpt)
