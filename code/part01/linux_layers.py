"""Chapter 1.1 model: Linux system layers, privilege boundaries, process creation
(fork/clone + execve), distribution families, and GPU/RDMA stack placement.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 1:
  Three layers (hardware, kernel, user space), CPU privilege modes (kernel mode vs
  user mode), the kernel's four jobs (process management, memory management via MMU
  and page tables, device drivers and pseudodevices, system calls and support),
  fork()/clone() + exec()/execve() PID preservation, and UID 0 (root) vs CPU mode.
- Jason Edelman, Scott S. Lowe, and Matt Oswalt, Network Programmability and
  Automation, 2nd ed. (network-programmability-and-automation-2nd-edition), Chapter 3:
  Linux in network operating systems (OCP Open Network Linux ONL, Switch Light,
  dentOS, Debian-based Cumulus Linux, SONiC), GNU (1980s) + Linux (1991, GPL v0.99
  in 1992), Red Hat lineage (Fedora -> CentOS Stream -> RHEL -> AlmaLinux/Rocky/
  Amazon Linux; rpm -> yum -> dnf), and Debian/Ubuntu lineage (1993 Ian Murdock,
  1996 Buzz 1.1, 2021 Bullseye 11.0, Ubuntu 4.10 Warty Warthog Oct 2004, 6-month
  releases, 2-year / 5-year LTS; dpkg -> dselect -> apt).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 7:
  POSIX / Single UNIX Specification (The Open Group, 1993) and real/effective/saved
  UID/GID boundaries.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple


LAYER_BY_COMPONENT: Dict[str, str] = {
    "cpu_cores": "hardware",
    "main_memory_ram": "hardware",
    "nvme_drive": "hardware",
    "connectx_hca": "hardware",
    "gpu_silicon": "hardware",
    "process_scheduler": "kernel",
    "virtual_memory_manager": "kernel",
    "vfs_and_block_layer": "kernel",
    "tcp_ip_netfilter": "kernel",
    "nvidia.ko": "kernel",
    "nvidia_uvm.ko": "kernel",
    "nvidia_peermem.ko": "kernel",
    "mlx5_core.ko": "kernel",
    "ib_core.ko": "kernel",
    "glibc": "user_space",
    "libcuda.so": "user_space",
    "libnvidia-ml.so": "user_space",
    "libibverbs.so": "user_space",
    "systemd": "user_space",
    "slurmd": "user_space",
    "kubelet": "user_space",
    "containerd": "user_space",
    "pytorch_training_script": "user_space",
}


PSEUDODEVICES: Dict[str, str] = {
    "/dev/null": "discards all bytes written and returns EOF on read",
    "/dev/zero": "supplies an endless stream of zero bytes",
    "/dev/random": "kernel cryptographic random number generator",
    "/dev/urandom": "non-blocking kernel cryptographic random number generator",
}


PROC_STATE_MEANINGS: Dict[str, Tuple[str, bool]] = {
    "R": ("running or runnable on a run queue", True),
    "S": ("interruptible sleep waiting for an event", True),
    "D": ("uninterruptible sleep inside a kernel I/O path", False),
    "T": ("stopped by job-control signal or debugger", True),
    "Z": ("zombie: terminated, waiting for parent wait4()", False),
}


@dataclass(frozen=True)
class ProcessEvent:
    parent_pid: int
    child_pid: int
    program_before_exec: str
    program_after_exec: str
    uid: int
    cpu_mode_in_userspace: str


def classify_component_layer(component: str) -> str:
    """Return 'hardware', 'kernel', or 'user_space' for a known system component."""
    if component not in LAYER_BY_COMPONENT:
        raise ValueError(f"Unknown component: {component}")
    return LAYER_BY_COMPONENT[component]


def evaluate_privilege_boundary(uid: int, in_syscall: bool) -> Dict[str, object]:
    """Explain the difference between user identity (UID 0 root) and CPU mode (ring 0 vs ring 3)."""
    if uid < 0:
        raise ValueError("UID must be non-negative")
    cpu_ring = 0 if in_syscall else 3
    cpu_mode = "kernel_mode" if in_syscall else "user_mode"
    return {
        "uid": uid,
        "is_superuser": uid == 0,
        "cpu_ring": cpu_ring,
        "cpu_mode": cpu_mode,
        "can_execute_privileged_cpu_insn_directly": in_syscall,
        "kernel_grants_superuser_requests": uid == 0,
    }


def simulate_fork_and_exec(
    shell_pid: int,
    allocated_child_pid: int,
    shell_program: str,
    target_binary: str,
    uid: int = 1000,
) -> ProcessEvent:
    """Model fork()/clone() followed by exec()/execve(): child keeps its PID across execve()."""
    if shell_pid <= 0 or allocated_child_pid <= shell_pid:
        raise ValueError("Child PID must be positive and distinct from parent PID")
    return ProcessEvent(
        parent_pid=shell_pid,
        child_pid=allocated_child_pid,
        program_before_exec=shell_program,
        program_after_exec=target_binary,
        uid=uid,
        cpu_mode_in_userspace="user_mode",
    )


def VirtualAddressTranslation(virtual_addr: int, page_table: Dict[int, int], page_size: int = 4096) -> Dict[str, int]:
    """Translate a virtual address via a 4 KiB page table or raise FaultError on unmapped page."""
    if virtual_addr < 0 or page_size <= 0:
        raise ValueError("Invalid address or page size")
    vpn = virtual_addr // page_size
    offset = virtual_addr % page_size
    if vpn not in page_table:
        return {"page_fault": 1, "virtual_page": vpn, "offset": offset, "physical_addr": -1}
    pfn = page_table[vpn]
    return {
        "page_fault": 0,
        "virtual_page": vpn,
        "physical_frame": pfn,
        "offset": offset,
        "physical_addr": pfn * page_size + offset,
    }


def diagnose_process_signal_behavior(state_code: str) -> Dict[str, object]:
    """Explain whether SIGKILL (kill -9) takes immediate effect for a given ps STAT code."""
    code = state_code[:1].upper()
    if code not in PROC_STATE_MEANINGS:
        raise ValueError(f"Unknown process state: {state_code}")
    meaning, killable = PROC_STATE_MEANINGS[code]
    return {
        "state": code,
        "meaning": meaning,
        "sigkill_effective_immediately": killable,
    }


def check_distro_lineage(distro_name: str) -> Dict[str, str]:
    """Return family, package format, low-level tool, and high-level manager per NPA Ch. 3 & HLW Ch. 1."""
    table = {
        "rhel": ("Red Hat", "rpm", "rpm", "dnf"),
        "fedora": ("Red Hat", "rpm", "rpm", "dnf"),
        "rocky": ("Red Hat", "rpm", "rpm", "dnf"),
        "almalinux": ("Red Hat", "rpm", "rpm", "dnf"),
        "amazon_linux_2022": ("Red Hat", "rpm", "rpm", "dnf"),
        "debian": ("Debian", "deb", "dpkg", "apt"),
        "ubuntu": ("Debian", "deb", "dpkg", "apt"),
        "cumulus_linux": ("Debian", "deb", "dpkg", "apt"),
        "dgx_os": ("Debian", "deb", "dpkg", "apt"),
        "sles": ("SUSE", "rpm", "rpm", "zypper"),
    }
    key = distro_name.lower().strip()
    if key not in table:
        raise ValueError(f"Unknown distribution: {distro_name}")
    fam, fmt, low, high = table[key]
    return {
        "family": fam,
        "package_format": fmt,
        "low_level_tool": low,
        "high_level_manager": high,
    }


def verify_container_kernel_sharing(host_uname_r: str, container_uname_r: str, host_has_nvidia_ko: bool) -> Dict[str, bool]:
    """Containers share the host kernel; GPU access in a container requires the host kernel module."""
    same_kernel = host_uname_r == container_uname_r
    return {
        "shares_host_kernel": same_kernel,
        "container_gpu_usable": same_kernel and host_has_nvidia_ko,
    }
