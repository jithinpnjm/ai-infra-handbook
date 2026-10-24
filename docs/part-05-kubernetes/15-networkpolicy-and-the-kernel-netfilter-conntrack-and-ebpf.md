---
id: "c05-15"
title: "5.15 NetworkPolicy and the kernel: netfilter, conntrack and eBPF"
sidebar_label: "5.15 NetworkPolicy and the kernel: netfilter, conntrack and eBPF"
sidebar_position: 15
description: "Network policy in Kubernetes: the NetworkPolicy API and its semantics, default-deny patterns, policy design for multi-tenant AI platforms, how CNIs enforce policy (iptables/ipsets, nftables, eBPF), conntrack interaction, extended policy (Calico, Cilium, admin and baseline policies), testing, and troubleshooting"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 5.15 NetworkPolicy and the kernel: netfilter, conntrack and eBPF

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | Kubernetes with Calico or Cilium (Flannel alone does not enforce policy); `kubectl`, `calicoctl`/`cilium`/`hubble`, `iptables-save`, `nft`, `ipset`, `conntrack`, `tcpdump` |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Kubernetes networking is flat and open by default: any pod can connect to any other pod and to the node. In a shared GPU platform that means one team's notebook could reach another team's model server, a compromised dependency in a training job could scan the cluster, metadata endpoints and the API server, and data-exfiltration paths are wide open. NetworkPolicy is the baseline control to segment tenants and workloads (inference vs training vs data services vs system components), to constrain egress to approved storage and registries, and to meet compliance requirements. Because enforcement lives in the node kernel (iptables/ipsets or eBPF programs), misunderstanding its semantics produces both security holes and self-inflicted outages (DNS blocked, probes failing, operators unable to reach webhooks). This chapter explains the API precisely, shows how enforcement works in the kernel, and gives practical policy patterns and testing methods for AI platforms.

## Prerequisites and outcomes

Needs 5.10, 5.13, 5.14 and Linux netfilter basics (2.23). After this chapter you can:

- Write correct `NetworkPolicy` resources: pod selectors, namespace selectors, ipBlock, ports (including port ranges), ingress/egress, policy types, additive semantics; predict allow/deny for any flow.
- Implement a layered pattern: default-deny per namespace, DNS/probe/system allowances, per-app allow rules, controlled egress.
- Explain how CNIs enforce policy: iptables chains + ipsets (Calico), eBPF policy maps with identities (Cilium), nftables; and how conntrack makes policies stateful.
- Use extended policy APIs (CalicoGlobalNetworkPolicy, CiliumNetworkPolicy, AdminNetworkPolicy/BaselineAdminNetworkPolicy) and L7/FQDN rules.
- Test and observe policy (Hubble, Calico flow logs, `cilium policy trace`, netshoot, kube-netpol linting tools) and debug failures.
- Design policy for multi-tenant GPU clusters including the traps (node-local traffic, hostNetwork pods, probes, webhooks, metadata services, RDMA/secondary networks).

## 1. The NetworkPolicy API

NetworkPolicy is namespaced, additive, and **allow-list based**. Key facts:

- A policy **selects pods** (`podSelector`) in its own namespace. Pods not selected by any policy for a given direction are **non-isolated** for that direction (all traffic allowed). Once a pod is selected by at least one policy that includes the direction in `policyTypes`, it becomes **isolated** for that direction: only traffic allowed by the union of all applicable policies is permitted.
- Policies are **additive**: there are no deny rules and no ordering; the allowed set is the union of all matching rules.
- **Stateful**: reply traffic for an allowed connection is automatically allowed (via connection tracking); policies describe the direction in which the connection is *initiated*.
- `policyTypes` default: `Ingress` always; `Egress` only if the policy has egress rules. Specify explicitly to avoid surprises.
- Enforcement is **implemented by the CNI**: with a CNI that doesn't support NetworkPolicy (plain Flannel, basic bridge), policies are accepted by the API and silently ignored.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-gateway-to-model
  namespace: serving
