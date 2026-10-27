#!/usr/bin/env python3
"""Chapter 14.16 model: NeMo Framework and Model Customisation.

Models:
1. NeMo Domain Customization Resource, Compute & Storage Planner (`V14` Ch. 5 & Lab 03):
   - Llama2-7B domain fine-tuning resource budget: `8` x `A100 80GB` GPUs (`NVLink` `600 GB/s`
     bidirectional per GPU, `4.8 TB/s` DGX A100 bisection, `480-540 GB/s` `nccl-tests` `busbw`
     at `80-90%` efficiency), `168` training hours (`1` week), `640` budgeted GPU-hours (`1,344`
     calendar GPU-hours), `batch_size_per_gpu = 8`, `gradient_accumulation_steps = 4`,
     `learning_rate = 1e-5`, `bfloat16`, `FSDP`.
   - Storage footprint: `14 GB` `BF16` weights, `40 GB` per-GPU activations in HBM, `50 GB`
     saved checkpoints (`15 GB` per archive every `1,000` steps, `save_total_limit = 3`,
     `~5 min` recovery), `5 GB` logs/data, `100 GB` minimum persistent storage (`10 GB`
     compressed -> `150 GB` uncompressed dataset, `500K` examples = `450K` train + `50K` val).
   - Lab 03 `4`-GPU Kubernetes `batch/v1` `Job` (`120Gi` request / `150Gi` limit, `max_steps = 5000`,
     `save_steps = 1000`, `per_device_train_batch_size = 8`, `gradient_accumulation_steps = 4`,
     `learning_rate = 5e-5`, `warmup_steps = 500`, `weight_decay = 0.01`, `500,000` samples processed).
2. NeMo 2.0 / Megatron-Core 3D/5D Parallelism & Pipeline Bubble Calculator (`V13` Ch. 7, `DAI` Ch. 5 & 8):
   - `175B` GPT-3 (`96` layers) on `1,024` H100 GPUs (`128` nodes x `8` GPUs):
     * Full mixed-precision Adam state (`16` bytes/param) = `2,800 GB` (`2.734 GB/GPU` under ZeRO-3).
     * Megatron-Core 3D layout `TP=8, PP=16, DP=8` (`8 * 16 * 8 = 1,024` GPUs): `6` layers/stage,
       `175B / 128 = 1.367B` (`~1.37B`) params/GPU = `21.875 GB` (`~22 GB`) state per `80 GB` H100.
     * `1F1B` pipeline bubble: at global batch `2,048` and micro-batch `1`, `M = 2,048 / 8 = 256`
       micro-batches per DP replica -> `bubble = (PP - 1) / (M + PP - 1) = 15 / 271 = 5.54%` (`~5.5%`)
       vs `15 / 47 = 31.91%` (`~27%` at `M = 32` total micro-batches).
     * Stage `0` / Stage `15` `50,000 * 12,288 * 2 bytes = 1.2288 GB` (`~1.2 GB`) vocabulary embedding
       and `lm_head` straggler (`+40%` step time) mitigated via asymmetric layer splits (`5` layers on
       stages `0`/`15`) or interleaved virtual pipeline stages (`VP`).
3. NeMo Curator & Data Pipeline Throughput Model (`ASP` Ch. 5, `V05` Ch. 1, `V14` Ch. 5):
   - Offline GPU curation (`DocumentDataset` JSONL/Parquet -> `.bin` + `.idx` memory-mapped files
     and `N` pre-shuffled epoch copies) vs raw JSONL over NFS (`18%` MFU).
   - DataLoader I/O wait reduction from `30%` to `5%` (`6x` step speedup); `50%` GPU idle waste from
     poorly tuned input pipelines; `DALI` CPU reduction from `800%` (`8` cores) to `200%` (`2` cores).
   - `dcgmi dmon -c 10` oscillation (`95% -> 15% -> 8% -> 88%` util, `320W -> 295W -> 280W -> 310W`)
     and DataLoader `< 0.5 batches/sec` threshold; batch-size halving/doubling test (`60 GB/s` vs
     `40 GB/s` on a `100 GB/s` NIC).
4. Customization Recipes (Full SFT vs PEFT LoRA/DoRA vs DPO/GRPO) & Checkpoint Economics (`GAK` Ch. 6, `DAI` Ch. 8):
   - Full SFT (`100,000+` examples, `100%` trainable parameters) vs PEFT LoRA (`100-1,000` examples,
     `< 1%` trainable parameters on `8B` model, `1%-10%` adapter size, dynamic multi-LoRA serving).
   - Distributed checkpointing (`.distcp` / DCP vs legacy `.nemo` single-file tarballs): `8.03B` model
     (`16.06 GB` `BF16` weights + `64.24 GB` `FP32` Adam = `80.30 GB` theoretical vs `108.0 GB` actual
     across `4 x 27.0 GB` `.distcp` shards); prevents the `1,024`-GPU `450 ms -> 45 min` single-file stall.
5. NeMo Evaluator, NeMo Guardrails & Enterprise Lineage Governance (`V14` Ch. 2, 5, 6, 12, Lab 03; `GAK` Ch. 5):
   - Evaluation gate: accuracy `92.0% -> 94.5%` (`+2.5` pp), loss `2.15 -> 1.87` (`12.8%` improvement),
     perplexity `18.7 -> 15.2` (`18.7%` reduction), `ROUGE-1` `0.31 -> 0.35` (`+12.9%`), `BLEU` `0.24 -> 0.28` (`+16.7%`).
   - NeMo Guardrails 5-rail latency budget: `45 ms` base LLM + `15 ms` input PII/length (`60 ms`) +
     `30 ms` intent classifier (`90 ms`) + `100 ms` RAG retrieval (`190 ms`) + `50 ms` output fact-check
     (`240 ms`) + `10 ms` audit log = `250 ms` total (`5.56x` / `5.5x` slower, `+205 ms` overhead).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class DomainFineTuneConfig:
    model_name: str = "llama2-7b-hf"
    params_billions: float = 7.0
    dataset_examples: int = 500_000
    train_examples: int = 450_000
    val_examples: int = 50_000
    compressed_gb: float = 10.0
    uncompressed_gb: float = 150.0
    max_seq_length: int = 2048
    gpus: int = 8
    gpu_memory_gb: int = 80
    training_hours: int = 168
    budgeted_gpu_hours: int = 640
    batch_size_per_gpu: int = 8
    grad_accum_steps: int = 4
    learning_rate: float = 1e-5
    checkpoint_interval_steps: int = 1000
    save_total_limit: int = 3
    single_checkpoint_gb: float = 15.0
    checkpoints_budget_gb: float = 50.0
    activations_per_gpu_gb: float = 40.0
    logs_gb: float = 5.0
    min_persistent_storage_gb: float = 100.0


def plan_nemo_domain_finetune(cfg: DomainFineTuneConfig = DomainFineTuneConfig()) -> Dict[str, float | int | str | bool]:
    """Computes compute, memory, network, and storage requirements for a NeMo domain fine-tune."""
    weights_bf16_gb = cfg.params_billions * 2.0  # 2 bytes/param in BF16 = 14.0 GB
    global_batch_sequences = cfg.gpus * cfg.batch_size_per_gpu * cfg.grad_accum_steps
    tokens_per_step = global_batch_sequences * cfg.max_seq_length
    calendar_gpu_hours = cfg.gpus * cfg.training_hours
    retained_checkpoints_gb = cfg.save_total_limit * cfg.single_checkpoint_gb
    total_active_hbm_per_gpu_gb = weights_bf16_gb + cfg.activations_per_gpu_gb
    fits_in_gpu_hbm = total_active_hbm_per_gpu_gb < cfg.gpu_memory_gb
    compression_ratio = cfg.uncompressed_gb / cfg.compressed_gb
    train_split_pct = round(100.0 * cfg.train_examples / cfg.dataset_examples, 1)
    val_split_pct = round(100.0 * cfg.val_examples / cfg.dataset_examples, 1)

    # A100 SXM4 NVLink 3rd-gen bidirectional bandwidth = 600 GB/s per GPU (4.8 TB/s aggregate on 8 GPUs)
    a100_nvlink_bidir_gbps = 600.0
    dgx_a100_bisection_tbps = (cfg.gpus * a100_nvlink_bidir_gbps) / 1000.0
    expected_busbw_low_gbps = 0.80 * a100_nvlink_bidir_gbps  # 480 GB/s
    expected_busbw_high_gbps = 0.90 * a100_nvlink_bidir_gbps  # 540 GB/s

    return {
        "model_name": cfg.model_name,
        "weights_bf16_gb": round(weights_bf16_gb, 2),
        "activations_per_gpu_gb": cfg.activations_per_gpu_gb,
        "total_active_hbm_per_gpu_gb": round(total_active_hbm_per_gpu_gb, 2),
        "fits_in_gpu_hbm": fits_in_gpu_hbm,
        "global_batch_sequences": global_batch_sequences,
        "tokens_per_step": tokens_per_step,
        "training_hours": cfg.training_hours,
        "budgeted_gpu_hours": cfg.budgeted_gpu_hours,
        "calendar_gpu_hours": calendar_gpu_hours,
        "retained_checkpoints_gb": round(retained_checkpoints_gb, 2),
        "checkpoints_budget_gb": cfg.checkpoints_budget_gb,
        "min_persistent_storage_gb": cfg.min_persistent_storage_gb,
        "compression_ratio": round(compression_ratio, 2),
        "train_split_pct": train_split_pct,
        "val_split_pct": val_split_pct,
        "a100_nvlink_bidir_gbps": a100_nvlink_bidir_gbps,
        "dgx_a100_bisection_tbps": round(dgx_a100_bisection_tbps, 2),
        "expected_busbw_low_gbps": round(expected_busbw_low_gbps, 1),
        "expected_busbw_high_gbps": round(expected_busbw_high_gbps, 1),
    }


def analyze_megatron_core_3d_recipe(
    params_billions: float = 175.0,
    num_layers: int = 96,
    hidden_size: int = 12288,
    vocab_size: int = 50000,
    tp_size: int = 8,
    pp_size: int = 16,
    dp_size: int = 8,
    gpus_per_node: int = 8,
    global_batch_size: int = 2048,
    micro_batch_size: int = 1,
) -> Dict[str, float | int | bool]:
    """Evaluates Megatron-Core 3D parallelism memory, pipeline bubble, and stage imbalance."""
    world_size = tp_size * pp_size * dp_size
    num_nodes = world_size // gpus_per_node
    model_parallel_size = tp_size * pp_size
    layers_per_stage = num_layers // pp_size

    # Mixed-precision Adam accounting: 4B FP32 master weights + 4B FP32 grads + 8B Adam states = 16 B/param
    total_state_gb = params_billions * 16.0  # 2,800 GB for 175B
    zero3_state_per_gpu_gb = total_state_gb / world_size  # 2.734375 GB/GPU
    params_per_gpu_billions = params_billions / model_parallel_size  # 1.3671875B (~1.37B)
    state_per_gpu_3d_gb = params_per_gpu_billions * 16.0  # 21.875 GB (~22 GB)

    # 1F1B pipeline bubble: (PP - 1) / (M + PP - 1) where M = global_batch_size / (dp_size * micro_batch_size)
    micro_batches_per_dp = global_batch_size // (dp_size * micro_batch_size)  # 256
    bubble_fraction = (pp_size - 1) / (micro_batches_per_dp + pp_size - 1)  # 15 / 271 = 5.535%
    small_batch_m = 4  # e.g., 32 total micro-batches across 8 DP replicas or 32 micro-batches
    bubble_at_32_total_pct = 100.0 * (pp_size - 1) / ((32 // dp_size) + pp_size - 1)  # 15/19 or 15/47
    bubble_at_m40_pct = 100.0 * (pp_size - 1) / (40 + pp_size - 1)  # 15 / 55 = 27.27% (~27%)

    # Stage 0 / Stage 15 vocabulary embedding / lm_head table size in BF16 (2 bytes)
    vocab_table_gb = (vocab_size * hidden_size * 2) / 1e9  # 50,000 * 12,288 * 2 = 1.2288 GB (~1.2 GB)
    endpoint_stage_slowdown_pct = 40.0  # Stage 0 and 15 take ~40% longer per micro-batch

    # Selective activation recomputation vs full recomputation
    selective_recompute_mem_saved_low_pct = 70.0
    selective_recompute_mem_saved_high_pct = 80.0
    full_recompute_backward_slowdown_low_pct = 30.0
    full_recompute_backward_slowdown_high_pct = 50.0

    tp_fits_in_nvlink_node = tp_size <= gpus_per_node and (gpus_per_node % tp_size == 0)

    return {
        "world_size": world_size,
        "num_nodes": num_nodes,
        "model_parallel_size": model_parallel_size,
        "layers_per_stage": layers_per_stage,
        "total_state_gb": round(total_state_gb, 2),
        "zero3_state_per_gpu_gb": round(zero3_state_per_gpu_gb, 2),
        "params_per_gpu_billions": round(params_per_gpu_billions, 2),
        "state_per_gpu_3d_gb": round(state_per_gpu_3d_gb, 3),
        "micro_batches_per_dp": micro_batches_per_dp,
        "bubble_pct": round(100.0 * bubble_fraction, 2),
        "bubble_at_m40_pct": round(bubble_at_m40_pct, 1),
        "vocab_table_gb": round(vocab_table_gb, 2),
        "endpoint_stage_slowdown_pct": endpoint_stage_slowdown_pct,
        "selective_recompute_mem_saved_low_pct": selective_recompute_mem_saved_low_pct,
        "selective_recompute_mem_saved_high_pct": selective_recompute_mem_saved_high_pct,
        "full_recompute_backward_slowdown_low_pct": full_recompute_backward_slowdown_low_pct,
        "full_recompute_backward_slowdown_high_pct": full_recompute_backward_slowdown_high_pct,
        "tp_fits_in_nvlink_node": tp_fits_in_nvlink_node,
    }


def evaluate_curator_and_data_pipeline(
    dcgm_util_samples: List[int] | None = None,
    dataloader_batches_per_sec: float = 0.35,
    io_wait_before_pct: float = 30.0,
    io_wait_after_pct: float = 5.0,
    dali_cpu_before_pct: float = 800.0,
    dali_cpu_after_pct: float = 200.0,
    nic_capacity_gbps: float = 100.0,
    nic_achieved_baseline_gbps: float = 60.0,
    nic_achieved_half_batch_gbps: float = 40.0,
) -> Dict[str, float | bool | str]:
    """Diagnoses NeMo data-loading starvation, NeMo Curator .bin/.idx gains, and comm-vs-compute limits."""
    if dcgm_util_samples is None:
        dcgm_util_samples = [95, 15, 8, 88]

    util_max = max(dcgm_util_samples)
    util_min = min(dcgm_util_samples)
    util_oscillating = (util_max >= 85) and (util_min <= 20)
    dataloader_starved = dataloader_batches_per_sec < 0.5

    io_wait_speedup_factor = io_wait_before_pct / io_wait_after_pct  # 30% / 5% = 6.0x
    dali_cpu_cores_before = int(dali_cpu_before_pct // 100)  # 8 cores
    dali_cpu_cores_after = int(dali_cpu_after_pct // 100)  # 2 cores
    dali_cpu_reduction_factor = dali_cpu_before_pct / dali_cpu_after_pct  # 4.0x

    # Batch-size halving diagnosis (ASP Ch. 5):
    # If halving batch size keeps NIC at 60 GB/s -> communication bound; if it drops to 40 GB/s -> compute bound
    bottleneck_when_drops_to_40 = (
        "compute_bound" if nic_achieved_half_batch_gbps < nic_achieved_baseline_gbps else "communication_bound"
    )

    return {
        "util_max_pct": util_max,
        "util_min_pct": util_min,
        "util_oscillating": util_oscillating,
        "dataloader_batches_per_sec": dataloader_batches_per_sec,
        "dataloader_starved": dataloader_starved,
        "io_wait_speedup_factor": round(io_wait_speedup_factor, 2),
        "dali_cpu_cores_before": dali_cpu_cores_before,
        "dali_cpu_cores_after": dali_cpu_cores_after,
        "dali_cpu_reduction_factor": round(dali_cpu_reduction_factor, 2),
        "raw_jsonl_nfs_mfu_pct": 18.0,
        "unoptimized_pipeline_gpu_waste_pct": 50.0,
        "nic_capacity_gbps": nic_capacity_gbps,
        "nic_achieved_baseline_gbps": nic_achieved_baseline_gbps,
        "nic_achieved_half_batch_gbps": nic_achieved_half_batch_gbps,
        "bottleneck_when_drops_to_40": bottleneck_when_drops_to_40,
    }


def compare_customization_and_checkpoints(
    base_params_billions: float = 8.03,
    num_layers: int = 32,
    hidden_size: int = 4096,
    lora_rank: int = 16,
    lora_alpha: int = 32,
    adapted_linear_layers_per_block: int = 4,
    distcp_num_shards: int = 4,
    distcp_shard_gb: float = 27.0,
) -> Dict[str, float | int | bool]:
    """Compares Full SFT vs PEFT LoRA parameter/memory footprint and .nemo vs .distcp checkpoints."""
    # LoRA parameter count: each adapted linear layer (d_in = d_out = hidden_size) adds 2 * r * d params
    lora_params_per_linear = 2 * lora_rank * hidden_size
    total_lora_params = num_layers * adapted_linear_layers_per_block * lora_params_per_linear
    base_params = int(base_params_billions * 1e9)
    lora_trainable_pct = 100.0 * total_lora_params / base_params
    lora_scaling_factor = lora_alpha / lora_rank
    lora_adapter_bf16_mb = (total_lora_params * 2) / 1e6

    # 8.03B Megatron-LM / NeMo distributed checkpoint sizing (DAI Ch. 8):
    # 16.06 GB BF16 weights + 64.24 GB FP32 Adam states = 80.30 GB theoretical vs 108.0 GB actual (4 x 27.0 GB .distcp)
    weights_bf16_gb = round(base_params_billions * 2.0, 2)  # 16.06 GB
    adam_fp32_gb = round(base_params_billions * 8.0, 2)  # 64.24 GB
    theoretical_ckpt_gb = round(weights_bf16_gb + adam_fp32_gb, 2)  # 80.30 GB
    actual_distcp_gb = round(distcp_num_shards * distcp_shard_gb, 2)  # 108.0 GB

    # 1,024-GPU checkpoint stall comparison (V05 Ch. 1):
    # Normal step = 450 ms (0.45 s); unstriped single-file checkpoint at step 1000 = 45 minutes (2,700 s = 6,000x step)
    normal_step_ms = 450.0
    single_file_stall_minutes = 45.0
    single_file_stall_ratio = (single_file_stall_minutes * 60.0 * 1000.0) / normal_step_ms  # 6,000x

    return {
        "total_lora_params": total_lora_params,
        "lora_trainable_pct": round(lora_trainable_pct, 4),
        "lora_under_one_percent": lora_trainable_pct < 1.0,
        "lora_scaling_factor": round(lora_scaling_factor, 2),
        "lora_adapter_bf16_mb": round(lora_adapter_bf16_mb, 2),
        "weights_bf16_gb": weights_bf16_gb,
        "adam_fp32_gb": adam_fp32_gb,
        "theoretical_ckpt_gb": theoretical_ckpt_gb,
        "actual_distcp_gb": actual_distcp_gb,
        "distcp_num_shards": distcp_num_shards,
        "distcp_shard_gb": distcp_shard_gb,
        "normal_step_ms": normal_step_ms,
        "single_file_stall_minutes": single_file_stall_minutes,
        "single_file_stall_ratio": round(single_file_stall_ratio, 1),
    }


def evaluate_nemo_governance_and_guardrails(
    baseline_accuracy_pct: float = 92.0,
    tuned_accuracy_pct: float = 94.5,
    baseline_loss: float = 2.15,
    tuned_train_loss: float = 1.87,
    tuned_eval_loss: float = 1.92,
    baseline_perplexity: float = 18.7,
    tuned_perplexity: float = 15.2,
    baseline_rouge1: float = 0.31,
    tuned_rouge1: float = 0.35,
    baseline_bleu: float = 0.24,
    tuned_bleu: float = 0.28,
    base_inference_ms: float = 45.0,
    input_rail_ms: float = 15.0,
    intent_rail_ms: float = 30.0,
    rag_rail_ms: float = 100.0,
    output_rail_ms: float = 50.0,
    audit_log_ms: float = 10.0,
) -> Dict[str, float | int | bool | List[str]]:
    """Evaluates NeMo Evaluator promotion gates, NeMo Guardrails latency budget, and compliance rules."""
    accuracy_gain_pp = round(tuned_accuracy_pct - baseline_accuracy_pct, 2)  # +2.5 pp
    loss_improvement_pct = round(100.0 * (baseline_loss - tuned_train_loss) / baseline_loss, 1)  # 13.0% / 12.8% Lab 03
    perplexity_reduction_pct = round(100.0 * (baseline_perplexity - tuned_perplexity) / baseline_perplexity, 1)  # 18.7%
    rouge1_gain_pct = round(100.0 * (tuned_rouge1 - baseline_rouge1) / baseline_rouge1, 1)  # 12.9%
    bleu_gain_pct = round(100.0 * (tuned_bleu - baseline_bleu) / baseline_bleu, 1)  # 16.7%

    promotion_passed = (
        (tuned_accuracy_pct > baseline_accuracy_pct)
        and (tuned_eval_loss < baseline_loss)
        and (tuned_perplexity < baseline_perplexity)
        and (tuned_rouge1 > baseline_rouge1)
        and (tuned_bleu > baseline_bleu)
    )

    # NeMo Guardrails 5-rail cumulative latency breakdown (V14 Ch. 6 & GAK Ch. 5)
    after_input_ms = base_inference_ms + input_rail_ms  # 60 ms
    after_intent_ms = after_input_ms + intent_rail_ms  # 90 ms
    after_rag_ms = after_intent_ms + rag_rail_ms  # 190 ms
    after_output_ms = after_rag_ms + output_rail_ms  # 240 ms
    total_guardrails_ms = after_output_ms + audit_log_ms  # 250 ms
    latency_multiplier = round(total_guardrails_ms / base_inference_ms, 2)  # 5.56x (~5.5x)
    guardrail_overhead_ms = round(total_guardrails_ms - base_inference_ms, 1)  # 205.0 ms

    rail_types = ["input_rails", "dialog_rails", "retrieval_rails", "execution_rails", "output_rails"]

    return {
        "accuracy_gain_pp": accuracy_gain_pp,
        "loss_improvement_pct": loss_improvement_pct,
        "perplexity_reduction_pct": perplexity_reduction_pct,
        "rouge1_gain_pct": rouge1_gain_pct,
        "bleu_gain_pct": bleu_gain_pct,
        "promotion_passed": promotion_passed,
        "base_inference_ms": base_inference_ms,
        "after_input_ms": after_input_ms,
        "after_intent_ms": after_intent_ms,
        "after_rag_ms": after_rag_ms,
        "after_output_ms": after_output_ms,
        "total_guardrails_ms": total_guardrails_ms,
        "guardrail_overhead_ms": guardrail_overhead_ms,
        "latency_multiplier": latency_multiplier,
        "rail_types": rail_types,
        "num_rail_types": len(rail_types),
        "audit_retention_days": 2555,
        "audit_retention_years": 7,
        "min_confidence_threshold": 0.85,
        "canary_traffic_pct": 10,
        "max_rejection_spike_pct": 5,
        "token_rotation_days": 90,
        "token_expiry_alert_days": 30,
    }


if __name__ == "__main__":
    ft = plan_nemo_domain_finetune()
    mc = analyze_megatron_core_3d_recipe()
    cur = evaluate_curator_and_data_pipeline()
    ckpt = compare_customization_and_checkpoints()
    gov = evaluate_nemo_governance_and_guardrails()
    print("NeMo Domain Fine-Tune Plan:", ft)
    print("Megatron-Core 175B 3D Recipe:", mc)
    print("NeMo Curator & Data Pipeline:", cur)
    print("Customization & Checkpoints:", ckpt)
    print("Evaluator & Guardrails:", gov)
