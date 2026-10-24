---
id: "c06-22"
title: "6.22 Provisioning with PXE, iPXE, DHCP, TFTP and image management"
sidebar_label: "6.22 Provisioning with PXE, iPXE, DHCP, TFTP and image management"
sidebar_position: 22
description: "How cluster nodes get an operating system: the boot chain (firmware, bootloader, kernel, initramfs, init), DHCP/TFTP/PXE, iPXE and UEFI HTTP boot, stateless and diskless images, NFS-root and squashfs, image building and versioning, node identity and discovery, a tested inventory-to-dnsmasq/iPXE generator, and a boot-failure triage method"
status: "drafted"
tier: "1b"
level: "A"
lab_venue: "GCP / GKE"
---

# 6.22 Provisioning with PXE, iPXE, DHCP, TFTP and image management

| | |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | libvirt/VirtualBox/QEMU VMs on a host-only network; or a spare rack |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. `code/part06/gen_provision.py` was run on a three-node inventory and on a deliberately broken one (outputs shown). dnsmasq option names were checked against the dnsmasq(8) manual (imp/dnsmasq mirror, commit `cf08eee`, 2026-03-15); dnsmasq itself, TFTP, iPXE, and actual network boots were **not** run (no installable dnsmasq here, no privileged ports). iPXE, UEFI HTTP Boot, Kea and image-tool details are from general knowledge and the NVIDIA-DevOps notes. Labs **untested** |

## Why this matters for AI infrastructure

A GPU cluster has hundreds to thousands of nodes that must be installed, reinstalled, patched and replaced without anyone touching a keyboard. When a node is swapped after a GPU failure it must come up with the right OS image, drivers, firmware settings, name and identity within minutes. Provisioning is therefore a first-class system with its own failure modes: DHCP misconfiguration, boot storms, image drift, mismatched firmware modes. NVIDIA Base Command Manager (Part 8), xCAT and Warewulf (6.23), MAAS and Foreman all build on the mechanisms described here.

## Prerequisites and outcomes

Needs Part 1 (boot process, systemd), Part 2 (DHCP, VLANs), 6.2 (management network). After this chapter you can:

- Describe the boot chain and where network boot plugs in (BIOS vs UEFI, PXE, iPXE, HTTP boot).
- Configure a provisioning server (DHCP, TFTP, HTTP) conceptually and generate configuration from an inventory with validation.
- Choose between stateful, stateless (diskless) and hybrid node designs; explain NFS-root and squashfs+overlay.
- Build, version, test and roll out node images; manage node identity and first-boot configuration.
- Troubleshoot network-boot failures with a staged method.
- Relate xCAT, Warewulf, MAAS, Foreman, BCM and out-of-the-box stacks to this foundation.

## 1. The boot chain

1. **Firmware** (legacy BIOS or UEFI) initialises hardware, selects a boot device from the boot order (disk, USB, network).
2. **Boot loader**: from disk (GRUB, systemd-boot) or from the network (PXE ROM/UEFI network stack loads a small NBP, "network bootstrap program").
3. **Kernel + initramfs** are loaded into memory; the kernel starts, runs the initramfs (early user space: drivers, assemble the root device, possibly fetch the root image).
4. **Root file system** is mounted (local disk, NFS, squashfs image in RAM).
5. **Init**: PID 1 starts services. The SCL book contrasts **init in the SystemV style** (SysV init: shell scripts in runlevel directories, sequential) with **systemd** (units, dependencies, parallel start, cgroups, journald); modern distributions use systemd, which also matters for cgroup-based Slurm (6.8).

Local-disk boot is covered by the book's "Booting from Hard Disk" (MBR/partitions/GRUB and initrd); this chapter concentrates on the network paths.

## 2. Network boot protocols

### DHCP

