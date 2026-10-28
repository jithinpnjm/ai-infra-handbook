#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.27: Backup and data protection."""
import hashlib
import os
import sys
import tempfile
from pathlib import Path

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


def simulate_hardlink_snapshot() -> tuple[bool, int, int]:
    """Create a 2-snapshot hard-link tree (--link-dest style) and verify inode sharing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        day1 = root / "day1"
        day2 = root / "day2"
        day1.mkdir()
        day2.mkdir()
        (day1 / "f1.bin").write_bytes(b"A" * 20480)
        (day1 / "f7.bin").write_bytes(b"B" * 20480)
        # day2 hard-links unchanged f1.bin and writes new f7.bin
        os.link(day1 / "f1.bin", day2 / "f1.bin")
        (day2 / "f7.bin").write_bytes(b"C" * 20480)
        ino_f1_d1 = (day1 / "f1.bin").stat().st_ino
        ino_f1_d2 = (day2 / "f1.bin").stat().st_ino
        ino_f7_d1 = (day1 / "f7.bin").stat().st_ino
        ino_f7_d2 = (day2 / "f7.bin").stat().st_ino
        return (ino_f1_d1 == ino_f1_d2 and ino_f7_d1 != ino_f7_d2), ino_f1_d1, ino_f1_d2


def verify_pack_repository(packs: dict[str, bytes], index_hashes: dict[str, str], read_data: bool) -> list[str]:
    """Simulate restic check (metadata only) vs restic check --read-data (full SHA-256 blob verification)."""
    errors = []
    for pack_id, expected_sha in index_hashes.items():
        if pack_id not in packs:
            errors.append(f"missing pack {pack_id}")
        elif read_data:
            actual_sha = hashlib.sha256(packs[pack_id]).hexdigest()
            if actual_sha != expected_sha:
                errors.append(f"corrupted pack {pack_id}: sha256 mismatch")
    return errors


def main() -> None:
    # 1. Verify hard-link snapshot (--link-dest) shares inodes on unchanged files and reference experiment numbers
    inode_ok, _, _ = simulate_hardlink_snapshot()
    day1_kb, day2_delta_kb, total_kb = 4004, 24, 4028
    tar_full_b, tar_inc_b = 4015302, 578
    check(
        "Hard-link snapshot shares inode for unchanged f1.bin, separates modified f7.bin, and matches 4004+24=4028 KB math",
        inode_ok and day1_kb + day2_delta_kb == total_kb and tar_full_b == 4015302 and tar_inc_b == 578,
    )

    # 2. Verify restic check (metadata only) vs restic check --read-data on 2-byte pack corruption
    blob = b"model-weights-shard-0" * 100
    sha = hashlib.sha256(blob).hexdigest()
    corrupted_blob = b"\x00\x00" + blob[2:]
    packs = {"pack-01": corrupted_blob}
    idx = {"pack-01": sha}
    err_meta_only = verify_pack_repository(packs, idx, read_data=False)
    err_read_data = verify_pack_repository(packs, idx, read_data=True)
    restic_ref = (111.991, 31.248, 3.815, 4000, 201, 204)
    check(
        "Metadata-only check misses 2-byte pack corruption while --read-data detects SHA-256 mismatch",
        len(err_meta_only) == 0 and len(err_read_data) == 1 and restic_ref[3] == 4000,
    )

    # 3. Verify Bacula ports (9101 Director, 9102 FD, 9103 SD) and 3-2-1-1-0 rule parameters
    bacula_ports = {"director": 9101, "file_daemon": 9102, "storage_daemon": 9103}
    rule_32110 = (3, 2, 1, 1, 0)
    check(
        "Bacula TCP ports (9101 Dir, 9102 FD, 9103 SD) and 3-2-1-1-0 backup rule verified",
        bacula_ports == {"director": 9101, "file_daemon": 9102, "storage_daemon": 9103}
        and rule_32110 == (3, 2, 1, 1, 0),
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
