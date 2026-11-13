# Voice rewrite ledger: Part 11 chapters 11.10, 11.11, 11.12

Scope: `docs/part-11-gpu-kubernetes/10-*.md`, `11-*.md`, `12-*.md` only. Not committed. `planning/EXTERNAL_EDITS.md` not edited (per run instructions).

## Words and gates

| File | Words before | Words after | Growth | rewrite_guard | chain_gate | Span check | Fences / tail / headings / front matter |
|---|---|---|---|---|---|---|---|
| 10-secondary-networks-multus-sr-iov-device-plugin-and-rdma-device-plugin.md | 7787 | 10092 | +29.6% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 1 (typed term), lost 0, residue 4 to 3 | 0.0 | {} | 14 blocks unchanged, checkpoints and Sources identical, headings identical, front matter identical |
| 11-nvidia-network-operator.md | 8069 | 10354 | +28.3% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 6 to 5 | 0.0 | {} | 18 blocks unchanged, checkpoints and Sources identical, headings identical, front matter identical |
| 12-dynamic-resource-allocation-dra.md | 7751 | 9938 | +28.2% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 6 (typed commands and terms), lost 0 | 0.0 | {} | 16 blocks unchanged, checkpoints and Sources identical, headings identical, front matter identical |

Words are `wc -w` on the whole file. Checkpoints and Sources sections are byte-identical to HEAD, so all growth is in the body.

`python3 tools/check_mermaid.mjs`: checked 776 diagrams, 0 failed (run once, after all three chapters). `npm run build` was not run (orchestrator instruction: no npm build for this batch).

## Method

- Each body was rewritten section by section. Code fences, tables, Mermaid blocks and the lab output were copied byte for byte from HEAD through placeholders, so no code, data table or number was retyped.
- Every section opens with a situation (a stalled training job, a Pod stuck in Pending, a node that looks healthy, and so on).
- Outcomes lists in all three chapters were rewritten as plain paragraphs. No "you will be able to" remains.
- Exercises keep their count (6 in each chapter). Multi-part asks were split into single-question sentences. Chapter 11 and chapter 12 split into more sentences per item; the item count is unchanged.
- Lab step lists keep the same commands and counts.
- Honest status: one sentence above each lab says the cluster commands were not run. Code-comment "(untested here)" tags and the locked headings "(tested here)" were kept, since code and headings are not to be changed.
- Residue removed from body text: first-person and "book says" lines. Attribution to *Generative AI on Kubernetes* Chapter 3 in chapter 12 is the original attribution and was kept.

## Needs source (general explanations added to the body)

These are plain-language definitions or general claims added for the new reader. None is a new number. Each should be checked against a vendor doc or the gem books before the next review.

Chapter 11.10
- RDMA definition (one machine writes into another's memory without the remote CPU).
- Definition of a NUMA node, a VLAN tag, the loopback interface, and an overlay tunnel.
- Expansion of RoCEv2 (RDMA over Converged Ethernet, version 2) and of OFED (OpenFabrics Enterprise Distribution).
- North-South and East-West analogy (shop and back room).
- Stateless service explanation.
- BGP described as the protocol that internet providers use.
- eBPF described as small verified programs in the kernel.
- AWS VPC CNI note that managed-cloud GPU nodes often hit the subnet or ENI limit first.
- Hotel analogy for ADD, DELETE and CHECK, and the claim that leaked addresses fill pools when DELETE does not run.
- Bounce buffer, HBM, BAR1 and PCIe root complex definitions.
- Definitions of HCA, Partition Key, Subnet Manager, leaf switch, IOMMU passthrough, QoS, and MAC spoofing.
- PIX, PHB and SYS as the labels that `nvidia-smi topo -m` prints, from fastest to slowest.
- Ring and Tree AllReduce "rarely set by hand" remark.
- Lexicographic order of CNI config files.
- Claims that deciding the fabric late means rebuilding node pools, and that hardware checks take minutes while tuning the wrong layer takes days.

Chapter 11.11
- MFU expansion and definition; barrier explanation.
- Helm as a package manager; CRD and upgrade hook definitions; node pool definition.
- Magnum IO description; POSIX and page cache explanations; cuFile role (application-facing library).
- SNMP description; incast definition; LID definition.
- Mirror port explanation.
- Switch queue "two marks" analogy and ECN-before-PFC ordering explanation.
- Claim that a few percent below line rate is normal after headers.
- Claim that a reboot clears evidence.
- Claim that a fabric-wide Subnet Manager fault stops every port, and that RoCEv2 faults usually show as one path that stops.
- Claim that a short tier-based stall diagnosis points as described (Tier 1 to Tier 0 is cache or PCIe; Tier 2 to Tier 1 is PFS).

Chapter 11.12
- Framebuffer, MIG, and socket definitions; NVLink as a link between GPUs in one server.
- Meaning of "stable" for an API; RPC definition; Filter and Score phases description.
- NVML expansion (already in original as NVIDIA Management Library).
- Kueue and ResourceFlavor description.
- SharedInformer cache explanation; etcd role; relist definition.
- CSI Identity, Controller and Node service roles.
- NoExecute taint effect explanation; bind mount definition.
- RBAC, GitOps and admission webhook definitions.
- Sandbox definition; data gravity definition.
- Claim that under memory pressure the kernel reaches for Burstable and then other Pods first, and that Guaranteed requests equal limits is how the kubelet protects a Pod.
- `minMemory` as a floor compared against each device's memory.
- The crictl listing-first safety step (listing before the loop is a suggested practice, not an original instruction).

## Unresolved

- None blocking. All three chapters pass the hard guard, the chain gate reads 0.0, the span check is empty, and checkpoints, Sources, headings and fences match HEAD.
- Guard "new code spans" are typed commands or terms (chapter 10: 1, chapter 12: 6). Kept as code because they are typed.
- The "(untested here)" tags inside code comments remain. They are part of the code blocks, which must not change.
- Chapter 11 checkpoint 9 and body text were not reconciled further. Checkpoints are locked, so no change was made.
- `planning/EXTERNAL_EDITS.md` was not edited (orchestrator instruction).
