#!/usr/bin/env python3
"""Kubernetes-under-BCM rules from the BCM 11 Containerization Manual (chapters 4 and 6), as small testable pieces. Not BCM, not Kubernetes.

Each part names the manual section it follows. Where the manual is silent the code says so.
"""
import ipaddress, math

class K8sError(ValueError):
    pass

# ---- 4.1 reference architecture, 4.2 setup -------------------------------------------------------------------------
MIN_RAM_GB, MIN_CORES = 16, 2

def etcd_fault_tolerance(n):
    """An even etcd cluster still has a quorum but tolerates no more failures than the odd number below it (3.x manual 4.2.8)."""
    if n < 1:
        raise K8sError("etcd needs at least one node")
    return (n - 1) // 2

def plan_problems(etcd, control, workers, resources, other_clusters=()):
    """resources: {node: (ram_gb, cores)}. Checks from 4.1 and 4.2: odd etcd count; >=3 etcd and >=2 control plane for HA; 16 GB RAM and two cores
    per node; nodes cannot be shared between Kubernetes clusters."""
    p = []
    if len(etcd) % 2 == 0:
        p.append(f"{len(etcd)} etcd nodes: an even number adds cost without adding fault tolerance (use an odd number)")
    if len(etcd) < 3:
        p.append("fewer than 3 etcd nodes: a single point of failure")
    if len(control) < 2:
        p.append("fewer than 2 control plane nodes: no control plane HA")
    for n in sorted(set(etcd) | set(control) | set(workers)):
        ram, cores = resources.get(n, (0, 0))
        if ram < MIN_RAM_GB or cores < MIN_CORES:
            p.append(f"{n}: {ram} GB RAM and {cores} cores is below the per-node minimum of {MIN_RAM_GB} GB and {MIN_CORES} cores")
    shared = (set(etcd) | set(control) | set(workers)) & set(other_clusters)
    if shared:
        p.append(f"nodes {sorted(shared)} already belong to another Kubernetes cluster: nodes cannot be shared")
    return p

def pod_network_capacity(pod_cidr, per_node_prefix=24):
    """4.2.1: entire /24 ranges are assigned to individual Kubernetes nodes from the pod CIDR, so the pod network size caps the node count."""
    net = ipaddress.ip_network(pod_cidr)
    if net.prefixlen > per_node_prefix:
        raise K8sError("the pod network is smaller than one per-node range")
    return 2 ** (per_node_prefix - net.prefixlen)

def networks_overlap(service_cidr, pod_cidr, existing=()):
    nets = [ipaddress.ip_network(x) for x in (service_cidr, pod_cidr, *existing)]
    return [(str(a), str(b)) for i, a in enumerate(nets) for b in nets[i + 1:] if a.overlaps(b)]

def typha_replicas(nodes):
    """4.2.2: Calico Typha is deployed automatically above 50 nodes: one replica per 150 nodes, at least 3, at most 20. Not enabled automatically if the
    cluster grows past 50 after install."""
    if nodes <= 50:
        return 0
    return max(3, min(20, math.ceil(nodes / 150)))

CNI_CHOICES = {"calico", "flannel"}      # in the wizard; Cilium is supported but installed outside it
DEFAULT_OPERATORS = {"Kgateway", "Kubernetes Metrics Server", "Kubernetes State Metrics", "MetalLB"}

def operator_problems(selected, cluster_has_gpus, kyverno_installed=True):
    p = []
    if cluster_has_gpus and "NVIDIA GPU Operator" not in selected:
        p.append("the cluster has GPUs but the NVIDIA GPU Operator is not selected: GPU workloads cannot run (the wizard does not warn)")
    if not kyverno_installed:
        p.append("no Kyverno: users are separated by RBAC but can run privileged pods and mount host paths (node-level exposure)")
    return p

