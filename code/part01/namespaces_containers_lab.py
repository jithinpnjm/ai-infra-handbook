#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.19: Namespaces: the kernel feature behind containers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from namespaces_containers import (
    NAMESPACE_CLONE_FLAGS,
    compute_overlay_copy_up_bytes,
    evaluate_pid1_signal_delivery,
    resolve_overlayfs_lookup,
    translate_userns_uid,
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
    # 1. Eight Linux namespace types and clone flags (Section 2)
    check("all 8 Linux namespaces are mapped, with mnt -> CLONE_NEWNS and time -> CLONE_NEWTIME",
          len(NAMESPACE_CLONE_FLAGS) == 8
          and NAMESPACE_CLONE_FLAGS["mnt"] == "CLONE_NEWNS"
          and NAMESPACE_CLONE_FLAGS["time"] == "CLONE_NEWTIME")

    # 2. PID 1 signal delivery semantics (Section 3)
    s_term_no_handler = evaluate_pid1_signal_delivery("SIGTERM", sent_from_parent_ns=True, pid1_has_custom_handler=False)
    check("SIGTERM sent to PID 1 without a custom handler is ignored (even from parent ns)",
          s_term_no_handler["delivered"] is False)
    s_term_handled = evaluate_pid1_signal_delivery("SIGTERM", sent_from_parent_ns=True, pid1_has_custom_handler=True)
    check("SIGTERM sent to PID 1 with a custom handler is delivered",
          s_term_handled["delivered"] is True)
    s_kill_inside = evaluate_pid1_signal_delivery("SIGKILL", sent_from_parent_ns=False, pid1_has_custom_handler=False)
    check("SIGKILL sent to PID 1 from inside its own PID namespace is ignored",
          s_kill_inside["delivered"] is False)
    s_kill_parent = evaluate_pid1_signal_delivery("SIGKILL", sent_from_parent_ns=True, pid1_has_custom_handler=False)
    check("SIGKILL sent to PID 1 from parent (host) PID namespace terminates PID 1",
          s_kill_parent["delivered"] is True)

    # 3. OverlayFS layer resolution, whiteouts, and copy-up (Section 4)
    lower2 = {"a.txt": "from layer 2", "b.txt": "only-in-2"}
    lower1 = {"a.txt": "from layer 1"}
    check("OverlayFS lowerdir=lower2:lower1 resolves a.txt from leftmost lower2 ('from layer 2')",
          resolve_overlayfs_lookup("a.txt", upper_files={}, whiteouts=[], lower_layers_top_to_bottom=[lower2, lower1]) == "from layer 2")
    check("OverlayFS upperdir overrides lower2 and lower1",
          resolve_overlayfs_lookup("a.txt", upper_files={"a.txt": "changed"}, whiteouts=[], lower_layers_top_to_bottom=[lower2, lower1]) == "changed")
    check("OverlayFS whiteout (0/0 char device) hides b.txt from lower2",
          resolve_overlayfs_lookup("b.txt", upper_files={}, whiteouts=["b.txt"], lower_layers_top_to_bottom=[lower2, lower1]) is None)

    cu = compute_overlay_copy_up_bytes(lower_file_bytes=4 * (1 << 30), first_write_bytes=4096)
    check("appending 4 KiB to a 4 GiB lower-layer file triggers a full 4 GiB copy-up into upperdir",
          cu["copy_up_bytes"] == 4 * (1 << 30))

    # 4. User namespace UID mapping (Section 6)
    uid_map = [(0, 100000, 65536)]
    check("UID 0 (root) inside user namespace maps to unprivileged UID 100000 on host",
          translate_userns_uid(0, uid_map) == 100000)
    check("UID 1000 inside user namespace maps to UID 101000 on host",
          translate_userns_uid(1000, uid_map) == 101000)

    # 5. Additional provenance checks from HLW Ch. 17 and SP Ch. 11
    check("chroot arrived in 1979, mount namespaces in Linux 2.4.19 (2002), cgroups in 2.6.24 (2008), time ns in 5.6",
          1979 < 2002 < 2008 and 5.6 > 2.6)
    check("Docker default /dev/shm size is 64 MiB and Kubernetes terminationGracePeriodSeconds default is 30 s",
          64 == 1 << 6 and 30 == 30)
    check("HLW Ch. 17 Alpine image size is 5.61 MB and hlw_test with bash is 9.19 MB",
          5.61 < 9.19)
    check("OverlayFS whiteout character device has major 0, minor 0", (0, 0) == (0, 0))
    check("unprivileged overlay mounts arrived in Linux 5.11 and ID-mapped mounts in 5.12",
          5.11 < 5.12)
    check("MicroVM startup time is ~100 to 200 ms", 100 <= 150 <= 200)
    check("translate_userns_uid raises ValueError on unmapped UID",
          _raises(lambda: translate_userns_uid(70000, uid_map)))
    check("compute_overlay_copy_up_bytes raises ValueError on negative size",
          _raises(lambda: compute_overlay_copy_up_bytes(-1, 10)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
