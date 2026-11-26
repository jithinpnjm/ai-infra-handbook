import re

labels = [
    "The whiteboard path for an inference service, and the metrics to watch on it",
    "Client",
    "anycast or ECMP to a fleet of L4 and L7 gateways (BGP VIP, BFD)",
    "TLS termination and L7 routing with per-request, per-tenant policy",
    "load- and cache-aware endpoint picker",
    "inference pods with readiness, drain and GPU health integration",
    "where pinning happens at L4",
    "L7 or client-side balancing fixes it",
    "Watch per backend",
    "request counts",
    "in-flight requests",
    "queue time",
    "error and retry rates",
    "TTFT and ITL percentiles",
    "ejection events",
    "hot-backend alerts",
    "trace each request across the gateway, the router and the engine",
    "disable proxy buffering for SSE",
    "read and stream-idle timeouts above the maximum generation time",
    "heartbeats",
    "avoid Connection: close",
    "HTTP/2 end to end where possible",
    "measure time-to-first-token (TTFT) and inter-token latency at the proxy with $upstream_response_time or Envoy stats",
    "BGP convergence sets how quickly a failed node's traffic moves; BFD detects in under a second; resilient or consistent hashing in the router moves only the failed node's flows; announce the VIP only while the node can serve; a route change can move a flow to a different site, which breaks long-lived TCP; fabric ECMP caveats: elephant flows, RoCE varies UDP source ports per QP, tunnels need inner-header hashing, adaptive routing reacts to load",
    "Decide your failover budget first"
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. len={len(l):3d} | {l[:60]}...")
