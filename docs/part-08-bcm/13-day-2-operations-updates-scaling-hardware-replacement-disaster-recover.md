---
id: "c08-13"
title: "8.13 Day-2 operations: updates, scaling, hardware replacement, disaster recovery"
sidebar_label: "8.13 Day-2 operations: updates, scaling, hardware replacement, disaster recovery"
sidebar_position: 13
description: "Running a BCM cluster after it is built: version numbers and update rules, running commands on many nodes safely, getting support with cm-diagnose, backups and database recovery, image revision control, checking new hardware, replacing nodes, scaling out, Ansible, and change runbooks, with the manual's rules reproduced in a tested model"
status: "drafted"
tier: "1b"
level: "A"
lab_venue: "Nebius GPU"
---

# 8.13 Day-2 operations: updates, scaling, hardware replacement, disaster recovery

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 8: NVIDIA Base Command Manager |
| Status | Drafted (`ops_lab.py`: 45 checks pass; cluster commands **untested** on live BCM) |

## Why this matters for AI infrastructure

Think about a bad night on a cluster. Someone makes a change at 3 a.m., and in the morning you have to find out what changed and how to undo it. Building a cluster is a project with an end. Running it is a job that never ends. Packages need updating, nodes fail, racks get added, and disks die. BCM gives you the tools for all of this, but much of the safety is habit: back up first, change little, check the result, and know the way back. This chapter collects those habits along with the exact tools the manual provides.

## Prerequisites and outcomes

This chapter assumes you have worked through the rest of Part 8. When you finish it, you should be able to read BCM version numbers and follow the update rules, including the ones for HA. You will be able to run a command on many nodes without causing a power surge or cutting off your own tool. You will know how to ask for help the way BCM support wants, with `cm-diagnose`. You will also back up the cluster, recover a corrupted database, and work with image revisions. Finally, you can check new hardware, replace a node, scale out efficiently, use Ansible with BCM, and write a short runbook for the three kinds of change you will do most.

## 1. Version numbers and the update rules (chapter 9)

Suppose a colleague asks which BCM version your head nodes run. You can check with `cmsh -c "main; versioninfo"`, or read `/etc/cm-release`. The version string itself has a pattern, and once you can read that pattern, you know what kind of update a release is.

The major releases are 10.0 and 11.0, which you can also write as 10 and 11. Point releases use one of two formats. The calendar format puts the year and month in the number, so `11.25.08` means August 2025. It was used up to `10.25.03` and `11.25.08`. The semantic format starts at `11.30.0`, with `11.31.0` and `11.34.0` following it. In that format, a number above 0 in the last place is a backward-compatible bug fix.

A lowercase letter, as in `10.23.02a`, marks a hotfix. Letter suffixes are never used in semantic releases.

Different packages can sit at different point releases. For that reason, the manual says not to depend on the exact point release. Let the package manager keep the BCM packages consistent. To see which package versions go with which point releases, run `cm-package-release-info` with `-f cmdaemon,cluster-tools`.

BCM packages carry `cm` and a developer git hash in their filenames, which is how you tell them apart. An RPM name looks like `<package>-<version>-<revision>_cm<x.y>_<hash>.<arch>.rpm`, for example `cmdaemon-11.0-152061_cm11.0_ec0ea0f4d1.x86_64.rpm`. A DEB name looks like `<package>_<version>-<revision>-cm<x.y>-<hash>_<arch>.deb`, for example `cmdaemon_11.0-152061-cm11.0-ec0ea0f4d1_amd64.deb`. DEB files are used on Ubuntu only, and all other supported distributions use RPM.

To check whether a file came from BCM or from the base distribution, use `rpm -qf <path>` on RPM systems. On Ubuntu, run `dpkg -S <path>` and then `dpkg -s <pkg>`. Never replace a BCM-supplied package, the ones marked with `_cm` or `-cm`, with a distribution package. If you do, the cluster enters an unsupported state, and subtle failures follow.

The `cmsh` command `device packages` asks the nodes directly what they have installed. It does not depend on `rpm` or `dpkg`. The output shows the fields `Name`, `Type`, `Version`, `Arch`, `Size` and `Install date`.

Be careful with that command at scale. Suppose you run `packages -a` across 1,000 nodes. Each node returns about 100 KB, roughly 1,000 lines, so the total is about 100 MB, which is nearly a million lines. Instead, filter by package name with one or more `-f|--find` flags, as in `packages -f cmdaemon -f cuda-dcgm-libs`. To check for upgrades, use `packages --outdated`, which lists only the upgradable BCM packages, or `packages --outdated -a`, which lists all installed BCM packages and the versions available for them.

Updating within an OS major release or a BCM release is normal. Moving the OS to the next major release while keeping BCM is not supported. Going from RHEL 8 to RHEL 9, for example, means installing BCM again on the new OS. DGX OS upgrades follow NVIDIA's DGX OS documentation.

