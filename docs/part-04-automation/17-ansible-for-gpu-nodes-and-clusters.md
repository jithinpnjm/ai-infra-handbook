---
id: "c04-17"
title: "4.17 Ansible for GPU nodes and clusters"
sidebar_label: "4.17 Ansible for GPU nodes and clusters"
sidebar_position: 17
description: "Applying Ansible to GPU fleets: ordered node bring-up (OS, kernel, OFED, NVIDIA driver, Fabric Manager, DCGM, container toolkit, Slurm/Kubernetes agents), role design, reboot handling, validation and burn-in, NCCL tests, drain/patch workflows, and the production incidents that shape the design"
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 4.17 Ansible for GPU nodes and clusters

| | |
|---|---|
| Level | Advanced |
| Priority tier | 0 |
| Lab venue | Ubuntu 22.04/24.04 or RHEL 9 nodes with NVIDIA GPUs (A100/H100 class for NVSwitch topics); ConnectX NICs optional; stub scripts for rehearsal on plain VMs |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs not run on live hardware |

## Why this matters for AI infrastructure

Picture a GPU node that has just come off the delivery truck. The GPUs are seated and the cables are in, but the machine can do very little useful work yet. Someone has to bring up a long stack of software, and the order matters. The stack starts with BIOS and firmware settings, then a kernel with matching headers. Next come the RDMA networking drivers (MLNX_OFED or DOCA), the NVIDIA driver, `nvidia-persistenced`, and Fabric Manager on NVSwitch systems. After those come the GPUDirect module `nvidia-peermem`, DCGM and its exporters for telemetry, and the container toolkit. Kernel tuning, filesystem mounts, and the scheduler or Kubernetes agent finish the stack.

Each link in that chain has to be correct, and the links have to work together. Think of a row of dominoes laid in a fixed order. A tile placed in the wrong spot makes the rest fall in a confusing way, often far from the real mistake. Install the GPU driver before the RDMA stack, and you spend an afternoon debugging `modprobe` failures that look like driver bugs. Mix a driver with a Fabric Manager from another branch, and a fleet can run at half speed while every job still reports success. Skip validation, and the first sign of a bad node may be a failed 64-node training job that wasted a long run of cluster time. Ansible's job is to bring nodes up, upgrade them and repair them in the same order every time, with a check after each step, across hundreds or thousands of machines.

## Prerequisites and outcomes

Before you start, you need chapters 4.3 to 4.16, plus the Linux and GPU basics from Parts 1, 9 and 10. Drivers, CUDA and NVLink are explained in those parts, so this chapter builds on them rather than repeating them. When you finish, you should be able to do the following:

- Describe the dependency order of a GPU node stack, and encode it in roles and playbooks with the right reboot points.
- Write roles for the OS and kernel, MLNX_OFED or DOCA, and the NVIDIA driver in its package and runfile forms.
- Write roles for Fabric Manager, DCGM, the container toolkit, MIG, GPU tuning, and the monitoring agents.
- Handle reboots, long installs (`async`), package pinning and holds, DKMS versus precompiled modules, and roll back safely.
- Validate nodes: check the GPU count, NVLink/NVSwitch state, ECC, PCIe link width and speed, IB link state, DCGM diagnostics, burn-in and NCCL tests. Then gate scheduling on the result.
- Run drain, patch, validate and resume workflows for Slurm and Kubernetes, with canary rollouts and fleet-wide diagnostics.
- Recognise and avoid the known incidents: interactive `dpkg` prompts, "green but dead" services, secrets leaking into logs, precedence surprises, and kernel and driver mismatches.

## 1. The node bring-up dependency graph

Suppose a freshly built node comes up with a driver that will not load. Before you touch anything, you need to know which step went wrong, and that means knowing the order the steps depend on. The graph below shows that order. Read each arrow as "needs", so the box at the end of an arrow needs the box at its start. The round markers show where a reboot or module reload has to happen, because the kernel will not swap modules under a running driver.

![The node bring-up dependency graph](./img/m4-17-1.svg)

*Figure 4.17.1. The node bring-up dependency graph, as a diagram.*

The graph gives you five rules, and each one prevents a failure you will eventually meet. First, install the RDMA stack before the GPU driver, because the driver's peer-memory module binds to it. If the order is reversed, `nvidia_peermem` loads without its RDMA partner and GPUDirect quietly stops working. Second, reboot or reload modules at every boundary where kernel modules change. Third, start Fabric Manager only after a matching driver is loaded, and before CUDA workloads run. Fourth, validate the node before the scheduler sees it, so a bad GPU never receives a job. Fifth, register the node with the scheduler last. Each rule is a dependency in the graph, so you can check your playbook against the arrows instead of against memory.

If you use the GPU Operator on Kubernetes, it can manage the driver container, toolkit and DCGM itself (Part 11). Ansible's role then narrows to OS, kernel, OFED, and kubelet. The arrows stay the same either way. Only the component that draws them changes.

When you write a bring-up playbook, follow the arrows rather than the order in which you remember the packages. Memory tends to skip the quiet steps, such as the reboot between OFED and the driver, and those are the steps that fail later.

## 2. Project structure

A bring-up playbook is easier to trust when its folders and task order mirror the graph. Picture a new engineer who opens the repository at 2 a.m. during a rack failure. If the folder names say where things live, that engineer finds the driver role in seconds and does not edit the wrong file. The layout below keeps inventory, playbooks and roles apart, so a change to one GPU model does not leak into every node.

```text
gpu-platform/
├── inventories/prod/{hosts.yml,group_vars/}
│   └── group_vars/
│       ├── gpu_h100.yml        # driver branch, clocks, nccl env, mig profile
│       ├── gpu_a100.yml
│       └── all/{vars.yml,vault.yml}
├── playbooks/
│   ├── gpu_bringup.yml         # new node: full ordered stack
│   ├── gpu_update_driver.yml   # driver/OFED upgrade with drain
│   ├── gpu_validate.yml        # diagnostics and burn-in
│   ├── gpu_patch_os.yml        # kernel/security patching
│   └── fleet_diag.yml          # read-only fleet checks
└── roles/
    ├── gpu_facts/ base_os/ kernel_tuning/ mofed/ nvidia_driver/ fabric_manager/ dcgm/ container_toolkit/
    ├── gpu_tuning/ gpu_validate/ slurm_client/ k8s_node_prereqs/ node_exporter/
```

The bring-up playbook should read like the graph, top to bottom, so a reviewer can compare the two side by side. Here is the first one. Each line in `roles:` is one box from the graph, in the same order, and Ansible runs them in that sequence for every host in the batch.

```yaml
# playbooks/gpu_bringup.yml
- name: Bring up GPU nodes
  hosts: "{{ target | default('gpu_new') }}"
  become: true
  serial: "{{ bringup_serial | default(10) }}"
  max_fail_percentage: 10
  roles:
    - { role: gpu_facts, tags: [facts] }
    - { role: base_os, tags: [base] }
    - { role: kernel_tuning, tags: [kernel] }
    - { role: mofed, tags: [mofed], when: "gpu_nic_family | default('') == 'connectx'" }
    - { role: nvidia_driver, tags: [driver] }
    - { role: fabric_manager, tags: [fm], when: ansible_local.gpu.nvswitch | default(false) }
    - { role: gpu_tuning, tags: [tuning] }
    - { role: dcgm, tags: [telemetry] }
    - { role: container_toolkit, tags: [containers], when: container_runtime is defined }
    - { role: gpu_validate, tags: [validate] }
    - { role: slurm_client, tags: [scheduler], when: "scheduler | default('') == 'slurm'" }
```

Notice the `serial` line. Without it, Ansible would start the same install on every host at once, and a bad package would reach the whole rack in one step. With `serial: 10`, the playbook finishes a batch of 10 nodes before it starts the next. `max_fail_percentage: 10` sets how many failures the run tolerates before it stops. Each role carries a tag, so you can run a single stage on its own, for example `--tags driver` after a driver fix, without repeating the OS work. When you add a role, place it where the graph says it belongs. A role placed too early will fail for a reason that has nothing to do with its own code.

## 3. Roles in detail

Each role does one job, and that job is easier to get right once you know the hardware underneath it. Read the roles in the order they run, because each one assumes the roles before it have already left the node in a known state. A role that writes a config file assumes the package is installed. A role that starts a service assumes the kernel module is loaded. When a role fails, the first question is which assumption broke.

### 3.1 gpu_facts: know the hardware before changing it

Consider a node where one GPU has dropped off the PCIe bus after a failed power cycle. The server still boots, the operating system still runs, and seven GPUs still answer. If the playbook keeps going, it installs software on a machine that is missing a GPU, and the job queue later sends an 8-GPU job to a 7-GPU node. The `gpu_facts` role prevents that by looking first. It asks the hardware what is there, and it records the answer before anything changes.

```yaml
- name: Detect NVIDIA devices
  ansible.builtin.shell: "lspci -d 10de: -nn | grep -Ei '3d controller|vga' | wc -l"
  args: { executable: /bin/bash }
  register: gpu_pci
  changed_when: false
  failed_when: false

- name: Detect NVSwitch (NVLink fabric)
  ansible.builtin.shell: "lspci -d 10de: | grep -ci nvswitch || true"
  args: { executable: /bin/bash }
  register: nvswitch
  changed_when: false

- name: Detect ConnectX / BlueField
  ansible.builtin.shell: "lspci -d 15b3: | grep -Eci 'infiniband|ethernet|mellanox' || true"
  args: { executable: /bin/bash }
  register: nic
  changed_when: false

- name: Publish local facts for later roles
  ansible.builtin.copy:
    dest: /etc/ansible/facts.d/gpu.fact
    mode: "0644"
    content: |
      {"count": {{ gpu_pci.stdout | int }}, "nvswitch": {{ (nvswitch.stdout | int > 0) | lower }}, "rdma_nics": {{ nic.stdout | int }}}
- ansible.builtin.setup: { filter: ansible_local }
```

