"""Chapter 5.2 model: CRI (`RuntimeService` + `ImageService`) pod sandbox and
container lifecycle simulator (including `containerd` daemon restart survival via
`containerd-shim-runc-v2`), `kubelet` vs `containerd` `SystemdCgroup` validator,
and `RuntimeClass` `overhead.podFixed` resource accounting.

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 3 ("Container Runtime"):
  * History of `dockershim` / `rktnetes` -> Container Runtime Interface (`CRI`
    gRPC `ImageService` and `RuntimeService` over Unix socket).
  * `containerd` (`/run/containerd/containerd.sock`, `ctr --namespace k8s.io`)
    vs `CRI-O` (`/var/run/crio/crio.sock`, `conmon`), `pause` sandbox container,
    CNI attachment during `RunPodSandbox`, and `runc` vs `Kata Containers`
    (`qemu-system-x86_64 -machine pc,accel=kvm`) vs `gVisor` (`runsc`) selected
    via `RuntimeClass`.
"""
from typing import Any, Dict, List, Mapping, Set, Tuple


class CRIRuntimeSimulator:
    """Model Section 1 & 2 CRI pod sandbox + container lifecycle and shim survival."""

    def __init__(self, configured_runtimes: Set[str], sandbox_image: str = "registry.k8s.io/pause:3.9") -> None:
        self.configured_runtimes = set(configured_runtimes)
        self.sandbox_image = sandbox_image
        self.pulled_images: Set[str] = {sandbox_image}
        self.sandboxes: Dict[str, Dict[str, Any]] = {}
        self.containers: Dict[str, Dict[str, Any]] = {}
        self.daemon_restarts = 0

    def run_pod_sandbox(self, pod_uid: str, pod_name: str, runtime_handler: str = "runc", cni_ok: bool = True) -> str:
        if runtime_handler not in self.configured_runtimes:
            raise KeyError(f"RuntimeClass handler {runtime_handler!r} not in containerd runtimes {sorted(self.configured_runtimes)}")
        if not cni_ok:
            raise RuntimeError("RunPodSandbox failed: failed to set up sandbox container network (CNI error)")
        sb_id = f"sb-{pod_uid}"
        self.sandboxes[sb_id] = {
            "pod_name": pod_name,
            "runtime_handler": runtime_handler,
            "pause_pid": 1000 + len(self.sandboxes),
            "shim_alive": True,
            "netns_ip": f"10.244.1.{10 + len(self.sandboxes)}",
        }
        return sb_id

    def create_and_start_container(self, sb_id: str, ctr_name: str, image: str) -> str:
        if sb_id not in self.sandboxes:
            raise KeyError(f"sandbox {sb_id!r} does not exist")
        self.pulled_images.add(image)
        ctr_id = f"{sb_id}-{ctr_name}"
        self.containers[ctr_id] = {
            "sandbox_id": sb_id,
            "name": ctr_name,
            "image": image,
            "state": "TASK_RUNNING",
        }
        return ctr_id

    def restart_containerd_daemon(self) -> Dict[str, int]:
        """Restarting `containerd` leaves `containerd-shim-runc-v2` processes and
        running containers alive; containerd reattaches to active shims on startup.
        """
        self.daemon_restarts += 1
        running = sum(1 for c in self.containers.values() if c["state"] == "TASK_RUNNING")
        return {"daemon_restarts": self.daemon_restarts, "running_containers": running}


def validate_cgroup_and_runtime_class(
    *,
    kubelet_cgroup_driver: str,
    containerd_systemd_cgroup: bool,
    runtime_class_handler: str,
    containerd_runtimes: Mapping[str, str],
    pod_cpu_request_m: int,
    pod_mem_request_mi: int,
    overhead_cpu_m: int = 0,
    overhead_mem_mi: int = 0,
) -> Tuple[bool, List[str], Dict[str, int]]:
    """Validate cgroup driver match (`systemd` <-> `SystemdCgroup = true`),
    `RuntimeClass.handler` registration, and effective pod resource request with
    `overhead.podFixed`.
    """
    errors: List[str] = []
    expected_systemd = kubelet_cgroup_driver == "systemd"
    if containerd_systemd_cgroup != expected_systemd:
        errors.append(
            f"cgroup driver mismatch: kubelet={kubelet_cgroup_driver!r} vs containerd SystemdCgroup={containerd_systemd_cgroup}"
        )
    if runtime_class_handler not in containerd_runtimes:
        errors.append(f"RuntimeClass handler {runtime_class_handler!r} missing from containerd runtimes")

    effective = {
        "effective_cpu_m": pod_cpu_request_m + overhead_cpu_m,
        "effective_mem_mi": pod_mem_request_mi + overhead_mem_mi,
    }
    return (len(errors) == 0), errors, effective
