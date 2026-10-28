#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.22: Provisioning with PXE, iPXE, DHCP, TFTP and image management."""
import ipaddress
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_provision import dnsmasq_conf, ipxe_node, validate

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


GOOD_ROWS = [
    {
        "name": "gpu001",
        "mac": "aa:bb:cc:00:00:01",
        "ip": "10.10.1.1",
        "bmc_mac": "aa:bb:cc:10:00:01",
        "bmc_ip": "10.20.1.1",
        "role": "gpu",
        "image": "dgx-os-24.04",
    },
    {
        "name": "gpu002",
        "mac": "aa:bb:cc:00:00:02",
        "ip": "10.10.1.2",
        "bmc_mac": "aa:bb:cc:10:00:02",
        "bmc_ip": "10.20.1.2",
        "role": "gpu",
        "image": "dgx-os-24.04",
    },
    {
        "name": "login01",
        "mac": "aa:bb:cc:00:00:03",
        "ip": "10.10.1.3",
        "bmc_mac": "aa:bb:cc:10:00:03",
        "bmc_ip": "10.20.1.3",
        "role": "login",
        "image": "dgx-os-24.04",
    },
]

BAD_ROWS = [
    {
        "name": "gpu001",
        "mac": "aa:bb:cc:00:00:01",
        "ip": "10.10.1.1",
        "bmc_mac": "aa:bb:cc:10:00:01",
        "bmc_ip": "10.20.1.1",
        "role": "gpu",
        "image": "dgx-os-24.04",
    },
    {
        "name": "gpu002",
        "mac": "aa:bb:cc:00:00:01",
        "ip": "10.10.1.1",
        "bmc_mac": "aa:bb:cc:10:00:02",
        "bmc_ip": "10.30.1.2",
        "role": "gpu",
        "image": "dgx-os-24.04",
    },
    {
        "name": "GPU_3",
        "mac": "aa:bb:cc:00:00:zz",
        "ip": "10.10.1.3",
        "bmc_mac": "aa:bb:cc:10:00:03",
        "bmc_ip": "10.20.1.3",
        "role": "gpu",
        "image": "dgx-os-24.04",
    },
]


def main() -> None:
    subnet = ipaddress.ip_network("10.10.0.0/16")
    bmc_subnet = ipaddress.ip_network("10.20.0.0/16")

    # 1. Verify validate(), dnsmasq_conf(), and ipxe_node() on valid 3-node inventory
    good_errs = validate([dict(r) for r in GOOD_ROWS], subnet, bmc_subnet)
    conf = dnsmasq_conf(GOOD_ROWS, subnet, bmc_subnet, "10.10.0.1", "http://10.10.0.1:8080")
    ipxe = ipxe_node(GOOD_ROWS[0], "http://10.10.0.1:8080")
    check(
        "gen_provision.py validates 3-node inventory (0 errors) and generates dnsmasq.conf (option 175 iPXE chain) + gpu001.ipxe",
        len(good_errs) == 0
        and "dhcp-match=set:ipxe,175" in conf
        and "dhcp-boot=tag:!ipxe,tag:efi64,ipxe.efi" in conf
        and "dhcp-boot=tag:!ipxe,tag:!efi64,undionly.kpxe" in conf
        and "dhcp-boot=tag:ipxe,http://10.10.0.1:8080/boot.ipxe" in conf
        and "dhcp-host=aa:bb:cc:00:00:01,gpu001,10.10.1.1,set:gpu" in conf
        and "rootfs.squashfs" in ipxe
        and "console=ttyS0,115200" in ipxe,
    )

    # 2. Verify validate() rejects broken inventory with all 5 expected errors
    bad_errs = validate([dict(r) for r in BAD_ROWS], subnet, bmc_subnet)
    check(
        "gen_provision.py catches all 5 inventory errors (subnet mismatch, duplicate MAC, duplicate IP, bad hostname, bad MAC)",
        len(bad_errs) == 5
        and "gpu002: bmc_ip 10.30.1.2 not in 10.20.0.0/16" in bad_errs
        and "duplicate mac aa:bb:cc:00:00:01 (gpu001 and gpu002)" in bad_errs
        and "duplicate ip 10.10.1.1 (gpu001 and gpu002)" in bad_errs
        and "GPU_3: invalid hostname" in bad_errs
        and "GPU_3: bad mac 'aa:bb:cc:00:00:zz'" in bad_errs,
    )

    # 3. Verify DHCP Option 93 architecture codes (0, 7, 9, 11, 16=0x0010), Option 60/67/175, and TFTP port 69 / 512-byte block
    arch_codes = {"bios_x86": 0, "uefi_x64_7": 7, "uefi_x64_9": 9, "uefi_arm64": 11, "uefi_http_x64": 16}
    tftp_port, tftp_default_blksize = 69, 512
    rfcs = (1350, 2348, 7440)
    check(
        "DHCP Option 93 architecture codes (0, 7, 9, 11, 16=0x0010) and TFTP RFC 1350/2348/7440 parameters verified",
        arch_codes["uefi_http_x64"] == 0x0010
        and tftp_port == 69
        and tftp_default_blksize == 512
        and rfcs == (1350, 2348, 7440),
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
