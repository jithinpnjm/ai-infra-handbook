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

Picture your first week on an AI infrastructure team. A training job that ran all weekend has slowed to a crawl on Monday morning. A container starts on every node except one. A colleague glances at an error message and says, "that looks like a user-space problem, not a GPU driver problem." If you cannot yet tell one layer of the system from another, you will spend the whole day guessing. This chapter exists so that you never have to guess.

![Three stacked layer boxes, user space on top of the kernel, with hardware at the bottom.](./img/g-0.jpg)
*Figure 1.1.1. Knowing which layer failed stops you from guessing.*


The first thing worth knowing surprises people new to the field. Every machine in an AI factory runs Linux. The GPU servers run it. The Slurm controller runs it, and so do the Kubernetes nodes and the storage servers. The companion hosts next to the BMCs run it. Even the data center switches run it. Open a modern leaf or spine switch on an AI fabric and you will find a full Linux distribution inside, driving the switching silicon. That is not a curiosity; it means a network fault can turn out to be a Linux fault. The OpenCompute Project builds Open Network Linux, or ONL, which underpins Big Switch's Switch Light and the DENT Project's dentOS. NVIDIA ships Debian-based Cumulus Linux on its Spectrum Ethernet switches. Microsoft, Intel, NVIDIA, Broadcom, and Dell collaborate on SONiC, which stands for Software for Open Networking in the Cloud. Your automation tools, Ansible and Python, also run from Linux control hosts. And kernel technologies such as eBPF and XDP are reshaping high-speed networking, security, and observability right now.

So when something breaks, the cause lives in one specific layer of one specific Linux system. You can find that layer quickly only if you can name the layers and say what each one does. Inside each component there is a tremendous amount of detail, and we will set that detail aside for the moment. The goal here is more modest: understand what each component does for the whole system.

That is what this chapter gives you: a high-level map of a Linux system. Everything later in the handbook, cgroups, namespaces, Kubernetes pods, GPU drivers, and RDMA, sits somewhere on that map. We start at the very beginning, and we assume nothing.

If you have used Linux for years but never learned *how it is put together*, this chapter is for you. You do not need to memorise commands. You need a clear picture in your head, so that when something fails you can say with confidence: this is a kernel problem, that is a user-space problem, and this other thing is a hardware problem.

## Prerequisites and outcomes

Before you start, you need only two things: a terminal on any Linux machine, and a willingness to type commands. By the end of the chapter you will be able to do the following:

- Explain what an operating system does, in plain words, using the three-layer model of hardware, kernel, and user space.
- Explain the difference between kernel mode and user mode, and why that boundary exists.
- Describe the four jobs of the kernel: running processes, managing memory, managing devices, and serving system calls.
- Explain what a process is, trace what happens when you type a command with `fork` or `clone` and `exec`, and watch it happen with `strace`.
- Explain what Linux is as a kernel, what a distribution is as a kernel plus everything else, and how the Red Hat and Debian families evolved.
- Place the NVIDIA driver, CUDA, the container runtime, `slurmd` and RDMA correctly on a layered diagram of a GPU node.
- Use a short set of commands to inspect any Linux machine, and recognise six classic confusions that come from mixing up the layers.

## 1. What an operating system is for

Picture a GPU server with several training jobs running at once. Each job wants CPU cores, memory, disks, and GPUs, and it wants them all the time. The machine, however, has only one set of each. Something has to hand those resources out and settle the arguments. That something is the operating system.

To see why you cannot do without it, imagine the machine with nothing in charge. Every program would need to know how to talk to every kind of disk and every kind of network card on its own. Programs could read and overwrite each other's memory, by accident or on purpose. One runaway program could freeze the whole machine, and everyone else's work with it.

An **operating system**, or **OS** for short, is the software that sits between programs and hardware. It solves exactly these problems. It does three things:

1. **Shares** the resources fairly. It decides which program runs on which CPU core and for how long. The shared resources are processor cores, memory, storage, network cards, and GPUs.
2. **Protects** programs from each other, and protects itself from programs. One crashing program must not take down the others.
3. **Simplifies** access to hardware. A program asks to "write these bytes to this file" and does not care whether the disk is an SSD, a network drive, or something else.

A good mental picture is a large office building. The people inside are the programs. The property manager handles the building itself. That manager allocates rooms, which is memory. The manager schedules the shared meeting rooms, which is CPU time. The manager decides who may enter which floor, which is protection. And the manager runs the plumbing and electricity, so a tenant can turn on a tap for hardware access without rewiring anything. Tenants never touch the building directly. They make requests at the front desk. In Linux, the property manager is the **kernel**, and the front desk is the **system call interface**. Keep the building in mind, because we will come back to it.

![A cross-section of an office building. Programs are tenants on the upper floors. They queue at a ground-floor front desk labelled System calls. Behind it the kernel manages memory keys, a CPU time schedule and a protection door. Hardware (CPU, disks, network, GPU) runs in the basement.](./img/ch01-fig1-office-building.jpg)

*Figure 1.1.2. The operating system as an office building: programs are tenants, the front desk is the system call interface, and the kernel manager hands out memory and CPU time and enforces protection.*

## 2. The three layers

Suppose a GPU job crashes with an error. Your first question is where the fault lives. Almost everything you will ever debug on Linux fits on the picture below.

![The three layers](./img/ch01-d1-luna.svg)

*Figure 1.1.3. The three layers.*

Read the picture from the bottom up, the way work actually travels.

**Hardware** is the physical machine. At the bottom sit the CPU cores, the parts that actually execute instructions. Next to them sits **main memory**, which engineers call RAM. Main memory holds the programs and data that are currently running. Around these two sit devices: storage, network cards, and GPUs.

One fact about hardware is worth stopping for. *The CPU only ever works on data that is in main memory.* Whatever the CPU touches, it touches in RAM. A program on disk, a network packet that just arrived, a file you are reading: while the CPU works on any of them, it is a sequence of bytes in RAM. Disks, networks, and GPUs are, from the CPU's point of view, places to move bytes to and from RAM. Keep that picture, because it will make virtual memory feel natural a few sections from now.

Before we move up a layer, one word needs a home in your head, because you will hear it constantly: **state**. Strictly speaking, a state is one exact arrangement of bits. Four bits holding 0110, 0001, and 1011 are three different states. A running process or the kernel spans millions of bits, so nobody describes state at that scale. People describe it in plain terms instead: "the process is waiting for input", or "the process is in stage 2 of startup". Think of it like a paused board game. What matters is not the plastic and cardboard, but the exact position of every piece at the moment you paused. The complete physical arrangement of bits that makes up a running program or the kernel is sometimes called its **image**. Nearly everything the kernel does revolves around main memory. It divides memory into pieces, tracks the state of every piece at all times, and makes sure each process stays inside its own share.

