"""Chapter 5.25 model: Container exit-code & OOM classifier, 4-hop Pod
connectivity bisection engine, and GPU/PCIe/XID node symptom triager (`KUR`
Ch. 4, `PK`, `NK`, `volume-03`).

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 4
  ("Common kubectl Commands").
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK).
- James Strong & Vallery Lancey, Networking and Kubernetes (networking-and-
  kubernetes, NK).
- nvidia-devops (`volume-03/01..03`).
"""
from typing import Any, Dict, Mapping


def classify_container_exit_code(
    exit_code: int,
    *,
    oom_killed: bool = False,
    shm_used_pct: float = 0.0,
) -> Dict[str, str]:
    """Model Section 2, 4.3, & 4.6 container exit-code triage."""
    if exit_code == 137:
        if oom_killed and shm_used_pct > 50.0:
            cause = "SIGKILL (128+9): Cgroup OOMKilled driven by /dev/shm tmpfs memory usage"
        elif oom_killed:
            cause = "SIGKILL (128+9): Cgroup OOMKilled (memory.current hit memory.max)"
        else:
            cause = "SIGKILL (128+9): Killed by livenessProbe failure, node pressure, or grace-period expiry"
        return {"signal": "SIGKILL", "root_category": cause}
    if exit_code == 139:
        return {
            "signal": "SIGSEGV",
            "root_category": "SIGSEGV (128+11): Segmentation fault (native C/C++/CUDA ABI or driver mismatch)",
        }
    if exit_code == 143:
        return {
            "signal": "SIGTERM",
            "root_category": "SIGTERM (128+15): Graceful termination requested by kubelet (eviction/rollout/probe)",
        }
    if exit_code == 126:
        return {"signal": "NONE", "root_category": "Command invoked cannot execute (permission denied / non-executable binary)"}
    if exit_code == 127:
        return {"signal": "NONE", "root_category": "Command not found (missing entrypoint binary or wrong PATH in image)"}
    return {"signal": "NONE", "root_category": f"Application error exit ({exit_code}): inspect kubectl logs --previous"}


def diagnose_pod_connectivity_bisection(
    *,
    same_node_pod_ip_ok: bool,
    cross_node_pod_ip_ok: bool,
    cluster_ip_ok: bool,
    dns_name_ok: bool,
) -> str:
    """Model Section 1 & 3.3 bisection across the 4 network hops:
    1. Same-node Pod IP (`curl http://<same-node-pod-ip>:8000`)
    2. Cross-node Pod IP (`curl http://<cross-node-pod-ip>:8000`)
    3. Service ClusterIP (`curl http://<cluster-ip>:80`)
    4. Service DNS name (`curl http://svc.ns.svc.cluster.local:80`)
    """
    if not same_node_pod_ip_ok:
        return "Layer 1 (Pod/App/Local CNI): Backend process not listening on targetPort, local veth broken, or ingress NetworkPolicy dropping all traffic"
    if not cross_node_pod_ip_ok:
        return "Layer 2 (Cross-Node CNI/Underlay/MTU): Overlay UDP port (4789/6081) or BGP blocked between nodes, missing node route, or MTU blackhole"
    if not cluster_ip_ok:
        return "Layer 3 (Service/kube-proxy/EndpointSlice): Selector/targetPort mismatch, 0 ready EndpointSlices, stale iptables/IPVS/eBPF rules, or conntrack full"
    if not dns_name_ok:
        return "Layer 4 (DNS/CoreDNS): CoreDNS down, egress NetworkPolicy blocking UDP/TCP 53, or resolv.conf misconfigured"
    return "Healthy: all 4 hops (Same-Node PodIP, Cross-Node PodIP, ClusterIP, DNS) succeeded"


def triage_gpu_node_symptoms(telemetry: Mapping[str, Any]) -> Dict[str, str]:
    """Model Section 3.6 & 4.10 GPU hardware/fabric symptom classification."""
    xid = int(telemetry.get("last_xid", 0))
    if xid == 79:
        return {"severity": "critical", "diagnosis": "Xid 79: GPU has fallen off the PCIe bus (cordon, drain, cold BMC power cycle / RMA)"}
    if xid in {48, 63, 64, 74, 94, 95}:
        return {"severity": "critical", "diagnosis": f"Xid {xid}: Fatal ECC / NVLink / row-remap hardware fault (cordon, drain, run dcgmi diag -r 3)"}
    if int(telemetry.get("pcie_width", 16)) < 16:
        return {"severity": "warning", "diagnosis": f"PCIe link downtrained to x{telemetry['pcie_width']} (expected x16; check lspci -vv LnkSta)"}
    if float(telemetry.get("gpu_util_pct", 0.0)) > 90.0 and float(telemetry.get("tensor_active_ratio", 0.5)) < 0.05:
        return {"severity": "warning", "diagnosis": "NCCL spin-wait / communication hang: GPU util >90% but Tensor Core activity <5%"}
    return {"severity": "ok", "diagnosis": "GPU node telemetry nominal"}