Each package manager has its own commands. On YUM systems, use `yum update`, and `yum list` shows what is available. On SUSE, run `zypper refresh; zypper up`, and list packages with `zypper pa`. YUM is not set up on SUSE by default and is not recommended there. On Ubuntu, run `apt update; apt upgrade`, and use `apt-cache gencaches` or `apt-cache search <regex>` to work with the cache. The refresh step matters on SUSE and Ubuntu, because it only updates the repository metadata. To flush caches, use `yum clean all`, `zypper clean -a` or `apt-get clean`.

All BCM packages are signed with the Bright Computing GPG public key, `0x5D849C16`. On Red Hat derivatives, the key is installed at `/etc/pki/rpm-gpg/RPM-GPG-KEY-cm`, and you import it with `rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-cm`. On Ubuntu, `cm-config-apt` imports it automatically into `/etc/apt/trusted.gpg.d/brightcomputing-archive-cm.gpg`. BCM also repackages third-party `modules`, `shorewall` and `gcc`.

In an HA pair, update `cmdaemon` and MySQL on the active head first. Confirm the state with `cmha status`, and only then update the passive head (chapter 8.12). Do not stop CMDaemon or MySQL by hand before an update.

Security fixes follow the same split. A vulnerability in a distribution package is fixed by updating the distribution. A vulnerability in a BCM package is fixed by updating the BCM packages, and for those you should contact BCM support. Hardening, which covers removing packages, blocking ports, disabling USB, disk encryption and SELinux, is possible. It is not done by default, and it is your responsibility. The manual warns that hardening can affect performance.

Software that the nodes need belongs in the software image (chapter 8.4). Software you compile from source, with `--prefix=/cm/shared/apps/<application>`, belongs under `/cm/shared`. It goes in one of six standard subdirectories: `apps`, `docs`, `etc`, `examples`, `licenses` or `modulefiles`.

On an HA pair, the active head always goes first, and you wait for `cmha status` to confirm before you touch the passive one.

## 2. Running commands on many nodes (14.1)

Suppose a whole rack needs a restart. Typing a command on each node is slow, so you send one command to all of them. Two tools can do that, and the one you choose depends on where the command should run.

| Tool | Where it runs | Notes |
|---|---|---|
| `pdsh` | OS shell | `-v` skips nodes that are down, `-a`/`-A` all nodes, `-g` genders query, `-w`/`-x` include/exclude, `-f` fanout. Default **genders**: `all`, `category=default`, `computenode`, `headnode`. Needs packages `pdsh`, `genders`, `pdsh-mod-cmupdown` and others |
| `pexec` | inside cmsh (CMDaemon) | `-j` join output; the cmsh way |

The manual gives two rules for this. The first one is about power. Do not power-cycle many nodes with `pdsh` or `pexec`, because all of them would start at once. The `cmsh` command `device power` inserts a deliberate delay between nodes (chapter 8.7), and that delay is what prevents the surge.

The second rule is about CMDaemon. A `pexec` command depends on the running CMDaemon of the node it targets, so it cannot sensibly stop that daemon. To restart CMDaemon on many regular nodes, use `pdsh`, for example `pdsh -g computenode systemctl start cmd`.

For bulk changes in `cmsh`, avoid a shell loop that starts `cmsh` once per node. Build one session instead: `(echo device; for i in {129..255}; do echo "set node00$i category newbunch"; done; echo commit) | cmsh`. The lab compares 127 `cmsh` runs against 1.

When you need to change many nodes, use one `cmsh` session or `pdsh`, and never power-cycle a rack with either tool.

## 3. Asking for help: `cm-diagnose` (14.2)

Suppose a head node problem has stumped you and you need to open a support case. Support will ask for logs, command output and file contents. `cm-diagnose` collects that material for you.

Open your request on the NVIDIA enterprise support portal. Set Product Type to `Software`, and set Product Category to `Base Command Manager` for BCM 10 and later. Older versions used the name Bright Cluster Manager. Logging in pre-fills your cluster details.

Support works mainly by e-mail. Run `cm-diagnose` on the head node. It gathers logs, command output, file contents and `cmsh` output for the head node and the images into one tar file. It can also include a `gdb` trace of CMDaemon, but only when support asks for one. Finally, it can upload the file for you. On a large cluster, raise the log limit and the timeout from their defaults of 50 MB and 60 s, with `cm-diagnose --limit 100 --timeout 240`. Release notes are on docs.nvidia.com/base-command-manager.

## 4. Backups and database recovery (14.3)

A backup you have never restored is only a hope. BCM has no backup facility for the cluster installation, so you decide what to back up. The manual says to test that a restore works. Back up the head node's full filesystem, including all software images. Back up node disks only if they hold important data. The manual suggests two open-source tools. Bacula needs the head node ports 9101 to 9103, which you open from the backup server's address through the `firewall` role's `openports`. rsnapshot uses port 22. Another option is to clone the head node (chapter 8.12).

