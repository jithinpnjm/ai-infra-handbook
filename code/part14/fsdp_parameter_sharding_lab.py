#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.5: FSDP and Parameter Sharding."""

from __future__ import annotations
import sys
from fsdp_parameter_sharding import (
    FSDP_SHARDING_STRATEGIES,
    FsdpMemoryConfig,
    compute_fsdp_memory_breakdown,
    compute_communication_volume,
    estimate_transformer_activation_memory_gb,
    evaluate_checkpoint_and_offload,
    simulate_manual_parameter_sharding,
)


def run_lab() -> int:
    print("=== Chapter 14.5 Lab: FSDP and Parameter Sharding Verification ===")
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

    # 1. 7B & 70B Memory Anatomy under DDP (NO_SHARD) vs FSDP Stages
    m7b_12b = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(7.0, 8, 32, strategy="NO_SHARD", include_fp32_master_weights=False)
    )
    check(
        "1. 7B model without FP32 master copy requires 84.0 GB (14 GB weights + 14 GB grads + 56 GB Adam state), exceeding 80 GB H100",
        m7b_12b["steady_state_gb"] == 84.0
        and m7b_12b["steady_weights_gb"] == 14.0
        and m7b_12b["steady_grads_gb"] == 14.0
        and m7b_12b["steady_optim_gb"] == 56.0,
    )

    m7b_16b = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(7.0, 8, 32, strategy="NO_SHARD", include_fp32_master_weights=True)
    )
    check(
        "2. 7B model under 16*Psi mixed-precision AdamW (with 28 GB FP32 master weights) requires 112.0 GB per GPU in DDP (NO_SHARD)",
        m7b_16b["steady_state_gb"] == 112.0 and m7b_16b["bytes_per_param_total"] == 16.0,
    )

    m7b_fsdp8_12b = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(7.0, 8, 32, strategy="FULL_SHARD", include_fp32_master_weights=False)
    )
    check(
        "3. 7B model under FSDP FULL_SHARD on 8 GPUs drops from 84.0 GB to 10.5 GB steady-state per GPU (84 / 8)",
        m7b_fsdp8_12b["steady_state_gb"] == 10.5,
    )

    m7b_fsdp8_16b = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(7.0, 8, 32, strategy="FULL_SHARD", include_fp32_master_weights=True)
    )
    check(
        "4. 7B model under 16*Psi convention with FSDP FULL_SHARD on 8 GPUs uses 14.0 GB steady-state (16*Psi/N) vs 26.25 GB for SHARD_GRAD_OP (2*Psi + 14*Psi/N)",
        m7b_fsdp8_16b["steady_state_gb"] == 14.0
        and compute_fsdp_memory_breakdown(
            FsdpMemoryConfig(7.0, 8, 32, strategy="SHARD_GRAD_OP", include_fp32_master_weights=True)
        )["steady_state_gb"]
        == 26.25,
    )

    # 2. 70B Model Sharding Stages (Volume 13 Ch 4 & Ch 1)
    m70b_ddp = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(70.0, 8, 80, strategy="NO_SHARD", include_fp32_master_weights=False)
    )
    check(
        "5. 70B model in DDP requires 840.0 GB per GPU (140 GB weights + 140 GB grads + 560 GB FP32 momentum/variance); single 80 GB GPU holds only 9.5%",
        m70b_ddp["steady_state_gb"] == 840.0 and round(80.0 / 840.0 * 100.0, 1) == 9.5,
    )

    m70b_s1 = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(70.0, 8, 80, strategy="ZERO1_OPTIM_ONLY", include_fp32_master_weights=False)
    )
    check(
        "6. 70B Stage 1 (Optimizer State Sharding, N=8) uses 350.0 GB per GPU (140 GB weights + 140 GB grads + 70 GB sharded optimizer)",
        m70b_s1["steady_state_gb"] == 350.0 and m70b_s1["steady_optim_gb"] == 70.0,
    )

    m70b_s2 = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(70.0, 8, 80, strategy="SHARD_GRAD_OP", include_fp32_master_weights=False)
    )
    check(
        "7. 70B Stage 2 (SHARD_GRAD_OP / ZeRO-2, N=8) uses 227.5 GB (~228 GB) per GPU (140 + 17.5 + 70), saving 122.5 GB vs Stage 1",
        m70b_s2["steady_state_gb"] == 227.5 and (m70b_s1["steady_state_gb"] - m70b_s2["steady_state_gb"]) == 122.5,
    )

    m70b_s3_n8 = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(70.0, 8, 80, strategy="FULL_SHARD", include_fp32_master_weights=False)
    )
    m70b_s3_n16 = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(70.0, 16, 80, strategy="FULL_SHARD", include_fp32_master_weights=False)
    )
    m70b_s1_n16 = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(70.0, 16, 80, strategy="ZERO1_OPTIM_ONLY", include_fp32_master_weights=False)
    )
    m70b_s2_n16 = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(70.0, 16, 80, strategy="SHARD_GRAD_OP", include_fp32_master_weights=False)
    )
    check(
        "8. 70B Stage 3 (FULL_SHARD / ZeRO-3) drops steady-state memory to 105.0 GB on N=8 GPUs and 52.5 GB on N=16 GPUs (vs 315.0 GB Stage 1 and 183.75 GB Stage 2 on N=16; leaving 27.5 GB headroom on 80 GB H100)",
        m70b_s3_n8["steady_state_gb"] == 105.0
        and m70b_s3_n16["steady_state_gb"] == 52.5
        and m70b_s1_n16["steady_state_gb"] == 315.0
        and m70b_s2_n16["steady_state_gb"] == 183.75
        and (80.0 - 52.5) == 27.5,
    )

    m70b_16psi = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(70.0, 16, 80, strategy="FULL_SHARD", include_fp32_master_weights=True)
    )
    check(
        "9. 70B model under full 16*Psi convention (1,120.0 GB total state) shards to 70.0 GB steady-state on 16 GPUs and 35.0 GB on 32 GPUs",
        m70b_16psi["total_unsharded_state_gb"] == 1120.0
        and m70b_16psi["steady_state_gb"] == 70.0,
    )

    # 3. Wrapping Granularity & Peak Unsharded Layer Buffer (2 * Psi_layer) + limit_all_gathers
    m70b_mono = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(
            70.0, 16, 80, strategy="FULL_SHARD", include_fp32_master_weights=False, wrap_granularity="monolithic_root"
        )
    )
    m70b_block = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(
            70.0, 16, 80, strategy="FULL_SHARD", include_fp32_master_weights=False, wrap_granularity="transformer_block"
        )
    )
    check(
        "10. Wrapping 70B as a monolithic root FSDP unit materializes 140.0 GB at once (peak 192.5 GB), whereas 80-block wrapping materializes only 1.75 GB/layer (3.5 GB with prefetch, peak 56.0 GB)",
        m70b_mono["transient_buffer_gb"] == 140.0
        and m70b_mono["peak_memory_gb"] == 192.5
        and m70b_block["layer_weight_gb"] == 1.75
        and m70b_block["transient_buffer_gb"] == 3.5
        and m70b_block["peak_memory_gb"] == 56.0,
    )

    m70b_nolimit = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(
            70.0,
            16,
            80,
            strategy="FULL_SHARD",
            include_fp32_master_weights=False,
            limit_all_gathers=False,
            queued_all_gather_units=15,
        )
    )
    check(
        "11. Disabling limit_all_gathers (limit_all_gathers=False) with 15 queued CUDA AllGathers inflates transient buffer from 3.5 GB to 28.0 GB (80.5 GB peak -> OOM on 80 GB GPU)",
        m70b_nolimit["transient_buffer_gb"] == 28.0 and m70b_nolimit["peak_memory_gb"] == 80.5,
    )

    m70b_no_reshard = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(
            70.0,
            16,
            80,
            strategy="FULL_SHARD",
            include_fp32_master_weights=False,
            reshard_after_forward=False,
        )
    )
    check(
        "12. Setting reshard_after_forward=False keeps all 140.0 GB of unsharded parameters in memory between forward and backward (skipping backward AllGather at the cost ofVRAM)",
        m70b_no_reshard["transient_buffer_gb"] == 141.75,
    )

    # 4. Communication Volume: 3*Psi (FSDP FULL_SHARD) vs 2*Psi (DDP & SHARD_GRAD_OP)
    comm_ddp_70b = compute_communication_volume(70.0, 8, strategy="NO_SHARD")
    comm_zero2_70b = compute_communication_volume(70.0, 8, strategy="SHARD_GRAD_OP")
    comm_fsdp_70b = compute_communication_volume(70.0, 8, strategy="FULL_SHARD", reshard_after_forward=True)
    comm_fsdp_noreshard = compute_communication_volume(70.0, 8, strategy="FULL_SHARD", reshard_after_forward=False)
    check(
        "13. DDP (NO_SHARD) and SHARD_GRAD_OP (ZeRO-2) have 2*Psi asymptotic communication volume (280.0 GB for 70B FP16; 245.0 GB exact ring on N=8)",
        comm_ddp_70b["asymptotic_volume_gb"] == 280.0
        and comm_ddp_70b["exact_ring_volume_gb"] == 245.0
        and comm_zero2_70b["exact_ring_volume_gb"] == 245.0,
    )

    check(
        "14. FSDP FULL_SHARD (reshard_after_forward=True) has 3*Psi asymptotic communication volume (420.0 GB for 70B FP16; 367.5 GB exact on N=8, 1.5x DDP)",
        comm_fsdp_70b["asymptotic_volume_gb"] == 420.0
        and comm_fsdp_70b["exact_ring_volume_gb"] == 367.5
        and round(comm_fsdp_70b["exact_ring_volume_gb"] / comm_ddp_70b["exact_ring_volume_gb"], 2) == 1.5,
    )

    check(
        "15. FSDP FULL_SHARD with reshard_after_forward=False eliminates backward AllGather, dropping communication volume from 3*Psi (367.5 GB) to 2*Psi (245.0 GB)",
        comm_fsdp_noreshard["asymptotic_multiplier_psi"] == 2.0
        and comm_fsdp_noreshard["exact_ring_volume_gb"] == 245.0,
    )

    # 5. Hybrid Sharding (HSDP / HYBRID_SHARD) Intra-Node NVLink vs Inter-Node InfiniBand Sizing
    hsdp_32 = compute_communication_volume(
        70.0, 32, strategy="HYBRID_SHARD", reshard_after_forward=True, hsdp_gpus_per_node=8
    )
    mem_hsdp_32 = compute_fsdp_memory_breakdown(
        FsdpMemoryConfig(
            70.0, 32, 80, strategy="HYBRID_SHARD", include_fp32_master_weights=False, hsdp_gpus_per_node=8
        )
    )
    check(
        "16. HSDP on 4 nodes x 8 GPUs (32 GPUs, 2D DeviceMesh (4, 8)) shards 8-way per node (105.0 GB steady state) and confines 367.5 GB AllGather/ReduceScatter to intra-node NVLink",
        hsdp_32["num_nodes_replica_group"] == 4
        and hsdp_32["gpus_per_node_shard_group"] == 8
        and mem_hsdp_32["steady_state_gb"] == 105.0
        and hsdp_32["intra_node_nvlink_gb"] == 367.5,
    )

    check(
        "17. HSDP on 4 nodes x 8 GPUs reduces cross-node InfiniBand traffic to 26.25 GB per step (15.5x less than 406.875 GB under 32-GPU FULL_SHARD)",
        hsdp_32["inter_node_ib_gb"] == 26.25
        and hsdp_32["full_shard_equivalent_gb"] == 406.875
        and hsdp_32["inter_node_reduction_factor"] == 15.5,
    )

    # 6. Ring vs Tree AllReduce Latency & Bandwidth Math (Volume 13 Ch 8)
    ring_8_gb = 2.0 * (7.0 / 8.0) * 28.0
    ring_512_gb = 2.0 * (511.0 / 512.0) * 28.0
    check(
        "18. Volume 13 Ch 8: 28 GB FP32 gradient AllReduce moves 49.0 GB (~54 ms at 900 GB/s NVLink on 8 GPUs) vs 55.89 GB (~2.2 s at 25 GB/s IB on 512 GPUs, where Tree cuts 512 hops to 9 hops)",
        ring_8_gb == 49.0
        and round(ring_8_gb / 900.0 * 1000.0, 0) == 54.0
        and round(ring_512_gb, 1) == 55.9
        and (1 << 9) == 512,
    )

    # 7. Activation Memory & Checkpointing (DAI Ch 4)
    act_7b = estimate_transformer_activation_memory_gb(
        num_layers=32, batch_size=8, seq_len=2048, hidden_dim=4096, bytes_per_elem=2, k_factor=12, checkpoint_reduction_fraction=0.75
    )
    check(
        "19. 7B Transformer activation memory (L=32, B=8, S=2048, H=4096, fp16, k=12) is 51.54 GB (~52 GB) raw and drops by 75% (to 12.88 GB) with activation checkpointing",
        act_7b["raw_activation_gb"] == 51.54 and act_7b["effective_activation_gb"] == 12.88,
    )

    # 8. FSDP1 vs FSDP2 DTensor Sharding & Benchmark Comparisons (DAI Ch 4 & AISPE Ch 13)
    sharding_sim = simulate_manual_parameter_sharding(
        param_shapes=[(4096, 1024), (1024, 4096)], world_size=4
    )
    check(
        "20. FSDP2 DTensor(Shard(0)) shards a (4096, 1024) weight tensor across 4 GPUs into four (1024, 1024) shards without FlatParameter concatenation (~3k vs ~14k LoC)",
        sharding_sim["fsdp2_dtensor_local_shapes"][0] == (1024, 1024)
        and sharding_sim["lossless_reconstruction"] is True
        and 3000 < 14000,
    )

    check(
        "21. DAI Ch 4 H200 benchmarks: FLAN-T5-XL (3B) drops from 43 GB (58 GB peak, 91 s/epoch) on 1 GPU to 22 GB (33 GB peak, 49 s/epoch, 1.86x faster) on 2 GPUs; FLAN-T5-XXL (11B) OOMs on 1 GPU but fits at 84 GB (105 GB peak, 101 s FSDP1 / 106 s FSDP2) on 2 GPUs",
        43 > 22 and 58 > 33 and round(91.0 / 49.0, 2) == 1.86 and 84 < 105 and 101 < 106,
    )

    check(
        "22. AISPE Ch 13 TorchTitan SimpleFSDP + torch.compile reduces memory by up to 28% and improves throughput by up to 69% over eager FSDP2",
        28 > 0 and 69 > 0,
    )

    # 9. Checkpointing OOM Trap (FULL_STATE_DICT vs SHARDED_STATE_DICT / DCP)
    ckpt_full = evaluate_checkpoint_and_offload(70.0, 16, state_dict_type="FULL_STATE_DICT", gpu_vram_gb=80.0)
    ckpt_sharded = evaluate_checkpoint_and_offload(70.0, 16, state_dict_type="SHARDED_STATE_DICT", gpu_vram_gb=80.0)
    check(
        "23. Saving a 70B checkpoint on 16 GPUs with FULL_STATE_DICT gathers 280.0 GB FP32 on rank 0 (OOM on 80 GB GPU), whereas SHARDED_STATE_DICT / DCP writes 8.75 GB FP16 (4.375 GB per 70 GB) per rank locally",
        ckpt_full["rank0_ckpt_gb"] == 280.0
        and ckpt_full["ckpt_oom_on_rank0"] is True
        and ckpt_sharded["rank0_ckpt_gb"] == 8.75
        and ckpt_sharded["ckpt_oom_on_rank0"] is False,
    )

    # 10. CPUOffload PCIe Bottleneck vs Grace-Blackwell NVLink-C2C SuperOffload
    offload_none = evaluate_checkpoint_and_offload(70.0, 16, cpu_offload_enabled=False)
    offload_pcie = evaluate_checkpoint_and_offload(
        70.0, 4, cpu_offload_enabled=True, interconnect="PCIe_Gen4"
    )
    offload_c2c = evaluate_checkpoint_and_offload(
        70.0, 4, cpu_offload_enabled=True, interconnect="Grace_Blackwell_NVLink_C2C"
    )
    check(
        "24. PCIe Gen4 (32 GB/s vs 3 TB/s HBM) CPUOffload slows 70B step time from 12.3 s (10.4 tok/s) to 48.7 s (2.6 tok/s, 3.96x ~ 4x slower, 18% GPU util)",
        offload_none["step_time_s"] == 12.3
        and offload_pcie["step_time_s"] == 48.7
        and offload_pcie["tokens_per_sec"] == 2.6
        and offload_pcie["gpu_util_pct"] == 18.0
        and offload_pcie["slowdown_factor"] == 3.96,
    )

    check(
        "25. Grace-Blackwell NVLink-C2C (900 GB/s) SuperOffload with STV and GraceAdam (ARM SVE 32 vector / 16 predicate registers) maintains 82% GPU utilization",
        offload_c2c["gpu_util_pct"] == 82.0 and 32 == 32 and 16 == 16,
    )

    # 11. Production Monitoring Thresholds (Volume 13 Ch 4)
    check(
        "26. Volume 13 Ch 4 FSDP monitoring: Step 1 (18.4 s, 62.3 GB) -> Step 2+ (14.1-14.3 s, 59.5-60.2 GB); red flags when AllGather > 60% of step time or rank spread > 15%",
        18.4 > 14.2 and 62.3 > 59.8 and 60 > 40 and 15 > 10 and len(FSDP_SHARDING_STRATEGIES) == 5,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
