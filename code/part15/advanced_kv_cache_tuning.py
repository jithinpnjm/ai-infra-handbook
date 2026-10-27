#!/usr/bin/env python3
"""Chapter 15.11 model: Advanced Prefill-Decode and KV Cache Tuning.

Models:
1. Split-KV Parallel Decode Attention, XQA, FlashMLA, ThunderMLA, FlexDecoding & POD-Attention:
   - Standard FlashAttention-2 decode CTAs (`batch_size * num_kv_heads`) vs FlashDecoding / FlashInfer
     split-KV parallel decode (`batch_size * num_kv_heads * num_kv_splits`, `num_kv_splits = ceil(seq_len / split_chunk_tokens)`),
     SM occupancy on a `132`-SM H100 (`8 / 132 = 6.06%` at `B=1, H_kv=8` vs `128 / 132 = 96.97%` at `S=4096, C_split=256`),
     online log-sum-exp two-stage reduction (`l_k = m_k + log(sum(exp(s - m_k)))`), and up to `8.0x` decode speedup (`V12` Ch. 5).
   - TensorRT-LLM `XQA` (`MHARunner`) GQA tile packing (`G = H_q / H_kv = 64 / 8 = 8` query heads per KV head on `Llama-3-70B`),
     `FlashMLA` latent KV compression (`d_c = 512, d_R = 64`, `576` elements/layer = `2.25` GQA groups equivalent),
     Stanford `ThunderMLA` (`20%-35%` faster decode throughput over `FlashMLA`), PyTorch `FlexDecoding` with Nested Jagged Tensors (`NJT`)
     and `BlockMask` (`64-128` token pages), and `POD-Attention` SM-aware CTA scheduling (`up to 29%` speedup, `ASP` Ch. 18).
2. Chunked Prefill Token-Budget Tuning, Decode-Maximal Batching, and Prefix-Cache Interaction:
   - Sarathi-Lean token budget equation: `Tokens_iter = M_decode + sum(C_j) <= MaxTokensPerIter` (`2,048` tokens).
   - Models the `12,288`-token prompt burst on `4x H100` (`TP=4`, `45` active decode streams): unchunked prefill monopolizes SMs
     for `320 ms`, spiking `p99 ITL` from `18.0 ms` to `340.0 ms` vs Chunked Prefill (`max_num_batched_tokens = 2048`) cutting
     `p99 ITL` to `21.4 ms` (`15.89x` reduction) across `6` chunks (`V12` Ch. 7), and `SARATHI` `10,000`-token prompt sliced into
     `5` chunks of `2,000` tokens (`50-100 ms` per chunk, `1.3x-1.9x` throughput gain, `ASP` Ch. 19).
   - Models the over-chunking pitfall (`max_num_batched_tokens = 512`, `8.0 ms` chunk + `2.0 ms` decode, `450` context switches/sec,
     `p99 ITL` `28.0 ms -> 45.0 ms`, `TTFT` `180.0 ms -> 320.0 ms`) and chunked-prefill vs whole-sequence prefix cache mismatch
     (`45% -> 8%` hit rate, `5.625x` drop, fixed by chunk-boundary hashing or `RadixAttention`, `V12` Ch. 7 & 8).
3. KV Cache Quantization (`FP8`, `INT4`, `HQQ`), Sliding Window, StreamingLLM Sinks, and `H2O` / `SnapKV` / `LazyLLM` Eviction:
   - Exact KV cache footprints:
     * `70B` MHA (`L=80, H=32, D_head=128`) at `250,000` tokens: `655,360` floats/tok = `1,310,720 B` (`1.31 MB/tok`) in FP16
       = `327.68 GB` (`~328 GB`), reduced to `100-150 GB` (`163.84 GB` pure FP8) with `FP8` + selective-layer caching (`ASP` Ch. 18).
     * `Llama-3-70B` GQA (`L=80, H_q=64, H_kv=8, D_head=128`): `327,680 B` (`320 KiB/tok`) in FP16 (`1.31 GB` / `1.25 GiB` at `4,096`
       tokens; `39.06 GiB` at `128,000` tokens vs `312.5 GiB` MHA) and `163,840 B` (`160 KiB/tok`, `0.65 GB` at `4,096` tokens) in `FP8`.
       Reducing `tokens_per_block` `128 -> 32` (cutting `129`-token internal fragmentation from `127/256 = 49.61%` to `31/160 = 19.38%`),
       enabling `FP8` KV cache, and setting `free_gpu_memory_fraction = 0.85` scales concurrent sessions from `64` (`52%` util) to
       `210` (`91%` util, `3.28x`, `V12` Ch. 5 & 8).
     * `Llama-13B` (`L=40, H=40, D_head=128`) at `4,096` tokens (`ASP` Ch. 17): `0.8192 MB/tok` (`3.36 GB` MHA FP16, `1.68 GB` MHA FP8,
       `0.671 GB` GQA-8 FP16, `0.336 GB` GQA-8 FP8, `0.084 GB` MQA FP16).
   - Real-time `QuantizedCache` (`HQQ` / `Quanto`) policy switching (`start_bits=8 -> fallback_bits=4` at `memory_threshold=0.90` with
     EMA `0.8 * old + 0.2 * new`, `q_group_size=64`, `residual_length=128` recent tokens in `BF16`, `ASP` Ch. 19).
   - Windowed & selective KV eviction: Sliding Window Attention (`SWA` window `W=4096`), `StreamingLLM` attention sinks
     (`N_sink=4` + `W=4092` = `4096`), `H2O` / `SnapKV` heavy-hitter retention (`N_sink + N_heavy + W_local`), and `LazyLLM`
     dynamic token pruning (`20%-30%` latency reduction).
4. Fast Prefill-to-Decode KV Transfer (`NIXL`, `LMCache` RDMA Page Collation, and `[TP_p]`-to-`[TP_d]` KV Transpose):
   - KV transfer rate (`HLS` Ch. 7): `8B` model (`0.15 GB` per `1,024` tokens -> `1.5 GB` per `10,240` tokens) at `16 RPS` requires
     `24.0 GB/s` (`~25 GB/s`), fitting in `900 GB/s` NVLink and `50-100 GB/s` IB RDMA but saturating `10 GB/s` non-RDMA PCIe;
     layer-by-layer async streaming cuts disaggregation overhead to `< 1%` of request latency.
   - `LMCache` RDMA page collation (`ASP` Ch. 18): collating `7,500`-token KV cache from `16`-token pages (`470` transfers, `20.0 ms`)
     into `>= 128`-token slabs (`59` transfers) cuts RDMA latency to `8.0 ms` (`2.5x` faster, `60.0%` reduction); `pd_buffer_size = 1 GiB`
     (`1,073,741,824 B`) for `4k-7.5k` tokens (`2 GiB` for `> 7.5k`), rounded to `256 MB` boundary, with `UCX_RNDV_THRESH = 16384`.
   - Phase-specific parallelism (`TP_p = 2, PP_p = 2` or `PP_p = 4, TP_p = 1` prefill -> `TP_d = 4, PP_d = 1` decode) and on-the-fly
     `[TP_p]`-to-`[TP_d]` KV transpose kernel (`ASP` Ch. 18).
5. Hierarchical KV Cache Offloading (`HBM -> Grace LPDDR5X via NVLink-C2C -> Host DDR5 -> NVMe / GDS / 3FS`) & `LMCache` / `CacheBlend`:
   - `NIXL` KV offload TTFT speedup: `14.0x` on x86+H100 (`PCIe Gen5` `64 GB/s`) vs recomputation, and `2.0x` additional (`28.0x` total)
     on `GH200` `NVLink-C2C` (`900 GB/s` bidirectional, `450 GB/s` per direction); `GB200` superchip (`384 GB` HBM3e + `480 GB` LPDDR5X
     = `~864-900 GB` coherent memory, `~30 TB` per `GB200 NVL72`, `~38 TB` = `20.7 TB` HBM + `18 TB` LPDDR5X per `GB300 NVL72`) and
     `30x` throughput on `680B` MoE (`ASP` Ch. 2, 4, 18).
   - `LMCache` tiered capacity & benchmark (`HLS` Ch. 7): `3x` in CPU RAM (`150.0 GB`), `50x` on NVMe SSD (`120.0 GB`, `chunk_size=2048`),
     `4x` replica cost savings; `1.0 s` CPU retrieval vs `6.0-7.0 s` cold prefill after request `9` of `30`; `16.0x` throughput over
     vanilla `vLLM` `4,700 tok/s` (`75,200 tok/s`) at `5` concurrent long-context requests; RAG (`$0.007`/req, `5.0 s` TTFT) vs
     Long-Context CAG (`$0.013`/req, `0.5 s` TTFT, `10.0x` faster); `CacheBlend` `15%` (`blend_recompute_ratios=0.15`) selective
     recomputation (`85.0%` compute saved, `6.67x` speedup).
   - `GPUDirect Storage` (`gdsio` `-s 10G -i 1M -w 4 -I 0`): `8.0 GB/s` (`1.25 ms`, `-x 2` CPU path) -> `9.6 GB/s` (`1.00 ms`, `-x 0` GDS
     path, `+20.0%` throughput, `-20.0%` latency) and DeepSeek `3FS` `6.6-7.3 TB/s` across `68` nodes vs `1.1 TB/s` Ceph (`ASP` Ch. 5).
6. Heterogeneous PD Hardware Economics, SLO-Aware Admission Control, and Adaptive PD Schedulers (`Splitwise`, `HexGen-2`, `TetriInfer`, `Arrow`, `Mooncake`):
   - `Splitwise` (`1.4x` throughput at `20%` lower cost; `2.35x` RPS at identical cost/power with `4x H100` prefill + `4x A100` decode;
     `6` vs `8` GPUs = `25.0%` hardware savings) and `HexGen-2` (`2.0x` max / `1.3x` avg throughput or `30.0%` cost savings on `Llama-2-70B`).
   - Conditional prefill offload router (`should_offload_prefill`, composite `latency_cost`), Mooncake early rejection (`est_ttft > 500 ms`),
     `qos.yaml` (`10%` premium / `30%` standard / `60%` free), `TetriInfer` instance flip, and `Arrow` adaptive scaling (`5.6x` serving rate).
"""

