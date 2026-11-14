# Voice rewrite ledger: Part 16 chapters 16.10, 16.11, 16.12 (run d)

Scope: `docs/part-16-mlops-llmops/10-monitoring-drift-and-continual-learning.md`, `11-cloud-mlops-platforms-vertex-ai-sagemaker-and-azure-ml.md`, `12-nvidia-enterprise-stack-ai-enterprise-ngc-and-licensing.md`. Warm teacher rewrite per `planning/HAIKU_REWRITE_INSTRUCTIONS.md` sections 0-3. Step 6 (EXTERNAL_EDITS.md) skipped on instruction. Nothing committed.

Method: front matter, the title table, every code block, Mermaid block, table, heading, the checkpoint block (all 20 questions and answers) and the Sources and review notes tail were copied from HEAD unchanged. Only the prose between "## Why this matters" and "## Checkpoint questions" was rewritten (exercises and lab included), and the splice was done by a scratch script that rebuilds the file from HEAD plus the new body.

## Word counts (`wc -w`, whole file, HEAD vs worktree)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 16.10 Monitoring, drift and continual learning | 7595 | 10533 | +38.7% |
| 16.11 Cloud MLOps platforms | 6442 | 8946 | +38.9% |
| 16.12 NVIDIA enterprise stack | 6813 | 9228 | +35.5% |

Prose-only counts from `rewrite_guard.py` (code and tail excluded): 16.10 6928 to 9866; 16.11 5728 to 8232; 16.12 6048 to 8463.

## Gates (run, output seen)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>` per chapter: 0 hard failures; new numbers 0, lost numbers 0, new code spans 0, lost code spans 0; residue 0 to 0 for 16.10 and 16.12, 0 to 0 for 16.11 (an earlier "the book" wording was caught and removed).
- `python3 tools/restore/chain_gate.py <file>`: 16.10 at 0.4, 16.11 at 0.0, 16.12 at 0.0 (limit 1.5).
- Span check (inline code spans in prose, HEAD vs worktree, the MANDATORY script): `{}` for all three chapters.
- Style sweep on prose: 0 exclamation marks, 0 "you will be able" / "you should be able" / "By the end of this chapter" phrases, 20 checkpoint blocks in each file.
- Honest status: each chapter keeps the word "untested" once in the lab intro. The remaining matches are in the locked Sources tail ("Not verified on live hardware") and in 16.12 Sources. 16.12 also keeps the one status word inside the lab intro only.
- `node tools/check_mermaid.mjs` and `npm run build`: NOT run (instruction: no npm build). Mermaid blocks are byte-identical to HEAD (guard code-block check passed), so no Mermaid edit was made.

## What changed (structure and voice)

- Every section (H2 and H3, including Exercises and Prerequisites) now opens with a situation sentence, not a definition or announcement. Where a locked heading sits above (Outcomes, Prerequisites), the situation is the first sentence under it.
- Outcomes lists rewritten as a plain paragraph of what the chapter walks through. No "you will be able to" lines remain.
- Lab "what to record" lead-ins rewritten without "you should be able to". The duplicate "still untested" sentence at the end of each lab was removed; the single honest status sentence is in the lab intro.
- Exercises and lab steps keep the same count, commands, expected lines and numbers. Lab step prose was rewritten to say why the step matters.
- Numbers: no digits were added to prose. Section cross-references added in rewritten text were replaced with wording (for example "the previous subsection", "the decision table earlier in this chapter") so the guard shows 0 new numbers.
- Number words: the original count words ("five", "three", "four") are kept where they match the original. A few new count words were avoided on purpose.
- Acronyms spelled out at first use in added prose: AUC, TTFT, SLO, IAM, CMDB, DAG, FinOps, LoRA, QLoRA, DPO, RLHF, etcd, ResourceQuota, Notary. KMS (16.11 Section 1.2, original prose) is not expanded; it was left as written.
- Semicolon chains: chain gate 0.4 / 0.0 / 0.0.

## Needs source (general explanations added in the rewrite, not attributed to any book)

