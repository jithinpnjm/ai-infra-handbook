"""Chapter 1.12 model: Flash partition alignment check (512-byte sectors vs 4 KiB pages),
ext4 reserved blocks and df Used + Available < Size accounting, O_DIRECT buffer/offset/length
alignment (EINVAL), iostat NVMe %util vs aqu-sz interpretation, and checkpoint metadata storm
scaling.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 4
  ("Disks and Filesystems": parted -l, fdisk, partition alignment /sys/block/sdf/sdf2/start
  1953126 not divisible by 8, mkfs/mke2fs, mount/fstab, df 5% reserved blocks, e2fsck 5 passes,
  inodes and directory entries).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 8 ("File Systems") and Chapter 9 ("Disks").
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 12 (6-step Linux
  quota setup workflow).
- nvidia-devops/volume-01/02-linux-storage-io-masterclass.md (5 meanings of disk full,
  O_DIRECT alignment, GPUDirect Storage vs page cache, NVMe %util trap, 64-node checkpoint
  metadata storm).
"""
from typing import Dict


def check_partition_page_alignment(start_sector_512b: int, flash_page_bytes: int = 4096) -> Dict[str, object]:
    """Check whether a 512-byte sector start offset is aligned to a flash page boundary (e.g. 4 KiB = 8 sectors)."""
    if start_sector_512b < 0 or flash_page_bytes <= 0 or flash_page_bytes % 512 != 0:
        raise ValueError("Invalid sector or flash page parameters")
    sectors_per_page = flash_page_bytes // 512
    rem = start_sector_512b % sectors_per_page
    return {
        "start_sector": start_sector_512b,
        "sectors_per_page": sectors_per_page,
        "remainder_sectors": rem,
        "aligned": rem == 0,
    }


def compute_df_available_blocks(total_blocks: int, used_blocks: int, reserved_pct: float = 5.0) -> Dict[str, int]:
    """Compute ext4 reserved blocks and non-root Available blocks (Why Used + Available < Size in df)."""
    if total_blocks <= 0 or used_blocks < 0 or not (0.0 <= reserved_pct < 100.0):
        raise ValueError("Invalid block or reservation parameters")
    reserved = int(round(total_blocks * (reserved_pct / 100.0)))
    avail = max(0, total_blocks - used_blocks - reserved)
    return {
        "total_blocks": total_blocks,
        "used_blocks": used_blocks,
        "reserved_blocks": reserved,
        "available_to_nonroot": avail,
    }


def validate_o_direct_request(
    buf_addr: int,
    file_offset: int,
    io_length: int,
    logical_block_size: int = 4096,
) -> Dict[str, object]:
    """Verify O_DIRECT alignment rules: buffer address, file offset, and I/O length must be multiples of block size."""
    if logical_block_size <= 0:
        raise ValueError("logical_block_size must be positive")
    misaligned = []
    if buf_addr % logical_block_size != 0:
        misaligned.append("buffer_address")
    if file_offset % logical_block_size != 0:
        misaligned.append("file_offset")
    if io_length <= 0 or io_length % logical_block_size != 0:
        misaligned.append("io_length")
    return {
        "valid": len(misaligned) == 0,
        "errno": None if len(misaligned) == 0 else "EINVAL",
        "misaligned_fields": misaligned,
    }


def classify_nvme_iostat(
    util_pct: float,
    aqu_sz: float,
    await_ms: float,
    achieved_mb_s: float,
    rated_mb_s: float,
) -> str:
    """Interpret iostat -xz on an NVMe SSD (avoiding the single-thread 100% %util trap)."""
    if util_pct >= 90.0 and aqu_sz < 4.0 and achieved_mb_s < rated_mb_s * 0.3:
        return "app_single_thread_sync_limited_not_drive_saturated"
    if aqu_sz >= 32.0 and await_ms >= 5.0:
        return "drive_queue_saturated"
    return "normal_operation"


def compute_filesystem_transaction_speedup(total_op_ms: float, fs_blocked_ms: float) -> Dict[str, float]:
    """Compute fraction of transaction time spent in filesystem I/O and Amdahl max speedup if eliminated."""
    if total_op_ms <= 0 or fs_blocked_ms < 0 or fs_blocked_ms > total_op_ms:
        raise ValueError("Invalid transaction timing values")
    fraction = fs_blocked_ms / total_op_ms
    non_fs = total_op_ms - fs_blocked_ms
    max_speedup = round(total_op_ms / non_fs, 2) if non_fs > 0 else float("inf")
    return {"fs_fraction": round(fraction, 3), "max_speedup_x": max_speedup}
