---
id: "c05-10"
title: "5.10 Services, endpoints and kube-proxy: the life of a Service"
sidebar_label: "5.10 Services, endpoints and kube-proxy: the life of a Service"
sidebar_position: 10
description: "Kubernetes Services in depth: ClusterIP, NodePort, LoadBalancer, headless and ExternalName; EndpointSlices; kube-proxy modes (iptables, IPVS, nftables) and eBPF replacements; packet path, conntrack and NAT; session affinity, traffic policies, topology-aware routing, dual-stack; debugging and scale limits"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 5.10 Services, endpoints and kube-proxy: the life of a Service

| | |
|---|---|
| Level | Advanced |
| Priority tier | 0 |
| Lab venue | Multi-node cluster; root on a node; `iptables-save`, `nft`, `ipvsadm`, `conntrack`, `tcpdump`, `curl`, `kubectl` |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Pods are ephemeral and their IPs change, so everything that talks to inference servers, vector databases, parameter servers, feature stores, metrics endpoints or the control plane does so through Services. At scale Services stop being "just load balancing": with thousands of Services and tens of thousands of endpoints, iptables rule updates take seconds and CPU, conntrack tables fill during burst traffic from training clients or inference gateways, long-lived gRPC/HTTP2 streams pin to a single backend, and `externalTrafficPolicy` decides whether your LLM gateway sees client IPs and balances evenly. Understanding exactly how a ClusterIP becomes a pod IP in the kernel is essential for debugging latency spikes, connection resets, uneven load and "Service works from some nodes but not others".

## Prerequisites and outcomes

Needs 5.3, 5.8; networking (Part 2: NAT, conntrack, iptables/nftables 2.23). After this chapter you can:

- Define Service types and fields (selectors, ports, targetPort, sessionAffinity, externalTrafficPolicy, internalTrafficPolicy, loadBalancerClass, IP families) and EndpointSlices; explain readiness gating and terminating endpoints.
- Trace a packet from a pod to a ClusterIP to a backend pod (DNAT, conntrack, reverse NAT) in iptables, IPVS and nftables modes, and in eBPF replacements (Cilium).
- Explain NodePort and LoadBalancer paths, source IP preservation, health checks, hairpin traffic, and Services without selectors.
- Diagnose Service failures with `kubectl`, `iptables-save`, `ipvsadm`, `conntrack`, `tcpdump`, and kube-proxy logs/metrics.
- Choose kube-proxy mode, tune conntrack, handle scale (large Service counts), and use topology-aware routing.

## 1. Service objects

A **Service** is a stable virtual IP (ClusterIP) and DNS name that load-balances to a set of pods selected by labels. It is purely a *control-plane and kernel* construct: there is no process listening on the ClusterIP; the packet rewrite happens in each node's kernel (or in the CNI datapath).

```yaml
apiVersion: v1
kind: Service
metadata:
  name: vllm
  namespace: serving
spec:
  type: ClusterIP                  # ClusterIP | NodePort | LoadBalancer | ExternalName | (headless: clusterIP: None)
  selector: { app: vllm }
  ports:
    - name: http
      port: 80                     # service port (what clients use)
      targetPort: http             # container port number or named port
      protocol: TCP
      appProtocol: http            # hints for L7 proxies/meshes
  sessionAffinity: None            # or ClientIP (+ sessionAffinityConfig.clientIP.timeoutSeconds)
  internalTrafficPolicy: Cluster   # or Local (only node-local endpoints)
  ipFamilyPolicy: SingleStack      # SingleStack | PreferDualStack | RequireDualStack
  trafficDistribution: PreferClose # topology-aware preference (newer releases)
```

### Types

| Type | What it creates | Notes |
|---|---|---|
| **ClusterIP** | Virtual IP from the service CIDR (configured on `kube-apiserver` via `--service-cluster-ip-range`, e.g., `10.96.0.0/12`, which must not overlap with Pod or node subnets), reachable inside the cluster | Default |
| **NodePort** | ClusterIP + a port (30000-32767) opened on every node forwarding to the Service | Basis for external LBs; `externalTrafficPolicy` matters |
| **LoadBalancer** | NodePort + external load balancer (cloud controller or MetalLB/kube-vip) with an external IP/hostname | `loadBalancerClass` selects implementation; `allocateLoadBalancerNodePorts: false` for LBs that route directly to pods |
| **ExternalName** | DNS CNAME to an external name; no proxying | No ports/selectors; avoid for TLS/host-header surprises |
| **Headless** (`clusterIP: None`) | No VIP; DNS returns pod IPs (A/AAAA per ready endpoint) | StatefulSets, client-side balancing, direct pod addressing, gRPC clients |
| **Services without selectors** | You manage EndpointSlices manually | Map to external databases/IPs or other-cluster pods |

