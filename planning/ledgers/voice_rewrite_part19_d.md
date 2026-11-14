# Voice rewrite, Part 19 chapters 10 to 12 (part19_d)

Scope: docs/part-19-capstone/10, 11 and 12. Rewritten in place with paragraph-level replacements. Not committed. EXTERNAL_EDITS.md not touched (step 6 ignored by instruction). Chapter ledgers 19-10, 19-11 and 19-12 were read and their corrections kept: the Larkfield figures, the 95.6 percent completeness, the 37 tests, the B200 and GB300 spine notes, the 14 and 16 bytes per parameter, the 2,252,160 dollar run cost, the 21 review findings, the KEDA CRD validation, the $4.50 placeholder, and the removal of the unsourced 70B and 320 KB figures.

## Words, guard, chain gate, span check

| Chapter | Words before | Words after | Growth (wc) | Guard (rewrite_guard) | Chain gate | Span check |
|---|---|---|---|---|---|---|
| 10 customer workshops and the consulting method | 8328 | 11466 | +37.7% | 0 hard, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.1 | {} |
| 11 system design a training cluster | 8433 | 11132 | +32.0% | 0 hard, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.0 | {} |
| 12 system design inference serving | 8571 | 11180 | +30.4% | 0 hard, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.0 | {} |

Other gates run:
- `node tools/check_mermaid.mjs`: "checked 776 diagrams, 0 failed" (run once, after all three).
- `npm run build`: not run (instruction for this run: no npm build).
- Scripted check against HEAD, all three chapters: front matter and top table identical; headings identical; every table row identical; every code fence identical (13, 7 and 5 fences); all 20 checkpoint blocks per chapter identical; "Sources and review notes" section identical to the end of file.
- Banned phrases: no "will be able to", "should be able to", "you will learn", "By the end" and no exclamation marks in prose. Raw `<` appears only in the locked checkpoint blocks.
- Honest status: each chapter keeps its original "not run" or "not verified" wording (the status row and the locked sections). No new status sentences were added.
- Outcomes: the "After this ... you will be able to" and "After this chapter you can:" lists in all three chapters are now short plain paragraphs under the locked "Outcomes" heading, opening with a situation.

## Rule 9 (lab steps and exercises)

Counts unchanged: chapter 10 has 5 lab steps and 6 exercises; chapter 11 has 5 lab steps and 6 exercises; chapter 12 has 5 lab steps and 6 exercises. Commands, file names and expected results are unchanged. Sentences in the exercises were split where they had more than two numbers (chapter 11, exercises 1, 2, 3 and 6). Two status sentences keep dates and more than two numbers, because they are lab intros, not steps: chapter 10 "Steps 1 to 5 were run on 2026-11-11", and chapter 12 "Every command below was run on ... 2026-11-10 and 2026-11-11".

## Needs source (general explanations added)

Chapter 10
- Fraunhofer halfway break described as "a planned place to stop, written into the schedule" (reading of the original halfway break).
- Plain-words definitions of mean time to detection, mean time to response and change failure rate (check wording against AI Engineering ch. 10).
- "Adjusters are the people who assess claims" (general).
- Reasoning for the ordering of the verdict rules, and the "two runs is not enough evidence" reading (author's policy, already labelled in the original).
- Illustrative scenarios: the Friday demo, the go-live drift paragraph (illustrations, not claims).

Chapter 11
- MFU expanded as model FLOPs utilisation (standard expansion; check against Distributed AI Systems ch. 2).
- "Derating" definition for breaker ratings; "half of the peak" explanation of N with two circuits.
- Rack cooling and throttling explanation (general).
- Rail intuition: "each GPU has its own network card" and "most collective traffic in training has this shape" (check against AI Data Center Network Design and Technologies ch. 3 and the GB300 reference architecture).
- Hidden cost of ports and the rewire risk of buying the minimum (general).
- Definition of a storage tier (general).
- Saved-game analogy for checkpoints; the scaling of failures with GPU count follows from the independence assumption the chapter already labels.
- Hung jobs still look busy (general observation).
- "Here is a plain way to hold the difference" Kubernetes versus Slurm framing (the chapter's own reading of Supercomputers for Linux SysAdmins ch. 13; check wording).

Chapter 12
- KEDA described as an add-on that scales on an external metric (general; check KEDA documentation).
- Why a CPU-based HPA says little about an LLM engine (reasoning on top of Generative AI on Kubernetes ch. 4).
- "A 16.4 GB model fits on one 80 GB GPU, which leaves room for the cache" (general).
- Canary ladder: "this chapter's first step is 5 percent, which costs one GPU" (read from the table; the reason for starting lower is not stated).
- Mechanism examples: a loop of long requests occupying a replica, and analyst replies slowing down (illustrative).
- "Traffic comes first" rollback reasoning (author's reasoning).
- Chargeback as a way to make cost visible (general).
- Spare node reasons: a rollout or a driver hang can take a node out of service (general).
- "Adding a second layer before it is needed only adds a place for bugs to hide" (opinion).

## Unresolved

1. Chapter 10, exercise 4: "use the four edits in lab step 4". The four verdict edits are in lab step 3; step 4 is the decision record. Kept as written, because facts and cross-references stay exact. Owner to decide whether to correct the reference.
2. Chapter 10, section 8.1 and the flag R09: the prose says the peak is six times the average, and the flag text says "more than 5 times." Both are original. Kept.
3. Chapter 12, prose lines with two dollar signs: four lines (cost section, for example $9,720 and $40,635 in one paragraph, and $0.45, $1.56 and $2.28 in another) already had this in HEAD. A remark-math parser may read the text between the signs as inline math. Not repaired here, as the rule asks. Check at `npm run build`, which was not run in this pass.
4. Checkpoint questions are locked (rule 5) and several read as recall, not scenario: chapter 10 questions 2, 6, 11 and 18; chapter 11 questions 1, 5 and 9; chapter 12 questions 3 and 12. Listed, not changed.
5. Chapter 11 and 12 Sources mention "Volume 8" and "Volume 23" in the locked review notes. These are not in reader prose, so they stay.
6. Chapter 12 Pod Security Policies statement stays flagged as unverified in the locked Not verified section; the body text says the same.
7. Chapter 11, the rail explanation claims in "Needs source" should be checked before the chapter is treated as final.