**The kernel** is, in one respect, a program like any other: a large piece of software loaded into memory. Two things make it special. It is the first piece of the OS to start when the machine boots, and it stays in place until shutdown. And the CPU runs it in a **privileged mode**, which lets it touch all memory and all hardware. This is the property manager from our building, now in real form.

**User space** is everything else: every program you have ever run, from `ls` to a PyTorch training job to a database. Programs in user space run in an **unprivileged mode**. They cannot touch hardware directly, and each one can see only its own memory. When a program needs something only the kernel may provide, opening a file, sending a packet, starting another program, asking for more memory, it walks to the front desk. That front desk is the **system call**: a controlled request through a defined doorway. The kernel checks the request, performs it, and hands the result back.

User space is not one lump. Its programs fall into a **rough layering**. At the bottom sit *basic services*: small components that do one uncomplicated job, such as a logging daemon. In the middle sit *utility services*: larger components such as mail, printing, a database, or a DNS cache that other programs use. At the top sit *applications*, the programs users touch directly, such as a browser or a training script. A component generally uses components at its own level or below.

Treat that layering as a sketch, not a law, because **user space has no real rules**. Most programs write diagnostic messages through the standard `syslog` service, yet some do their own logging. A database server can be called a high-level application, because its task is complicated. It can just as fairly be called a middle-level service, because applications depend on it. Both descriptions are correct. From the kernel's point of view all processes are equal; the layers are a human way to reason about dependencies. Along the way you will also hear the informal word **userland**, which means user space, or sometimes the programs in it.

### Why two modes? Kernel mode and user mode

![Concentric rings showing Ring 3 user mode and Ring 0 kernel mode, illustrating how CPU hardware traps illegal privileged instructions to protect the system.](./img/p4-0101-cpu-rings.svg)

*Figure 1.1.4. The CPU hardware boundary: user processes run in Ring 3 and trap into Ring 0 via system calls, while illegal privileged instructions trigger hardware faults that terminate the rogue process without halting the system.*

You might wonder who stops a program from simply ignoring these rules. Nobody's honor is required, because modern CPUs build the split into the hardware. A CPU can run in at least two privilege levels. On x86 processors, people traditionally call them **ring 0** and **ring 3**. Ring 0 is the most privileged level, and the kernel runs there. Ring 3 is the least privileged level, and your programs run there. In ring 0, the CPU allows the dangerous instructions: the ones that control memory protection, talk to devices, and handle interrupts. In ring 3, those same instructions are refused. If a normal program tries one, the CPU raises a fault and hands the case to the kernel. The kernel then decides what to do, and usually it kills the offending program.

![Infographic titled Kernel mode and user mode. The kernel runs in the inner ring 0 and programs run in the outer ring 3. When a program attempts a privileged instruction the CPU refuses it, raises a fault and hands it to the kernel, which usually kills the program. A user-space crash lets the rest of the system continue, while a kernel bug can stop the whole machine.](./img/ch01-fig2-kernel-user-mode.jpg)

*Figure 1.1.5. Kernel mode and user mode. A privileged instruction tried from ring 3 triggers a fault that the kernel handles, and the program is usually killed.*

This boundary buys you a property you rely on every single day. **If a user-space program crashes, the kernel cleans it up and the rest of the system continues.** A buggy Python script can die without corrupting the kernel's memory or another user's process. The reverse is why kernel problems are more serious: a bug *inside* the kernel can bring down the whole machine. That includes a bug in a kernel module, such as a GPU driver, because that code runs in kernel mode. When the kernel itself concludes it cannot safely continue, the machine stops with a "kernel panic".

Two details are worth knowing now, because they appear again later:

- **Kernel threads.** The kernel runs its own background workers, called kernel threads. You will see names like `kthreadd`, `kworker`, and `ksoftirqd` in the process list, enclosed in square brackets. They look like processes, but they live entirely inside the kernel.
- **Privilege is not the same as being `root`.** `root` is a *user account* that the kernel lets ask for almost anything. A root process still runs in unprivileged *CPU mode*; the kernel simply chooses to say yes to its requests. Keep kernel mode and root apart: kernel mode is a CPU state, and root is a kind of user.

Before you change a single setting on a broken machine, train yourself to answer one question: does this failure live in hardware, in kernel space, or in user space?

## 3. What the kernel does: four jobs

Everything the kernel does fits under four headings: processes, memory, devices, and system calls. Programs reach the kernel through system calls, so we will look at each of the four areas in turn here, and then meet them in depth in chapters 1.8, 1.10, 1.11, and 1.17. If later you want the academic and source-level view, two classic textbooks are the standard companions. One is *Operating System Concepts*, 10th edition, by Abraham Silberschatz, Peter B. Galvin, and Greg Gagne. The other is *Linux Kernel Development*, 3rd edition, by Robert Love.

### Job 1: running processes

Start with a distinction people blur in everyday speech. A **program** is a file on disk; it does nothing by itself. A **process** is a program that is running. The kernel loads the program into memory and keeps a record for it, and that record holds the process ID, the memory map, the files the process has open, its owner, and what it is doing right now.

A real machine has far more processes than CPU cores, so the kernel has to share the cores among them. It does this by **time slicing**. A core runs one process for a very short slice, typically a few milliseconds or less. Then the kernel interrupts it, saves where it was, picks another process that is ready, and lets that one run. Each switch from one process to another is called a **context switch**. The slices are so short that, to you, everything appears to run at once. That illusion is called **multitasking**, and the part of the kernel that picks who runs next is the **scheduler**. This is how several training jobs, an editor, and a monitoring agent can all share the same cores.

For many years, Linux's default scheduler for ordinary processes was the Completely Fair Scheduler. Starting with kernel 6.6 it was replaced by EEVDF. You do not need the details yet; the idea of fair sharing is what matters.

What triggers the switch? A hardware timer. At the end of a slice, the timer interrupts the CPU. The CPU switches into privileged mode and hands control to the kernel. Here is the sequence in everyday terms:

![Job 1: running processes](./img/ch01-d2-luna.svg)

*Figure 1.1.6. Job 1: running processes.*

Two consequences of this design are worth carrying with you. First, *the kernel only runs between slices of user programs*, or when a program makes a system call, or when a device raises an interrupt. The kernel is not a separate program running in parallel with yours; it is the manager who steps in on a regular basis, does the bookkeeping, and steps out again. Second, on a machine with several cores, this same dance happens per core, with one extra decision: which core a process should run on. That placement matters a great deal for performance with GPUs and fast networks, and chapter 1.17 covers it under the name NUMA.

### Job 2: managing memory