### Ports

`port` is the Service's port; `targetPort` is the pod port (number or the container's named port, which allows changing numbers without touching Services); multiple ports require names; `nodePort` fixed if needed; `protocol` TCP/UDP/SCTP. Named `appProtocol` values (`http`, `h2c`, `grpc`) help gateways and meshes.

### DNS

Services get `my-svc.my-ns.svc.cluster.local` A/AAAA records (ClusterIP), SRV records for named ports, and pods can resolve short names via search domains (5.11). Headless services resolve to endpoint IPs.

## 2. EndpointSlices

Endpoints track the pods behind a Service. The legacy **Endpoints** object (one per Service, a single big list) does not scale (every change rewrites and re-sends the whole list to every node). **EndpointSlice** (default since 1.21) shards endpoints into slices of up to 100 (configurable) with per-endpoint fields:

```yaml
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: vllm-abcde
  labels: { kubernetes.io/service-name: vllm }
addressType: IPv4
ports: [ { name: http, port: 8000, protocol: TCP } ]
endpoints:
  - addresses: ["10.244.3.17"]
    conditions: { ready: true, serving: true, terminating: false }
    nodeName: gpu-node-3
    zone: us-central1-a
    targetRef: { kind: Pod, name: vllm-6d9f-xk2lm, namespace: serving }
    hints: { forZones: [ { name: us-central1-a } ] }
```

The **EndpointSlice controller** (kube-controller-manager) creates/updates slices from Services and Pods: a pod is `ready` only when its Ready condition is true (readiness probe passing, readiness gates satisfied). `serving` and `terminating` fields let proxies keep sending traffic to terminating-but-still-serving pods (graceful drain) when no ready endpoints remain. The **EndpointSliceMirroring controller** mirrors manually created Endpoints to slices. Large Services (5,000+ pods) produce many slices; each pod change updates one slice (small update), unlike legacy Endpoints. Observe: `kubectl get endpointslices -l kubernetes.io/service-name=vllm -o wide`.

Consequences:

- **Readiness controls traffic**: unready pods are removed from endpoints; a pod stuck NotReady gets no traffic. Slow readiness at scale (thousands of pods starting) causes endpoint churn.
- **Propagation delay** between "pod ready" and "all nodes route to it" is typically 1 to 5 seconds (controller → API → kube-proxy sync, plus its batch interval); the reverse (removing a terminating pod) is a source of errors during rollouts (fix: preStop sleep, graceful shutdown, 5.7).
- Services without ready endpoints: connections fail (iptables mode `REJECT` with ICMP port unreachable / connection refused; IPVS: no real server); `kubectl get endpointslices` empty shows selector mismatch or no ready pods.

## 3. kube-proxy

`kube-proxy` runs on every node (DaemonSet or static), watches Services and EndpointSlices (and Node topology labels), and programs the node's datapath so ClusterIP:port traffic reaches a backend. It does **not** proxy traffic in the data path in modern modes (the older userspace mode did); it only programs rules. Configuration: `KubeProxyConfiguration` (ConfigMap `kube-system/kube-proxy`): `mode`, `clusterCIDR`, `iptables`/`ipvs`/`nftables` sections (`syncPeriod`, `minSyncPeriod`, `masqueradeAll`, `scheduler`, `strictARP`), `conntrack` (`maxPerCore`, `min`, `tcpEstablishedTimeout`, `tcpCloseWaitTimeout`), `nodePortAddresses`, `metricsBindAddress`.

### iptables mode (default for many years)

For each Service/endpoint kube-proxy writes chains in the `nat` table (and `filter` for rejects):

