"""Chapter 1.14 model: 7-stage Linux boot progression and failure stage localization,
MBR 512-byte layout (446/441-byte boot code + 64-byte partition table + 0x55AA),
kernel /proc/cmdline parsing (root=, ro, console= primary selection), and PXE
RFC 4578 DHCP client architecture matching.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 5
  ("How the Linux Kernel Boots": journalctl -k startup messages, /proc/cmdline,
  boot loaders GRUB 2, SYSLINUX/ISOLINUX, systemd-boot, coreboot, EFISTUB,
  efilinux, GRUB root vs Linux root=, /etc/default/grub and /etc/grub.d,
  UEFI Secure Boot shim/MOK, MBR 441/446-byte boot code).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 23
  ("Booting and Init": BIOS/MBR vs UEFI/GPT 18+ EB, SysV inittab and LSB headers,
  systemd Lennart Poettering & Kay Sievers, PXE DHCP/TFTP/NFS-root, snmpwalk
  dot1dTpFdbEntry MAC discovery, 1-2s boot-storm stagger).
"""
from typing import Dict, List, Optional


PXE_ARCH_LOADERS: Dict[str, str] = {
    "PXEClient:Arch:00000": "pxelinux.0",
    "PXEClient:Arch:00007": "grubnetx64.efi",
    "PXEClient:Arch:00009": "ipxe.efi",
}


def validate_mbr_sector_layout(
    boot_code_bytes: int = 446,
    partition_entries: int = 4,
    entry_bytes: int = 16,
    signature_hex: int = 0x55AA,
) -> Dict[str, object]:
    """Verify the 512-byte Master Boot Record structure (446 + 4*16 + 2 = 512, signature 0x55AA)."""
    part_table_bytes = partition_entries * entry_bytes
    sig_bytes = 2
    total = boot_code_bytes + part_table_bytes + sig_bytes
    valid = total == 512 and signature_hex == 0x55AA
    return {
        "total_bytes": total,
        "partition_table_bytes": part_table_bytes,
        "signature_valid": signature_hex == 0x55AA,
        "valid_mbr": valid,
    }


def parse_kernel_cmdline(cmdline: str) -> Dict[str, object]:
    """Parse /proc/cmdline into root, ro/rw mode, consoles (last is primary /dev/console), and flags."""
    tokens = cmdline.strip().split()
    root_dev: Optional[str] = None
    mount_mode = "rw"
    consoles: List[str] = []
    kv_params: Dict[str, str] = {}
    flags: List[str] = []

    for tok in tokens:
        if tok in {"ro", "rw"}:
            mount_mode = tok
            flags.append(tok)
        elif tok.startswith("console="):
            consoles.append(tok.split("=", 1)[1])
        elif "=" in tok:
            k, v = tok.split("=", 1)
            kv_params[k] = v
            if k == "root":
                root_dev = v
        else:
            flags.append(tok)

    return {
        "root": root_dev,
        "mount_mode": mount_mode,
        "consoles": consoles,
        "primary_console": consoles[-1] if consoles else "tty0",
        "params": kv_params,
        "flags": flags,
    }


def select_pxe_boot_filename(vendor_class_id: str) -> str:
    """Select the DHCP PXE boot filename based on the first 20 chars of vendor-class-identifier (RFC 4578)."""
    prefix = vendor_class_id[:20]
    return PXE_ARCH_LOADERS.get(prefix, "UNKNOWN_ARCH")


def diagnose_boot_failure_stage(symptom: str) -> str:
    """Map a boot failure symptom to the exact stage of the 7-stage boot pipeline."""
    s = symptom.lower()
    if "no bootable device" in s or "pxe-e53" in s:
        return "stage_1_firmware_or_pxe_rom"
    if "grub rescue>" in s or "invalid magic" in s:
        return "stage_2_bootloader_grub"
    if "unable to mount root fs" in s or "(initramfs)" in s or "dracut:/#" in s:
        return "stage_4_initramfs_root_mount"
    if "a start job is running for dev-disk-by-uuid" in s or "emergency mode" in s:
        return "stage_6_systemd_fstab_mount"
    if "required key not available" in s or "module verification failed" in s:
        return "stage_7_secure_boot_unsigned_module"
    return "unknown_stage"
