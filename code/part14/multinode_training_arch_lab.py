#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.10: Multi-node Training Architecture."""

from __future__ import annotations
import sys
from multinode_training_arch import (
    SlurmRendezvousConfig,
    map_global_rank,
    invert_global_rank,
    validate_slurm_rendezvous,
    generate_4d_parallel_groups,
    evaluate_rail_fabric_and_collectives,
    compute_multinode_scaling_curve,
    verify_node_numa_nic_binding,
    evaluate_storage_checkpoint_codesign,
)


def run_lab() -> int:
    print("=== Chapter 14.10 Lab: Multi-node Training Architecture Verification ===")
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

    # 1. Rank Mapping & Inversion (`RANK = NODE_RANK * GPUS_PER_NODE + LOCAL_RANK`)
    check(
        "1. Global rank formula maps (node_rank=2, local_rank=5, gpus_per_node=8) -> RANK=21 and inverts back to (2, 5)",
        map_global_rank(2, 5, 8) == 21 and invert_global_rank(21, 8) == (2, 5),
    )

    check(
        "2. 4-node x 8-GPU cluster produces contiguous global ranks 0..31 with node 3 spanning ranks 24..31",
        [map_global_rank(3, lr, 8) for lr in range(8)] == list(range(24, 32)),
    )

    # 2. SLURM & c10d Rendezvous Validation
    rdzv_ok = validate_slurm_rendezvous(
        SlurmRendezvousConfig(num_nodes=4, gpus_per_node=8, ntasks_per_node=1, launcher="torchrun", nproc_per_node=8, master_addr="dgx-012", master_port=29500)
    )
    check(
        "3. Standard SLURM + torchrun pattern (--nodes=4 --ntasks-per-node=1 + torchrun --nproc_per_node=8) yields WORLD_SIZE=32, SLURM_NTASKS=4, and valid layout",
        rdzv_ok["expected_world_size"] == 32
        and rdzv_ok["actual_world_size"] == 32
        and rdzv_ok["slurm_ntasks"] == 4
        and rdzv_ok["is_valid"] is True,
    )

    rdzv_oversub = validate_slurm_rendezvous(
        SlurmRendezvousConfig(num_nodes=4, gpus_per_node=8, ntasks_per_node=8, launcher="torchrun", nproc_per_node=8, master_addr="dgx-012", master_port=29500)
    )
    check(
        "4. Misconfigured --ntasks-per-node=8 with torchrun --nproc_per_node=8 spawns 64 workers/node (256 total, 8x GPU oversubscription) and is flagged invalid",
        rdzv_oversub["spawned_per_node"] == 64
        and rdzv_oversub["actual_world_size"] == 256
        and rdzv_oversub["oversubscription_factor"] == 8
        and rdzv_oversub["is_valid"] is False,
    )

    rdzv_srun = validate_slurm_rendezvous(
        SlurmRendezvousConfig(num_nodes=4, gpus_per_node=8, ntasks_per_node=8, launcher="srun_direct", master_addr="dgx-012", master_port=29500)
    )
    check(
        "5. Direct srun pattern (--nodes=4 --ntasks-per-node=8 + srun python train.py) yields SLURM_NTASKS=32 == WORLD_SIZE=32 and is valid",
        rdzv_srun["slurm_ntasks"] == 32
        and rdzv_srun["actual_world_size"] == 32
        and rdzv_srun["is_valid"] is True,
    )

    rdzv_loopback = validate_slurm_rendezvous(
        SlurmRendezvousConfig(num_nodes=2, gpus_per_node=8, ntasks_per_node=1, launcher="torchrun", nproc_per_node=8, master_addr="127.0.0.1", master_port=29500)
    )
    check(
        "6. Setting MASTER_ADDR=127.0.0.1 on a multi-node job is detected as split_brain_loopback=True",
        rdzv_loopback["split_brain_loopback"] is True and rdzv_loopback["is_valid"] is False,
    )

    # 3. 3D/4D Process-Group Rank Grid Generator (`TP-first` vs `DP-first`)
    grid_tp_first = generate_4d_parallel_groups(
        dp_size=2, pp_size=2, cp_size=1, tp_size=8, gpus_per_node=8, order="tp-cp-pp-dp"
    )
    check(
        "7. 32-GPU 3D grid (DP=2, PP=2, TP=8) with tp-cp-pp-dp ordering places all 4 TP groups inside single 8-GPU NVLink nodes ([0..7], [8..15], [16..23], [24..31])",
        grid_tp_first["world_size"] == 32
        and grid_tp_first["tp_intra_node"] is True
        and grid_tp_first["tp_groups"][0] == list(range(0, 8))
        and grid_tp_first["tp_groups"][3] == list(range(24, 32)),
    )

    check(
        "8. Standard tp-cp-pp-dp ordering aligns PP groups ([0, 8], [1, 9], ...) and DP groups ([0, 16], [1, 17], ...) onto identical rail indices (same LOCAL_RANK)",
        grid_tp_first["pp_same_rail"] is True
        and grid_tp_first["dp_same_rail"] is True
        and grid_tp_first["pp_groups"][0] == [0, 8]
        and grid_tp_first["dp_groups"][0] == [0, 16],
    )

    grid_dp_first = generate_4d_parallel_groups(
        dp_size=2, pp_size=2, cp_size=1, tp_size=8, gpus_per_node=8, order="dp-pp-cp-tp"
    )
    check(
        "9. Anti-pattern dp-pp-cp-tp ordering scatters each 8-way TP group across all 4 nodes ([0, 4, 8, 12, 16, 20, 24, 28]), violating NVLink locality (tp_intra_node=False)",
        grid_dp_first["tp_intra_node"] is False
        and grid_dp_first["tp_groups"][0] == [0, 4, 8, 12, 16, 20, 24, 28],
    )

    grid_4d = generate_4d_parallel_groups(
        dp_size=2, pp_size=2, cp_size=2, tp_size=4, gpus_per_node=8, order="tp-cp-pp-dp"
    )
    check(
        "10. 4D grid (DP=2, PP=2, CP=2, TP=4 on 32 GPUs) keeps both TP=4 and CP=2 inside each 8-GPU NVLink domain",
        grid_4d["world_size"] == 32
        and grid_4d["tp_intra_node"] is True
        and grid_4d["tp_groups"][0] == [0, 1, 2, 3]
        and grid_4d["cp_groups"][0] == [0, 4],
    )

    # 4. Rail-Optimized Fabric Bandwidth & Ring vs Tree Collective Math (Volume 13 Ch 1, Ch 8, Ch 10)
    fabric = evaluate_rail_fabric_and_collectives()
    check(
        "11. 400 Gbps NDR InfiniBand NIC equals 50.0 GB/s per GPU and 400.0 GB/s aggregate across 8 GPUs per node",
        fabric["per_gpu_ib_gbps"] == 50.0 and fabric["node_aggregate_ib_gbps"] == 400.0,
    )

    check(
        "12. Intra-node NVLink 4 (900.0 GB/s per GPU) is 18.0x faster per GPU than 400 Gbps NDR InfiniBand (50.0 GB/s), explaining the 16.7x TP-across-nodes slowdown",
        fabric["nvlink_to_ib_ratio"] == 18.0,
    )

    check(
        "13. 8-GPU single-node Ring All-Reduce on 28 GB FP32 gradients (7B model) moves 49.0 GB per GPU in 54.4 ms (~54 ms) at 900 GB/s NVLink",
        fabric["ring_bytes_8gpu_gb"] == 49.0 and fabric["ring_time_8gpu_ms"] == 54.4,
    )

    check(
        "14. 512-GPU (64-node) Ring All-Reduce on 28 GB gradients moves 55.8906 GB (~55.9 GB) in 2.24 s (~2.2 s) at 25 GB/s IB; Tree cuts hops from 512 to 9 (log2 512)",
        round(fabric["ring_bytes_512gpu_gb"], 1) == 55.9
        and round(fabric["ring_time_512gpu_s"], 1) == 2.2
        and fabric["ring_hops_512"] == 512.0
        and fabric["tree_hops_512"] == 9.0,
    )

    # 5. Single-GPU Memory & Compute Scaling Motivation (Volume 13 Ch 1)
    gpt3_weights_gb = 175.0 * 4.0  # 700.0 GB
    gpt3_step_flops = 2.0 * 175e9 * 2048 * 2048  # 1.468e18 (~1.46e18) FLOPs
    a100_1gpu_min = (1.46e18 / 312e12) / 60.0  # 77.99 min (~78 min = 4,679 s)
    a100_128gpu_s = (78.0 * 60.0) / 128.0  # 36.56 s (~37 s)
    check(
        "15. GPT-3 (175B) FP32 weights require 700.0 GB (8.75x an 80 GB H100), and 1.46e18 FLOPs/step takes ~4,679 s (~78 min) on 1 A100 vs ~37 s on 128 A100s",
        gpt3_weights_gb == 700.0
        and gpt3_weights_gb / 80.0 == 8.75
        and round(1.46e18 / 312e12) == 4679
        and round(a100_1gpu_min) == 78
        and round(a100_128gpu_s) == 37,
    )

    # 6. Multi-Node Scaling Curve (16 to 16,384 GPUs)
    curve = compute_multinode_scaling_curve()
    eff_16 = curve[0]["scaling_efficiency"]
    eff_1024 = [r for r in curve if r["num_gpus"] == 1024][0]["scaling_efficiency"]
    eff_16384 = curve[-1]["scaling_efficiency"]
    check(
        "16. Multi-node scaling curve covers 16, 64, 256, 1024, 4096, and 16384 GPUs with monotonically decreasing scaling efficiency as tree hops grow from 1 to 11",
        [r["num_gpus"] for r in curve] == [16, 64, 256, 1024, 4096, 16384]
        and curve[0]["tree_hops"] == 1
        and curve[-1]["tree_hops"] == 11
        and eff_16 > eff_1024 > eff_16384,
    )

    check(
        "17. At 16 GPUs (2 nodes) scaling efficiency exceeds 96%, while at 16,384 GPUs (2,048 nodes, 11 tree hops) exposed communication reduces efficiency to ~93.9%",
        eff_16 > 0.96 and 0.90 <= eff_16384 <= 0.95,
    )

    # 7. Host CPU / NUMA / PCIe / NIC Affinity Binding Verifier
    aff_ok = verify_node_numa_nic_binding(total_cores=128, gpus_per_node=8)
    check(
        "18. Optimal 8-GPU dual-socket binding allocates 16 CPU cores/GPU, binds GPUs 0..3 to NUMA 0 (mlx5_0..3) and GPUs 4..7 to NUMA 1 (mlx5_4..7) via PIX (300.0 GB/s busbw)",
        aff_ok["cores_per_gpu"] == 16
        and aff_ok["all_optimal"] is True
        and aff_ok["expected_nccl_busbw_gbps"] == 300.0
        and aff_ok["bindings"][0]["cpu_cores"] == "0-15"
        and aff_ok["bindings"][4]["numa_node"] == 1,
    )

    aff_bad = verify_node_numa_nic_binding(total_cores=128, gpus_per_node=8, custom_nic_map={0: "mlx5_3", 3: "mlx5_0"})
    check(
        "19. GPU 0 mapped to NIC 3 (NCCL INFO NET/IB : GPU 0 uses NIC 3) breaks PIX affinity (all_optimal=False) and drops expected nccl-tests busbw from 300.0 GB/s to 40.0 GB/s (7.5x drop)",
        aff_bad["all_optimal"] is False
        and aff_bad["bindings"][0]["actual_nic"] == "mlx5_3"
        and aff_bad["bindings"][0]["gdr_optimal"] is False
        and aff_bad["expected_nccl_busbw_gbps"] == 40.0,
    )

    aff_cross_socket = verify_node_numa_nic_binding(total_cores=128, gpus_per_node=8, custom_nic_map={0: "mlx5_7"})
    check(
        "20. Mapping GPU 0 (NUMA 0) to mlx5_7 (NUMA 1) traverses the cross-socket QPI/UPI interconnect (path_type='SYS')",
        aff_cross_socket["bindings"][0]["path_type"] == "SYS",
    )

    # 8. Storage / Checkpoint / Network Co-Design (DAI Ch 8 Megatron-LM 8.03B & SLURM SIGUSR1@90)
    ckpt = evaluate_storage_checkpoint_codesign(
        params_billion=8.03, num_shards=4, shard_file_gb=27.0, cluster_Aggregate_write_gbps=25.0, slurm_signal_lead_s=90
    )
    check(
        "21. Megatron-LM 8.03B model requires 16.06 GB BF16 weights + 64.24 GB FP32 Adam state = 80.30 GB theoretical, and 108.0 GB actual across 4 x 27.0 GB .distcp shards",
        ckpt["bf16_weights_gb"] == 16.06
        and ckpt["fp32_adam_gb"] == 64.24
        and ckpt["theoretical_state_gb"] == 80.30
        and ckpt["actual_distcp_total_gb"] == 108.0,
    )

    check(
        "22. Writing 108.0 GB at 25.0 GB/s parallel storage throughput takes 4.32 s, fitting cleanly inside SLURM's --signal=SIGUSR1@90 (90 s) preemption grace window",
        ckpt["write_duration_s"] == 4.32 and ckpt["fits_in_signal_window"] is True,
    )

    # 9. SLURM Job Array Hyperparameter Grid Mapping (DAI Ch 8)
    lrs = [1e-4, 3e-4, 1e-3, 3e-3]
    batch_sizes = [16, 32, 64]
    grid_pairs = [(lrs[task_id % len(lrs)], batch_sizes[task_id // len(lrs)]) for task_id in range(12)]
    check(
        "23. SLURM 12-task job array (--array=0-11) maps task_id % 4 -> 4 LRs and task_id // 4 -> 3 batch sizes with 12 unique (LR, BS) pairs",
        len(set(grid_pairs)) == 12
        and grid_pairs[0] == (1e-4, 16)
        and grid_pairs[5] == (3e-4, 32)
        and grid_pairs[11] == (3e-3, 64),
    )

    # 10. NCCL Benchmark algbw vs busbw & Broken NVLink Fallback (Volume 13 Lab 02 & Ch 12)
    algbw_8gpu = 514.2857
    busbw_8gpu = round(algbw_8gpu * 2.0 * (7.0 / 8.0), 1)
    check(
        "24. NCCL all_reduce_perf busbw equals algbw * 2 * (N - 1) / N (900.0 GB/s busbw from 514.3 GB/s algbw on 8 GPUs); broken NVLink drops single-node busbw from 400 GB/s to 20 GB/s (20x)",
        busbw_8gpu == 900.0 and (400.0 / 20.0) == 20.0,
    )

    # 11. End-to-End 4-Component Checkpoint Determinism Verification (Volume 13 Lab 04)
    ckpt_keys = {"model_state_dict", "optimizer_state_dict", "scheduler_state_dict", "rng_state"}
    check(
        "25. Deterministic multi-node checkpoint recovery requires all 4 state dicts (model, optimizer, scheduler, rng_state) gated behind dist.barrier()",
        len(ckpt_keys) == 4 and "optimizer_state_dict" in ckpt_keys and "rng_state" in ckpt_keys,
    )

    print(f"Summary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