def gpu_operator_values(toolkit=True, driver=False, nfd=True, dgx_os=False):
    """6.7.1: three independent checklist options: toolkit.enabled (default on), driver.enabled (default off), nfd.enabled (default on). On DGX OS images
    the driver is always provisioned by the host, so driver.enabled must be false. With the toolkit off, BCM provides it as a system package and uses
    containerd runtime-class drop-in files."""
    if dgx_os and driver:
        raise K8sError("on DGX OS images the driver is always provisioned by the host: driver.enabled must be false")
    v = {"toolkit.enabled": toolkit, "driver.enabled": driver, "nfd.enabled": nfd}
    v["gpu access via"] = "operator toolkit daemonset (CDI where available)" if toolkit else "containerd runtime-class drop-ins from the BCM package"
    return v

def kubelet_gpu_settings(node_has_gpus, deployed_bcm_version=(11, 34, 0)):
    """4.9.4: from BCM 11.34, GPU worker nodes get static CPU manager, best-effort topology manager at pod scope and kubeReserved cpu 250m.
    Control plane nodes, non-GPU workers and clusters deployed before 11.34 are not affected."""
    if not node_has_gpus or tuple(deployed_bcm_version) < (11, 34, 0):
        return {}
    return {"cpuManagerPolicy": "static", "topologyManagerPolicy": "best-effort", "topologyManagerScope": "pod", "kubeReserved": {"cpu": "250m"}}

# ---- 4.5 overlays ------------------------------------------------------------------------------------------------
OVERLAYS = {"kube-default-etcd": (500, "Etcd::Host"), "kube-default-master": (510, "kubelet (control plane)"),
            "kube-default-worker": (500, "kubelet (worker)"), "kube-default-netq": (501, "netq")}

def kubelet_mode(in_master, in_worker):
    """A node in both kube-default-master (510) and kube-default-worker (500) gets the master overlay's kubelet role: the higher priority wins.
    (The manual's own example shows control-plane,worker nodes, so the role set can include both; this models only which overlay's parameters apply.)"""
    if in_master:
        return "control-plane", OVERLAYS["kube-default-master"][0]
    if in_worker:
        return "worker", OVERLAYS["kube-default-worker"][0]
    return None, None

# ---- 4.10-4.15 users and policy ------------------------------------------------------------------------------------------
K8S_ROLES = ("view", "edit", "admin", "cluster-admin")

def k8s_user(name, role="edit", allow_all_uids=False, user_paths=None, operators=()):
    """cm-kubernetes-setup --add-user: needs an existing PAM user. Creates service account <name>, namespace <name>-restricted, binds the role there,
    read-only on nodes. Kyverno policies: hostPath must be the user's home (/home/<name>) unless --user-paths; UID/GID are the PAM user's unless
    --allow-all-uids, in which case any UID is possible only when no hostPath volume is used."""
    if role not in K8S_ROLES:
        raise K8sError(f"role must be one of {K8S_ROLES}")
    paths = list(user_paths) if user_paths is not None else [f"/home/{name}"]
    return {"name": name, "namespace": f"{name}-restricted", "service_account": name, "role": role, "paths": paths,
            "allow_all_uids": allow_all_uids, "operators": list(operators), "can_list_nodes": True}

def pod_allowed(user, host_paths=(), uid_is_user=True, privileged=False, kyverno=True):
    """Whether a pod created by `user` in their namespace is admitted by the Kyverno policies."""
    if not kyverno:
        return True, "no Kyverno: nothing restricts the pod inside the namespace"
    if privileged:
        return False, "privileged pods are denied by the Pod Security Standards policies"
    for hp in host_paths:
        if not any(hp == p or hp.startswith(p.rstrip("/") + "/") for p in user["paths"]):
            return False, f"hostPath {hp} is not under the user's allowed paths {user['paths']}"
    if not uid_is_user:
        if not user["allow_all_uids"]:
            return False, "the UID/GID must equal the user's PAM UID/GID"
        if host_paths:
            return False, "with allow-all-uids, hostPath volumes are rejected"
    return True, "admitted"

PSS_POLICIES = ["disallow-host-namespaces", "disallow-host-path", "disallow-host-ports"]

def kyverno_replicas(ha):
    """4.14.1: the HA option sets replicaCount to 3."""
    return 3 if ha else 1

