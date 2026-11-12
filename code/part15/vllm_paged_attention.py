#!/usr/bin/env python3
"""Chapter 15.3 model: vLLM in Depth (PagedAttention, APC, Chunked Prefill, V1 Engine, Multi-LoRA, and Parallelism).

Models:
1. KV Cache Footprint & PagedAttention Block Table / Fragmentation Model:
   - Per-token KV cache bytes: `2 * num_layers * num_kv_heads * head_dim * precision_bytes`.
   - Llama-3-70B (`L=80, H_q=64, H_kv=8, D_head=128, P=2` BF16): `327,680 B = 320 KiB/token` (`8x` smaller
     than MHA `H_kv=64` at `2,621,440 B = 2.56 MiB/token`, an `87.5%` reduction); `1.25 GiB` at `S=4096` and
     `39.0625 GiB` (`39.06 GiB`) at `S=128,000` (vs `312.5 GiB` under MHA); 250,000-token MHA (`H_kv=32`)
     at FP16 = `1.31072 MB/token` (`~1.31 MB/token`) = `327.68 GB` (`~328 GB`) vs `100-150 GB` FP8.
   - Contiguous allocation (`S_max=4096` or `32768`, `60%-80%` VRAM waste) vs PagedAttention (`B=16` or `32`
     tokens/block, `N_i = ceil(S_actual / B)`, `0%` external fragmentation, `< B / S_actual` internal
     fragmentation, `< 4%` overall waste; at `S_actual=500, B=16`, internal waste is `12/500 = 2.4% < 3.2%`
     max bound `15/500 = 3.0%` vs `(4096 - 500) / 4096 = 87.79% > 87%` contiguous waste).
   - Zero padding FLOPs: batch of `[4, 7, 3]` tokens padded to `7 * 3 = 21` positions wastes `7 / 21 = 33.33%`
     (`33%`) of attention FLOPs on `<pad>` tokens vs `14` true tokens (`0%` padding FLOPs) in PagedAttention.
2. PagedAttention BlockSpaceManager, Copy-on-Write (CoW), and Automatic Prefix Caching (APC):
   - Simulates `BlockSpaceManager` logical-to-physical Block Table mapping, reference counting (`ref_count`),
     Copy-on-Write beam search / parallel sampling (`n=4` forks sharing prompt physical blocks until a child
     writes to a shared block), and SHA-256 block-hash Automatic Prefix Caching (`block_size=16`).
   - Models the V12 Ch. 6 24,000-token RAG scenario (`ceil(24000 / 16) = 1,500` blocks per request, `15,000`
     blocks for `10` concurrent requests) and compares RAG vs Long-Context CAG token/cost math (`HLS` Ch. 7:
     `5,500` vs `500` uncached prefill tokens, `5.0 s -> 0.5 s` TTFT, `$0.007` vs `$0.013` per request).
3. Continuous Batching, Chunked Prefill, and Preemption (Swap vs Recompute):
   - Models vLLM's token-budget scheduler (`num_new_tokens = num_tokens_with_spec + num_output_placeholders -
     num_computed_tokens`, capped by `long_prefill_token_threshold` and `max_num_batched_tokens=2048`).
   - Compares PCIe `Swap` (`t_swap = 2 * KV_bytes / B_PCIe`, `62.5 ms` one-way / `125.0 ms` round-trip for `4 GB`
     over `64 GB/s` PCIe Gen4/Gen5) against GPU `Recompute` (`t_recompute = (2 * L * S^2 * H + 12 * L * S * H^2)
     / T_GPU` on `989 TFLOPS` dense BF16 H100, an upper bound that assumes 100 percent utilisation). For the GQA
     Llama-3-70B (8 KV heads) the round-trip swap at `S=4096` is about `42 ms` against about `289 ms` recompute,
     so on paper swap is faster; vLLM V1 recomputes anyway because it removed swap.
4. Distributed Parallelism (TP, PP, DP, EP), Concurrency Capacity Planning & Speculative Decoding:
   - Models Llama-3-70B concurrency `C_max` across `4x 80 GB` (`TP=4`, `140 GB` KV pool -> `218, 54, 13`
     requests at `S=2048, 8192, 32768`) and `8x 80 GB` (`TP=8`, `428 GB` KV pool -> `668, 167, 41` requests),
     `140B` on `141 GB` H200 (`~20 GB` free on 1 GPU vs `~70 GB`/GPU at `TP=2`), and DeepSeek-R1 `671B`
     (`256` routed experts, `EP_SIZE = TP_SIZE * DP_SIZE = 8` -> `32` experts/GPU; `TP=4, PP=8` across `32`
     GPUs -> `83.875B` / `~84B` params per stage, activation shard `hidden_size / 4 = 2048`).
5. Multi-LoRA Serving (Punica / S-LoRA) & Lab 03 Telemetry Verification:
   - Models LoRA parameter footprint (`2 * r * d_model * num_adapted_projections * num_layers * bytes`) and
     single-GPU multi-LoRA batching (`1` GPU vs `N` GPUs), plus Lab 03 `Qwen2.5-Coder-1.5B-Instruct` block pool
     (`14,258` GPU blocks at `0.85` utilization = `55.69x` concurrency at `4096` tokens vs `120` blocks at `0.25`)
     and streaming TTFT (`44.83 ms` mean, `47.72 ms` p95) / ITL (`12.72 ms` mean, `13.05 ms` p95).
"""