A node's firmware broadcasts DHCPDISCOVER; the server returns IP, router, DNS, and **boot information**: next-server (`siaddr`) and boot file name (`file`, option 67), plus vendor options. The client identifies itself with options such as **60** (vendor class: `PXEClient`, `HTTPClient`) and **93** (client system architecture: 0 = x86 BIOS, 7 and 9 = x64 UEFI, 16 = x64 UEFI HTTP, 11 = ARM64 UEFI; values from the PXE/UEFI specifications). The server uses these to send different boot files for BIOS, UEFI and HTTP clients. Static assignment by MAC address (`dhcp-host=mac,name,ip` in dnsmasq, `host` blocks in ISC dhcpd, reservations in Kea) gives each node a stable identity; an unknown MAC gets a **discovery pool** address and is added to the inventory (6.23).

Servers: ISC `dhcpd` (end-of-life, widely deployed), **ISC Kea** (its successor, JSON config, hooks, database backends), **dnsmasq** (lightweight DHCP+TFTP+DNS, popular in small and medium clusters, used inside many deployment tools), vendor appliances. Run one authoritative DHCP server per provisioning VLAN; two DHCP servers on one segment cause intermittent wrong-image boots. Disable DHCP relay surprises: the switch must forward DHCP between VLANs only intentionally (`ip helper-address`).

### TFTP and PXE

**PXE** (Preboot Execution Environment) is firmware-resident: it obtains DHCP, downloads the boot file by **TFTP** (Trivial File Transfer Protocol, UDP port 69, RFC 1350), and executes it. TFTP is simple enough to implement in a NIC ROM. Its reputation for slowness comes from its default stop-and-wait protocol with 512-byte blocks; modern servers and clients negotiate larger block sizes (`blksize`, RFC 2348) and windows (`windowsize`, RFC 7440), which makes it adequate for the small bootloader. Large kernels and initramfs should not travel over TFTP on big clusters; they should travel over HTTP. TFTP has no authentication or encryption, and in a "boot storm" (a rack power-cycles) hundreds of simultaneous UDP transfers can overwhelm a single server: stage boot, spread over several servers, rate-limit, or use HTTP.

### iPXE

**iPXE** is an open-source network boot firmware that adds a scriptable shell, HTTP/HTTPS, iSCSI, and many NIC drivers. The usual pattern is **chain loading**: PXE ROM fetches `undionly.kpxe` (BIOS) or `ipxe.efi` (UEFI) over TFTP, then iPXE starts, re-runs DHCP and recognises itself via DHCP **option 175** (the dnsmasq tag `ipxe`), and the server then hands it an HTTP URL to a script instead of another binary. This avoids the infinite loop where iPXE keeps being chain-loaded. A script is a few lines:

```text
#!ipxe
dhcp
kernel http://10.10.0.1:8080/images/dgx-os-24.04/vmlinuz ip=dhcp root=live:http://.../rootfs.squashfs hostname=gpu001
initrd http://10.10.0.1:8080/images/dgx-os-24.04/initrd.img
boot || goto failed
```

Scripts can branch on variables (`${mac}`, `${hostname}`, `${uuid}`, `${serial}`, `${asset}`), chain per-node scripts, and fall back to a discovery or rescue image. Because they run as text on an HTTP server, per-node and per-role images are easy to manage and audit.

### UEFI HTTP Boot

Modern UEFI firmware can boot directly over HTTP(S) without PXE/TFTP: the DHCP offer carries a boot URL in option 67 and vendor class `HTTPClient` (client architecture 16). The firmware downloads the boot file (often `grubx64.efi` or `shimx64.efi`) over TCP, which allows full-speed transfer, TLS, and standard web servers. Differences from PXE: the DHCP server must answer HTTPClient requests with a URL (not a filename relative to TFTP) and option 60 `HTTPClient`; DNS names require the firmware to resolve; HTTPS needs the CA certificate enrolled in firmware. NVIDIA DGX systems and many servers support UEFI HTTP Boot; BCM uses its own boot flow built on these primitives (Part 8). The NVIDIA-DevOps note that "TFTP has no window scaling and needs an ACK per 512-byte block" is the default behaviour only, as above; the conclusion (use HTTP for large payloads) stands.

