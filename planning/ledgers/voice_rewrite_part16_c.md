# Voice rewrite ledger: Part 16 chapters 16.7, 16.8, 16.9 (run c)

Scope: `docs/part-16-mlops-llmops/07-model-serving-platforms-kserve-seldon-and-bentoml.md`, `08-llmops-rag-vector-databases-and-agents.md`, `09-llm-evaluation-and-guardrails.md`. Warm teacher voice rewrite per `planning/HAIKU_REWRITE_INSTRUCTIONS.md` sections 0-3. Step 6 (EXTERNAL_EDITS.md) skipped on instruction. Nothing committed.

## Word counts (`wc -w`, whole file, HEAD vs worktree)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 16.7 Model serving platforms | 9530 | 12320 | +29.3% |
| 16.8 LLMOps: RAG, vector databases and agents | 7432 | 9629 | +29.6% |
| 16.9 LLM evaluation and guardrails | 7914 | 10294 | +30.1% |

Prose-only counts from `rewrite_guard.py`: 16.7 8719 to 11510; 16.8 6516 to 8713; 16.9 6595 to 8975.

## Gates (run, output seen)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <3 files>`: "3 chapters, 0 with hard failures. words 21830 -> 29197. new numbers 0, lost numbers 0, new code spans 0, lost 0". Residue 0 to 0 in each file. Code blocks, Mermaid blocks, table rows, headings and front matter match HEAD (checked with a separate script; 20 checkpoints per chapter unchanged).
- `python3 tools/restore/chain_gate.py <3 files>`: 16.7 at 0.1, 16.8 at 0.1, 16.9 at 0.0 (limit 1.5, exit 0).
- Span check (inline code spans in prose, HEAD vs worktree, rerun after the last edits): `{}` for all three chapters (no missing, no added spans).
- `node tools/check_mermaid.mjs`: "checked 776 diagrams, 0 failed". Mermaid blocks are byte-identical to HEAD.
- `npm run build`: NOT run (task said no npm build).
- `python3 tools/language_audit.py`: not run in this run.
- Exclamation marks in prose: none. Raw `<` or `{` in prose: none added.

## What changed (structure and voice)

- Every section opens with a situation: a release day, a pull request, a night-time alert, a support lead's question, a finance report, an on-call phone call. Under the locked "Outcomes" headings the situation is the first sentence of the paragraph.
- Outcomes lists rewritten as plain paragraphs in all three chapters. No "you will be able to" or "should be able to" phrasing remains. The "Outcomes" headings stay.
- Exercises: same count (6 per chapter), same commands, same spans, same solution sketches. Bold exercise titles converted to plain sentences so each section has at most one bold idea. Each exercise opens with a situation.
- Lab: same step headings, commands, expected lines and "what to record" questions (5 each). Lab intro carries one honest sentence about the lab not being run or tested. Duplicate status sentences at the end of 16.7 section 7.8 and 16.8 section 7.8 and 16.9 section 7.8 removed (the Sources tail still says "untested", which is locked).
- 16.7 section 4.4: four bold lead-ins converted to plain paragraph openers ("Deployment mode comes first.", "The vLLM runtime is next.", etc.) to keep one bold idea per section.
- Number and count hygiene: no digits added. Spelled-out counts that were not in the original were reduced (for example "three places" became "several places" in 16.7 section 1.1; "a few hundred" was used in 16.9 instead of a numeral).
- Honest status: 16.7 lab intro ("has not run the lab against a live GKE cluster"); 16.8 lab intro ("untested in this repository"); 16.9 lab intro ("has not been tested in this repository"). The locked Sources tails also contain "untested" or "not verified".
- Part 16 remediation carried forward and kept (not reintroduced or reverted):
  - 16.7 section 4.2: Seldon YAML is one predictor with a retriever graph node and a generator child; text explains that several predictors are alternatives (voice_rewrite_R10 and rework_X7 fix).
  - 16.7 section 4.3: `BentoModel` declared at class scope, loaded with `path_of` and `joblib` in `__init__`, API method uses `@bentoml.api` (R10 fix).
  - 16.7 section 2.5 and 4.4: repository state dated 2026-11-12 and KServe v0.21 facts kept exactly.
  - 16.7 section 3.3: canary described as serverless-mode only; 100 percent promotes the revision; shadow is not a 100 percent canary (rework_X7 fix).
  - 16.9 section 4.3: system prompt described as "the first layer of defence, but it is not enough on its own" (R10 fix); classifiers described as rule-based stand-ins for trained models (R10 fix).
  - 16.9 section 4.2 and 4.4: stand-in code is labelled as stand-in (R10 fix).
