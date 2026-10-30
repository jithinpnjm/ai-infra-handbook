---
id: "c01-01"
title: "1.1 The Linux big picture: kernel, userspace, distributions"
sidebar_label: "1.1 The Linux big picture: kernel, userspace, distributions"
sidebar_position: 1
description: "A from-zero map of a Linux system: hardware, the kernel, user space, system calls, processes, users and distributions, tied to what runs on a GPU node."
status: "drafted"
tier: "0"
level: "B"
lab_venue: "GCP VM"
---

# 1.1 The Linux big picture: kernel, userspace, distributions

| Field | Value |
|---|---|
| Level | Basics |
| Priority tier | Tier 0 (foundations) |
| Lab venue | Small Ubuntu VM on GCP (`linux_layers_lab.py`: 26 checks pass; VM commands **untested** here) |
| Part | Part 1: Linux, from the command line to the kernel and performance |

## Why this matters for AI infrastructure

Think about a bad day on an AI cluster. A training run slows to a crawl, a container refuses to start, or a driver stops loading after an update. Before you can fix any of these, you need to know how much of the factory runs Linux.

Every machine in an AI factory runs Linux. That includes the GPU servers, the Slurm controller, the Kubernetes nodes, the storage servers, the BMCs' companion hosts, and even the data center switches. Look inside a modern spine or leaf switch on an AI fabric and you will find a full Linux distribution driving the switching silicon. Even the switches run Linux, so a network fault can have a Linux cause. The OpenCompute Project builds Open Network Linux, or ONL, which underpins Big Switch's Switch Light and the DENT Project's dentOS. NVIDIA ships Debian-based Cumulus Linux on its Spectrum Ethernet switches. Microsoft, Intel, NVIDIA, Broadcom, and Dell collaborate on SONiC, which stands for Software for Open Networking in the Cloud. Automation tools like Ansible and Python also run from Linux control hosts. Kernel technologies like eBPF and XDP are reshaping high-speed networking, security, and observability.

The cause of any such failure lives in one specific layer of the system. You can only find it quickly if you can name the layers and know what each one does. Each component has a tremendous amount of internal detail, and we will set that aside at first. We will focus on what each component does for the whole system.

This chapter gives you a high-level map of the components that make up a Linux system. Nothing later in the book makes sense without that map. That includes cgroups, namespaces, Kubernetes pods, GPU drivers, and RDMA. So we start at the very beginning and assume nothing.

If you have used Linux for years but never learned *how it is put together*, this chapter is for you. You do not need to memorise commands. You need a clear picture in your head, so that you can say: "this is a kernel problem, that is a user-space problem, and this other thing is a hardware problem."

## Prerequisites and outcomes

What do you need before you start? A terminal on any Linux machine, and a willingness to type commands. By the end, you will be able to do the following:

- Explain what an operating system does, in plain words, using the three-layer model of hardware, kernel, and user space.
- Explain the difference between kernel mode and user mode, and why that boundary exists.
- Describe the four jobs of the kernel: running processes, managing memory, managing devices, and serving system calls.
- Explain what a process is, trace what happens when you type a command with `fork` or `clone` and `exec`, and watch it happen with `strace`.
- Explain what Linux is as a kernel, what a distribution is as a kernel plus everything else, and how the Red Hat and Debian families evolved.
- Place the NVIDIA driver, CUDA, the container runtime, `slurmd` and RDMA correctly on a layered diagram of a GPU node.
- Use a short set of commands to inspect any Linux machine, and recognise six classic confusions that come from mixing up the layers.

## 1. What an operating system is for

Picture a GPU server with several training jobs running at once. Each job wants CPU cores, memory, disks, and GPUs, but the machine has only one set of each. As you will see, the operating system is what makes that sharing possible. The shared resources here are processor cores, memory, storage, network cards, and GPUs. Without something in charge, every program would have to know how to talk to every kind of disk and network card. Programs could read and overwrite each other's memory, and one runaway program could freeze the whole machine.

An **operating system**, or **OS** for short, is the software that sits between programs and hardware. It solves exactly these problems. It does three things:

1. **Shares** the resources fairly. It decides which program runs on which CPU core and for how long.
2. **Protects** programs from each other and itself from programs. One crashing program must not take down the others.
3. **Simplifies** access to hardware. A program asks to "write these bytes to this file" and does not care whether the disk is an SSD, a network drive, or something else.

Think of a large office building. The people inside are the programs. The property manager handles the building. That manager allocates rooms for memory, schedules the shared meeting rooms for CPU time, and decides who may enter which floor. The same manager runs the plumbing and electricity, so a tenant can turn on a tap for hardware access without rewiring anything. Tenants never touch the building directly. They make requests at the front desk. In Linux, the property manager is the **kernel**, and the front desk is the **system call interface**. Keep the building in mind, because we will come back to it.

## 2. The three layers

Suppose a GPU job crashes with an error. Your first question is where the fault lives. Almost everything you will ever debug on Linux fits on the picture below.

```mermaid
flowchart TB
  subgraph UserSpace["USER SPACE: restricted mode"]
    direction LR
    APPS["Applications<br/>python, slurmd, containerd"]
    LIBS["Shared libraries<br/>glibc, libcuda.so, libibverbs.so"]
    INIT["System services<br/>systemd (PID 1), cron, journald"]
  end
  subgraph Kernel["KERNEL: privileged mode"]
    direction LR
    SCHED["Process scheduler"]
    MEM["Memory manager<br/>virtual memory"]
    FS["Filesystems and block layer"]
    NET["Network stack<br/>TCP/IP, netfilter"]
    DRV["Device drivers<br/>nvidia.ko, mlx5, nvme, e1000"]
  end
  subgraph HW["HARDWARE"]
    direction LR
    CPU["CPU cores"]
    RAM["Main memory: RAM"]
    DISK["Disks, NVMe"]
    NIC["NICs, InfiniBand HCAs"]
    GPU["GPUs"]
  end
  APPS --> LIBS
  LIBS -->|"system calls"| Kernel
  INIT -->|"system calls"| Kernel
  Kernel --> HW
```

Read the picture from the bottom up.

**Hardware** is the physical machine. At the bottom sit the CPU cores, which execute instructions. Next to them sits **main memory**, which engineers call RAM. Main memory holds the programs and data that are currently running. Around them are devices: storage, network cards, and GPUs. The most important fact about hardware for this chapter is simple. *The CPU only ever works on data that is in main memory.* A program, the kernel, a network packet that just arrived, or a file you are reading is, while the CPU works on it, a sequence of bytes in RAM. Disks, networks, and GPUs are all places to move bytes to and from RAM.

You will hear the word **state** constantly, so fix its meaning now. Strictly, a state is one exact arrangement of bits. Four bits holding 0110, 0001 and 1011 are three different states. A running process or the kernel can be millions of bits, so nobody talks about raw bits at that scale. Instead, people describe state in plain terms, such as "the process is waiting for input" or "the process is in stage 2 of startup." The physical arrangement of bits that makes up a running program or kernel is sometimes called its **image**. Nearly everything the kernel does revolves around main memory. It divides memory into pieces, tracks the state of every piece at all times, and makes sure each process stays inside its own share.

**The kernel** is a program like any other in one respect. It is a large piece of software loaded into memory. It is special in two ways. First, it is the first piece of the OS to start when the machine boots, and it stays until shutdown. Second, the CPU runs it in a **privileged mode** that lets it touch all memory and all hardware. This is the property manager from our analogy.