A Kea client-class sketch for serving different boot files (general knowledge, adapt and validate with `kea-dhcp4 -t`):

```json
{ "Dhcp4": {
  "client-classes": [
    { "name": "HTTPClient", "test": "option[93].hex == 0x0010",
      "option-data": [ { "name": "vendor-class-identifier", "data": "HTTPClient" } ],
      "boot-file-name": "http://10.10.0.1:8080/boot/shimx64.efi" },
    { "name": "UEFI_PXE", "test": "option[93].hex == 0x0007", "boot-file-name": "ipxe.efi" }
  ] } }
```

(The class test must exist: a bare `boot-file-name` at the subnet level, as in some tutorials, sends the same file to every client, including PXE clients that cannot fetch HTTP URLs.)

## 3. A tested generator

Hand-editing DHCP files for a thousand nodes is how typos reach production. `code/part06/gen_provision.py` reads an inventory CSV (`name,mac,ip,bmc_mac,bmc_ip,role,image`), **validates** it (hostname syntax, MAC syntax, subnet membership, duplicates), then emits a `dnsmasq.conf` and one iPXE script per node plus a `boot.ipxe` dispatcher. Using option names from the dnsmasq(8) manual (`dhcp-range`, `dhcp-host`, `dhcp-match` with `option:client-arch` and the special number 175 for iPXE, `dhcp-boot=[tag:<tag>,]<filename>`, `enable-tftp`, `tftp-root`, `port=0`). Input of three nodes produced:

```text
# DHCP+TFTP only; DNS is served elsewhere
port=0
enable-tftp
tftp-root=/srv/tftp
dhcp-authoritative
# discovery pools for unknown machines
dhcp-range=10.10.3.232,10.10.7.207,255.255.0.0,1h
dhcp-range=10.20.3.232,10.20.7.207,255.255.0.0,1h
dhcp-match=set:ipxe,175
dhcp-match=set:efi64,option:client-arch,7
dhcp-match=set:efi64,option:client-arch,9
dhcp-boot=tag:!ipxe,tag:efi64,ipxe.efi
dhcp-boot=tag:!ipxe,tag:!efi64,undionly.kpxe
dhcp-boot=tag:ipxe,http://10.10.0.1:8080/boot.ipxe
dhcp-host=aa:bb:cc:00:00:01,gpu001,10.10.1.1,set:gpu
dhcp-host=aa:bb:cc:10:00:01,gpu001-bmc,10.20.1.1
...
```

and `ipxe/gpu001.ipxe` with the kernel/initrd/root lines for that node's image. A second, deliberately broken inventory (duplicate MAC and IP, BMC address outside its subnet, uppercase/underscore hostname, malformed MAC) was rejected with five errors and no files written:

```text
ERROR gpu002: bmc_ip 10.30.1.2 not in 10.20.0.0/16
ERROR duplicate mac aa:bb:cc:00:00:01 (gpu001 and gpu002)
ERROR duplicate ip 10.10.1.1 (gpu001 and gpu002)
ERROR GPU_3: invalid hostname
ERROR GPU_3: bad mac 'aa:bb:cc:00:00:zz'
```

Limits: the discovery pool arithmetic is naive (fixed offsets), dnsmasq itself was not available to run its `--test` syntax check (do that in CI: `dnsmasq --test -C dnsmasq.conf`), one image per node, no IPv6, no secure boot signing. The principle matters more than the script: **inventory is the source of truth (in Git); everything else is generated and validated**. The same pattern drives BCM, MAAS and Foreman, which keep the inventory in a database.

## 4. Stateless, stateful and hybrid nodes

