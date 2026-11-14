---
id: "c18-06"
title: "18.6 BlueField, DOCA and confidential computing"
sidebar_label: "18.6 BlueField and confidential computing"
sidebar_position: 6
description: "NVIDIA BlueField DPUs, DOCA framework, and confidential computing for AI infrastructure: the BlueField-3 DPU as a security root of trust, the DOCA offload of security functions, confidential VMs (NVIDIA GPU CC, SEV-SNP, TDX), attestation chains, and the operational patterns that move trust from the host CPU to the DPU."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 18.6 BlueField, DOCA and confidential computing

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP / GKE |
| Part | Part 18: Security |
| Cross-references | Chapter 18.1 (Threat modeling); Chapter 18.2 (Hardware and firmware trust); Chapter 18.4 (Kubernetes access control); Chapter 18.5 (GPU sharing security); Chapter 11 (GPU Kubernetes) |
| Coverage file | `planning/coverage/chapters/18-06.md` |
| Claim & number ledger | `planning/ledgers/18-06.md` |

## Why this matters for AI infrastructure

A lender wants to run its credit model on rented GPU servers. Its security team has done everything in the earlier chapters: patched firmware, locked down Kubernetes, encrypted storage. Then the auditor asks one more question. Can an administrator of the hosting company, with root on the host, read the model weights and the applicant data while the job runs?

Standard controls cannot answer yes or no, because the administrator sits below them. Root is the highest administrator account on a Linux machine, and it can usually see anything the operating system can see. Confidential computing exists to answer that question with hardware evidence. This chapter explains what it guarantees, what it leaves trusted, and what a BlueField DPU adds. It does not repeat the mechanics of installing either. Chapters 11.27 and 11.28 cover virtual machines on Kubernetes and the DPU.

Not every workload needs this. The design costs money and operational effort. For a regulated model that handles patient or financial records on infrastructure you do not control, it is the only control that addresses the operator as an attacker. For everything else, the earlier controls in this part usually carry the load.

## Prerequisites and outcomes

A platform engineer is handed a request to host a regulated model on hardware she does not own. Before she can answer the auditor, she needs a few ideas from earlier chapters and this part of the handbook.

### Prerequisites

Chapter 18.1 for the threat model, Chapter 18.2 for firmware and attestation basics, and Chapter 18.5 for GPU sharing. You should know what a virtual machine and a trusted platform module are. A virtual machine, or VM, is a computer that runs inside another computer, with its own operating system. A trusted platform module, or TPM, is a small chip that stores keys and records measurements of the software that starts on a machine.

### Outcomes

The chapter walks through which attacker confidential computing stops and which it leaves out. It then covers the attestation flow that must finish before a key is released, and how to check the confidential computing mode of a GPU and set its ready state. It explains what the CPU-GPU link costs in performance. It ends with what a BlueField DPU's zero-trust mode and secure boot do for you, and what they do not do.

---

## 1. What confidential computing guarantees

Your team already encrypts the model on disk and on the network. The auditor still asks what protects the model while a GPU is computing with it. That question is the reason this section exists.

### 1.1 Data in use

A model is loaded into GPU memory at the start of a job and stays there for hours. For that whole stretch, the data is neither on disk nor on the wire. Data can be encrypted at rest on disk and in transit on the network. The gap is data in use, while the CPU and GPU are working on it. Confidential computing closes that gap by running the workload inside a hardware-protected environment. NVIDIA's documentation says it protects AI workloads, model weights and sensitive data during processing.

A confidential virtual machine, or CVM, runs inside a trusted execution environment on a CPU with AMD SEV-SNP or Intel TDX. A trusted execution environment is a protected region that the CPU enforces in hardware. SEV-SNP and TDX are the two CPU technologies that provide it. The CPU isolates the VM's memory from privileged host software. NVIDIA Hopper and Blackwell GPUs passed through to the CVM extend that protection to GPU memory and to the data that moves between CPU and GPU. Passing a GPU through means the VM gets direct control of the card.