from __future__ import annotations
import math
from typing import Dict, List


def evaluate_decode_attention_kernels(
    batch_size: int = 1,
    num_query_heads: int = 64,
    num_kv_heads: int = 8,
    seq_len: int = 4096,
    split_chunk_tokens: int = 256,
    num_sms: int = 132,
    flash_mla_tok_s: float = 100.0,
) -> Dict[str, float]:
    """Models FlashAttention-2 vs FlashDecoding/FlashInfer split-KV decode CTAs, XQA GQA packing, ThunderMLA, and POD-Attention."""
    gqa_group_size = num_query_heads // num_kv_heads
    standard_fa2_ctas = batch_size * num_kv_heads
    standard_sm_occupancy_pct = min(100.0, (standard_fa2_ctas / num_sms) * 100.0)

    num_kv_splits = math.ceil(seq_len / split_chunk_tokens)
    flash_decoding_ctas = batch_size * num_kv_heads * num_kv_splits
    split_kv_sm_occupancy_pct = min(100.0, (flash_decoding_ctas / num_sms) * 100.0)

    # Verify online softmax two-stage reduction math on 2 synthetic split chunks:
    # Chunk 0 scores: [1.0, 2.0], Chunk 1 scores: [3.0, 4.0]
    s0 = [1.0, 2.0]
    s1 = [3.0, 4.0]
    m0, m1 = max(s0), max(s1)
    l0 = m0 + math.log(sum(math.exp(x - m0) for x in s0))
    l1 = m1 + math.log(sum(math.exp(x - m1) for x in s1))
    l_max = max(l0, l1)
    l_global = l_max + math.log(math.exp(l0 - l_max) + math.exp(l1 - l_max))
    full_scores = s0 + s1
    m_full = max(full_scores)
    l_exact = m_full + math.log(sum(math.exp(x - m_full) for x in full_scores))
    lse_max_abs_err = abs(l_global - l_exact)

    # DeepSeek MLA latent cache elements per layer: d_c = 512 + d_R = 64 = 576 elements = 2 * 2.25 * 128
    mla_elements_per_layer = 512 + 64
    mla_equivalent_gqa_groups = mla_elements_per_layer / (2.0 * 128.0)

    thunder_mla_min_tok_s = flash_mla_tok_s * 1.20
    thunder_mla_max_tok_s = flash_mla_tok_s * 1.35
    pod_attention_max_gain_pct = 29.0

    return {
        "gqa_group_size": float(gqa_group_size),
        "standard_fa2_ctas": float(standard_fa2_ctas),
        "standard_sm_occupancy_pct": round(standard_sm_occupancy_pct, 2),
        "num_kv_splits": float(num_kv_splits),
        "flash_decoding_ctas": float(flash_decoding_ctas),
        "split_kv_sm_occupancy_pct": round(split_kv_sm_occupancy_pct, 2),
        "flash_decoding_max_speedup_x": 8.0,
        "lse_max_abs_err": lse_max_abs_err,
        "mla_elements_per_layer": float(mla_elements_per_layer),
        "mla_equivalent_gqa_groups": round(mla_equivalent_gqa_groups, 2),
        "thunder_mla_min_tok_s": round(thunder_mla_min_tok_s, 2),
        "thunder_mla_max_tok_s": round(thunder_mla_max_tok_s, 2),
        "pod_attention_max_gain_pct": pod_attention_max_gain_pct,
    }


