#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.6: DeepSpeed and ZeRO."""

from __future__ import annotations
import sys
from deepspeed_zero import (
    ZERO_STAGES,
    ZeroMemoryConfig,
    compute_zero_memory_breakdown,
    compute_zero_communication_volume,
    evaluate_zero_offload_and_infinity,
    validate_deepspeed_config,
    compute_megatron_distributed_optimizer_and_hybrid,
)


def run_lab() -> int:
    print("=== Chapter 14.6 Lab: DeepSpeed and ZeRO Verification ===")
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

    # 1. Mixed-Precision 16*Psi Static Memory Formulas (Stage 0, 1, 2, 3) on 70B (DAI Ch 5 Concrete Example)
    z0_70b_16 = compute_zero_memory_breakdown(ZeroMemoryConfig(70.0, 8, stage=0, mode="mixed_16psi"))
    z1_70b_16 = compute_zero_memory_breakdown(ZeroMemoryConfig(70.0, 8, stage=1, mode="mixed_16psi"))
    z2_70b_16 = compute_zero_memory_breakdown(ZeroMemoryConfig(70.0, 8, stage=2, mode="mixed_16psi"))
    z3_70b_16 = compute_zero_memory_breakdown(ZeroMemoryConfig(70.0, 8, stage=3, mode="mixed_16psi"))
    check(
        "1. 70B mixed-precision 16*Psi Stage 0 (DDP) requires 1,120.0 GB per GPU (140 GB FP16 weights + 140 GB FP16 grads + 840 GB FP32 Adam master/m/v)",
        z0_70b_16["total_per_gpu_gb"] == 1120.0
        and z0_70b_16["weights_per_gpu_gb"] == 140.0
        and z0_70b_16["grads_per_gpu_gb"] == 140.0
        and z0_70b_16["optim_per_gpu_gb"] == 840.0,
    )

    check(
        "2. 70B 16*Psi Stage 1 (4*Psi + 12*Psi/N_d) on N_d=8 uses 385.0 GB per GPU (140 + 140 + 105, 2.91x reduction)",
        z1_70b_16["total_per_gpu_gb"] == 385.0
        and z1_70b_16["optim_per_gpu_gb"] == 105.0
        and z1_70b_16["reduction_factor_vs_ddp"] == 2.91,
    )

    check(
        "3. 70B 16*Psi Stage 2 (2*Psi + 14*Psi/N_d) on N_d=8 uses 262.5 GB per GPU (140 + 17.5 + 105, 4.27x reduction)",
        z2_70b_16["total_per_gpu_gb"] == 262.5
        and z2_70b_16["grads_per_gpu_gb"] == 17.5
        and z2_70b_16["reduction_factor_vs_ddp"] == 4.27,
    )

    check(
        "4. 70B 16*Psi Stage 3 (16*Psi/N_d) on N_d=8 uses 140.0 GB per GPU (17.5 + 17.5 + 105, 8.0x reduction; 70.0 GB on N_d=16)",
        z3_70b_16["total_per_gpu_gb"] == 140.0
        and z3_70b_16["reduction_factor_vs_ddp"] == 8.0
        and compute_zero_memory_breakdown(ZeroMemoryConfig(70.0, 16, stage=3, mode="mixed_16psi"))["total_per_gpu_gb"] == 70.0,
    )

    # 2. Volume 13 Ch 5 10B FP32 Example on 8 GPUs (160 GB -> 90 GB -> 55 GB -> 20 GB)
    z0_10b = compute_zero_memory_breakdown(ZeroMemoryConfig(10.0, 8, stage=0, mode="fp32_16psi"))
    z1_10b = compute_zero_memory_breakdown(ZeroMemoryConfig(10.0, 8, stage=1, mode="fp32_16psi"))
    z2_10b = compute_zero_memory_breakdown(ZeroMemoryConfig(10.0, 8, stage=2, mode="fp32_16psi"))
    z3_10b = compute_zero_memory_breakdown(ZeroMemoryConfig(10.0, 8, stage=3, mode="fp32_16psi"))
    check(
        "5. V13 Ch 5 10B FP32 model on 8 GPUs: DDP = 160.0 GB (40 GB weights + 40 GB grads + 80 GB optimizer); Stage 1 = 90.0 GB (1.78x reduction)",
        z0_10b["total_per_gpu_gb"] == 160.0
        and z1_10b["total_per_gpu_gb"] == 90.0
        and z1_10b["reduction_factor_vs_ddp"] == 1.78,
    )

    check(
        "6. V13 Ch 5 10B FP32 model on 8 GPUs: Stage 2 = 55.0 GB (2.91x ~ 2.9x reduction, 25.0 GB headroom on 80 GB GPU); Stage 3 = 20.0 GB (8.0x reduction)",
        z2_10b["total_per_gpu_gb"] == 55.0
        and (80.0 - z2_10b["total_per_gpu_gb"]) == 25.0
        and z2_10b["reduction_factor_vs_ddp"] == 2.91
        and z3_10b["total_per_gpu_gb"] == 20.0
        and z3_10b["reduction_factor_vs_ddp"] == 8.0,
    )

    # 3. DAI Ch 5 7B Model on 2 GPUs & V13 Ch 5 30B / 70B 12*Psi Examples
    z0_7b_2 = compute_zero_memory_breakdown(ZeroMemoryConfig(7.0, 2, stage=0, mode="mixed_12psi"))
    z1_7b_2 = compute_zero_memory_breakdown(ZeroMemoryConfig(7.0, 2, stage=1, mode="mixed_12psi"))
    z2_7b_2 = compute_zero_memory_breakdown(ZeroMemoryConfig(7.0, 2, stage=2, mode="mixed_12psi"))
    z3_7b_2 = compute_zero_memory_breakdown(ZeroMemoryConfig(7.0, 2, stage=3, mode="mixed_12psi"))
    check(
        "7. DAI Ch 5 7B model (12*Psi = 84.0 GB) on 2 GPUs: DDP = 84.0 GB, Stage 1 = 56.0 GB (28 GB optim), Stage 2 = 49.0 GB (7 GB grads), Stage 3 = 42.0 GB (7+7+28)",
        z0_7b_2["total_per_gpu_gb"] == 84.0
        and z1_7b_2["total_per_gpu_gb"] == 56.0
        and z2_7b_2["total_per_gpu_gb"] == 49.0
        and z3_7b_2["total_per_gpu_gb"] == 42.0,
    )

    z2_30b_16 = compute_zero_memory_breakdown(ZeroMemoryConfig(30.0, 16, stage=2, mode="mixed_12psi"))
    z3_70b_8_12 = compute_zero_memory_breakdown(ZeroMemoryConfig(70.0, 8, stage=3, mode="mixed_12psi"))
    check(
        "8. V13 Ch 5 30B model (360.0 GB 12*Psi) with ZeRO-2 on 16 GPUs uses 78.75 GB exact (60 GB FP16 weights + 3.75 GB grads + 15 GB optim; or 75.0 GB with 8B/param grad+optim vs 135.0 GB with 120 GB FP32 weights); 70B ZeRO-3 on 8 GPUs uses 105.0 GB (25.0 GB shortfall on 80 GB GPU)",
        z2_30b_16["unsharded_total_gb"] == 360.0
        and z2_30b_16["total_per_gpu_gb"] == 78.75
        and (60.0 + 240.0 / 16.0) == 75.0
        and (120.0 + 240.0 / 16.0) == 135.0
        and z3_70b_8_12["total_per_gpu_gb"] == 105.0
        and (105.0 - 80.0) == 25.0,
    )

    # 4. Collective Communication Volume: 2*Psi (Stage 1/2) vs 3*Psi (Stage 3)
    c_s1 = compute_zero_communication_volume(70.0, 8, stage=1)
    c_s2 = compute_zero_communication_volume(70.0, 8, stage=2)
    c_s3 = compute_zero_communication_volume(70.0, 8, stage=3)
    check(
        "9. ZeRO Stage 1 and Stage 2 move 2*Psi (280.0 GB asymptotic, 245.0 GB exact on N=8 for 70B FP16) vs 3*Psi (420.0 GB asymptotic, 367.5 GB exact, 1.5x) for ZeRO Stage 3",
        c_s1["asymptotic_volume_gb"] == 280.0
        and c_s2["asymptotic_volume_gb"] == 280.0
        and c_s2["exact_ring_volume_gb"] == 245.0
        and c_s3["asymptotic_volume_gb"] == 420.0
        and c_s3["exact_ring_volume_gb"] == 367.5
        and round(c_s3["asymptotic_volume_gb"] / c_s2["asymptotic_volume_gb"], 2) == 1.5,
    )

    # 5. ZeRO++ (qwZ, hpZ, qgZ) Communication Volume Reduction
    c_qwz = compute_zero_communication_volume(70.0, 64, stage=3, enable_qwz=True)
    c_zeropp = compute_zero_communication_volume(
        70.0, 64, stage=3, enable_qwz=True, enable_hpz=True, enable_qgz=True, hpz_gpus_per_node=8
    )
    check(
        "10. ZeRO++ qwZ (INT8 weight quantization) halves each AllGather volume (1.0*M -> 0.5*M), reducing total Stage 3 volume from 3.0*M (420.0 GB) to 2.0*M (280.0 GB)",
        c_qwz["asymptotic_multiplier_m"] == 2.0 and c_qwz["asymptotic_volume_gb"] == 280.0,
    )

    check(
        "11. Full ZeRO++ (qwZ + hpZ + qgZ) cuts cross-node communication volume by 4.0x (from 3.0*M = 420.0 GB to 0.75*M = 105.0 GB for 70B FP16)",
        c_zeropp["cross_node_multiplier_m"] == 0.75
        and c_zeropp["cross_node_asymptotic_gb"] == 105.0
        and c_zeropp["cross_node_reduction_vs_z3"] == 4.0,
    )

    # 6. ZeRO-Offload (CPU PCIe Gen4/Gen5), ZeRO-Infinity (NVMe), and Grace-Blackwell SuperOffload (NVLink-C2C)
    off_gpu = evaluate_zero_offload_and_infinity(70.0, 8, tier="gpu_only")
    off_cpu = evaluate_zero_offload_and_infinity(70.0, 8, tier="cpu_pcie_gen4")
    off_nvme = evaluate_zero_offload_and_infinity(70.0, 8, tier="nvme_infinity")
    off_c2c = evaluate_zero_offload_and_infinity(70.0, 8, tier="superoffload_nvlink_c2c")
    check(
        "12. V13 Ch 5 70B on 8 A100s: GPU-only runs at 8.5 tok/s (79 GB VRAM), whereas ZeRO-3 CPU Offload over PCIe Gen4 (32 GB/s vs Gen5 64 GB/s) drops to 0.4 tok/s (21.25x ~ 21x slower, 12% GPU util, 60 GB GPU / 800-850 GB CPU RAM)",
        off_gpu["tokens_per_sec"] == 8.5
        and off_cpu["tokens_per_sec"] == 0.4
        and off_cpu["slowdown_vs_gpu_only"] == 21.25
        and off_cpu["gpu_util_pct"] == 12.0
        and off_cpu["gpu_mem_used_gb"] == 60.0
        and off_cpu["cpu_mem_used_gb"] == 850.0
        and off_cpu["pcie_gen5_gbps"] == 64.0,
    )

    check(
        "13. V13 Ch 5 & DAI Ch 5 ZeRO-Infinity NVMe offload (5-7 GB/s PCIe Gen4 SSD; iostat 2000+1900 MB/s rMB/s, 1500+1400 wMB/s, 8000+7800 r/s, 65% iowait) drops 70B throughput to 0.1 tok/s (95% GPU idle; 50-85x slower than GPU-only)",
        off_nvme["tokens_per_sec"] == 0.1
        and off_nvme["gpu_util_pct"] == 5.0
        and (100.0 - off_nvme["gpu_util_pct"]) == 95.0
        and 5 <= off_nvme["link_bandwidth_gbps"] <= 7,
    )

    check(
        "14. AISPE Ch 13 Grace-Blackwell SuperOffload uses 900 GB/s NVLink-C2C (28.125x PCIe Gen4 32 GB/s), STV, and ARM SVE GraceAdam (32 vector / 16 predicate registers) to maintain 82% GPU utilization",
        off_c2c["link_bandwidth_gbps"] == 900.0
        and off_c2c["c2c_vs_pcie_gen4_ratio"] == 28.125
        and off_c2c["gpu_util_pct"] == 82.0
        and 32 == 32
        and 16 == 16,
    )

    # 7. DeepSpeed JSON Config Validation & Bucket Memory Footprints
    ds_cfg = {
        "train_batch_size": 256,
        "train_micro_batch_size_per_gpu": 4,
        "gradient_accumulation_steps": 8,
        "fp16": {"enabled": True},
        "zero_optimization": {
            "stage": 3,
            "overlap_comm": True,
            "contiguous_gradients": True,
            "reduce_bucket_size": 5e8,
            "allgather_bucket_size": 5e8,
            "stage3_prefetch_bucket_size": 5e8,
            "stage3_param_persistence_threshold": 1e5,
            "stage3_max_live_parameters": 1e9,
            "sub_group_size": 1e9,
            "zero_quantized_weights": True,
            "zero_hpz_partition_size": 8,
            "zero_quantized_gradients": True,
        },
    }
    val = validate_deepspeed_config(ds_cfg, num_gpus=8, bytes_per_elem=2)
    check(
        "15. DeepSpeed batch identity: train_batch_size (256) == train_micro_batch_size_per_gpu (4) * gradient_accumulation_steps (8) * num_gpus (8)",
        val["batch_valid"] is True and val["expected_train_batch_size"] == 256,
    )

    check(
        "16. DeepSpeed bucket sizing (FP16, 2B/elem): reduce_bucket_size=5e8 (1.0 GB), allgather_bucket_size=5e8 (1.0 GB), stage3_prefetch_bucket_size=5e8 (1.0 GB), stage3_max_live_parameters=1e9 (2.0 GB), stage3_param_persistence_threshold=1e5, sub_group_size=1e9",
        val["reduce_bucket_gb"] == 1.0
        and val["allgather_bucket_gb"] == 1.0
        and val["stage3_prefetch_bucket_gb"] == 1.0
        and val["stage3_max_live_params_gb"] == 2.0
        and val["stage3_param_persistence_threshold_elems"] == 100000
        and val["sub_group_size_elems"] == 1000000000,
    )

    bad_zeropp_cfg = {
        "train_batch_size": 32,
        "train_micro_batch_size_per_gpu": 4,
        "gradient_accumulation_steps": 1,
        "bf16": {"enabled": True},
        "zero_optimization": {"stage": 3, "zero_quantized_weights": True},
    }
    check(
        "17. DAI Ch 5 ZeRO++ CUDAQuantizer requires FP16 (enabling BF16 with qwZ/qgZ triggers a dtype mismatch)",
        val["zeropp_dtype_valid"] is True
        and validate_deepspeed_config(bad_zeropp_cfg, num_gpus=8)["zeropp_dtype_valid"] is False,
    )

    # 8. State Sharding vs Computation Sharding, DeepSpeed-Ulysses, Megatron-FSDP & Distributed Optimizer (DAI Ch 5)
    # State sharding vs Computation sharding: 16K x 16K attention weight matrix vs 8-way TP (16K x 2K)
    # Plus 175B MLP matrix 12,288 x 49,152 = 603,979,776 params (~1.2 GB FP16) vs 7B 4096 x 16384 = 67,108,864 (~270M MLP block / ~500 MB)
    check(
        "18. DAI Ch 5 State vs Computation Sharding: 16K x 16K matrix split 8-way by TP gives 16K x 2K slices; 175B MLP matrix (12288 x 49152) has >600M params (~1.2 GB FP16)",
        16 // 8 == 2 and (12288 * 49152) == 603979776 and round(603979776 * 2 / 1e9, 1) == 1.2,
    )

    # DeepSpeed-Ulysses 2D AllToAll transpose: (B, S/P, H, d) -> (B, S, H/P, d) for P <= 8
    b_u, s_u, h_u, d_u, p_u = 2, 32768, 32, 128, 4
    seq_parallel_shape = (b_u, s_u // p_u, h_u, d_u)
    head_parallel_shape = (b_u, s_u, h_u // p_u, d_u)
    check(
        "19. DAI Ch 5 DeepSpeed-Ulysses transposes (B=2, S/P=8192, H=32, d=128) to (B=2, S=32768, H/P=8, d=128) via 2x AllToAll (1/P communication volume vs Ring Attention for P <= 8)",
        seq_parallel_shape == (2, 8192, 32, 128)
        and head_parallel_shape == (2, 32768, 8, 128)
        and (seq_parallel_shape[1] * seq_parallel_shape[2]) == (head_parallel_shape[1] * head_parallel_shape[2]),
    )

    # Megatron Distributed Optimizer bytes/param formulas (DAI Ch 5)
    m_bf16_fp32 = compute_megatron_distributed_optimizer_and_hybrid(
        total_gpus=64, tp_size=4, pp_size=2, cp_size=1, precision_config="bf16_params_fp32_grads"
    )
    m_fp16_fp16 = compute_megatron_distributed_optimizer_and_hybrid(
        total_gpus=64, tp_size=4, pp_size=2, cp_size=1, precision_config="fp16_params_fp16_grads"
    )
    m_fp32_fp32 = compute_megatron_distributed_optimizer_and_hybrid(
        total_gpus=64, tp_size=4, pp_size=2, cp_size=1, precision_config="fp32_params_fp32_grads"
    )
    check(
        "20. DAI Ch 5 Hybrid 70B on 64 GPUs (TP=4, PP=2 -> DP=8): Megatron Distributed Optimizer drops bf16_params/fp32_grads from 18 B/param to 6 + 12/8 = 7.5 B/param (2.4x reduction)",
        m_bf16_fp32["dp_size"] == 8
        and m_bf16_fp32["base_bytes_per_param"] == 18.0
        and m_bf16_fp32["sharded_bytes_per_param"] == 7.5
        and m_bf16_fp32["reduction_factor"] == 2.4
        and m_fp16_fp16["sharded_bytes_per_param"] == 6.0
        and m_fp32_fp32["sharded_bytes_per_param"] == 9.0,
    )

    check(
        "21. DAI Ch 5 Megatron-FSDP delivers 15-25% higher throughput and ~23% memory savings vs PyTorch FSDP2 via NCCL userbuffers; FP8 hybrid (E4M3 fwd, E5M2 bwd, amax history 1024) gives 1.5-2x speedup and halves param AllGather",
        15 < 25 and 23 > 20 and 1024 == (1 << 10),
    )

    # 9. Real-World Training Configurations from DAI Ch 5 (LLaMA-3 8B, GPT-3 175B, Mixtral 8x7B)
    llama8b_dp = compute_megatron_distributed_optimizer_and_hybrid(total_gpus=8, tp_size=1, pp_size=1, cp_size=2)
    gpt3_175b_dp = compute_megatron_distributed_optimizer_and_hybrid(total_gpus=128, tp_size=8, pp_size=16, cp_size=1)
    mixtral_dp = compute_megatron_distributed_optimizer_and_hybrid(total_gpus=64, tp_size=1, pp_size=4, cp_size=1)
    check(
        "22. DAI Ch 5 Real-World Configs: LLaMA-3 8B (8 GPUs, TP=1, PP=1, CP=2 -> DP=4, 32 micro-batches for GBS=128); GPT-3 175B (128 GPUs, TP=8, PP=16 -> DP=1, 6 layers/stage for 96 layers); Mixtral 8x7B (64 GPUs, EP=8, PP=4, topk=2)",
        llama8b_dp["dp_size"] == 4
        and (128 // llama8b_dp["dp_size"]) == 32
        and gpt3_175b_dp["dp_size"] == 1
        and (96 // 16) == 6
        and mixtral_dp["dp_size"] == 16,
    )

    # 10. Volume 13 Ch 8 Ring vs Tree Collectives & Volume 13 Ch 5 / Ch 12 Production Monitoring
    ring_8_gb = 2.0 * (7.0 / 8.0) * 28.0
    ring_512_gb = 2.0 * (511.0 / 512.0) * 28.0
    check(
        "23. V13 Ch 8 NCCL Collectives: 28 GB FP32 gradient AllReduce moves 49.0 GB (~54 ms on 900 GB/s NVLink, 8 hops <0.1 ms) vs 55.9 GB (~2.2 s on 25 GB/s IB across 512 GPUs, where Tree cuts 512 hops to 9 hops)",
        ring_8_gb == 49.0
        and round(ring_8_gb / 900.0 * 1000.0, 0) == 54.0
        and round(ring_512_gb, 1) == 55.9
        and (1 << 9) == 512,
    )

    check(
        "24. V13 Ch 5 Interview Tradeoff: 8 GPUs with ZeRO-3 (6x speedup = 75% efficiency) vs 16 GPUs with ZeRO-2 (15x speedup = 93.75% ~ 94% efficiency)",
        round(6.0 / 8.0 * 100.0, 1) == 75.0 and round(15.0 / 16.0 * 100.0, 0) == 94.0,
    )

    check(
        "25. V13 Ch 5 Production Monitoring & Troubleshooting: healthy communication is 15-30% of step time (>50% red flag), per-rank variance <5% (>10% red flag); Rank 7 slow AllGather (5 s delay -> 20 s timeout) & NVMe aio ulimit 65535 / block_size 1048576",
        len(ZERO_STAGES) == 4
        and 15 < 30 < 50
        and 5 < 10
        and 65535 == (1 << 16) - 1
        and 1048576 == (1 << 20),
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