# ---- 4.17 gateway --------------------------------------------------------------------------------------------------------
def gateway_default_ip(network, used):
    """The wizard pre-fills the highest address on the node network that is not in use (excluding device addresses, head-node mounts, the dynamic
    range and MetalLB pools). `used` is a set of addresses and ranges as strings/networks."""
    net = ipaddress.ip_network(network)
    taken = set()
    blocked = []
    for u in used:
        if "-" in str(u):
            a, b = str(u).split("-")
            blocked.append((int(ipaddress.ip_address(a)), int(ipaddress.ip_address(b))))
        else:
            taken.add(int(ipaddress.ip_address(str(u))))
    for ip in range(int(net.broadcast_address) - 1, int(net.network_address), -1):
        if ip in taken or any(a <= ip <= b for a, b in blocked):
            continue
        return str(ipaddress.ip_address(ip))
    raise K8sError("no free address")

def gateway_traffic_path():
    return ["client", "Gateway proxy (NGINX on head node, port 443, chooses by TLS SNI hostname)", "Gateway (MetalLB LoadBalancer IP)", "Kgateway proxy pods (HTTPRoute/TLSRoute)", "service"]

def gateway_exposes_traffic(kgateway_operator, gateway_exists):
    """Only installing the Kgateway operator exposes nothing: a Gateway (with a GatewayClass) must exist so the operator creates proxy pods."""
    return bool(kgateway_operator and gateway_exists)

# ---- ports ---------------------------------------------------------------------------------------------------------------
PORTS = {"api_server_proxy": 10443, "gateway_proxy": 443, "etcd_client": 5001, "etcd_peer": 5002, "etcd_spool": "/var/lib/etcd"}

def netq_prereq_problems(nodes, disk_gib, mem_gib, ubuntu_ok, kyverno, default_cmd_ports_in_use):
    """6.9.1: 1 or 3 NetQ nodes (regular compute nodes), >=250 GiB disk, >=64 GiB RAM, Ubuntu 24.04+, no Kyverno, and BCM's default CMDaemon ports
    cannot be used (move them with cm-cmd-ports --http 8083 --https 8084 and restart cmd)."""
    p = []
    if nodes not in (1, 3):
        p.append("the number of NetQ nodes must be 1 or 3")
    if disk_gib < 250:
        p.append("NetQ nodes need at least 250 GiB of disk")
    if mem_gib < 64:
        p.append("NetQ nodes need at least 64 GiB of memory")
    if not ubuntu_ok:
        p.append("NetQ 4.15+ is supported only on Ubuntu 24.04 and later")
    if kyverno:
        p.append("Kyverno is not supported together with NetQ")
    if default_cmd_ports_in_use:
        p.append("the BCM default ports cannot be used: run cm-cmd-ports --http 8083 --https 8084 && systemctl restart cmd")
    return p

# ---- preflight and air-gap versions ------------------------------------------------------------------------------------------
PREFLIGHT = {"dns": "--skip-dns-configuration-check", "ping": "--skip-ping-check", "mtu": "--skip-mtu-check",
             "package manager": "--skip-package-manager-update-check", "kube version": "--skip-kube-version-check"}

def airgap_version_problems(required, found):
    """From BCM 11.34 the wizard validates the air-gapped bundle first and names each package whose found version differs from the expected one."""
    return [f"{pkg}=={want} (found: {found.get(pkg, 'missing')})" for pkg, want in required.items() if found.get(pkg) != want]

# ---- upgrade -----------------------------------------------------------------------------------------------------------------
def upgrade_steps(control_plane_nodes, workers):
    """4.22: one node at a time, first control plane node, then the other control plane nodes, then workers, then update the Kubernetes version in BCM.
    kubeadm upgrades only itself and a few central components; etcd, CNI, CSI, container runtimes and unmanaged pods are not covered. `--ignore-daemonsets`
    on drain skips DaemonSet pods, which then need a separate upgrade."""
    if not control_plane_nodes:
        raise K8sError("no control plane nodes")
    steps = [f"upgrade the first control plane node {control_plane_nodes[0]} (kubeadm upgrade apply)"]
    steps += [f"upgrade control plane node {n} (kubeadm upgrade node)" for n in control_plane_nodes[1:]]
    steps += [f"drain, upgrade and uncordon worker {n}" for n in workers]
    steps.append("update the Kubernetes version in BCM (cmsh kubernetes mode) so it matches")
    steps.append("separately upgrade etcd, CNI, CSI, runtimes and DaemonSet-managed components as needed")
    return steps


