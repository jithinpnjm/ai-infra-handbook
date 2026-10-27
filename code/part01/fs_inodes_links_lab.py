#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.3: Files and the directory hierarchy: paths, links, inodes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fs_inodes_links import (
    FHS_DIRECTORIES,
    FILE_TYPE_CHARS,
    InodeState,
    compute_directory_link_count,
    diagnose_enospc,
    evaluate_timestamps_on_operation,
    simulate_hard_link,
    simulate_unlink,
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
    # 1. FHS directories (HLW Ch. 2.19)
    check("/etc holds system-wide configuration", "configuration" in FHS_DIRECTORIES["/etc"])
    check("/usr/include holds C compiler headers", "header" in FHS_DIRECTORIES["/usr/include"])
    check("/usr/local holds administrator-installed software", "local" in FHS_DIRECTORIES["/usr/local"])
    check("/usr/share holds architecture-independent files", "architecture-independent" in FHS_DIRECTORIES["/usr/share"])
    check("/proc and /sys are virtual filesystems", "virtual" in FHS_DIRECTORIES["/proc"] and "virtual" in FHS_DIRECTORIES["/sys"])
    check("/lib/modules holds loadable kernel modules", "modules" in FHS_DIRECTORIES["/lib/modules"])

    # 2. File type characters in ls -l
    check("all 7 ls -l file type characters are modeled (-, d, l, c, b, s, p)",
          set(FILE_TYPE_CHARS.keys()) == {"-", "d", "l", "c", "b", "s", "p"})
    check("'c' is character device and 'b' is block device",
          FILE_TYPE_CHARS["c"] == "character device" and FILE_TYPE_CHARS["b"] == "block device")

    # 3. Directory link count rule (2 + subdirectories)
    check("empty directory has link count 2 (parent entry + '.')", compute_directory_link_count(0) == 2)
    check("directory with 5 subdirectories has link count 7 (2 + 5 '..' entries)", compute_directory_link_count(5) == 7)

    # 4. Hard links: same-device success, cross-device EXDEV, and VFAT restriction (HLW Ch. 4)
    ino = InodeState(inode_number=7401, device_id=2049, size_bytes=200 * 1024 * 1024, link_count=1, open_fd_count=0, mtime=100, ctime=100, atime=100)
    ok, msg = simulate_hard_link(ino, target_device_id=2049, fs_type="ext4")
    check("same-filesystem hard link increments link_count to 2 and updates ctime",
          ok is True and ino.link_count == 2 and ino.ctime == 101 and ino.mtime == 100)
    ok_xdev, msg_xdev = simulate_hard_link(ino, target_device_id=2050, fs_type="ext4")
    check("cross-filesystem hard link fails with EXDEV",
          ok_xdev is False and "EXDEV" in msg_xdev and ino.link_count == 2)
    ok_vfat, msg_vfat = simulate_hard_link(ino, target_device_id=2049, fs_type="vfat")
    check("hard link on mounted VFAT filesystem fails because VFAT lacks Unix inode links",
          ok_vfat is False and "VFAT" in msg_vfat)

    # 5. Unlink when link_count == 2 keeps data intact
    res1 = simulate_unlink(ino)
    check("removing first of 2 hard links leaves link_count=1 and retains data",
          res1["link_count"] == 1 and res1["blocks_freed"] is False and res1["retained_bytes"] == 200 * 1024 * 1024)

    # 6. Deleted-but-open file (lsof +L1) retains disk blocks until closed
    open_ino = InodeState(inode_number=8800, device_id=2049, size_bytes=200 * 1024 * 1024, link_count=1, open_fd_count=1, mtime=100, ctime=100, atime=100)
    res_open = simulate_unlink(open_ino)
    check("unlinking a 200 MiB file with 1 open descriptor keeps blocks allocated and shows in lsof +L1",
          res_open["link_count"] == 0 and res_open["blocks_freed"] is False and res_open["visible_in_lsof_plus_L1"] is True)
    closed_ino = InodeState(inode_number=8801, device_id=2049, size_bytes=200 * 1024 * 1024, link_count=1, open_fd_count=0, mtime=100, ctime=100, atime=100)
    res_closed = simulate_unlink(closed_ino)
    check("unlinking a file with link_count=1 and 0 open descriptors frees blocks immediately",
          res_closed["link_count"] == 0 and res_closed["blocks_freed"] is True and res_closed["retained_bytes"] == 0)

    # 7. Timestamps: write_content updates mtime+ctime; chmod updates only ctime
    t_ino = InodeState(inode_number=9001, device_id=2049, size_bytes=1024, link_count=1, open_fd_count=0, mtime=100, ctime=100, atime=100)
    evaluate_timestamps_on_operation(t_ino, "write_content")
    check("writing file content updates both mtime and ctime", t_ino.mtime == 110 and t_ino.ctime == 110 and t_ino.atime == 100)
    evaluate_timestamps_on_operation(t_ino, "chmod")
    check("chmod updates only ctime, leaving mtime unchanged", t_ino.mtime == 110 and t_ino.ctime == 120)

    # 8. ENOSPC diagnosis: inode exhaustion vs block exhaustion
    check("0 free inodes with free bytes diagnoses as inode_exhaustion (df -i at 100%)",
          "inode_exhaustion" in diagnose_enospc(free_bytes=10 * 1024 * 1024, free_inodes=0))
    check("0 free bytes diagnoses as block_exhaustion",
          "block_exhaustion" in diagnose_enospc(free_bytes=0, free_inodes=5000))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
