#!/usr/bin/env python3
"""Chapter 15.4 model: SGLang and Cross-Request Optimisation.

Models:
1. RadixAttention Prefix Tree (`RadixCache`) & Two-Level Memory Pool:
   - Compressed prefix tree (trie) storing arbitrary-length token sequences (`DAI` Ch. 7, `V12` Ch. 6 & 8).
   - Two-level memory pool (`SGLang v0.5`):
     * Level 1: Request-to-token KV index mapping table.
     * Level 2: Physical KV cache tensor pool shaped `[num_layers, max_tokens, num_heads, head_dim]`.
   - Arbitrary subsequence matching (`seq1=[1,2,3,4,5]`, `seq2=[1,2,3,6,7]`, `seq3=[1,2,8,9]`,
     query `[1,2,3,4,10,11]` -> `match_len=4`) vs vLLM block-hash Automatic Prefix Caching (`APC`)
     constrained to fixed block boundaries (`B=16` or `B=32`, `< 4%` fragmentation vs `60-80%`
     contiguous waste, `< 3.2%` internal fragmentation at `500` tokens with `B=16`).
   - Leaf-first Least Recently Used (`LRU`) eviction protecting active parent prefix nodes (`ref_count > 0`)
     while evicting unreferenced leaf conversation branches (`ref_count == 0`).
2. Cross-Request Prefix Reuse, Cache-Aware Scheduling & Multi-Tenant Isolation:
   - System prompt sharing math (`500`-token system prompt across `100` concurrent users = `500` tokens
     computed once vs `50,000` tokens without sharing, `99.0%` system-prompt compute savings, up to `90%`
     total prefill reduction, `2-3x` follow-up latency speedup, `50-90%` TTFT reduction).
   - Workload prefix sharing sweep (`prefix_len in [0, 100, 500, 1000]`, `100` requests, `unique_len=50`).
   - Longest-shared-prefix batch sorting and RAG document chunk canonical ordering (`Document 1..4`).
   - Multi-tenant timing side-channel isolation via `<id> {tenant_id}` injection between `<system>` and
     `<context>` (`HLS` Ch. 6), plus chunked prefill vs prefix caching interaction (`45%` hit ratio
     dropping `5.6x` to `8%` without chunk-boundary-aware radix matching; `32%` hit ratio reducing TTFT
     from `420 ms` to `280 ms` = `140 ms` / `33.3%` speedup, `V12` Ch. 8).
   - Cache thrashing diagnosis under `0%` prefix overlap (`400%` P90 TTFT degradation at
     `mem_fraction_static=0.85`, remediated with `--mem-fraction-static 0.92` or `--disable-radix-cache`
     to stabilize TTFT at `22 ms`, `V12` Ch. 6).
3. Structured Output Decoding (`XGrammar`, `Outlines`, Compressed FSM & Jump-Forward Decoding):
   - Vocabulary mask overhead across `128,000` (`128K`, or `128,256` Llama-3) tokens on CPU vs
     precompiled compressed finite-state machine (`FSM`) GPU bitmasking and pushdown automata with
     tree-based stack management for context-sensitive rules (`DAI` Ch. 7, `V12` Ch. 6, `ASP` Ch. 15).
   - Jump-Forward Decoding token splicing for deterministic JSON schema transitions (e.g., `Person`
     schema `{"name": "John Smith", "age": 35, "occupation": "software engineer"}`), converting
     multi-token structural boilerplate from sequential decode forward passes into direct prefix appends.
4. Zero-Overhead CPU Scheduler, Operator Fusion & Parallel Forking (`s.fork`):
   - Serial scheduler (`50%+` CPU scheduling overhead) vs SGLang Zero-Overhead Scheduler overlapping
     Batch `N-1` post-processing, Batch `N` GPU execution, and Batch `N+1` pre-scheduling via
     `Scheduler CPU` + `Launch CPU` and token placeholders for up to `2.0x` throughput (`DAI` Ch. 7).
   - Parallel branching generation (`s.fork(N)`, `sgl.join`, `sgl.select` best-of-`N` for `N=4`).
5. SGLang Model Gateway (Router), PD Disaggregation & Hybrid MoE / DP Attention Scaling:
   - Router policies (`cache_aware` with `--cache-threshold 0.5 --balance-abs-threshold 10
     --balance-rel-threshold 1.5`, `round_robin`, `shortest_queue`, `power_of_two_choices`), `session_id`
     session affinity, and `5`-failure worker circuit breaker (`DAI` Ch. 7).
   - Prefill (`85%` compute / `40%` memory BW) vs Decode (`25%` compute / `90%` memory BW) disaggregation
     via `Mooncake` RDMA (`mlx5_roce0`), `NIXL` UCX, or `ASCEND`, and worker pool ratios (`2:1` or `3:1`
     long-context vs `1:2` chatbot).
   - Data-Parallel Attention (`--enable-dp-attention --dp-size 8 --tp-size 8`) eliminating `8x` KV cache
     duplication when `H_kv=1 < TP=8` for up to `1.9x` decode throughput (`DAI` Ch. 7).
   - Hybrid parallelism (`TP=8, PP=2, DP=4, EP=2 -> 128` GPUs) and Speculative Decoding
     (`--speculative-num-draft-tokens 4`, `70-90%` acceptance, `2-4x` speedup; `EAGLE` `3.5x`,
     `EAGLE-2` `20-40%` faster, `EAGLE-3` `1.4x` over EAGLE-2 and `6.5x` over baseline, `Medusa` `2.2-3.6x`).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class RadixNode:
    """Node in SGLang's RadixAttention compressed prefix tree."""
    tokens: Tuple[int, ...] = ()
    children: Dict[int, "RadixNode"] = field(default_factory=dict)
    parent: Optional["RadixNode"] = None
    ref_count: int = 0
    last_access: int = 0
    kv_indices: List[int] = field(default_factory=list)