### 1.2 Three ways to deploy

A bank and a cloud provider want to share one set of GPU servers, but neither wants to trust the other with its data. The answer depends on who owns the host. NVIDIA defines three deployment modalities. They move the trust boundary to match who runs the infrastructure.

| Modality | Who controls the host | What is trusted | What is outside the boundary |
|---|---|---|---|
| Confidential bare metal | The model owner, on dedicated hosts | The model owner's host software and administrators | The infrastructure owner, including its management controller |
| Confidential virtual machine | The infrastructure owner, with the tenant inside the guest | The guest OS, driver and workload | Host OS, hypervisor and other tenants |
| Confidential containers | The cluster operator, with the workload in a confidential pod | The workload and its policy | Privileged host software, subject to control-plane separation |

Read the table by asking one question per row: who holds the root password of the machine the workload runs on? The answer tells you who is trusted, and the last column tells you who is not. The hypervisor, which is the software that splits a server into VMs, sits in the outside column for the VM row.

NVIDIA states that the modalities do not provide interchangeable guarantees. The protection depends on the real topology, the trusted software and the policy you enforce. Pick the row that matches the people you need to keep out, not the one that sounds strongest.

**Confidential computing does not remove trust. It moves trust from the host operator to the CPU vendor, NVIDIA, the guest software and the service that releases keys.**

Keep that sentence in mind through the rest of the chapter. Every guarantee in this part rests on a party you still trust, and the job of the design review is to name that party.

### 1.3 What the GPU does

Picture a technician who walks up to a server rack, plugs a probe into a GPU card, and tries to read what is in its memory. Does the card protect that memory from him? For GPU memory, the answer comes from access controls rather than from encryption. GPU memory is not encrypted by the card. NVIDIA's CVM threat model says hardware access controls protect plaintext data in GPU memory, and that memory encryption is not the mechanism. The NVIDIA H100 blog states that the on-package memory is not encrypted and is considered secure against everyday physical attack tools.

Data crossing the PCIe link is encrypted. PCIe is the bus that connects the GPU to the CPU. The GPU is blocked by the CPU hardware from reading CVM memory directly. The driver, inside the CPU's protected environment, moves data through an encrypted bounce buffer in shared system memory. A bounce buffer is a staging area where data is copied before it crosses to the other side. Command buffers and kernels are encrypted and signed before they cross PCIe. A command buffer is the list of instructions the CPU sends to the GPU, and a kernel is a small program that runs on the GPU.

The modes differ in how they protect the links.

| Configuration | CPU to GPU traffic | GPU to GPU traffic |
|---|---|---|
| Single-GPU CC mode, Hopper or Blackwell | Encrypted | Not applicable |
| Multi-GPU CC mode, Blackwell | Encrypted | Encrypted over NVLink |
| Multi-GPU protected PCIe mode, Hopper | Encrypted | Unencrypted over NVLink |

In the Hopper protected PCIe mode, the unencrypted NVLink path means you must assess the fabric, including NVSwitch and physical access. NVLink is NVIDIA's fast link between GPUs, and NVSwitch is the chip that connects several GPUs through it. Read the table as a list of links to inspect, not as a single yes or no answer.

### 1.4 Performance cost

A team moves its first job into confidential mode, and the run takes longer than before. Is that normal, or is something broken? The answer depends on where the job spends its time.

The cost is in the data path, not in compute. NVIDIA's H100 blog says raw GPU compute and memory bandwidth are on par with non-confidential mode. It says CPU-GPU interconnect bandwidth is limited by CPU encryption performance, which NVIDIA measured at roughly 4 GB per second at the time of writing, and that encrypted bounce buffers add latency.

Read that as a design rule. A job with a lot of computation per byte it receives will run close to normal speed. A job that streams large inputs across the PCIe link every step will slow down. Measure your own job before you promise a number to anyone. A quick test is to run the same job twice, once with the mode on and once with it off, and compare the two times.