The role runs three discovery commands before it changes anything. The first counts NVIDIA devices by vendor ID `10de`, which `lspci` reads from the PCI bus. The second checks for NVSwitch chips, which only HGX and DGX boards carry. The third counts ConnectX and BlueField NICs by their vendor ID `15b3`. Each command has `failed_when: false`, because a server with no NVSwitch should not fail the play just because the search found nothing. The role then writes the results to a small JSON file under `/etc/ansible/facts.d/`. Ansible reads that file on the next fact gathering and exposes it as `ansible_local`, so later roles can ask "is there an NVSwitch here?" without running the search again.

Compare the discovered count with the inventory's intended `expected_gpus`. A mismatch must stop the bring-up and raise a hardware ticket instead of continuing. Think of it as a gate at the door. The software installed after the gate assumes all eight GPUs exist, so a missing GPU found later costs you the whole driver install to rediscover. Treat that comparison as a gate you never skip.

### 3.2 base_os and kernel_tuning

Start with the basics, because every later role depends on them. The base OS role sets time sync with `chrony`. Clocks that drift apart make log timelines useless when you chase a fleet-wide fault. The role also sets consistent users and UIDs (SSSD/LDAP or static), applies SSH hardening, and points package repositories at internal mirrors. It deals with `unattended-upgrades`, which you disable or control, because a competing apt process caused the incident in section 7. A background upgrade that installs a new kernel in the middle of your bring-up is the kind of surprise that breaks DKMS later. Pin the kernel version with `dpkg_selections hold` or `versionlock`. Then install matching headers for DKMS with `linux-headers-$(uname -r)`, so the driver can build against the kernel that is actually running.

Kernel parameters go into GRUB drop-ins through `GRUB_CMDLINE_LINUX_DEFAULT`. GRUB is the boot loader, and this variable is the list of options handed to the kernel on every boot. The parameters include `intel_iommu=on iommu=pt` or `amd_iommu=on`, which the RDMA and GPU passthrough paths need. They also include `default_hugepagesz=1G hugepagesz=1G hugepages=N` where you use hugepages, and `transparent_hugepage=madvise`, which lets applications ask for huge pages rather than receiving them unpredictably. Add `isolcpus` or `nohz_full` only when you have a measured reason, because each one takes CPU cores away from the general scheduler. Set `pci=realloc` where the BIOS leaves PCIe address space too small for every GPU. Also set `processor.max_cstate`, which caps how deep idle cores may sleep. Set `numa_balancing=disable` as a sysctl, so the kernel does not move memory pages between sockets behind your back. Apply the changes with `update-grub` or `grub2-mkconfig`, followed by a controlled reboot. A parameter that is wrong in GRUB will not show up until the next boot, which is why the reboot belongs in the same change.

For networking and memory, the role sets sysctls such as `net.core.rmem_max`, `vm.max_map_count` and `vm.swappiness=1`. A sysctl is a kernel setting you change at runtime through `/proc/sys`. The `vm.swappiness=1` value tells the kernel to avoid swapping almost entirely, because swapping a training process to disk stalls every GPU that waits on it. The role writes `limits.d` entries, with memlock unlimited for RDMA, since RDMA pins memory so the NIC can read it directly, and a high nofile limit for many open file handles. It also sets tuned or `cpupower` governors, and IRQ affinity through an `irqbalance` policy or explicit pinning for NICs. An IRQ is the interrupt a device raises to ask the CPU for attention, and pinning it keeps NIC interrupts off the cores that feed the GPUs. The role sets `ulimit` values in systemd units, disables services you do not need, and keeps `/dev/shm` sizes consistent for NCCL and PyTorch. Those shared-memory sizes matter because data loaders pass batches through `/dev/shm`, and a small default size makes them fail with bus errors. The details are in Parts 1, 9 and 12.

Four tuning insights belong in this role, and the first one is about GPU bubbles. A GPU bubble is an idle gap on the GPU, a stretch where the device waits for work and does nothing. The GPU does the matrix math, but the host CPU must keep launching CUDA kernels and preparing data batches. Picture a line cook who has to hand the next plate to the grill every few seconds. If the cook dozes off between tickets, the grill sits cold, even though the grill itself is fine. When a CPU core falls into a deep sleep state (`C-state`), waking it adds microseconds of delay. Each delay is small, but they add up across millions of kernel launches, and the result is a GPU that runs in short bursts. Set the BIOS profile to High Performance, lock the Linux CPU frequency governor to `performance` with `cpupower frequency-set -g performance`, and disable deep C-states. Launch latency then stays predictable from one step to the next.

The second insight is NUMA affinity. NUMA stands for non-uniform memory access. On a dual-socket server, each CPU socket has its own memory, and reaching the other socket's memory takes a longer trip over the link between them. Now picture a data-loader process on NUMA node 0 feeding a GPU attached to the PCIe root complex on NUMA node 1. The batch has to cross the inter-socket UPI or Infinity Fabric link on every copy, and that nearly doubles memory access latency. Capture `nvidia-smi topo -m` in the playbook, so you can see which GPUs and NICs sit behind which socket before any job runs. Configure the Kubernetes kubelet with `--topology-manager-policy=single-numa-node` (or `restricted`) and `--cpu-manager-policy=static`, so the scheduler keeps a pod's CPUs and GPU on one socket. Then verify `pin_memory=True` and `non_blocking=True` in the data loader, so host-to-device copies use pinned memory and run asynchronously.

On integrated Grace Blackwell superchips, the Grace CPU and the Blackwell GPU share coherent memory over NVLink-C2C at up to 900 GB/s. Coherent means both processors see the same memory contents without an explicit copy, so the CPU-to-GPU distance shrinks a great deal. An NVL72 rack domain provides 130 TB/s of aggregate bidirectional NVLink bandwidth, or 1.8 TB/s per GPU. These are the numbers your NUMA plan should match, because a topology that mismatches them loses that bandwidth at the first copy.

The third insight is page-cache write-back. The page cache is the memory Linux uses to hold file data before it reaches disk. Large training runs write multi-gigabyte checkpoints in bursts, and the kernel can hold a large amount of dirty data before flushing it. When the flush finally starts, it competes with the training process for I/O and stalls the step that was running. Tuning `vm.dirty_background_ratio` and `vm.dirty_ratio` makes the kernel start writing earlier and in smaller pieces. Asynchronous or distributed checkpointing does the rest by moving the write off the training loop. Preloading `jemalloc` (`narenas`, `background_thread:true`) or `tcmalloc` reduces host RAM fragmentation in multi-worker Python data loaders, because each worker otherwise grows its own pool of small allocations that never returns cleanly.

The fourth insight covers ECC, clocks and MIG. ECC (error-correcting code) is the memory protection that detects and fixes bit flips, and it is the reason to keep it on. A single undetected cosmic-ray bit flip during a multi-week training run can silently corrupt gradients into `NaN`, which is the not-a-number value that poisons every later step. Nothing crashes, and the loss curve simply goes bad days later. Changing ECC requires a GPU reset or a reboot, so decide it in the build, not in the middle of a run. For acceptance benchmarks, use locked clocks (`nvidia-smi -lgc`), so thermal throttling on later runs does not skew the comparison. Without locked clocks, the same benchmark can look faster on a cold rack than on a warm one, and the difference has nothing to do with the software. MIG (Multi-Instance GPU) splits one physical GPU into isolated slices, and it suits many small inference jobs that each need a fraction of the device. The Blackwell B200 profiles include `MIG 1g.23gb` x7, `1g.45gb` x4, `2g.45gb` x3, `3g.90gb` x2, `4g.90gb` x1, or `7g.180gb` x1. Large multi-GPU training jobs turn MIG off so they can use full GPUs and the full NVLink path.

### 3.3 mofed (MLNX_OFED / DOCA-Host)

Suppose someone bumps the OFED version for one rack on a Tuesday afternoon. The installer replaces the in-box kernel networking drivers on every node in that rack, and a reboot follows. Nothing about the change looks risky in the pull request, yet several steps here can break a node quietly, so each one needs care. OFED (OpenFabrics Enterprise Distribution) is NVIDIA's and Mellanox's bundle of RDMA drivers and user-space tools, and it is the layer the NICs need before any GPU traffic can leave the node.

```yaml
- name: Download and verify the OFED bundle
  ansible.builtin.get_url:
    url: "{{ mofed_base_url }}/MLNX_OFED-{{ mofed_version }}/MLNX_OFED_LINUX-{{ mofed_version }}-{{ ansible_facts['distribution'] | lower }}{{ ansible_facts['distribution_version'] }}-x86_64.tgz"
    dest: "/var/cache/mofed/{{ mofed_version }}.tgz"
    checksum: "sha256:{{ mofed_sha256 }}"
    mode: "0644"

- name: Unpack
  ansible.builtin.unarchive: { src: "/var/cache/mofed/{{ mofed_version }}.tgz", dest: /opt/mofed, remote_src: true, creates: "/opt/mofed/MLNX_OFED_LINUX-{{ mofed_version }}-{{ ansible_facts['distribution'] | lower }}{{ ansible_facts['distribution_version'] }}-x86_64" }

- name: Install (long-running; async protects the SSH session)
  ansible.builtin.command:
    cmd: "./mlnxofedinstall --force --without-fw-update --add-kernel-support"
    chdir: "/opt/mofed/MLNX_OFED_LINUX-{{ mofed_version }}-{{ ansible_facts['distribution'] | lower }}{{ ansible_facts['distribution_version'] }}-x86_64"
    creates: /etc/infiniband/openib.conf         # idempotency guard; better: compare `ofed_info -s` with the target version
  async: 3600
  poll: 60
  register: ofed_install
  notify: reboot node

- name: Rebuild initramfs so the new modules load early
  ansible.builtin.command: update-initramfs -u -k all
  when: ofed_install is changed and ansible_facts['os_family'] == 'Debian'

- ansible.builtin.meta: flush_handlers       # reboot now, before the NVIDIA driver build
```

