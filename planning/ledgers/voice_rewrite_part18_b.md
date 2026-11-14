# Voice rewrite ledger: Part 18, chapters 18.5 to 18.7 (pass b)

Scope: `docs/part-18-security/05`, `06`, `07`. Front matter, headings, tables, code fences, Mermaid blocks, the 20 checkpoint blocks per chapter and the Sources and review notes section are byte-identical to HEAD (checked by script: fences, details, sources, front matter and table lines all equal). Only body prose changed. Nothing committed. `planning/EXTERNAL_EDITS.md` not touched (step 6 skipped as instructed).

## Word counts (`wc -w`, full file)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 18.5 GPU sharing security, DMA, IOMMU and SR-IOV | 4758 | 6257 | +31.5% |
| 18.6 BlueField, DOCA and confidential computing | 3915 | 5189 | +32.6% |
| 18.7 Data and model protection, audit and compliance | 3595 | 4800 | +33.5% |

Guard prose counts (code and tables removed): 05 4571 to 6062 (+32.6%), 06 3764 to 5038 (+33.8%), 07 3288 to 4493 (+36.7%). All three sit inside the +25 to +40 band on both measures.

## Gates (run on the final files)

- Span check (`{}` required): `{}` on 05, 06 and 07 (old-minus-new inline code spans, fenced blocks removed).
- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
  - 05: 0 hard failures, new numbers 0, lost numbers 0, new code spans 1 (`/sys`, a path seen on screen in a sentence explaining the sysfs tree; kept as a path, not a command).
  - 06: 0 hard failures, new numbers 0, lost numbers 0, new code spans 0.
  - 07: 0 hard failures, new numbers 0, lost numbers 0, new code spans 0.
  - Residue: 0 on all three.
- `python3 tools/restore/chain_gate.py <file>`: 0.0 per 1000 words on all three (target 0.2 or lower).
- Raw `<` or `{` outside code: 0 on all three. Exclamation marks: 0. Outcomes phrasing ("you will be able", "should be able"): 0 on all three.
- Status sentence: one per chapter. 05 and 06 and 07 each keep "have not been run" or "has not been run" once, in the sentence above the lab. The status line in 06 section 3 was reworded to "Check them against your own driver version", so it is not a second status word.
- `node tools/check_mermaid.mjs`: not run in this pass. The Mermaid blocks are byte-identical to HEAD, so nothing in them changed.
- `npm run build`: not run (the task said no npm build).

## Rule compliance notes

- Every `##` and `###` section opens with a situation sentence. Where the locked heading sits above, the situation is the first sentence under it (for example "## Prerequisites and outcomes", "## How it fails", "## Exercises", "## Checkpoint questions" where one sentence was added above the locked details blocks).
- 05 "### Outcomes" list (five numbered items) rewritten as one plain paragraph. 06 "### Outcomes" list rewritten the same way. 07 "### Outcomes" list rewritten the same way. No outcome lists remain.
- Exercises and lab steps: same counts (05: 6 exercises, 5 lab steps; 06: 6 exercises, 6 lab steps; 07: 6 exercises, 6 lab steps). Same commands and facts. Sentences split so that most have at most two numbers. Sentences the original wrote with three or more numbers in a solution sketch were split where the facts allowed (05 exercise 4 and 6, 06 exercise 3). Exercise 6 in 05 now reads "Multiply by 3 dollars and you get 1,200 dollars an hour." Facts unchanged.
- Bold: 05 keeps the original bold line in section 1. 06 keeps the original bold line in section 1.2. 07 has no bold line. One bold idea per section held.
- Gem books: none added. Original attributions kept as written (*Production Kubernetes* in the Sources sections only).
- Checkpoint blocks: unchanged (count 20 in each chapter, form and answers identical).
- Math `$...$` with stray backticks: none found in the three chapters. Nothing to note.
- Acronyms spelled out at first use in prose: SR-IOV (05 prerequisites), CVE (05 section 3.1), CDI (05 section 3.1), CUDA (05 section 2.1), VFIO (05 section 2.2), ACS (05 section 2.2), MPS (05 section 4), NVLink (05 section 4), DPU (06 section 5), TPM (06 prerequisites), VM (06 prerequisites), CVM (06 section 1.1), TDX and SEV-SNP (06 section 1.1), NIC and RDMA (06 section 4), ROM and eFuses (06 section 5), KMS (07 section 3.2 uses existing name only), etcd and API server (07 section 3.2), OIDC and PKCS 11 (07 section 2), SHA-256 (07 section 4.2), NaN (07 section 1.2), TLS (07 section 3.3, original).
- Invented attributions: none added. Every new sentence explains a term or a teaching point, not a claim about a source.

## Needs source (general explanations added in prose, not from the original text)

These are plain definitions or teaching points added during the rewrite. None adds a number. Each would need a citation if the handbook requires one.

