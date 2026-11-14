# Voice rewrite ledger: Part 16 chapters 16.1, 16.2, 16.3 (run a)

Scope: `docs/part-16-mlops-llmops/01-mlops-foundations-and-lifecycle.md`, `02-data-versioning-and-experiment-tracking-dvc-mlflow-weights-and-biases.md`, `03-data-pipelines-and-feature-stores.md`. Warm teacher voice rewrite per `planning/HAIKU_REWRITE_INSTRUCTIONS.md` sections 0-3. Step 6 (EXTERNAL_EDITS.md) skipped on instruction. Nothing committed.

## Word counts (`wc -w`, whole file, HEAD vs worktree)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 16.1 MLOps foundations and lifecycle | 13625 | 17804 | +30.6% |
| 16.2 Data versioning and experiment tracking | 9769 | 12945 | +32.5% |
| 16.3 Data pipelines and feature stores | 11420 | 14707 | +28.8% |

Prose-only counts from `rewrite_guard.py` (code and tail excluded): 12218 to 16397, 7859 to 11035, 10229 to 13516.

## Gates (run, output seen)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <3 files>`: 0 chapters with hard failures. New numbers 0, lost numbers 0, new code spans 0, lost code spans 0, residue 0 to 0, code blocks unchanged, front matter unchanged, checkpoint count unchanged, Mermaid unchanged.
- `python3 tools/restore/chain_gate.py <3 files>`: 16.1 at 0.2, 16.2 at 0.3, 16.3 at 0.1 (limit 1.5, exit 0).
- Span check (inline code spans in prose, HEAD vs worktree): `{}` for all three chapters.
- `node tools/check_mermaid.mjs` and `npm run build`: NOT run (task said no npm build). Mermaid blocks are byte-identical to HEAD, so no Mermaid change was made.

## What changed (structure and voice)

- Every H3 and H2 section opens with a situation sentence (a pager, a Monday review, a regulator, a notebook handover). Headings, tables, code fences, Mermaid, checkpoint blocks and the "Sources and review notes" tail were not touched.
- Outcome lists removed. 16.1 "Outcomes" (5 items), 16.2 "Outcomes" (6 items) and 16.3 "Outcomes" (2 paragraphs) are now plain paragraphs with no "you will be able to". The "Outcomes" headings stay.
- Exercises: 6 per chapter, same commands, same spans and same numbers. Bold item titles removed so the section has no more than one bold idea.
- Lab: 16.1 has 6 steps (Steps 1 to 6, lab prose kept, commands unchanged). 16.2 has 6 steps and 5 "what to record" questions. 16.3 has 6 steps and 5 questions. Question lists are unchanged from HEAD.
- Honest status: one "not run" sentence above each lab (16.1 lab intro, 16.2 lab intro, 16.3 lab intro). The duplicate "untested" sentences after the labs were removed. The word "untested" still appears once in the locked Sources tails of 16.1 and 16.2 (not prose).
- 16.2 Section 2.1 five-question list and the Section 3.3 bold idea were kept; bold labels inside "How it fails" (Symptom, Diagnosis, Fix) kept as structure.
- Drafting residue: none added. No "Volume N", "the book", "my tool".
- Rule 6 "no invented attribution": every book attribution in the prose was already in HEAD (Practical MLOps, Designing Machine Learning Systems, Machine Learning Platform Engineering, LLMOps, Engineering AI Systems, Production Kubernetes, Generative AI on Kubernetes, LLM Engineer's Handbook, AI Engineering). No new book claims were added.

## Needs source (general explanations added in the rewrite, not in HEAD)

These are definitions or general-practice claims written as explanation. None adds a number. Each should be checked before the chapter is marked final.

16.1
- Definitions: LLMOps as "large language model operations"; MLOps as "machine learning operations"; CUDA, cuDNN and NCCL one-line roles; confusion matrix; shadow traffic; runbook; aggregation window; vector index as a list of numbers per document; digest as an image hash.
- General practice: teams often buy a tracking server or registry before the basics and believe the work is done (Section 1); a rollback rehearsal finds the missing step (7.3); a tag change takes seconds while a retrain takes hours or days (7.3 fix); many teams combine a reviewed pull request with a signed tag (3.4); gates that need one person to press a button are habits (2.3 append); Gartner described as an industry research firm whose forecasts are predictions (5.2.1).
- Claim-shaped sentence to re-check: "The distributed filesystem is also the place where a quiet change is easiest to make" (6.3 append).
- Claim-shaped sentence to re-check: a fail-open Gatekeeper "quietly lets unsigned pods through during an outage" (6.2). Derived from HEAD's fail-open statement; wording is new.

16.2
- Definitions: DVC expanded to Data Version Control; S3-compatible object store; Git LFS as an extension outside normal history; object lock blocks changes during the retention window; hash-chained log; try/except as a block that hides errors; Sigstore cosign as the tool that signs images and files; HTTP 403 meaning; Pachyderm control plane as the scheduler and tracker; Delta Lake transaction log as the record of every change; stateless server; dead man's switch wording kept from HEAD.
- General practice: a new release that rewords one log line can silence a page (Section 5.4); a migration report kept with the run records (6.6 append); policy audit mode surfaces internal tools that push unsigned images (6.5 append); seed-stability query takes minutes (2.4).
- Scenario framing (no facts): the two-incident comparison in 2.1 append; the Friday-night and Monday examples.

16.3
- Definitions: DAG as directed acyclic graph; ETL as extract, transform, load; materialisation as copying computed values into the online store; embedding as a vector of numbers placing text by meaning; A/B test; expectation as a plain statement about data; chunk as a passage that fits a prompt; ETL and DAG first use.
- General practice: Parquet schema travels inside the file; hash check cost versus a failed job (1.1 append); secrets baked into images leak to every copy of the image (6.2 append); a repository of a pipeline config file leaks passwords into backups (6.2 append); a corpus is the source of truth and the index is a derived copy (5.1 append); a rebuild schedule belongs in the runbook (5.3 append); a parity failure is a stop-the-line event (6.3 append).
- Mechanism claim to re-check: "Soda Core ... means the checks are written as configuration files rather than code" (3.1), which expands the HEAD phrase "YAML-first alternative".

## Unresolved

1. 16.3: HEAD has no "## 4" heading. Section 4 content (4.1, 4.2, 4.3) sits under "## 3" in the original file. Heading order is locked by the rules, so it was left as is. Needs an owner decision (add "## 4" heading or move subsections).
2. 16.2: the locked code fence in Section 2.5 reads "Practical MMOps" (typo in a locked code block). Not changed.
3. 16.2 Section 6.4 keeps HEAD's claim "DVC's default is to overwrite on `dvc push --force`" and "GCS is not exposed to this by default, but only while object versioning stays enabled." These are original claims. They were not re-verified and should be checked against DVC and GCS documentation before the chapter is marked final.
4. 16.1 Section 8.5 keeps HEAD's `storageUri` in the InferenceService example, which uses the S3 scheme with a GCS-based lab. Locked code; flagged only.
5. Math: the three files contain 12 `$` characters. All are shell variables inside code blocks or code spans (for example `$IMAGE`, `${PROJECT_ID}`). No `$...$` math in prose, so no stray-backtick repair was needed.
6. Bold: some sections still carry more than one bold idea where the HEAD bold was a structural label (Symptom, Diagnosis, Fix; checkpoints; list labels in 16.1 Section 3.1). Not removed because they are structure in the HEAD layout.
7. Build: `npm run build` and `node tools/check_mermaid.mjs` not run per task instruction. Needs one run before the chapters are marked final.