BCM does back up one thing on its own: the CMDaemon database. Most cluster settings live there. Every night, BCM saves it into `/var/spool/cmd/backup/` as seven rotating files, named `backup-Mon.sql.gz` through `backup-Sun.sql.gz`. Raw monitoring data is not backed up, because it can be huge. The monitoring configuration is backed up, because it lives in the database.

You can make a backup on demand with `cmdaemon-backup`. With no argument, it overwrites today's default file. With a string, it writes a file named `<string>-<YY-MM-DD_HH-MM-SS>_<Day>.sql.gz`, for example `manual-24-08-28_13-19-59_Wed.sql.gz`. Run it before any big change.

A corrupted database usually follows an improper shutdown. When MySQL starts, it checks and repairs itself. If MySQL cannot start, CMDaemon cannot start either. If MySQL starts but finds corruption later, it runs read-only. The `mysql` health check then fails, an info message appears, and `journalctl -xeu mysql.service` shows checksum errors.

The fix depends on your setup. On an HA cluster, run `cmha dbreclone <passive>` from the healthy head. It gives you a current CMDaemon and Slurm database, but not the monitoring data. If you have extra databases, you need `extradbclone.xml` and `replicate-do-db` lines in `/etc/my.cnf` (chapter 8.12). On a cluster that is not HA, gunzip the latest local backup and pipe it into MySQL for the CMDaemon user.

MySQL for Slurm can run on the compute nodes, set up with `cm-mysql-setup` (chapter 8.8). That setup has one primary and one asynchronous replica, which use GTID, with `mysql-router` on the clients. Failover is manual. Run `cm-slurm-mysql-ha --config /root/mysql-ha-config.conf failover --host <primary>`, and add `--force` if the primary crashed. After a forced failover, run `remediate --host <new primary> --target <old primary>` once the old primary is back. That command replaces the target's data with a fresh clone. Keep `/root/mysql-ha-config.conf` readable by root only, because it holds passwords.

Decide now where your off-cluster copies will go, and test one restore before you need it.

## 5. Image revisions, hardware checks, replacements, scale

Suppose a software image update breaks a rack of nodes. You want to return to the image that worked. Before a new node joins the cluster, you also want proof that its hardware matches the rest.

Image revision control (14.4) uses Btrfs, so each image becomes a subvolume. Run `softwareimage; newrevision default-image "description"` to create `default-image@1` in `/cm/images/default-image-1`. Then use `revisions` and `list -r` to see the revisions. `setparent` rolls the parent back to a revision, and `remove -a -d` deletes them. Btrfs was removed from RHEL 8 onward, but SLES 15 supports it. Keep important images on a non-Btrfs filesystem too, and migrate them with `cm-migrate-image`, never `cp`. The manual says revision control suits test clusters better than production clusters, because it uses a lot of disk. Image sync tools and exclude lists are in chapter 8.4.

Hardware matching works like this (14.6). Add the new nodes to a category, then save one node as the reference with `node-hardware-profile -n node129 -s newbunch`. That stores the profile under `/cm/shared/apps/cmd/hardware-profiles/`. Next, enable the `hardware-profile` data producer with an interval, and add a `nodeexecutionfilters` category filter. The manual uses an interval of 600 s. After that, CMDaemon alerts you when a node does not match the reference. The reference can itself be faulty. If it is, most nodes get reported as bad, and that is how you notice the problem.

Replacing a dead node follows a similar path (14.9). If the new machine's MAC address is known, run `device use node031; set mac <new mac>; commit`. If it is not known, run `clear mac; commit`. Then choose the node's name at the node installer. That name is the placeholder identity from chapter 8.4. If the disk size and everything else match, that is all. On a switch-port setup, a swapped node shows up as a port mismatch (chapter 8.4). The `swap` command can exchange the names (chapter 8.5).

Scaling out has several steps. For new nodes, use `foreach --clone`, the node creation wizard, and then `newnodes` in power-on order (8.4). Set up the network and IP addresses (8.3), and assign roles and overlays for Slurm or Kubernetes (8.8, 8.9). Run a burn-in (8.2), then the hardware match check described above. Bulk operations belong in one `cmsh` session, as in section 2 of this chapter. At fleet scale, add boot and provisioning roles per rack (8.4), and consider offloaded monitoring (8.11).

Whenever you replace or add hardware, run the match check before you trust the new nodes.

## 6. Ansible with BCM (14.10)

Suppose you need the same user accounts on a new cluster that you set up on the last one. Ansible lets you write those steps into a file that you can review and repeat.

BCM publishes Ansible collections named for the BCM version. For BCM 11, the collection is `brightcomputing.bcm110`, which you install with `ansible-galaxy collection install brightcomputing.bcm110`. Most modules come in pairs. One queries an entity, and its partner sets it. The head node has examples in `/cm/local/examples/cmd/ansible/`, such as `add-user.yaml`. To read the documentation for one module, run `ansible-doc brightcomputing.bcm110.user`.

