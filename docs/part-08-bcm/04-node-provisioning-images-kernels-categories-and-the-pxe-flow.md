---
id: "c08-04"
title: "8.4 Node provisioning: images, kernels, categories and the PXE flow"
sidebar_label: "8.4 Node provisioning: images, kernels, categories and the PXE flow"
sidebar_position: 4
description: "How a blank node becomes a working cluster member in BCM: PXE and the boot menu, the 13 steps of the node installer, install modes and why NOSYNC is not data protection, how new nodes are identified, provisioning nodes at scale, software images and kernels, live image updates and exclude lists, node states, and a troubleshooting checklist, with the manual's rules reproduced in a tested model"
status: "drafted"
tier: "1b"
level: "A"
lab_venue: "Nebius GPU"
---

# 8.4 Node provisioning: images, kernels, categories and the PXE flow

| | |
|---|---|
| Level | Beginner to intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 8: NVIDIA Base Command Manager |
| Status | Drafted from the BCM 11 Administrator Manual, chapter 5 (read in full except the InfiniBand and VLAN provisioning sections 5.3.3 and 5.3.4) and chapter 9 sections 9.3 to 9.5 (kernels, packages in images, node-to-image sync). **No BCM system was available.** `code/part08/bcm_provision.py` is **my model of the rules the manual states**, and `provision_lab.py` checks 72 of them. It tests my reading of the manual, not BCM itself. Every command shown is from the manual and untested here |

## Why this matters for AI infrastructure

A GPU cluster is only as good as its worst node. Provisioning is how BCM makes 500 nodes identical: every node boots, gets the same software image, and joins the cluster without anyone logging in. When it goes wrong you get nodes that will not boot, nodes that quietly lost their local data, or nodes running an old image. This chapter is the "how a node comes up" story, step by step, and where each step can break.

## Prerequisites and outcomes

You need chapters 8.1 to 8.3. After this chapter you can:

- walk through the PXE boot and the 13 steps of the node installer
- choose and explain an install mode, and say which ones can erase local data
- explain how BCM recognises a new node and what the seven identification cases mean
- scale provisioning with boot and provisioning roles
- update a running node from the image safely (dry run first)
- manage software images and kernels without breaking the next reboot
- read node states and use `close`, `open`, `mute` and `drain` correctly
- work through the troubleshooting list in order

## 1. The big picture

**Booting** and **provisioning** are different jobs. Booting gets a small program (the boot loader, then a kernel and a ramdisk) onto the node. Provisioning copies the **software image** (a complete Linux filesystem) onto the node's disk. The head node does both by default; you can hand each job to other nodes when the cluster grows.

```mermaid
flowchart LR
  A[Power on] --> B[PXE: DHCP + boot loader]
  B --> C[Kernel + ramdisk]
  C --> D[Node installer: 13 steps]
  D --> E[Image copied to disk]
  E --> F[Hand over to local init]
  F --> G[CMDaemon connects: UP]
```

## 2. Before the kernel loads (5.1)

- Nodes **boot from the network by default**. On x86_64 this is PXE. The head node runs a TFTP server, and the files live under `/tftpboot/pxelinux.cfg/`.
- The boot loader shows a **menu**. If nobody picks anything within the timeout, the **AUTO** install mode runs. The timeout is 5 seconds, written `TIMEOUT 50` (deciseconds). Do not change the menu files unless you must.
- A per-node **PXE label** (`set pxelabel MEMTEST`, for example) overrides the menu default for one node or a whole category. Setting it to `localdrive` makes the node boot from its own disk, which the manual discourages because it makes management harder.
- The boot protocol is `bootloaderprotocol`, **HTTP by default**. Even then the first stage is still TFTP on x86_64, and HTTP takes over for the kernel and ramdisk. Set `tftp` if your hardware cannot switch over. **HTTPS** almost never works. **ARMv8 nodes boot over TFTP only** and get a GRUB binary.
- On disked nodes BCM also installs **iPXE** on the drive as a fallback if the BIOS PXE attempt fails.
- **Boot role.** DHCP and TFTP can be overwhelmed when hundreds of nodes boot together: random nodes fail to boot, and a different set each time. The fix is to give the `boot` role to one regular node per rack or subnet. The head node always has the boot role.

## 3. The node installer: 13 steps (5.4)

After the ramdisk is up, a program called the **node installer** runs on the node.

