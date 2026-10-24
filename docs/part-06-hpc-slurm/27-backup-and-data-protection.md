---
id: "c06-27"
title: "6.27 Backup and data protection"
sidebar_label: "6.27 Backup and data protection"
sidebar_position: 27
description: "Backup and data protection for GPU clusters: what to protect and what not to, RPO/RTO and the 3-2-1 rule, tar, rsync snapshots, Bacula, modern deduplicating tools (restic, borg, kopia), snapshots and replication, parallel file system backup challenges, ransomware and immutability, and restore testing, with tested rsync, GNU tar and restic experiments"
status: "drafted"
tier: "3"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.27 Backup and data protection

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 2 |
| Lab venue | Laptop (tested experiments) |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. **Run on a macOS laptop with conda-forge builds**: rsync 3.4.4 `--link-dest` snapshots, GNU tar 1.35 `--listed-incremental`, restic 0.19.1 (init, backup, snapshots, restore, check, `--read-data` corruption detection, forget/prune); outputs shown. Bacula, tape, ZFS/Lustre snapshots, Globus and cloud tiers were **not** run; those sections are from the SCL book and general knowledge. Labs for production tools are **untested** |

## Why this matters for AI infrastructure

Training clusters feel disposable (checkpoints can be regenerated, nodes are reimaged), which tempts teams to skip backups. But a cluster holds irreplaceable things: user code and results, curated datasets and labels, trained models and their lineage, the configuration that makes the cluster work, and the databases that define identity and accounting. Losing the Slurm accounting database, the LDAP directory, the head-node image repository, or a project's only copy of a fine-tuned model costs weeks. Ransomware aimed at research and cloud environments makes immutable, tested backups a security control as much as an operations task. This chapter separates what must be protected from what can be rebuilt, and shows the tools and tests.

## Prerequisites and outcomes

Needs 6.18 to 6.24. After this chapter you can:

- Classify cluster data by value and reproducibility and set RPO/RTO per class.
- Apply 3-2-1 and its modern variants (immutability, air gap, offsite).
- Use tar, rsync (hard-link snapshots), Bacula-style enterprise backup, and deduplicating tools (restic/borg/kopia), and understand the trade-offs.
- Design backups for parallel file systems and object stores; know why snapshots are not backups.
- Protect the control-plane state: head node, Slurm, LDAP, Git, Terraform state, secrets, container registries.
- Test restores and detect silent corruption; monitor backup health.

## 1. What to protect

| Class | Examples | Reproducible? | Policy |
|---|---|---|---|
| **Cluster definition** | Git repos for configs, Ansible/Terraform, images build files, Slurm configs, Helm values | Mostly (if in Git) | Git hosting with backups; mirror offsite; protect Terraform state (versioned, locked, backed up) |
| **Control-plane state** | `slurmdbd` database, `StateSaveLocation` (before upgrades), LDAP/FreeIPA database, BCM/xCAT/Warewulf databases, CA keys, munge key, secrets store, DNS/DHCP data, registry metadata | No | Frequent (hourly to daily), tested restore, offsite copy |
| **Software and images** | Node images, container registry blobs, module trees, Spack/EasyBuild caches | Yes, with time and compute | Keep build recipes; back up the current "golden" images and registry; rebuild is the fallback |
| **User homes** | Code, notebooks, small results, dotfiles | No | Daily snapshots + backup; quotas keep size manageable |
| **Project / shared data** | Curated datasets, labels, evaluation sets, trained models, papers' data | Partly (raw data may be re-downloaded; labels and curation cannot) | Backup to a different failure domain; versioned object store; DOIs/archival for published data |
| **Scratch / work** | Intermediate results, temporary datasets | Yes | **Not backed up** by policy; purged; state this loudly |
| **Checkpoints** | Training state | Regenerable at a cost | Retention policy; keep milestone checkpoints and final models in protected storage; checkpoints on the parallel file system are *not* a backup (6.21) |
| **Logs and metrics** | Syslog, job logs, accounting history | No (audit value) | Ship offsite; retention per compliance |
| **Databases for applications** | MLflow, experiment trackers, vector databases | No | Application-consistent dumps |

State **RPO** (recovery point objective: how much data you can lose) and **RTO** (recovery time objective: how long recovery may take) per class. A model-registry database may need RPO of minutes; a home directory 24 hours; scratch none.

## 2. Principles

