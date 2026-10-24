---
id: "c01-03"
title: "1.3 Files and the directory hierarchy: paths, links, inodes"
sidebar_label: "1.3 Files and the directory hierarchy: paths, links, inodes"
sidebar_position: 3
description: "How Linux organises files: paths, the standard directory layout, file types, inodes, hard and symbolic links, timestamps, finding files, and archiving and compression."
status: "drafted"
tier: "0"
level: "B"
lab_venue: "GCP VM"
---

# 1.3 Files and the directory hierarchy: paths, links, inodes

**Level:** basics → intermediate · **Tier 0 (foundations)** · **Lab venue:** a small Ubuntu VM on GCP (root access needed for two labs) · **Status:** drafted, labs untested

## Why this matters for AI infrastructure

Everything in an AI cluster ends up as files on a filesystem: datasets with millions of small files, multi-gigabyte checkpoints, container image layers, Slurm and Kubernetes configuration, logs, driver modules, and the pseudo-files under `/proc` and `/sys` that expose the kernel and the hardware. Many of the failures that stop training runs are filesystem facts that look mysterious until you know the model: a disk that is "full" while `df` shows free space, a checkpoint directory whose `latest` link points at nothing, a dataset directory that takes ten minutes to list, a tarball that overwrote system files. This chapter gives you the mental model of how Linux names, stores and links files, so that these become easy to diagnose and, better, never happen.

## Prerequisites and outcomes

You need chapters 1.1 and 1.2 (processes, system calls, the shell). After this chapter you will be able to:

- read and write absolute and relative paths correctly, and explain `.`, `..`, `~` and `/`;
- describe what lives in each top-level directory of a Linux system and where to look for configuration, logs, binaries, devices and kernel information;
- identify the type of any file from `ls -l` and `stat`, and explain what an inode is and what a directory really contains;
- create and reason about hard links and symbolic links, and know when each breaks;
- read the three timestamps of a file and understand what changes each;
- find files by name, type, size and age with `find`, and identify mystery files with `file`;
- package, compress, inspect and unpack archives with `tar` and common compressors, safely;
- diagnose six common filesystem failures: full disk with free space, dangling links, cross-device link errors, deleted-but-open files, unsafe extraction, and slow huge directories.

## 1. Paths: how you name a file

Every file or directory on Linux is reached through a **path**: a string of names separated by `/`. There is **one tree** with a single top, the **root directory**, written `/`. Unlike some other systems, there are no drive letters; additional disks and network filesystems are *attached into the same tree* at chosen directories (called mount points, chapter 1.12).

```mermaid
flowchart TB
  R["/ (root)"] --> etc["/etc<br/>configuration"]
  R --> home["/home"]
  R --> usr["/usr"]
  R --> var["/var"]
  home --> alice["/home/alice"]
  alice --> proj["/home/alice/project"]
  proj --> f["/home/alice/project/train.py"]
  usr --> bin["/usr/bin<br/>commands"]
  var --> log["/var/log<br/>logs"]
```

- An **absolute path** starts with `/` and means the same thing everywhere: `/home/alice/project/train.py`.
- A **relative path** does not start with `/` and is interpreted starting from the **current working directory** (`pwd`) of the process: `project/train.py`. Relative paths are convenient interactively and a classic source of bugs in scripts, because the working directory is whatever the caller happened to be in. Cron jobs, systemd services, Slurm jobs and containers each start in a different directory, so automation should use absolute paths or `cd` explicitly first.
- `.` means "this directory" and `..` means "the parent directory". The root's parent is itself.
- `~` is shell shorthand for your home directory (the shell expands it; the kernel never sees a tilde, chapter 1.2).
- Names are **case-sensitive** (`Data` and `data` are different), may contain almost any character except `/` and the NUL byte, and are **just bytes**: Linux imposes no encoding or file-extension meaning. A file called `train.py` is not special because of `.py`; the extension is a human and tool convention (section 7).

Two helpful commands for paths: `realpath path` prints the absolute, symlink-resolved path, and `basename`/`dirname` split a path into its last component and the rest.

## 2. The standard layout: where things live

Almost every Linux distribution follows the **Filesystem Hierarchy Standard (FHS)**: a convention for what belongs under each top-level directory. Knowing it tells you where to look before you search.

