# Voice audit report 1 (sample_1: part-00, part-08, part-11)

Strict grading. No file earned a 5. Most chapters open well (a concrete "Picture..." scene) but the body paragraphs fall back to command dumps (part 08) or abstract, stock-phrase prose (part 11).

| file | grade | main problem (one phrase) |
|---|---|---|
| part-00/01-the-ai-factory-landscape-and-the-roles-in-it | 3 | summary of a source book, "The book traces/estimates", flat facts, stale figure |
| part-00/02-how-to-use-this-book-and-set-up-your-labs | 3 | checklist and Q&A fragments, no prose |
| part-00/03-learning-paths-by-role | 3 | Q&A fragments, thin paragraph |
| part-08/01-bcm-architecture-and-concepts | 3 | good opener, then config-directive dump |
| part-08/02-planning-and-installing-bcm | 3 | stacked numbers and commands |
| part-08/03-cluster-configuration-networks-nodes-and-categories | 2 | command and term stacks, repeated 70*1g example |
| part-08/04-node-provisioning-images-kernels-categories-and-the-pxe-flow | 3 | "Habit 8/9/10" shorthand, terse |
| part-08/05-cmsh-and-base-view-administering-the-cluster | 3 | semicolon and command chains |
| part-08/06-users-authentication-and-security-in-bcm | 3 | requirement lists, undefined LDAP/AD/WAN jargon |
| part-08/07-power-bmc-and-hardware-management-in-bcm | 3 | flag and command dumps, "Mistake 6..10" list |
| part-08/08-workload-managers-under-bcm-slurm-setup | 3 | "the manual I read" aside, command chains |
| part-08/09-kubernetes-under-bcm-deployment-and-gpu-enablement | 3 | role/port term stack |
| part-08/10-containerization-in-bcm-docker-apptainer-and-enroot | 4 | good scene and arithmetic, last para too dense |
| part-08/11-monitoring-health-checks-and-alerts-in-bcm | 2 | bold-headed numbered blocks, parenthesis and backtick stacking |
| part-08/12-high-availability-and-head-node-failover | 3 | long step-by-step run of states and scripts |
| part-08/13-day-2-operations-updates-scaling-hardware-replacement | 4 | plain, human ("A backup you have never restored is only a hope") |
| part-08/14-air-gapped-installation-and-upgrades | 3 | thin prose, lists of mistakes and tasks |
| part-08/15-bcm-in-an-ai-factory-dgx-superpod-integration | 3 | stacked bandwidth numbers, first-person process notes |
| part-08/16-mission-control-dgx-cloud-and-autonomous-recovery | 3 | abstract, version-bug narration |
| part-11/01-why-kubernetes-needs-a-gpu-platform-layer | 3 | dense term chain, "must therefore" |
| part-11/02-device-plugin-container-toolkit-cdi-and-runtime-classes | 3 | validation-process note leaked into chapter |
| part-11/03-node-feature-discovery-and-gpu-feature-discovery | 3 | coined label "SKU-coupled manifest fragility" |
| part-11/04-gpu-operator-architecture-and-operands | 3 | module and command lists, abstract "breaks down at cluster scale" |
| part-11/05-gpu-operator-installation-configuration-and-upgrades | 2 | stock phrases, abstract dangers, "strictly governed contract" |
| part-11/06-scheduling-gpus-requests-topology-manager-cpu-and-numa-alignment | 3 | roadmap sentence, good worked example |
| part-11/07-multi-node-jobs-why-a-pod-cannot-span-nodes | 3 | dense, over-absolute ("immediate CUDA OOM crashes") |
| part-11/08-kueue-volcano-and-scheduler-plugins | 3 | term stacks, exercises overstuffed |
| part-11/09-jobset-leaderworkerset-pytorchjob-and-the-mpi-operator | 3 | off-topic prompt-engineering paragraph |
| part-11/10-secondary-networks-multus-sr-iov-device-plugin-and-rdma-device-plugin | 3 | noun-chain sentences |
| part-11/11-nvidia-network-operator | 2 | marketing tone, stacked acronyms, "completely blind" |
| part-11/12-dynamic-resource-allocation-dra | 3 | bold-headed list, term dump |
| part-11/13-kai-scheduler-why-default-scheduling-is-not-enough | 3 | "failure mode" rhetoric, unsourced 60% and 85% |
| part-11/14-kai-scheduler-architecture-and-resources | 3 | "Step 1/2/3" number run, fixture list |
| part-11/15-kai-queues-quotas-and-fair-sharing | 3 | word problems with stacked numbers |
| part-11/16-kai-gang-scheduling-and-topology-aware-placement | 3 | "Read each row" filler |
| part-11/17-kai-gpu-sharing-and-fractions | 3 | abstract, "Start with the symptom" filler |
| part-11/18-kai-operations-and-troubleshooting | 2 | repeated "Resist" / "must never", abstract |
| part-11/19-the-run-ai-platform-view | 2 | abstract governance prose, three-horizon framing |
| part-11/20-scheduler-comparison-guide | 3 | mixed; Slurm tier paragraph is a term dump |
| part-11/21-pcie-iommu-vfio-and-device-passthrough | 3 | confusing arithmetic, "must never" |
| part-11/22-sr-iov-for-nics-and-gpus | 2 | bold-claim list items, abstract, "ransomware outage" |
| part-11/23-nvidia-vgpu-architecture-profiles-and-licensing | 3 | "Read the rows as..." filler, exercise lists |
| part-11/24-mig-in-depth | 3 | clear explanations, but a "corrected 2026-11-11" note sits in the prose |
| part-11/25-time-slicing-mps-and-oversubscription | 3 | exercises full of identifiers |
| part-11/26-choosing-a-gpu-sharing-model | 3 | prerequisite filler, abstract |
| part-11/27-virtual-machines-on-kubernetes-kubevirt-kata-and-gpu-passthrough | 3 | name chains, abstract opener |
| part-11/28-dpus-bluefield-and-doca | 2 | marketing ("zero x86 CPU tax"), figure-reference filler |
| part-11/29-multi-tenancy-quotas-fault-tolerance-and-health-on-gpu-clusters | 3 | slightly rhetorical, sound content |
| part-11/30-lab-multi-node-gpu-kubernetes-on-gke-and-nebius | 3 | cross-reference sprawl, stacked checks |
| part-11/31-nvidias-open-source-ai-factory-kubernetes-stack | 4 | plain and direct, minor term stacking |
| part-11/32-nvke-nvidia-kubernetes-engine-in-depth | 4 | honest first person, but [ran]/[source-code] tags clutter |
| part-11/33-nvke-in-depth-part-2-installation-nvkr-and-cluster-lifecycle | 3 | command and flag stacks |
| part-11/34-nvke-in-depth-part-3-operations-security-failure-modes-and-comparison | 4 | plain, human ("short and unpleasant"), tag clutter |

