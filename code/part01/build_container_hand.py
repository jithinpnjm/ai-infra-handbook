"""Chapter 1.20 model: Hand-built container assembly sequence (enter.sh pivot_root
ordering and preconditions), minimal /dev character device major/minor table,
cgroup v2 lab-ctr resource specification (cpu.max, memory.max, pids.max), and
veth + bridge + NAT network readiness validation.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 17
  (container concepts, overlayfs, Docker vs Podman, inspecting container processes).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 11 (namespaces, cgroups, container observability).
- nvidia-devops/volume-01/04-linux-systemd-containers-masterclass.md (unshare and
  OverlayFS container assembly lab).
"""
from typing import Dict, List, Tuple


MINIMAL_DEV_NODES: Dict[str, Tuple[str, int, int, str]] = {
    "dev/null": ("c", 1, 3, "0666"),
    "dev/zero": ("c", 1, 5, "0666"),
    "dev/urandom": ("c", 1, 9, "0666"),
    "dev/tty": ("c", 5, 0, "0666"),
}

ENTER_SH_STEPS: List[str] = [
    "1_mount_make_rprivate_root",
    "2_bind_mount_merged_to_itself",
    "3_mount_proc_sys_ro_dev_tmpfs",
    "4_mknod_minimal_dev_nodes",
    "5_pivot_root_to_merged_and_umount_oldroot",
    "6_set_hostname_and_exec_pid1",
]


def validate_pivot_root_preconditions(
    root_propagation_is_private: bool,
    new_root_is_mount_point: bool,
    put_old_inside_new_root: bool,
) -> Dict[str, object]:
    """Check kernel preconditions for pivot_root(new_root, put_old); returns EINVAL reasons if violated."""
    errors: List[str] = []
    if not root_propagation_is_private:
        errors.append("parent_mount_propagation_is_shared")
    if not new_root_is_mount_point:
        errors.append("new_root_is_not_a_mount_point")
    if not put_old_inside_new_root:
        errors.append("put_old_not_under_new_root")
    return {
        "valid": len(errors) == 0,
        "errno": None if len(errors) == 0 else "EINVAL",
        "errors": errors,
    }


def evaluate_lab_ctr_cgroup_limits(
    cpu_max_str: str = "50000 100000",
    memory_max_mib: int = 128,
    pids_max: int = 64,
) -> Dict[str, object]:
    """Parse the Step 5 /sys/fs/cgroup/lab-ctr resource limits."""
    q_str, p_str = cpu_max_str.strip().split()
    quota = int(q_str)
    period = int(p_str)
    return {
        "cpu_fraction": round(quota / float(period), 2),
        "memory_max_bytes": memory_max_mib * (1 << 20),
        "pids_max": pids_max,
    }


def validate_container_veth_nat_config(
    bridge_up_with_ip: bool,
    veth_peer_in_ctr_netns: bool,
    ctr_default_route_via_bridge: bool,
    ip_forward_enabled: bool,
    nat_masquerade_rule_present: bool,
) -> Dict[str, bool]:
    """Determine whether the container can reach the host bridge (10.77.0.1) and external internet (8.8.8.8)."""
    can_ping_bridge = bridge_up_with_ip and veth_peer_in_ctr_netns
    can_ping_internet = (
        can_ping_bridge
        and ctr_default_route_via_bridge
        and ip_forward_enabled
        and nat_masquerade_rule_present
    )
    return {
        "can_ping_host_bridge": can_ping_bridge,
        "can_ping_external_internet": can_ping_internet,
    }
