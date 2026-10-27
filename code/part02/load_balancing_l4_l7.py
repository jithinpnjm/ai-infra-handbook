"""Chapter 2.20 model: Power-of-Two-Choices (P2C) vs Round-Robin backend selection,
Rendezvous (Highest Random Weight, HRW) consistent hashing with bounded load for
LLM KV-cache prefix affinity, L4 vs L7 gRPC HTTP/2 connection-pinning simulator,
and active health-check detection time calculator.

Sources modeled:
- Josh Rosso et al., Production Kubernetes (production-kubernetes, PK), Chapter 6
  ("Service Routing": Services, Endpoints/EndpointSlices, kube-proxy iptables vs
  IPVS, Ingress controllers, externalTrafficPolicy Local, service meshes).
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapters 2 and 7 (ECMP hashing, anycast, multiplexing).
- Dinakaran Setty et al., AI Data Center Network Design and Technologies (ADC),
  Chapter 6 ("Efficient Load Balancing").
- nvidia-devops/volume-09 and volume-12 (gRPC/HTTP2 L4 connection pinning, NGINX
  and Envoy inference load balancing, prefix-cache-aware routing).
"""
import hashlib
from typing import Dict, List


def select_backend_p2c(
    cand_a: str,
    cand_b: str,
    backend_loads: Dict[str, int],
) -> str:
    """Pick the less-loaded of two candidate backends (Power of Two Choices, P2C)."""
    if cand_a not in backend_loads or cand_b not in backend_loads:
        raise ValueError("Candidate backend not in backend_loads")
    return cand_a if backend_loads[cand_a] <= backend_loads[cand_b] else cand_b


def select_backend_rendezvous_bounded(
    key: str,
    backends: List[str],
    current_loads: Dict[str, int],
    max_load_per_backend: int,
) -> str:
    """Rendezvous (HRW) consistent hashing with bounded-load spillover for LLM prefix-cache affinity."""
    if not backends:
        raise ValueError("backends must be non-empty")

    def score(b: str) -> int:
        h = hashlib.sha256(f"{key}|{b}".encode("utf-8")).hexdigest()[:16]
        return int(h, 16)

    ranked = sorted(backends, key=score, reverse=True)
    for b in ranked:
        if current_loads.get(b, 0) < max_load_per_backend:
            return b
    # If all backends are at/above cap, return the top-ranked one
    return ranked[0]


def simulate_grpc_l4_vs_l7_distribution(
    num_backends: int,
    num_http2_connections: int,
    rpc_calls_per_connection: int,
) -> Dict[str, List[int]]:
    """Compare RPC call distribution across num_backends under L4 connection balancing vs L7 request balancing."""
    if num_backends <= 0 or num_http2_connections <= 0 or rpc_calls_per_connection <= 0:
        raise ValueError("Counts must be positive")
    l4_counts = [0] * num_backends
    l7_counts = [0] * num_backends
    total_rpcs = num_http2_connections * rpc_calls_per_connection
    for c in range(num_http2_connections):
        l4_counts[c % num_backends] += rpc_calls_per_connection
    for r in range(total_rpcs):
        l7_counts[r % num_backends] += 1
    return {"l4_rpc_counts": l4_counts, "l7_rpc_counts": l7_counts}


def compute_health_check_detection_sec(interval_sec: float, fall_count: int) -> float:
    """Compute active health-check failure detection time = interval_sec * fall_count."""
    if interval_sec <= 0 or fall_count <= 0:
        raise ValueError("interval_sec and fall_count must be positive")
    return round(interval_sec * fall_count, 2)
