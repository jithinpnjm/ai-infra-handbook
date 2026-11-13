# Voice rewrite, Part 10 chapters 10.7, 10.8, 10.9 (batch c)

Not committed. Edits limited to the three chapter files below. EXTERNAL_EDITS.md not touched (per run instructions).

## Files and word counts (`wc -w`, whole file)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 07-gpu-generations-and-product-line (10.7) | 8652 | 11715 | +35.4% |
| 08-operating-gpu-nodes (10.8) | 7681 | 10682 | +39.1% |
| 09-the-nvidia-software-stack (10.9) | 10026 | 13974 | +39.4% |

Body (before the locked Checkpoint section) grew from 6894 / 6294 / 7668 to 9957 / 9297 / 11618. Locked tail (checkpoints and Sources) is unchanged at 1758 / 1387 / 2358 words.

## Gate results (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
  - 07: 0 hard failures; new numbers 0; lost numbers 0; new code spans 1 (`code/part10/gpu_generations_lab.py` path in the lab intro, a file path); lost spans 0.
  - 08: 0 hard failures; new numbers 0; lost numbers 0; new code spans 0; lost spans 0.
  - 09: 0 hard failures; new numbers 0; lost numbers 1 (the `Volume 03` / `Volume 04` labels in the removed prose attribution, intended residue removal); new code spans 6 (inline command or file names in new prose, such as `sort`, `echo $?`, `nvidia.com/gpu=all`); lost spans 0.
- `python3 tools/restore/chain_gate.py <file>`: 07 = 0.1, 08 = 0.2, 09 = 0.0 (all at or under the 0.2 target; exit 0).
- Span check (`git show HEAD:<file>` vs worktree, code fences removed): `{}` for all three files.
- `node tools/check_mermaid.mjs`: 776 diagrams checked, 0 failed (whole repo run).
- `npm run build`: not run (the run instructions say no npm build).
- Structure check: heading lines identical to HEAD; 20 checkpoint `<details>` blocks each; every fenced code block identical to HEAD in content and order.

## What changed (summary)

- Each section opens with a situation (a training job at 100 percent with no progress, a container that sees no GPUs, a fleet choosing cards for a rack).
- Outcome lists under "Prerequisites and outcomes" are now one plain paragraph in each chapter. No "you will be able to" lines remain.
- Lab intro and exercises use one question per sentence. Exercise count is unchanged: 07 has 6, 08 has 7, 09 has 7. Exercise 2 of 07 and exercise 4 of 08 keep the same parameter blocks. The 09 exercises had no parameter block in HEAD, and none was added.
- Tables, Mermaid blocks, code blocks, front matter, headings, checkpoints and Sources are unchanged.
- Body attribution residue (`Volume 03`, `V4 Ch 1` plain-text parentheticals, `my inference`, `(untested here)`, `Table 2.2` / `Table 3.3` labels) was removed from prose. Inline `nvidia-devops` spans were kept, since the span rule requires them; their surrounding plain-text chapter numbers were dropped.
- Honest status appears once per chapter above the lab (one sentence each: "These steps were not run on a live cluster" in 07 and 09; "The commands in section 4 need a real GPU node, and this lab does not run them" in 08).
- The 09 section 4 intro no longer carries the "marked ****" residue.

## Needs source (general explanations added in prose; not in HEAD)

Check these against an authoritative source or mark them as general background before the book is published.