- Attribution: every book attribution in prose was already in HEAD (Generative AI on Kubernetes, Designing Machine Learning Systems, Practical MLOps, Machine Learning Platform Engineering, LLMOps, AI Engineering, LLM Engineer's Handbook, LLMs in Production, Engineering AI Systems, Production Kubernetes, AI Factory). No new book attribution was added. Gem books are named in full.

## Needs source (general explanations added in the rewrite, not in HEAD)

These are definitions, general practice or scenario framing written as explanation. None adds a number. Check each before the chapters are marked final.

16.7
- Definitions: SLO expansion; IAM expansion; Flask as a small Python web server; circuit breaker; CRD and controller; replica; revision; service account; network policy; Secret; External Secrets Operator; IAM binding; line rate and Gbps; HBM as high-bandwidth memory; KV cache; prefill and decode; round-robin; SHAP, LIME and attention maps as per-prediction explanation methods; BPE expansion; collocated containers share network and need different ports; Helm and chart; tensor; `hey` as a load generator; idle window; cold path (6.2); edge (6.5); OOM and 503 meaning; HTTP 403 meaning.
- General practice or mechanism: GPU-bound LLM can look idle on CPU (3.1); a startup spike triggers HPA scale-out (3.1 expansion); a single Bento with two models means one bug can take down both (4.3); Bento packaging dependency drift (2.3); A/B sticky variant assignment makes comparison fair (3.4); ground truth definition (3.4); "the install order matters" for InferencePool (4.4, kept to the documented warning only).
- Scenarios (no facts): the on-call pager opening (Why section); the quiet afternoon walkthrough for scale-to-zero (3.2); the support lead and the Monday night examples (1.1 to 6); the Seldon operator reads SeldonDeployment (2.2).
- Load measured in concurrent connections, and the advice to check the scale metric when replicas do not move (7.6).

16.8
- Definitions: embedding as a list of numbers; hash as fingerprint; top-K; held-out set; QPS; Jinja as a templating language; eval suite as fixed questions run automatically; partition; cosine distance; segment in Milvus; IVF and HNSW mechanics (cluster search; layered graph); structural cap; schema as contract; span; immutable log; OpenTelemetry as common standard; Prometheus series; metrics adapter.
- General practice or mechanism: sorted keys make the snapshot id stable (2.3); the order of checks corpus, chunking, embedding (2.3); a freshness scenario and "nothing in the logs says so" (2.3 scenario); tool schema mismatch as a useful failure (3.2); trace headers that drop split the trace (3.4); a fixed bounded graph lets you estimate cost (3.3); separate budget layers so one failure does not disable the others (5.2); a dashboard only the platform team reads does not help prompt tuning (5.3); a template change is cheapest to change but not safe (4.1); one regression case per customer-found bad answer (4.2).
- Scenarios (no facts): the agent walkthrough with the shipping and order tools (3.1); the busy-morning opener in 16.8 section 1.2 has no numbers; the relay-race analogy for the lab (7 intro); the 2,000-token and 20,000-token prices kept exactly from HEAD.

16.9
- Definitions: PII expansion; JSONL; Kubernetes Job and CronJob; sidecar; named-entity recogniser; false positive; hallucination; bias as systematic lean; rubric; jailbreak as override; dead man's switch wording kept from HEAD.
- General practice or mechanism: reviewers who do not know the domain give fluent wrong answers high scores (2.4); two reviewers scoring the same answer as a clarity check (2.4); a golden set that is broad can hide a regression on a narrow group such as refunds (1.2, scenario with no numbers); without each workflow step you lose a specific signal (1.3); "the gate tests yesterday's product" (6.5); self-preference is invisible inside the suite (6.2); "no classifier catches everything" (6.4); "a monitor that fails silently looks like a quiet night" (5.3); input checks save the cost of a refused generation (4.1); the three modes as levels of attention (2.1 analogy); "the jailbreak check is the only layer that sees the prompt" (4.3); the stand-in factuality code uses word overlap and is a teaching model only (4.4).
- Claim-shaped sentences to re-check: "Every case you add is a bug that cannot quietly return" (3.1); "an incomplete log is worse than none" (5.2); "a gate can only enforce what its test set contains" (6.1).
- Lab: "each one is installed as its own workload" (7.3 replaces an earlier "runs as its own pod" wording); "starting from the cron job means the run uses the same settings as the nightly schedule" (7.4); "the tag ties a run to the exact eval set" (7.5); "the new sets go through review like any other change" (7.7).

## Changed fact wording (flagged for review)

- 16.9 section 4.4: HEAD said "The factuality filter is LLM-as-judge". Now "The production factuality filter is LLM-as-judge". The code block is labelled a word-overlap stand-in, so the word "production" makes the prose agree with the code. No number changed. Owner should confirm that the production factuality filter really is LLM-as-judge.

## Unresolved

1. Build: `npm run build` not run (per task). `node tools/check_mermaid.mjs` passed (776 diagrams). Needs one `npm run build` run before the chapters are marked final.
2. `python3 tools/language_audit.py` and `python3 -m pytest code/part16` not run in this pass.
3. Checkpoint questions and answers are locked by the task and were not changed. Several answers in 16.7 and 16.8 are longer than the 2-5 sentence rule in RULES_AND_WORKFLOW section 1.10 or use a paragraph of prose; that is an owner decision.
4. Exercise solution sketches kept as HEAD wrote them. Known weak sketches: 16.7 exercise 2 (a sidecar that polls `nvidia-smi` is not a sidecar-of-transformer pattern; flagged in rework_X7.md), 16.7 exercise 4 (Alibi explainer is named but not sourced), 16.8 exercise 6 (Argo DAG wording), 16.9 exercise 2 (`judge-model` config key not defined in the chapter).
5. 16.7 section 4.4: `LLMInferenceService` is `v1alpha1` and the example is copied from documentation, untested. Kept as the locked Sources tail says.
6. 16.8 section 2.2 and 2.4: Milvus component names, the `vector(1536)` column width in the SQL and the pgvector operator are from HEAD and were not re-verified against vendor docs in this pass.
7. 16.9 section 5.1: the classifier size phrase "a few hundred megabytes to a few gigabytes" is HEAD text, not verified.
8. Math: no `$...$` math in these three files. Dollar amounts are plain prose, not math.
9. Bold: 16.8 keeps one bold line in the Why section plus the locked table bold labels; 16.9 keeps one bold line in the Why section plus locked table labels.
10. Scratch: no scratch files written. Nothing committed. Other chapters (10, 11) show as modified in `git status` from other agents; not touched here.