from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import math
from typing import Dict, List, Optional, Tuple


def compute_kv_cache_metrics(
    num_layers: int = 80,
    num_query_heads: int = 64,
    num_kv_heads: int = 8,
    head_dim: int = 128,
    precision_bytes: float = 2.0,
    seq_len: int = 4096,
    block_size: int = 16,
    max_model_len: int = 4096,
) -> Dict[str, float]:
    """Computes per-token and per-sequence KV cache footprints and PagedAttention vs contiguous waste."""
    gqa_group_size = num_query_heads // num_kv_heads
    bytes_per_token_gqa = 2.0 * num_layers * num_kv_heads * head_dim * precision_bytes
    bytes_per_token_mha = 2.0 * num_layers * num_query_heads * head_dim * precision_bytes
    kib_per_token_gqa = bytes_per_token_gqa / 1024.0
    mib_per_token_mha = bytes_per_token_mha / (1024.0 * 1024.0)
    gqa_savings_pct = (1.0 - (bytes_per_token_gqa / bytes_per_token_mha)) * 100.0

    seq_bytes_gqa = bytes_per_token_gqa * seq_len
    seq_gib_gqa = seq_bytes_gqa / (1024.0 ** 3)
    seq_gib_mha = (bytes_per_token_mha * seq_len) / (1024.0 ** 3)

    num_blocks = math.ceil(seq_len / block_size)
    allocated_paged_tokens = num_blocks * block_size
    wasted_paged_tokens = allocated_paged_tokens - seq_len
    paged_internal_frag_pct = (wasted_paged_tokens / seq_len) * 100.0
    paged_max_bound_pct = (block_size / seq_len) * 100.0
    contiguous_waste_pct = ((max_model_len - seq_len) / max_model_len) * 100.0 if max_model_len >= seq_len else 0.0

    return {
        "gqa_group_size": float(gqa_group_size),
        "bytes_per_token_gqa": bytes_per_token_gqa,
        "bytes_per_token_mha": bytes_per_token_mha,
        "kib_per_token_gqa": kib_per_token_gqa,
        "mib_per_token_mha": mib_per_token_mha,
        "gqa_savings_pct": round(gqa_savings_pct, 2),
        "seq_gib_gqa": round(seq_gib_gqa, 4),
        "seq_gib_mha": round(seq_gib_mha, 4),
        "num_blocks": float(num_blocks),
        "allocated_paged_tokens": float(allocated_paged_tokens),
        "wasted_paged_tokens": float(wasted_paged_tokens),
        "paged_internal_frag_pct": round(paged_internal_frag_pct, 2),
        "paged_max_bound_pct": round(paged_max_bound_pct, 2),
        "contiguous_waste_pct": round(contiguous_waste_pct, 2),
    }


def compute_padding_flops_waste(seq_lengths: List[int]) -> Dict[str, float]:
    """Computes attention position count and wasted padding FLOPs in contiguous batching vs PagedAttention."""
    batch_size = len(seq_lengths)
    max_len = max(seq_lengths) if seq_lengths else 0
    padded_positions = batch_size * max_len
    true_tokens = sum(seq_lengths)
    wasted_positions = padded_positions - true_tokens
    wasted_flops_pct = (wasted_positions / padded_positions) * 100.0 if padded_positions > 0 else 0.0
    return {
        "batch_size": float(batch_size),
        "max_len": float(max_len),
        "padded_positions": float(padded_positions),
        "true_tokens": float(true_tokens),
        "wasted_positions": float(wasted_positions),
        "wasted_flops_pct": round(wasted_flops_pct, 2),
        "paged_attention_positions": float(true_tokens),
        "paged_wasted_flops_pct": 0.0,
    }


