# Ledger FB (Worklist B, Parts 1 to 15)

## Gem-book abbreviations
- confirmed-wrong-and-fixed: about 270 prose uses (backticked, italic and bare) of HLW, SCL, ASP, AISPE, KUR, AUR, TUR, NK, KPG, PK, DAI, K8GS, AIE, GAK, EAS, and NPA (Network Programmability and Automation, 4.4) replaced with full italic titles across Parts 1 to 15 (all files with hits). Redundant "(`X`)" parentheticals after a full title removed. Left alone on purpose: NPA in 12.21 (UALink Network Physical Address), PK in 7.15 (UEFI Platform Key) and 3.6 code, DAI in 2.9 and 2.21 (Dynamic ARP Inspection). Volume labels such as V7 or VL6 not touched (not in the list).
- Note: backticked forms counted as abbreviations too, so the count is much higher than the worklist's 27.

## Part 11
- 11.13: confirmed-wrong-and-fixed. 60/85 percent figures now carry the "author's design notes, not measured" caveat in both tables and checkpoint Q2.
- 11.x Sources "validation pass 2026-10-25/26" lines: fixed in 1, 3 (checked, content is not a process note), 6 to 30 where present: rewritten as plain provenance or removed. The KAI "check 2026-10-25" note in 11.14 to 11.18 kept (real provenance).

## Part 15
- 15.2: confirmed-wrong-and-fixed. H100/H200 1,979/3,958 are with-sparsity; headers labelled, dense figures (989 BF16, 1,979 FP8; ridge about 295 and 206) given in a note, prose lines 346 and 767 corrected. The lab and code still print the table values as written (sparse) and were not changed. B200 and H100 PCIe/NVL rows are also with-sparsity (noted).
- code/part15/dynamo_disaggregated_serving.py docstring: fixed to 288 GB / 218 GB. check_code_files part15 clean. No pytest tests exist for it.
- 15.10 MLA 4.66x: already-correct (327,680 / 70,272 = 4.66; 37.3x vs MHA also right).
- 15.16 Nagle 200 ms: confirmed-wrong-and-fixed, softened to tens of ms (about 40 ms Linux delayed ACK, up to 200 ms on some stacks) in two places.
- 6.30 PSU N+1: already-correct (NVIDIA SuperPOD B200 text says internal N+1 PSU).

## Part 14
- 14.10: confirmed-wrong-and-fixed. Lab computes 94.41 percent (range check only); "~93.9%" changed to "~94.4%" in the lab code label and the doc output.
- 14.1 vs 14.12 MFU: reconciled to 35 to 55 percent published range (PaLM 46.2, Llama 3 38 to 43) with 40 to 50 a good target; source line added to both.
- 14.16 "Ghost Straggler": replaced with "edge-stage straggler" in the chapter. Still appears in code/part14/tp_pp_ep_megatron(_lab).py comments and docstring (14.7), left for code parity.
- 14.5/14.6/14.8: SimpleFSDP 28/69 percent is paper best-case (labelled), AsyncTP 21.25 percent labelled as worked example with assumed 85 percent overlap, SuperOffload 82 percent / 13.5 s labelled book-reported, not measured.
- Pre-existing, not mine: check_code_files code/part14 reports 2 undefined names (checkpoint_fault_tolerance.py line 84, finetuning_infra_cost.py line 433).

## Math markup (12.1, 12.5 to 12.13, 13.7 and other Part 12 files)
- confirmed-wrong-and-fixed: stray backticks and `\{ \}` escapes inside `$...$` and `$$...$$` removed in 18 Part 12/13 files; every math span brace-balanced afterwards. Not rendered (site build not allowed).

## Other
- 12.21 Figure 9-8: already-correct against *AI Data Center Network Design and Technologies*.
- 13.3 VAST 20 and 30 percent: already-correct (in *AI Systems Performance Engineering*). 3FS: book figures match, but 68 nodes with 2x100 Gb/s NICs cannot reach 6.6 TB/s (about 1.7 TB/s ceiling): caveat added; unresolved which node count is real (check DeepSeek 3FS repo).
- 10.1 NVIDIA drop about 17 percent: already-correct. 180 GB B200: reworded to "roughly 180 GB usable, 192 GB physical". 10.4: already-correct (192 physical / 180 usable).
- 10.7: reworded to H100 PCIe 350 W vs SXM5 700 W.
- 10.10: 15 s labelled illustrative from the book example, softened in two places.
- 5.14, 5.30: dense paragraphs turned into tables (Cilium BPF maps; resource.Quantity; GVK/GVR RESTMapper). 5.23: its two densest paragraphs are readable prose, left. Partial: 5.30 lines about Go helper types (277, 323, 757, 926) not redone.

Gates: chain_gate clean on Parts 1 to 15; summary counts unchanged; check_code_files part15 clean.