- 18.5 section 0: the Wiz-era teaching point that a container runs on a node's file system (definitions of container image and file system); the apartment-building analogy for the GPU node.
- 18.5 prerequisites: definitions of SR-IOV (single-root I/O virtualization), container runtime, device plugin.
- 18.5 section 1: the reader question "which of the risks you are covering" (teaching frame only).
- 18.5 section 2.1: CUDA as NVIDIA's programming platform; the warehouse and private-locker analogy.
- 18.5 section 2.2: a network card writing into another process's memory without a check (general scenario); VFIO as the Linux framework for user-space or VM device control; ACS as access control services; the `/sys` tree as a kernel-built view with no real files on disk.
- 18.5 section 3.1: CVE as the public numbering system for security flaws; CDI as the Container Device Interface; time-of-check time-of-use as a general concept; a hook as a small program the runtime runs at container start.
- 18.5 section 3.2: provenance as a record of where an image came from; privileged as broad host rights; the kubelet as the node agent.
- 18.5 section 4: MPS as Multi-Process Service; fault domain definition; NVLink as NVIDIA's fast GPU link; peer access as one GPU reading another's memory directly; the sink and pipe analogy.
- 18.5 section 5.1: kernel as a small parallel program on the GPU; local memory as fast memory a kernel uses while it runs.
- 18.5 section 5.2: side channel as a way to learn a secret from indirect signals.
- 18.5 section 6.1: cordon as marking a node so no new pods are placed on it; a host escape can read anything the node can read.
- 18.5 section 6.3: passthrough as direct device control by a VM.
- 18.5 section 6.5: attestation as a check that a VM started with the expected software.
- 18.5 section 7: profile as a slice size the card allows; instance as a created slice; scheduling and pending pod definitions; replica as one share of a GPU offered by the device plugin.
- 18.6 introduction: root as the highest administrator account on Linux.
- 18.6 prerequisites: VM and TPM definitions (TPM as a chip that stores keys and records measurements).
- 18.6 section 1.1: trusted execution environment as a region the CPU enforces in hardware; passthrough as direct GPU control by the VM; hypervisor as the software that splits a server into VMs.
- 18.6 section 1.2: "ask who holds the root password" reading frame.
- 18.6 section 1.3: bounce buffer as a staging area; command buffer as the list of instructions the CPU sends; NVSwitch as the chip connecting several GPUs; technician-with-probe scenario.
- 18.6 section 1.4: "run the same job twice" test method.
- 18.6 section 2: a key service handing a model key to a just-booted VM (scenario); a signature proves who made a statement, not whether it is acceptable; the ready state as a door opening after checks.
- 18.6 section 3: privileged as needing root rights on the host; NVIDIA persistence daemon as a background service keeping the driver loaded; Secure Boot as the firmware check that each boot component is signed.
- 18.6 section 4: baseboard management controller as a small computer on the server board; RDMA as direct memory-to-memory transfer; NIC as network interface card.
- 18.6 section 5: DPU as data processing unit; ROM as read-only memory fixed after manufacture; eFuses as one-time-programmable bits.
- 18.6 section 6.3: keeping data on the GPU means the next step reads it from GPU memory.
- 18.7 section 0: pickle as Python's object-saving format; loading as running code.
- 18.7 section 1.1: tensor as the basic array of numbers.
- 18.7 section 1.2: the loader reads a tensor description then copies numbers; NaN as not-a-number; provenance as a record of origin; the registry as the store for approved models; a sandbox as a throwaway environment.
- 18.7 section 2: digest as a short fingerprint of a file's contents; OIDC as the login standard many services use; PKCS 11 devices as hardware security modules; transparency log as a public append-only signing record; "failing loudly" point.
- 18.7 section 3.1: wrapping as encrypting the data key with the outer key; rotation as replacing keys on a schedule; the scenario of a key stored in the same bucket.
- 18.7 section 3.2: encoding is not encryption (base64 decoding); etcd as the cluster database and the API server as the front door; seed as the starting value for derived keys; managed control-plane flags can be overwritten by the platform.
- 18.7 section 3.3: ingress as the entry point routing outside requests; service mesh as a proxy layer between services.
- 18.7 section 4.1: allUsers as anyone on the internet; allAuthenticatedUsers as anyone with a Google account.
- 18.7 section 4.2: SHA-256 as a standard hash function; sketch-versus-bucket-lock note.
- 18.7 section 5: edge as one link between two graph items.
- 18.7 section 6.2: red-team checks as deliberate attempts to make the model misbehave.
- 18.7 section 6.4: rewriting as moving old plain-text copies into encrypted form.
- 18.7 section 6.5: pinned key version as a fixed reference to one old key copy.
- 18.7 section 7: a lab rationale ("a quick answer shows the controls work").

## Unresolved (not changed)

- 18.6 checkpoint 15 "Which GPUs and CPUs does NVIDIA support for confidential VMs?" reads as a lookup question, close to a bare-definition question. Left unchanged because checkpoints are locked and the answer is supported by section 3 of the chapter.
- 18.7 checkpoint 8 "What is envelope encryption, in one sentence?" reads as a bare-definition question. Left unchanged for the same reason. Listed for the checkpoint owner.
- 18.7 checkpoint 7 and 14 are short but scenario-adjacent. Left unchanged.
- 18.5 checkpoint 19 and 20 answers are supported by the chapter. No change.
- 18.7 lab step 5 and the sample `gcloud storage buckets update gs://audit-log-bucket --retention-period=90d`: kept as in original. The earlier F-pass note (argument order versus `gsutil`) no longer applies because the text uses `gcloud`.
- 18.7 section 1.2 says "The project describes pickle as unsafe" and section 2 attributes the signing statement to "the project"; these attributions were already in the original.
- 18.7 Python audit-log code block (locked) writes entries as mode 0o444 and uses a local directory. The prose says the sketch "models" an object-lock bucket, which matches the code comment. No change.
- 18.7 "Open items" still lists a `watermark` helper referenced in no chapter text. Locked.
- 18.5 earlier F-pass note about the MIG layout arithmetic (1+1+2+4 = 8 vs "7") and the 1g.5gb vs 1g.10gb request: the MIG layout arithmetic is not in the rewritten text. The 1g.5gb vs 1g.10gb mismatch remains in the locked lab step 4 and is explained in the prose, as the original was.
- 18.6 earlier F-pass note on "How it fails" numbering (section 6 vs 7) is not present in the current headings. No action.
- 18.6 "The 4 GB per second figure was published for H100. Check current numbers for Blackwell." remains in Open items and in the prose. Kept.
- Locked Sources and Corrections text in all three chapters was not edited.