| Directory | Purpose | What you will find on an AI node |
|---|---|---|
| `/` | root of the whole tree | |
| `/bin`, `/sbin`, `/lib`, `/lib64` | essential commands and libraries; on modern distributions these are **symbolic links** into `/usr` | |
| `/usr` | the bulk of installed software, read-mostly | `/usr/bin` commands, `/usr/lib` libraries, `/usr/share` data and docs, `/usr/local` software you installed yourself, `/usr/src` kernel and driver sources |
| `/etc` | **system-wide configuration** (plain text) | `slurm/slurm.conf`, `ssh/sshd_config`, `fstab`, `hosts`, `docker/`, `kubernetes/`, `systemd/system/` |
| `/var` | **variable** data that changes while the system runs | `/var/log` logs, `/var/lib` application state (`docker`, `kubelet`, `containerd`), `/var/spool` queues (`slurmd`), `/var/cache` caches |
| `/home` | users' personal files | code, notebooks, SSH keys; often on a shared filesystem in a cluster |
| `/root` | the superuser's home | |
| `/tmp` | temporary files, may be cleared at boot or periodically | scratch space; usually small and shared |
| `/run` | runtime data since boot (an in-memory filesystem) | PID files, sockets (`/run/munge`, `/run/containerd`) |
| `/dev` | device files | `nvidia0`, `nvme0n1`, `null`, `zero`, `tty`, `shm/` |
| `/proc` | a **virtual** filesystem: the kernel's view of processes and system state | `/proc/cpuinfo`, `/proc/meminfo`, `/proc/<pid>/`, `/proc/driver/nvidia/` |
| `/sys` | a **virtual** filesystem exposing devices, drivers and kernel settings | `/sys/class/infiniband/`, `/sys/class/net/`, `/sys/fs/cgroup/`, `/sys/bus/pci/` |
| `/boot` | what is needed to start the machine | the kernel image (`vmlinuz-*`), initramfs, bootloader files |
| `/opt` | self-contained third-party software | vendor tools, sometimes CUDA or NVIDIA utilities |
| `/mnt`, `/media` | places to mount filesystems temporarily or removable media | |
| `/srv` | data served by this system (rarely used) | |
| `/lost+found` | recovered file fragments after a filesystem check (on ext filesystems) | |

Three practical notes:

1. **"Merged usr".** On current Debian, Ubuntu, Rocky and RHEL, `/bin` is a symlink to `/usr/bin` (and likewise for `/sbin` and `/lib`). So `/bin/ls` and `/usr/bin/ls` are the same file. Older documentation that distinguishes them is out of date.
2. **`/proc` and `/sys` are not on disk.** They are generated by the kernel on demand, which is the "everything is a file" idea in its purest form: reading `/proc/meminfo` runs kernel code and returns text, and writing to many files under `/sys` or `/proc/sys` changes live kernel settings (`sysctl`, chapter 1.22). They take no disk space. Be careful in them: a stray write can change system behaviour.
3. **`/usr/local` and `/opt` are for local software**, so package updates do not overwrite your work. A good example: NVIDIA's CUDA toolkit installs into a versioned directory such as `/usr/local/cuda-12.4` and creates a symlink `/usr/local/cuda` pointing at the default version. Switching CUDA versions is just repointing that link (section 5).

More detail on the directories that cause the most confusion:

- **`/bin` and `/sbin`.** `/bin` holds ready-to-run programs, including most basic commands such as `ls` and `cp`; most are compiled binaries but some are shell scripts. `/sbin` holds **system-administration** programs (`fdisk`, `iptables`, `reboot`); regular users often do not have the sbin directories in their command path, and many of these tools only work as root.
- **`/lib` and libraries.** Libraries are code that executables share. They come in two kinds, **static** (linked into a program at build time) and **shared** (loaded at run time, `.so` files). `/lib` should contain only shared libraries, while other `lib` directories such as `/usr/lib` hold both kinds plus auxiliary files. Chapter 1.11 explains shared libraries.
- **`/tmp` and `/var/tmp`.** `/tmp` is for small temporary files you do not care about: any user may create files there but cannot touch each other's. Most distributions clear it at boot and some delete old files periodically, so **never keep anything important in `/tmp`**; and do not let it fill up, because its space is often shared with something critical such as the root filesystem. `/var/tmp` is similar but is not wiped at boot.
- **`/run`.** Runtime data since boot: PID files, sockets, status records and, often, logging state. It is a relatively recent addition; on older systems this lived in `/var/run`, which is now normally a symlink to `/run`.
- **`/usr`.** Pronounced "user", but it contains **no user files**: it holds the bulk of the installed system and has subdirectories that mirror the root (`/usr/bin`, `/usr/sbin`, `/usr/lib`). The split exists for historical reasons (the root filesystem used to be kept small). Beyond those: `/usr/include` has the C compiler's header files; **`/usr/local`** is where administrators install their own software and should mirror the structure of `/` and `/usr` (so local binaries go in `/usr/local/bin`); **`/usr/share`** holds architecture-independent data that programs read as needed, which in practice means documentation (`man`, `info`, `doc`) and many auxiliary files (long ago it could be shared from a file server, but that is now rare).
- **`/var`.** The "variable" directory where programs record information that changes over time: logs, caches, queues, user-tracking data, spool files.
- **`/boot`, `/media`, `/opt`.** `/boot` contains only the files for the very first stage of startup (the kernel and boot loader files), not information about how services start; `/media` is the usual attachment point for removable media; `/opt` may hold additional third-party software, though many systems do not use it.
- **Where the kernel and its modules are.** On Linux the kernel is a binary file, normally `/boot/vmlinuz-<version>` (historically `/vmlinuz`), which the boot loader loads into memory and starts. After that the file is no longer used by the running system. **Loadable kernel modules**, which the kernel loads and unloads on demand (chapter 1.1; the GPU driver is one), live under `/lib/modules/<kernel version>/`, which is why a module built for one kernel version is not found under another.