| Design | How it works | Pros | Cons |
|---|---|---|---|
| **Stateful (installed)** | OS on local disk installed by Kickstart/preseed/autoinstall; config management maintains it | Boots fast, survives provisioning-server outage, familiar | Drift between nodes; reinstall is slow; disk wear/failure |
| **Stateless (diskless/RAM-root)** | Image downloaded at every boot into RAM (squashfs + overlay or tmpfs); reboot = clean state | Perfect consistency; reimage = reboot; replace a node with no residue | Needs RAM for the OS (GBs, trivial on GPU nodes with 1-2 TB), boot-time image download, provisioning must be highly available |
| **NFS root** | Root mounted read-only (often with per-node overlay) from an NFS server | Smaller RAM, changes visible instantly | NFS server becomes critical path and bottleneck; boot storms; latency |
| **Hybrid** | Read-only image in RAM plus local NVMe for scratch/logs/containers | Best of both; the common GPU-cluster choice | Need to manage persistent per-node state (SSH host keys, machine-id, logs) |

Compression and layering: root image as a squashfs (compressed, read-only), writable layer as tmpfs or overlayfs on local NVMe, optional "node-local config overlay" applied at boot. Persistent identity needs deliberate handling: SSH host keys, `machine-id`, hostname (from DHCP/hostname hook), Munge key (6.7), GPU/NIC configuration, and credentials; inject them from the provisioning server or a secret store at first boot, not baked into shared images.

The book's chapter on booting describes the classic composition for diskless nodes: PXE ROM, DHCP, TFTP kernel/initrd, **NFS-root** (and a read-only common tree with per-node writable parts), and it also covers building an initrd for that. Today's equivalents use HTTP-delivered squashfs and `dracut` (RHEL family) or `initramfs-tools`/`mkinitramfs` (Debian family) with live-boot hooks, or vendor tooling.

## 5. Image management

An **image** is the node's root file system plus kernel and initramfs. Good practice:

1. **Build reproducibly** from a definition under version control: `debootstrap`/`mmdebstrap` (Debian family), `dnf --installroot` or `mock`/`kiwi` (RHEL family), `mkosi`, `Packer` with a chroot/QEMU builder, container-based builds (build a container image, export the rootfs), or the cluster manager's image tooling (BCM software images, Warewulf containers). Pin package repositories to snapshots (or a local mirror) so rebuilds are repeatable.
2. **Layer** by role: a base OS layer, a GPU layer (driver, CUDA, DCGM, NCCL, fabric manager, Mellanox OFED/DOCA), a Slurm layer, and role overlays (login, compute, storage gateway). Keep drivers coupled to the kernel in the same image build.
3. **Test before promoting**: boot the candidate on a canary node group; run health checks (6.14), a GPU smoke test, NCCL test, a small Slurm job, storage mount checks; only then promote. Keep the previous image for instant rollback (a pointer change, since images are files).
4. **Version and sign**: semantic names with date (`dgx-os-24.04-2026-10-24`), store checksums, sign with a key if secure boot/shim chain is used.
5. **Roll out in waves** (rings): nodes assigned to an image via inventory attribute or iPXE script; drain nodes via Slurm before rebooting (`scontrol reboot ASAP nextstate=resume`, 6.14).
6. **Keep the image minimal**; put frequently changing software in modules/containers (6.6, 6.13), not in the base image.
7. **Config at boot**: cloud-init, Ignition, systemd units, or cluster-manager agents apply node-specific configuration (hostname, network, mounts, Slurm node name) from metadata; avoid per-node image builds.
8. **Firmware and BIOS** state is part of provisioning (settings via Redfish, Part 7; firmware baselines, 6.14/Part 9): enforce a known BIOS profile (boot mode UEFI, SR-IOV, NUMA, power profile) before the OS image matters.
9. **Security**: restrict who can change boot scripts and images; serve images only on the provisioning VLAN; use HTTPS with a private CA where firmware supports it; keep BMC and provisioning networks isolated (Part 18).

## 6. Node identity and lifecycle