**User space** is everything else. It holds every program you have ever run, from `ls` to a PyTorch training job to a database. Programs in user space run in an **unprivileged mode**. They cannot touch hardware directly, and they can only see their own memory. When a program needs something only the kernel can provide, such as opening a file, sending a packet, starting another program, or asking for more memory, it makes a **system call**. A system call is a controlled request through a defined doorway. The kernel checks the request, performs it, and returns the result.

User space is not one lump. Its programs fall into a **rough layering**. At the bottom sit *basic services*, which are small components that do one uncomplicated job, such as a logging daemon. In the middle sit *utility services*, which are larger components such as mail, printing, a database, or a DNS cache that other programs use. At the top sit *applications*, the programs users touch directly, such as a browser or a training script. A component generally uses components at its own level or below.

Treat this picture as an approximation, because **user space has no real rules**. Most programs write diagnostic messages through the standard `syslog` service, yet some do their own logging. A database server can be called a high-level application because its task is complicated. It can also be called a middle-level service because applications depend on it. From the kernel's point of view, all processes are equal. The layers are a human way to reason about dependencies. You will also hear the informal word **userland** for user space, and sometimes for the programs in it.

### Why two modes? Kernel mode and user mode

Modern CPUs build the split into hardware. A CPU can run in at least two privilege levels. On x86 processors, people traditionally call them **ring 0** and **ring 3**. Ring 0 is the most privileged level, and the kernel uses it. Ring 3 is the least privileged level, and normal programs use it. In ring 0, the CPU allows instructions that control memory protection, talk to devices, and handle interrupts. In ring 3, trying to run one of those instructions makes the CPU raise a fault. The kernel then decides what to do, and usually it kills the offending program.

This boundary gives you a property you rely on every day. **If a user-space program crashes, the kernel cleans it up and the rest of the system continues.** A buggy Python script can crash without corrupting the kernel's memory or another user's process. The reverse is also true, and it is why kernel problems are more serious. A bug *inside* the kernel can bring down the whole machine. That includes a bug in a kernel module, such as a GPU driver that runs in kernel mode. A "kernel panic" happens when the kernel itself decides it cannot safely continue.

Two details are worth knowing now, because they appear later:

- **Kernel threads.** The kernel also runs its own background workers, called kernel threads. You will see names like `kthreadd`, `kworker`, and `ksoftirqd` in the process list, enclosed in square brackets. They look like processes, but they live entirely in the kernel.
- **Privilege is not the same as being `root`.** `root` is a *user account* that the kernel lets ask for almost anything. A root process still runs in unprivileged *CPU mode*. The kernel chooses to say yes to its requests. Keep kernel mode and root apart. Kernel mode is a CPU state, and root is a kind of user.

Always identify whether a failure lives in hardware, kernel space, or user space before changing any setting.

## 3. What the kernel does: four jobs

Everything the kernel does fits under four headings: processes, memory, devices, and system calls. Programs normally use system calls to reach the kernel. We will briefly explore each of these four areas here, then meet them in depth in chapters 1.8, 1.10, 1.11, and 1.17. If you want the detailed academic and source-level view of a kernel, read two classic textbooks. One is *Operating System Concepts*, 10th edition, by Abraham Silberschatz, Peter B. Galvin, and Greg Gagne. The other is *Linux Kernel Development*, 3rd edition, by Robert Love.

### Job 1: running processes

A **program** is a file on disk. A **process** is a program that is running. The kernel loads the program into memory and keeps a record for it. That record holds the process ID, the memory map, the files the process has open, its owner, and what it is doing right now.

A computer has far more processes than CPU cores, so the kernel has to share the cores. It does this by **time slicing**. A core runs one process for a very short slice of time, typically a few milliseconds or less. Then the kernel interrupts it, saves where it was, picks another process that is ready, and lets that one run. Switching from one process to another is called a **context switch**. The slices are so short that, to a human, everything appears to run at once. That illusion is **multitasking**. The part of the kernel that picks who runs next is the **scheduler**. For example, several programs can share the same cores this way.

For many years, Linux's default scheduler for ordinary processes was the Completely Fair Scheduler. Starting with kernel 6.6, it was replaced by EEVDF. You do not need the details yet. The idea of fair sharing is what matters.

What triggers the switch? A hardware timer. At the end of a slice, the timer interrupts the CPU, which switches into privileged mode and hands control to the kernel. Here is the sequence in everyday terms:

```mermaid
flowchart LR
  A["Process A runs<br/>in user mode"] --> B["Timer interrupt fires<br/>CPU enters kernel mode"]
  B --> C["Kernel saves A's state:<br/>registers and counter"]
  C --> D["Scheduler picks next<br/>ready process B"]
  D --> E["Kernel loads B's state<br/>and memory mappings"]
  E --> F["Back to user mode:<br/>B runs for its slice"]
  F -->|"timer fires again"| B
```

Two consequences matter, and you should keep both in mind. First, *the kernel only runs between slices of user programs*, or when a program makes a system call or a device raises an interrupt. It is not a separate program running in parallel with yours. It is the thing that steps in on a regular basis. Second, with several cores the picture is the same per core, with the extra job of deciding which core a process should run on. Placement matters a great deal for performance with GPUs and fast networks, as chapter 1.17 covers under NUMA.

### Job 2: managing memory

Every process believes it owns a large, private, continuous block of memory. That belief is an illusion. The kernel builds it with help from a piece of CPU hardware called the **memory management unit**, or **MMU** for short. The design is called **virtual memory**.

Here is the idea. The addresses a program uses are called virtual addresses. They are not physical locations in the RAM chips. The kernel keeps a translation table for each process, called the **page table**. The page table maps chunks of virtual addresses, called **pages**, to chunks of physical RAM. A page is usually 4 KiB. Every time a program reads or writes memory, the MMU translates the address using the table. It does this in hardware, at full speed. This one trick gives the kernel several powers at once:

- **Isolation.** Process A's pages simply are not mapped into process B's table, so B has no way to even name A's memory.
- **Sharing.** Two processes can have page-table entries pointing at the *same* physical page. This is how programs share a library, or how a container image's files are shared in memory.
- **Protection.** Entries can be marked read-only or non-executable.
- **Overcommit and swap.** The kernel can promise more memory than exists. It can also move rarely used pages out to disk and bring them back on demand.
- **Lazy loading.** Pages can be filled in only when first touched.

When a program touches a page that is not currently mapped, the CPU raises a **page fault**, and the kernel handles it. The kernel may load the page, allocate a fresh one, or kill the program if the access was illegal. The famous "segmentation fault" is the last case. You will meet page faults again in GPU work, because GPU unified memory uses the same idea.

Part of the kernel's own bookkeeping is also memory. The kernel needs a private region that user processes can never map. That region is **kernel space**. The part that user processes may use is **user space**.

### Job 3: managing devices

Disks, network cards, keyboards and GPUs all speak different low-level languages. Programs should not have to learn them all. The kernel includes **device drivers**, one for each kind of hardware. Each driver understands its device and exposes it through a common, simple interface. A driver is code that runs in kernel mode. That is the key fact for GPU nodes. **The NVIDIA driver is kernel code.** It is delivered as kernel modules named `nvidia`, `nvidia_uvm` and a few more, plus user-space libraries that talk to it.

Linux presents many devices as **special files** under `/dev`. A program can open `/dev/nvidia0` or `/dev/nvme0n1` and use ordinary file operations. The kernel routes those operations to the right driver. This is the first appearance of a Linux idea you will see everywhere: *many things are made to look like files*. Devices, processes under `/proc`, hardware information under `/sys`, and network sockets all look like files. That way, the same small set of tools and system calls works on all of them.