Use the collection for configuration you need to repeat and review, such as users and profiles. Part 7 shows the Redfish side of Ansible. BCM can also install the cluster with an Ansible add-on installer (chapter 8.2).

For a change that will repeat or needs review, write it as Ansible rather than a one-off `cmsh` session.

## 7. Disaster recovery: an outline (my assembly)

Picture the head node that will not answer in the middle of the night. What you do next depends on which part failed, so it helps to have the plan written before that night comes. The manual gives the pieces, but not the order to use them in. The outline below is how I would put them in order. Adapt it to your site, and test it.

| Failure | First move | Recover from |
|---|---|---|
| Head node dies, HA in place | automatic or `cmha makeactive` (chapter 8.12) | the passive head; then clone a new passive with `cm-clone-install --failover` |
| Head node dies, single head | restore hardware, reinstall BCM with the same license MAC rules (chapter 8.2) | site backup of the head filesystem and the latest database backup |
| CMDaemon database corrupt | check `mysql` health, journal | HA: `cmha dbreclone`; single: restore the local `backup-<Day>.sql.gz` |
| Software image damaged | lock it (8.4) | an image revision (Btrfs), a clone, or a backup copy on non-Btrfs |
| A rack of nodes bad after a change | `close` and `drain` (8.4, 8.8) | the previous image or setting; burn-in before returning them |
| Monitoring history lost | not backed up locally | recreate from now; raw data restore only from your own site backup |
| Everything lost | rebuild | external backup of `/cm/images`, `/cm/shared`, `/home`, the database dump, license, and the written install plan (8.2) |

Read each row as a separate failure. The middle column is the first move, and the last column is what you recover from.

Planning for this means keeping off-cluster copies of the database dump, the images, `/cm/shared` and the installation notes. Keep the license and its MAC rules in mind as well. And rehearse a restore, because the manual itself says to.

## 8. Change management: the fleet-scale habits

A change on a fleet reaches many nodes at once, so the habits matter more than any single tool.

The notes from the fleet-scale chapter boil down to a few habits. Split the boot and provisioning loads across roles (8.4). Know which way each sync runs: `imageupdate` copies the image to the node and does a dry run by default, while `grabimage` copies the node back into the image. Protect scratch mounts from `imageupdate`, because autofs is not detected. Remember that `close` is not `drain`. Build your own remediation (8.11). For HA, combine fencing, quorum and power control (8.12). Each of these is an operational habit more than a tool.

## 9. Common first mistakes

Watch for these common first mistakes. Each one is easy to make on a busy night.

1. Relying on the nightly database dump alone, with no tested backup.
2. Updating the passive head first, before the active one.
3. Power-cycling a rack with `pdsh`.
4. Restarting CMDaemon on nodes with `pexec`.
5. Running a shell loop with one `cmsh` run per node.
6. Upgrading the OS major version in place.
7. Believing Btrfs revision control is available on RHEL.
8. Replacing a node without clearing or setting its MAC.
9. Skipping a burn-in on replaced hardware.
10. Making a big change without `cmdaemon-backup`.

Read this list before your next maintenance window, and treat each item as a question you must answer first.

## 10. Change runbooks (my assembly)

A change window can go wrong halfway through. You may have updated some racks, and then the next rack shows a regression. A runbook written before the window tells you what to do at that point. The flowchart below shows the order of a safe change: back up, test on one node, roll out in waves, then verify. If a regression appears, you take the rollback path.

```mermaid
flowchart LR
    BACKUP["1. Pre-Change Backup<br/>cmdaemon-backup before-change<br/>+ clone/lock software image"] --> CANARY["2. Canary Test (1 Node)<br/>chroot edit -> updateprovisioners<br/>-> imageupdate dry-run & synclog -> -w"]
    CANARY --> WAVE["3. Rolling Rack Waves<br/>drain -> apply/reboot -> health check<br/>-> undrain (Active head first for HA)"]
    WAVE --> VERIFY["4. Post-Change Verification<br/>cmha status, hardware-profile,<br/>sinfo / kubectl get nodes"]
    WAVE -. "regression detected" .-> ROLLBACK["Rollback Path<br/>setparent / previous image<br/>or cmha dbreclone / sql.gz"]
```

Every change starts the same way. Write down the change and its undo, then take a named database backup with `cmdaemon-backup before-change`. The steps after that depend on what you are changing.

**Image change.** Lock or clone the image first, then change it in a chroot. Run `updateprovisioners`, and then run `imageupdate` as a dry run. Read `synclog`, and apply the change to one node. Roll out the rest in batches, draining each batch first. Verify the result, and keep the old image until the new one has run for a while.

**Head node package update.** In HA, update the active head first, and confirm with `cmha status` before you move to the passive head. Let the package manager restart services. Afterward, verify `cmsh`, Base View and a provisioning test.

**BIOS or firmware.** Test the change on one node, then do one rack at a time. Use an AC power cycle if the Result column says so. Finish by verifying the versions and running a GPU test (chapter 8.7).