![A worked example translating virtual address 8,320 through a page table to physical frame 15, and virtual address 28,736 hitting an unmapped page and causing a page fault.](./img/p3-0101-pagetable-example.svg)

*Figure 1.1.7. Worked example: virtual page 2 maps to frame 15 and the access succeeds, while virtual page 7 is not mapped and raises a page fault.*

Every process believes it owns a large, private, continuous block of memory. That belief is an illusion, and the kernel works hard to maintain it, with help from a piece of CPU hardware called the **memory management unit**, or **MMU** for short. The design behind the illusion is called **virtual memory**.

Here is how the illusion works. The addresses a program uses are virtual addresses, not physical locations in the RAM chips. For each process, the kernel keeps a translation table called the **page table**. The table maps chunks of virtual addresses, called **pages**, to chunks of physical RAM. A page is usually 4 KiB. Every time the program reads or writes memory, the MMU translates the address through that table, and it does so in hardware, at full speed. This one trick hands the kernel several powers at once:

- **Isolation.** Process A's pages simply are not mapped into process B's table, so B has no way to even name A's memory.
- **Sharing.** Two processes can hold page-table entries pointing at the *same* physical page. This is how programs share a library, and how a container image's files are shared in memory.
- **Protection.** Entries can be marked read-only or non-executable, so whole classes of bugs become impossible.
- **Overcommit and swap.** The kernel can promise more memory than exists, and it can move rarely used pages out to disk and bring them back on demand.
- **Lazy loading.** Pages can be filled in only when first touched, so a program never pays for memory it does not use.

![Infographic titled Virtual memory. Process A and Process B each have their own page table. One MMU translates each virtual address to a page in physical RAM. A shared page is mapped by both processes, and an address that is not mapped raises a page fault. Four steps: virtual address, MMU lookup, mapped access to RAM, or not mapped and a page fault.](./img/ch01-fig3-virtual-memory.jpg)

*Figure 1.1.8. Virtual memory. Each process has its own page table, the MMU translates every access in hardware, and an access to a page that is not mapped raises a page fault.*

What happens when a program touches a page that is not currently mapped? The CPU raises a **page fault**, and the kernel takes over. The kernel may load the page from disk, allocate a fresh one, or kill the program if the access was illegal. That last case is the famous "segmentation fault". You will meet page faults again in GPU work, because GPU unified memory is built on this same idea.

The kernel's own bookkeeping is also memory, and the kernel needs a private region that user processes can never map. That reserved region is **kernel space**, and the part that user processes may use is **user space**.

### Job 3: managing devices

![Diagram illustrating how file operations on device nodes under slash dev route through kernel device drivers to physical hardware or software pseudodevices.](./img/p4-0101-device-files.svg)

*Figure 1.1.9. Linux device architecture: ordinary file system calls on files under slash dev are routed by the kernel to either hardware device drivers or kernel-internal pseudodevices.*

Disks, network cards, keyboards, and GPUs all speak different low-level languages, and no program should have to learn them all. The kernel's answer is the **device driver**: one piece of code per kind of hardware that understands its device and exposes it through a common, simple interface. A driver is code that runs in kernel mode, and this one fact explains a lot about GPU nodes: **the NVIDIA driver is kernel code.** It arrives as kernel modules named `nvidia`, `nvidia_uvm`, and a few more, together with user-space libraries that talk to those modules.

Linux goes one step further and presents many devices as **special files** under `/dev`. A program can open `/dev/nvidia0` or `/dev/nvme0n1` and use ordinary file operations on it, and the kernel quietly routes those operations to the right driver. Notice the idea underneath, because it is one you will see everywhere in Linux: *many things are made to look like files*. Devices, processes under `/proc`, hardware information under `/sys`, and network sockets all look like files, so the same small set of tools and system calls works on all of them.

![Infographic titled Many things look like files. A program performs ordinary file operations on /dev/nvidia0, /dev/nvme0n1 and /dev/null. The kernel routes each operation to the device driver, which talks to the GPU, the NVMe disk or discards what is written. Proc, sys and network sockets are also made to look like files.](./img/ch01-fig4-everything-is-a-file.jpg)

*Figure 1.1.10. Many things look like files. A program uses ordinary file operations, and the kernel quietly routes them to the right driver for the hardware.*

Some device files do not correspond to any hardware at all. **Pseudodevices** look like devices to programs, but they are implemented purely in software, usually inside the kernel for practical reasons. `/dev/null` discards whatever you write. `/dev/zero` provides an endless supply of zero bytes. `/dev/random` and `/dev/urandom` supply random numbers from the kernel's generator, which would be hard to implement securely in an ordinary program. Notice also that a process still needs a system call to open one of these; on Linux, processes never escape system calls entirely.

Finally, drivers can be built into the kernel itself, or loaded on demand as **kernel modules** shipped in `.ko` files. Loading a module puts new code *into the running kernel*. That is why a module compiled for one kernel version often refuses to load on another, and it is the origin of one of the most common GPU-node failures, which you will meet at the end of this chapter.

### Job 4: system calls and the services around them

![Diagram of a system call journey showing user code calling glibc, transitioning through the CPU syscall instruction into kernel subsystems, with strace intercepting at the boundary.](./img/p4-0101-syscall-boundary.svg)

*Figure 1.1.11. The system call path: user applications invoke glibc wrappers that trigger the hardware syscall instruction, transitioning execution to the kernel dispatcher across five functional categories while strace observes the boundary.*

You have walked past the front desk several times now, so here is its proper definition. A **system call**, often shortened to syscall, is a request from a user program to the kernel through the defined doorway. There are a few hundred of them, and together they are the entire vocabulary a program has for dealing with the world outside its own memory. The table groups the common ones by category. Learn the categories first; the individual names will become familiar with use.

| Category | Typical system calls | What they let a program do |
|---|---|---|
| Files | `open`, `read`, `write`, `close`, `stat` | work with files and devices |
| Processes | `clone` (and `fork`), `execve`, `wait4`, `exit_group`, `kill` | create, run, wait for and end processes |
| Memory | `mmap`, `brk`, `munmap`, `mprotect` | ask for or change memory |
| Network | `socket`, `connect`, `bind`, `listen`, `accept`, `sendto`, `recvfrom` | talk over the network |
| Control and info | `ioctl`, `getpid`, `uname`, `clock_gettime` | talk to drivers, ask the kernel questions |

In practice you almost never call these directly. Your program calls a function in a library, such as `printf`, `open`, or `socket`, and that library function eventually performs the actual system call on your behalf. The most important of these libraries is **glibc**, the GNU C library, which lives in the file `libc.so.6`. Nearly every program on mainstream distributions uses it.

