#!/usr/bin/env python3
"""Air-gapped BCM rules from the Containerization Manual appendices B and C, the Administrator Manual 9.6.3 and 14.12, and the Installation Manual (Ansible installer,
DOCA OFED), as small testable pieces. Not BCM. Where I derive something it is labelled.
"""
import math, re

class AirgapError(ValueError):
    pass

# ---- Appendix C: upgrade prerequisites ---------------------------------------------------------------------------------------
MIN_BCM = {10: (10, 31, 0), 11: (11, 32, 0)}

def _tuple(v):
    return tuple(int(x) for x in re.match(r"(\d+)\.(\d+)\.(\d+)", v).groups())

def bcm_version_ok_for_airgap_upgrade(version):
    major = _tuple(version)[0]
    if major not in MIN_BCM:
        raise AirgapError("the appendix covers BCM 10 and 11")
    return _tuple(version) >= MIN_BCM[major]

def minor(v):
    return tuple(int(x) for x in v.split(".")[:2])

def upgrade_target_problems(node_versions, target):
    """Kubernetes version skew policy as the manual states it: only two ADJACENT minor releases may exist in the cluster at any time (1.34 and 1.35 fine; 1.33, 1.34, 1.35 not).
    If nodes are on two adjacent minors the only valid upgrade is to the newer of them."""
    minors = sorted({minor(v) for v in node_versions})
    p = []
    if len(minors) > 2 or (len(minors) == 2 and minors[1][1] - minors[0][1] != 1):
        p.append(f"the cluster already spans {['%d.%d' % m for m in minors]}: only two adjacent minor releases may exist")
    tm = minor(target)
    if len(minors) == 2 and tm != minors[1]:
        p.append(f"nodes are on two minors: the only valid target is the newer one, {minors[1][0]}.{minors[1][1]}")
    if len(minors) == 1 and tm[1] - minors[0][1] > 1:
        p.append("a minor upgrade goes to the next minor only (skipping minors violates the skew policy)")
    return p

def upgrade_kind(current, target):
    return "patch" if minor(current) == minor(target) else "minor"

# ---- Appendix B: preparing the bundle ---------------------------------------------------------------------------------------------
BUNDLE_DIRS = ["packages", "packages-head", "packages-non-dgx", "packages-cuda", "k8s-images", "helm-charts", "crds"]

def bundle_problems(files_by_dir):
    """`find <dirs> -type f` must show files in every category: an empty category (even if the directory or its subdirectories exist) means its download script did not
    complete and must be re-run before tarballing."""
    return [d for d in BUNDLE_DIRS if not files_by_dir.get(d)]

def workdir_gb(runai=False):
    """Without Run:ai about 8.6 GB (images about 8.1 GB); Run:ai adds 13 to 14 GB: plan upwards of 20 GB."""
    return 22 if runai else 9

def dockerhub_pull_windows(images, authenticated):
    """Unauthenticated pulls: 100 per 6 hours; authenticated: 200 per 6 hours. Returns the minimum number of 6-hour windows needed."""
    limit = 200 if authenticated else 100
    return math.ceil(images / limit)

def arch_ok(initial_host_arch, cluster_arch, mixed_cluster=False):
    if mixed_cluster:
        return False, "the tarball supports one architecture at a time: a mixed-architecture cluster needs a more customized approach"
    return (initial_host_arch == cluster_arch), ("ok" if initial_host_arch == cluster_arch else "the initial host architecture and OS must match the cluster")

def helm_version_ok(version):
    """The download host needs helm 3.x, not 4.x (as of April 2026 in the manual)."""
    return version.startswith("3.")

# ---- ordered procedure ------------------------------------------------------------------------------------------------------------------
STEPS = [
    "assign control-plane, worker and etcd nodes (must be done before the cluster is air-gapped)",
    "generate cm-kubernetes-setup.conf: cm-kubernetes-setup --airgap-registry <registry> --airgap-registry-as-helm (save, do not deploy)",
    "on the internet host: install helm 3 and skopeo, run the download scripts, check every category has files, tar the airgapped directory",
    "carry the tarball to the active head node and extract it (Ubuntu: not under /root, e.g. /tmp)",
    "cm-kubernetes-setup --airgap-install-system-packages -c cm-kubernetes-setup.conf (from the extracted directory; also updates the secondary head)",
    "cm-container-registry-setup --skip-packages (active head, SAN such as master.cm.cluster)",
    "trust the registry CA system-wide (copy to /usr/local/share/ca-certificates and update-ca-certificates)",
    "cm-docker-setup --skip-packages (only needed for the Run:ai installation)",
    "cm-kubernetes-setup --airgap-push-container-images -c ...",
    "cm-kubernetes-setup --airgap-push-helm-charts -c ...",
    "$K8S_AG_SCRIPTS/extract_crds.sh",
    "cm-kubernetes-setup -c cm-kubernetes-setup.conf (deploy)",
    "Run:ai only: cm-runai-setup after Kubernetes is deployed",
]

def order_problems(done):
    """done: a list of step indices in the order they were carried out. Checks a few hard dependencies the manual states."""
    need = {5: [4], 6: [5], 8: [5, 6], 9: [5, 6], 10: [3], 11: [8, 9, 10, 1], 12: [11], 4: [1, 3]}
    seen, p = set(), []
    for s in done:
        missing = [d for d in need.get(s, []) if d not in seen]
        if missing:
            p.append(f"step {s} ({STEPS[s][:40]}...) before step(s) {missing}")
        seen.add(s)
    return p

