# Voice rewrite ledger, R1 (Part 14 chapters 01, 02, 05, 06, 07, 08)

Gates after the final edit: chain_gate 0.0 to 0.2 per 1000 words for all six; language_audit 0 warnings for all six; 20 details blocks each; no exclamation marks in prose.
Common changes: removed the "Coverage file" and "Claim ledger" rows from the front table (the paths now sit in Sources and review notes); removed bold-label lead-ins from Common first mistakes and Interview angles; rewrote every Exercises list as one situation per item with short sentences (reference blocks kept); fixed First/Second/Third shapes.

## 14-01
Rewrote: Why this matters (concrete 64-GPU 7B story, three limits as prose), section 5.1 MFU slogan, Exercises (six situations), mistakes, interview intro, Commands and How it fails intros.
Corrected: "312 TFLOPS FP32 tensor ops" in the compute-wall table row changed to the BF16/FP16 peak rate; the 78 min figure is forward pass only and is now labelled so (full 6PD step is about 3.9 hours at that peak, 4.404e18 / 312e12 = 14,115 s). "More than an hour" kept, now "almost four hours".
Softened: "miss your deadline by more than double" to "roughly two to three times" (1/0.55 to 1/0.35). MFU 35 to 55 percent is now attributed to "the sources behind this chapter".
Not checked: the MFU range against the cited sources (14-12 says 40 to 50 percent is excellent; the two chapters still differ, supervisor should reconcile).

## 14-02
Rewrote: Why this matters, 1.2 slogan, 2.3 and 2.1 and 3.2 First/Second shapes, 4.1 and 4.3, section 7 intro, lab intro, exercises, mistakes, interview intro.
Confirmed with source: 98 percent / 2 percent is InstructGPT-specific (AI Engineering Ch. 2); wording now says so. 10x to 20x vLLM throughput over Hugging Face generate is in Hands-On LLM Serving and Optimization ("in many benchmarks"); attributed.
Corrected: "wastes 20 to 30 percent to fragmentation" was a misreading. The PagedAttention paper (quoted in Hands-On) says only 20.4 to 38.2 percent of KV memory held token states without paging. Fixed in prose, the vLLM table row and failure mode 1 row.
Replaced unsourced "3.6x to 18x" with the two example values it came from (Mixtral 3.62x, DeepSeek-V3 18.14x). "5x to 40x" now tied to the 13B example.
Not checked: Chinchilla/scaling numbers, GPT-3 cost figures, MASSIVE token counts (left as is).
Checkpoint question text and long tables not rewritten (tables are lookup material).

## 14-05
Rewrote: Why this matters (bottleneck paragraph split), 1.2 opener, 4.3 SuperOffload list into prose, DMA defined at first use, "As verified in Volume 13 Lab 04" leak, exercises, mistakes, interview.
Confirmed by arithmetic: Stage 2 saves 122.5 GB per GPU on 70B over 8 GPUs (140 GB / 8 shard removed).
Not checked: FLAN-T5 benchmark numbers, SimpleFSDP 28/69 percent figures.

## 14-06
Rewrote: Why this matters (First to Fourth into short story plus ladder), the three byte conventions into one explanation (16-byte mixed, 12-byte without master copy, 16-byte pure FP32; the text block after it unchanged), 2.2 prerequisites, 2.3 and 3.1 First/Second/Third, 4.3 stacked-term paragraph, section 5 intro, exercises, mistakes, interview.
Not checked: 21x offload slowdown, 85x NVMe slowdown, Megatron 50x checkpoint resharding claim.

## 14-07
Rewrote: Why this matters (four-limit bold list into prose), slogans, list bold labels, exercises, mistakes, interview.
Renamed "Ghost Straggler" to "edge-stage straggler" in prose, headings of the text block and checkpoint question 12. The term comes from NVIDIA Zero-to-Hero Volume 13 Chapter 7 (also in code/part14 comments); a note in Sources says so. Code files untouched.
Not checked: 16.7x TP cross-node slowdown (derived from source numbers, left), DualPipe near-zero bubble.

## 14-08
Rewrote: Why this matters opener and bold slogan, "our" first-person (three places), list bold labels, section 3 pattern intros, exercises, mistakes, interview.
Not checked: 30.24 percent MoE compile gain and Table 13-x values (from the source book); interview Q2 says dense 70B gained 6 percent while the text says under 10 percent, consistent.

## Neighbouring chapter notes (not fixed)
14-12 MFU (40 to 50 percent excellent) vs 14-01 (35 to 55); 14-05 uses the 12*Psi count while 14-01 and 14-06 treat 16 bytes as standard (explained in 14-06 now).