@dataclass
class PhysicalBlock:
    block_id: int
    block_size: int
    ref_count: int = 0
    tokens: List[int] = field(default_factory=list)
    block_hash: Optional[str] = None


class PagedAttentionSimulator:
    """Simulates vLLM's BlockSpaceManager with logical-to-physical Block Tables, Copy-on-Write, and APC."""

    def __init__(self, num_blocks: int, block_size: int = 16, enable_prefix_caching: bool = True) -> None:
        self.num_blocks = num_blocks
        self.block_size = block_size
        self.enable_prefix_caching = enable_prefix_caching
        self.blocks: Dict[int, PhysicalBlock] = {
            i: PhysicalBlock(block_id=i, block_size=block_size) for i in range(num_blocks)
        }
        self.free_block_ids: List[int] = list(range(num_blocks))
        self.block_tables: Dict[int, List[int]] = {}
        self.hash_to_block_id: Dict[str, int] = {}
        self.cache_hits: int = 0
        self.cache_queries: int = 0
        self.cow_copies: int = 0

    @property
    def num_free_blocks(self) -> int:
        return len(self.free_block_ids)

    @staticmethod
    def _compute_hash(parent_hash: str, token_Tuple: Tuple[int, ...]) -> str:
        payload = f"{parent_hash}:{','.join(map(str, token_Tuple))}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]

    def _alloc_new_block(self) -> PhysicalBlock:
        if not self.free_block_ids:
            raise MemoryError("No available memory for the cache blocks")
        bid = self.free_block_ids.pop(0)
        blk = self.blocks[bid]
        blk.ref_count = 1
        blk.tokens = []
        blk.block_hash = None
        return blk

    def allocate_sequence(self, seq_id: int, tokens: List[int]) -> List[int]:
        """Allocates physical blocks for a prompt sequence, reusing full prefix blocks when APC is enabled."""
        table: List[int] = []
        parent_hash = "ROOT"
        prefix_matched = True

        for start in range(0, len(tokens), self.block_size):
            chunk = tokens[start : start + self.block_size]
            is_full = len(chunk) == self.block_size
            if is_full:
                self.cache_queries += 1
                h = self._compute_hash(parent_hash, tuple(chunk))
                parent_hash = h
                if self.enable_prefix_caching and prefix_matched and h in self.hash_to_block_id:
                    bid = self.hash_to_block_id[h]
                    blk = self.blocks[bid]
                    if blk.ref_count == 0 and bid in self.free_block_ids:
                        self.free_block_ids.remove(bid)
                    blk.ref_count += 1
                    self.cache_hits += 1
                    table.append(bid)
                    continue
                prefix_matched = False
                blk = self._alloc_new_block()
                blk.tokens = list(chunk)
                blk.block_hash = h
                if self.enable_prefix_caching:
                    self.hash_to_block_id[h] = blk.block_id
                table.append(blk.block_id)
            else:
                prefix_matched = False
                blk = self._alloc_new_block()
                blk.tokens = list(chunk)
                table.append(blk.block_id)

        self.block_tables[seq_id] = table
        return list(table)

    def fork_sequence(self, parent_seq_id: int, child_seq_id: int) -> List[int]:
        """Forks a child Block Table sharing physical blocks via reference counting (Copy-on-Write)."""
        parent_table = self.block_tables[parent_seq_id]
        child_table = list(parent_table)
        for bid in child_table:
            self.blocks[bid].ref_count += 1
        self.block_tables[child_seq_id] = child_table
        return list(child_table)

    def append_token(self, seq_id: int, token_id: int) -> int:
        """Appends one generated token to a sequence, triggering Copy-on-Write if the tail block is shared."""
        table = self.block_tables[seq_id]
        if not table:
            blk = self._alloc_new_block()
            blk.tokens.append(token_id)
            table.append(blk.block_id)
            return blk.block_id

        last_bid = table[-1]
        last_blk = self.blocks[last_bid]
        if len(last_blk.tokens) == self.block_size:
            new_blk = self._alloc_new_block()
            new_blk.tokens.append(token_id)
            table.append(new_blk.block_id)
            return new_blk.block_id

        # Tail block is incomplete: trigger Copy-on-Write if shared (ref_count > 1)
        if last_blk.ref_count > 1:
            last_blk.ref_count -= 1
            cow_blk = self._alloc_new_block()
            cow_blk.tokens = list(last_blk.tokens)
            cow_blk.tokens.append(token_id)
            table[-1] = cow_blk.block_id
            self.cow_copies += 1
            return cow_blk.block_id

        last_blk.tokens.append(token_id)
        return last_blk.block_id

    def free_sequence(self, seq_id: int) -> None:
        """Decrements reference counts and returns unreferenced blocks to the free pool."""
        table = self.block_tables.pop(seq_id, [])
        for bid in table:
            blk = self.blocks[bid]
            blk.ref_count -= 1
            if blk.ref_count == 0:
                if not self.enable_prefix_caching and blk.block_hash in self.hash_to_block_id:
                    self.hash_to_block_id.pop(blk.block_hash, None)
                if bid not in self.free_block_ids:
                    self.free_block_ids.append(bid)