```text
PREROUTING / OUTPUT  → KUBE-SERVICES
KUBE-SERVICES:   -d <ClusterIP> -p tcp --dport 80 → KUBE-SVC-XXXX     (one jump per Service port)
                 (also -m addrtype --dst-type LOCAL → KUBE-NODEPORTS for NodePorts)
KUBE-SVC-XXXX:   -m statistic --mode random --probability 0.33333 → KUBE-SEP-AAAA
                 -m statistic --mode random --probability 0.50000 → KUBE-SEP-BBBB
                 → KUBE-SEP-CCCC                                        (random load balancing, no real round robin)
KUBE-SEP-AAAA:   -s <podIP> → KUBE-MARK-MASQ  (hairpin: pod talking to its own Service)
                 -p tcp → DNAT --to-destination <podIP>:<targetPort>
POSTROUTING:     KUBE-POSTROUTING: -m mark --mark 0x4000 → MASQUERADE   (for NodePort/external traffic needing SNAT)
```

Packet path for pod A → ClusterIP: pod's netns sends to ClusterIP (default route to the node/bridge) → node's netfilter `PREROUTING` (for traffic from pods) → `KUBE-SERVICES` match → random `KUBE-SEP` → `DNAT` to pod IP; **conntrack** records the translation so return packets from the backend are un-NAT'd to look like they came from the ClusterIP; the packet is then routed to the destination pod (local veth or via CNI overlay/route to another node). Return traffic hits conntrack and is reverse-translated.

Characteristics: rule count grows linearly with Services × endpoints (O(n) chain traversal for `KUBE-SERVICES` matching, mitigated since 1.2x by using hash-based jumps for some cases); every sync rewrites the whole ruleset with `iptables-restore` (takes the xtables lock, can take seconds for tens of thousands of rules and consume significant CPU); connection-based random load balancing (new connections only; established flows stay on their backend via conntrack); no health checking of endpoints beyond readiness; per-packet cost small but rule update latency large at scale.

### IPVS mode

Uses the kernel's IP Virtual Server (L4 load balancer in netfilter) with hash tables: kube-proxy creates a virtual server per ClusterIP:port in a dummy interface `kube-ipvs0` and real servers (endpoints) with schedulers (`rr`, `lc`, `sh`, `dh`, `sed`, `nq`; set `ipvs.scheduler`); uses `ipset` sets for matching (`KUBE-CLUSTER-IP`, `KUBE-NODE-PORT-TCP`, ...) and a few iptables rules for masquerade. Complexity O(1) lookup; incremental updates (add/remove real server) instead of full rewrites; more schedulers; supports connection tracking and graceful termination (weight 0). Requirements: `ip_vs*` modules, `ipset`, `ipvsadm` for inspection; `strictARP: true` needed when using MetalLB L2. Caveats: still uses conntrack/iptables for SNAT/policy; historical bugs; upstream is deprioritising IPVS in favour of nftables; some CNIs/NetworkPolicy implementations assume iptables.

```bash
ipvsadm -Ln | head -30                  # virtual servers and real servers
ipvsadm -Lnc | head                     # IPVS connection table
ipset list KUBE-CLUSTER-IP | head
ip addr show kube-ipvs0 | head
```

### nftables mode

The modern kernel packet filter. kube-proxy (stable in recent releases) programs a single `kube-proxy` table with maps and verdict maps for O(1) Service lookup and incremental updates (`nft -f` transactions only changing deltas). Better scale and update latency than iptables, without IPVS's extra dependencies. Check availability in your Kubernetes and kernel version; coexistence with other iptables-based tooling (legacy `iptables` front-ends over nft backend) needs care. `nft list table ip kube-proxy`, `nft list chain ip kube-proxy services`.

### eBPF replacements (Cilium kube-proxy replacement, Calico eBPF dataplane)

An eBPF datapath replaces kube-proxy entirely: Service resolution happens at socket-connect time (`cgroup/connect4` hooks translate ClusterIP to a backend before the packet exists: "socket LB") or at tc/XDP ingress (for NodePort/external); load-balancing state lives in BPF maps (Maglev consistent hashing available, DSR (direct server return) to avoid SNAT hops), health checking, no conntrack for socket-level translations, much lower CPU at scale and faster updates. Run with `kubeProxyReplacement=true` (Cilium) and disable kube-proxy (`kubeadm init --skip-phases=addon/kube-proxy`). Requirements: modern kernels (5.10+ recommended), careful MTU/encap settings. Inspect with `cilium service list`, `cilium bpf lb list`, `hubble observe`. Trade-offs: different debug tools (no iptables rules to read), kernel-version dependency, CNI lock-in. See 5.14.