---

## 2. Attestation: the step that makes the guarantee usable

A key service is about to hand a model decryption key to a VM that has just booted. Before it does, it needs proof that the machine is what it claims to be. Attestation is that proof. Attestation answers one question: is this machine really what it claims to be? The GPU collects and signs measurements, and a verifier compares them with known-good reference values. NVIDIA's documentation states that attestation provides evidence for a trust decision and does not replace the policy that decides whether a workload may receive secrets.

```mermaid
flowchart LR
    CPU[CPU evidence, guest launch state] --> V[Verifier with approved reference values]
    GPU[Evidence from every assigned GPU] --> V
    V -->|all checks pass| KBS[Key release service]
    KBS -->|protected channel| W[Approved workload gets the model key]
```

NVIDIA's threat model says the verification and release flow must:

1. Verify CPU evidence against the tenant's policy for the CPU environment and guest launch state.
2. Verify evidence for every assigned GPU, covering identity, firmware measurements, security mode, reference values and certificate status.
3. Establish that the approved guest software and configuration will receive the secrets.
4. Release secrets over a protected channel to that approved recipient, and only when every check succeeds.

Each step closes a gap the previous step leaves open. The first step proves the CPU side. The second proves the GPU side, which the CPU evidence cannot show. The third makes sure the key goes to the approved software and not to something that merely looks similar. The fourth sends the key over a path that only the approved recipient can read.

A successful GPU attestation does not validate the CPU environment or your workload. CPU evidence alone does not establish the state of the GPUs. A valid signature does not authorise key release, because the policy must also reject firmware versions you do not accept. A signature proves who made a statement, not whether the statement is acceptable.

The GPU also has a ready state. In the documented flow, a user in the CVM sets it with `nvidia-smi conf-compute -srs 1` after attestation. The GPU does not accept work until then, and attestation does not set it automatically. NVIDIA warns that the ready state is not evidence that your release policy has been satisfied. Think of it as the GPU opening its door after the checks have passed, not as the checks themselves.

---

## 3. Commands that check the state

An on-call engineer needs to confirm, from inside a running VM, that the GPU is in the mode the release policy expects. The commands below answer that question, and they come from NVIDIA's confidential computing deployment guide. Check them against your own driver version before you rely on them.

```bash
# In the guest: confirm the GPU runs in the mode you expect
nvidia-smi conf-compute -f

# In the guest, after attestation succeeds: let the GPU accept work
nvidia-smi conf-compute -srs 1
```

The first command prints a line such as CC status: ON. NVIDIA recommends that `nvidia-persistenced` is running in the guest. That is the NVIDIA persistence daemon, a small background service that keeps the driver loaded so that the GPU is not reset between jobs.

The mode itself is set on the host, with a privileged call, through NVIDIA's gpu-admin-tools. Privileged means the call needs root rights on the host. NVIDIA's guide shows `nvidia_gpu_tools.py` with `--set-cc-mode=on` and `--reset-after-cc-mode-switch`, and `--query-cc-settings` to print the current mode. It says CC mode and protected PCIe mode are mutually exclusive, that you must set the mode of every GPU you pass through, and that the mode persists across reboots and power cycles. It also says you cannot set the mode from a host that boots with Secure Boot enabled: either disable Secure Boot in the BIOS or set the mode from within the guest. Secure Boot is the firmware feature that checks each boot component is signed before it runs.

The supported platforms today are Hopper and Blackwell GPUs with Intel Emerald Rapids or Granite Rapids on TDX, or AMD Milan, Genoa or Turin on SEV-SNP. NVIDIA supports only the listed combinations of hardware and software, so check its compatibility matrix before you buy. A matching CPU and GPU on paper is not enough if the pair is not on the list.

---

## 4. What is still trusted, and what is not covered

A design review is coming up, and the reviewer asks one simple question: after all the hardware is in place, what is still trusted? The table below is the answer NVIDIA's own threat models give, and a design review should read it before approving a deployment.