The install task uses `async: 3600`, so a long build does not hold the SSH session. A kernel module build can run for many minutes, and a dropped SSH connection in the middle would leave the install half finished. With `async`, Ansible starts the job, then polls it every 60 seconds until it completes or the hour runs out. Now look at the rest of the install task, because several parts of it deserve attention. The installer replaces in-box kernel networking drivers, so version pinning, kernel matching (`--add-kernel-support` rebuilds for a running kernel) and a rollback path all matter. The rollback path matters most. If the new OFED fails on one rack, you need to know which version to reinstall, and where its tarball lives, before the change starts.

Firmware updates (`mlxfwmanager`, `--without-fw-update`) are a separate, carefully staged workflow, covered in Part 9. Keep firmware out of the same run as the driver, so a problem can be traced to one change. The idempotency guard should compare installed and requested versions (`ofed_info -s`), so that version bumps re-run the installer. The `creates:` guard in the code above only checks for a file, so it never re-runs when the version changes. DOCA-Host is the successor bundle for ConnectX and BlueField. It uses repository packages (`doca-ofed`), which are easier to automate than the ISO or tarball installer, because the package manager already tracks versions for you.

The reboot handler is the piece that makes the new driver real. Until the node reboots, the old modules keep running, so a successful install alone changes nothing on the running system. Here is the handler.

```yaml
- name: reboot node
  ansible.builtin.reboot:
    msg: "Ansible: loading new kernel/RDMA modules"
    pre_reboot_delay: 10
    reboot_timeout: 1800            # GPU servers can take 10+ minutes to POST
    post_reboot_delay: 60
    test_command: "uptime"
```

GPU servers with many GPUs and NICs POST slowly, which means the firmware tests and initializes each device before it hands control to the operating system. Memory training alone can take minutes on a large server. Give them generous timeouts, and check the BMC (the baseboard management controller, the small computer that offers remote power and console access) for stuck boots, as Part 7 describes. Decide the OFED version and the rollback path before the installer runs anywhere, because the moment to think about rollback is before anything has gone wrong.

### 3.4 nvidia_driver

The driver is where many bring-ups stall, so the role makes its decisions explicit rather than leaving them to whoever ran the last install. It keeps five decisions in variables, and each one is a question you answer once and then reuse on every node. The first is the branch: production or LTS, or a newer feature branch. A branch is a driver release line, and staying on one line keeps the CUDA libraries and the kernel modules in agreement. The second is the flavour. Open kernel modules are required on Blackwell and recommended for recent data-centre GPUs, while proprietary modules are the alternative. The third is the install method. Distribution or NVIDIA repository packages, using DKMS (Dynamic Kernel Module Support, which rebuilds the module for each new kernel) or precompiled kernel modules, are the usual choice, and the `.run` file is for special cases only, because it bypasses the package manager's tracking. The last two are the version pin and the holds. A pin fixes the exact version, and a hold tells the package manager not to upgrade it on its own.

```yaml
- name: Add the NVIDIA CUDA repository key and source (keyring-based)
  ansible.builtin.get_url:
    url: "https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub"
    dest: /etc/apt/keyrings/nvidia-cuda.asc
    mode: "0644"
- ansible.builtin.apt_repository:
    repo: "deb [signed-by=/etc/apt/keyrings/nvidia-cuda.asc] https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/ /"
    filename: nvidia-cuda
    state: present

- name: Blacklist nouveau
  ansible.builtin.copy:
    dest: /etc/modprobe.d/blacklist-nouveau.conf
    content: "blacklist nouveau\noptions nouveau modeset=0\n"
    mode: "0644"
  notify: rebuild initramfs

- name: Install the pinned driver (non-interactive)
  ansible.builtin.apt:
    name:
      - "nvidia-driver-{{ nv_driver_branch }}-server-open"       # naming varies by distro/repo: verify
      - "nvidia-utils-{{ nv_driver_branch }}-server"
    state: present
    dpkg_options: "force-confold,force-confdef"
    lock_timeout: 300
    update_cache: true
    cache_valid_time: 3600
  environment: { DEBIAN_FRONTEND: noninteractive }
  register: driver_pkg
  notify: reboot node

- name: Hold packages to prevent drift
  ansible.builtin.dpkg_selections:
    name: "{{ item }}"
    selection: hold
  loop: ["nvidia-driver-{{ nv_driver_branch }}-server-open", "nvidia-utils-{{ nv_driver_branch }}-server"]
  when: nv_hold_packages | default(true)

- ansible.builtin.meta: flush_handlers

- name: Confirm driver and expected GPU count
  ansible.builtin.command: nvidia-smi --query-gpu=driver_version,index --format=csv,noheader
  register: smi
  changed_when: false
  failed_when: (smi.stdout_lines | length) != expected_gpus or (smi.stdout_lines[0].split(',')[0] | trim) is not match('^' ~ nv_driver_branch)
```

The code comment already warns you that package names vary by distribution, so verify them on one host before you roll the role out. A typo in a package name is cheap to find on a test node and expensive to find across a rack. DKMS builds need headers and can fail after a kernel update, which is why the kernel pin and hold matter. If the kernel moves and the headers do not, DKMS has nothing to compile against, and the node boots with no GPU at all.

Upgrades follow a fixed sequence. First, unload dependent modules (`nvidia_uvm`, `nvidia_peermem`, `nvidia_drm`), because the kernel refuses to replace a module that a running module still uses. Second, stop the services that use the GPUs, such as DCGM, persistenced, exporters and containers. Third, install the new package. Last, reload the modules or reboot, depending on what the install touched. Downgrades need explicit permission variables, so an accidental older version cannot slip in through a routine run. RHEL families use `dnf` modules, such as `dnf module enable nvidia-driver:550-open`, plus `versionlock` and the same cautions. Mixing the driver from the OS repository with the one from NVIDIA's repository is a classic break, because the two packages claim the same files and the package manager cannot tell which one is correct. Pin the branch and the holds in the same change, so the driver cannot drift on its own.

### 3.5 fabric_manager, GPU tuning, MIG

On HGX and DGX systems, GPUs talk to each other through NVSwitch chips, which act like a small network switch placed inside the server board. Fabric Manager is the service that programs those switches, telling them which GPU pairs may route to which. Until Fabric Manager is running, the switches have no routing tables, and CUDA applications cannot initialize. A job that starts on such a node fails at the first CUDA call, which is confusing if you only look at the training script. The role installs Fabric Manager to match the driver branch, starts it, and then checks the fabric.

```yaml
- name: Fabric Manager matching the driver branch (NVSwitch systems: HGX/DGX)
  ansible.builtin.apt:
    name: "nvidia-fabricmanager-{{ nv_driver_branch }}"
    state: present
    dpkg_options: "force-confold,force-confdef"
- ansible.builtin.systemd_service: { name: nvidia-fabricmanager, state: started, enabled: true }
- name: Verify NVSwitch fabric is up
  ansible.builtin.command: nvidia-smi nvlink --status -i 0
  register: nvl
  changed_when: false
  failed_when: "'inactive' in nvl.stdout | lower"
```

Fabric Manager's version must exactly match the driver. The two components speak a private protocol, and a mismatch is not a small warning. The daemon refuses to start, and the node stays unusable until the versions line up again. On NVLink-switch fabrics such as GB200 NVL72, the multi-node NVLink domain uses extra components: IMEX and NVLink management software. Part 9 covers those.

The GPU tuning role handles the persistence daemon, clocks, power, ECC, compute mode and MIG. Each setting changes how the GPU behaves between jobs or during them, so each one needs a reason. The table lists each setting with its command and the situation that calls for it, and a setting with no situation in the last column should not be applied at all.

| Setting | Command | When you need it |
|---|---|---|
| Persistence | `nvidia-persistenced`, or the older `nvidia-smi -pm 1` | On every Linux GPU server, so the GPU stays initialised and its settings are kept between jobs |
| Clocks | `nvidia-smi -lgc` | When policy or acceptance benchmarks require locked clocks |
| Power limit | `nvidia-smi -pl`, or the `gpu_power_limit` module from 4.15 | When policy caps power |
| ECC and compute mode | `nvidia-smi -e` for ECC, `nvidia-smi -c EXCLUSIVE_PROCESS` for compute mode | ECC stays on for production training. Change the compute mode only when policy asks for one process per GPU |
| MIG | `nvidia-smi -mig 1`, then `nvidia-smi mig -cgi ... -C` | For multi-tenant small workloads |

