# Voice rewrite ledger: R3 (Part 10 chapters 02, 04, 10, 13, 16, 18, 19, 20)

Gates run per chapter: chain_gate 0.0-0.1 per 1000 words, language_audit shows no row for these files, checkpoint count 20 in each, no exclamation marks added.

## 10.02 Execution model
- Rewrote: opening (three concrete incidents instead of the "silicon factory" stack), chapter roadmap, "In one minute" bullets (one bold idea), exercises (seven single-question items), table header "Classic failure mode", status row.
- First-person: three "my inference" sentences and the review-note bullet replaced with plain statements that the combined functions are the handbook's own.
- Checked: none needed (no figures changed).

## 10.04 Tensor cores and precision
- Rewrote: opening (removed "dissects", "massive"), outcomes (removed First/Second/Third), exercises (six single-question items, numbering kept to match the parameter block), two "my inference" notes.
- Not checked: the "192 GB physical / 180 GB usable" B200 figure is quoted from the book in a text block and Sources; I did not re-verify it against the book. Reviewer flagged the same figure in 10.01.

## 10.10 Fabric Manager, NVSM, NVLink domains
- Rewrote: opening (a reboot incident), roadmap, "In one minute", outcomes, exercises (11 items, one question each), "my inference" note, "we" in 1.1 and 4.1.
- Suspect claim "15 seconds at boot to train 144 NVLink sub-links": softened to the systemd-analyze blame example (15.234 s, versus 10.123 s containerd and 5.234 s kubelet); the sub-link attribution is now stated as the source example's. Not independently verified against NVIDIA docs.
- Defined ASIC, ABI (application binary interface), RMA at first use. Fixed exercise 1 pointer to Section 1.2.

## 10.13 Memory access patterns
- Rewrote: opening (removed First..Fifth stack and "massive"), table caution paragraph, outcomes, exercises (nine items), "my inference" note.
- Not checked: all Nsight Compute table values remain the book's illustrative numbers, as the chapter already says.

## 10.16 Intra-kernel pipelining
- Rewrote: opening, "massive" x2, exercises (11 items), section name "Explicitly labelled inferences" to "Calculations and verification notes".
- Suspect FlashAttention-3 "roughly 75 percent of peak FP16": CONFIRMED in the book (Chapter 10, "around 75% percent", and "about ~75%"); now attributed to the book. "Cuts execution time in half": tied to the book's illustrative Table 10-2 (41.3 ms to 20.5 ms).
- Noted, not changed: Table 10-4 "0.6x time = 40% speedup" is flagged in the chapter's notes (1.67x faster).

## 10.18 Dynamic scheduling and CUDA graphs (graded 1)
- Rewrote: opening (broken fragments and bare API names replaced with one concrete decode scenario, then three bottlenecks), outcomes (backticks for API names, fewer names), two broken sentences in 1.1, exercises (13 items; removed stray text fences), notes.
- Not checked: the NVL72 "30 TB" row and Table 12-1/12-2 numbers are the book's illustrative figures.

## 10.19 Triton and compilers
- Rewrote: opening (Ampere to Hopper port scenario), defined IR, FX graph, AOTAutograd; outcomes; exercises (13 items); inference note; "our companion module" x2.

## 10.20 Profiling tools
- Rewrote: opening (removed "As our infrastructure notes emphasize" and X-ray framing as a first line), defined NVTX, CUPTI, FSDP, DDP; outcomes; exercises (12 items); first-person "we" in sections 2 to 4; inference note.

## Not done / noticed
- Long backtick-heavy table cells and "ASP"/"V2 Ch" abbreviations remain inside code blocks, lab output blocks, and some table headers (lab output must match the scripts, so not edited). Only the 10.16 table header was expanded.
- The "Sources used" and "Coverage file" metadata rows with planning paths remain in front matter tables of 10.10 to 10.20.
- Neighbouring chapters (10.01, 10.07) still carry the suspect figures the reviewer listed; not touched.