Some device files do not correspond to any hardware. **Pseudodevices** look like devices to programs, but they are implemented purely in software, usually inside the kernel for practical reasons. `/dev/null` discards what you write. `/dev/zero` provides an endless supply of zero bytes. `/dev/random` and `/dev/urandom` supply random numbers from the kernel's generator, which would be hard to implement securely in an ordinary program. Strictly, a process still needs a system call to open one. So processes can never escape system calls entirely.

Drivers can be built into the kernel, or loaded on demand as **kernel modules** in `.ko` files. Loading a module puts new code *into the running kernel*. That is why a module compiled for one kernel version often refuses to load on another. This is the origin of one of the most common GPU-node failures, covered at the end of this chapter.

### Job 4: system calls and the services around them

A **system call** (syscall) is a request from a user program to the kernel through the defined doorway. There are a few hundred of them. They are the entire vocabulary a program has for dealing with the world outside its own memory. The table below groups the common ones by category. Learn the categories first, because the names will become familiar with use.

| Category | Typical system calls | What they let a program do |
|---|---|---|
| Files | `open`, `read`, `write`, `close`, `stat` | work with files and devices |
| Processes | `clone` (and `fork`), `execve`, `wait4`, `exit_group`, `kill` | create, run, wait for and end processes |
| Memory | `mmap`, `brk`, `munmap`, `mprotect` | ask for or change memory |
| Network | `socket`, `connect`, `bind`, `listen`, `accept`, `sendto`, `recvfrom` | talk over the network |
| Control and info | `ioctl`, `getpid`, `uname`, `clock_gettime` | talk to drivers, ask the kernel questions |

You almost never call these directly. Your program calls a function in a library, such as `printf`, `open`, or `socket`. That library function eventually performs the actual system call. The most important library is **glibc**, the GNU C library. Its file is `libc.so.6`. Nearly every program on mainstream distributions uses it.

Two notation points appear in every book and manual page that you read. System calls are written with parentheses, such as `fork()`, `exec()`, and `execve()`. That habit comes from the C language, in which they are called. You do not need to know C. Just remember that *a system call is an interaction between a process and the kernel*. A name like `exec()` usually stands for a **family** of related C library functions, such as `execl()`, `execv()`, and `execvp()`. Those functions differ only in how they pass arguments. All of them invoke the underlying kernel system call `execve()`.

There is also a lighter variant of a process, called a **thread**. A thread shares most of its memory with the process that created it. That is how a single program uses several cores, as chapter 1.8 explains.

Everything in Linux eventually reduces to system calls, which is why **`strace`**, a tool that prints every system call a program makes, is the best learning and debugging tool you will meet. When a program hangs or fails mysteriously, trace its system calls. That shows the exact kernel boundary where it stopped.

## 4. Processes, users, and who starts what

### What happens when you type a command

Here is the most important worked example in this chapter. It answers the question "how does anything start?" Suppose you type `ls` into a terminal. The program you type into is a **shell**, such as `bash`. A shell is just a user-space program. It reads your text and runs other programs.

```mermaid
sequenceDiagram
  participant You
  participant Shell as bash (process 100)
  participant K as Kernel
  participant Child as New process 101
  You->>Shell: types "ls" and presses Enter
  Shell->>K: system call clone: create a copy of myself
  K-->>Shell: returns the child's process ID, 101
  K->>Child: new process 101 exists, copy of shell
  Child->>K: system call execve("/usr/bin/ls")
  K->>Child: replace program with ls, keep PID 101
  Child->>K: write(1, "file1 file2 ...")
  Child->>K: exit_group(0)
  Shell->>K: wait4: wait for child to end
  K-->>Shell: child 101 finished with status 0
  Shell->>You: prints a new prompt
```

Two steps do all the work. The first is to create a new process. The classic Unix call is `fork()`, which makes the child an almost exact copy of the parent. On modern Linux, the C library implements `fork()` using the `clone` system call, so `strace` will show `clone` or `clone3`.

The second step is to replace the child's program. When the child calls one of the C library's `exec()` functions, such as `exec(ls)` in simplified notation, the library calls the kernel's `execve()` system call. That call throws away the child's current program and loads the new one into the same process. The process ID, or PID, stays the same. Only the program inside it changes.

Every process except the first is created this way, so processes form a **tree**. The first user-space process the kernel starts is called **init**. It has process ID 1, and it is the ancestor of everything. On modern distributions it is **systemd**, covered in chapter 1.15. If a process's parent dies, the process is adopted by PID 1. This tree is why `pstree` is a useful command. It is also why container runtimes and Slurm care so much about who the parent of a process is. In chapter 6.7, `slurmstepd` must be the parent of job processes, so it can track and clean them up.

### Users, owners, and `root`

Linux is a multi-user system. Each user has a numeric **user ID**, or **UID**, and belongs to one or more groups. Each group has a numeric **group ID**, or **GID**. Every process runs *as* some UID and GID, and every file has an owner and a group. The kernel makes access decisions by comparing these numbers with permission bits stored on files. The special account **root** has UID 0, and it bypasses most permission checks.

Why have users at all? **Users exist to provide permissions and boundaries.** Every user-space process has an owner, and it is said to run as that user. A user can end or alter their own processes within limits. But they cannot interfere with other users' processes, and users own files and choose whether to share them. Besides the accounts for human beings, a system has several service accounts, covered in chapter 1.6. The one to know now is `root`, the **superuser**. It is an exception to these rules. The `root` user can terminate or alter any process and read any file on the local system. That is why a person who can act as root is the system's administrator.

Operating as root is dangerous. The system will let you do anything, even if it is destructive, and mistakes are hard to spot. System designers therefore keep working to make root access unnecessary. For example, an ordinary user can switch Wi-Fi networks without root. Groups are sets of users, used mostly to share file access among members.

You will learn permissions properly in chapter 1.6. For now, remember two things. *Processes have an identity*, which comes from whoever started them. *The kernel enforces access on numbers, not names.* So keep numeric UIDs identical across all nodes of a cluster. That way Slurm's munge authentication and shared filesystems agree on who owns every file and job.

## 5. Seeing it with your own eyes

Reading about layers is not enough. You need to see them on a real machine. Every command below targets a live Linux VM, so each one is marked `(untested here)`. The deterministic model checks run locally instead, in `code/part01/linux_layers_lab.py`.

### 5.1 What machine and which kernel is this?

```bash
uname -a            # (untested here) kernel name, node name, kernel release, architecture
cat /etc/os-release # (untested here) which distribution and version this is (the user-space side)
lscpu | head -20    # (untested here) CPU model, sockets, cores, threads, NUMA nodes
free -h             # (untested here) RAM and swap, human-readable
lsblk               # (untested here) block devices: disks, partitions, mount points
ip -br addr         # (untested here) network interfaces and addresses
```

Two of these commands answer different questions, and you should read both. `uname -r` prints the **kernel release**, such as `6.8.0-1020-gcp`. That version tells you which kernel is running. `/etc/os-release` names the **distribution**, such as Ubuntu 24.04 or Rocky Linux 9. These are separate facts. You can update one without the other, and mismatches between them cause real trouble.

### 5.2 What is running, and in what tree?

```bash
ps -ef --forest | head -40     # (untested here) every process, drawn as a tree (PID, parent PID)
pstree -p | head -30           # (untested here) the same tree, compact
ps -eo pid,ppid,user,stat,comm | head   # (untested here) chosen columns
ls /proc/1                     # (untested here) PID 1's "files": cmdline, status, maps, fd, ns ...
cat /proc/1/cmdline | tr '\0' ' '; echo # (untested here)
```

