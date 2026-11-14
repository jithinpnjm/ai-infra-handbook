# Voice rewrite, Part 19 chapters 04 to 06 (part19_b)

Scope: docs/part-19-capstone/04, 05 and 06. Rewritten in place with Edit. Not committed. EXTERNAL_EDITS.md not touched (step 6 ignored by instruction). Earlier fixes from `voice_rewrite_part19_a.md` and the 19-04/19-05/19-06 claim ledgers were kept: the corrected figures (Llama 3 counts, no NCCL_TIMEOUT, app=nvidia-dcgm-exporter, 4.9.0 metric names, 7.3 h and 43.8 min budgets, 1-node budget on a 4-node pool, Xid class table) are unchanged.

## Words, guard, chain gate, span check

| Chapter | Words before | Words after | Growth (wc) | Guard (rewrite_guard) | Chain gate | Span check |
|---|---|---|---|---|---|---|
| 04 multi-node training with fault tolerance | 12961 | 16806 | +29.7% | 0 hard, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.1 (<=0.2) | {} |
| 05 nccl-tests fabric lab | 8683 | 11248 | +29.5% | 0 hard, new numbers 0, lost numbers 0, new code spans 1, lost 0 | 0.1 | {} |
| 06 node-health automation | 11258 | 14542 | +29.2% | 0 hard, new numbers 0, lost numbers 0, new code spans 3, lost 0 | 0.1 | {} |

Other gates run:
- `node tools/check_mermaid.mjs`: "checked 776 diagrams, 0 failed" (run once, after all three chapters).
- `npm run build`: not run (instruction: no npm build for this run).
- Checkpoint blocks: 20 per chapter, unchanged, byte-identical to HEAD. Sources and review notes: byte-identical to HEAD in all three. Code fences, front matter and headings: identical to HEAD in all three. No `$...$` math in prose.
- No "will be able to", "should be able to", "you will learn" or "By the end" left in any of the three.
- Honest status: each chapter keeps its original "not run" / "untested" status wording (the status row, the lab intro, and the locked step headings "not run"). No new status sentences were added.

