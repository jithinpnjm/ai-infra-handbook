#!/usr/bin/env python3
r"""Chapter 14.14 model: Dataset Engineering for Fine-Tuning.

Models:
1. Data Curation, Scaling Laws, Domain Composition & Curation Funnel (`AIE` Ch. 8, `LLO` Ch. 4, `LEH` Ch. 5 & 6):
   - Kaplan scaling law (`D_opt ~ C^0.27`, `N_opt ~ C^0.73`) vs Chinchilla compute-optimal balance (`D_opt ~ C^0.50`, `N_opt ~ C^0.50`).
   - Pre-training vs post-training scale: `Llama 2` (`2 trillion` tokens = `1,000,000,000` examples at `2,000` tokens/example)
     vs `Llama 3` (`16 trillion` tokens = `15,000,000,000` examples).
   - `Llama 3` domain composition across Pre-training (`50%` English, `25%` math/reasoning, `17%` coding, `8%` multilingual),
     SFT (`52.66%` English, `21.19%` math/reasoning, `14.89%` coding, `8.14%` exam-like, `3.01%` multilingual, `0.11%` long context),
     and Preference alignment (`81.99%` English, `6.93%` coding, `5.89%` math/reasoning, `5.19%` multilingual; `12.82%` combined code+math).
   - Annotation budget and hybrid curation funnel (`10,000` raw -> `9,000` valid instructions -> `6,000` clean pairs + `3,000`
     rewritten + `2,000` synthetic from `100` templates = `11,000` examples; `$10,000` budget at `$2`/example = `5,000` examples).
2. Exact, Fuzzy (`MinHash` + `LSH`), and Semantic Deduplication & Data Decontamination (`AIE` Ch. 8, `LEH` Ch. 5, `LLO` Ch. 4):
   - Anthropic repetition degradation (`0.1%` data repeated `100` times degrades an `800M` model to `400M` equivalent performance
     even with `90%` unique tokens).
   - Exact deduplication via normalized `SHA-256` / `MD5` digests.
   - Fuzzy deduplication via $k$-gram shingling, `MinHash` signatures (`num_perm = b * r`), Jaccard similarity $J(A, B) = |A \cap B| / |A \cup B|$,
     and `Locality-Sensitive Hashing` (`LSH`) candidate probability $P(\text{candidate}) = 1 - (1 - J^r)^b$ around threshold $J \approx 0.8$.
   - Semantic deduplication via cosine similarity over embeddings (`text-embedding-3-small` `8,191` max tokens -> `1,536` dimensions)
     and evaluation set decontamination.
3. Quality Filtering, HTML/Markdown Cleaning, PII Redaction & `NVIDIA NeMo Curator` Storage I/O (`AIE` Ch. 8, `LLO` Ch. 4, `ASP` Ch. 5):
   - Databricks HTML/Markdown stripping (`+20%` accuracy, `-60%` input token length).
   - Rule-based length, punctuation, curly-brace, and PII redaction filters (`email`, `phone`, `SSN`, `IPv4`).
   - `NeMo Curator` `DocumentDataset` offline pipeline (`JSONL`/`Parquet` -> `.bin` + `.idx` memory-mapped files, `N` pre-shuffled epoch copies)
     and GPU DataLoader I/O stall math (`50%` wasted GPU time; reducing I/O wait from `30%` to `5%` yields `6x` step speedup;
     `NVIDIA DALI` drops CPU utilization from `800%` [`8` cores] to `200%` [`2` cores]).
4. Synthetic Data Generation, `LLM-as-a-Judge` Verification, and Model Collapse (`AIE` Ch. 8, `LEH` Ch. 5 & 6):
   - `LEH` regex sentence chunker (`1,000` to `2,000` chars) with `ThreadPoolExecutor(max_workers=4)` and `gpt-4o-mini`
     (`3,335` SFT pairs + `10,000` `FineTome`; `2,970` raw DPO triples -> `1,467` filtered triples with `min_length=100`).
   - `Llama 3.1` `2,700,000` synthetic coding pipeline (`20%` initial failures self-corrected via parser/linter/unit-test feedback).
   - `Nemotron-4 340B-Instruct` (`98%` synthetic data from `56B` `Mixtral-8x7B-Instruct-v0.1`) and swapped-order pairwise judge
     (`(A, B)` and `(B, A)` consistency check to eliminate first-position bias) + `1-4` rubric and `80%` human agreement target.
5. Chat Templates, Sequence Packing (`packing=True`), and `FlashAttention` Varlen (`cu_seqlens`) (`AIE` Ch. 8, `LEH` Ch. 5 & 6):
   - Formatting across `Alpaca`, `ShareGPT`, `OpenAI`, `ChatML` (`<|im_start|>`, `<|im_end|>`), `Llama 3` (`<|begin_of_text|>`,
     `<|start_header_id|>`, `<|end_header_id|>`, `<|eot_id|>`), `Phi-3`, and `Gemma`, plus `3`-shot prompt compression (`burger -->`).
   - Naive padding vs sequence packing (`12 * 1,024 = 12,288` tokens vs `12 * 512 = 6,144` tokens; `1,500`-token sample truncated to `1,024`
     loses `476` tokens; packing `200-300` token samples fits `3-4` samples per `1,024`-token slot), `cu_seqlens` cumulative sequence lengths,
     block-diagonal attention FLOP savings vs dense cross-contamination, and assistant-only loss masking (`-100` on prompt tokens).
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import math
import re
from typing import Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. Data Curation, Scaling Laws, Domain Mix & Curation Funnel
# ---------------------------------------------------------------------------

LLAMA3_DOMAIN_MIX: Dict[str, Dict[str, float]] = {
    "pretraining": {
        "general_knowledge": 50.0,
        "math_and_reasoning": 25.0,
        "coding": 17.0,
        "multilingual": 8.0,
        "exam_like": 0.0,
        "long_context": 0.0,
    },
    "sft": {
        "general_knowledge": 52.66,
        "math_and_reasoning": 21.19,
        "coding": 14.89,
        "multilingual": 3.01,
        "exam_like": 8.14,
        "long_context": 0.11,
    },
    "preference": {
        "general_knowledge": 81.99,
        "math_and_reasoning": 5.89,
        "coding": 6.93,
        "multilingual": 5.19,
        "exam_like": 0.0,
        "long_context": 0.0,
    },
}


def evaluate_scaling_and_domain_mix() -> Dict[str, object]:
    """Evaluates Kaplan vs Chinchilla scaling exponents and Llama 3 domain mixes across training phases."""
    pre = LLAMA3_DOMAIN_MIX["pretraining"]
    sft = LLAMA3_DOMAIN_MIX["sft"]
    pref = LLAMA3_DOMAIN_MIX["preference"]

    pre_code_math = round(pre["math_and_reasoning"] + pre["coding"], 2)
    sft_code_math = round(sft["math_and_reasoning"] + sft["coding"], 2)
    pref_code_math = round(pref["math_and_reasoning"] + pref["coding"], 2)

    return {
        "kaplan_d_exponent": 0.27,
        "kaplan_n_exponent": 0.73,
        "chinchilla_d_exponent": 0.50,
        "chinchilla_n_exponent": 0.50,
        "llama2_pretrain_tokens_trillion": 2.0,
        "llama3_pretrain_tokens_trillion": 16.0,
        "llama2_equiv_examples_billion": 1.0,
        "llama3_equiv_examples_billion": 15.0,
        "pre_total_pct": round(sum(pre.values()), 2),
        "sft_total_pct": round(sum(sft.values()), 2),
        "pref_total_pct": round(sum(pref.values()), 2),
        "pre_code_math_pct": pre_code_math,
        "sft_code_math_pct": sft_code_math,
        "pref_code_math_pct": pref_code_math,
        "lima_curated_examples": 1000,
        "lima_gpt4_win_or_tie_pct": 43.0,
        "yi_curated_instructions": 10000,
        "chung_task_scaling_ milestones": (9, 282, 1836),
        "openai_snli_scaling_examples": (100, 550000),
    }


def simulate_curation_funnel_and_budget(
    initial_public_examples: int = 10000,
    low_quality_instructions_removed: int = 1000,
    low_quality_responses_set_aside: int = 3000,
    manually_rewritten_responses: int = 3000,
    synthetic_templates: int = 100,
    synthetic_instructions_generated: int = 2000,
    annotation_budget_usd: float = 10000.0,
    cost_per_example_usd: float = 2.0,
) -> Dict[str, int | float]:
    """Models the AIE Chapter 8 dataset curation funnel and annotation budget."""
    after_instruction_filter = initial_public_examples - low_quality_instructions_removed
    retained_clean_pairs = after_instruction_filter - low_quality_responses_set_aside
    after_manual_rewrite = retained_clean_pairs + manually_rewritten_responses
    final_curated_examples = after_manual_rewrite + synthetic_instructions_generated
    max_affordable_annotations = int(annotation_budget_usd // cost_per_example_usd)

    return {
        "initial_public_examples": initial_public_examples,
        "after_instruction_filter": after_instruction_filter,
        "retained_clean_pairs": retained_clean_pairs,
        "after_manual_rewrite": after_manual_rewrite,
        "synthetic_templates": synthetic_templates,
        "synthetic_instructions_generated": synthetic_instructions_generated,
        "final_curated_examples": final_curated_examples,
        "max_affordable_annotations": max_affordable_annotations,
    }


# ---------------------------------------------------------------------------
# 2. Deduplication (Exact, MinHash + LSH, Semantic) & Decontamination
# ---------------------------------------------------------------------------

def normalize_for_dedup(text: str) -> str:
    """Normalizes alphanumeric tokens, whitespace, and case for exact hash deduplication."""
    return " ".join(re.findall(r"\w+", text.lower()))


def exact_deduplicate_sha256(documents: Sequence[str]) -> Dict[str, object]:
    """Performs exact deduplication using SHA-256 over normalized text."""
    seen_hashes: set[str] = set()
    kept_indices: List[int] = []
    removed_indices: List[int] = []

    for idx, doc in enumerate(documents):
        norm_text = normalize_for_dedup(doc)
        digest = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()
        if digest not in seen_hashes:
            seen_hashes.add(digest)
            kept_indices.append(idx)
        else:
            removed_indices.append(idx)

    return {
        "total_docs": len(documents),
        "kept_count": len(kept_indices),
        "removed_count": len(removed_indices),
        "kept_indices": kept_indices,
        "removed_indices": removed_indices,
    }


def extract_word_shingles(text: str, k: int = 3) -> set[str]:
    """Extracts k-word shingles from normalized text."""
    tokens = re.findall(r"\w+", text.lower())
    if len(tokens) < k:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def compute_jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Computes exact Jaccard similarity |A n B| / |A u B|."""
    if not set_a and not set_b:
        return 1.0
    union = len(set_a | set_b)
    return len(set_a & set_b) / union if union > 0 else 0.0