![Infographic titled System calls. Your program calls a library function such as open, glibc (libc.so.6) makes the system call, and the call crosses a dashed line to the system call interface in the kernel, which has counters for files, processes, memory, network, and control and info. strace prints every system call a program makes.](./img/ch01-fig5-system-calls.jpg)

*Figure 1.1.12. System calls. A program's library call, through glibc, becomes the system call that enters the kernel, which serves it by category.*

Two notation habits will greet you in every book and manual page. First, system calls are written with parentheses, such as `fork()`, `exec()`, and `execve()`; the habit comes from the C language, in which they are called. You do not need to know C. Just remember that *a system call is an interaction between a process and the kernel*. Second, a name like `exec()` usually stands for a **family** of related C library functions, such as `execl()`, `execv()`, and `execvp()`. Those functions differ only in how they pass their arguments, and all of them invoke the same underlying kernel system call, `execve()`.

One relative of the process also deserves a name while we are here. A **thread** is a lighter variant of a process that shares most of its memory with the process that created it. Threads are how a single program uses several cores at once, and chapter 1.8 picks up that story.

Here is the payoff for this whole section: everything in Linux eventually reduces to system calls. That is why **`strace`**, a tool that prints every system call a program makes, is the best learning and debugging companion you will find. When a program hangs or fails mysteriously, trace its system calls, and you will see the exact kernel boundary where it stopped.

## 4. Processes, users, and who starts what

### What happens when you type a command

Here is the most important worked example in the whole chapter, because it answers a question most people never think to ask: how does anything start at all? Suppose you type `ls` into a terminal and press Enter. The program that reads your typing is a **shell**, such as `bash`. A shell is just a user-space program with no magic in it: it reads your text and runs other programs. Watch what that looks like through the kernel's eyes.

![What happens when you type a command](./img/ch01-d3-luna.svg)

*Figure 1.1.13. What happens when you type a command.*

Two steps in that diagram do all the real work. The first step creates a new process. The classic Unix call for this is `fork()`, which makes the child an almost exact copy of the parent. On modern Linux, the C library implements `fork()` using the `clone` system call, so `strace` will show `clone` or `clone3`.

The second step replaces the child's program. When the child calls one of the C library's `exec()` functions, written `exec(ls)` here in simplified notation, the library calls the kernel's `execve()` system call. That call throws away the child's current program and loads the new one into the same process. The process ID, or PID, stays the same; only the program inside it changes. Copy first, then swap. That two-step is how every command you have ever typed began.

Every process except the very first is created this way, so processes form a **tree**: parents and children, all the way down. The first user-space process the kernel starts is called **init**. It has process ID 1, and it is the ancestor of everything else; on modern distributions it is **systemd**, which chapter 1.15 covers properly. If a process's parent dies, the orphaned process is adopted by PID 1. This tree is why `pstree` is a useful command. It is also why container runtimes and Slurm care so much about who the parent of a process is: in chapter 6.7 you will see that `slurmstepd` must be the parent of job processes, precisely so that it can track them and clean them up.

### Users, owners, and `root`

![A process with a UID and GID and a file with owner and permission bits are compared by the kernel.](./img/l01-uid-gid.svg)

*Figure 1.1.14. The kernel decides access by comparing the numeric IDs of the process with the owner, group and permission bits on the file.*

Everything so far was about one program asking one machine for things. Linux adds a second question: who is asking? Linux is a multi-user system. Each user has a numeric **user ID**, or **UID**, and belongs to one or more groups, and each group has a numeric **group ID**, or **GID**. Every process runs *as* some UID and GID, and every file carries an owner and a group. The kernel makes access decisions by comparing these numbers with permission bits stored on files. The special account **root** has UID 0, and it bypasses most permission checks.

Why have users at all? **Users exist to provide permissions and boundaries.** Every user-space process has an owner and is said to run as that user. A user can end or alter their own processes within limits, but cannot interfere with other users' processes, and users own files and choose whether to share them. Besides the accounts for human beings, a system runs several service accounts, covered in chapter 1.6. The one to know now is `root`, the **superuser**, because it is the exception to all of these rules: `root` can terminate or alter any process and read any file on the local system. That is why a person who can act as root is the system's administrator.

Operating as root is dangerous. The system will let root do anything, even when it is destructive, and mistakes are hard to spot afterwards. System designers therefore keep working to make root access unnecessary; an ordinary user can switch Wi-Fi networks without root, for example. Groups, meanwhile, are simply sets of users, used mostly to share file access among members.

You will learn permissions properly in chapter 1.6. For now, hold on to two ideas. *Processes have an identity*, inherited from whoever started them, and *the kernel enforces access on numbers, not names*. The practical consequence for your clusters: keep numeric UIDs identical on every node, so that Slurm's munge authentication and your shared filesystems agree on who owns every file and every job.

## 5. Seeing it with your own eyes

Maps are useful, but this chapter truly lands the day you see the layers on a real machine with your own eyes. That is what this section is for. The commands below target a live Linux VM and were not run on live hardware; the deterministic model checks run locally instead, in `code/part01/linux_layers_lab.py`.

![A two-row table showing which command reveals the kernel release and which reveals the distribution.](./img/g-1.jpg)
*Figure 1.1.15. The kernel and the distribution are two separate facts, so check both.*


### 5.1 What machine and which kernel is this?

```bash
uname -a            # kernel name, node name, kernel release, architecture
cat /etc/os-release # which distribution and version this is (the user-space side)
lscpu | head -20    # CPU model, sockets, cores, threads, NUMA nodes
free -h             # RAM and swap, human-readable
lsblk               # block devices: disks, partitions, mount points
ip -br addr         # network interfaces and addresses
```

Two of these commands answer different questions, and people mix up the answers all the time. `uname -r` prints the **kernel release**, such as `6.8.0-1020-gcp`; that tells you which kernel is running. `/etc/os-release` names the **distribution**, such as Ubuntu 24.04 or Rocky Linux 9; that tells you which user space you have. Read both every time you log into an unfamiliar machine. They are separate facts, you can update one without the other, and mismatches between them cause real trouble.

### 5.2 What is running, and in what tree?

```bash
ps -ef --forest | head -40     # every process, drawn as a tree (PID, parent PID)
pstree -p | head -30           # the same tree, compact
ps -eo pid,ppid,user,stat,comm | head   # chosen columns
ls /proc/1                     # PID 1's "files": cmdline, status, maps, fd, ns ...
cat /proc/1/cmdline | tr '\0' ' '; echo
```