## Worst 15 files with one example sentence each

1. part-08/03: "`nodeoverview` shows uptime, load, memory, WLM slots, and NIC and disk use." Term stack. A human would pick the two commands an admin runs first and say why. Move the rest to a table.
2. part-08/11: "Write the health check script to return `PASS`, `FAIL [severity]`, or `UNKNOWN` plus fd 3 `InfoMessage`" (bold list heading). Use a plain heading ("Write the check script") and start with the failure this prevents.
3. part-11/05: "Upgrades deserve the same suspicion." Abstract. Write one real story: one node had Secure Boot on, the chart upgrade wedged its driver, and rollback did not unload the module.
4. part-11/11: "That coarse interval is completely blind to synchronized AI incast microbursts." Say: a switch counter read every 30 s cannot see a burst that lasts microseconds.
5. part-11/18: "Responders must never start by restarting DaemonSets or rebooting worker nodes." Say what restarting destroys (the evidence) and give the first safe step.
6. part-11/19: "A durable fairness policy works across three time horizons." Start with the lab that floods the queue and say who loses. Then name the horizons.
7. part-11/22: "Slicing a network card into Virtual Functions does not restrict which host physical RAM addresses those Virtual Functions can read." Split it: a Virtual Function is a slice of the card. Without an IOMMU it can still reach any host memory.
8. part-11/28: "achieves line-rate encryption with zero x86 CPU tax." Marketing. Write: encrypting 400 Gbps in software would use every x86 core, so the DPU does it instead.
9. part-11/02: "The validation pass on 2026-10-25 passed `validate_chapter.py` and `check_coverage.py`." Build-process note in reader prose. Delete it, keep only "commands are untested; check API versions".
10. part-11/24: "corrected 2026-11-11: the 70 GB for seven 1g.10gb slices is memory-slice geometry..." Editorial correction note in the body. Fold into one plain sentence; put the source in a footnote.
11. part-11/09: "Prompt engineering and context engineering guide an aligned foundation model." Off-topic paragraph in a JobSet/PyTorchJob chapter. Remove it, or tie it to the job.
12. part-11/21: "Fifty times that is 3,200 GB/s. The H100's internal HBM3 bandwidth is 3,350 GB/s..." Confusing. Write: the card's memory moves about 3,350 GB/s, roughly fifty times what a PCIe Gen5 x16 link carries.
13. part-11/13: "That change lifts utilization to 85%." A bare, unsourced figure. State the source and conditions, or say "in one vendor example".
14. part-08/15: "These bandwidths are my own products of the document's per-tray figures." Process voice. Say "Multiply per-tray figures by 144 to get per-SU totals" and show the worked lines.
15. part-00/01: "The book estimates 75 billion by 2025." Dated figure from a source book, in the "The book traces..." voice. Teach the idea directly and give the year the estimate was made.

## Other flags
- Suspicious or odd: 00/01 IoT counts and the "early 1970s patent" are dated, check the source. 11/13 60% to 85% utilization needs a source. 11/06 CPU-core arithmetic (64 cores across two sockets, 14 free) is hard to follow, re-check it. 08/03 repeats the same overallocation example three times, with "70*1g.5gb" adding nothing.
- Semicolon chains: 08/05, 08/08 (cmsh command lines are fine as commands but are run together in prose).
- Parenthesis and backtick stacking: 08/03, 08/07, 08/11, 11/32, 11/33. Backticks also appear on plain concepts, for example `Port` and `init` in 08/01.
- Undefined acronyms at first use: CPS (00/01), WLM and SOL (08/07, 08/08), AD, WAN, LDAP (08/06), PLEG (11/12), HFQ expanded but "NVL72" and "SU" not (08/15, 11/15).
- First-person process voice ("the manual I read", "I did not cover", "my own products"): 08/08, 08/15.
- Meta-text in reader prose: 11/02 validation date, 11/24 correction note. Misplaced exercise content: 11/08 (etcd/APF items in a Kueue chapter).
- Repeated opener shape: "Picture a ..." / "Suppose ..." appears in about half the chapters. Good device, overused.
