---
id: "c05-11"
title: "5.11 DNS and service discovery with CoreDNS"
sidebar_label: "5.11 DNS and service discovery with CoreDNS"
sidebar_position: 11
description: "How cluster DNS works: records for Services and Pods, resolv.conf and ndots, CoreDNS architecture and Corefile plugins, scaling and caching, NodeLocal DNSCache, stub domains and external resolvers, DNS-based discovery for StatefulSets and distributed training, performance pitfalls and debugging"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 5.11 DNS and service discovery with CoreDNS

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Any cluster; `kubectl`, a `netshoot`/`dnsutils` pod, node access for `tcpdump` and `conntrack` |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

DNS is the first dependency of almost every pod: a training worker resolves its rendezvous address, a data loader resolves object-store endpoints, an inference gateway resolves model servers, MPI and PyTorch use headless Services for peer discovery, and every external API call (registries, Hugging Face, telemetry) begins with a lookup. Cluster DNS is also a classic hidden bottleneck: Kubernetes' default `ndots:5` multiplies queries, UDP conntrack races add 5-second stalls, one CoreDNS pod serving a 2,000-pod job start causes timeouts, and a failing DNS looks like "the network is down" across the entire platform. Knowing how records are generated, how resolvers behave inside pods, how CoreDNS is configured, and how to scale and debug it is basic platform hygiene.

## Prerequisites and outcomes

Needs 5.8, 5.10 and DNS fundamentals (2.8). After this chapter you can:

- List the DNS records Kubernetes creates (Services, headless Services, SRV, Pods, ExternalName) and the naming scheme.
- Explain `/etc/resolv.conf` in pods (`nameserver`, `search`, `ndots`, `options`), `dnsPolicy` values and `dnsConfig`, and the query amplification caused by `ndots:5`.
- Read and modify the CoreDNS Corefile (kubernetes, forward, cache, loop, errors, health, ready, prometheus, rewrite, hosts, template, autopath, ...) and configure stub domains and upstream resolvers.
- Scale and harden CoreDNS (replicas, autoscaling, resources, anti-affinity, PDB, NodeLocal DNSCache) and monitor it.
- Use DNS-based discovery for StatefulSets, headless Services and distributed training rendezvous; avoid DNS pitfalls with large jobs.
- Debug resolution failures systematically.

## 1. Records Kubernetes creates

DNS names follow `<name>.<namespace>.svc.<cluster-domain>` (default `cluster.local`). The DNS server is **CoreDNS** (the default since 1.13), deployed as a Deployment `coredns` in `kube-system` behind the Service `kube-dns` (ClusterIP usually `10.96.0.10`; legacy name retained). It watches the Kubernetes API (Services, EndpointSlices, Namespaces, optionally Pods) and answers authoritatively for the cluster domain.

| Object | Record |
|---|---|
| ClusterIP Service `svc` in `ns` | `svc.ns.svc.cluster.local.` A (and AAAA for IPv6) → ClusterIP |
| Headless Service (no ClusterIP) | `svc.ns.svc.cluster.local.` A/AAAA → set of ready pod IPs |
| Named port | SRV `_http._tcp.svc.ns.svc.cluster.local.` → target + port; for headless: one SRV per pod `pod.svc.ns.svc...` |
| StatefulSet pod behind headless Service with `serviceName` | `pod-0.svc.ns.svc.cluster.local.` A → that pod IP (stable per-pod identity) |
| ExternalName Service | CNAME → external name |
| Pod IP (optional `pods insecure`/`verified` mode) | `10-244-3-17.ns.pod.cluster.local.` A → 10.244.3.17 (rarely useful) |
| Pod with `hostname`/`subdomain` set and matching headless Service | `hostname.subdomain.ns.svc.cluster.local.` |
| Reverse lookups | PTR for Service IPs and pod IPs (via `kubernetes` plugin `PTR`) |

Short names work through the pod's search path: from namespace `ns`, `svc` resolves via `svc.ns.svc.cluster.local`; `svc.other-ns` resolves through `svc.cluster.local`. Cross-namespace access should use at least `svc.ns` or the FQDN.

