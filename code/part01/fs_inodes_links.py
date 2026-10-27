"""Chapter 1.3 model: Filesystem Hierarchy Standard (FHS), file types, inodes,
directory link counts, hard vs symbolic links, deleted-but-open files, and timestamps.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 2
  (sections 2.4, 2.5.5, 2.5.6, 2.17.2, 2.18, 2.19 FHS) and Chapter 4 (section 4.5
  inode and directory internals, VFAT lack of hard links).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 7 (file naming,
  extensions, directory tree commands, tar/gzip).
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


FHS_DIRECTORIES: Dict[str, str] = {
    "/etc": "system-wide plain-text configuration files",
    "/var/log": "variable system and service log files",
    "/run": "volatile runtime data since boot (PID files, sockets)",
    "/dev": "character and block device nodes",
    "/proc": "virtual filesystem exposing kernel process and system state",
    "/sys": "virtual filesystem exposing devices, drivers, and kernel objects",
    "/boot": "kernel image (vmlinuz), initramfs, and bootloader files",
    "/usr/include": "header files used by the C compiler",
    "/usr/local": "administrator-installed local software mirroring /usr",
    "/usr/share": "architecture-independent shared data and documentation",
    "/lib/modules": "loadable kernel modules (.ko) organized by uname -r",
}


FILE_TYPE_CHARS: Dict[str, str] = {
    "-": "regular file",
    "d": "directory",
    "l": "symbolic link",
    "c": "character device",
    "b": "block device",
    "s": "local domain socket",
    "p": "named pipe (FIFO)",
}


@dataclass
class InodeState:
    inode_number: int
    device_id: int
    size_bytes: int
    link_count: int
    open_fd_count: int
    mtime: int
    ctime: int
    atime: int


def compute_directory_link_count(num_subdirectories: int) -> int:
    """An empty directory has link count 2 ('name' in parent + '.' in itself); each subdir adds 1 via '..'."""
    if num_subdirectories < 0:
        raise ValueError("num_subdirectories must be non-negative")
    return 2 + num_subdirectories


def simulate_hard_link(inode: InodeState, target_device_id: int, fs_type: str = "ext4") -> Tuple[bool, str]:
    """Attempt to create a hard link to an inode; check cross-device EXDEV and VFAT limitation."""
    if fs_type.lower() in {"vfat", "msdos", "fat32"}:
        return False, "EPERM: VFAT directory structure does not support Unix hard links"
    if inode.device_id != target_device_id:
        return False, "EXDEV: Invalid cross-device link"
    inode.link_count += 1
    inode.ctime += 1
    return True, "ok"


def simulate_unlink(inode: InodeState) -> Dict[str, object]:
    """Model unlink(2) / rm: blocks are freed only when link_count == 0 AND open_fd_count == 0."""
    if inode.link_count <= 0:
        raise ValueError("Cannot unlink an inode with link_count <= 0")
    inode.link_count -= 1
    inode.ctime += 1
    blocks_freed = inode.link_count == 0 and inode.open_fd_count == 0
    retained_bytes = 0 if blocks_freed else inode.size_bytes
    return {
        "link_count": inode.link_count,
        "open_fd_count": inode.open_fd_count,
        "blocks_freed": blocks_freed,
        "retained_bytes": retained_bytes,
        "visible_in_lsof_plus_L1": inode.link_count == 0 and inode.open_fd_count > 0,
    }


def evaluate_timestamps_on_operation(inode: InodeState, op: str, relatime: bool = True) -> InodeState:
    """Update mtime, ctime, and atime according to POSIX/Linux rules."""
    if op == "write_content":
        inode.mtime += 10
        inode.ctime += 10
    elif op in {"chmod", "chown", "link", "unlink"}:
        inode.ctime += 10
    elif op == "read":
        if not relatime or inode.atime <= inode.mtime:
            inode.atime += 10
    else:
        raise ValueError(f"Unknown file operation: {op}")
    return inode


def diagnose_enospc(free_bytes: int, free_inodes: int) -> str:
    """Diagnose why a write returned ENOSPC ('No space left on device')."""
    if free_inodes == 0 and free_bytes > 0:
        return "inode_exhaustion: df -h shows free bytes, but df -i is at 100%"
    if free_bytes == 0:
        return "block_exhaustion: data blocks are full"
    return "quota_or_container_layer_limit"