def compare_rag_vs_cag_prefix_caching(
    system_tokens: int = 500,
    rag_chunks: int = 10,
    rag_chunk_tokens: int = 500,
    cag_context_tokens: int = 100000,
    user_tokens: int = 500,
    regular_cost_per_m: float = 1.25,
    cached_cost_per_m: float = 0.125,
    rag_ttft_sec: float = 5.0,
) -> Dict[str, float]:
    """Models RAG vs Long-Context Cache-Augmented Generation (CAG) prefill tokens, TTFT, and API cost (HLS Ch. 7)."""
    rag_cached = system_tokens
    rag_uncached = (rag_chunks * rag_chunk_tokens) + user_tokens
    cag_cached = system_tokens + cag_context_tokens
    cag_uncached = user_tokens

    rag_cost = (rag_cached * cached_cost_per_m + rag_uncached * regular_cost_per_m) / 1e6
    cag_cost = (cag_cached * cached_cost_per_m + cag_uncached * regular_cost_per_m) / 1e6
    # HLS Ch. 7 notes CAG prefill is ~1/10th of RAG (500 vs 5,500 tokens), shaving 5.0 s TTFT to ~0.5 s
    cag_ttft_sec = rag_ttft_sec / 10.0

    return {
        "rag_cached_tokens": float(rag_cached),
        "rag_uncached_tokens": float(rag_uncached),
        "cag_cached_tokens": float(cag_cached),
        "cag_uncached_tokens": float(cag_uncached),
        "rag_cost_usd": round(rag_cost, 3),
        "cag_cost_usd": round(cag_cost, 3),
        "rag_ttft_sec": rag_ttft_sec,
        "cag_ttft_sec": cag_ttft_sec,
    }