spec:
  podSelector:                                  # pods this policy applies to
    matchLabels: { app: vllm }
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - namespaceSelector:                     # AND within one element: pods labelled in namespaces labelled
            matchLabels: { kubernetes.io/metadata.name: edge }
          podSelector:
            matchLabels: { app: gateway }
        - ipBlock:                               # separate list element = OR
            cidr: 10.20.0.0/16
            except: [10.20.5.0/24]
      ports:
        - { protocol: TCP, port: 8000 }
        - { protocol: TCP, port: 9000, endPort: 9010 }
  egress:
    - to:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } }
          podSelector: { matchLabels: { k8s-app: kube-dns } }
      ports: [ { protocol: UDP, port: 53 }, { protocol: TCP, port: 53 } ]
    - to: [ { ipBlock: { cidr: 10.30.0.0/16 } } ]   # object storage VIPs
      ports: [ { protocol: TCP, port: 443 } ]
```

### Selector semantics (a common source of mistakes)

Within a `from`/`to` list:

- Each **list element** is OR'd with the others.
- Within one element, `namespaceSelector` **and** `podSelector` are AND'd (pods matching `podSelector` in namespaces matching `namespaceSelector`).
- An element with only `podSelector` means "pods in the **policy's own namespace**"; with only `namespaceSelector` means "all pods in matching namespaces"; an empty `namespaceSelector: {}` matches all namespaces; an empty `podSelector: {}` matches all pods (in the relevant namespace scope).
- `ipBlock` matches IP ranges (with `except`), intended for **cluster-external** IPs; pod IPs are ephemeral and CNI-dependent in how/if `ipBlock` applies to them; avoid using it to select pods.
- Namespaces have the automatic label `kubernetes.io/metadata.name: <name>`, which makes by-name namespace selection reliable.
- An **empty `ingress: []`/no rules with `policyTypes: [Ingress]`** denies all ingress to selected pods; `ingress: [{}]` allows all.
- Ports: protocol default TCP; named ports allowed (resolved per target pod); `endPort` ranges; SCTP support depends on the CNI. Omitting `ports` allows all ports for that peer.

### Default-deny and baseline patterns

```yaml
# 1. Default deny all ingress and egress in a namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-all, namespace: team-a }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
# 2. Allow DNS egress for all pods (otherwise nothing resolves)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-dns, namespace: team-a }
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } }
          podSelector: { matchLabels: { k8s-app: kube-dns } }
        - ipBlock: { cidr: 169.254.20.10/32 }          # NodeLocal DNSCache (5.11)
      ports: [ { protocol: UDP, port: 53 }, { protocol: TCP, port: 53 } ]
---
# 3. Allow same-namespace traffic (optional baseline for a team namespace)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-same-namespace, namespace: team-a }
spec:
  podSelector: {}
  policyTypes: [Ingress]
  ingress: [ { from: [ { podSelector: {} } ] } ]