# ---- Gap pass: 4.3, 4.4, 4.7, 4.8, 4.16, 4.18-4.21, ch. 5, ch. 6 other operators, ch. 7 Edge, ch. 8 CAPI, App. A ------------
K8S_HEALTH_CHECKS = ("KubernetesChildNode", "KubernetesComponentsStatus", "KubernetesNodesStatus", "KubernetesPodsStatus")
EDGE_SKIP_FLAGS = ("--skip-package-install", "--skip-reboot", "--skip-image-update", "--skip-disksetup-changes")
ALLOY_DEFAULT_LOG_SOURCES = {"pod_logs": True, "kube_events": True, "varlog": False}


def etcd_member_cert_source(etcd_cluster_cert, etcd_host_role_cert=None):
    """4.8 Table 4.2 (p. 63): the EtcdHost role can specify a member certificate/key as well, and in that case it overwrites
    any value set on the global EtcdCluster object."""
    return (etcd_host_role_cert, "EtcdHost") if etcd_host_role_cert else (etcd_cluster_cert, "EtcdCluster")


def amd_gpu_daemonset_nodes(all_nodes, gpu_nodes, tainted_head_nodes, has_control_plane_toleration=False, has_labelset_affinity=False):
    """4.4.3 & 4.4.4 (pp. 55-57): by default the AMD GPU device plugin DaemonSet runs on every untainted node (even nodes without
    GPUs) and skips tainted head/control-plane nodes. Adding the node-role.kubernetes.io/control-plane NoSchedule toleration
    includes tainted head nodes; adding a LabelSet (nvidia.com/amd-gpu-accelerator=) and nodeAffinity restricts it to GPU nodes."""
    candidates = [n for n in all_nodes if (n not in set(tainted_head_nodes) or has_control_plane_toleration)]
    if has_labelset_affinity:
        candidates = [n for n in candidates if n in set(gpu_nodes)]
    return candidates


def external_fqdn_from_trusted_domains(trusted_domains):
    """4.16.1 (p. 80): the external FQDN of the Kubernetes cluster is the first item in the trusteddomains list on the
    kubernetes cluster entity."""
    if not trusted_domains:
        raise K8sError("trusteddomains is empty")
    return trusted_domains[0]


def alloy_loki_selection_ok(alloy_selected, loki_selected):
    """6.4 & 6.4.1 (pp. 111-112): Grafana Alloy is a collector and depends on Grafana Loki; selecting Alloy without Loki is
    rejected by the wizard, whereas Loki can be installed without Alloy."""
    if alloy_selected and not loki_selected:
        return False, "Grafana Alloy requires Grafana Loki to be selected as well"
    return True, "ok"


def loki_wizard_flow(num_workers, has_default_storage_class, chosen_mode="SingleBinary", expose_httproute=False, route_user="", route_password=""):
    """6.5.1 (pp. 113-114):
    - The Loki deployment mode screen (SingleBinary / SimpleScalable / Distributed) is shown only if the cluster has >= 3 worker
      nodes AND a default StorageClass; otherwise SingleBinary is selected automatically without prompting.
    - The Basic Loki configuration screen (MinIO, S3/FileSystem, Replica factor) is shown only if SingleBinary is used; for
      SimpleScalable or Distributed it is skipped and MinIO + S3 are enabled automatically.
    - If Gateway HTTPRoute is enabled, username and password are mandatory (empty fields are rejected)."""
    mode_prompted = (num_workers >= 3 and bool(has_default_storage_class))
    effective_mode = chosen_mode if mode_prompted else "SingleBinary"
    basic_screen_shown = (effective_mode == "SingleBinary")
    minio_s3_forced = (effective_mode in ("SimpleScalable", "Distributed"))
    route_creds_ok = (not expose_httproute) or (bool(route_user) and bool(route_password))
    return {
        "mode_prompted": mode_prompted,
        "effective_mode": effective_mode,
        "basic_screen_shown": basic_screen_shown,
        "minio_s3_forced": minio_s3_forced,
        "route_creds_ok": route_creds_ok,
    }


