# Rework ledger X4: chapters 10.8, 14.11, 13.7, 13.5

## 10.8 (docs/part-10-gpu-cuda/08-...)
Changed: rewritten body; removed section 5.5, "Corrections to the author's notes", the 25-line migration list, "(untested here)" noise, V16/V20 tags in tables, lab output and answers. Added "Utilization you can trust" (SM_ACTIVE, SM_OCCUPANCY, TENSOR_ACTIVE, DRAM_ACTIVE) and an NCCL-hang row (failure 4, checkpoint Q20). Exercise 4 replaced by a throttle-mask decode (0x44); Q14 replaced by a thermal-resistance answer. Code: code/part10/gpu_node_ops.py persistence message, lab labels stripped of source tags (41 checks pass).
Watch list:
- Persistence mode mechanism: fixed. Modules stay loaded; driver deinitialises GPU when no client holds it; nvidia-persistenced preferred over legacy -pm (NVIDIA driver persistence docs, from knowledge, not re-fetched).
- PyTorch 75-95 percent preallocation: fixed. Caching allocator grows on demand; 75 percent default is JAX (JAX docs); not re-fetched.
- Thermal W/degC model: fixed. Replaced by thermal resistance degC/W relative to inlet; no numbers invented.
- GPU_UTIL definition: restated as "a kernel was executing" (NVML definition) instead of per-SM warp residency.
- APPLICATIONS_CLOCKS_SETTING tied to -ac: fixed; whether -lgc sets the bit stated as undocumented (unresolved, softened).
- H100 base clock 1.4 GHz: not stated in the chapter now (already absent).
- Throttle bit values: match nvml.h as known; unverified live.
- dcgm-exporter 4.9.0 note kept unchanged.
Neighbour notes: 10.21 should own the Xid table; 10.8 now defers to it.

## 14.11
Rewrote body. Code rewritten: code/part14/checkpoint_fault_tolerance.py and _lab.py (21 checks pass; was 25).
- NCCL default timeout: fixed to 10 min (matches 12.18 line 232). Heartbeat speedup now 75x.
- Gradients in checkpoint: fixed. 14 B/param (12 minimal); 70B = 980 GB; all worked times recomputed (235.2 s vs 2.45 s, still 96x).
- Xid 63: fixed (row-remap record, tier 1). Xid 48/79/95 drain.
- Sample code: now saves per-rank RNG (torch.cuda.get_rng_state per rank), data loader state, scheduler, atomic tmp dir + barrier + rename. Note on world-size change.
- Swap advice: removed (pinned memory cannot be swapped); lab check removed.
- Extra errors found and fixed: goodput table (88.82 percent was wrong; formula gives 89.13; 4 h 73.77), 0.999^100000 = 3.5e-44 not 3.7e-44, hacked mantissa in code removed.
- Removed lab checks 23, 24 (off-topic), storage-tier table moved to 13.7. Added in-memory/peer checkpoint and torchft pointers (unsourced, flagged as pointers only: unresolved).
- Owns Young-Daly derivation; links 13.7, 19.4, 20.17.

## 13.7
Rewrote body; removed five components, gather-vs-sharded, Young-Daly, 7B/GPT-3 compute wall; owns storage side (sizing, phases/straggler, staged path, host-RAM guard, bandwidth sizing, striping, atomic publish, retention, restore RTO, cuda-checkpoint). Links 14.11 and 19.4. No LaTeX left (FB's math repair superseded; file re-read before save, 5 dollar signs in prose were present, none remain). Code: code/part13/checkpoint_architecture_lab.py trimmed to 18 checks (dropped sizing/gather/YD checks now in 14.11), source tags stripped. Payload accounting now consistent with 14.11 (14 B/param). Swap mitigation removed. Q/exercise counts unchanged (20 summaries, 6 exercises).

## 13.5
Targeted rewrite. Removed gdsio table/commands (13.3 owns); added section 6 comparing BeeGFS, WekaFS, VAST and object storage (metadata rate, small files, failure modes, how to pick). Stripped "(untested here)". Fixed 3FS: README (fetched 2026-11-12) says 180 nodes, 2x200 Gbps NICs, 16x14 TiB SSDs, about 6.6 TiB/s; the chapter's 68 nodes, 100 Gb/s NICs, 1.4 TB/s background, 7.3 peak and Ceph 1.1 TB/s comparison were unsupported (the old per-node 97 GB/s also exceeded the stated 25 GB/s NIC). Code beegfs_weka_vast_object.py and lab corrected; lab now 25 checks pass. MDS "50-100K ops/s" softened to a starting point, measure with mdtest. Unresolved: WekaFS 4 KB chunk and VAST 146+4 stripe are from notes, unmeasured. Metadata table row left as is.

## Noticed in neighbouring chapters
- 13.3 line ~311, 13.2, 13.1 and 6.21 repeat the 68-node / Ceph 3FS claim (13.3 also exercise 6 and Q12): need the same correction.
- 9.6 and 9.x quote 16 B/param checkpoint payload; check.
- language_audit shows no row for any of my four files. chain_gate: 0.0 to 0.5 per 1000 words.