```mermaid
flowchart TB
  S1[1 request a node certificate] --> S2[2 decide node configuration]
  S2 --> S3[3 bring up network interfaces]
  S3 --> S4[4 decide install mode]
  S4 --> S5[5 initialize script]
  S5 --> S6[6 check partitions, mount]
  S6 --> S7[7 sync disk with the image]
  S7 --> S8[8 write network config files]
  S8 --> S9[9 write fstab]
  S9 --> S10[10 boot record and SELinux]
  S10 --> S11[11 finalize script]
  S11 --> S12[12 unload drivers]
  S12 --> S13[13 switch to local init]
```

**1. Certificate.** The node asks the head node for a certificate. The setting `signinstallercertificates` is `AUTO` (default) or `MANUAL`. A network can refine this with `allowautosign`: Always, Automatic (default; only networks of type internal), Never, or Secret (for edge sites). In an untrusted network use MANUAL and approve each request in `cert` mode (`listrequests`, `issuecertificate`). The certificate is stored under `/cm/node-installer/certificates/<MAC>/`; if a node gets a bad certificate, delete that directory so it can ask again.

**2. Who am I?** The installer asks CMDaemon whether the booting MAC address belongs to a known node, and which switch port the node is on. Section 4 below covers the seven cases.

**3. Network.** It brings up the interfaces, but first checks that each IP address is not already in use. `BOOTIF` is a special name that means "whichever interface I booted from". Non-provisioning interfaces stay down unless `bringupduringinstall` is `yes` (up during install) or `yesandkeep` (up and stays up).

**4. Install mode.** See section 5.

**5. Initialize script.** Runs before disks are touched (category script first, then node script). For hardware the standard flow does not know how to start.

**6. Partitions.** Checks (or creates) the layout from the node's disk-layout XML, then mounts.

**7. Sync.** Copies the image to the node using rsync. Which files are skipped depends on the exclude lists (section 8). `provisioninginterface` picks the interface that receives the data (default `BOOTIF`; choose the fastest one). `provisioningtransport` is `rsyncdaemon` (unencrypted) or `rsyncssh` (encrypted, heavy on the provisioner).

**8 and 9.** Writes the interface files and `/etc/fstab`.

**10.** Optionally writes a boot record so the node can start from its own disk (`installbootrecord`), and sets up SELinux if configured.

**11. Finalize script.** Runs just before the handover. The right place to append a setting that the installer would otherwise overwrite every boot.

**12. Unload drivers.** The IPMI drivers are needed to configure the BMC, then keep using CPU and power; by default they are unloaded here (`removeModulesBeforeInit`).

**13.** Hands over to `/sbin/init` on the local disk. The node then behaves like any Linux machine.

## 4. Who is this node? The seven cases (5.4.2)

A new or returning node can be recognised by its **MAC address**, by the **switch port** it is plugged into, or both. The manual has a seven-row truth table:

| # | Node known? | Port detected? | Port configuration | Result |
|---|---|---|---|---|
| 1 | no | yes | found | suggested, accepted after a timeout |
| 2 | no | yes | none | **manual**: dialog loops |
| 3 | no | no | none | **manual**: dialog loops |
| 4 | yes | yes | same as the MAC's | suggested, accepted |
| 5 | yes | yes | **differs** from the MAC's | **manual**: port mismatch |
| 6 | yes | no | the MAC's config expects a port | **manual**: port mismatch |
| 7 | yes | yes | the MAC's config has no port | suggested, accepted |

Practical meaning: a **brand-new node with no switch configuration always stops for a human** (cases 2 and 3). A **port mismatch (cases 5 and 6)** usually means two nodes were swapped by mistake, and the installer protects you by stopping. For case 6 the manual's simplest fix is `cmsh -c "device clear node001 switchports; commit"` (or enable port detection on the switch).

**Naming new nodes: `newnodes`.** In cmsh device mode, `newnodes` lists MAC addresses waiting to be named. `newnodes -s -n node001..node032` assigns names in the order the nodes arrived. So **power nodes on in the order you want them named**. `-w` assigns without saving; `-s` saves; `-o 1` skips the first arrival; `-f` forces a name that is already taken (and moves it to the new MAC; use with care). The lab checks the manual's `-o` example.

**Node objects can also be created in advance** (`add physicalnode node002 10.141.0.2` in device mode, the Base View node creation wizard, or `foreach --clone`). A node object with no MAC address is a **placeholder**; the installer lets someone pick the identity at the console.