Start a small hunt in that output. First find PID 1, which is `systemd` or `init`; that is the root of the tree. Then look for the processes in square brackets, such as `[kthreadd]` and `[kworker/0:0]`: those are the kernel threads you met earlier. Everything else descends from PID 1. The `STAT` column tells you what each process is doing right now. `S` means sleeping and `R` means running. `D` marks uninterruptible sleep, where a process waits on I/O and cannot be interrupted, and `Z` marks a zombie, a process that finished but has not yet been collected by its parent. Remember `D` and `Z`; both return in the failure stories at the end of the chapter.

### 5.3 Watch a command start: `strace`

```bash
sudo apt-get install -y strace     # Debian/Ubuntu; use dnf on Rocky/RHEL
strace -f -e trace=execve,clone,clone3,wait4,exit_group bash -c 'ls /tmp > /dev/null' 2>&1 | head -30
```

In the output you should recognise the four moves from the diagram. The shell calls `clone` or `clone3`. The child calls `execve("/usr/bin/ls", ...)`. The child exits with `exit_group`, and the parent waits with `wait4`. Want to see everything? Drop the `-e trace=` filter and send the output to a file, then read the opening lines: they show the dynamic loader at work, mapping the C library, reading `/etc/ld.so.cache`, and calling `mmap` for memory before the real work starts. Reading even a few dozen lines of `strace` output for a simple program is the single best habit you can build for understanding Linux.

### 5.4 Watch the kernel/user boundary yourself

Now prove the boundary to yourself instead of taking my word for it: write the smallest program that makes a system call, compile it, and trace it.

```bash
cat > hello.c <<'EOF'
#include <unistd.h>
int main(void) { write(1, "hello from user space\n", 22); return 0; }
EOF
gcc -static -o hello hello.c && strace ./hello
```

The static build keeps the trace tiny. You will see `execve`, a few memory calls, the `write(1, "hello from user space\n", 22)` request to the kernel, and then `exit_group`. Drop the `-static` flag and you will also watch the dynamic loader join in. Either way, you can now see without any trust required that *a program is just a sequence of ordinary computation and system calls*.

### 5.5 Where do devices and kernel modules show up?

```bash
ls /dev | head -30            # device files (null, zero, tty, sda or nvme0n1, ...)
lsmod | head                  # kernel modules currently loaded into the running kernel
modinfo nvme 2>/dev/null | head -5   # details of a module
dmesg | tail -20              # kernel log ring buffer (may need sudo)
```

On a GPU machine, the same commands tell a richer story. The device list adds `/dev/nvidia0`, `/dev/nvidiactl`, and `/dev/nvidia-uvm`, and the `lsmod` output adds `nvidia`, `nvidia_uvm`, and `nvidia_modeset`. File this away for your first on-call shift: whenever a user-space tool reports that no GPUs are present, check `lsmod` and `/dev/nvidia*` first.

## 6. Distributions: Linux is a kernel, not a system

Why should a history lesson matter to a working engineer? Because this history explains the standards, and the standards explain why your skills transfer from one machine to the next. The UNIX operating system was developed at AT&T. After AT&T's breakup, the trademark and the rights to the original source code changed hands several times. Since 1993, the trademark and the right to certify compliance have been held by the X/Open consortium, now **The Open Group**, which develops the **Single UNIX Specification**. POSIX is the core of that specification.
Only systems certified against that specification, such as Solaris and AIX, may be *called* UNIX. Systems that did not seek certification, Linux among them, deliberately follow the same standards anyway. That choice pays off for you every day: programs written to the standard interfaces and libraries port between these systems easily. Portability, together with UNIX's earlier popularity, helped the family win leadership on servers. Its successors include Solaris, OpenBSD, FreeBSD, AIX, and Linux, and today **Linux is the de facto standard for clusters and supercomputers**.

The creation of Linux itself weaves together two threads, and you will hear both names whenever old-timers argue. The first thread starts in the early 1980s, when Richard Stallman launched the **GNU Project** to build a completely free Unix-like operating system. GNU is a recursive acronym for *GNU's Not Unix*. Stallman's **GNU General Public License**, or **GPL**, grew out of this work. The GNU Project wrote free versions of almost all essential Unix user-space utilities, compilers, and libraries. Its own kernel, called **GNU Hurd**, never gained momentum.

The second thread began in 1991, when Linus Torvalds started writing a free **MINIX** clone, because no free Unix kernel was readily available at the time. His kernel, named **Linux**, attracted contributors around the world remarkably fast, and it was licensed under the GNU GPL in 1992 with the release of version 0.99. Put the two threads together, Torvalds's kernel and the GNU user-space collection, and you get a complete operating system. That is why organizations such as Debian sometimes call the full system **GNU/Linux**. You will see both names, and they refer to the same system.

A **distribution**, or **distro** for short, bundles that kernel with a selection of open-source utilities. It also adds a C library, an init system, a **package manager**, configuration defaults, and a support policy. Early distributions like Slackware pioneered this packaging. The key idea is that when you choose a distribution, you choose all five parts at once, not just a logo. And in AI infrastructure, almost every server and cluster you touch belongs to one of two major distribution lineages.

![Distributions: Linux is a kernel, not a system](./img/ch01-d4-luna.svg)

*Figure 1.1.16. Distributions: Linux is a kernel, not a system.*

### 6.1 The Red Hat, Fedora, CentOS, and Amazon Linux branch

![Lineage diagram showing the flow of packages from upstream Fedora through midstream CentOS Stream to downstream RHEL and binary rebuilds Rocky Linux, AlmaLinux, and Amazon Linux.](./img/p4-0101-rhel-lineage.svg)

*Figure 1.1.17. The Red Hat distribution lineage: innovations flow from upstream Fedora through midstream CentOS Stream to RHEL, which downstream community distributions like Rocky Linux and cloud distributions like Amazon Linux rebuild or adapt using RPM and DNF.*

The easiest way to remember this branch is as a river, because the family itself talks in upstreams and downstreams. At the mouth of the river sits **Red Hat Enterprise Linux**, or **RHEL**, the first major commercial success in the Linux market. Enterprise and HPC data centers prize it for multi-year stability, vendor certifications, and commercial support contracts. Fast-moving upstream kernel development clashes with the slow, careful stability that RHEL customers need, so Red Hat sponsors **Fedora** as its upstream distribution. New kernels, package tools, and system features land in Fedora first, developers and the open-source community vet them there, and they later flow downstream into RHEL.

Because the GNU GPL requires Red Hat to publish the source code of RHEL, community engineers used that source to rebuild RHEL as **CentOS**, short for *Community Enterprise OS*, a free, binary-compatible clone of RHEL without paid support. In late 2020, Red Hat shifted CentOS into **CentOS Stream**, a "midstream" distribution that sits between upstream Fedora and downstream RHEL. Organizations that wanted a strict downstream binary rebuild of RHEL created **AlmaLinux** and **Rocky Linux** as direct CentOS replacements.


