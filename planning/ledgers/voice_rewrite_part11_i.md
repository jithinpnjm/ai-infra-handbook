# Voice rewrite ledger: Part 11 chapters 11.25, 11.26, 11.27

Scope: `docs/part-11-gpu-kubernetes/25-*.md`, `26-*.md`, `27-*.md` only. Not committed. `planning/EXTERNAL_EDITS.md` not edited (step 6 ignored per run instructions). Other chapters not touched.

## Words, gates

| File | Words before | Words after | Growth | rewrite_guard | chain_gate | Span check | Mermaid |
|---|---|---|---|---|---|---|---|
| 25-time-slicing-mps-and-oversubscription.md | 7982 | 10415 | +30.5% | 0 hard failures; new numbers 0; lost numbers 0; new code spans 0; lost 0; residue 5 to 4 | 0.0 | `{}` (lost) | `node tools/check_mermaid.mjs`: 776 diagrams, 0 failed |
| 26-choosing-a-gpu-sharing-model.md | 8736 | 11376 | +30.2% | 0 hard failures; new numbers 0; lost numbers 0; new code spans 0; lost 0 | 0.0 | `{}` (lost) | same run |
| 27-virtual-machines-on-kubernetes-kubevirt-kata-and-gpu-passthrough.md | 7276 | 10056 | +38.2% | 0 hard failures; new numbers 0; lost numbers 0; new code spans 0; lost 0 | 0.0 | `{}` (lost) | same run |

Word counts are `wc -w` on the whole file, before (HEAD) and after. The front matter, the checkpoint block (all 20 `<details>` blocks per chapter), the Sources and review notes block, all code fences, Mermaid blocks, tables, and every heading are byte-identical to HEAD. Growth is in the body prose only.

The span check used the run-instruction script with the chapter path. Its "lost" result is `{}` for all three chapters. Its "new" result lists spans that already existed in code fences or tables and now also appear in prose; the guard reports 0 new code spans for each chapter.

`npm run build` was not run (the batch instructions say no npm build).

## Method

- Body rewritten section by section with line-range splices against HEAD. Code fences, tables, Mermaid blocks and locked headings were never inside a replaced range. The splice script refused any range that touched a table row, a fence or an HTML line.
- Every section opens with a situation: "Picture...", "Suppose...", "Imagine...", or a concrete scene. Under the locked "Outcomes" headings in 26 and 27, the first sentence is a situation, followed by a plain paragraph of what the chapter walks through. The outcome bullets were removed. No "you will be able to" or "should be able to" remains.
- Exercises (6 per chapter, same count, same functions, commands and facts) were rewritten as one-question sentences. Multi-part asks were split. No nested (a)(b).
- Lab step lists and the bash/YAML blocks were kept byte-identical. Only the surrounding prose changed.
- Residue removed from body: "This is the output captured from this repository" (25, 26, 27 now "The block below shows what a passing run prints"); "The Volume 11 notes record" (26); "The Volume 11 capacity model" (26); "The commands below" honest status kept once in 27; "the book" phrasing not used.
- Honest status, one per chapter: 25 "...were not run on live hardware" (venue paragraph); 26 "...were not run on live hardware" (venue paragraph); 27 "The commands below were not run on a live cluster." (existing Commands intro, kept). The Step 1 headings still say "(tested here)" because the heading text is locked (see Unresolved).
- Bullets rewritten as "Label: sentence" with the bold removed in the reserves list (26), owners list (26), anti-pattern list (26), and the outcomes lists (26 and 27). This keeps at most one bold idea per section.
- Semicolon chains: none in new prose. chain_gate reports 0.0 for all three.
- No exclamation marks, no raw `<` or `{` in prose (the `<pod>`, `<name>` and `<id>` tokens are inside code spans already in HEAD).
- No new numbers. Every digit token in the new prose is a number that already appears in the original chapter. Spelled-out numbers only restate counts already present.
- Attribution kept as in HEAD: "As Josh Rosso et al. explain in *Production Kubernetes* Chapter 3" (27), "Brendan Gregg's *Systems Performance* Chapter 11" (27). No attribution was added.
- Analogies used (hostel room, hotel suites, penthouse, office kitchen, two tickets to one room, hotel suites share one building manager, bounce buffer as a staging area). None introduces a number.
- Walkthroughs added in 26 for the choice between MIG, Time-Slicing, MPS and vGPU: four situations in the decision-tree section, an embedding-service walk through the table rows, a layer walkthrough, a month-of-billing example, a three-question check on delivered efficiency, a class-migration canary, a capacity record example, a governance example, a review-a-design-with-screenshot check, and an exit-gate example. These restate table cells and the decision tree. No new product claim is made.