| Limit | What it means for you |
|---|---|
| Guest software stays trusted | Malicious or vulnerable code inside the VM can leak data. Attestation does not prove the approved code is free of vulnerabilities |
| The verifier and key service stay trusted | A compromised verifier, wrong reference values or a permissive release policy can admit an unsafe host |
| Availability | The infrastructure owner can stop the VM, cut the network or remove power |
| Physical attacks and side channels | Invasive probing is outside the GPU threat model, and CPU side channels follow the CPU vendor's model |
| Network and storage | Protect data leaving the VM separately. Do not infer protection for another device from GPU attestation |
| Sharing | The model assumes a whole GPU assigned to one VM. MIG, MPS and GPUDirect RDMA are not supported in these configurations |
| Debug modes | CC-DevTools allows profiling and must be excluded from a production policy |

Work through the table one row at a time and ask who could act on that row. In most rows the answer is the infrastructure owner, the verifier or the guest software. Those are the parties that move trust around, so they belong in the review.

In the dedicated-host modality, NVIDIA also states that the infrastructure owner's management interfaces, including the baseboard management controller, must not have access to workload plaintext. The baseboard management controller is a small computer on the server board that manages the machine from outside its operating system. A network card does not become trusted just because it supports attestation. Baseline NICs stay outside the trusted boundary, so the model owner's software must encrypt sensitive RDMA payloads and restrict the memory the NIC can see. RDMA is the direct memory-to-memory transfer used between machines, and NIC means network interface card.

---

## 5. What a BlueField DPU adds

A network team asks whether a compromised host could change the card that handles its traffic. The question is about where the card sits, and a BlueField DPU sits in a useful place to answer it. A BlueField DPU is a card with its own Arm cores and firmware that sits between the host and the network. DPU stands for data processing unit. Chapter 11.28 covers its architecture. Two documented features matter for security.

Secure boot on the DPU is rooted in unmodifiable ROM code. ROM means read-only memory that cannot be changed after the card is made. NVIDIA's BlueField documentation says the ROM verifies the off-chip public key against a hash stored in eFuses, and each stage then verifies the next. eFuses are one-time-programmable bits on the chip. Secured devices ship with NVIDIA-signed software. You can check this state from the host with `flint`, which should report the life cycle GA SECURED, or from the Arm console with `mlxbf-bootctl`.

Zero-trust mode is a variation of DPU mode, which is the default. NVIDIA's documentation says it stops the host administrator from accessing BlueField from the host, so control shifts to the Arm cores or the management controller. The operations that can be restricted individually include assigning the host as port owner, reading hardware counters, using the tracer, using the RShim interface and flashing firmware. Each of those is a lever a host administrator could otherwise pull, so each one can be closed on its own.

What a DPU does not do is also important. It does not encrypt the host's memory, and it does not replace a CVM. NVIDIA's threat model treats NICs as outside the workload's trusted boundary unless you explicitly establish otherwise. Use the DPU to make the network edge harder for a compromised host to change, and use confidential computing to protect the workload from the host. The two tools guard different things, and a design that uses only one of them leaves the other gap open.

---

## 6. How it fails

Confidential designs can fail quietly. The job still runs, and the dashboards look normal. Each case below starts from a symptom that someone might actually see, and then shows where to look first.

### 6.1 The workload started with CC mode off

An engineer checks a job's logs and sees nothing unusual. The job finished, the output looks right, and the GPU ran at normal speed. The mode was never switched on, so the memory and data were not protected at all. The cause is that the GPU mode was never set to on, or the host mode differs from what the guest sees. Check `nvidia-smi conf-compute -f` in the guest and make the release policy reject any GPU whose attested mode is not what you require.

### 6.2 Attestation passes but the key release is too permissive

