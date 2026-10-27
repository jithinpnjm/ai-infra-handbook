"""Chapter 1.6 model: Linux numeric UID/GID identity, non-cumulative permission
evaluation (owner -> group -> other), octal modes and special bits (setuid 4000,
setgid 2000, sticky 1000), umask calculation, POSIX ACL mask capping, real/effective/
saved UID transitions, and cluster identity synchronization (SCL Ch. 11 & 12).
"""
from typing import Dict, List, Set, Tuple


def evaluate_posix_permission(
    proc_euid: int,
    proc_groups: Set[int],
    file_uid: int,
    file_gid: int,
    mode_octal: int,
    requested_bits: int,
) -> Dict[str, object]:
    """Evaluate classic Unix permissions in strict non-cumulative order: root -> owner -> group -> other."""
    if proc_euid == 0:
        matched_class = "root_superuser"
        effective_triple = 0o7 if (requested_bits & 0o1 == 0 or (mode_octal & 0o111) != 0) else 0o6
        allowed = (effective_triple & requested_bits) == requested_bits
        return {"allowed": allowed, "matched_class": matched_class, "triple_octal": effective_triple}

    if proc_euid == file_uid:
        matched_class = "user_owner"
        triple = (mode_octal >> 6) & 0o7
    elif file_gid in proc_groups:
        matched_class = "group"
        triple = (mode_octal >> 3) & 0o7
    else:
        matched_class = "other"
        triple = mode_octal & 0o7

    allowed = (triple & requested_bits) == requested_bits
    return {"allowed": allowed, "matched_class": matched_class, "triple_octal": triple}


def compute_default_mode_with_umask(is_directory: bool, umask_octal: int) -> int:
    """Compute default creation mode: (0o777 if directory else 0o666) & ~umask."""
    base = 0o777 if is_directory else 0o666
    return base & (~umask_octal & 0o777)


def evaluate_acl_effective_rights(entry_bits: int, mask_bits: int) -> int:
    """POSIX ACL mask caps the effective permissions of named users, named groups, and owning group."""
    return entry_bits & mask_bits


def simulate_setuid_exec(
    caller_ruid: int,
    binary_owner_uid: int,
    has_setuid_bit: bool,
) -> Dict[str, int]:
    """Model ruid, euid, and saved_uid when executing a binary with or without setuid (4000)."""
    euid = binary_owner_uid if has_setuid_bit else caller_ruid
    return {
        "ruid": caller_ruid,
        "euid": euid,
        "saved_uid": euid,
    }


def evaluate_sticky_directory_unlink(
    caller_euid: int,
    dir_uid: int,
    file_uid: int,
    dir_has_write_and_exec: bool,
    dir_has_sticky_bit: bool,
) -> bool:
    """Model whether caller can unlink a file in a directory (sticky bit 1000 restricts delete to root, dir owner, or file owner)."""
    if not dir_has_write_and_exec and caller_euid != 0:
        return False
    if not dir_has_sticky_bit or caller_euid == 0:
        return True
    return caller_euid in {dir_uid, file_uid}


def estimate_cluster_sync_duration(num_nodes: int, delay_sec: float = 0.1) -> Dict[str, object]:
    """Model SCL Ch. 11 staggered master-sync loop duration and NIS+ 30-40 client threshold."""
    if num_nodes < 0 or delay_sec < 0:
        raise ValueError("num_nodes and delay_sec must be non-negative")
    return {
        "num_nodes": num_nodes,
        "stagger_delay_sec": round(num_nodes * delay_sec, 2),
        "exceeds_single_nis_server_limit": num_nodes > 40,
    }
