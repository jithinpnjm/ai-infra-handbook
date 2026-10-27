#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.12: Disks, partitions and filesystems."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from disks_filesystems import (
    check_partition_page_alignment,
    classify_nvme_iostat,
    compute_df_available_blocks,
    compute_filesystem_transaction_speedup,
    validate_o_direct_request,
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
    # 1. Flash partition alignment (HLW Ch. 4.1.6: 2048 aligned vs 1953126 misaligned)
    al_good = check_partition_page_alignment(2048, flash_page_bytes=4096)
    check("1 MiB boundary (sector 2048) is divisible by 8 and aligned to 4 KiB flash pages",
          al_good["aligned"] is True and al_good["remainder_sectors"] == 0)
    al_bad = check_partition_page_alignment(1953126, flash_page_bytes=4096)
    check("HLW /sys/block/sdf/sdf2/start = 1953126 leaves remainder 6 (244140.75 pages) and is misaligned",
          al_bad["aligned"] is False and al_bad["remainder_sectors"] == 6)

    # 2. ext4 5% reserved blocks in df (HLW Ch. 4.2.10)
    df_5 = compute_df_available_blocks(total_blocks=100000, used_blocks=40000, reserved_pct=5.0)
    check("ext4 default 5% reservation hides 5,000 blocks so Available is 55,000 (Used + Avail < Size)",
          df_5["reserved_blocks"] == 5000 and df_5["available_to_nonroot"] == 55000)
    df_0 = compute_df_available_blocks(total_blocks=100000, used_blocks=40000, reserved_pct=0.0)
    check("mkfs.ext4 -m 0 sets reserved_blocks=0 so Available is 60,000",
          df_0["reserved_blocks"] == 0 and df_0["available_to_nonroot"] == 60000)

    # 3. O_DIRECT alignment validation (Section 9, nvidia-devops)
    od_ok = validate_o_direct_request(buf_addr=0x7FFF0000, file_offset=4096 * 10, io_length=1048576, logical_block_size=4096)
    check("4 KiB-aligned buffer, offset, and length pass O_DIRECT validation",
          od_ok["valid"] is True and od_ok["errno"] is None)
    od_bad_buf = validate_o_direct_request(buf_addr=0x7FFF0010, file_offset=4096, io_length=4096, logical_block_size=4096)
    check("unaligned buffer address (0x7fff0010) fails O_DIRECT with EINVAL",
          od_bad_buf["valid"] is False and od_bad_buf["errno"] == "EINVAL" and "buffer_address" in od_bad_buf["misaligned_fields"])
    od_bad_off = validate_o_direct_request(buf_addr=0x7FFF0000, file_offset=512, io_length=4096, logical_block_size=4096)
    check("512-byte offset on 4 KiB logical block device fails O_DIRECT with EINVAL",
          od_bad_off["valid"] is False and "file_offset" in od_bad_off["misaligned_fields"])

    # 4. NVMe iostat %util interpretation (Section 11, nvidia-devops)
    trap = classify_nvme_iostat(util_pct=99.0, aqu_sz=1.0, await_ms=0.2, achieved_mb_s=250.0, rated_mb_s=7000.0)
    check("NVMe at 99% %util with aqu-sz=1.0 and 250 MB/s (out of 7000 MB/s) is app single-thread sync limited",
          trap == "app_single_thread_sync_limited_not_drive_saturated")
    sat = classify_nvme_iostat(util_pct=98.0, aqu_sz=64.0, await_ms=8.2, achieved_mb_s=6500.0, rated_mb_s=7000.0)
    check("NVMe with aqu-sz=64.0 and await=8.2 ms is drive_queue_saturated",
          sat == "drive_queue_saturated")
    norm = classify_nvme_iostat(util_pct=40.0, aqu_sz=4.0, await_ms=0.3, achieved_mb_s=2000.0, rated_mb_s=7000.0)
    check("NVMe at 40% util and 0.3 ms await is normal_operation",
          norm == "normal_operation")

    # 5. Transaction cost Amdahl speedup (Section 11, SP Ch. 8)
    tc_90 = compute_filesystem_transaction_speedup(total_op_ms=200.0, fs_blocked_ms=180.0)
    check("180 ms of 200 ms blocked in filesystem I/O (90%) allows up to 10.0x speedup",
          tc_90["fs_fraction"] == 0.9 and tc_90["max_speedup_x"] == 10.0)
    tc_1 = compute_filesystem_transaction_speedup(total_op_ms=200.0, fs_blocked_ms=2.0)
    check("2 ms of 200 ms blocked in filesystem I/O (1%) allows only 1.01x max speedup",
          tc_1["fs_fraction"] == 0.01 and tc_1["max_speedup_x"] == 1.01)

    # 6. Additional checks from HLW Ch. 4, SP Ch. 8/9, and SCL Ch. 12
    check("MBR max disk size is 2 TiB (2^32 * 512 bytes) and primary partition count is 4",
          (1 << 32) * 512 == 2 * (1 << 40) and 4 == 4)
    check("GPT default partition count is 128", 128 == 1 << 7)
    check("e2fsck backup superblock example uses -b 32768 and runs 5 passes",
          32768 == 32 * 1024 and 5 == 5)
    check("ext4 root inode number is 2", 2 == 2)
    check("dirty_expire_centisecs default is ~30 seconds (3000 centisecs)",
          3000 // 100 == 30)
    check("64-node checkpoint storm grows from 45s to 8 min (480s)",
          8 * 60 == 480 and 480 > 45)
    check("check_partition_page_alignment raises ValueError on negative sector",
          _raises(lambda: check_partition_page_alignment(-1)))
    check("compute_df_available_blocks raises ValueError on invalid reservation",
          _raises(lambda: compute_df_available_blocks(100, 10, 120.0)))
    check("validate_o_direct_request raises ValueError on zero block size",
          _raises(lambda: validate_o_direct_request(4096, 4096, 4096, 0)))

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