Look for PID 1, which is `systemd` or `init`. If you find it, you have the root of the tree. Then look for processes in square brackets, such as `[kthreadd]` and `[kworker/0:0]`. Those are kernel threads. Everything else descends from PID 1. The `STAT` column tells you what each process is doing. `S` means sleeping, and `R` means running. `D` marks uninterruptible sleep, where a process waits on I/O. `Z` marks a zombie, a process that finished but has not yet been collected by its parent.

### 5.3 Watch a command start: `strace`

```bash
sudo apt-get install -y strace     # (untested here) Debian/Ubuntu; use dnf on Rocky/RHEL
strace -f -e trace=execve,clone,clone3,wait4,exit_group bash -c 'ls /tmp > /dev/null' 2>&1 | head -30 # (untested here)
```

You should see four things. The shell calls `clone` or `clone3`. A child calls `execve("/usr/bin/ls", ...)`. The child exits with `exit_group`, and the parent waits with `wait4`. Want every call? You can drop the `-e trace=` filter and send the output to a file. The opening lines show the dynamic loader at work. It maps the C library, reads `/etc/ld.so.cache`, and calls `mmap` for memory before the real work starts. Reading even a few dozen lines of `strace` output for a simple program is the best habit you can build for understanding Linux.

### 5.4 Watch the kernel/user boundary yourself

Write the smallest program that makes a system call, compile it, and trace it.

```bash
cat > hello.c <<'EOF'
#include <unistd.h>
int main(void) { write(1, "hello from user space\n", 22); return 0; }
EOF
gcc -static -o hello hello.c && strace ./hello # (untested here)
```

The static build keeps the trace tiny. You will see `execve`, a few memory calls, the `write(1, "hello from user space\n", 22)` request to the kernel, and then `exit_group`. Drop `-static` to watch the dynamic loader join in. This shows, without any trust required, that *a program is just a sequence of ordinary computation and system calls*.

### 5.5 Where do devices and kernel modules show up?

```bash
ls /dev | head -30            # (untested here) device files (null, zero, tty, sda or nvme0n1, ...)
lsmod | head                  # (untested here) kernel modules currently loaded into the running kernel
modinfo nvme 2>/dev/null | head -5   # (untested here) details of a module
dmesg | tail -20              # (untested here) kernel log ring buffer (may need sudo)
```

On a GPU machine, the output adds more. You will see `/dev/nvidia0`, `/dev/nvidiactl` and `/dev/nvidia-uvm` in the device list. You will also see `nvidia`, `nvidia_uvm` and `nvidia_modeset` in the `lsmod` output. Whenever a user-space tool reports that no GPUs are present, check `lsmod` and `/dev/nvidia*` first.

## 6. Distributions: Linux is a kernel, not a system

Start with a little history, because it explains the standards and the two threads behind Linux. The UNIX operating system was developed at AT&T. After AT&T's breakup, the trademark and the rights to the original source code changed hands several times. Since 1993, the trademark and the right to certify compliance have been held by the X/Open consortium. It is now **The Open Group**, which develops the **Single UNIX Specification**. POSIX is the core of that specification.
Only systems certified against it, such as Solaris and AIX, may be *called* UNIX. Systems that did not seek certification, Linux among them, deliberately follow the same standards. Programs written to the standard interfaces and libraries therefore port between them easily. That portability, together with UNIX's earlier popularity, helped the family win leadership on servers. Its successors include Solaris, OpenBSD, FreeBSD, AIX and Linux. Today, **Linux is the de facto standard for clusters and supercomputers**.
The creation of Linux itself weaves together two historical threads from the 1980s and early 1990s. The first thread started in the early 1980s, when Richard Stallman launched the **GNU Project** to build a completely free Unix-like operating system. The name GNU is a recursive acronym for *GNU's Not Unix*. Stallman's **GNU General Public License**, or **GPL**, grew out of this work. The GNU Project wrote free versions of almost all essential Unix user-space utilities, compilers, and libraries. Its own kernel, called **GNU Hurd**, never gained momentum.

The second thread began in 1991, when Linus Torvalds started writing a free **MINIX** clone. No free Unix kernel was readily available at the time. His kernel, named **Linux**, rapidly attracted contributors around the world. It was licensed under the GNU GPL in 1992 with the release of version 0.99. Combining Torvalds's Linux kernel with the GNU Project's user-space software collection produced a complete operating system. That is why organizations such as Debian sometimes call the full system **GNU/Linux**. You may see both names, and they refer to the same system.

A **distribution**, or **distro** for short, bundles the Linux kernel with a selection of open-source utilities. It also adds a C library, an init system, a **package manager**, configuration defaults, and a support policy. Early distributions like Slackware pioneered this packaging. When you choose a distribution, you choose all five parts at once. Today, almost every server and cluster you touch in AI infrastructure belongs to one of two major distribution lineages.

```mermaid
flowchart LR
  subgraph Distro["A Linux distribution bundles these five parts"]
    K["Linux kernel build<br/>+ modules"]
    C["C library, core tools,<br/>shell, systemd"]
    P["Package manager<br/>apt, dnf, zypper"]
    S["Services and defaults<br/>networking, logging"]
    D["Support policy and<br/>release schedule"]
  end
  K --- C --- P --- S --- D
```

### 6.1 The Red Hat, Fedora, CentOS, and Amazon Linux branch

Red Hat became the first major commercial success in the Linux market with **Red Hat Enterprise Linux**, or **RHEL**. Enterprise and HPC data centers prize it for multi-year stability, vendor certifications, and commercial support contracts. Fast-moving upstream kernel development clashes with the slow, careful stability that RHEL customers need. So Red Hat sponsors **Fedora** as an upstream distribution. New kernels, package tools, and system features land in Fedora first. Developers and the open-source community vet them there, and they later flow downstream into RHEL.
The GNU GPL requires Red Hat to publish the source code of RHEL. Community engineers used that source to rebuild RHEL as **CentOS**, short for *Community Enterprise OS*. CentOS was a free, binary-compatible clone of RHEL without paid support. In late 2020, Red Hat shifted CentOS into **CentOS Stream**, a "midstream" distribution. It sits between upstream Fedora and downstream RHEL. Organizations that wanted a strict downstream binary rebuild of RHEL created **AlmaLinux** and **Rocky Linux** as direct CentOS replacements.

AWS also builds **Amazon Linux** in this family. It launched in September 2011 and was succeeded by **Amazon Linux 2** in 2018. Next came **Amazon Linux 2022** and **Amazon Linux 2023**, which draw from Fedora, CentOS Stream, and RHEL sources. Other members include Oracle Linux and Scientific Linux.

Every distribution in this branch uses the **RPM** format, and its package files end in `.rpm`. The name comes from the original Red Hat Package Manager utility, `rpm`. While `rpm` installs individual package files, modern Red Hat derivatives use higher-level dependency resolvers that pull from online repositories. The first of these was `yum`, short for *Yellowdog Updater, Modified*. Today it is `dnf`, short for *Dandified YUM*.

### 6.2 The Debian and Ubuntu branch

**Debian GNU/Linux** was founded by Ian Murdock in 1993. It received early sponsorship from the Free Software Foundation's GNU Project from November 1994 through November 1995. Debian remains the only major Linux distribution governed entirely by a community project rather than a corporate parent. Every Debian release since version 1.1 in June 1996, code-named *Buzz*, is named after a *Toy Story* character. Examples include Debian 11.0 *Bullseye*, released in August 2021, and Debian 12 *Bookworm*. Debian maintains three branches: `unstable` (always named *Sid*), `testing`, and `stable`. Packages mature through `unstable` and `testing` before they freeze into a rock-solid `stable` release. That makes Debian a favorite base for other distributions, including NVIDIA's Cumulus Linux on network switches.