A new node passes its checks on the first try, which feels like good news until someone notices that the firmware on the card is old. The verifier accepted the signature, and nothing in the policy looked at the version. NVIDIA warns that a valid signature alone does not establish that a firmware version is acceptable. Add version checks to the policy and track the vendor's advisories.

### 6.3 The job is slower than expected

A training job runs far longer on the confidential node than on a normal one. The likely reason is that the job moves large batches across PCIe each step, and CPU encryption limits that link. Measure with and without CC mode and consider keeping data on the GPU between steps. Keeping data on the GPU means the next step reads it from GPU memory instead of fetching it again from the CPU side.

### 6.4 A debug mode slipped into production

An engineer switches a node into a debugging mode to chase a bug, and then forgets to switch it back. The node now permits profiling, which is useful to a developer and risky to a tenant. A production policy that requires the restrictions must reject that mode in attestation.

### 6.5 The management controller is trusted by mistake

A design review is clean on paper, and everyone agrees the workload is safe. Then someone asks which chip actually has to be trusted, and the answer includes the host's baseboard controller. The design assumed the controller could not see workload data, yet the controller has a vulnerability. Chapter 18.2 describes why the controller must stay outside the trust boundary and be patched.

---

## 7. Hands-on lab

A new node has arrived with a supported GPU and a DPU, and the team wants the basic checks done before a vendor test is booked. The lab needs a Hopper or Blackwell GPU on a supported CPU, which most readers do not have. Read it as a checklist for a vendor test, not as a runnable recipe. It has not been run here.

1. On the host, query the GPU mode with the gpu-admin-tools script and its `--query-cc-settings` option.
2. In the guest, run `nvidia-smi conf-compute -f` and confirm CC status ON.
3. Install the NVIDIA attestation SDK, which NVIDIA's guide names NVAT, and attest the GPU.
4. Only after attestation succeeds, run `nvidia-smi conf-compute -srs 1`.
5. On a BlueField host, run `sudo mst start`, then `sudo flint -d /dev/mst/mt41686_pciconf0 q full` and look for the life cycle line.
6. Time a data-heavy job with CC mode on and off, and record the ratio.

Record: the mode of every GPU, the life cycle state of every DPU, and the measured slowdown for your job. Keep the record with the node, so the next reviewer can see what was checked and when.

---

## Exercises

Each exercise starts from a request a platform team could really receive. Work through them in order, because the later ones build on the first.

1. A security review asks you to prove that a cloud administrator cannot read model weights during inference. List the four verification steps before key release. Say which one a valid GPU attestation alone does not cover. *Solution sketch:* the four steps are CPU evidence, GPU evidence, approved guest software and a protected release. GPU attestation does not cover the CPU environment or the workload.
2. A team runs a Hopper multi-GPU job in protected PCIe mode and says all traffic is encrypted. Correct the claim. *Solution sketch:* CPU to GPU traffic is encrypted, but GPU to GPU traffic over NVLink is unencrypted in that mode, so fabric and physical access must be assessed.
3. A data-loading step moves 40 GB across PCIe in each training step. NVIDIA's blog reports a roughly 4 GB per second figure for CPU encryption. How long does the move take, and what do you do about it? *Solution sketch:* divide 40 by 4. The move takes about 10 seconds, so reduce data movement or keep data resident on the GPU, and measure on your platform.
4. A host boots with Secure Boot enabled, and the gpu-admin-tools call to set CC mode fails. What are your two options? *Solution sketch:* disable Secure Boot in the BIOS, or set the mode from within the guest, as NVIDIA's guide describes.
5. A BlueField card reports a life cycle other than GA SECURED. What do you conclude, and what do you do next? *Solution sketch:* the secure boot chain is not anchored in eFuses as expected. Keep the card out of the trusted path until NVIDIA support explains it.
6. Decide whether a team needs confidential computing for an internal notebook cluster. The cluster runs open models on public data. *Solution sketch:* probably not, since the cost and operational effort protect against a host operator the team already trusts.

---

## Checkpoint questions

