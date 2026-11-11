# Voice sample 2: parts part-01-linux, part-14-training-finetuning

## FILE docs/part-01-linux/01-the-linux-big-picture-kernel-userspace-distributions.md

The cause of any such failure lives in one specific layer of the system. You can only find it quickly if you can name the layers and know what each one does. Each component has a tremendous amount of internal detail, and we will set that aside at first. We will focus on what each component does for the whole system.

---

Picture a GPU server with several training jobs running at once. Each job wants CPU cores, memory, disks, and GPUs, but the machine has only one set of each. As you will see, the operating system is what makes that sharing possible. The shared resources here are processor cores, memory, storage, network cards, and GPUs. Without something in charge, every program would have to know how to talk to every kind of disk and network card. Programs could read and overwrite each other's memory, and one runaway program could freeze the whole machine.

---

Everything the kernel does fits under four headings: processes, memory, devices, and system calls. Programs normally use system calls to reach the kernel. We will briefly explore each of these four areas here, then meet them in depth in chapters 1.8, 1.10, 1.11, and 1.17. If you want the detailed academic and source-level view of a kernel, read two classic textbooks. One is *Operating System Concepts*, 10th edition, by Abraham Silberschatz, Peter B. Galvin, and Greg Gagne. The other is *Linux Kernel Development*, 3rd edition, by Robert Love.

---

Linux is a multi-user system. Each user has a numeric **user ID**, or **UID**, and belongs to one or more groups. Each group has a numeric **group ID**, or **GID**. Every process runs *as* some UID and GID, and every file has an owner and a group. The kernel makes access decisions by comparing these numbers with permission bits stored on files. The special account **root** has UID 0, and it bypasses most permission checks.

---

## FILE docs/part-01-linux/02-the-command-line-shells-commands-pipes-and-redirection.md

Second, **every Unix system needs a Bourne-compatible shell at `/bin/sh`**, because system scripts assume it is there. On some distributions `/bin/sh` is a link to bash. On **Debian and Ubuntu it is dash**, a smaller, faster POSIX shell that lacks bash extensions such as arrays and `[[ ]]`. That difference bites scripts. A script that starts with `#!/bin/sh` but uses bash features works on one distribution and fails on another. Check with `ls -l /bin/sh`.

---

The GNU project publishes many manuals in **info** format. Run `info coreutils`, navigate it with its own keys, or pipe it through `less`. Info pages often hold more detail than the man page. Some packages also install README files and examples under `/usr/share/doc`, with no man or info page at all. For a fast option check, `command --help` or `command -h` prints a short usage summary. Inside `man`, press `/word` to search forward, `n` to jump to the next match, and `q` to quit. On a cluster, **the manual of the exact version installed on the machine is authoritative**. Trust `man slurm.conf` on your login node over any blog post.

---

Keeping errors in a *separate* stream was a deliberate design choice, and it matters a lot. You can capture results without mixing in warnings. You can still see errors when the output is redirected. The shell rewires these descriptors before it starts a program, and the program does not know or care where they lead. This is the "everything is a file" idea from chapter 1.1, applied to standard streams.

---

The table leaves out two points. First, **`>` destroys the previous contents of the target file the moment the command starts**, even if the command then fails. A typo such as `sort data.txt > data.txt` empties the file before `sort` reads it. In bash, `set -o noclobber` or `set -C` makes `>` refuse to overwrite an existing file. You can force an overwrite with `>|`, and that is a worthwhile safety net in interactive shells. Second, pipes can chain as many commands as you like, one after another. For example, `head /proc/cpuinfo | tr a-z A-Z` upper-cases the first lines of the CPU description. The `<` operator is rarely needed, because most commands accept file names directly. `head < /proc/cpuinfo` and `head /proc/cpuinfo` do the same thing. A few programs only read standard input, though.

---

## FILE docs/part-01-linux/03-files-and-the-directory-hierarchy-paths-links-inodes.md

An **absolute path** starts with `/` and means the same thing everywhere, such as `/home/alice/project/train.py`. A **relative path** does not start with `/`. The system reads it from the **current working directory** (`pwd`) of the process, so `project/train.py` depends on where the process started. Relative paths are convenient at a prompt. They are also a classic source of script bugs, because the working directory is whatever the caller happened to be in. Cron jobs, systemd services, Slurm jobs and containers each start in a different directory. Automation should therefore use absolute paths, or `cd` explicitly first.

---

An example makes the dots clear. Suppose you are working in `/usr/lib`. Then `..` refers to `/usr`, and `../bin` refers to `/usr/bin`. The path `.` is still `/usr/lib`, so `./X11` means `/usr/lib/X11`. Most commands use the current directory when a path does not begin with `/`, so `X11` alone works just as well as `./X11`.

---

Symlinks have pitfalls worth learning once. Argument order matters. `ln -s TARGET LINKNAME` puts the target first, as in `ln -s /usr/local/cuda-12.4 /usr/local/cuda`. If you reverse the arguments and `LINKNAME` is an existing directory, `ln` quietly creates a link inside that directory, named after the target. Unless you used a full path, that new link points at itself. So if a symlink to a directory misbehaves, look inside the directory for stray links.

---

Linux does not care about extensions, but tools and humans do. Stick to lowercase letters, digits, `-`, `_` and `.`. Avoid spaces and leading dashes, and never put a newline in a name. A name that starts with `.` is hidden from plain `ls`, which needs `ls -a` to show it, and from the `*` glob. Common conventions include `.sh` for scripts, `.py` for Python, `.conf`, `.cfg`, `.ini` and `.yaml` for configuration, `.log` for logs, `.tar.gz` for archives, `.so` for shared libraries, `.service` for systemd units, and `.pt` or `.safetensors` for model weights. Executability comes from the permission bit and a `#!` first line, not from the extension. Chapter 1.9 covers that.

---

## FILE docs/part-01-linux/04-text-processing-essentials-grep-sed-awk-find-xargs-sort.md

Try a small practice in your terminal: `echo "step=120 loss=0.43" | grep -oE 'loss=[0-9.]+'` prints just the match. For the full specification, read `man 1 grep` and `man 7 regex`. They are dense, but they are the authoritative reference. To go deeper, Brian Ward's *How Linux Works* recommends *Mastering Regular Expressions*, 3rd edition, by Jeffrey E. F. Friedl (O'Reilly, 2006), and Chapter 20 of *Unix Power Tools*, 3rd edition, by Shelley Powers, Jerry Peek, Tim O'Reilly, and Mike Loukides (O'Reilly, 2002).

---

`paste a b` places files side by side, line by line. `join` merges two sorted files on a common field, like a small database join. `column -t` aligns whitespace-separated text into a readable table, as in `mount | column -t`. And `tee`, covered in chapter 1.2, copies a stream to a file and passes it onward.

---

Part G covers JSON. (18) Install `jq` with `sudo apt-get install -y jq`, then process `ip -j addr` to print each interface name with its first IPv4 address (untested here). (19) Use `jq` to pick two fields out of a JSON file you write by hand.

---

Part H covers the traps. (20) Make a file with mixed-case words, and show how `sort` and `LC_ALL=C sort` order them differently (untested here). (21) Demonstrate the `uniq` without `sort` pitfall. (22) Create a CRLF file and show that `grep '^ERROR$'` fails on it, then fix it with `tr -d '\r'`.

---

## FILE docs/part-01-linux/05-working-remotely-ssh-keys-file-transfer-tmux-and-editors.md

SSH combined with `scp`, `sftp` and `rsync` covers nearly all normal operation. This chapter teaches SSH from the beginning. It also covers the tools that make remote work reliable: `rsync`, `tmux`, parallel shells, an editor you can survive in, and out-of-band access for when the operating system is down. Learn the SSH core first, because the rest of the chapter builds on it.

---

Suppose you connect to a GPU server for the first time, and your client stops to ask you something. That question is there to protect you. **SSH (Secure Shell)** is a protocol and a pair of programs. The **client**, `ssh`, runs on your machine. The **server**, `sshd`, the daemon, runs on the remote machine and listens on TCP port 22 by default. SSH replaced older tools such as `telnet` and `rsh`. Those tools sent everything, passwords included, as plain text.

---

When a login fails, start with verbose output. `ssh -v host`, with up to `-vvv`, prints the negotiation step by step. It shows which keys were offered, which authentication methods the server allows, and where the attempt stopped. It is the single best tool for any login problem. On the server, the authentication log says why the server refused you. On Debian and Ubuntu, that log is `/var/log/auth.log`. On the Red Hat family, it is `/var/log/secure`. You can also use `journalctl -u ssh` or `journalctl -u sshd`. Read the client-side negotiation first, then the server log, before you change any setting.

---

Clusters have hundreds of nodes, so logging in to each one to check is not a plan. Suppose you want the GPU count on every node. You can ask all of them at once. Here are the main options, from simplest to most capable.

---

## FILE docs/part-01-linux/06-users-groups-permissions-acls-sudo-and-user-environments.md

An absolute change sets all of the permission bits at once. That is quick, but it is blunt, because the whole mode is replaced. Each digit in the mode is a number from 0 to 7 in base 8, and each digit stands for one permission set. You do not need to build these numbers from scratch every time. Learn the handful you use most often, such as `644` for ordinary files and `755` for programs and directories. The `chmod(1)` manual page or its info manual has the full rules.

---

Be careful with world-writable files. Obviously, you should not make a file writable by everyone, because that lets any user on the system change it. Could someone on the internet change it too? Probably not, unless the system has a network security hole. In that case, file permissions will not protect you anyway.

---

A program that needs its own username calls `geteuid()` to get the number. Then it asks the C library to map that number to a name with `getpwuid()`. The library decides where to look, and the site can configure that (section 8.5). This extra step is what lets a site move from local files to a network directory without changing any program. The old approach of simply reading `/etc/passwd` had three limits. It used one fixed hashing method, it always prompted for a password, and it had no support for tokens or smart cards. **PAM**, the Pluggable Authentication Modules framework, was created to remove those limits (chapter 1.21).

---

Why is account synchronization non-negotiable on a cluster? Shared filesystems, such as NFS, `Lustre` and `WEKA`, and workload managers, such as Slurm with munge (chapter 6.7), pass around **numeric UIDs and GIDs**, not usernames. Suppose alice is UID `1042` on the login node and UID `1043` on `gpu05`. Her training job on `gpu05` cannot read her own files on the shared home directory. And munge rejects her job steps when it validates their credentials.

---

## FILE docs/part-01-linux/07-packages-repositories-and-software-installation.md

Every package on your node came from somewhere. A **repository** is an indexed directory of packages. You can reach it over HTTP(S), read it from local disk, or read it from an optical medium. The index lets the manager find a package and its dependencies without downloading anything first. When you install an operating system, a repository (the installation medium or a network mirror) is set up for you. After installation, the main network repositories are added. These normally include separate channels for the base release, bug-fix updates and security updates.

---

The third question is "what would this install do?" Simulate the install before you run it. Use `apt install -s pkg` (or `apt-get -s`), or `dnf install --assumeno pkg`. Then read the list of packages that will be removed. If that list says an unrelated meta-package, such as `ubuntu-desktop` or a driver, will be **removed**, stop and find out why.

---

Preprocessor commands, called directives, begin with `#`. `#include <stdio.h>` inserts a file. Angle brackets mean "search the system include directories". Double quotes, as in `#include "greet.h"`, mean "look next to this source file first". If you hit a problem with a double-quoted include, the source is probably incomplete.

---

Notice a few things. `OBJS = ...` defines a macro, which you use as `$(OBJS)`. `CC` is predefined, with the default `cc`. The first target in the file, `all` here, is the default when you run `make` with no arguments. You wrote no rule for `main.o` or `greet.o`, because `make` has built-in rules that know how to get a .o file from a .c file, using `$(CC) -c` and the standard flag variables. The recipe lines must start with a tab. Spaces cause `*** missing separator. Stop.`

---

## FILE docs/part-01-linux/08-processes-signals-and-job-control.md

When you see high latency on a GPU node, interrupt latency is one place to look. **Preemption** is the ability to take the CPU away from something. User threads can always be preempted by the scheduler. Whether the kernel itself can be interrupted depends on a build option. With no preemption you get the best throughput and the worst latency. **Voluntary preemption**, the common server default, has the kernel check for preemption at certain points. Full preemption gives low latency for real-time use, through the `PREEMPT_RT` patch set. You can check the setting yourself with `uname -v` or in the kernel config.