The most widely deployed Debian derivative in AI infrastructure is **Ubuntu**. Mark Shuttleworth's company **Canonical** started it in April 2004. Ubuntu's first release came in October 2004 as version 4.10, where 4 stands for the year 2004 and 10 for October. It was code-named *Warty Warthog*, and later releases followed with alliterative animal names such as *Hoary Hedgehog* and *Breezy Badger*. Ubuntu pulls packages from Debian's `unstable` branch. It ships a regular release every six months, plus a **Long-Term Support (LTS)** release every two years. Each LTS release is supported for at least five years. NVIDIA's **DGX OS** is built directly on Ubuntu LTS.
All Debian and Ubuntu systems share the `.deb` package format. `dpkg` manages that format at the low level. `apt`, `apt-get`, and `aptitude` manage it at the repository and dependency level. `aptitude` replaced the older `dselect` tool.

The table compares the three families. Its last column shows where each one appears in your clusters. Notice that each family pairs its package format with its own tools, so learn the tools for the family you run.

| Family | Examples | Package format & tools | Where you meet it in AI infrastructure |
|---|---|---|---|
| Debian and Ubuntu | Debian, Ubuntu LTS, DGX OS, Cumulus Linux | `.deb` via `dpkg` and `apt` | NVIDIA DGX OS, Cumulus switches, cloud GPU images, and container base images |
| Red Hat family | RHEL, Fedora, CentOS Stream, Rocky Linux, AlmaLinux, Amazon Linux | `.rpm` via `rpm`, `yum`, and `dnf` | Enterprise HPC clusters, Slurm supercomputers, and NVIDIA Base Command Manager nodes |
| SUSE | SLES, openSUSE | `.rpm` via `rpm` and `zypper` | European HPC centers and enterprise appliances |

Three practical points will save you hours of cluster debugging.

1. **Same package format does not mean portable packages.** RHEL, Fedora, Rocky, and SUSE all use `.rpm` files. Debian and Ubuntu both use `.deb` files. Even so, you cannot safely install a package built for one distribution on another. Slight differences in package naming, library versions, and file paths make cross-distro binary packages fail dependency resolution or crash at runtime.
2. **Kernel versions are not what they seem.** Enterprise distributions keep an older base kernel version number, but they *backport* security fixes and hardware drivers into it. For example, RHEL 9 reports a `5.14`-series kernel while containing many newer features. Ubuntu ships newer kernels and offers Hardware Enablement kernels, shown as `HWE`, that advance during an LTS lifecycle. Always check `uname -r` and your vendor's support matrix before installing GPU or InfiniBand drivers.
3. **The kernel and user space move independently, with two strict asymmetries.** The Linux kernel strictly obeys the rule "never break user space," so old user-space binaries almost always keep running on newer kernels. The reverse fails in two ways. First, *user-space programs compiled against a newer `glibc` will fail to start on an older distribution*. Second, *kernel modules (`.ko`) compiled for one kernel build will refuse to load on another*. Standardise a single tested OS release across every node in a cluster.

Want a deeper sysadmin library to go with this handbook? Sergey Zhumatiy's *Supercomputers for Linux SysAdmins* recommends four timeless companions. The first is *UNIX and Linux System Administration Handbook*, by Evi Nemeth, Garth Snyder, Trent Hein, and Ben Whaley. The second and third are *The Practice of System and Network Administration*, by Thomas Limoncelli, Christina Hogan, and Strata Chalup, and Limoncelli's *Time Management for System Administrators*. The fourth is Brian Kernighan and Rob Pike's classic *The UNIX Programming Environment*.
## 7. Putting a GPU node on the map

Now apply the layered picture to the machine you will actually work on. It is a server with GPUs, InfiniBand adapters, and a Kubernetes or Slurm agent. Every layer below has a role on that box.

```mermaid
flowchart TB
  subgraph US["USER SPACE"]
    direction LR
    JOB["Training job<br/>python + PyTorch"]
    CUDA["CUDA libraries<br/>libcuda.so, libcudart, NCCL"]
    RDMA["RDMA libraries<br/>libibverbs, UCX"]
    CTR["Container runtime<br/>containerd, runc"]
    AGENT["Agents<br/>slurmd, kubelet, dcgm"]
    SYSD["systemd, sshd"]
  end
  subgraph KS["KERNEL SPACE"]
    direction LR
    SCH["Scheduler"]
    VM["Memory manager"]
    NSCG["Namespaces and cgroups"]
    NETK["Network stack"]
    NVK["NVIDIA kernel modules<br/>nvidia, nvidia_uvm"]
    IBK["RDMA kernel drivers<br/>mlx5_core, ib_core"]
    NVMEK["NVMe & FS drivers"]
  end
  subgraph HW["HARDWARE"]
    direction LR
    G["GPUs & NVLink"]
    H["ConnectX HCAs"]
    N["NVMe drives"]
    CPUs["CPUs, RAM, NUMA"]
  end
  JOB --> CUDA --> NVK
  JOB --> RDMA --> IBK
  CTR --> NSCG
  AGENT --> NSCG
  NVK --> G
  IBK --> H
  NVMEK --> N
  SCH --> CPUs
```

The table below lists each component with its layer, its role, and the boundary where its failures show up, so you know where to look first.

| GPU Node Component | Layer | Exact Role and Failure Boundary |
|---|---|---|
| `nvidia.ko`, `nvidia_uvm.ko`, `nvidia_peermem.ko` | Kernel space | Own the GPU hardware, manage GPU virtual memory page faults, and expose `/dev/nvidia*` character devices |
| `libcuda.so`, `libnvidia-ml.so` (`nvidia-smi`) | User space | Ship with the driver; translate CUDA Driver API and NVML calls into `ioctl` system calls on `/dev/nvidia*` |
| `libcudart.so`, `cuBLAS`, `cuDNN`, `NCCL` | User space | CUDA Toolkit and math/collective libraries; run in user space inside the job or container |
| `mlx5_core.ko`, `ib_core.ko` | Kernel space | Own the ConnectX NIC/HCA, register pinned memory, and set up RDMA queue pairs |
| `libibverbs.so`, `UCX` | User space | Post RDMA work requests directly to adapter hardware from user space (kernel bypass for data) |
| `containerd`, `runc`, `slurmd`, `kubelet` | User space | User-space daemons that ask the kernel to isolate and limit jobs via namespaces and cgroups |

Treat this map as a lookup table. The points below explain the parts that most often confuse people.

- **The NVIDIA driver has two halves.** The *kernel modules*, such as `nvidia.ko` and its friends, run in kernel mode. They own the GPU and create `/dev/nvidia*`. The *user-space libraries* are what your programs link against. They include `libcuda.so` and `libnvidia-ml.so`, which `nvidia-smi` uses. These libraries talk to the kernel half through `ioctl` system calls on those device files. The two halves must be compatible versions. That is why a "driver/library version mismatch" happens when the kernel module is not reloaded after an upgrade.
- **CUDA toolkit libraries and cuDNN are pure user space.** They do not need the kernel to change. You can run several toolkit versions side by side in different containers, as long as the host *driver* is new enough for them.
- **Containers are not virtual machines.** A container is an ordinary set of user-space processes. The kernel isolates it using **namespaces**, which give each container a separate view of processes, network, and mounts. It limits the container using **cgroups**. All containers on a node *share the host's kernel*. So a container can see GPUs only if the host has the driver and the device files are passed in. The kernel version on the node, not the one in the container image, determines which kernel features exist. Chapters 1.18 to 1.20 build this from scratch.
- **RDMA bypasses the kernel for data, not for setup.** The kernel driver sets up resources such as queues and memory registrations. Then the application, using `libibverbs`, talks to the adapter directly from user space. That "kernel bypass" is why InfiniBand achieves low latency. It is also why standard Linux packet capture tools like `tcpdump` cannot see RDMA payload traffic. If you run it on that path, you will not see the payload.
- **`slurmd` and `kubelet` are just user-space programs.** They are not part of the kernel. They ask the kernel, through system calls, cgroup files, and namespaces, to start and limit jobs. When you wonder who is in charge of a job, the answer is a user-space daemon *using* kernel features.