A node's lifecycle: **racked** (physical), **discovered** (MAC seen by DHCP in the discovery pool, or imported from a vendor manifest), **registered** (named, assigned role/image, BMC credentials set), **provisioned** (image booted), **configured** (first-boot config, joins Slurm/Kubernetes), **in service**, **drained/failed** (6.14), **replaced** (new hardware inherits the old name by updating MAC addresses in inventory) or **decommissioned**. Good inventories also track serial numbers, asset tags, rack/U position, switch ports (from LLDP), firmware versions and warranty.

Discovery methods: DHCP logs showing unknown MACs, switch MAC tables per port (maps MAC to rack position), BMC Redfish queries (Part 7), or vendor-supplied CSVs. Use LLDP/port mapping so that a node's identity follows its physical location, which makes replacement a one-line inventory edit.

## 7. Cluster managers built on this foundation

(Detailed in 6.23 and Part 8; the SCL book's chapters 25 and 26.)

- **ROCKS** (historic Rocks Clusters, CentOS-based; "Rolls" bundle software; installs nodes via Kickstart) and **Parallel Knoppix/PelicanHPC** (live-CD clusters for teaching) are the out-of-the-box stacks the book reviews; both are largely of historic interest now.
- **xCAT** (IBM/Lenovo lineage): DHCP/TFTP/DNS, node definitions in a database, `nodeset`, `rpower`, `rinstall`, stateless/statelite/diskful images, hierarchies of service nodes.
- **Warewulf 4**: container-based stateless provisioning, simple and popular.
- **Canonical MAAS**: bare-metal cloud (discover, commission, deploy Ubuntu), API-driven; **Foreman** with Katello/Puppet: lifecycle management for mixed fleets.
- **NVIDIA Base Command Manager (BCM)**: the NVIDIA-supported cluster manager: head node, software images, categories, node discovery, provisioning, health, Slurm/Kubernetes integration (Part 8).

## 8. Boot triage

A staged method (the NVIDIA-DevOps notes call it D-T-B-I; the stages are standard):

| Stage | Question | Checks |
|---|---|---|
| **D**HCP | Did the node get an address and the right boot information? | Console/BMC serial-over-LAN shows "DHCP..."; on the provisioning host `tcpdump -i eth1 -n -vvv port 67 or port 68`; server logs (`log-dhcp` in dnsmasq, Kea logs); correct VLAN/relay; MAC in inventory; only one DHCP server answering; option 93 value seen |
| **T**ransfer | Did the bootloader download? | TFTP: `tcpdump port 69`, server log, file path under `tftp-root`, permissions, firewall (TFTP uses ephemeral ports after the first packet, which stateful firewalls must allow); HTTP: web server access log, status codes, URL reachable from the node network |
| **B**oot-mode | Does the binary match the firmware? | UEFI vs BIOS (`ipxe.efi` vs `undionly.kpxe`), architecture (x86_64 vs ARM64), Secure Boot signing (shim), correct NIC driver in iPXE (some NICs need a specific build) |
| **I**mage | Did kernel, initramfs and root load and start the OS? | Serial console output of the kernel, initramfs shell (`rd.break`), missing NIC driver in initramfs (no network to fetch rootfs), wrong `root=`/URL, not enough RAM for the image, DNS failures, time/TLS errors |

Common specific causes: two DHCP servers; PXE client sent to relay that drops option 60/93; boot order (disk before network after the first install, so the node does not reimage: set via IPMI `chassis bootdev pxe options=efiboot` or Redfish `BootSourceOverrideTarget`); firmware set to legacy while the server offers UEFI binaries; Secure Boot rejecting unsigned iPXE; a big initramfs over TFTP timing out; storm of 500 nodes against one HTTP server (add caching or multiple mirrors); node's MAC changed after a NIC/board swap; stale ARP/DHCP lease for a replaced node; wrong VLAN on the switch port (PXE only works untagged unless the NIC firmware supports VLAN tagging).

Always get **serial-over-LAN** or BMC console access (Part 7) before debugging remotely.

## 9. Lab

Tested: run the generator on the sample inventory and the broken one; extend `validate()` to check that BMC IPs are in a different /16 than node IPs and that role values come from an allowed list; add a `--check` mode that only validates.

Untested (two VMs on a host-only network): 1) set up dnsmasq (DHCP+TFTP) with a BIOS client and boot an iPXE ROM, then chain to an HTTP script that boots a small live image. 2) Switch the VM to UEFI and observe the different boot file; add `ipxe.efi`. 3) Add per-node scripts; boot two clients with different images. 4) Intentionally run two DHCP servers and capture the intermittent failure with tcpdump. 5) Boot a stateless node with squashfs+overlay; reboot to show clean state; add a persistent overlay for logs. 6) Practise D-T-B-I: break each stage and write the symptom. 7) Time a boot storm of ten VMs against one TFTP server vs an HTTP server.