### 10.1 Deep dive: Managing software-image lifecycles without breaking running jobs

In a busy AI cluster, multi-node training jobs can run twenty-four hours a day for weeks at a time. How do you roll out a security patch, an updated CUDA toolkit, an `MLNX_OFED` / `DOCA-Host` driver or a new Linux kernel across five hundred compute nodes without interrupting active jobs?

BCM separates software images (`/cm/images/<name>`), categories and drain-action chaining. Together they give you two rollout patterns. Which one you use depends on whether the change is a user-space package update or a kernel or driver change.

1. **Pattern A — In-place canary and wave sync for user-space updates (`imageupdate`):**
   Use this pattern for user-space packages that do not need a kernel reboot, such as `htop`, monitoring agents, `/etc/sssd/sssd.conf` or container hooks.
   - Start with a database backup, `cmdaemon-backup before-pkg-update`. Then clone the production image with `softwareimage; clone default-image default-image-rollback; commit -w`, so you have an instant rollback copy.
   - Enter the image with `cm-chroot-sw-img /cm/images/default-image`. Lock it first with `softwareimage lock default-image` while `apt` or `dnf` runs, and unlock it afterward.
   - Run `updateprovisioners` (`softwareimage; updateprovisioners`). Any regular node with the `provisioning` role then receives the updated image at once, instead of waiting for the `300 s` `dirtyautoupdatetimeout` or the midnight UTC sync.
   - Run a dry run against one canary node with `imageupdate -n node001`, without the `-w` flag. Then read `synclog node001` to check that no unexpected node-local files or `autofs` mounts are slated for deletion. This is where `excludelistupdate` comes in.
   - Apply the change to the canary with `imageupdate -n node001 -w`, check its health with `samplenow`, and then roll out across the category in waves.
2. **Pattern B — Zero-downtime rolling category switch for kernel, driver, and OFED upgrades:**
   Use this pattern when the change touches the Linux kernel (`set kernelversion` with `createramdisk`), the NVIDIA GPU kernel driver (`nvidia.ko`), or the `MLNX_OFED` / `DOCA-Host` RDMA stack. Syncing files onto a running node with `imageupdate -w` is risky here. The running kernel and the loaded `.ko` modules in RAM no longer match the files on disk. Any new job step or `nvidia-smi` call on that node can then fail with a driver or library version mismatch.
   Use a rolling category or image switch with chained drain actions instead.
   - Clone the production image (`dgx-prod-v1` → `dgx-prod-v2`). Make all the kernel, driver and `createramdisk` updates inside `dgx-prod-v2`, while production nodes keep running on `dgx-prod-v1`.
   - Create a canary category, `dgx-canary`, that points to `dgx-prod-v2`. Move one idle test node into it, reboot it, and validate GPUDirect RDMA and GDS with `gdscheck.py -p` and `all_reduce_perf`.
   - After validation, point the production category at `dgx-prod-v2`, or move racks into the new category. Then schedule a rolling reboot across busy nodes with chained drain actions:
     ```bash
     cmsh -c 'device; drain -n node001..node032 --setactions powerreset ; drain -n node001..node032 --appendactions undrain'
     ```
     Each node finishes its running Slurm job first. Then it resets its power and provisions `dgx-prod-v2` at boot. It passes its `prejob` and boot health checks, and it undrains itself back into the Slurm pool.

For a kernel or driver change, use the category switch rather than an in-place sync.

### 10.2 End-to-end bare-metal disaster recovery rehearsal

Every quarter, pull up Table 7 in Section 7 and ask your team a hard question: *if the primary storage array in our management rack suffered a double fault tonight, and both head nodes lost their local disks, could we rebuild this cluster from our off-cluster backups?*

An off-cluster disaster recovery bundle needs five artifacts. Store them on an external backup target, outside the cluster's own `/cm/shared` NAS.

1. The latest `CMDaemon` MySQL dump, `/var/spool/cmd/backup/backup-<Day>.sql.gz` or a dump from `cmdaemon-backup`, plus any external databases (`slurm_acct_db`, Keycloak, Harbor).
2. Tarballs or `rsync` mirrors of `/cm/images/*` and `/cm/node-installer*`, which hold the exact golden software images for every category and architecture.
3. Configuration files that live outside the `CMDaemon` database: `/cm/local/apps/cmd/etc/cmd.conf`, `/etc/named.conf.include`, `/cm/excludelistnormal`, `/cm/excludelistfailover`, custom health checks and actions in `/cm/local/apps/cmd/scripts/`, and TLS/CA keys under `/root/.cm/` and `/etc/kubernetes/pki/`.
4. The BCM cluster license file and its bound head-node MAC addresses. With them, you can restore onto the same NIC MAC, or request an emergency license re-host from NVIDIA Enterprise Support before the maintenance window.
5. The written Day-0 installation parameters (Chapter 8.2): the network topology type, the `internalnet`, `externalnet` and `bmcnet` subnets with their IP offsets, and the disk layout XMLs.

