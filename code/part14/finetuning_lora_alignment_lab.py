#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.13: Fine-tuning: SFT, LoRA and QLoRA, preference alignment."""

from __future__ import annotations
import sys
from finetuning_lora_alignment import (
    NF4_QUANT_LEVELS,
    evaluate_adaptation_benchmarks,
    compute_finetuning_vs_prompting_economics,
    compute_training_and_inference_memory,
    compute_lora_adapter_math,
    evaluate_model_lora_configurations,
    compute_dora_update,
    quantize_dequantize_nf4_block,
    compute_qlora_double_quant_and_memory,
    compute_sft_batch_and_packing,
    compute_weighted_sft_loss,
    compute_bradley_terry_rm,
    compute_dpo_step_metrics,
    compute_grpo_group_advantages,
    compare_alignment_vram_budgets,
    slerp_vectors,
    ties_and_dare_merge,
)


def run_lab() -> int:
    print("=== Chapter 14.13 Lab: Fine-tuning (SFT, LoRA/QLoRA, Preference Alignment) Verification ===")
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

    # 1. Adaptation Decision Matrix & Benchmark Evidence (`AIE` Ch. 7 Tables 7-1 & 7-2, `LLO` Ch. 5)
    bench = evaluate_adaptation_benchmarks()
    check(
        "1. Table 7-1: Zero-shot GPT-4-0314 (87.15 FiQA, 76.48 ConvFinQA) outperforms 50B BloombergGPT (75.07, 43.41; 1.3M A100 GPU hours, $1.3M-$2.6M)",
        bench["financial_benchmarks"]["GPT-4-0314"]["fiqa_f1"] == 87.15
        and bench["financial_benchmarks"]["BloombergGPT_50B"]["fiqa_f1"] == 75.07
        and bench["financial_benchmarks"]["BloombergGPT_50B"]["a100_gpu_hours"] == 1_300_000,
    )

    check(
        "2. Table 7-2 (Ovadia et al., 2024): Base + RAG outperforms fine-tuning on current-events QA across Mistral-7B (0.875 vs 0.588), Llama-2-7B (0.585 vs 0.392), and Orca-2-7B (0.876 vs 0.566)",
        bench["ovadia_rag_vs_ft"]["Mistral-7B"]["base_rag"] == 0.875
        and bench["ovadia_rag_vs_ft"]["Llama-2-7B"]["base_rag"] == 0.585
        and bench["ovadia_rag_vs_ft"]["Orca-2-7B"]["base_rag"] == 0.876
        and bench["ovadia_rag_vs_ft"]["mmlu_rag_plus_ft_improves_pct"] == 43.0,
    )

    check(
        "3. Task-specific efficiency & context extension: Grammarly Flan-T5 beats 60x larger GPT-3 with 82,000 SFT pairs; Code Llama extends Llama 2 context from 4,096 to 16,384 tokens",
        bench["flan_t5_vs_gpt3_size_ratio"] == 60
        and bench["flan_t5_sft_pairs"] == 82_000
        and bench["code_llama_context_base"] == 4096
        and bench["code_llama_context_extended"] == 16384,
    )

    econ = compute_finetuning_vs_prompting_economics(
        finetune_tokens_millions=1.0,
        finetune_cost_per_m_tokens_usd=25_000.0,
        extra_prompt_tokens_per_request=2000,
        inference_input_cost_per_m_tokens_usd=2.50,
        requests_per_year=500_000,
        model_lifespan_years=2.0,
    )
    check(
        "4. Fine-tuning vs Prompting economics (LLMOps Ch. 5): $25,000 upfront API fine-tune vs $2,500/yr prompt overhead requires 10.0 years to break even (uneconomical for a 2.0-year model lifespan)",
        econ["upfront_ft_cost_usd"] == 25_000.0
        and econ["annual_prompt_overhead_usd"] == 2_500.0
        and econ["breakeven_years"] == 10.0
        and econ["economical_within_lifespan"] is False,
    )

    # 2. Full Fine-Tuning & Inference Memory Math (`AIE` Ch. 7 & `LEH` Ch. 5)
    mem_13b = compute_training_and_inference_memory(total_params_billions=13.0, trainable_params_billions=13.0)
    mem_13b_peft = compute_training_and_inference_memory(total_params_billions=13.0, trainable_params_billions=1.0)
    check(
        "5. 13B model in 16-bit (AIE Ch. 7): weights = 26.0 GB, inference (1.2x) = 31.2 GB, full Adam grad+opt states = 78.0 GB vs 6.0 GB for 1B trainable parameters",
        mem_13b["weights_gb"] == 26.0
        and mem_13b["inference_total_gb"] == 31.2
        and mem_13b["grad_and_opt_gb"] == 78.0
        and mem_13b_peft["grad_and_opt_gb"] == 6.0,
    )

    mem_7b = compute_training_and_inference_memory(total_params_billions=7.0, trainable_params_billions=7.0)
    mem_70b = compute_training_and_inference_memory(total_params_billions=70.0, trainable_params_billions=70.0)
    check(
        "6. 7B and 70B full fine-tuning memory: 7B 16-bit total = 56.0 GB (14 GB weights + 42 GB states); 16-byte/param baseline (LEH Ch. 5) = 112.0 GB for 7B and 1,120.0 GB for 70B",
        mem_7b["training_16bit_total_gb"] == 56.0
        and mem_7b["baseline_16byte_gb"] == 112.0
        and mem_70b["baseline_16byte_gb"] == 1120.0,
    )

    # 3. LoRA Matrix Math & Multi-LoRA Serving Storage (`AIE` Ch. 7, `LEH` Ch. 5, `KFG` Ch. 4)
    lora_4096 = compute_lora_adapter_math(d_in=4096, d_out=4096, rank=8, alpha=16.0, num_adapters=100)
    check(
        "7. Single 4096x4096 matrix (16,777,216 / 16.8M params) with r=8 has 65,536 LoRA params (256.0x compression) and scaling factor alpha/r = 2.0",
        lora_4096["full_matrix_params"] == 16_777_216
        and lora_4096["lora_matrix_params"] == 65_536
        and lora_4096["compression_ratio"] == 256.0
        and lora_4096["scaling_factor"] == 2.0,
    )

    check(
        "8. Multi-LoRA serving storage for 100 customers (AIE Ch. 7): 100 merged matrices = 1.68B params vs 1 base matrix + 100 (A, B) adapters = 23.3M params",
        lora_4096["book_option1_billions"] == 1.68
        and lora_4096["book_option2_millions_exact"] == 23.3,
    )

    model_cfg = evaluate_model_lora_configurations()
    check(
        "9. GPT-3 175B LoRA (96 layers, d=12,288, r=2 across Wq, Wk, Wv, Wo): 196,608 params/layer and 18,874,368 total params (37.7 MB in 16-bit vs 350 GB base weights), scoring 73.7% WikiSQL and 91.7% MultiNLI",
        model_cfg["gpt3_params_per_layer"] == 196_608
        and model_cfg["gpt3_total_lora_params"] == 18_874_368
        and model_cfg["gpt3_adapter_mb_16bit"] == 37.7
        and model_cfg["gpt3_base_gb_16bit"] == 350
        and model_cfg["gpt3_table_7_5"]["Wq_Wk_Wv_Wo_r2"]["multinli"] == 91.7,
    )

    check(
        "10. Llama 2 13B (r=2 on Wq, Wk -> 3,276,800 / 3.28M params = 6.55 MB vs 26 GB) and Llama 3 8B (all 7 linear modules: r=16 -> 41,943,040 / ~42M params = 0.5196%; r=32 + lm_head -> 88,121,344 params vs 4,628,721,664)",
        model_cfg["llama2_13b_lora_params"] == 3_276_800
        and model_cfg["llama2_13b_adapter_mb"] == 6.55
        and model_cfg["llama3_8b_r16_params"] == 41_943_040
        and model_cfg["llama3_8b_r32_with_lm_head_params"] == 88_121_344,
    )

    # 4. DoRA (Weight-Decomposed Low-Rank Adaptation)
    dora_w = compute_dora_update(
        w0=[[3.0, 0.0], [4.0, 5.0]],
        lora_b=[[0.0, 0.0], [0.0, 0.0]],
        lora_a=[[1.0, 1.0], [1.0, 1.0]],
        magnitude=[5.0, 5.0],
        alpha=4.0,
        rank=2,
    )
    check(
        "11. At initialization (B = 0), DoRA preserves exact base weights W_0 when m = ||W_0||_c ([3.0, 0.0], [4.0, 5.0])",
        dora_w == [[3.0, 0.0], [4.0, 5.0]],
    )

    # 5. QLoRA Internals: NF4 Quantization, Double Quantization & Memory Benchmarks
    nf4_res = quantize_dequantize_nf4_block([-0.8, -0.4, 0.0, 0.2, 0.8])
    check(
        "12. 4-bit NormalFloat (NF4) codebook has 16 quantile levels in [-1.0, 1.0] with exact 0.0 representation at index 7",
        len(NF4_QUANT_LEVELS) == 16
        and NF4_QUANT_LEVELS[0] == -1.0
        and NF4_QUANT_LEVELS[7] == 0.0
        and NF4_QUANT_LEVELS[15] == 1.0
        and nf4_res["nf4_indices"][2] == 7
        and nf4_res["max_abs_error"] < 0.025,
    )

    qlora_math = compute_qlora_double_quant_and_memory(model_params_billions=65.0, block_size_b1=64, double_quant_block_b2=256)
    check(
        "13. QLoRA Double Quantization (B1=64, B2=256) cuts scale overhead from 0.500 to 0.127 bits/param (saving 0.373 bits/param, or 3.03 GB on 65B, giving 4.127 effective bits/param)",
        qlora_math["single_quant_overhead_bits"] == 0.5
        and qlora_math["double_quant_overhead_bits"] == 0.127
        and qlora_math["saved_bits_per_param"] == 0.373
        and qlora_math["effective_bits_per_param"] == 4.127
        and qlora_math["saved_gb_for_model"] == 3.03,
    )

    check(
        "14. 7B LoRA vs QLoRA benchmark (LEH Ch. 5): QLoRA cuts init VRAM from 14.0 GB to 9.1 GB (35% reduction) and peak training VRAM from 15.6 GB to 9.3 GB (~40% reduction) with ~30% slower speed",
        qlora_math["leh_7b_comparison"]["lora_init_gb"] == 14.0
        and qlora_math["leh_7b_comparison"]["qlora_init_gb"] == 9.1
        and qlora_math["leh_7b_comparison"]["lora_peak_train_gb"] == 15.6
        and qlora_math["leh_7b_comparison"]["qlora_peak_train_gb"] == 9.3
        and qlora_math["leh_7b_comparison"]["qlora_slowdown_pct"] == 30.0,
    )

    check(
        "15. Guanaco 65B QLoRA (AIE Ch. 7 Table 7-7): 41 GB footprint fits on a single 48 GB GPU and achieves 1022 Elo vs ChatGPT 966 Elo",
        qlora_math["guanaco_table_7_7"]["Guanaco-65B"]["size_gb"] == 41
        and qlora_math["guanaco_table_7_7"]["Guanaco-65B"]["elo"] == 1022
        and qlora_math["guanaco_table_7_7"]["ChatGPT"]["elo"] == 966,
    )

    # 6. SFT Hyperparameters, Effective Batch Size, Packing & Prompt Loss Weighting
    pack_1gpu = compute_sft_batch_and_packing(per_device_batch_size=2, num_gpus=1, gradient_accumulation_steps=8)
    pack_2gpu = compute_sft_batch_and_packing(per_device_batch_size=4, num_gpus=2, gradient_accumulation_steps=4)
    check(
        "16. Effective batch size formula (LEH Ch. 5): 2 * 1 * 8 = 16 (TwinLlama-3.1-8B SFT) and 4 * 2 * 4 = 32 (2-GPU example)",
        pack_1gpu["effective_batch_size"] == 16 and pack_2gpu["effective_batch_size"] == 32,
    )

    check(
        "17. Sequence packing (max_seq_length=1024) packs 8 short (210-280 token) samples into 2 sequences (4.0x slot reduction), raising token utilization from 23.93% to 95.7%",
        pack_1gpu["unpacked_slots"] == 8
        and pack_1gpu["packed_slots"] == 2
        and pack_1gpu["slot_reduction_factor"] == 4.0
        and pack_1gpu["packed_utilization_pct"] == 95.7,
    )

    loss_completion_only = compute_weighted_sft_loss([2.0, 2.0, 2.0, 2.0], [0.5, 0.5], prompt_loss_weight=0.0)
    loss_default_10pct = compute_weighted_sft_loss([2.0, 2.0, 2.0, 2.0], [0.5, 0.5], prompt_loss_weight=0.1)
    loss_full_100pct = compute_weighted_sft_loss([2.0, 2.0, 2.0, 2.0], [0.5, 0.5], prompt_loss_weight=1.0)
    check(
        "18. Prompt loss weight (AIE Ch. 7): 0% masks prompt tokens completely (loss=0.5), 10% weights prompts lightly (loss=0.75), and 100% weights prompt and response tokens equally (loss=1.5)",
        loss_completion_only == 0.5 and loss_default_10pct == 0.75 and loss_full_100pct == 1.5,
    )

    # 7. Preference Alignment: Bradley-Terry RM, RLHF (PPO), DPO, and GRPO
    bt_rm = compute_bradley_terry_rm(r_chosen=2.4, r_rejected=0.4, num_ranked_candidates=3)
    check(
        "19. Bradley-Terry Reward Model (AIE Ch. 2): ranking 3 responses (A > B > C) yields 3 pairs ($3.50 comparison vs $25.00 write cost, 73% agreement), and r_w - r_l = 2.0 gives P(chosen) = 88.08%",
        bt_rm["num_pairs_from_k_ranked"] == 3
        and bt_rm["comparison_cost_usd"] == 3.50
        and bt_rm["demonstration_write_cost_usd"] == 25.00
        and round(bt_rm["prob_chosen"] * 100.0, 2) == 88.08,
    )

    dpo_metrics = compute_dpo_step_metrics(
        policy_chosen_logps=[-10.0, -8.0, -12.0, -9.0],
        policy_rejected_logps=[-15.0, -14.0, -11.0, -16.0],
        ref_chosen_logps=[-12.0, -10.0, -12.0, -11.0],
        ref_rejected_logps=[-12.0, -11.0, -13.0, -12.0],
        beta=0.5,
    )
    check(
        "20. DPO metrics (beta=0.5, LEH Ch. 6): positive chosen reward (+0.75), negative rejected reward (-1.0), positive margin (+1.75), and 75.0% reward accuracy (3 of 4 pairs)",
        dpo_metrics["mean_chosen_reward"] == 0.75
        and dpo_metrics["mean_rejected_reward"] == -1.0
        and dpo_metrics["mean_reward_margin"] == 1.75
        and dpo_metrics["reward_accuracy"] == 0.75,
    )

    grpo = compute_grpo_group_advantages([1.0, 2.0, 3.0, 6.0])
    check(
        "21. DeepSeek GRPO group-normalized advantages over G=4 completions sum to 0.0 with positive advantage (+1.566699) for highest reward without a Critic model",
        grpo["group_size"] == 4
        and grpo["mean_reward"] == 3.0
        and abs(grpo["advantages_sum"]) < 1e-5
        and grpo["advantages"][-1] > 1.5,
    )

    vram_align = compare_alignment_vram_budgets(model_params_billions=8.0, bytes_per_weight=2.0, lora_trainable_fraction=0.01)
    check(
        "22. 8B Alignment VRAM comparison: Full PPO (4 models) = 160.0 GB, Full GRPO (3 models, no Critic) = 96.0 GB, Full DPO (2 models) = 80.0 GB, and LoRA DPO (ref_model=None) = 16.64 GB; OpenRLHF rollout generation = 80% of step time",
        vram_align["ppo_full_gb"] == 160.0
        and vram_align["grpo_full_gb"] == 96.0
        and vram_align["dpo_full_gb"] == 80.0
        and vram_align["dpo_lora_gb"] == 16.64
        and vram_align["openrlhf_rollout_time_pct"] == 80.0,
    )

    # 8. Model Merging (Linear, SLERP, TIES, DARE, Layer Stacking)
    slerp_mid = slerp_vectors([1.0, 0.0], [0.0, 1.0], t=0.5)
    check(
        "23. SLERP at t=0.5 between orthogonal unit vectors [1, 0] and [0, 1] lies on the unit circle at [0.707107, 0.707107] (norm = 1.0 vs linear average norm = 0.7071)",
        slerp_mid == [0.707107, 0.707107],
    )

    merge_res = ties_and_dare_merge(
        task_vec_a=[0.9, -0.05, 0.02, -0.8, 0.01],
        task_vec_b=[0.7, 0.04, -0.03, 0.1, -0.02],
        top_k_fraction=0.4,
        dare_drop_prob=0.8,
    )
    check(
        "24. TIES-Merging trims redundant small task-vector deltas and resolves sign interference; DARE with drop probability p=0.8 rescales surviving deltas by 1/(1-p) = 5.0x",
        merge_res["trimmed_a"] == [0.9, 0.0, 0.0, -0.8, 0.0]
        and merge_res["ties_merged"][0] == 0.8
        and merge_res["ties_merged"][3] == -0.8
        and merge_res["dare_rescale_factor"] == 5.0,
    )

    check(
        "25. Layer stacking / depthwise scaling (AIE Ch. 7): SOLAR 10.7B merges two 32-layer 7B models with 16 summed layers into 48 layers; Goliath-120B stacks 72 of 80 layers from two Llama-2-70B models into 144 layers",
        merge_res["solar_10_7b_layers"] == 48 and merge_res["goliath_120b_layers"] == 144,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