Chapter 16.10:
- AUC as the area under the ROC curve, a single score for ranking (Why section).
- Percentile definition (p50 median, p99 slowest requests) and TTFT meaning (Section 1.2).
- Sidecar definition (Section 1.3); SLO definition (Why section).
- Autoencoder and reconstruction error definitions (Section 2.2).
- Kolmogorov-Smirnov p-value and PSI binning explanations (Section 2.2).
- Reference distribution as a photograph analogy (Section 2.3).
- Threshold tuning by replaying last month's traffic and the two-level threshold reasoning (Section 2.4). Practice advice, not sourced.
- Trigger check order: the function returns at the first passing check (Section 4.2). Read from the code in this chapter; the claim about why the order matters is an explanation.
- DAG definition as a set of steps with no loops (Section 4.2).
- Label cardinality and series count explanation (Section 5.3).
- Dead man's switch: explanation of the alert pattern; the cited chapter reference is original.
- Dashboard ordering advice (Section 5.3). Opinion, not sourced.
- Proxy-signal guidance: a cancellation page view as a churn proxy and the "grading its own homework" reasoning (Section 3.2).
- CSAT and NPS as short names for customer satisfaction and net promoter score (Section 1.5).

Chapter 16.11:
- Notebook and IDE definitions; MLflow as an open-source tracking and registry tool (Section 1.3).
- Egress billing claim: "Traffic that crosses clouds is billed as it leaves one provider and enters the other" (Section 1.1). NEEDS VERIFICATION against provider pricing pages before anyone relies on it.
- Cost estimation procedure (hours times hourly rate, then storage and endpoint hours) (Section 2.2). Practice advice, not sourced.
- Spot instance definition (Section 3.1); checkpoint advice for spot capacity (Section 3.1).
- Single pane of glass definition of federation (Section 4.3).
- IAM definition (Section 4.1); FinOps definition (Section 4.2); label definition (Section 4.2); SLO definition (Section 4.3).
- Cold start definition (Section 5.4).
- Open format definition (Section 2.3).
- Admission of a managed registry as a single point of failure and mirror-with-drill advice (Sections 4.4, 5.5). Practice advice.

Chapter 16.12:
- NVLink definition and Fabric Manager role (Section 1.1).
- CUDA and NCCL one-line definitions (Section 1.1).
- CMDB definition (Section 1.3).
- Notary as the image signing system (Section 2.2). NEEDS VERIFICATION of wording against Notary docs.
- Admission webhook definition (Section 3.2).
- etcd as the Kubernetes API state store (Section 6.1).
- Kueue as the admission queue that admits jobs when quota is free (Section 7.4). The Kueue wording is general.
- ResourceQuota as the object that caps namespace use (Section 7.5).
- Kubelet retry with longer waits (Section 7.1). General Kubernetes behaviour, not sourced here.
- Secret store encrypts and records reads, unlike a plain Kubernetes Secret by default (Section 2.3). NEEDS VERIFICATION: default Secret encryption at rest depends on cluster config.
- LoRA, QLoRA, DPO, RLHF one-line definitions (Section 4.1).
- Fine-tuning as continued training on your own examples (Section 4.1).
- Guardrails sit between user and model (Section 4.3); the "rails object" reading of the snippet is from the code.
- The copy-back-to-CPU reasoning for cuDF (Section 5.2).
- Gang job holds GPUs while waiting (Section 4.2): explanation of the waste mechanism.
- Scale-up burst reasoning for the pull-through proxy (Section 2.2).

## Unresolved (not changed, flagged)

- Chapter 16.11 table row "Azure AD" (IAM column) is a locked table cell. Microsoft has renamed Azure AD to Microsoft Entra ID; the row is not changed here. Owner decision.
- Chapter 16.12 `ngc-api-secret` and `ngc-secret` names are kept as in the original lab; no change.
- Chapter 16.12 Section 3.3 manifest uses `mlops.example.com/v1` and `signature_id: sha256:nvidia-signed...`. Locked code, original text. Placeholder, not a real signature.
- `code/part16/...` paths in all three chapters remain as in the original; the referenced code files were not checked here.
- Chapter 16.10 lab step 7.4 uses `my-charts/retraining-trigger` and `evidentlyai/evidently`; not verified.
- Attributions kept as in the original and not verified in this run: "Designing Machine Learning Systems" Chapters 8 and 9 (16.10); "Practical MLOps" Chapters 6, 7, 8, 9 (16.10, 16.11); "Production Kubernetes" chapters 2, 7, 9, 12, 15 (16.10, 16.11, 16.12); "NVIDIA Zero-to-Hero volume 14" in the locked text block (16.12); "Chapter 14.5", "Chapter 15.7", "Chapter 10.9" cross references (16.12).
- Checkpoint answers in all three chapters are unchanged from HEAD (locked by instruction). Several answers in 16.10 and 16.11 are short and could be made scenario-style later; not done here because the checkpoint block was locked.
- Honest status: each chapter keeps one "untested" in the lab intro. Sources tails retain their "Not verified on live hardware" headings.
- `check_mermaid.mjs` and `npm run build` not run.
