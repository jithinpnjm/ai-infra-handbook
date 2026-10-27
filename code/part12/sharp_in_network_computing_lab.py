"""Self-checking verification lab for Chapter 12.20: SHARP and In-Network Computing.

Run with:
    python3 -B code/part12/sharp_in_network_computing_lab.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sharp_in_network_computing import (
    GB300_SUPERPOD_SCALE_TABLE,
    SHARP_HARDWARE_GENERATIONS,
    UEC_INC_VS_XCCL_MATRIX,
    SharpAggregationManagerSim,
    analyze_fp32_reduction_determinism,
    compare_ring_vs_sharp_volume,
    compute_hierarchical_nvls_ib_sharp,
    compute_overlapped_nvls_exchange,
    validate_sharp_nccl_config,
)


def run_lab() -> int:
    passed = 0
    failed = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name} :: {detail}")

    print("=== Chapter 12.20 Lab: SHARP and In-Network Computing ===")

    # 1. Ring vs NVLS / SHARP on 8 GPUs (800 MB tensor -> 700 MB Ring RS rx vs 100 MB SHARP RS rx, 7x ratio)
    cmp_8 = compare_ring_vs_sharp_volume(
        num_ranks=8,
        tensor_bytes=800_000_000,
        per_rank_link_gb_s=50.0,
    )
    check(
        "1. 8-GPU ReduceScatter: Ring receives 700 MB (B*(N-1)/N) vs SHARP/NVLS 100 MB (B/N)",
        cmp_8.ring_reduce_scatter_rx_bytes == 700_000_000.0
        and cmp_8.sharp_reduce_scatter_rx_bytes == 100_000_000.0,
        f"got {cmp_8}",
    )
    check(
        "2. 8-GPU ReduceScatter and AllGather volume reduction factor is (N - 1) = 7.0x",
        cmp_8.reduce_scatter_volume_ratio == 7.0 and cmp_8.all_gather_volume_ratio == 7.0,
        f"got {cmp_8}",
    )
    check(
        "3. 8-GPU Ring AllReduce transfers 2*(N-1)/N * B = 1,400 MB unidirectional (14 steps vs 6 tree steps)",
        cmp_8.ring_allreduce_tx_Plus_rx_bytes == 1_400_000_000.0
        and cmp_8.sharp_allreduce_tx_plus_rx_bytes == 1_600_000_000.0
        and cmp_8.ring_steps == 14
        and cmp_8.tree_steps == 6,
        f"got {cmp_8}",
    )

    # 2. Ring vs NVLS on 72-GPU GB200/GB300 NVL72 rack (720 MB tensor -> 710 MB vs 10 MB, 71x ratio)
    cmp_72 = compare_ring_vs_sharp_volume(
        num_ranks=72,
        tensor_bytes=720_000_000,
        per_rank_link_gb_s=900.0,  # 900 GB/s unidirectional (1.8 TB/s bidirectional NVLink 5)
    )
    check(
        "4. 72-GPU NVL72 ReduceScatter: Ring receives 710 MB vs NVLS 10 MB (71.0x volume reduction)",
        cmp_72.ring_reduce_scatter_rx_bytes == 710_000_000.0
        and cmp_72.sharp_reduce_scatter_rx_bytes == 10_000_000.0
        and cmp_72.reduce_scatter_volume_ratio == 71.0,
        f"got {cmp_72}",
    )
    check(
        "5. 72-GPU NVL72 Ring requires 142 steps vs 14 tree steps and 1,420 MB Ring unidirectional bytes",
        cmp_72.ring_steps == 142
        and cmp_72.tree_steps == 14
        and cmp_72.ring_allreduce_tx_Plus_rx_bytes == 1_420_000_000.0,
        f"got {cmp_72}",
    )

    # 3. 32-node InfiniBand SHARP AllReduce (1,024 MB = 1.024 GB on 400G NDR = 50 GB/s)
    cmp_32 = compare_ring_vs_sharp_volume(
        num_ranks=32,
        tensor_bytes=1_024_000_000,
        per_rank_link_gb_s=50.0,
        ring_hop_latency_us=2.0,
        sharp_tree_latency_us=3.0,
    )
    check(
        "6. 32-node IB ReduceScatter: Ring receives 992 MB vs SHARP 32 MB (31.0x volume reduction)",
        cmp_32.ring_reduce_scatter_rx_bytes == 992_000_000.0
        and cmp_32.sharp_reduce_scatter_rx_bytes == 32_000_000.0
        and cmp_32.reduce_scatter_volume_ratio == 31.0,
        f"got {cmp_32}",
    )
    check(
        "7. 32-node IB AllReduce: Ring transfers 1,984 MB across 62 steps vs SHARP 1,024 MB per direction across 10 steps (~1.94x bandwidth + latency speedup)",
        cmp_32.ring_allreduce_tx_Plus_rx_bytes == 1_984_000_000.0
        and cmp_32.ring_steps == 62
        and cmp_32.tree_steps == 10
        and 1.9 <= cmp_32.speedup_factor <= 2.1,
        f"got {cmp_32}",
    )

    # 4. Overlapped NVLS multicast AllGather + in-network ReduceScatter (~1/2 wall time)
    ovl = compute_overlapped_nvls_exchange(all_gather_ms=8.0, reduce_scatter_ms=8.0)
    check(
        "8. Overlapping NVLS multicast AllGather (8 ms) with in-network ReduceScatter (8 ms) cuts wall time from 16.0 ms to 8.0 ms (50.0% / ~1/2 reduction)",
        ovl.serial_total_ms == 16.0
        and ovl.overlapped_nvls_ms == 8.0
        and ovl.wall_time_reduction_fraction == 0.5,
        f"got {ovl}",
    )

    # 5. Two-level Hierarchical NVLS + IB SHARP (32 nodes x 8 GPUs = 256 GPUs, 1,024 MB tensor)
    hier_256 = compute_hierarchical_nvls_ib_sharp(
        num_domains=32,
        gpus_per_domain=8,
        tensor_bytes=1_024_000_000,
    )
    check(
        "9. Hierarchical 32x8 (256-GPU) NVLS+SHARP: intra-node NVLS RS receives 128 MB/GPU and inter-node IB SHARP injects 1,024 MB/node vs 1,984 MB/node in hierarchical Ring",
        hier_256.total_gpus == 256
        and hier_256.intra_domain_nvls_rs_rx_bytes_per_gpu == 128_000_000.0
        and hier_256.hier_sharp_inter_domain_bytes_per_domain == 1_024_000_000.0
        and hier_256.hier_ring_inter_domain_bytes_per_domain == 1_984_000_000.0
        and hier_256.ring_vs_sharp_inter_domain_ratio == 1.9375,
        f"got {hier_256}",
    )

    # 6. Two-level Hierarchical NVLS + IB SHARP across 16 NVL72 racks (16 x 72 = 1,152 GPUs = 2 SUs, 720 MB tensor)
    hier_nvl72 = compute_hierarchical_nvls_ib_sharp(
        num_domains=16,
        gpus_per_domain=72,
        tensor_bytes=720_000_000,
    )
    check(
        "10. Hierarchical 16x72 NVL72 (1,152 GPUs): intra-rack NVLS RS receives 10 MB/GPU and inter-rack IB SHARP sends 720 MB/rack vs 1,350 MB/rack in inter-rack Ring (1.875x ratio)",
        hier_nvl72.total_gpus == 1152
        and hier_nvl72.intra_domain_nvls_rs_rx_bytes_per_gpu == 10_000_000.0
        and hier_nvl72.hier_sharp_inter_domain_bytes_per_domain == 720_000_000.0
        and hier_nvl72.hier_ring_inter_domain_bytes_per_domain == 1_350_000_000.0
        and hier_nvl72.ring_vs_sharp_inter_domain_ratio == 1.875,
        f"got {hier_nvl72}",
    )

    # 7. Hardware generations & GB300 SuperPOD Quantum-X800 Q3400-RD scale-out table
    check(
        "11. SHARPv1 (100G EDR, 36p, no FP16/BF16) vs SHARPv2 (200G HDR, 40p, adds FP16/BF16) vs SHARPv3 (400G NDR, 64p) vs SHARPv4 (800G XDR Q3400-RD, 144p, adds FP8)",
        SHARP_HARDWARE_GENERATIONS["SHARPv1"].port_rate_gbps == 100
        and "FP16" not in SHARP_HARDWARE_GENERATIONS["SHARPv1"].supported_dtypes
        and SHARP_HARDWARE_GENERATIONS["SHARPv2"].port_rate_gbps == 200
        and "BF16" in SHARP_HARDWARE_GENERATIONS["SHARPv2"].supported_dtypes
        and SHARP_HARDWARE_GENERATIONS["SHARPv3"].port_rate_gbps == 400
        and SHARP_HARDWARE_GENERATIONS["SHARPv3"].switch_radix_ports == 64
        and SHARP_HARDWARE_GENERATIONS["SHARPv4"].port_rate_gbps == 800
        and SHARP_HARDWARE_GENERATIONS["SHARPv4"].switch_radix_ports == 144,
        "SHARP generation mismatch",
    )
    check(
        "12. NVSwitch Gen 4 (NVL72) delivers 7,200 Gbps (1.8 TB/s bidir) per GPU across 144-port switch trays with FP4/FP8/FP16/BF16/FP32 NVLS support",
        SHARP_HARDWARE_GENERATIONS["NVLS_Gen4"].port_rate_gbps == 7200
        and SHARP_HARDWARE_GENERATIONS["NVLS_Gen4"].switch_radix_ports == 144
        and "FP4" in SHARP_HARDWARE_GENERATIONS["NVLS_Gen4"].supported_dtypes,
        f"got {SHARP_HARDWARE_GENERATIONS['NVLS_Gen4']}",
    )
    check(
        "13. DGX GB300 SuperPOD Quantum-X800 Q3400-RD 2-layer fabric scales from 2 SUs (1,152 GPUs, 16 leaves, 8 spines) to 16 SUs (9,216 GPUs, 128 leaves, 72 spines)",
        GB300_SUPERPOD_SCALE_TABLE[2].num_gpus == 1152
        and GB300_SUPERPOD_SCALE_TABLE[2].ib_leaf_switches_total == 16
        and GB300_SUPERPOD_SCALE_TABLE[2].ib_spine_switches_total == 8
        and GB300_SUPERPOD_SCALE_TABLE[4].num_gpus == 2304
        and GB300_SUPERPOD_SCALE_TABLE[4].ib_spine_switches_total == 18
        and GB300_SUPERPOD_SCALE_TABLE[8].num_gpus == 4608
        and GB300_SUPERPOD_SCALE_TABLE[8].ib_spine_switches_total == 36
        and GB300_SUPERPOD_SCALE_TABLE[16].num_gpus == 9216
        and GB300_SUPERPOD_SCALE_TABLE[16].ib_leaf_switches_total == 128
        and GB300_SUPERPOD_SCALE_TABLE[16].ib_spine_switches_total == 72,
        f"got {GB300_SUPERPOD_SCALE_TABLE}",
    )

    # 8. SHARP Aggregation Manager (sharp_am) tree quota and switch buffer fallback simulator
    am = SharpAggregationManagerSim(max_concurrent_trees=64, max_collective_mb_per_tree=256.0)
    d1 = am.allocate_job_trees(job_id=101, requested_trees=32, message_size_mb=64.0)
    d2 = am.allocate_job_trees(job_id=102, requested_trees=32, message_size_mb=128.0)
    d3_quota_exhausted = am.allocate_job_trees(job_id=103, requested_trees=4, message_size_mb=64.0)
    check(
        "14. sharp_am allocates 32 + 32 = 64 SHARP trees across Jobs 101 and 102 (0 remaining)",
        d1.allocated is True
        and d2.allocated is True
        and d2.remaining_trees == 0
        and d1.mode == "SHARP_COLLNET",
        f"got d1={d1}, d2={d2}",
    )
    check(
        "15. Job 103 requesting 4 trees when 64/64 trees are in use triggers HOST_RING_TREE_FALLBACK",
        d3_quota_exhausted.allocated is False
        and d3_quota_exhausted.mode == "HOST_RING_TREE_FALLBACK"
        and "quota exhausted" in d3_quota_exhausted.reason,
        f"got {d3_quota_exhausted}",
    )
    released = am.release_job_trees(101)
    d4_oversized = am.allocate_job_trees(job_id=104, requested_trees=8, message_size_mb=512.0)
    d5_reclaimed = am.allocate_job_trees(job_id=105, requested_trees=16, message_size_mb=64.0)
    check(
        "16. Collective size 512.0 MB > 256.0 MB switch AN buffer limit falls back to non-SHARP host aggregation",
        d4_oversized.allocated is False
        and d4_oversized.mode == "HOST_RING_TREE_FALLBACK"
        and "exceeds switch AN buffer limit" in d4_oversized.reason,
        f"got {d4_oversized}",
    )
    check(
        "17. Releasing Job 101 frees 32 trees and allows Job 105 (16 trees) to allocate cleanly (16 remaining)",
        released == 32 and d5_reclaimed.allocated is True and d5_reclaimed.remaining_trees == 16,
        f"got released={released}, d5={d5_reclaimed}",
    )

    am_down = SharpAggregationManagerSim(sm_ufm_active=False)
    d_down = am_down.allocate_job_trees(job_id=201, requested_trees=2, message_size_mb=16.0)
    am_daemon_fail = SharpAggregationManagerSim(sharp_daemons_healthy=False)
    d_daemon = am_daemon_fail.allocate_job_trees(job_id=202, requested_trees=2, message_size_mb=16.0)
    check(
        "18. Inactive UFM/SM sharp_am or dead compute-node sharp_daemons triggers immediate fallback",
        d_down.allocated is False
        and "sharp_am control plane is inactive" in d_down.reason
        and d_daemon.allocated is False
        and "sharp_daemons" in d_daemon.reason,
        f"got d_down={d_down}, d_daemon={d_daemon}",
    )

    # 9. IEEE-754 FP32 non-associativity in Ring rank rotations vs deterministic SHARP AN tree
    fp_inputs = [1.0e7, -1.0e7, 1.0, 0.25, 1.0e6, -1.0e6, 0.5, 0.125]
    fp_res = analyze_fp32_reduction_determinism(fp_inputs)
    check(
        "19. IEEE-754 FP32 Ring reduction across 8 rank start offsets produces multiple distinct results (non-associativity)",
        fp_res.ring_unique_outputs >= 2 and fp_res.ring_max_spread > 0.0,
        f"got {fp_res}",
    )
    check(
        "20. Fixed-topology binary SHARP Aggregation Node (AN) tree reduction is bit-repeatable and preserves exact sum 1.875",
        fp_res.sharp_tree_repeatable is True and fp_res.sharp_tree_sum == 1.875,
        f"got {fp_res}",
    )

    # 10. NCCL & OpenMPI HCOLL SHARP / NVLS configuration validation
    cfg_prod = validate_sharp_nccl_config(
        env={
            "NCCL_COLLNET_ENABLE": "1",
            "NCCL_NVLS_ENABLE": "1",
            "NCCL_SHARP_DISABLE": "0",
            "HCOLL_ENABLE_SHARP": "1",
        },
        fabric_type="infiniband",
        has_nvswitch_nvls_hw=True,
        has_sharp_plugin_and_am=True,
        peermem_or_dmabuf_loaded=True,
        all_ranks_registered_buffers=True,
        symmetric_buffer_offsets=True,
    )
    check(
        "21. Production IB + NVSwitch config enables CollNet_IB_SHARP, NVSwitch_NVLS, zero-copy user buffers, and MPI HCOLL SHARP with 0 warnings",
        cfg_prod.ib_sharp_active is True
        and cfg_prod.nvls_active is True
        and cfg_prod.zero_copy_user_buffer_active is True
        and cfg_prod.mpi_hcoll_sharp_active is True
        and cfg_prod.selected_inter_node_path == "CollNet_IB_SHARP"
        and cfg_prod.selected_intra_node_path == "NVSwitch_NVLS"
        and len(cfg_prod.warnings) == 0,
        f"got {cfg_prod}",
    )

    cfg_ab_disable = validate_sharp_nccl_config(
        env={
            "NCCL_COLLNET_ENABLE": "1",
            "NCCL_NVLS_ENABLE": "1",
            "NCCL_SHARP_DISABLE": "1",
            "HCOLL_ENABLE_SHARP": "1",
        },
        fabric_type="infiniband",
    )
    check(
        "22. Setting NCCL_SHARP_DISABLE=1 disables IB SHARP (RDMA_Ring_Tree) while keeping intra-node NVSwitch_NVLS active",
        cfg_ab_disable.ib_sharp_active is False
        and cfg_ab_disable.nvls_active is True
        and cfg_ab_disable.selected_inter_node_path == "RDMA_Ring_Tree"
        and cfg_ab_disable.selected_intra_node_path == "NVSwitch_NVLS",
        f"got {cfg_ab_disable}",
    )

    cfg_spectrum_x = validate_sharp_nccl_config(
        env={"NCCL_COLLNET_ENABLE": "1", "NCCL_NVLS_ENABLE": "1"},
        fabric_type="spectrum-x-ethernet",
    )
    check(
        "23. Spectrum-X Ethernet with NCCL_COLLNET_ENABLE=1 warns that Ethernet switches lack SHARP reduction engines and selects RDMA_Ring_Tree",
        cfg_spectrum_x.ib_sharp_active is False
        and cfg_spectrum_x.selected_inter_node_path == "RDMA_Ring_Tree"
        and any("does not expose switch-resident SHARP" in w for w in cfg_spectrum_x.warnings),
        f"got {cfg_spectrum_x}",
    )

    cfg_no_gdr = validate_sharp_nccl_config(
        env={"NCCL_COLLNET_ENABLE": "1", "NCCL_NVLS_ENABLE": "1"},
        fabric_type="infiniband",
        peermem_or_dmabuf_loaded=False,
    )
    check(
        "24. Missing GPUDirect RDMA (nvidia-peermem / dma-buf) blocks InfiniBand SHARP offload",
        cfg_no_gdr.ib_sharp_active is False
        and any("SHARP requires GDR" in w for w in cfg_no_gdr.warnings),
        f"got {cfg_no_gdr}",
    )

    cfg_asym_buf = validate_sharp_nccl_config(
        env={"NCCL_COLLNET_ENABLE": "1", "NCCL_NVLS_ENABLE": "1"},
        fabric_type="infiniband",
        all_ranks_registered_buffers=True,
        symmetric_buffer_offsets=False,
    )
    check(
        "25. Asymmetric user-buffer head offsets disable zero-copy ncclCommRegister fast path",
        cfg_asym_buf.zero_copy_user_buffer_active is False
        and any("Buffer head offsets differ" in w for w in cfg_asym_buf.warnings),
        f"got {cfg_asym_buf}",
    )

    # 11. UEC In-Network Collectives (INC) vs xCCL architectural matrix
    check(
        "26. UEC INC executes inside network switches (sFEPs) coordinated by INC Manager (gRPC OOB) + Libfabric fi_collective",
        "sFEPs" in UEC_INC_VS_XCCL_MATRIX["Primary execution"][0]
        and "fi_collective" in UEC_INC_VS_XCCL_MATRIX["Integration"][0]
        and "gRPC OOB" in UEC_INC_VS_XCCL_MATRIX["Required infrastructure"][0],
        f"got {UEC_INC_VS_XCCL_MATRIX}",
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_lab())