---

Add `w` (up to three times) to widen the command column. `VSZ` is the virtual size, and `RSS` is the resident set, which is the physical RAM the process holds right now. Chapter 1.17 explains the difference. To list threads inside a multithreaded process, such as `Xorg` or a multi-worker Python process, pass `ps m` (BSD style) or `ps m -o pid,tid,command`. See `HLW` Listings 8-1 and 8-2. Lines with a dash (`-`) in the `PID` column are individual threads of the process above them. The `tid` column shows each thread's kernel Thread ID (`TID`).

---

The `si` column can rise when the kernel pulls pages back in from swap. This often happens when the new program uses shared library code that another process already loaded and that was swapped out. A few processes may also appear in the `b` column while they wait for memory pages. Disk traffic shows up in the `bi` and `bo` columns.

---

Three rules trip people up. Processes can live only in **leaf** cgroups, which have no child cgroups. The root cgroup is the exception. A child can use only the controllers that its **parent** has enabled in `cgroup.subtree_control`. And you must enable controllers explicitly. Editing `/sys/fs/cgroup` by hand on a systemd machine can conflict with systemd's own management. For anything beyond experiments, let **systemd** create the cgroup. It then gets a unit name and persists.

---

## FILE docs/part-01-linux/09-shell-scripting-that-survives-production.md

Make it a habit to double-quote every expansion, such as `"$var"`, `"$(cmd)"` and `"$@"`. Skip the quotes only when you have a specific reason. There are two exceptions. One is when you want splitting, such as a variable that holds a list of options, where an array usually serves better. The other is when you want globbing. ShellCheck flags the rest with `SC2086`.

---

The marker can be any word, though it is conventionally uppercase. It must appear alone on a line to end the block. An unquoted marker lets `$var`, `$(cmd)` and backslashes expand. A quoted marker, as in `<<'EOF'`, suppresses all of that. Quote it when you write another script or a config file that contains `$`. A **here string**, `<<< "$var"`, supplies a single string on standard input in bash. For example, `read -r a b <<< "$line"` splits one line into two variables. Here documents are the clean way to write multi-line files and to run remote scripts, as in `ssh node 'bash -s' <<'EOF' ... EOF`.

---

You may already have roundabout versions of these. Some common ones and their better forms are listed here: `echo "$var" | wc -c` → `"${#var}"`; `echo "$var" | sed 's/^.*abc//'` → `"${var#*abc}"`; `[ "x$VAR" = x ]` → `[ -z "${VAR:-}" ]`; `if [ -z "$VAR" ]; then VAR=abc; fi` → `VAR=${VAR:-abc}`; `cat file | grep x` → `grep x file`; `sort | uniq` → `sort -u` (but `sort | uniq -c` stays); `sudo su` → `sudo -s` or `sudo -i`.

---

Know whether a word is a builtin, a function, an alias or a program. Use `type -a cmd` to see every match. Use `command -v cmd` for a portable existence check. Use `which` only for external programs, since it is less reliable. `exec cmd` replaces the shell with `cmd`, and the shell never returns. Put it on the last line of a wrapper script, so signals go straight to the real program. `source file` includes another file. After you move programs around, run `hash -r` to clear the remembered command locations. `eval` runs a string as code, which makes it a common source of injection bugs. Avoid it, and use arrays instead.

---

## FILE docs/part-01-linux/10-devices-udev-sysfs-and-procfs.md

Device files are a convenience. Any program that can read and write files can talk to many devices, and some devices work with ordinary tools such as `cat`, `dd` and `less`. A plain read and write interface cannot express everything a device can do, though. The rest goes through the `ioctl` system call, as the NVIDIA driver does, or through `sysfs` attributes.

---

Traditional names such as `/dev/sda` and `/dev/sdb` are assigned in the order the kernel's drivers find devices. That order can change between boots, or after a disk is added or fails. Suppose three disks are `sda`, `sdb` and `sdc`, and `sdb` fails. The old `sdc` becomes `sdb`. An `fstab` entry that said `/dev/sdb1` now mounts the wrong disk, or none at all.

---

Assignments do the work. `NAME` applies only to network devices, because the kernel names device nodes itself. `SYMLINK+=` adds extra names. `OWNER`, `GROUP` and `MODE` set permissions. `TAG+=` adds a tag. `ENV{key}=` sets a property. `ATTR{name}=` writes a sysfs attribute. `RUN+=` runs a program after processing. `IMPORT{program}=` runs a program and imports its `KEY=value` output as properties. `GOTO` and `LABEL` jump within the file, and `OPTIONS+=` sets options.

---

A **driver** claims a device by matching the device's ID tables. Those tables might hold a PCI vendor and device pair, a USB class, or a device-tree compatible string. The kernel's **modalias** mechanism lets udev load the right module automatically. When a device appears, its uevent carries a `MODALIAS` value, and udev runs `modprobe` for it. Look at each piece on a real system:

---

## FILE docs/part-01-linux/11-how-a-program-runs-system-calls-libraries-elf-strace-and-ldd.md

The loader then builds an initial **stack**. The stack holds `argc`, `argv`, `envp` and an **auxiliary vector**. That vector carries system values such as the page size, the location of the vDSO, the entry point, and random bytes for ASLR. Last, the loader picks a starting point for the **heap**.

---

You have several ways to reduce this. You can recycle processes by restarting workers periodically, using `maxtasksperchild`. You can preload `jemalloc` or `tcmalloc` with `LD_PRELOAD`. You can tune `MALLOC_ARENA_MAX` and `MALLOC_TRIM_THRESHOLD_`, or call `malloc_trim`. Memory accounting and the OOM killer are covered in chapter 1.17.

---

Two things follow from that order. First, **user-space CUDA libraries travel with the application**, inside a wheel or a container image. They can differ from one application to the next on the same node, and that is what makes several CUDA versions on one host possible. Second, **`libcuda.so.1` and the kernel module belong to the driver**, so they must come from the host. The application's CUDA version must be supported by the host driver. The driver is backwards compatible with older CUDA runtimes. For newer CUDA than the driver supports, a compatibility package exists for data-centre GPUs, so check NVIDIA's compatibility documentation.

---

4. **`strace` Overhead and Diagnosing Hung Processes:** (a) Why can running `strace` on `dd if=/dev/zero of=/dev/null bs=1k count=200000` slow the run down by about 70 times? Which low-overhead kernel tracing tools avoid stopping the process on every syscall? (b) When you attach `strace -f -p PID` to a hung training rank, what does it mean if threads are blocked in `futex(..., FUTEX_WAIT...)`, `epoll_wait`, or `ioctl` on `/dev/nvidia0`?

---

## FILE docs/part-01-linux/12-disks-partitions-and-filesystems.md

The kernel buffers writes, so a filesystem can have unwritten changes in memory. `umount` flushes them. `sync` forces a flush of all filesystems. Use it before cutting power to a machine that cannot be shut down cleanly, although a proper shutdown is better.

---

By default, `df` counts 1 KiB blocks. Use `-k` to say so explicitly, `-m` for 1 MiB blocks, or `-h` to let the tool pick readable units. The POSIX standard defines 512-byte blocks. Set the `POSIXLY_CORRECT` environment variable to get them. The same size options work with `du`.

---

When `fsck` finds a problem in manual mode, it stops and asks how to fix it. Many questions concern the internal structure, such as reconnecting an inode or clearing blocks. A reconnection question means it found a file with no name. The file goes into `lost+found` under a number. You usually have to guess the original name from the contents.

---

A short history explains many of these choices. The original Unix filesystem had one inode table and 512-byte blocks, and it fragmented its free list. It fell to a few percent of disk bandwidth. BSD's **Fast File System** added **cylinder groups**, which place inodes and data together. It also added larger blocks and fragments, and most later designs inherit them. ext2 came next, then ext3 with its journal. ext4 added extents, delayed allocation, large files and volumes, journal checksums and a faster fsck. XFS, from SGI, brought allocation groups, extents and scalability. ZFS and btrfs added pooled storage, copy-on-write, checksums and snapshots.

---

## FILE docs/part-01-linux/13-lvm-raid-and-nvme.md

Follow three rules. Always build filesystems and LVM on the multipath device, never on a component path, and exclude the paths in the LVM filter. Blacklist local disks and virtio disks. Set `no_path_retry` on purpose, choosing between queueing forever and failing fast. NVMe-oF is different. The kernel has **native NVMe multipath**, visible at `/sys/module/nvme_core/parameters/multipath`, so the tool to use there is `nvme list-subsys`, not `multipath -ll`.

---

Bandwidth is limited by the **PCIe link**. A Gen3 x4 link gives about 3.5 GB/s. Gen4 x4 gives about 7 GB/s, and Gen5 x4 gives about 14 GB/s, each per direction. A drive running at x2, or at a lower generation, will be slow. Check the link state with `lspci -vv`, or read `/sys/class/nvme/nvme0/device/current_link_speed` and `max_link_width`.

---

When a disk misbehaves, you need the right tool for the question. The table below lists the main tools, with what each one shows. Start with the cheap ones, and move to the heavier tracers only when they are needed.

---

If you are unsure where to begin, look at `r_await` and `w_await` first, and compare them with what you expect. Use a few rules of thumb, and apply them to your own numbers. For a single HDD, `%util` near 100%, a growing `aqu-sz` and an `await` of tens of milliseconds mean the disk is saturated. For flash, watch `await` and the percentiles from `biolatency`. For arrays, look at the individual members too, since the virtual device can hide a single bad drive.

---

## FILE docs/part-01-linux/14-boot-firmware-grub-kernel-initramfs.md

On a BIOS system with a **GPT** disk, that gap holds the GPT entry array instead. GPT supports `128` partitions and disks larger than `18` exabytes. GRUB therefore needs a small **BIOS boot partition**, with type GUID `21686148-6449-6E6F-744E-656564454649`, to store its core. The firmware reads the disk through BIOS calls with simple **LBA** addressing. That is slow, but a boot loader needs it only briefly.

---

GRUB device names look like `(hd0)`, `(hd0,gpt2)` and `(hd0,msdos1)`. Each name gives the disk number, the partition table type and the partition number, in that order. The numbering can change, so entries use `search` by UUID instead. `linux` loads the kernel image and takes the parameters. `initrd` loads the initial RAM filesystem, and `boot` starts it.

---

GRUB can hand over to another boot loader instead of loading a kernel. You might do this for dual boot, or to reach a vendor recovery partition. `chainloader +1` loads the first sector of a partition. On UEFI, `chainloader /EFI/Microsoft/Boot/bootmgfw.efi` does the job.

---

Next, use a disposable local VM, such as QEMU/KVM, VirtualBox or UTM, or a throwaway GCP VM with serial console access. Every interactive VM command below is marked `untested here`, so treat each one as a step to confirm. Work through these steps in order.

---

## FILE docs/part-01-linux/15-systemd-units-targets-timers-journald.md

Each echo instance reads the connection as standard input and output, so it does not need to know that the data came from a network. That simple gateway suits only simple services. Most network services need more flexibility, so do not expect a complex server to work from a unit like this one. If a service can accept connections by itself, leave the `@` out of its filename and leave `Accept=true` out of the socket unit. The service then takes full control of the socket, and systemd does not listen on the port again until the service finishes.

---

`Persistent=true` stores the last run time on disk, and it runs a missed job at the next start, which covers a machine that was off. `RandomizedDelaySec=` spreads the load across machines. `AccuracySec=` defaults to one minute, which lets systemd combine wake-ups. Set it to `1s` when you need precision. A timer's service cannot overlap itself. If a `Type=oneshot` service is still active at the next trigger, that trigger is skipped, so you rarely need `flock`.

---

`chkconfig`, `update-rc.d`, `rc.local` and `service NAME start` still work through this compatibility layer. Do not expect miracles from it, though. It runs legacy scripts serially and offers poor readiness tracking, so replace them with native units where you can. `run-parts` still appears in cron and in package scripts, and it runs every script in a directory in lexical order.

---