- **3-2-1(-1-0)**: three copies of the data, on two different media/systems, one offsite, **one immutable or offline**, and zero errors verified by restore testing. The last two additions answer ransomware and silent corruption.
- **Snapshots are not backups.** File-system snapshots (ZFS, GPFS, Btrfs, array snapshots) protect against accidental deletion quickly but live in the same failure domain as the data (same array, same admin credentials). Use them as the first line and combine with replication or backup to a separate system.
- **Replication is not backup.** Synchronous or asynchronous mirrors copy deletions and corruption as faithfully as data.
- **Independent credentials and failure domains**: the backup system's admin account must not be the same identity that can delete production data; ideally append-only credentials for the writer.
- **Consistency**: for databases and busy file systems take application-consistent copies (`mysqldump --single-transaction`, `pg_basebackup`, LVM/ZFS snapshot then copy, quiesce). Backing up a live Postgres directory with `cp` yields garbage.
- **Encrypt** backups at rest and in transit; protect the keys separately (losing the key is losing the backups).
- **Test restores** regularly: a backup you have not restored is a hope. Include full-system recovery drills for the control plane.
- **Monitor**: job success, age of the newest backup per class, size and duration trends, error counts, repository integrity checks, restore-test results; alert on "no successful backup in N hours".

## 3. Classic tools (SCL chapter 20)

The SCL book's backup chapter covers three families: `tar`, **Bacula**, and `rsync` "and others".

### tar

`tar` archives files (optionally compressed) to a file or tape. GNU tar supports **incremental backups** with a snapshot (listed-incremental) file that records what was archived. Tested with GNU tar 1.35 on a 4 MB directory:

```bash
tar --listed-incremental=lvl.snar -czf full.tgz data      # level 0 (the .snar file is created)
echo more > data/new.txt
tar --listed-incremental=lvl.snar -czf inc1.tgz data      # only what changed since
```

