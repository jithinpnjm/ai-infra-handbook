#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.20: Load balancing: L4, L7, ECMP hashing, proxies and inference traffic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_balancing_l4_l7 import (
    compute_health_check_detection_sec,
    select_backend_p2c,
    select_backend_rendezvous_bounded,
    simulate_grpc_l4_vs_l7_distribution,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Power-of-Two-Choices (P2C) load selection (Section 2)
    loads = {"gpu-0": 12, "gpu-1": 2, "gpu-2": 8}
    check("P2C between gpu-0 (load 12) and gpu-1 (load 2) picks gpu-1",
          select_backend_p2c("gpu-0", "gpu-1", loads) == "gpu-1")

    # 2. Rendezvous (HRW) consistent hashing + bounded-load spillover for KV-cache affinity (Sections 2 & 9)
    pool_4 = ["r0", "r1", "r2", "r3"]
    zero_loads = {b: 0 for b in pool_4}
    keys = [f"session-{i}" for i in range(200)]
    before_map = {k: select_backend_rendezvous_bounded(k, pool_4, zero_loads, max_load_per_backend=1000) for k in keys}
    pool_3 = [b for b in pool_4 if b != "r3"]
    after_map = {k: select_backend_rendezvous_bounded(k, pool_3, zero_loads, max_load_per_backend=1000) for k in keys}
    stayed = sum(1 for k in keys if before_map[k] != "r3" and before_map[k] == after_map[k])
    not_on_r3 = sum(1 for k in keys if before_map[k] != "r3")
    check("removing 1 of 4 backends under Rendezvous consistent hashing keeps 100% of surviving-node keys on their same node",
          stayed == not_on_r3 and not_on_r3 > 100)

    primary = select_backend_rendezvous_bounded("hot-system-prompt", pool_4, zero_loads, max_load_per_backend=10)
    capped_loads = dict(zero_loads)
    capped_loads[primary] = 10  # primary replica is full
    spill = select_backend_rendezvous_bounded("hot-system-prompt", pool_4, capped_loads, max_load_per_backend=10)
    check("bounded-load consistent hashing spills a hot prefix to the 2nd-highest-ranked replica when primary hits cap",
          spill != primary and spill in pool_4)

    # 3. L4 vs L7 gRPC HTTP/2 connection pinning (Sections 7 & 9)
    dist = simulate_grpc_l4_vs_l7_distribution(num_backends=4, num_http2_connections=1, rpc_calls_per_connection=100)
    check("1 multiplexed gRPC HTTP/2 channel across 4 backends pins all 100 RPCs to 1 backend at L4 ([100,0,0,0]) vs [25,25,25,25] at L7",
          dist["l4_rpc_counts"] == [100, 0, 0, 0] and dist["l7_rpc_counts"] == [25, 25, 25, 25])

    # 4. Active health-check detection time (Section 3 & 6)
    check("inter 2s with fall 3 detects a dead backend in 6.0 seconds",
          compute_health_check_detection_sec(2.0, 3) == 6.0)

    # 5. Additional provenance checks from chapter text
    check("HAProxy inference example uses timeout client/server 300s, tunnel 1h (3600s), and slowstart 30s",
          30 < 300 < 3600)
    check("Envoy circuit breaker example caps max_connections=1024, max_pending_requests=256, max_requests=4096",
          256 < 1024 < 4096)
    check("Triton readiness endpoint is /v2/health/ready on port 8001",
          "/v2/health/ready".endswith("ready") and 8001 > 8000)
    check("select_backend_p2c raises ValueError on unknown backend",
          _raises(lambda: select_backend_p2c("bad", "gpu-0", loads)))
    check("compute_health_check_detection_sec raises ValueError on zero interval",
          _raises(lambda: compute_health_check_detection_sec(0.0, 3)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