Most failures in this chapter come from a few habits. The twenty items below are the ones that come up most often. Each one gives the symptom and the first thing to check. If you hit one of these, start with the first check listed. Read each item as a question you can ask about your own node.

---

## FILE docs/part-01-linux/16-logging-time-synchronisation-cron-and-batch-jobs.md

This chapter covers system logging end to end: syslog concepts, `rsyslog`, the journal, `logrotate` and central collection. It covers time: the kernel clock, the RTC, time zones, NTP with `chrony` and `timesyncd`, PTP, and the failure modes in clusters. It also covers scheduling: cron, `anacron`, `at`, `batch` and systemd timers, including patterns for fleets. Systemd and `journalctl` mechanics are in chapter 1.15. Users and PAM are in 1.6 and 1.21, and monitoring systems are in Part 9.

---

Each line holds a timestamp, the host, the program with its PID, and the message. Every message also carries a facility, which names the category of the sender, and a severity, which gives its urgency. Together they form the priority.

---

Several options come up again and again. `daily`, `weekly` and `monthly` set the schedule. `size 500M` or `maxsize` rotates by size, and `rotate N` keeps N old copies. `maxage N` limits how old a kept file can be. Two more options matter for daemons. `copytruncate` copies the log and then truncates the original in place. That suits programs that cannot reopen their log, but it may lose lines in the copy window. `postrotate` ... `endscript` runs a command after rotation, and that command typically tells the daemon to reopen its log. The rest are simpler. `compress` and `delaycompress` control gzip, `dateext` swaps the numbers for a date suffix, `create mode user group` sets the new file's permissions and owner, and `su user group` rotates as that user.

---

Read `chronyc tracking` first. Its `System time` line gives the current offset, in the form `System time : 0.000012345 seconds fast of NTP time`. On a LAN, an offset of microseconds to low milliseconds is good. Watch `Last offset`, `RMS offset`, `Frequency`, which shows the drift in ppm, and `Leap status: Normal`. A `Stratum` of 16, or the words "Not synchronised", means no usable source exists.

---

## FILE docs/part-01-linux/17-memory-management-virtual-memory-numa-huge-pages-oom.md

Large-scale services often prefer to be OOM-killed and rescheduled rather than limp along. Make sure the OOM victim is the job, not `sshd` or `kubelet`. Chapter 1.15 covers that in section 10. On small hosts, `zram` and `zswap` offer middle options, because they compress swap in RAM.

---

PSI, or pressure stall information, appeared in Linux 4.20 and later. `some` is the percentage of time at least one task stalled while waiting for memory. `full` is the time when all non-idle tasks stalled. Both come as averages over 10, 60 and 300 seconds. Any sustained non-zero `some` value, and any `full` value, signals saturation more directly than free-memory numbers do. Per-cgroup pressure lives in `memory.pressure`.

---

Grace-based systems, such as GH200 and GB200, expose CPU memory as NUMA nodes. Depending on configuration, GPU memory can appear as NUMA nodes too, and the distances differ a lot. The unified, coherent address space removes the need to copy data, but it does not remove the need to place data well. Always read `numactl -H` and the platform guide.

---

Data loaders with many workers have one more trap. `fork` shares pages copy-on-write, but Python reference counting writes to objects, and that breaks the sharing. Each worker then gradually copies the dataset. Store datasets in NumPy, Arrow, `mmap` or shared memory instead of Python lists, so the pages stay shared.

---

## FILE docs/part-01-linux/18-cpu-scheduling-and-cgroups-v1-and-v2.md

Caches sit between the core and main memory, and they come in levels. **L1** belongs to each core and is split into instruction and data parts. It is about 32 to 64 KiB in size. It answers in about 1 ns. **L2** also belongs to each core, at about 0.5 to 2 MiB. **L3** is shared by a group of cores. It holds tens of MiB and answers in ten-plus ns. Past the caches sits DRAM, which can be local or remote. Remote memory is the NUMA effect from chapter 1.17.

---

Since Linux 2.6.38, **autogroup** groups tasks by session. Its purpose is to stop a `make -j` in one terminal from drowning the interactive shells in other terminals. The side effect is that nice between sessions behaves per group, not per process. You can inspect this in `/proc/PID/autogroup` and the `kernel.sched_autogroup_enabled` setting. On a systemd host, cgroups provide the real weighting between services, through `CPUWeight`.

---

`cpuset.cpus` and `cpuset.mems` restrict the CPUs and NUMA nodes a group may use. `cpuset.cpus.effective` and `cpuset.mems.effective` show what is actually in force, after parent constraints and hotplug. In v1 the files are `cpuset.cpus`, `cpuset.mems`, `cpuset.cpu_exclusive` and `cpuset.memory_migrate`. v2 adds **partitions**. Setting `cpuset.cpus.partition` to `root` or `isolated` makes a group with exclusive CPUs. An isolated partition comes out of the parent's scheduler load balancing. That gives you a runtime alternative to `isolcpus`.

---

Several gotchas catch people out. CPU limit throttling is the first one, covered in section 7. Memory limits count page cache, so a container can look like it leaks memory that is only cache. The kernel reclaims that cache at the limit, but alerts fire first. Use the working set instead, and check `inactive_file` in `memory.stat`. An `OOMKilled` status with exit 137 is a different event from a node-level eviction. Limits can also make `nproc`-sized thread pools oversubscribe.

---

## FILE docs/part-01-linux/19-namespaces-the-kernel-feature-behind-containers.md

Gregg puts it this way: the kernel keeps a pointer, `struct nsproxy`, from each task to its namespaces. That structure is the closest thing the kernel has to a "container". Because the kernel is shared, a container starts in milliseconds. It uses no guest-kernel memory, has no virtualisation overhead on CPU or memory, and calls the GPU driver natively. The price is real, though. All containers contend for the same kernel locks, caches and queues, which is the noisy-neighbour problem. A kernel bug or panic affects every container. Guests cannot load their own kernel modules or run a different kernel. Isolation is also weaker than hardware virtualisation, because the attack surface is the whole system-call interface.

---

Kubernetes support for user namespaces, `hostUsers: false`, is newer and sits behind a feature gate, so check its status for your version. User namespaces also enlarge the kernel's attack surface. Some distributions restrict unprivileged creation, through `kernel.unprivileged_userns_clone` or, on recent Ubuntu releases, an AppArmor restriction. Check your distribution's policy.

---

To give a container a GPU, a runtime has to do three things. First, it makes the device nodes exist in the container's mount namespace, by bind mount or by `mknod`. Second, it allows those devices in the devices cgroup, which chapter 1.18 covers. Third, it mounts the driver's user-space libraries and binaries, such as `nvidia-smi`, from the host. The CUDA toolkit libraries can live in the image, but the driver library cannot.

---

1. **Inspect**: `ls -l /proc/$$/ns`, `lsns`. Start `docker run -d --name nsdemo alpine sleep 600` (if Docker is installed), get its PID with `docker inspect -f '{{.State.Pid}}' nsdemo`, then run `sudo ls -l /proc/<PID>/ns` and compare inode numbers with the host shell. Which are the same, and which differ? With default settings, `user` should be the same, while `mnt`, `pid`, `net`, `ipc`, `uts` and `cgroup` differ.
2. **UTS**: `sudo unshare --uts bash -c 'hostname lab-box; hostname'`, then run `hostname` in your original shell.
3. **PID**: `sudo unshare --pid --fork --mount-proc bash`. Run `ps aux` and `echo $$`. From another terminal, find that shell's host PID with `pgrep -f 'unshare --pid'`, then `pstree -p`, and note the two PIDs. Try `kill -9 1` inside, where nothing happens, then `kill -9 <host PID>` from outside.
4. **PID 1 signals**: In the PID namespace, run `sh -c 'sleep 1000'` as PID 1 with `sudo unshare --pid --fork --mount-proc sh -c 'sleep 1000'`. Try `kill -TERM` from outside, using the host PID, and then from a second process inside. Next, compare `exec sleep 1000` with a script that uses `trap 'echo got TERM; exit' TERM`.
5. **Mount**: Run `sudo unshare --mount bash`, then `mkdir /tmp/m && mount -t tmpfs tmpfs /tmp/m && touch /tmp/m/x && findmnt /tmp/m`. Open another host shell and look: the mount is not visible. Repeat with `mount --make-rshared /` first, and with a bind mount, to see propagation. Use `findmnt -o TARGET,PROPAGATION`.
6. **Overlay**: Run the OverlayFS commands from section 4. Inspect `upper/` after you write and delete, and examine a whiteout with `ls -l`.
7. **Network**: Follow the `ip netns` and veth recipe in section 5, and ping in both directions. Then add `iptables -t nat -A POSTROUTING -s 10.9.0.0/24 -j MASQUERADE` and `sysctl -w net.ipv4.ip_forward=1` to give the namespace Internet access. Delete the namespace afterwards.
8. **User**: Run `unshare --user --map-root-user bash`, then view `id` and `/proc/self/uid_map`. Try to read `/etc/shadow`, and try `mount -t tmpfs`, which works only when combined with `--mount`.
9. **Enter an existing container's namespaces**: `sudo nsenter -t <PID> -n -p -m ip addr`, then `sudo nsenter -t <PID> -n ss -tlnp`.
10. **IPC**: Run `ipcmk -M 1024` on the host, then `ipcs -m`. Next, run `sudo unshare --ipc ipcs -m`. The segment is invisible there. Compare this with `docker run --ipc=host`.
11. **Clean up**: Run `docker rm -f nsdemo`, and remove the `/tmp/m` directories, the overlay directories and the namespaces.

---

## FILE docs/part-01-linux/20-lab-build-a-container-by-hand-with-unshare-chroot-cgroups-and-overlayf.md

After the `chroot`, you see a different filesystem. Everything else still belongs to the host, though: the hostname, the network and the processes. `ps` fails because `/proc` is absent, and if you mount `/proc`, you see the whole host. So write down everything that is still shared. Remember, too, that a root process can escape a `chroot`. Treat `chroot` as a convenience, not as isolation.

---

So far the container can see very little, but it can still use up the whole machine. Picture a noisy neighbour that runs a fork bomb on a shared GPU node. A cgroup puts a ceiling on that use. The order matters. Create the group first, then move the starting shell into it. Every child then inherits the membership.

---

Now comes the payoff. Use the output above to line the real container up against yours. Make a table with one row for each property. The rows are namespaces, cgroup limits, the rootfs mount, the veth and bridge setup, capabilities from `grep Cap /proc/$P/status`, and seccomp from `grep Seccomp /proc/$P/status`. In each row, record what your hand-built container has and what Docker adds. The typical gaps you will find are masked `/proc` paths, a read-only `/sys`, the default seccomp profile, the capability drop list, a user-defined bridge with DNS, and port publishing rules.

---

1. Remove the `mount --make-rprivate /` line from `enter.sh`, mount something inside, and look for a leak on the host with `findmnt -o TARGET,PROPAGATION`.
2. Make PID 1 a shell script without `exec`, then send `SIGTERM` from the host (host PID) and from inside.
3. Skip mounting `/proc` and run `ps` and `free`. Then mount it and compare `free` with the cgroup's `memory.max`.
4. Write 200 MB into the container's `/` and see where the bytes land with `du -sh /lab/upper`.
5. Set `memory.max` very low and watch `memory.events` count `oom_kill`.
6. Create a file in `/lab/merged` while the container runs, and see when the container sees it.
7. Delete the cgroup directory while processes remain, and note which error you get.

---

## FILE docs/part-01-linux/21-linux-security-capabilities-selinux-apparmor-seccomp-pam-ssh-hardening.md

Containers start with a reduced bounding set. Docker's default drops `SYS_ADMIN`, `NET_ADMIN`, `SYS_MODULE`, `SYS_PTRACE`, `SYS_TIME` and more. Kubernetes `securityContext.capabilities.drop: ["ALL"]` drops everything first, and then `add` grants only what is needed. `--privileged` (Docker) or `privileged: true` (Kubernetes) is a different story. It gives all capabilities, all devices, and disables seccomp and LSM confinement. That makes the container effectively root on the host, so it must never be a casual fix.

---

When something is denied, follow a fixed order. (1) Reproduce the problem. (2) Read the AVC with `ausearch` or `sealert`. (3) Check whether a boolean, a file label (`semanage fcontext` with `restorecon`), or a port label fixes it. (4) Only then consider a custom module with `audit2allow`, reviewed for over-breadth. Do not run `setenforce 0` or disable SELinux as the fix.

