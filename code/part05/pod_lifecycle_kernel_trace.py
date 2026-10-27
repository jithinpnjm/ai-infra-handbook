"""Chapter 5.8 model: Pod startup latency analyzer (`created -> scheduled ->
initialized -> ready` and `kubelet_pod_start_sli_duration_seconds` excluding
image pull), `pause` sandbox vs application container `/proc/<pid>/ns` inode
sharing verifier (`NK` Ch. 3 & 4, `PK` Ch. 3 & 5), and cgroup v2 GPU device
allow-list verifier.

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 5.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapters 3 & 5.
- James Strong & Vallery Lancey, Networking and Kubernetes (networking-and-
  kubernetes, NK), Chapters 3 & 4 (container network namespaces, `veth` pairs,
  `/proc/$PID/ns/net` -> `/var/run/netns`, CNI `ADD`/`DEL` IPAM JSON, `readinessGates`).
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition, HLW),
  Chapter 17 ("Virtualization" — VMs vs containers, overlayfs, namespaces, cgroups).
"""
from typing import Dict, List, Mapping, Sequence, Set, Tuple


def compute_pod_startup_intervals(
    *,
    created_sec: float,
    scheduled_sec: float,
    initialized_sec: float,
    containers_ready_sec: float,
    ready_sec: float,
    image_pull_duration_sec: float,
) -> Dict[str, float]:
    """Model Section 8 Pod startup latency intervals and
    `kubelet_pod_start_sli_duration_seconds` (which measures scheduled ->
    containers_ready minus image pull duration).
    """
    sched_delay = round(scheduled_sec - created_sec, 3)
    init_delay = round(initialized_sec - scheduled_sec, 3)
    start_delay = round(containers_ready_sec - initialized_sec, 3)
    readiness_delay = round(ready_sec - containers_ready_sec, 3)
    total_start = round(ready_sec - created_sec, 3)
    sli_duration = round(max(0.0, (containers_ready_sec - scheduled_sec) - image_pull_duration_sec), 3)
    return {
        "scheduling_sec": sched_delay,
        "initialization_sec": init_delay,
        "container_start_sec": start_delay,
        "readiness_probe_sec": readiness_delay,
        "total_to_ready_sec": total_start,
        "pod_start_sli_sec": sli_duration,
    }


def verify_pod_namespace_inodes(
    pause_ns_inodes: Mapping[str, int],
    app_ns_inodes: Mapping[str, int],
    share_process_namespace: bool = False,
) -> Tuple[bool, List[str]]:
    """Model Section 4 & 5 `/proc/<pid>/ns` comparison between the `pause`
    sandbox container and an application container:
    - `net`, `ipc`, `uts`, `cgroup` MUST match `pause`.
    - `mnt` MUST differ from `pause` (each container has its own rootfs overlay).
    - `pid` matches `pause` ONLY when `shareProcessNamespace: true`, else differs.
    """
    errors: List[str] = []
    for shared_ns in ("net", "ipc", "uts", "cgroup"):
        if pause_ns_inodes.get(shared_ns) != app_ns_inodes.get(shared_ns):
            errors.append(f"namespace {shared_ns!r} inode mismatch with pause sandbox")
    if pause_ns_inodes.get("mnt") == app_ns_inodes.get("mnt"):
        errors.append("mount ('mnt') namespace must be isolated per container")
    pid_same = pause_ns_inodes.get("pid") == app_ns_inodes.get("pid")
    if share_process_namespace and not pid_same:
        errors.append("shareProcessNamespace=True requires shared 'pid' namespace with pause")
    elif not share_process_namespace and pid_same:
        errors.append("shareProcessNamespace=False requires isolated 'pid' namespace per container")
    return (len(errors) == 0), errors


def verify_gpu_cgroup_device_isolation(
    allocated_gpu_indices: Sequence[int],
    container_dev_nodes: Set[str],
    cgroup_allowed_devices: Set[str],
) -> Tuple[bool, List[str]]:
    """Model Section 5 GPU isolation: container must only receive device nodes
    and cgroup eBPF allow-list entries for its allocated GPU indices (plus
    control devices `/dev/nvidiactl` and `/dev/nvidia-uvm`).
    """
    expected_devs = {f"/dev/nvidia{i}" for i in allocated_gpu_indices} | {
        "/dev/nvidiactl",
        "/dev/nvidia-uvm",
    }
    errors: List[str] = []
    if container_dev_nodes != expected_devs:
        errors.append(f"container /dev nodes {sorted(container_dev_nodes)} != expected {sorted(expected_devs)}")
    if cgroup_allowed_devices != expected_devs:
        errors.append(f"cgroup device allow-list {sorted(cgroup_allowed_devices)} != expected {sorted(expected_devs)}")
    return (len(errors) == 0), errors
