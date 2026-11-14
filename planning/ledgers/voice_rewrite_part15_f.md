# Voice rewrite ledger: Part 15 chapters 16, 17, 18

Scope: docs/part-15-inference/16-production-serving-stack-and-reliability.md, 17-lab-serve-and-benchmark-on-gke-and-nebius.md, 18-inference-cost-capacity-and-cost-per-token.md. Not committed. EXTERNAL_EDITS.md not edited (per run instructions).

## Words (wc -w, HEAD vs worktree)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 15.16 production serving stack and reliability | 12508 | 16037 | +28.2% |
| 15.17 lab: serve and benchmark on GKE and Nebius | 9430 | 12076 | +28.1% |
| 15.18 inference cost, capacity and cost per token | 14299 | 18308 | +28.0% |

## Gates (run on the files on disk)

- `tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures in all three.
  - 15.16: new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 15.17: new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 15.18: new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 15.16 residue count 1 -> 1 (same residue word as HEAD, not added).
- `tools/restore/chain_gate.py <file>`: 0.0 per 1000 words for all three (target 0.2 or lower).
- Span check (`old - new` on inline code spans outside fences): `{}` for all three.
- Locked blocks byte-identical to HEAD: every code fence, table, Mermaid block, checkpoint `<details>` block (20 per chapter) and the Sources and review notes section. Front matter identical.
- Heading list follows HEAD order. The dcgm-exporter 4.9.0 version note and the Xid 62 correction in 15.16, 15.17 and 15.18 are copied verbatim.
- Honest status: each chapter keeps one plain sentence above its live-hardware steps and the word `untested` or `not run` appears in the status text.
- Not run: `node tools/check_mermaid.mjs` and `npm run build` (the run instructions for this batch asked only for the span check, guard, chain gate and ledger). Mermaid blocks are byte-identical to HEAD, so no diagram text changed.

## How each chapter was built

- Each chapter was drafted as prose in a scratch file with placeholders for locked units. A scratch assembler copied each locked unit from `git show HEAD:` in order, so locked blocks are not retyped.
- Each section opens with a situation (an on-call morning, a launch week, a finance review). The Outcomes headings were kept. Their lists became one plain paragraph, without "you will be able to".
- Exercises: 15.16 nested (a)/(b) items became "first part / second part" wording. The same four exercises and the same parameter block are kept. 15.17 keeps its ten numbered exercises and the Solution sketch paragraph (rewritten, same numbers). 15.18 keeps its four exercises and the parameter table.
- Bullets in the chapters hold a question and the answer. Bold labels were removed from bullets. One bold idea remains where the original had a bold sentence.
- Numbers: no new numeric token was added to prose. One rounded phrasing ("about $5.56") was restored to the original exact value ($5.556) before the gate run. One new percentile example in 15.17 and one new figure in 15.18 were removed.

## Needs source (general explanations added in the rewrite)

15.16
- Presidio is an open-source PII detection library.
- Colang is the scripting language NeMo Guardrails uses for conversation flows.
- HGX is NVIDIA's reference eight-GPU server design.
- k3d runs a small Kubernetes cluster inside Docker.
- SHA-256 is a standard hash function (used for stable bucketing).
- A zero-shot classifier labels text it was not trained on.
- CUDA Graphs record a sequence of GPU work for replay.
- Kubelet is the per-node agent that starts and restarts containers.
- A PodDisruptionBudget limits how many replicas a planned drain may remove.
- Least Recently Used eviction and a retry budget (explanations only).
- NCCL is NVIDIA's collective communication library; shared memory as scratch space between GPU processes.

15.17
- MK8s and GKE descriptions (managed Kubernetes services).
- RoCEv2 is RDMA carried over Ethernet; NVSwitch is the switch fabric inside a GPU server.
- DaemonSet runs one pod per node; Gateway and HTTPRoute object roles.
- P8 and P0 as resting and fastest performance states.
- Streaming Multiprocessors as the compute units inside a GPU.
- AWQ keeps the most important weights at higher precision; calibration samples; MMLU as a broad multiple-choice test.
- KEDA is an event-driven autoscaler; ServiceMonitor is the Prometheus Operator object for scraping.
- Cold-start queueing across replicas (teaching analogy, no figure).

15.18
- FinOps as a shared engineering and finance practice.
- Roofline model and the ridge point.
- Total Cost of Ownership and Operational Expenditure as recurring cost.
- PUE covers cooling and power distribution on top of chip power.
- Bisection bandwidth; MoE as mixture of experts.
- Fragmentation as memory too scattered to use.
- Iteration slot as one step of the batch loop.
- Goodput and SLO definitions (explanations, restating the chapter's own targets).
- Analogies (restaurant, shop, toll gate, bus route, parking garage, bank statement) carry no numbers.

## Unresolved

- Math `$...$` with stray backticks: none found in these three chapters, so nothing was repaired.
- Chapter 15.16 exercise and checkpoint text still refers to chapters 20.18 and 20.21 as in HEAD. Those cross-references were kept, not verified against the Part 20 files.
- The status sentence in 15.18 uses `untested` only in the HEAD code-comment spans, which are locked. The prose sentence "were not run on a live cluster" is the honest status line.