---

Logs answer the question of what happened on a node, but only if you set them up in advance. Start with the audit subsystem. **auditd** records security-relevant events from the kernel audit subsystem, including syscalls, file watches, logins, privilege use and SELinux denials. Its rules live in `/etc/audit/rules.d/*.rules`. For example, `-w /etc/passwd -p wa -k identity` watches the password file, and `-w /etc/sudoers -p wa -k scope` watches the sudo rules.

---

With UEFI Secure Boot, the firmware runs only signed boot loaders. The signed kernel then enforces **lockdown**, and it loads only kernel modules signed by a key in the kernel's trusted keyrings. The NVIDIA driver, open or proprietary, is out-of-tree. So on a Secure Boot node you must **sign it** with a key enrolled in the firmware `db` or the Machine Owner Key (MOK) list. Generate a key pair first. Then run `mokutil --import` on the public key, which is confirmed at the next boot on the console. Sign `nvidia*.ko` with the kernel's `sign-file` tool. DKMS can do this automatically once you configure the key paths. Finally, verify with `modinfo nvidia | grep sig`.

---

## FILE docs/part-01-linux/22-kernel-modules-dkms-and-sysctl-tuning-for-gpu-nodes.md

Before you tackle a driver failure, you need some background. You should know the boot sequence and initramfs (1.14), systemd (1.15), memory and NUMA (1.17), `/proc` and `/sys` (1.10), the ELF/dynamic-linking basics (1.11), and the security layer (1.21, especially Secure Boot). Each of these explains one part of what happens when a module loads.

---

A node with Secure Boot turned on can refuse a driver that loads fine on another node. To see why, you need to know how the firmware and the kernel decide what is trusted. With **Secure Boot**, the firmware starts only signed boot loaders. The signed kernel then restricts what can be loaded. This restriction is called kernel **lockdown**, and it can require **signed modules** (`CONFIG_MODULE_SIG_FORCE` or lockdown "integrity" mode). The kernel's trusted keyrings come from three places: the built-in keys, the firmware `db` (via `shim`), and the **Machine Owner Key (MOK)** list, which you manage with `mokutil`.

---

Order matters. Some parameters exist only after a module is loaded. The `net.netfilter.*` and `net.bridge.*` keys need `br_netfilter`. A sysctl file applied before that module loads fails silently. You can fix this by loading the module earlier through `modules-load.d`, or by applying the settings with a service that runs after the module.

---

1. `uname -r`; `ls /lib/modules/$(uname -r)/kernel/drivers | head`; `lsmod | wc -l`.
2. Pick a harmless module (e.g. `dummy` or `loop`): `modinfo dummy`; `sudo modprobe dummy numdummies=2`; `ip -br link | grep dummy`; `lsmod | grep dummy`; `sudo modprobe -r dummy`.
3. Persist with `/etc/modules-load.d/dummy.conf` and `/etc/modprobe.d/dummy.conf` (`options dummy numdummies=2`); reboot; verify; remove the files.
4. Blacklist a module (`blacklist floppy` or another unused one); see `modprobe -c | grep floppy`; rebuild initramfs (`sudo update-initramfs -u`); compare `lsinitramfs` before/after.
5. Write a minimal "hello world" module (`hello.c`, `Makefile` with `obj-m += hello.o`, `make -C /lib/modules/$(uname -r)/build M=$PWD modules`; needs `build-essential` and `linux-headers-$(uname -r)`); `sudo insmod hello.ko`; `dmesg | tail`; `modinfo hello.ko`; `sudo rmmod hello`. Observe `vermagic`. Then try loading it on a different kernel (or inspect with `modinfo -F vermagic`) and note the refusal.
6. Register the same module under DKMS: create `/usr/src/hello-1.0/` with source, `Makefile`, `dkms.conf` (`PACKAGE_NAME`, `PACKAGE_VERSION`, `BUILT_MODULE_NAME[0]`, `DEST_MODULE_LOCATION[0]="/updates/dkms"`, `AUTOINSTALL="yes"`); `sudo dkms add -m hello -v 1.0 && sudo dkms build -m hello -v 1.0 && sudo dkms install -m hello -v 1.0`; install a second kernel (`apt install linux-image-<other>`) and watch DKMS build for it; `dkms status`.

---

## FILE docs/part-01-linux/23-performance-methodology-use-workload-characterisation-drill-down.md

Last, you learn to tell load problems from architecture problems. Scalability curves help here: linear, contention, coherence, knee and ceiling. You fit Amdahl and USL to them. You use Little's law and the 60% rule for queueing, and percentiles, distributions and averages over intervals for statistics. Finally, you quantify the gain from a fix before you make it, decide when to stop, and write findings that others can verify.

---

Most performance work aims at one of three goals. You can reduce latency, which shows up as user experience, step time or time to first token. You can raise throughput. You can also reduce cost by removing waste. On GPU clusters, idle accelerators dominate cost, so cost reduction usually means raising goodput. Goodput is the useful work you get per GPU-hour.

---

A resource with low utilisation, no saturation and no errors is valuable evidence. It removes that resource from the search. Document these negative findings as carefully as the positive ones, so other teams do not re-check the same dead end.

---

Experiments need repetition. Run enough repeats, report the median and the spread, and control confounders such as clocks, thermal state, cache state and neighbours. Compare like with like. A 3% difference with 5% run-to-run variation is noise. Write the setup down with the result, so someone else can repeat it.

---

## FILE docs/part-01-linux/24-observability-tools-perf-ftrace-bpf-and-bpftrace.md

Picture the system as a stack. At the top are applications, then system libraries, then the system-call interface. Below those sit the kernel subsystems: VFS and filesystems, the scheduler, the memory manager, TCP/IP and the block layer. Device drivers and devices sit at the bottom. Most tools focus on one resource. A few are **multi-tools** that reach every layer, and those are `perf`, Ftrace, BCC and bpftrace.

---

Processors expose programmable registers that count low-level events at cycle granularity. The events include cycles, instructions retired, branch misses, L1, L2 and LLC references and misses, TLB misses, stalled cycles, and uncore memory bandwidth. Only PMCs can show instruction efficiency (IPC), cache hit ratios, memory-bus utilisation and stall cycles. The details follow.

---

`trace-cmd` is more concise than hand-editing tracefs, and it is safer because it restores the state when it finishes. It can record to a binary `trace.dat` file, stream over the network, and work well with KernelShark. Compared with `perf`, `trace-cmd` has better function and function_graph support, very low output overhead, and network capture. `perf` has PMCs, timed sampling, and complete kprobe, uprobe and USDT integration.

---

Unlike older tracers, BPF is programmable. A program can filter events and store state in **maps**, such as hash tables, arrays, per-CPU maps and histograms. It can compute latency too. The program aggregates **in the kernel** and sends only summaries to user space. That makes per-event latency histograms and stack counting affordable on production systems. Copying every event to user space would drown those systems. BPF also powers networking (XDP, tc, Cilium), security (Falco, Tetragon, seccomp-bpf) and observability products. This chapter covers the tracing front ends.

---

## FILE docs/part-01-linux/25-benchmarking-correctly.md

Then compare the "easy" pattern, which is large sequential I/O with per-process files, with the "hard" pattern, which is small unaligned I/O to a shared file. Metadata-heavy workloads, with millions of small files, are the usual surprise. For client cache, use `IOR -C` or drop caches between the write and read phases. Check that a read-after-write across different nodes is not served from the writer's cache.

---

Automate the whole sequence. Store results per serial number. Define pass and fail thresholds from the vendor spec and the fleet median, and track outliers over time. Re-run a short version after maintenance and as periodic health checks. Many sites run lightweight checks as Slurm prolog or epilog scripts, or as node-health scripts.

---

The steps after that need a disposable Linux VM with an attached scratch disk. Steps 7 to 13 also need a GPU VM or a pair of nodes. Every interactive VM command below is `untested here`, so run them only on machines you can afford to rebuild.

---

1. The first exercise is the Bonnie++ case study. Start by defining casual benchmarking, blind faith, benchmark specials, and the benchmark paradox. The function `compute_benchmark_paradox_win_prob(0.5, 3)` in `code/part01/benchmarking_correctly.py` covers the paradox. Then walk through how Gregg used `iostat`, `bpftrace` on `tracepoint:block:*` and `kprobe:vfs_write`, and `cachestat` to show that Bonnie++'s `739 KB/s` "sequential per-character disk output" test never touched the disk.
2. The second exercise covers the six-question checklist and quick bandwidth arithmetic. State the six checklist questions, which live in `SIX_CHECKLIST_QUESTIONS`. Then evaluate `check_iops_link_sanity()` for a claim of `50,000` NFS `8 KiB` IOPS over a `1 GbE` link. Finally, decide whether each of three claims is physically possible: `"350 MB/s"` over `1 GbE`, `"55 GB/s"` unidirectional over `400 Gb/s` Ethernet, and `"40 GB/s"` unidirectional over PCIe Gen4 x16.
3. The third exercise covers storage. Explain why `fio --rw=read --bs=1M --size=2G --numjobs=8` on a `1 TiB` RAM host reported `40 GB/s`. Then write the corrected `fio` flags, `--direct=1`, `--size=64G`, `--iodepth=32`, `--ramp_time=10` and `--lat_percentiles=1`, to measure true NVMe sequential and random 4 KiB performance. Finally, explain how `IOR -C` defeats client page-cache hits on multi-node parallel filesystems. Check your answer against Worked Example A.
4. The fourth exercise covers GPU traps. Explain why Canary Node C in Worked Example C appeared `6%` slower after a driver upgrade, at `1,410 MHz` against `1,740 MHz`. Then name the four controls that you need for a valid GPU micro-benchmark: `torch.cuda.synchronize()` or CUDA events, warm-up discard, `nvidia-smi -lgc` clock locking, and explicit dtype/sparsity reporting.
5. The fifth exercise covers `nccl-tests`. (a) Use `compute_nccl_allreduce_busbw()` to compute `algbw` in `GB/s`, the scaling factor `2(n - 1)/n`, and `busbw` in `GB/s`, for the case where `all_reduce_perf` completes a `1 GB` (`1,000,000,000`-byte) AllReduce in `10 ms` (`0.010 s`) across `n = 8` GPUs. Your answer should match the formula given earlier in this chapter. (b) In Worked Example B, explain why the 2-node run plateaued at `22 GB/s` instead of `46 GB/s`. Show how `NCCL_DEBUG=INFO` and `ibstat`/`perfquery` pinpointed both the TCP fallback and the degraded cable.
6. The sixth exercise covers inference load and regression gating. (a) Contrast closed-loop fixed-concurrency benchmarking with open-loop Poisson-arrival benchmarking, and explain *coordinated omission*. Then explain why Worked Example D's capacity dropped from `4,200` to `1,350` tokens/s/GPU under realistic `3,000`-token prompt distributions. (b) Use `evaluate_median_mad_regression_gate()` to evaluate the candidate runs `[98.8, 99.2, 100.1, 99.0, 99.4]` and `[92.0, 91.5, 93.0, 92.2, 91.8]` against the baseline `[100.0, 101.0, 99.0, 100.5, 99.5]`. Your output should show which candidate passes the gate and which one fails.

---

## FILE docs/part-01-linux/26-kvm-qemu-and-libvirt-basics.md

There are several ways to give a guest access to a device. The table compares them. Read it from left to right: the faster methods usually need more from the driver or the hardware, and passthrough ties a device to a single VM.

---

Pay attention to the comments. `destroy` powers a VM off without deleting it. The `--config` changes to `setvcpus` and `setmem` are saved to the definition, so they take effect after a restart. The `undefine` command with `--remove-all-storage` deletes the VM and its disks, so use it carefully.

---

Choose the mode by asking who needs to reach the guest. You want the NAT network for dev and test work, because guests are not reachable from outside without forwarding. A Linux bridge puts the guest on the physical network, so the host's NIC carries no IP address of its own. You can see that choice in the table.

---

