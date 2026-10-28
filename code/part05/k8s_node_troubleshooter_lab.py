#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.25: Troubleshooting Kubernetes from the node: crictl, nsenter, tcpdump and ip."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from k8s_node_troubleshooter import (
    classify_container_exit_code,
    diagnose_pod_connectivity_bisection,
    triage_gpu_node_symptoms,
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
    # 1. Section 2, 4.3, 4.6: Exit code 137 (/dev/shm OOM), 139 (SIGSEGV), 143 (SIGTERM), 127
    e137 = classify_container_exit_code(137, oom_killed=True, shm_used_pct=65.0)
    e139 = classify_container_exit_code(139)
    e143 = classify_container_exit_code(143)
    e127 = classify_container_exit_code(127)
    check(
        "classify_container_exit_code identifies 137 (/dev/shm OOM), 139 (SIGSEGV), 143 (SIGTERM), and 127 (command not found)",
        "/dev/shm" in e137["root_category"]
        and e139["signal"] == "SIGSEGV"
        and e143["signal"] == "SIGTERM"
        and "not found" in e127["root_category"],
    )

    # 2. Section 1 & 3.3: 4-hop connectivity bisection (PodIP same-node -> Cross-node -> ClusterIP -> DNS)
    d_cni = diagnose_pod_connectivity_bisection(
        same_node_pod_ip_ok=True,
        cross_node_pod_ip_ok=False,
        cluster_ip_ok=False,
        dns_name_ok=False,
    )
    d_svc = diagnose_pod_connectivity_bisection(
        same_node_pod_ip_ok=True,
        cross_node_pod_ip_ok=True,
        cluster_ip_ok=False,
        dns_name_ok=False,
    )
    d_dns = diagnose_pod_connectivity_bisection(
        same_node_pod_ip_ok=True,
        cross_node_pod_ip_ok=True,
        cluster_ip_ok=True,
        dns_name_ok=False,
    )
    check(
        "diagnose_pod_connectivity_bisection isolates Layer 2 (Cross-Node CNI), Layer 3 (Service/kube-proxy), and Layer 4 (DNS)",
        d_cni.startswith("Layer 2") and d_svc.startswith("Layer 3") and d_dns.startswith("Layer 4"),
    )

    # 3. Section 3.6 & 4.10: GPU node symptom triage (Xid 79, PCIe x4 downtrain, and NCCL spin-wait)
    t_xid79 = triage_gpu_node_symptoms({"last_xid": 79})
    t_pcie = triage_gpu_node_symptoms({"last_xid": 0, "pcie_width": 4})
    t_nccl = triage_gpu_node_symptoms({"last_xid": 0, "pcie_width": 16, "gpu_util_pct": 99.0, "tensor_active_ratio": 0.01})
    check(
        "triage_gpu_node_symptoms catches Xid 79, PCIe x4 downtrain, and NCCL spin-wait (99% GPU util, 1% Tensor active)",
        t_xid79["severity"] == "critical"
        and "x4" in t_pcie["diagnosis"]
        and "NCCL spin-wait" in t_nccl["diagnosis"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
