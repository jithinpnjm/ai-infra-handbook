# Voice rewrite ledger: Part 11 chapters 11.1, 11.2, 11.3

Scope: `docs/part-11-gpu-kubernetes/01-*.md`, `02-*.md`, `03-*.md` only. Not committed. `planning/EXTERNAL_EDITS.md` not edited (per run instructions).

## Words, gates

| File | Words before | Words after | Growth | rewrite_guard | chain_gate | Span check | Mermaid |
|---|---|---|---|---|---|---|---|
| 01-why-kubernetes-needs-a-gpu-platform-layer.md | 8905 | 11340 | +27.3% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.1 | {} | 2 diagrams, 0 failed |
| 02-device-plugin-container-toolkit-cdi-and-runtime-classes.md | 9179 | 11617 | +26.6% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 6 (typed or on-screen terms), lost 0 | 0.0 | {} | 3 diagrams, 0 failed |
| 03-node-feature-discovery-and-gpu-feature-discovery.md | 8334 | 10634 | +27.6% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 5 (typed or on-screen terms), lost 0 | 0.0 | {} | 2 diagrams, 0 failed |

Word counts are `wc -w` on the whole file, before (HEAD) and after. Checkpoints and Sources sections are unchanged, so all growth is in the body.

Lab re-runs (outputs match the chapter summary lines): 11.1 `gpu_platform_layer_lab.py` 25/25; 11.2 `device_plugin_toolkit_cdi_lab.py` 26/26; 11.3 `nfd_and_gfd_lab.py` 26/26.

## Method

- Body rewritten section by section. Each chapter's body was assembled from prose plus the original code blocks, tables, blockquote and Mermaid blocks, copied byte for byte. Headings were checked to match the original in order and text (38, 50 and 38 heading lines).
- Front matter, title table, checkpoint questions and Sources and review notes were not touched.
- Every section now opens with a situation (an on-call alert, a maintenance window, a node that looks healthy, and so on).
- Outcomes lists in 11.2 and 11.3 were rewritten as plain paragraphs without "you will be able to".
- Exercises: 11.1 has 6 exercises, 11.2 has 6 numbered exercises, 11.3 has 6 numbered exercises plus the original inputs table (kept as a data table). Multi-part asks were split into single-question sentences where that kept the same facts.
- Lab step lists keep the same commands and the same counts.

## Needs source (general explanations added in prose, no new facts)

11.1
- gRPC as the remote procedure call protocol used by kubelet and device plugins.
- Kernel headers as the definitions a module needs to compile against a kernel version.
- Extended resource as a named resource that a plugin adds outside CPU and memory.
- NVLink and NUMA, described in one sentence each.
- Secure Boot as the firmware feature that refuses unsigned kernel code.
- `lsmod` and `dmesg` one-line descriptions.
- Time-slicing has no hard memory wall per Pod (the sentence follows from the memory math in the chapter, but the claim itself is general).
- MIG as hardware-isolated slices; canary node; drain and uncordon.
- Activations and cache need headroom beyond weights.

11.2
- CNCF as the Cloud Native Computing Foundation, the group that hosts Kubernetes.
- CUDA context; DMA; `ioctl()`; UNIX domain sockets; ABI (application binary interface).
- CRI as the Container Runtime Interface; runc; OCI pre-start hook; bind mount; entrypoint.
- PTX as portable intermediate code and the JIT step that compiles it.
- Dynamic linker and `LD_LIBRARY_PATH` role.
- Multi-Process Service as NVIDIA's mechanism for concurrent GPU sharing.
- Tegra as the NVIDIA platform for embedded Jetson-class boards (flag description in the values section).
- SLA, predicate, state machine, Helm values file, Xid as the driver's fault codes.

11.3
- BF16 and FP8 as compact number formats with tensor-core support.
- HBM as the fast memory package beside the GPU die.
- CPUID as the instruction set reporting processor features; vendor ID as the PCI manufacturer number.
- InfiniBand as the high-speed fabric connecting GPU nodes.
- SELinux as the Linux security policy layer.
- Kustomize, Helm and Terraform one-line descriptions.
- Taint semantics (NoSchedule as a node rule) and the guest-list and door-policy analogy.
- Framebuffer as the memory the driver reports as usable.
- RBAC as the access control model for Kubernetes objects.

## Unresolved items

1. Headings keep their original text, including "(untested here)" and "(tested here)", because heading text is locked. The code-block comments keep "(untested here)" because code blocks are locked. Prose uses one honest "not run" sentence per chapter (11.1 above section 7, 11.2 in the Venue and scope paragraph and Step 2 runbook heading, 11.3 in the Venue and scope paragraph).
2. 11.3 says "seven-layer GPU platform model" in Prerequisites. 11.1 describes six layers. The original 11.3 wording is kept. Needs an owner decision on which count is right.
3. 11.1 section 2.2 said "three tainted workload pools" but described one untainted general pool. Prose now reads "three workload pools, two of them tainted" (same numbers, no new facts).
4. 11.2 had an unclear phrase "the production fleet chapter 4" with no antecedent. Rewritten as "a production fleet of 40 GPU worker nodes" (same number).
5. 11.1 removed the "Volume 10 Chapter 2" attribution in section 4.1 and replaced it with a plain description of the incident on `gpu-node-22`. The Sources section still carries the original attributions.
6. 11.1 dcgm-exporter 4.9.0 blockquote kept verbatim (it is a blockquote atom with a link and numbers).
7. 11.2 attribution "Chapter 3, Example 3-13, of *Generative AI on Kubernetes*" and 11.3 "Chapter 10 of *Kubernetes for Generative AI Solutions*" kept as the original attributions.
8. 11.2 "The output below was captured from this repository" was rewritten to "shows what a passing run prints", because the capture claim could not be checked.
9. The 11.3 exercise inputs table is kept as a data table, and the exercises refer to it.
10. The lab in 11.2 and 11.3 uses `Lab` and `Summary` lines copied from the chapter output; they match the current lab run.