```bash
kubectl run -it --rm dns --image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.3 --restart=Never -- sh
nslookup kubernetes.default
dig +short kubernetes.default.svc.cluster.local
dig +short SRV _https._tcp.kubernetes.default.svc.cluster.local
dig +short my-headless.ns.svc.cluster.local          # multiple A records
dig +short pod-0.my-headless.ns.svc.cluster.local
cat /etc/resolv.conf
```

## 2. Resolver behaviour inside pods

The kubelet writes the pod's `/etc/resolv.conf` according to `dnsPolicy`:

| `dnsPolicy` | Result |
|---|---|
| `ClusterFirst` (default) | `nameserver <kube-dns ClusterIP>`; search domains `<ns>.svc.<domain> svc.<domain> <domain>` plus the node's search domains; `options ndots:5`. Names not under the cluster domain are forwarded upstream by CoreDNS |
| `Default` | Inherit the node's resolver config (`/etc/resolv.conf` or the kubelet `resolvConf`) — **not** the default policy despite the name |
| `ClusterFirstWithHostNet` | For `hostNetwork: true` pods that still want cluster DNS |
| `None` | Use only `dnsConfig` (custom nameservers, searches, options) |

```yaml
spec:
  dnsPolicy: ClusterFirst
  dnsConfig:
    options:
      - { name: ndots, value: "2" }
      - { name: single-request-reopen }
      - { name: timeout, value: "2" }
      - { name: attempts, value: "3" }
    searches: ["extra.example.com"]
```

### The ndots:5 problem

`ndots:5` means "if the name has fewer than 5 dots, try the search domains first." A lookup of `api.example.com` (2 dots) from namespace `ml` produces up to **8+ queries** (A and AAAA each for): `api.example.com.ml.svc.cluster.local` → NXDOMAIN, `api.example.com.svc.cluster.local` → NXDOMAIN, `api.example.com.cluster.local` → NXDOMAIN, `api.example.com.<node-search>` ... and finally `api.example.com.` → answer. For external-heavy workloads (downloading datasets, calling APIs), this multiplies CoreDNS load and latency, and failed lookups produce many NXDOMAINs in CoreDNS logs. Mitigations:

- Use **fully qualified names with a trailing dot** in configs (`api.example.com.`) for external endpoints (skips search).
- Lower `ndots` (2 is a common compromise) via `dnsConfig` for pods that mostly call external names. With `ndots:2`, a name such as `api.example.com` (two dots) is tried as an absolute name first, while one-dot in-cluster names like `svc.ns` still go through the search path; names with no dot (`svc`) always use it.
- Use **CoreDNS `autopath`** plugin (requires pod mode verified and adds API load) to short-circuit the search path server-side.
- Enable NodeLocal DNSCache (below) so repeated NXDOMAINs are cached locally.
- Avoid musl-libc DNS quirks: Alpine's resolver (older versions) queries all nameservers in parallel and doesn't support the full search semantics reliably (known issues with `ndots` and TCP fallback); another reason to avoid Alpine in ML containers.

Also note: glibc sends A and AAAA queries in parallel from the same socket (source port), which hit the conntrack race (below); `options single-request` / `single-request-reopen` serialize them (the latter reopens the socket), at some latency cost; `use-vc` forces TCP.

## 3. CoreDNS architecture

CoreDNS is a plugin chain. Each server block in the **Corefile** (ConfigMap `kube-system/coredns`) defines zones and plugins executed in a fixed order defined at compile time (not file order):

```text
.:53 {
    errors
    health { lameduck 5s }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
        pods insecure
        fallthrough in-addr.arpa ip6.arpa
        ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
        max_concurrent 1000
        prefer_udp
    }
    cache 30
    loop
    reload
    loadbalance
}
```