Result: `full.tgz` 4,015,302 bytes; `inc1.tgz` 578 bytes, containing the new directory entries and `data/new.txt`. To restore, extract the full archive then each incremental in order, using `--listed-incremental=/dev/null`. (macOS's default `tar` is bsdtar, which lacks this option; use GNU tar.) Limits: no deduplication, no integrity verification beyond the compressor's checksums, no catalog, restore requires the chain, ACLs/xattrs need `--acls --xattrs`, sparse files need `--sparse`. Good for simple, offline, long-term archives and as a building block.

### rsync and hard-link snapshots

`rsync -a` mirrors a tree efficiently (delta transfer, preserves permissions/times/links). The classic trick for versioned backups without dedup software is `--link-dest`: each new snapshot directory hard-links unchanged files from the previous one. Tested with rsync 3.4.4 (200 files of 20 KB, 4,004 KB total):

```bash
rsync -a data/ snaps/day1/
# modify one file and append to another
rsync -a --delete --link-dest=$PWD/snaps/day1 data/ snaps/day2/
```

Results: `ls -li` showed the **same inode** for the unchanged `f1.bin` in both snapshots and different inodes for the modified `f7.bin`; `snaps/day1` measured 4,004 KB while `snaps/day2` counted only 24 KB (its own changed files; `du` counts a hard-linked file once per invocation), and both together took 4,028 KB. Each snapshot directory looks like a full copy and can be browsed and restored with plain `cp`. Caveats: the first run copies everything; files modified in place cost a full copy each time (no block-level dedup); permissions and ownership require running as root on the target; hard links do not cross file systems; rotation scripts must prune old snapshots; macOS ships an old `openrsync`, so use a current rsync. `rsync` also moves data between systems (`rsync -aH --delete-after -e ssh`), the usual tool for syncing images and configuration to a standby head node, with `--checksum`, `--partial`, `--bwlimit` and `-z` as needed. For parallel file systems with millions of files use parallel tools (`mpifileutils` `dsync`/`dcp`, `fpsync`, `rclone` with many transfers) because single-threaded rsync walks the tree serially.

### Bacula

Bacula is an enterprise network backup system (Bacula, forks Bareos). Its components as listed in the book's chapter: **Director** (the scheduler/brain; configuration `bacula-dir.conf`), **Storage Daemon** (writes to disk, tape, or virtual tape libraries), **File Daemon** (the client agent on each machine), the **Catalog** (database of what was backed up, MySQL/PostgreSQL), and the **console** (`bconsole`) for operators. Configuration objects: **Client**, **FileSet** (what to include/exclude), **Schedule** (when; full/differential/incremental levels), **Pool** (a set of volumes with retention), **Storage**, **Job**, **JobDefs**, **Messages**. Strengths: central policy, tape support, long retention, mature. Costs: complexity, catalog dependency (you must back up and be able to restore the catalog first), per-file catalog growth on huge file counts, and scan times on tens of millions of files.

## 4. Deduplicating repositories: restic, borg, kopia

Modern tools split files into content-defined chunks, deduplicate across all snapshots and hosts, compress and **encrypt** client-side, and store everything in a repository (local directory, SFTP, S3-compatible object store, REST server). Properties: every backup is a full-looking snapshot but costs only changed chunks; integrity checks via content hashes; flexible retention (`forget --keep-daily 7 --keep-weekly 4 ...`); mountable snapshots; fast restores of single files. restic is a single Go binary (the examples below use it); borg (Python/C, strong compression and append-only options) and kopia (Go, with server/UI) are alternatives.

Tested with restic 0.19.1 (tiny data set; the point is behaviour, not speed):

```text
restic init -r repo
restic -r repo backup data --tag day1          # 201 files, 3.8 MiB
(add a new 20 KB file / change one)
restic -r repo backup data
  Files: 0 new, 1 changed, 201 unmodified
  Added to the repository: 111.991 KiB (31.248 KiB stored)
restic -r repo snapshots      -> 2 snapshots, each showing the full 3.815 MiB
du -sk repo                   -> 4000 KB    (two full-looking snapshots stored in about the size of one)
restic -r repo check          -> no errors were found
restic -r repo restore latest --target restore   -> Restored 204 files/dirs
```

A second experiment on a 3-file directory: restoring the latest snapshot into a fresh directory and running `diff -r` against the live data printed "identical", while restoring the *first* snapshot differed from the live data in the modified file (`f2`), as it should. Then a pack file in the repository was corrupted by overwriting two bytes: `restic check --read-data` (which reads and verifies every pack) reported "repository contains errors" and suggested repair steps, while the default `restic check` (metadata only) is cheaper but would not read data blobs. The lesson: **schedule periodic `--read-data` (or `--read-data-subset`) checks**, and keep a second repository copy for repair. Finally `restic forget --keep-last 1 --prune` removed old packs, showing retention in action.

Operational notes: the repository password/key is essential (store it in a secret manager and on paper offsite; the experiments used a throwaway password); use a dedicated service account with **append-only** access to the repository (restic REST server `--append-only`, S3 object lock/versioning) so a compromised client cannot delete history; pin tool versions; test restores of a sample every week; watch memory use on huge trees (index size).

## 5. Parallel file systems, object stores and AI-scale data

Backing up petabytes of small and large files is a different problem:

- **Walking the namespace is the bottleneck**: a full scan of 500 million files takes hours to days. Use change tracking instead of scanning: Lustre **changelogs** (consumed by tools such as Robinhood) and `lfs find` with `--newer`/mtime filters; GPFS **policy engine** (`mmapplypolicy`) and `mmbackup`; WEKA/VAST snapshot-and-diff APIs; object-store versioning and replication; ZFS `send/receive` incrementals.
- **Parallel data movers**: `mpifileutils`, `dsync`, `fpsync`, `rclone --transfers N`, Globus, vendor tools; spread over multiple data transfer nodes (6.25).
- **Tiering and HSM**: copy cold data to object storage or tape via HSM (Lustre HSM, GPFS ILM) so that backup and archive coincide.
- **Datasets and models**: store in a versioned object store (S3 with versioning, object lock) or a data-versioning layer (DVC, lakeFS) with immutable snapshots; record dataset versions in experiment metadata so a training run is reproducible and a lost model can be retrained. Large model checkpoints and weights go to object storage with lifecycle policies; do not stream TB-scale checkpoints through a backup agent.
- **Home directories** are small enough for the standard tools; enforce quotas (6.24) to keep them so.
- **What to exclude**: scratch, caches (`~/.cache`, pip/conda caches), job outputs flagged ephemeral, container layers; document exclusions.

## 6. Protecting the control plane

| Component | How to back up | Notes |
|---|---|---|
| Slurm accounting DB | `mysqldump --single-transaction` or physical replica snapshot, daily plus before upgrades (6.15) | Test importing into a scratch `slurmdbd` |
| Slurm state dir | Snapshot before upgrade; HA shared storage during operation | Not a long-term backup |
| LDAP/FreeIPA | `slapcat` (OpenLDAP) / `ipa-backup` (FreeIPA), CA and Kerberos keys | Offline copy of CA private keys |
| Cluster manager DB | BCM/xCAT/Warewulf native backup, plus Git of exports | Includes node inventory and images metadata |
| Images and registry | Store images in the registry with replication; keep build recipes in Git | Rebuild path documented |
| Git hosting / CI | Mirror repos to a second system; export CI config | Treat as critical |
| Terraform/OpenTofu state | Versioned, encrypted remote state with locking; periodic export | Losing state is painful (Part 4) |
| Secrets (Vault, SOPS keys) | Vault snapshots (`vault operator raft snapshot`), key escrow | Never in the same repository as data backups unencrypted |
| Switch/BMC configs | Config export on change, stored in Git | Part 2, 7 |
| DNS/DHCP | Zone and lease files from the provisioning source of truth (6.22 inventory) | Generated, so back up the source |

Disaster recovery drill: rebuild the head node and one compute node from nothing using only the backups and documentation; time it; record gaps.

## 7. Ransomware and insider risk

- **Immutability**: object lock/WORM (S3 Object Lock in compliance mode, immutable ZFS snapshots with holds, tape taken offline), append-only repositories.
- **Separate trust domain**: backup servers on a management network not reachable from user nodes; credentials not in LDAP groups users can influence; MFA for deletion; "four-eyes" retention changes.
- **Detect**: backup size anomalies (sudden growth or total change of every file), canary files, monitoring of mass deletions/encryption (entropy), alerts on repository integrity failures.
- **Recover**: documented order of restoration (identity, DNS, provisioning, storage, scheduler, then users), clean-room rebuild, rotation of all secrets after an incident.
- **Offsite and offline copy** of the most critical state (control-plane DB dumps, keys, Git mirrors).

## 8. Restore testing and metrics

Test levels: (1) automated daily restore of a random file and checksum compare; (2) weekly restore of a database dump into a scratch instance and a smoke query; (3) quarterly full-system recovery drill. Track: backup success rate, age of newest good backup per class, restore success and time versus RTO, data growth, dedup ratio, repository check status. Report to management as part of risk review.

## 9. Lab

Tested here (install GNU tar, rsync 3 and restic; conda-forge has all three): 1) reproduce the three experiments on a small directory. 2) Delete a file, restore it from each tool. 3) Corrupt a restic pack file and detect it with `check --read-data`; repair the repository by restoring the pack from a second copy (`restic copy` to a second repo beforehand). 4) Script a rotation: 7 daily rsync snapshots with `--link-dest` pruning older ones; confirm disk usage stays near one full copy plus changes. 5) Write the RPO/RTO table for your cluster classes.

