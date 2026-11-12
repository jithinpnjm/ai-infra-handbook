# Rework ledger W3 (9.1, 9.2, 9.6, 9.7, 9.8, 9.9, 9.10, 9.12, 9.14)

Status: all nine chapters done. Gates: chain_gate 0.0 to 0.3, 20 summaries each, no In-one-minute boxes, no Concepts H2, language_audit has no row for my files (only 9.11, not mine), check_code_files 0 problems, dgx_families_lab 38/38.

## 9.1
- Removed the info box, all "In one minute" boxes, "workload physics" wording, "golden reference"; shortened sentences; failure table turned into five prose subsections; generation table cells shortened.
- KV-cache formula: old example (8 bytes x 128 heads x 8,192 tokens) was wrong. Now 2 x layers x KV heads x head size x bytes: Llama-3-70B 327,680 B/token, 1.34 GB at 4,096 tokens (matches Part 15.1). code/part09/dgx_families.py and lab updated (new signature num_kv_heads, head_dim); lab 38/38 pass; check_code_files 0 problems. Exercise 1 rewritten (13B, 24 users).
- DGX H100/H200 weight 370 lbs/168 kg: fixed to nearly 300 lbs/130 kg (corpus: hardware notes ch. 4); code catalog weight 287.6.
- Rack depth: old "1,000 mm too shallow, need 1,200" replaced with B200 data-center deck FAQ (min 600x1100 mm, 48U; recommended 700x1200 mm, 52U). "4-node rack exceeds 2,000 lbs" removed (4 x 287.6 lb does not support it).
- Verified against B200 DC deck: 14.3 kW, 458 kW/32-node SU, 127 nodes, 28.6/57.2 kW, 4,290/8,580 CFM, 5-of-6 PSU, circuits: already correct. GB300 RA: 8x33 kW shelves, 6x5.5 kW PSUs, 4x CX-8 + 1 BF3, 4x3.84 E1.S + 1.92 M.2, 1.2 MW per SU: already correct.
- "B200 SXM6" and "4 NVSwitches" in DGX B200 row: not in corpus; removed (UNRESOLVED: my recollection is 2 NVSwitch chips, not sourced).
- Unresolved: "40% PCIe TP wait", "30-50% NUMA loss" (softened, unsourced); DGX GB200 NIC row (72x 400/800G) unsourced.
- Neighbours: code/part09/power_thermal_cooling_lab.py line 158 still uses 8 x 370 lb (9.11, not mine); 10.7 repeats the 8,192-token 1.34 GB KV error.

## 9.2
- Removed scope box, Concepts H2, tips, aircraft/elevator analogies, "senior engineers" tone, "my inference" first person; "sub-links" now "links" in prose (lab output text keeps old wording); symbol table and spec table cells shortened; firmware table "What they control" column moved to prose.
- Verified arithmetic: 46 = 16 + 30; 7 ERoT; 144 links; 7.2/3.6 TB/s; 1.76x / 1.43x; MFU 43.48%. Weight 370 lbs fixed to nearly 300 lbs.
- Unresolved: even NVMe split two per PCIe switch (labelled as chapter reading); 2x-3x host RAM guideline unsourced.

Common to all nine: removed every 'In one minute' box, the empty Concepts H2, the 'Corpus scope note' boxes, 'physical twin' and 'physics' wording, and body mentions of Volume/V21/Module paths (kept in Sources). 'How it fails' tables turned into Symptom/Cause/Fix prose; explanation-bearing table cells shortened or moved to prose. Each section got an opening situation and a closing decision sentence where one was missing.

## 9.6
- Checked against B200 DC deck and GB300 RA: SU table (31/63/95/127 nodes, leaves, spines, cables), GB300 576 GPUs/1.2 MW/144 trays, IB leaf and spine counts (8/16/8, 32/18, 64/36, 128/72), Ethernet leaf/spine/storage counts, 90/45 and 280/140 GB/s tiers, 5 of 6 PSU: already correct. Arithmetic (checkpoint 980 GB, ring 24 ms, TCO $7.19M, 99.5% = 3.6 h) correct.
- Fixed: Eos/Selene names removed (not in RA). Source's InfiniBand cost scenario says '$15K per node' but multiplies $7K by 64 GPUs (64 GPUs = 8 nodes): stated as the source does, flagged in Sources. 'Up to 64 SUs' now attributed as NVIDIA guidance. Partial-SU/no-patch-panel rules now include the cable reach numbers from the deck.
## 9.7
- All ten power-table rows, cable limits, ASHRAE A1, ISO Class 8 particle limits, 2,145 CFM, 4,290/8,580 CFM, 96/101 dB: already correct vs deck. Deck lists a 42U rack in the power table but 48U minimum cabinet in the FAQ: both now stated. 'Blackwell SXM6': not in the deck, not used. Stranded-capacity reason (why 2 not 3 nodes at 100% rating) is still the chapter's own reading, labelled.
## 9.8
- Fixed: 'the RA does not state a deployment time' was wrong (RA says months to weeks). Removed dcgmi/nvsm as Mission Control checks (not in RA). 1-SU spine row (4) is the chapter's own, labelled. 'Physical twin' explained. Power shelf 264 kW now called installed capacity. Rail hop sentence: RA is ambiguous (same-rail one hop vs racks cross spine), repeated as stated. UNRESOLVED: nothing else.
## 9.9
- Clos counts (256 GPUs/8 leaves/4 spines, 2,048, 4.5x, 14,336) re-derived and correct. UNRESOLVED: DCQCN ECN codes and rail-only/rail-unified descriptions rest on the network design book only.
## 9.10
- Arithmetic all checked (see chapter Sources). Six-stage table turned into six subsections. 'Aviation' analogy removed. UNRESOLVED: prices, 2 to 16 node envelope, MPS 48 clients and MIG 7 instances not rechecked against current NVIDIA docs; BasePOD vendor RAs not in corpus.
## 9.12
- CUDA minimum-driver table (450/525/580) matches NVIDIA's compatibility rule; ZeRO per-GPU numbers re-derived and correct; gang-scheduling description correct. 'Volume 21 Chapter N Part N' references deleted. PYTORCH_CUDA_ALLOC_CONF: added that newer PyTorch accepts PYTORCH_ALLOC_CONF (check release notes; unresolved for exact version).
## 9.14
- BCM Topograph port 49021, defaults, topograph4 steps, AWS/OCI prerequisites re-verified in the BCM 11 manual. 'Serverless SuperPODs' heading removed. SXM6 removed. UNRESOLVED: A3 split (a3-highgpu-8g TCPX, a3-megagpu-8g TCPXO) from memory of Google docs, not re-fetched; Nebius/CoreWeave attribute names not re-fetched.

## Neighbouring chapters noticed, not changed
- 9.11 code/part09/power_thermal_cooling_lab.py line 158 still assumes 370 lb per DGX H100 node.
- 10.7 (docs/part-10-gpu-cuda/07-*) repeats the 8,192-token / 1.34 GB KV-cache error and code/part10/gpu_generations.py uses the same formula.
- 9.1 lab output lines and 9.10/9.12 lab expected-output lines still carry 'V4 Ch1', 'V21 Ch13' labels because they mirror code output; code labels were not edited except dgx_families.
