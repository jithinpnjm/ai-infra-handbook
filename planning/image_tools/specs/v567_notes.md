# Vol 5/6/7 figure notes (read-only planning pass)

Status: PARTIAL. Chapters done: 1 of 105 (v5 ch01). Remaining chapters are not yet read.

## part-05-kubernetes

| Chapter file | Topic | Mermaid blocks | Mermaid weak/overcomplex (do not redraw?) | Raster candidates |
|---|---|---|---|---|
| 01-containers-from-first-principles-images-layers-registries.md | Container as a process, OCI image layers, registries, rootless, GPU containers | 3 (L52 container process tree, L142 tag-to-index-to-blob tree, L585 GPU request path) | None flagged; all three are simple and fine | None |

SVG specs written for ch01 (v5_01.json): k01-whiteout-layers (L183), k01-pull-cache (L531), k01-multistage (L448), k01-userns-map (L567). Anchors verified unique with grep -cxF.
| 02-container-runtimes-containerd-runc-cri-and-oci.md | CRI stack (kubelet to CRI to containerd/CRI-O to shim to OCI runtime), pod sandbox, containerd config, RuntimeClass, GPU runtime, cgroup drivers | 1 (L48 stack diagram) | None flagged; the stack diagram is a dense 9-node flowchart but it is the chapter's core picture, so do not duplicate it | None |

SVG specs for ch02 (v5_02.json): k02-sandbox (L90), k02-cri-sequence (L100, swimlane from the 5-call CRI order), k02-isolation (L311), k02-cgroup-match (L522). All anchors verified unique.

## ch03 (part-05 03-kubernetes-architecture-overview-components-and-what-talks-to-what.md)
Topic: control-plane and node components, declarative object model, kubectl-to-container flow, HA topologies, failure table, extension points, GPU cluster architecture.
Mermaid: 3 blocks. L44 big-picture flowchart (dense, 9+ nodes, but it is the core map; keep). L302 sequenceDiagram for kubectl apply to running container (fine, keep). L433 GPU cluster topology (fine, keep). None flagged for redraw.
SVG specs (v5_03.json): k03-allocatable (Node Capacity/Allocatable), k03-etcd-topology (L334 stacked vs external), k03-kubelet-timeline (L346 failure table, 0/40/340 s), k03-quorum (L144 etcd quorum table). Anchors verified unique.
Raster candidates: none.

## ch04 (part-05 04-bare-metal-kubernetes-from-scratch-with-kubeadm-lab.md)
Topic: planning and building a kubeadm cluster by hand (node prep, containerd, kubeadm init phases, CNI, join, HA with kube-vip, GPU worker, troubleshooting).
Mermaid: 1 block (L311 kubeadm init phase chain, 6 steps, linear). Fine, keep. No redraw flagged.
SVG specs (v5_04.json): k04-cidr-blocks (L55 CIDR plan), k04-join-trust (L379-400 join token and CA hash), k04-layers-debug (L698 troubleshooting order). Anchors verified unique.
Raster candidates: none.

## ch05 (part-05 05-the-api-server-and-etcd-how-a-request-becomes-cluster-state.md)
Topic: API surface (groups, verbs), request pipeline, resourceVersion and concurrency, write operations and SSA, audit and auth, APF, etcd internals (Raft, MVCC, compaction, defrag, encryption at rest, backup), scaling levers, saturation table.
Mermaid: 1 block (L95, request pipeline flowLR, 9 nodes). Clear, keep. No redraw flagged.
SVG specs (v5_05.json): k05-conflict (L144, 409 swimlane), k05-raft-write (L266 write path, numbered), k05-apf (L200 FlowSchema to PriorityLevel to shuffle-sharded queues), k05-compact-defrag (L274). Anchors verified unique.
Raster candidates: none.

## ch06 (part-05 06-controllers-and-the-reconcile-loop-how-kubernetes-thinks.md)
Topic: controller pattern, informers and work queues, built-in controllers (Deployment, StatefulSet, DaemonSet, Job, node lifecycle, EndpointSlice), ownerReferences, finalizers, conditions, leader election, failure modes, safe automation.
Mermaid: 1 block (L59 informer -> work queue -> reconcile flow, 7 edges). Clear, keep. No redraw flagged.
SVG specs (v5_06.json): k06-deploy-chain (L100 Deployment/ReplicaSet shift), k06-quarantine (L179 label removal, orphan and replace), k06-lease (L215 timings 2/10/15 s). Anchors verified unique.
Raster candidates: none.

## ch07 (part-05 07-pods-and-workloads-deployments-statefulsets-daemonsets-and-jobs.md, 1921 lines, read in full)
Topic: pod anatomy (init, native sidecars, ephemeral containers), resources/QoS/OOM, volumes, env, securityContext, termination and probes, label/annotation selectors, controller choice (Deployment, StatefulSet, DaemonSet, Job, CronJob), rollout commands, PDB, GPU sizing, lab, checkpoint questions.
Mermaid: 1 block (L62 pod lifecycle flowchart TD: sandbox, init, native sidecars, app, termination). Grep earlier suggested 5; the fence count is 1. Keep it. Do NOT redraw the termination sequence (k07 has no termination figure) because the mermaid already covers it in node 4.
SVG specs (v5_07.json): k07-rollout-shift (anchor L823 Controlling Deployment rollouts), k07-statefulset-identity (L875 StatefulSet example), k07-daemonset-reconcile (L953 DaemonSet scheduling and reconciliation). Anchors verified unique with grep -cxF.
Skipped on purpose: label selector table, Job completions/parallelism table (already tables), work-queue producer/consumer (text-only, kept to 3 figures).
Raster candidates: none.

## ch08 (part-05 08-the-life-of-a-pod-end-to-end-including-what-the-kernel-does.md, 551 lines, read in full)
Topic: end-to-end pod trace from apply to running and termination; admission and scheduling; kubelet syncPod, PLEG, volumes, device plugin; sandbox, pause and CNI ADD; image pull and container create; kernel artefacts; running state; termination; startup latency measurement; debugging by stage.
Mermaid: 1 block (L49 sequenceDiagram, 20 autonumbered steps from create Pod to remove Pod object). Keep. Do NOT redraw: it already covers the whole lifecycle including termination (L77-80), so no separate termination or hand-off figure.
SVG specs (v5_08.json): k08-sandbox-network (anchor L140 "## 4. Sandbox creation and networking"), k08-namespace-map (anchor "## 5. Images and containers"), k08-gpu-isolation (anchor "### GPU specifics"). Anchors verified unique with grep -cxF.
Skipped on purpose: termination endpoint-vs-preStop race (text only; mermaid covers termination), debugging-by-stage table (already a table), startup latency intervals (table).
Raster candidates: none.

## ch09 (part-05 09-the-kubelet-and-the-node-cri-cgroups-qos-classes-probes-and-eviction.md, 737 lines, read in full)
Topic: kubelet responsibilities and hub, production KubeletConfiguration for GPU nodes, cgroup tree and QoS, node allocatable, CPU/memory/topology/device managers, probes, node-pressure eviction, OOMKilled, GC and logs, node leases, static pods, kubelet API security, observability, troubleshooting, tuning checklist, checkpoint questions.
Mermaid: 1 block (L41 flowchart TB, kubelet hub: pod sources, PM, PW, VM, DM, CRI, PLEG, status, eviction, GC, cAdvisor, lease, kubelet API). Keep. Do NOT redraw: it is the kubelet component map; the cgroup tree and eviction ordering are separate concepts.
SVG specs (v5_09.json): k09-cgroup-tree (anchor L161 "### The hierarchy (cgroup v2, systemd driver)"), k09-eviction-order (anchor L341 "## 6. Node-pressure eviction"), k09-startup-gate (anchor L289 "### A startup probe sized for a model load"). Anchors verified unique.
Skipped on purpose: Capacity minus reservations bar (already drawn as k03-allocatable in v5_03 for the same concept, so not repeated), CPU manager shared vs static (text), topology policy table (table), probe table (table).
Raster candidates: none.

## ch10 (part-05 10-services-endpoints-and-kube-proxy-the-life-of-a-service.md, 1009 lines, read in full)
Topic: Service types and fields, DNS and env var pitfalls, readiness gating, EndpointSlices, kube-proxy modes (iptables, IPVS, nftables, eBPF), NodePort/LoadBalancer paths, externalTrafficPolicy, session affinity and gRPC pinning, conntrack, topology routing, debugging ladder, scaling, checkpoint questions.
Mermaid: 1 block (L468 flowchart LR, mode comparison: iptables/nftables, IPVS, Cilium eBPF socket-LB). Keep. Do NOT redraw the forward iptables DNAT path as its own figure: the mermaid already shows Pod -> PREROUTING -> KUBE-SEP DNAT + conntrack. A return-path (un-NAT) figure would overlap, so it was skipped.
SVG specs (v5_10.json): k10-endpoint-slices (anchor L220 "## 2. EndpointSlices"), k10-traffic-policy (anchor "### `externalTrafficPolicy`"), k10-grpc-pinning (anchor "### Session affinity and long-lived connections"). Anchors verified unique with grep -cxF.
Skipped on purpose: mode comparison table (already a table and mermaid), conntrack fill (text), debugging ladder (code block plus table).
Raster candidates: none.

## ch11 (part-05 11-dns-and-service-discovery-with-coredns.md, 621 lines, read in full)
Topic: records CoreDNS creates, resolv.conf and dnsPolicy, ndots:5 query amplification, CoreDNS Corefile and plugins, scaling, NodeLocal DNSCache, conntrack/UDP 5-second race, distributed rendezvous discovery, observability, debugging method, checkpoint questions.
Mermaid: 1 block (L159 flowchart LR, pod resolver -> NodeLocal DNSCache -> CoreDNS -> kubernetes / forward). Keep. Do NOT redraw: it covers the resolution path; the three figures below are the mechanisms it does not show (query walk, race, deadlock).
SVG specs (v5_11.json): k11-ndots-walk (anchor "### The ndots:5 problem" at L128), k11-conntrack-race (anchor "### The conntrack/UDP race and 5-second delays"), k11-rendezvous-deadlock (anchor "## 5. DNS-based discovery for distributed AI workloads"). Anchors verified unique with grep -cxF.
Skipped on purpose: dnsPolicy table, Corefile plugin table, metrics dashboard (text and tables), debugging ladder (numbered steps and table).
Raster candidates: none.

## ch12 (part-05 12-ingress-load-balancers-and-the-gateway-api.md, 1034 lines, read in full)
Topic: L4 vs L7 layers, Ingress resource, controllers and Contour, host and path routing and precedence, annotations, TLS and cert-manager, Gateway API roles and HTTPRoute, bare-metal LBs (MetalLB, kube-vip), LLM/streaming edge design, status-code debugging, checkpoint questions.
Mermaid: 1 block (L51 flowchart LR, clients -> edge -> L7 gateway -> Service -> pods, with a canary branch). Keep. Do NOT redraw: it covers the layer path; the three figures below cover mechanisms it does not (precedence rule, persona ownership and ReferenceGrant, streaming timers).
SVG specs (v5_12.json): k12-path-precedence (anchor "### Routing by path"), k12-gateway-roles (anchor "## 3. Gateway API"), k12-stream-timers (anchor "## 6. Designing the edge for AI/LLM traffic"). Anchors verified unique with grep -cxF.
Skipped on purpose: status-code table (table), TLS/cert-manager flow (text plus YAML), controller table, dedicated edge node pool (text, DaemonSet pattern), L4 vs L7 layers (covered by mermaid).
Raster candidates: none.

## Summary v5 ch07-12
Files: v5_07.json (3 specs), v5_08.json (3), v5_09.json (3), v5_10.json (3), v5_11.json (3), v5_12.json (3). Total 18 specs. Mermaid blocks: 1 per chapter (6 total), none flagged for redraw.

## ch13 (part-05 13-pod-networking-under-the-hood-veth-bridges-routes-and-cni-plugins.md)
Topic: Kubernetes network model, hand-built pod network (netns, veth, cni0 bridge, MASQUERADE), multi-node options, CNI spec and conflist chaining, implementation families table, MTU math, Multus/SR-IOV/RDMA secondary networks, troubleshooting matrix.
Mermaid: 1 block (L100 multi-node flowchart with the three cross-node options). Keep; it is the chapter's core cross-node map. No redraw.
SVG specs (v5_13.json): k13-veth-bridge (L62 script, section 2), k13-cni-chain (conflist and env vars, section 3), k13-mtu-budget (section 5), k13-multus-attach (Multus annotation to net1/net2, section 6).
Raster candidates: none.