def compute_minhash_signature(shingles: set[str], num_perm: int = 128) -> List[int]:
    """Computes a deterministic MinHash signature vector of length num_perm."""
    if not shingles:
        return [0] * num_perm
    sig: List[int] = []
    for perm_idx in range(num_perm):
        min_hash = min(
            int.from_bytes(
                hashlib.blake2b(f"{perm_idx}:{shingle}".encode("utf-8"), digest_size=4).digest(),
                byteorder="big",
            )
            for shingle in shingles
        )
        sig.append(min_hash)
    return sig


def estimate_jaccard_from_minhash(sig_a: Sequence[int], sig_b: Sequence[int]) -> float:
    """Estimates Jaccard similarity from two equal-length MinHash signatures."""
    if len(sig_a) != len(sig_b) or not sig_a:
        raise ValueError("MinHash signatures must be non-empty and equal length")
    matches = sum(1 for a, b in zip(sig_a, sig_b) if a == b)
    return matches / len(sig_a)


def lsh_candidate_probability(jaccard: float, bands: int, rows_per_band: int) -> float:
    """Computes LSH candidate collision probability: P = 1 - (1 - J^r)^b."""
    if not (0.0 <= jaccard <= 1.0):
        raise ValueError("jaccard must be in [0, 1]")
    return 1.0 - ((1.0 - (jaccard ** rows_per_band)) ** bands)