AWS also builds **Amazon Linux** in this family. It launched in September 2011 and was succeeded by **Amazon Linux 2** in 2018, then by **Amazon Linux 2022** and **Amazon Linux 2023**, which draw from Fedora, CentOS Stream, and RHEL sources. Other members of the family include Oracle Linux and Scientific Linux.

Every distribution in this branch shares the **RPM** format, and its package files end in `.rpm`. The name comes from the original Red Hat Package Manager utility, `rpm`. While `rpm` installs individual package files, modern Red Hat derivatives use higher-level dependency resolvers that pull from online repositories. The first of these was `yum`, short for *Yellowdog Updater, Modified*, and today it is `dnf`, short for *Dandified YUM*.

### 6.2 The Debian and Ubuntu branch

![Old programs run on new kernels, but newer glibc programs and kernel modules fail on mismatched systems.](./img/l01-asymmetry.svg)

*Figure 1.1.18. Kernel and user space move independently, and the reverse direction fails in two ways.*

The second lineage starts with **Debian GNU/Linux**, founded by Ian Murdock in 1993 and sponsored early on by the Free Software Foundation's GNU Project, from November 1994 through November 1995. Debian remains the only major Linux distribution governed entirely by a community project rather than a corporate parent. It also has a naming habit you will grow to like: every Debian release since version 1.1 in June 1996, code-named *Buzz*, is named after a *Toy Story* character. You will meet Debian 11.0 *Bullseye*, released in August 2021, and Debian 12 *Bookworm*. Debian maintains three branches: `unstable`, which is always named *Sid*, then `testing`, and finally `stable`. Packages mature through `unstable` and `testing` before they freeze into a rock-solid `stable` release. That patience makes Debian a favorite base for other distributions, including NVIDIA's Cumulus Linux on network switches.

The most widely deployed Debian derivative in AI infrastructure is **Ubuntu**, started in April 2004 by Mark Shuttleworth's company **Canonical**. Ubuntu's first release came in October 2004 as version 4.10, where the 4 stands for the year 2004 and the 10 for October, and it was code-named *Warty Warthog*. Later releases kept the alliterative animal names, such as *Hoary Hedgehog* and *Breezy Badger*. Ubuntu pulls its packages from Debian's `unstable` branch, and it ships on two rhythms at once: a regular release every six months, plus a **Long-Term Support (LTS)** release every two years, with each LTS supported for at least five years. NVIDIA's **DGX OS** is built directly on Ubuntu LTS.
All Debian and Ubuntu systems share the `.deb` package format. `dpkg` manages that format at the low level, while `apt`, `apt-get`, and `aptitude` manage it at the repository and dependency level. `aptitude` itself replaced the older `dselect` tool.

The table lines the three families up side by side, and its last column shows where each one appears in your clusters. Notice how each family pairs its package format with its own tools, so learn the tools for the family you run.

| Family | Examples | Package format & tools | Where you meet it in AI infrastructure |
|---|---|---|---|
| Debian and Ubuntu | Debian, Ubuntu LTS, DGX OS, Cumulus Linux | `.deb` via `dpkg` and `apt` | NVIDIA DGX OS, Cumulus switches, cloud GPU images, and container base images |
| Red Hat family | RHEL, Fedora, CentOS Stream, Rocky Linux, AlmaLinux, Amazon Linux | `.rpm` via `rpm`, `yum`, and `dnf` | Enterprise HPC clusters, Slurm supercomputers, and NVIDIA Base Command Manager nodes |
| SUSE | SLES, openSUSE | `.rpm` via `rpm` and `zypper` | European HPC centers and enterprise appliances |

Three lessons from this history will save you hours of cluster debugging later.

1. **Same package format does not mean portable packages.** RHEL, Fedora, Rocky, and SUSE all use `.rpm` files. Debian and Ubuntu both use `.deb` files. Even so, you cannot safely install a package built for one distribution on another. Slight differences in package naming, library versions, and file paths make cross-distro binary packages fail dependency resolution or crash at runtime.
2. **Kernel versions are not what they seem.** Enterprise distributions keep an older base kernel version number, but they *backport* security fixes and hardware drivers into it. For example, RHEL 9 reports a `5.14`-series kernel while containing many newer features. Ubuntu ships newer kernels and offers Hardware Enablement kernels, shown as `HWE`, that advance during an LTS lifecycle. Always check `uname -r` and your vendor's support matrix before installing GPU or InfiniBand drivers.
3. **The kernel and user space move independently, with two strict asymmetries.** The Linux kernel strictly obeys the rule "never break user space," so old user-space binaries almost always keep running on newer kernels. The reverse fails in two ways. First, *user-space programs compiled against a newer `glibc` will fail to start on an older distribution*. Second, *kernel modules (`.ko`) compiled for one kernel build will refuse to load on another*. Standardise a single tested OS release across every node in a cluster.

If this chapter leaves you wanting a deeper sysadmin library, Sergey Zhumatiy's *Supercomputers for Linux SysAdmins* recommends four timeless companions. The first is *UNIX and Linux System Administration Handbook*, by Evi Nemeth, Garth Snyder, Trent Hein, and Ben Whaley. The second and third are *The Practice of System and Network Administration*, by Thomas Limoncelli, Christina Hogan, and Strata Chalup, and Limoncelli's *Time Management for System Administrators*. The fourth is Brian Kernighan and Rob Pike's classic *The UNIX Programming Environment*.

## 7. Putting a GPU node on the map

Time to land the map on the machine you will actually work on: a server with GPUs and InfiniBand adapters, running a Kubernetes or Slurm agent. Walk the picture below layer by layer, and notice how everything you have met so far has a home on this box.

![Putting a GPU node on the map](./img/ch01-d5-luna.svg)

*Figure 1.1.19. Putting a GPU node on the map.*

The table lists each component with its layer, its role, and the boundary where its failures show up, so when something breaks you know where to look first.

| GPU Node Component | Layer | Exact Role and Failure Boundary |
|---|---|---|
| `nvidia.ko`, `nvidia_uvm.ko`, `nvidia_peermem.ko` | Kernel space | Own the GPU hardware, manage GPU virtual memory page faults, and expose `/dev/nvidia*` character devices |
| `libcuda.so`, `libnvidia-ml.so` (`nvidia-smi`) | User space | Ship with the driver; translate CUDA Driver API and NVML calls into `ioctl` system calls on `/dev/nvidia*` |
| `libcudart.so`, `cuBLAS`, `cuDNN`, `NCCL` | User space | CUDA Toolkit and math/collective libraries; run in user space inside the job or container |
| `mlx5_core.ko`, `ib_core.ko` | Kernel space | Own the ConnectX NIC/HCA, register pinned memory, and set up RDMA queue pairs |
| `libibverbs.so`, `UCX` | User space | Post RDMA work requests directly to adapter hardware from user space (kernel bypass for data) |
| `containerd`, `runc`, `slurmd`, `kubelet` | User space | User-space daemons that ask the kernel to isolate and limit jobs via namespaces and cgroups |