10.7 (07):
- GPUDirect RDMA as a path that lets the NIC read and write GPU memory without a CPU detour (general definition of the feature).
- ECC as "error-correcting code memory that fixes single-bit flips" (general).
- HBM as "stacked memory packed beside the GPU die" (general).
- Interpreting the 64 GB/s and 900 GB/s rows as GPU-to-GPU bandwidth and not memory capacity (reading of the table).
- Optical reticle definition and multichip module definition (general).
- Cache coherence and "both dies see the same data" (general; the source says fully hardware cache-coherent).
- ASIC definition and NVSwitch as a router for NVLink traffic (general).
- Non-blocking crossbar definition (general).
- Rear-Door Heat Exchanger and Direct-to-Chip cooling descriptions (general).
- Mezzanine definition and "bolt horizontally" (general).
- `x16` as the widest common PCIe slot width (general PCIe fact; no number added).
- BMC, Redfish and IPMI definitions (general).
- Underflow definition (general).
- Transformer Engine as the unit that picks precision layer by layer (general reading of the source's description).
- KV cache definition as attention data for every token of every active conversation (general).
- Activations as temporary tensors in a forward pass (general).
- The gate reasoning in 5.3 that Candidate C wins because it has fewer NVSwitch hops and less power and footprint (reasoning from the original verdict; the source gives only "2 GPUs instead of 4").
- Advice to drain the node before MIG mode changes, and to run the GPU reset in a maintenance window (general practice).
- The scorecard reading that the two memory rows are the largest share (reading of the table; no number added).

10.8 (08):
- BMC definition as the controller that watches sensors and drives chassis fans (general).
- Redfish as the standard web interface to BMC data (general).
- Cordon and RMA definitions (general Kubernetes and vendor process).
- NUMA node definition and advice to pin data loaders to the matching node (general systems practice).
- Time to first token and inter-token latency definitions (general LLM serving terms).
- P99 definition (general).
- Persistence-mode cost "a few extra watts" (original said "a few extra watts"; kept).
- A probe timeout can make Kubernetes restart a healthy pod (general Kubernetes liveness behaviour).
- Topology matrix and peer-to-peer read/write definitions (general nvidia-smi behaviour).
- Explanation of the PSU 1.3 factor as headroom for spikes above average draw (rule-of-thumb reasoning).
- Sampling test for bursty workloads: the reading of "stable, borderline and oscillating" is the chapter's own wording; the explanation of why a 30-second poll misses a short burst is general.

10.9 (09):
- Ring 0 as the most privileged processor level (general).
- Mount namespace and PID namespace definitions (general Linux container terms).
- A character device as a file in /dev that stands for a control stream to a driver (general Linux).
- ioctl as the standard Linux control call to a device driver (general Linux).
- Zero-copy GPUDirect RDMA description (general; source says "zero-copy").
- Eager mode and TorchDynamo / AOT Autograd / TorchInductor role descriptions (general PyTorch; the source names the components).
- Kernel fusion as merging small operations to move data through memory fewer times (general).
- Domain-specific language definition (general).
- PTX as a stable intermediate language not tied to one chip, and SASS as the chip's real instruction set (general NVIDIA toolchain description).
- Fatbinary as one file carrying several compiled versions (general; the source defines it as embedded native CUBINs plus optional PTX).
- Compute capability as the version number of the instruction set (general).
- JIT meaning just-in-time compilation at load (general).
- Dynamic linker and LD_LIBRARY_PATH search order (general Linux).
- NGC as NVIDIA's container catalog (general).
- Declarative specification definition (general).
- containerd and CRI-O as the two runtimes Kubernetes commonly uses (general).
- Drop-in configuration file definition (general systemd and containerd practice).
- SR-IOV as PCIe feature for virtual functions (general PCIe).
- Slurm as a batch scheduler for HPC clusters (general).
- cmsh as the BCM command-line shell (general BCM).
- Wheel as the packaged form of a Python library (general).
- Warmup probe advice (general serving practice).
- Host PID sharing lets a container see every process on the node, and the security trade it implies (general Kubernetes).
- Virtual machine versus container kernel description (general).
- Ten-pod RAM arithmetic in the incident table is reproduced from the source numbers only (no new arithmetic added in the text).

## Unresolved

1. Locked tails (Checkpoints and Sources) still contain residue that the run rules keep unchanged: 07 Sources has `(untested here)` and "my inference" wording and a "Volume 04" label; 09 Sources has "my inference", `(untested here)` and "Volume 03" / "Legacy Volume 04" labels; 08 Sources has volume-number labels in the field-notes row. Owner decision needed on whether the locked tails should be cleaned in a later pass.
2. 10.7 keeps the two loose hardware claims the owner flagged, unchanged: the B200 "180 GB usable vs 192 GB" wording, and the "PCIe envelope restricts power to half of SXM" sentence in section 3.1. Both are exact in HEAD and were left as they are.
3. 10.9 growth is 39.4 percent, close to the 40 percent ceiling. Trimming any further would cut explanation that the rules ask for, so it was left as is.
4. 10.9 section 4 commands reference `/etc/containerd/config.toml`, `nvidia-ctk`, `cuobjdump` and `lspci`; these are kept as in HEAD. They were not run on a live node (stated once above the lab).
5. The 10.8 `dcgm-exporter 4.9.0` version note is kept verbatim (it is a fact note with a link). It is the only version note in the three chapters.
6. Cross references kept as text: chapter 10.21 (10.8), chapter 12.18 and 15.3 (10.8), chapter 10.10 (10.9), chapters 5.2 and 9.12 (10.9), and the 17.4 link in 10.8 (the link target was not checked in this run).