def evaluate_repetition_and_lsh_profile(
    bands: int = 16,
    rows_per_band: int = 8,
    threshold: float = 0.8,
) -> Dict[str, float | int]:
    """Evaluates Anthropic repetition penalty and LSH S-curve probabilities."""
    num_perm = bands * rows_per_band
    approx_threshold = (1.0 / bands) ** (1.0 / rows_per_band)
    return {
        "anthropic_repeated_data_pct": 0.1,
        "anthropic_repeat_count": 100,
        "anthropic_unique_tokens_pct": 90.0,
        "anthropic_base_model_params_m": 800,
        "anthropic_degraded_equiv_params_m": 400,
        "num_perm": num_perm,
        "bands": bands,
        "rows_per_band": rows_per_band,
        "target_jaccard_threshold": threshold,
        "approx_s_curve_inflection": round(approx_threshold, 4),
        "prob_at_j_0_2": round(lsh_candidate_probability(0.2, bands, rows_per_band), 6),
        "prob_at_j_0_5": round(lsh_candidate_probability(0.5, bands, rows_per_band), 6),
        "prob_at_j_0_8": round(lsh_candidate_probability(0.8, bands, rows_per_band), 6),
        "prob_at_j_0_9": round(lsh_candidate_probability(0.9, bands, rows_per_band), 6),
    }


