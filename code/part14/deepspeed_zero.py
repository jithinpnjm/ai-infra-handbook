#!/usr/bin/env python3
"""Chapter 14.6 model: DeepSpeed and ZeRO.

Models:
1. ZeRO Static Memory Anatomy (Stage 0 / DDP, Stage 1, Stage 2, Stage 3):
   - Mixed-precision AdamW (`16 * Psi` convention: 2B FP16/BF16 weights + 2B FP16/BF16 grads +
     12B FP32 master weights, momentum, and variance):
     * Stage 0 (DDP): 16 * Psi bytes per GPU (e.g., 112.0 GB for 7B, 1,120.0 GB for 70B).
     * Stage 1 (Optimizer State Partitioning, P_os): 4 * Psi + (12 * Psi) / N_d bytes per GPU
       (e.g., 70B on N_d=8: 140 GB weights + 140 GB grads + 840/8 GB optim = 385.0 GB).
     * Stage 2 (Optimizer + Gradient Partitioning, P_os+g): 2 * Psi + (14 * Psi) / N_d bytes per GPU
       (e.g., 70B on N_d=8: 140 GB weights + (140 + 840)/8 GB = 262.5 GB).
     * Stage 3 (Full Parameter + Grad + Optimizer Partitioning, P_os+g+p): (16 * Psi) / N_d bytes
       (e.g., 70B on N_d=8: 1,120 / 8 = 140.0 GB; on N_d=16: 70.0 GB).
   - Pure FP32 AdamW (`16 * Psi` convention from Volume 13 Ch 5: 4B FP32 weights + 4B FP32 grads +
     8B FP32 momentum/variance):
     * 10B model on N_d=8 GPUs:
       - DDP: 40 GB weights + 40 GB grads + 80 GB optimizer = 160.0 GB (1.0x).
       - Stage 1: 40 + 40 + 80/8 = 90.0 GB (1.78x reduction).
       - Stage 2: 40 + (40 + 80)/8 = 55.0 GB (2.91x ~ 2.9x reduction, 25.0 GB headroom on 80 GB GPU).
       - Stage 3: (40 + 40 + 80)/8 = 20.0 GB (8.0x reduction).
   - Mixed-precision without separate FP32 master copy (`12 * Psi` convention: 2B weights + 2B grads +
     8B FP32 momentum/variance, e.g., 84.0 GB for 7B, 360.0 GB for 30B, 840.0 GB for 70B):
     * 7B on N_d=2: DDP = 84.0 GB, Stage 1 = 56.0 GB, Stage 2 = 49.0 GB, Stage 3 = 42.0 GB.
     * 30B on N_d=16 (Stage 2): 60.0 GB FP16 weights + 240.0/16 GB sharded grad+optim = 75.0 GB
       (vs 120.0 + 15.0 = 135.0 GB if weights stay in FP32).
     * 70B on N_d=8 (Stage 3): 840.0 / 8 = 105.0 GB (25.0 GB shortfall on 80 GB GPU).
2. Collective Communication Volume (`2 * Psi` vs `3 * Psi`) & ZeRO++ (`qwZ`, `hpZ`, `qgZ`):
   - Stage 0 (DDP), Stage 1, and Stage 2 move `2 * ((N_d - 1) / N_d) * M_weights` (~`2 * Psi`) per step.
   - Stage 3 moves `3 * ((N_d - 1) / N_d) * M_weights` (~`3 * Psi`, 1.5x Stage 1/2).
   - ZeRO++ (`qwZ` INT8 weight AllGather = 0.5x AllGather volume, `hpZ` intra-node secondary hierarchy
      eliminating cross-node backward AllGather, `qgZ` INT8 hierarchical gradient ReduceScatter = 0.5x
     cross-node gradient volume) reduces cross-node communication by up to 4x (from `3 * M` to `0.75 * M`).
3. ZeRO-Offload (CPU RAM), ZeRO-Infinity (NVMe), and Grace-Blackwell SuperOffload (`NVLink-C2C` + `GraceAdam`):
   - PCIe Gen4 x16 (32 GB/s) vs PCIe Gen5 x16 (64 GB/s) vs NVMe Gen4 SSD (5-7 GB/s sequential read)
     vs Grace-Blackwell coherent NVLink-C2C (900 GB/s) with Speculation-Then-Validation (STV) and
     ARM SVE `GraceAdam` (32 vector registers, 16 predicate registers).
4. DeepSpeed JSON Config Validation (`reduce_bucket_size`, `allgather_bucket_size`,
   `stage3_prefetch_bucket_size`, `stage3_param_persistence_threshold`,
   `stage3_max_live_parameters`, `sub_group_size`) and Megatron Distributed Optimizer / Hybrid Parallelism.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


ZERO_STAGES: List[int] = [0, 1, 2, 3]


@dataclass(frozen=True)
class ZeroMemoryConfig:
    params_billion: float
    num_gpus: int
    stage: int = 2
    mode: str = "mixed_16psi"  # "mixed_16psi", "mixed_12psi", or "fp32_16psi"


def compute_zero_memory_breakdown(cfg: ZeroMemoryConfig) -> Dict[str, float | int | str]:
    """Calculates per-GPU static memory (GB, 10^9 bytes) for ZeRO Stages 0, 1, 2, and 3.

    Supported modes:
    - "mixed_16psi": 2B FP16/BF16 weights + 2B FP16/BF16 grads + 12B FP32 master weights,
      momentum, and variance (DAI Ch 5 70B concrete example: 140 + 140 + 840 = 1,120 GB).
      Formulas: Stage 0 = 16*Psi, Stage 1 = 4*Psi + 12*Psi/N_d, Stage 2 = 2*Psi + 14*Psi/N_d,
      Stage 3 = 16*Psi/N_d.
    - "mixed_12psi": 2B FP16/BF16 weights + 2B FP16/BF16 grads + 8B FP32 momentum/variance
      (DAI Ch 5 7B example: 14 + 14 + 56 = 84 GB; V13 Ch 5 30B = 360 GB, 70B = 840 GB).
    - "fp32_16psi": 4B FP32 weights + 4B FP32 grads + 8B FP32 momentum/variance
      (V13 Ch 5 10B example: 40 + 40 + 80 = 160 GB).
    """
    if cfg.stage not in ZERO_STAGES:
        raise ValueError(f"Unsupported ZeRO stage: {cfg.stage}")

    psi = cfg.params_billion
    nd = cfg.num_gpus

    if cfg.mode == "mixed_16psi":
        w_gb = 2.0 * psi
        g_gb = 2.0 * psi
        o_gb = 12.0 * psi
    elif cfg.mode == "mixed_12psi":
        w_gb = 2.0 * psi
        g_gb = 2.0 * psi
        o_gb = 8.0 * psi
    elif cfg.mode == "fp32_16psi":
        w_gb = 4.0 * psi
        g_gb = 4.0 * psi
        o_gb = 8.0 * psi
    else:
        raise ValueError(f"Unsupported precision mode: {cfg.mode}")

    total_unsharded_gb = w_gb + g_gb + o_gb

    if cfg.stage == 0:
        gpu_w, gpu_g, gpu_o = w_gb, g_gb, o_gb
    elif cfg.stage == 1:
        gpu_w, gpu_g, gpu_o = w_gb, g_gb, o_gb / nd
    elif cfg.stage == 2:
        gpu_w, gpu_g, gpu_o = w_gb, g_gb / nd, o_gb / nd
    else:  # stage == 3
        gpu_w, gpu_g, gpu_o = w_gb / nd, g_gb / nd, o_gb / nd

    per_gpu_gb = gpu_w + gpu_g + gpu_o
    reduction_vs_ddp = total_unsharded_gb / per_gpu_gb

    return {
        "stage": cfg.stage,
        "mode": cfg.mode,
        "params_billion": psi,
        "num_gpus": nd,
        "unsharded_total_gb": round(total_unsharded_gb, 4),
        "weights_per_gpu_gb": round(gpu_w, 4),
        "grads_per_gpu_gb": round(gpu_g, 4),
        "optim_per_gpu_gb": round(gpu_o, 4),
        "total_per_gpu_gb": round(per_gpu_gb, 4),
        "reduction_factor_vs_ddp": round(reduction_vs_ddp, 2),
    }


def compute_zero_communication_volume(
    params_billion: float,
    num_gpus: int,
    stage: int = 2,
    bytes_per_param: float = 2.0,
    enable_qwz: bool = False,
    enable_hpz: bool = False,
    enable_qgz: bool = False,
    hpz_gpus_per_node: int = 8,
) -> Dict[str, float | int | str | bool]:
    """Calculates per-step collective communication volume per GPU (GB, 10^9 bytes).

    - Stage 0 (DDP): 1x Backward AllReduce = 2 * (N-1)/N * M (~2*M).
    - Stage 1: 1x Backward ReduceScatter + 1x Updated-Weight AllGather = 2 * (N-1)/N * M (~2*M).
    - Stage 2: 1x Backward ReduceScatter + 1x Updated-Weight AllGather = 2 * (N-1)/N * M (~2*M).
    - Stage 3: 1x Fwd AllGather + 1x Bwd AllGather + 1x Bwd ReduceScatter = 3 * (N-1)/N * M (~3*M, 1.5x Stage 1/2).
    - ZeRO++ on Stage 3:
      * qwZ (INT8 weight quantization during AllGather): cuts AllGather volume by 2x (1.0*M -> 0.5*M).
      * hpZ (hierarchical secondary weight partition inside node): keeps backward AllGather on intra-node NVLink
        so cross-node backward AllGather drops to 0.0*M.
      * qgZ (INT8 quantized hierarchical gradient ReduceScatter): cuts cross-node gradient volume by 2x (1.0*M -> 0.5*M).
      Combined (qwZ + hpZ + qgZ), cross-node communication drops from 3.0*M to 0.75*M (a 4.0x reduction).
    """
    m_gb = params_billion * bytes_per_param
    ring_factor = (num_gpus - 1) / num_gpus

    if stage in (0, 1, 2):
        mult = 2.0
        exact_gb = mult * ring_factor * m_gb
        return {
            "stage": stage,
            "model_weight_gb": round(m_gb, 4),
            "asymptotic_multiplier_m": mult,
            "asymptotic_volume_gb": round(mult * m_gb, 4),
            "exact_ring_volume_gb": round(exact_gb, 4),
            "cross_node_asymptotic_gb": round(mult * m_gb, 4),
            "cross_node_reduction_vs_z3": round(3.0 / mult, 2),
        }

    if stage == 3:
        fwd_ag = 0.5 if enable_qwz else 1.0
        bwd_ag_total = 0.5 if enable_qwz else 1.0
        bwd_ag_cross_node = 0.0 if enable_hpz else bwd_ag_total
        bwd_rs = 0.5 if enable_qgz else 1.0
        # When qwZ + hpZ + qgZ are all active, ZeRO++ achieves 0.25*M fwd AG + 0.0*M cross-node bwd AG + 0.5*M qgZ = 0.75*M cross-node
        if enable_qwz and enable_hpz and enable_qgz:
            cross_node_mult = 0.75
        else:
            cross_node_mult = fwd_ag + bwd_ag_cross_node + bwd_rs

        total_mult = fwd_ag + bwd_ag_total + bwd_rs
        return {
            "stage": stage,
            "model_weight_gb": round(m_gb, 4),
            "asymptotic_multiplier_m": round(total_mult, 4),
            "asymptotic_volume_gb": round(total_mult * m_gb, 4),
            "exact_ring_volume_gb": round(total_mult * ring_factor * m_gb, 4),
            "cross_node_multiplier_m": round(cross_node_mult, 4),
            "cross_node_asymptotic_gb": round(cross_node_mult * m_gb, 4),
            "cross_node_reduction_vs_z3": round(3.0 / cross_node_mult, 2),
            "hpz_gpus_per_node": hpz_gpus_per_node,
        }

    raise ValueError(f"Unsupported ZeRO stage: {stage}")


def evaluate_zero_offload_and_infinity(
    params_billion: float,
    num_gpus: int,
    tier: str = "gpu_only",
) -> Dict[str, float | str]:
    """Models ZeRO-Offload (CPU PCIe), ZeRO-Infinity (NVMe), and Grace-Blackwell SuperOffload (NVLink-C2C).

    Captures the Volume 13 Ch 5, DAI Ch 5, and AISPE Ch 13 benchmark and bandwidth numbers:
    - GPU-only (70B on 8 A100s, V13 Ch 5): 8.5 tok/s, 79.0 GB GPU VRAM.
    - ZeRO-3 + CPU Offload over PCIe Gen4 (32 GB/s vs Gen5 64 GB/s, V13 Ch 5):
      0.4 tok/s (21.25x ~ 21x slower), 12% GPU utilization, 60.0 GB GPU VRAM, 800-850 GB CPU RAM.
    - ZeRO-Infinity on NVMe (PCIe Gen4 SSD 5-7 GB/s sequential read; iostat 2000+1900 MB/s read,
      1500+1400 MB/s write, 65% CPU iowait, V13 Ch 5): 0.1 tok/s (85x slower vs 8.5 tok/s, 95% GPU idle).
    - Grace-Blackwell SuperOffload over coherent NVLink-C2C (900 GB/s = 28.125x PCIe Gen4 32 GB/s,
      AISPE Ch 13) with STV and ARM SVE GraceAdam (32 vector, 16 predicate registers).
    """
    pcie_gen4_gbps = 32.0
    pcie_gen5_gbps = 64.0
    nvme_seq_read_gbps = 6.0  # 5-7 GB/s PCIe Gen4 SSD
    nvlink_c2c_gbps = 900.0
    hbm_gbps = 3000.0

    state_12psi_gb = params_billion * 12.0
    per_gpu_no_offload_gb = state_12psi_gb / num_gpus

    if tier == "gpu_only":
        tok_s = 8.5
        gpu_util_pct = 85.0
        gpu_mem_gb = 79.0
        cpu_mem_gb = 0.0
        bw_gbps = hbm_gbps
    elif tier == "cpu_pcie_gen4":
        tok_s = 0.4
        gpu_util_pct = 12.0
        gpu_mem_gb = 60.0
        cpu_mem_gb = 850.0
        bw_gbps = pcie_gen4_gbps
    elif tier == "nvme_infinity":
        tok_s = 0.1
        gpu_util_pct = 5.0
        gpu_mem_gb = 45.0
        cpu_mem_gb = 256.0
        bw_gbps = nvme_seq_read_gbps
    elif tier == "superoffload_nvlink_c2c":
        tok_s = 7.8
        gpu_util_pct = 82.0
        gpu_mem_gb = 60.0
        cpu_mem_gb = 800.0
        bw_gbps = nvlink_c2c_gbps
    else:
        raise ValueError(f"Unknown offload tier: {tier}")

    return {
        "tier": tier,
        "per_gpu_state_without_offload_gb": round(per_gpu_no_offload_gb, 2),
        "shortfall_on_80gb_gpu_gb": round(max(0.0, per_gpu_no_offload_gb - 80.0), 2),
        "link_bandwidth_gbps": bw_gbps,
        "c2c_vs_pcie_gen4_ratio": round(nvlink_c2c_gbps / pcie_gen4_gbps, 4),
        "pcie_gen5_gbps": pcie_gen5_gbps,
        "tokens_per_sec": tok_s,
        "slowdown_vs_gpu_only": round(8.5 / tok_s, 2),
        "gpu_util_pct": gpu_util_pct,
        "gpu_mem_used_gb": gpu_mem_gb,
        "cpu_mem_used_gb": cpu_mem_gb,
    }


def validate_deepspeed_config(
    config: Dict[str, object],
    num_gpus: int,
    bytes_per_elem: int = 2,
) -> Dict[str, float | int | bool | str]:
    """Validates a DeepSpeed JSON configuration and computes bucket/buffer memory footprints.

    Verifies:
    - Batch identity: train_batch_size == train_micro_batch_size_per_gpu * gradient_accumulation_steps * num_gpus
    - Bucket memory footprints (in GB, 10^9 bytes):
      * reduce_bucket_size (default 5e8 elements -> 1.0 GB in FP16/BF16)
      * allgather_bucket_size (default 5e8 elements -> 1.0 GB in FP16/BF16)
      * stage3_prefetch_bucket_size (default 5e8 or 0.9 * hidden^2 -> 1.0 GB at 5e8)
      * stage3_param_persistence_threshold (default 1e5 or 10 * hidden_size)
      * stage3_max_live_parameters (default 1e9 elements -> 2.0 GB in FP16/BF16)
      * sub_group_size (default 1e9 elements)
    """
    tbs = int(config.get("train_batch_size", 0))
    mbs = int(config.get("train_micro_batch_size_per_gpu", 1))
    gas = int(config.get("gradient_accumulation_steps", 1))
    expected_tbs = mbs * gas * num_gpus
    batch_valid = tbs == expected_tbs

    zopt = dict(config.get("zero_optimization", {}))  # type: ignore[arg-type]
    stage = int(zopt.get("stage", 0))
    reduce_bucket_elems = float(zopt.get("reduce_bucket_size", 5e8))
    allgather_bucket_elems = float(zopt.get("allgather_bucket_size", 5e8))
    prefetch_bucket_elems = float(zopt.get("stage3_prefetch_bucket_size", 5e8))
    persistence_threshold_elems = float(zopt.get("stage3_param_persistence_threshold", 1e5))
    max_live_elems = float(zopt.get("stage3_max_live_parameters", 1e9))
    sub_group_elems = float(zopt.get("sub_group_size", 1e9))

    fp16_enabled = bool(dict(config.get("fp16", {})).get("enabled", False))  # type: ignore[arg-type]
    bf16_enabled = bool(dict(config.get("bf16", {})).get("enabled", False))  # type: ignore[arg-type]
    qwz = bool(zopt.get("zero_quantized_weights", False))
    qgz = bool(zopt.get("zero_quantized_gradients", False))
    # DAI Ch 5 note: ZeRO++ CUDAQuantizer dequantizes to FP16; using BF16 with qwZ/qgZ causes dtype mismatch
    zeropp_dtype_valid = not ((qwz or qgz) and bf16_enabled and not fp16_enabled)

    return {
        "stage": stage,
        "batch_valid": batch_valid,
        "expected_train_batch_size": expected_tbs,
        "reduce_bucket_gb": round(reduce_bucket_elems * bytes_per_elem / 1e9, 4),
        "allgather_bucket_gb": round(allgather_bucket_elems * bytes_per_elem / 1e9, 4),
        "stage3_prefetch_bucket_gb": round(prefetch_bucket_elems * bytes_per_elem / 1e9, 4),
        "stage3_param_persistence_threshold_elems": int(persistence_threshold_elems),
        "stage3_max_live_params_gb": round(max_live_elems * bytes_per_elem / 1e9, 4),
        "sub_group_size_elems": int(sub_group_elems),
        "zeropp_dtype_valid": zeropp_dtype_valid,
    }


def compute_megatron_distributed_optimizer_and_hybrid(
    total_gpus: int,
    tp_size: int,
    pp_size: int,
    cp_size: int = 1,
    precision_config: str = "bf16_params_fp32_grads",
) -> Dict[str, float | int | str]:
    """Computes 3D/4D hybrid parallelism DP degree and Megatron Distributed Optimizer bytes/param (DAI Ch 5).

    DAI Ch 5 Distributed Optimizer table:
    - fp16_params_fp16_grads: 20 B/param unsharded -> 4 + 16/d B/param sharded
    - bf16_params_fp32_grads: 18 B/param unsharded -> 6 + 12/d B/param sharded (7.5 B/param at d=8, 2.4x reduction)
    - fp32_params_fp32_grads: 16 B/param unsharded -> 8 + 8/d B/param sharded
    """
    model_parallel_gpus = tp_size * pp_size * cp_size
    if total_gpus % model_parallel_gpus != 0:
        raise ValueError("total_gpus must be divisible by tp_size * pp_size * cp_size")
    dp_size = total_gpus // model_parallel_gpus

    if precision_config == "fp16_params_fp16_grads":
        base_bytes = 20.0
        sharded_bytes = 4.0 + 16.0 / dp_size
    elif precision_config == "bf16_params_fp32_grads":
        base_bytes = 18.0
        sharded_bytes = 6.0 + 12.0 / dp_size
    elif precision_config == "fp32_params_fp32_grads":
        base_bytes = 16.0
        sharded_bytes = 8.0 + 8.0 / dp_size
    else:
        raise ValueError(f"Unsupported precision_config: {precision_config}")

    return {
        "total_gpus": total_gpus,
        "tp_size": tp_size,
        "pp_size": pp_size,
        "cp_size": cp_size,
        "dp_size": dp_size,
        "base_bytes_per_param": base_bytes,
        "sharded_bytes_per_param": round(sharded_bytes, 4),
        "reduction_factor": round(base_bytes / sharded_bytes, 2),
    }


if __name__ == "__main__":
    z2 = compute_zero_memory_breakdown(ZeroMemoryConfig(10.0, 8, stage=2, mode="fp32_16psi"))
    z3 = compute_zero_memory_breakdown(ZeroMemoryConfig(10.0, 8, stage=3, mode="fp32_16psi"))
    print(f"10B FP32 on 8 GPUs -> ZeRO-2: {z2['total_per_gpu_gb']} GB | ZeRO-3: {z3['total_per_gpu_gb']} GB")