When you hit a path you do not recognise, `man hier` (or `man 7 hier`) describes the layout on your system.

## 3. File types and what `ls -l` really shows

The kernel knows several kinds of file. The first character of the `ls -l` line tells you which:

```
$ ls -l /etc/hostname /usr/bin/ls /dev/null /dev/nvme0n1 /run/munge/munge.socket.2 /bin
-rw-r--r-- 1 root root   12 Oct 23 10:02 /etc/hostname
-rwxr-xr-x 1 root root 142K Mar 14  2025 /usr/bin/ls
crw-rw-rw- 1 root root 1, 3 Oct 23 09:58 /dev/null
brw-rw---- 1 root disk 259, 0 Oct 23 09:58 /dev/nvme0n1
srwxrwxrwx 1 munge munge 0 Oct 23 09:58 /run/munge/munge.socket.2
lrwxrwxrwx 1 root root    7 Mar 14  2025 /bin -> usr/bin
```

| Char | Type | Meaning |
|---|---|---|
| `-` | regular file | bytes: text, a program, an image, a checkpoint |
| `d` | directory | a file that lists other names |
| `l` | symbolic link | a small file that contains another path |
| `c` | character device | stream-oriented device (terminals, `/dev/null`, `/dev/nvidia0`) |
| `b` | block device | storage-style device with addressable blocks (disks, partitions) |
| `s` | socket | an endpoint for local inter-process communication |
| `p` | named pipe (FIFO) | a pipe that has a name in the filesystem |

The remaining columns of a long listing are: the nine **permission** characters (`rwxr-xr-x`, explained in chapter 1.6), the **link count**, the **owner** and **group**, the **size** in bytes (for devices, the major and minor numbers that identify the driver and unit), the **modification time**, and the **name** (with `-> target` for symlinks).

The command `file` identifies a file from its *contents*, not its name, by looking for characteristic starting bytes ("magic numbers"). It is the right first step with an unknown file: `file model.bin`, `file /usr/bin/python3`, `file run.sh` (which also reports CRLF line endings, the trap from chapter 1.2).

## 4. Inodes: what a file really is

A file in Linux is not its name. Underneath, a filesystem keeps for every file an object called an **inode** (index node), which holds everything about the file *except its name and its data*:

- the file type and permission bits;
- the owner and group IDs;
- the size, and the timestamps (section 6);
- the **link count**: how many names point at this inode;
- where the data blocks live on the device.

A **directory** is a special file that holds a simple table of **(name → inode number)** entries. That is all a directory is. When you open `/home/alice/train.py`, the kernel walks the path component by component: it looks up `home` in the root directory's table to get an inode, then `alice` in that directory's table, then `train.py`, arriving at the file's own inode and then its data.

```mermaid
flowchart LR
  subgraph D["Directory /home/alice (a table)"]
    n1["train.py → inode 7401"]
    n2["run.sh → inode 7402"]
    n3["latest → inode 7420"]
  end
  n1 --> I1["inode 7401<br/>type, mode, owner, size<br/>times, link count = 1<br/>data block pointers"]
  I1 --> B1["data blocks on disk"]
  n2 --> I2["inode 7402"]
```

See it directly:

```bash
ls -li ~/project            # first column is the inode number
stat train.py               # all of the inode's metadata, in readable form
df -i /home                 # inode usage per filesystem (not just bytes!)
```

This model explains several behaviours that otherwise seem arbitrary:

- **Renaming a file within a filesystem is instant**, regardless of size: only the directory table entry changes. Moving across filesystems must copy the data and then delete the original.
- **Deleting a file removes a name, not data.** The command `rm` calls `unlink`, which removes the entry and decrements the inode's link count. The data is freed only when the link count reaches zero **and no process still has the file open**. A running program can keep using a deleted file (section 8, failure mode 4).
- **A filesystem has two independent capacities:** bytes of data blocks, and the number of inodes. Creating millions of tiny files can exhaust inodes while plenty of bytes are free, producing "No space left on device" with a seemingly half-empty disk. Datasets of small images or text shards make this a real AI-infrastructure concern (failure mode 1).
- **A file can have several names.** That is what hard links are.

## 5. Links: hard and symbolic

### Hard links

A **hard link** is simply another directory entry pointing at the same inode. After `ln a.txt b.txt`, both names are completely equal citizens of the same file; the link count is 2; editing through either changes the one set of data; deleting one name leaves the file intact under the other. There is no "original".

```bash
echo hello > a.txt
ln a.txt b.txt              # hard link: same inode
ls -li a.txt b.txt          # identical inode numbers, link count 2
rm a.txt; cat b.txt         # still prints hello
```

Hard links have two limits that follow from the model: they **cannot cross filesystems** (inode numbers are only meaningful within one filesystem; the error is "Invalid cross-device link", EXDEV), and by default they **cannot point to directories**. They are used for deduplication (backup tools such as `rsnapshot` and `rsync --link-dest` use them heavily) and appear inside package and image storage.

### Symbolic (soft) links

A **symbolic link** (symlink) is a tiny file of type `l` whose content is a *path*, resolved each time the link is used. It can point anywhere: another directory, another filesystem, even a path that does not exist.