class RadixCache:
    """Deterministic simulation of SGLang's RadixAttention prefix tree with LRU leaf eviction."""

    def __init__(self, max_size: int = 1000, num_layers: int = 32, num_heads: int = 32, head_dim: int = 128):
        self.max_size = max_size
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.root = RadixNode()
        self.clock = 0
        self.cached_tokens = 0
        self.total_lookup_tokens = 0
        self.matched_lookup_tokens = 0

    def _touch(self, node: RadixNode) -> None:
        self.clock += 1
        curr: Optional[RadixNode] = node
        while curr is not None and curr is not self.root:
            curr.last_access = self.clock
            curr = curr.parent

    def insert(self, token_ids: List[int], pin_active: bool = False) -> RadixNode:
        """Inserts a token sequence into the radix tree, splitting edges on partial prefix matches."""
        curr = self.root
        idx = 0
        n = len(token_ids)

        while idx < n:
            first_tok = token_ids[idx]
            if first_tok not in curr.children:
                if self.cached_tokens + (n - idx) > self.max_size:
                    self.evict(self.cached_tokens + (n - idx) - self.max_size)
                new_node = RadixNode(
                    tokens=tuple(token_ids[idx:]),
                    parent=curr,
                    kv_indices=list(range(idx, n)),
                )
                curr.children[first_tok] = new_node
                self.cached_tokens += len(new_node.tokens)
                curr = new_node
                break

            child = curr.children[first_tok]
            child_tokens = child.tokens
            match_len = 0
            max_common = min(len(child_tokens), n - idx)
            while match_len < max_common and child_tokens[match_len] == token_ids[idx + match_len]:
                match_len += 1

            if match_len == len(child_tokens):
                curr = child
                idx += match_len
            else:
                # Split existing edge into shared prefix parent + two child branches
                shared_node = RadixNode(
                    tokens=child_tokens[:match_len],
                    parent=curr,
                    ref_count=child.ref_count,
                    last_access=child.last_access,
                    kv_indices=child.kv_indices[:match_len],
                )
                curr.children[first_tok] = shared_node

                child.tokens = child_tokens[match_len:]
                child.kv_indices = child.kv_indices[match_len:]
                child.parent = shared_node
                shared_node.children[child.tokens[0]] = child

                curr = shared_node
                idx += match_len

        if pin_active:
            p: Optional[RadixNode] = curr
            while p is not None and p is not self.root:
                p.ref_count += 1
                p = p.parent
        self._touch(curr)
        return curr

    def lookup(self, token_ids: List[int]) -> Tuple[int, List[int]]:
        """Finds the longest matching prefix in the radix tree and returns (match_length, kv_indices)."""
        curr = self.root
        idx = 0
        n = len(token_ids)
        matched_indices: List[int] = []
        last_matched_node = self.root

        while idx < n:
            first_tok = token_ids[idx]
            if first_tok not in curr.children:
                break
            child = curr.children[first_tok]
            child_tokens = child.tokens
            match_len = 0
            max_common = min(len(child_tokens), n - idx)
            while match_len < max_common and child_tokens[match_len] == token_ids[idx + match_len]:
                match_len += 1

            matched_indices.extend(child.kv_indices[:match_len])
            idx += match_len
            last_matched_node = child
            if match_len < len(child_tokens):
                break
            curr = child

        if last_matched_node is not self.root:
            self._touch(last_matched_node)
        self.total_lookup_tokens += n
        self.matched_lookup_tokens += idx
        return idx, matched_indices

    def _collect_evictable_leaves(self, node: RadixNode, leaves: List[RadixNode]) -> None:
        for child in node.children.values():
            if len(child.children) == 0:
                if child.ref_count == 0:
                    leaves.append(child)
            else:
                self._collect_evictable_leaves(child, leaves)

    def evict(self, num_tokens_needed: int) -> int:
        """Evicts Least Recently Used (LRU) unreferenced leaf nodes recursively."""
        evicted_tokens = 0
        while evicted_tokens < num_tokens_needed:
            leaves: List[RadixNode] = []
            self._collect_evictable_leaves(self.root, leaves)
            if not leaves:
                break
            victim = min(leaves, key=lambda nd: nd.last_access)
            parent = victim.parent
            if parent is not None:
                del parent.children[victim.tokens[0]]
            evicted_tokens += len(victim.tokens)
            self.cached_tokens -= len(victim.tokens)
        return evicted_tokens

    def get_cache_stats(self) -> Dict[str, float | int | Tuple[int, int, int, int]]:
        hit_rate = (
            self.matched_lookup_tokens / self.total_lookup_tokens
            if self.total_lookup_tokens > 0
            else 0.0
        )
        return {
            "cached_tokens": self.cached_tokens,
            "max_size": self.max_size,
            "hit_rate": round(hit_rate, 4),
            "level2_pool_shape": (self.num_layers, self.max_size, self.num_heads, self.head_dim),
        }


