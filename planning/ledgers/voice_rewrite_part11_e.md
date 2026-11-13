# Voice rewrite ledger: Part 11 chapters 11.13, 11.14, 11.15

Scope: `docs/part-11-gpu-kubernetes/13-*.md`, `14-*.md`, `15-*.md` only. Not committed. `planning/EXTERNAL_EDITS.md` not edited (run instruction overrides step 6).

## Words and gates

| File | Words before | Words after | Growth | rewrite_guard | chain_gate | Span check | Mermaid |
|---|---|---|---|---|---|---|---|
| 13-kai-scheduler-why-default-scheduling-is-not-enough.md | 8384 | 10759 | +28.3% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 14 to 14 | 0.1 | `{}` | `tools/check_mermaid.mjs`: 776 checked, 0 failed |
| 14-kai-scheduler-architecture-and-resources.md | 8143 | 10296 | +26.4% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 16 to 13 | 0.1 | `{}` | same run |
| 15-kai-queues-quotas-and-fair-sharing.md | 7944 | 10023 | +26.2% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 23 to 14 | 0.0 | `{}` | same run |

Word counts are `wc -w` on the whole file. `npm run build` was not run (run instructions say no npm build).

## Method

- Front matter, title table, all fenced code blocks, Mermaid diagrams, data tables, the Sources and review notes, and the checkpoint questions were kept byte-for-byte from HEAD. They were spliced back in by block index. Every heading was checked against HEAD (same text, same order).
- Every body section was rewritten. Each section opens with a situation (a job, a team, a pod, a meeting), not with a definition.
- The Outcomes lists in 11.13, 11.14 and 11.15 became plain paragraphs. No "you will be able to" or "by the end of this chapter" lines remain.
- Exercises: 6 per chapter, same count and same function names and inputs. Multi-part asks were split into single-question sentences. 11.13 and 11.14 exercises were rewritten from paragraphs or table lines; 11.15 exercises are the six prose exercises.
- Lab commands unchanged: `python3 code/part11/kai_why_default_not_enough_lab.py`, `python3 code/part11/kai_architecture_and_resources_lab.py`, `python3 code/part11/kai_queues_quotas_fair_sharing_lab.py`.
- Gem books: none cited in these three chapters. The "Generative AI on Kubernetes" and "NVIDIA Base Command Manager 11 Containerization Manual" attributions are the originals and were kept.
- KAI quota units (devices for GPU, millicores for CPU, MB for memory) kept as in the original, not reverted.
- "Volume N" residue in prose was replaced with "the design notes" or "the NVIDIA zero-to-hero capacity-planning notes". The `volume-NN/chapter-NN` spans were kept where they sit in tables, the locked Sources, and a few prose sentences (span check requires it).
- Residue in the caution admonitions (11.13 and 11.14): "come from the book example" became "come from the *Generative AI on Kubernetes* example", and "the corpus" became "the sources used here". Prose only; spans unchanged.
- Honest status, one per chapter: 11.13 "Cluster commands are marked `(untested here)`, so these steps were not run on a live cluster."; 11.14 "Cluster commands are marked `(untested here)`, so you can tell them apart from what you actually ran."; 11.15 "The cluster commands in earlier sections are marked `(untested here)`, so these steps were not run on a live cluster, and the lab does not check them."
- Captured output in 11.15 reworded to "The block below shows what a passing result looks like." (the capture claim could not be checked). 11.13 uses "shows what a passing run prints". 11.14 keeps "The captured output from this repository is below." because the locked Sources say the lab was run.

## Needs source (general explanations added in prose, no new facts)

11.13
- PriorityClass as a fixed importance number the scheduler reads without history; VRAM and NVSwitch as plain terms; MIG profile and leaf switch as plain terms; HBM as on-package memory.
- Gang as a set of Pods that must start together; relay-race and reserved-desk analogies.
- Shared-kitchen analogy; library reading-room analogy; fire-drill / warning-bell analogy for SIGTERM and SIGKILL.
- SIGTERM and SIGKILL as polite and forceful signals; exit code 0 as normal finish; kubelet as the per-node agent.
- Helm as the package manager that records release history; SAN as the list of names a certificate is valid for; air-gapped as having no direct internet link.
- Defense-in-depth and jitter as plain terms (11.14 uses the same wording).
- Claim that a gradient exchange over Ethernet pays its cost on every training step (general, check against the NCCL / network sources if quoted).
- Claim that a failed Kubernetes deployment should not leave a half-written Run:ai configuration (design reasoning, not sourced).

11.14
- CRD as the way Kubernetes learns a new object kind; ownerReference as the parent link that garbage collection uses.
- Sorting-center and restaurant-host analogies; point-in-time snapshot as a copy at one moment.
- Canary environment as a small copy of production that gets changes first.
- MIG slice as a hardware partition with its own compute and memory paths; VM-backed tier as its own guest kernel.
- Claim that a Project change is reflected in the Queue "within a session or two" and that the scheduler reads it in the next snapshot (behavior claim; verify against upstream queue-controller).
- Reclaim runs before Preempt because the owner's claim crosses team lines (reasoning; the Stage order is from the original).
- Each fixture is named after the behavior it checks (wording only; the original said five test cases).
- Claim that an unresolved reference stops the job at the admission step (verify against admission-webhook behavior).

11.15
- Floor-office and bus-schedule analogies for hierarchy and Level 1-3 HFQ.
- Hotel analogy for headroom reserves.
- Slurm account and QOS as policy objects; claim that QOS priority orders tiers and account priority orders groups inside a tier (verify against Slurm sacctmgr and priority docs).
- Claim that an integer maxgpus cap rounds a fractional share in a way the scheduler can use (verify).
- Showback vs Chargeback definitions (the original gave the checkpoint definition; the no-money-moves wording is ours).
- Claim that a purchase request is the most expensive fix and usually fixes nothing if the sharing rule stays the same (opinion, not sourced).
- Rounding up to whole nodes as the reason for buying nine nodes (the formula's ceil makes this explicit; the "eight cannot hold the demand" sentence was reworded without a new number).
- Canary environment definition; leading and lagging signals as plain terms.

## Unresolved items

1. No cluster gate was run. Kubectl, Helm, cm-runai-setup, Slurm sacctmgr and every live-cluster command in these chapters are still untested, as the honest status lines say.
2. "Volume" and "Example N-N" residue remains only inside locked Sources blocks, the caution block's upstream references, and span-preserved prose mentions of `volume-NN/chapter-NN`. Guard residue counts are 14 to 14, 16 to 13, and 23 to 14.
3. The 11.13 and 11.14 caution admonitions are the only prose edited inside a locked block (wording only).
4. Chapters 11.14 and 11.15 keep the November 2026 update blockquote and the dcgm-exporter note verbatim, including the link targets.
5. Three Needs-source behavior claims in 11.14 (Project to Queue propagation, admission rejection timing) and two in 11.15 (Slurm priority ordering, integer cap rounding) should be verified against upstream before publishing.