Use the map as a lookup table from now on. The notes below walk through the five places where people most often get confused.

- **The NVIDIA driver has two halves.** The *kernel modules*, such as `nvidia.ko` and its friends, run in kernel mode; they own the GPU and create `/dev/nvidia*`. The *user-space libraries* are what your programs link against, and they include `libcuda.so` and the `libnvidia-ml.so` that `nvidia-smi` uses. The two halves talk to each other through `ioctl` system calls on those device files, and they must be compatible versions. That is why a "driver/library version mismatch" appears when the kernel module is not reloaded after an upgrade.
- **CUDA toolkit libraries and cuDNN are pure user space.** They never require the kernel to change. You can therefore run several toolkit versions side by side in different containers, as long as the host *driver* is new enough for all of them.
- **Containers are not virtual machines.** A container is an ordinary set of user-space processes. The kernel isolates it using **namespaces**, which give each container a separate view of processes, network, and mounts, and it limits the container using **cgroups**. All containers on a node *share the host's kernel*. Two consequences follow. A container can see GPUs only if the host has the driver and the device files are passed in. And the kernel version on the node, not anything inside the container image, decides which kernel features exist. Chapters 1.18 to 1.20 build all of this from scratch.
- **RDMA bypasses the kernel for data, not for setup.** Read that clause twice, because people misquote it. The kernel driver sets up the resources, such as queues and memory registrations. After that, the application talks to the adapter directly from user space through `libibverbs`. That "kernel bypass" is why InfiniBand achieves its low latency, and it is why standard Linux packet capture tools like `tcpdump` cannot see RDMA payload traffic: on that path, the payload never crosses the kernel's network stack.
- **`slurmd` and `kubelet` are just user-space programs.** They are not part of the kernel. They ask the kernel, through system calls, cgroup files, and namespaces, to start and limit jobs. So when you wonder who is in charge of a job, the answer is always a user-space daemon *using* kernel features.

**In one minute:** every GPU node splits into three parts: hardware; kernel space, home of `nvidia.ko`, `mlx5_core.ko`, namespaces, and cgroups; and user space, home of `libcuda.so`, PyTorch, `containerd`, `slurmd`, and `kubelet`. Containers bring their own user space, but they always share the host kernel. So when a container cannot see a GPU, check the host driver first.

## 8. How it fails: six classic confusions

![A table mapping six classic failure symptoms to the system layer that causes them.](./img/l01-layer-failures.svg)

*Figure 1.1.20. Before touching anything, ask which layer of the system the failure actually lives in.*

Everything in this chapter pays off here. Each of the six stories below is a real incident pattern, born from mixing up the layers. Read them with one habit in mind: before you touch anything, ask which layer of the system the failure actually lives in.

### 1. "I updated the kernel and the GPU disappeared"
**Symptom:** after an OS update and reboot, `nvidia-smi` fails with "couldn't communicate with the NVIDIA driver." **Cause:** the NVIDIA kernel modules were built for the old kernel. On the new kernel they are missing, or they will not load, because kernel modules are tied to one specific kernel build. **Diagnose:** `uname -r`, `lsmod | grep nvidia`, `dmesg | grep -i nvidia`, `modinfo nvidia | grep vermagic`. **Fix:** install modules that match the running kernel, using prebuilt packages or DKMS. You can also boot the old kernel. In production, pin kernels and update them in a tested image, never ad hoc. If you see this after a reboot, start with `uname -r`.

### 2. "Works in the container, not on the host" (and the reverse): confusing library layers
**Symptom:** your binary fails with `GLIBC_2.xx not found` or `error while loading shared libraries`. **Cause:** programs depend on user-space libraries. A binary built against a newer `glibc` cannot run on a host with an older one. **Diagnose:** `ldd ./binary`, `ldd --version`, `cat /etc/os-release`. **Fix:** build on the oldest distribution you need to support. Or ship the binary in a container that brings its own user space. Or use a matching base image. If you copy a binary between hosts, check both versions first.

### 3. A process that "cannot be killed": state D
**Symptom:** `kill -9` has no effect, and the process shows `D` in `ps`. **Cause:** the process is inside a system call, waiting for I/O on a dead NFS server, a failing disk, or a hung driver. It is uninterruptible by design. **Diagnose:** `ps -eo pid,stat,wchan:30,comm | awk '$2 ~ /D/'`, `dmesg`, and then check the storage or mount. **Fix:** fix the underlying device or mount. No signal works while the kernel is waiting on hardware. This is a *kernel/hardware layer* problem, and no amount of user-space restarting solves it. If you see a D state, stop sending signals and look at the mount.

![Two panels comparing a process in state D, stuck in a kernel system call waiting on I/O, with a zombie in state Z, which has finished and waits for its parent to call wait4.](./img/p3-0101-d-versus-z.svg)

*Figure 1.1.21. State D is alive and waiting inside the kernel on I/O, while state Z is already finished and only waits for its parent to collect it.*

### 4. "The kernel killed my job": the out-of-memory killer
**Symptom:** a training process vanishes with no error in its own log, and `dmesg` shows "Out of memory: Killed process ...". **Cause:** physical memory plus swap was exhausted. The kernel's OOM killer chose a victim to save the machine. **Diagnose:** `dmesg -T | grep -i -E "killed process|oom"`, `free -h`, and the per-cgroup limits in `memory.max`. **Fix:** reduce memory use, add memory, or set realistic limits. In containers and Slurm, the same event happens at the cgroup limit instead of at whole-machine exhaustion, as chapters 1.17 and 1.18 explain. If you see this in your logs, check the cgroup limit first.

### 5. "Permission denied" versus "No such file": wrong layer of cause
**Symptom:** a command fails with an error that looks like a file problem. **Cause:** these two errors are different system call return codes. `ENOENT` means the path does not exist. `EACCES` means the path exists, but your user ID may not use it. Treating one as the other wastes hours. **Diagnose:** `strace -f -e trace=openat,execve program 2>&1 | grep -E "ENOENT|EACCES"`, `ls -l`, `id`. **Fix:** correct the path, or correct the permissions, ownership, or SELinux label, as the error requires. Read the error code before you change anything.