Each question below begins with a node, a tenant or a ticket that you might meet on the job.

<details><summary>1. An auditor asks whether a hosting company's root administrator can read your model weights while it runs. Which control answers, and what must you also check?</summary>
A confidential VM with GPU confidential computing mode isolates the workload from privileged host software. You must also check attestation and the key release policy, because the model key should reach only a verified workload.
</details>

<details><summary>2. A team says confidential computing means GPU memory is encrypted. Is that right?</summary>
No. NVIDIA's threat model says hardware access controls protect plaintext in GPU memory and that memory encryption is not the mechanism. Data crossing PCIe is encrypted.
</details>

<details><summary>3. Attestation succeeds, but the GPU still refuses work. Why?</summary>
The GPU does not accept work until a user in the VM sets the ready state with nvidia-smi conf-compute -srs 1. Attestation does not set it automatically.
</details>

<details><summary>4. A verifier accepts a GPU with older firmware that has a known flaw because its signature is valid. What is the fix?</summary>
Add firmware version checks to the policy and reject disallowed versions. NVIDIA states that a valid signature does not establish that a version is acceptable.
</details>

<details><summary>5. A job runs twice as slow in CC mode. Where do you look first?</summary>
At data movement across PCIe. CPU encryption limits CPU-GPU bandwidth, and encrypted bounce buffers add latency. Compute and memory bandwidth on the card are on par with normal mode.
</details>

<details><summary>6. A team wants to run confidential tenants on MIG instances carved from one shared GPU to save money. What is wrong with that plan, and what replaces it?</summary>
NVIDIA's confidential VM threat model assumes a whole GPU for each VM, and it lists MIG, MPS and GPUDirect RDMA as unsupported in those configurations. Give each confidential tenant a whole GPU, assigned to one confidential VM, instead of a MIG slice. The sharing row of the table in section 4 of this chapter states the same limit.
</details>

<details><summary>7. A tenant's RDMA traffic runs through a network card that supports attestation. Does the workload still have to protect its payloads, and why?</summary>
Yes. NVIDIA says a network card does not become trusted just because it supports attestation, so a baseline NIC stays outside the trusted boundary unless a deployment explicitly places it inside. The workload software must therefore encrypt sensitive RDMA payloads and restrict the memory the NIC can see.
</details>

<details><summary>8. A company wants to hide user data from the model owner too. Does confidential bare metal do that?</summary>
No. NVIDIA says it trusts the model owner's privileged software and does not isolate end-user data from the model owner. An additional CVM can place the approved workload inside a CPU-protected environment so host administrators are outside the boundary.
</details>

<details><summary>9. An admin needs to reach a BlueField from the host during an incident. Does zero-trust mode allow that, and what does it leave unprotected?</summary>
Zero-trust mode stops the host administrator from accessing BlueField from the host, so control moves to the Arm cores or the management controller. Each lever, such as port ownership, counters, the tracer, RShim and firmware flashing, can be restricted on its own. Zero-trust mode does not encrypt the host's memory, and it does not replace a confidential VM.
</details>

<details><summary>10. A reimaged BlueField has to show that its secure boot is anchored before it joins the pool. Which two checks do you run, and what do they tell you?</summary>
From the host, run `flint` and look for the life cycle GA SECURED. From the Arm console, run `mlxbf-bootctl` and read the lifecycle line. The ROM verifies the off-chip public key against a hash stored in eFuses, and each stage verifies the next, so both checks reflect a chain that starts in unmodifiable ROM.
</details>

<details><summary>11. You must set CC mode on a host that boots with Secure Boot. What happens?</summary>
NVIDIA's guide says you cannot set the GPU mode from such a host. Disable Secure Boot in the BIOS, or set the mode from within the guest.
</details>

<details><summary>12. A team wants confidential computing for public open-model notebooks. What do you advise?</summary>
Probably not. The design adds cost and effort. It protects against a host operator, and these notebooks have no secret to protect from one.
</details>

