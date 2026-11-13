# Voice rewrite, Part 11 batch J (chapters 11.28, 11.29, 11.30)

Scope: `docs/part-11-gpu-kubernetes/28-dpus-bluefield-and-doca.md`, `29-multi-tenancy-quotas-fault-tolerance-and-health-on-gpu-clusters.md`, `30-lab-multi-node-gpu-kubernetes-on-gke-and-nebius.md`. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (per owner instruction). Chapters 11.31 to 11.34 and all other chapters untouched.

Method: the body (everything above `## Checkpoint questions`) was rewritten section by section. Front matter, title, metadata table, every heading, every code fence, every data table, the Mermaid blocks, the dcgm-exporter note and the lab output blocks are byte-for-byte from HEAD. The checkpoint questions and the Sources and review notes section were spliced in from HEAD unchanged (checkpoint count unchanged: 20, 20 and 20 per chapter as before). Every section opens with a situation. Outcomes lists were rewritten as plain paragraphs with no "you will be able to". Exercise counts are unchanged (6, 6, 6). Each exercise now carries one question per sentence where the original had a multi-part ask. Commands, file paths and facts are unchanged.

## Word counts (`wc -w` on the whole file)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 11.28 DPUs, BlueField and DOCA | 7227 | 9435 | +30.6% |
| 11.29 Multi-tenancy, quotas, fault tolerance and health | 8580 | 11065 | +29.0% |
| 11.30 Lab: multi-node GPU Kubernetes on GKE and Nebius | 8804 | 11369 | +29.1% |

## Gates (run, output seen)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
  - 11.28: 0 hard failures. Words 6041 -> 8249 (body). New numbers 0, lost numbers 0, new code spans 0, lost 0, residue 0 -> 0.
  - 11.29: 0 hard failures. Words 6873 -> 9358 (body). New numbers 0, lost numbers 0, new code spans 1, lost 0, residue 2 -> 2 (both are locked Sources or lab-output lines).
  - 11.30: 0 hard failures. Words 7177 -> 9742 (body). New numbers 0, lost numbers 0, new code spans 1, lost 0, residue 2 -> 2 (locked lab output and Sources lines).