1. Compare emulation with hardware-assisted virtualisation, and Config A with Config B. (a) Contrast software emulation (QEMU TCG) with hardware-assisted virtualisation (KVM plus VT-x or AMD-V). Then contrast Gregg's Config A (native hypervisor plus dom0) with Config B (the kernel-module hypervisor KVM, where each VM is a `qemu-system-x86_64` process and each vCPU is a `CPU n/KVM` thread). (b) Use `classify_kvm_exit_reason()` in `code/part01/kvm_qemu_libvirt.py` to classify `HLT`, `MSR_WRITE` and `IO_INSTRUCTION`. For each one, decide whether it represents idle sleep or active overhead, and whether the host kernel or user-space QEMU handles it.
2. Work through nested paging, 2D page walks and huge pages. Explain the three address spaces in a VM (Guest Virtual, Guest Physical and Host Physical), and explain why hardware nested paging (EPT or NPT) replaced shadow page tables. Then use `compute_2d_page_walk_max_reads()` to calculate the worst-case number of memory reads on a TLB miss. Compare 4-level guest and 4-level host page tables, which give 24 reads, with the case where both guest and host use 1 GiB huge pages, which gives 8 reads.
3. Compare the I/O virtualisation spectrum and the IOMMU. Compare full device emulation, virtio (virtqueues), vhost-net or vhost-user, SR-IOV (PFs and VFs) and VFIO PCIe passthrough, looking at performance and sharing flexibility. Then explain why passthrough is unsafe without an IOMMU (VT-d or AMD-Vi).
4. Work through VM storage and networking. (a) Explain why virtio-blk and virtio-scsi disks should use `cache='none'` (`O_DIRECT`, set as `cache=none`) and dedicated iothreads. Then explain how a thin qcow2 copy-on-write backing file works, using `qemu-img create -f qcow2 -F qcow2 -b base.img vm1.qcow2`. (b) Contrast QEMU user-mode networking (SLIRP), the libvirt `default` NAT network (`virbr0` `192.168.122.0/24`), a host L2 bridge (`br0`) and SR-IOV VFs.
5. Observe a VM from the host and from the guest. (a) On a KVM host, how do you read `%guest`, `%system` and `%usr` in `pidstat -tp <qemu-pid> 1`? Why does `perf kvm stat report` show high total time in `HLT` exits on an idle guest? (b) Inside the guest, what does sustained `%steal` (`st` in `vmstat` or `mpstat`) tell you? How would you tell whether virtual disk latency outliers come from guest I/O patterns or from host noisy neighbours?
6. Check GPU passthrough and guest topology. (a) Evaluate `validate_iommu_group_passthrough()` when a GPU (`0000:3b:00.0`) shares an IOMMU group with its audio function (`0000:3b:00.1`), or with a host-critical device. (b) Audit an untuned VM that uses `qemu64`, `i440fx` and `cache='writeback'`, and has no huge pages, locked memory or pinning, using `audit_gpu_vm_domain_config()`. Then explain why OVMF `X-PciMmio64Mb=262144` and an accurate guest PCIe and NUMA topology (`nvidia-smi topo -m`) are critical for multi-GPU NCCL and GPUDirect RDMA in VMs.

---

## FILE docs/part-01-linux/27-cloud-computing-and-virtualization-internals-for-linux-engineers.md

Cloud computing changes the performance problem in three ways. **Capacity is elastic but not unlimited**, because GPU quota and availability are scarce. **Resources are shared** through multitenancy, noisy neighbours and resource controls. **Observability is partial**, so you see a slice of the machine, not the whole machine.

---

Enterprise systems historically scaled **vertically**, meaning larger machines. That path ends at physical size, cache coherency, power and cooling. Cloud systems scale **horizontally** instead. They run many small instances in parallel at each layer, such as load balancers, web servers, application servers and databases. You add them one at a time, or as vertical partitions called cells or "pods" of a full stack. Databases that need a single primary are split into **shards**, or replaced by distributed or cloud-native databases. Fine-grained instance sizes let you match capacity to load, rather than buying for the peak.

---

The trap is easy to fall into. A container tested on an idle host appears to run at 100% CPU. Later, when neighbours move in, it drops to its 10% minimum. Users then see a ten-fold slowdown. That slowdown is the system working as designed, but it feels like a bait and switch. The fixes are bandwidth caps, which bound the performance range to something like 10% to 20%. You can also notify tenants when they are bursting, and monitor that bursting. Bandwidth is expressed as a number of CPUs, so 2.5 means two and a half CPUs. That number maps to quota and period in microseconds.

---

When you bring up a cloud Slurm cluster by hand, automate the first infrastructure provisioning with Terraform. Install the software with Ansible or custom golden images, or with cluster managers such as BCM. Test the automation on cheap instances first.

---

## FILE docs/part-01-linux/28-putting-it-together-tuning-a-linux-node-for-gpu-and-hpc-work.md

This chapter gives you a layered node tuning playbook. It covers BIOS, firmware, boot parameters, the kernel, OS services, memory, CPU and IRQs, storage, network, the GPU driver and runtime, and containers and schedulers. It also gives you a verification suite that runs in minutes, the configuration-as-code pattern that keeps a fleet consistent, and a retold performance case study. The case study shows how the methodology of chapters 1.23 to 1.25 resolves a real mystery. The chapter also has a lab in which you build your own node audit.

---

System tuning is not a one-time job. Workloads change, a new model arrives, and the best CPU affinity or batch size from last quarter may not be the best one now. Monitor the key metrics on a regular schedule. Adjust CPU affinities, batch sizes and prefetch settings as the workload evolves. Small gains add up into a large improvement over time.

---

The NVML path is the most direct answer. If the driver exposes the NUMA node, the helper uses it. If not, it reads the GPU's CPU affinity mask and maps those CPUs to NUMA nodes, and the node that holds most of them wins. The sysfs file is the next fallback. The `numactl --show` output is the final resort.

---

PyTorch allocates GPU memory only as needed. Its caching allocator keeps freed blocks for reuse instead of returning them to the OS. Watch the usage with `nvidia-smi` or the NVML APIs during training and inference. When you get close to the limit, reduce the batch size, use activation checkpointing for training, or reduce precision.

---

## FILE docs/part-01-linux/29-remote-administration-reference-ssh-server-and-client-options-host-bas.md

The directory and the file must belong to `foo`, and nobody else may be able to write to them. Otherwise `sshd` ignores them. This check is controlled by `StrictModes`. A public key sent to you in the multi-line **RFC 4716** format needs conversion. Some Windows tools produce that format. Convert the key to the single-line OpenSSH format before you use it: `ssh-keygen -i -f rfc-key.pub >> ~foo/.ssh/authorized_keys`. Check the exact flags in `man ssh-keygen`, because the direction of conversion is easy to get wrong.

---

The system-wide client file is `/etc/ssh/ssh_config`. Your own settings go in **`~/.ssh/config`**, and those take precedence. The `~/.ssh` directory also holds your keys. It contains `authorized_keys`, which lists the public keys allowed to log in as you. It also contains `known_hosts`, which records the host keys of machines you have connected to.

---

A wrong line in the server configuration can lock you out, so edit it with care. The server is configured in **`/etc/ssh/sshd_config`**, and current distributions also read drop-ins in `sshd_config.d/`. After you edit the file, validate it with `sshd -t`, then reload it with `systemctl reload sshd`. A reload does not affect existing sessions. That helps, because a mistake need not lock you out of the session you are already using. Still, keep a second session open.

---

This key works only from the management subnet, and it can run only one command. A monitoring system or a web-server front end gets exactly that narrow capability, and nothing more. A "queue status" web page on a separate server can call the cluster safely the same way.

---

## FILE docs/part-01-linux/30-network-file-sharing-and-remote-graphical-access-rsync-in-depth-samba.md

By default, `rsync` ignores what already exists at the destination. Copy `d`, which contains `a` and `b`, to a machine that already has `d/c`, and the destination ends up with `d/a`, `d/b` and `d/c`. To make an **exact replica**, tell `rsync` to delete anything the source does not have:

---

Centralized storage made sense for two traditional reasons. One user could log in to any machine on the network and find the same home directory. It was also cheaper to concentrate storage on a few servers than to buy and maintain a large disk for every machine. Those advantages are overshadowed by one disadvantage that has stayed the same for decades. Network storage performance is often poor compared with local storage.

---

Network file sharing can feel incomplete, and that is because it is. NFS has a low base security level, and raising it is costly. CIFS is better, since modern software builds in encryption. Its performance limits are hard to remove, though. A client can also behave badly when it temporarily cannot reach its storage. Its processes hang in uninterruptible sleep, a state chapter 1.1 explains.

---

Desktop components also rely on D-Bus (How Linux Works, section 14.5), an interprocess communication bus. It has a system instance, used by `systemd`, `NetworkManager` and `Upstart`, which you monitor with `dbus-monitor --system`. It also has a per-user session instance, monitored with `dbus-monitor --session`. Printing uses CUPS, which stands for Common UNIX Printing System. Its commands include `lp`, `lpr`, `lpstat`, `cancel` and `cupstestppd`. It converts PostScript and PDF jobs through RIP filters, and it sends them to IPP or LPD network printers. How Linux Works, section 14.6, covers CUPS in more depth.

---

## FILE docs/part-14-training-finetuning/01-ml-and-deep-learning-fundamentals-for-infrastructure-engineers.md

Second, consider the compute wall. Every dense linear layer executes one forward matrix multiplication and two backward matrix multiplications during backpropagation. A single training step on a large language model therefore requires quintillions of floating-point operations. Running that single batch update on one GPU would take more than an hour. Across a full multi-hundred-billion-token pretraining corpus, total required compute reaches hundreds of zettaFLOPs, making multi-node distributed execution mandatory.

---

Summing the 2PD forward pass and the 4PD backward pass yields the fundamental 6PD training FLOPs law for dense Transformers. When memory limits force engineers to enable full activation checkpointing, intermediate activations are discarded during the forward pass. Those activations are then recomputed on the fly via an extra 2PD forward pass during backpropagation. **Standard dense Transformer training costs 6PD FLOPs per token, and enabling full activation checkpointing raises that cost by one-third to 8PD FLOPs.**

---

The learning rate is the single most sensitive hyperparameter in deep learning. At step zero, model weights are randomly initialized and AdamW variance estimates are completely uncalibrated. Applying a large peak learning rate on step one causes massive parameter jumps and immediate gradient divergence. Conversely, keeping the learning rate high at the end of training causes the optimizer to bounce around the walls of the loss valley.

---

To bridge the gap between theoretical hardware peak and real-world cluster throughput, platform engineers measure Model FLOPs Utilization. MFU is the ratio of useful 6PD mathematical operations achieved per second per GPU to the GPU's datasheet dense Tensor Core peak. Notice that MFU deliberately uses the 6PD baseline in the numerator rather than 8PD. Any extra compute spent on activation recomputation is therefore penalized as overhead rather than rewarded as useful throughput. In well-tuned multi-node LLM training runs, MFU typically lands between 35 percent and 55 percent. **Sizing a training cluster from datasheet peak TFLOPS without multiplying by a realistic MFU between 0.35 and 0.55 will miss your deadline by more than double.**

---

## FILE docs/part-14-training-finetuning/02-transformers-and-llm-architecture.md

Similarly, moving from a dense model to a sparse Mixture-of-Experts architecture like DeepSeek-V3 or Mixtral 8x7B splits memory and compute scaling in two. Total HBM capacity still scales with the total parameter count across all experts. By contrast, per-token compute FLOPs scale only with the active parameters routed per token. At the same time, network traffic shifts from predictable data-parallel AllReduce rings to latency-sensitive AllToAll expert dispatch across nodes.

---

Organizations that scale model parameters without balancing training token volume or inference economics waste millions of dollars in cluster compute. First-generation foundation models scaled parameters aggressively while starving the models of training tokens. That imbalance produced bloated checkpoints that were both under-trained and expensive to serve. Modern frontier engineering replaces brute-force dense scaling with sparse Mixture-of-Experts routing, Chinchilla-informed over-training, and targeted post-training alignment.

---

In a dense Transformer, every token activates 100 percent of the model's parameters. In a sparse Mixture-of-Experts Transformer, each dense SwiGLU MLP block is replaced by a pool of parallel expert MLPs. A lightweight router then dispatches each token to only the top-k experts. Because only a small fraction of experts run per token, per-token compute FLOPs drop by 3.6x to 18x while total capacity scales to hundreds of billions of parameters. **When provisioning an MoE cluster, size HBM capacity for total parameters, size FLOPs for active parameters, and engineer your network for AllToAll dispatch.**

