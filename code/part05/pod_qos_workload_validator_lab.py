#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.7: Pods and workloads: Deployments, StatefulSets, DaemonSets and Jobs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pod_qos_workload_validator import (
    compute_pod_qos_and_effective_requests,
    validate_k8s_label,
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
    # 1. Section 2: Guaranteed vs Burstable vs BestEffort QoS, oom_score_adj, and init-container max(init, sum(app))
    guar = compute_pod_qos_and_effective_requests(
        init_containers=[
            {"requests": {"cpu_m": 16000, "mem_mi": 64000, "gpu": 0}, "limits": {"cpu_m": 16000, "mem_mi": 64000, "gpu": 0}}
        ],
        app_containers=[
            {"requests": {"cpu_m": 64000, "mem_mi": 819200, "gpu": 8}, "limits": {"cpu_m": 64000, "mem_mi": 819200, "gpu": 8}}
        ],
    )
    # Init container requests MORE CPU (32 cores) than the app container (8 cores)
    burst = compute_pod_qos_and_effective_requests(
        init_containers=[
            {"requests": {"cpu_m": 32000, "mem_mi": 16000, "gpu": 0}, "limits": {"cpu_m": 32000, "mem_mi": 32000, "gpu": 0}}
        ],
        app_containers=[
            {"requests": {"cpu_m": 8000, "mem_mi": 64000, "gpu": 1}, "limits": {"cpu_m": 0, "mem_mi": 64000, "gpu": 1}}
        ],
    )
    be = compute_pod_qos_and_effective_requests(init_containers=[], app_containers=[{"requests": {}, "limits": {}}])
    check(
        "compute_pod_qos_and_effective_requests derives Guaranteed (-997), Burstable (with max(init=32000m, app=8000m)=32000m CPU), and BestEffort (1000)",
        guar["qos_class"] == "Guaranteed"
        and guar["oom_score_adj"] == -997
        and burst["qos_class"] == "Burstable"
        and burst["effective_requests"]["cpu_m"] == 32000
        and be["qos_class"] == "BestEffort"
        and be["oom_score_adj"] == 1000,
    )

    # 2. Section 1 & KUR Ch. 6: Label key/value syntax rules (253-char DNS prefix, 63-char name/value)
    ok_lbl, _ = validate_k8s_label("nvidia.com/gpu.product", "NVIDIA-H100-80GB-HBM3")
    bad_dash, _ = validate_k8s_label("acme.com/-bad", "1.0.0")
    bad_len, _ = validate_k8s_label("app", "x" * 64)
    check(
        "validate_k8s_label accepts 'nvidia.com/gpu.product=NVIDIA-H100-80GB-HBM3' and rejects leading dash or >63-char value",
        ok_lbl is True and bad_dash is False and bad_len is False,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
