# Rework ledger: W5 (1.27, 1.23, 1.26, 1.22, 2.2, 2.19)

Gates run on all six: chain_gate (0.0 to 0.3), summary counts unchanged (20 each), no exclamation marks in prose, no raw `<` or `{` in prose, no stray `$`. language_audit still lists 1.22 (2 warnings: backtick density and semicolons, inherent to a sysctl/command chapter; not compared with a before-count because git is off limits).

## 2.19 Queuing, QoS, ECN, PFC, DCB (light edit)
- Fixed: 64-byte packet behind 9,000 bytes waits about 140 times (0.72 ms / 5.12 µs), not 14. Verdict: FIXED. Evidence: 9,000/64 = 140.6; 64 B at 100 Mb/s = 5.12 µs.
- "1:1 overprovisioning" now "non-oversubscribed, ratio 1:1". FIXED.
- Added "Where the thresholds live" (PFC on ingress priority-group buffer, ECN on egress queue, shared buffer with dynamic alpha) and a credit-based flow control plus lossy-RoCE paragraph; ordering sentence reworded. General switch design knowledge, flagged in review notes.
- SFC reworded to IEEE P802.1Qdw project, "still under development". UNRESOLVED: current project status not re-checked online.
- CSIG bullet split in two. Spectrum-X mentioned in one sentence (vendor production alternative), no numbers.
- Removed book citations in summaries and an exercise, inline "untested here", "2-bit vs 1-bit" ECN inconsistency in Q17, raw `<` in prose, and the sources line's "0.05 ms" (wrong; 64 B takes 5.12 µs).

## 1.22 Kernel modules, DKMS, sysctl
- DKMS groups six vs five: FIXED, six everywhere (Q6 text rewritten to match the list, exercise 3, summary).
- ptrace_scope: FIXED, row says 1 is the hardened default, 0 or CAP_SYS_PTRACE needed for Open MPI/UCX CMA single copy.
- Cross-reference "chapter 6.x on BCM and Redfish": FIXED (Part 7 Redfish, Part 8 BCM).
- PYTORCH_ALLOC_CONF: ALREADY CORRECT in direction; verified: PyTorch 2.15 CUDA notes (docs.pytorch.org, read 2026-11-12) name PYTORCH_ALLOC_CONF primary and PYTORCH_CUDA_ALLOC_CONF a backward-compatible alias; the 2.9 notes mention only the old name. Text now says so.
- Removed leaks ("operations notes (Volume 10)", "book's examples"), "(flag...)" markers, MLPerf "< 2%" claim (unsourced), fatbin and clock/allocator bullets cut to short pointers to 10.8, 10.9, 14.8. Added kernel ABI/kABI explanation, GPU Operator precompiled-driver kernel matching note, Ubuntu signed-module note (UNRESOLVED: re-check against current Ubuntu/NVIDIA docs). Outcomes said "six things" for seven bullets: now seven.

## 1.23 Performance methodology
- Removed Gregg attributions from body and Q4/Q14, vocabulary table replaced by a paragraph, "(adapted)" dropped, inline untested tag removed, "Parts 7 and 8" for GPU specifics corrected to Parts 9 and 10, `$/million tokens` table cell changed (stray `$` could parse as math).
- Added "When the method itself fails" (missing counters, interval hides bursts, observer effect, premature stop, GPU-Util meaning). Case 1 already is a GPU-cluster worked example.

## 1.26 KVM, QEMU, libvirt
- Removed "Gregg's Config A/B" framing everywhere (body, Q2, exercise 1, sources); Mermaid subgraph labels lost the "Config A/B:" prefix (only label text changed).
- Added KubeVirt subsection (VM in a pod, VFIO passthrough, pointers to 11.21 and 11.27); chapter intro now states the GPU passthrough goal. Cross-reference "Part 5 (KubeVirt and Kata) and Part 7 GPU virtualization" corrected to Part 11. GPU Operator label names deliberately not stated (UNRESOLVED, release-dependent).
- Not done: further restructuring of sections 1-7 around GPUs; sections kept.

## 1.27 Cloud computing and virtualization internals
- Cut about 20 percent (13.2k to 10.6k words), not the 50 percent the review asked: removed database families, detailed SaaS/PaaS/IaaS, deployment models, front/back end, technology history, "Building an HPC cluster" (duplicate of storage and placement), "Other types"; condensed hardware virtualisation recap, microVMs, orchestration. Checkpoint answers (fixed 20) still cover vertical/horizontal scaling, autoscaling, storage, so those short sections stay. Further cuts need checkpoint changes.
- Added "Why a cloud GPU node behaves differently" (noisy neighbours, virtual topology/NUMA, passthrough and SR-IOV, nested virtualisation). UNRESOLVED: provider-specific nested virtualisation support not verified.
- Removed Gregg, Supercomputers for Linux SysAdmins, Zhumatiy references from body, exercises and summaries.

## 2.2 How networks work
- Opening rewritten as one packet story with three defined terms (header, encapsulation, layer); acronym list removed. Circuit switching, packet switching, ATM compressed; SDN/OpenFlow history not expanded. Checkpoint Q1-Q2 unchanged. "Parts 8 and 9" for AI fabrics corrected to 9 and 12. Book citations removed from exercises and Q3.

## Neighbouring notes
- 1.23 mentions "chapter 1.28" for tuning; not verified. 2.19 sources cite chapters "2.28-2.29" and study items; left alone.