**In one minute:** every GPU node splits into three parts. There is hardware. There is kernel space, with `nvidia.ko`, `mlx5_core.ko`, namespaces and cgroups. And there is user space, with `libcuda.so`, `pytorch`, `containerd`, `slurmd` and `kubelet`. Containers bring their own user space, but they always share the host kernel. When your container cannot see a GPU, check the host driver first.

## 8. How it fails: six classic confusions

Each of these is a real incident pattern. Before you touch anything, ask which layer the failure lives in.

### 1. "I updated the kernel and the GPU disappeared"
**Symptom:** after an OS update and reboot, `nvidia-smi` fails with "couldn't communicate with the NVIDIA driver." **Cause:** the NVIDIA kernel modules were built for the old kernel. On the new kernel they are missing, or they will not load, because kernel modules are tied to one specific kernel build. **Diagnose:** `uname -r`, `lsmod | grep nvidia`, `dmesg | grep -i nvidia`, `modinfo nvidia | grep vermagic`. **Fix:** install modules that match the running kernel, using prebuilt packages or DKMS. You can also boot the old kernel. In production, pin kernels and update them in a tested image, never ad hoc. If you see this after a reboot, start with `uname -r`.

### 2. "Works in the container, not on the host" (and the reverse): confusing library layers
**Symptom:** your binary fails with `GLIBC_2.xx not found` or `error while loading shared libraries`. **Cause:** programs depend on user-space libraries. A binary built against a newer `glibc` cannot run on a host with an older one. **Diagnose:** `ldd ./binary`, `ldd --version`, `cat /etc/os-release`. **Fix:** build on the oldest distribution you need to support. Or ship the binary in a container that brings its own user space. Or use a matching base image. If you copy a binary between hosts, check both versions first.

### 3. A process that "cannot be killed": state D
**Symptom:** `kill -9` has no effect, and the process shows `D` in `ps`. **Cause:** the process is inside a system call, waiting for I/O on a dead NFS server, a failing disk, or a hung driver. It is uninterruptible by design. **Diagnose:** `ps -eo pid,stat,wchan:30,comm | awk '$2 ~ /D/'`, `dmesg`, and then check the storage or mount. **Fix:** fix the underlying device or mount. No signal works while the kernel is waiting on hardware. This is a *kernel/hardware layer* problem, and no amount of user-space restarting solves it. If you see a D state, stop sending signals and look at the mount.

### 4. "The kernel killed my job": the out-of-memory killer
**Symptom:** a training process vanishes with no error in its own log, and `dmesg` shows "Out of memory: Killed process ...". **Cause:** physical memory plus swap was exhausted. The kernel's OOM killer chose a victim to save the machine. **Diagnose:** `dmesg -T | grep -i -E "killed process|oom"`, `free -h`, and the per-cgroup limits in `memory.max`. **Fix:** reduce memory use, add memory, or set realistic limits. In containers and Slurm, the same event happens at the cgroup limit instead of at whole-machine exhaustion, as chapters 1.17 and 1.18 explain. If you see this in your logs, check the cgroup limit first.

### 5. "Permission denied" versus "No such file": wrong layer of cause
**Symptom:** a command fails with an error that looks like a file problem. **Cause:** these two errors are different system call return codes. `ENOENT` means the path does not exist. `EACCES` means the path exists, but your user ID may not use it. Treating one as the other wastes hours. **Diagnose:** `strace -f -e trace=openat,execve program 2>&1 | grep -E "ENOENT|EACCES"`, `ls -l`, `id`. **Fix:** correct the path, or correct the permissions, ownership, or SELinux label, as the error requires. Read the error code before you change anything.

### 6. "It behaves differently on the other cluster": distribution differences
**Symptom:** a script or a package name that works on Ubuntu fails on Rocky. **Cause:** different package managers, package names, default paths, init and firewall defaults, and kernel feature backports cause the difference. **Diagnose:** `cat /etc/os-release`, `uname -r`, and `command -v` for the tool. Then read the distribution's documentation. **Fix:** standardise the OS on the cluster. Write scripts that detect the distribution, or use Ansible from chapters 4.3 onward. Keep a compatibility matrix, and check it before you upgrade.

## Hands-on lab: layer verification and VM tour

Start with the self-checking Python lab. Run it locally before you touch a VM. It verifies layer placement, privilege rules, `fork` and `execve` PID transitions, `4 KiB` virtual page translation, process states, and distribution lineage rules.

```bash
python3 code/part01/linux_layers_lab.py
```

Next, move to an `e2-small` Ubuntu 24.04 VM, or any Linux machine. These steps run on live cloud hardware, so they are untested here. Work through them in order. Keep notes as you go, so you can compare results later.

**Part A: identify the layers.**
1. Run the commands from section 5.1. Record the distribution, the kernel release, the CPU count, and the RAM. Then explain which of those belong to user space, the kernel, and hardware.
2. Run `ps -ef --forest` (untested here). Find PID 1. Find three kernel threads. Find your own shell, and draw its ancestors up to PID 1.

**Part B: watch a program start.**
3. Run the `strace` command from section 5.3. Mark which line creates the child, which line replaces the program, and which line is the exit.
4. Run `strace -c ls /usr/bin > /dev/null` (untested here). This summarises system calls by count and time. Which system call is called most? Why does `ls` need it?
5. Compile and trace the `hello.c` program from section 5.4, with and without `-static`. Compare the length of the two traces. Then explain the difference that the dynamic loader causes.

**Part C: see the privilege boundary.**
6. As a normal user, try to read a protected kernel interface. Start with `cat /proc/kcore | head -c 10` (untested here). Then try `sudo cat /proc/1/maps | head` (untested here). Explain the difference in outcome in terms of user ID and what the kernel allows.
7. Write a program that dereferences a null pointer. Run it, and read the shell's message, `Segmentation fault`. Explain which hardware component noticed the problem, which software component acted, and why the machine was unaffected. The MMU is the hardware, and the kernel is the software.

**Part D: processes and states.**
8. Start `sleep 300 &` (untested here). Then run `ps -o pid,ppid,stat,comm -p $!` (untested here) and `ls -l /proc/$!/` (untested here). Kill it. Next, start `sleep 300`, press Ctrl-Z, and run `ps` again. Note how the state letter changes.
9. Create a zombie on purpose, so you can see state `Z`. Use a short Python snippet that forks a child. The child exits while the parent sleeps without waiting. Explain what a zombie is, and who removes it.

**Part E: distribution awareness.**
10. Run a Rocky Linux container on an Ubuntu host with `docker run --rm -it rockylinux:9 bash` (untested here). Compare `cat /etc/os-release` and the package command, `dnf` versus `apt`. Then run `uname -r` inside the container and on the host. You will see that they are the *same kernel*.

## Exercises

Work through these on paper first, then check your answers. You should answer before you look.