```bash
ln -s /usr/local/cuda-12.4 /usr/local/cuda     # needs root; "latest version" pointer
ls -l /usr/local/cuda                          # cuda -> /usr/local/cuda-12.4
readlink -f /usr/local/cuda                    # the final target, fully resolved
```

Properties: a symlink to a missing target is a **dangling link**; `ls -l` shows it but opening it fails with "No such file or directory". Relative targets are interpreted relative to the *link's* directory, not your current one, which is why moving a relative symlink often breaks it. Symlinks are cheap and used everywhere: `/usr/bin/python3 -> python3.12`, the `/lib` merge, `latest` pointers for checkpoints and releases, CUDA version switching.

Symlinks have pitfalls worth learning once. **Argument order:** `ln -s TARGET LINKNAME` (the target first, as in `ln -s /usr/local/cuda-12.4 /usr/local/cuda`). If you reverse the arguments and `LINKNAME` is an existing directory, `ln` quietly creates a link *inside* that directory, named after the target, and (unless you used a full path) the new link points at itself; if a symlink to a directory misbehaves, look inside the directory for stray links. **Forgetting `-s`** creates a *hard link* instead of a symbolic one; hard links are subtler and best avoided until you are comfortable with inodes. **Chained links** (a link pointing at a link) are legal and a nuisance to trace: `readlink -f` follows the whole chain. **You cannot tell whether a link points to a file or a directory from its name**, only by following it, and you can easily edit what you believe is a private copy but is really a link to the original. Finally, a dangling link is confusing because `ls` shows it but any other program reports that the name does not exist. The reasons to use symlinks anyway are practical: a program expects a file or directory at a fixed path, you cannot or do not want to change the program, and you do not want a second copy; and they let you reorganise or switch versions with one command.

| | Hard link | Symbolic link |
|---|---|---|
| Is | another name for the same inode | a separate small file containing a path |
| Across filesystems | no | yes |
| To directories | no (normally) | yes |
| If the original is deleted | still works | becomes dangling |
| Shows in `ls -l` as | an ordinary file with link count above 1 | `l`, with `->` target |
| Typical use | backups, deduplication | version pointers, convenience paths |

### The atomic "latest" pattern

A very common AI-infrastructure idiom is a `latest` symlink to the newest checkpoint that readers can switch to without ever seeing a half-written state. Renaming a symlink *over* another is atomic on a filesystem:

```bash
ln -sfn checkpoints/step_001000 latest.tmp   # create the new link under a temporary name
mv -T latest.tmp latest                       # atomic replace (rename over the old link)
```

Here `-f` replaces an existing link, `-n` treats an existing directory-symlink as a file instead of descending into it, and `mv -T` treats the destination as a normal name. Readers following `latest` always see either the old or the new target, never nothing.

## 6. Timestamps

Every inode records three times, shown by `stat`:

| Name | Abbrev. | Changes when | Shown by |
|---|---|---|---|
| Modification time | mtime | the **contents** are written | `ls -l`, `ls -lt` |
| Change time | ctime | the **inode** changes: permissions, owner, link count, or content | `ls -lc`, `stat` |
| Access time | atime | the file is **read** (subject to a mount option, below) | `ls -lu`, `stat` |

Notes: ctime is not "creation time" (a common mistake); modern filesystems may also record a creation (birth) time, which `stat` shows when available. To limit write overhead, Linux mounts filesystems with `relatime` by default, which updates atime only occasionally, so do not rely on atime to find unread data. `touch -d "2026-01-01 12:00" file` sets mtime (and atime) for testing, but you cannot set ctime. These times drive `find -mtime`, `make`'s rebuild decisions, `rsync`'s change detection and backup tools.

## 7. Names, extensions and finding things

**Naming conventions.** Linux does not care about extensions, but tools and humans do. Stick to lowercase letters, digits, `-`, `_` and `.`; avoid spaces and leading dashes; never put a newline in a name. A file whose name starts with `.` is **hidden** from plain `ls` (use `ls -a`) and from the `*` glob. Typical conventions: `.sh` scripts, `.py` Python, `.conf`/`.cfg`/`.ini`/`.yaml` configuration, `.log` logs, `.tar.gz` archives, `.so` shared libraries, `.service` systemd units, `.pt`/`.safetensors` model weights. Executability comes from the permission bit and a `#!` first line, not the extension (chapter 1.9). On macOS the default filesystem (APFS) is case-**insensitive**, while Linux is case-sensitive, so `Model.pt` and `model.pt` collide on a Mac and are two files on a server, a frequent source of "works on my laptop" bugs.

### `find`: search by properties

`find` walks a directory tree and tests each file against conditions you give it. It is the most important file-search tool.

```bash
find /var/log -type f -name '*.log'                 # regular files named *.log (quote the pattern!)
find /data -type f -size +1G                        # files larger than 1 GiB
find /tmp -type f -mtime +7                         # modified more than 7 days ago
find . -type f -newer reference.txt                 # newer than another file
find . -type d -empty                               # empty directories
find /home -user alice -perm -o+w                   # owned by alice and world-writable
find . -name '*.pyc' -delete                        # act on every match (careful)
find . -type f -name '*.log' -exec gzip {} \;       # run a command per file
find . -type f -name '*.log' -exec gzip {} +        # batch many files per command (faster)
find . -type f -print0 | xargs -0 ls -l             # safe with spaces; xargs in chapter 1.4
```

