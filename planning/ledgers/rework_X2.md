# Rework ledger X2 (15.1, 15.3, 15.16)

## 15.3 vLLM in depth
Changed: section 3.3 rewritten (swap vs recompute, GQA round trip, V1 recomputes because swap was removed); failure mode 4 reduced to the TP=16 NCCL case (PP imbalance deleted); sparse TFLOPS labelled (dense 495/989/1,979, sparse 989/1,979/3,958); two api_server examples replaced by `vllm serve`; swap-space guidance dated pre-v0.18 in failure mode 1, metrics table and alert text; checklist lines 13/14, exercise 3(b) and checkpoint 11 corrected; correction note added to Sources.
Code: code/part15/vllm_paged_attention.py now uses GQA KV bytes (kv_heads*head_dim), adds t_swap_mha_ms and kv_size_mha_gb; lab checks 13 and 14 updated; lab 25 passed, check_code_files part15 0 problems.
Watch list:
- recompute 29.01 ms: fixed (289.05 ms by formula and code); also the 65,536 figure 994 ms was wrong (9,961 ms) and the "335 ms GQA swap" was one-way, round trip 671 ms.
- swap faster for GQA: fixed (41.94 ms vs 289 ms, about 6.9x).
- sparse TFLOPS: fixed. Also noted 64 GB/s is Gen5 x16 theoretical.
- PP KV imbalance: deleted.
- swap-space removed in v0.18.0: already correct, verified from tags v0.17.0 (swap_space in vllm/config/cache.py) vs v0.18.0 (absent) and v0.18.0 docs/configuration/optimization.md ("default preemption mode is RECOMPUTE rather than SWAP").
- V0 names: `BlockSpaceManager` still used in the PagedAttention sections (conceptual V0 name), api_server fixed. Unresolved/not done: replacing BlockSpaceManager everywhere, price lists, split of chapter, metric name vllm:gpu_cache_usage_perc (20.18 uses vllm:kv_cache_usage_perc in v0.32.0), 0.90 vs 0.92 default.
## 15.1
Opening replaced by a concrete request story (numbers from the chapter's own worked example); drafter "we" in the opener and two "Volume 12" labels removed. Sentence-length trimming and moving stage tables not done.
## 15.16
Section 5.1 rewritten: gateway load shedding vs per-replica circuit breaker, 429 vs 503, retry budget (aligned to 20.21 sections 7-8), preemption by recompute (20.18 section 3); swap-space guidance dated pre-v0.18 in summary, stage table, failure mode 3, checkpoint 17, takeaways; probes: /health reports crash not stall (20.18 section 6), liveness/readiness separation and ready-vs-desired alert (20.18 section 8).
Not done: chapter text still uses vllm:gpu_cache_usage_perc in alert rules and "Volume 12" mentions elsewhere; lab PASS line 21 mirrors the code's pre-v0.18 case.
## Neighbours
20.18 and 20.22 vs 15.3: metric names and gpu_memory_utilization default still disagree.