```

Design guidance: start with default-deny **ingress** everywhere (low risk), then add default-deny **egress** with explicit DNS, API server, storage, registry and monitoring allowances; roll out gradually using policy audit/logging modes (Calico staged policies, Cilium audit mode, Hubble) to see what would be blocked; manage policies as code (GitOps, 4.26) with label conventions (`app`, `tier`, `team`) and shared "building block" policies.

## 2. Things NetworkPolicy does not do (and traps)

| Gap/trap | Detail | Mitigation |
|---|---|---|
| No cluster-wide policy | Policies are namespaced; a platform-wide rule must be repeated per namespace | Admin/Baseline policies, CNI global policies, Kyverno generating default policies per namespace |
| No explicit deny / ordering | Cannot say "allow all except X" across policies | Use CNI extended policies with ordering and deny actions (Calico, Cilium, AdminNetworkPolicy) |
| No L7 (HTTP path, gRPC method, DNS names) | Only L3/L4 | CiliumNetworkPolicy L7, Calico Enterprise/Istio AuthorizationPolicy, proxies |
| No FQDN egress | `ipBlock` requires static IPs; SaaS endpoints change | Cilium `toFQDNs`, Calico DNS policy (Enterprise), egress proxies |
| Node-local traffic | Traffic from the pod's own node (kubelet probes, hostPort) is generally allowed by CNIs regardless; cross-node host traffic treatment varies | Understand your CNI: Calico `defaultEndpointToHostAction`, Cilium host policies; ensure probes work with deny |
| `hostNetwork` pods | Not subject to pod NetworkPolicy (they share the node's identity) | Pod Security to restrict hostNetwork; host firewall policies (Calico HostEndpoints, Cilium host policy) |
| Service IPs | Policies see pods (post-DNAT) in most CNIs; selecting by ClusterIP via `ipBlock` is unreliable | Match backend pods by labels |
| Egress to cluster services | Egress rules should target pod endpoints (post-NAT), not ClusterIP, except in implementations that evaluate pre-NAT | Test; prefer selectors |
| API server access | Egress to the Kubernetes API (`kubernetes.default`) is a node/control-plane IP | Allow `ipBlock` for control plane IPs or use Cilium `toEntities: kube-apiserver` |
| Admission webhooks | API server (host network or control plane) must reach webhook pods | Allow ingress from control plane CIDRs/nodes to webhook ports |
| Probes | Kubelet probes originate from the node | Allowed by default in most CNIs; with host firewalls allow node → pod |
| Multi-network pods | Policy applies to the primary CNI interface only; Multus secondary interfaces (RDMA) bypass it | Treat RDMA fabrics as separate trust domains (VLAN/PKey isolation); `MultiNetworkPolicy` for supported plugins |
| Cross-cluster / external traffic | Source IP may be SNATed by LBs (`externalTrafficPolicy`), breaking `ipBlock` | Use `Local` policy, PROXY protocol, or L7 auth |
| Policy creation races | A pod can start before policy is programmed (brief allow window or deny window) | Some CNIs block endpoint creation until policy loaded (Cilium), readiness gating |
| Logging | Standard API has no logging | CNI features: Calico flow logs/log action, Cilium Hubble |

## 3. How enforcement works in the kernel

### Netfilter basics and conntrack

Policy engines hook packets traversing the node: pod egress on the host-side veth (or tc ingress on the veth), pod ingress when delivering to the veth, and node-to-pod traffic. Linux **netfilter** provides hooks (`PREROUTING`, `FORWARD`, `INPUT`, `OUTPUT`, `POSTROUTING`) used by iptables/nftables; **conntrack** tracks flows so rules can match `ESTABLISHED,RELATED` and replies pass automatically (the "stateful" property). Because conntrack entries persist across rule changes, an already-established connection may continue after a policy that would block new connections is applied (until it ends or the entry times out), a frequent confusion when testing; to cut existing flows delete the conntrack entries (`conntrack -D`) or use CNI features that flush on policy change.

### Calico (iptables dataplane)

Felix compiles policy into iptables chains with **ipsets** for selectors:

```text
cali-FORWARD → cali-from-wl-dispatch / cali-to-wl-dispatch
cali-from-wl-dispatch → cali-fw-<iface>  (traffic from workload <iface>): applies egress policies of that pod
cali-to-wl-dispatch   → cali-tw-<iface>  (traffic to workload): applies ingress policies
cali-pi-<policy> / cali-po-<policy>     chains per policy ingress/egress rules
ipsets: cali40s:<selector-hash> (sets of pod IPs matching a selector), cali40masq-ipam-pools ...
Rule form: -m set --match-set cali40s:xxxx src -p tcp --dport 8000 -j MARK --set-xmark 0x10000/0x10000 (allow mark) ... drop at end of profile chain
```

Selectors become ipsets maintained incrementally (membership changes = `ipset add/del`, cheap); rule counts grow with policies × ports, not with pod counts. Calico's **eBPF dataplane** replaces this with BPF programs and maps. Inspect: `iptables-save | grep cali-`, `ipset list | head`, `calicoctl get networkpolicy -A -o wide`, `calicoctl get globalnetworkpolicy`, `calicoctl get workloadendpoint -n ns pod -o yaml` (shows applied profiles).

### Cilium (eBPF)

Each endpoint has BPF programs at tc ingress/egress on its device; identities (from labels) replace IPs in policy decisions. The policy map per endpoint (`cilium_policy_<id>`) contains entries keyed by (identity, port, protocol, direction) with allow/deny flags and optional L7 redirect to Envoy. Pod → pod: egress program looks up the destination identity via `ipcache`, checks the source endpoint's egress policy, then the destination's ingress policy is checked at the receiver (for local) or via identity carried in the tunnel header (for remote). Connection tracking in BPF CT maps makes it stateful; policy verdicts are reported to Hubble. L7 policies redirect matching flows to a per-node Envoy proxy (adds latency but allows HTTP/gRPC/Kafka/DNS awareness; DNS-based `toFQDNs` rules use the DNS proxy to learn IPs for names and update maps with TTL). Inspect: `cilium endpoint list`, `cilium policy get`, `cilium bpf policy get <ep-id>`, `cilium monitor --type policy-verdict`, `hubble observe --verdict DROPPED`, `cilium policy trace --src-k8s-pod ns:pod --dst-k8s-pod ns:pod --dport 8000`.

### nftables-based and other implementations

Antrea (OVS flows), OVN-Kubernetes (OVN ACLs/OVS), kube-router (iptables + ipsets), and nftables backends exist; semantics are the Kubernetes API's, differences are in extended features and performance. Cloud: AWS VPC CNI supports policy via eBPF in newer versions or Calico add-on; GKE Dataplane V2 (Cilium) and Azure NPM/Cilium.

### Performance considerations

Policy evaluation cost is O(#rules) per new connection in iptables (ipset lookups are O(1) per set), BPF map lookups O(1); most cost is on connection establishment. Large numbers of policies/selectors increase compile time and memory (Felix full resyncs, Cilium regeneration); avoid thousands of near-duplicate policies (generate fewer, label-driven ones). Egress to large dynamic FQDN sets expands maps. For AI nodes, policy overhead matters less for long-lived bulk flows and more for connection-heavy services (ingress gateways, DNS).

## 4. Extended policy models

### Calico

`NetworkPolicy` (namespaced) and `GlobalNetworkPolicy` (cluster-wide, can target host endpoints) with `order` (priority), `Allow`/`Deny`/`Log`/`Pass` actions, `selector` expressions on labels (`app == 'x' && has(team)`), namespace selectors, service accounts selectors, ICMP, protocols, CIDRs, `doNotTrack`/`preDNAT`/`applyOnForward` for host policies, staged policies (`StagedNetworkPolicy`) to preview effects, and tiers (Enterprise) for hierarchical governance.

```yaml
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata: { name: deny-metadata-and-private-egress }
spec:
  order: 100
  selector: has(tenant)
  types: [Egress]
  egress:
    - action: Deny
      destination: { nets: [169.254.169.254/32] }          # cloud metadata endpoint
    - action: Allow
      destination: { selector: app == 'object-gateway' }
    - action: Allow
      protocol: UDP
      destination: { ports: [53] }
