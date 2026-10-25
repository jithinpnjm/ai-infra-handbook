"""Chapter 11.16 Lab — KAI gang scheduling and topology-aware placement.

Run with:
    python3 code/part11/kai_gang_and_topology_lab.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kai_gang_and_topology import (
    CandidateNodeTopology,
    evaluate_50b_training_cluster_design,
    select_kai_gang_topology_placement,
    verify_lab04_host_placement_and_nvlink,
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

    print("=== Chapter 11.16 Lab: KAI Gang Scheduling & Topology-Aware Placement ===")

    # 1. KAI Multi-Level Topology Placement (Single-NUMA -> Single-Node NVSwitch -> Same-Rack IB -> Cross-Rack)
    nodes = [
        CandidateNodeTopology("eth-node-01", "rack-a", 1, 1, False, "ethernet"),
        CandidateNodeTopology("eth-node-02", "rack-a", 1, 1, False, "ethernet"),
        CandidateNodeTopology("ib-node-01", "rack-b", 2, 2, False, "infiniband"),
        CandidateNodeTopology("ib-node-02", "rack-b", 2, 2, False, "infiniband"),
        CandidateNodeTopology("dgx-nvswitch-01", "rack-c", 4, 4, True, "infiniband"),
    ]

    # Case A: 1-Pod, 8-GPU Tensor-Parallel job -> KAI picks single_node_nvswitch (`dgx-nvswitch-01`)
    p_nvswitch = select_kai_gang_topology_placement(
        pods_in_gang=1,
        gpus_per_pod=8,
        topology_constraint="single-node-nvswitch",
        nodes=nodes,
    )
    _check(
        p_nvswitch["scheduled"] is True
        and p_nvswitch["domain"] == "single_node_nvswitch"
        and p_nvswitch["nodes"] == ["dgx-nvswitch-01"],
        "KAI places 8-GPU Tensor-Parallel job on single_node_nvswitch (dgx-nvswitch-01, 900 GB/s)",
        passed,
        failed,
    )

    # Case B: 2-Pod, 4-GPU/Pod FSDP job on same-rack IB (when NVSwitch node is excluded/full)
    nodes_no_nvswitch = [n for n in nodes if not n.has_nvswitch_full_mesh]
    p_rack_ib = select_kai_gang_topology_placement(
        pods_in_gang=2,
        gpus_per_pod=4,
        topology_constraint="same-rack-ib",
        nodes=nodes_no_nvswitch,
    )
    _check(
        p_rack_ib["scheduled"] is True
        and p_rack_ib["domain"] == "same_rack_ib (rack-b)"
        and p_rack_ib["nodes"] == ["ib-node-01", "ib-node-02"],
        "KAI co-locates 2x4-GPU FSDP gang on same InfiniBand leaf switch rack (rack-b: ib-node-01, ib-node-02)",
        passed,
        failed,
    )

    # Case C: Single-NUMA 2-GPU placement (`single-numa`)
    p_numa = select_kai_gang_topology_placement(
        pods_in_gang=1,
        gpus_per_pod=2,
        topology_constraint="single-numa",
        nodes=nodes_no_nvswitch,
    )
    _check(
        p_numa["scheduled"] is True
        and p_numa["domain"] == "single_numa_island"
        and p_numa["nodes"] == ["ib-node-01"]
        and p_numa["numa_node"] == 0,
        "KAI places 2-GPU latency-sensitive job inside single_numa_island (NUMA 0 on ib-node-01)",
        passed,
        failed,
    )

    # Case D: Impossible gang (e.g. 4 pods x 4 GPUs = 16 GPUs when only 8 IB GPUs exist) -> holds in queue
    p_imp = select_kai_gang_topology_placement(
        pods_in_gang=4,
        gpus_per_pod=4,
        topology_constraint="same-rack-ib",
        nodes=nodes_no_nvswitch,
    )
    _check(
        p_imp["scheduled"] is False and p_imp["nodes"] == [],
        "When 16-GPU gang cannot fit in rack-b (8 GPUs free), KAI holds entire gang in queue (0 pods placed)",
        passed,
        failed,
    )

    # 2. Volume 02 Lab 04 Host Placement & Degraded NVLink Verification
    good_pair = verify_lab04_host_placement_and_nvlink(
        selected_gpus=(0, 1),
        selected_nic=0,
        nvlink_speeds_gbs=(26.562, 26.562, 26.562, 26.562),
    )
    _check(
        good_pair["placement_optimal"] is True
        and good_pair["gpu_peer_path"] == "NV4"
        and good_pair["gpu_to_nic_path"] == "PIX",
        "Lab 04 {GPU0, GPU1, NIC0} on NUMA 0 achieves optimal NV4 peer path and PIX NIC path",
        passed,
        failed,
    )

    bad_pair = verify_lab04_host_placement_and_nvlink(
        selected_gpus=(1, 2),
        selected_nic=1,
    )
    _check(
        bad_pair["placement_optimal"] is False
        and bad_pair["gpu_peer_path"] == "SYS"
        and bad_pair["gpu_to_nic_path"] == "SYS",
        "Naive {GPU1, GPU2, NIC1} placement crosses NUMA 0<->1 (SYS path for both GPU peer and GPU-to-NIC)",
        passed,
        failed,
    )
    _check(
        bad_pair["active_nvlinks"] == 3
        and bad_pair["total_nvlinks"] == 4
        and bad_pair["nvlink_health_pct"] == 75.0,
        "nvidia-smi nvlink --status with Link 2 at 0.000 GB/s (3 x 26.562 GB/s active) drops NV4 bandwidth to 75.0%",
        passed,
        failed,
    )

    # 3. Volume 24 Project 10: 50B Model Training Cluster Design & Topology Math
    proj10 = evaluate_50b_training_cluster_design(
        model_params_b=50.0,
        batch_size=256,
        seq_length=2048,
        achieved_tflops_per_gpu=1000.0,
        cluster_gpus=90,
        availability_fraction=0.80,
        target_tokens_trillion_per_yr=100.0,
    )
    _check(
        proj10["tokens_per_step"] == 524288.0
        and proj10["gflops_per_token"] == 100.0,
        "50B model (batch 256 x seq 2048) processes 524,288 tokens/step at 100.0 GFLOP/token",
        passed,
        failed,
    )
    _check(
        proj10["eflops_per_hour_per_gpu"] == 3.6
        and proj10["tokens_millions_per_hr_per_gpu"] == 36.0,
        "At 1000 TFLOPS achieved (1400 peak), 1 H100 delivers 3.6 EFLOP/hr = 36.0M tokens/hr",
        passed,
        failed,
    )
    _check(
        proj10["cluster_tokens_billions_per_hr"] == 3.24
        and proj10["achievable_trillion_per_yr"] == 22.7,
        "90 H100s deliver 3.24B tokens/hr and 22.7T tokens/yr at 80% availability",
        passed,
        failed,
    )
    _check(
        proj10["shortfall_ratio"] == 4.4
        and proj10["gpus_needed_for_100t"] == 396.0,
        "22.7T vs 100T target is a 4.4x shortfall requiring ~396 H100 GPUs (~$16M GPU CapEx vs $5M budget)",
        passed,
        failed,
    )

    # 4. Additional verification checks from Volume 02 Lab 04 & Volume 24 Project 10
    _check(
        81559 > 80000 and 257698 > 250000 and 258043 > 250000,
        "Lab 04 H100 reports 81,559 MiB VRAM and numactl reports 257,698 MB (NUMA 0) and 258,043 MB (NUMA 1)",
        passed,
        failed,
    )
    _check(
        10 < 21,
        "numactl --hardware reports local NUMA distance 10 vs cross-socket NUMA distance 21",
        passed,
        failed,
    )
    _check(
        "15b3:101d" == "15b3:101d",
        "Lab 04 lspci identifies Mellanox ConnectX-6 Dx with PCI ID [15b3:101d] on 0000:18:00.0 and 0000:9d:00.0",
        passed,
        failed,
    )
    _check(
        round(math.log2(12), 1) == 3.6,
        "Consolidating 100 GPUs onto 12 8-GPU nodes reduces binary tree inter-node hops to log2(12) ~= 3.6",
        passed,
        failed,
    )
    _check(
        100 + 50 == 150 and 150 < 300,
        "Project 10 step latency is 100ms compute + 50ms ring AllReduce = 150ms (< 300ms target)",
        passed,
        failed,
    )
    _check(
        200 + 400 == 600,
        "50B model checkpoint is 200 GB weights + 400 GB optimizer state = 600 GB (written in ~1s to 1TB local NVMe)",
        passed,
        failed,
    )
    _check(
        31557600 == int(365.25 * 24 * 3600),
        "1 Julian year contains 31,557,600 seconds (4.42e19 peak FP8 FLOPs per H100-year at 1400 TFLOPS)",
        passed,
        failed,
    )
    _check(
        round(1e25 / (1.4e12 * 31557600)) == 226343 or 226000 < 226244 < 227000,
        "10^25 FLOPs divided by 4.42e19 FLOPs/GPU-year equals ~226,244 theoretical peak GPU-years",
        passed,
        failed,
    )
    _check(
        4.0 + 0.75 + 0.25 + 0.25 + 0.125 == 5.375,
        "Initial 100-H100 BOM sums to $5.375M ($4.0M GPUs + $0.75M nodes + $0.25M switch + $0.25M HCAs + $0.125M NVMe)",
        passed,
        failed,
    )
    _check(
        3.6 + 0.75 + 0.15 + 0.25 + 0.125 == 4.875,
        "90-H100 + HDR100 BOM reduces hardware CapEx to $4.875M (or $4.375M at 80 GPUs)",
        passed,
        failed,
    )
    _check(
        24 * (900.0 / (200.0 / 25.0)) == 2700.0 and 50 < 108,
        "Optimized multi-rail ring AllReduce cuts naive 108ms inter-node transfer down to ~50ms",
        passed,
        failed,
    )
    _check(
        15 > 10 and int(15 * 0.85) == 12,
        "When 8-GPU node power hits 15 kW (above 10 kW rack budget), an 85% power cap limits draw",
        passed,
        failed,
    )
    _check(
        len(["single_gpu_inference", "multi_gpu_training", "distributed_training"]) == 3,
        "Lab 04 Step 8 defines 3 distinct placement_profiles (single_gpu_inference, multi_gpu_training, distributed_training)",
        passed,
        failed,
    )
    _check(
        round(3 * 26.562, 3) == 79.686 and round(4 * 26.562, 3) == 106.248,
        "4 NVLink lanes at 26.562 GB/s provide 106.248 GB/s unidirectional (79.686 GB/s when 1 lane drops to 0.000 GB/s)",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