- `python3 tools/restore/chain_gate.py <file>`: 11.28 = 0.0, 11.29 = 0.1, 11.30 = 0.0 per 1000 words (target 0.2 or lower).
- Inline code span check (the owner's snippet, run on each file against HEAD): `{}` for all three files.
- `node tools/check_mermaid.mjs`: checked 776 diagrams, 0 failed.
- `npm run build`: not run (owner instruction for this batch: "No npm build").
- Checkpoint and Sources sections: byte-identical to HEAD (spliced).

## New code spans (soft, guard counts these as "new")

These are things typed or seen on screen that I put in backticks in prose. None changes a command.

- 11.28: `node09` (the node name as seen in the scenario).
- 11.29: `kubectl exec`, `s3:GetObject`, `nvidia-smi`, `for` (the YAML keyword in the rule-file explanation).
- 11.30: `nvidia-smi`, `blkid` (second mention), `/etc/fstab` (second mention), `/healthz`, `nvidia.ko`, `lsblk`, `dmesg`, `tee -a`.

## Needs source (general explanations added in the body)

These are plain explanations around facts already in the chapter. None adds a number, a version, a flag, a command, a vendor claim or a product claim. Each one should be checked against the vendor or standard documentation before the owner relies on it.

11.28 (DPUs, BlueField, DOCA):
- ASIC expanded as application-specific integrated circuit, described as a chip built for one job.
- IDS expanded as intrusion detection system; DDoS expanded as distributed denial-of-service attack; port scan described as a probe for open doors.
- Leaf switch described as the top-of-rack switch a server cable plugs into.
- RDMA described as one machine reading or writing another's memory without either CPU in the copy; RoCEv2 described as RDMA over Ethernet.
- Packet steering described as choosing a queue or port from packet contents.
- Out-of-band management described as a separate management-only network.
- SDK expanded as software development kit; CUDA-to-DOCA analogy is the original.
- PCIe expanded as Peripheral Component Interconnect Express; PCIe function described as one device the host sees on the bus.
- Representor described as the port that stands in for a host-facing function inside the embedded switch; flow described as packets sharing addresses and ports; line rate described as forwarding at the link's full speed.
- Open vSwitch described as a software switch used in Kubernetes networks.
- CVE described as a publicly catalogued vulnerability; API and artifact described.
- IPSec and TLS described as standard network-encryption protocols; AES-256 described as a standard algorithm with a 256-bit key; ciphertext described.
- DCGM expanded as Data Center GPU Manager; crypto miner, dataloader, east-west traffic described.
- BMC expanded as baseboard management controller; rshim described as the host-to-DPU Arm channel. Confirm the rshim description against the BlueField documentation.
- UTC expanded as Coordinated Universal Time; join identifier described.
- NOS profile described as the switch network operating system configuration; BFB described as the bundle that installs the DPU Arm OS.
- Canary, baseline, rack, reconciliation, node readiness, and benchmark described in general terms.
- PKI expanded as public key infrastructure.
- Desired-state orchestration described in general terms.

11.29 (multi-tenancy, health):
- etcd described as the Kubernetes database; ResourceQuota and namespace described.
- Taints and tolerations described as node-marking and pod-allowing rules.
- Calico and Cilium described as network plugins that enforce policies; default-deny described.
- Kernel-bypass described as traffic that skips the Linux networking stack.
- IOPS and QoS expanded; OOM expanded; MIG, MPS, KubeVirt, Kata, RBAC, DCGM Exporter described.
- Harbor, ECR, Falco, Prisma Cloud, Aqua described as registries and runtime scanners; CI/CD expanded; RollingUpdate described.
- Golden image, OIDC, STS, ServiceAccount, prefix-scoped role, Splunk and Elastic described in general terms. STS described as temporary tokens from the AWS Security Token Service.
- Triton described as NVIDIA's inference server; dynamic batching described; CUDA kernel described; KV cache described.
- Streaming Multiprocessor expanded and described.
- Commvault and Veeam described as backup products.
- Kured described as an open-source reboot coordinator. Confirm against the Kured documentation.
- ABI expanded as application binary interface; kernel headers described.
- Thanos, Cortex and VictoriaMetrics described as long-term metrics systems behind Prometheus; Grafana described as the dashboard tool.
- Cardinality, label, time series described.
- Recording rule described.
- NVMe described as flash storage; ransomware described.
- RPO and RTO described; checkpoint described.
- WORM expanded as Write Once Read Many; Compliance mode described as the strictest lock.
- Copy-on-Write described as pointer snapshots; dark fiber and asynchronous delta replication described.
- Tensor Cores, HBM, ICMP, runbook, Follow-the-Sun handoff, ECC error, collective operation, sysfs described.
- FinOps described as cloud spend management; Spot, reserved and On-Demand described.

11.30 (lab, GKE and Nebius):
- Nebius described only in general terms (VM, managed Kubernetes). No Nebius product claim was added.
- CDI described as the standard device handoff to a container; Helm described as the package manager; kubelet and API server described.
- Container runtime, device-plugin socket, Fargate, NodePort, kube-proxy, IPVS, NodeLocal DNSCache, CoreDNS, CNI, CIDR, VXLAN encapsulation described.
- UFW described as a front end to the Linux firewall; /etc/fstab and UUID persistence described.
- PCIe topology, IOMMU, NUMA, PodGroup, gang coordination described in general terms; all_reduce_perf described as a test that measures GPU data exchange.
- Terraform described as infrastructure as code; Auto Scaling Group, subnet tags, DaemonSet, custom resource, NodePool, EC2NodeClass described.
- HPA, VPA, KEDA, Karpenter expanded and described; stabilization window and flapping described.
- Qdrant described as the vector database; RAG and lateral movement described.
- Istio Ambient Mesh and placement groups described in general terms. Confirm the Ambient Mesh wording against the Istio documentation.
- `/healthz` described as a readiness-style HTTP check.

## Unresolved

- Honest status: the original sentences "The cluster commands are untested." (11.29 venue), "The cloud commands are untested." (11.30 venue) and "The commands and manifests below were not run on a live cluster" (11.29 commands) were kept as they were. The rule asks for one honest sentence per section. The owner may want to trim the duplicates.
- Exercises: the node names and image tags such as `node09`, `dpu-image-24.07-prod-1` or `node07` carry digits, so some sentences still hold more than two numbers. Splitting them further would change the facts quoted, so I kept them.
- Soft: the new code spans listed above. Remove the backticks if the owner prefers prose.
- 11.30 lab steps: the chapter has one run step (Step 1) with its output. Each command block has a walkthrough paragraph added around it. The commands are unchanged.
- Locked residue: "Volume N" labels remain only inside lab output blocks, code comments and Sources sections, where the rule keeps them.
- Not verified: no lab or cluster command was run in this pass. The local lab script was not executed.