---

Pre-training consumes 98 percent of total compute, yet produces an untamed document-completion model that answers a question with more questions. Post-training consumes the remaining 2 percent of compute across Supervised Fine-Tuning and Preference Fine-Tuning. Preference Fine-Tuning uses either Reinforcement Learning from Human Feedback with PPO or reward-model-free Direct Preference Optimization to align the assistant.

---

## FILE docs/part-14-training-finetuning/03-training-memory-and-compute-anatomy.md

An infrastructure engineer often receives a request to train a large language model on a single GPU node. Five minutes after the job starts, the training script crashes with an out-of-memory error. Model parameter counts have grown exponentially over the last five years. Single-GPU high-bandwidth memory and compute throughput have grown only linearly. **Distributed training exists because modern models exceed both the memory capacity and the compute throughput of any single accelerator.**

---

Why can the GPU not discard intermediate layer outputs as soon as the forward pass moves to the next layer? During the backward pass, the chain rule requires those exact forward-pass tensors to compute weight gradients. Without them, autograd cannot calculate how much each weight contributed to the loss.

---

To compute the gradient for the second layer during `loss.backward()`, autograd must read the activation output computed during the forward pass. To compute the gradient for the first layer, autograd needs the layer input and the derivative of the activation function. Whether PyTorch saves the post-activation output or the pre-activation input depends on the mathematical form of that derivative:

---

Monitoring GPU utilization with `nvidia-smi` often misleads infrastructure teams into thinking a slow job is running efficiently. A GPU can report full utilization while spending most of its time stalled on memory-bandwidth-bound element-wise kernels or waiting on network collectives. To measure true hardware efficiency, you must count the useful floating-point operations completed per token and compute Model FLOPs Utilization.

---

## FILE docs/part-14-training-finetuning/04-data-parallelism-and-ddp.md

Data parallelism addresses the compute wall when the model state and micro-batch activations fit inside each GPU's memory. That fit can be achieved natively for smaller models, through mixed precision and activation checkpointing, or as the outer loop around Tensor and Pipeline Parallelism shards. The DDP contract executes four lockstep stages on every training iteration:

---

Before DDP existed, PyTorch engineers used `torch.nn.DataParallel` to utilize multiple GPUs on a single server. Even on a four-GPU or eight-GPU machine, legacy DataParallel is a severe performance anti-pattern. It runs inside a single Python process with multi-threading and turns GPU 0 into a centralized communication and memory bottleneck.

---

When you wrap a model with `DDP(model, device_ids=[local_rank])`, DDP calls `_sync_module_states()` during construction. That function broadcasts both parameters and buffers from rank 0 to all peer ranks. It guarantees identical starting weights even if you forgot to seed random number generators identically.

---

In standard DDP, if a single worker crashes or a spot node is preempted, the entire collective aborts. Passing `--max_restarts=3`, `--rdzv_id=<job_id>`, `--rdzv_backend=c10d`, and `--rdzv_endpoint=$MASTER_ADDR:29400` activates Torch Distributed Elastic:
- Fault-tolerant mode uses a fixed node count such as two nodes with up to three restarts. If a worker crashes, the elastic agent terminates surviving workers and re-runs rendezvous across the two nodes. It then respawns workers and resumes from the latest atomic checkpoint.
- Elastic mode uses a dynamic range such as `--nnodes=2:4`. Nodes can join or leave mid-run, dynamically changing the world size and the global batch size at resize boundaries.

---

## FILE docs/part-14-training-finetuning/05-fsdp-and-parameter-sharding.md

If you wrap a 70B model as one monolithic FSDP unit on sixteen GPUs, steady-state memory sits at 52.5 GB per GPU. However, at the start of `model.forward()`, FSDP executes a single AllGather across the entire model at once. That operation materializes all 140 GB of unsharded weights simultaneously on every GPU, spiking peak state memory to 192.5 GB.

---

Scaling flat FSDP full sharding from a single eight-GPU node to a multi-node cluster often causes per-GPU throughput to plummet. Inside a node, NVLink 4 delivers 900 GB/s of bidirectional bandwidth, and NVLink 5 delivers 1.8 TB/s. Across nodes, InfiniBand NICs provide only 25 to 50 GB/s per GPU. Forcing every layer's AllGather and ReduceScatter across the inter-node fabric stalls GPU compute streams on network transfers.

---

Modern GPUs have dedicated DMA copy and communication engines separate from Tensor Core compute streams. Forward prefetching launches the AllGather for upcoming layers on a secondary communication stream while the current layer computes on the default stream. During backpropagation, `BackwardPrefetch.BACKWARD_PRE` prefetches the previous layer's parameters before the current layer's backward compute finishes, allowing AllGather and ReduceScatter to overlap with matmuls.

---

On Grace Hopper and Grace Blackwell superchips, however, SuperOffload eliminates this PCIe bottleneck using four hardware-aware mechanisms. First, coherent NVLink-C2C links connect the Grace ARM CPU and Blackwell GPU at 900 GB/s. Second, Speculation-Then-Validation allows the Grace CPU to run speculative optimizer updates concurrently with GPU backpropagation before validating for NaN or Inf values. Third, heterogeneous optimizer partitioning splits compute-heavy tensor casts onto the GPU while keeping momentum and variance updates on the CPU. Fourth, `GraceAdam` vectorizes the Adam update across ARM Scalable Vector Extension registers.

---

## FILE docs/part-14-training-finetuning/06-deepspeed-and-zero.md

Before PyTorch introduced native FSDP in Chapter 14.5, Microsoft Research introduced the Zero Redundancy Optimizer and the DeepSpeed engine to break the single-GPU memory wall. When teams launch distributed training with standard DistributedDataParallel, every GPU stores a full redundant copy of the model weights, gradients, and AdamW optimizer states. That duplication causes immediate out-of-memory crashes on 80 GB GPUs as soon as models pass a few billion parameters. Platform engineers feel this pain when expensive multi-node jobs fail at initialization or crawl at single-digit GPU utilization.

---

Across production literature and our reference sources, engineers use three standard byte-accounting conventions for model state. The first convention is the 16-byte mixed-precision rule. It counts 2 bytes for FP16 or BF16 weights, 2 bytes for gradients, and 12 bytes for FP32 master weights, momentum, and variance. The second convention is the 12-byte mixed-precision rule. It omits a separate FP32 master weight copy and counts 8 bytes for FP32 momentum and variance. The third convention is the 16-byte pure FP32 rule. It counts 4 bytes for FP32 weights, 4 bytes for FP32 gradients, and 8 bytes for FP32 momentum and variance.

---

For a 10B model trained in pure FP32 on eight GPUs, both Stage 0 and Stage 1 overflow an 80 GB card. Moving to ZeRO Stage 2 drops per-GPU state to 55 GB, leaving comfortable headroom for activations without Stage 3 communication overhead. For a 70B model on eight GPUs, even ZeRO Stage 3 exceeds a single 80 GB card. That footprint forces either horizontal scaling to sixteen GPUs or memory offloading.

---

Enabling `zero_quantized_weights` or `zero_quantized_gradients` alongside BF16 crashes on the very first AllGather with a `Half` versus `BFloat16` tensor type error. DeepSpeed's `CUDAQuantizer` dequantizes INT8 communication buffers exclusively to FP16 (`torch.float16`). Disable BF16 and enable FP16 when using ZeRO++ quantization, or use Megatron-FSDP with `--fp8-format hybrid --fp8-param-gather` on Hopper and Blackwell GPUs.

---

## FILE docs/part-14-training-finetuning/07-tensor-pipeline-and-expert-parallelism-megatron.md

1. **Single-layer matrices exceed single-GPU efficiency.** A single projection matrix in a 175B model holds over 600 million parameters and consumes 1.2 GB in half precision. At 1 trillion parameters, mixed-precision state reaches 12 TB, far exceeding the memory of two 8-GPU nodes.
2. **Per-layer AllGather collectives saturate inter-node links.** Even when sharded state per GPU is small, gathering full layers across hundreds of nodes on every pass stalls on slower InfiniBand fabric links.
3. **Long-context activations overwhelm GPU memory.** At sequence lengths of 32K to 128K tokens, intermediate activations exceed 40 GB to 52 GB per GPU even when weights are sharded.
4. **Single-device compute time is far too slow.** Executing a single training step of a 175B model on one GPU would take over an hour. Iteration becomes impossible without splitting the math itself.

---

A common mistake is treating FSDP2 and Megatron Core as competing tools where you only need one. Suppose a team trains a 175B model across a thousand GPUs using pure FSDP2 or ZeRO-3. Every GPU must reconstruct each full layer before multiplying it. That design floods the inter-node network with global AllGather traffic on every layer and leaves activations unsharded.

---

1. **Virtual Pipeline Parallelism (`--num-layers-per-virtual-pipeline-stage`).** Instead of giving each GPU one large contiguous block of layers, Interleaved 1F1B assigns `v` smaller non-contiguous layer chunks to each GPU. Each virtual stage finishes `v` times faster. The pipeline warm-up and cool-down bubbles shrink by a factor of `1 / v` while point-to-point transfers increase by `v`.
2. **Eliminating the Ghost Straggler on edge stages.** Suppose a 96-layer model is split evenly into 6 layers per stage across 16 stages. Stage 0 and Stage 15 still run about 40 percent slower than Stages 1 through 14. Stage 0 must also compute the 1.2 GB vocabulary embedding lookup, and Stage 15 must compute the final projection and cross-entropy loss. Assigning fewer Transformer layers to the first and last stages and sharding the vocabulary with `VocabParallelEmbedding` removes the stall.
3. **Bidirectional overlap with DeepSeek DualPipe.** Introduced in the DeepSeek-V3 Technical Report, DualPipe feeds micro-batches from both ends of the pipeline at the same time. Pairing a forward chunk and a backward chunk on each GPU hides point-to-point and AllToAll communication behind matrix math. That overlap reduces pipeline bubbles to near zero even on bandwidth-constrained H800 clusters.

---

At thousand-GPU scale, no single parallelism technique can handle width, depth, sequence length, and batch throughput on its own. Megatron Core solves this by organizing the cluster into an orthogonal multi-dimensional grid using `megatron.core.parallel_state`. Every GPU belongs simultaneously to distinct Tensor, Pipeline, Context, Expert, and Data Parallel groups.

---

## FILE docs/part-14-training-finetuning/08-pytorch-performance-profiling-tuning-and-scaling.md

When a training step runs slowly, looking only at GPU kernel times leaves you blind to Python interpreter overhead, data loader stalls, and memory fragmentation. Conversely, looking only at a system timeline hides which PyTorch operator launched a slow kernel. Engineers waste days guessing at root causes when their profiling tools cannot talk to each other.

---

General compiler fusion cannot rewrite the quadratic memory traffic of naive self-attention or automatically quantize weights to 8-bit and 4-bit formats with structured sparsity. To reach hardware Roofline limits on attention and low-precision GEMMs, compose `torch.compile` with four native PyTorch APIs:

---

1. **SimpleFSDP.** SimpleFSDP expresses FSDP parameter sharding and selective activation checkpointing directly in a compiler-traceable DTensor graph. TorchInductor then buckets and reorders intermediate representation nodes to maximize overlap. Compared to eager FSDP2, SimpleFSDP cuts peak memory usage by up to 28 percent and boosts training throughput by up to 69 percent.
2. **Asynchronous Tensor Parallelism (AsyncTP).** Standard Tensor Parallelism places an AllGather or ReduceScatter directly on the critical path of every layer. AsyncTP uses `torch.compile` to decompose the GEMM and collective across dual CUDA streams with an SM-wave-aware schedule. It overlaps late-arriving AllGather chunks with the next SM wave's matrix multiplications.
3. **AutoParallel.** Building on the DTensor operator-strategy cost model, AutoParallel automatically searches and applies hybrid FSDP, TP, and PP sharding plans across a model graph. It selects the optimal plan using cluster memory and interconnect bandwidth constraints.

---