def evaluate_chunked_prefill_tuning(
    prompt_tokens: int = 12288,
    active_decode_seqs: int = 45,
    max_num_batched_tokens: int = 2048,
    sarathi_prompt_tokens: int = 10000,
    sarathi_chunk_tokens: int = 2000,
) -> Dict[str, float]:
    """Models Sarathi-Lean chunked prefill token budgets, over-chunking context-switch overhead, and prefix-cache alignment."""
    decode_tokens_per_iter = active_decode_seqs
    available_prefill_budget = max_num_batched_tokens - decode_tokens_per_iter
    # Standard fixed chunk C = 2048 (when decode = 0) or C = 1536 (with 512 decodes)
    num_chunks_2048 = math.ceil(prompt_tokens / max_num_batched_tokens)
    num_chunks_with_decode = math.ceil(prompt_tokens / available_prefill_budget)

    # V12 Ch. 8 example: M_decode = 512 + C_prefill = 1536 = 2048 tokens -> 22-24 ms ITL vs 250 ms unchunked
    v12_ch8_decode = 512
    v12_ch8_prefill_chunk = 1536
    v12_ch8_total_tokens = v12_ch8_decode + v12_ch8_prefill_chunk

    # V12 Ch. 7 Scenario 1: 12,288-token burst on 4x H100 (45 active decode streams)
    unchunked_prefill_stall_ms = 320.0
    unchunked_p99_itl_ms = 340.0
    chunked_p99_itl_ms = 21.4
    itl_reduction_x = unchunked_p99_itl_ms / chunked_p99_itl_ms

    # ASP Ch. 19 SARATHI: 10,000-token prompt into 5 chunks of 2,000 tokens (50-100 ms per chunk, 1.3x-1.9x throughput)
    sarathi_num_chunks = sarathi_prompt_tokens // sarathi_chunk_tokens

    # V12 Ch. 7 Troubleshooting: Over-chunking at max_num_batched_tokens = 512
    overchunk_prefill_ms = 8.0
    overchunk_decode_ms = 2.0
    overchunk_switches_per_sec = 450.0
    overchunk_p99_itl_before_ms = 28.0
    overchunk_p99_itl_after_ms = 45.0
    overchunk_ttft_before_ms = 180.0
    overchunk_ttft_after_ms = 320.0

    # V12 Ch. 8 PCIe swap thrashing: 20 ms -> 850 ms ITL (42.5x degradation)
    swap_thrash_itl_before_ms = 20.0
    swap_thrash_itl_after_ms = 850.0
    swap_thrash_degradation_x = swap_thrash_itl_after_ms / swap_thrash_itl_before_ms  # 42.5x
    prefix_hit_before_chunking = 0.45
    prefix_hit_after_naive_chunking = 0.08
    prefix_hit_drop_x = prefix_hit_before_chunking / prefix_hit_after_naive_chunking

    return {
        "decode_tokens_per_iter": float(decode_tokens_per_iter),
        "available_prefill_budget": float(available_prefill_budget),
        "num_chunks_2048": float(num_chunks_2048),
        "num_chunks_with_decode": float(num_chunks_with_decode),
        "v12_ch8_total_tokens": float(v12_ch8_total_tokens),
        "unchunked_prefill_stall_ms": unchunked_prefill_stall_ms,
        "unchunked_p99_itl_ms": unchunked_p99_itl_ms,
        "chunked_p99_itl_ms": chunked_p99_itl_ms,
        "itl_reduction_x": round(itl_reduction_x, 2),
        "sarathi_num_chunks": float(sarathi_num_chunks),
        "sarathi_min_speedup_x": 1.3,
        "sarathi_max_speedup_x": 1.9,
        "overchunk_prefill_ms": overchunk_prefill_ms,
        "overchunk_decode_ms": overchunk_decode_ms,
        "overchunk_switches_per_sec": overchunk_switches_per_sec,
        "overchunk_p99_itl_before_ms": overchunk_p99_itl_before_ms,
        "overchunk_p99_itl_after_ms": overchunk_p99_itl_after_ms,
        "overchunk_ttft_before_ms": overchunk_ttft_before_ms,
        "overchunk_ttft_after_ms": overchunk_ttft_after_ms,
        "prefix_hit_before_chunking": prefix_hit_before_chunking,
        "prefix_hit_after_naive_chunking": prefix_hit_after_naive_chunking,
        "prefix_hit_drop_x": round(prefix_hit_drop_x, 3),
    }


