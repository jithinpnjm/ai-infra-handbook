# Voice rewrite ledger: R2

Chapters: 14.09, 14.10, 14.12, 14.13, 14.15, 14.16, 01.25. All saved. Gates: chain_gate 0.0-0.3 per 1000 words; checkpoint `<summary>` count is 20 in every file (unchanged); no exclamation marks in prose.

language_audit warnings left: 14.12 (numbers per 100 words 6.3), 14.15 (numbers 7.4, long sentences 7.0 percent; most come from checkpoint answers I did not rewrite), 01.25 (semicolons 1.8 per 1000 in a table-heavy chapter). Others have none.

## 14.09 PyTorch compilers
Rewrote: opener and three-bottleneck list (now prose), prerequisites line (TMA, HBM defined), outcomes, intro of section 1, the three rules in 1.4, dynamic-shape bullets, TORCH_LOGS follow-up bullets (Philox PRNG defined), 4.1 numbered list (now three prose paragraphs), common mistakes, interview answers, section-end bold slogans (plain sentences), exercises (6 nested items became 12 single-situation ones), table headers (ASP abbreviation removed). A few checkpoint answers de-parenthesised.
Confirmed: nothing numeric changed. Not checked against source: all figures carried from the chapter's cited text.
Left: "ASP Ch 14" remains inside code/text blocks and the lab output block.

## 14.10 Multi-node architecture
Rewrote: opener (memory and compute walls), cliff and three-mistakes list, outcomes, rail-optimized three-part list, 18x paragraph, rendezvous steps, Slurm daemon list (now a table), preemption/sharded checkpoint reasons, Slurm workflow bullets, NUMA verification bullets, common mistakes, exercises (12 single-situation items), interview answers, section-end slogans. Fixed "our benchmarks / our production troubleshooting case" leaks to "reference benchmark / reference troubleshooting case". Heading "(DAI Ch. 8)" now full title.
Corrected/softened: "a single frontier step takes well over an hour on one GPU ... centuries" replaced by the GPT-3 example the chapter actually computes (about 78 minutes on one A100, about 37 seconds on 128 A100s if communication were free). Dropped "millions of steps ... centuries" (unsourced).
Not checked: 16.7x TP-across-nodes and 300 to 40 GB/s figures come from NVIDIA Zero-to-Hero Volume 13 only.
Neighbour issue noticed, not fixed: lab output line 17 says efficiency at 16,384 GPUs is "~93.9%", but the table says 94.41%. One of them (code or table) is wrong. Also the 6N vs 2N FLOP convention: the GPT-3 step FLOPs (1.46e18) uses 2*N*tokens, which is a forward-only count, though the text calls it a training step; I did not convert because the source gives the number as is.

## 14.12 Training performance and troubleshooting
Rewrote: opener, two-traps list (prose), outcomes, 1.1 explanation, 1.2 FLOPs paragraph, Goodput paragraph, five-phase intro, diagnostic funnel, host CPU/DataLoader fixes (numbered), Roofline intro, communicator lifecycle, DDP/FSDP overlap paragraph, straggler paragraph, regression-gate intro, 54-day ledger intro, symptom table intro, key takeaways (prose), exercises (13 single-situation items), table header abbreviations (DAI, ASP, V13 now spelled out).
Reviewer-flagged claims: "70 to 75 percent of theoretical compute can be lost" confirmed in ASP Chapter 1 as one Meta example ("while the cluster appeared 100% utilized, 70-75% of compute was lost"); softened from a general statement to that cited case. "40 to 50 percent MFU excellent": now phrased as the range this chapter's sources treat as healthy.
Neighbour issue: chapter 14.01 gives MFU 35 to 55 percent; this chapter says 40 to 50. Reconcile in 14.01 (not mine).
Interruption shares (35.3, 52.5, 64.0 percent) left as in the 2026-11-11 correction note.

## 14.13 Fine-tuning (SFT, LoRA, QLoRA, alignment)
Rewrote: opener and three infrastructure points (prose), outcomes, 1.1 information/behavior bullets, BloombergGPT and Ovadia paragraphs, 1.2 mortgage paragraph, progression/distillation paths, six-stage dataset pipeline, template mistakes, 2.3 hyperparameter bullets, 3.2 LoRA details, 3.3 QLoRA three mechanisms, 4.1 preference data (cost, scale, judge bias), PPO infrastructure reasons, DPO techniques, 5.1 merging, 5.2 serving, key takeaways, exercises (15 single-situation items replacing the number-dump pairs). Abbreviations AIE, LEH, HSO, GAK, KFG expanded to full titles in prose and tables (20 places); not in code/text blocks.
Reviewer-flagged claim (LoRA A init): the chapter said A is Gaussian with std proportional to 1/sqrt(r). I could not find that in the cited books (search of LLM Engineer's Handbook and AI Engineering chapters returned nothing). Changed text and the Mermaid label to "small random values", with the LoRA paper's Gaussian and the Hugging Face PEFT Kaiming-uniform default stated. The PEFT default is from my own knowledge and was not re-checked in the corpus. Checkpoint answer 13 text also changed.
"98 percent vs 2 percent": now attributed to the InstructGPT example as the code block does.
Not checked: all other figures carried from the chapter.

## 14.15 Fine-tuning infrastructure and cost
Structural repair: 28 stray ```text fences wrapped bullet lines in prose (breaking rendering) and 15 more wrapped checkpoint and interview answers; all removed. Also removed ":." artifacts after bold list headings.
Rewrote: opener and three cliffs, outcomes, 1.1 bullets, multi-LoRA paragraph, 2.2 QLoRA bullets, 2.3 PPO/DPO/GRPO, 3.1 intro, 3.2 regime bullets (fixed a broken sentence about FSDP regimes), 5.1 merging, 6.1 four-lever FinOps lists, key takeaways, exercises (14 single-situation items; the parameter reference block kept and renumbered), interview answers, section-end slogans, abbreviations.
Not checked: BOM prices, 14.06x and 5x slowdown claims (source Zero-to-Hero Volumes 4 and 21 only); dcgm-exporter note untouched.

## 14.16 NeMo framework
Rewrote: opener, three failures list, outcomes, NeMo/NIM/Guardrails three components, four NeMo 2.0 layers, Megatron-Core parallelism bullets, Curator five steps, checkpoint formats section, key takeaways, exercises (10 single-situation items), abbreviations.
Left: "The Ghost Straggler" label stays inside the Megatron-Core text block (invented name; rename belongs with the code-block owner). Ghost Straggler in 14.07 is not mine.
Not checked: 70 to 80 percent recomputation recovery and 30 to 50 percent slowdown figures (carried from chapter text).

## 01.25 Benchmarking correctly
Chapter was already close to book voice. Rewrote: outcomes bullets 2, 4, 6 (term stacks), lab intro paragraph (backtick and number pile), exercises (6 nested items became 12 single-situation items, no (a)/(b)). No factual changes. Section 6 tool lists left as is.
Not checked: Worked Example numbers (illustrative scenarios, not sourced).
