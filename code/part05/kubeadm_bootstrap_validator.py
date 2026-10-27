"""Chapter 5.4 model: `kubeadm` node preflight & CIDR non-overlap validator,
bootstrap token format (`[a-z0-9]{6}.[a-z0-9]{16}`) & `--discovery-token-ca-cert-hash`
verifier, and `kubeadm init` phase sequence simulator.

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapters 3,
  4, and Appendix A ("Building a Raspberry Pi Kubernetes Cluster"):
  * Chapter 3 ("Deploying a Kubernetes Cluster") & Appendix A: bare-metal node
    prep (`swapoff -a`, cgroups, static IPs), `kubeadm init --pod-network-cidr`,
    copying `/etc/kubernetes/admin.conf` to `$HOME/.kube/config`, CNI installation,
    and `kubeadm join --token <token> --discovery-token-ca-cert-hash sha256:<hash>`.
  * Chapter 4 ("Common kubectl Commands"): `kubectl config set-context` /
    `use-context`, `view-last-applied`/`edit-last-applied`/`set-last-applied`,
    `kubectl attach`, and `kubectl completion bash`.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapters 1 & 2 ("Path to Production" and
  "Deployment Models"):
  * Kubernetes as foundation ("engine" vs "driveable car" / "house foundation"
    vs "habitable home"), in-tree vs out-of-tree CPI/CSI/CRI/CNI interfaces.
  * Managed Services vs Prebuilt Installers vs Roll Your Own, bare-metal vs
    virtualization trade-offs, HA control-plane & etcd topology, and golden
    machine images (Packer + Ansible).
"""
import ipaddress
import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

BOOTSTRAP_TOKEN_RE = re.compile(r"^[a-z0-9]{6}\.[a-z0-9]{16}$")
CA_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

KUBEADM_INIT_PHASES: Tuple[str, ...] = (
    "preflight",
    "certs",
    "kubeconfig",
    "kubelet-start",
    "control-plane",
    "etcd",
    "upload-config",
    "upload-certs",
    "mark-control-plane",
    "bootstrap-token",
    "addon",
)


def validate_node_preflight_and_cidrs(cfg: Mapping[str, Any]) -> Tuple[bool, List[str]]:
    """Model Section 1, 2, 3, 4 node preflight checks and CIDR validation:
    1. Swap must be disabled (`swap_enabled == False`).
    2. Required kernel modules (`overlay`, `br_netfilter`) must be loaded.
    3. Required sysctls (`net.bridge.bridge-nf-call-iptables == 1`, `net.ipv4.ip_forward == 1`).
    4. `kubelet` cgroup driver (`systemd`) must match containerd `SystemdCgroup = True`.
    5. `node_cidr`, `pod_Subnet`, and `service_subnet` must not overlap, and CNI
       pool CIDR must match `kubeadm` `podSubnet`.
    """
    errors: List[str] = []
    if cfg.get("swap_enabled", False):
        errors.append("swap is enabled; kubelet requires swap off (swapoff -a)")
    mods = set(cfg.get("loaded_modules", ()))
    for req_mod in ("overlay", "br_netfilter"):
        if req_mod not in mods:
            errors.append(f"missing required kernel module: {req_mod}")
    sysctls = cfg.get("sysctls", {})
    for req_key in ("net.bridge.bridge-nf-call-iptables", "net.ipv4.ip_forward"):
        if int(sysctls.get(req_key, 0)) != 1:
            errors.append(f"sysctl {req_key} must be 1")
    if cfg.get("kubelet_cgroup_driver") != "systemd" or not cfg.get("containerd_systemd_cgroup", False):
        errors.append("cgroup driver mismatch: both kubelet and containerd must use systemd")

    node_net = ipaddress.ip_network(str(cfg["node_cidr"]))
    pod_net = ipaddress.ip_network(str(cfg["pod_subnet"]))
    svc_net = ipaddress.ip_network(str(cfg["service_subnet"]))
    cni_net = ipaddress.ip_network(str(cfg["cni_pool_cidr"]))

    if node_net.overlaps(pod_net) or node_net.overlaps(svc_net) or pod_net.overlaps(svc_net):
        errors.append("node_cidr, pod_subnet, and service_subnet must not overlap")
    if pod_net != cni_net:
        errors.append(f"CNI pool CIDR ({cni_net}) does not match kubeadm podSubnet ({pod_net})")

    return (len(errors) == 0), errors


def verify_kubeadm_join_credentials(
    token: str,
    discovery_ca_hash: str,
    expected_ca_sha256_hex: str,
    is_control_plane_join: bool = False,
    certificate_key_age_minutes: int = 0,
) -> Tuple[bool, List[str]]:
    """Model Section 5 & 7 `kubeadm join` token, CA cert hash pinning, and
    `--upload-certs` 2-hour (`120` min) certificate key expiry.
    """
    errors: List[str] = []
    if not BOOTSTRAP_TOKEN_RE.match(token):
        errors.append("invalid bootstrap token format (expected [a-z0-9]{6}.[a-z0-9]{16})")
    if not CA_HASH_RE.match(discovery_ca_hash):
        errors.append("invalid discovery-token-ca-cert-hash format (expected sha256:<64-hex>)")
    elif discovery_ca_hash != f"sha256:{expected_ca_sha256_hex}":
        errors.append("CA hash mismatch: API server CA does not match pinned --discovery-token-ca-cert-hash")
    if is_control_plane_join and certificate_key_age_minutes > 120:
        errors.append("kubeadm-certs secret expired (> 120 minutes); re-run 'kubeadm init phase upload-certs --upload-certs'")
    return (len(errors) == 0), errors
