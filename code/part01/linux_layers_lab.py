#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.1: The Linux big picture."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from linux_layers import (
    PSEUDODEVICES,
    VirtualAddressTranslation,
    check_distro_lineage,
    classify_component_layer,
    diagnose_process_signal_behavior,
    evaluate_privilege_boundary,
    simulate_fork_and_exec,
    verify_container_kernel_sharing,
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
    # 1. Three-layer classification (HLW Ch. 1)
    check("CPU cores belong to hardware layer", classify_component_layer("cpu_cores") == "hardware")
    check("Main memory (RAM) belongs to hardware layer", classify_component_layer("main_memory_ram") == "hardware")
    check("ConnectX HCA belongs to hardware layer", classify_component_layer("connectx_hca") == "hardware")
    check("nvidia.ko runs in kernel space", classify_component_layer("nvidia.ko") == "kernel")
    check("nvidia_uvm.ko runs in kernel space", classify_component_layer("nvidia_uvm.ko") == "kernel")
    check("mlx5_core.ko runs in kernel space", classify_component_layer("mlx5_core.ko") == "kernel")
    check("libcuda.so runs in user space", classify_component_layer("libcuda.so") == "user_space")
    check("libnvidia-ml.so runs in user space", classify_component_layer("libnvidia-ml.so") == "user_space")
    check("libibverbs.so runs in user space", classify_component_layer("libibverbs.so") == "user_space")
    check("systemd (PID 1) runs in user space", classify_component_layer("systemd") == "user_space")
    check("slurmd and kubelet run in user space", classify_component_layer("slurmd") == "user_space" and classify_component_layer("kubelet") == "user_space")

    # 2. Privilege boundary: root UID 0 vs CPU mode (HLW Ch. 1, SCL Ch. 7)
    root_user_mode = evaluate_privilege_boundary(uid=0, in_syscall=False)
    check("root (UID 0) outside a syscall still runs in unprivileged CPU user_mode (ring 3)",
          root_user_mode["is_superuser"] is True and root_user_mode["cpu_mode"] == "user_mode" and root_user_mode["cpu_ring"] == 3)
    check("root in user mode cannot execute privileged CPU instructions directly without a syscall",
          root_user_mode["can_execute_privileged_cpu_insn_directly"] is False)
    normal_in_syscall = evaluate_privilege_boundary(uid=1000, in_syscall=True)
    check("ordinary user (UID 1000) enters kernel_mode (ring 0) during a system call",
          normal_in_syscall["is_superuser"] is False and normal_in_syscall["cpu_mode"] == "kernel_mode" and normal_in_syscall["cpu_ring"] == 0)

    # 3. fork()/clone() + exec()/execve() process creation (HLW Ch. 1)
    ev = simulate_fork_and_exec(shell_pid=100, allocated_child_pid=101, shell_program="/bin/bash", target_binary="/usr/bin/ls")
    check("fork/clone allocates child PID 101 from parent bash PID 100", ev.parent_pid == 100 and ev.child_pid == 101)
    check("execve replaces bash with /usr/bin/ls while preserving child PID 101",
          ev.program_before_exec == "/bin/bash" and ev.program_after_exec == "/usr/bin/ls" and ev.child_pid == 101)

    # 4. Virtual memory 4 KiB page translation and page fault (HLW Ch. 1)
    pt = {2: 15, 3: 9}
    vaddr_hit = 8320  # 2 * 4096 + 128
    vaddr_miss = 28736  # 7 * 4096 + 64
    hit = VirtualAddressTranslation(vaddr_hit, pt, page_size=4096)
    check("MMU translates mapped 4 KiB virtual address 8320 (page 2 + offset 128) to physical frame 15 (61568)",
          vaddr_hit == 2 * 4096 + 128 and hit["page_fault"] == 0 and hit["physical_addr"] == 61568)
    miss = VirtualAddressTranslation(vaddr_miss, pt, page_size=4096)
    check("unmapped virtual address 28736 (page 7 + offset 64) raises a hardware page fault to the kernel",
          vaddr_miss == 7 * 4096 + 64 and miss["page_fault"] == 1 and miss["physical_addr"] == -1)

    # 5. Pseudodevices (HLW Ch. 1)
    check("all four classic kernel pseudodevices are present (/dev/null, /dev/zero, /dev/random, /dev/urandom)",
          set(PSEUDODEVICES.keys()) == {"/dev/null", "/dev/zero", "/dev/random", "/dev/urandom"})

    # 6. Process states and state D / Z behavior (HLW Ch. 1)
    st_r = diagnose_process_signal_behavior("R")
    st_d = diagnose_process_signal_behavior("D")
    st_z = diagnose_process_signal_behavior("Z")
    check("running process (state R) responds to SIGKILL", st_r["sigkill_effective_immediately"] is True)
    check("uninterruptible I/O sleep (state D) ignores SIGKILL until kernel I/O returns", st_d["sigkill_effective_immediately"] is False)
    check("zombie process (state Z) is already dead and awaits parent wait4()", st_z["sigkill_effective_immediately"] is False)

    # 7. Distribution lineages and network OSes (NPA Ch. 3)
    rhel = check_distro_lineage("rhel")
    rocky = check_distro_lineage("rocky")
    ubuntu = check_distro_lineage("ubuntu")
    cumulus = check_distro_lineage("cumulus_linux")
    dgx = check_distro_lineage("dgx_os")
    check("RHEL and Rocky Linux use rpm packages and dnf", rhel["package_format"] == "rpm" and rocky["high_level_manager"] == "dnf")
    check("Ubuntu, Cumulus Linux, and DGX OS use deb packages and apt",
          ubuntu["package_format"] == "deb" and cumulus["family"] == "Debian" and dgx["high_level_manager"] == "apt")

    # 8. Container kernel sharing on GPU nodes (HLW Ch. 1)
    ok_ctr = verify_container_kernel_sharing("6.8.0-1020-gcp", "6.8.0-1020-gcp", host_has_nvidia_ko=True)
    missing_kmod = verify_container_kernel_sharing("6.8.0-1020-gcp", "6.8.0-1020-gcp", host_has_nvidia_ko=False)
    check("container shares host kernel release 6.8.0-1020-gcp and sees GPUs when host loads nvidia.ko",
          ok_ctr["shares_host_kernel"] is True and ok_ctr["container_gpu_usable"] is True)
    check("container cannot use GPU if host kernel lacks matching nvidia.ko module",
          missing_kmod["container_gpu_usable"] is False)

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