```

### Cilium

`CiliumNetworkPolicy` / `CiliumClusterwideNetworkPolicy`: `endpointSelector`, `ingress`/`egress` plus `ingressDeny`/`egressDeny` (deny takes precedence), `fromEntities`/`toEntities` (`world`, `cluster`, `host`, `remote-node`, `kube-apiserver`, `health`), `toFQDNs` (`matchName`, `matchPattern`), `toCIDR/toCIDRSet`, `toServices`, `toPorts` with L7 `rules.http` (`method`, `path`, headers), `kafka`, `dns`; `CiliumCIDRGroup`; host policies (`nodeSelector`); policy audit mode (`policyAuditMode`); `enable-policy` modes (`default`, `always`, `never`).

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata: { name: trainer-egress, namespace: training }
spec:
  endpointSelector: { matchLabels: { app: trainer } }
  egress:
    - toEndpoints:
        - matchLabels: { "k8s:io.kubernetes.pod.namespace": kube-system, "k8s:k8s-app": kube-dns }
      toPorts:
        - ports: [ { port: "53", protocol: ANY } ]
          rules: { dns: [ { matchPattern: "*" } ] }          # enable DNS visibility for toFQDNs learning
    - toFQDNs:
        - matchName: storage.googleapis.com
        - matchPattern: "*.huggingface.co"
      toPorts: [ { ports: [ { port: "443", protocol: TCP } ] } ]
    - toEntities: [kube-apiserver]
```

### Admin and baseline network policies

The `policy.networking.k8s.io` API group (SIG Network) defines **AdminNetworkPolicy** (cluster-scoped, evaluated *before* namespace NetworkPolicies, with `Allow`/`Deny`/`Pass` and priority; cluster admins set guardrails that tenants cannot override) and **BaselineAdminNetworkPolicy** (default posture evaluated *after* NetworkPolicies; e.g., default deny egress to the Internet unless allowed). Support is arriving in Cilium, Calico, OVN-K, Antrea and others: a standard route to cluster-wide guardrails for multi-tenant platforms; verify implementation maturity.

## 5. Policy design for a multi-tenant GPU platform

Tiers of the cluster and their expected flows:

