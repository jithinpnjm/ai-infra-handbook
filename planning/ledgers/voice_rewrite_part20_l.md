# Voice rewrite ledger: Part 20, chapters 34 to 36 (run l)

Scope: `docs/part-20-nebius-sre-interview/34-nebius-hardware-data-centers-and-the-gpu-fleet.md`, `35-the-nebius-api-surface-grpc-cli-sdks-iam-and-terraform.md`, `36-managed-kubernetes-and-soperator-how-nebius-runs-kubernetes-and-slurm.md`. Not committed. `planning/EXTERNAL_EDITS.md` not edited (step 6 ignored per run instruction). `npm run build` and `node tools/check_mermaid.mjs` not run (run instruction: no npm build; Mermaid blocks are byte-identical to HEAD). Only the three chapters and this ledger were touched.

## Method

Each chapter was rewritten whole from its `HEAD` version, section by section. Front matter, the H1, every heading, every fenced block (yaml, text, python, Mermaid), every table, all `<details>` checkpoint blocks, "What I could not find", the Sources and review notes tail and the Verification log are byte-identical to HEAD. Teaching prose was added around the locked content. Each section opens with a situation. Original first-person verification lines ("I ran steps 1 to 4", "I did not run it", "was not run") are kept as the honest status.

## Word counts (`wc -w`, HEAD vs worktree)

| File | Before | After | Growth |
| --- | --- | --- | --- |
| 34 hardware, data centers and the GPU fleet | 5146 | 6876 | +33.6% |
| 35 the Nebius API surface | 5597 | 7536 | +34.6% |
| 36 managed Kubernetes and Soperator | 4981 | 6871 | +37.9% |

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three.
  - 34: `words 5146 -> 6876, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 9->9`
  - 35: `words 5597 -> 7536, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 9->9`
  - 36: `words 4981 -> 6871, new numbers 0, lost numbers 0, new code spans 1 lost 0, residue 7->7`
- `python3 tools/restore/chain_gate.py <file>`: exit OK on all three, 0.0 per 1000 words each.
- Mandatory inline-span check (HEAD vs worktree, fenced blocks excluded): `{}` for all three.
- Structure, HEAD vs worktree: fenced blocks identical, table lines identical, `<details>` blocks identical, heading lines identical, Sources and review notes tail identical on all three.
- Banned-pattern scan: no `!`, no "will be able to", no "should be able to", no "In this chapter", no "you will learn", no "By the end". Semicolon count equal to HEAD on all three. No `$` math.

## Number and fact discipline

- No digits were added to prose. Two new digit tokens in the first draft of 34 (`03:00`, which was rewritten to "in the middle of the night") and one in 36 (`1.36` explanation, removed) were caught by the guard and reverted.
- A spelled-out "a thousand" in 34 was replaced with "every process in the job". 35 had "ten minutes" in the opening, replaced with "since the start of the run". Both are word numbers that were not in the original.
- No Nebius fact was added. Every new sentence is either a restatement of an original fact or a general explanation (listed below).

## New code spans (explained)

- 36: six backticked terms that were plain text in the original prose now carry backticks: `NotReady`, `slurmctld`, `slurmd`, `pivot_root`, `slurm.conf`, `CLOUD`. All are things typed or seen on screen. The guard counted 1 new span. Revert these if strict span parity is wanted.

## Needs source (general explanations added, not Nebius facts)

These are textbook explanations of general technology. They are not attributed to any book or Nebius page. Check them before the owner signs off.

