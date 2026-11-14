# Voice rewrite ledger: Part 19 chapters 19.13, 19.14, 19.15 (pass e, 2026-11-14)

Scope: `docs/part-19-capstone/13-*.md`, `14-*.md`, `15-*.md`. Not committed. No other chapter touched. `planning/EXTERNAL_EDITS.md` not edited (step 6 ignored by instruction). No npm build (instruction). Earlier Part 19 fixes (chapters 19.1 to 19.12 ledgers) were not changed.

## Method

- Rewritten in place. Chapters 13 and 14 were written with one Write each; chapter 15 with one Write, then section-level Edits to add teaching sentences. Code fences, Mermaid blocks, tables, checkpoint blocks, front matter, the top table, headings and the Sources and Verification tails are byte-identical to HEAD (checked by script: fence lists equal, `<details>` blocks equal, heading lists equal, text from `## Sources and review notes` to the end equal, text before the first `##` equal).
- "Outcomes" lists (ch13 six items, ch14 four items, ch15 five items) rewritten as one plain paragraph under the locked `### Outcomes` heading. Each paragraph opens with a situation. No "you will be able to" or "By the end" phrase remains (checked).
- Every `##` section opens with a real situation (locked headings kept, situation in the first sentence under them). Exercise sections gained a situation sentence before the list.
- Exercise and lab step counts unchanged (ch13: 6 exercises, 7 lab steps; ch14: 6 exercises, 5 lab steps; ch15: 6 exercises, 5 lab steps). Commands unchanged.
- Chapter 14 section 4: each of the 40 sample entries keeps its question, level line, teaching-chapter link, model answer, weak answer and follow-up unchanged. Each gained a one-sentence "what this tests" lead-in above the level line and a one-to-two sentence reading note after the model answer. The reading notes restate only what the answer already says and contain no new numbers.
- Chapter 15 section 2: each lettered subsection (A to L) gained one sentence under its heading. The tables are unchanged.
- Chapter 15 step 4: the original sentence "scores of 100, 32.5 and 0.0 and a session mean of 44.2" is kept verbatim. The guard's cross-reference pattern (`\d+\.\d+ and \d+\.\d+`) treats that pattern specially, so a reworded version showed 32.5 as new. Restored.
- Chapter 13 "I" and "my" in reader text removed where they were the author's own choices ("my assumption" became "an assumption for a worked example"; "I set 1800" became "this chapter sets 1800"). "I" in quoted interviewer speech, such as "I will assume 25 researchers", was kept on purpose.
- Chapter 14 backtick span `ulimit` was made plain text in a teaching sentence (the guard counted it as a new span).

## Words, guard, chain gate, span check (run 2026-11-14, final)

| File | Words before (wc) | Words after (wc) | Growth (wc) | rewrite_guard | chain_gate | span check |
|---|---|---|---|---|---|---|
| 13 system design, research infrastructure | 8752 | 11421 | +30.5% | ok, 0 hard, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 4 to 1 | 0.0 per 1000 words | {} |
| 14 interview question bank | 8886 | 11863 | +33.5% | ok, 0 hard, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 4 to 4 | 0.0 per 1000 words | {} |
| 15 interview cheat sheet | 7791 | 10069 | +29.2% | ok, 0 hard, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 4 to 0 | 0.1 per 1000 words | {} |

Guard output lines are copied from the final run. The guard's "words" column (prose words) is 7800 to 10469, 8680 to 11657, and 7403 to 9681.

Other gates run:
- `node tools/check_mermaid.mjs`: "checked 776 diagrams, 0 failed" (run once, after all three chapters). Mermaid blocks are byte-identical to HEAD.
- `npm run build`: not run (instruction: no npm build for this run).

## Numbers

- No digit token was added to prose or removed (guard: new 0, lost 0 in all three).
- Two rewrites were caught and reverted before the final run: a "256 GPUs" example added in chapter 15 (removed) and a split of "scores of 100, 32.5 and 0.0" (restored to the original sentence).
- Chapter 13 exercise 6 and chapter 14 exercise 6 prompts were split into shorter sentences with the same numbers. The "at most two numbers per sentence" split is applied to lab steps and exercises in all three chapters. Some split sentences keep three numbers when they are a single comparison (for example the chapter 13 step 1 summary line).
- Chapter 15 `2 x 32 x 8 x 128 x 2` and other formula lines are unchanged.

## Content changes that need a check

- Chapter 13, section 2: the added sentence about following one request through the diagram says the notebook's GPU is capped by the namespace quota "which is a separate rule from the batch queues". This matches the chapter's existing statement that notebooks use a namespace quota, not Kueue. I first wrote it as if notebooks went through Kueue, caught it on re-read, and fixed it.
- Chapter 13, section 3: "a server idle past that timeout is stopped" replaces "idle for half an hour" (the original value 1800 is unchanged in the YAML and in the sentence before it).
- Chapter 15, section 3: "If the script and the sheet ever disagree, the script wins, because it is the one that was run." is a policy statement added by the rewrite. It is listed under Needs source.