def jupyter_kernel_helm_upgrade_ok(installed_namespace, upgrade_namespace):
    """6.6.1 (p. 114): when upgrading cm-jupyter-kernel-operator with helm upgrade, the -n namespace must match the release's
    existing namespace (e.g. 'cm'), not a hardcoded 'cm-jupyter-kernel-operator-system' (mismatched -n prunes the old Namespace
    and deletes the entire release)."""
    return installed_namespace == upgrade_namespace


def grafana_autoloads_configmap(labels):
    """6.10.2 (p. 143): by default Grafana automatically loads dashboards from ConfigMaps containing the label grafana_dashboard='1'
    in any namespace."""
    return labels.get("grafana_dashboard") == "1"


def modify_operators_remove(installed_operators, to_remove, dependencies):
    """6.15.2 (pp. 155-156): from BCM 11.34+, Modify operators uninstalls selected Helm releases in reverse dependency order,
    refuses to remove an operator that another installed operator still depends on, and leaves CRDs, namespaces, node labels,
    and taints in place."""
    remaining = set(installed_operators) - set(to_remove)
    blocked = []
    for rem in remaining:
        for dep in dependencies.get(rem, ()):
            if dep in set(to_remove):
                blocked.append(f"cannot remove {dep}: {rem} still depends on it")
    if blocked:
        return {"ok": False, "errors": blocked, "uninstall_order": [], "retained_artifacts": []}
    # reverse dependency order: if A depends on B and both are removed, uninstall A before B
    order = sorted(to_remove, key=lambda op: sum(1 for other in to_remove if op in dependencies.get(other, ())))
    return {
        "ok": True,
        "errors": [],
        "uninstall_order": order,
        "retained_artifacts": ["CRDs", "namespaces", "DaemonSets", "node labels", "taints"],
    }


def capi_template_resolution(requested_label, mgmt_cluster_name, existing_templates):
    """8.8 (pp. 181-182): fallback sequence for the KubeCluster CAPI template:
    (1) the label infrav1.nvidia.x-k8s.io/capi-kube-template if it exists,
    (2) capi-<mgmt_cluster_name>-template if it exists,
    (3) capi-template."""
    cands = []
    if requested_label:
        cands.append(requested_label)
    cands.append(f"capi-{mgmt_cluster_name}-template")
    cands.append("capi-template")
    for c in cands:
        if c in set(existing_templates):
            return c
    return "capi-template"


def capi_rolling_upgrade_ok(spare_byohosts, strategy="RollingUpdate", workers_scaled_down=False):
    """8.3.4 (p. 170): CAPI rolling upgrades replace machines one by one and require at least one spare ByoHost so the new
    machine can be provisioned before the old one is deleted, unless OnDelete strategy is used or workers are scaled down first."""
    if strategy == "OnDelete" or workers_scaled_down:
        return True
    return spare_byohosts >= 1


def gateway_self_signed_cert_paths(cluster_name="default"):
    """Appendix A (pp. 185-186): self-signed Gateway TLS files generated by cm-kubernetes-setup on the active head node."""
    base = f"/etc/kubernetes/pki/{cluster_name}"
    return {
        "ca_crt": f"{base}/gateway-ca.crt",
        "ca_key": f"{base}/gateway-ca.key",
        "tls_crt": f"{base}/gateway-bcm-gateway.crt",
        "tls_key": f"{base}/gateway-bcm-gateway.key",
        "secret_name": "gateway-bcm-gateway-cert",
        "secret_namespace": "bcm-gateway",
    }