Remember to quote patterns (`'*.log'`) so the shell does not expand them first (chapter 1.2). Combine tests with implicit AND, `-o` for OR, and `\( ... \)` for grouping. Always run a `find` without `-delete` first and read the list.

**The basic form first.** Learn this until it is automatic: `find DIR -name 'PATTERN' -print`, where `DIR` is where to start, `-name` matches the file name against a pattern, and `-print` prints each match (GNU `find` prints by default if no action is given, but older and other versions require it). The pattern is single-quoted because `find`, not the shell, must interpret the `*` and `?`; unquoted, the shell would expand it against the current directory first. Only once that form is second nature should you reach for `-exec`, `-delete` and the other actions, because an action applied to the wrong set of files is how data is lost.

### `locate`: search by name in an index

`locate name` searches a prebuilt database of all file names (built by `updatedb`, usually nightly), so it is instant but may be **stale**: new files are missing and deleted ones still appear. Use it for "where is that config file?", and `find` when you need current truth or property tests. Some systems install `plocate` or `mlocate` as the implementation.

### Where is that command?

`type -a cmd`, `command -v cmd`, `which cmd`, and `whereis cmd` (binary, source and man page locations) answer "which file runs when I type this?" (chapter 1.2).

## 8. Archiving and compression

Moving a whole directory tree as one object, or saving a snapshot of it, needs an **archive**: a single file that contains many files plus their metadata (names, permissions, owners, times). The classic tool is **`tar`** (tape archive). Archiving and compressing are separate steps: `tar` collects; a compressor shrinks. Combining them gives names like `.tar.gz`.

Four modes, each with an option letter, and a few modifiers:

| Option | Meaning |
|---|---|
| `-c` | create an archive |
| `-x` | extract |
| `-t` | list the contents (table of contents) without extracting |
| `-f FILE` | the archive file (`-f -` means standard input or output) |
| `-v` | verbose: list files as they are processed |
| `-z` | filter through gzip (`.tar.gz`, `.tgz`) |
| `-j` | bzip2 (`.tar.bz2`) |
| `-J` | xz (`.tar.xz`) |
| `--zstd` | zstd (`.tar.zst`) |
| `-C DIR` | change to DIR before working (extract elsewhere, archive relative paths) |
| `--strip-components=N` | drop N leading path levels when extracting |

```bash
tar -czf project.tar.gz project/              # create, gzip
tar -tzf project.tar.gz | head                # ALWAYS list before you extract an unknown archive
tar -xzf project.tar.gz -C /tmp/restore       # extract into a chosen directory
tar -cf - project | ssh gpu01 'tar -xf - -C /data'   # stream a tree over SSH without a temp file
zcat file.gz | head                           # read a gzip file without unpacking (also zless, zgrep)
```

Details of the classic usage, which you will see in every README:

- **`gzip` compresses one file** (`gzip file` replaces `file` with `file.gz`) and does not make archives; `gunzip file.gz` (or `gzip -d`) restores it and removes the `.gz` suffix. `gzip -k` keeps the original. A `.gz` file is a GNU zip file, and `.tar.gz` is a tar archive that was then gzipped.
- The traditional `tar` command is written without a dash: `tar cvf archive.tar file1 dir2` creates (`c`), verbosely (`v`; a second `v` adds sizes and permissions), into the file named by `f`. The **`f` flag must be followed by the archive's name** (use `-` for standard input or output), which is why `f` is conventionally the last letter in a bundle like `cvf` or `xzf`. `tar xvf archive.tar` extracts; you can name individual members at the end to extract just those (you must give their exact names, which `t` shows you). `tar` never deletes the archive after extracting.
- **`t` is also an integrity check.** Listing reads the whole archive, so it verifies the archive is readable as well as showing its contents. Check that **all paths start with one common top-level directory**; if not, extract into a new empty directory (you can always move things up afterwards).
- **Permissions on extraction.** The `p` option restores the exact permissions stored in the archive, overriding your `umask`; it is the default when you extract as root. `tar` has to read the *whole* archive even to extract one member, and it applies permissions and ownership **at the end**, so do not interrupt it, and wait for the shell prompt before judging the result.
- **Decompress from the right.** A `.tar.gz` is two layers; peel the outer one first: `gunzip file.tar.gz` then `tar xvf file.tar`. To create, reverse the order (`tar` first, `gzip` second). That works but writes an intermediate file, wasting disk space and I/O, so combine them in a pipe, `zcat file.tar.gz | tar xvf -` (`zcat` is `gunzip -dc`: decompress to standard output), or use the GNU `tar` shortcut `z`: `tar xzvf file.tar.gz`, `tar tzvf file.tar.gz`. Remember that the shortcut still performs two steps. A **`.tgz`** file is just a `.tar.gz` (the short suffix was chosen to fit old DOS-style filesystems).
- **Other compressors.** `xz` (`.xz`, undone with `unxz`) and `bzip2` (`.bz2`, undone with `bunzip2`) are slightly slower than `gzip` and often compress text a little better; their options are close enough to `gzip`'s that you do not need to relearn anything. `zip` and `unzip` handle the Windows ZIP format, including self-extracting `.exe` archives. A file ending in `.Z` is a relic of the old `compress` program: `gunzip` can read it, `gzip` will not create it.