Guard "new code spans": ch05 has one new span (`ARITHMETIC_MISMATCH`, a flag name that the chapter's table already shows in a code span); ch06 has three new spans (flag and command names used in prose). These are soft and were left as they are.

## Outcomes lists

Each of the three chapters had a numbered "After this capstone you will be able to" list under a locked "Outcomes" heading. Each was rewritten as one plain paragraph under the heading, starting with a situation. The heading text is unchanged. The `torchrun` span from the original list item 5 is kept in the ch04 paragraph.

## Needs source (general explanations added)

These were added as teaching explanations. None adds a new fact about this project. A reviewer should check the wording against a source or accept it as common background.

ch04
- Definition of a checkpoint as a saved copy of weights and training state.
- FSDP2 as the second generation of PyTorch fully sharded data parallel.
- DTensor as a tensor that records which slice each rank holds.
- "Loading in place means no second full copy of the model."
- Pinned memory as memory the OS may not move, which makes device copies faster.
- "Memory-to-memory moves are quicker than writes to a shared file system" (general, not measured here).
- Future as a handle for work still running; barrier as a wait point for all ranks.
- An all-reduce of the stop flag makes all ranks stop at the same step (mechanism, from the script, not from a PyTorch doc).
- Inference: "Without that separation a checkpoint wait could sit in the same queue as training traffic" (labelled as reasoning in prose? No: stated plainly; treat as inference).
- NFS as the network file system used for shared storage; a claim class (SIGKILL, SIGTERM) explanations.
- Silent data corruption, NaN and held-out set definitions; "deterministic resume" definition.
- Memoryless failure definition; rendezvous as the meeting point; TCP store as a small key-value service; homogeneous nodes.
- A liveness probe as a check that tells Kubernetes a container is stuck.
- A prologue as a script Slurm runs before a job starts; an Xid as an NVIDIA kernel-log message for a GPU fault.
- A ring buffer for the flight recorder; TorchComms as a newer communications path (one line of prose; check the 2.15 distributed page).
- A SIG as a special interest group; a CRD as a CustomResourceDefinition schema; a claim as a storage request.
- Half a period as the average lost work when a failure lands at a random moment (follows from the Aupy waste model; verify wording).
- Two conventions "differ by a small offset, which matters only when C is not small compared with M" (derived from 2C; check).
- A "fake" as a stand-in program in the Slurm test; a rank as one GPU process.

ch05
- Gradient synchronization as averaging gradients across GPUs; a collective as an operation all GPUs take part in; AlltoAll as every-to-every exchange.
- Algorithm (pattern of movement) and protocol (packing and sync on the wire) definitions.
- SHARP as in-network reduction on supported switches; NVLS as the NVLink equivalent inside the node (the chapter cites both as "can change the data path"; the NVLS description needs a source).
- A plateau as the flat top of the bandwidth curve.
- `#wrong` as the count of elements that differ from the correct result.
- The root column names the rank holding the result for rooted collectives.
- NVSwitch as the switch chip connecting every GPU in a node; a rail as one NIC-to-switch path; HCA as the InfiniBand host adapter.
- Passive copper carries no power; active optical cable has electronics at each end (general).
- sysfs as the Linux interface for device state; ACS as the PCIe access control feature; `NCCL_NET_GDR_LEVEL` distance counted in PCIe hops.
- `dmesg` as the kernel log; subnet manager and rdma-core definitions; a trained width (x8 versus x16) explanation.
- RAS as NCCL's reliability and status service; DDP bucket as a group of gradients sent in one call.
- Communicator as the group of GPUs that run collectives together; a "silent fallback" description.
- Bisection as repeated halving; the reason bisection saves time (counting argument).
- Spread as how far repeats scatter; a gate as a pass or fail check with a written criterion.
- "Exit non-zero" as a failure code a pipeline reads.

ch06
- Xid as a driver error code in the kernel log; corrected error as a memory bit flip fixed by hardware.
- DCGM and dcgmi descriptions; Prometheus as the time-series store; Alertmanager as the routing component; `up` set to 0 on failed scrape (general Prometheus behaviour).
- Mode 0400 meaning owner-only read; ConfigMap and ClusterPolicy definitions; DaemonSet definition.
- Labels as Prometheus series tags; the `for` clause and `increase()` explanations.
- "A group is the set of GPUs DCGM watches together" was removed from the checkpoint answer; the section 1 text does not use it.
- The four signal groups paragraph (events, thermal and power, memory, interconnect) is the chapter's framing, not a source statement.
- InfoROM as the board's configuration storage; SRAM as on-chip memory; RMA as the vendor return process.
- SLO definition; post-mortem definition; alert fatigue as a term.
- Node condition as the status field on the Kubernetes node object; strategic merge patch definition; annotation definition.
- Envtest as a harness that starts a real API server and etcd; CRD as the API schema.
- Circuit breaker analogy; disruption budget definition; NoExecute and drain differences (control plane acts on its own clock; refusals from eviction are informational).
- Xid 74 "a bad link can be the fault of either end" (from the Xid 74 text, which says the remote end can cause it; check wording).
- "Hopper is the GPU generation that this chapter's counters are written against" (claim; check).
- "A Ready condition is separate from GPUHealthy, so the two should not interfere" (claim about Kubernetes node conditions; check).
- "The exporter will come back on its own, because the DaemonSet recreates it" (claim about the GPU Operator's exporter; unverified on a cluster).
- "Do not invent a rescan on the spot, because a rescan that goes wrong can hide evidence" (advice, no source).
- "The reset is a convenience... belongs in the next maintenance window" (advice, follows the catalog's "when convenient" wording).
- Game-day advice (announce the window, one person watches dashboards, one holds the stop button) is advice, not a source claim.
- "Silence is the dangerous state" and the three-line runbook order are framing.

## Unresolved

1. ch04, lab intro (section 12): the original sentence says "Steps 1 to 4 ran on the host for this chapter. Step 5 ran in a container." But step 3 is the CPU smoke test in a container, per the lab's own step 3 text and its "What was run here" line. Kept verbatim (facts stay exact). Owner decision: correct the numbering sentence.
2. ch04, exercise 1 sketch: "The factor is 2 times 15 over 16." has three numbers in one sentence (rule 9 asks for at most two). Kept as written to keep the numbers exact.
3. ch05, exercise 1 sketch: same issue, "The factor is 2 times 15 over 16." Kept.
4. ch05 and ch06 checkpoint questions that read as bare definitions. Locked by rule 5, listed here only.
   - ch05: Q4 "Define algbw." Q5 "Define busbw and why it exists." Q13 "What does PIX mean in the topology matrix?" Q7 "Which collectives use a factor of 1?" Q9 "What does the default of -c tell you?" (recall-style).
   - ch06: Q2 "Which counters are off in the 4.9.0 default file that this chapter needs?" Q5 "What are the classes in this policy, and who defines them?" Q6 "What does the catalog list as the immediate action for Xid 79, and for Xid 92?" Q7 "Why is Xid 61 not in the alert rules?" Q18 "How long is a level 3 run on an 8-GPU system?" (recall-style).
   - ch04: Q2 "Name the five failure shapes in this chapter." Q3 "What does the Young interval depend on?" Q14 "What does torchrun do when one worker fails?" Q16 "What is the default NCCL collective timeout in PyTorch 2.15 and what happens at expiry?" Q20 "Which JobSet fields bound and shape restarts?" (recall-style).
5. ch04 and ch06: the `(untested here)`-type span check is not affected. ch06 keeps the Sources line "Everything that needs GPUs... is untested here" (locked).
6. ch05 Section 5 flags table and section 4 log text: the phrase "NET/IB" and "NET/Socket" stay as the original wrote them.
7. ch06: the claim in "Ready condition" sentence and the DaemonSet recreation sentence need a cluster check (listed above under Needs source).
8. Honest-status word count: the original chapters have many "not run" phrases in locked step headings and locked Sources text. I did not add any new status sentences. The rule says to say it once; the locked headings make that impossible to fully honour without changing headings.
9. ch06 introduces the phrase "the detection window you are testing" (lab step 6); it is an explanation of the exporter gap, not a number.

## Notes on the rewrite

- Every section now opens with a situation, including the lab intros and the exercise and runbook openings. Locked headings (Outcomes, Prerequisites, Exercises, Checkpoint questions, Sources) keep their text.
- Tone: plain "you", one idea per paragraph, reasons before details. No exclamation marks. No new numbers in prose (the guard reports 0 new numbers in all three chapters).
- Where a number appears in the original and was restated in a sentence of my own, I kept the same value (e.g. 112 GB, 22.5 seconds, 16,384 GPUs, 0.90 efficiency, 121 seconds).