Untested: 6) Bacula/Bareos: director, storage daemon, file daemon on three VMs; back up and restore a directory; back up and restore the catalog. 7) restic to an S3-compatible bucket with object lock and an append-only credential; attempt deletion with the backup credential. 8) ZFS snapshot + `zfs send | receive` incremental replication to a second host. 9) Lustre changelog consumer (Robinhood-style) driving incremental copy. 10) Full DR drill of a test head node.

## 10. Interview angles

- Walk through 3-2-1-1-0. Why aren't snapshots and replication backups?
- How would you back up a 5 PB Lustre file system?
- Design backups for a Slurm cluster's control plane. Which pieces need application-consistent copies?
- tar vs rsync vs restic vs Bacula: when each?
- How does `rsync --link-dest` create space-efficient snapshots? Limitations?
- How do you prove your backups work?
- A ransomware incident encrypts user homes and your NFS server: what saves you?
- Should checkpoints be backed up? What is retained, what is not?
- What are RPO and RTO and how do you choose them for model artefacts?

## 11. Checkpoint questions (30)

1. What classes of data does a GPU cluster hold?
2. Which class is deliberately not backed up?
3. Define RPO and RTO.
4. State 3-2-1-1-0.
5. Why are snapshots not backups?
6. Why is replication not backup?
7. What is application-consistent backup?
8. How does GNU tar `--listed-incremental` work?
9. What is the restore procedure for tar incrementals?
10. How does `--link-dest` save space? Evidence from the experiment?
11. What are the limits of hard-link snapshots?
12. List Bacula's components.
13. Why must the Bacula catalog be backed up separately?
14. How do deduplicating tools work?
15. What did `restic check` versus `--read-data` show?
16. What did the experiment show about a restore of an old snapshot?
17. What does `forget --prune` do?
18. Why use append-only credentials?
19. Why is namespace walking a problem at scale?
20. Name change-tracking mechanisms for Lustre and GPFS.
21. Which tools parallelise file copies?
22. How should datasets and models be versioned?
23. List control-plane items and their backup methods.
24. What is a DR drill?
25. List three immutability mechanisms.
26. How do you detect ransomware in backups?
27. What is the order of restoration after a major incident?
28. What are the three levels of restore testing?
29. Which metrics do you track?
30. Why encrypt backups and where do you keep the key?

## 12. Sources and review notes

- tar, Bacula (Director, Storage Daemon, File Daemon, Catalog, FileSet, Schedule, Pool, console) and rsync coverage, and the framing of backup in the cluster context: *Supercomputers for Linux SysAdmins* chapter 20 ("Backup"), restated in my words.
- Experiments: run locally as described (tools from conda-forge: rsync 3.4.4, GNU tar 1.35, restic 0.19.1). Tool behaviours not shown there (borg, kopia, ZFS, Lustre/GPFS change tracking, Object Lock, `mpifileutils`) are from general knowledge.
- Related: 6.15 (Slurm backups and upgrades), 6.18 to 6.21 (storage), 6.24 (identity), Part 4 (state), Part 18 (security).
- Unverified: sizing and timing claims for petabyte-scale scans, vendor-specific snapshot/backup tooling names, Bacula configuration syntax (not shown), the exact restic flags on other versions.