**Compressors compared:** `gzip` is fast and universal; `bzip2` compresses better and slower; `xz` compresses best and is slow; **`zstd`** gives gzip-like speed with much better ratios and is a good modern default; `pigz` and `pbzip2` are parallel versions of gzip and bzip2 that use many cores for big files. **Do not compress what is already compressed**: model checkpoints in `.safetensors`, images, video and most archives gain nothing and waste CPU. `zip`/`unzip` produce portable archives for sharing with other operating systems.

Safe-use rules that prevent real accidents:

1. **List before extracting** (`tar -tf`). Some archives contain absolute paths (`/etc/...`) or `..` components. GNU tar strips a leading `/` by default and warns, but do not rely on it for untrusted archives.
2. **Extract into an empty, dedicated directory** (`-C`). A "tarbomb" dumps hundreds of files into the current directory instead of one subdirectory.
3. **Mind ownership when running as root.** Extracting as root restores the archived owners and permissions, which may create files owned by UIDs that do not exist on this machine, or clobber system files. Extract as a normal user unless you need ownership preserved.
4. **Verify integrity of large transfers** with a checksum: `sha256sum file.tar.gz` on both ends.
5. Create archives with **relative paths** from a clean location: `tar -czf x.tar.gz -C /data dataset/`, so that extraction does not depend on where it was created.

## 9. AI-infrastructure patterns, in one place

- **Datasets of millions of small files** stress inode counts, directory lookup time and metadata servers on network filesystems. Pack small files into shards (tar-based formats such as WebDataset, Parquet, TFRecord) and read them sequentially. This is a major topic in chapter 13.6.
- **Checkpoints** are huge sequential files; write them to a temporary name and rename when complete (a rename within a filesystem is atomic) so a crash mid-write never leaves a corrupt "latest". Use the symlink pattern from section 5.
- **`/dev/shm`** is an in-memory filesystem used by PyTorch data loaders and NCCL for shared memory between processes. Its default size is small inside containers (Docker defaults to 64 MB), which causes mysterious dataloader crashes; the fix is to enlarge it (`--shm-size`, or an `emptyDir` with `medium: Memory` in Kubernetes).
- **`/tmp` is not scratch for big data.** It may be small, cleaned automatically, or on the root disk; use node-local NVMe mounts for scratch (chapter 13.2).
- **`/proc` and `/sys` are your hardware dashboard:** `/proc/driver/nvidia/gpus/*/information`, `/sys/class/infiniband/*/ports/1/rate`, `/sys/bus/pci/devices/*/numa_node`. Read these to confirm what the kernel sees.

## How it fails

### 1. "No space left on device" but `df -h` shows free space
**Symptom:** writes fail with ENOSPC. **Cause:** the filesystem ran out of **inodes**, not bytes (typically millions of tiny files), or a per-user or project quota is reached, or a container's writable layer is full. **Diagnose:** `df -h` **and** `df -i` on the path, `find /dir -xdev -type f | wc -l`, `quota -s` where used. **Fix:** delete or pack the small files, recreate the filesystem with more inodes (`mkfs.ext4 -N` or a different filesystem such as XFS, which allocates inodes dynamically), or move the data. Prevention: shard datasets.

### 2. A dangling symlink: `latest -> checkpoints/step_900` but the directory was cleaned
**Symptom:** `cat latest/model.pt`: No such file or directory, though `ls -l latest` shows the link. **Diagnose:** `readlink latest`, `ls -l $(readlink -f latest)`, `find . -xtype l` (lists broken symlinks). **Fix:** repoint the link, and make retention scripts update the link before deleting its target. Relative link targets move with their link's location, so test after moving directories.

### 3. "Invalid cross-device link" when hard-linking or renaming
**Symptom:** `ln` or `mv` fails with EXDEV, or a tool that "renames to publish" suddenly copies and is slow. **Cause:** source and destination are on different filesystems (a mount boundary, a different volume, an overlay), so inode links and atomic rename are impossible. **Diagnose:** `df path1 path2`, `stat -c %d path` (device number). **Fix:** write the temporary file on the same filesystem as the final path, use symlinks instead of hard links, or accept a copy.

### 4. The disk is full, but `du` cannot find the files: deleted but still open
**Symptom:** `df` shows 95% used, `du -sh /*` totals much less. **Cause:** a large log or temporary file was deleted while a process still has it open (the data is retained until the process closes it or exits); the name is gone, the space is not. **Diagnose:** `sudo lsof +L1` (open files with link count below 1), or `ls -l /proc/<pid>/fd | grep deleted`. **Fix:** restart or signal the process to reopen its log (`logrotate` with `copytruncate` or `postrotate` handles this properly), or truncate through the descriptor: `: > /proc/<pid>/fd/<n>`.