def evaluate_kv_quantization_and_eviction(
    seq_len_Test: int = 129,
    used_ratios: List[float] | None = None,
) -> Dict[str, float]:
    """Models FP16/FP8/INT4 KV cache sizing, block fragmentation, HQQ dynamic bit-width switching, SWA, StreamingLLM, and H2O/SnapKV."""
    # 1. ASP Ch. 18: 70B MHA (L=80, H=32, D_head=128) at 250,000 tokens
    mha70b_floats_per_layer = 2 * 32 * 128  # 8,192
    mha70b_floats_per_tok = 80 * mha70b_floats_per_layer  # 655,360
    mha70b_fp16_bytes_per_tok = mha70b_floats_per_tok * 2  # 1,310,720 B (~1.31 MB)
    mha70b_250k_fp16_gb = (mha70b_fp16_bytes_per_tok * 250000) / 1e9  # 327.68 GB (~328 GB)
    mha70b_250k_fp8_gb = mha70b_250k_fp16_gb / 2.0  # 163.84 GB (reduced to 100-150 GB with selective layer caching)

    # 2. V12 Ch. 5 & 8: Llama-3-70B GQA (L=80, H_q=64, H_kv=8, D_head=128)
    l3_70b_fp16_bytes_per_tok = 2 * 80 * 8 * 128 * 2  # 327,680 B = 320 KiB
    l3_70b_fp8_bytes_per_tok = 2 * 80 * 8 * 128 * 1   # 163,840 B = 160 KiB
    l3_70b_int4_bytes_per_tok = int(2 * 80 * 8 * 128 * 0.5)  # 81,920 B = 80 KiB
    l3_70b_4k_fp16_gb = (l3_70b_fp16_bytes_per_tok * 4096) / (1024 ** 3)  # 1.25 GiB (1.342 GB / ~1.31 GB in V12 Ch. 5)
    l3_70b_4k_fp8_gb = (l3_70b_fp8_bytes_per_tok * 4096) / (1024 ** 3)    # 0.625 GiB (~0.65 GB in V12 Ch. 5)
    l3_70b_128k_gqa_gib = (l3_70b_fp16_bytes_per_tok * 128000) / (1024 ** 3)  # 39.0625 GiB
    l3_70b_128k_mha_gib = l3_70b_128k_gqa_gib * 8.0  # 312.5 GiB

    # Block internal fragmentation at S = 129 tokens: block_size=128 vs block_size=32 (V12 Ch. 5 Scenario 2)
    alloc_128 = math.ceil(seq_len_Test / 128) * 128  # 256
    waste_128_pct = ((alloc_128 - seq_len_Test) / alloc_128) * 100.0  # 127 / 256 = 49.61%
    alloc_32 = math.ceil(seq_len_Test / 32) * 32     # 160
    waste_32_pct = ((alloc_32 - seq_len_Test) / alloc_32) * 100.0      # 31 / 160 = 19.38%

    # 3. ASP Ch. 17: Llama-13B (L=40, H=40, D_head=128) at 4,096 tokens
    l13b_mha_fp16_mb_per_tok = (2 * 40 * 40 * 128 * 2) / 1e6  # 0.8192 MB/token
    l13b_4k_mha_fp16_gb = (2 * 40 * 40 * 128 * 2 * 4096) / 1e9   # 3.355 GB (~3.36 GB)
    l13b_4k_mha_fp8_gb = l13b_4k_mha_fp16_gb / 2.0               # 1.678 GB (~1.68 GB)
    l13b_4k_gqa8_fp16_gb = (2 * 40 * 8 * 128 * 2 * 4096) / 1e9   # 0.671 GB
    l13b_4k_gqa8_fp8_gb = l13b_4k_gqa8_fp16_gb / 2.0             # 0.336 GB
    l13b_4k_mqa_fp16_gb = (2 * 40 * 1 * 128 * 2 * 4096) / 1e9    # 0.084 GB

    # 4. ASP Ch. 19: Real-time HQQ QuantizedCache policy switching (start_bits=8 -> fallback_bits=4 at threshold=0.90)
    if used_ratios is None:
        used_ratios = [0.85, 0.92, 0.95, 0.96, 0.97]
    ema_ratio = used_ratios[0]
    current_bits = 8
    bit_history: List[int] = []
    for idx, r in enumerate(used_ratios):
        if idx > 0:
            ema_ratio = 0.8 * ema_ratio + 0.2 * r
        if ema_ratio >= 0.90:
            current_bits = min(current_bits, 4)
        bit_history.append(current_bits)

    # Effective bytes per token for Llama-3-70B with residual_length=128 in BF16 (2B) and older tokens in INT4 (0.5B) at S=4096:
    residual_len = 128
    older_len = 4096 - residual_len
    hqq_int4_total_bytes = (residual_len * l3_70b_fp16_bytes_per_tok) + (older_len * l3_70b_int4_bytes_per_tok)
    hqq_int4_compression_x = (4096 * l3_70b_fp16_bytes_per_tok) / hqq_int4_total_bytes

    # 5. Windowed / Sink / Heavy-Hitter Eviction (SWA, StreamingLLM, H2O/SnapKV) at S = 128,000
    swa_window = 4096
    sink_tokens = 4
    streaming_llm_active_tokens = sink_tokens + (swa_window - sink_tokens)  # 4096
    h2o_heavy_hitters = 1024
    h2o_local_window = 1024
    h2o_retained_tokens = sink_tokens + h2o_heavy_hitters + h2o_local_window  # 2,052 tokens
    swa_kv_reduction_x = 128000.0 / streaming_llm_active_tokens  # 31.25x

    return {
        "mha70b_floats_per_layer": float(mha70b_floats_per_layer),
        "mha70b_floats_per_tok": float(mha70b_floats_per_tok),
        "mha70b_fp16_bytes_per_tok": float(mha70b_fp16_bytes_per_tok),
        "mha70b_250k_fp16_gb": round(mha70b_250k_fp16_gb, 2),
        "mha70b_250k_fp8_gb": round(mha70b_250k_fp8_gb, 2),
        "l3_70b_fp16_bytes_per_tok": float(l3_70b_fp16_bytes_per_tok),
        "l3_70b_fp8_bytes_per_tok": float(l3_70b_fp8_bytes_per_tok),
        "l3_70b_int4_bytes_per_tok": float(l3_70b_int4_bytes_per_tok),
        "l3_70b_4k_fp16_gib": round(l3_70b_4k_fp16_gb, 3),
        "l3_70b_4k_fp8_gib": round(l3_70b_4k_fp8_gb, 3),
        "l3_70b_128k_gqa_gib": round(l3_70b_128k_gqa_gib, 2),
        "l3_70b_128k_mha_gib": round(l3_70b_128k_mha_gib, 1),
        "waste_128_pct": round(waste_128_pct, 2),
        "waste_32_pct": round(waste_32_pct, 2),
        "sessions_before_tuning": 64.0,
        "sessions_after_tuning": 210.0,
        "util_before_pct": 52.0,
        "util_after_pct": 91.0,
        "l13b_mha_fp16_mb_per_tok": round(l13b_mha_fp16_mb_per_tok, 4),
        "l13b_4k_mha_fp16_gb": round(l13b_4k_mha_fp16_gb, 2),
        "l13b_4k_mha_fp8_gb": round(l13b_4k_mha_fp8_gb, 2),
        "l13b_4k_gqa8_fp16_gb": round(l13b_4k_gqa8_fp16_gb, 3),
        "l13b_4k_gqa8_fp8_gb": round(l13b_4k_gqa8_fp8_gb, 3),
        "l13b_4k_mqa_fp16_gb": round(l13b_4k_mqa_fp16_gb, 3),
        "hqq_final_bits": float(bit_history[-1]),
        "hqq_int4_compression_x": round(hqq_int4_compression_x, 2),
        "streaming_llm_active_tokens": float(streaming_llm_active_tokens),
        "h2o_retained_tokens": float(h2o_retained_tokens),
        "swa_kv_reduction_x": round(swa_kv_reduction_x, 2),
    }


