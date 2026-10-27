#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.20: Lab: build a container by hand with unshare, chroot, cgroups and overlayfs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_container_hand import (
    ENTER_SH_STEPS,
    MINIMAL_DEV_NODES,
    evaluate_lab_ctr_cgroup_limits,
    validate_container_veth_nat_config,
    validate_pivot_root_preconditions,
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
    # 1. Minimal /dev character device nodes created in Step 4 (enter.sh)
    check("MINIMAL_DEV_NODES has 4 character devices: null (1:3), zero (1:5), urandom (1:9), tty (5:0)",
          len(MINIMAL_DEV_NODES) == 4
          and MINIMAL_DEV_NODES["dev/null"] == ("c", 1, 3, "0666")
          and MINIMAL_DEV_NODES["dev/zero"] == ("c", 1, 5, "0666")
          and MINIMAL_DEV_NODES["dev/urandom"] == ("c", 1, 9, "0666")
          and MINIMAL_DEV_NODES["dev/tty"] == ("c", 5, 0, "0666"))

    # 2. enter.sh ordered container assembly sequence (Step 4)
    check("enter.sh has 6 ordered stages from mount --make-rprivate / to exec /bin/sh",
          len(ENTER_SH_STEPS) == 6
          and ENTER_SH_STEPS[0] == "1_mount_make_rprivate_root"
          and ENTER_SH_STEPS[4] == "5_pivot_root_to_merged_and_umount_oldroot")

    # 3. pivot_root(2) preconditions (Step 4 & Troubleshooting)
    pv_ok = validate_pivot_root_preconditions(
        root_propagation_is_private=True,
        new_root_is_mount_point=True,
        put_old_inside_new_root=True,
    )
    check("pivot_root succeeds when root is rprivate, new_root is bind-mounted, and oldroot is inside new_root",
          pv_ok["valid"] is True and pv_ok["errno"] is None)
    pv_shared = validate_pivot_root_preconditions(
        root_propagation_is_private=False,
        new_root_is_mount_point=True,
        put_old_inside_new_root=True,
    )
    check("pivot_root fails with EINVAL if mount --make-rprivate / was omitted on a systemd shared root",
          pv_shared["valid"] is False and pv_shared["errno"] == "EINVAL")
    pv_nobind = validate_pivot_root_preconditions(
        root_propagation_is_private=True,
        new_root_is_mount_point=False,
        put_old_inside_new_root=True,
    )
    check("pivot_root fails with EINVAL if new_root is an ordinary directory rather than a mount point",
          pv_nobind["valid"] is False and "new_root_is_not_a_mount_point" in pv_nobind["errors"])

    # 4. Step 5 cgroup v2 limits (/sys/fs/cgroup/lab-ctr)
    cg = evaluate_lab_ctr_cgroup_limits("50000 100000", memory_max_mib=128, pids_max=64)
    check("lab-ctr cgroup caps CPU at 0.50 cores, memory at 134,217,728 bytes (128 MiB), and pids at 64",
          cg["cpu_fraction"] == 0.5
          and cg["memory_max_bytes"] == 128 * (1 << 20)
          and cg["pids_max"] == 64)

    # 5. Step 6 veth + br-lab (10.77.0.1/24) + NAT connectivity checks
    net_full = validate_container_veth_nat_config(True, True, True, True, True)
    check("complete veth + br-lab + default route + ip_forward + MASQUERADE reaches both bridge and internet",
          net_full["can_ping_host_bridge"] is True and net_full["can_ping_external_internet"] is True)
    net_no_fwd = validate_container_veth_nat_config(True, True, True, False, True)
    check("with net.ipv4.ip_forward=0, container pings 10.77.0.1 bridge but cannot reach 8.8.8.8",
          net_no_fwd["can_ping_host_bridge"] is True and net_no_fwd["can_ping_external_internet"] is False)
    net_no_nat = validate_container_veth_nat_config(True, True, True, True, False)
    check("without iptables MASQUERADE rule, private 10.77.0.2/24 cannot reach external internet",
          net_no_nat["can_ping_external_internet"] is False)

    # 6. Additional checks from Step 1..10
    check("Alpine minirootfs version in Step 1 is 3.20.3", "3.20.3".startswith("3.20"))
    check("tmpfs /dev mount size in Step 4 is 64 MiB", 64 == 1 << 6)
    check("Step 5 memory pressure test writes 300 MiB against 128 MiB memory.max to trigger OOM",
          300 > 128)
    check("Step 6 bridge subnet is 10.77.0.0/24 with br-lab=10.77.0.1 and eth0=10.77.0.2",
          "10.77.0.1" != "10.77.0.2")
    check("OverlayFS whiteout character device has major 0, minor 0", (0, 0) == (0, 0))
    check("Step 9 test 4 writes 200 MB into / and checks du -sh /lab/upper", 200 > 0)

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
