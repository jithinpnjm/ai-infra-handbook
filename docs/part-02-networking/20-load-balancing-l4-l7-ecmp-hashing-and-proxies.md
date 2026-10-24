---
id: "c02-20"
title: "2.20 Load balancing: L4, L7, ECMP hashing, proxies and inference traffic"
sidebar_label: "2.20 Load balancing: L4, L7, ECMP hashing, proxies and inference traffic"
sidebar_position: 20
description: "Load balancing from ECMP and IPVS to Envoy, HAProxy and nginx, health checks, gRPC pinning, and LLM-aware routing"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 2.20 Load balancing: L4, L7, ECMP hashing, proxies and inference traffic

| | |
|---|---|
| Level | Intermediate to advanced |
| Priority tier | 0 |
| Lab venue | Linux VM with HAProxy/nginx/Envoy, IPVS, FRR for ECMP VIPs |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Inference endpoints are only as good as the layer that spreads requests across GPUs. A generic round-robin load balancer in front of long-lived gRPC or Server-Sent-Event token streams can leave one GPU at 100% and nine idle; a proxy reload can sever hour-long generations; an HTTP/2 connection pinned to one backend turns a "balanced" cluster into a hot spot; a health check that only tests TCP routes traffic to a server whose GPU has an Xid error. Beyond inference, load balancing is everywhere in the platform: ECMP and anycast VIPs at the fabric edge, Kubernetes Services (kube-proxy/IPVS/eBPF), ingress and gateways, cloud load balancers, DNS-based steering, and service meshes. This chapter builds the general theory (what a load balancer is, layers, algorithms, state, failure handling), the practical tools (IPVS, HAProxy, nginx, Envoy, cloud LBs), and the AI-specific problems (streaming, pinning, load-aware and cache-aware routing).

## Prerequisites and outcomes

You should know TCP/TLS/HTTP (2.6, 2.10), ECMP hashing (2.12), BGP (2.15, 2.16), NAT (2.9) and conntrack basics.

After this chapter you can:

- Classify load balancers by layer (DNS, L3/ECMP, L4, L7), topology (NAT/proxy, DSR, tunnel) and deployment (appliance, software, cloud-managed, in-cluster).
- Explain the algorithms: round robin, weighted, least connections, least response time, hash and consistent hashing (ring, rendezvous, Maglev), power-of-two-choices, EWMA, and when each fits.
- Explain ECMP and anycast as load balancing for VIPs, resilient hashing, and how L4 LBs scale out behind ECMP with connection consistency.
- Configure HAProxy, nginx and Envoy for HTTP, TLS termination/passthrough, gRPC, health checks, retries, timeouts, draining; set up IPVS.
- Diagnose problems: uneven load, connection pinning, hot backends, slow health detection, reload-induced stream loss, SNAT port exhaustion, sticky sessions, idle-timeout resets, client IP loss.
- Design inference load balancing: streaming, long-lived connections, queue/token-aware routing, prefix-cache-aware routing, autoscaling and drain, multi-tenant fairness.
- Choose between cloud load balancer types and Kubernetes patterns (Service, Ingress, Gateway API, mesh) at a high level (details in Part 5).

## 1. What a load balancer does

A **load balancer (LB)** presents one stable address (a **virtual IP**, VIP, or a name) and distributes incoming work across a pool of **backends** (real servers), providing: **scale** (more capacity than one server), **availability** (health checks remove failed backends), **maintainability** (drain one backend, upgrade it, return it), and often **security and policy** (TLS termination, rate limiting, WAF, authentication). Every LB must answer five design questions:

1. **Where is the decision made?** (client-side, DNS, the network (ECMP), a dedicated L4 device, an L7 proxy, the server.)
2. **What identifies a unit of work?** (packet, flow/connection, HTTP request, gRPC stream, token-generation job.)
3. **How is a backend chosen?** (algorithm and state.)
4. **How does the reply return?** (through the LB (proxy/NAT) or directly (DSR).)
5. **How are failures detected and handled?** (health checks, outlier detection, retries, draining.)

### Layers and families

| Family | Decision on | Examples | Notes |
|---|---|---|---|
| **DNS / GSLB** | Name resolution (round-robin records, weighted/geo/latency/health-checked answers) | Route 53, Cloud DNS routing policies, NS1 | Coarse; TTL and client caching limit agility; no connection awareness |
| **L3 ECMP / anycast** | Packet/flow hash across equal-cost next hops | Router ECMP, BGP-announced VIPs from many servers | Stateless, line rate; no health awareness beyond routing; flow remap on change |
| **L4 (transport)** | TCP/UDP connections (5-tuple) | IPVS/LVS, Maglev, AWS NLB, GCP Network LB, Katran (XDP), HAProxy `mode tcp`, nginx `stream` | Fast, protocol-agnostic; cannot see requests inside a connection |
| **L7 (application)** | HTTP/gRPC requests, headers, paths, cookies | HAProxy `mode http`, nginx, Envoy, Traefik, AWS ALB, GCP HTTP(S) LB, Istio gateway | Rich routing, retries, TLS, observability; more CPU, protocol-specific |
| **Client-side** | The client library | gRPC `round_robin`/`pick_first` with xDS, Finagle, Ribbon | No LB hop; needs service discovery and smart clients |
| **In-cluster / mesh** | Per-pod sidecars or node proxies | kube-proxy, Cilium eBPF, Envoy sidecar, Linkerd | Service-to-service balancing |