def compare_radix_vs_block_hash_apc(
    shared_prefix_tokens: int,
    unique_suffix_tokens: int,
    num_requests: int = 100,
    block_size: int = 16,
) -> Dict[str, float | int]:
    """Compares SGLang RadixAttention token-exact prefix reuse against vLLM block-hash APC.

    - RadixAttention matches all `shared_prefix_tokens` after the first request.
    - Block-hash APC only matches complete blocks of size `block_size` (`(shared_prefix_tokens // block_size) * block_size`),
      missing sub-block trailing tokens.
    """
    # Total tokens at prefix_len=1000, unique_len=50 across 100 requests = 100 * 1050 = 105,000 (105000) tokens
    total_tokens_per_req = shared_prefix_tokens + unique_suffix_tokens
    total_tokens_all = num_requests * total_tokens_per_req

    # Without prefix caching: every request computes full prompt
    unoptimized_prefill_tokens = total_tokens_all

    # SGLang RadixAttention: request 0 computes full prompt; requests 1..N-1 reuse exact shared_prefix_tokens
    radix_cached_per_followup = shared_prefix_tokens
    radix_computed_tokens = total_tokens_per_req + (num_requests - 1) * unique_suffix_tokens
    radix_saved_tokens = unoptimized_prefill_tokens - radix_computed_tokens
    radix_prefill_savings_pct = (radix_saved_tokens / unoptimized_prefill_tokens) * 100.0 if unoptimized_prefill_tokens else 0.0
    radix_hit_rate = ( (num_requests - 1) * shared_prefix_tokens ) / total_tokens_all if total_tokens_all else 0.0

    # vLLM Block-Hash APC: matches only full multiples of `block_size`
    apc_matched_per_followup = (shared_prefix_tokens // block_size) * block_size
    apc_missed_subblock_tokens = shared_prefix_tokens - apc_matched_per_followup
    apc_computed_tokens = total_tokens_per_req + (num_requests - 1) * (unique_suffix_tokens + apc_missed_subblock_tokens)
    apc_hit_rate = ((num_requests - 1) * apc_matched_per_followup) / total_tokens_all if total_tokens_all else 0.0

    # Internal fragmentation bound for PagedAttention at S_actual = shared_prefix_tokens + unique_suffix_tokens
    paged_internal_frag_bound_pct = (block_size / total_tokens_per_req) * 100.0

    return {
        "total_tokens_all": total_tokens_all,
        "unoptimized_prefill_tokens": unoptimized_prefill_tokens,
        "radix_computed_tokens": radix_computed_tokens,
        "radix_saved_tokens": radix_saved_tokens,
        "radix_prefill_savings_pct": round(radix_prefill_savings_pct, 2),
        "radix_hit_rate": round(radix_hit_rate, 4),
        "apc_matched_per_followup": apc_matched_per_followup,
        "apc_missed_subblock_tokens": apc_missed_subblock_tokens,
        "apc_computed_tokens": apc_computed_tokens,
        "apc_hit_rate": round(apc_hit_rate, 4),
        "paged_internal_frag_bound_pct": round(paged_internal_frag_bound_pct, 2),
    }


def benchmark_prefix_sharing_sweep(
    prefix_lengths: List[int] = [0, 100, 500, 1000],
    num_requests: int = 100,
    unique_len: int = 50,
    prefill_rate_tok_per_ms: float = 25.0,
) -> List[Dict[str, float | int]]:
    """Models the DAI Ch. 7 Exercise 2 prefix-sharing benchmark across [0, 100, 500, 1000] shared tokens."""
    results: List[Dict[str, float | int]] = []
    for prefix_len in prefix_lengths:
        stats = compare_radix_vs_block_hash_apc(
            shared_prefix_tokens=prefix_len,
            unique_suffix_tokens=unique_len,
            num_requests=num_requests,
            block_size=16,
        )
        cold_ttft_ms = (prefix_len + unique_len) / prefill_rate_tok_per_ms
        warm_ttft_ms = unique_len / prefill_rate_tok_per_ms
        ttft_speedup = cold_ttft_ms / warm_ttft_ms if warm_ttft_ms > 0 else 1.0
        results.append(
            {
                "prefix_len": prefix_len,
                "unique_len": unique_len,
                "num_requests": num_requests,
                "cache_hit_rate": stats["radix_hit_rate"],
                "prefill_savings_pct": stats["radix_prefill_savings_pct"],
                "cold_ttft_ms": round(cold_ttft_ms, 2),
                "warm_ttft_ms": round(warm_ttft_ms, 2),
                "ttft_speedup_x": round(ttft_speedup, 2),
            }
        )
    return results


def evaluate_rag_and_multitenant_prefix_design(
    sys_tokens: int = 256,
    doc_chunk_tokens: List[int] = [256, 256, 256, 256],
    user_query_tokens: int = 32,
) -> Dict[str, int | float | bool]:
    """Evaluates RAG document ordering, multi-tenant `<id>` isolation, and chunked prefill hit-rate impact."""
    total_doc_tokens = sum(doc_chunk_tokens)
    total_prompt_tokens = sys_tokens + total_doc_tokens + user_query_tokens  # 256 + 1024 + 32 = 1312

    # Canonical sorted order [1, 2, 5, 7] vs reordered [5, 7, 1, 2] when first 2 chunks match cached [1, 2, 3, 4]
    sorted_prefix_match_tokens = sys_tokens + sum(doc_chunk_tokens[:2])  # 256 + 512 = 768
    reordered_prefix_match_tokens = sys_tokens  # 256 (misses all doc chunks because chunk 5 is first)

    # Multi-tenant isolation via `<id> {tenant_id}` placed between `<system>` and `<context>`
    tenant_isolated_shared_tokens = sys_tokens  # Only system prompt is shared across distinct tenants
    cross_tenant_context_leak_possible = False

    # Chunked prefill interaction from V12 Ch. 8:
    # Naive sequence-boundary prefix matching drops hit rate from 45% to 8% (5.625x -> 5.6x drop)
    hit_rate_before_chunking = 0.45
    hit_rate_after_naive_chunking = 0.08
    chunking_drop_factor = round(hit_rate_before_chunking / hit_rate_after_naive_chunking, 1)

    # Effective TTFT speedup from V12 Ch. 8: 32% hit rate, 420 ms without hit vs 280 ms with hit (140 ms / 33% saved)
    ttft_without_hit_ms = 420.0
    ttft_with_hit_ms = 280.0
    ttft_saved_ms = ttft_without_hit_ms - ttft_with_hit_ms
    ttft_hit_speedup_pct = round((ttft_saved_ms / ttft_without_hit_ms) * 100.0, 1)

    return {
        "total_prompt_tokens": total_prompt_tokens,
        "sorted_prefix_match_tokens": sorted_prefix_match_tokens,
        "reordered_prefix_match_tokens": reordered_prefix_match_tokens,
        "tenant_isolated_shared_tokens": tenant_isolated_shared_tokens,
        "cross_tenant_context_leak_possible": cross_tenant_context_leak_possible,
        "hit_rate_before_chunking": hit_rate_before_chunking,
        "hit_rate_after_naive_chunking": hit_rate_after_naive_chunking,
        "chunking_drop_factor": chunking_drop_factor,
        "ttft_without_hit_ms": ttft_without_hit_ms,
        "ttft_with_hit_ms": ttft_with_hit_ms,
        "ttft_saved_ms": ttft_saved_ms,
        "ttft_hit_speedup_pct": ttft_hit_speedup_pct,
    }


def simulate_xgrammar_jump_forward_decoding(
    vocab_size: int = 128256,
    decode_step_ms: float = 12.0,
    naive_cpu_mask_ms_per_step: float = 18.0,
    xgrammar_gpu_mask_ms_per_step: float = 0.15,
) -> Dict[str, int | float | str]:
    """Models XGrammar / Outlines compressed FSM structured decoding and SGLang Jump-Forward Decoding.

    Schema (`DAI` Ch. 7 Exercise 3 `Person`):
      `{"name": "John Smith", "age": 35, "occupation": "software engineer"}`
    Deterministic structural segments (singular-transition FSM edges jumped without decode forward passes):
      1. `{"name": "`           (5 tokens)
      2. `", "age": `           (5 tokens)
      3. `, "occupation": "`    (6 tokens)
      4. `"}`                   (2 tokens)
      Total deterministic structural tokens = 18 tokens (4 jump-forward splices).
    Variable value tokens requiring LLM sampling:
      - `John Smith"`           (2 tokens)
      - `35`                    (1 token)
      - `software engineer`     (2 tokens)
      Total sampled value tokens = 5 tokens.
    """
    deterministic_segments = ['{"name": "', '", "age": ', ', "occupation": "', '"}']
    deterministic_token_counts = [5, 5, 6, 2]
    value_token_counts = [2, 1, 2]

    jumped_tokens = sum(deterministic_token_counts)  # 18
    sampled_tokens = sum(value_token_counts)         # 5
    total_output_tokens = jumped_tokens + sampled_tokens  # 23

    # 1. Naive per-token CPU grammar validation across 128K vocab (23 steps)
    naive_total_ms = total_output_tokens * (decode_step_ms + naive_cpu_mask_ms_per_step)

    # 2. Precompiled FSM bitmask without jump-forward (23 steps on GPU)
    fsm_only_total_ms = total_output_tokens * (decode_step_ms + xgrammar_gpu_mask_ms_per_step)

    # 3. XGrammar + SGLang Jump-Forward Decoding (5 sampled steps + 4 fast prefix splices at 1.2 ms each)
    jump_splice_overhead_ms = len(deterministic_segments) * 1.2
    jump_forward_total_ms = sampled_tokens * (decode_step_ms + xgrammar_gpu_mask_ms_per_step) + jump_splice_overhead_ms

    decode_steps_saved_pct = (jumped_tokens / total_output_tokens) * 100.0
    speedup_vs_naive_x = naive_total_ms / jump_forward_total_ms
    speedup_vs_fsm_only_x = fsm_only_total_ms / jump_forward_total_ms
    xgrammar_mask_overhead_pct = (xgrammar_gpu_mask_ms_per_step / decode_step_ms) * 100.0

    return {
        "vocab_size": vocab_size,
        "total_output_tokens": total_output_tokens,
        "jumped_tokens": jumped_tokens,
        "sampled_tokens": sampled_tokens,
        "decode_steps_saved_pct": round(decode_steps_saved_pct, 2),
        "naive_total_ms": round(naive_total_ms, 2),
        "fsm_only_total_ms": round(fsm_only_total_ms, 2),
        "jump_forward_total_ms": round(jump_forward_total_ms, 2),
        "speedup_vs_naive_x": round(speedup_vs_naive_x, 2),
        "speedup_vs_fsm_only_x": round(speedup_vs_fsm_only_x, 2),
        "xgrammar_mask_overhead_pct": round(xgrammar_mask_overhead_pct, 2),
    }


def simulate_zero_overhead_scheduler_and_fork(
    num_batches: int = 10,
    gpu_compute_ms: float = 20.0,
    cpu_preschedule_ms: float = 12.0,
    cpu_postprocess_ms: float = 8.0,
    fork_branches: int = 4,
    shared_prompt_tokens: int = 500,
    branch_gen_tokens: int = 200,
) -> Dict[str, float | int]:
    """Models SGLang's Zero-Overhead Scheduler (`Batch N-1 / N / N+1` overlap) and `s.fork(4)` parallel generation."""
    cpu_total_ms = cpu_preschedule_ms + cpu_postprocess_ms  # 20.0 ms (50% of 40.0 ms serial step)
    serial_step_ms = gpu_compute_ms + cpu_total_ms          # 40.0 ms
    serial_cpu_overhead_pct = (cpu_total_ms / serial_step_ms) * 100.0  # 50.0%

    # Zero-overhead scheduler overlaps CPU pre-scheduling (N+1) and post-processing (N-1) with GPU (N)
    overlapped_step_ms = max(gpu_compute_ms, cpu_preschedule_ms, cpu_postprocess_ms)  # 20.0 ms
    serial_total_ms = num_batches * serial_step_ms
    overlapped_total_ms = cpu_preschedule_ms + num_batches * overlapped_step_ms + cpu_postprocess_ms
    steady_state_speedup_x = serial_step_ms / overlapped_step_ms  # 2.0x

    # Parallel generation with `s.fork(4)` vs sequential 4x generation
    sequential_kv_tokens = fork_branches * (shared_prompt_tokens + branch_gen_tokens)  # 4 * 700 = 2800
    fork_shared_kv_tokens = shared_prompt_tokens + fork_branches * branch_gen_tokens   # 500 + 800 = 1300
    fork_kv_memory_savings_pct = ((sequential_kv_tokens - fork_shared_kv_tokens) / sequential_kv_tokens) * 100.0

    return {
        "serial_step_ms": serial_step_ms,
        "overlapped_step_ms": overlapped_step_ms,
        "serial_cpu_overhead_pct": round(serial_cpu_overhead_pct, 1),
        "steady_state_speedup_x": round(steady_state_speedup_x, 2),
        "serial_total_ms": round(serial_total_ms, 1),
        "overlapped_total_ms": round(overlapped_total_ms, 1),
        "sequential_kv_tokens": sequential_kv_tokens,
        "fork_shared_kv_tokens": fork_shared_kv_tokens,
        "fork_kv_memory_savings_pct": round(fork_kv_memory_savings_pct, 2),
    }


def evaluate_router_and_distributed_sglang(
    worker_match_ratios: List[float] = [0.15, 0.72, 0.40, 0.10],
    worker_queue_loads: List[int] = [6, 8, 5, 12],
    cache_threshold: float = 0.5,
    balance_abs_threshold: int = 10,
    balance_rel_threshold: float = 1.5,
    consecutive_failures: int = 5,
    tp_size: int = 8,
    pp_size: int = 2,
    dp_size: int = 4,
    ep_size: int = 2,
    num_kv_heads: int = 1,
) -> Dict[str, int | float | str | bool]:
    """Evaluates SGLang Model Gateway cache-aware routing, circuit breakers, PD disaggregation, and DP Attention."""
    best_cache_worker = max(range(len(worker_match_ratios)), key=lambda i: worker_match_ratios[i])
    best_match = worker_match_ratios[best_cache_worker]

    min_load = min(worker_queue_loads)
    max_load = max(worker_queue_loads)
    load_imbalanced = (max_load - min_load > balance_abs_threshold) and (
        max_load > min_load * balance_rel_threshold
    )

    if best_match >= cache_threshold and not load_imbalanced:
        selected_worker = best_cache_worker
        routing_decision = "cache_hit_route"
    else:
        selected_worker = min(range(len(worker_queue_loads)), key=lambda i: worker_queue_loads[i])
        routing_decision = "load_balance_fallback"

    # Circuit breaker opens at 5 consecutive health-probe/request failures (DAI Ch. 7)
    circuit_breaker_open = consecutive_failures >= 5

    # Prefill vs Decode resource utilization profile (DAI Ch. 7 Fig 7.8)
    prefill_compute_util_pct = 85
    prefill_mem_bw_util_pct = 40
    decode_compute_util_pct = 25
    decode_mem_bw_util_pct = 90

    # 4D hybrid parallelism total GPUs (DAI Ch. 7: TP=8, PP=2, DP=4, EP=2 -> 128 GPUs)
    hybrid_total_gpus = tp_size * pp_size * dp_size * ep_size

    # Data-Parallel Attention (DAI Ch. 7: 1 KV head with TP=8 duplicates KV cache 8x without DP Attention,
    # whereas --enable-dp-attention eliminates duplication and achieves up to 1.9x decode throughput)
    standard_tp_kv_replication_factor = max(1, tp_size // num_kv_heads)
    dp_attention_kv_replication_factor = 1
    dp_attention_throughput_gain_x = 1.9

    return {
        "selected_worker": selected_worker,
        "best_match_ratio": best_match,
        "routing_decision": routing_decision,
        "load_imbalanced": load_imbalanced,
        "circuit_breaker_open": circuit_breaker_open,
        "prefill_compute_util_pct": prefill_compute_util_pct,
        "prefill_mem_bw_util_pct": prefill_mem_bw_util_pct,
        "decode_compute_util_pct": decode_compute_util_pct,
        "decode_mem_bw_util_pct": decode_mem_bw_util_pct,
        "hybrid_total_gpus": hybrid_total_gpus,
        "standard_tp_kv_replication_factor": standard_tp_kv_replication_factor,
        "dp_attention_kv_replication_factor": dp_attention_kv_replication_factor,
        "dp_attention_throughput_gain_x": dp_attention_throughput_gain_x,
    }


if __name__ == "__main__":
    cache = RadixCache(max_size=1000)
    cache.insert([1, 2, 3, 4, 5])
    cache.insert([1, 2, 3, 6, 7])
    cache.insert([1, 2, 8, 9])
    match_len, kv_idx = cache.lookup([1, 2, 3, 4, 10, 11])
    print(f"RadixCache lookup [1,2,3,4,10,11]: match_len={match_len}, stats={cache.get_cache_stats()}")
    print("Prefix sharing sweep:", benchmark_prefix_sharing_sweep())
    print("XGrammar + Jump-Forward:", simulate_xgrammar_jump_forward_decoding())
    print("Zero-overhead scheduler + fork:", simulate_zero_overhead_scheduler_and_fork())
    print("Router + DP Attention:", evaluate_router_and_distributed_sglang())
