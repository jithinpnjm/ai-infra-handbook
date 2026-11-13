# Voice rewrite, Part 11 batch C (chapters 11.7, 11.8, 11.9)

Scope: `docs/part-11-gpu-kubernetes/07-*.md`, `08-*.md`, `09-*.md` only. No commits. EXTERNAL_EDITS.md not touched (per lead instruction).
Tone bar: `02-device-plugin-container-toolkit-cdi-and-runtime-classes.md` and `08-operating-gpu-nodes-nvidia-smi-topology-clocks-and-throttling.md`.

## Word counts (`wc -w`, HEAD vs worktree)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 11.7 multi-node jobs (file 07) | 8365 | 10989 | +31.4 percent |
| 11.8 Kueue, Volcano and scheduler plugins (file 08) | 8232 | 10583 | +28.6 percent |
| 11.9 JobSet, LeaderWorkerSet, PyTorchJob, MPI Operator (file 09) | 7738 | 10126 | +30.9 percent |

## Gates (run and read)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: all three `ok`, 0 hard failures, new numbers 0, lost numbers 0. New code spans added: 2 (07), 4 (08), 7 (09). Lost code spans: 0.
  - Guard run on 08 first reported `code blocks changed: +1 -1` because the captured-output block lost its final `Summary:` line. Restored; guard then clean.
- `python3 tools/restore/chain_gate.py <file>`: 07 = 0.0, 08 = 0.1, 09 = 0.1 (target 0.2 or lower).
- Mandatory span check (`{}` required): 07 `{}`, 08 `{}`, 09 `{}`.
- Structure: headings, front matter, Mermaid, tables, code blocks, checkpoint `<details>` blocks (20 / 20 / 20) and Sources sections left as in HEAD. Exercises: 07 six paragraphs, 08 six numbered items, 09 six numbered items.
- Not run: `node tools/check_mermaid.mjs` and `npm run build` (lead said no npm build). Mermaid blocks are unchanged text, so no new Mermaid risk was introduced, but the check was not executed.
- Honest status: each chapter keeps one "were not run on a live cluster" sentence above its lab, and the Sources sections still carry their "Not verified on live hardware" notes.

## Fact fixes that hold

- Kueue API version `kueue.x-k8s.io/v1beta2` kept in 07 (table and text) and 08 (manifests and text).
- Kueue quota units: 08 now says `nominalQuota` for `nvidia.com/gpu` counts whole GPU devices, and the borrowing limit is counted the same way (see Needs source).
- KAI quota units: 08 now says the KAI Project `gpuQuota` is a count of GPUs, the same unit as the Kueue device count (see Needs source).
- Numbers: no digit added or removed anywhere (guard `new numbers 0`). Spelled-out counts that appear only in new prose were kept to ones already in the source.

## Needs source (general explanations added in prose, not from the book corpus)

These were added as definitions or mechanism explanations. They carry no new numbers, but a reviewer should confirm them against upstream docs.

- 07: Allocatable (what a node advertises after system reservation); RDMA and RoCE and InfiniBand definitions; MIG definition; c10d and TCP store description; DDP, FSDP, DeepSpeed, Megatron-LM one-line descriptions; atomic barrier release semantics; S3, GCS, MinIO, NVMe, burst buffer, CSI descriptions; cloudpickle serialization risk wording; default-deny NetworkPolicy semantics; Ray as the framework behind ports 6379, 8265, 10001; the sentence that North-South and East-West describe traffic into and between servers.
- 08: Dominant Resource Fairness definition; HPC and MPI one-line definitions; mutating webhook semantics; cordoned node meaning; "unsuspend" meaning (clearing the suspend flag); the menu analogy for flavor order; the recall-clause analogy for cohort lending; quorum split example (four members split into two halves of two); shuffle-sharding "hand" explanation; the "Kueue units count whole GPU devices" statement; the "KAI gpuQuota is a count of GPUs" statement (highest priority to verify against KAI Scheduler docs, since the source only shows `gpuQuota: 8`).
- 09: Headless Service and StatefulSet and Indexed mode definitions; CoreDNS role; TCP rendezvous store as a small server; SIG-Apps role; JobSet failure-domain wording; Multus definition; Secret and ConfigMap definitions; sshd role in MPIJob; server-side apply explanation; DeepSpeed and TRL and PEFT definitions; catastrophic forgetting explanation; distillation definition; prompt-first reasoning; Gateway API Inference Extension one-line definition; leaf switch and NVLink domain definitions; gRPC definition; tensor and pipeline parallelism definitions; X-LoRA and QLoRA one-line descriptions (QLoRA 4-bit wording was already in HEAD checkpoint answer 8); KubeRay and Katib and Ray definitions; notebook magic and DAG and lineage definitions; the `numNodes: 1` versus `num_nodes=8` comparison (stated as a contrast only, no claim about override behavior).

## Unresolved

1. `check_mermaid.mjs` and `npm run build` not run (lead instruction). Needs a run before merge.
2. KAI `gpuQuota` unit wording needs an upstream check (see Needs source).
3. Exercise input blocks (07 and 08) keep their original multi-value lines by design, because the rule says to keep the same commands and facts. Prose exercises are split into one-question sentences.
4. Captured lab output blocks are unchanged, so they still reflect the HEAD capture. The lab was not re-run in this pass.
