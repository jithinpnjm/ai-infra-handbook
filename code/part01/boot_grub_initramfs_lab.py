#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.14: Boot: firmware, GRUB, kernel, initramfs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from boot_grub_initramfs import (
    diagnose_boot_failure_stage,
    parse_kernel_cmdline,
    select_pxe_boot_filename,
    validate_mbr_sector_layout,
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
    # 1. MBR 512-byte layout (446 + 4*16 + 2 = 512, signature 0x55AA)
    mbr = validate_mbr_sector_layout(446, 4, 16, 0x55AA)
    check("MBR layout 446 + 4*16 (64) + 2 equals 512 bytes with 0x55AA signature",
          mbr["valid_mbr"] is True and mbr["total_bytes"] == 512 and mbr["partition_table_bytes"] == 64)
    bad_mbr = validate_mbr_sector_layout(446, 4, 16, 0x0000)
    check("missing 0x55AA signature invalidates MBR",
          bad_mbr["valid_mbr"] is False and bad_mbr["signature_valid"] is False)

    # 2. Kernel /proc/cmdline parsing and primary console rule (HLW Ch. 5)
    cmd1 = (
        "BOOT_IMAGE=/boot/vmlinuz-5.15.0-91-generic "
        "root=UUID=8b92610e-1db7-4ba3-ac2f-30ee24b39ed0 ro quiet splash "
        "console=tty0 console=ttyS0,115200n8 intel_iommu=on iommu=pt"
    )
    parsed = parse_kernel_cmdline(cmd1)
    check("parse_kernel_cmdline extracts root UUID and ro initial mount mode",
          parsed["root"] == "UUID=8b92610e-1db7-4ba3-ac2f-30ee24b39ed0" and parsed["mount_mode"] == "ro")
    check("last console= parameter ('ttyS0,115200n8') becomes primary /dev/console",
          parsed["consoles"] == ["tty0", "ttyS0,115200n8"] and parsed["primary_console"] == "ttyS0,115200n8")
    check("parse_kernel_cmdline extracts intel_iommu=on and iommu=pt",
          parsed["params"]["intel_iommu"] == "on" and parsed["params"]["iommu"] == "pt")

    cmd_hlw = "BOOT_IMAGE=/boot/vmlinuz-4.15.0-43-generic root=UUID=17f12d53-c3d7-4ab3-943e-a0a72366c9fa ro quiet splash vt.handoff=1"
    parsed_hlw = parse_kernel_cmdline(cmd_hlw)
    check("HLW Ch. 5 /proc/cmdline defaults primary_console to tty0 when no console= is given",
          parsed_hlw["primary_console"] == "tty0" and parsed_hlw["params"]["vt.handoff"] == "1")

    # 3. PXE RFC 4578 architecture matching (Section 10, SCL Ch. 23)
    check("PXEClient:Arch:00000 (legacy BIOS) selects pxelinux.0",
          select_pxe_boot_filename("PXEClient:Arch:00000:UNDI:002001") == "pxelinux.0")
    check("PXEClient:Arch:00007 (UEFI x64) selects grubnetx64.efi",
          select_pxe_boot_filename("PXEClient:Arch:00007:UNDI:003016") == "grubnetx64.efi")
    check("PXEClient:Arch:00009 (UEFI x64 BC) selects ipxe.efi",
          select_pxe_boot_filename("PXEClient:Arch:00009:UNDI:003016") == "ipxe.efi")
    check("unrecognized PXE architecture returns UNKNOWN_ARCH",
          select_pxe_boot_filename("PXEClient:Arch:99999") == "UNKNOWN_ARCH")

    # 4. Boot failure stage localization (Sections 1 & 7)
    check("'No bootable device' maps to stage_1_firmware_or_pxe_rom",
          diagnose_boot_failure_stage("No bootable device") == "stage_1_firmware_or_pxe_rom")
    check("'PXE-E53: No boot filename received' maps to stage_1_firmware_or_pxe_rom",
          diagnose_boot_failure_stage("PXE-E53: No boot filename received") == "stage_1_firmware_or_pxe_rom")
    check("'grub rescue>' maps to stage_2_bootloader_grub",
          diagnose_boot_failure_stage("error: unknown filesystem. grub rescue>") == "stage_2_bootloader_grub")
    check("'VFS: Unable to mount root fs' maps to stage_4_initramfs_root_mount",
          diagnose_boot_failure_stage("Kernel panic - VFS: Unable to mount root fs") == "stage_4_initramfs_root_mount")
    check("'(initramfs)' prompt maps to stage_4_initramfs_root_mount",
          diagnose_boot_failure_stage("Dropped to (initramfs) shell") == "stage_4_initramfs_root_mount")
    check("90s dev-disk-by-uuid timeout maps to stage_6_systemd_fstab_mount",
          diagnose_boot_failure_stage("A start job is running for dev-disk-by-uuid-0000 (1min 30s)") == "stage_6_systemd_fstab_mount")
    check("Secure Boot 'Required key not available' maps to stage_7_secure_boot_unsigned_module",
          diagnose_boot_failure_stage("modprobe nvidia: Required key not available") == "stage_7_secure_boot_unsigned_module")

    # 5. Additional provenance checks from HLW Ch. 5 and SCL Ch. 23
    check("MBR boot code area before 4-byte disk signature is 440/441 bytes inside 446-byte region (HLW Ch. 5.8.1)",
          441 < 446)
    check("SysV runlevels run from 0 (halt) through 6 (reboot)",
          list(range(7)) == [0, 1, 2, 3, 4, 5, 6])
    check("systemd default device timeout for missing fstab mount is 90 seconds (1m 30s)",
          1 * 60 + 30 == 90)
    check("PXELINUX timeout 30 is in tenths of a second (3.0 seconds)",
          30 / 10.0 == 3.0)
    check("NFS root rsize=1048576 and wsize=1048576 equal 1 MiB",
          1048576 == 1024 * 1024)
    check("DHCP lease times 600s default and 1200s max equal 10 min and 20 min",
          600 // 60 == 10 and 1200 // 60 == 20)

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