def evaluate_chunked_prefill_and_preemption(
    prompt_tokens: int = 12288,
    active_decode_seqs: int = 45,
    max_num_batched_tokens: int = 2048,
    long_prefill_threshold: int = 512,
    num_layers: int = 80,
    hidden_size: int = 8192,
    num_kv_heads: int = 8,
    head_dim: int = 128,
    precision_bytes: float = 2.0,
    pcie_bw_gbps: float = 64.0,
    gpu_tflops: float = 989.0,
    seq_len_for_preemption: int = 4096,
) -> Dict[str, float | str | bool]:
    """Models Chunked Prefill token budgeting and Preemption Swap vs Recompute decision math (V12 Ch. 7 & HLS Ch. 8)."""
    avail_prefill_budget = max(0, max_num_batched_tokens - active_decode_seqs)
    chunk_size = min(long_prefill_threshold, avail_prefill_budget)
    num_prefill_chunks = math.ceil(prompt_tokens / chunk_size)
    scheduled_tokens_step = active_decode_seqs + chunk_size

    # Swap vs recompute for one sequence. The KV bytes of a GQA model use the KV head count, not the
    # hidden size: 2 (K and V) * layers * tokens * kv_heads * head_dim * bytes. The MHA figure (hidden_size
    # in place of kv_heads * head_dim) is kept only as the worst case. Round trip = out to host and back.
    kv_bytes = 2.0 * num_layers * seq_len_for_preemption * num_kv_heads * head_dim * precision_bytes
    kv_bytes_mha = 2.0 * num_layers * seq_len_for_preemption * hidden_size * precision_bytes
    t_swap_sec = (2.0 * kv_bytes) / (pcie_bw_gbps * 1e9)
    t_swap_mha_sec = (2.0 * kv_bytes_mha) / (pcie_bw_gbps * 1e9)
    prefill_flops = (
        2.0 * num_layers * (seq_len_for_preemption ** 2) * hidden_size
        + 12.0 * num_layers * seq_len_for_preemption * (hidden_size ** 2)
    )
    t_recompute_sec = prefill_flops / (gpu_tflops * 1e12)

    # Also compute 4 GB one-way PCIe transfer time from V12 Ch. 7 (4 GB / 64 GB/s = 62.5 ms)
    four_gb_one_way_ms = (4.0 / pcie_bw_gbps) * 1000.0

    return {
        "chunk_size": float(chunk_size),
        "num_prefill_chunks": float(num_prefill_chunks),
        "scheduled_tokens_step": float(scheduled_tokens_step),
        "within_token_budget": scheduled_tokens_step <= max_num_batched_tokens,
        "kv_size_gb": round(kv_bytes / 1e9, 4),
        "kv_size_mha_gb": round(kv_bytes_mha / 1e9, 4),
        "t_swap_ms": round(t_swap_sec * 1000.0, 2),
        "t_swap_mha_ms": round(t_swap_mha_sec * 1000.0, 2),
        "t_recompute_ms": round(t_recompute_sec * 1000.0, 2),
        "recompute_faster_than_swap": t_recompute_sec < t_swap_sec,
        "recommended_policy": "recompute" if t_recompute_sec < t_swap_sec else "swap",
        "four_gb_one_way_swap_ms": round(four_gb_one_way_ms, 1),
    }