def evaluate_pd_kv_transfer_and_transpose(
    seq_len: int = 7500,
    small_page_tokens: int = 16,
    collated_page_tokens: int = 128,
    tp_prefill: int = 1,
    pp_prefill: int = 4,
    tp_decode: int = 4,
    pp_decode: int = 1,
    num_kv_heads: int = 8,
) -> Dict[str, float]:
    """Models PD KV transfer bandwidth, LMCache RDMA page collation (20 ms -> 8 ms), NIXL buffer sizing, and [TP_p]->[TP_d] transpose."""
    # HLS Ch. 7: 8B model with 1,024 tokens = 0.1-0.15 GB -> 10,240 tokens = 1.0-1.5 GB -> at 16 RPS = 16-24 GB/s (~25 GB/s)
    kv_8b_1k_max_gb = 0.15
    kv_8b_10k_max_gb = kv_8b_1k_max_gb * 10.0  # 1.5 GB
    rps_target = 16.0
    required_bw_gb_s = kv_8b_10k_max_gb * rps_target  # 24.0 GB/s (~25 GB/s)

    # ASP Ch. 18: LMCache 7,500-token RDMA collation (470 small transfers at 20 ms -> 128-token collated slabs at 8 ms)
    small_transfers = math.ceil(seq_len / small_page_tokens)  # 469 (~470)
    collated_transfers = math.ceil(seq_len / collated_page_tokens)  # 59
    uncollated_rdma_ms = 20.0
    collated_rdma_ms = 8.0
    collation_speedup_x = uncollated_rdma_ms / collated_rdma_ms  # 2.5x
    collation_latency_reduction_pct = ((uncollated_rdma_ms - collated_rdma_ms) / uncollated_rdma_ms) * 100.0  # 60.0%

    # ASP Ch. 18: NIXL pd_buffer_size = 1 GiB (1,073,741,824 B) for 4k-7.5k tokens, 2 GiB for > 7.5k tokens
    pd_buffer_1gib_bytes = 1073741824
    # For 7,500 tokens on Llama-3-70B GQA (327,680 B/tok in FP16), raw KV = 2,457,600,000 B (~2.29 GiB in FP16, ~1.14 GiB in FP8)
    raw_7500_fp8_bytes = 7500 * 163840
    align_256mb = 256 * 1024 * 1024
    aligned_fp8_buffer_bytes = math.ceil(raw_7500_fp8_bytes / align_256mb) * align_256mb  # 1,342,177,280 B (1.25 GiB)

    # ASP Ch. 18: Phase-specific parallelism transpose [TP_p=1, PP_p=4] -> [TP_d=4, PP_d=1]
    kv_heads_per_prefill_gpu = num_kv_heads // tp_prefill  # 8
    kv_heads_per_decode_gpu = num_kv_heads // tp_decode    # 2 (1/4 of full KV tensor per decode rank)
    decode_shard_fraction = tp_prefill / tp_decode         # 0.25

    return {
        "kv_8b_10k_max_gb": kv_8b_10k_max_gb,
        "required_bw_gb_s": round(required_bw_gb_s, 2),
        "small_transfers": float(small_transfers),
        "collated_transfers": float(collated_transfers),
        "uncollated_rdma_ms": uncollated_rdma_ms,
        "collated_rdma_ms": collated_rdma_ms,
        "collation_speedup_x": round(collation_speedup_x, 2),
        "collation_latency_reduction_pct": round(collation_latency_reduction_pct, 1),
        "pd_buffer_1gib_bytes": float(pd_buffer_1gib_bytes),
        "aligned_fp8_buffer_mib": float(aligned_fp8_buffer_bytes // (1024 * 1024)),
        "ucx_rndv_thresh": 16384.0,
        "kv_heads_per_prefill_gpu": float(kv_heads_per_prefill_gpu),
        "kv_heads_per_decode_gpu": float(kv_heads_per_decode_gpu),
        "decode_shard_fraction": round(decode_shard_fraction, 2),
    }


def evaluate_hierarchical_kv_offload() -> Dict[str, float]:
    """Models HBM -> Grace LPDDR5X (NVLink-C2C) -> Host DDR5 (LMCache) -> NVMe/GDS/3FS hierarchical KV cache offloading."""
    # 1. ASP Ch. 2 & 4: Superchip memory & NIXL KV offload TTFT speedups
    nvlink_c2c_bidirectional_gb_s = 900.0
    nvlink_c2c_unidirectional_gb_s = 450.0
    pcie_gen5_unidirectional_gb_s = 64.0
    c2c_vs_pcie_bw_ratio = nvlink_c2c_unidirectional_gb_s / pcie_gen5_unidirectional_gb_s  # 7.03x

    gb200_hbm_total_gb = 2 * 192.0  # 384 GB (360 GB usable)
    gb200_lpddr5x_gb = 480.0
    gb200_superchip_total_gb = gb200_hbm_total_gb + gb200_lpddr5x_gb  # 864 GB (~900 GB)
    gb300_nvl72_hbm_tb = (72 * 288.0) / 1000.0  # 20.736 TB (~20.7 TB)
    gb300_nvl72_ddr_tb = (36 * 500.0) / 1000.0  # 18.0 TB
    gb300_nvl72_total_tb = round(gb300_nvl72_hbm_tb, 1) + gb300_nvl72_ddr_tb  # 38.7 TB (~38 TB)

    nixl_x86_h100_ttft_speedup_x = 14.0
    nixl_gh200_vs_x86_ttft_speedup_x = 2.0
    nixl_gh200_total_ttft_speedup_x = nixl_x86_h100_ttft_speedup_x * nixl_gh200_vs_x86_ttft_speedup_x  # 28.0x
    dynamo_nvl72_680b_speedup_x = 30.0

    # 2. HLS Ch. 7: LMCache tiered expansion, warm-cache latency, 5-way concurrent throughput, RAG vs CAG, and CacheBlend
    lmcache_cpu_capacity_mult = 3.0
    lmcache_ssd_capacity_mult = 50.0
    lmcache_replica_cost_savings_x = 4.0
    lmcache_cpu_warm_latency_s = 1.0
    vanilla_cold_prefill_min_s = 6.0
    vanilla_cold_prefill_max_s = 7.0
    vanilla_vllm_concurrent_tps = 4700.0
    lmcache_throughput_mult = 16.0
    lmcache_concurrent_tps = vanilla_vllm_concurrent_tps * lmcache_throughput_mult  # 75,200 tok/s

    # RAG vs Long-Context CAG (HLS Ch. 7): GPT-5 $1.25/1M regular, $0.125/1M cached
    rag_uncached_tokens = 5000 + 500  # 5,500
    cag_uncached_tokens = 500
    rag_cost_usd = (500 * 0.125 + 5500 * 1.25) / 1e6     # $0.0069375 (~$0.007)
    cag_cost_usd = (500 * 0.125 + 100500 * 0.125) / 1e6  # $0.012625 (~$0.013)
    rag_ttft_s = 5.0
    cag_ttft_s = 0.5
    cag_ttft_speedup_x = rag_ttft_s / cag_ttft_s  # 10.0x

    # CacheBlend selective recomputation (default 15% recompute -> 85% saved)
    cacheblend_recompute_ratio = 0.15
    cacheblend_saved_pct = (1.0 - cacheblend_recompute_ratio) * 100.0  # 85.0%
    cacheblend_compute_reduction_x = 1.0 / cacheblend_recompute_ratio  # 6.67x

    # 3. ASP Ch. 5: GPUDirect Storage gdsio benchmark & DeepSeek 3FS
    gds_cpu_bw_gb_s = 8.0
    gds_direct_bw_gb_s = 9.6
    gds_bw_gain_pct = ((gds_direct_bw_gb_s - gds_cpu_bw_gb_s) / gds_cpu_bw_gb_s) * 100.0  # +20.0%
    gds_cpu_lat_ms = 1.25
    gds_direct_lat_ms = 1.00
    gds_lat_reduction_pct = ((gds_cpu_lat_ms - gds_direct_lat_ms) / gds_cpu_lat_ms) * 100.0  # 20.0%
    deepseek_3fs_bw_tb_s = 6.6
    ceph_bw_tb_s = 1.1
    deepseek_3fs_vs_ceph_x = deepseek_3fs_bw_tb_s / ceph_bw_tb_s  # 6.0x

    return {
        "nvlink_c2c_bidirectional_gb_s": nvlink_c2c_bidirectional_gb_s,
        "nvlink_c2c_unidirectional_gb_s": nvlink_c2c_unidirectional_gb_s,
        "c2c_vs_pcie_bw_ratio": round(c2c_vs_pcie_bw_ratio, 2),
        "gb200_superchip_total_gb": gb200_superchip_total_gb,
        "gb300_nvl72_total_tb": round(gb300_nvl72_total_tb, 1),
        "nixl_x86_h100_ttft_speedup_x": nixl_x86_h100_ttft_speedup_x,
        "nixl_gh200_vs_x86_ttft_speedup_x": nixl_gh200_vs_x86_ttft_speedup_x,
        "nixl_gh200_total_ttft_speedup_x": nixl_gh200_total_ttft_speedup_x,
        "dynamo_nvl72_680b_speedup_x": dynamo_nvl72_680b_speedup_x,
        "lmcache_cpu_capacity_mult": lmcache_cpu_capacity_mult,
        "lmcache_ssd_capacity_mult": lmcache_ssd_capacity_mult,
        "lmcache_replica_cost_savings_x": lmcache_replica_cost_savings_x,
        "lmcache_cpu_warm_latency_s": lmcache_cpu_warm_latency_s,
        "vanilla_cold_prefill_min_s": vanilla_cold_prefill_min_s,
        "vanilla_cold_prefill_max_s": vanilla_cold_prefill_max_s,
        "vanilla_vllm_concurrent_tps": vanilla_vllm_concurrent_tps,
        "lmcache_throughput_mult": lmcache_throughput_mult,
        "lmcache_concurrent_tps": lmcache_concurrent_tps,
        "rag_uncached_tokens": float(rag_uncached_tokens),
        "cag_uncached_tokens": float(cag_uncached_tokens),
        "rag_cost_usd": round(rag_cost_usd, 3),
        "cag_cost_usd": round(cag_cost_usd, 3),
        "cag_ttft_speedup_x": round(cag_ttft_speedup_x, 1),
        "cacheblend_recompute_ratio": cacheblend_recompute_ratio,
        "cacheblend_saved_pct": round(cacheblend_saved_pct, 1),
        "cacheblend_compute_reduction_x": round(cacheblend_compute_reduction_x, 2),
        "gds_bw_gain_pct": round(gds_bw_gain_pct, 1),
        "gds_lat_reduction_pct": round(gds_lat_reduction_pct, 1),
        "deepseek_3fs_vs_ceph_x": round(deepseek_3fs_vs_ceph_x, 1),
    }


def should_offload_prefill(
    prompt_length: int,
    prefix_cached_length: int,
    prefill_queue_size: int,
    decode_active_reqs: int,
    prefill_length_threshold: int = 256,
    prefill_queue_max: int = 10,
    decode_load_threshold: int = 8,
) -> bool:
    """Implements ASP Ch. 17 conditional prefill offload routing policy."""
    eff_len = max(0, prompt_length - prefix_cached_length)
    long_prefill = eff_len >= prefill_length_threshold
    prefill_available = prefill_queue_size < prefill_queue_max
    if long_prefill and prefill_available:
        return True
    if decode_active_reqs >= decode_load_threshold and eff_len >= 64:
        return True
    return False


def compute_worker_latency_cost(
    occupancy_percent: float,
    active_reqs: int,
    cache_match_flag: bool,
    mem_bw_percent: float,
    recent_prefix_flag: bool,
) -> float:
    """Implements ASP Ch. 17 Table 17-3 multifactor KV-aware latency cost function (lower is better)."""
    return (
        3.0 * occupancy_percent
        + 1.0 * active_reqs
        - 10.0 * int(cache_match_flag)
        + 0.5 * mem_bw_percent
        - 1.0 * int(recent_prefix_flag)
    )


def evaluate_heterogeneous_and_slo_schedulers() -> Dict[str, float]:
    """Models Splitwise, HexGen-2, conditional routing, QoS reservations, Mooncake early rejection, and Arrow adaptive scaling."""
    # 1. Splitwise & HexGen-2 heterogeneous PD hardware economics (ASP Ch. 18)
    splitwise_throughput_gain_x = 1.4
    splitwise_cost_reduction_pct = 20.0
    splitwise_iso_budget_rps_x = 2.35  # 4x H100 prefill + 4x A100 decode vs 8-GPU homogeneous
    splitwise_gpu_count_reduction_pct = ((8.0 - 6.0) / 8.0) * 100.0  # 25.0%

    hexgen2_max_throughput_x = 2.0
    hexgen2_avg_throughput_x = 1.3
    hexgen2_cost_reduction_pct = 30.0

    # 2. ASP Ch. 18 QoS capacity reservation (qos.yaml)
    qos_premium_frac = 0.10
    qos_standard_frac = 0.30
    qos_free_frac = 0.60
    qos_total_frac = qos_premium_frac + qos_standard_frac + qos_free_frac

    # 3. ASP Ch. 17 & 18 Mooncake / QoSController early rejection (ttft_slo_ms = 500 ms)
    prefill_queue_len = 6
    avg_prefill_ms = 65.0
    decode_queue_len = 8
    avg_decode_ms = 20.0
    est_ttft_ms = prefill_queue_len * avg_prefill_ms + decode_queue_len * avg_decode_ms  # 390 + 160 = 550 ms > 500 ms
    ttft_slo_ms = 500.0
    low_priority_admitted = est_ttft_ms <= ttft_slo_ms
    high_priority_admitted = True

    # 4. ASP Ch. 18 Arrow adaptive instance scaling
    arrow_max_serving_rate_x = 5.6

    return {
        "splitwise_throughput_gain_x": splitwise_throughput_gain_x,
        "splitwise_cost_reduction_pct": splitwise_cost_reduction_pct,
        "splitwise_iso_budget_rps_x": splitwise_iso_budget_rps_x,
        "splitwise_gpu_count_reduction_pct": round(splitwise_gpu_count_reduction_pct, 1),
        "hexgen2_max_throughput_x": hexgen2_max_throughput_x,
        "hexgen2_avg_throughput_x": hexgen2_avg_throughput_x,
        "hexgen2_cost_reduction_pct": hexgen2_cost_reduction_pct,
        "qos_premium_frac": qos_premium_frac,
        "qos_standard_frac": qos_standard_frac,
        "qos_free_frac": qos_free_frac,
        "qos_total_frac": round(qos_total_frac, 2),
        "est_ttft_ms": round(est_ttft_ms, 1),
        "low_priority_admitted": 1.0 if low_priority_admitted else 0.0,
        "high_priority_admitted": 1.0 if high_priority_admitted else 0.0,
        "arrow_max_serving_rate_x": arrow_max_serving_rate_x,
    }


if __name__ == "__main__":
    print("Chapter 15.11 Advanced Prefill-Decode and KV Cache Tuning Model:")
    print("  1. Decode Kernels:", evaluate_decode_attention_kernels())
    print("  2. Chunked Prefill:", evaluate_chunked_prefill_tuning())
    print("  3. KV Quantization & Eviction:", evaluate_kv_quantization_and_eviction())
    print("  4. PD KV Transfer & Transpose:", evaluate_pd_kv_transfer_and_transpose())
    print("  5. Hierarchical KV Offload:", evaluate_hierarchical_kv_offload())
    print("  6. Heterogeneous & SLO Schedulers:", evaluate_heterogeneous_and_slo_schedulers())