def decontaminate_training_samples(
    train_samples: Sequence[str],
    eval_samples: Sequence[str],
    jaccard_threshold: float = 0.8,
    shingle_k: int = 3,
) -> Dict[str, object]:
    """Removes training samples that overlap with evaluation benchmark samples (exact or fuzzy >= threshold)."""
    eval_shingle_sets = [extract_word_shingles(s, k=shingle_k) for s in eval_samples]
    eval_norm_set = {normalize_for_dedup(s) for s in eval_samples}

    clean_train: List[str] = []
    contaminated_indices: List[int] = []

    for idx, sample in enumerate(train_samples):
        if normalize_for_dedup(sample) in eval_norm_set:
            contaminated_indices.append(idx)
            continue
        sample_shingles = extract_word_shingles(sample, k=shingle_k)
        max_sim = max(
            (compute_jaccard_similarity(sample_shingles, es) for es in eval_shingle_sets),
            default=0.0,
        )
        if max_sim >= jaccard_threshold:
            contaminated_indices.append(idx)
        else:
            clean_train.append(sample)

    return {
        "initial_train_count": len(train_samples),
        "eval_benchmark_count": len(eval_samples),
        "clean_train_count": len(clean_train),
        "contaminated_count": len(contaminated_indices),
        "contaminated_indices": contaminated_indices,
    }


# ---------------------------------------------------------------------------
# 3. Quality Filtering, Cleaning, PII Redaction & NeMo Curator Storage I/O
# ---------------------------------------------------------------------------

PII_PATTERNS: Dict[str, re.Pattern[str]] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}


def clean_html_and_redact_pii(text: str) -> Dict[str, object]:
    """Strips HTML/Markdown clutter and redacts PII tokens (email, phone, SSN, IPv4)."""
    raw_char_len = len(text)
    stripped = re.sub(r"<[^>]+>", " ", text)
    stripped = re.sub(r"```.*?```", " ", stripped, flags=re.S)
    stripped = re.sub(r"[#*_`~>]+", " ", stripped)

    redaction_counts: Dict[str, int] = {}
    for pii_type, pattern in PII_PATTERNS.items():
        stripped, count = pattern.subn(f"[{pii_type.upper()}_REDACTED]", stripped)
        redaction_counts[pii_type] = count

    cleaned = re.sub(r"\s+", " ", stripped).strip()
    return {
        "cleaned_text": cleaned,
        "raw_char_len": raw_char_len,
        "cleaned_char_len": len(cleaned),
        "redaction_counts": redaction_counts,
        "total_redactions": sum(redaction_counts.values()),
    }


