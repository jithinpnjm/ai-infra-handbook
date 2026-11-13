# Voice rewrite, Part 9 chapters 9.1 to 9.3 (run a)

Scope: `docs/part-09-nvidia-systems/01-dgx-system-families-and-what-they-are-for.md`, `02-inside-a-dgx-h100-and-h200-system.md`, `03-hgx-platforms-and-oem-integration.md`. Checkpoints, Sources and review notes are untouched (spliced from HEAD). EXTERNAL_EDITS.md not edited, per instruction.

## Word counts (whole file, `wc -w`)

| File | Before | After | Growth |
|---|---|---|---|
| 01 DGX system families | 10313 | 13586 | +31.7% |
| 02 Inside a DGX H100 and H200 | 8072 | 10503 | +30.1% |
| 03 HGX platforms and OEM integration | 9271 | 11780 | +27.1% |

Body only (before the Checkpoint questions): 01 7754 to 11949 (+54%, guard count), 02 5963 to 9045, 03 7124 to 10660.

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three. New numbers: 0 on all three (an early "99 out of 100" wording and a repeated chapter number were removed). Lost numbers: 0. Lost code spans: 0. New code spans: 0 to 1 (plain prose spans added, e.g. `nvidia-smi topo -m`).
- `python3 tools/restore/chain_gate.py <file>`: 01 = 0.2, 02 = 0.1, 03 = 0.2 (target <= 0.2 met).
- Span check (inline backtick spans, HEAD vs worktree): `{}` on all three after restoring two lost spans in 02 and one in 03.
- Checkpoint count: 20 / 20 / 20, unchanged.
- Mermaid check and `npm run build`: not run (task said no npm build). All Mermaid blocks, code blocks, tables and headings are byte-identical to HEAD; the guard's code-block check passes.

## What changed in every chapter

- Front matter, heading text and order, tables, code blocks and Mermaid: unchanged.
- Status row: "untested" replaced with "not run" (honest status kept once in the row and once above the lab, in the Commands section).
- "Prerequisites and outcomes": the "you will be able to" lists replaced with a plain paragraph of what the chapter walks through.
- Bold lead-ins in bullets replaced by question-and-answer bullets (at most one bold idea per section).
- Every top-level section now opens with a situation, not a definition.
- Exercises: same count (01 = 6, 02 = 6, 03 = 6). Multi-part exercises split into short sentences. Lab step counts kept (01 = 5 modules and 1 run command; 02 = 5 checks and 1 run command; 03 = 4 engines and 1 run command). Commands unchanged.
- Gem book titles: full titles only (*AI Systems Performance Engineering*, *Distributed AI Systems*, *Data Center Best Practices with DGX B200*, *NVIDIA DGX SuperPOD Reference Architecture Featuring NVIDIA DGX GB300 Systems*). No abbreviations added.
- Residue removed from body prose: "(untested here)", "my tool", "this chapter's own" (replaced by "made for this chapter" or "a convention this chapter uses"), "the book says", "Volume N" in body text.

## Needs source (general explanations added in prose; facts stay exact, these are definitions or interpretations that a reviewer should check)

01 DGX system families:
- NGC described as NVIDIA's container catalog (expansion of the acronym not given in the source).
- Streaming Multiprocessors and Tensor Cores described as the matrix-math units.
- Prefill described as reading the whole prompt at once; TTFT and ITL definitions.
- RDMA described as a remote machine writing into memory without going through the OS on either side.
- Adam optimizer (two running averages per weight) and backpropagation described in one line each.
- CUDA context overhead described as per-process setup memory.
- LoRA described as training a small set of extra weights.
- P99 described as the value only the slowest few requests exceed.
- Mixture-of-Experts described as routing each token to specialist sub-networks.
- Transformer Engine, FP8/FP4 "trade precision for speed", and TDP as a power and cooling proxy.
- RT cores described as ray-tracing units; OEM expanded as Original Equipment Manufacturer.
- "Passive backplane" described as holding no active chips and drawing no power.
- Coolant Distribution Unit described as moving liquid between cold plates and the facility loop.
- "Power shelves ride through short power dips" for GB300: inferred from "extra energy storage"; needs source.
- BMC kept working when the host OS is down; isolated VLAN explained as protecting the operator.
- Hot-swap, hot and cold aisle containment, three-phase circuit described in one line each.