### 6. "It behaves differently on the other cluster": distribution differences
**Symptom:** a script or a package name that works on Ubuntu fails on Rocky. **Cause:** different package managers, package names, default paths, init and firewall defaults, and kernel feature backports cause the difference. **Diagnose:** `cat /etc/os-release`, `uname -r`, and `command -v` for the tool. Then read the distribution's documentation. **Fix:** standardise the OS on the cluster. Write scripts that detect the distribution, or use Ansible from chapters 4.3 onward. Keep a compatibility matrix, and check it before you upgrade.

## Hands-on lab: layer verification and VM tour

Time to get your hands dirty. Start with the self-checking Python lab, and run it locally before you touch a VM. It verifies layer placement, privilege rules, `fork` and `execve` PID transitions, `4 KiB` virtual page translation, process states, and distribution lineage rules.

```bash
python3 code/part01/linux_layers_lab.py
```

Then move to an `e2-small` Ubuntu 24.04 VM, or any Linux machine you have. Work through them in order, and keep notes as you go so that you can compare results later.

**Part A: identify the layers.**
1. Run the commands from section 5.1. Record the distribution, the kernel release, the CPU count, and the RAM. Then explain which of those belong to user space, the kernel, and hardware.
2. Run `ps -ef --forest`. Find PID 1. Find three kernel threads. Find your own shell, and draw its ancestors up to PID 1.

**Part B: watch a program start.**
3. Run the `strace` command from section 5.3. Mark which line creates the child, which line replaces the program, and which line is the exit.
4. Run `strace -c ls /usr/bin > /dev/null`. This summarises system calls by count and time. Which system call is called most? Why does `ls` need it?
5. Compile and trace the `hello.c` program from section 5.4, with and without `-static`. Compare the length of the two traces. Then explain the difference that the dynamic loader causes.

**Part C: see the privilege boundary.**
6. As a normal user, try to read a protected kernel interface. Start with `cat /proc/kcore | head -c 10`. Then try `sudo cat /proc/1/maps | head`. Explain the difference in outcome in terms of user ID and what the kernel allows.
7. Write a program that dereferences a null pointer. Run it, and read the shell's message, `Segmentation fault`. Explain which hardware component noticed the problem, which software component acted, and why the machine was unaffected. Hint: the MMU is the hardware, and the kernel is the software.

**Part D: processes and states.**
8. Start `sleep 300 &`. Then run `ps -o pid,ppid,stat,comm -p $!` and `ls -l /proc/$!/`. Kill it. Next, start `sleep 300`, press Ctrl-Z, and run `ps` again. Note how the state letter changes.
9. Create a zombie on purpose, so you can see state `Z`. Use a short Python snippet that forks a child. The child exits while the parent sleeps without waiting. Explain what a zombie is, and who removes it.

**Part E: distribution awareness.**
10. Run a Rocky Linux container on an Ubuntu host with `docker run --rm -it rockylinux:9 bash`. Compare `cat /etc/os-release` and the package command, `dnf` versus `apt`. Then run `uname -r` inside the container and on the host, and notice the moment the lesson lands: they print the *same kernel*.

## Exercises

Work through these on paper first, and answer before you look; that is where the learning happens.

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

The four jobs are process management and scheduling, memory management through virtual memory and page tables, device management through device drivers, and serving system calls and kernel support routines. Hold on to those four, and you can reason about any Linux machine you log into.
</details>

<details>
<summary>6. What triggers a context switch, and what does the kernel do during it?</summary>

A hardware timer interrupt at the end of a time slice triggers a context switch, and a blocking system call can trigger one too. Either event switches the CPU into kernel mode. The kernel saves the current process's CPU registers and instruction pointer, invokes the scheduler to pick the next runnable process, loads that process's registers and page-table mappings, and returns the CPU to user mode. That is the whole cycle: timer, scheduler, switch.
</details>

<details>
<summary>7. Explain virtual memory, the MMU, and page tables in three sentences.</summary>

Every process uses virtual addresses, not physical RAM addresses. On every memory access, the CPU's Memory Management Unit, or MMU, translates the virtual page number, typically a `4 KiB` page, into a physical frame number. It does this using a per-process page table that the kernel maintains. If a virtual page is unmapped, the MMU raises a page fault, and the kernel can allocate memory lazily, swap a page in, or send `SIGSEGV` on an illegal access. When you meet a segmentation fault later, picture the MMU raising the alarm and the kernel answering.
</details>

<details>
<summary>8. What is a pseudodevice? Name four classic Linux pseudodevices and what each does.</summary>

A pseudodevice is a file under `/dev` that the kernel implements purely in software; nothing physical sits behind it. `/dev/null` discards all writes and returns EOF on read. `/dev/zero` supplies an endless stream of `0x00` bytes. `/dev/random` and `/dev/urandom` provide cryptographic random numbers from the kernel's entropy pool. All four are kernel code wearing a `/dev` costume.
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

Debian was founded by Ian Murdock in 1993 and uses *Toy Story* codenames, such as `1.1` *Buzz* and `11.0` *Bullseye*. It moves packages from `unstable` through `testing` into `stable`. Ubuntu, started by Canonical in 2004 with `4.10` *Warty Warthog*, pulls from Debian `unstable` and ships six-month releases plus two-year LTS releases, each supported for five years. NVIDIA's DGX OS is built directly on Ubuntu LTS.
</details>

<details>
<summary>16. Why can't you reliably install a Fedora `.rpm` on Rocky Linux or an Ubuntu `.deb` on Debian even though they share the same package format?</summary>

Sharing the `.rpm` or `.deb` container format does not guarantee binary or dependency compatibility. The `.rpm` tools are `rpm`, `yum`, and `dnf`. The `.deb` tools are `dpkg` and `apt`. If you mix package files, you should expect failures. Shared library versions, such as `glibc` and `libssl`, can differ between distributions. So can package naming conventions and filesystem paths. Those differences cause dependency resolution failures or runtime crashes.
</details>

<details>
<summary>17. The NVIDIA GPU driver has a kernel half and a user-space half. Name the files in each half and explain how they communicate.</summary>

The kernel half is made of kernel modules: `nvidia.ko`, `nvidia_uvm.ko`, and `nvidia_peermem.ko`. They run in ring 0 and expose `/dev/nvidia*`. The user-space half is made of the libraries `libcuda.so` and `libnvidia-ml.so`, plus the `nvidia-smi` tool. These talk to the kernel modules through `ioctl` system calls on `/dev/nvidia*`. So when your training job opens `/dev/nvidia0`, it is the kernel half of the driver that answers.
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
- **Not verified on live hardware:** All interactive VM shell commands (`uname -a`, `ps`, `pstree`, `strace`, `gcc -static`, `lsmod`, `modinfo`, `dmesg`, `docker run`) are marked and should be executed on a Linux VM.