def filter_preference_chosen_answers(
    samples: Sequence[Dict[str, str]],
    min_length: int = 100,
) -> List[Dict[str, str]]:
    """Implements LEH Chapter 6 filter_short_answers (min_length=100) and filter_answer_format."""
    kept: List[Dict[str, str]] = []
    for ex in samples:
        chosen = ex.get("chosen", "")
        if len(chosen) >= min_length and chosen[0].isupper() and chosen[-1] in (".", "!", "?"):
            kept.append(ex)
    return kept


def evaluate_nemo_curator_and_dataloader_io(
    initial_io_wait_pct: float = 30.0,
    tuned_io_wait_pct: float = 5.0,
    num_workers: int = 8,
    prefetch_factor: int = 4,
    batch_size: int = 32,
) -> Dict[str, float | int | bool]:
    """Evaluates NeMo Curator offline indexing and ASP Chapter 5 DataLoader I/O stall metrics."""
    io_stall_reduction_ratio = initial_io_wait_pct / tuned_io_wait_pct
    queued_batches = num_workers * prefetch_factor
    queued_samples = queued_batches * batch_size

    return {
        "unoptimized_pipeline_gpu_waste_pct": 50.0,
        "initial_io_wait_pct": initial_io_wait_pct,
        "tuned_io_wait_pct": tuned_io_wait_pct,
        "step_speedup_factor": round(io_stall_reduction_ratio, 2),
        "dali_cpu_util_before_pct": 800,
        "dali_cpu_util_after_pct": 200,
        "dali_cpu_cores_before": 8,
        "dali_cpu_cores_after": 2,
        "databricks_html_strip_accuracy_gain_pct": 20.0,
        "databricks_html_strip_token_reduction_pct": 60.0,
        "num_workers": num_workers,
        "prefetch_factor": prefetch_factor,
        "queued_batches": queued_batches,
        "queued_samples": queued_samples,
        "pin_memory": True,
        "persistent_workers": True,
    }


# ---------------------------------------------------------------------------
# 4. Synthetic Data Generation, Chunking & LLM-as-a-Judge Verification
# ---------------------------------------------------------------------------

def clean_article_text(text: str) -> str:
    """Implements LEH Chapter 5 & 6 clean_text regex normalization."""
    text = re.sub(r"[^\w\s.,!?']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_sentence_substrings(
    articles: Sequence[str],
    min_length: int = 1000,
    max_length: int = 2000,
) -> List[str]:
    """Implements LEH Chapter 5 & 6 extract_substrings sentence-aware chunker (1,000 to 2,000 chars)."""
    extracts: List[str] = []
    sentence_pattern = r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s"
    for article in articles:
        cleaned_article = clean_article_text(article)
        sentences = re.split(sentence_pattern, cleaned_article)
        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence + " "
            else:
                if len(current_chunk) >= min_length:
                    extracts.append(current_chunk.strip())
                current_chunk = sentence + " "
        if len(current_chunk) >= min_length:
            extracts.append(current_chunk.strip())
    return extracts