Rehearse a database restore, `gunzip < backup.sql.gz | mysql ...`, and a single-node image boot in a small virtual or lab environment. Rehearsal turns disaster recovery from a hope into a verified thirty-minute procedure.

### 10.3 Automating BCM Day-2 configuration as code with `brightcomputing.bcm110`

A cluster can grow from one rack to several scalable units, run by a team instead of one person. Interactive changes in `cmsh` that nobody reviews slowly make staging and production drift apart. How do you manage BCM objects, such as categories, networks, racks, users, profiles and monitoring triggers, through Git pull requests and CI pipelines?

Section 6 introduced the `brightcomputing.bcm110` Ansible collection, which lives in `/cm/local/examples/cmd/ansible/`. Knowing how the collection talks to CMDaemon lets you combine Git discipline with BCM's provisioning engine.

1. The modules talk to CMDaemon directly. Generic Linux modules, such as `ansible.builtin.copy` or `lineinfile`, SSH into compute nodes and edit files in `/etc` behind CMDaemon's back. The modules in `brightcomputing.bcm110` (`category`, `physical_node`, `network`, `user`, `profile`, `software_image` and `configuration_overlay`) connect directly to CMDaemon on the active head node. Each one reads the current object state, compares it with the YAML attributes in your playbook, and commits only the properties that differ. It reports `ok` or `changed`, and running it again is safe.
2. Suppose you prepare a new CUDA or driver image. A playbook that uses `brightcomputing.bcm110.category` with `cloneFrom: "dgx-h100-prod"` creates the `dgx-h100-canary` category. It points that category's `softwareImageProxy` at the new image and updates its kernel parameters, all in one reviewed Git commit.
3. Keep the ownership boundary from Chapter 8.1 Section 3.8 clear. Use Ansible with `brightcomputing.bcm110` to manage BCM objects on the head node. Or run Ansible inside a chrooted software image on the head node, before you run `updateprovisioners` and `imageupdate -w`. Never use Ansible to SSH into running compute nodes and overwrite files that CMDaemon or the software image manages. The next `imageupdate -w` or node reboot will erase those unmanaged edits.

Put BCM object changes in Git and let CI review them, and leave the node files to the image.

### 10.4 Pre-flight and post-flight checklist for every Day-2 maintenance window

Before a maintenance window starts, you want to know two things. The cluster must be healthy, and you must be able to get back if something goes wrong. Whether the window covers head node packages, a kernel image, faulty hardware or a new Slurm rack, the same six checks apply.

1. Take an explicit, named database backup first. Run `cmdaemon-backup pre-maint-<date>` on the active head node, and check that the `.sql.gz` file appears under `/var/spool/cmd/backup/`.
2. Check HA and replication health before you touch either head node. Run `cmha status` and confirm that both head nodes show `OK` for `ping`, `failoverping`, `status` and `mysql`.
3. Check provisioning, and lock or clone the target images. Run `softwareimage; provisioningstatus` to make sure no nodes are mid-transfer. Clone any image you plan to change with `clone <img-prod> <img-backup>; commit -w` before you modify its packages or kernel.
4. Drain the target compute nodes cleanly through the workload manager. Use `drain -n <nodes>` or a Slurm maintenance reservation. Confirm that the running jobs have finished with `wlm; jobs; list` before you reboot or power-cycle the nodes.
5. Validate on one canary node before you widen the change. Apply the image, BIOS or firmware change to that node first. Check the `samplenow` health checks, `ipaddresses --check`, and a quick GPU or fabric test. Only then roll out across racks, using `device power` stagger delays or chained `drain --setactions powerreset --appendactions undrain`.
6. Confirm the cluster converged after the window. Verify `cmha status`, `cmdaemonversions`, `packages --outdated`, `healthoverview`, and `sinfo` or `kubectl get nodes`. That proves the whole cluster returned to a clean, uniform baseline.

Do not close the change ticket until step six is done.

## Exercises

1. Run `python3 ops_lab.py`. Pick four checks, and explain each rule in your own words.
2. Sort these versions into calendar, semantic or hotfix: `10.25.03`, `11.25.08`, `11.30.0`, `11.31.0b`.
3. Write a one-session cmsh script that moves 200 nodes into a new category, then check the result.
4. Plan the restore test you would run every quarter. Give it a stop condition, and name who signs off on it.
5. Draft the runbook for replacing a failed DGX node. Use chapters 8.4, 8.7, 8.8 and this one.
6. List what is on your own cluster but not in any backup.

## 12. Interview angles