## Needs source (general explanations added in this pass, not from the original)

Chapter 13
- Admission control as the gate the API server runs before it accepts an object (can refuse unsigned or unapproved images).
- PodDisruptionBudget as the limit on replicas taken down during a drain; NetworkPolicy as the rule for who may talk to a pod.
- Gang job as a job that needs all its GPUs before it starts.
- Tag as a movable name and digest as a fixed fingerprint of image contents.
- Lock file as an exact list of package versions; reproducibility checklist's purpose.
- "Floating-point rounding can leave a cent missing or extra" (cost calculator motivation).
- Showback as a report and chargeback as billing; "Most platforms start with showback" (general practice, not sourced).
- Runbook as a written procedure for a known failure.
- Opinions framed as advice: a hand-written Deployment as a maintenance burden; "buying hardware before measuring idle time is the most expensive way to solve a sharing problem"; "a rule that costs a day gets skipped" (section 4 lab note).
- Stage 2 as the stage where sharing starts to hurt; stage 3 mostly repeats stage 2 (chapter reasoning, labelled in the Explicitly labelled inferences list as the staged growth plan).
- A NetworkPolicy and a namespace described as "a label on a box, not a wall around it" (paraphrase of the Production Kubernetes point about logical boundaries).
- Kueue reclaim described as "stop their jobs to take the capacity back" (explains the preemption term).

Chapter 14
- "Few interviews go that deep on every topic" (stretch-question advice).
- Reading notes after each sample model answer (40 entries). They describe what the answer already says and carry no new facts. A reviewer should check that none of them states a fact absent from the model answer. The notes that name a mechanism (for example "the cache is a memory trade") repeat the answer's own words.
- "Stretch questions are worth attempting" and "a miss there is not a reason to panic".
- Practice advice: answer before reading (the bank's design rationale); "recognition does not hold up under pressure".

Chapter 15
- Spacing and memory: "Spacing works because you forget a little between sessions, and the effort of recalling it is what fixes it in memory." (learning-science claim, not in any cited source.)
- "The clarifying step at the start is the one candidates skip most often, and it saves the most time" (general interview advice).
- "A changed count often means a test was skipped or added" (test-run interpretation).
- Reading notes on the 6ND and burn-rate paragraphs ("a spending pace", "the factor-of-eight error is a units error" is original).
- "A row that says the chapters disagree is more useful in an interview" and similar advice paragraphs in sections 1, 2 and 5 and in the "How to answer out loud" intro.
- The Verification and Sources text is locked and was not edited.

## Unresolved (not changed)

- Checkpoint questions that are near bare definitions, left byte-identical per rule 5 (list for the owner):
  - 13: Q1 (what a design question tests, answered in general terms), Q14 (what nominal quota, cohort, borrowing and reclaim mean), Q11 (what `--serve-artifacts` gives researchers).
  - 14: Q2 (first-touch rule definition), Q8 (difference between Xid 63 and Xid 64), Q13 (PagedAttention mechanism, definitional-leaning).
  - 15: Q1 (what makes a row valid), Q2 (what an anchor proves), Q4 (GB per second of a 400 Gbps link), Q6 (what MFU is), Q10 (define burn rate), Q19 (list the rubric parts).
- Locked Sources and Verification log text still contains first-person residue, flagged for the owner (not in the reader body):
  - 13: "I did not open those files", "I did not verify", "I read the docs in git", "I checked the" lines, and the "Explicitly labelled inferences" list ("my assumptions", "my reasoning", "my preference", "my design choice").
  - 14: "my choice" and "my design choices" in the inferences list.
  - 15: "my reasoning" (memorisation and answer order), "my simplification" wording in the Not verified list, and "I checked the PCIe, HBM and NVLink 5 figures" in the Not verified list.
- Chapter 15 Sources: "Read in the local copy; the figures on the sheet match." and the NVIDIA catalog fetch dates are kept as written. Not re-verified in this pass.
- Math `$...$` with stray backticks: none in these three files. Dollar amounts (for example `$12.40`, `$4`) are plain text and were not changed.
- Chapter 13 "(untested here)" span: none in these files. Honest status wording kept as in the original: "Not run", "Untested here", "Not verified on a live cluster" (ch13), "Not run" and "What was run here and what was not" (ch15), "Not run" heading and status wording (ch14).
- Chapter 15 Step 5 printed block is unchanged; the Outcomes list is now a paragraph.
- Original-content observation, not changed: chapter 13 section 6 says the worst borrow wait is 448 minutes and that team d's first training job waits 7.5 hours. These are both kept as the original figures.