def verify_order_swapped_pairwise_judge(
    comparisons: Sequence[Dict[str, str]],
) -> Dict[str, object]:
    """Implements NVIDIA Nemotron-4 swapped-order pairwise judge verification to eliminate position bias.

    Each item in `comparisons` has:
      - `id`: sample identifier
      - `forward_pick`: "A" or "B" when presented in order (Response A, Response B)
      - `swapped_pick`: "A" or "B" (referring to the first/second slot in the swapped prompt (Response B, Response A))
        For a consistent judge: if `forward_pick == "A"` (candidate 1 wins), then when swapped to `(candidate 2, candidate 1)`,
        the judge must pick slot `"B"` (candidate 1 still wins). If both slots return `"A"`, the judge exhibits first-position bias.
    """
    consistent_ids: List[str] = []
    position_biased_ids: List[str] = []

    for item in comparisons:
        cid = item["id"]
        fwd = item["forward_pick"]
        swp = item["swapped_pick"]
        if (fwd == "A" and swp == "B") or (fwd == "B" and swp == "A"):
            consistent_ids.append(cid)
        else:
            position_biased_ids.append(cid)

    return {
        "total_evaluated": len(comparisons),
        "consistent_count": len(consistent_ids),
        "position_biased_count": len(position_biased_ids),
        "consistent_ids": consistent_ids,
        "position_biased_ids": position_biased_ids,
        "nemotron4_synthetic_ratio_pct": 98.0,
        "nemotron4_student_params_b": 340,
        "nemotron4_teacher_params_b": 56,
        "llama3_1_synthetic_code_examples": 2700000,
        "llama3_1_self_correction_rate_pct": 20.0,
        "leh_sft_generated_pairs": 3335,
        "leh_finetome_upsample_pairs": 10000,
        "leh_dpo_raw_triples": 2970,
        "leh_dpo_filtered_triples": 1467,
        "judge_human_agreement_target_pct": 80.0,
        "fineweb_edu_samples": 450000,
        "fineweb_edu_epochs": 20,
    }


# ---------------------------------------------------------------------------
# 5. Chat Templates, Sequence Packing (`packing=True`), and FlashAttention Varlen
# ---------------------------------------------------------------------------

def format_chat_template(
    template_name: str,
    user_message: str,
    assistant_message: str | None = None,
    system_message: str | None = None,
    add_generation_prompt: bool = False,
) -> str:
    """Formats messages into exact Alpaca, ChatML, Llama 3, Phi-3, or Gemma chat strings."""
    if template_name == "chatml":
        parts: List[str] = []
        if system_message:
            parts.append(f"<|im_start|>system\n{system_message}<|im_end|>")
        parts.append(f"<|im_start|>user\n{user_message}<|im_end|>")
        if assistant_message is not None:
            parts.append(f"<|im_start|>assistant\n{assistant_message}<|im_end|>")
        elif add_generation_prompt:
            parts.append("<|im_start|>assistant\n")
        return "\n".join(parts)

    if template_name == "llama3":
        out = "<|begin_of_text|>"
        if system_message:
            out += f"<|start_header_id|>system<|end_header_id|>\n\n{system_message}<|eot_id|>"
        out += f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"
        if assistant_message is not None:
            out += f"<|start_header_id|>assistant<|end_header_id|>\n\n{assistant_message}<|eot_id|>"
        elif add_generation_prompt:
            out += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        return out

    if template_name == "alpaca":
        if assistant_message is not None:
            return f"### Instruction: {user_message}\n### Response: {assistant_message}<EOS>"
        return f"### Instruction: {user_message}\n### Response:"

    if template_name == "phi3":
        out = f"<|user|>\n{user_message}<|end|>"
        if assistant_message is not None:
            out += f"\n<|assistant|>\n{assistant_message}<|end|>"
        elif add_generation_prompt:
            out += "\n<|assistant|>\n"
        return out

    if template_name == "gemma":
        out = f"<bos><start_of_turn>user\n{user_message}<end_of_turn>"
        if assistant_message is not None:
            out += f"\n<start_of_turn>model\n{assistant_message}<end_of_turn>"
        elif add_generation_prompt:
            out += "\n<start_of_turn>model\n"
        return out

    raise ValueError(f"Unsupported template_name: {template_name}")


def build_assistant_only_labels(
    prompt_token_ids: Sequence[int],
    response_token_ids: Sequence[int],
    ignore_index: int = -100,
) -> Dict[str, List[int] | int]:
    """Constructs input_ids and labels where prompt tokens are masked with -100."""
    input_ids = list(prompt_token_ids) + list(response_token_ids)
    labels = [ignore_index] * len(prompt_token_ids) + list(response_token_ids)
    supervised_tokens = sum(1 for x in labels if x != ignore_index)
    return {
        "input_ids": input_ids,
        "labels": labels,
        "total_tokens": len(input_ids),
        "masked_prompt_tokens": len(prompt_token_ids),
        "supervised_response_tokens": supervised_tokens,
    }