When a training job scales to dozens or thousands of GPUs, opening individual trace files by hand is impossible. Moreover, the legacy PyTorch TensorBoard profiler plugin is deprecated as of 2025. Without automated multi-rank trace alignment and continuous regression gates, a single straggler GPU or a bad pull request can silently burn thousands of GPU hours.

---

## FILE docs/part-14-training-finetuning/09-pytorch-compilers-and-kernels-torch-compile.md

Because AOTAutograd sees the entire forward and backward dataflow graph ahead of time, it solves a **min-cut graph partitioning problem**. This algorithm splits the joint graph into a forward subgraph and a backward subgraph. Rather than saving every intermediate activation tensor to HBM or recomputing everything from scratch, the min-cut partitioner finds the minimum-memory cut of tensors to save across the pass boundary. It automatically recomputes cheap elementwise intermediates inside the fused backward kernel instead of reading and writing them to HBM. It also applies common-subexpression elimination, cross-boundary operator fusion, and buffer reuse while preserving exact eager autograd semantics.

---

PyTorch's C++ ATen operator library exposes more than 2,000 operators. Many of these operators overlap in functionality or mutate tensors in place. That huge surface makes it practically impossible to write a compiler backend that supports all 2,000 operators for every new GPU or custom ASIC.

---

Beyond `TORCH_LOGS`, three debugging and numerical-accuracy workflows are essential for production training:
- **Disk artifact dumps and trace parsing:** Setting `TORCH_COMPILE_DEBUG=1` writes a per-process debug directory containing FX graphs, runnable Python code, Inductor IR dumps, and compiled PTX. Setting `TORCH_TRACE="/tmp/tracedir"` and running `tlparse` renders a hierarchical stack-frame tree and a Perfetto timeline. The trace overhead is low enough for production runs.
- **Pinpointing numerical discrepancies with the Level 4 minifier:** If a compiled training step produces `NaN` values or mismatches eager mode, export `TORCHDYNAMO_REPRO_AFTER="aot"` and `TORCHDYNAMO_REPRO_LEVEL=4`. Checking after AOTAutograd tests both forward and backward passes. Level 4 runs every subgraph in both eager and compiled mode, compares their outputs numerically, and invokes the minifier on the first mismatch.
- **Random number parity and cuBLAS bitwise determinism:** TorchInductor fuses and reorders parallel Philox PRNG calls in Triton. As a result, compiled dropout sequences differ from eager mode unless you enable `fallback_random`. To enforce bitwise determinism across runs, you must also disable non-deterministic cuBLAS split-K reductions by exporting `CUBLAS_WORKSPACE_CONFIG=:4096:8` before starting Python.

---

Finally, when targeting non-NVIDIA accelerators, PyTorch XLA (`backend="openxla"`, Figure 14-6 in Chapter 14) lowers PyTorch graphs into OpenXLA StableHLO and HLO executables. This backend supports Google Cloud TPUs, Meta MTIA, and AWS Trainium or Inferentia via the AWS Neuron SDK:

---

## FILE docs/part-14-training-finetuning/10-multi-node-training-architecture.md

This eight-lane highway design matches how NCCL runs hierarchical collectives across nodes. First, the GPUs inside each node exchange and reduce data chunks locally over NVLink. Second, all first-index GPUs across nodes communicate with each other over the first rail. Meanwhile, all second-index GPUs communicate over the second rail in parallel. Because each rail has its own dedicated leaf switch, cross-node AllReduce traffic on one rail never contends for switch buffers with traffic on another rail. Within a Scalable Unit of thirty-two nodes, same-index ranks communicate in a single non-blocking leaf switch hop. They never even traverse the spine layer.

---

In PyTorch, this control-plane handshake is called rendezvous and is backed by `c10d` `TCPStore`:
1. **The master process starts the TCP server:** The launcher or first rank on the master node opens a TCP listening socket on the master address and port.
2. **Every worker registers its coordinates:** Each process connects to the master endpoint and reports its world size, node rank, local rank, and global rank. You must never set the master address to `127.0.0.1` on multi-node jobs. You should also randomize the master port on shared nodes to prevent port collisions.
3. **NCCL communicator bootstrap:** Once all ranks enter `init_process_group`, the first rank generates a bootstrap handle and writes it into `TCPStore`. Every rank reads that handle and initializes its NCCL communicator. Communication then switches from the TCP control socket to high-speed NVLink and RDMA data planes.

---

From a distributed training job's perspective, three Slurm daemons and two resource abstractions govern execution:
- **Controller daemon (`slurmctld`):** Runs on the head node, often as an active-backup HA pair. It manages the job queue, evaluates fair-share and backfill policies, and allocates whole nodes.
- **Compute node daemon (`slurmd`):** Runs on every GPU server. It receives allocations from the controller, forks job steps, enforces Linux `cgroup` isolation, and reports node health.
- **Database daemon (`slurmdbd`):** Records historical job accounting metrics and GPU-hours into MySQL or MariaDB for `sacct` queries.
- **Partitions and GRES:** Partitions group homogeneous nodes like `gpu-h100`. Generic Resource Scheduling maps requested GPUs to physical device files via `gres.conf` and sets `CUDA_VISIBLE_DEVICES`.

---

Maintaining high scaling efficiency across thousands of GPUs requires three architectural invariants. First, keep TP and FSDP AllGather sharding inside the NVLink domain. That layout ensures cross-node collectives move only one-eighth of the gradient state. Second, scale the global batch size or gradient accumulation steps so the compute time per step stays much larger than the collective communication time. Third, overlap DP gradient synchronization with backward compute and set `CUDA_DEVICE_MAX_CONNECTIONS=1` in Megatron-LM.

---

## FILE docs/part-14-training-finetuning/11-checkpointing-fault-tolerance-and-elastic-training.md

Saving state at foundation-model scale introduces three severe engineering challenges.
- **Massive payload size:** A seventy-billion-parameter model checkpoint exceeds one terabyte. Moving a terabyte to persistent storage across a shared network takes substantial time and bandwidth.
- **The checkpoint pause:** While GPUs wait for a synchronous checkpoint write to finish, they sit at zero percent compute utilization. Pausing for five minutes every hour wastes about eight percent of your entire GPU cluster budget.
- **Shattered state assembly:** Under FSDP, ZeRO-3, or Megatron-LM 3D parallelism, no single GPU holds the whole model. Every rank holds only a small puzzle piece. The cluster must save and reassemble those shards even if node failures shrink the cluster size upon restart.

---

A common beginner mistake is saving only the neural network weights. If a job crashes halfway through training and resumes with only the model weights, training does not fail with an error message. Instead, the loss immediately spikes or silently diverges from the trajectory of an uninterrupted run.

---

In small DDP jobs where every GPU holds a full copy of a small model, only rank zero writes the checkpoint file while other ranks wait at a distributed barrier. When you move to a seventy-billion-parameter model sharded across 128 H100 GPUs with FSDP or ZeRO-3, gathering the full state dictionary onto rank zero creates an immediate network and storage bottleneck.

---

Even at the Young-Daly optimum, a three-minute synchronous checkpoint write still leaves a thousand GPUs idle for 5.6 percent of every hour. Worse, shared parallel filesystems suffer from noisy-neighbor congestion. When another job on the cluster dumps a massive checkpoint at the same time, your ninety-second write can suddenly balloon to twelve minutes.

---

## FILE docs/part-14-training-finetuning/12-training-performance-engineering-and-troubleshooting.md

To measure whether the car is actually moving down the road, performance engineers ignore coarse utilization and calculate **Model FLOPs Utilization**. Model FLOPs Utilization divides the mathematical operations required by the model per second by the theoretical peak floating-point throughput of the silicon. For large language model training, a Model FLOPs Utilization between 40 and 50 percent is excellent. By contrast, a figure near 15 to 20 percent proves that a severe bottleneck is starving the Tensor Cores.

---

While Model FLOPs Utilization measures how fast a step executes while the training loop is running, **Goodput** measures end-to-end useful tokens processed per second across the entire wall-clock calendar. Goodput discounts all time lost to checkpoint pauses, job preemptions, node failures, and rollback restarts. Meta's infrastructure analysis defines this ratio as the Effective Training Time Ratio. Even when a cluster appears 100 percent allocated, 70 to 75 percent of theoretical compute can be lost to communication stalls, data delays, and fault recovery.

---

Performance engineers hunt bottlenecks from the outside in across three diagnostic levels. First, inspect macroscopic system telemetry in Prometheus, Grafana, DCGM, and `nvidia-smi`. That telemetry classifies whether the job is starved by the host CPU, blocked on the network, or executing inefficiently on the GPU. Second, capture a multi-rank timeline in PyTorch Profiler, Nsight Systems, or Holistic Trace Analysis to locate exact idle gaps, non-overlapped transfers, and straggler ranks. Third, run Nsight Compute on the specific hot kernels identified in the timeline to determine whether they are memory-bandwidth-bound or compute-bound on the Roofline chart.

---

When scaling PyTorch Distributed with `torch.compile`, you must also preserve bucketed compute-communication overlap. In DDP, PyTorch divides gradients into 25 MB buckets (`bucket_cap_mb=25`) and inserts intentional TorchDynamo graph breaks between buckets. Each bucket's AllReduce then overlaps with the next bucket's backward pass. In FSDP, wrapping at the transformer-block granularity materializes only one block at a time and overlaps AllGather and ReduceScatter with block compute. In TorchTitan, SimpleFSDP lowers peak GPU memory by 28 percent and raises training throughput by 69 percent compared to eager FSDP2. Similarly, AsyncTP overlaps Tensor Parallelism collectives with SM-wave matrix multiplications, cutting sequential phase latency by over 21 percent.

---

## FILE docs/part-14-training-finetuning/13-fine-tuning-sft-lora-and-qlora-preference-alignment.md

For an infrastructure engineer, post-training changes the memory, compute, and serving profile of the cluster in three critical ways.
- **The trainable-parameter memory wall:** Full fine-tuning updates every weight in the network. It also stores gradients and Adam optimizer states for every parameter. Under a standard sixteen-byte-per-parameter mixed-precision baseline, full fine-tuning requires 112 GB of VRAM for a seven-billion-parameter model. A seventy-billion-parameter model requires 1,120 GB of VRAM before counting activations. Even in pure sixteen-bit precision, a seven-billion-parameter model needs 56 GB of VRAM just for weights, gradients, and Adam states.
- **Parameter-efficient compression and quantization:** Parameter-Efficient Fine-Tuning methods such as LoRA freeze the base model. They train low-rank adapter matrices that represent less than 1 percent of the total parameters. Combining LoRA with four-bit NormalFloat quantization, Double Quantization, and Paged Optimizers in QLoRA cuts peak training memory for a seven-billion-parameter model down to 9.3 GB. That reduction lets a sixty-five-billion-parameter model train on a single 48 GB GPU. The trade-off is roughly 30 percent slower step times from dequantization overhead.
- **Multi-model alignment orchestration:** Aligning a model with human preferences via Reinforcement Learning from Human Feedback and Proximal Policy Optimization requires four distinct models in GPU memory at once. Furthermore, autoregressive rollout generation on serving engines like vLLM or SGLang consumes 80 percent of the wall-clock step time. Newer algorithms like Direct Preference Optimization and Group Relative Policy Optimization eliminate separate reward or value networks. Those algorithms cut cluster memory requirements by half or more.

---

Three mathematical details govern how LoRA behaves during training and serving.
1. **Zero-perturbation initialization:** Matrix A is initialized from a Gaussian distribution with standard deviation inversely proportional to the square root of the rank. Matrix B is initialized strictly to **zeros**. Because B is zero at step 0, the product of A and B is zero. Therefore, the fine-tuned model begins training with the exact behavior of the pre-trained base model.
2. **The alpha-over-rank scaling factor:** The adapter output is multiplied by the ratio of alpha to rank before being added to the frozen base output. Scaling by the inverse of the rank normalizes activation variance as you change the rank. Consequently, you do not have to retune the learning rate from scratch every time you double the rank from 16 to 32. Common heuristics set alpha equal to the rank or twice the rank.
3. **Target modules:** Originally, Hu et al. applied LoRA to the four attention matrices. On GPT-3 175B with a fixed 18M trainable parameter budget, applying rank 2 across all four attention matrices achieved 73.7 percent on WikiSQL and 91.7 percent on MultiNLI. That configuration outperformed applying rank 8 to any single attention matrix, which scored between 70.0 percent and 73.2 percent on WikiSQL. Subsequent studies by Databricks and Dettmers et al. showed that applying LoRA to **all seven linear layers** in a modern Transformer—including the SwiGLU MLP projections `gate_proj`, `up_proj`, and `down_proj`—delivers the largest quality gains. All-linear LoRA matches full fine-tuning much more closely than attention-only LoRA.

