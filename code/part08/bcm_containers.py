#!/usr/bin/env python3
"""Container runtime, Docker, registry and Enroot rules around BCM, as small testable pieces.

Sources: BCM 11 Containerization Manual chapters 1 to 3 and 4.21; Administrator Manual 7.3.3 (Enroot, Pyxis); the HPC sysadmin book chapter 16; the
NVIDIA-DevOps notes (volume 10 chapter 8, for Enroot credentials and Pyxis sbatch quoting). Not BCM. Where a source is silent the code says so.
"""
import re

class CtrError(ValueError):
    pass

# ---- which runtime for which job -----------------------------------------------------------------------------------------
RUNTIMES = {
    "docker": {"daemon": True, "root_daemon": True, "slurm_integration_in_bcm": False, "multi_host": "no (Swarm not supported; use Kubernetes)",
               "set_up_by": "cm-docker-setup (DockerHost role)"},
    "kubernetes (containerd)": {"daemon": True, "root_daemon": True, "slurm_integration_in_bcm": False, "multi_host": "yes",
                                "set_up_by": "cm-kubernetes-setup"},
    "enroot+pyxis": {"daemon": False, "root_daemon": False, "slurm_integration_in_bcm": True, "multi_host": "through Slurm",
                     "set_up_by": "cm-wlm-setup --with-pyxis"},
    "apptainer": {"daemon": False, "root_daemon": False, "slurm_integration_in_bcm": False, "multi_host": "through Slurm (srun)",
                  "set_up_by": "not covered by the BCM manuals read: install it in the software image yourself"},
}

def choose_runtime(need_slurm_jobs, need_k8s_services, users_unprivileged=True, want_bcm_support=True):
    """A judgment table, not a manual rule. Slurm batch jobs: Enroot+Pyxis (BCM-integrated). Long-running services: Kubernetes. Docker directly means
    being root on the host, so it is for administrators and registry hosts, not users."""
    out = []
    if need_slurm_jobs:
        out.append("enroot+pyxis" if want_bcm_support else "apptainer")
    if need_k8s_services:
        out.append("kubernetes (containerd)")
    if not out:
        out.append("docker")
    return out

# ---- Docker host role -------------------------------------------------------------------------------------------------------
DOCKER_DEFAULTS = {"spool": "/var/lib/docker", "tmp dir": "$spool/tmp", "enable selinux": True, "log level": "info", "mtu": 0,
                   "api sockets": "unix:///var/run/docker.sock", "iptables": True, "enable tls": False, "verify tls": False,
                   "certificates path": "/etc/docker", "storage backend": "overlay2", "runtime": "runc"}

def docker_role_problems(p):
    """Docker::Host role parameter checks from the manual's table 2.1."""
    q = []
    if p.get("storage backend", "overlay2") != "overlay2":
        q.append("the only storage backend BCM offers is overlay2")
    if p.get("enable tls") or p.get("verify tls"):
        for k in ("tls ca", "tls certificate", "tls key"):
            if not p.get(k):
                q.append(f"TLS is on but '{k}' is not set")
    if p.get("verify tls") and not p.get("tls ca"):
        q.append("verify TLS trusts only certificates signed by the TLS CA: set it")
    if p.get("user namespace remap") and not p.get("kernel option user_namespace.enable=1"):
        q.append("user namespace remap needs user_namespace.enable=1 in the kernel options of those nodes, and a reboot")
    if p.get("log level", "info") not in ("fatal", "error", "warn", "info", "debug"):
        q.append("log level is fatal, error, warn, info or debug")
    return q

def docker_swarm_supported():
    return False

def docker_available_to(user):
    """After setup only the administrator can run docker; regular users are meant to use Kubernetes for containers."""
    return user == "root"

# ---- registries ----------------------------------------------------------------------------------------------------------------
HARBOR_UI_PORT = 9443
KEYCLOAK_PORTS = (9443, 9999)
REGISTRY_DEFAULT_PORT = 5000