- "What does BCM back up for you?" Only the CMDaemon database, every night, in seven rotating files. The rest is yours to back up.
- "How do you update head nodes in HA?" Update the active head first for CMDaemon and MySQL, confirm it, then update the passive head.
- "A node died. How do you replace it?" Set or clear the MAC, commit, name the node at install, and then run a burn-in.
- "Why not `pdsh` for a rack reboot?" It causes a power surge. Use `device power` instead, because it adds a delay.
- "Walk me through a bad image rollout." Lock the image, roll back to the previous revision or image, drain the nodes, run `imageupdate` or reboot them, and then verify.

## Checkpoint questions (20)

<details>
<summary>1. What are the two point-release numbering schemes used in BCM 10 and 11 (§9.1)?</summary>

1. **Calendar versioning (`YY.MM`):** This scheme was used up to `10.25.03` and `11.25.08`. For example, `11.25.08` means August 2025.
2. **Semantic versioning (`Major.Minor.Patch`):** This scheme is used from `11.30.0` onward, with releases such as `11.30.0`, `11.31.0` and `11.34.0`. A non-zero third number marks a backward-compatible bug-fix release.
</details>

<details>
<summary>2. What does a lowercase letter suffix on a BCM version (such as `10.23.02a`) signify, and does it appear in semantic releases?</summary>

A letter suffix marks a **hotfix** on the calendar-versioned point releases. You will never see a lowercase letter suffix on a semantic release.
</details>

<details>
<summary>3. Is an in-place major OS upgrade (such as RHEL 8 to RHEL 9) supported on a BCM head node?</summary>

**No.** Upgrading the Linux distribution to a new major release in place, while keeping BCM, is not supported. You have to do a fresh BCM installation on the new OS major version.
</details>

<details>
<summary>4. How can you recognize a BCM-supplied RPM or DEB package from its filename, and why must you never replace it with an upstream distribution package?</summary>

BCM packages carry `_cm<x.y>_<git_hash>` in an RPM filename, or `-cm<x.y>-<git_hash>` in a DEB filename. They are also signed with the GPG key `0x5D849C16`. If you replace one with a standard OS package, the cluster enters an unsupported state, and the `CMDaemon` integration breaks.
</details>

<details>
<summary>5. What are the four default `genders` groups configured for `pdsh -g` in BCM?</summary>

The four default groups are **`all`**, **`category=default`**, **`computenode`**, and **`headnode`**.
</details>

<details>
<summary>6. Why must you use `pdsh` (an OS-level SSH tool) rather than `cmsh`'s `pexec` to restart or start `cmd` (`CMDaemon`) across regular nodes?</summary>

`pexec` runs commands through the running `CMDaemon` on the remote node (the `cmd` service). So it cannot start a stopped `cmd` daemon, and if you use it to stop `cmd`, it cuts off its own connection.
</details>

<details>
<summary>7. Why should you never use `pdsh` or `pexec` to power-cycle or reboot a rack of GPU servers simultaneously?</summary>

`pdsh` runs in parallel across all target nodes with no stagger delay. When every node boots together, the electrical inrush can cause a massive **power surge**. Use `cmsh` `device power` instead, which enforces a `1 s` per-node delay or a `20 s` batch delay.
</details>

<details>
<summary>8. What does `cm-diagnose` collect for NVIDIA Enterprise Support, and what do `--limit` and `--timeout` adjust?</summary>

`cm-diagnose` packages the logs, configs and `cmsh` output for the head node and images into a support tarball. It can add a `gdb` trace of `CMDaemon` as well. `--limit` raises the largest log file size it collects, from the default `50 MB` (for example `--limit 100`). `--timeout` raises the per-command timeout, from the default `60 s` (for example `--timeout 240`), for large clusters.
</details>

<details>
<summary>9. When opening a support case in the NVIDIA Enterprise Support Portal for BCM 10 or 11, which Product Type and Product Category do you select?</summary>

Choose **Product Type: `Software`** and **Product Category: `Base Command Manager`**. Versions before 10 used `Bright Cluster Manager`.
</details>

<details>
<summary>10. What does BCM back up automatically out of the box, where are those files stored, and how many are kept?</summary>

Out of the box, BCM backs up **only the `CMDaemon` MySQL database**. It does this every night, into **`/var/spool/cmd/backup/`**, as **seven rotating daily files** named `backup-Mon.sql.gz` through `backup-Sun.sql.gz`.
</details>

<details>
<summary>11. What filename format does `cmdaemon-backup before-change` create compared to running `cmdaemon-backup` with no arguments?</summary>

With no arguments, `cmdaemon-backup` overwrites today's rotating `backup-<Day>.sql.gz` file. With a label such as `before-change`, it writes a timestamped file named **`before-change-<YY-MM-DD_HH-MM-SS>_<Day>.sql.gz`**. The nightly rotation never overwrites that file.
</details>

<details>
<summary>12. Which critical cluster assets are NOT backed up by `cmdaemon-backup` and require your own site backup solution?</summary>

1. **Software images (`/cm/images/*`)**.
2. **Shared storage (`/cm/shared` and `/home`)**.
3. **Head node OS filesystem and custom scripts**.
4. **Raw monitoring time-series data**.
</details>