def pack_sequences_and_compute_cu_seqlens(
    sample_lengths: Sequence[int],
    max_seq_length: int = 1024,
) -> Dict[str, object]:
    """Packs variable-length sequences into bins of max_seq_length and computes FlashAttention cu_seqlens.

    Also compares naive padded batching vs packed batching token efficiency and block-diagonal attention
    operations (`sum(L_i^2)` vs `(sum L_i)^2`).
    """
    valid_lengths = [min(L, max_seq_length) for L in sample_lengths if L > 0]
    truncated_tokens = sum(max(0, L - max_seq_length) for L in sample_lengths if L > 0)

    bins: List[List[int]] = []
    current_bin: List[int] = []
    current_sum = 0

    for length in valid_lengths:
        if current_sum + length <= max_seq_length:
            current_bin.append(length)
            current_sum += length
        else:
            if current_bin:
                bins.append(current_bin)
            current_bin = [length]
            current_sum = length
    if current_bin:
        bins.append(current_bin)

    # Cumulative sequence lengths (`cu_seqlens`) for the first packed bin
    first_bin = bins[0] if bins else []
    cu_seqlens: List[int] = [0]
    running = 0
    for seg_len in first_bin:
        running += seg_len
        cu_seqlens.append(running)

    total_real_tokens = sum(valid_lengths)
    naive_padded_tokens = len(valid_lengths) * max_seq_length
    naive_pad_waste_tokens = naive_padded_tokens - total_real_tokens
    naive_utilization_pct = (total_real_tokens / naive_padded_tokens * 100.0) if naive_padded_tokens else 0.0
    naive_pad_waste_pct = round(100.0 - round(naive_utilization_pct, 2), 2)  # 75.59% on 3,000 / 12,288

    packed_allocated_tokens = len(bins) * max_seq_length
    packed_utilization_pct = (total_real_tokens / packed_allocated_tokens * 100.0) if packed_allocated_tokens else 0.0
    batch_slot_reduction_factor = (len(valid_lengths) / len(bins)) if bins else 1.0

    # Attention complexity on the first packed bin: block-diagonal sum(L_i^2) vs unmasked (sum L_i)^2
    block_diag_attn_ops = sum(seg_len * seg_len for seg_len in first_bin)
    dense_unmasked_attn_ops = running * running
    attn_compute_reduction_factor = (
        dense_unmasked_attn_ops / block_diag_attn_ops if block_diag_attn_ops > 0 else 1.0
    )

    return {
        "num_samples": len(valid_lengths),
        "max_seq_length": max_seq_length,
        "total_real_tokens": total_real_tokens,
        "truncated_tokens": truncated_tokens,
        "naive_padded_tokens": naive_padded_tokens,
        "naive_pad_waste_tokens": naive_pad_waste_tokens,
        "naive_utilization_pct": round(naive_utilization_pct, 2),
        "num_packed_bins": len(bins),
        "packed_bins": bins,
        "packed_allocated_tokens": packed_allocated_tokens,
        "packed_utilization_pct": round(packed_utilization_pct, 2),
        "batch_slot_reduction_factor": round(batch_slot_reduction_factor, 2),
        "first_bin_cu_seqlens": cu_seqlens,
        "first_bin_max_seqlen": max(first_bin) if first_bin else 0,
        "first_bin_block_diag_attn_ops": block_diag_attn_ops,
        "first_bin_dense_unmasked_attn_ops": dense_unmasked_attn_ops,
        "first_bin_attn_reduction_factor": round(attn_compute_reduction_factor, 2),
    }


if __name__ == "__main__":
    print("Dataset Engineering for Fine-Tuning model loaded successfully.")
