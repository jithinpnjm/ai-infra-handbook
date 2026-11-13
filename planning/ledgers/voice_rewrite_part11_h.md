# Voice rewrite, Part 11 batch H (chapters 11.22, 11.23, 11.24)

Scope: `docs/part-11-gpu-kubernetes/22-sr-iov-for-nics-and-gpus.md`, `23-nvidia-vgpu-architecture-profiles-and-licensing.md`, `24-mig-in-depth.md`. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (per owner instruction). Other chapters untouched.

Method: prose rewritten and extended in place, section by section. Front matter, title, metadata table, headings, every code fence, every data table, the Mermaid blocks, all checkpoint questions and answers, lab output blocks and the Sources and review notes section are byte-for-byte from HEAD. Exercises and the Outcomes list were rewritten as short single-question sentences (same six exercises per chapter) and a plain paragraph (no "you will be able to").

## Word counts (`wc -w` on the whole file)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 11.22 SR-IOV for NICs and GPUs | 8042 | 10280 | +27.8% |
| 11.23 NVIDIA vGPU: architecture, profiles and licensing | 7852 | 10066 | +28.2% |
| 11.24 MIG in depth | 8504 | 10964 | +28.9% |

## Gates (run, output seen)

- Inline code span check (`/private/tmp/.../scratchpad/spancheck.py`, same logic as the owner snippet): `{}` for all three files.
- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures for all three.
  - 11.22: words 6745 -> 8983 (body), new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 11.23: words 6197 -> 8411 (body), new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 11.24: words 6747 -> 9207 (body), new numbers 0, lost numbers 0, new code spans 0, lost 0.
- `python3 tools/restore/chain_gate.py <file>`: 11.22 = 0.0, 11.23 = 0.0, 11.24 = 0.0 per 1000 words (target 0.2 or lower).
- `node tools/check_mermaid.mjs`: checked 776 diagrams, 0 failed (repo-wide run; no Mermaid text was edited in these chapters).
- `npm run build`: not run (owner instruction for this batch: "No npm build").
- Checkpoint count unchanged in each file (20 each, form `<details><summary>N. ...</summary>`).

## Needs source (general explanations added in the body)

These are plain explanations added around the original facts. None adds a number, a version, a flag, a command or a product claim. Each should be checked against the vendor or standard before the owner relies on it.

11.22 (SR-IOV):
- PCIe spelled out as Peripheral Component Interconnect Express.
- Bare-metal passthrough defined as direct hardware access with no hypervisor in between.
- IOMMU expanded as input-output memory management unit, described as a gate between devices and RAM that checks each device request against the device's allowed range.
- HCA expanded as host channel adapter, described as the RDMA endpoint of the card.
- Sysfs described as the Linux virtual filesystem that exposes device settings as files.
- Custom resource and operator described in general Kubernetes terms; SR-IOV device plugin described as the component that reports free Virtual Functions to the scheduler.
- Memory-request walkthrough (IOMMU lookup by Requester ID, table per tenant, fault on a blocked request) is an explanation of the mechanism described in the chapter's table, not a new fact. Confirm wording against the PCIe and IOMMU documentation.
- eBPF expanded as extended Berkeley Packet Filter; CNI expanded as Container Network Interface; statement that Calico and Cilium are both CNI plugins.
- Trivy described as an open-source image scanner; Cosign described as a signing tool for images.
- RBAC expanded as role-based access control.
- Pickle described as Python's serialized object format that can run code on load; .safetensors described as holding only tensor data.
- Volatile memory defined.
- NetworkPolicy behaviour (applies only to pods matched by the selector) described.
- Hypervisor described as the software that runs virtual machines.
- Analogies only (hotel elevator, building with separate doors, locked doors in a row, cordon and drain as planning) carry no facts.

11.23 (vGPU):
- Intake contract described as a written agreement covering workload, memory, latency, trust, failure behaviour and placement.
- UUID expanded as universally unique identifier; the test "same UUID means shared device" explained.
- Hypervisor examples (KVM, VMware ESXi); role of the Virtual GPU Manager on the host and the guest vGPU driver in the VM.
- Paravirtualized explained as the guest cooperating with the host.
- Grace period described as the window before throttling; a pending license check is described as the reason for the grace window. Confirm against the NVIDIA licensing guide.
- License edition claim: "a virtual workstation edition and a compute edition are not interchangeable on the same VM" (the original names vWS and vCS/NVAIE but does not say this). Needs NVIDIA licensing source.
- Drain, canary and soak window defined in plain terms.
- Support bundle described as logs, versions and timestamps for a vendor engineer.
- Owner-by-layer description (host team, hypervisor team, guest team, license owner, operations plane) is an interpretation of the five-layer table.
- Time-sliced vs MIG-backed analogy: time-shared rooms in one office (analogy only). Editorial claim that "time-slicing alone will not fix" a compute-contention problem and that MIG is the stronger tool for it: a reasoned reading of the table, confirm against NVIDIA guidance.
- "Most arguments about vGPU design are settled by one of the five rows" is an editorial summary, not a source claim. Owner may want to cut it.

11.24 (MIG):
- Building-with-flats analogy for MIG (analogy only).
- KV cache expanded as key-value memory filled while an LLM serves requests.
- HBM, memory controllers, L2 cache and copy engines described in plain words.
- Claim that the GPU Instance is the memory and cache path and the Compute Instance is the part CUDA sees (restates the chapter; confirm with the NVIDIA MIG user guide).
- Claim that a mode toggle can stall the whole card while an instance change touches only the slice being rebuilt. Needs NVIDIA MIG user guide source.
- Claim that MIG slices inherit the board's heat, power limit and single PCIe connection (restates the shared-envelope row; confirm).
- ECC (error-correcting code) described; single-bit error corrected by hardware, double-bit error uncorrectable. RMA expanded as return merchandise authorization.
- Statement that a MIG profile needs both a memory share and a compute share (derived from the table and the geometry paragraph).
- DCGM CSV description: clocks, temperature and power, tensor-core and NVLink fields as four kinds of signal (grouping is editorial).
- Label described as a name tag on each time series.
- Node pool described as identical machines partitioned the same way (restates the GKE paragraph).
- Reserved whole-GPU nodes described as absorbing batch work and enabling maintenance drains (editorial, consistent with the Chapter fleet plan).

## Unresolved

1. The two "Step 1: Run the self-checking ... (tested here)" headings (11.23 and 11.24) are kept as written because heading text is locked by rule 5. Owner to decide whether the "(tested here)" suffix should go. The honest status is carried by the sentence "were not run on live hardware" in each chapter's venue section.
2. 11.23 original text said "four recurring trade-offs" but its table lists five rows. The count was changed to "several recurring trade-offs" to remove the contradiction. Owner should confirm the intended count.
3. 11.24 original venue sentence ended with a double-backtick artifact ("marked ``"). Replaced with an honest sentence that the host and cluster commands were not run on live hardware.
4. Residue that remains only inside locked blocks: "Volume N" and "Volume 18" wording in lab output blocks and checkpoint questions, "author's notes" and "untested" in the Sources and review notes sections. These are locked by rule 5 and were not touched.
5. The 11.22 Sources "Corrections to the author's notes" section and the 11.23/11.24 "Not verified on live hardware" sections still say "(untested here)"; they are in the locked tail.
6. `npm run build` was not run (owner instruction for this batch).
7. Exercise counts unchanged: 6 in each chapter. Checkpoint counts unchanged: 20 in each chapter.
