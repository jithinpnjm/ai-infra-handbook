#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.14: Dataset Engineering for Fine-Tuning."""

from __future__ import annotations
import sys
from dataset_engineering_finetuning import (
    evaluate_scaling_and_domain_mix,
    simulate_curation_funnel_and_budget,
    exact_deduplicate_sha256,
    extract_word_shingles,
    compute_jaccard_similarity,
    compute_minhash_signature,
    estimate_jaccard_from_minhash,
    lsh_candidate_probability,
    evaluate_repetition_and_lsh_profile,
    decontaminate_training_samples,
    clean_html_and_redact_pii,
    filter_preference_chosen_answers,
    evaluate_nemo_curator_and_dataloader_io,
    clean_article_text,
    extract_sentence_substrings,
    verify_order_swapped_pairwise_judge,
    format_chat_template,
    build_assistant_only_labels,
    pack_sequences_and_compute_cu_seqlens,
)


def run_lab() -> int:
    print("=== Chapter 14.14 Lab: Dataset Engineering for Fine-Tuning Verification ===")
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

    # 1. Scaling Laws & Llama 3 Domain Mix across Pre-training, SFT, and Preference Alignment
    scaling = evaluate_scaling_and_domain_mix()
    check(
        "1. Kaplan scaling exponents (D_opt ~ C^0.27, N_opt ~ C^0.73) vs Chinchilla compute-optimal balance (0.50, 0.50)",
        scaling["kaplan_d_exponent"] == 0.27
        and scaling["kaplan_n_exponent"] == 0.73
        and scaling["chinchilla_d_exponent"] == 0.50,
    )

    check(
        "2. Llama 2 (2T tokens = 1B 2K-token examples) vs Llama 3 (16T tokens = 15B examples) pre-training scale",
        scaling["llama2_pretrain_tokens_trillion"] == 2.0
        and scaling["llama3_pretrain_tokens_trillion"] == 16.0
        and scaling["llama2_equiv_examples_billion"] == 1.0
        and scaling["llama3_equiv_examples_billion"] == 15.0,
    )

    check(
        "3. Llama 3 domain mixes sum to 100.0% across Pre-training, SFT, and Preference tuning",
        scaling["pre_total_pct"] == 100.0
        and scaling["sft_total_pct"] == 100.0
        and scaling["pref_total_pct"] == 100.0,
    )

    check(
        "4. Llama 3 combined math+code share is 42.0% in pre-training, 36.08% in SFT, and 12.82% in preference alignment",
        scaling["pre_code_math_pct"] == 42.0
        and scaling["sft_code_math_pct"] == 36.08
        and scaling["pref_code_math_pct"] == 12.82,
    )

    check(
        "5. LIMA (1,000 examples -> 43.0% win/tie vs GPT-4), Yi (10,000 examples), Chung tasks (9 -> 282 -> 1,836), and OpenAI SNLI (100 vs 550,000)",
        scaling["lima_curated_examples"] == 1000
        and scaling["lima_gpt4_win_or_tie_pct"] == 43.0
        and scaling["yi_curated_instructions"] == 10000
        and scaling["chung_task_scaling_ milestones"] == (9, 282, 1836)
        and scaling["openai_snli_scaling_examples"] == (100, 550000),
    )

    # 2. Curation Funnel & Annotation Budget
    funnel = simulate_curation_funnel_and_budget()
    check(
        "6. Curation funnel (10,000 raw -> 9,000 valid instructions -> 6,000 clean + 3,000 rewritten + 2,000 synthetic = 11,000 examples; $10,000 / $2 = 5,000)",
        funnel["after_instruction_filter"] == 9000
        and funnel["retained_clean_pairs"] == 6000
        and funnel["after_manual_rewrite"] == 9000
        and funnel["final_curated_examples"] == 11000
        and funnel["max_affordable_annotations"] == 5000,
    )

    # 3. Exact Deduplication (SHA-256), Fuzzy Deduplication (MinHash + LSH), and Decontamination
    dedup_res = exact_deduplicate_sha256(
        [
            "{item: pencil, color: red} -> $20",
            "{item: compass, color: green} -> $2",
            "  {ITEM: pencil,   color: RED} -> $20  ",
            "{item: pencil, color: red} -> $20",
            "{item: pencil, color: green} -> $1",
        ]
    )
    check(
        "7. Exact SHA-256 deduplication over AIE Table 8-3 toy dataset keeps 3 unique items and removes indices [2, 3]",
        dedup_res["kept_count"] == 3
        and dedup_res["removed_count"] == 2
        and dedup_res["removed_indices"] == [2, 3],
    )

    doc_a = "supervised fine tuning adapts a pretrained language model using curated instruction response pairs"
    doc_b = "supervised fine tuning adapts a pretrained language model using curated instruction answer pairs"
    sh_a = extract_word_shingles(doc_a, k=3)
    sh_b = extract_word_shingles(doc_b, k=3)
    exact_j = compute_jaccard_similarity(sh_a, sh_b)
    sig_a = compute_minhash_signature(sh_a, num_perm=128)
    sig_b = compute_minhash_signature(sh_b, num_perm=128)
    est_j = estimate_jaccard_from_minhash(sig_a, sig_b)
    check(
        "8. 3-gram Jaccard similarity (8/12 = 0.6667) and 128-permutation MinHash signature estimate agree within 0.08 on near-duplicate texts",
        0.65 <= exact_j <= 0.85 and abs(exact_j - est_j) <= 0.08,
    )

    lsh_prof = evaluate_repetition_and_lsh_profile(bands=16, rows_per_band=8, threshold=0.8)
    check(
        "9. Anthropic repetition study (0.1% repeated 100x degrades 800M model to 400M) and LSH (16 bands x 8 rows = 128 perms) S-curve",
        lsh_prof["anthropic_base_model_params_m"] == 800
        and lsh_prof["anthropic_degraded_equiv_params_m"] == 400
        and lsh_prof["num_perm"] == 128
        and lsh_prof["prob_at_j_0_2"] < 0.001
        and lsh_prof["prob_at_j_0_8"] > 0.94,
    )

    decontam = decontaminate_training_samples(
        train_samples=[
            doc_a,
            "explain how rocev2 uses priority flow control and ecn to prevent packet loss",
            "what is the capital of france paris is the capital of france",
        ],
        eval_samples=[
            doc_b,
            "What is the capital of France? Paris is the capital of France.",
        ],
        jaccard_threshold=0.65,
        shingle_k=3,
    )
    check(
        "10. Data decontamination removes both exact and near-duplicate benchmark leaks ([0, 2]), keeping only clean sample [1]",
        decontam["clean_train_count"] == 1
        and decontam["contaminated_count"] == 2
        and decontam["contaminated_indices"] == [0, 2],
    )

    # 4. HTML/Markdown Cleaning, PII Redaction, DPO Filtering & NeMo Curator Storage I/O
    cleaned_pii = clean_html_and_redact_pii(
        "<div class='post'># Header\nContact admin@corp.example.com or 415-555-0199 from host 10.24.8.15 (SSN 123-45-6789).</div>"
    )
    check(
        "11. HTML/Markdown cleaner strips tags and redacts all 4 PII classes (email, phone, SSN, IPv4)",
        cleaned_pii["total_redactions"] == 4
        and "<div" not in str(cleaned_pii["cleaned_text"])
        and "[EMAIL_REDACTED]" in str(cleaned_pii["cleaned_text"])
        and "[SSN_REDACTED]" in str(cleaned_pii["cleaned_text"]),
    )

    dpo_filtered = filter_preference_chosen_answers(
        [
            {"chosen": "Too short."},
            {"chosen": "lowercase start despite being over one hundred characters long so that it fails the uppercase format check in the pipeline."},
            {"chosen": "Missing terminal punctuation despite starting with an uppercase letter and exceeding one hundred characters in total length"},
            {"chosen": "Supervised fine-tuning adapts a pre-trained language model to follow instructions using curated pairs of prompts and responses."},
        ],
        min_length=100,
    )
    check(
        "12. LEH Ch. 6 preference answer filter (min_length=100, uppercase start, terminal .!?) retains only valid sample",
        len(dpo_filtered) == 1
        and dpo_filtered[0]["chosen"].startswith("Supervised fine-tuning"),
    )

    io_metrics = evaluate_nemo_curator_and_dataloader_io(
        initial_io_wait_pct=30.0,
        tuned_io_wait_pct=5.0,
        num_workers=8,
        prefetch_factor=4,
        batch_size=32,
    )
    check(
        "13. ASP Ch. 5 I/O tuning: 30% -> 5% I/O wait gives 6.0x step speedup; DALI cuts CPU from 800% (8 cores) to 200% (2 cores); Databricks HTML strip (+20% acc, -60% tokens)",
        io_metrics["step_speedup_factor"] == 6.0
        and io_metrics["dali_cpu_util_before_pct"] == 800
        and io_metrics["dali_cpu_util_after_pct"] == 200
        and io_metrics["databricks_html_strip_accuracy_gain_pct"] == 20.0
        and io_metrics["databricks_html_strip_token_reduction_pct"] == 60.0
        and io_metrics["queued_batches"] == 32
        and io_metrics["queued_samples"] == 1024,
    )

    # 5. Sentence-Aware Chunking, Synthetic Data & Order-Swapped LLM-as-a-Judge
    long_article = " ".join(
        [f"Sentence number {i} explains how distributed dataset engineering pipelines process raw articles into clean chunks." for i in range(30)]
    )
    chunks = extract_sentence_substrings([long_article], min_length=1000, max_length=2000)
    check(
        "14. LEH Ch. 5/6 sentence-aware regex chunker splits articles into extracts strictly between 1,000 and 2,000 characters",
        len(chunks) >= 2 and all(1000 <= len(c) <= 2000 for c in chunks),
    )

    judge_res = verify_order_swapped_pairwise_judge(
        [
            {"id": "pair-1", "forward_pick": "A", "swapped_pick": "B"},
            {"id": "pair-2", "forward_pick": "A", "swapped_pick": "A"},
            {"id": "pair-3", "forward_pick": "B", "swapped_pick": "A"},
            {"id": "pair-4", "forward_pick": "B", "swapped_pick": "B"},
        ]
    )
    check(
        "15. Nemotron-4 swapped-order pairwise judge retains only consistent winners (['pair-1', 'pair-3']) and rejects position-biased picks (['pair-2', 'pair-4'])",
        judge_res["consistent_ids"] == ["pair-1", "pair-3"]
        and judge_res["position_biased_ids"] == ["pair-2", "pair-4"],
    )

    check(
        "16. Synthetic data provenance metrics: Nemotron-4 340B (98.0% synthetic from 56B Mixtral), Llama 3.1 (2.7M code, 20.0% self-corrected), LEH SFT (3,335 + 10,000) & DPO (2,970 -> 1,467)",
        judge_res["nemotron4_synthetic_ratio_pct"] == 98.0
        and judge_res["llama3_1_synthetic_code_examples"] == 2700000
        and judge_res["llama3_1_self_correction_rate_pct"] == 20.0
        and judge_res["leh_sft_generated_pairs"] == 3335
        and judge_res["leh_dpo_raw_triples"] == 2970
        and judge_res["leh_dpo_filtered_triples"] == 1467,
    )

    # 6. Chat Templates, Assistant-Only Loss Masking (-100), and Sequence Packing / cu_seqlens
    chatml_str = format_chat_template(
        "chatml",
        user_message="What is the capital of France?",
        assistant_message="The capital of France is Paris.",
    )
    check(
        "17. ChatML template formats <|im_start|>user and <|im_start|>assistant with <|im_end|> delimiters",
        chatml_str
        == "<|im_start|>user\nWhat is the capital of France?<|im_end|>\n<|im_start|>assistant\nThe capital of France is Paris.<|im_end|>",
    )

    llama3_str = format_chat_template(
        "llama3",
        user_message="What is the capital of France?",
        assistant_message="The capital of France is Paris.",
    )
    check(
        "18. Llama 3 template formats <|begin_of_text|>, <|start_header_id|>, <|end_header_id|>, and <|eot_id|> tokens",
        llama3_str.startswith("<|begin_of_text|><|start_header_id|>user<|end_header_id|>")
        and llama3_str.endswith("The capital of France is Paris.<|eot_id|>"),
    )

    alpaca_str = format_chat_template(
        "alpaca",
        user_message="What is the capital of France?",
        assistant_message="The capital of France is Paris.",
    )
    phi3_str = format_chat_template(
        "phi3",
        user_message="What is the capital of France?",
        assistant_message="The capital of France is Paris.",
    )
    gemma_str = format_chat_template(
        "gemma",
        user_message="What is the capital of France?",
        assistant_message="The capital of France is Paris.",
    )
    check(
        "19. Alpaca (<EOS>), Phi-3 (<|user|>/<|end|>), and Gemma (<bos><start_of_turn>/<end_of_turn>) templates format accurately",
        alpaca_str.endswith("<EOS>")
        and "<|user|>" in phi3_str
        and "<bos><start_of_turn>user" in gemma_str,
    )

    masked = build_assistant_only_labels(prompt_token_ids=[10, 11, 12, 13], response_token_ids=[20, 21, 22])
    check(
        "20. Assistant-only loss masking assigns -100 to all 4 prompt tokens and keeps 3 response tokens supervised",
        masked["labels"] == [-100, -100, -100, -100, 20, 21, 22]
        and masked["masked_prompt_tokens"] == 4
        and masked["supervised_response_tokens"] == 3,
    )

    # 7. Sequence Packing, Truncation, and FlashAttention cu_seqlens Math
    trunc_check = pack_sequences_and_compute_cu_seqlens([1500], max_seq_length=1024)
    check(
        "21. LEH Ch. 5 truncation math: a 1,500-token sample at max_seq_length=1,024 loses exactly 476 tokens",
        trunc_check["truncated_tokens"] == 476 and trunc_check["total_real_tokens"] == 1024,
    )

    pack_res = pack_sequences_and_compute_cu_seqlens(
        [250, 300, 200, 250, 300, 220, 260, 220, 250, 250, 250, 250],
        max_seq_length=1024,
    )
    check(
        "22. Naive padding on 12 samples at max_seq_length=1,024 allocates 12,288 tokens (9,288 pad tokens = 24.41% utilization)",
        pack_res["naive_padded_tokens"] == 12288
        and pack_res["total_real_tokens"] == 3000
        and pack_res["naive_pad_waste_tokens"] == 9288
        and pack_res["naive_utilization_pct"] == 24.41,
    )

    check(
        "23. Sequence packing fits 12 short samples (200-300 tokens) into 3 bins of 1,024 tokens (4.0x batch reduction, 97.66% token utilization)",
        pack_res["num_packed_bins"] == 3
        and pack_res["packed_allocated_tokens"] == 3072
        and pack_res["batch_slot_reduction_factor"] == 4.0
        and pack_res["packed_utilization_pct"] == 97.66,
    )

    check(
        "24. FlashAttention varlen cumulative sequence lengths (cu_seqlens) for first packed bin [250, 300, 200, 250] is [0, 250, 550, 750, 1000]",
        pack_res["first_bin_cu_seqlens"] == [0, 250, 550, 750, 1000]
        and pack_res["first_bin_max_seqlen"] == 300,
    )

    check(
        "25. Block-diagonal varlen attention on [250, 300, 200, 250] computes 255,000 ops vs 1,000,000 dense ops (3.92x attention compute reduction)",
        pack_res["first_bin_block_diag_attn_ops"] == 255000
        and pack_res["first_bin_dense_unmasked_attn_ops"] == 1000000
        and pack_res["first_bin_attn_reduction_factor"] == 3.92,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