Changing MIG mode may need a GPU reset or a reboot, and no processes can be running on the GPU at the moment you flip it. The role then takes an `nvidia-smi topo -m` snapshot for inventory, so the record of how the node is wired lives next to the node's facts. It installs the GDRCopy kernel module, which gives CUDA code a fast path for small host-to-GPU copies. It also loads `nvidia-peermem` at boot through `modules-load.d`, so GPUDirect RDMA is ready before the first job arrives. If non-root runtimes need device nodes, the role can set udev rules under `/etc/udev`, which control the permissions the kernel gives to `/dev/nvidia*` files.

```yaml
- name: Enable persistence daemon
  ansible.builtin.systemd_service: { name: nvidia-persistenced, state: started, enabled: true }

- name: Load GPUDirect RDMA module at boot and now
  community.general.modprobe: { name: nvidia_peermem, state: present, persistent: present }
  when: ansible_local.gpu.rdma_nics | default(0) | int > 0

- name: Configure MIG when requested
  ansible.builtin.include_tasks: mig.yml
  when: mig_profile is defined
```

Settle the MIG decision for each workload before you write the tuning role. Ask who will run on the node. A notebook pool that shares a GPU across many users wants MIG, while a multi-node training job wants the whole GPU and its NVLink path. Mixing both on one node means you must drain the node to change its mode, so decide the node's purpose first and set the role from that answer.

### 3.6 dcgm and telemetry

A node can look fine from the outside and still have a failing GPU. The server answers ping, the operating system boots, and the job starts. Only a tool that reads the GPU's own health counters shows the problem. DCGM (Data Center GPU Manager) is NVIDIA's tool for that job, and its exporter turns those counters into metrics that Prometheus can scrape. The exporter then lets you alert before a job fails, rather than after.

```yaml
- ansible.builtin.apt: { name: datacenter-gpu-manager, state: present }
- ansible.builtin.systemd_service: { name: nvidia-dcgm, state: started, enabled: true }
- name: Deploy the metrics selection for the exporter
  ansible.builtin.copy: { src: dcp-metrics-custom.csv, dest: /etc/dcgm-exporter/dcp-metrics-custom.csv, mode: "0644" }
  notify: restart dcgm-exporter
- name: Run the exporter (container or package)
  community.docker.docker_container: { ... }          # see 4.16; or systemd unit for the binary
- name: Quick health check
  ansible.builtin.command: dcgmi diag -r 1
  register: diag1
  changed_when: false
  failed_when: diag1.rc != 0 or "Fail" in diag1.stdout
```