## Needs source (general explanations added in prose, no new facts)

11.25
- Multi-Instance GPU as the feature that cuts a card into isolated slices; CUDA as NVIDIA's programming platform; kernel as one piece of GPU work; Streaming Multiprocessors as compute-core groups; background proxy daemon; SM and warp meanings; HBM as the fast memory on the card and VRAM as its usual name; cgroup definition; fault domain; ConfigMap as a Kubernetes object that stores configuration text; device node as the file Linux uses to talk to a device; CUDA context and register state and time quantum; jitter as uneven delay; UNIX domain socket as a file-based local connection; CUDA stream as an ordered line of work; "exclusive process mode means only one process may hold the compute context, and that process is the MPS server" (consistent with checkpoint 5, but the definition is general).
- High-water mark as the highest level a value reaches; tenant as one workload using the shared card; regression check; telemetry; PyTorch as a Python library for neural networks; notebook as a browser coding page; headroom; starvation; noisy neighbor; binary admission ticket; scheduler as the component that picks a node; ResourceQuota as a namespace request limit; namespace as a grouping that the quota applies to; best-effort; staged rollout; rollback path and diagnostic bundle; ClusterPolicy as the GPU Operator's main configuration object; "contract" as a signed-off written agreement; allocatable as the count a node offers; patch as a small update; Pending state meaning.
- Procedure claim: the diagnostic order (host first, then pod) and the advice to re-read the lab script before running it on a shared node.
- Explanation of the MPS pipe and log directories (`CUDA_MPS_PIPE_DIRECTORY` as where clients find the daemon, `CUDA_MPS_LOG_DIRECTORY` as where the daemon writes messages) added in the Commands section 2 walkthrough.
- Advice: a green Pod status does not prove the sharing setting is active; a count that matches physical GPUs rather than replicas suggests the ConfigMap did not reach the node. Check the owner's view against a live node.

