#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.16: NeMo Framework and Model Customisation."""

from __future__ import annotations
import sys
from nemo_framework_customisation import (
    DomainFineTuneConfig,
    plan_nemo_domain_finetune,
    analyze_megatron_core_3d_recipe,
    evaluate_curator_and_data_pipeline,
    compare_customization_and_checkpoints,
    evaluate_nemo_governance_and_guardrails,
)


def run_lab() -> int:
    print("=== Chapter 14.16 Lab: NeMo Framework and Model Customisation Verification ===")
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

    # 1. NeMo Domain Customization Resource, Compute & Storage Planner (V14 Ch. 5 & Lab 03)
    ft = plan_nemo_domain_finetune(DomainFineTuneConfig())
    check(
        "1. Llama2-7B BF16 weights equal 14.0 GB and fit alongside 40.0 GB per-GPU activations inside an 80 GB A100 (54.0 GB < 80 GB)",
        ft["weights_bf16_gb"] == 14.0
        and ft["total_active_hbm_per_gpu_gb"] == 54.0
        and ft["fits_in_gpu_hbm"] is True,
    )

    check(
        "2. 8 GPUs x batch_size_per_gpu=8 x grad_accum=4 yields global batch 256 sequences and 524,288 tokens/step at max_length=2048",
        ft["global_batch_sequences"] == 256 and ft["tokens_per_step"] == 524_288,
    )

    check(
        "3. 168-hour (1-week) 8-GPU domain fine-tune records 640 budgeted GPU-hours (1,344 calendar GPU-hours)",
        ft["training_hours"] == 168
        and ft["budgeted_gpu_hours"] == 640
        and ft["calendar_gpu_hours"] == 1344,
    )

    check(
        "4. Retaining save_total_limit=3 checkpoints at 15.0 GB each uses 45.0 GB within the 50.0 GB checkpoint budget and 100.0 GB persistent floor",
        ft["retained_checkpoints_gb"] == 45.0
        and ft["checkpoints_budget_gb"] == 50.0
        and ft["min_persistent_storage_gb"] == 100.0,
    )

    check(
        "5. 500K-example domain corpus splits 90%/10% (450K train / 50K val) and decompresses 15.0x from 10.0 GB to 150.0 GB",
        ft["train_split_pct"] == 90.0
        and ft["val_split_pct"] == 10.0
        and ft["compression_ratio"] == 15.0,
    )

    check(
        "6. 8-GPU DGX A100 NVLink fabric provides 600 GB/s bidirectional per GPU (4.8 TB/s bisection) and 480.0-540.0 GB/s healthy nccl-tests busbw",
        ft["a100_nvlink_bidir_gbps"] == 600.0
        and ft["dgx_a100_bisection_tbps"] == 4.8
        and ft["expected_busbw_low_gbps"] == 480.0
        and ft["expected_busbw_high_gbps"] == 540.0,
    )

    lab03_ft = plan_nemo_domain_finetune(
        DomainFineTuneConfig(gpus=4, batch_size_per_gpu=8, grad_accum_steps=4, learning_rate=5e-5)
    )
    check(
        "7. Lab 03 4-GPU Kubernetes Job (batch=8, grad_accum=4, max_length=2048) processes 128 sequences (262,144 tokens) per step",
        lab03_ft["global_batch_sequences"] == 128 and lab03_ft["tokens_per_step"] == 262_144,
    )

    # 2. NeMo 2.0 / Megatron-Core 3D/5D Parallelism & Pipeline Bubble Calculator (V13 Ch. 7)
    mc = analyze_megatron_core_3d_recipe()
    check(
        "8. 175B model mixed-precision Adam state (16 bytes/param) totals 2,800.0 GB (2.73 GB/GPU across 1,024 GPUs under ZeRO-3)",
        mc["total_state_gb"] == 2800.0 and mc["zero3_state_per_gpu_gb"] == 2.73,
    )

    check(
        "9. Megatron-Core 3D layout (TP=8, PP=16, DP=8) spans 1,024 GPUs (128 nodes), placing 6 layers/stage and 1.37B params (21.875 GB state) per GPU",
        mc["world_size"] == 1024
        and mc["num_nodes"] == 128
        and mc["layers_per_stage"] == 6
        and mc["params_per_gpu_billions"] == 1.37
        and mc["state_per_gpu_3d_gb"] == 21.875,
    )

    check(
        "10. At global_batch=2048 and micro_batch=1 (M=256 per DP replica), 16-stage 1F1B pipeline bubble is 15/271 = 5.54% (~5.5%) vs ~27.3% at M=40",
        mc["micro_batches_per_dp"] == 256
        and mc["bubble_pct"] == 5.54
        and mc["bubble_at_m40_pct"] == 27.3,
    )

    check(
        "11. 50K-vocab x 12,288-hidden BF16 embedding/lm_head table adds 1.23 GB (~1.2 GB) and +40.0% micro-batch straggler latency on stages 0 and 15",
        mc["vocab_table_gb"] == 1.23 and mc["endpoint_stage_slowdown_pct"] == 40.0,
    )

    check(
        "12. Selective activation recomputation recovers 70-80% of memory savings while avoiding full recomputation's 30-50% backward slowdown",
        mc["selective_recompute_mem_saved_low_pct"] == 70.0
        and mc["selective_recompute_mem_saved_high_pct"] == 80.0
        and mc["full_recompute_backward_slowdown_low_pct"] == 30.0
        and mc["full_recompute_backward_slowdown_high_pct"] == 50.0,
    )

    check(
        "13. TP=8 fits inside a single 8-GPU NVLink node, whereas TP=16 or TP=32 crosses InfiniBand rails (tp_fits_in_nvlink_node=False)",
        mc["tp_fits_in_nvlink_node"] is True
        and analyze_megatron_core_3d_recipe(tp_size=16, pp_size=8, dp_size=8)["tp_fits_in_nvlink_node"] is False,
    )

    # 3. NeMo Curator & Data Pipeline Throughput Model (ASP Ch. 5, V05 Ch. 1, V14 Ch. 5)
    cur = evaluate_curator_and_data_pipeline()
    check(
        "14. dcgmi dmon utilization oscillating between 95% and 8% with DataLoader throughput 0.35 < 0.5 batches/sec flags data starvation",
        cur["util_max_pct"] == 95
        and cur["util_min_pct"] == 8
        and cur["util_oscillating"] is True
        and cur["dataloader_starved"] is True,
    )

    check(
        "15. Cutting DataLoader I/O wait from 30% to 5% delivers a 6.0x step speedup and avoids the 50% GPU idle waste of unoptimized pipelines",
        cur["io_wait_speedup_factor"] == 6.0 and cur["unoptimized_pipeline_gpu_waste_pct"] == 50.0,
    )

    check(
        "16. NVIDIA DALI reduces multimodal preprocessing CPU load 4.0x from 800% (8 cores) to 200% (2 cores), while raw JSONL over NFS traps MFU at 18%",
        cur["dali_cpu_cores_before"] == 8
        and cur["dali_cpu_cores_after"] == 2
        and cur["dali_cpu_reduction_factor"] == 4.0
        and cur["raw_jsonl_nfs_mfu_pct"] == 18.0,
    )

    check(
        "17. Batch-size halving test on a 100 GB/s NIC: dropping from 60 GB/s to 40 GB/s identifies a compute-bound workload, whereas staying at 60 GB/s is communication-bound",
        cur["bottleneck_when_drops_to_40"] == "compute_bound"
        and evaluate_curator_and_data_pipeline(nic_achieved_half_batch_gbps=60.0)["bottleneck_when_drops_to_40"]
        == "communication_bound",
    )

    # 4. Customization Recipes (SFT vs LoRA) & Checkpoint Economics (GAK Ch. 6, DAI Ch. 8, V05 Ch. 1)
    ckpt = compare_customization_and_checkpoints()
    check(
        "18. Rank-16 LoRA across 4 linear projections in 32 layers (hidden=4096, alpha=32) adds 16,777,216 trainable params (0.2089% < 1% of 8.03B, 33.55 MB in BF16, scale=2.0)",
        ckpt["total_lora_params"] == 16_777_216
        and ckpt["lora_under_one_percent"] is True
        and ckpt["lora_scaling_factor"] == 2.0
        and ckpt["lora_adapter_bf16_mb"] == 33.55,
    )

    check(
        "19. 8.03B Megatron/NeMo checkpoint totals 80.30 GB theoretical (16.06 GB BF16 weights + 64.24 GB FP32 Adam) and 108.0 GB actual across 4 x 27.0 GB .distcp shards",
        ckpt["weights_bf16_gb"] == 16.06
        and ckpt["adam_fp32_gb"] == 64.24
        and ckpt["theoretical_ckpt_gb"] == 80.30
        and ckpt["actual_distcp_gb"] == 108.0,
    )

    check(
        "20. Unstriped 1,024-GPU single-file checkpoint stalls step 1000 for 45.0 minutes vs 450.0 ms normal iteration (6,000.0x stall ratio)",
        ckpt["normal_step_ms"] == 450.0
        and ckpt["single_file_stall_minutes"] == 45.0
        and ckpt["single_file_stall_ratio"] == 6000.0,
    )

    # 5. NeMo Evaluator, NeMo Guardrails & Enterprise Lineage Governance (V14 Ch. 2, 5, 6, 12, Lab 03; GAK Ch. 5)
    gov = evaluate_nemo_governance_and_guardrails()
    check(
        "21. NeMo Evaluator gate verifies accuracy +2.5 pp (92.0% -> 94.5%), perplexity 18.7 -> 15.2 (18.7% reduction), ROUGE-1 +12.9% (0.31 -> 0.35), and BLEU +16.7% (0.24 -> 0.28)",
        gov["accuracy_gain_pp"] == 2.5
        and gov["perplexity_reduction_pct"] == 18.7
        and gov["rouge1_gain_pct"] == 12.9
        and gov["bleu_gain_pct"] == 16.7
        and gov["promotion_passed"] is True,
    )

    check(
        "22. NeMo Guardrails 5-rail pipeline (Input, Dialog, Retrieval, Execution, Output) increases latency from 45.0 ms to 250.0 ms (+205.0 ms overhead, 5.56x / ~5.5x multiplier)",
        gov["num_rail_types"] == 5
        and gov["after_input_ms"] == 60.0
        and gov["after_intent_ms"] == 90.0
        and gov["after_rag_ms"] == 190.0
        and gov["after_output_ms"] == 240.0
        and gov["total_guardrails_ms"] == 250.0
        and gov["guardrail_overhead_ms"] == 205.0
        and gov["latency_multiplier"] == 5.56,
    )

    check(
        "23. Guardrails policy enforces min_confidence=0.85, 2,555-day (~7-year) immutable S3 audit retention, and 10% canary rollout with 5% rejection alert threshold",
        gov["min_confidence_threshold"] == 0.85
        and gov["audit_retention_days"] == 2555
        and gov["audit_retention_years"] == 7
        and gov["canary_traffic_pct"] == 10
        and gov["max_rejection_spike_pct"] == 5,
    )

    check(
        "24. Enterprise NVAIE artifact governance enforces 90-day NGC token rotation with 30-day pre-expiry alerting",
        gov["token_rotation_days"] == 90 and gov["token_expiry_alert_days"] == 30,
    )

    failed_gate = evaluate_nemo_governance_and_guardrails(tuned_perplexity=19.4)
    check(
        "25. Regression in post-tuning perplexity (19.4 > 18.7 baseline) automatically blocks model promotion to NIM packaging (promotion_passed=False)",
        failed_gate["promotion_passed"] is False,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