---

The following production pipeline from `LLM Engineer's Handbook` Chapters 5 and 6 fine-tunes Meta-Llama-3.1-8B into TwinLlama-3.1-8B with `SFTTrainer`. It upsamples 3,335 domain pairs with 10,000 FineTome samples, applies rank 32 across all 7 linear layers, and completes 3 epochs in 50 minutes on one A100 GPU. Stage 2 aligns the model into TwinLlama-3.1-8B-DPO using `DPOTrainer` on 1,467 filtered preference triples.

---

1. **Adaptation Decision Matrix and Break-Even Token Economics.**
   - **(a)** In Ovadia et al.'s current-events QA benchmark, compare the accuracy of Mistral-7B, Llama 2-7B, and Orca 2-7B across Base, Base plus RAG, and standalone fine-tuning. Explain why Llama 2-7B dropped from 0.353 to 0.219 under regular fine-tuning and why RAG outperformed fine-tuning across all three models.
   - **(b)** Suppose fine-tuning a proprietary model via API costs 25,000 dollars for 1,000,000 training tokens. Doing so eliminates 2,000 few-shot prompt tokens per request, billed at 2.50 dollars per 1,000,000 input tokens. Calculate the per-request prompt cost, the annual prompt overhead at 500,000 requests per year, and the break-even time in years. State whether fine-tuning is cost-effective if the model will be replaced in 2.0 years.
2. **Full Fine-Tuning vs LoRA Parameter and Memory Math.**
   - **(a)** Using the pure 16-bit calculation from `AI Engineering` Chapter 7, calculate the inference memory with the 1.2x multiplier and full training memory for a 13B model and a 7B model. Then compare the 7B and 70B full fine-tuning footprints under the 16-byte-per-parameter mixed-precision baseline from `LLM Engineer's Handbook` Chapter 5.
   - **(b)** For GPT-3 175B with 96 layers and hidden dimension 12,288, calculate the per-layer and total trainable LoRA parameters when applying rank 2 to all 4 attention matrices. Also compute the 16-bit adapter size in MB. Next, for Llama 3 8B with 32 layers, compute the exact trainable parameter count at rank 16 across all 7 linear modules, and at rank 32 when `lm_head` is also adapted.
3. **Multi-LoRA Serving Storage vs Merged Checkpoints.**
   - **(a)** Consider a single 4,096 by 4,096 weight matrix of 16,777,216 parameters adapted with LoRA rank 8 for 100 enterprise customers. Compute the number of parameters in a single adapter pair, the total parameters required to store 100 merged matrices, and the total parameters required to store 1 shared base matrix plus 100 unmerged adapter pairs.
   - **(b)** Explain how the Punica kernel executes a mixed batch of requests targeting different LoRA adapters in vLLM. State when you should use `model.merge_and_unload()` instead of Multi-LoRA serving.
4. **QLoRA Internals and Double Quantization Bit-Budget Derivation.**
   - **(a)** Derive the quantization scale overhead in bits per parameter for single block-wise quantization with an FP32 scale per 64 weights. Compare that against QLoRA Double Quantization with an FP8 first-level scale per 64 weights plus an FP32 second-level scale per 256 blocks. Calculate the net bits saved per parameter, the effective bits per parameter for NF4 weights, and the gigabytes of VRAM saved on a 65B model.
   - **(b)** Compare initialization VRAM, peak training VRAM, and training speed between 16-bit LoRA and 4-bit QLoRA on a 7B model. Explain how `paged_adamw_8bit` prevents OOM crashes on long sequences.
5. **SFT Effective Batch Size, Sequence Packing, and Prompt Loss Weighting.**
   - **(a)** Calculate the effective batch size for a single GPU with micro-batch 2 and accumulation 8, and for 2 GPUs with micro-batch 4 and accumulation 4. Next, consider 8 training examples of token lengths 220, 260, 240, 280, 250, 230, 270, and 210 with a maximum sequence length of 1,024. Compute the number of batch slots and token utilization percentage with and without sequence packing.
   - **(b)** Consider an example with 4 prompt tokens of loss 2.0 each and 2 response tokens of loss 0.5 each. Compute the weighted sample loss when the prompt loss weight is 0 percent, 10 percent, and 100 percent.
6. **Preference Alignment and Model Merging.**
   - **(a)** Consider 4 preference pairs trained with DPO at beta equal to 0.5 using the log-probabilities in Section 4.3. Compute the mean chosen reward, mean rejected reward, mean reward margin, and reward accuracy. Compare the 8B model-state VRAM across Full PPO, Full GRPO, Full DPO, and LoRA DPO with `ref_model=None`.
   - **(b)** Given a group of 4 completions with rewards 1.0, 2.0, 3.0, and 6.0, compute the GRPO group-normalized advantages. Finally, calculate the rescaling factor for DARE with drop probability 0.8 and the final layer counts of SOLAR 10.7B and Goliath-120B.

---

## FILE docs/part-14-training-finetuning/14-dataset-engineering-for-fine-tuning.md

In early deep learning benchmarks, researchers held the dataset fixed and competed to design better model architectures. Modern post-training has inverted that paradigm into data-centric AI. Teams now hold the base model architecture fixed and compete to engineer cleaner, more diverse, and more compute-efficient datasets.

---

Most importantly, concentrated repetition cripples the internal representations of a neural network. In a landmark study, Anthropic researchers repeated a tiny fraction of a dataset a hundred times. That duplication degraded an eight-hundred-million-parameter model to the level of a four-hundred-million-parameter model. That fifty percent loss of effective model capacity occurred even though ninety percent of the training tokens remained completely unique. Similarly, repeating an entire fine-tuning dataset over too many epochs triggers multi-epoch degradation, where validation perplexity climbs as the model memorizes phrasing.

---

Generating synthetic text is easy, but training on unverified synthetic outputs is dangerous. When functional execution checks like unit tests or back-translation are unavailable, pipelines rely on **LLM-as-a-Judge** evaluators. These evaluators use either a 1-to-4 absolute scoring rubric or pairwise comparison between two candidate responses, targeting at least eighty percent agreement with human annotators.

---

Every LLM judge exhibits three systematic biases that must be engineered out of your verification pipeline.
1. **First-position bias:** In pairwise ranking, LLM judges consistently favor whichever response is presented first. To eliminate position bias, NVIDIA researchers on Nemotron-4 evaluated every candidate pair twice. They ran one pass in forward order and a second pass in swapped order. A preference triplet is kept only if the judge selects the exact same underlying response in both orderings.
2. **Length and verbosity bias:** Both humans and LLM judges favor longer, formal responses even when they are repetitive. Apply length-normalized scoring and include concise gold examples in few-shot rubrics. During Direct Preference Optimization, raise `beta` from `0.1` to `0.5` with a low learning rate of `2e-6` for one epoch when preserving casual human writing styles.
3. **Intra-model family favoritism:** Models score outputs from their own model family higher than external models. Replace single-model judges with a multi-model jury of smaller, diverse evaluators.

---

## FILE docs/part-14-training-finetuning/15-fine-tuning-infrastructure-and-cost.md

When a foundation model produces poor answers on an enterprise task, teams often jump straight to fine-tuning. That reflex wastes engineering weeks and thousands of dollars in GPU compute when the failure is actually caused by missing context. In the LLM lifecycle, pre-training consumes thousands of GPUs for weeks to build a base text predictor. Alignment then teaches safety boundaries and instruction following. Model customization, also called post-training, adapts an already aligned model to domain tasks.

---

QLoRA, introduced by Dettmers et al., attacks that base-weight footprint through three stacked systems optimizations in `bitsandbytes`.
- **4-Bit NormalFloat Storage.** Pre-trained neural network weights follow a zero-centered normal distribution. NormalFloat-4 is an information-theoretically optimal four-bit data type that assigns equal numbers of values to each quantile of the standard normal distribution. Base weights are stored in HBM at half a byte per parameter via `bnb_4bit_quant_type="nf4"`. They are then dequantized on the fly to BF16 tiles inside GPU registers during forward and backward matrix multiplications.
- **Double Quantization.** Blockwise four-bit quantization requires a thirty-two-bit scaling constant for every block of sixty-four weights. That adds half a bit per parameter of metadata overhead. Enabling `bnb_4bit_use_double_quant=True` quantizes those scaling constants themselves into eight-bit floats in blocks of two hundred fifty-six. That trims metadata overhead down to roughly a tenth of a bit per parameter.
- **Paged 8-Bit Optimizers.** Long sequence lengths can still trigger transient activation memory spikes during `loss.backward()`. Setting `optim="paged_adamw_8bit"` allocates optimizer states in CUDA Unified Memory. The driver automatically pages optimizer buffers to host CPU RAM during activation spikes and pages them back to HBM during `optimizer.step()`.

---

In addition to fine-tuning, teams increasingly apply model merging to combine multiple task-specific models or adapters without requiring a GPU.
- **Linear Combination and Task Arithmetic:** Averages model weights or adds task vectors computed by subtracting the base weights from the fine-tuned weights.
- **SLERP Spherical Linear Interpolation:** Interpolates two models along the shortest geodesic arc on a hypersphere using an interpolation factor between 0 and 1. A factor of 0.5 selects the exact midpoint.
- **TIES and DARE Pruning:** Yadav et al. showed that keeping only the top 20 percent of task-vector parameters preserves full accuracy while eliminating parameter interference across merged tasks.

---

1. **RAG is for facts; fine-tuning is for form and context compression.** Always start with systematic prompt engineering and retrieval for missing or dynamic facts. Fine-tune when you need strict output schemas, domain tone, or to embed slow-changing context into an 8B to 16B Small Language Model so recurring prompt costs drop.

---

## FILE docs/part-14-training-finetuning/16-nemo-framework-and-customisation.md

In a production AI factory, training workloads and inference services have opposite operational profiles. Training and customization are throughput-oriented batch jobs. They allocate gang-scheduled GPU clusters for hours or weeks, stream terabytes of training tokens, synchronize gradients over NVLink and InfiniBand, and write multi-gigabyte checkpoints to parallel storage. Inference serving is a latency-bound, long-running microservice. It must satisfy strict Time To First Token and Time Per Output Token objectives while scaling elastically with user traffic.

---

NVIDIA separates these two worlds cleanly across three core components.
- **NeMo Framework** owns the **model creation and customization lifecycle**. It provides modular components for dataset curation via NeMo Curator, distributed pre-training and fine-tuning via Megatron-Core and NeMo Customizer, preference alignment via NeMo Aligner, and benchmark verification via NeMo Evaluator.
- **NVIDIA NIM** owns the **production serving lifecycle**. At container startup, NIM inspects the physical GPU architecture, such as Hopper H100 or Blackwell B200. It selects a matching TensorRT-LLM or vLLM execution profile, configures paged KV cache allocation, and exposes an OpenAI-compatible REST and gRPC API over Triton Inference Server.
- **NeMo Guardrails** bridges the **policy and safety boundary** at runtime. It sits in front of the deployed NIM microservice as a programmable Colang gateway. That gateway filters user inputs, dialog state, RAG retrievals, tool calls, and generated outputs without requiring model retraining.

---

Before a customized checkpoint is promoted to production NIM serving, **NeMo Evaluator** runs automated academic and domain test suites. It measures perplexity, ROUGE-1, BLEU, MMLU, GSM8K, and asynchronous LLM-as-a-Judge rubrics. In production, teams sample 1 to 10 percent of live traffic asynchronously so judge models do not block user responses.

---

Once deployed in NIM, **NeMo Guardrails** enforces deterministic corporate and security policies around the statistical model using **Colang**, a domain-specific modeling language for conversational flows. NeMo Guardrails intercepts traffic across **five distinct rail stages** and introduces an explicit latency trade-off that architects must budget against their Service-Level Objectives.

---