11.26
- Definitions: MIG GPU Instance and Compute Instance (in the boundary paragraph, as the terms the chapter already uses); SR-IOV as a PCIe feature that presents one device as several virtual functions; hypervisor as the layer that runs and separates virtual machines; guest domain; SSH as the encrypted remote login; UUID as the unique identifier of a GPU or slice; kubelet as the node agent; RMA; cordoned host; drain as the controlled emptying of a node; geometric fragmentation and hidden saturation (glosses of the table's own terms); Showback and Chargeback; Prometheus and kube-state-metrics roles; digest as the image fingerprint; canary as a small share of traffic to a new pool; Job as the run-to-completion object; envelope and anti-pattern as glosses; drift; timeout; ad-hoc.
- Rule of thumb: when host and cluster observations disagree, trust the host (closest to the hardware). Empty listings are findings. Both are general troubleshooting advice, not from the source.
- The decision-tree situations (notebook exploration, microservices owned by one team, a bank with a strict latency promise, Windows desktops in VMs) are illustrative. They follow the tree's branches. Owner should check that the bank and desktop examples match the intended policy.
- Walkthrough statements derived from table cells: "a time-sliced card can look fine on replica count while its memory is full" follows the Hidden saturation row.
- Advice to write the incident commands into notes as they run.

11.27
- Definitions: threat model; syscall; kernel as core of the OS; kernel panic; MicroVM; shim; launcher Pod; VFIO as the framework that hands a device to a VM; OCI as the image and runtime specifications; bundle; runc as the low-level container tool; content-addressable layers; image index as a list of platform choices; gRPC and Protocol Buffers; socket as a local file path; namespace as a label that separates containers; DaemonSet as one pod per matching node; unbind and bind; sysfs as the device file tree; QEMU as the VM emulator; VFIO group; vGPU as a virtual GPU slice; HIPAA as the US health privacy law; etcd as the Kubernetes database; taint as a node mark that keeps ordinary Pods away; crossbar port; IOMMU as the hardware unit that stops a device from reading unassigned memory; logic analyzer; DRAM; TEE as a protected CPU region; silicon-level encryption; enclave; quote; KMS; bounce buffer; Root of Trust; tool-calling sandbox.
- Procedure statements (not from the source): drain the node before changing the label; run the patch before the label takes effect; the node change is a planned change.
- The "(Mode A / Mode B) trades whole-card guarantee for density" sentence is a summary of the two modes already in the chapter.
- The Multi-Tenant threat-matrix analogy wording ("the hotel suites share one building manager, and that manager is the kernel") is a metaphor for the shared host kernel stated in the chapter.
- Note on the GPU-count sentence: "The count goes down by one for each VM" restates the chapter's "leaves seven" example.

## Unresolved

1. KNOWN OPEN ISSUE, 11.25: the time-slicing configuration field names may be wrong, and they are left exactly as written. The fields to verify against the installed GPU Operator release are: `version`, `sharing`, `timeSlicing`, `renameByDefault`, `failRequestsGreaterThanOne`, `resources`, `name`, `replicas`, the `any` key under `data` in the ConfigMap, and the patch path `spec.devicePlugin.config` (with `name` and `default`) in the ClusterPolicy patch. The matching `nvidia-cuda-mps-control` commands (`set_default_active_thread_percentage`, `set_default_device_pinned_mem_limit`) are also unverified here.
2. 11.25 ResourceQuota manifest (and the production-namespace paragraph): the hard values `"0"` and `"unlimited"`, and the unprefixed extended-resource names `nvidia.com/gpu` and `nvidia.com/gpu.shared` in the quota, need checking against the Kubernetes release in use. Owner should confirm that `unlimited` is an accepted quota value.
3. Locked Step 1 headings in all three chapters still say "(tested here)": 25 "Step 1: Run the self-checking time-slicing, MPS and oversubscription lab (tested here)", 26 "Step 1: Run the self-checking GPU sharing model selection and capacity lab (tested here)", 27 "Step 1: Run the self-checking KubeVirt, Kata and GPU passthrough lab (tested here)". This conflicts with the honest "not run on live hardware" status. Heading text is locked by rule 5, so the owner should decide whether to drop "(tested here)".
4. Locked Sources and review notes and locked checkpoint answers still contain "untested here", "Volume N", "Volume 11", "Volume 18", "the author's notes" and "captured" wording. Left as-is under rule 5. Owner decision whether to clean them.
5. Code-block comments and the output blocks still say "(untested here)", "(PK Ch. 3, untested here)" and "Volume 11 Ch 4 ..." lines. These sit inside locked code fences and were not changed.
6. 25 dcgm-exporter 4.9.0 version note (blockquote) kept as in HEAD. It was not rewritten, and its link is unchanged.
7. Growth: 25 is +30.5%, 26 is +30.2%, 27 is +38.2% (within the 40 percent ceiling).
8. `npm run build` not run (batch instruction). `node tools/check_mermaid.mjs` ran: 776 diagrams, 0 failed.
9. `planning/EXTERNAL_EDITS.md` not edited, per the run instructions.