| Zone | Examples | Policy stance |
|---|---|---|
| **Edge** | Ingress/Gateway, auth proxy | Ingress from LB/Internet on 443; egress to tenant model namespaces only |
| **Serving** | vLLM/Triton/gateways | Ingress only from gateway namespace; egress to storage/registry/metrics/DNS; no pod-to-pod across tenants |
| **Training** | Jobs, operators, launcher pods | Intra-job pod communication (rendezvous, NCCL over TCP if used) allowed within the job's label; egress to datasets/checkpoint storage; deny to other tenants; secondary RDMA networks isolated at fabric level |
| **Data services** | Vector DB, feature store, metadata (MLflow), object gateways | Ingress from approved client namespaces/labels; egress limited |
| **Platform/system** | kube-system, monitoring, GPU operator, Argo CD, cert-manager, Kueue | Controlled interactions; webhook/metrics/API server reachability |
| **Interactive** | Notebooks (JupyterHub) | Egress allow-list (package mirrors, internal APIs), no access to other tenants or cloud metadata; time-limited |
| **Untrusted code** | Customer containers, arbitrary notebooks | Default deny egress except specific proxies; sandboxed runtimes (5.2); no node/API access |

Practical rules:

1. **Label discipline** underpins policy: standardise `app.kubernetes.io/name`, `team`, `tier`, `job-name`/`training.kubeflow.org/job-name`; operators propagate job labels to pods; policy selects by those labels.
2. **Default deny + building blocks**: namespaces created by automation (Terraform/GitOps, 4.25) get default-deny and DNS/allowlist baseline automatically; teams add app-specific rules by PR.
3. **Protect the control plane and metadata**: deny egress to the cloud metadata IP (169.254.169.254) and to node/management networks from tenant pods; allow only the Kubernetes API where needed (operators), preferably through narrow RBAC.
4. **Training job communication**: allow all intra-job traffic by a label selector (`job-name: run-142`) in both directions; if workers need peer discovery before readiness (5.11), the policy allows the headless Service ports; sidecars, exporters and probes must be included. For NCCL over the secondary RDMA network, policy does not apply, so enforce isolation on the fabric (separate VLANs/VRFs, IB partition keys, or per-tenant physical racks) and keep primary-network policy for control traffic.
5. **Egress to storage and registries**: allow by CIDR of internal storage gateways; for SaaS endpoints use FQDN-capable policies or an egress proxy/gateway with allow-lists and logging.
6. **Observability**: enable flow logging/Hubble in audit mode first; review dropped flows weekly; alert on denies from production workloads (misconfiguration) and on allow-flows to forbidden destinations.
7. **Test in CI**: render policies and run `kubectl` e2e tests with netshoot (connect tests matrix) or tools such as `netassert`, `cyclonus` (NetworkPolicy conformance/test generator), Cilium connectivity tests, `kube-linter`/`kubesec` for missing policies, `kubectl-np-viewer`/Network Policy Editor (editor.networkpolicy.io) for visualisation and review.
8. **Break-glass and debugging**: provide a documented way to diagnose (policy trace, Hubble) and to temporarily widen a policy via PR with expiry, not by deleting the default-deny.

## 6. Testing and debugging

Method: define the exact flow (source pod, destination pod/IP, port, direction), identify applicable policies for both ends, predict, then test.

```bash
# What policies select this pod?
kubectl get netpol -n serving -o wide
kubectl describe netpol allow-gateway-to-model -n serving
# Quick tests
kubectl run -n edge tester --rm -it --image=nicolaka/netshoot --restart=Never -- bash
  curl -m 3 -v http://vllm.serving.svc:8000/health
  nc -vz -w 3 <pod-ip> 8000
# Is traffic dropped by policy? (Cilium)
hubble observe --from-pod edge/tester --to-pod serving/vllm-xxx --verdict DROPPED --last 20
cilium policy trace --src-k8s-pod edge:tester --dst-k8s-pod serving:vllm-xxx --dport 8000/tcp
cilium monitor --type drop
# Calico
calicoctl get networkpolicy -n serving -o yaml
sudo iptables -L cali-tw-<iface> -n -v --line-numbers | head -40          # counters on drop rules
sudo iptables -L | grep -E 'DROP.*cali'                                   # packet counters
calico-node -bird-ready; kubectl logs -n calico-system ds/calico-node | grep -i policy
# kernel view
conntrack -L -p tcp --dport 8000 | head
sudo tcpdump -ni <host-veth> 'tcp port 8000' -c 20                       # see SYN without SYN-ACK: dropped upstream
dmesg | grep -i 'cali\|DROP'                                              # if Log action configured
```