## 10. Interview angles

- Walk through a PXE boot from power-on to a running OS.
- PXE versus iPXE versus UEFI HTTP Boot: differences and when to use each.
- Why chain-load iPXE, and how does option 175 prevent a loop?
- Stateless versus stateful nodes: trade-offs for a GPU cluster.
- A node reimages itself every reboot. Why, and how do you stop it?
- How do you roll out a new OS image to 1,000 nodes safely?
- How do you keep node identity when hardware is replaced?
- Two DHCP servers on one VLAN: symptoms and fix.
- What belongs in the image versus modules/containers?

## 11. Checkpoint questions (30)

1. List the steps of the boot chain.
2. What is the role of the initramfs?
3. Compare SysV init and systemd.
4. What information does a DHCP offer carry for network boot?
5. What are DHCP options 60 and 93 for?
6. Name three DHCP servers.
7. What is PXE? What protocol transfers the NBP?
8. Why is TFTP slow by default and how is it improved?
9. What is a boot storm?
10. What is iPXE and what does it add?
11. What does dnsmasq tag `ipxe` match (option 175) and why?
12. What is UEFI HTTP Boot and what does the DHCP offer contain?
13. Why does the generator emit separate BIOS and UEFI boot files?
14. List validation checks in `gen_provision.py`.
15. What does `dhcp-host` do?
16. Describe stateless, stateful, NFS-root, hybrid designs.
17. What per-node state must be injected at boot?
18. Name three image build tools.
19. What are image layers for a GPU node?
20. How do you promote and roll back an image?
21. How are images tied to Slurm draining?
22. List node lifecycle states.
23. How do switch port maps help identity?
24. Name five cluster managers and one trait each.
25. State D-T-B-I and one check per stage.
26. How do you stop reimaging after install?
27. Why does PXE fail across a VLAN trunk misconfiguration?
28. What security measures protect boot infrastructure?
29. Why firmware/BIOS baselines belong to provisioning?
30. Why is inventory-as-source-of-truth valuable?

## 12. Sources and review notes

- Boot chain, SysV and systemd init, DHCP/TFTP/PXE/NFS-root, node setup, out-of-the-box stacks (ROCKS, Parallel Knoppix/PelicanHPC), xCAT, MAAS, Foreman, BCM: *Supercomputers for Linux SysAdmins* chapters 23 to 26, restated in my words. Network boot comparison (PXE/TFTP vs UEFI HTTP Boot), Kea DHCP and the D-T-B-I triage: the author's NVIDIA-DevOps volume-10 chapter 1 section 7, with two corrections: the TFTP slowness description (defaults, not a hard limit) and the Kea snippet (client classes added so that PXE clients are not given an HTTP URL).
- dnsmasq options verified in dnsmasq(8) (mirror commit `cf08eee`).
- Original and run: `gen_provision.py`.
- Unverified: iPXE script syntax details beyond common usage, Kea class tests, DHCP option numbers for architectures (standard values from the PXE/UEFI specifications as I recall them), BCM and MAAS specifics, firmware behaviours. No network boot was performed.