1. **Layer Classification on a GPU Node:** Classify each of the following 8 components as hardware, kernel, or user space. The components are (a) `connectx_hca`, (b) `nvidia.ko`, (c) `nvidia_uvm.ko`, (d) `mlx5_core.ko`, (e) `libcuda.so`, (f) `libibverbs.so`, (g) `systemd`, and (h) `slurmd`. Check your answers with `classify_component_layer()` in `code/part01/linux_layers.py`.
2. **Root (UID 0) versus Kernel Mode (Ring 0):** A system administrator runs a Python script as `root` (UID 0). First, while the Python interpreter executes a normal `for` loop in user space, state which x86 privilege ring (0 or 3) and mode (user mode or kernel mode) the CPU is in. State whether it can execute a privileged CPU instruction directly, without a system call. Second, an ordinary user (UID 1000) invokes the `read()` system call. State which CPU ring and mode the processor switches into while it executes inside the kernel.
3. **Tracing `fork()`/`clone()` and `execve()` PIDs:** Suppose an interactive `bash` shell runs at PID 100 (UID 1000). It launches `/usr/bin/ls`, and the kernel's `clone` call allocates PID 101 to the child process. What is the child process's PID and program image immediately *before* `execve("/usr/bin/ls")`, and immediately *after* it?
4. **Virtual Memory Page Table Translation (4 KiB Pages):** Assume a 4 KiB page size, which is 4,096 bytes. The per-process page table maps virtual page 2 to physical frame 15, and virtual page 3 to physical frame 9. First, calculate the virtual page number, byte offset, and physical RAM address for virtual address 8,320. That address is 2 * 4096 + 128. Second, state what the MMU and kernel do when the process dereferences virtual address 28,736. That address is 7 * 4096 + 64.
5. **Process States (R, D, Z) and `kill -9`:** Two troubled processes appear in `ps`. Process A has `STAT = D`, waiting on an unresponsive NFS mount. Process B has `STAT = Z` (`<defunct>`). Explain why `kill -9` (`SIGKILL`) fails to remove either process immediately. Then state the exact recovery action each one requires.
6. **Distribution Lineages and Container Kernel Sharing:** An Ubuntu 24.04 host runs with `uname -r` = `6.8.0-1020-gcp`. It also runs a Rocky Linux 9 container, where `cat /etc/os-release` shows Rocky Linux 9. (a) What does `uname -r` print inside the Rocky Linux 9 container? Which package manager, `apt` or `dnf`, runs inside the container? (b) Suppose the Ubuntu host updates its kernel to `6.8.0-1021-gcp` and reboots, without building `nvidia.ko` for the new kernel. Can a container with `/usr/local/cuda` installed use the GPUs?

## Checkpoint questions (20)

<details>
<summary>1. What three things does an operating system do for programs?</summary>

It shares hardware resources fairly, by scheduling CPU time and allocating RAM. It protects programs from each other, and it protects the kernel from programs. It also simplifies access to diverse hardware through uniform abstractions, such as files and sockets.
</details>

<details>
<summary>2. Name the three layers of a Linux system and state what runs in each.</summary>

Hardware sits at the bottom. It includes CPU cores, main memory, NVMe disks, network cards, and GPUs. The kernel sits in the middle. It runs the process scheduler, the memory manager, the filesystems, the network stack, and the device drivers. User space sits at the top. It runs applications, shared libraries such as `glibc` and `libcuda.so`, shells, and system services such as `systemd`.
</details>

<details>
<summary>3. Why does the CPU have a privileged mode (ring 0) and an unprivileged mode (ring 3)? What happens if a user program tries a privileged instruction?</summary>

The hardware split lets the kernel enforce isolation. User programs run in unprivileged mode, ring 3, where direct hardware access and page-table changes are forbidden. If a user program runs a privileged instruction, the CPU raises a hardware fault and traps into the kernel. The kernel then terminates that process without harming the rest of the system.
</details>

<details>
<summary>4. What is the difference between "kernel mode" and "root" (UID 0)?</summary>

Kernel mode, ring 0, is a CPU execution state in which kernel code runs. Root, which is `UID 0`, is a user identity in user space. A root process still runs its own instructions in unprivileged user mode, ring 3. To do privileged work, it makes system calls. The kernel grants them because `UID == 0`. If you ever see root in a log, remember it names a user, not a CPU mode.
</details>

<details>
<summary>5. List the four primary jobs of the Linux kernel.</summary>

The four jobs are process management and scheduling, memory management through virtual memory and page tables, device management through device drivers, and serving system calls and kernel support routines. You can test these four ideas on any machine.
</details>

<details>
<summary>6. What triggers a context switch, and what does the kernel do during it?</summary>

A hardware timer interrupt at the end of a time slice triggers a context switch. A blocking system call can trigger one too. Either event switches the CPU into kernel mode. The kernel saves the current process's CPU registers and instruction pointer, then invokes the scheduler to pick the next runnable process. It loads that process's registers and page-table mappings, and returns the CPU to user mode. When you trace a process, look for the timer and the scheduler.
</details>

<details>
<summary>7. Explain virtual memory, the MMU, and page tables in three sentences.</summary>

Every process uses virtual addresses, not physical RAM addresses. On every memory access, the CPU's Memory Management Unit, or MMU, translates the virtual page number, typically a `4 KiB` page, into a physical frame number. It does this using a per-process page table that the kernel maintains. If a virtual page is unmapped, the MMU raises a page fault, and the kernel can allocate memory lazily, swap a page in, or send `SIGSEGV` on an illegal access. For example, when you read a segfault later, the MMU is behind it.
</details>

<details>
<summary>8. What is a pseudodevice? Name four classic Linux pseudodevices and what each does.</summary>

A pseudodevice is a file under `/dev` that the kernel implements purely in software. Nothing physical sits behind it. `/dev/null` discards all writes and returns EOF on read. `/dev/zero` supplies an endless stream of `0x00` bytes. `/dev/random` and `/dev/urandom` provide cryptographic random numbers from the kernel's entropy pool. For example, you can read `/dev/zero` to get zero bytes.
</details>

<details>
<summary>9. What is a system call, and what role does `glibc` (`libc.so.6`) play when your program calls `open()` or `printf()`?</summary>

A system call is the controlled entry point from user space into the kernel. Examples include `openat`, `read`, `write`, `clone`, `execve`, `mmap`, and `ioctl`. Programs normally call wrapper functions in the GNU C library, `glibc`. The wrappers format the arguments and run the architecture's syscall instruction on the program's behalf.
</details>

<details>
<summary>10. Describe step by step what happens from typing `ls` in `bash` to seeing its output. How do `fork()`/`clone()`, `exec()`, and `execve()` fit together?</summary>

First, the shell calls `fork()`, which the `clone` or `clone3` system call implements, to create a child process with a new PID. Next, the child calls a function in the C library's `exec()` family, such as `execl()`, `execv()`, or `execvp()`. That function invokes the kernel's `execve()` system call. It replaces the child's memory image with `/usr/bin/ls` and keeps the same PID. Finally, `ls` opens and reads the directory with `openat` and `getdents64`. It writes its output with `write()` and exits with `exit_group(0)`. The parent shell collects the exit status with `wait4()`.
</details>

<details>
<summary>11. Why are processes arranged in a tree, and what is special about PID 1?</summary>

Every process after boot is created by an existing parent that calls `clone()` or `fork()`. That is why processes form a tree. PID 1 is `init`, which is `systemd` on modern distributions. It is the first user-space process the kernel starts. It is the ancestor of all other user-space processes, and it adopts orphaned children whose parent has exited.
</details>

<details>
<summary>12. How did the GNU Project (1980s) and Linus Torvalds's 1991 kernel come together to form GNU/Linux?</summary>