| Symptom | Likely cause | Fix |
|---|---|---|
| Everything breaks after default-deny | DNS egress missing; probes/webhooks/API server blocked | Add DNS allow; check kubelet probe paths (node-origin traffic); allow control-plane → webhook |
| Policy has no effect | CNI doesn't enforce policy; policy selects wrong namespace/labels; `policyTypes` missing | Verify CNI support, `kubectl get netpol -o yaml`, label match |
| Allowed flow still blocked | Missing reverse policy on the other end (ingress on dest AND egress on source if both isolated) | Check both sides; named port mismatch; SNAT hides source IP |
| Established connection survives new deny | conntrack | Delete conntrack entries / restart connection |
| `ipBlock` for pod IPs doesn't work | Pod IPs aren't intended for ipBlock (or SNAT in path) | Use podSelector/namespaceSelector |
| Works from node, not from pod | Node-origin traffic exempt | Test from a pod in the right namespace |
| Intermittent failures after pod restarts | Endpoint policy not yet programmed; ipset sync delay | Readiness gates; CNI settings for policy-before-start |
| Egress to Internet blocked unexpectedly | Default deny egress with no `world` allow or NAT/masquerade interplay | Add explicit egress; check proxies |
| Cross-namespace allow not working | Namespace label mismatch (`kubernetes.io/metadata.name`), AND/OR semantic error in selector list | Review the `from` list structure |
| NCCL/MPI works across tenants | Secondary network not under policy | Enforce at fabric/VLAN/PKey level |
| High CPU on CNI agent during policy churn | Too many policies/selectors; frequent label changes | Consolidate policies; avoid per-job unique policies; use stable labels |

## 7. Lab (untested)

1. **Prove CNI enforcement**: on a CNI without policy (Flannel), apply default-deny and show no effect; on Calico/Cilium show enforcement; read the netfilter/BPF artefacts.
2. **Selector semantics**: build the namespace/pod selector truth table by creating `from` lists with AND/OR variations and testing each with netshoot; record results.
3. **Layered policy**: implement default deny + DNS + gateway-to-app + app-to-DB rules for a three-tier app in two namespaces; add egress allowance to an "object store" pod by CIDR and by FQDN (Cilium `toFQDNs`).
4. **Kernel view**: for Calico, trace one packet through `cali-*` chains with counters and `ipset` membership; for Cilium, read the endpoint policy map and run `cilium policy trace`; compare which is easier to reason about.
5. **conntrack effect**: start a long TCP connection, apply a deny policy, show the connection continues; flush conntrack and show it breaks; discuss operational implications.
6. **Probe and webhook traps**: apply default-deny egress+ingress and break readiness probes/webhooks (use a validating webhook pod); restore by allowing node/control-plane sources.
7. **hostNetwork bypass**: show a `hostNetwork` pod ignoring pod policies; add a host policy (Calico HostEndpoint or Cilium host policy) and Pod Security restriction.
8. **Global guardrails**: create a Calico `GlobalNetworkPolicy` or Cilium clusterwide deny for the metadata IP and cross-tenant traffic; then, if available, an AdminNetworkPolicy/BaselineAdminNetworkPolicy and observe precedence versus namespace policies.
9. **Training job policy**: deploy a 4-pod distributed job (headless Service) with default-deny; write the policy that allows intra-job traffic by job label and egress to storage; verify rendezvous works, then block a neighbour tenant.
10. **Observability and audit mode**: enable Hubble (or Calico flow logs); run policies in audit/staged mode; produce a report of flows that would be denied; promote to enforce.
11. **Policy testing in CI**: generate a connectivity matrix test (expected allow/deny pairs) and run with cyclonus or a custom script against a kind cluster in CI (4.13).
12. **Scale test**: create thousands of pods and hundreds of policies; measure agent CPU/memory and time-to-enforce; compare Calico iptables, Calico eBPF and Cilium.
13. **Clean up**.

Mark tested only after execution.

## 8. Common mistakes

- Creating NetworkPolicies on a CNI that doesn't enforce them and believing the cluster is segmented.
- Default-deny egress without DNS, API server, or probe allowances; breaking operators and webhooks.
- Misreading selector AND/OR semantics (a missing dash converts OR into AND, widening or narrowing the rule).
- Using `ipBlock` for pod or Service IPs; ignoring SNAT effects on source IP.
- Assuming policy covers `hostNetwork` pods, node processes, and secondary (Multus/RDMA) interfaces.
- Testing only from the node (exempt) or only the allow path (never the deny).
- Forgetting both directions: ingress on the destination and egress on the source must both permit.
- Per-job unique policies at scale, causing agent churn.
- No audit/rollout mode; no flow visibility; applying cluster-wide deny during peak hours.
- Treating NetworkPolicy as the only isolation: it does not replace authentication, authorisation, mTLS, runtime isolation or fabric-level tenant separation.

