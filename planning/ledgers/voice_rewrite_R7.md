# Voice rewrite ledger: R7

Chapters: 12.3, 12.4, 12.15, 12.16, 12.21, 12.22, 13.2, 13.3 (plus the 12.17 cross-reference). Gates run on all eight: chain_gate under 0.2 per 1000 words, 20 details blocks each, no exclamation marks in prose.

## 12.3 RoCEv2
- Rewrote: Why-this-matters opener (four failure modes now one short paragraph each), prerequisites, GID rule (split into three short paragraphs), "classic trap" and "massive" wording, all six exercises (one situation each), last Sources bullet (removed a stacked term list).
- Not changed: tables, code blocks, checkpoint questions.

## 12.4 PFC, ECN, DCQCN
- Rewrote: "This chapter builds on" paragraph, the XOFF/XON lifecycle paragraph (frame values stay in the table), six exercises, "innocent" to "unrelated", "deterministic" removed, Not-verified bullet.
- Fixed broken math markup throughout (backticks inside dollar signs, for example K_max, R_Gbps) so it renders as normal LaTeX. No values changed.
- Removed a leaked temp path from the Sources block.

## 12.15 NCCL collectives
- Rewrote: two-paragraph opener, outcomes (list instead of ordinal prose), exercise stems, closing Sources paragraph; removed leaked temp paths; fixed broken math markup.
- Claim checked: the "Tree 4.27x faster at 1 MiB" and "37.24 MiB crossover" figures. Recomputed from the chapter's own model (alpha 1 us, 100 GB/s, k_tree 1.15, N=72): Ring 162.68 us, Tree 38.12 us, crossover 37.24 MiB. Arithmetic is right but it is a model with assumed parameters, not a measurement. Softened common mistake 4 to say so.
- Corrected: "two orders of magnitude" for Gloo versus GPUDirect RDMA changed to "about fifty-fold", matching the chapter's own 4 ms versus 200 ms figures.
- Corrected cross-reference: GPUDirect RDMA was cited as Chapters 12.1/12.2; it is 12.19, now stated as a later chapter.

## 12.16 NCCL topology
- Rewrote: outcomes (list), all six exercises (the repeated "This one" opener removed, plain question per exercise); fixed math markup; removed leaked paths.
- Checked: 0.5 GB over 900 GB/s = 0.56 ms and over 28 GB/s = 17.86 ms, ratio 32.14. Correct.

## 12.21 Storage networks and UEC
- Rewrote: sections 1.6 and 1.7 (Figure 9-8 description now two short paragraphs, the duplicated Fabric B description removed), "the book" replaced with the full title in four places, six exercises (bold labels removed, one situation each). Removed leaked paths, fixed math markup.
- Not checked against the source book: the Figure 9-8 leaf/spine numbering (kept as the source gives it; leaf1/leaf2 for the NICs and "Fabric A holds leaves 1 and 2" read slightly differently).

## 12.22 Telemetry and KPIs
- Rewrote: opener, "This chapter connects" paragraph, six exercises (each asks one result per step). Removed leaked paths, fixed math markup.

## 13.2 Local NVMe
- Rewrote: "Used badly" bold slogan paragraph, all six exercises (number walls split). Arithmetic spot-checked: 8 x 200 MB/s = 1.6 GB/s, 72 x 200 = 14.4 GB/s, break-even 250/45 = 5.56 epochs.

## 13.3 GPUDirect Storage
- Rewrote: all six exercises (one question per sentence); the "cuts copy latency in half" general claim now says it holds in the Exercise 1 model (3,000 vs 6,000 MB/s) and that measured gdsio shows 20 percent lower latency.
- Not checked: the 3FS and VAST Data figures (taken from the sources as given).

## 12.17 cross-reference
- Chapter 12.17 said "Chapter 12.14 on GPUDirect RDMA and GPUDirect Storage". That chapter is 12.19. Fixed in docs/part-12-ai-networking/17-nccl-tests-and-fabric-benchmarking.md. Chapter 12.14 is load balancing.

## Neighbouring issues seen, not fixed
- The same broken math markup (backticks inside dollar signs) exists in 12.1, 12.5 to 12.13 and 13.7. Mechanical fix: remove backticks inside $...$ and turn \{ into {.
- Remaining stacked-number reference blocks in code fences (12.15 hardware generations, 12.21 domains) were left alone as code blocks.