<details>
<summary>13. What happens to `CMDaemon` if MySQL cannot start, versus if MySQL starts but detects table corruption later?</summary>

If MySQL cannot start, **`CMDaemon` refuses to start**. If MySQL finds corruption while it is running, it switches to **read-only mode**. The `mysql` health check then fails, and checksum errors appear in `journalctl -xeu mysql.service`.
</details>

<details>
<summary>14. How do you recover a corrupted `CMDaemon` MySQL database on an HA cluster versus a single-head-node cluster?</summary>

- **On an HA cluster:** From the healthy head node, with `CMDaemon` stopped, run **`cmha dbreclone <passive>`**. That re-clones the live `cmdaemon` and `slurm_acct_db` databases.
- **On a single head node:** Gunzip the newest `/var/spool/cmd/backup/backup-<Day>.sql.gz` (or a manual backup), and pipe it into the `mysql` client.
</details>

<details>
<summary>15. What filesystem does BCM's built-in `softwareimage` revision control (`newrevision`, `setparent`) require, and why is it unavailable on RHEL 8/9?</summary>

It requires **Btrfs** subvolumes. Red Hat removed Btrfs support from RHEL 8 onward, so revision control is not available there. SLES 15 still supports Btrfs.
</details>

<details>
<summary>16. Why should you never run `device packages -a` across 1,000 nodes without `-f <package>`?</summary>

`packages -a` returns about **`100 KB` (`~1,000` lines) per node**. Across 1,000 nodes, that adds up to about **`100 MB` (`~1,000,000` lines)**. Always filter with `-f cmdaemon`, or use `packages --outdated`.
</details>

<details>
<summary>17. How does `node-hardware-profile` verify that a newly delivered batch of servers matches a reference node, and how can you tell if the reference node itself was faulty?</summary>

`node-hardware-profile -n node129 -s newbunch` saves the hardware inventory of `node129` under `/cm/shared/apps/cmd/hardware-profiles/`. The `hardware-profile` data producer then alerts on any node in `newbunch` that differs from it. If `node129` itself has a fault, such as a missing DIMM or a bad card, every other healthy node in the batch gets flagged as mismatched.
</details>

<details>
<summary>18. What are the two ways in `cmsh` to replace a dead compute node `node031` with a new physical chassis?</summary>

1. **If the replacement MAC is known:** Run `device use node031; set mac <new-mac>; commit`, then PXE-boot the new machine.
2. **If the replacement MAC is not known in advance:** Run `device use node031; clear mac; commit` to turn `node031` into a placeholder. Then PXE-boot the new machine, and select `node031` at the `node-installer` console prompt.
</details>

<details>
<summary>19. What is the official Ansible Galaxy collection name for BCM 11, and where are example playbooks stored on the head node?</summary>

The collection is **`brightcomputing.bcm110`**. Its example playbooks are in **`/cm/local/examples/cmd/ansible/`**.
</details>

<details>
<summary>20. When MySQL for Slurm accounting is deployed on compute nodes via `cm-mysql-setup`, how do you fail over after a primary crash and re-sync the old primary afterward?</summary>

Run **`cm-slurm-mysql-ha --config /root/mysql-ha-config.conf failover --host <primary> --force`**. Once the old primary node is repaired, run **`cm-slurm-mysql-ha --config /root/mysql-ha-config.conf remediate --host <new-primary> --target <old-primary>`**.
</details>

## Sources and review notes

- **BCM 11 Administrator Manual:** chapter 9 (9.1 package naming and point releases, 9.2 head node packages and the HA note), chapter 14 (14.1 parallel shells, 14.2 support and `cm-diagnose`, 14.3 backups and database recovery, 14.4 image revision control, 14.6 hardware match, 14.9 node replacement, 14.10 Ansible, 14.12 `cm-mysql-setup` and its maintenance).
- **NVIDIA-DevOps notes**, volume 10 chapter 13: fleet-scale operating habits (used here and in 8.4, 8.11 and 8.12).
- **Run here:** `ops_lab.py` (45 checks): version schemes, BCM package filename parsing (`.rpm` and `.deb`), `device packages -a` output volume, GPG key and `/cm/shared` layout, parallel tool choice, bulk script, `cm-diagnose` and support, backup names and scope, restore paths, Btrfs, revisions, hardware match, node replacement, MySQL HA commands, runbook shapes.
- **My own choices, not the manual's:** the disaster recovery table (section 7) and the change runbooks (section 10); the "unknown" classification for versions between the calendar and semantic ranges (the manual gives no rule there).
- **Not read or not covered:** 14.5 and 14.7 beyond chapter 8.7; Btrfs `cm-clone-install` issue (page 828); 14.11; the Cluster Extension and cloud topics; Bacula and rsnapshot configuration; air-gapped updates (chapter 8.14); upgrading BCM to a new major release (11 to 12 procedure, not in the text I read).
- **Not verified:** everything about a real BCM system.