## ch14 (part-05 14-overlay-versus-routed-pod-networking-vxlan-bgp-with-calico-ebpf-with-c.md)
Topic: decision frame table, VXLAN/Geneve/IPIP/WireGuard overlays, routed BGP designs (Calico mesh vs route reflectors vs ToR eBGP), Cilium eBPF concepts (identity, hooks, kube-proxy replacement, host routing, encryption, Hubble), Helm profiles, comparison table, GPU-cluster choice, benchmarks, migration.
Mermaid: 2 blocks. L69 sequenceDiagram (one VXLAN packet from Pod A to Pod B) and L107 flowchart (leaf-spine eBGP topology with ASNs). Both keep; do NOT redraw them. The new bgp-sessions figure covers session counts, not the topology, so it does not duplicate L107.
SVG specs (v5_14.json): k14-bgp-sessions (section 3, session counts), k14-identity-policy (section 4 Concepts), k14-socket-lb (section 4 Socket-LB, anchored on the H2 "## 4. Cilium and eBPF").
Source inconsistency to flag to author: route-reflector session count is 1,494 in exercise 3 but 1,500 (3 x 500) in checkpoint 5. Spec uses 1,494 per exercise 3.
Raster candidates: none. Section 5 comparison table is a table, not a figure; no figure.