### 5. An archive overwrote system files or exploded the working directory
**Symptom:** after `sudo tar -xf x.tar` strange files appear in the current directory or `/etc` changed. **Cause:** a tarbomb, absolute paths, or root restoring archived ownership. **Diagnose:** `tar -tf x.tar | head -50`, `tar -tf x.tar | awk -F/ '{print $1}' | sort -u`. **Fix:** always list first, extract with `-C` into an empty directory as a normal user, and use `--no-same-owner` and `--no-same-permissions` when you do not want the archive to dictate them.

### 6. `ls` or a job takes forever in a directory with millions of entries
**Symptom:** listing or globbing a dataset directory hangs, `rm *` says "Argument list too long". **Cause:** large directories are slow to read and sort, especially on network filesystems where every entry may cost a metadata round trip, and globs expand into one huge command. **Diagnose:** `ls -f dir | wc -l` (unsorted, much faster), `strace -c ls dir`. **Fix:** avoid listing; use `find -print0 | xargs -0`; split data across subdirectories (`aa/bb/file` sharding by hash prefix); use shards instead of loose files.

## Hands-on lab (a GCP Ubuntu VM; untested)

Work in a scratch directory (`mkdir -p ~/lab/files && cd ~/lab/files`).

**Part A: paths and the tree.**
1. Run `tree -L 2 /` if `tree` is installed (`sudo apt install tree`), or `ls /`. For each top-level directory, state its FHS purpose without looking at section 2, then check.
2. Confirm "merged usr": `ls -ld /bin /sbin /lib` and `readlink -f /bin/ls`. Where does `/usr/bin/python3` really point? (`readlink -f $(command -v python3)`)
3. Explore `/proc` and `/sys` read-only: `cat /proc/meminfo | head -3`, `cat /proc/sys/kernel/hostname`, `ls /sys/class/net`, `cat /sys/class/net/*/mtu`. Explain why `ls -l /proc/cpuinfo` shows size 0 yet `cat` prints text.

**Part B: types and inodes.**
4. Create one of each type you can (a file, a directory, a symlink, a FIFO with `mkfifo p`) and list them with `ls -l`; read the type characters. Find a `c`, a `b` and an `s` file on the system (`ls -l /dev | head -30`, `find /run -type s 2>/dev/null`).
5. `echo data > f1; ls -li f1; stat f1`. Identify inode, size, link count and the three times. Run `cat f1` and check that atime does or does not change (relatime), then `echo more >> f1` and see mtime and ctime change; then `chmod 600 f1` and see only ctime change. Explain each.

**Part C: links.**
6. Make a hard link and a symlink to `f1`. Compare inode numbers and link counts. Delete `f1`; which still works and why? Make the symlink target relative and move the link to another directory; observe it break.
7. Try a hard link across filesystems: `ln /etc/hostname /dev/shm/x` (or between `/tmp` and your home if they are separate mounts). Record the error and explain it in terms of inodes.
8. Implement the atomic `latest` pattern from section 5 with three fake checkpoint directories. In a second terminal run `while true; do readlink latest; done` while repointing `latest` in a loop; confirm the reader never sees an empty result.

**Part D: inode exhaustion and deleted-but-open files (needs sudo).**
9. Inode exhaustion safely: `sudo mkdir /mnt/t && sudo mount -t tmpfs -o size=10m,nr_inodes=200 tmpfs /mnt/t`, then `for i in $(seq 1 300); do sudo touch /mnt/t/f$i || break; done`. Observe the error, run `df -h /mnt/t` and `df -i /mnt/t`, and explain why one shows free space and the other full. Clean up with `sudo umount /mnt/t`.
10. Deleted-but-open: `sudo dd if=/dev/zero of=/tmp/big bs=1M count=200`, then `sleep 600 < /tmp/big &`, then `rm /tmp/big`. Compare `df -h /tmp` before and after the delete, find the culprit with `sudo lsof +L1 | grep big`, release it with `kill %1`, and watch the space return.

**Part E: find, file and archives.**
11. Use `find` to list files in `/var/log` larger than 1 MiB, regular files modified in the last day, and broken symlinks under `/etc` (`find /etc -xtype l`). Use `file` on a script, a binary, an image and a gzip file.
12. Create a directory with a few files, then `tar -czf a.tar.gz dir`, `tar -tzf a.tar.gz`, extract into `/tmp/out` with `-C`, and verify with `diff -r dir /tmp/out/dir`. Create an archive with absolute paths (`tar -cf abs.tar /etc/hostname 2>&1 | head`) and read GNU tar's warning. Compare sizes and times of gzip, xz and zstd on a copy of `/usr/share` (`time tar -cf - /usr/share/doc | gzip | wc -c`, with `xz -T0` and `zstd -T0`).
13. Safety drill: build a tarbomb on purpose (a tar whose members have no common top directory), extract it in the wrong place, and clean up. Then extract it correctly with `-C`.

## Checkpoint questions