def plan_vllm_capacity_and_parallelism(
    tp_size: int = 4,
    pp_size: int = 1,
    dp_size: int = 1,
    gpu_vram_gb: float = 80.0,
    gpu_memory_utilization: float = 0.90,
    model_params_b: float = 70.0,
    precision_bytes: float = 2.0,
    workspace_total_gb: Optional[float] = None,
    kv_kib_per_token: float = 320.0,
    enable_expert_parallel: bool = False,
    total_routed_experts: int = 256,
) -> Dict[str, object]:
    """Computes vLLM VRAM allocation, C_max concurrency across sequence lengths, and TP/PP/DP/EP topology."""
    total_gpus = tp_size * pp_size * dp_size
    total_vram_gb = (tp_size * pp_size) * gpu_vram_gb
    weight_memory_gb = model_params_b * precision_bytes
    if workspace_total_gb is None:
        # V12 Ch. 8 reserves 8.0 GB workspace on 4x 80 GB (TP=4 -> 140 GB KV pool) and 8.0 GB per 4-GPU half-node on 8x 80 GB (TP=8 -> 16.0 GB -> 576 - 140 - 8 = 428 GB KV pool)
        total_workspace_gb = 8.0
    else:
        total_workspace_gb = workspace_total_gb
    kv_pool_gb = (total_vram_gb * gpu_memory_utilization) - weight_memory_gb - total_workspace_gb

    c_max_by_seq: Dict[int, int] = {}
    for seq_len in (2048, 8192, 32768):
        # V12 Ch. 8 uses 320 KiB / 1,024,000 = 0.0003125 GB/token -> C_max = int(VRAM_kv_pool // (0.0003125 * S))
        # giving 218, 54, 13 (at 140 GB KV pool) and 668, 167, 41 (at 428 GB KV pool)
        seq_kv_gb = (kv_kib_per_token / (1024.0 * 1000.0)) * seq_len
        c_max_by_seq[seq_len] = int(kv_pool_gb / seq_kv_gb)

    ep_active = enable_expert_parallel and (tp_size * dp_size > 1)
    ep_size = (tp_size * dp_size) if ep_active else 1
    experts_per_gpu = (total_routed_experts // ep_size) if ep_active else total_routed_experts
    ep_comm_pattern = "all_to_all" if (ep_active and dp_size > 1) else "all_reduce"

    return {
        "total_gpus": total_gpus,
        "total_vram_gb": round(total_vram_gb, 1),
        "weight_memory_gb": round(weight_memory_gb, 1),
        "kv_pool_gb": round(kv_pool_gb, 1),
        "c_max_2048": c_max_by_seq[2048],
        "c_max_8192": c_max_by_seq[8192],
        "c_max_32768": c_max_by_seq[32768],
        "allreduces_per_token_80_layers": 2 * 80 if tp_size > 1 else 0,
        "ep_active": ep_active,
        "ep_size": ep_size,
        "experts_per_gpu": experts_per_gpu,
        "ep_comm_pattern": ep_comm_pattern,
    }


def evaluate_multi_lora_and_lab03(
    base_params_b: float = 8.0,
    num_layers: int = 32,
    d_model: int = 4096,
    lora_rank: int = 16,
    num_adapted_modules_per_layer: int = 4,
    max_loras_in_hbm: int = 8,
    precision_bytes: float = 2.0,
) -> Dict[str, float]:
    """Models Multi-LoRA memory overhead (Punica/S-LoRA) and Lab 03 Qwen2.5-Coder-1.5B telemetry."""
    base_weights_gb = base_params_b * precision_bytes
    # Each adapted projection has A (d_model x r) and B (r x d_model) -> 2 * d_model * r parameters
    params_per_lora = num_layers * num_adapted_modules_per_layer * (2 * d_model * lora_rank)
    mb_per_lora = (params_per_lora * precision_bytes) / (1024.0 ** 2)
    lora_pct_of_base = (params_per_lora / (base_params_b * 1e9)) * 100.0
    total_hbm_with_loras_gb = base_weights_gb + (max_loras_in_hbm * params_per_lora * precision_bytes) / 1e9

    # Lab 03 telemetry: 14,258 GPU blocks (block_size=16) for max_model_len=4096 -> 14258 * 16 / 4096 = 55.6953125 (logged as 55.69x)
    lab03_gpu_blocks_normal = 14258
    lab03_cpu_blocks = 2048
    lab03_max_concurrency_4k = math.floor(((lab03_gpu_blocks_normal * 16) / 4096.0) * 100.0) / 100.0
    lab03_gpu_blocks_constrained = 120
    lab03_constrained_max_tokens = lab03_gpu_blocks_constrained * 16

    ttfts = [42.15, 45.80, 43.10, 48.20, 44.90]
    itls = [12.40, 12.85, 12.55, 13.10, 12.70]
    mean_ttft = sum(ttfts) / len(ttfts)
    mean_itl = sum(itls) / len(itls)

    return {
        "base_weights_gb": round(base_weights_gb, 2),
        "params_per_lora": float(params_per_lora),
        "mb_per_lora": round(mb_per_lora, 2),
        "lora_pct_of_base": round(lora_pct_of_base, 4),
        "total_hbm_with_loras_gb": round(total_hbm_with_loras_gb, 4),
        "gpus_saved_vs_dedicated": float(max_loras_in_hbm - 1),
        "lab03_gpu_blocks_normal": float(lab03_gpu_blocks_normal),
        "lab03_cpu_blocks": float(lab03_cpu_blocks),
        "lab03_max_concurrency_4k": round(lab03_max_concurrency_4k, 2),
        "lab03_constrained_max_tokens": float(lab03_constrained_max_tokens),
        "lab03_mean_ttft_ms": round(mean_ttft, 2),
        "lab03_mean_itl_ms": round(mean_itl, 2),
    }


if __name__ == "__main__":
    kv = compute_kv_cache_metrics(seq_len=500, block_size=16, max_model_len=4096)
    print("Llama-3-70B KV Cache & PagedAttention (S=500, B=16):", kv)
    pad = compute_padding_flops_waste([4, 7, 3])
    print("Padding FLOPs Waste ([4, 7, 3]):", pad)
    cp = evaluate_chunked_prefill_and_preemption()
    print("Chunked Prefill & Preemption:", cp)
    cap4 = plan_vllm_capacity_and_parallelism(tp_size=4)
    cap8 = plan_vllm_capacity_and_parallelism(tp_size=8)
    print("Llama-3-70B TP=4 Concurrency:", cap4)
    print("Llama-3-70B TP=8 Concurrency:", cap8)
    lora = evaluate_multi_lora_and_lab03()
    print("Multi-LoRA & Lab 03 Telemetry:", lora)