### Mode comparison

| | iptables | IPVS | nftables | eBPF (Cilium) |
|---|---|---|---|---|
| Lookup | Linear rule traversal | Hash O(1) | Map O(1) | Map O(1), socket-level |
| Update | Full `iptables-restore` | Incremental | Incremental | Incremental |
| LB algorithms | Random | rr, lc, sh, ... | Random (map-based) | Random, Maglev, DSR |
| Scale (10k+ Services) | Poor (seconds-long syncs) | Good | Good | Very good |
| Debuggability | Familiar (iptables-save) | ipvsadm, ipset | nft | Hubble, cilium CLI |
| Dependencies | iptables | ip_vs, ipset | nft kernel support | Kernel BPF features |

## 4. NodePort, LoadBalancer and traffic policies

### NodePort path

External client → `<nodeIP>:30080` on any node → `KUBE-NODEPORTS` → Service chains → DNAT to a pod (possibly on another node) and, in `Cluster` policy, **SNAT** (masquerade to the node's IP) so replies return via the node that received the connection. Costs: extra hop, source IP lost (pods see the node IP), potential imbalance.

### `externalTrafficPolicy`

- **`Cluster`** (default): any node may forward to any pod; load spreads across all pods but loses client source IP and adds a hop.
- **`Local`**: only endpoints on the receiving node are used; no SNAT, client IP preserved, no extra hop; nodes with no local endpoint fail health checks from the LB (a `healthCheckNodePort` is allocated; the LB must use it) and drop out. Risk: uneven load when endpoints are unevenly distributed (e.g., 3 pods across 10 nodes), and connection drops during rolling updates if the LB's health check lags. Use with topology spread and `maxSurge`, or with cloud LBs that route directly to pods (NEG/IP target mode).
- **`internalTrafficPolicy: Local`** does the same for in-cluster clients (node-local DNS caches, per-node daemon Services).

### LoadBalancer implementations

Cloud (AWS NLB/ALB, GCP LB, Azure LB): cloud-controller-manager creates LBs and node ports or direct pod targets. By default, a cloud `LoadBalancer` Service provisions a public internet-facing load balancer; to expose a Service only inside your private VPC/VNet, add the cloud provider's internal load-balancer annotation to `metadata.annotations`, as listed in *Kubernetes: Up and Running* (3rd edition, Chapter 7; untested here):

- **Google Cloud Platform (GKE)**: `cloud.google.com/load-balancer-type: "Internal"`
- **Amazon Web Services (EKS)**: `service.beta.kubernetes.io/aws-load-balancer-internal: "true"`
- **Microsoft Azure (AKS)**: `service.beta.kubernetes.io/azure-load-balancer-internal: "true"`
- **Alibaba Cloud**: `service.beta.kubernetes.io/alibaba-cloud-loadbalancer-address-type: "intranet"`

Bare metal/GPU clouds: **MetalLB** (L2 ARP/NDP announcements or BGP), **kube-vip**, **Cilium LB IPAM + BGP control plane**, **Calico BGP**, hardware LBs. For inference gateways prefer L7 ingress/Gateway API (5.12) in front of Services; keep L4 LBs for raw TCP (SSH bastions, databases, gRPC with specific needs).

### Session affinity and long-lived connections

- `sessionAffinity: ClientIP` pins a client IP to a backend for `timeoutSeconds` (default 10800): uses `recent` module (iptables) or IPVS persistence; breaks behind NAT where many clients share an IP.
- **L4 balancing is per connection**: HTTP/2 and gRPC multiplex many requests over one connection, so a client opens one connection and all requests hit one pod (the classic "uneven gRPC load" problem, severe for inference gateways). Solutions: headless Service + client-side load balancing (gRPC `round_robin`, xDS), L7 proxies (Envoy/Istio/Linkerd/ingress), connection age limits (`MAX_CONNECTION_AGE` on servers), or a service mesh (5.28).

### Source IP and hairpin

Pod-to-own-Service traffic ("hairpin") requires `KUBE-MARK-MASQ` for same-endpoint selection, and bridge `hairpin_mode` or promiscuous setups for bridge CNIs. Pod-to-Service traffic normally keeps the client pod IP as source (no SNAT) inside the cluster for iptables/IPVS modes; traffic leaving the cluster is SNAT'd by the CNI/NAT gateway.

## 5. conntrack: the hidden state

Every NAT'd Service connection uses a `conntrack` entry on the node (and often on the destination node's reverse path in overlay setups). Limits: `net.netfilter.nf_conntrack_max` (default scales with memory), hash buckets, per-state timeouts (TCP established 5 days default; kube-proxy sets `tcpEstablishedTimeout` 24 h, `tcpCloseWaitTimeout` 1 h). Failure modes:

