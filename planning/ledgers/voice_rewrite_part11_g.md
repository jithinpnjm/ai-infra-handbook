# Voice rewrite ledger: Part 11 chapters 11.19, 11.20, 11.21

Scope: `docs/part-11-gpu-kubernetes/19-*.md`, `20-*.md`, `21-*.md` only. Not committed. `planning/EXTERNAL_EDITS.md` not edited (step 6 ignored per run instructions).

## Words, gates

| File | Words before | Words after | Growth | rewrite_guard | chain_gate | Span check | Mermaid |
|---|---|---|---|---|---|---|---|
| 19-the-run-ai-platform-view.md | 8267 | 11532 | +39.5% | 0 hard failures; new numbers 4 (150, 250, 500, 600, restated from the Professor A/B arithmetic in the locked spec block; see Needs source); lost numbers 0; new code spans 1; lost 0 | 0.0 | `{}` | `node tools/check_mermaid.mjs`: 776 diagrams, 0 failed |
| 20-scheduler-comparison-guide-kai-kueue-volcano-yunikorn-and-slurm.md | 7464 | 10242 | +37.2% | 0 hard failures; new numbers 0; lost numbers 0; new code spans 0; lost 0 | 0.0 | `{}` | same run |
| 21-pcie-iommu-vfio-and-device-passthrough.md | 8944 | 11541 | +29.0% | 0 hard failures; new numbers 0; lost numbers 0; new code spans 1; lost 0 | 0.0 | `{}` | same run |

Word counts are `wc -w` on the whole file, before (HEAD) and after. The checkpoint questions and Sources and review notes are locked and were spliced byte-for-byte from HEAD, so the growth is in the body only.

`npm run build` was not run (the run instructions say no npm build for this batch).

## Method

- Body rewritten section by section. Headings, front matter, title tables, all code fences, Mermaid blocks, and data tables were kept exactly. Code blocks and tables were re-inserted from HEAD by script, so they match byte-for-byte.
- Checkpoint questions (`<details>` blocks) and Sources and review notes were restored from HEAD unchanged (rule 5).
- Each body section opens with a situation or a picture of one. Under the locked "Outcomes" headings, the first sentence is a situation, followed by a plain paragraph of what the chapter walks through. The Outcomes lists in 11.19, 11.20 and 11.21 were rewritten as paragraphs, with no "you will be able to".
- 11.20 (comparison chapter): every table cell is unchanged. Plain-language "when each choice wins" walkthroughs were added after the matrix (no new product claims; each statement follows from a table cell or the flowchart).
- 11.21 (hardware/virtualization): everyday analogies used, with no new numbers: a building's door guard for the IOMMU, a hallway and lending desk for IOMMU groups and VFIO, two office buildings joined by one bridge for NUMA, roundabout and highway for PCIe switches, and housing for OS containers, VMs and MicroVMs.
- Exercises: 6 per chapter, same counts and same commands, paths and figures. Multi-part asks were split into one-question sentences. No nested (a)(b).
- Honest status: 11.19 "The cluster commands in this chapter were not run on live hardware." (Venue and scope); 11.20 "None of them was run on a live cluster" (Commands intro) and "The cluster and Slurm commands were not run on live hardware" (Venue and scope); 11.21 "The host commands shown earlier were not run on live hardware".
- Residue removed from body: "The output below was captured from this repository" (19, 20) and "Captured output from this repository" (21) became "the block below shows what a passing run prints"; "as the source gives it" removed (20); "The source compares" rewritten (20).
- Bullets and lists: 20 Prerequisites rewritten as plain bullets without "You should". 

## Needs source (general explanations added in prose, no new facts)

11.19
- Custom resource, control plane, REST API, RBAC, namespace, persistent storage provisioning, scope, Pod, gang scheduling, preemption, license (Apache 2.0 meaning), single sign-on, showback, self-service templates, YAML.
- Session pipeline stage meanings (preempt, reclaim, staleness, over-quota, allocate, consolidate); pod group, bind request, topology as general terms.
- MIG, device-plugin time-slicing, CUDA Multi-Process Service, vGPU as one-sentence definitions; over-quota borrowing; parking-garage analogy.
- SIGTERM and SIGKILL as standard Linux process signals; noisy neighbor; blast radius; privilege escalation; BMC as a small management controller that stays on when the server is off; the BMC sits in the Management plane (explanation of the chapter's own plane list).
- DGX SuperPOD and DGX GPU servers described as "a large group of DGX GPU servers that the design treats as one building block"; fine-tuning, inference, pre-training; Slurm login node; NFS; PXE boot; Redfish; OFED; double-bit ECC.
- The gate-ordering explanation (later gates do not run after an early failure).

11.20
- CNI overlay; `kube-scheduler` role; cohort; session cycle; pod group; slurmctld and slurmd roles; collective rendezvous; NCCL; optical transceiver; spinlock; straggler; leaf-spine network; RDMA; bridge; root daemon.
- Placeholder pods; resource flavor; local queue label; suspended job; NVLink domain.
- OCI image format; squashfs; namespaces; cgroups v2; SPANK plugin; Lustre; Prolog and Epilog roles; drain and requeue; ECC; DCGM and dcgm-exporter role; Xid as numbered kernel-logged GPU errors; Day-2 runbook; cutover; fault injection; failure domain; UFM; Solutions Architect methodology stage explanations (wording only).
- Stage descriptions of the six-stage methodology kept their original names; only plain glosses for "cutover" and "Day-2 runbook" were added.

11.21
- PCIe lanes, Root Complex, Host Bridge, Transaction Layer Packet, Requester ID, Bus:Device.Function, GPUDirect RDMA, Peer-to-Peer, NUMA, UPI and xGMI as links, IOTLB, ACS (Access Control Services), MMU and TLB, page walker, CR3, shadow tables, hypercall, Ring 0 and Ring 3, root mode, VM-EXIT, balloon driver, stolen CPU time, `bpftrace`, Ftrace, NVMe, OverlayFS, `seccomp-bpf`, Kata `runtimeClassName`, CFS share as a weight, cpuset, nonvoluntary context switch, kernel panic, blast radius.
- Hypervisor descriptions of Domain-0 and Isolated Driver Domains as one-sentence glosses; user-space hypervisor and user-space emulator definitions; housing analogy for the three runtime models.

## Unresolved

1. 11.21 heading "### Step 1: Run the self-checking PCIe, IOMMU, VFIO and passthrough lab (tested here)" kept because heading text is locked. It conflicts with the honest "not run" status. Owner should change the heading to drop "(tested here)".
2. Sources and review notes in all three chapters still contain "untested here", "Volume N", and "the book's" wording. These are locked by rule 5. Owner decision whether to clean them.
3. 11.19 "new numbers" 150, 250, 500, 600 are not new facts. They restate the Professor A and Professor B arithmetic that already appears in the locked spec block and the lab output, used in prose for the walkthrough. Left in place; the guard flags them only because the prose repeats them.
4. 11.19 growth is +39.5%, close to the 40 percent ceiling. Trimming a further paragraph would bring it nearer the +30 percent aim if the owner prefers.
5. 11.21 growth is +29.0%, just above the floor.
6. Checkpoint answers were not rewritten (locked). Some answers in 11.19 and 11.20 still use phrasing from the original, which is acceptable under rule 5.
7. `npm run build` not run (no npm build for this batch).