## ch15 (part-05 15-networkpolicy-and-the-kernel-netfilter-conntrack-and-ebpf.md)
Topic: NetworkPolicy API and additive semantics, selector AND/OR, default-deny baseline, kuard proof, traps table, kernel enforcement (Calico iptables/ipset, Cilium eBPF maps, conntrack), extended policies (Calico GlobalNetworkPolicy, CiliumNetworkPolicy, AdminNetworkPolicy), multi-tenant GPU design, debugging.
Mermaid: 1 block (L313 flowchart: CT check, then AdminNetworkPolicy, NetworkPolicy, BaselineAdminNetworkPolicy). Keep. Do NOT redraw; the new figures do not repeat the decision order.
SVG specs (v5_15.json): k15-selector-and-or (section 1 selector semantics, AND vs OR), k15-deny-proof (kuard three-step test, section 1 "Proving a default deny").
Considered and skipped: conntrack survival (already encoded in the L313 flowchart's ALLOW-on-established branch); a both-ends-must-allow figure (only a single sentence in the text, no mechanism section).
Raster candidates: none.

## ch16 (part-05 16-configuration-secrets-and-rbac.md, 1557 lines)
Topic: ConfigMaps (consumption doors, live-update behaviour, immutable, key rules), Secrets (five protection layers, tmpfs, consumption models, Vault injector, Sealed Secrets, CSI driver, GitOps patterns), projected volumes, ServiceAccount tokens and TokenReview, PSAT, authentication (certs, OIDC, static files, CSR), RBAC objects, verbs, escalation paths, impersonation, auditing, design patterns, troubleshooting table.
Mermaid: 1 block (L111 flowchart: Secret and config lifecycle subgraph plus RBAC subject-binding-role subgraph). Keep. Do NOT redraw; the new figures cover the update behaviour, the TokenReview exchange, rotation and impersonation, which the mermaid does not show.
SVG specs (v5_16.json): k16-config-doors (section 1 ConfigMaps, three consumption doors with update behaviour), k16-tokenreview (section 3, TokenReview swimlane), k16-two-phase-rotation (section 2 Rotation, anchored on the H3 "### Rotation"), k16-impersonate-sudo (section 5 impersonation pattern).
Source defects to flag to author:
- Duplicate H2 heading "## 6. Configuration management patterns for AI workloads" appears twice (lines 1243 and 1245). Anchor avoided. Remove one copy.
- Checkpoint 2 says kubelet sync is ~60-120 s; the body says about 1 to 2 minutes. Consistent, no action.
- Checkpoint 7 says kubelet rotates the bound token at 80% of lifetime; body only says refreshed automatically. Not used in any figure.
Considered and skipped: RBAC/secret lifecycle (covered by L111 mermaid); the Vault injector annotation list (text, not a mechanism diagram); the authentication methods list (a list, not a flow).
Raster candidates: none.

## ch17 (part-05 17-storage-internals-volumes-pv-and-pvc-csi-and-mounts.md, 783 lines)
Topic: volume types and lifetimes, block/file/object, PV/PVC/StorageClass model (binding, reclaim, binding modes, access modes, expansion, snapshots), external Postgres/StatefulSet patterns, CSI architecture and sidecars, seven-step lifecycle, multi-attach, fsGroup, CSIDriver/CSINode, mount mechanics, AI storage pattern table, throughput arithmetic, troubleshooting table, data protection.
Mermaid: 2 blocks. L71 flowchart (pod to PVC to PV to StorageClass to backend) and L297 flowchart (CSI controller and node services with sidecars). Both keep; do NOT redraw. The new k17-csi-handoffs is a time-ordered swimlane of the same system (sequence, not topology), so it is not a duplicate of L297.
SVG specs (v5_17.json): k17-lifetime-boxes (section 1, nested lifetimes), k17-csi-handoffs (section 3 Lifecycle, seven steps), k17-mount-stack (section 4, device to staging to pod bind mount).
Considered and skipped: multi-attach (paragraph analogy only, no heading); the AI storage pattern table (a lookup table); the Immediate vs WaitForFirstConsumer contrast (prose analogy only, could be a figure in future but adds a 4th figure over the cap).
Raster candidates: none.
Note: chapter text says CSI sidecars include the 6 listed in the prereq bullet (livenessprobe too); no action.

## ch18 (part-05 18-scheduling-in-depth-kube-scheduler-affinity-taints-priority-and-preemp.md, 844 lines)
Topic: scheduler model and cycle, queues, Filter/Score/Bind, KubeSchedulerConfiguration profiles, resource fit and fragmentation, nodeSelector/affinity/anti-affinity/topology spread, taints and tolerations, PriorityClass and preemption, PDB, gang scheduling (Kueue, Volcano, coscheduling, JobSet), topology and DRA, descheduling and tuning, debugging table, GPU platform patterns.
Mermaid: 1 block (L52 flowchart of the scheduling queues and cycle). Keep. Do NOT redraw; the new figures do not repeat the queue or cycle stages.
SVG specs (v5_18.json): k18-gang-deadlock (section 5, two 4-pod jobs on six nodes, default vs Kueue), k18-fragmentation (section 2, LeastAllocated vs MostAllocated over four 8-GPU nodes; numbers from checkpoint 4), k18-taint-toleration-selector (section 3 Taints and tolerations, three-column trap).
Considered and skipped: priority tier lanes (text analogy, no mechanism flow); the nodeSelector/affinity OR-AND rule (a text rule, better as a table).
Raster candidates: none.
Source defect to flag: the chapter's section 9 and checkpoint 20 give 20-node FailedScheduling counts that sum to more than 20, which the text explains as overlapping reasons; no action needed for the figures.
Raw count gap: the descheduler checkpoint mentions the annotation descheduler.alpha.kubernetes.io/evict; not used in figures.

## ch19 (part-05 19-cluster-deployment-models-and-day-2-operations.md, 657 lines, read in full)
Topic: deployment models (managed, GPU cloud, kubeadm/Kubespray, distributions, CAPI, vendor-integrated), tiers, topology table, node pools, cluster sizing and etcd thresholds, node lifecycle, drain and checkpoint, capacity and quota, add-on lifecycle, SLOs and runbooks, Cluster API hub versus pivot.
Mermaid: 1 block (L202 stateDiagram-v2 node lifecycle: Provisioned to Ready, Cordoned, Draining, Quarantined). Keep; do NOT redraw.
SVG specs (v5_19.json): k19-checkpoint-drain (section 3 Draining and maintenance, four-step checkpoint flow), k19-capi-pivot (section 8, hub-and-spoke versus pivoted), k19-etcd-scale (etcd colocated versus dedicated thresholds 50 and 200; distinct from k03-etcd-topology, which is the stacked-versus-external layout).
Considered and skipped: deployment model table and topology table (tables); the tier list (text); the cordon/drain bash block (commands, not a flow); the capacity three-number comparison (text, could be a figure later).
Raster candidates: none.

## ch20 (part-05 20-upgrades-etcd-backup-and-restore-and-disaster-recovery.md, 700 lines, read in full)
Topic: version skew and API deprecation, upgrade planning checklist and strategies, kubeadm upgrade block, GPU stack order, etcd snapshot backup, restore scenarios A to E, Velero and layered data protection, DR tiers (RPO/RTO), failure table.
Mermaid: 1 block (L114 flowchart TD upgrade order: pre-flight, cp1, cp2 and cp3, add-ons, canary pool, rolling fleet). Keep; do NOT redraw. The new figures do not repeat the stage order.
SVG specs (v5_20.json): k20-skew-ladder (section 1, component lag limits), k20-restore-decision (section 5 Restore scenarios, quorum decides replace versus restore), k20-quorum-trap (section 2 Upgrade strategies in detail, subtractive 3 to 2 to 3 versus additive learner).
Anchor note: "### Restore scenarios" is also where the snapshot rewind story sits (noon snapshot, 2 to 8 replicas, ConfigMap lost). Not drawn: a second figure there would need the same anchor. Could be a future timeline figure if placement is relaxed.
Considered and skipped: kubeadm command block (covered by the mermaid stages); the backup layers table and Velero commands (table and commands); DR tier RPO/RTO (text and table); failure scenario table (table).
Raster candidates: none.

## ch21 (part-05 21-certificates-identity-admission-control-and-policy.md, 1528 lines, read in full)
Topic: kubeadm PKI and CA trust domains, cert renewal and CA rotation, kubelet TLS bootstrapping and CSR approval, workload mTLS, OIDC and IRSA versus kube2iam and kiam, SPIFFE and SPIRE, admission chain and webhook config, Pod Security Standards, kube-bench, Kyverno, Gatekeeper, VAP, guardrail table, troubleshooting table.
Mermaid: 1 block (L55 flowchart TB, PKI signing tree). Keep; do NOT redraw. The new figures show the request path, CSR paths and identity flow, not the signing tree.
SVG specs (v5_21.json): k21-admission-chain (section 3, request path to etcd), k21-csr-paths (section 1, kubelet TLS bootstrapping, auto client versus checked serving), k21-pod-identity-evolution (section 2, kube2iam to kiam to IRSA), k21-spire-attestation (section 2, node then workload attestation).
Anchor check: "### Cloud metadata proxies..." and "### Cross-platform..." verified unique with grep -cxF.
Considered and skipped: the Pod Security Standards table and the three-level ladder (table); the Gatekeeper ConstraintTemplate flow (code and text); the guardrail set table (table); the troubleshooting table (table); the CA rotation overlap (text, a figure would be a 4th over the cap).
Raster candidates: none.

## ch22 (part-05 22-multitenancy-and-platform-services.md, 973 lines, read in full)
Topic: tenancy models and trust levels, isolation layers, namespace building blocks (quota, LimitRange, RBAC, priority, GPU sharing options, node isolation), HNC, Capsule, vCluster, self-service onboarding, abstraction spectrum and Team operator, platform services table, application platform concepts, cost showback, troubleshooting, lab, checkpoint.
Mermaid: 1 block (L75 flowchart TD tenant onboarding fan-out: identity, compute and GPU, network and storage, observability). Keep; do NOT redraw.
SVG specs (v5_22.json): k22-abstraction-spectrum (section 4, four developer-abstraction stages with break-glass door; anchor is the Team operator and spectrum heading), k22-cohort-borrow (section 2 Priority and fair sharing, Kueue cohort borrow and preempt).
Considered and skipped: soft versus hard tenancy table and isolation layers table (tables); GPU sharing methods table (table, the kitchen analogy is text); vCluster versus namespace (analogy text, a figure would be a third one over the cap of 4 is fine but low value); the Team operator reconcile rule (text, anchor shares the spectrum heading); the showback methods (text and PromQL).
Raster candidates: none.

## ch23 (part-05 23-autoscaling-hpa-vpa-keda-and-the-cluster-autoscaler.md, 792 lines, read in full)
Topic: layers of autoscaling, HPA formula and behavior, metric types, inference signals, prometheus-adapter rules, CPA, VPA modes, KEDA ScaledObject and ScaledJob, cluster autoscaler and expanders, overprovisioning pause pods, Karpenter, ProvisioningRequest, AI workload pattern table, troubleshooting, lab, checkpoint.
Mermaid: 1 block (L50 flowchart TB, layers from metrics to HPA, VPA, pending pods, CA, nodes, scheduler, scale-down). Keep; do NOT redraw. The new figures do not repeat the layer chain.
SVG specs (v5_23.json): k23-overprovision-preempt (section 5 Cluster overprovisioning, pause pods preempted then buffer rebuilt), k23-gang-atomic (section 5 Atomic capacity, pod-by-pod versus ProvisioningRequest), k23-scale-down-window (section 2 Behaviour tuning, stabilization window keeps the highest recent recommendation).
Considered and skipped: the spike walkthrough timeline in section 1 (the mermaid already shows the same chain; a timed version would duplicate it); HPA formula (one line, text); the metric source table (table); the VPA modes (table and text); KEDA light-switch analogy (text); the inference signal table (table).
Raster candidates: none.

## ch24 (part-05 24-observability-for-kubernetes.md, 1046 lines, read in full)
Topic: observability signals and RED/USE/golden signals, Prometheus model and Operator CRDs, kube-prometheus-stack, PromQL, alert design and burn rates, Alertmanager, GPU alerts, log pipeline and Loki labels, Kubernetes events, OpenTelemetry and tracing vocabulary, dashboards, cardinality, retention and security, diagnosis flows, lab, checkpoint.
Mermaid: 1 block (L66 flowchart LR, GPU worker node pipeline: exporters to Prometheus, Thanos or Mimir, Alertmanager, Fluent Bit to Loki). Keep; do NOT redraw. The new log figure shows the detailed log path (stages inside the node agent, label card), which the mermaid only sketches as one arrow.
SVG specs (v5_24.json): k24-alert-routing (section 3 Alertmanager, group, inhibit, silence, route to page, ticket, Watchdog), k24-log-path (section 4 Architecture, stdout to Loki with four labels), k24-trace-handoff (section 5 Instrumenting services, header handoff and span nesting), k24-burn-windows (section 3 Principles, 1 h and 5 min windows and the 14.4 threshold).
Considered and skipped: the signal table and RED/USE text (table and analogy); the Prometheus pull model (text, the mermaid covers the pipeline); the PromQL block (code); the diagnosis decision tree in section 8 (a text tree in a code block that a figure would repeat, not drawn); the dashboard list (list).
Raster candidates: none.

## ch25 (part-05 25-troubleshooting-kubernetes-from-the-node-crictl-nsenter-tcpdump-and-ip.md, 553 lines, read in full)
Topic: symptom-to-layer method and scope, kubectl toolkit and debug modes, node tools (crictl paths, nsenter into pod namespaces, networking and capture, storage, processes, GPU hardware), failure playbooks (Pending, ContainerCreating, CrashLoopBackOff, network, NotReady, OOM, Terminating, DNS, storage, GPU table, control plane), chaos, evidence, lab, checkpoints.
Mermaid: 1 block (L44 flowchart TD, symptom to scope to layer to hypothesis). Keep; do NOT redraw. The figures show the capture path, the nsenter room and the OOM scopes, not the layer tree.
SVG specs (v5_25.json): k25-capture-points (section 3.3, client veth, node uplink, server veth), k25-nsenter-room (section 3.2, host tools via nsenter -n), k25-oom-scope (section 4.6, CONSTRAINT_MEMCG versus CONSTRAINT_NONE).
Considered and skipped: 4-hop bisection (only in checkpoint 6 text, a figure would be a fourth and duplicates the order text); exit code table and 128+N (text and checkpoint list); GPU symptom table (table); the Terminating finalizer flow (text); the playbook steps (lists).
Raster candidates: none.

## ch26 (part-05 26-how-kubernetes-uses-the-linux-kernel-a-complete-map.md, 607 lines, read in full)
Topic: master map from Kubernetes concepts to kernel features and inspection commands, namespaces (pause, shared net/ipc/uts, pid 1 signals), cgroups v2 controllers and CFS throttling arithmetic, memory categories and working_set, security primitives (capabilities, no_new_privs, seccomp, LSMs), overlayfs copy-up, mounts and tmpfs, block/NFS/FUSE, netfilter/conntrack/eBPF/tc, CPU/NUMA, GPU/RDMA device stack, kernel versions, boot params and sysctl baseline, observability tools, failure-to-kernel table, lab, checkpoints.
Mermaid: 1 block (L48 flowchart TB, Kubernetes concept to Linux kernel feature). Keep; do NOT redraw. The master map is the same concept as the first figure, so the new figures show one mechanism each (shared pod namespaces, CFS period, overlay copy-up).
SVG specs (v5_26.json): k26-pod-namespaces (section 2, pause holds net/ipc/uts, each container has mnt and pid), k26-cpu-throttle-period (section 3, 8 threads drain 200 ms in 25 ms, 75 ms stall), k26-overlay-copy-up (section 5, lowerdir/upperdir/workdir and whole-file copy-up).
Considered and skipped: the master map table (table, duplicates the mermaid); memory categories and working_set (text and checkpoint list; a stacked-bar figure was an option but the chapter lists them as text); security primitives (lists); sysctl block (code); observability and failure table (tables); the device filter and GPU module stack (lists in text).
Raster candidates: none.

## ch27 (part-05 27-software-supply-chain-security.md, 770 lines, read in full)
Topic: threat model and six attack classes, frameworks (SLSA, in-toto, Sigstore, Notary v2), source and build controls, Tekton and buildpacks, SBOMs, scanning and VEX, cosign keyless and key-based signing, Kyverno verifyImages, quarantine and promotion, registries, Python and ML dependency hygiene, model and data supply chain, runtime controls, incident response, maturity table, lab, checkpoints.
Mermaid: 2 blocks. L48 flowchart LR (source to runtime threat model with A1..A6 attack points) and L411 flowchart LR (upstream image to quarantine, scan, policy, sign, promote, admission). Keep both; do NOT redraw. The promotion mermaid already covers the quarantine flow, so the new figures do not repeat it.
SVG specs (v5_27.json): k27-keyless-signing (section 2, CI job, OIDC token, Fulcio, Rekor, ephemeral key), k27-admission-two-checks (section Admission-time enforcement, who built it versus where it came from), k27-pickle-vs-safetensors (section 8, __reduce__ runs on load versus JSON header plus raw bytes).
Considered and skipped: the Kyverno YAML (code); the Tekton manifests (code); the SBOM/VEX triage (text); the Golden Base Images antipattern (text, the two problems are prose); the maturity table (table); the incident response six steps (numbered list); the GitOps push versus pull (text).
Raster candidates: none.

## ch28 (part-05 28-service-mesh.md, 798 lines, read in full)
Topic: what a mesh provides and its three pillars, control plane and data plane, SPIFFE identity and mTLS, data-plane models (sidecar, node proxy, ambient, eBPF, proxyless, library, gateway-only), Istio resources (PeerAuthentication, AuthorizationPolicy, DestinationRule, VirtualService, Sidecar), Envoy listener/filter/route/cluster and xDS, istiod injection, Linkerd, Cilium, SMI, mTLS rollout, canary/mirror/retries/outlier detection, observability, costs, native sidecars and Job lifecycle, protocol sniffing, exclusions for NCCL and storage, when not to use a mesh, lab, checkpoints.
Mermaid: 1 block (L54 flowchart LR, control plane CA/config/policy and two sidecar pods with mTLS). Keep; do NOT redraw. It shows the architecture; the new figures show the Envoy request path, retry load, and sidecar start/stop order, not the box diagram.
SVG specs (v5_28.json): k28-envoy-route-path (section Envoy and the xDS APIs; listener, filter chain, route, cluster, endpoints, xDS feeds), k28-retry-doubling (section Traffic management for model rollouts; retry once doubles load, attempts 0 for POST), k28-native-sidecar-order (section 7 Startup and shutdown ordering; regular sidecar versus native sidecar lifecycle).
Considered and skipped: the iptables interception path (section 1 bullet 2; overlaps the L54 mermaid's app-to-sidecar and mTLS links, so not drawn); Istio YAML (code); the canary 90/10 DestinationRule and VirtualService (code); the data-plane comparison table (table); the SMI TrafficSplit/TrafficTarget (code); the memory arithmetic for 5,000 pods (one arithmetic line); RESPONSE_FLAGS (list); the when-to-use decision (text).
Raster candidates: none.

## ch29 (part-05 29-extending-kubernetes-crds-and-operators.md, 947 lines, read in full)
Topic: extension points table, CRD anatomy (GPUHealthPolicy example and WebApp example), kinds and resources, schema, pruning, CEL, subresources (status, scale), versions and conversion with storage migration, ownerReferences and finalizers, status and conditions, API design rules, operator pattern and Operator Framework capability levels, reconcile structure, operator use cases and implementation choices, Python kubernetes client patterns, API groups, create/replace/patch, watch, pods logs/exec/port-forward, packaging and OLM, CRD upgrades, least-privilege RBAC, failure modes, AI-platform operator table, lab, mistakes, interview, exercises, checkpoints.
Mermaid: 1 block (L403 flowchart TB, operator reconcile structure with requeue paths). Keep; do NOT redraw. The reconcile flow is already drawn, so the figures show the object fan-out, the finalizer cleanup split, and the schema gate.
SVG specs (v5_29.json): k29-webapp-fanout (section 2 Kinds and WebApp example, one object to six children), k29-owner-vs-finalizer (section 2 Garbage collection, ownerReferences versus finalizers and the uninstall trap), k29-schema-gate (section 2 Schema and validation, enum refusal and default fill).
Considered and skipped: the GPUHealthPolicy CRD YAML (code); the extension points table (table); the create/replace/patch table (table); the Python client snippet (code); the AI-platform operator table (table); the capability levels table (table); the webhook request-path list (airport analogy text, a figure would partly duplicate chapter 5.21); the storage version four-step procedure (numbered text, a timeline was an option but the checkpoint covers it in text); the watch versus polling analogy (text).
Raster candidates: none.

## ch30 (part-05 30-go-for-kubernetes-engineers.md, 1022 lines, read in full)
Topic: toolchain and module layout, Go language subset (types, interfaces, errors, slices and maps, pointers, packages), concurrency (goroutines, channels, sync, context), JSON/YAML and Kubernetes types, scheme and RESTMapper, client-go (clients, CRUD and patch and apply, watch, informers and work queues, leader election, dynamic client, logging and metrics), nodectl CLI walkthrough, testing (table tests, fake clientset, envtest), packaging with distroless, idioms and pitfalls table, lab, interview angles, exercises, checkpoints.
Mermaid: 1 block (L375 flowchart LR, Reflector to DeltaFIFO to Indexer to WorkQueue to workers). Keep; do NOT redraw. The informer pipeline is already drawn, so the figures show the update options, the bounded probe fan-out and the error wrap chain.
SVG specs (v5_30.json): k30-change-three-ways (section 5 CRUD, patch, apply; Update conflict, RetryOnConflict, merge patch), k30-bounded-probes (section 3 Goroutines; sem of 16, results channel, WaitGroup close), k30-error-wrap-chain (section 2 Errors; %w wrap, errors.Is and errors.As).
Considered and skipped: the informer and work-queue handler code (the mermaid covers the pipeline); the leader election Lease code (code); the Go type and struct listings (code); the generics and slice gotchas (text); the Resource.Quantity suffix table (table); the GVK versus GVR translation (text and a table); the Dockerfile (code); the idioms table (table); the watch 410 Gone handling (code).
Raster candidates: none.

## ch31 (part-05 31-operators-in-go-controller-runtime-and-kubebuilder.md, 975 lines, read in full)
Topic: controller-runtime layers (manager, shared cache, caching client, queue), kubebuilder markers and controller-gen, API design rules, manager options, Reconcile signature and return patterns, status guard, watches and predicates, field indexes, owner references and finalizers, provenance annotation, events and metrics, RBAC, webhooks (admission handler, plain HTTPS), testing layers, hardening table, mistakes, lab, checkpoints.
Mermaid: 1 block (L48 flowchart TB, operator process: manager, cache, client, controllers, webhook, leader election, API server). Keep; do NOT redraw. The figures cover the reconcile pass, the event path and the finalizer timeline, not the process layout.
SVG specs (v5_31.json): k31-reconcile-steps (section 4, Observe, Decide, Act, Report with the four return options), k31-event-filter (section 5, watch sources to predicates to queued key to Reconcile), k31-finalizer-flow (section 6, add finalizer, side effects, deletion timestamp, release, remove finalizer).
Placement note: the insert script puts a figure directly under a heading, so k31-reconcile-steps lands before the section 4 opening paragraph. Move it below the Observe/Decide/Act/Report code block if the opener should stay first.
Considered and skipped: the 3-step CreationInProgress crash recovery (text only, a figure would repeat the reconcile pass); the RBAC and marker lines (code); the return-option table (table); the webhook Handle flow (code, text is enough); the Metacontroller and Operator Framework comparisons (text).
Raster candidates: none.

## ch32 (part-05 32-project-a-gpu-node-health-operator.md, 754 lines, read in full)
Topic: GPU node health operator requirements, GPUHealthPolicy API and CEL rule, pure Judge/Budget/Plan core and decision table, the Reconcile ordered steps, cordon with provenance annotations, releaseAll and drain with eviction and PDB backoff, envtest scope and what the tests do not prove, failure modes, extensions, lab, checkpoints.
Mermaid: 1 block (L50 flowchart LR, detection to Node condition to Reconcile to Node, Pods, policy, events, RequeueAfter loop). Keep; do NOT redraw.
SVG specs (v5_32.json): k32-decision-pipeline (section "The decision core (pure)", Judge to Budget to Plan with the room count and act vs blocked), k32-window-timeline (section "The reconciler", condition False to Pending to RequeueAfter to cordon, then healthyFor to uncordon, no sleep), k32-provenance-release (section "Design decisions and why", owner annotation decides which cordon is released on policy delete).
Placement note: each figure lands directly under its heading, so k32-decision-pipeline sits before the decision-core intro paragraph and k32-window-timeline before the reconciler intro paragraph.
Considered and skipped: the decision table (table, already lists the eight rows); the Go helper signatures and the cordon snippet (code); the envtest scenario table (table); the failure-modes table (table); the drain and evictable filter (text and code).
Raster candidates: none.

## ch33 (part-05 33-reading-the-gpu-operator-and-network-operator-source.md, 567 lines, read in full)
Topic: method for reading an operator, GPU Operator repo map and controllers, ClusterPolicy flow and singleton, DaemonSet() eight-step apply and readiness (RollingUpdate vs OnDelete), node gating by deploy labels and workload config, validator file chain, driver DaemonSet vs NVIDIADriver CRD, the upgrade state labels, SetupWithManager predicates, Network Operator State interface, wait labels, secondary networks, comparison table, debugging recipes, lab, checkpoints.
Mermaid: 3 blocks. L92 flowchart TB (ClusterPolicy reconcile flow, singleton, states, RequeueAfter 5s). L158 sequenceDiagram (validator chain: driver, validator, toolkit, device plugin, kubelet). L238 flowchart TB (Network Operator reconcile, InfoCatalog, state manager, mofed.wait). Keep all three; do NOT redraw. The validator sequence is already the per-node chain, so no figure repeats it.
SVG specs (v5_33.json): k33-node-operand-gating (section 5, deploy labels and workload config select DaemonSets, gpuStateLabels table, operands=false), k33-upgrade-states (section 6, upgrade state label chain from upgrade-required to done or failed), k33-wait-compare (subsection "Wait labels", GPU Operator in-node init wait vs Network Operator scheduler wait).
Placement note: the figure sits directly under "## 5. Node gating and the validator chain", before its first paragraph.
Considered and skipped: the repo map tables (tables); the ClusterPolicy singleton rule (text); the DaemonSet() eight steps (numbered list, text); SetupWithManager predicate list (list); the secondary-network text; the debugging recipe table (table); the comparison table in section 10 (table, the k33-wait-compare figure covers only the wait row).
Raster candidates: none.

## ch34 (part-05 34-gke-for-gpu-workloads-setup-node-pools-and-quotas.md, 620 lines, read in full)
Topic: Standard vs Autopilot, GPU machine families, cluster and node pool creation flags, what GKE sets up after pool creation (driver DaemonSet, device plugin, labels, taint and automatic toleration), quota vs stockout and consumption models, Pod scheduling, GPU sharing (time-sharing, MPS, MIG, DRA), multi-node networking, autoscaling and upgrades, observability and cost, Terraform sketch, failure table, lab, checkpoints.
Mermaid: 1 block (L66 flowchart TD, five decisions: quota, cluster, GPU pool, multi-node fabric, scheduling and sharing). Keep; do NOT redraw.
SVG specs (v5_34.json): k34-pool-after-create (section 4 "What happens after creation", driver DaemonSet, nvidia.com/gpu, label and taint, automatic toleration), k34-sharing-walls (section 7, time-sharing, MPS and MIG as shared desk, shared room, separate offices), k34-spot-window (section 5, Spot preemption grace period and checkpoint window, two options), k34-gpu-nics (section 8, default VPC NIC vs GPU NICs to the fabric, gVNIC, multi-networking, compact placement).
Placement note: k34-spot-window lands under the "## 5." heading, before the quota-symptom table. The spot text sits later in that section, so move it below the consumption list if preferred.
Considered and skipped: the quota vs stockout table (table; the Mermaid already gives the decision order); the gcloud and Terraform code (code); the GPU-type and sharing tables (tables); the MIG single and mixed and DRA list (text, numbers in list); the failure table (table); the autoscaling and cost prose (text).
Raster candidates: none.

## ch35 (part-05 35-multicluster-and-fleet-management.md, 659 lines, read in full)
Topic: why more than one cluster and the driver table, foundations and automation, central identity, replicated silo and data consistency, management clusters and Cluster API autoscaler dependency, six layers of fleet management, provisioning and lifecycle, GitOps with Argo CD ApplicationSet and Flux, progressive sync, Kueue MultiKueue (dispatchers, credentials, limits), other tools table, cross-cluster networking options, identity and policy, observability, upgrade rings and soak, failure-domain table, lab, checkpoints.
Mermaid: 2 blocks. L130 flowchart TB (six fleet layers: provisioning, configuration delivery, placement, connectivity, identity and policy, observability and ops). L277 sequenceDiagram (MultiKueue job lifecycle, manager and workers W1 and W2). Keep both; do NOT redraw. The figures do not repeat either the layer stack or the MultiKueue sequence.
SVG specs (v5_35.json): k35-geodns-anycast (section "User traffic: GeoDNS and anycast", resolver caches vs one virtual IP advertised by BGP), k35-gitops-fanout (section 4, a new labelled cluster becomes one generated Application), k35-rings (section 9, canary to dev and staging to prod ring 1 to prod ring 2 with soak times and pause switch), k35-mgmt-autoscaler (subsection "Cluster federation and management clusters", central CAPI and autoscaler dependency vs self-contained CAPI).
Placement note: k35-gitops-fanout lands directly under "## 4. Configuration delivery with GitOps", before the ApplicationSet intro paragraph.
Considered and skipped: the MultiKueue lifecycle (already a sequence diagram); the layered mermaid (already drawn); the other-tools table and the networking options list (tables and lists); the identity and observability bullets (lists); the failure-domain table (table); the MultiKueue dispatcher and credential text (text).
Raster candidates: none.

## part-06 ch01 (06 01-what-a-supercomputer-is-top500-linpack-hpc-versus-ai-factory.md, 604 lines, read in full)
Topic: what makes a computer super (three definitions, orchestra analogy), nine levels of parallelism, pipeline cycle formula, FLOPS precision and Rpeak/Rmax/MFU, benchmark lists (TOP500, HPL, HPCG, Green500, IO500, MLPerf), HPC versus AI factory table, cluster types (HA, HTC, HPC), eight invariants, power-on hazards, command-line fleet checks, software stack, misconceptions, lab, checkpoints.
Mermaid: 1 block (L360 flowchart TB, user to login, scheduler, compute, apps, fabric, storage, management, facility). Keep; do NOT redraw. It is the stack map; the figures show the pipeline, the Rpeak/Rmax gap, and the startup order.
SVG specs (v6_01.json): h01-pipeline-conveyor (parallelism section, 104 vs 500 cycles), h01-rpeak-rmax (section 2, ceiling vs measured HPL), h01-power-on-order (power-on hazards and startup sequence).
Considered and skipped: the HA/HTC/HPC cluster-type table (a figure would repeat the table); the eight-invariant table (table); the benchmark table (table); the HPC versus AI factory table (table); the floor-area and utilization facts (text); the pdsh one-liner (code); the Python calculator (code).
Raster candidates: none.

## part-06 ch02 (06 02-cluster-anatomy-head-login-compute-storage-and-management-nodes.md, 548 lines, read in full)
Topic: four infrastructure layers, node roles (control, login, compute, service, storage), license and login-node rules, four networks, latency and fabric topologies (3D torus hop formula), DAS/NAS/SAN and RAID, SMP versus NUMA pinning, HyperThreading declaration trick, RDMA and RoCE, planning rules, documentation, post-build checks, runbook schema, job life cycle, Slurm-to-Kubernetes mapping, cloud note, lab.
Mermaid: 1 block (L58 flowchart TB, user to login, control node, compute field, shared storage, service nodes, BMC). Keep; do NOT redraw. It already shows the node-role path and side attachments.
SVG specs (v6_02.json): h02-job-lifecycle (section 6, five numbered steps from login to epilogue), h02-torus-ring (section 3, loop halves the far distance, 4+4+4=12), h02-numa-pinning (section 4, unpinned versus pinned process on two sockets).
Considered and skipped: the HyperThreading 256-to-128 declaration trick (three numbered steps, text is clear and the NUMA figure covers the core-binding idea); the four-layer anatomy list (text, overlaps the mermaid); the network latency table and RAID table (tables); DAS/NAS/SAN (text); the planning checklists, runbook columns and check lists (lists and tables); the Slurm-to-Kubernetes mapping (table).
Raster candidates: none.

## part-06 ch03 (06 03-parallel-computing-concepts-amdahl-scaling-shared-memory-versus-messag.md, 660 lines, read in full)
Topic: speedup and efficiency, Amdahl (strong scaling), Gustafson (weak scaling), Karp-Flatt, scaling script results, causes of stalled scaling table, programming models (MPI, OpenMP, PGAS/OpenSHMEM, CUDA, OpenCL, OpenACC, PMIx, UCX, NCCL), Hockney cost model, ring AllReduce volume, domain decomposition and halo exchange, ScaLAPACK/PETSc/FFTW/TBB, parallel debuggers and profilers, five communication patterns, lab, checkpoints.
Mermaid: 1 block (L210 flowchart TB, shared memory, distributed memory, accelerators, converging on hybrid MPI+X). Keep; do NOT redraw. It maps the model families; the figures show the serial floor, halo swaps and the ring phases.
SVG specs (v6_03.json): h03-amdahl-floor (section 2, fixed serial slice across 1 and 1,024 processors), h03-halo-exchange (section 9, neighbour swaps and the shrinking-block surface share), h03-ring-allreduce (section 8, ReduceScatter then AllGather on eight GPUs).
Considered and skipped: the Hockney latency-bandwidth crossover (formula and one number; the text covers it and it would be a bar chart); the MPI pi program seven-call list (table, and a sequence diagram would only restate it); the Gustafson versus Amdahl comparison (table); the parallel debugger and profiler table (table); the five communication patterns (list); the SLmake.inc and PETSc build snippets (code); the 8-core scaling run (table).
Raster candidates: none.

## ch07 (part-06 07-slurm-architecture-and-installation.md, 885 lines, read in full)
Topic: what a workload manager does, daemons (slurmctld, slurmd, slurmstepd, slurmdbd, slurmrestd, sackd, munge), job life from sbatch to accounting, plugin families, state and HA, munge auth, configless mode, planning and install methods, accounting tree, first slurm.conf, bring-up order, seven install failures, log patterns, lab.
Mermaid: 5 blocks (grep '^```mermaid' count 5). L113 daemon map (dense 15-node flowchart, keep, do NOT redraw); L170 sequenceDiagram of one job from sbatch to accounting (keep, do NOT redraw); L267 HA primary/backup and slurmdbd pair (keep, do NOT redraw); L354 config-file hub around slurm.conf (keep); L431 account tree (keep). Flag for author: the L170 sequence draws direct C->>D1 and C->>D2 launches while section 3 text says launch goes through a TreeWidth RPC fan-out tree. Not redrawn here; figure skipped to avoid a second conflicting picture.
SVG specs (v6_07.json): h07-munge-credential (anchor "## 6. Authentication: munge, and its successor"), h07-bringup-order (anchor "## 11. Bringing it up, and verifying"), h07-upgrade-order (anchor "### Versions and upgrades"). Anchors to be verified unique with grep -cxF.
Skipped on purpose: TreeWidth RPC fan-out (text plus conflicting mermaid), daemon/port table, plugin family table, what-lives-where table, failure-mode list (section 12), log-pattern snippets, accounting tree (already mermaid).
Raster candidates: none.

## part-06 ch04 (06 04-mpi-in-practice-open-mpi-ranks-collectives-and-tuning.md, 589 lines, read in full)
Topic: MPI execution model (ranks, communicators, local rank), eager versus rendezvous protocols and send-send deadlock, collectives mapped to NCCL/DDP equivalents, thread levels, MPI implementation families, Open MPI MCA framework and five-level precedence, HCOLL and UCX tuning, launchers (srun --mpi=pmix, mpirun, torchrun), mapping/ranking/binding, CUDA-aware MPI and GPUDirect checks, OSU and nccl-tests bandwidth, four-layer hang ladder, lab, checkpoints.
Mermaid: 1 block (L162 flowchart TB, application, MCA plugins pml/coll/btl/runtime, UCX and SHARP). Keep; do NOT redraw. It is the Open MPI plugin architecture; the figures show the deadlock timeline and the debug ladder.
SVG specs (v6_04.json): h04-eager-deadlock (section 2, two blocking sends across two lanes, eager versus rendezvous), h04-debug-ladder (section 10, four layers in order).
Considered and skipped: the MPI collective-to-NCCL mapping table (table); the thread-level table (table); the MPI implementation history bullets (text); the mapping, ranking and binding steps (text, and the NUMA idea already has a figure in ch02); the GPUDirect three-check list (list); the algorithmic versus bus bandwidth formulas (formula); the launcher comparison (code and text); the NCCL interface prefix table (table).
Raster candidates: none.

## ch08 (part-06 08-slurm-configuration-nodes-partitions-and-cgroups.md, 472 lines, read in full)
Topic: config file layout (/etc/slurm, Include, 0644 vs 0600), node lines from slurmd -C, RealMemory margin, node states and sinfo suffix symbols, ReturnToService 0/1/2, partitions (attributes, four states, PriorityTier vs PriorityJobFactor, OverSubscribe), select/cons_tres and cgroup Constrain* flags, topology.conf and SwitchAsNodeRank, PrologFlags and SchedulerParameters, lint and gen scripts, interview angles, exercises, 20 checkpoints.
Mermaid: 1 block (L41 flowchart LR, config files to slurmctld and slurmstepd). Keep; do NOT redraw. The cgroup-fence figure below shows the controller-to-stepd split in lane form, and the mermaid only shows which file feeds which daemon, so the concept differs.
SVG specs (v6_08.json): h08-switch-rank (anchor "## 5. Topology awareness (...)"), h08-node-states (anchor "### Node states, state suffix symbols (...)"), h08-cgroup-fence (anchor "## 4. Resource selection (`select/cons_tres`) and cgroup containment"). Anchors to be verified unique.
Skipped on purpose: the sinfo suffix table and the partition-state list (both tables), PriorityTier vs PriorityJobFactor (table plus text), OverSubscribe table, PrologFlags/SchedulerParameters table, the 4-row ReturnToService bullet list (folded into the node-state figure as text only), lint error block (code output).
Raster candidates: none.

## part-06 ch05 (06 05-openmp-compilers-and-optimisation-flags.md, 497 lines, read in full)
Topic: OpenMP fork-join model, clauses and OMP_* variables, measured scaling (triad saturation versus sin/cos), NUMA first-touch and hybrid oversubscription, data races and false sharing, compiler families and flags, link order, FlexLM licence traps, CUDA driver setup, optimisation levels and -march=native and -ffast-math, floating-point reduction experiment, vectorisation reports, lab, checkpoints.
Mermaid: 1 block (L45 flowchart LR, master thread, fork, four threads on NUMA 0 and 1, implicit barrier join, serial continuation). Keep; do NOT redraw. It is the fork-join flow; the figures show the lost update, false sharing and first-touch placement, which the flow does not show.
SVG specs (v6_05.json): h05-race-lost-update (section 4, read-modify-write race on a shared counter), h05-false-sharing (section 4, neighbouring elements on one 64-byte line, padded fix), h05-first-touch (section 3, serial versus parallel initialization on two sockets).
Considered and skipped: the scaling measurement table and the -O flags and fast-math output (numeric tables); the compiler family table (table); the OMP_* variable table (table); the FlexLM licence traps (list); the CUDA install rules (list); the link-order rules (text and code); the hybrid oversubscription arithmetic (one line, the first-touch figure already covers placement).
Raster candidates: none.

## ch09 (part-06 09-slurm-accounting-and-scheduling-policy-qos-fairshare-backfill-preempti.md, 601 lines, read in full)
Topic: accounting model and associations, TRES and billing, AdminLevel and coordinators, limits and QOS flags, 6-level limit precedence, multifactor priority formula, Fair Tree and decay, backfill parameters, preemption modes, multi-team policy design (9 steps), sacct and sreport, pending-reason decision list, lab, interview angles, 20 checkpoints.
Mermaid: 1 block (L41 flowchart TB, sacctmgr association tree with usage and FairShare per user). Keep; do NOT redraw. Note it is close to the ch07 account-tree mermaid (ch07 L431) but shows usage and LF, so it is a different picture. The h09-fairtree-walk figure reuses the same tree and adds visit order, so if the author wants no repeat, drop that figure first.
SVG specs (v6_09.json): h09-fairtree-walk (anchor "### The simulator"), h09-backfill-gap (anchor "## 5. Backfill"), h09-preempt-flow (anchor "## 6. Preemption"). Anchors to be verified unique.
Skipped on purpose: the priority formula (code block, reads as a sum), 6-level precedence list (list, text), QOS flag table, decay numbers (8,000 to 4,000 to 2,000 to 500; text only), billing example (text), sacct/sreport commands (code), pending-reason list (list).
Raster candidates: none.

## part-06 ch06 (06 06-environment-modules-spack-and-easybuild.md, 545 lines, read in full)
Topic: how PATH and the dynamic loader find binaries and libraries (five-step search order), installing compilers on shared storage, Tcl Environment Modules and Lmod (commands, stderr rule, Core-Compiler-MPI hierarchy, module spider, version sorting), EasyBuild and Spack (specs, concretization hashes, environments, externals, buildcaches), the 11-step minicluster deployment, disk-cloning fixes, the shared /opt/apps tree, and where containers and conda fit.
Mermaid: 1 block (L75 flowchart TB, Core, Compiler and MPI MODULEPATH hierarchy with module load arrows). Keep; do NOT redraw. It already shows the hierarchy that Lmod reveals on load; the figures show the loader search order, the minicluster sequence and the shared tree layout.
SVG specs (v6_06.json): h06-loader-order (section 1, five ordered search locations), h06-minicluster-sequence (section 4, eleven steps in three phases with the clone fixes), h06-opt-apps-layout (section 4, read-only /opt/apps split by CPU baseline).
Considered and skipped: the Lmod inactive and auto-reload swap (overlaps the existing mermaid hierarchy; text covers it); the Tcl and Lua modulefile code (code); the module command table (table); the Spack spec operators and concretization (text and code); the EasyBuild and Spack command blocks (code); the containers-versus-conda rule table (table); the module spider output (code).
Raster candidates: none.

## ch10 (part-06 10-slurm-gpu-scheduling-gres-nvml-autodetect-mig-and-device-constraints.md, 468 lines, read in full)
Topic: GRES in slurm.conf and gres.conf, AutoDetect values, manual gres.conf fields (Cores, Links, File), request options (--gres vs --gpus vs --gpus-per-task), job environment variables and CUDA_VISIBLE_DEVICES renumbering, binding (closest, map, none, enforce/disable-binding), isolation with ConstrainDevices, MIG/MPS/sharding, GPU accounting, operations, troubleshooting table, lab, 10 interview angles, 20 checkpoints.
Mermaid: 1 block (L41 flowchart LR, GRES discovery to slurmctld to cgroup to binding). Keep; do NOT redraw. It already shows the discovery-isolation-binding path, so no figure repeats that flow. The renumbering figure is a different (job-view) concept.
SVG specs (v6_10.json): h10-task-remap (anchor "### What the job sees"), h10-numa-binding (anchor "## 3. Binding GPUs to tasks and CPUs"), h10-sharing-spectrum (anchor "## 5. Sharing a GPU: MIG, MPS and sharding"). Anchors to be verified unique.
Notes for author: h10-sharing-spectrum orders Whole GPU at the far left as a layout choice; the source says only that whole-GPU is the right default for training. The "Choosing" table already maps needs to mechanisms, so drop the spectrum figure if it reads as a repeat.
Skipped on purpose: request-options table, gres.conf field table, troubleshooting symptom table, Links vector (text), GPU monitoring anomaly thresholds (text and code), isolation check commands (code).
Raster candidates: none.

## ch11 (part-06 11-submitting-and-launching-jobs-sbatch-srun-salloc-arrays-dependencies.md, 661 lines, read in full)
Topic: allocation vs batch step vs job step, the 6-stage life cycle, batch script anatomy, output and export pitfalls, srun and overlap/exact, salloc and interactive steps, job arrays and throttles, 2D grid mapping, dependencies, signals/checkpoint/requeue, squeue/sacct/scancel, linter output, submission patterns, common mistakes, lab, interview angles, 20 checkpoints.
Mermaid: 1 block (L39 flowchart LR, five boxes: submit, job start prolog, batch step, job steps, termination and epilog). Keep; do NOT redraw. Heading says 6-stage life cycle but the mermaid has 5 nodes (the text has 6 stages; the mermaid merges the preemption stage). Flag for author; not redrawn.
Source-consistency flag (author): section 7 prose says the handler "sends USR1 to the training program", but the bash code uses scancel --signal=USR1 --batch-only (targets the batch shell) then kill -TERM on the training PID. The h11-signal-requeue figure follows the code (TERM to training) and labels the USR1 as the batch-shell signal only. Fix the prose or the code before publishing.
SVG specs (v6_11.json): h11-batch-vs-steps (anchor "## 1. Allocations, batch jobs and steps"), h11-array-grid (anchor "### 2D hyperparameter grid search with job arrays (*Distributed AI Systems* Chapter 8)"), h11-dependency-chain (anchor "## 6. Dependencies and pipelines"), h11-signal-requeue (anchor "## 7. Time limits, signals, checkpoints, requeue"). Anchors to be verified unique.
Skipped on purpose: sbatch directive block (code), keys table, env-var table, squeue format table, dependency-type table, linter output (code), submission-pattern table, common-mistakes list, rendezvous code, rank-logging layers (text).
Raster candidates: none.

## ch12 (part-06 12-multi-node-training-on-slurm-pmix-torchrun-nccl-environment-binding-to.md, 464 lines, read in full)
Topic: layers (Slurm, launcher, rendezvous, framework, NCCL, fabric), two launch styles (srun per GPU vs torchrun per node), the dist_env glue and its tested output, rendezvous gotchas, NCCL variable table, binding, framework patterns (DDP, FSDP, DeepSpeed, Megatron), failure triage, diagnose_nccl ladder, lab, interview angles, 20 checkpoints.
Mermaid: 1 block (L39 flowchart TB, Slurm to launcher to rendezvous to framework to NCCL to NVLink and IB). Keep; do NOT redraw. It is the layer stack, and h12-launch-styles and h12-glue-translation show two different things (launch shape and variable mapping), so they do not repeat it.
Source-consistency flag (author): section 3 says "the output looked like this" with a second run start_step=1; the checkpoint answer 2 says PyTorch uses c10d TCP rendezvous, consistent. No conflict found. Section 8.2 item 1 quotes gloo 200 ms vs nccl 4 ms; the 1.75x ring factor is noted in review notes only, so the figures here avoid timing numbers.
SVG specs (v6_12.json): h12-launch-styles (anchor "## 2. Two launch styles"), h12-glue-translation (anchor "## 3. The glue, tested"), h12-master-addr-trap (anchor "## 7. Framework patterns"), h12-diagnose-ladder (anchor "## 8. Failure and diagnosis"). Anchors to be verified unique.
Skipped on purpose: NCCL variable table (table), rendezvous gotcha list (list), binding paragraph (text, covered by ch10 numa figure), framework table (table), failure symptom table (table), pitfalls lists (lists), Megatron checkpoint size math (text and code).
Raster candidates: none.

Anchor check (ch07-12): all 20 anchors match exactly one line in their chapter (python exact-line count).

## ch19 (part-06 19-lustre-architecture-and-operation.md, 625 lines, read in full)
Topic: Lustre roles (MGS, MDS/MDT, OSS/OST, clients, LNet), creating targets with mkfs.lustre, raid0 striping, defaults and lfs setstripe, PFL and DoM, pools, DNE, quotas, migration and OST retirement, failure and recovery, monitoring, AI guidance, lab, checkpoint.
Mermaid: 1 block (L48 flowchart TB, clients to MDS/MDT and OSS/OST with MGS). Keep; do NOT redraw. It is the metadata-versus-data split, and the new figures do not repeat it.
SVG specs (v6_19.json): h19-stripe-roundrobin (anchor "### The raid0 layout"), h19-pfl-bands (anchor "### Progressive File Layouts (PFL) and other layouts"), h19-failover-sequence (anchor "## 5. Failure and recovery model"). Anchors verified with grep -cxF (count 1 each).
Skipped on purpose: mkfs/mount command blocks (code), role table (table), striping defaults table, quota commands, OST retirement list (covered by text and commands), diagnosis ladder (text list), OSS RAM formula block (code), AI guidance table.
Raster candidates: none.

## part-06-hpc-slurm, chapters 13-18 (figure pass, specs in v6_13.json to v6_18.json)

| Chapter file | Topic | Mermaid blocks | Mermaid do-not-redraw | Raster candidates |
|---|---|---|---|---|
| 13-containers-on-slurm-enroot-and-pyxis.md | enroot/pyxis, why not Docker, image caching, pyxis options, hooks | 1 (L40 image path flowchart: registry to sqsh to pyxis to unpack to hooks) | Keep as is. Enroot import/create steps are the same concept, so no enroot command-workflow figure was drawn | None; SVG suffices |
| 14-slurm-operations-prolog-epilog-health-checks-drain-reason-codes-troubl.md | Prolog/epilog, health checks, node lifecycle, unkillable steps, logs, reservations | 1 (L129 node state diagram: IDLE/ALLOCATED/DRAINING/DRAINED/DOWN) | Keep as is. Node-state transitions are not redrawn | None; SVG suffices |
| 15-slurm-high-availability-upgrades-and-scaling.md | Controller HA, backups, upgrade windows and order, scaling, sdiag saturation | 1 (L55 controller HA pair and accounting HA pair) | Keep as is. The upgrade order in the mermaid arrow is the same concept as the upgrade procedure, so no order figure was drawn | None; SVG suffices |
| 16-slurm-on-kubernetes-slinky-and-soperator.md | Slinky vs Soperator architecture, NodeSet scale-in, drain ownership, pod tuning | 1 (L51 Slinky and Soperator architecture flowchart, includes the shared jail) | Keep as is. The shared jail and CRD boxes are already drawn there | None; SVG suffices |
| 17-other-schedulers-pbs-torque-lsf-and-flux.md | PBS select/place, Torque, LSF, Flux subinstances, command map, migration | 1 (L41 shared scheduler architecture: PBS, LSF, Flux) | Keep as is. The top and worker split is already drawn there | None; SVG suffices |
| 18-parallel-storage-concepts-and-the-limits-of-nfs.md | NFS limits, close-to-open consistency, parallel FS striping, I/O patterns, checkpoint arithmetic | 1 (L207 metadata and data server flowchart) | Keep as is. Metadata and data split is already drawn there; the striping and alignment figure is a separate idea | None; SVG suffices |

SVG specs written (anchors verified unique with grep -cxF):
- v6_13.json: h13-herd-pull (### Why caching matters at job start), h13-named-unnamed (## 3. pyxis). Enroot workflow figure dropped as a duplicate of the mermaid import/create concept.
- v6_14.json: h14-prolog-epilog-timeline (## 1. Prolog and epilog), h14-health-check-flow (## 2. Health checks), h14-unkillable-escalation (## 4. Unkillable steps and stuck jobs).
- v6_15.json: h15-upgrade-hops (### A path planner), h15-sdiag-order (### 7.1 Deep dive, sdiag).
- v6_16.json: h16-scale-in-drain (### How the operator talks to Slurm). Drain-ownership rule not drawn, since the mermaid already shows the cordon/drain link.
- v6_17.json: h17-select-place (### Request model: select and place), h17-flux-subinstance (## 4. Flux), h17-migration-steps (## 7. Migration plan (any scheduler to Slurm)).
- v6_18.json: h18-close-to-open (## 2. NFS: what it is and where it ends), h18-stripe-alignment (## 5. I/O patterns and what breaks), h18-bytes-per-param (## 6. Arithmetic you should be able to do).

Notes: chapter 15 and 16 checkpoint sections were skimmed, not read line by line. The lab, exercise and checkpoint sections were skimmed for figure ideas only. Ch16 section 6.2 comparison is a table and was left as a table.

## ch20 (part-06 20-beegfs-gpfs-wekafs-and-vast.md, 430 lines, read in full)
Topic: common frame of eight design questions, BeeGFS services and write path, GPFS shared-disk and tokens, PanFS appliance, WEKA user-space and erasure coding, VAST DASE, six-system comparison table, selection and validation, GPUDirect Storage data path, lab, interview angles, checkpoint.
Mermaid: 1 block (L38 flowchart TB, one box per system's parts: BeeGFS, GPFS, WEKA, VAST). Keep; do NOT redraw. It is the per-system component summary, and the figures show the BeeGFS write flow and the GDS path, not the four-system split.
SVG specs (v6_20.json): h20-beegfs-write-path (anchor "## 2. BeeGFS"), h20-gds-bounce-vs-direct (anchor "### 8.1 The AI data path: GPUDirect Storage (`GDS`) and NVMe staging (Volume 15)"), h20-ec-efficiency-bars (anchor "## 5. WEKA (WekaFS) and other distributed filesystems (*Supercomputers for Linux Sysadmins* Chapter 9)"). Anchors verified with grep -cxF (count 1 each).
Skipped on purpose: design-question table, service table, comparison table (section 7, six columns: table), selection steps (list), benchmark commands (code), GPFS and PanFS prose, lab steps, checkpoint answers.
Raster candidates: none.

## ch25 (part-06 25-remote-access-bastions-open-ondemand-and-user-environments.md, 508 lines, read in full)
Topic: access architecture (bastion, login, DTNs, OOD portal, compute), SSH auth methods and hardening audit, ProxyJump client config, X11 and graphical access, OOD architecture and batch connect, user environment, support and communication, security, lab, checkpoint.
Mermaid: 1 block (L43 flowchart LR, laptop to bastion/portal to login to Slurm to compute, DTN and storage). Keep; do NOT redraw. It is the whole access architecture, and the new figures zoom into one hop each.
SVG specs (v6_25.json): h25-proxyjump-hop (anchor "### Client-side practices (document these for users)"), h25-x11-role-swap (anchor "### X11 and graphical tools (*Supercomputers for Linux Sysadmins* Chapter 18)"), h25-ood-request-chain (anchor "### Architecture (from the OOD documentation)"). Anchors verified with grep -cxF (count 1 each).
Skipped on purpose: auth method table, sshd_audit output (code), ssh config block (code), X server log and xorg paths (text), Xming start command (code), user environment and etiquette lists, support/ticketing text (no visual flow), checkpoint answers (repeat text).
Raster candidates: none.

## ch21 (part-06 21-parallel-i-o-and-checkpoint-patterns.md, 613 lines, read in full)
Topic: MPI-IO and HDF5 stack, collective buffering and hints, alignment rules, checkpoint layouts, tested DCP resharding, async and tiered checkpointing, driver-level cuda-checkpoint and CRIU, crash-safe commit protocol, restart validation, data loading (NVMe tuning, DataLoader, GDS, 3FS, DALI, NeMo Curator), storage sizing, lab, checkpoint.
Mermaid: 1 block (L36 flowchart TB, layered stack: application, HDF5, MPI-IO, file system client). Keep; do NOT redraw. The collective-buffer figure shows the aggregator flow inside the MPI-IO layer, which the stack does not show.
SVG specs (v6_21.json): h21-collective-buffer (anchor "## 1. Parallel I/O in HPC: MPI-IO and HDF5"), h21-dcp-reshard (anchor "### Tested: sharded checkpoint and resharding"), h21-commit-protocol (anchor "## 3. Crash-safe commits (tested)"), h21-loader-overlap (anchor "### Workers, pinned memory, and overlap"). Anchors verified with grep -cxF (count 1 each).
Skipped on purpose: layout comparison table (table), MPI calls and hint lists (text/code), HDF5 call groups (list), alignment rules (list), async-stall arithmetic and Young/Daly formula (formula, covered by text), GDS and 3FS prose, sizing arithmetic, cuda-checkpoint call sequence (list), DataLoader code block.
Raster candidates: none.

## ch26 (part-06 26-cluster-monitoring-and-health-at-scale.md, 607 lines, read in full)
Topic: monitoring tool landscape (SNMP, Ganglia, Nagios, Zabbix, XDMoD, Prometheus/DCGM), SNMP traps, lm_sensors, NUT/apcupsd UPS shutdown order, what to monitor by layer, DCGM fields, Slurm exporter (tested), alert design, health checks and scans, usage analytics, scaling the stack, lab, checkpoint.
Mermaid: 1 block (L43 flowchart LR, collectors to Prometheus/VictoriaMetrics to Grafana/Alertmanager and XDMoD). Keep; do NOT redraw. It is the collector-to-store-to-consumer shape, and the new figures do not repeat it.
SVG specs (v6_26.json): h26-trap-pipeline (anchor "### SNMP, `snmpconf`, and `snmptrapd` handlers"), h26-ups-shutdown-order (anchor "### UPS monitoring with Network UPS Tools (`NUT`) and `apcupsd`"), h26-alert-decision (anchor "## 5. Alerting"), h26-util-vs-tensor (anchor "## 3. GPU metrics with DCGM"). Anchors verified with grep -cxF (count 1 each).
Skipped on purpose: tool landscape table, SNMP command blocks (code), snmpd/trap config (code), Ganglia and Zabbix bullets (text), sensors and apcaccess output (code), NUT config files (code), layer table (table), DCGM field table (table), exporter sample output (code), scaling and security lists (text), checkpoint answers.
Flag for author: section 5 "Golden Rule" text and the exercise-13 numbers are the source of the alert and util examples; the spec uses those numbers only. No source conflict found.
Raster candidates: none.

## ch22 (part-06 22-provisioning-with-pxe-ipxe-dhcp-tftp-and-image-management.md, 540 lines, read in full)
Topic: boot chain, DHCP options 60/67/93, PXE and TFTP limits, iPXE chain-loading and option 175, UEFI HTTP Boot and Kea client classes, tested dnsmasq/iPXE generator and inventory validation, stateless/stateful/hybrid designs, image management habits, node identity lifecycle, cluster managers (ROCKS, PelicanHPC, xCAT, Warewulf, MAAS, Foreman, BCM), D-T-B-I boot triage, lab, checkpoint.
Mermaid: 1 block (L36 flowchart LR, five boot stages: firmware, DHCP+TFTP, iPXE, HTTP image fetch, rootfs and init). Keep; do NOT redraw. It shows stage order only. The h22-ipxe-handshake figure shows the message exchange and loop prevention, which the mermaid does not show.
SVG specs (v6_22.json): h22-ipxe-handshake (anchor "### iPXE"), h22-stateless-layers (anchor "## 4. Stateless, stateful and hybrid nodes"), h22-dtb-triage (anchor "## 8. Boot triage"). Anchors verified with grep -cxF (count 1 each).
Skipped on purpose: option 93 table (table), TFTP and PXE prose, Kea JSON and dnsmasq config blocks (code), generator error block (code output), image habits list (list), identity lifecycle states (text), cluster manager walkthrough steps (lists), D-T-B-I check table (table, its checks are condensed into the triage figure).
Raster candidates: none.

## ch27 (part-06 27-backup-and-data-protection.md, 661 lines, read in full)
Topic: what to protect by class, RPO/RTO, 3-2-1-1-0, snapshots vs replication vs backup, tar, rsync and --link-dest, Bacula, restic/borg/kopia, parallel FS and object stores, control-plane backup table, ransomware and restore order, restore testing tiers, lab, checkpoint.
Mermaid: 1 block (L61 flowchart LR, primary data to on-site dedup to offsite WORM to quarterly DR drill). Keep; do NOT redraw. It is the 3-2-1-1-0 copy chain, and h27-snapshot-vs-backup covers a different point (failure domain), not the copy chain.
SVG specs (v6_27.json): h27-snapshot-vs-backup (anchor "## 2. Principles"), h27-link-dest-snapshots (anchor "### rsync, batch updates, and hard-link snapshots"), h27-dr-restore-order (anchor "## 7. Ransomware and insider risk"), h27-restore-test-tiers (anchor "## 8. Restore testing and metrics"). Anchors verified with grep -cxF (count 1 each).
Skipped on purpose: class table (table), tar operation-mode table, rsync flag table, tar and restic command blocks (code), Bacula config blocks (code), bconsole table (table), control-plane table (table), RPO/RTO prose (text). Bacula ports and daemon layout were considered for a figure but dropped: the source gives roles and ports but few explicit connections, so a figure would be mostly a labelled list with no arrows.
Flag for author: section 7 gives the restore order as identity, DNS, provisioning, storage, scheduler, users. The checkpoint 17 answer lists more detail (network, secrets/PKI, Slurm DB before slurmctld). Spec uses the body list only. No conflict.
Raster candidates: none.

## ch23 (part-06 23-xcat-warewulf-and-cluster-managers-compared-with-bcm.md, 583 lines, read in full)
Topic: common model across managers, xCAT architecture and object model, xCAT tables and statelite recipe, xCAT status (Confluent successor), Warewulf 4 architecture and overlays, Confluent/MAAS/Foreman, BCM architecture and trade-offs, selection matrix, operating practices, lab, interview angles, checkpoint.
Mermaid: 1 block (L40 flowchart TB, one box per manager: xCAT, Warewulf 4, BCM). Keep; do NOT redraw. It is the one-line architecture summary per tool, and the three figures show the statelite workflow, the BCM image path and the Warewulf overlay rendering in more depth.
SVG specs (v6_23.json): h23-statelite-flow (anchor "#### Loading and Controlling: Step-by-step `statelite` provisioning workflow (Chapters 26 and 28)"), h23-bcm-image-flow (anchor "## 5. NVIDIA Base Command Manager (BCM)"), h23-warewulf-overlays (anchor "### Architecture"). Anchors verified with grep -cxF (count 1 each).
Skipped on purpose: abstraction table and selection matrix (tables), xCAT object and table lists (lists), policy CSV and regex code blocks (code), rpower and psh command list (text), MAAS lifecycle (short list, covered in text), operating-practice bullets, lab table, checkpoint answers (node replacement steps appear only in checkpoint, so no figure for them here).
Raster candidates: none.

## ch28 (part-06 28-hpc-benchmarking-hpl-hpcg-ior-osu-and-nccl-tests.md, 530 lines, read in full)
Topic: benchmarking methodology (active benchmarking, 16 failure modes, four benchmark types), statistics harness with thread-count surprise, STREAM/HPL/HPCG/IOR/mdtest/gdsio/OSU/NCCL tests, busbw formulas, acceptance and burn-in, reporting, lab, interview angles.
Mermaid: 1 block (L37 flowchart LR, five methodology steps: characterize, execute, active benchmarking, sanity check and stats, acceptance and regression). Keep; do NOT redraw. It is the five-step method, and h28-acceptance-order is the eight-stage cluster plan, a different sequence.
SVG specs (v6_28.json): h28-bonnie-layers (anchor "## 1. Methodology (Systems Performance, chapter 12)"), h28-acceptance-order (anchor "## 4. Acceptance testing and burn-in"), h28-batch-halving (anchor "### NCCL tests"). Anchors verified with grep -cxF (count 1 each).
Considered and dropped: busbw worked example (14.3 to 28.2 GB/s vs 50 GB/s NIC). It is a calculation, which the text already shows step by step, and it would need a second figure under the same "### NCCL tests" heading. Also dropped: the 3.2 Gbps sanity-check bar (calculation only).
Skipped on purpose: thread-count table (table), statistics output, benchmark-type list, HPL.dat settings (text), gdsio command blocks (code), nccl-tests command and flag lists, busbw factor table (table), checklist lists (lists), lab and interview lists.
Raster candidates: none.

## ch24 (part-06 24-users-ldap-sssd-quotas-and-accounting-at-scale.md, 571 lines, read in full)
Topic: account sync options (static pull with timeout wrapper, NIS, LDAP, FreeIPA, AD), UID/GID ranges, LDAP layout and generator outputs, standing up a directory, SSSD and nsswitch/PAM, compute-node lookups and enable_nss_slurm, blocking users, homes and quotas, Slurm accounting alignment, onboarding and offboarding, scale and security, containers note, lab, checkpoint.
Mermaid: 1 block (L40 flowchart LR, validated CSV feeding LDAP, SlurmDBD and shared storage, then nodes). Keep; do NOT redraw. It shows the one-source fan-out, which the figures do not repeat. The generator's validation and the three outputs are not drawn again.
SVG specs (v6_24.json): h24-lookup-path (anchor "## 4. SSSD, nsswitch and PAM on the nodes"), h24-launch-lookups (anchor "### Compute nodes"), h24-offboard-order (anchor "## 6. Slurm accounting alignment"). Anchors verified with grep -cxF (count 1 each).
Skipped on purpose: sync script and wrapper (code), NIS paragraph (text), method table (table), LDIF and sacctmgr excerpts (code), sssd.conf and nsswitch blocks (code), blocking methods (list), quota and limits prose, onboarding and offboarding table (table), symptom table (table), checkpoint answers.
Raster candidates: none.

## Summary across ch19-24
Figures planned: 3 per chapter (18 total) in v6_19.json to v6_24.json. Each spec uses an anchor that appears exactly once. Mermaid blocks in all six chapters (one each) are kept.

## ch29 (part-06 29-containers-and-reproducibility-in-hpc-apptainer-and-enroot.md, 481 lines, read in full)
Topic: what a container is (cgroups, namespaces, chroot), HPC vs Docker model, Apptainer (SIF, def files, cache, --nv, MPI hybrid/bind models, security), runtime comparison table, reproducibility discipline (12 practices, linter), distribution at scale, lab, troubleshooting (glibc, CUDA compat, HOME leak, fabric providers).
Mermaid: 1 block (L41 flowchart LR, recipe to CI build and sign to shared store to Slurm launch). Keep; do NOT redraw. It is the lifecycle pipeline, and the new figures cover MPI models, the glibc failure and the reproducibility levels.
SVG specs (v6_29.json): h29-mpi-models (anchor "### MPI"), h29-glibc-mismatch (anchor "### GPUs"), h29-repro-levels (anchor "## 4. Reproducibility discipline"). Anchors verified with grep -cxF (count 1 each).
Source issues flagged for author:
- The "## Exercises" heading appears TWICE (around L327 and L338), with identical text. One copy should be removed. Not a figure issue; do not anchor on it.
- The troubleshooting section (6.1, "### 6.1 Troubleshooting guide...") says "Work through these five checks", but only four are described (glibc, CUDA forward compatibility, HOME leakage, fabric providers). No figure drawn for it, to avoid a five-step figure with a missing step.
Considered and dropped: 12-practice list (list), HPC-vs-Docker table and runtime comparison table (tables), container-start staging at scale (text, no numbers), security-model text, linter output (code).
Raster candidates: none.

## ch30 (part-06 30-facility-basics-power-cooling-racks-and-liquid-cooling.md, 481 lines, read in full)
Topic: units (W, kW, MW, kWh), equipment power, three-phase circuit capacity and stranded power, PSU redundancy designs, rack PDUs, UPS and staged haltall shutdown, air cooling (CFM, room conditions, airflow direction), liquid cooling types, PUE and energy cost, racks and cabling, ownership, physical monitoring, lab, checkpoint.
Mermaid: 1 block (L41 flowchart LR, utility/UPS to PDU to GPU server to heat rejection). Keep; do NOT redraw. It is the one-path power and heat chain, and the new figures cover shutdown order, PSU wiring and the liquid loop.
SVG specs (v6_30.json): h30-staged-shutdown (anchor "### 3.4 UPS and staged shutdown"), h30-psu-feed-designs (anchor "### 3.2 Redundancy: why servers with internal power supplies need care"), h30-cold-plate-loop (anchor "## 5. Liquid cooling"). Anchors verified with grep -cxF (count 1 each).
Considered and dropped: airflow direction (text with a rule, low value over the existing table), power unit table (table), circuit table (table), redundancy design table (table, the psu figure covers two of its rows), PUE worked example (arithmetic in text), cabling rules (text), ownership list (list).
Source notes flagged for author:
- Section 3.4 says the staged script "haltall" and the sim output show 40 idle nodes and "75 min left" at 30 minutes. The figure uses only the stage order and the 30-minute and 5-minute thresholds from the text, not the sim numbers.
- Section 3.2 table says the 6-to-make-5 design is "usually limited to 2 servers per rack". Not drawn (the PSU figure covers two designs only).
- Checkpoint 13 says fans cool DIMMs and NICs (cold-plate chapter detail), which section 5 does not state. The cold-plate figure uses that label because it is in the same chapter.
Raster candidates: none.

## part-07-redfish-bmc (Vol 7)

| 01-bmcs-ipmi-and-out-of-band-management.md | BMC role, in-band vs OOB doors, failure table, dual-tray DGX/HGX anatomy, OOB network design, ipmitool groups and power ops, SOL/conman/powerman/iKVM, credential audit, IPMI vs Redfish | 3 (L55 two-doors flow, L127 dual-tray map, L179 rack OOB network). All three keep; none flagged for redraw. | Do NOT redraw the three mermaid blocks. The failure table (1.1) and power table (4.2) are tables and skipped. | None |
SVG specs (v7_01.json): r01-bmc-recovery (anchor "### 1.1 Modeling failure boundaries (`code/part07/oob_sim.py`)", KCS reset, PDU drain, smart hands), r01-power-cycle (anchor "### 4.2 Core `ipmitool` command groups and power operations", off/poll/wait/on). Anchors verified with grep -cxF (1 each).
Skipped on purpose: ipmitool -I lan vs lanplus (two bullets), SOL ~. escape trap (text), credential fingerprint flow (code output), IPMI vs Redfish comparison (table).

| 02-redfish-concepts-service-root-resources-collections-odata.md | Service Root and graph, collection tables, resource anatomy, annotations, active vs Settings, OEM, pagination loop, crawler code, SSDP, BCM redfish commands | 1 (L56 Service Root tree with containment and Links cross-links). Keep; do NOT redraw. | Do NOT redraw the L56 tree. Tables, annotation table, and the resource JSON are skipped. | None |
SVG specs (v7_02.json): r02-collection-paging (anchor "## 5. Resource collections and pagination"), r02-settings-stage (anchor "### 4.1 Active resources vs `/Settings` resources (DSP0266 §9.10)"), r02-crawl-loop (anchor "### 6.1 How the hypermedia crawler works (`code/part07/redfish_crawl.py`)"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: well-known URI table, ServiceRoot ProtocolFeaturesSupported list, value rules (empty vs null), SSDP and cmsh tables (text/tables).

## ch31 (part-06 31-capstone-build-and-operate-a-small-slurm-gpu-cluster.md, 564 lines, read in full)
Topic: whole-cluster bottom-up build (plan, build, prove, run), eight-layer build order, single-source-of-truth pipeline (inputs, ten stages, RealMemory 97% rule), ten-gate acceptance protocol, Day-2 drills, three whiteboard scenarios (128-node design, 64-node hang triage, Slurm vs Kubernetes), interview myths, exercises, checkpoint.
Mermaid: 3 blocks. Keep ALL THREE; do NOT redraw.
- L44 flowchart TB, four-phase Plan/Build/Prove/Run loop with RMA feedback. Keep.
- L78 flowchart TD, six runtime planes (physical, provisioning, OS, fabrics and storage, orchestration, collectives). Keep. The build-order figure is a numbered sequence of eight layers, not the plane stack.
- L325 flowchart TD, 64-node frozen-job triage decision tree (Scenario B). Keep. It is a decision tree; the drill figure is a recovery path for a single fault, not a triage tree.
SVG specs (v6_31.json): h31-build-order (anchor "## 2. Build order and dependency chains"), h31-single-source-pipeline (anchor "## 3. Single-source-of-truth pipeline lab"), h31-acceptance-gates (anchor "## 4. Ten-gate acceptance testing and burn-in protocol"), h31-drill-recovery-loop (anchor "## 5. Day-2 operations drills: practicing the bad day"). Anchors verified with grep -cxF (count 1 each).
Skipped on purpose: Scenario A, B, C tables and lists (text and table), Drill table (table, the drill-1 figure covers one row), stage table (table), inventory schemas (table), generated slurm.conf and PASS output (code), RealMemory and DefMemPerGPU details (text), Slurm vs K8s table (table), interview myths list, checkpoint answers.
Source notes flagged for author:
- Exercise 9 asks how many DGX nodes fit a 25 kW rack; the chapter's worked answers use a 30 kW cap. The 25 kW case has no in-chapter answer key.
- Checkpoint 4 gives the RealMemory reserve as about 2 to 3 percent of RAM, while section 3.3 uses a 0.97 multiplier (3 percent). Consistent in intent, not a conflict to fix in figures.
Raster candidates: none. The gates and build order fit SVG.

| 03-the-redfish-protocol-http-methods-headers-status-codes-query-parameter.md | HTTP methods table, PATCH vs POST, array PATCH and OperationApplyTime, headers tables, ETag and If-Match, 50+ status code table, @Message.ExtendedInfo, PATCH partial success, query parameter order and reference, 36-check lab | 2 (L143 ETag collision sequenceDiagram with 4 playbook messages; L260 seven-step query-order flowchart LR). Both keep; do NOT redraw. | Do NOT redraw the L143 sequence or the L260 query-order chain. The status code table is a table. | None |
SVG specs (v7_03.json): r03-patch-outcomes (anchor "### 4.2 The `PATCH` partial-success rule (DSP0266 §7.6)"), r03-patch-vs-post (anchor "### 1.1 `PATCH` (properties) versus `POST` (actions and creation)"), r03-array-patch (anchor "### 1.2 `PATCH` on array properties and `@Redfish.OperationApplyTime` (DSP0266 §7.7 & §7.12)"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: method table, header tables, status code table (tables); the $expand specifier list (text); the 36-check lab output.

## ch09 (part-07 09-storage-network-adapters-and-pcie-devices.md, 440 lines, read in full)
Topic: where drives, volumes, NICs, ports and PCIe devices live in the Redfish tree; Drive/Volume/Port fields; PCIe Gen and width arithmetic; rf_hardware.py rules table; lab output; Day-0/Day-2 gates; Redfish blind spots; checkpoint questions.
Mermaid: 1 block (L54 flowchart LR, Storage to StorageController, Drive, Volume). Keep; do NOT redraw (it is the storage map and the chapter's only mermaid).
SVG specs (v7_09.json): r09-pcie-link (anchor "## 4. PCIe: the hidden speed limit"), r09-port-triage (anchor "### 6.2 Diagnosing optical and copper `Port` speed mismatches"), r09-gates (anchor "### 6.4 Integrating `rf_hardware.py` into Day-0 and Day-2 automation"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: where-hardware-lives table, Drive and Port property tables, NIC building analogy (text), rf_hardware rules table, lab PASS list and tool output (code and tables), 6.1 degraded-link narrative (text; r09-pcie-link covers its arithmetic), 6.3 drive signals (bullets), 6.5 lspci mapping table, 6.6 OEM quirks (text), exercises and checkpoints.
Raster candidates: none.

| 04-redfish-authentication-sessions-and-security.md | TLS and certificates, Basic vs session, session lifecycle, roles and Privilege Registry, mTLS and OAuth, lockout and password rules, lab, safe script habits, session exhaustion, Day 0 rotation, directory integration | 1 (L75 session steps sequenceDiagram: POST Sessions, token, Location, DELETE). Keep; do NOT redraw. | Do NOT redraw the L75 session sequence. The role and lockout tables are tables. | None |
SVG specs (v7_04.json): r04-day0-rotation (anchor "### 6.3 Designing zero-touch factory password rotation on Day 0"), r04-override-precedence (anchor "### 3.1 Privilege Registry overrides, logical AND/OR, and Restricted Roles (DSP0266 §13.4.2–13.4.3)"), r04-session-leak (anchor "### 6.1 Anatomy of a session-table exhaustion outage"). Anchors verified with grep -cxF (1 each).
CONTENT FLAG (r04-day0-rotation): chapter 6.3 step 3 says both NewPassword and SessionAccountPassword are the factory password. That looks wrong (step 5 says the bootstrap account then moves to the vault secret). The spec draws NewPassword as the vault-managed secret and SessionAccountPassword as the factory password. Fix the chapter text or confirm before the figure ships.
Skipped on purpose: role and privilege tables, lockout settings table, Basic vs session table, OAuth/mTLS prose, checkpoint answers.

## ch10 (part-07 10-firmware-inventory-and-the-updateservice.md, 486 lines, read in full)
Topic: firmware groups and the 30-component GPU tray, UpdateService and FirmwareInventory fields, drift against a baseline, SimpleUpdate pull vs multipart push, Targets and OperationApplyTime, task messages, activation by reset type, BCM firmware commands, nvfwupd, safe fleet procedure, lab.
Mermaid: 1 block (L82 flowchart TD, admin to UpdateService inventory, pull and push, task stages, activation resets, back to inventory). Keep; do NOT redraw (it is the whole update flow, and the stage and activation figures below are not repeated from it as flow; r10-staged-active is a flash-slot mechanism, r10-waves is a rollout order).
SVG specs (v7_10.json): r10-staged-active (anchor "## 5. Staged is not active: activation"), r10-waves (anchor "## 8. A safe fleet procedure"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: pull vs push table (table; mermaid already shows both paths), stage message and failure message tables (tables), drift result list (text), HTTP 202/413/411 notes (text), BCM 5-step list (text), nvfwupd commands (code), lab PASS list and plan output (code/tables), 11-step procedure (list; r10-waves covers its wave order only), exercises, checkpoints.
Source note: the 11-step list in section 8 says "11-step" in exercise 5, and the wave sizes (1 node, rack of 8, SU of 32) come from exercise 5, used in r10-waves.
Raster candidates: none.

| 05-redfish-actions-tasks-events-and-subscriptions.md | Actions and POST target, ResetType meanings, 202 and task monitor, push subscriptions and event body, SSE, BCM commands, actions lab, power-control workflow, async poller, event scaling | 1 (L114 task-monitor sequenceDiagram: POST, 202, loop of GET monitor, final 200, Task Completed). Keep; do NOT redraw. | Do NOT redraw the L114 sequence; the 202 polling loop is pseudo-code, already covered. Subscription property table and push/SSE/polling comparison table are tables. | None |
SVG specs (v7_05.json): r05-reset-ladder (anchor "### What each `ResetType` means"), r05-power-escalation (anchor "### 5.1 Designing idempotent node power-control workflows"), r05-event-sweep (anchor "### 5.3 Scaling event-driven monitoring across a thousand BMCs"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: 202 pseudo-code loop (code block), subscription property table, push vs SSE vs polling table, TaskState list, action status code list.

| 06-the-redfish-schema-reading-csdl-json-schema-and-the-resource-guide.md | Three schema formats, @odata.type to file names, versioning rules, Resource Guide columns, annotations, message registries, OEM, schema_lab validation, $ref and allOf, CI contract test | 1 (L49 flowchart TD: payload to unversioned/versioned schema, version chain, Message/Attribute/Privilege registries). Keep; do NOT redraw; it is the registry map. | Do NOT redraw the L49 map. The version-chain arrow inside it is already there, so the step-back figure below covers the procedure, not the map. Property table and annotation table are tables. | None |
SVG specs (v7_06.json): r06-type-to-schema (anchor "## 2. From `@odata.type` to the schema file"), r06-step-back (anchor "## 3. Versioning: what a client must do"), r06-message-decision (anchor "## 6. Message registries: how errors and events get their text"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: CSDL/JSON Schema/OpenAPI format table, Resource Guide column table, annotation table, schema_lab check list, mockup crawl table, 8.2 $ref prose (prose only).
Source note (not for figure): section 7 says the NVIDIA OEM claim is from user notes and unchecked; figure avoids it.

## ch11 (part-07 11-log-services-event-logs-and-diagnostics.md, 522 lines, read in full)
Topic: where LogServices live, Event vs SEL entries and fields, rf_logs.py show/filter, overwrite policy and capacity warnings, BMC clock skew, ClearLog with ETag guard, CollectDiagnosticData three-step bundle, cross-layer crash timeline, RMA evidence order, IPMI SEL to Redfish mapping table, lab, checkpoints.
Mermaid: 1 block (L78 flowchart LR, owners to LogService policy, entries, actions). Keep; do NOT redraw. Its ACT node already draws the CollectDiagnosticData 202 to LogEntry to AdditionalDataURI chain, so a separate bundle-steps figure was deliberately NOT made (duplicate concept).
SVG specs (v7_11.json): r11-overwrite-policy (anchor "## 4. What the log tells you about itself"), r11-crash-timeline (anchor "### 8.1 Reconstructing a cross-layer hardware crash timeline"), r11-rma-order (anchor "### 8.4 End-to-end RMA evidence collection workflow (`CollectDiagnosticData` + `nvsm`)"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: LogService property and LogEntry field tables, services output and show output (code), DMTF example output, investigation method list (text), 8.2 NTP clock drift (text, procedural), 8.3 capacity hazards (covered by r11-overwrite-policy), 8.5 legacy SEL to Event mapping (table), lab PASS list, exercises, checkpoints.
Raster candidates: none.

## ch12 (part-07 12-automating-redfish-with-python-ansible-and-go.md, 484 lines, read in full)
Topic: TLS and certificate trust (no -k), Python client and session rules, DMTF redfish library, Ansible uri block/always and community.general modules, serial/forks scale, Go gofish, fleet runner rules and lab, tool choice table, retry engine, chaos tests, secret management, exercises, checkpoints.
Mermaid: 1 block (L209 flowchart LR, fleet runner: CSV to bounded pool to login to task or no-retry or retry to logout to summary). Keep; do NOT redraw. Its retry and no-retry branches are the same concept as the fleet rules table, so no retry-policy figure was made.
SVG specs (v7_12.json): r12-tls-trust (anchor "## 1. First, TLS: stop using `-k`"), r12-session-lifecycle (anchor "### 2.1 The client I used in all labs"), r12-serial-batches (anchor "### 3.3 Scale in Ansible"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: rules list 2.3 (list), Ansible uri block/always YAML (code; r12-session-lifecycle covers the Python equivalent, so no duplicate session figure), community.general module table (table), fleet lab results table (table; mermaid covers the flow), tool choice table (table), chaos and secrets sections (text), Go snippet (code), exercises, checkpoints.
Raster candidates: none.

| 07-systems-chassis-and-managers-the-core-resource-model.md | System, Chassis and Manager families, property tables, DPU and blade cases, rf_model link check, inventory tool, absent and standby states, find-a-GPU steps, DGX names, checkpoint questions | 2 (L47 flowchart LR: System/Chassis/Manager with Links pairs; L158 flowchart TB: blade enclosure example graph with 5 managers and 4 systems). Both keep; do NOT redraw. | Do NOT redraw L47 (it is the core relationship map, and r07-link-states covers the consistency rule without repeating it) or L158 (a specific DMTF example graph). The property tables and manager type table are tables. The 9.1 topology list is text. | None |
SVG specs (v7_07.json): r07-find-gpu (anchor "## 8. Steps for finding a value"), r07-absent-states (anchor "## 7. Present, absent and temporarily unavailable"), r07-link-states (anchor "### 9.4 Auditing graph integrity across vendors with `rf_model.py`"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: ChassisType and ManagerType lists (text), DGX name bullets (text), 9.2 BootProgress and watchdog prose, rf_inventory output (code).

| 08-power-thermal-sensors-and-environment.md | Modern vs legacy telemetry designs, Sensor properties, thresholds, Status vs Reading, fans and redundancy, PSUs and power caps, rf_sensors tool, Prometheus export, TelemetryService, DCGM vs BMC, unknown-machine lookup, liquid cooling, cap controller, cardinality | 1 (L46 flowchart TD: modern Sensors/Subsystem/EnvironmentMetrics vs legacy Thermal/Power). Keep; do NOT redraw. | Do NOT redraw L46; it is the design comparison and the chapter's core map. The sensor property table, Status/Health table, and checkpoint answers are tables or text. Section 8.3 and 8.4 are prose lists. | None |
SVG specs (v7_08.json): r08-threshold-steps (anchor "### Thresholds"), r08-fan-redundancy (anchor "## 3. Thermal: fans, heat and cooling"), r08-straggler-triage (anchor "### 8.1 Correlating out-of-band BMC sensors with in-band DCGM throttling"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: Sensor property table, Status vs Reading table, power-cap JSON (code), tool output blocks (code), Prometheus output (code), 8.2 liquid-cooling and 8.3 guardrails (prose lists), 8.4 cardinality (prose).
Note: the section 4 power cap is illustrated only as JSON, so no figure. Chapter 8 section 8.3 guardrail list would make a fine figure later if asked.

## ch13 (part-07 13-redfish-on-nvidia-dgx-and-hgx-bmc-gpu-baseboard-and-management.md, 396 lines, read in full)
Topic: DGX vs OEM HGX vs rack-scale ownership table, HGX baseboard FRU and RMA boundaries, GPU tray controllers (HMC, ERoT, FPGA/CPLD, retimers), GB300 NVL72 rack contents and OOB network, NVSM vs Redfish, acceptance profiles and DMTF validators, rec/replay with rf_record.py, 8-step bring-up checklist, architecture comparison, exercises, checkpoints.
Mermaid: 1 block (L70 flowchart TB, host tray with main BMC, GPU tray with HMC/ERoT/NVSwitch/retimers, OOB switch). Keep; do NOT redraw. Its controller layout overlaps the controller table and r13 specs deliberately avoid repeating it.
SVG specs (v7_13.json): r13-nvl72-rack (anchor "## 3. Rack-scale: GB200 and GB300"), r13-two-views (anchor "## 4. NVSM and BCM next to Redfish"), r13-bringup (anchor "## 7. A bring-up checklist for a new GPU server model"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: ownership comparison table (table; a figure would repeat it), HGX FRU vs soldered NVSwitch and power-delivery arithmetic (text), controller role table (table; the mermaid covers the layout), redfish endpoint table (table), nvsm command table (table), acceptance profile details and validator run output (text and code), rf_record round trip (text), exercises, checkpoints, 7.1 architecture comparison (text, long).
Raster candidates: none.
- v7 ch04 line 253: chapter text says NewPassword AND SessionAccountPassword both = factory password (likely wrong; NewPassword should be the new secret). Fix chapter text.

## ch14 (part-07 14-fleet-scale-hardware-management-and-node-lifecycle-automation.md, 444 lines, read in full)
Topic: fleet mindset, BIOS Settings pattern (live vs pending), attribute registry validation, BIOS matrix cautions, rf_bios plan/apply, one-time vs continuous boot override, node_lifecycle six-gate state machine with dry-run and resume, keeping a fleet in line (waves, exceptions, RMA re-baselining), five NVIDIA-notes scenarios, BIOS deep dive, idempotent state machine, exercises, checkpoints.
Mermaid: 1 block (L145 flowchart LR, six-gate node lifecycle with STOP branches). Keep; do NOT redraw. Its gates are the chapter's core state machine.
SVG specs (v7_14.json): r14-settings-staging (anchor "### 2.1 The Settings resource pattern"), r14-boot-override (anchor "## 3. Boot override: one time or forever"), r14-bmc-escalation (anchor "### Scenario 3: A \"bricked\" BMC after a bad firmware push"). Anchors verified with grep -cxF (1 each). The heading contains straight double quotes, copied exactly.
Overlap note: r14-settings-staging is the same staged-vs-active idea as r10-staged-active (ch10), but for BIOS Settings objects rather than firmware flash slots. Both are kept because they are different resources and different chapters.
Skipped on purpose: BIOS matrix table (table, and its cautions are text), registry error table (table), BCM biossettings description (text), plan/apply command output (code), node_lifecycle lab PASS list (code), the six-gate table (table; mermaid covers it), Scenarios 1, 2, 4 and 5 (text and tool pointers), BIOS deep dive section 6.1 (long text, mechanism per row, no single clean drawing), exercises, checkpoints.
Source note: the Scenario 3 sub-line gives the notes' "ipmitool bmc reset cold" form. Chapter 7.1 and 7.10 use "ipmitool mc reset cold"; the chapter itself says it did not verify that these are aliases. The figure keeps the notes' form and does not claim equivalence.
Raster candidates: none.

## ch15 (part-07 15-bmc-security-hardening-and-attestation.md, 444 lines, read in full)
Topic: threat model, seven defence layers, protocol and account hardening, certificate replacement through GenerateCSR/ReplaceCertificate, rf_harden audit and apply, firmware trust, UEFI Secure Boot through Redfish, attestation (SPDM, TPM, nonce, RIM), BMC checklist, incident response, exercises, checkpoints.
Mermaid: 2 blocks. L56 flowchart TB, seven defence layers (keep, do NOT redraw; it is the chapter's layer map and the Secure Boot and attestation figures below are the mechanisms it only names). L102 sequenceDiagram, GenerateCSR and ReplaceCertificate exchange (keep, do NOT redraw; it is the certificate workflow, so no certificate figure was made).
SVG specs (v7_15.json): r15-trust-chain (anchor "## 5. Firmware trust"), r15-secureboot-steps (anchor "## 6. UEFI Secure Boot through Redfish"), r15-attest-steps (anchor "## 7. Attestation: what it is, and what I did not do"). Anchors verified with grep -cxF (1 each).
Skipped on purpose: threat table (table), rf_harden FIX/MANUAL output (code), protocol JSON snippet (code), certificate verification table (table), firmware trust point 2 and 3 details (text), database PK/KEK/db/dbx list (text and checkpoint), section 8.1 SPDM/TPM 4-step deep dive (long text; r15-attest-steps covers the four steps at beginner level), section 8.2 incident-response order (text), checklist (list), exercises, checkpoints.
Source notes: the chapter flags one correction (notes say Secure Boot db is on the BMC; chapter says the databases belong to the host UEFI). r15-secureboot-steps does not depend on that point.
Raster candidates: none.