| Plugin | Function |
|---|---|
| `errors` | Log errors |
| `health` / `ready` | Liveness (`:8080/health`, `lameduck` drains) and readiness (`:8181/ready`) endpoints |
| `kubernetes` | Answers for the cluster domain from API objects; options `pods disabled\|insecure\|verified`, `ttl`, `endpoint_pod_names`, `fallthrough`, `namespaces`, `labels` |
| `forward` | Send non-cluster queries to upstream resolvers (node's resolv.conf or explicit list); health checks, policy (`random`, `round_robin`, `sequential`), TLS/DoT |
| `cache` | Cache positive and negative responses (`cache 30` seconds; `success`/`denial` capacity and TTL); prefetch |
| `loop` | Detect forwarding loops (CoreDNS crash with "Loop detected" when node resolv.conf points to 127.0.0.53 on systemd-resolved: set kubelet `resolvConf: /run/systemd/resolve/resolv.conf`) |
| `reload` | Auto-reload on Corefile change |
| `loadbalance` | Randomise order of A records |
| `prometheus` | Metrics |
| `rewrite` | Rewrite names/types (migrate domains, alias) |
| `hosts` | Serve entries from a hosts file |
| `template` | Synthesize records by regex |
| `autopath` | Server-side search path completion |
| `log` | Query logging (verbose; use for debugging only) |
| `acl`, `dnssec`, `nsid`, `trace`, `forward` variants | Access control, DNSSEC, tracing |

### Customisation recipes

**Stub domain / split-horizon** (internal corporate zone to an internal resolver):

```text
corp.example.com:53 {
    errors
    cache 30
    forward . 10.1.0.53 10.1.0.54
}
```

**Route object-store or registry names to internal addresses** (`hosts` or `rewrite`):

```text
.:53 {
    ...
    rewrite name huggingface.mirror.local huggingface-proxy.registry.svc.cluster.local
    hosts {
        10.20.0.15 storage.lab.internal
        fallthrough
    }
    ...
}
```

**Upstream with DoT** or a specific resolver: `forward . tls://1.1.1.1 { tls_servername cloudflare-dns.com; health_check 5s }`. **Rate-limit or ACL** abusive clients with `acl` or by NetworkPolicy to DNS.

Edit the Corefile with `kubectl -n kube-system edit cm coredns`; `reload` picks it up within ~30 s (verify with logs); in managed clusters (GKE, EKS) use the provider's `CoreDNS` customisation path (`coredns-custom` ConfigMap `*.override`/`*.server` imports on AKS/EKS add-on; kube-dns on GKE uses `kube-dns` ConfigMap `stubDomains`/`upstreamNameservers`).

## 4. Scaling and hardening

### Capacity

CoreDNS is lightweight but QPS grows with pod count × lookup rate × ndots amplification: a 5,000-pod job starting at once with `getaddrinfo` per connection easily generates 100k+ queries in seconds. Rules of thumb: ~10-20k QPS per CPU-core with caching; CoreDNS pods are stateless, so scale horizontally. Defaults ship with 2 replicas; recommended: replicas ≈ nodes/100 to nodes/20 (min 3 for HA), spread across nodes/zones with anti-affinity and a PDB (`minAvailable: 1` or 50%), requests/limits sized (e.g., 100m CPU / 70 Mi request, memory limit ~170 Mi at modest scale; raise with cache size), `priorityClassName: system-cluster-critical`, `GOMAXPROCS`/cpu limits aligned (avoid CPU throttling which adds latency).

**Autoscaling**: the **cluster-proportional-autoscaler** scales CoreDNS replicas by node/core counts (`linear` or `ladder` params); HPA on CPU can lag for bursts; keep a floor sized for bursts.

### NodeLocal DNSCache

A DaemonSet running a caching CoreDNS (`node-local-dns`) on every node, listening on a link-local address (`169.254.20.10`) and the kube-dns ClusterIP via a dummy interface and NOTRACK iptables rules. Pods query the local cache (no DNAT, no conntrack, no cross-node hop); cache misses are forwarded over **TCP** to the upstream `kube-dns` Service, avoiding the UDP conntrack race and spreading load; negative caching reduces NXDOMAIN storms. Install via the manifest from the Kubernetes repository (set `__PILLAR__LOCAL__DNS__`, `__PILLAR__DNS__SERVER__`, `__PILLAR__DNS__DOMAIN__`), configure the kubelet `clusterDNS` to the link-local IP (or leave and use the dummy-interface binding in iptables mode). Operate it as a critical DaemonSet: per-node failure means that node's pods lose DNS until the cache restarts (it uses `hostNetwork` and a dedicated interface; use proper rollout limits `maxUnavailable: 10%`, readiness, and consider fallback to the cluster DNS Service with search order). For Cilium, local DNS can be handled by its DNS proxy or `localRedirectPolicy`.

### The conntrack/UDP race and 5-second delays

Symptoms: sporadic DNS lookups taking exactly 5 s (default resolver timeout) or intermittent `EAI_AGAIN`. Cause: glibc sends A and AAAA queries from the same UDP socket concurrently; both packets hit netfilter `conntrack` simultaneously, one entry insertion races (DNAT via kube-proxy to the kube-dns ClusterIP creates entries) and the packet is dropped; the resolver times out and retries. Mitigations: NodeLocal DNSCache (no DNAT), `single-request-reopen` option, TCP for DNS, newer kernels (races mostly fixed in 5.0+ with later patches), eBPF kube-proxy replacement (no conntrack for socket LB), reduce simultaneous lookups (connection pooling, caching in apps), and Alpine-specific caveats.

### Other hardening and operations

- Keep CoreDNS and the Corefile in GitOps; test changes in staging; version-skew with Kubernetes releases; watch for the `loop` plugin crash.
- NetworkPolicy allowing DNS egress (UDP/TCP 53 to `kube-dns` and node-local IP) in default-deny namespaces (5.15).
- Limit blast radius from abuse: `ratelimit` via external proxies is limited; use pod quotas and alerts on per-pod QPS (metrics by client IP require query logging).
- Security: DNS exfiltration/tunnelling detection (log anomalies), DNSSEC not typical in-cluster; avoid exposing CoreDNS outside the cluster; restrict zone transfer (not enabled).
- TTLs: `kubernetes ttl 30` for Services (default 5s in some distros) vs. cache; short TTL + cache keeps endpoints fresh; long TTL delays failover for headless discovery.
- IPv6 and dual-stack: AAAA lookups for Services without IPv6 return NODATA but still cost a query; serialise lookups (`single-request`) or set address-family hints in applications where it matters.

## 5. DNS-based discovery for distributed AI workloads

- **StatefulSet + headless Service**: workers address peers as `trainer-0.trainer.ml.svc.cluster.local` (stable even when pods are rescheduled; IP changes, name stays). PyTorch `torchrun --rdzv_backend=c10d --rdzv_endpoint=trainer-0.trainer:29500`, Ray head `ray-head.ray.svc:6379`, MPI hostfiles generated from pod names. Operators (Kubeflow Training Operator, MPI Operator, JobSet, KubeRay) create headless Services and set env vars/hostfiles for you.
- **Readiness and DNS**: headless Services publish only **ready** pods by default; peers needing to discover each other *before* readiness (rendezvous during startup) require `publishNotReadyAddresses: true` on the headless Service (or avoid readiness probes on worker pods). Without it, pods can deadlock waiting for each other's DNS names.
- **Negative caching**: a lookup that returned NXDOMAIN for a peer before its pod existed may be cached for the negative-TTL (default SOA minimum 30 s in CoreDNS `cache denial` settings); workers should retry with backoff and bounded timeouts, and applications should not cache failures (JVM `networkaddress.cache.negative.ttl`, Python `socket.getaddrinfo` doesn't cache but libraries do).
- **Job start storms**: thousands of workers resolving the same few names at once: set generous CoreDNS replicas and NodeLocal caches before launching large jobs; stagger startup; avoid resolving per-iteration.
- **JVM and long-lived clients** cache DNS indefinitely by default with a security manager or for 30 s without; after a service failover, clients keep old IPs; set TTL properties. gRPC resolvers: `dns:///svc.ns:443` re-resolves periodically (30 s minimum with some implementations); for headless service balancing use `round_robin` policy.
- **External dependencies**: object stores, registries, model hubs: use IP-pinned mirrors or internal resolvers for stability; consider local caching proxies; failing external DNS appears as training job hangs at startup; add DNS health to preflight checks (Part 17).
- **Multi-cluster discovery**: Multicluster Services API (`ServiceExport`/`ServiceImport`, `clusterset.local`), Cilium ClusterMesh, Istio multi-cluster DNS proxying, or external DNS (ExternalDNS publishes Service/Ingress records to Route53/CloudDNS/Cloudflare) (5.35).

## 6. Observability

CoreDNS metrics (port 9153): `coredns_dns_requests_total{type,proto,zone}`, `coredns_dns_responses_total{rcode}` (watch NXDOMAIN/SERVFAIL rates), `coredns_dns_request_duration_seconds_bucket`, `coredns_cache_hits_total`/`misses_total`, `coredns_forward_requests_total`, `coredns_forward_healthcheck_failures_total`, `coredns_panics_total`, `coredns_health_request_failures_total`, `coredns_kubernetes_rest_client_requests_total`. Alerts: SERVFAIL ratio > 1%, p99 latency > 100 ms, forward healthcheck failures, CoreDNS restarts, cache hit ratio dropping, CPU throttling. Enable the `log` plugin briefly or `errors`; use `dnstap` or packet capture for forensics. Node-local: `node-local-dns` exposes metrics (port 9253).

```bash
kubectl -n kube-system get deploy,po -l k8s-app=kube-dns -o wide
kubectl -n kube-system logs deploy/coredns --tail=50
kubectl -n kube-system top pod -l k8s-app=kube-dns
kubectl -n kube-system get cm coredns -o yaml
kubectl get svc -n kube-system kube-dns; kubectl get endpointslices -n kube-system -l kubernetes.io/service-name=kube-dns
# test load
kubectl run -it --rm perf --image=registry.k8s.io/perf-tests/dnsperf --restart=Never -- sh   # or dnsperf/queryperf with a query file
```

## 7. Debugging method

1. **Is it DNS?** From a failing pod: `getent hosts svc.ns` and `dig` both; `curl` by IP works while name fails → DNS.
2. **Which resolver?** `cat /etc/resolv.conf` (nameserver IP matches kube-dns or node-local; `ndots`; search list; `dnsPolicy`).
3. **Is CoreDNS healthy?** pods Running/Ready, endpoints present, logs for `loop`, `SERVFAIL`, forward errors; query CoreDNS pod IP directly: `dig @<coredns-pod-ip> kubernetes.default.svc.cluster.local`.
4. **Service vs pod path:** query via the ClusterIP (tests kube-proxy/CNI) vs the pod IP (tests CoreDNS itself) vs node-local cache.
5. **Upstream:** `dig @<upstream> example.com` from the CoreDNS pod/node; check `forward` health, firewall/security group for UDP/TCP 53, node `resolv.conf`.
6. **Records exist?** Service selectors/endpoints (empty headless → no A records), namespace spelling, `fallthrough`, `pods` mode.
7. **Packet capture:** `tcpdump -ni any port 53` on the node or the pod's netns; look for unanswered queries, retransmits at 5 s, truncated UDP (TC bit) falling back to TCP (blocked TCP/53 breaks large responses).
8. **Timing:** `dig +stats`, `time getent hosts`, client-side `strace -T` to see which query is slow; CoreDNS request duration histogram.
9. **Search-path effects:** compare `dig name.` (absolute) vs `dig name` using search; count NXDOMAINs.
10. **Conntrack:** `conntrack -S`, `conntrack -L -p udp --dport 53 | wc -l`, insert_failed counters; kernel version.

| Symptom | Likely cause | Fix |
|---|---|---|
| CoreDNS CrashLoop "Loop detected" | Upstream is itself/127.0.0.53 | Kubelet `resolvConf` to real upstream file; `forward . 10.x.x.x` |
| `SERVFAIL` for external names | Upstream unreachable, firewall, forward misconfigured | Test from CoreDNS pod; fix routes/SG; add secondary upstream |
| `NXDOMAIN` for existing Service | Wrong namespace/search, headless with no ready pods, label mismatch | FQDN, endpoints |
| Random 5 s delays | UDP conntrack race | NodeLocal DNS, `single-request-reopen`, TCP |
| High NXDOMAIN rate and load | ndots:5 + external names | FQDNs with trailing dot, lower ndots, autopath, node-local |
| Names don't resolve for hostNetwork pods | `dnsPolicy: ClusterFirst` ignored for hostNetwork | Use `ClusterFirstWithHostNet` |
| Intermittent failures during CoreDNS rollout | No lameduck/PDB, single replica | `lameduck`, PDB, ≥3 replicas |
| External resolution works, cluster names fail | `kubernetes` plugin API access (RBAC), CoreDNS cache of API, wrong cluster domain | CoreDNS logs, ClusterRole, `clusterDomain` consistency (kubelet vs Corefile) |
| Large responses fail | Blocked TCP/53, EDNS issues | Allow TCP, check MTU |

## 8. Lab (untested)

1. **Record tour**: create Services (ClusterIP, headless, named ports), a StatefulSet with `serviceName`, and an ExternalName; query A/AAAA/SRV/PTR for each; observe how readiness changes headless answers.
2. **resolv.conf and ndots**: inspect `/etc/resolv.conf` under each `dnsPolicy`; with CoreDNS `log` enabled, resolve `api.github.com` and count the queries (ndots 5 vs 2 vs trailing dot); measure latency differences with a loop of 1,000 lookups.
3. **Corefile edits**: add a stub zone to an internal resolver, a `rewrite` and a `hosts` entry; verify with `dig`; break `forward` and observe `SERVFAIL` and metrics; fix.
4. **Loop plugin**: reproduce "Loop detected" by pointing upstream at 127.0.0.53 on a systemd-resolved host; fix via kubelet `resolvConf`.
5. **Scale test**: run `dnsperf`/`k6` DNS load against `kube-dns`; find the QPS at which latency degrades with 2 replicas; add replicas/cluster-proportional-autoscaler and a NodeLocal DNSCache; compare p99 and conntrack counts.
6. **5-second delays**: with glibc client in a loop (parallel A/AAAA) and heavy UDP traffic on a lab node, look for 5 s outliers; apply `single-request-reopen`, then NodeLocal DNSCache; document.
7. **NodeLocal DNSCache**: install, point kubelet `clusterDNS`, verify with `dig @169.254.20.10`, kill the local cache pod and observe client behaviour; check metrics.
8. **Distributed rendezvous**: run a 4-worker PyTorch (or simple TCP) job on a StatefulSet + headless Service; show failure without `publishNotReadyAddresses` when readiness is gated on peers; fix; test pod reschedule (IP changes, name stable).
9. **Negative caching**: query a not-yet-created Service, create it, and measure how long the NXDOMAIN persists; tune CoreDNS `cache` and application retry.
10. **Failure drills**: delete CoreDNS pods during a request loop; scale to 1; add PDB/lameduck; block upstream UDP/53; simulate an expired CoreDNS RBAC; practise the debugging method.
11. **Observability**: scrape CoreDNS and node-local metrics, build a dashboard (QPS, rcode ratios, latency, cache hit), and define alerts.
12. **Clean up**.

Mark tested only after execution.

## 9. Common mistakes

- Treating `Default` dnsPolicy as the default; forgetting `ClusterFirstWithHostNet` for host-network pods.
- Leaving `ndots:5` on heavy external-call workloads and wondering why CoreDNS is saturated.
- Two CoreDNS replicas for a 2,000-node cluster; no PDB or lameduck; CPU-throttled CoreDNS.
- Pointing CoreDNS upstream at systemd-resolved's stub (loop).
- Blocking TCP/53 or EDNS/large packets at firewalls.
- Using DNS names with low TTL assumptions in JVM/gRPC clients that cache indefinitely.
- Gating worker readiness on peer discovery without `publishNotReadyAddresses`.
- Not allowing DNS egress in default-deny NetworkPolicies.
- Custom Corefile changes made by hand in production and lost on upgrade.
- Using Pod DNS A records (`10-0-0-1.ns.pod...`) as identity.

## 10. Interview angles

- "What happens when a pod resolves `my-service`? Walk through resolv.conf, search domains, CoreDNS." 
- "What is `ndots:5`? What problems does it cause and how do you fix them?" 
- "How is a headless Service different in DNS? Why do StatefulSets need it?" 
- "What causes 5-second DNS delays in Kubernetes? How does NodeLocal DNSCache help?" 
- "How would you scale CoreDNS for a 5,000-node cluster?" 
- "Explain the Corefile plugins you'd use for a split-horizon setup." 
- "A distributed training job hangs at startup resolving peers. Why might that be?" 
- "How do you debug a cluster-wide DNS failure?" 

## 11. Checkpoint questions (35)

1. DNS server in Kubernetes? **A:** CoreDNS.
2. Service name format? **A:** `svc.ns.svc.cluster.local`.
3. Headless Service DNS? **A:** Returns pod IPs.
4. StatefulSet pod DNS? **A:** `pod-0.svc.ns.svc.cluster.local`.
5. SRV record purpose? **A:** Port discovery via named ports.
6. Default `dnsPolicy`? **A:** `ClusterFirst`.
7. `dnsPolicy: Default` means? **A:** Inherit node resolver config.
8. `ClusterFirstWithHostNet` for? **A:** Host-network pods using cluster DNS.
9. `ndots:5` effect? **A:** Names with fewer than 5 dots go through search domains first.
10. Fix for search amplification? **A:** Trailing-dot FQDN, lower ndots, autopath, caching.
11. Where is the Corefile? **A:** ConfigMap `coredns` in `kube-system`.
12. Plugin that answers cluster names? **A:** `kubernetes`.
13. Plugin forwarding upstream? **A:** `forward`.
14. What does `loop` detect? **A:** Forwarding loops.
15. Cause of loop crash? **A:** Upstream is 127.0.0.53/itself.
16. Plugin to cache? **A:** `cache`.
17. `lameduck` purpose? **A:** Graceful shutdown/drain.
18. `health` vs `ready`? **A:** Liveness vs readiness endpoints.
19. Metrics port? **A:** 9153.
20. NodeLocal DNSCache address? **A:** 169.254.20.10 (link-local).
21. NodeLocal benefits? **A:** Avoid conntrack/DNAT, cache, TCP upstream.
22. 5 s delay cause? **A:** conntrack race on parallel A/AAAA UDP.
23. Resolver option to serialise A/AAAA? **A:** `single-request` / `single-request-reopen`.
24. `publishNotReadyAddresses` use? **A:** Discover peers before readiness.
25. Stub domain configured how? **A:** Extra server block with `forward`.
26. CoreDNS scaling method? **A:** Replicas, cluster-proportional-autoscaler, node-local cache.
27. CoreDNS HA settings? **A:** ≥3 replicas, anti-affinity, PDB.
28. Why Alpine DNS issues? **A:** musl resolver differences.
29. Negative caching risk? **A:** NXDOMAIN cached before peer exists.
30. JVM DNS caching pitfall? **A:** Indefinite caching of resolved IPs.
31. External DNS for Services? **A:** ExternalDNS controller.
32. Multi-cluster DNS standard? **A:** MCS API `clusterset.local`.
33. How to bypass search? **A:** Use absolute names (trailing dot).
34. How verify CoreDNS directly? **A:** `dig @<coredns-pod-ip>`.
35. Network policy requirement? **A:** Allow DNS egress (UDP/TCP 53).

## 12. Sources and review notes

**Written in original words.** Principal sources:

- Brendan Burns et al., *Kubernetes: Up and Running* (3rd edition; chapter 7 on service discovery).
- James Strong and Vallery Lancey, *Networking and Kubernetes* (chapter 5 on Services and DNS behaviour).
- Kubernetes documentation (DNS for Services and Pods, customizing DNS, NodeLocal DNSCache) and CoreDNS documentation (plugins, kubernetes plugin).
- Examples are the author's constructions.

**Flagged for verification before publishing:** CoreDNS plugin option names and defaults for the version in your distribution, managed-Kubernetes DNS customisation mechanisms, kernel versions where the conntrack race is fixed, `trafficDistribution`/MCS status, metric names, and every command listing; all labs are **untested**.