02 Inside a DGX H100 and H200:
- Bisection bandwidth and "non-blocking crossbar" explained as the fabric's behavior under a cut and under concurrent pairs.
- SHARP-over-NVLink explained as combining data inside the switch (the source names the feature; the mechanism sentence is ours).
- NUMA, UPI described as a cache-coherence link "not built for" GPU traffic (the "not built for" is an interpretation).
- DataLoader worker, memory-mapped shards, `cudaMallocHost` page-locked buffers, DDR5 channel described.
- Kernel launch described as the CPU telling a GPU what to run next; host tray as the "dispatch office" (analogy only).
- PCIe switch described as a small PCIe router chip; DMA described as a device transfer without CPU copying bytes.
- RoCEv2 expanded as RDMA over Converged Ethernet.
- Standby rails described as the low-level supply that stays live while AC is plugged in; the reason the satellite BMC does not cold-boot is our reading of the source.
- Root of trust, VBIOS, `.fwpkg` (signed package), non-volatile memory, PDU outlet relay, RMA, link training, affinity, rank and `LOCAL_RANK` described in one line each.
- MFU: "recomputed work and padding do not count" is an interpretation of the definition; the "six times parameters times tokens" rule is stated in the source, but "six counts the multiply and add operations of the forward and backward passes" is our explanation.
- The statement that a `pending` state means "stored but not running" is our reading of the BCM output.
- Redfish described as a JSON-over-HTTP resource tree; SEL described as the System Event Log.
- AllReduce ring described as GPUs passing data around in a fixed order.

03 HGX platforms and OEM integration:
- Merchant silicon described as a chip or module sold to other companies for their own products.
- ASIC, retimer (cleans a signal so it travels further), point-of-load regulator, root of trust, microcontroller described.
- SLA, control plane, SDN offload, blind-mate, E1.S ruler form factor, "pilot unit" described.
- Field replaceable unit (FRU) described as a part a technician can swap on site.
- Busbar, derating (running below rated maximum), three-phase AC supply described.
- "Frankenstein server" is a term used by the source; "a machine assembled from parts never tested together" is our gloss.
- Xid defined as the NVIDIA driver's numbered error message; PCIe link framing explained as how bits are packed and recognized.
- Rail defined as the set of links that connect the same NIC position on every node.
- NCCL_NET_GDR_LEVEL described as the threshold that decides how close a GPU and NIC must be before direct transfers are used (confirm against NCCL docs).
- Closed-loop liquid cooling explained as a loop with no building water connection.
- Transceiver described as converting electrical signals to light and back.
- "Ask for the topology output as evidence" and the "shared checklist" and "escalation order protects the relationship" paragraphs are advice, not facts.

## Unresolved

1. Sources rows in 02 and 03 still carry volume labels (`nvidia-devops` V5 Ch. 2; V7 Ch. 2; V10 Ch. 1 in 02, and `nvidia-devops` V6 in 03). They are in the header metadata table, and I kept them because the original backtick spans must survive. Replacing them needs a decision about the Sources wording. Ch. 01's row was rewritten without volume labels.
2. Some subsections open with a definition rather than a situation (for example 1.1, 2.2, 3.1 in 01; 2.1 and 4.1 in 03). Top-level sections all open with a situation.
3. Numbers and claims from the original that were not checked here and are not changed: 02 "a 405B FP8 model plus KV cache fits in one node"; 02 "1.1 TB of unsharded H200 state"; 02 the per-NUMA "1 TB DDR5" against "16 memory channels" and "eight channels" wording; 03 the "$30,000" SXM price; 03 "two-fold" and "10x" throughput claims; 03 "48 hours" and "1.6 kW headroom" figures in the worked examples; 03 "roughly 20 kW" optical transceiver saving.
4. Chapter 9.1 Exercise 1 asks whether either version fits on one 80 GB H100. That exercise uses a 13B model with its own numbers, so the reader must recompute; no answer is given in the text. Not changed beyond splitting the sentences.
5. Mermaid check and `npm run build` not run (out of scope for this task). No Mermaid text changed.
6. Checkpoint answers were not reviewed (locked by the task).