### Packet paths

```mermaid
flowchart LR
  subgraph PROXY["Proxy / NAT mode (reply returns via LB)"]
    C1[Client] --> L1["LB (VIP)\nterminates or DNATs"] --> B1[Backend]
    B1 --> L1 --> C1
  end
  subgraph DSR["Direct Server Return (reply bypasses LB)"]
    C2[Client] --> L2["LB (VIP)\nrewrites L2 dst / tunnels"] --> B2["Backend\n(VIP on loopback)"]
    B2 -. "reply with src=VIP" .-> C2
  end
```

- **Proxy mode (L4 or L7)**: the LB terminates the client connection and opens a separate one to the backend (a full proxy), so it can modify, buffer, retry and inspect; the backend sees the LB's address (so preserve the client IP via `X-Forwarded-For`, `Forwarded` header, or PROXY protocol). Stateful, costs CPU and memory, bounded by the LB's capacity.
- **NAT mode**: the LB rewrites the destination IP (DNAT) to the backend and the source if needed (SNAT/masquerade); the replies must come back through the LB (backend's default gateway is the LB, or SNAT is used, hiding the client IP).
- **DSR (Direct Server Return, "DR" in IPVS)**: the LB forwards the packet to the backend by rewriting only the destination MAC (same L2 segment) or by tunnelling (IPIP/GRE/GUE); the backend holds the VIP on a non-ARPing interface (`lo` with `arp_ignore=1`, `arp_announce=2`, chapter 2.3) and replies **directly** to the client with source = VIP. Replies (usually much larger than requests) skip the LB, giving huge throughput; the backend sees the real client IP. Limitations: L2 adjacency (or tunnels), no L7 features, health checking must be careful, and asymmetric flows complicate firewalls.
- **Tunnel/encapsulation (e.g. Maglev, Katran)**: L4 LB encapsulates the original packet toward the backend (GRE/IPIP/GUE), and the backend decapsulates and replies directly (DSR).

## 2. Algorithms

| Algorithm | How it chooses | Good for | Pitfall |
|---|---|---|---|
| **Round robin** (RR) / weighted RR | Rotate through backends (weights for unequal capacity) | Homogeneous, short, stateless requests | Ignores request cost and backend load |
| **Least connections** / weighted | Backend with fewest active connections | Variable-length requests, long-lived connections | Counts connections, not work; needs shared state across LB instances |
| **Least outstanding requests / least request** | Fewest in-flight requests | HTTP/gRPC | Same as above but request-granular |
| **Least response time / EWMA / peak-EWMA** | Lowest recent latency × in-flight | Heterogeneous backends | Needs measurement; can oscillate (herding) |
| **Power of two random choices (P2C)** | Pick two random backends, send to the less loaded | Large pools with imperfect load info; scalable | Needs load info per backend |
| **Source/URL/header hash** | `hash(key) mod N` | Session affinity, cache locality | Remaps most keys when N changes |
| **Consistent hashing (ring, rendezvous/HRW, jump hash)** | Map keys and backends onto a ring/score space; adding/removing one backend moves only ~1/N of keys | Caches, sticky sessions, sharded stores, stateful backends | Load imbalance (virtual nodes help); hot keys |
| **Maglev hashing** | Lookup table built from backend preference permutations; near-uniform load with minimal disruption | L4 LBs behind ECMP (Google Maglev) | Table rebuild cost; small disruption on change |
| **Random** | Uniform random | Simple | Variance |
| **Locality-aware / zone-aware** | Prefer same zone/rack | Cost, latency | Capacity imbalance across zones |
| **Priority/failover groups** | Use group 2 only if group 1 unhealthy | DR, spillover | Cold backups |
| **Load-aware custom (GPU/queue/KV-cache)** | Use backend-reported metrics | LLM inference | Needs telemetry, careful staleness handling |

Principles: (1) **choose the metric that represents work** (connections ≠ requests ≠ tokens ≠ GPU-seconds); (2) with multiple LB instances, local least-connections **herds**; P2C or randomised choice reduces synchronised stampedes; (3) **hash-based affinity** is for cache locality and state, but accept uneven load and plan for reshuffling (use consistent/resilient hashing); (4) **slow start** (ramp weight up for newly added or recovered backends) avoids flooding a cold server (JIT, caches, GPU warm-up).

## 3. Health checks, failure handling and draining

- **Active checks**: the LB probes backends periodically (TCP connect, HTTP `GET /healthz` expecting 200, gRPC health protocol `grpc.health.v1`, custom script). Parameters: interval, timeout, rise (successes to mark up), fall (failures to mark down). Detection time ≈ interval × fall; too aggressive causes flapping under load; too lax keeps sending traffic to dead nodes.
- **Passive checks / outlier detection**: observe real traffic: eject a backend after N consecutive 5xx or connection failures for a period (Envoy outlier detection, HAProxy `observe layer7`, nginx `max_fails`); catches failures the probe misses and brownouts.
- **What to check**: liveness (process up) versus **readiness** (can serve now: model loaded, GPU healthy, queue not full). For inference, `ready` should reflect model load state; extended checks might consult GPU health (DCGM, Xid errors) so that a failing GPU is removed (requires integration).
- **Retries**: only for idempotent requests or failures before any bytes were sent; use retry budgets and per-try timeouts to avoid retry storms (amplification during outages); hedged requests carefully.
- **Timeouts**: connect, request/stream idle, total; LLM streams need generous read timeouts and heartbeats; mismatch between client, LB, and server idle timeouts causes mysterious resets (chapter 2.10).
- **Circuit breaking / overload protection**: cap concurrent connections/requests/pending queue per backend; shed load with 503 + `Retry-After` instead of queueing indefinitely.
- **Connection draining**: when removing a backend (deploy, scale-in), stop new requests but let existing ones finish up to a deadline. Essential for long streams; coordinate with the orchestrator (Kubernetes `terminationGracePeriodSeconds`, `preStop` hook, readiness going false before shutdown).
- **Graceful reload**: proxies like nginx/HAProxy keep old workers until old connections end; for long streams that means workers can live for hours; use dynamic config APIs (Envoy xDS, HAProxy runtime API, nginx Plus/resolver variables) to avoid reloads on endpoint changes.

## 4. ECMP, anycast and scaling out the L4 tier

A single LB node is a throughput limit and a single point of failure. The standard scale-out is to put the L4 tier **behind ECMP**:

1. Each L4 LB node announces the **VIP** to the upstream router (or leaf) via BGP (FRR/BIRD/ExaBGP); the router sees N equal-cost next hops and spreads flows across them by 5-tuple hash.
2. A node fails or is drained: its BGP session drops (BFD makes this sub-second) and the router removes it from the ECMP set; flows that hashed to it get remapped. With plain modulo hashing **all** flows may be rehashed (existing connections break); with **resilient/consistent hashing** in the router, only the flows of the failed node move.
3. Surviving nodes receive flows they have no state for. To avoid breaking established connections, L4 LBs use **consistent hashing keyed on the 5-tuple** (Maglev-style) so any node computes the *same* backend for the same flow without synchronised state; or they share/replicate connection state. Google Maglev and Meta Katran work this way.
4. The L4 node forwards to the backend by DSR/encapsulation or proxying.

This is "anycast within a data centre": the same VIP from many nodes. The same mechanism serves DNS anycast and global anycast across data centres (nearest healthy site wins by BGP path). Caveats: BGP convergence time determines failover; flows can shift to a different site on a route change (long-lived TCP breaks); asymmetric routing and `rp_filter` (chapter 2.5); path MTU and ICMP (chapter 2.7); the hash must be stable across the tier; health coupling between the LB's backend health and the VIP announcement (withdraw the VIP if the node cannot serve).

Also from AI-fabric context (chapter 2.12): ECMP hashing at fabric tiers is itself a form of load balancing for *flows*, with the same caveats: few elephant flows → imbalance; RoCE varies UDP source ports per QP for entropy; inner-header hashing for tunnels; adaptive routing to react to load.

## 5. L4 tools: IPVS and friends

**Linux IPVS (LVS)** is a kernel L4 load balancer (netfilter-based, used by kube-proxy IPVS mode and keepalived):

```bash
sudo modprobe ip_vs ip_vs_rr ip_vs_wlc ip_vs_sh
sudo ipvsadm -A -t 10.0.0.100:443 -s wlc                       # virtual service, weighted least-connection
sudo ipvsadm -a -t 10.0.0.100:443 -r 10.1.0.11:443 -g -w 1     # -g direct routing (DSR), -m masquerade (NAT), -i tunnel
sudo ipvsadm -a -t 10.0.0.100:443 -r 10.1.0.12:443 -g -w 1
sudo ipvsadm -Ln --stats --rate ; sudo ipvsadm -Lcn             # services, per-connection table
# DR mode backend prerequisites (on each real server):
sudo ip addr add 10.0.0.100/32 dev lo
sudo sysctl -w net.ipv4.conf.all.arp_ignore=1 net.ipv4.conf.all.arp_announce=2
```

Schedulers: `rr`, `wrr`, `lc`, `wlc`, `sh` (source hash), `dh`, `mh` (Maglev hashing), `sed`, `nq`. **keepalived** adds VRRP (active/passive VIP failover) and health checks that add/remove IPVS real servers. Other L4 options: HAProxy/nginx in TCP mode, eBPF/XDP balancers (Katran, Cilium's kube-proxy replacement), cloud network LBs. NAT-mode IPVS depends on conntrack (state, `nf_conntrack_max`), DR mode does not.

## 6. L7 tools: HAProxy, nginx, Envoy

### HAProxy (HTTP and TCP)

```text
global
  maxconn 100000
  nbthread 8
defaults
  mode http
  timeout connect 3s
  timeout client  300s        # long for streaming
  timeout server  300s
  timeout tunnel  1h          # websocket/gRPC streams
  option httplog
frontend fe_https
  bind :443 ssl crt /etc/haproxy/certs/ alpn h2,http/1.1
  http-request set-header X-Forwarded-Proto https
  acl is_grpc hdr(content-type) -i application/grpc
  use_backend be_infer if is_grpc
  default_backend be_web
backend be_infer
  balance leastconn
  option httpchk
  http-check send meth GET uri /v2/health/ready
  default-server check inter 2s fall 3 rise 2 slowstart 30s maxconn 64
  server triton1 10.1.0.11:8001 proto h2
  server triton2 10.1.0.12:8001 proto h2
backend be_web
  balance roundrobin
  cookie SRV insert indirect nocache
  server web1 10.1.1.11:8080 check cookie w1
frontend fe_pg
  mode tcp
  bind :5432
  default_backend be_pg
backend be_pg
  mode tcp
  balance leastconn
  server pg1 10.1.2.11:5432 check
# runtime API: echo "set server be_infer/triton1 state drain" | socat stdio /var/run/haproxy.sock
```

### nginx

```nginx
upstream triton_grpc { least_conn; keepalive 32; server 10.1.0.11:8001; server 10.1.0.12:8001; }
server {
  listen 443 ssl http2;
  ssl_certificate     /etc/nginx/certs/api.pem; ssl_certificate_key /etc/nginx/certs/api.key;
  location / {
    grpc_pass grpc://triton_grpc;
    grpc_read_timeout 300s; grpc_send_timeout 300s;
    grpc_buffer_size 4k;                 # small buffers: tokens are small, buffering adds latency
  }
  location /v1/ {                         # SSE token streaming over HTTP/1.1
    proxy_pass http://vllm_pool; proxy_http_version 1.1; proxy_set_header Connection "";
    proxy_buffering off; proxy_cache off; proxy_read_timeout 600s;
  }
}
stream { upstream pg { server 10.1.2.11:5432; } server { listen 5432; proxy_pass pg; } }   # L4
```

Notes: open-source nginx resolves upstream hostnames at config load, so new endpoints need a reload (or `resolver` + variables, or nginx Plus dynamic upstreams); reload starts new workers while old ones live until their connections end; `worker_shutdown_timeout` can cap them but cuts streams.

### Envoy

Envoy is a modern L4/L7 proxy built around dynamic configuration (**xDS** APIs: listeners, routes, clusters, endpoints, secrets), first-class HTTP/2 and gRPC, rich observability (stats, access logs, tracing), and advanced load balancing and resilience.

```yaml
static_resources:
  listeners:
  - name: ingress
    address: { socket_address: { address: 0.0.0.0, port_value: 8443 } }
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress
          stream_idle_timeout: 600s
          route_config:
            virtual_hosts:
            - name: infer
              domains: ["*"]
              routes:
              - match: { prefix: "/" }
                route: { cluster: triton, timeout: 0s, retry_policy: { retry_on: "connect-failure,refused-stream", num_retries: 2 } }
          http_filters: [{ name: envoy.filters.http.router, typed_config: { "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router } }]
  clusters:
  - name: triton
    type: STRICT_DNS
    lb_policy: LEAST_REQUEST            # P2C over least-request; also ROUND_ROBIN, RING_HASH, MAGLEV, RANDOM
    typed_extension_protocol_options:
      envoy.extensions.upstreams.http.v3.HttpProtocolOptions:
        "@type": type.googleapis.com/envoy.extensions.upstreams.http.v3.HttpProtocolOptions
        explicit_http_config: { http2_protocol_options: {} }
    health_checks: [{ timeout: 1s, interval: 2s, unhealthy_threshold: 3, healthy_threshold: 2, grpc_health_check: {} }]
    outlier_detection: { consecutive_5xx: 5, interval: 5s, base_ejection_time: 30s }
    circuit_breakers: { thresholds: [{ max_connections: 1024, max_pending_requests: 256, max_requests: 4096 }] }
    load_assignment: { cluster_name: triton, endpoints: [{ lb_endpoints: [ { endpoint: { address: { socket_address: { address: triton-svc, port_value: 8001 } } } } ] }] }
```

Features worth knowing: least-request with P2C, ring-hash and Maglev for affinity, **slow start** windows, **outlier detection**, **locality-weighted** load balancing, panic thresholds (when too many hosts are unhealthy, spread to all rather than overloading the few), retry budgets, hedging, rate limiting, **connection draining on listener updates**, the admin interface (`/clusters`, `/stats`), and use as the data plane for Istio, Contour, Envoy Gateway, Gloo, Ambassador and many cloud edges.

## 7. TLS, client identity and L4/L7 interplay

- **TLS termination at the LB** (decrypt, inspect/route at L7, re-encrypt or plaintext to backends) enables routing on headers and WAF; **passthrough** (L4 on SNI) keeps end-to-end encryption and mTLS but loses L7 features; **re-encryption** keeps encryption inside the data centre. Certificate management is covered in chapter 2.10.
- **Preserving client IP**: L7: `X-Forwarded-For`/`Forwarded` (trust only from known proxies to avoid spoofing); L4: **PROXY protocol** (v1/v2) header prefixed by the LB so the backend can learn the original client address and TLS info; DSR and `externalTrafficPolicy: Local` in Kubernetes avoid SNAT; cloud LBs differ on whether they preserve source IP.
- **HTTP/2 and gRPC multiplexing**: many requests share one connection. **At L4, balancing is per connection**: all streams of a client connection go to one backend (connection pinning). Fix with L7 proxies that balance per request/stream (nginx `grpc_pass`, Envoy, HAProxy with `proto h2`, ALB for gRPC), client-side balancing (`round_robin` across resolved addresses, xDS), or by capping connection age (`MAX_CONNECTION_AGE`) so clients periodically reconnect and rebalance.
- **WebSockets/SSE**: long-lived; configure idle timeouts and heartbeats, disable response buffering.
- **HTTP/3/QUIC**: UDP-based; L4 LBs must hash on QUIC connection IDs (not 5-tuple) to survive client IP/port changes; check support.
- **Rate limiting and fairness**: per-client/token-bucket limits at the gateway, concurrency limits per tenant, priority queues, and 429 with `Retry-After`.

## 8. Cloud and Kubernetes load balancing (overview)

- **Cloud**: GCP offers external/internal **Application LBs** (L7 HTTP(S), global or regional, built on Envoy/GFE), **Network LBs** (L4 pass-through or proxy), and **internal TCP/UDP** LBs; AWS has ALB (L7), NLB (L4), GLB (L3 gateway for appliances), CLB (legacy); Azure has Application Gateway, Load Balancer, Front Door. Differences to check: source IP preservation, idle timeouts (often 60 s for HTTP LBs; 350 s for some L4), supported protocols (gRPC, WebSockets, HTTP/2 end to end), connection draining settings, health check semantics, quotas, cross-zone behaviour, and cost per GB. Chapter 2.32 covers GCP specifics.
- **Kubernetes** (details in Part 5): a **Service** (ClusterIP/NodePort/LoadBalancer/Headless) gives a stable virtual IP; **kube-proxy** implements it with iptables rules (random probability chain), IPVS (real L4 scheduler) or eBPF replacement (Cilium); **EndpointSlices** list ready pods; readiness probes control membership; **Ingress** and **Gateway API** provide L7 HTTP routing and TLS via controllers (nginx, HAProxy, Envoy-based Contour/Emissary/Envoy Gateway, Traefik, cloud controllers); **service meshes** add per-pod proxies for mTLS, retries and L7 balancing between services; **MetalLB/kube-vip/Cilium** provide LoadBalancer VIPs on bare metal via ARP or BGP (ECMP). Remember: kube-proxy's iptables mode balances **connections** randomly, not load-aware, and long-lived gRPC connections need L7 or client-side balancing.

## 9. Load balancing for AI inference

LLM serving breaks several assumptions of web load balancing:

1. **Requests are long, variable and stateful-ish.** A request may stream tokens for minutes; cost varies with prompt and output length by orders of magnitude; a backend's real load is its **queue depth, number of running sequences, and KV-cache occupancy**, not its connection count.
2. **Connections are long-lived.** HTTP/2/gRPC streams and SSE hold resources; reloads, scale-in and deploys must drain gracefully; idle timeouts at any hop can cut a slow generation.
3. **Cache locality matters.** Prefix caching (system prompts, RAG context, multi-turn chat) makes a request cheaper on the replica that already holds the prefix KV blocks; routing the same session/prefix to the same replica raises hit rates, but pure affinity can create hot spots.
4. **Backends are expensive and heterogeneous.** GPU types, tensor-parallel group sizes, disaggregated prefill/decode pools, LoRA adapters loaded per replica, and quantised variants.
5. **Autoscaling is slow.** GPU nodes and model loads take minutes, so the router must absorb bursts (queueing/shedding) rather than rely on instant scale-out.

Practices:

- **Balance per request, not per connection**: use L7 (Envoy, HAProxy, nginx `grpc_pass`, Gateway API inference extensions) or client-side balancing; avoid pure L4 for multiplexed gRPC (symptom: servers 1 and 2 overloaded while 3 to 10 idle; mitigations: periodic reconnect via max connection age, then true L7 balancing).
- **Choose a load signal**: least-outstanding-requests as a baseline; better, backend-reported metrics (running + waiting requests, KV-cache usage, estimated tokens) exposed via Prometheus or response headers/ORCA-style load reports; use **P2C over load** to avoid herding; consider token-count-aware estimates (prompt length known at admission, output length predicted).
- **Cache- and session-aware routing**: consistent hashing on a session ID or prompt-prefix hash with **bounded loads** (spill to the next replica when one exceeds its share), or a router that tracks which replica holds which prefix blocks (the approach of LLM-specific routers and "gateway API inference extension" endpoint pickers).
- **Disaggregated serving**: route prefill and decode to separate pools, handle KV transfer between them, and keep the two pools' autoscaling and admission coupled (Part on inference).
- **Health and readiness**: health checks hit the serving framework's readiness endpoint (e.g. Triton `/v2/health/ready`, vLLM `/health`), and optionally integrate GPU health (DCGM Xid/ECC); mark not-ready during model load; use `slowstart` for cold replicas.
- **Streaming hygiene**: disable proxy buffering for SSE; set read/stream-idle timeouts above the maximum generation time; send heartbeats; avoid `Connection: close`; use HTTP/2 end to end where possible; measure time-to-first-token (TTFT) and inter-token latency at the proxy (access logs with `$upstream_response_time`, Envoy stats).
- **Drain on deploy/scale-in**: readiness false → stop new → wait for in-flight streams up to the grace period → terminate; align `terminationGracePeriodSeconds`, `preStop`, LB deregistration delay, and proxy shutdown timeouts; reloads should be hot (xDS/runtime API) so old workers don't linger for hours.
- **Overload control and fairness**: per-tenant concurrency and token-rate limits; priority queues (interactive vs batch); return 429/503 early rather than building unbounded queues; admission control that considers KV-cache headroom.
- **Observability**: per-backend request counts, in-flight, queue time, error and retry rates, TTFT/ITL percentiles, ejection events, hot-backend alerts; trace requests across gateway → router → engine.

Whiteboard framing for interviews: client → anycast/ECMP to a fleet of L4/L7 gateways (BGP VIP, BFD) → TLS termination and L7 routing (per-request, per-tenant policy) → load/cache-aware endpoint picker → inference pods (readiness, drain) with GPU health integration; show where pinning happens at L4 and how L7/client-side fixes it. In enterprise environments you may meet appliance or software ADCs (for example VMware Avi, F5, Citrix) that scale out service engines behind BGP/ECMP VIPs, understand HTTP/2 and gRPC at L7, and support custom health monitors; the architectural ideas are the same, and any specific product capability claim must be validated against current vendor documentation and a load test.

## 10. Troubleshooting

| Symptom | Likely cause | Check/fix |
|---|---|---|
| One backend hot, others idle | L4 pinning of multiplexed connections; hash-based affinity; slow start missing; stale weights | Switch to L7/per-request; `max_connection_age`; `ss -tn` per backend; LB stats |
| Intermittent 502/504 | Backend timeouts shorter than LB; backend resets idle connection; keepalive mismatch | Align idle/keepalive timers; `upstream_response_time`; retry only idempotent |
| Streams cut during deploy | Reload/scale-in without drain; shutdown timeout | Hot reload; drain; larger grace; `terminationGracePeriodSeconds` |
| Client IP missing in logs | SNAT/proxy | `X-Forwarded-For`, PROXY protocol, DSR, `externalTrafficPolicy: Local` |
| Connection resets after N seconds idle | LB/NAT idle timeout | Keepalives below the timeout; raise timeout |
| New backend gets no traffic | Health check failing, wrong port/path, readiness false, not registered | Health status; `curl` from the LB host; service discovery |
| Existing connections break after LB change | ECMP rehash without consistent hashing; state not shared | Resilient hashing; Maglev-style hashing; connection draining |
| Source port exhaustion at LB | Many connections to few backends from one IP | More SNAT IPs, connection reuse/keepalive, DSR |
| High p99 only on some requests | Head-of-line blocking at HTTP/1.1 backend; slow backend not ejected; retry storms | Outlier detection; per-try timeouts; least-request |
| Health flapping | Aggressive interval; overloaded backend failing probes | Tune rise/fall; separate health endpoint; lighter check |

Tools: `ss -s`, `ss -tni`, `conntrack -L`, `ipvsadm -Ln --stats`, HAProxy `show stat`/`show servers state`, Envoy `/clusters` and `/stats`, nginx `stub_status`/`$upstream_*` log variables, `curl -w` timing, `tcpdump` on LB and backend, `wrk`/`hey`/`ghz` (gRPC load generator)/`vegeta` for load tests, and application metrics.

## 11. Lab: build and break load balancers (untested)

1. **L4 IPVS DR**: three namespaces (lb, rs1, rs2) on a bridge; configure the VIP on `lo` of the real servers with `arp_ignore/arp_announce`; IPVS in DR mode; verify distribution with `ipvsadm -Lcn`; capture to show replies bypass the LB; switch to NAT mode and observe conntrack and the return path.
2. **Algorithms**: run `hey`/`wrk` against RR, least-connection, source-hash, Maglev (`mh`); add a slow backend (`tc netem delay`) and compare distributions and tail latency; change a weight.
3. **HAProxy L7**: two HTTP backends; configure active health checks (`check inter 1s fall 2 rise 2`); stop one backend and measure detection time; add `slowstart`; use the runtime API to drain.
4. **gRPC pinning**: a simple gRPC server that returns its hostname (or Triton/`grpcbin`); front with (a) nginx `stream` (L4) and (b) nginx `grpc_pass`/Envoy; one client with one channel sending many calls via `ghz`; show all go to one backend in L4 and spread in L7; apply `MAX_CONNECTION_AGE` and observe periodic rebalancing.
5. **Reload vs streams**: start a long SSE/gRPC stream through nginx; `nginx -s reload`; see old worker lingering (`ps`), set `worker_shutdown_timeout` and watch the stream get cut; compare Envoy dynamic update (file-based xDS) with no cut.
6. **Consistent hashing**: Envoy `RING_HASH`/`MAGLEV` or HAProxy `balance hdr()`+`hash-type consistent`; map session IDs; remove a backend and count how many sessions remapped versus plain modulo hash.
7. **ECMP VIP**: two LB namespaces announcing the same VIP to a router namespace via FRR/BGP; verify ECMP; fail one LB; measure convergence with and without BFD; observe which flows break (consistent hashing vs not); test resilient hashing if supported.
8. **Inference-aware routing (simulation)**: write a tiny Python backend with variable service time and an exposed `queue_depth` metric; implement round-robin vs least-outstanding vs P2C-on-queue-depth in a minimal proxy (`asyncio`) and compare p99 latency under a heavy-tailed job-size distribution; add prefix-hash affinity with bounded load and measure cache-hit proxy metric.
9. **Overload and retries**: add a retry policy without budget and trigger a retry storm by killing a backend; add circuit breaking and a retry budget and compare.
10. **Clean up.**

Mark tested only after execution.

## 12. Common mistakes

- L4 balancing multiplexed HTTP/2 or gRPC and expecting even load.
- Using connection count as the load signal for long, heterogeneous requests; synchronised least-connection herding across many LB instances.
- Health checks that test only TCP, or that are too aggressive; no slow start; no outlier detection.
- Retries without budgets; non-idempotent retries; timeouts shorter than the longest legitimate generation.
- Reloading proxies to update endpoints in long-stream workloads; no drain in deploys.
- Trusting `X-Forwarded-For` from the Internet; losing client IP behind SNAT.
- Plain modulo hashing behind ECMP/anycast (mass remapping); VIP announced while the node cannot serve.
- Treating the LB as infinitely scalable: no capacity limits, no overload shedding.

## 13. Interview angles

- "L4 versus L7 load balancing: when and why? What's DSR?"
- "Walk me through scaling a load balancer horizontally behind ECMP/anycast. What breaks on a change?"
- "Consistent hashing: how does it work and why use it? What's Maglev?"
- "Why does round-robin L4 in front of gRPC give uneven load? How do you fix it?"
- "Design load balancing for an LLM inference service with streaming responses."
- "How do health checks, outlier detection and circuit breaking differ?"
- "How do you do a zero-downtime deploy for long-lived streaming connections?"
- "How do you preserve the client IP through a load balancer?"
- "What does kube-proxy do and what are its limits for load balancing?"

## 14. Checkpoint questions (40)

1. What five questions does every LB design answer? **A:** Where decided, unit of work, algorithm, reply path, failure handling.
2. L4 vs L7? **A:** Transport connections vs application requests.
3. What is DSR? **A:** Replies go straight from backend to client with VIP as source.
4. What must a DSR backend do with the VIP? **A:** Hold it on loopback without ARPing (`arp_ignore`/`arp_announce`).
5. What is the PROXY protocol for? **A:** Carrying original client address through an L4 proxy.
6. Round robin weakness? **A:** Ignores request cost/load.
7. Least connections weakness? **A:** Counts connections, not work; herding across LB instances.
8. What is P2C? **A:** Pick two random backends, choose the less loaded.
9. Why consistent hashing? **A:** Only ~1/N keys move when the pool changes.
10. What is Maglev hashing? **A:** Lookup-table-based consistent hashing with even load and minimal disruption.
11. How are L4 LBs scaled out? **A:** Behind ECMP with the VIP announced via BGP.
12. What breaks on ECMP membership change with modulo hashing? **A:** Most flows are remapped.
13. What does resilient hashing do? **A:** Moves only flows of the affected next hop.
14. Active vs passive health checks? **A:** Probes vs observing live traffic failures.
15. Liveness vs readiness? **A:** Process alive vs able to serve now.
16. What are rise/fall? **A:** Successes/failures needed to mark up/down.
17. What is slow start? **A:** Gradually ramp traffic to a new/recovered backend.
18. What is outlier detection? **A:** Ejecting backends that return errors in live traffic.
19. What is a retry budget? **A:** Cap on retry volume to prevent storms.
20. Why drain connections? **A:** Let in-flight requests finish before removal.
21. What causes gRPC connection pinning? **A:** L4 balancing of multiplexed HTTP/2 connections.
22. Two fixes for pinning? **A:** L7/per-request balancing; client-side balancing/max connection age.
23. Why can nginx reloads hurt streams? **A:** Old workers persist or are cut at shutdown timeout.
24. What's xDS? **A:** Envoy's dynamic configuration APIs.
25. Envoy panic threshold? **A:** When too many hosts are unhealthy, spread load across all.
26. How does IPVS do NAT vs DR? **A:** NAT rewrites addresses and uses conntrack; DR rewrites the L2 destination.
27. Which IPVS scheduler is hashing-based Maglev? **A:** `mh`.
28. What does kube-proxy iptables mode balance? **A:** Connections, randomly.
29. What is the L7 solution for ingress in Kubernetes? **A:** Ingress/Gateway API with a controller (nginx, Envoy, HAProxy...).
30. Why is connection count a poor signal for LLMs? **A:** Request costs vary hugely; queues/KV cache are the real load.
31. What signal helps LLM routing? **A:** Running/waiting requests, KV-cache occupancy, estimated tokens.
32. Why prefix-aware routing? **A:** Reuse cached KV blocks to cut prefill cost.
33. Risk of pure affinity routing? **A:** Hot spots.
34. Disable what for SSE through a proxy? **A:** Response buffering.
35. What TTL-like timer must exceed generation time? **A:** Proxy read/stream idle timeout.
36. How do you route QUIC consistently? **A:** Hash on connection ID.
37. What does BFD give VIP failover? **A:** Sub-second detection of LB node failure.
38. Why use slowstart with GPU backends? **A:** Cold caches/models/JIT.
39. Name a gRPC load generator. **A:** `ghz`.
40. Which health endpoint does Triton expose? **A:** `/v2/health/ready` (and live).

## 15. Sources and review notes

**Written in original words.** Principal sources:

- The author's own `nvidia-devops` repository, volume 09 (inference/MLOps gauntlet): the inference load-balancing conundrum (gRPC/HTTP-2 connection pinning, NGINX baseline configuration and reload behaviour, enterprise ADC scale-out behind BGP/ECMP, GPU-aware health monitors, the L4 pinning production scenario and its fixes), volume 12 (end-to-end inference request path and proxy buffering of token streams), and volume 01 (ECMP hashing and RoCE entropy).
- Brian Ward, *How Linux Works*, 3rd ed., and *Production Kubernetes* chapter 6 (service routing: Services, kube-proxy modes, ingress, service meshes) for the Kubernetes overview; the full Kubernetes treatment is in Part 5 chapters.
- Algorithms, HAProxy/nginx/Envoy/IPVS configuration, anycast scale-out and LLM-routing guidance are the author's synthesis from the product manuals, the Maglev and consistent-hashing literature, and RFCs for the PROXY protocol and HTTP/2.

**Flagged for verification before publishing:** all configuration snippets (HAProxy, nginx, Envoy) against the target versions; cloud LB idle timeouts and feature sets; Avi or other ADC feature claims; LLM-aware routing project names and capabilities; all labs are **untested**.