<details><summary>13. Attestation passed, so a developer says the application code is safe. Is that right?</summary>
No. NVIDIA says attestation does not establish that approved code is free of vulnerabilities. Malicious or vulnerable guest code can still leak data.
</details>

<details><summary>14. Who can stop a confidential VM, and why does that matter for an SLA?</summary>
The infrastructure owner can stop the VM, interrupt networking, detach devices or remove power. Confidential computing does not guarantee availability against that operator.
</details>

<details><summary>15. A customer proposes a confidential VM on a CPU that is not on NVIDIA's list, paired with a Hopper GPU. Is that pairing supported?</summary>
Only the listed combinations are supported. The listed platforms are Hopper and Blackwell GPUs with Intel TDX on Emerald Rapids or Granite Rapids, or AMD SEV-SNP on Milan, Genoa or Turin. A matching GPU and CPU on paper is not enough, so check NVIDIA's compatibility matrix before you buy.
</details>

<details><summary>16. A job moves 24 GB across PCIe per step at 4 GB per second. How long, and what does it suggest?</summary>
24 divided by 4 is 6 seconds per step spent on transfer alone. It suggests keeping data on the GPU or cutting the transfer, and measuring on your platform.
</details>

<details><summary>17. A debug mode that permits profiling is on in production. What should the policy do?</summary>
Reject it. NVIDIA's threat model says CC-DevTools permits profiling access and must be excluded from a production policy that requires the stronger restrictions.
</details>

<details><summary>18. In protected PCIe mode on Hopper, what is still exposed?</summary>
GPU to GPU traffic over NVLink is unencrypted. You must assess NVSwitch and physical access, and CPU to GPU encryption alone does not establish confidentiality on that path.
</details>

<details><summary>19. What do you check in order when a new confidential node fails to release a key?</summary>
First the guest CC status, then GPU attestation evidence and reference values, then CPU evidence, then the release policy. NVIDIA says the policy must cover both CPU and GPU evidence.
</details>

<details><summary>20. After a confidential workload ends, how do you hand the GPU to the next tenant?</summary>
Follow the supported GPU reset and reassignment lifecycle. NVIDIA says session keys are ephemeral and reset clears protected state, and that stopping a workload is not a substitute.
</details>

---

## Sources and review notes

- NVIDIA Confidential Computing documentation: overview, virtual machine overview, supported platforms, deployment guide pages "Configuring the GPUs" and "Attesting the GPU", virtual machine and bare metal threat models. Fetched 2026-11-12 from docs.nvidia.com/confidential-computing.
- NVIDIA developer blog, "Confidential Computing on H100 GPUs for Secure and Trustworthy AI": performance primitives, bounce buffers, the roughly 4 GB per second figure, and unencrypted on-package memory. Fetched 2026-11-12. The 4 GB per second figure is NVIDIA's measurement at the time of the post.
- NVIDIA BlueField BSP documentation, modes of operation (version 4.8.0) and secure boot (version 4.5.2). Fetched 2026-11-12.
- *Production Kubernetes*, chapter 7, for secret handling that still applies inside a confidential VM.

### Corrections made in this rework

- Removed the invented query `nvidia-smi --query-gpu=cc_mode`, the placeholder `--cc-mode` flag, the unverified `doca_service list` command, a verifier sketch calling `tpm2_pytss.verify` on DPU and CVM quotes, and the `highassurance.*` roles. None appears in vendor documentation.
- The earlier text said GPU CC encrypts GPU memory and that a DPU takes the host out of the trust chain. NVIDIA says GPU access controls protect GPU memory, and treats NICs as outside the trusted boundary by default.
- The earlier chapter listed BlueField core counts, memory sizes and DOCA library names without a source. They are removed.

### Open items

- NVIDIA's documentation does not describe a single end-to-end chain from TPM through DPU to CVM. The earlier diagram of that chain is removed.
- The 4 GB per second figure was published for H100. Check current numbers for Blackwell.
