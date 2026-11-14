# Voice rewrite ledger: Part 16 chapters 04, 05, 06 (part16_b)

Scope: `docs/part-16-mlops-llmops/04-pipeline-orchestration-kubeflow-pipelines-argo-flyte-airflow.md`, `05-distributed-compute-for-ml-ray-kuberay-training-operator-and-katib.md`, `06-model-registry-ci-cd-and-gitops-for-models.md`. Not committed. EXTERNAL_EDITS.md not edited (per run instructions).

## Words (wc -w, HEAD vs worktree)

| File | Before | After | Growth |
|---|---|---|---|
| 04 pipeline orchestration | 8276 | 10762 | +30.0% |
| 05 distributed compute | 7473 | 9615 | +28.7% |
| 06 model registry, CI/CD, GitOps | 8826 | 11596 | +31.4% |

## Gates (run after final edits)

- `tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three. New numbers 0, lost numbers 0, new code spans 0, lost 0 (04 and 05 and 06 each). Residue 1 to 1 on 06 (unchanged from HEAD, not introduced by this rewrite).
- `tools/restore/chain_gate.py <file>`: 04 = 0.0, 05 = 0.0, 06 = 0.2 per 1000 words.
- Span check (mandatory): `{}` for all three (no missing inline code spans). No new spans added to prose either.
- `node tools/check_mermaid.mjs`: 776 diagrams checked, 0 failed (run once, covers all three).
- `npm run build`: not run (run instructions say no npm build).
- Checkpoints: 20 per chapter, same form and count, unchanged. Sources and review notes: unchanged.
- Code blocks, tables, Mermaid, front matter, headings: unchanged (guard).

## Fixes made during the run

- Removed numeric references that were not in the original (`Section 4.2`, `Section 6.2`, `3 a.m.` wording) so guard reports 0 new numbers.
- Removed inline code spans added in prose (`dependencies`, `schedulerName`, `schedulingGates`, `requests`, `default_args`, `minReplicas`, `maxReplicas`, `objective`, `parameters`, `trialTemplate`, `training_pipeline`, `prepare_op`, `train_op`). Original spans all kept.
- Replaced "you should be able to" lab lines (04 section 7.8, 06 section 7.9) with "try to answer".
- Outcomes sections rewritten as plain paragraphs; no "you will be able to" lists remain.
- No exclamation marks in prose. No `$` math in these chapters (checked: 0 spans).

## Needs source (general explanations added in the rewrite, not attributed to any book)

Chapter 04:
- Definition of a DAG (directed acyclic graph) in the Outcomes paragraph.
- NUMA and NVLink one-line definitions (Section 2.2).
- Content hash as a fingerprint of bytes (Section 2.3).
- Postgres vacuum as cleanup that marks space reusable (Section 6.3).
- Presigned URL as a short-lived single-use upload link (Section 6.4).
- "Backoff" meaning longer waits for a recovering system (Section 2.5).
- NCCL as the GPU collective library and a timeout often meaning shared-resource contention (Section 2.5).
- MIG and GPU fractions one-line definitions (Section 3.3).
- Claim that a tool's debuggability matters more than features (Section 1.6) is an opinion, not a sourced claim.

Chapter 05:
- Ray task, actor, object one-line definitions; placement group description (Section 1.1).
- KubeRay as a controller that reconciles desired and real pod state (Section 1.2).
- Rank 0 as the process that handles shared output (Section 3.2).
- ECC errors as hardware-detected memory errors (Section 3.1).
- Required vs preferred node affinity behaviour (Section 2.3). This is Kubernetes scheduling semantics, not from a cited source.
- Rack affinity description (Section 3.1).
- I/O bound meaning (Section 5.3).
- Explanation that DeepSpeed saves are spread across the cluster because each process writes its own shards (Section 3.3). Derived from the sharded-state description, not from a cited page. Verify against the DeepSpeed checkpoint docs.
- Kueue preemption rehearsal advice (Section 3.4) is a practice suggestion.
- Gang-definition mismatch advice (Section 2.1).

Chapter 06:
- Content hash and signature one-line definitions (Section 2.2).
- Admission webhook as an in-cluster checkpoint that sees each pod before creation (Section 2.2).
- Supply-chain / chain-of-custody framing (Section 2.2).
- GitOps definition and the three rules (Section 3.1).
- Reconciler credentials risk paragraph (Section 3.3): a leaked reconciler credential can change production.
- Lineage stores-disagree advice (Section 1.3).
- Argo Rollouts traffic split explanation: canary and stable services (Section 4.2).
- Warm rollback explanation and tag-based serving (Section 4.3).
- LLM note: cold start means loading a large model into GPU memory (Section 4.4); "prompt regression test" definition.
- Object lock protects against careless as well as deliberate deletion (Section 5.3).
- Admin role should stay small (Section 5.2).
- Recreate / rolling / blue-green trade-off prose (Section 4.1).

## Unresolved (not changed, flagged)

- Chapter 05, code block `train_elastic.py` (locked): line `model, opt = build_model(), build_optimiser(build_model())` is immediately overwritten by `opt = build_optimiser(model)`, so the model is built twice and the first optimiser is discarded. This is a code issue in the original; code blocks are locked for this run. Fix in a separate code-review pass.
- Chapter 05 table row ` JaxJob` (locked table) has a leading space inside the code span.
- Chapter 05 Section 1.3 table: the CRD table is locked; no change.
- Attributions kept as in the original and not verified in this run: "Production Kubernetes, chapter 13" (autoscaling advice, 05 Section 6.5 and checkpoint 14); "Production Kubernetes, chapter 12" (quota, 05 Section 6.6); "Production Kubernetes Chapter 15" on Notary and admission webhooks (06 Section 2.2); "Practical MLOps Chapter 4" and "Designing Machine Learning Systems Chapter 9" on the rollback and deployment patterns (06 Sections 4.1, 4.4).
- Chapter 06 Section 3.3 "the book gives as 5 minutes" retry cap: original attribution kept, unverified here.
- Honest status: each lab is marked untested. Chapter 06 also has one plain sentence above the lab that none of its steps has been run against a live cluster. The original "Not verified on live hardware" sections remain.
- Residue count on chapter 06 stays at 1 (same as HEAD); the guard did not show its source. Not investigated.
- `npm run build` not run (run instructions: no npm build).
