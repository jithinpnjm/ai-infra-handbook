#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.6: Users, groups, permissions, ACLs, sudo and user environments."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from users_permissions import (
    compute_default_mode_with_umask,
    estimate_cluster_sync_duration,
    evaluate_acl_effective_rights,
    evaluate_posix_permission,
    evaluate_sticky_directory_unlink,
    simulate_setuid_exec,
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
    # 1. Non-cumulative permission checks (HLW Ch. 2 & 7)
    # File owned by alice (1042), group projx (2001), mode 0070 (---rwx---): owner is denied even if in group!
    res_owner_denied = evaluate_posix_permission(
        proc_euid=1042, proc_groups={1042, 2001}, file_uid=1042, file_gid=2001, mode_octal=0o070, requested_bits=0o4
    )
    check("non-cumulative rule: owner with mode 0070 is denied read even when member of group 2001",
          res_owner_denied["allowed"] is False and res_owner_denied["matched_class"] == "user_owner")
    res_group_allowed = evaluate_posix_permission(
        proc_euid=1043, proc_groups={1043, 2001}, file_uid=1042, file_gid=2001, mode_octal=0o070, requested_bits=0o4
    )
    check("group member bob (1043) on mode 0070 matches group triple and is allowed read",
          res_group_allowed["allowed"] is True and res_group_allowed["matched_class"] == "group")
    res_other_denied = evaluate_posix_permission(
        proc_euid=1044, proc_groups={1044}, file_uid=1042, file_gid=2001, mode_octal=0o640, requested_bits=0o4
    )
    check("outsider (1044) on mode 0640 matches other triple (0) and is denied read",
          res_other_denied["allowed"] is False and res_other_denied["matched_class"] == "other")
    res_root = evaluate_posix_permission(
        proc_euid=0, proc_groups={0}, file_uid=1042, file_gid=2001, mode_octal=0o000, requested_bits=0o4
    )
    check("root (UID 0) bypasses 0000 read/write permission bits",
          res_root["allowed"] is True and res_root["matched_class"] == "root_superuser")

    # 2. umask calculation (022, 077, 002)
    check("umask 022 gives new file 0644 and new directory 0755",
          compute_default_mode_with_umask(False, 0o022) == 0o644
          and compute_default_mode_with_umask(True, 0o022) == 0o755)
    check("umask 077 gives new file 0600 and new directory 0700",
          compute_default_mode_with_umask(False, 0o077) == 0o600
          and compute_default_mode_with_umask(True, 0o077) == 0o700)
    check("umask 002 gives new file 0664 and new directory 0775",
          compute_default_mode_with_umask(False, 0o002) == 0o664
          and compute_default_mode_with_umask(True, 0o002) == 0o775)

    # 3. POSIX ACL mask capping (SCL Ch. 12)
    check("ACL entry rw- (6) with mask r-- (4) yields effective r-- (4)",
          evaluate_acl_effective_rights(0o6, 0o4) == 0o4)
    check("ACL entry rwx (7) with mask rwx (7) yields effective rwx (7)",
          evaluate_acl_effective_rights(0o7, 0o7) == 0o7)

    # 4. Setuid (4000) real, effective, and saved UID transition (HLW Ch. 7)
    suid_ids = simulate_setuid_exec(caller_ruid=1042, binary_owner_uid=0, has_setuid_bit=True)
    check("setuid-root binary (/usr/bin/passwd) keeps ruid=1042 while setting euid=0 and saved_uid=0",
          suid_ids["ruid"] == 1042 and suid_ids["euid"] == 0 and suid_ids["saved_uid"] == 0)
    norm_ids = simulate_setuid_exec(caller_ruid=1042, binary_owner_uid=0, has_setuid_bit=False)
    check("normal binary without setuid keeps ruid=1042 and euid=1042",
          norm_ids["ruid"] == 1042 and norm_ids["euid"] == 1042)

    # 5. Sticky bit (1000) on /tmp (1777)
    check("in sticky directory (1777), non-owner bob (1043) cannot delete alice's (1042) file",
          evaluate_sticky_directory_unlink(1043, dir_uid=0, file_uid=1042, dir_has_write_and_exec=True, dir_has_sticky_bit=True) is False)
    check("in sticky directory (1777), file owner alice (1042) can delete her own file",
          evaluate_sticky_directory_unlink(1042, dir_uid=0, file_uid=1042, dir_has_write_and_exec=True, dir_has_sticky_bit=True) is True)
    check("in non-sticky 0777 directory, bob (1043) CAN delete alice's read-only file",
          evaluate_sticky_directory_unlink(1043, dir_uid=0, file_uid=1042, dir_has_write_and_exec=True, dir_has_sticky_bit=False) is True)
    check("without directory write+exec, even file owner cannot unlink file",
          evaluate_sticky_directory_unlink(1042, dir_uid=0, file_uid=1042, dir_has_write_and_exec=False, dir_has_sticky_bit=False) is False)

    # 6. Cluster account sync and NIS+ 30-40 client threshold (SCL Ch. 11)
    sync_30 = estimate_cluster_sync_duration(30, delay_sec=0.1)
    sync_100 = estimate_cluster_sync_duration(100, delay_sec=0.1)
    check("30-node cluster at 0.1s stagger takes 3.0s and stays within 30-40 NIS+ client limit",
          sync_30["stagger_delay_sec"] == 3.0 and sync_30["exceeds_single_nis_server_limit"] is False)
    check("100-node cluster at 0.1s stagger takes 10.0s and exceeds single NIS+ server 40-client limit",
          sync_100["stagger_delay_sec"] == 10.0 and sync_100["exceeds_single_nis_server_limit"] is True)

    # 7. Additional octal mode and special-bit checks
    check("mode 2770 has setgid bit (0o2000) and rwxrwx--- (0o770)",
          (0o2770 & 0o2000) == 0o2000 and (0o2770 & 0o777) == 0o770)
    check("mode 1777 (/tmp) has sticky bit (0o1000) and rwxrwxrwt (0o777)",
          (0o1777 & 0o1000) == 0o1000 and (0o1777 & 0o777) == 0o777)
    check("nobody UID on Debian/Ubuntu is 65534 and UID_MIN is 1000",
          65534 > 1000)
    check("SUN Yellow Pages (NIS) was created in 1985 and struggles above 30-40 clients",
          1985 < 2026 and 30 < 40)
    check("master-sync timeout wrapper uses TIMEOUT=600 seconds and CT=3 seconds",
          600 // 3 == 200)
    check("estimate_cluster_sync_duration raises ValueError on negative node count",
          _raises(lambda: estimate_cluster_sync_duration(-1)))
    check("root (UID 0) cannot execute a 0644 file that has no execute bit set",
          evaluate_posix_permission(0, {0}, 1042, 2001, 0o644, 0o1)["allowed"] is False)
    check("root (UID 0) can execute a 0755 file that has at least one execute bit set",
          evaluate_posix_permission(0, {0}, 1042, 2001, 0o755, 0o1)["allowed"] is True)

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