1. What is the difference between an absolute and a relative path? Why do automation scripts prefer absolute paths?
2. Where would you look for: a service's configuration, its logs, its runtime socket, a device file, the kernel image, a user's files?
3. What are `/proc` and `/sys`? Do they take disk space? Why can reading `/proc/meminfo` give different answers a second apart?
4. What does the first character of an `ls -l` line tell you? Name five values.
5. What is an inode, and what information does it not contain?
6. What does a directory contain? What happens, step by step, when the kernel opens `/home/alice/a.txt`?
7. Explain why renaming a 100 GB file in the same directory is instant but moving it to another disk takes minutes.
8. What happens to a file's data when you `rm` its only name? What if a process still has it open?
9. Compare hard links and symbolic links on four properties.
10. Why does `ln` fail with "Invalid cross-device link"?
11. What do mtime, ctime and atime each record? Which one changes when you run `chmod`?
12. A disk reports "No space left on device" but `df -h` shows 40% free. Give two causes and the commands to confirm them.
13. `df` says the disk is almost full but `du` finds little. What is the most likely cause and how do you find it?
14. Why should you run `tar -tf` before `tar -xf` on a file from the internet? What is a tarbomb?
15. Why is `Model.pt` versus `model.pt` a problem when moving between a Mac and a Linux server?
16. How do you update a `latest` symlink atomically?

### Answers

1. An absolute path starts at `/` and names the same file regardless of context; a relative path is resolved from the process's current working directory. Scripts started by cron, systemd, Slurm or containers do not share your working directory, so absolute paths (or an explicit `cd`) avoid errors.
2. Configuration in `/etc`; logs in `/var/log` (or the journal); runtime sockets and PID files in `/run`; device files in `/dev`; the kernel image in `/boot`; user files in `/home`.
3. They are virtual filesystems generated by the kernel on demand: `/proc` exposes processes and system state, `/sys` exposes devices, drivers and kernel objects. They use no disk space. The values are computed from live kernel state, so they change from moment to moment.
4. The file type: `-` regular file, `d` directory, `l` symlink, `c` character device, `b` block device, `s` socket, `p` named pipe.
5. An inode is the filesystem's record of a file: type, permissions, owner, size, timestamps, link count and the location of the data. It does not contain the file's name or (directly) its content.
6. A directory contains a table mapping names to inode numbers. To open the path, the kernel looks up `home` in `/`, then `alice` in `/home`, then `a.txt` in `/home/alice`, ending at that file's inode, checking permissions at each step.
7. A same-filesystem rename only changes a directory entry; a move to another filesystem must copy all data blocks and then delete the original.
8. `rm` removes the name and decrements the link count. If the count reaches zero and no process has the file open, the space is freed; if a process still has it open, the data stays until the process closes it.
9. Hard link: same inode, cannot cross filesystems, cannot point to directories, survives deletion of the other name. Symlink: separate file containing a path, can cross filesystems, can point to directories and missing targets, breaks if the target disappears.
10. Hard links reference an inode number, which only has meaning within one filesystem, so a link cannot be created from a different filesystem.
11. mtime: contents modified; ctime: inode metadata changed (permissions, owner, link count, content); atime: last read (subject to `relatime`). `chmod` changes ctime.
12. Inode exhaustion (`df -i` shows 100%) and quota limits (`quota -s`, or project/user quotas); also a full container writable layer. Confirm with `df -i`, `quota`, and `df` inside the container.
13. A deleted file still held open by a process. Find it with `lsof +L1` or `ls -l /proc/*/fd | grep deleted`, then restart the process or truncate through its descriptor.
14. Archives may contain absolute paths, parent-directory components or many top-level files; listing shows what extraction would do. A tarbomb is an archive without a single top-level directory, scattering files into the current directory.
15. APFS on macOS is case-insensitive by default, so the two names collide into one file, while Linux treats them as separate files, so code working on a Mac may fail or use the wrong file on Linux.
16. Create the new link under a temporary name and rename it over the old one: `ln -sfn target latest.tmp && mv -T latest.tmp latest`; the rename is atomic.

## Sources and further reading

- Brian Ward, *How Linux Works*, 3rd ed., ch. 2 (file naming and `file`, `find` and `locate`, symbolic links, archiving and compressing with gzip, tar and zcat, the Linux directory hierarchy essentials including `/usr` and kernel location) and ch. 4 for the inode model, which is expanded in chapter 1.12.
- Sergey Zhumatiy, *Supercomputers for Linux SysAdmins*, ch. 7 (file naming conventions, extension agreements, commands for directory trees and files), used for the cluster-administration viewpoint.
- Man pages: `man 7 hier`, `man 1 find`, `man 1 tar`, `man 1 ln`, `man 2 stat`, `man 7 inode`, `man 5 proc`.
- Related chapters: 1.12 disks and filesystems, 1.6 permissions, 13.6 data loading and small files, 13.7 checkpoints.

*Notes for review:* the container default of 64 MB for `/dev/shm`, the `relatime` default and the "merged usr" status are standard for current mainstream distributions and container runtimes but should be confirmed on the exact versions you deploy. All lab commands are **untested** and must be run on a Linux VM before this chapter moves to `reviewed`.