- **Table full** (`nf_conntrack: table full, dropping packet` in `dmesg`): random connection failures on busy nodes (ingress gateways, NAT'd egress, DNS storms). Fix: raise `nf_conntrack_max` (and buckets), reduce lifetimes, avoid per-request connections, use NodeLocal DNSCache, eBPF datapath, or avoid conntrack for UDP DNS (`NOTRACK` for NodeLocal).
- **UDP stale entries**: when a UDP backend pod (e.g., DNS, syslog) is deleted, conntrack may keep sending to the old IP until timeout; kube-proxy deletes stale UDP conntrack entries on endpoint changes, but bugs/races occurred; check with `conntrack -L -p udp | grep <svc>`.
- **Races causing 1 s/5 s DNS delays**: parallel A/AAAA lookups sharing a UDP source port racing DNAT insertion (kernel conntrack race, mitigated with `single-request-reopen`/TCP/NodeLocal DNS; fixed in newer kernels) (5.11).
- **Asymmetric routing/unexpected SNAT** breaking stateful firewalls.

```bash
sysctl net.netfilter.nf_conntrack_max net.netfilter.nf_conntrack_count
conntrack -S | head                       # per-CPU stats: drops, insert_failed, search_restart
conntrack -L | wc -l
conntrack -L -d 10.96.12.34 | head        # entries for a ClusterIP
cat /proc/net/stat/nf_conntrack | head -3
dmesg -T | grep -i conntrack
```

## 6. Topology-aware routing and other features

- **Topology Aware Routing / `trafficDistribution: PreferClose`** (and the annotation `service.kubernetes.io/topology-mode: Auto` in earlier releases): EndpointSlice **hints** keep traffic within the same zone when endpoints are balanced, reducing cross-zone latency and cost; requires zone labels on nodes and enough endpoints per zone, else falls back to cluster-wide.
- **Terminating endpoints**: when all ready endpoints are gone, proxies use `serving && terminating` endpoints to avoid dropping connections during rolling updates (needs `externalTrafficPolicy: Local` fallback semantic in recent versions).
- **Dual-stack**: IPv4+IPv6 ClusterIPs, `ipFamilies`, `ipFamilyPolicy`; EndpointSlices per address family; ensure CNI and kube-proxy support it.
- **Service CIDR changes** are hard; allocate a large service range initially; newer releases support multiple ServiceCIDRs (`ServiceCIDR`/`IPAddress` objects).
- **Load balancer source ranges** (`loadBalancerSourceRanges`), `externalIPs` (avoid; security risk CVE class), `publishNotReadyAddresses` for headless discovery before readiness (StatefulSet peers), `allocateLoadBalancerNodePorts`.
- **ServiceInternalTrafficPolicy and node-local services**: per-node daemons (log agents, DNS caches, GPU metrics scrapers) can be reached node-locally.

## 7. Debugging Services

Method: **resolve → endpoints → rules → datapath → backend**.

```bash
# 1. Does the Service select pods and do they have ready endpoints?
kubectl get svc vllm -n serving -o wide
kubectl get endpointslices -n serving -l kubernetes.io/service-name=vllm -o yaml | yq '.items[].endpoints'
kubectl get pods -n serving -l app=vllm -o wide           # labels match? Ready?
kubectl describe svc vllm -n serving                      # Endpoints: <none> means selector or readiness problem

# 2. From a client pod: DNS and connectivity
kubectl run -it --rm dbg --image=nicolaka/netshoot --restart=Never -n serving -- bash
  nslookup vllm; dig +short vllm.serving.svc.cluster.local
  curl -v http://vllm.serving.svc.cluster.local/health
  curl -v http://<clusterIP>:80/                           # bypass DNS
  curl -v http://<podIP>:8000/health                       # bypass Service (tests pod/CNI)

# 3. On the node: kube-proxy rules
kubectl -n kube-system logs ds/kube-proxy | tail            # mode, sync errors
iptables-save -t nat | grep -E "vllm|KUBE-SVC" | head -20   # service chain for the ClusterIP
iptables -t nat -L KUBE-SERVICES -n | grep <clusterIP>
nft list ruleset | grep -A3 <clusterIP>                     # nftables mode
ipvsadm -Ln | grep -A4 <clusterIP>                          # ipvs mode
conntrack -L -d <clusterIP>                                  # live translations

# 4. Packets
tcpdump -ni any host <clusterIP> or host <podIP> -c 50       # before/after DNAT: ClusterIP on the pod veth, pod IP after the node
tcpdump -ni <veth> port 8000
```

| Symptom | Likely cause | Check |
|---|---|---|
| `connection refused` immediately | No ready endpoints (iptables REJECT) or app not listening on targetPort | EndpointSlices, `ss -ltn` in pod |
| Timeout from some nodes only | CNI/overlay issue, NetworkPolicy, kube-proxy not running there, `br_netfilter` off | kube-proxy pod on that node, `sysctl net.bridge.bridge-nf-call-iptables`, route tables |
| Works via PodIP, not ClusterIP | kube-proxy rules missing/stale, conntrack, wrong targetPort | `iptables-save \| grep`, kube-proxy logs, `kubectl get endpointslices` |
| Works inside cluster, not via NodePort/LB | Firewall/security group, `externalTrafficPolicy: Local` with no local pod, LB health check | `healthCheckNodePort`, cloud LB status |
| Client IP is node IP | `externalTrafficPolicy: Cluster` SNAT | Use `Local` or LB with proxy protocol/XFF |
| Sporadic 1-5 s delays on DNS | conntrack UDP race | NodeLocal DNS, single-request-reopen, kernel update |
| Resets during rollouts | Endpoint removal race, no preStop, readiness too eager | 5.7 termination practices |
| Uneven load on gRPC | L4 balancing of long-lived connections | headless + client LB, L7 proxy |
| kube-proxy high CPU / slow updates | iptables mode with huge rule count | IPVS/nftables/eBPF, reduce Services, tune `minSyncPeriod` |
| `Service has no endpoints` for a StatefulSet headless | pods not ready, `publishNotReadyAddresses` needed | Readiness |
| NodePort unreachable on some interfaces | `nodePortAddresses` restrictions | kube-proxy config |

kube-proxy metrics: `kubeproxy_sync_proxy_rules_duration_seconds`, `kubeproxy_sync_proxy_rules_last_timestamp_seconds`, `kubeproxy_network_programming_duration_seconds` (time from endpoint change to programmed), `kubeproxy_sync_proxy_rules_iptables_total`. Alert if programming latency exceeds a few seconds or syncs stall.

## 8. Scaling guidance

- Count: Services (thousands), EndpointSlices (tens of thousands), rules/entries per node. iptables mode degrades beyond ~5,000 Services or ~25,000 endpoints (sync times grow to many seconds; CPU spikes on every change). Use IPVS/nftables/eBPF beyond that.
- Reduce churn: avoid flapping readiness; batch rollouts; set `kube-proxy --iptables-min-sync-period`; consolidate redundant Services; avoid per-job Services for thousands of short jobs unless headless DNS is required (JobSet/MPI operators create headless Services per job: monitor total count).
- Conntrack sizing for gateway/ingress nodes; dedicated nodes for heavy NAT.
- NodeLocal DNSCache to remove DNS from the conntrack path (5.11).
- For AI inference at high QPS: avoid sending bulk token streams through multiple NAT layers; prefer direct pod IP routing (LB with pod targets, DSR), keep-alive and HTTP/2 tuned connection reuse, and L7 gateways with request-aware balancing (least-outstanding-requests, cache-aware routing, 5.12 and Part 15).
- For RDMA/NCCL traffic: Services are irrelevant; use pod IPs on secondary networks (Part 12); rendezvous via headless Services or the launcher's hostfile.

## 9. Lab (untested)

1. **Anatomy**: create a Deployment and ClusterIP Service; list the EndpointSlice; compare ready vs unready (fail the readiness probe on one pod) and watch the slice change; delete selectors' labels and see `Endpoints: <none>`.
2. **iptables mode walk**: on a node, find the `KUBE-SVC-*` and `KUBE-SEP-*` chains for the Service; compute the probabilities; use `conntrack -E` while curling to watch `NEW` and `DESTROY` events and DNAT mapping; use `tcpdump` at the pod veth and the node interface to see ClusterIP vs pod IP.
3. **Mode switch**: change kube-proxy to `ipvs` (modules loaded), compare `ipvsadm -Ln`, connection tables and update latency with 2,000 Services (create with a loop or `kube-burner`); then `nftables` mode if available; measure `kubeproxy_sync_proxy_rules_duration_seconds` in each.
4. **NodePort and policies**: expose via NodePort; curl from outside with `externalTrafficPolicy: Cluster` and `Local`, print `X-Forwarded-For`/source IP in the server; deploy fewer pods than nodes and see Local failing on nodes without endpoints; check `healthCheckNodePort`.
5. **MetalLB**: install MetalLB in L2 mode on the lab network; create a `LoadBalancer` Service; observe ARP announcements (`arping`, `ip neigh`); switch to BGP with FRR (2.15, 2.27) and see routes; test failover by cordoning the speaker node.
6. **Headless and DNS**: create a headless Service and StatefulSet; resolve A records per pod; use `dig SRV`; compare to ClusterIP resolution; show gRPC client-side round-robin.
7. **gRPC imbalance**: deploy a gRPC echo service; run a client with one connection and 1,000 requests; show all land on one pod; fix with headless + `round_robin` or an Envoy gateway; graph per-pod request counts.
8. **conntrack exhaustion**: set a tiny `nf_conntrack_max` on a lab node and generate many connections (hping/ab/fortio); observe drops and `dmesg`; raise limits and compare; measure impact of NodeLocal DNSCache.
9. **Rollout race**: serve traffic through a Service while rolling a Deployment with and without `preStop` sleep and readiness delay; count errors; tune.
10. **Topology routing**: label nodes with zones, enable `trafficDistribution: PreferClose`, and show requests staying in-zone via per-pod logs; observe fallback when a zone has no endpoints.
11. **Cilium kube-proxy replacement**: in a lab cluster install Cilium with `kubeProxyReplacement=true`; verify no `KUBE-SVC` rules; use `cilium service list`, `hubble observe`; compare latency and CPU in a load test.
12. **Debug drill**: break a Service in five ways (wrong selector, wrong targetPort, readiness failing, NetworkPolicy deny, kube-proxy stopped on one node) and diagnose each with the method above.
13. **Clean up**.

Mark tested only after execution.

## 10. Common mistakes

- Selectors that don't match pod labels (or match pods from another Deployment); wrong `targetPort`; forgetting named-port mismatches.
- Expecting round-robin: iptables mode is random per new connection; long-lived connections stay put.
- Assuming a Service IP is pingable (ICMP to ClusterIP usually isn't handled).
- Using `externalTrafficPolicy: Local` without topology spread or LB health checks.
- Running iptables-mode kube-proxy with tens of thousands of Services; ignoring sync latency.
- Ignoring conntrack limits on ingress/gateway nodes; DNS over UDP storms without NodeLocal DNS.
- Treating `ExternalName` as a proxy; using `externalIPs` or exposing NodePort ranges publicly.
- Running L4 balancing for HTTP/2/gRPC inference traffic and expecting even load.
- Forgetting that NetworkPolicy and host firewalls affect node→pod probes and Service traffic.

## 11. Interview angles

- "How does a ClusterIP work? There's no process; explain what happens to a packet." 
- "iptables vs IPVS vs nftables vs eBPF kube-proxy: trade-offs and scale limits." 
- "What is an EndpointSlice and why did it replace Endpoints?" 
- "Explain `externalTrafficPolicy: Local` vs `Cluster`." 
- "A Service works from some pods but not others. How do you debug?" 
- "Why does gRPC load balance badly through a Service? Fixes?" 
- "What breaks when conntrack fills up? How do you size/monitor it?" 
- "How would you expose an inference gateway on bare metal?" (MetalLB/BGP, ingress/Gateway, traffic policy.)

## 12. Checkpoint questions (40)

1. Is there a process behind a ClusterIP? **A:** No; kernel rules/BPF implement it.
2. Service types, what `kube-apiserver` flag sets the ClusterIP range, and what annotations request an internal cloud LoadBalancer on GCP, AWS, and Azure? **A:** ClusterIP, NodePort, LoadBalancer, ExternalName (+ headless); `--service-cluster-ip-range` (e.g., `10.96.0.0/12`); `cloud.google.com/load-balancer-type: "Internal"`, `service.beta.kubernetes.io/aws-load-balancer-internal: "true"`, and `service.beta.kubernetes.io/azure-load-balancer-internal: "true"`.
3. NodePort range? **A:** 30000-32767.
4. Headless Service means? **A:** `clusterIP: None`; DNS returns pod IPs.
5. What replaced Endpoints? **A:** EndpointSlices.
6. Slice default size? **A:** 100 endpoints.
7. What makes an endpoint ready? **A:** Pod Ready condition true.
8. What are `serving`/`terminating`? **A:** Endpoint states for graceful drain.
9. kube-proxy role? **A:** Program Service datapath rules on each node.
10. iptables mode LB? **A:** Random via statistic match.
11. Why DNAT? **A:** Rewrite ClusterIP to pod IP.
12. What does conntrack do here? **A:** Remember translation for return traffic.
13. IPVS advantages? **A:** O(1) lookup, incremental updates, more schedulers.
14. nftables advantage? **A:** Maps, incremental, modern.
15. eBPF replacement example? **A:** Cilium kube-proxy replacement.
16. Socket LB means? **A:** Translate at connect() before packets are created.
17. `externalTrafficPolicy: Local` preserves what? **A:** Client source IP, no extra hop.
18. Risk of Local? **A:** Uneven load/nodes without endpoints.
19. `healthCheckNodePort` purpose? **A:** LB health checks for Local policy.
20. `sessionAffinity: ClientIP` effect? **A:** Pin client IP to a backend.
21. gRPC imbalance cause? **A:** Long-lived multiplexed connection on L4 balancing.
22. Fix for gRPC imbalance? **A:** Client-side LB (headless), L7 proxy, mesh.
23. What is hairpin traffic? **A:** Pod to its own Service back to itself.
24. What is `internalTrafficPolicy: Local`? **A:** Cluster clients only use node-local endpoints.
25. What does `trafficDistribution: PreferClose` do? **A:** Prefer same-zone endpoints.
26. conntrack full symptom? **A:** Dropped packets, `table full` in dmesg.
27. sysctl for conntrack size? **A:** `net.netfilter.nf_conntrack_max`.
28. DNS 5s delay cause? **A:** conntrack race with parallel A/AAAA over UDP.
29. NodeLocal DNSCache benefit? **A:** Avoid conntrack/DNAT for DNS, caching.
30. MetalLB modes? **A:** L2 and BGP.
31. `strictARP` needed for? **A:** IPVS with MetalLB L2.
32. ExternalName behaviour? **A:** DNS CNAME only.
33. Services without selectors use? **A:** Manually managed EndpointSlices.
34. Metric for programming delay? **A:** `kubeproxy_network_programming_duration_seconds`.
35. iptables mode sync method? **A:** `iptables-restore` full rewrite.
36. Why not ping ClusterIP? **A:** No ICMP handling by default.
37. `publishNotReadyAddresses` use? **A:** Headless discovery before readiness.
38. Dual-stack field? **A:** `ipFamilyPolicy`.
39. How check which backend got a connection? **A:** `conntrack -L`, server logs.
40. When not to use Services? **A:** RDMA/NCCL data plane (use pod IPs/secondary nets).

## 13. Sources and review notes

**Written in original words.** Principal sources:

- Brendan Burns et al., *Kubernetes: Up and Running* (`kubernetes-up-and-running-3rd-edition`, 3rd edition; Chapter 7: `7. Service Discovery` — read in full for Service DNS, readiness checks, `--service-cluster-ip-range` on `kube-apiserver`, internal LoadBalancer annotations across GCP/AWS/Azure/Alibaba, and selector-less Services with manual `Endpoints`).
- James Strong and Vallery Lancey, *Networking and Kubernetes* (chapters on Services, kube-proxy modes, ingress).
- Josh Rosso et al., *Production Kubernetes* (chapter 6 on service routing).
- Kubernetes documentation on Services, EndpointSlices, kube-proxy modes and topology-aware routing; Cilium and MetalLB documentation.
- Examples are the author's constructions.

**Flagged for verification before publishing:** nftables kube-proxy status, `trafficDistribution` and multiple ServiceCIDR feature status by release, conntrack timeout defaults, chain names across versions, scale thresholds, and every command listing; all labs are **untested**.