def extraction_dir_ok(distro, path):
    """On Ubuntu APT runs as the _apt user, which cannot read under /root: extract to /tmp or another APT-readable place. Rocky and RHEL can extract in place."""
    if distro.lower().startswith("ubuntu") and path.startswith("/root"):
        return False
    return True

def passive_head_problems(on_passive, use_force=False):
    p = []
    if on_passive:
        p.append("do not run cm-kubernetes-setup on a passive head node: images are local to each head and synced from the active, so a write on the passive is reverted")
    if use_force:
        p.append("do not use --force to override the 'not the active head node' refusal")
    return p

def gpu_operator_available(version, downloaded_charts):
    """Only chart versions that were downloaded can be installed in an air-gapped cluster; a certified version is not necessarily downloaded and vice versa."""
    return version in downloaded_charts

# ---- Run:ai ------------------------------------------------------------------------------------------------------------------------------
RUNAI_DEPENDENCIES = ["NVIDIA GPU Operator", "Grafana Operator", "Kgateway", "Knative Operator", "Kubeflow Training Operator", "Kubernetes Metrics Server", "Kubernetes MPI Operator",
                      "Kubernetes State Metrics", "LeaderWorkerSet Operator", "MetalLB", "Network Operator", "NIM Operator", "Prometheus Adapter", "Prometheus Operator Stack"]
RUNAI_PRE_AIRGAP = ["three reserved IP addresses from the internal network", "DNS records for the Run:ai control plane FQDN", "two wildcard subdomains", "a TLS certificate and private key", "an NGC API key"]

def runai_problems(distro, version, selected_operators, prerequisites_ready):
    p = []
    if not distro.lower().startswith(("ubuntu",)):
        p.append("the cm-setup-runai-bcm11 package is only published as a .deb: an air-gapped Run:ai deployment on RHEL is not supported in this release")
    parts = tuple(int(x) for x in version.split("."))
    if parts < (2, 23, 60):
        p.append("Run:ai 2.23.60 or later is required (multi-arch support)")
    required = set(RUNAI_DEPENDENCIES) - {"Network Operator", "NIM Operator"}
    missing = sorted(required - set(selected_operators))
    if missing:
        p.append(f"operators Run:ai depends on were not selected when the configuration was generated: {missing}")
    if not prerequisites_ready:
        p.append("Run:ai prerequisites (IPs, DNS, wildcard subdomains, TLS, NGC key) cannot be arranged once the cluster is air-gapped")
    return p

def sha256_line_ok(sha_file_text, filename):
    """The .sha256 file contains only the checksum; for `sha256sum -c` the file name must be appended on the same line."""
    return filename in sha_file_text

# ---- OS packages and local repositories ---------------------------------------------------------------------------------------------------
def apt_local_repo_line_problems(line):
    """9.6.3: the BCM packages line from the ISO does not need trusted=yes (the cm-config-apt package imports the BCM keyring). The second line, for the base Ubuntu
    packages on the same ISO, uses trusted=yes (a deliberate risk acceptance for local, physically controlled media) and must not be copied to a network-hosted repository."""
    p = []
    if "trusted=yes" in line and re.search(r"https?://", line):
        p.append("trusted=yes on a network-hosted repository: the manual allows it only for local, physically controlled installation media")
    return p

def offline_options():
    return {"DOCA OFED": "cm-doca-ofed-install.sh ... --cmdvd installs from a BCM install medium", "cm-mysql-setup": "--skip-packages, with mysql-server packages preinstalled in the server nodes' image and mysql-router in client images",
            "cm-create-image": "-e -s with a local repository (9.6.4)", "RHEL installer": "pre_install_repo_files points to an internal mirror and --basedistrepo points at it; keep the ISO's Rocky repos disabled on a RHEL host"}


# ---- Appendix C.4 (pp. 215-218): step-by-step kubeadm upgrade sessions (added in gap pass) --------------------------------
def c4_control_plane_upgrade_cmd(is_first_control_plane, target_version="v1.33.6", kubeconfig="/root/.kube/config-default"):
    """Appendix C.4.1 & Updating Subsequent Control Plane Nodes (pp. 215-217):
    - The first control plane node runs `kubeadm upgrade plan` and then `kubeadm upgrade apply <version> --kubeconfig=...`.
    - Subsequent control plane nodes run `kubeadm upgrade node --kubeconfig ...` (no `upgrade apply` and no version argument)."""
    if is_first_control_plane:
        return f"kubeadm upgrade apply {target_version} --kubeconfig={kubeconfig}"
    return f"kubeadm upgrade node --kubeconfig {kubeconfig}"


def c4_worker_upgrade_steps(host, kube_instance="default", write_flag=True):
    """Appendix C.4 (pp. 217-218): worker upgrade order across head node and worker node.
    Without -w on imageupdate it only runs a dry run."""
    if not write_flag:
        raise AirgapError("imageupdate without -w|--write is only a dry-run and does not update binaries on the node (C.4.1 p. 215)")
    return [
        f"head: kubectl drain {host} --ignore-daemonsets",
        f"head: cmsh -c 'device use {host}; imageupdate -w --wait'",
        f"worker: kubeadm upgrade node --kubeconfig=/root/.kube/config-{kube_instance}",
        "worker: systemctl daemon-reload",
        "worker: systemctl restart kubelet",
        f"head: kubectl uncordon {host}",
    ]


def c4_apiserver_image_matches(describe_image_line, registry="master.cm.cluster:5000", target_version="v1.33.6"):
    """Appendix C.4.1 (p. 217): verify that kube-apiserver-<node> uses <registry>/kube-apiserver:<target_version>."""
    return f"{registry}/kube-apiserver:{target_version}" in describe_image_line