34 (hardware, data centers, GPU fleet):
- A die is the single piece of silicon that does the computing inside a GPU. NVLink is NVIDIA's high-speed GPU-to-GPU link. A PCIe connection is the slower bus that attaches a card to a host. A NIC is a network interface card.
- An inlet is where cooling air or coolant enters a server, so an inlet rating is the highest temperature the box is built to accept.
- A toolless rack lets a technician swap a part without a screwdriver, which shortens repair time.
- HGX is NVIDIA's board design for eight GPUs. NVSwitch is the chip that connects GPUs inside a node. An NVLink domain is a set of GPUs that talk over NVLink as one large machine.
- A tray is the sled that holds GPUs and CPUs and slides into a rack as one piece.
- Scale-out network, rail, leaf and spine roles in a rail-optimised fabric. Oversubscription means uplink capacity below downlink capacity, so traffic can queue. ECN is explicit congestion notification.
- A collective runs at the speed of its slowest link.
- N+1 redundancy: the node runs on fewer supplies than it has.
- Direct liquid cooling runs coolant through cold plates on the chips.
- Xid is NVIDIA's family of GPU error messages written by the driver to the kernel log. This is a general description, and the chapter's own text only names Xid codes.
- A prolog runs before a job and an epilog after it.
- NVMe is a fast flash-storage protocol. All-flash means no spinning disks. Metadata means the file information (names, sizes, directories) rather than file contents.
- A rank is one process in a distributed job.
- Bare metal means running directly on the physical machine, as opposed to a virtual machine on a hypervisor.
- Load shedding means turning away the least important requests. A canary is a small first batch that gets a change. A soak period is time under load before trust. RMA is return merchandise authorisation. NCCL is NVIDIA's collective communication library. A communicator is the GPU group a collective spans. Version skew means different versions running side by side.

35 (Nebius API surface):
- Protobuf is a binary message format defined in `.proto` files. gRPC is a remote procedure call system over HTTP/2. REST and SDK are described in plain words.
- Immutable means fixed once set. Optimistic concurrency means sending back a version so a stale write is refused.
- Control plane versus data plane. IAM is identity and access management. Port 443 is standard HTTPS.
- Alpha means an early version whose shape may still change.
- Backoff and jitter. A storm means a burst of extra requests. A retry budget caps retries as a fraction of calls.
- Bearer token, UUID, interceptor (hook order), OIDC, JWT, RFC 8693 (token exchange standard), least privilege.
- Token bucket (spare permission that refills), quota as a ceiling, rate limit as a speed cap.
- Terraform plan versus state. Write-only fields.
- Request ID versus trace ID, and joining audit events on a shared ID.

36 (Managed Kubernetes and Soperator):
- Controller and reconcile loops. Roles of API server, scheduler, autoscaler, controller manager and etcd. The reason a manual edit to a managed node is overwritten.
- CoreDNS and Cilium roles. Taints and labels as scheduler selection. NVIDIA Container Toolkit. MIG (multi-instance GPU). Live migration. SLA as a promised time.
- Node Problem Detector as a daemon that reports node problems. DaemonSet as one pod per node.
- Minor version and skew. Why the control plane leads an upgrade.
- Max unavailable and max surge as rollout limits.
- kubelet and admission. PodDisruptionBudget. emptyDir. tmpfs and cgroup. PAM. SPANK and `pivot_root` as Slurm plugin mechanics. StatefulSet and PVC. Munge as the Slurm authentication service. Toleration as a time-limited pod stay on a bad node. Ordinal. Topology data. Passive check. Reservation as a holding area. Series in a metrics store. All-reduce as the gradient-sum collective. Submount. CRD and Helm render.
- The claim that the control plane must be upgraded before node groups because newer components expect older ones is general Kubernetes practice, not a Nebius statement.

## Unresolved

- 36: six new backticked terms (see above). Owner decides whether to keep.
- 34 and 35: none.
- Lab steps in all three keep their original commands, counts and expected results. Step 4 of 34 keeps "was not run". Step 5 of 35 and step 5 of 36 keep "not run".
- Original residue hits are unchanged in count (9, 9, 7). The one new "I did not" phrase in 35 was rewritten to avoid a first-person residue match.
- Mermaid check and `npm run build` were not run (run instruction: no npm build). The Mermaid blocks are byte-identical to HEAD.