The health check fails the task on a non-zero return code, or when the output contains `Fail`. Either signal means the node should not take work, so the play stops for that host. Expose node health to Prometheus through the DCGM exporter on port 9400, along with node_exporter, which covers the CPU and disk side of the same machine. Set labels for `cluster`, `rack` and `gpu_model`, so a query can answer "which rack shows throttling?" without a lookup table. Then make sure alerts exist for XID errors (the GPU's error codes, which the driver writes to the kernel log), ECC errors, thermal throttling, NVLink errors, PCIe replay counters and missing GPUs, as Part 17 covers.

The `dcgmi diag -r 1|2|3` levels trade time for coverage. Level 1 takes seconds and checks that the software stack is sane. Level 2 takes minutes and adds a stress pass across the hardware. Level 3 runs about 15 to 30 minutes of stress and is the most thorough. Match the level to the moment. Run quick checks on every playbook execution, and save the long level for bring-up, when a bad card is cheapest to swap.

### 3.7 container_toolkit and runtimes

Once the host driver works, the container runtime needs to know how to pass GPUs into containers. A container is isolated from the host, so the GPU device files and driver libraries must be mounted into it on purpose. The NVIDIA container toolkit does that mounting. Install `nvidia-container-toolkit`, then configure the runtime with `nvidia-ctk runtime configure --runtime=containerd|docker|crio` and restart it. The configure step edits the runtime's own config file, so the runtime knows about the NVIDIA hook. If you use CDI (Container Device Interface, a standard way to describe devices to runtimes), generate the specs with `nvidia-ctk cdi generate`. Then test with a short container that runs `nvidia-smi`. Keep the toolkit versions aligned with the driver and with the Kubernetes device plugin, which Part 11 covers. Treat that container test as your proof that the runtime can reach the GPUs. A host where `nvidia-smi` works but the container version fails has a runtime problem, not a driver problem.

### 3.8 Scheduler and Kubernetes agents

Scheduler agents come last, because a scheduler that sees a node will send it work immediately. For Slurm (the workload manager that queues and places jobs on nodes), the `slurm_client` role sets up the munge key, which authenticates messages between Slurm daemons, plus `slurm.conf` and `gres.conf`. The `gres.conf` file describes generic resources such as GPUs, and it auto-detects GPUs through NVML (the NVIDIA Management Library). The role also sets up cgroups, which fence each job's CPU and memory, and it starts `slurmd`, the daemon that runs on every compute node. For Kubernetes, the node needs a container runtime, the kubelet, and the `nvidia.com/gpu` device plugin through the GPU Operator. It also needs node labels and taints for GPU pools, so ordinary pods stay off GPU nodes, plus hugepages and topology manager settings. A node joins the scheduler only after validation succeeds, as section 5 explains. Register the node with the scheduler last, and only after the checks in section 5 pass.

## 4. Reboots, long tasks and idempotent upgrades

A driver upgrade on a busy node raises one question first: does this node need a full reboot, or only a module reload? The answer shapes the rest of the upgrade, and it decides how long the node stays out of service. A reboot can take a long time on a GPU server, while a reload can take seconds when nothing holds the device.

Put reboots where they belong, which is after kernel, OFED or driver changes that need new modules. A module is a piece of kernel code, and the running kernel keeps the copy it loaded at boot until something replaces it. Use handlers with `meta: flush_handlers`, so the play continues on a clean boot. A handler is a task that runs once, at the end of a play or at a flush point, and it fires only when another task reports a change. Do not reboot blindly. Detect the need first, by checking `/var/run/reboot-required` or `needs-restarting -r`, or by comparing running and installed module versions with `modinfo` and `cat /proc/driver/nvidia/version`. The last command prints the version of the driver the kernel is running, so it tells you what is live, and that can differ from what the package manager installed.

OFED installs, DKMS builds and large package sets can take a long time. Run them with `async` and `poll`, or set a `timeout`, so one stuck task cannot hold the whole play. Keep `forks` and `throttle` in mind as well. `forks` controls how many hosts Ansible works on at once, and `throttle` limits how many tasks run at the same time. Many parallel installs put heavy load on the package mirror, and a mirror that slows to a crawl makes every node look broken.

A reload can replace a reboot when it is safe. Picture the modules as a stack of dependent parts, where the top ones need the ones below. Stop the dependent services first, then unload `nvidia_uvm nvidia_drm nvidia_modeset nvidia` in that order, which removes the top of the stack before the base. Load the new modules with `modprobe`. If unloading fails with `rmmod: in use`, something still holds a file open, and the kernel will not let go. Find the holders with `lsof /dev/nvidia*` or `fuser -v /dev/nvidia*`, which list the processes with those device files open. If the unload still fails, fall back to a reboot. A reboot is slower, but it leaves no half-unloaded state behind.

Compare installed and desired versions explicitly. If your role only checks whether any driver is present, it will never upgrade one, because the check passes on the old driver every time. The check should ask "is this exact version here?" rather than "is some version here?"

Keep the previous package versions in the mirror, so you have something to roll back to. A rollback is only possible if the older package still exists. Use the `block/rescue` pattern from 4.8 to reinstall the previous version, and leave the node drained when validation fails. The `block` runs the upgrade, and the `rescue` runs only if the block fails, so the failure path is written down before it happens.

Stop or hold `unattended-upgrades` and the `apt-daily` timers on GPU nodes, and apply security patches in controlled windows. A background upgrade can grab the dpkg lock while your play waits for it, or install a new kernel between your driver install and your reboot. Either one breaks DKMS in a way that is hard to trace back to its cause.

Decide the reload-or-reboot path before the upgrade starts, and write the rollback steps down alongside it. Someone reading the runbook at 3 a.m. should not have to decide the path under pressure.

## 5. Validation and burn-in

A node can pass every install step and still be wrong under load. Every package installed cleanly, every service started, and the node still drops a GPU the first time it runs a heavy load. Validation is how you find that out before the node takes work, and it is the reason a fast install is not the same as a ready node.

Gate a node's entry to production with progressively heavier tests. Start with the cheap checks, because they catch most dead hardware in seconds. Only a node that passes them earns the expensive stress tests. Each test runs as a task in `gpu_validate`. The table lists the stages from cheapest to most expensive.

| Stage | Checks | Tools | Time |
|---|---|---|---|
| Inventory sanity | GPU count/model, PCIe link width and speed (x16 Gen5), NUMA mapping, NIC count/speed/state, no AER errors in `dmesg` | `nvidia-smi -q`, `lspci -vv`, `nvidia-smi topo -m`, `ibstat`, `ibdev2netdev`, `ethtool`, `dmesg` | seconds |
| Driver/health | No XID errors, ECC clean, retired pages within limits, clocks and temperatures sane, NVLink all active, Fabric Manager healthy | `nvidia-smi -q -d ECC,PAGE_RETIREMENT`, `nvidia-smi nvlink -s`, `journalctl -k \| grep -i xid`, `dcgmi health -c` | seconds |
| DCGM diagnostics | Level 1 to 3 | `dcgmi diag -r 1/2/3` | seconds to 30 min |
| Single-node stress | Thermal/power stability, ECC under load | `gpu-burn`, DCGM level 3, `nvbandwidth`, `dcgmproftester` | 10 to 30 min |
| GPUDirect/P2P | P2P and NVLink bandwidth | `nvbandwidth`, `p2pBandwidthLatencyTest`, `nvidia-smi nvlink` | minutes |
| Network | Link state, RDMA perftest (`ib_write_bw`, `ib_send_lat`) to a peer, GID/RoCE config, MTU | `perftest`, `ibv_devinfo`, `rdma link` | minutes |
| Multi-node collectives | NCCL all-reduce within tolerance of the expected bus bandwidth | `nccl-tests` (`all_reduce_perf`), `mpirun`/`srun` | minutes |

Read the table from the top. The first rows take seconds, while the stress rows take 10 to 30 minutes. A failure in an early row means the later rows never need to run, so the cheap checks save you real time across a large fleet.

The burn test runs for 30 minutes in the background. Running it as an `async` task keeps the SSH session from timing out during the run. Afterward, the play checks the kernel log as well, because a GPU can survive a stress test with a fault written only to the log.

```yaml
- name: Single-node GPU stress (30 min) in the background
  ansible.builtin.command: ./gpu_burn 1800
  args: { chdir: "{{ burn_dir }}" }
  register: burn
  async: 2100
  poll: 60
  changed_when: false

- name: No hardware errors during burn
  ansible.builtin.shell: "journalctl -k --since '-40min' | grep -Ei 'xid|nvrm.*error|fallen off the bus' || true"
  args: { executable: /bin/bash }
  register: kerr
  changed_when: false
  failed_when: kerr.stdout | length > 0 or ('faulty' in burn.stdout | lower)
```

Use your standard burn tool, pinned by commit SHA and built into your image. A commit SHA is the exact version of the code, so the same test runs on every node and every month. Do not compile it from a moving branch at test time, because a new commit upstream would change the test without anyone deciding to. Xid errors appear in the kernel log, not in the burn tool's output, so the kernel log check is not optional. The burn tool reports what it measured, and the kernel reports what the hardware complained about.

The multi-node collectives test runs from a controller or login node, as a normal user rather than root. A collective is an operation where many GPUs exchange data at once, such as an all-reduce that sums gradients across every GPU. This test is the closest thing to a real training step, so it catches problems the single-node tests miss, such as one slow rail in the fabric.

```yaml
# Multi-node NCCL test from a controller/login node (run as a normal user, not root)
- name: NCCL all_reduce across a rack
  hosts: login[0]
  become: false
  vars: { nodes_per_rack: 8, gpus_per_node: 8 }
  tasks:
    - ansible.builtin.template: { src: hostfile.j2, dest: "/tmp/hosts.{{ rack }}" }
    - name: Run nccl-tests
      ansible.builtin.command: >
        mpirun --hostfile /tmp/hosts.{{ rack }} -np {{ nodes_per_rack * gpus_per_node }} --map-by ppr:{{ gpus_per_node }}:node
        -x LD_LIBRARY_PATH -x NCCL_DEBUG=WARN -x NCCL_IB_HCA={{ nccl_ib_hca }}
        /opt/nccl-tests/build/all_reduce_perf -b 8 -e 8G -f 2 -g 1
      register: nccl
      changed_when: false
    - name: Check bus bandwidth against the expected floor
      ansible.builtin.assert:
        that: (nccl.stdout | regex_search('Avg bus bandwidth\s*:\s*([0-9.]+)', '\1') | first | float) >= expected_busbw_gbps
        fail_msg: "NCCL busbw below {{ expected_busbw_gbps }} GB/s on rack {{ rack }}"
```

Bus bandwidth expectations depend on topology, NIC speeds and message sizes. Bus bandwidth is the figure `nccl-tests` reports for how fast data moves across the GPUs, adjusted so numbers compare across different GPU counts. A rack with a different NIC layout will show a different number, and a number that is right for one rack can be wrong for another. Derive the baselines from known-good runs, and record them. Store the results as JSON artefacts with node serials, so trends and repeat offenders show up. A node that is always slightly below the floor, across many weeks, points to a real hardware or cabling problem. Tag failing nodes `quarantine` and keep them out of the scheduler until someone fixes them.

Set the expected bus bandwidth from your own known-good runs before you enforce it in an assert. A floor copied from a vendor slide will fail good nodes on your own network, and it will pass bad ones that happen to beat the slide's setup.

## 6. Day-2: drain, patch, validate, resume

Suppose a driver update must reach a fleet that is busy running training jobs. You cannot pull every node out at once, because the jobs on them would die and their work would be lost. Each node has to leave the scheduler, wait for its current job to finish, get patched and validated, and then rejoin. The pattern comes from 4.8, with GPU-aware checks added. The `serial` list below is the main safety control, because it limits how much of the fleet is in maintenance at any moment.

```yaml
- name: Patch GPU nodes safely
  hosts: gpu
  become: true
  serial: [1, "5%", "10%"]
  max_fail_percentage: 3
  vars: { scheduler_host: "{{ groups['slurm_controller'][0] }}" }
  tasks:
    - name: Drain from Slurm and wait for jobs to finish
      block:
        - ansible.builtin.command: scontrol update NodeName={{ inventory_hostname }} State=DRAIN Reason="maintenance {{ change_id }}"
          delegate_to: "{{ scheduler_host }}"
          changed_when: true
        - ansible.builtin.command: squeue -h -w {{ inventory_hostname }} -o %i
          delegate_to: "{{ scheduler_host }}"
          register: jobs
          until: jobs.stdout == ""
          retries: "{{ drain_wait_retries | default(240) }}"
          delay: 30
          changed_when: false

    - name: Apply updates
      block:
        - ansible.builtin.import_role: { name: nvidia_driver }
        - ansible.builtin.import_role: { name: gpu_validate, tasks_from: quick }
      rescue:
        - ansible.builtin.debug: { msg: "Maintenance failed on {{ inventory_hostname }}; leaving node DRAINED" }
        - ansible.builtin.fail: { msg: "Node {{ inventory_hostname }} requires investigation" }

    - name: Return to service
      ansible.builtin.command: scontrol update NodeName={{ inventory_hostname }} State=RESUME
      delegate_to: "{{ scheduler_host }}"
      changed_when: true
```

The `serial` list moves in stages: one node first, then 5 percent, then 10 percent of the fleet. The first single node acts as a canary, a test case that shows whether the change is safe before it spreads. `max_fail_percentage: 3` stops the rollout once failures pass 3 percent. The play drains the node and waits for its jobs to finish. The `until` loop checks `squeue` again every 30 seconds, up to the retry limit, and it moves on only when the node's job list is empty. It then applies the driver and runs a quick validation. If anything fails, the `rescue` block leaves the node drained and stops for investigation. A drained node keeps its running jobs but takes no new ones. Only a clean run returns the node to service.

On Kubernetes, the equivalent is `kubernetes.core.k8s_drain`, which respects PodDisruptionBudgets. A PodDisruptionBudget is a limit that tells the cluster how many replicas of an app may be down at once, so a drain does not take a serving endpoint offline all at once. Taint the node with `nvidia.com/gpu=maintenance:NoSchedule`, patch it, validate it with DCGM or NVML, and then uncordon it. Uncordon marks the node schedulable again. Under the GPU Operator, let its upgrade controller handle driver upgrades rather than changing hosts by hand, as Part 11 explains. Two owners for the same driver is the mistake to avoid here.

Fleet-wide diagnostics are read-only, so you can run them at any time, even during a busy shift, without changing anything on the nodes.

```yaml
- name: Fleet GPU health sweep
  hosts: gpu
  gather_facts: false
  become: true
  tasks:
    - name: Collect a compact health record
      ansible.builtin.shell: |
        set -o pipefail
        nvidia-smi --query-gpu=index,name,driver_version,temperature.gpu,power.draw,clocks_throttle_reasons.active,ecc.errors.uncorrected.volatile.total,pcie.link.gen.current,pcie.link.width.current --format=csv,noheader,nounits
      args: { executable: /bin/bash }
      register: health
      changed_when: false
      failed_when: false
    - ansible.builtin.copy:
        content: "{{ {'host': inventory_hostname, 'rc': health.rc, 'rows': health.stdout_lines} | to_nice_json }}"
        dest: "reports/{{ inventory_hostname }}.json"
      delegate_to: localhost
      become: false
```

The sweep writes one JSON file per host. Each file holds a row for every GPU on that node, so a single host with a missing GPU shows up as a short list. Aggregate those files into a report that counts nodes with fewer than 8 GPUs, PCIe links degraded below x16, nonzero uncorrected ECC, and active throttle reasons. A throttle reason is the GPU's own note that it slowed down, usually for heat or power. That report is a typical first step when many jobs slow down during an incident, because it turns "training is slow" into a short list of suspects. Run this sweep first when throughput drops, before you change any node, so you do not fix the wrong thing.

## 7. Incidents that shaped the design

Each incident below shaped one part of the design. Read them as stories from a real fleet, and for each one, trace the fix back to a rule you have already seen in this chapter. The rule is the lesson. The story is how you remember it under pressure.

1. A package upgrade across 256 GPU nodes stalled forever on a `dpkg` configuration-file prompt, because no terminal was attached. The cause was apt running non-interactively without a conffile policy, or competing with `unattended-upgrades`. The fix uses the `apt` module with `dpkg_options: force-confold,force-confdef`, `lock_timeout`, `DEBIAN_FRONTEND=noninteractive`, disabled unattended upgrades on nodes, and a task `timeout`.
2. A green but dead service: systemd reported a successful start, while `slurmctld` crashed seconds later on a bad `slurm.conf`. The fix verifies behaviour after every critical start (`sinfo`, `curl /health`) with `until/retries`, and validates configs before they are installed (4.7).
3. A `command` task with a database password on the command line printed that password into job logs. The fix is `no_log: true`, passing secrets through files or stdin, and scanning logs (4.12).
4. A forgotten `host_vars` file pinned one DGX to an old driver version, while `group_vars` said otherwise. The fix is to inspect with `ansible-inventory --host`, treat `host_vars` as exceptional, and add an assert or report that lists driver versions per node after each run (4.5).
5. A kernel update, applied unattended or by a different team, invalidated the DKMS module build, and nodes lost their GPUs after reboot. The fix pins kernel and driver together, holds the packages, tests updates on a canary, and uses precompiled or signed modules where Secure Boot is required, with module signing keys managed deliberately.
6. A node's ConnectX port came up at a lower speed, or one rail was down, and training ran at half speed. The fix compares link speed and state per rail with the design. Fleet sweeps record `ibstat` and `rdma link` output and flag any deviation.
7. 1,000 nodes downloading the same driver and OFED at once saturated the mirror. The fix uses `throttle`, `serial`, local caches or proxies, and preseeded images.
8. A bad GRUB parameter or module config prevented boot, and automation kept retrying reboots. The fix is a canary first, `max_fail_percentage`, and BMC out-of-band access to recover (Part 7). It also follows one rule: automation never retries a reboot without human review when a node fails to return.

Use the canary and `max_fail_percentage` settings from incident 8 on every fleet-wide change. The goal is that one bad change stays small. A canary of one node costs little, and a bad change that reaches 256 nodes before anyone notices costs a great deal more.

## 8. Lab

You can work through much of this chapter without a GPU. Start with the self-checking Python lab, which runs on your laptop and needs no hardware. It checks three things, and each one turns a rule from this chapter into a test. The first is the bring-up order validator, `validate_bringup_role_order`, which confirms that `mofed` runs before `nvidia_driver`, `nvidia_driver` before `fabric_manager`, and `gpu_validate` before `slurm_client`. The second is the health sweep classifier, `evaluate_gpu_health_sweep`, which catches GPUs that fell off the bus, uncorrected ECC errors, and PCIe `Gen4x8` degradation. The third is the parser and gate for `nccl-tests`, `parse_and_gate_nccl_busbw`, which reads the `all_reduce_perf` bus bandwidth and checks it against a floor.

```bash
python3 code/part04/ansible_gpu_cluster_lab.py
```

If you have no physical GPU, rehearse the interactive steps below with stub `nvidia-smi`, `dcgmi` and `ibstat` scripts on a plain VM. A stub is a small script that prints the output a real tool would print, so your roles see something familiar. The commands in the steps below have not been run on live hardware. Roles, ordering, handlers, reboots and validation logic still get exercised that way, and a stub catches typos in your YAML long before a real node does. Save the hardware steps for a real node, where the output can surprise you in ways a stub never will.

1. Implement `gpu_facts`, and compare the discovered counts with what you expect. Publish `ansible_local.gpu`. Test with stubs first, then on a GPU host.
2. Write the playbook from the graph, with its reboot points. Run it on a fresh VM or node. Check that `--list-tasks` shows the right order, and that a rerun reports `changed=0`, apart from validation probes.
3. Pin a branch, hold the packages, and run non-interactively with `dpkg_options`. Simulate a conffile prompt to prove the fix. Try an upgrade, then a blocked downgrade, and test the `rescue` rollback.
4. Add the async install, the checksum, version-aware idempotency, the initramfs rebuild and the reboot flush to the OFED role. Document the rollback.
5. Trigger a reboot through the handler. Check `post_reboot_delay` and `test_command`. Then test what happens when the node fails to return, using the timeout and the failure policy.
6. Set up the persistence daemon, a power limit (use the 4.15 module), a MIG profile on a MIG-capable GPU, and peermem. Verify with `nvidia-smi` and `lsmod`.
7. Deploy DCGM and the exporter, and scrape them from Prometheus. Create an alert test for a missing GPU, using a metric from a stub.
8. Implement the quick (seconds), standard (DCGM level 2) and burn (30 min) task files. Gate scheduler registration on success, and store JSON reports.
9. Run nccl-tests on two or more nodes, and record a baseline bus bandwidth for each message size. Assert against the floor. Then compare with a deliberately degraded NIC, using an MTU change or `NCCL_IB_DISABLE=1`.
10. Run the drain and resume workflow on a lab Slurm cluster, and inject a validation failure to confirm the node stays drained. Then do the Kubernetes variant with `k8s_drain` and a PDB.
11. Run the health sweep across many simulated nodes, aggregate the results into a table, and flag the outliers.
12. Reproduce the interactive `dpkg` hang, the green-but-dead service and the stale `host_vars` precedence problem. Fix each one with the patterns above.
13. Clean up the nodes, VMs and cloud GPUs when you finish.

Work through the steps in order, because each one builds on the one before it.

## 9. Common mistakes

Most of these mistakes are shortcuts that looked reasonable at the time. A shortcut saves ten minutes on the day it is written and costs a night of recovery later. Seeing the mistakes grouped makes them easier to spot in a pull request, so the groups below are the checklist to hold up when you review a GPU role.

- Ordering: installing the NVIDIA driver before the RDMA stack, or skipping the reboot or module reload between them.
- Versions: letting packages float with `state: latest`, letting `unattended-upgrades` change kernels and drivers, or mixing kernel, headers, driver branch, Fabric Manager and DCGM versions.
- Health: treating "service started" as "node healthy", skipping burn-in and collectives tests, or retrying reboots on nodes that do not return.
- Rollout: going fleet-wide without a canary or `max_fail_percentage`, or leaving a half-configured node visible to the scheduler after a role fails halfway.
- Reproducibility: hard-coded package names across distributions, benchmark tools built from moving branches, and no record of results, so repeat-offender nodes go unnoticed.
- Safety: secrets in command lines and verbose logs, and Ansible driver changes underneath the GPU Operator, which gives the same component two managers.

Review your roles against the ordering and version mistakes first. The health and rollout mistakes are easier to fix once the ordering is right, because a correct order makes every later check mean what it says.

## 10. Interview angles

Use these questions to test whether you can explain the chapter out loud.

- "Walk through bringing up a new DGX/HGX node with Ansible from bare OS to schedulable." Cover the order, the reboots, the validation, and the scheduler last.
- "How do you upgrade GPU drivers across a running cluster?" Cover the drain, the canary, DKMS and headers, the holds, validation and rollback.
- "Why install MOFED before the NVIDIA driver? What is nvidia-peermem?"
- "How do you validate a node before releasing it to users?" Cover the DCGM diag levels, burn-in, the NVLink, PCIe and IB checks, and an NCCL test.
- "A playbook upgrading packages hangs on 200 nodes. Diagnose." Cover the dpkg prompt, locks, unattended upgrades, non-interactive mode, and timeouts.
- "How do you keep GPU nodes consistent over time?" Cover golden images, pins, drift checks, scheduled `--check` runs, and fleet sweeps.
- "How do you coordinate with Slurm or Kubernetes during maintenance?" Cover drain and cordon, PDBs, and resuming only after validation.
- "How do you detect a degraded node whose job is merely slow?" Cover link speeds, throttle reasons, ECC, and an NCCL baseline.

## Exercises

Work through these exercises after you have read the chapter and run the lab. Compare your answers with the lab output, and check the code you read against the lines it names.

1. Your bring-up run shows `nvidia_driver` ahead of `mofed` in the task list. Use `validate_bringup_role_order()` in `code/part04/ansible_gpu_cluster.py` to find the failing pair. Why must the MOFED or DOCA stack and its reboot finish first?
2. A node with NVSwitch chips refuses to start Fabric Manager after a driver bump. Why must the Fabric Manager version match the exact driver version?
3. A Slurm node registers before `gpu_validate` finishes, and a job lands on a bad GPU. What order rule did the playbook break?
4. A host reports 7 GPUs where the inventory expects 8. How does `gpu_facts` count the GPUs with `lspci -d 10de:`, and where does it publish the result?
5. *AI Systems Performance Engineering*, Chapter 3, sets the `performance` CPU governor and disables deep C-states. How does that stop the GPU from sitting idle between kernels?
6. The kubelet runs with `--topology-manager-policy=single-numa-node`. Why does that keep a pod's CPU and GPU on one socket?
7. A package upgrade hangs on a conffile prompt across 200 nodes. Which two settings stop the prompt?
8. A reboot on a large GPU server times out after 600 seconds. Why does `reboot_timeout: 1800` fix it?
9. A training job's first CUDA call is slow on an idle node. What does `nvidia-persistenced` keep alive between jobs?
10. A notebook pool and a training pool share the same hardware class. Name two Blackwell B200 MIG profiles, and say when the training job turns MIG off.
11. A burn-in must finish within one maintenance window. How do `dcgmi diag -r 1`, `-r 2` and `-r 3` differ by time and coverage?
12. A stress test exits with code 0, yet the node later drops a GPU. Trace the validation stages from PCIe and NVLink checks up to `gpu-burn`, and say where `journalctl -k` fits.
13. A rack reports a bus bandwidth just below its floor. Use `parse_and_gate_nccl_busbw()` to follow the multi-node assertion and say what it returns.
14. A fleet sweep shows one node with 7 of 8 GPUs, a `Gen4x8` PCIe link, and uncorrected ECC. Use `evaluate_gpu_health_sweep()` to explain why the node is flagged.
15. A kernel patch must reach a Slurm partition and a Kubernetes pool. Trace the maintenance workflow, and say where `k8s_drain` fits.

## Checkpoint questions (20)

<details>
<summary>1. Why must the RDMA stack (`MLNX_OFED` / `DOCA-Host`) be installed and booted BEFORE the NVIDIA GPU driver and `nvidia-peermem`?</summary>

GPUDirect RDMA depends on the `nvidia_peermem` kernel module. That module registers GPU HBM memory pages directly with the Mellanox/NVIDIA InfiniBand/RoCE kernel IB core (`ib_core` / `mlx5_core`), using peer-memory client symbols. If the NVIDIA driver is built or loaded before the matching OFED or DOCA modules are installed and loaded, `modprobe nvidia_peermem` fails with `Invalid argument` or unresolved symbol errors. All inter-node NCCL traffic then falls back through host system RAM.
</details>

<details>
<summary>2. What does `gpu_facts` check via `lspci` before installing any drivers, and why is `/etc/ansible/facts.d/gpu.fact` useful?</summary>

Before any driver goes in, `lspci -d 10de:` lists the physical GPU functions (shown as `3D controller` or `VGA`) and the NVSwitch functions. The vendor ID `0x10de` is NVIDIA. `lspci -d 15b3:` lists the ConnectX and BlueField RDMA NICs, where `0x15b3` is Mellanox's vendor ID. Comparing the PCIe count with `expected_gpus` (`8`) catches a dead riser or a GPU that fell off the bus. That check comes before you waste 30 minutes installing software. Writing `/etc/ansible/facts.d/gpu.fact` then gives later roles the values `ansible_local.gpu.nvswitch` and `ansible_local.gpu.rdma_nics`, so they can enable Fabric Manager and `nvidia_peermem` only where they apply.
</details>

<details>
<summary>3. When is `nvidia-fabricmanager` required, and what happens if its version does not exactly match the NVIDIA driver?</summary>

You need `nvidia-fabricmanager` on systems with NVSwitch chips. Examples are 8-GPU HGX and DGX A100, H100, H200 and B200 nodes, where all-to-all NVLink traffic routes through baseboard NVSwitches. Fabric Manager programs the NVSwitch routing tables. Until `nvidia-fabricmanager` runs, CUDA applications cannot initialize and report `cudaErrorSystemNotReady`. Its package version must match the exact driver version string, for example both `550.90.07`. If the versions differ, the daemon refuses to start.
</details>

<details>
<summary>4. In *AI Systems Performance Engineering* Chapter 3, how do CPU sleep states (`C-states`) and CPU frequency governors cause \"GPU bubbles\", and how does Ansible prevent them?</summary>

The GPU does the heavy matrix multiplications, but the host CPU must wake up at the end of every kernel or step. It queues the next CUDA stream operations and fills pinned memory buffers. If CPU cores drop into deep power-saving C-states, or run at low frequencies under `powersave` or `ondemand`, the wake-up delay opens GPU bubbles. A GPU worth $30,000+ then sits at 0% utilization, waiting on a sleeping CPU core. Ansible prevents this by setting the `performance` governor (`cpupower frequency-set -g performance`) and capping `processor.max_cstate` and `intel_idle.max_cstate` in GRUB.
</details>

<details>
<summary>5. Why does crossing NUMA nodes between a CPU data-loader worker and its target GPU hurt performance (*AI Systems Performance Engineering* Chapter 3), and how do you configure NUMA alignment?</summary>

On a dual-socket server, half the PCIe root complexes (GPUs 0–3 and NICs 0–3) attach to socket 0, NUMA node 0. The other half (GPUs 4–7 and NICs 4–7) attach to socket 1, NUMA node 1. If a CPU worker on NUMA node 0 copies pinned host memory (`H2D`) to GPU 4 on NUMA node 1, every byte crosses the inter-socket UPI or Infinity Fabric link. That nearly doubles latency and cuts PCIe bandwidth. Use `nvidia-smi topo -m` to inspect the topology, and disable automatic kernel NUMA page migration with `kernel.numa_balancing = 0`. Then set the kubelet to `--topology-manager-policy=single-numa-node` and `--cpu-manager-policy=static`.
</details>

<details>
<summary>6. How does Grace Blackwell (`GB200 NVL72`) change the CPU-to-GPU and multi-node interconnect architecture (*AI Systems Performance Engineering* Chapter 3)?</summary>

Grace Blackwell changes two links. The first is the CPU-to-GPU link. Instead of PCIe Gen5 at 64 GB/s unidirectional, the Grace Arm CPU and the Blackwell GPU connect over NVLink-C2C at up to 900 GB/s. They share one hardware-coherent virtual address space, which the hardware Address Translation Service (ATS) supports. The second is the rack-scale GPU-to-GPU link. 72 Blackwell GPUs across 18 compute trays connect through 9 NVLink Switch trays into one NVLink-5 domain. That domain delivers 1.8 TB/s per GPU, or 130 TB/s of aggregate bidirectional bandwidth, and multi-node NVLink fabric software and IMEX (Internode Memory Exchange) channels manage it.
</details>

<details>
<summary>7. Why did a package upgrade playbook hang indefinitely across 256 GPU nodes in Section 7, and what five settings prevent it?</summary>

The playbook hung because `apt` or `dpkg` hit a modified configuration file on the target nodes. It then prompted on stdin with `What would you like to do about modified configuration file...`, but no terminal was attached. It could also wait forever on an `apt` lock held by `unattended-upgrades`. Five controls prevent this:
1. `environment: { DEBIAN_FRONTEND: noninteractive }`
2. `dpkg_options: "force-confold,force-confdef"` on the `apt` module.
3. `lock_timeout: 300` on the `apt` module, so lock contention fails cleanly after 5 minutes.
4. Disable `unattended-upgrades` (`apt-daily.timer`) on production GPU nodes, and hold kernel and driver packages with `dpkg_selections: { selection: hold }`.
5. Set a task-level `timeout:` (`timeout: 1800`).
</details>

<details>
<summary>8. How do you prevent automatic kernel updates from breaking DKMS NVIDIA and OFED kernel modules after a reboot?</summary>

If `apt upgrade` installs a new Linux kernel image (`linux-image-generic`) without matching `linux-headers-$(uname -r)`, or DKMS fails to compile the driver against the new kernel ABI, the node boots into the new kernel with no `nvidia.ko` or `mlx5_core.ko` modules. Three steps prevent this.
1. Install `linux-headers-{{ target_kernel_version }}` alongside the kernel image.
2. Pin and hold the kernel, headers, OFED or DOCA, the NVIDIA driver and `nvidia-fabricmanager` together, as one tested set. The mechanisms are `dpkg_selections: hold` and `yum versionlock`.
3. Prefer precompiled, signed driver packages when UEFI Secure Boot is enabled.
</details>

<details>
<summary>9. Why do bare-metal GPU servers need `reboot_timeout: 1800` and `post_reboot_delay: 60` on `ansible.builtin.reboot`?</summary>

An 8-GPU HGX or DGX server carries 1.5–2 TiB of DDR5 ECC RAM, 8 H100 or B200 GPUs, 6 NVSwitches, and 8 to 10 ConnectX-7 or BlueField NICs. Such a server routinely takes 8 to 15 minutes for UEFI POST, memory training, PCIe bus enumeration and BMC handshakes. The default, `reboot_timeout: 600`, gives only 10 minutes, so it times out and marks healthy servers `FAILED` mid-POST. Setting `reboot_timeout: 1800` gives 30 minutes, and `post_reboot_delay: 60` handles enterprise POST times reliably.
</details>

<details>
<summary>10. What does `nvidia-persistenced` do, and why should it always be enabled on Linux GPU servers?</summary>

When no user process has `/dev/nvidia*` open on Linux, the NVIDIA kernel driver tears down the GPU hardware state. The next `nvidia-smi` or CUDA start then pays a multi-second initialization delay across 8 GPUs, and any applied power or clock settings reset. The `nvidia-persistenced` systemd service keeps the GPU device state initialized in the kernel with minimal power overhead. That is why you should enable it on every Linux GPU server.
</details>

<details>
<summary>11. Should ECC (`Error-Correcting Code`) memory be enabled or disabled on AI training and inference clusters (*AI Systems Performance Engineering* Chapter 3)?</summary>

Keep ECC enabled in production with `nvidia-smi -e 1`. Disabling ECC frees a small fraction of HBM capacity. At thousand-GPU scale, though, bit flips in HBM happen regularly. Without ECC, a silent single-bit or double-bit corruption can inject `NaN` values into model weights during a multi-day run, or crash the job hours later. Watch the volatile and aggregate corrected and uncorrected ECC counters, along with retired pages, using `nvidia-smi -q -d ECC,PAGE_RETIREMENT`.
</details>

<details>
<summary>12. When should you use Multi-Instance GPU (`MIG`) versus full GPUs, and what is required to change MIG mode in Ansible?</summary>

- Use MIG for multi-tenant small-model inference, development notebooks and CI jobs that do not saturate a full H100 or B200 GPU. MIG partitions SMs, HBM bandwidth, L2 cache and copy engines into isolated instances. Examples are `1g.23gb`, `2g.45gb` and `3g.90gb` on B200, or `1g.10gb` and `3g.40gb` on A100 and H100. Each instance gets hard fault and QoS isolation.
- For large distributed training or large LLM tensor-parallel inference, keep MIG disabled, so the workload uses the whole GPU and the NVLink fabric.
- To change MIG mode in Ansible, run `nvidia-smi -i 0 -mig 1`. That needs zero active processes on the GPU. You often also need a GPU reset with `nvidia-smi -r`, or a node reboot, before you create GPU Instances (`-cgi`) and Compute Instances (`-C`).
</details>

<details>
<summary>13. How do `dcgmi diag -r 1`, `-r 2`, and `-r 3` differ, and when do you run each level?</summary>

- `dcgmi diag -r 1` takes seconds. It checks software, the driver, the NVML library, persistence mode and basic device presence. Run it on every playbook execution and in the pre-job prologue.
- `dcgmi diag -r 2` takes about 2 minutes. It checks hardware, PCIe and NVLink bandwidth, and memory. Run it after driver or OS maintenance, in `post_tasks`, before you resume the node.
- `dcgmi diag -r 3` takes 15 to 30 minutes. It runs extended thermal, power, SM stress, memory and EUD hardware burn-in. Run it during initial bring-up with `gpu_bringup.yml`, and for post-RMA hardware qualification.
</details>

<details>
<summary>14. Why must you check `journalctl -k` (or `dmesg`) after running `gpu-burn`, rather than relying only on `gpu-burn`'s exit code?</summary>

Hardware faults that appear under heavy thermal and power load go to the kernel log, not the burn tool's output. Examples include NVIDIA XID errors, such as `Xid 79: GPU has fallen off the bus`, `Xid 48: Double Bit ECC Error`, `Xid 74: NVLink Error` and `Xid 63: Row Remapping`. PCIe AER errors and thermal throttling also land there. The `nvidia` kernel module writes them to the Linux kernel ring buffer, which you read with `dmesg` or `journalctl -k`. A short stress tool can still exit `0` after a non-fatal XID or a PCIe replay storm during the run, so the exit code alone does not tell you the node is healthy.
</details>

<details>
<summary>15. How does the Multi-Node `nccl-tests` (`all_reduce_perf`) validation play work, and why is it run as a non-root user?</summary>

The play fills in an MPI hostfile for the rack or batch, and then runs `mpirun --hostfile /tmp/hosts.r01 -np 64 --map-by ppr:8:node -x NCCL_DEBUG=WARN -x NCCL_IB_HCA=... /opt/nccl-tests/build/all_reduce_perf -b 8 -e 8G -f 2 -g 1`. It parses `# Avg bus bandwidth : <GB/s>` and asserts that the value exceeds `expected_busbw_gbps`. The play runs with `become: false`, as a standard user. OpenMPI refuses to run as root by default without `--allow-run-as-root`. Running user-space collective benchmarks as root across the cluster is also an unnecessary security risk.
</details>

<details>
<summary>16. What is the \"Silent Half-Fabric\" failure mode on a GPU node, and how does Ansible validation catch it?</summary>

Take an 8-rail GPU node, with 8 GPUs paired with 8 ConnectX-7 400G NICs. Suppose one PCIe slot drops from `Gen5 x16` to `Gen4 x8`, or one InfiniBand or RoCE port links up at `100G` instead of `400G`, or that port is `Down`. `nvidia-smi` still reports 8 healthy GPUs. Every multi-node all-reduce scheduled onto that node, though, waits on the slowest rail. The job then runs at half speed across all 64+ nodes in the job. Validation catches this. It asserts `pcie.link.gen.current == 5` and `pcie.link.width.current == 16`. It also checks that every `ibstat` or `rdma link` port is `Active` at `400` Gbps, and that `all_reduce_perf` bus bandwidth is above the threshold.
</details>

<details>
<summary>17. How do you unload and reload the NVIDIA kernel modules without rebooting the server, and how do you find processes blocking `rmmod`?</summary>

1. Stop all user jobs, containers, `dcgm-exporter`, `nvidia-dcgm`, `nvidia-fabricmanager` and `nvidia-persistenced`.
2. Unload the kernel modules in reverse dependency order with `modprobe -r nvidia_peermem nvidia_uvm nvidia_drm nvidia_modeset nvidia`.
3. If `rmmod` fails with `Module nvidia is in use`, find the process holding a device file open with `fuser -v /dev/nvidia*` or `lsof /dev/nvidia*`, and stop it. If a kernel reference stays held, fall back to the full `ansible.builtin.reboot` handler.
</details>

<details>
<summary>18. If your Kubernetes cluster runs the NVIDIA GPU Operator, which roles in `gpu_bringup.yml` should Ansible skip?</summary>

When the NVIDIA GPU Operator runs on Kubernetes with `driver.enabled=true` and `toolkit.enabled=true`, it manages the driver, `nvidia-container-toolkit`, the Kubernetes device plugin, DCGM, DCGM Exporter and MIG Manager. It runs them as DaemonSet pods inside the cluster. If Ansible also installs `nvidia-driver-*` and `datacenter-gpu-manager` on the host, the host packages and the Operator containers fight over the kernel modules and `/dev/nvidia*`. You have two options. Let the GPU Operator own the driver, toolkit and DCGM, and limit Ansible to the base OS, kernel tuning, MOFED and kubelet. Or pre-install the driver on the host with Ansible, and set `driver: { enabled: false }` in the GPU Operator Helm values.
</details>

<details>
<summary>19. What does the read-only `fleet_diag.yml` health sweep collect, and why is it the first tool to run when training throughput drops?</summary>

`fleet_diag.yml` runs one fast, non-disruptive `nvidia-smi --query-gpu=index,name,driver_version,temperature.gpu,power.draw,clocks_throttle_reasons.active,ecc.errors.uncorrected.volatile.total,pcie.link.gen.current,pcie.link.width.current --format=csv,noheader,nounits` command on all GPU nodes in parallel. It sets `gather_facts: false` and `changed_when: false`, and writes `reports/<host>.json` on the controller. In under 15 seconds across 500 nodes, it reveals nodes with missing GPUs (fewer than 8), mismatched driver versions, thermal or power clock throttling, uncorrected volatile ECC errors, or degraded PCIe lanes. That is why it is the first tool to run when training throughput drops.
</details>

<details>
<summary>20. Why must automation NEVER automatically retry rebooting a bare-metal GPU node in a loop when `ansible.builtin.reboot` times out?</summary>

If a GPU server does not return within `reboot_timeout: 1800` after a kernel, GRUB or firmware update, it is likely stuck. It may be in UEFI POST, in an initramfs emergency shell, or hung on a PCIe fatal error. Repeated IPMI or Redfish hard power cycles can corrupt filesystems, or brick a BMC or NIC firmware staging step in progress. The playbook should instead leave the node `DRAIN`ed in Slurm or cordoned in Kubernetes, and halt that host. `max_fail_percentage` then guards the rest of the fleet. An engineer should inspect the Redfish Serial-over-LAN (`SoL`) or the virtual console.
</details>

## Sources and review notes

- **Sources read in full:**
  - `ai-systems-performance-engineering` — Chris Fregly, *AI Systems Performance Engineering*, **Chapter 3: OS, Docker, and Kubernetes Tuning for GPU-Based Environments** (read in full: Linux OS kernel and driver interaction, avoiding CPU-induced GPU bubbles via BIOS High Performance profile, `performance` CPU frequency governor, and disabling deep C-states; NUMA node locality via `nvidia-smi topo -m`, `numactl`, `psutil.Process().cpu_affinity`, `_libnuma`, and Grace Blackwell NVLink-C2C `900 GB/s` coherent memory + NVL72 `130 TB/s` aggregate / `1.8 TB/s` per GPU; `transparent_hugepage=madvise`, `vm.swappiness=1`, checkpoint write-back tuning `vm.dirty_background_ratio`/`vm.dirty_ratio`, `jemalloc`/`tcmalloc`; `nvidia-persistenced`, ECC `-e 1`, clock locking `-lgc` for reproducible benchmarks, and Blackwell B200 MIG profiles `Table 3-1` `1g.23gb`..`7g.180gb`; `/dev/shm` sizing for NCCL; and Kubernetes `--topology-manager-policy=single-numa-node` and `--cpu-manager-policy=static`).
  - `ansible-up-and-running-3rd-edition` — Bas Meijer, Lorin Hochstein & René Moser, *Ansible: Up and Running*, 3rd ed. (Ansible role architecture, handlers, `async`/`poll`, `block`/`rescue`, and `dpkg_options` mechanics).
  - `nvidia-devops` (`volume-10/04-ansible-for-infrastructure-automation.md`): MOFED role and reboot flow, Fabric Manager and DCGM roles, non-interactive `apt` troubleshooting, green-but-dead service verification, `gpu-burn` and `nccl-tests` diagnostic playbooks.
- **Run here:** `python3 code/part04/ansible_gpu_cluster_lab.py` (3 passed, 0 failed).
- **Explicitly labelled inferences:** The `validate_bringup_role_order`, `evaluate_gpu_health_sweep`, and `parse_and_gate_nccl_busbw` models in `code/part04/ansible_gpu_cluster.py`, the 11-role `gpu_bringup.yml` dependency DAG, and the `fleet_diag.yml` sweep are the author's constructions synthesizing *AI Systems Performance Engineering*, Chapter 3, *Ansible: Up and Running*, and `volume-10/04` (plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, and 35).
- **Not verified on live hardware:** Live `mlnxofedinstall`, `nvidia-smi`, `nvidia-fabricmanager`, `dcgmi diag`, `gpu_burn`, `mpirun ... all_reduce_perf`, and `scontrol` executions (`10de:`, `15b3:`, `3600`s async, `1800`s reboot timeout, `550`, `9400`, `2100`s burn, `-b 8 -e 8G`, `256` / `1,000` nodes) are marked where not executed by `ansible_gpu_cluster_lab.py`.