Richard Stallman started the GNU Project, "GNU's Not Unix", in the early 1980s. He also created the GPL and user-space Unix utilities. But the project's kernel, `GNU Hurd`, stalled. In 1991, Linus Torvalds wrote a free, MINIX-inspired kernel called `Linux`. He licensed version `0.99` under the GNU GPL in 1992. Combined with the GNU user space, it formed a complete operating system.
</details>

<details>
<summary>13. Why is Linux central to modern data center switches as well as servers?</summary>

Modern network operating systems run on Linux. The OpenCompute Project's Open Network Linux, `ONL`, powers Switch Light and `dentOS`. NVIDIA's Cumulus Linux is a full Debian-based distribution that runs on Spectrum switches. `SONiC`, which stands for Software for Open Networking in the Cloud, runs Linux and containers on white-box switches across hyperscale fabrics.
</details>

<details>
<summary>14. How do Fedora, CentOS Stream, RHEL, and Rocky Linux / AlmaLinux relate to each other?</summary>

Fedora is Red Hat's fast-moving upstream distribution, where new kernels and features are tested first. CentOS Stream sits midstream, between Fedora and Red Hat Enterprise Linux, the commercial enterprise release. Rocky Linux and AlmaLinux are downstream community distributions. They are rebuilt from RHEL's GPL source code, after CentOS shifted to CentOS Stream in late 2020.
</details>

<details>
<summary>15. How do Debian's three branches (`unstable`, `testing`, `stable`) relate to Ubuntu's release cadence and NVIDIA DGX OS?</summary>

Debian was founded by Ian Murdock in 1993 and uses *Toy Story* codenames, such as `1.1` *Buzz* and `11.0` *Bullseye*. It moves packages from `unstable` through `testing` into `stable`. Ubuntu, started by Canonical in 2004 with `4.10` *Warty Warthog*, pulls from Debian `unstable`. If you run DGX OS, you are running on Ubuntu LTS. It ships six-month releases and two-year LTS releases, which are supported for five years. NVIDIA's DGX OS is built on Ubuntu LTS.
</details>

<details>
<summary>16. Why can't you reliably install a Fedora `.rpm` on Rocky Linux or an Ubuntu `.deb` on Debian even though they share the same package format?</summary>

Sharing the `.rpm` or `.deb` container format does not guarantee binary or dependency compatibility. The `.rpm` tools are `rpm`, `yum`, and `dnf`. The `.deb` tools are `dpkg` and `apt`. If you mix package files, you should expect failures. Shared library versions, such as `glibc` and `libssl`, can differ between distributions. So can package naming conventions and filesystem paths. Those differences cause dependency resolution failures or runtime crashes.
</details>

<details>
<summary>17. The NVIDIA GPU driver has a kernel half and a user-space half. Name the files in each half and explain how they communicate.</summary>

The kernel half is made of kernel modules: `nvidia.ko`, `nvidia_uvm.ko`, and `nvidia_peermem.ko`. They run in ring 0 and expose `/dev/nvidia*`. The user-space half is made of the libraries `libcuda.so` and `libnvidia-ml.so`, plus the `nvidia-smi` tool. These talk to the kernel modules through `ioctl` system calls on `/dev/nvidia*`. For example, when your job opens `/dev/nvidia0`, the kernel driver answers.
</details>

<details>
<summary>18. Why does a kernel module (`.ko`) built on one kernel refuse to load on another, whereas old user-space binaries keep working on newer kernels?</summary>

The Linux kernel keeps a strict, stable ABI for system calls. That is the rule "don't break userspace," so old user binaries keep working. Inside the kernel, however, internal data structures and function signatures change between builds. So `.ko` modules are version-checked, through `vermagic`, against the exact kernel release from `uname -r` they were compiled for. So when you rebuild a kernel, rebuild its modules too.
</details>

<details>
<summary>19. Why does `tcpdump` fail to see InfiniBand or RoCEv2 RDMA payload traffic on a GPU node?</summary>

RDMA uses the kernel, through `mlx5_core` and `ib_core`, only during setup. The kernel registers pinned memory and creates queue pairs. After that, `libibverbs` in user space posts work requests directly to the ConnectX adapter. This is kernel bypass. The payload never crosses the Linux TCP/IP and netfilter stack, so `tcpdump` hooks never see it. For example, if you debug RDMA, look at the adapter path rather than `tcpdump`.
</details>

<details>
<summary>20. Why does `kill -9` fail on a process in state `D`, and how is state `D` different from state `Z`?</summary>

A process in state `D`, uninterruptible sleep, is inside the kernel. It waits on hardware or network storage I/O, such as a dead NFS or Lustre mount. Signals are not delivered until that system call returns, so `kill -9` has no effect. A process in state `Z`, a zombie, has already terminated and released its memory. Only its process-table entry remains, until its parent calls `wait4()`. If you see state `D`, check the storage mount before you try a signal.
</details>

## Sources and review notes

- **Sources read in full:**
  - `how-linux-works-3rd-edition` — Brian Ward, *How Linux Works*, 3rd ed., **Chapter 1: The Big Picture**. Read sections 1.1–1.6 in full. Covers levels and layers of abstraction, hardware and main memory state/image, the kernel's four tasks, context switches, virtual memory and page tables, device drivers and pseudodevices, `fork()` and `exec()`/`execve()` system calls, Silberschatz *Operating System Concepts* 10th ed. and Love *Linux Kernel Development* 3rd ed. references, user-space layering, and users/groups/root.
  - `network-programmability-and-automation-2nd-edition` — Jason Edelman, Scott S. Lowe, and Matt Oswalt, *Network Programmability and Automation*, 2nd ed., **Chapter 3: Linux**. Read "Examining Linux in a Network Automation Context", "Exploring a Brief History of Linux", and "Understanding Linux Distributions" in full. Covers OCP Open Network Linux (ONL), Switch Light, dentOS, NVIDIA Debian-based Cumulus Linux, SONiC, eBPF/XDP, Richard Stallman's 1980s GNU Project and GPL vs Linus Torvalds's 1991 Linux kernel v0.99 in 1992, Red Hat/Fedora/CentOS Stream/RHEL/AlmaLinux/Rocky Linux/Amazon Linux 2 & 2022 with `rpm`/`yum`/`dnf`, and Debian 1993 Ian Murdock / 1.1 *Buzz* 1996 / 11.0 *Bullseye* 2021 / Ubuntu 4.10 *Warty Warthog* Oct 2004 with `dpkg`/`dselect`/`apt`.
  - `supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to` — Sergey Zhumatiy, *Supercomputers for Linux SysAdmins*, **Chapter 7: UNIX and Linux – the Basics**. Read UNIX/POSIX standards history (1993 X/Open / The Open Group Single UNIX Specification), UID/GID privilege model, and classic sysadmin book recommendations (Nemeth et al., Limoncelli et al., and Kernighan & Pike).
  - `systems-performance-2nd-edition` — Brendan Gregg, *Systems Performance*, 2nd ed., **Chapter 3: Operating Systems**. Cross-checked kernel vs user mode, system calls, interrupts, context switches, and virtual memory.
- **Run here:** `python3 code/part01/linux_layers_lab.py` (26 passed, 0 failed).
- **Explicitly labelled inferences:** The EEVDF scheduler note (Linux kernel 6.6 onward) and x86 ring 0 / ring 3 terminology are standard architecture background alongside the cited books.
- **Not verified on live hardware:** All interactive VM shell commands (`uname -a`, `ps`, `pstree`, `strace`, `gcc -static`, `lsmod`, `modinfo`, `dmesg`, `docker run`) are marked (untested here) and should be executed on a Linux VM.