def port_conflicts(services):
    """services: {name: [ports]} on one node. Returns ports claimed twice. The manual puts the Harbor UI on the head node at 9443 and Keycloak
    also needs 9443 and 9999 free on the head node."""
    seen, out = {}, []
    for name, ports in services.items():
        for p in ports:
            if p in seen:
                out.append((p, seen[p], name))
            seen[p] = name
    return out

def registry_problems(kind, node_is_head=False, port_opened_on_head=False, password="Harbor12345", datanode=True, as_hub_proxy=False, mirror_url=None):
    q = []
    if kind not in ("docker-registry", "harbor"):
        raise CtrError("registry kind is docker-registry or harbor")
    if kind == "harbor":
        if password == "Harbor12345":
            q.append("Harbor still has its default admin password Harbor12345: change it after the first login")
        if node_is_head and not port_opened_on_head:
            q.append("Harbor on the head node is not reachable from outside until the port (9443) is opened on the head node")
    if not datanode:
        q.append("the registry node lacks the datanode protection: a reprovision could wipe the registry, and its images cannot be restored")
    if as_hub_proxy and kind != "docker-registry":
        q.append("pull-through caching for Docker Hub is a Docker Registry mode, not Harbor's (as the manual describes it)")
    if as_hub_proxy and mirror_url and not re.search(r":\d+", mirror_url):
        q.append("the proxy mirror URL must include the port, for example https://node001:5000")
    return q

DOCKERHUB_RATE_LIMIT_REMEDIES = ["authenticate pulls with a personal Docker Hub account (higher allowance)", "Pro, Team or Business account (unlimited pulls)",
                                 "Docker Registry as a caching proxy mirror for connected clusters", "Skopeo to manage images on air-gapped clusters"]

def harbor_pull_secret(server, user):
    """4.21: Kubernetes pods that pull from Harbor need a docker-registry secret referenced as imagePullSecrets."""
    return f"kubectl create secret docker-registry myregistrykey --docker-server={server} --docker-username={user} --docker-password=<password>"

# ---- Enroot, Pyxis, Apptainer ------------------------------------------------------------------------------------------------
def enroot_credentials_problems(netrc_text, uses_ngc=True, uses_dockerhub=False):
    """Notes (volume 10 ch 8, from the Enroot docs): NGC needs BOTH nvcr.io and authn.nvidia.com entries with login $oauthtoken; Docker Hub is
    registry-1.docker.io. The file should be mode 600 (not checked here)."""
    machines = set(re.findall(r"^\s*machine\s+(\S+)", netrc_text, re.M))
    q = []
    if uses_ngc:
        for m in ("nvcr.io", "authn.nvidia.com"):
            if m not in machines:
                q.append(f"NGC needs a 'machine {m}' entry")
        if uses_ngc and "$oauthtoken" not in netrc_text:
            q.append("the NGC login name is the literal $oauthtoken")
    if uses_dockerhub and "registry-1.docker.io" not in machines:
        q.append("Docker Hub needs a 'machine registry-1.docker.io' entry")
    return q

def sbatch_container_image(image):
    """In an #SBATCH line the # that separates registry and image starts a comment: escape it (Pyxis README, via the notes)."""
    return image.replace("#", "\\#")

def image_distribution(nodes_in_job):
    """Judgment from the notes: import once to shared storage and reference the .sqsh path for jobs larger than a few nodes."""
    return "import once to shared storage, reference the .sqsh path" if nodes_in_job > 4 else "a registry URI is fine"

def apptainer_gpu_command(image, command, gpus=True):
    """`apptainer exec --nv` exposes NVIDIA GPUs (the notes' job example). The HPC book says NVIDIA GPUs need nvidia-container-toolkit on the node.
    Under Slurm the book recommends srun rather than mpirun."""
    return f"apptainer exec {'--nv ' if gpus else ''}{image} {command}"

def apptainer_on_bcm_steps():
    return ["install Apptainer in the software image (cm-chroot-sw-img, chapter 8.4) or on /cm/shared with a module file",
            "install cm-nvidia-container-toolkit so GPUs can be exposed",
            "imageupdate or reboot the nodes",
            "put .sif files on shared storage; launch with srun, not mpirun",
            "own the support: BCM's manuals do not cover Apptainer"]