## 9. Interview angles

- "How does NetworkPolicy work? What's the default? What is additive semantics?" 
- "Write a policy that only allows the gateway namespace to reach model servers on 8000, with DNS egress." 
- "AND vs OR in `from` selectors." 
- "How does Calico implement policy? How does Cilium? What changes with eBPF?" 
- "Why do established connections survive a new deny rule?" (conntrack.)
- "How would you isolate tenants on a shared GPU cluster, including RDMA traffic?" 
- "What are AdminNetworkPolicy and Cilium/Calico global policies for?" 
- "After applying default-deny everything broke. What did you forget?" 

## 10. Checkpoint questions (35)

1. NetworkPolicy scope? **A:** Namespaced.
2. Default without policies? **A:** All traffic allowed.
3. What isolates a pod? **A:** Being selected by a policy for a direction.
4. Are policies additive? **A:** Yes; union of allows.
5. Is there deny action? **A:** Not in the standard API.
6. Stateful? **A:** Yes, replies are allowed.
7. policyTypes default? **A:** Ingress; Egress only if egress rules exist.
8. `podSelector: {}` means? **A:** All pods in the namespace.
9. Two peers in one `from` element? **A:** AND (namespace and pod selector).
10. Separate `from` elements? **A:** OR.
11. Namespace name label? **A:** `kubernetes.io/metadata.name`.
12. `ipBlock` intended for? **A:** External IP ranges.
13. Who enforces policy? **A:** The CNI.
14. Calico selectors become? **A:** ipsets.
15. Cilium policy keyed on? **A:** Security identities.
16. What makes policy stateful in kernel? **A:** conntrack.
17. Why old connections survive? **A:** Established conntrack entries.
18. L7 policy tool? **A:** Cilium (Envoy), mesh.
19. FQDN egress? **A:** `toFQDNs` (Cilium) / DNS policy (Calico Enterprise).
20. hostNetwork pods and policy? **A:** Not covered by pod policies.
21. Secondary interfaces and policy? **A:** Not covered.
22. Probes and policy? **A:** Node-origin traffic usually allowed; verify.
23. AdminNetworkPolicy precedence? **A:** Evaluated before NetworkPolicy.
24. BaselineAdminNetworkPolicy? **A:** Default posture after namespace policies.
25. Calico global policy kind? **A:** `GlobalNetworkPolicy`.
26. Cilium deny field? **A:** `ingressDeny`/`egressDeny`.
27. Observe drops in Cilium? **A:** Hubble `--verdict DROPPED`.
28. Trace policy in Cilium? **A:** `cilium policy trace`.
29. Calico staged policy purpose? **A:** Preview before enforcing.
30. DNS egress required why? **A:** Name resolution needs UDP/TCP 53.
31. API server egress target? **A:** Control-plane IP / `kube-apiserver` entity.
32. Metadata endpoint IP? **A:** 169.254.169.254.
33. Test pod image? **A:** netshoot.
34. Policy testing tool? **A:** cyclonus.
35. Policy is not a replacement for? **A:** AuthN/Z, mTLS, runtime isolation.

## 11. Sources and review notes

**Written in original words.** Principal sources:

- James Strong and Vallery Lancey, *Networking and Kubernetes* (chapters 4 and 5 on network abstractions, policies and implementation details).
- Josh Rosso et al., *Production Kubernetes* (chapter 5 on pod networking including network policy).
- The author's `nvidia-devops` repository, volume 03 (networking and security operations masterclass: CNI dataplane, multi-tenancy, admission).
- Kubernetes NetworkPolicy documentation and the SIG Network AdminNetworkPolicy specification; Calico and Cilium policy documentation.
- Examples are the author's constructions.

**Flagged for verification before publishing:** AdminNetworkPolicy API group/version and implementation support, Cilium `toEntities` names and policy modes, Calico chain names, the exact behaviour of node-origin traffic and `ipBlock` for pod IPs per CNI, and every manifest/command; all labs are **untested**.
