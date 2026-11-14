# Voice rewrite ledger: Chapter 11.31 (NVIDIA's open-source AI factory Kubernetes stack)

File: `docs/part-11-gpu-kubernetes/31-nvidias-open-source-ai-factory-kubernetes-stack.md`
Scope: this chapter only. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (owner instruction). Chapters 11.32 to 11.34 and all other files untouched.

## Words

| Measure | Before | After | Change |
|---|---|---|---|
| `wc -w` (whole file) | 13,576 | 22,439 | +65 percent |
| Prose, per `rewrite_guard.py` (code fences removed) | 12,902 | 21,802 | +69 percent |

Over the 25 to 40 percent band in the instructions. The rewrite was not trimmed, because the rules say never trim. Owner decision needed on whether to cut back to about 18,000 to 19,000 words.

## Gates (run, output seen)

- `python3 tools/rewrite_guard.py HEAD WORKTREE docs/part-11-gpu-kubernetes/31-nvidias-open-source-ai-factory-kubernetes-stack.md`: `ok`, 0 hard failures. New numbers 0, lost numbers 0. New code spans 8, lost 0. Residue 7 to 7.
- Literal backticked-span Counter check, HEAD vs worktree, outside fences: old minus new is empty.
- `python3 tools/restore/chain_gate.py <file>`: 0.1 per 1000 words (limit 1.5, target 0.2 or lower). Exit 0.
- Build: not run (owner instruction, no `npm run build`). `node tools/check_mermaid.mjs` not run. The Mermaid block is byte-identical to HEAD (restored from HEAD).

## How the structure was kept exact

- Front matter, the title, the top metadata table, all 15 fenced blocks (YAML, bash, Mermaid) and all 15 pipe tables were restored from HEAD by position after drafting. The draft was not allowed to change them.
- The checkpoint block (20 questions, `<details><summary>` form) and the Sources and review notes section, including the Verification log, were copied verbatim from HEAD.
- The Exercises section keeps its six exercises. The Hands-on lab keeps its five steps and steps 2b and 4 with the same commands and expected results.
- Section 14 keeps its six numbered steps and five follow-up questions.
- The "Decision rule" and "In one minute" lines were kept as in the original. They are chapter convention. There are 41 bold spans in the file.
- No exclamation marks. Semicolon chains: chain gate 0.1. No "you will be able to" or learning-goal lines.
- "Untested", "not run" and "not verified" appear in the status and lab text (14 matches).

## Changes made in the rewrite

- Each section opens with a situation (a Monday cluster, a Sunday night alert, a pending job, a delivery team).
- The Outcomes list in "Prerequisites and outcomes" was rewritten as one plain paragraph, with no "you will be able to".
- Acronyms spelled out at first use: NVKE, NVKR, AICR, NVCRE, CNCF, SRE, CRD, CEL, DCGM, NCCL, NGC, NIM, SPIFFE, TPM, SBOM, SLA, RBAC, OpenAPI, NICo (as given in the original table).
- Two numeric phrasings were removed during drafting ("a dozen", "twenty"). Analogies introduce no new digits.
- In section 8 I removed a sentence that implied the NVCRE rerun pod tolerates the taint. The chapter's sources do not say that.
- Several unsourced glosses were softened (see Needs source below).

## New code spans (informational)

The 8 new span occurrences are identifiers that already appear in the chapter's YAML, bash or tables, or in the original prose: `kai-scheduler`, `dynamo-platform`, `dependencyRefs`, `thresholds`, `nodesPerJob`, `NoSchedule`, `queue_allocated_gpus`, `queue_deserved_gpus`, plus lab flags such as `--depth 1`, `-I`, `:ro` and `NVKE_OPENAPI`. Lost spans: 0.

## Needs source

Explanations I added beyond the chapter's own sources. Each is general knowledge or an interpretation, not a fact from the NVIDIA posts or repositories read on 2026-11-11. A reviewer should check them.

1. Xid as "the number NVIDIA's driver writes to the system log" (section 8 opener).
2. Nodewright's role, "the piece that prepares the node software" (section 3). The text now says its details were not checked.
3. CNCF Sandbox as "the earliest of its hosted stages" (section 3).
4. Responsibilities of a cloud provider's managed Kubernetes (section 3, "What managed means here"). This is general industry knowledge, not from the NVKE docs.
5. The janitor in NVSentinel. The chapter's sources do not define it. The text now says so and asks the reader to check the repository.
6. How the NVCRE rerun gets past the `NoSchedule` taint (section 8). Open question in the text.
7. Meaning of `queue_allocated_gpus` and `queue_deserved_gpus` (section 12). Read from the metric names, not the metrics document.
8. KAI PodGroup and Queue as "KAI's gang object" and "the object that holds a team's share" (section 4). Check against 11.13 to 11.18.
9. OpenShell as "software that limits what an AI agent is allowed to do" (section 3).
10. Node Feature Discovery, the DRA GPU driver, and cert-manager's role for webhooks (section 6).
11. Level 4 DCGM and the NCCL tests as the way "to push data between GPUs the way a real training job does", NeMo as "NVIDIA's framework for training large models", and goodput as "the share of work that counts as useful progress" (section 7).
12. Cloud maintenance events as "notices that a host is about to be moved or restarted" (section 8).
13. Go as the language "most of these projects are written in" (section 11, checklist item 4).
14. NGC, NIM, Slinky Slurm, Kubeflow, Kueue, the Model Context Protocol, node-problem-detector and Renovate, each given a one-line gloss (sections 2, 4, 6, 10).
15. General Kubernetes and infrastructure definitions: Helm chart, CRD, Deployment, PodDisruptionBudget, Eviction API, taint, cordon, uncordon, SBOM, image digest, fail-closed webhooks, Temporal, PostgreSQL, SPIFFE, TPM, Stars, Apache 2.0 permissions. These are standard meanings and need only a glance.

## Unresolved issues

- Word growth is +65 percent, above the 25 to 40 percent band. Owner decision.
- `planning/EXTERNAL_EDITS.md` not updated, per the owner's instruction. Owner or Claude should add the line.
- Nothing committed. The worktree also shows `docs/part-11-gpu-kubernetes/32-nvke-...md` and `33-nvke-in-depth-part-2-...md` as modified. This run did not touch them, and they are outside this chapter's scope.
- Build and Mermaid check were not run (owner instruction for build). The Mermaid block is unchanged from HEAD, so no new Mermaid risk was introduced.
- Lab steps were rewritten as prose around unchanged commands and expected results. Nothing was run on a cluster. The lab remains honest about this ("not run").