## 5. Install modes (5.4.4)

The install mode decides what the installer does to the node's disk. Five values:

| Mode | Disk check | What happens | Wipes data? |
|---|---|---|---|
| **FULL** | none | repartition, new filesystems, full image copy | **yes** |
| **AUTO** (default) | yes | healthy: quick incremental sync. Unhealthy: becomes FULL | only if unhealthy |
| **MAIN** | none | drops into **maintenance mode**; drive untouched | no |
| **NOSYNC** | yes | healthy: **no sync**, local contents kept. Unhealthy: rewrite partitions and FULL sync | only if unhealthy |
| **SKIP** | none | no check and no sync, for data recovery | no |

**The trap, in the manual's words:** NOSYNC "should therefore not be regarded as a way to protect data". The manual's own example: a burn run (chapter 8.2) destroys the partition layout; on the next reboot the layout no longer matches, so even NOSYNC does a FULL sync. A failing drive that renumbers (`/dev/sdb` becomes `/dev/sda`) or a node with a new MAC address can do the same to AUTO and NOSYNC.

**Where the mode comes from.** The manual lists six places, in this order: the category's `newnodeinstallmode` (default FULL, for new nodes), the PXE menu choice (this boot only, default AUTO), the node's `nextinstallmode` (cleared after one boot), the node's `installmode`, the category's `installmode` (default AUTO), and a console dialog (a last chance to overrule). I could not work out from the text which one wins when several are set, so check on a test node before relying on it.

**Protecting nodes that hold data.** Set `datanode yes` on a node or category (Boolean: category OR node). Then any FULL install, even one that AUTO or NOSYNC falls back to, **waits for a human to confirm**: at the console, or `installerinteractions -w -n node001 --confirm` (also `--deny`, to go to maintenance mode). The manual also describes XML assertions (halt if the expected drive is missing) and `blockdevicesclearedonnextboot` (the opposite: erase named devices on the next boot, ignoring `datanode`; be careful).

**A mass planned reboot without a re-sync:** `device foreach -n node001..node999 (set nextinstallmode nosync)`, then commit.

## 6. Scaling provisioning: provisioning nodes (5.2)

The head node always has a **provisioning role**. Give the role to other nodes to share image traffic. Its parameters:

| Parameter | Meaning |
|---|---|
| `provisioningslots` | How many nodes it serves at once. **Default 10.** Lower it if the NIC or disk saturates |
| `allimages` | `onlocaldisk` (default), `onlocaldiskexceptsharedimages`, `onsharedstorage`, or `no` (then only `localimages` / `sharedimages`) |
| `nodegroups` | If set, this provisioner serves only nodes in those groups, and those nodes only use provisioners that list the group. Nodes in no group use provisioners with no nodegroups. Use it to build a rack-by-rack hierarchy |

The head node's housekeeping rules:

- First come, first served. Among eligible provisioners, the one with the **fewest started tasks** gets the request.
- A cluster-wide ceiling `MaxNumberOfProvisioningThreads` (in the head node's `cmd.conf`) limits all provisioning together.
- No free provisioner: the request is **deferred** and retried when a task finishes. A **locked image** also defers.
- A failed transfer is retried **5 times**, then fails. A provisioner that loses connectivity keeps its requests for **180 seconds**, then they fail.
- **Cold start order:** head node, then provisioning nodes (they must be provisioned too), then everything else.
- Provisioners keep a **copy of every image they serve**, in the same path as the head node. Give them disk for it.
- `updateprovisioners` pushes images to the provisioners. It runs by itself after changes made through cmsh or Base View, **and every midnight (UTC)** by default. After you change an image **outside** BCM (a file copied in from the shell) you must run it yourself. A provisioner being updated serves nobody until it finishes.
- `dirtyautoupdatetimeout` (default **300 s**) stops it from running too often. 0 disables the automatic trigger.
- `drain` and `undrain` (in `softwareimage` mode) stop a provisioner from taking new requests while active ones finish. `provisioningstatus` shows slots and state; `synclog` shows what rsync did; `syncinfo` gives statistics.

What this does **not** fix: CMDaemon, the database and monitoring data still live on the head node (and its HA partner). Provisioning nodes scale image delivery and booting, not the whole management plane.

## 7. Software images and kernels (5.3, chapter 9)

A **software image** is a directory such as `/cm/images/default-image` on the head node. It contains a kernel and a ramdisk. The ramdisk holds the drivers needed to reach the network and the disk; the rest of the image arrives later.

**Kernel modules** (for the ramdisk) can be set on the image, the category or the node. **A lower level replaces the higher level completely; it does not add to it.** A wrong list at a lower level can stop a node from booting. Normally set them on the image only. Changing the list makes CMDaemon rebuild the ramdisk (`createramdisk`).

**Safe habits from the manual:**

1. **Clone a working image before changing it.**
2. Change an image with `cm-chroot-sw-img /cm/images/default-image` (it mounts the special directories for you) and use `yum`, `zypper` or `apt` inside it. Or use `yum --installroot`.
3. **Lock the image first** (`softwareimage lock default-image`) if package tools complain that it is being provisioned; unlock afterwards.
4. A new kernel in an image is **not used until you set the image's `kernelversion`** (commit; tab completion lists the choices). BCM keeps old kernels instead of the distribution's "keep 3".
5. After a kernel or module change made with a package manager, **run `createramdisk`**. The package manager updates the normal ramdisk, not BCM's extended one. If you forget, nodes fail while loading the ramdisk.
6. Inside a chroot, `uname -a` shows the kernel running **outside** the chroot. To see the kernel the node will load: `cmsh -c "softwareimage; use default-image; get kernelversion"`.
7. A `chrootprocess` health check warns when a daemon is running inside an image.
8. Keep the **node-installer image** (`/cm/node-installer`) updated too.
9. `yum --exclude kernel update` (or `apt-mark hold`, `zypper addlock`) keeps a kernel from changing.
10. On an HA head node, change the passive head first when installing a kernel, because the active head's network might stop and trigger a failover.

**Changing a node and saving it back (`grabimage`).** The cleanest way to change an image is directly (chroot). `grabimage` copies from a running node **into** the image, using `excludelistgrab`; `grabimage -i <newimage>` makes a new image using `excludelistgrabnew`. The manual warns that unwanted changes can be captured, so compare the images (its tip: `vimdiff <(cd image1; find . | sort) <(cd image2; find . | sort)`).

## 8. Updating a running node: `imageupdate` and exclude lists (5.6)

Three directions, three lists:

| Operation | List used | Direction |
|---|---|---|
| `imageupdate` | `excludelistupdate` | image to **running** node (sync) |
| install, FULL | `excludelistfullinstall` | image to starting node (full) |
| install, AUTO healthy | `excludelistsyncinstall` | image to starting node (sync) |
| `grabimage` | `excludelistgrab` | node to existing image (sync) |
| `grabimage -i` | `excludelistgrabnew` | node to new image (full) |

**`imageupdate` is a dry run by default.** It writes nothing. Read the result with `synclog`, then run `imageupdate -n node001 -w` to apply.

**The update list has two parts.** Paths on the first part: if they exist on the node they are left alone; if missing, they are copied from the image. Paths on the second part (prefixed `no-new-files:`): left alone if present, **not copied** if missing. **Everything on neither part is overwritten from the image, and node-only files are deleted.** The manual: content not on the lists "is normally not protected from deletion".

**Protected automatically:** statically imported filesystems of these types are skipped: NFS, Lustre, FUSE, CephFS, CIFS, PanFS, FhGFS, BeeGFS, GlusterFS and GPFS. **Not protected:** **autofs mounts** (BCM cannot see them reliably) and filesystems you mounted by hand into the image. Add those to the exclude list yourself, or an update can wipe them.

**Two more traps.** (1) **The five-minute trap:** if an image changed within `dirtyautoupdatetimeout`, the provisioners may not have it, so nodes do not get it; run `updateprovisioners` right before `imageupdate`. (2) For larger changes the manual suggests a **reboot** instead (a reboot does an AUTO install of the latest image and restarts all services). **Reinstall node** in Base View is like a reboot but forces a FULL install.

`excludelistmanipulatescript` lets you rewrite the lists on the fly, and `excludelist get full /` shows what a node would really use. Be careful: the manual notes that saving a script with a single stray space can do harm.

## 9. Node states (5.5)

A healthy boot goes **BOOTING, INSTALLING (with messages such as "checking disks", "provisioning started"), INSTALLER_CALLINGINIT, UP**. UP means the node's CMDaemon has connected to the head node.

```mermaid
stateDiagram-v2
  [*] --> DOWN
  DOWN --> BOOTING: power on
  BOOTING --> INSTALLING
  INSTALLING --> INSTALLER_CALLINGINIT: handover
  INSTALLER_CALLINGINIT --> UP: CMDaemon connects
  UP --> DOWN: CMDaemon lost
  INSTALLING --> INSTALLER_FAILED: unrecoverable problem
  INSTALLING --> INSTALLER_UNREACHABLE: pings lost
  INSTALLING --> INSTALLER_REBOOTING: kernel reboot
  INSTALLER_REBOOTING --> INSTALLER_FAILED: too slow
  INSTALLER_CALLINGINIT --> INSTALLER_FAILED: too slow
```

- `BOOTING` can be seen only if an interface is called `BOOTIF` (or one interface carries the revision tag `bootif`).
- **CLOSED** is added by the administrator (`close -m "fan dead" -n node001`) and shows as `UP/CLOSED` or `DOWN/CLOSED`. It stays through reboots. The only way out is `open` (through a short OPENING state, about 5 seconds, never more than 30). OPEN is never printed.
- **A closed node keeps running jobs**, because the workload manager does not depend on CMDaemon. Drain first (not obligatory).
- **mute** keeps the state but silences alerts and triggers, for maintenance. Remember to `unmute`.
- `restart-required` appears after changes to network settings, disk setup, software image or category.

## 10. When a node will not boot: a checklist (5.8)

In this order:

1. **Does the network allow boot?** `network use internalnet; get nodebooting` must be yes. Is `lockdowndhcpd` on (new nodes get no lease)? Is a **rogue DHCP server** on the network (`nmap --script broadcast-dhcp-discover` can list them)?
2. **BIOS:** boot order (the boot NIC first); UEFI network boot can be buggy, try legacy; **spanning tree (STP) on the switch** makes nodes randomly fail to boot, so disable it on managed switches.
3. **Cables, switch, wrong interface.** Test with a direct cable. Since BCM 9.0 the consistent naming scheme (`eno1`) is the default and recommended.
4. **TFTP hung** (`ps ax | grep [t]ftp`) or the TFTP-to-HTTP switch hung: set `bootloaderprotocol tftp`.
5. **Node installer log:** `/var/log/node-installer` on the head node (facility `local5`); on the node console press Alt+F7. Debug logging is a field in `node-installer.conf`. No log at all can mean the image is **locked** (`provisioningstatus -a` says "request deferred") or `nodegroups` is wrong.
6. **Provisioning log:** `synclog`. An rsync exit code 23 is a transfer error (the manual's example: a missing `lscratch` mount point in the image).
7. **Ramdisk fails** after an image update: run `createramdisk`; check the kernel module lists at every level. "No space left on device" while making the ramdisk: raise `RamdiskCreationTmpfsSize` (the default tmpfs was 256 MB before 11.31.0 and 512 MB from then on).
8. **Ramdisk cannot start the network:** add the NIC's kernel module to the image (`kernelmodules`, then `add e1000`, as in the manual).
9. **Cannot create the disk layout:** the log shows the device not found; check the layout XML against the real device name.
10. **Cannot start the BMC:** add IPMI modules to the image; if the BMC still fails, `setupBmc`, `failOnMissingBmc` and `failOnFailedBmcCommand` in `node-installer.conf` loosen the checks; a BMC in a glitchy state may need a **cold reset** (`ipmitool ... mc reset cold`). Read the BMC's SEL for CPU, ECC and memory errors. (Part 7 shows the Redfish way.)

## 11. Booting from the node's own disk (5.4.10)

Four things must all be true: `installbootrecord yes`, **the BIOS tries the disk before the network**, a **working bootloader** (default syslinux, a custom image may need `grub`), and **`BOOTIF` renamed to a real device name** such as `eth0`, because `BOOTIF` means nothing when the node did not PXE boot. This is a step toward a standalone node; most AI clusters keep netbooting instead.

## 12. Common first mistakes

1. Treating NOSYNC as data protection.
2. Not setting `datanode` on nodes that hold local data.
3. Powering nodes on in random order and then wondering about names.
4. Editing an image by hand and forgetting `updateprovisioners`.
5. Running `imageupdate -w` without reading `synclog`.
6. Installing a kernel into an image and forgetting `kernelversion` and `createramdisk`.
7. Expecting kernel modules at node level to add to the image's list.
8. Leaving autofs mounts off the exclude list.
9. Closing a node and assuming its jobs stopped.
10. Leaving STP on a managed switch.

## 13. Exercises

1. Run `python3 provision_lab.py`. Pick four checks and explain each rule in your own words.
2. Add a fourth provisioner with `nodegroups={"rack-b"}` and show where nodes in `rack-b` and nodes in no group go.
3. A node has useful local data. Which settings keep it safe if its drive renumbers? Test them with `install_plan`.
4. Write the sequence of commands (from this chapter, untested) to put a new kernel into `gpu-image` safely.
5. For an update of 200 nodes, write a runbook: lock, update, `updateprovisioners`, dry run, review, `-w`, verify.
6. Use `sync_update` to show what happens to a file that is only on the node, with and without an exclude entry.

## 14. Interview angles

- "Walk me through a BCM node boot." PXE, kernel and ramdisk, certificate, identification, interfaces, install mode, disk check, rsync, config files, finalize script, init, CMDaemon connects.
- "A node lost its data after a reboot. Why?" A FULL install: forced mode, or AUTO and NOSYNC falling back after a partition or MAC change. Prevent with `datanode` and assertions.
- "How do you roll an image to 500 nodes?" Edit in a chroot, lock if needed, `updateprovisioners`, `imageupdate` dry run, review, `-w`, or reboot for larger changes.
- "What does CLOSED mean?" Monitoring stops; jobs do not. Only `open` clears it.
- "How does the head node avoid being the bottleneck?" Boot role, provisioning role, slots, nodegroups; but CMDaemon and the database stay on the head.

## 15. Checkpoint questions (20)

1. What is the difference between booting and provisioning?
2. Which protocol does the first PXE stage use on x86_64 even when `bootloaderprotocol` is HTTP?
3. What does the boot role fix?
4. Name the 13 node-installer steps (at least ten).
5. What does `signinstallercertificates` control, and what does `allowautosign` add?
6. What is `BOOTIF`?
7. Name the five install modes.
8. Which install modes can wipe a disk?
9. Why is NOSYNC not data protection?
10. What does `datanode` do, and how is it combined between category and node?
11. How do you give new nodes names in the order they were powered on?
12. What is a port mismatch and what usually causes it?
13. What is the default number of provisioning slots?
14. How is a provisioner chosen among several?
15. After how many failures does a provisioning request fail?
16. What does `dirtyautoupdatetimeout` do?
17. Is `imageupdate` a dry run by default? How do you apply it?
18. Which filesystems does BCM skip automatically, and which must you add yourself?
19. What replaces what when kernel modules are set at several levels?
20. What does CLOSED do to running jobs?

## 16. Sources and review notes

- **BCM 11 Administrator Manual, chapter 5:** 5.1 (PXE, labels, protocol, boot role), 5.2 (provisioning nodes, housekeeping), 5.3 (kernel modules; InfiniBand and VLAN provisioning 5.3.3 and 5.3.4 not read), 5.4 (all 13 steps), 5.5 (states), 5.6 (live updates and exclude lists), 5.7 (adding nodes), 5.8 (troubleshooting, to the BMC section).
- **Chapter 9:** 9.3 (kernels), 9.4 (packages in images, `cm-chroot-sw-img`), 9.5 (non-RPM software, `grabimage`). **Not read:** 9.1, 9.2 (packages on the head node), 9.6 (`cm-create-image`, only the introduction) and 9.7 (multi-distro and multi-arch, `cm-image`).
- **NVIDIA-DevOps notes**, volume 10 chapter 13: provisioning tiers, image drift and the remediation tiers. Its own preface says an earlier draft invented a "proxy tier", BitTorrent seeding and Pacemaker; it was rewritten against the manual, and the facts used here agree with the manual text I read. Its remediation-tier model is the author's design recommendation, not a BCM feature; chapter 8.11 covers it.
- **Run here:** `provision_lab.py` (72 checks): boot path, install modes and the datanode guard, the seven identification cases, `newnodes`, node states, the scheduler (slots, groups, fewest tasks, deferral, locks, retries, 180 s), the update timeout trap, kernel module override, standalone boot, exclude-list sync.
- **My own choices, not the manual's:** tie-breaking between equally loaded provisioners; the "automatic" reading for a known node with no ports involved; treating the six install-mode places as a list without a verified precedence.
- **Not verified:** everything about a real BCM system: screens, command output, defaults on a newer point release.
