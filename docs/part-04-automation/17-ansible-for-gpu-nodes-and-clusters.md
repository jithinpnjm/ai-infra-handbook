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
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

This is where the previous chapters meet the hardware. A GPU node is only useful when a long chain of dependent components is correct and mutually compatible: BIOS and firmware settings, a kernel with matching headers, RDMA networking drivers (MLNX_OFED/DOCA), the NVIDIA driver, `nvidia-persistenced`, Fabric Manager on NVSwitch systems, GPUDirect modules (`nvidia-peermem`), DCGM and exporters for telemetry, the container toolkit, kernel tuning, filesystem mounts and the scheduler or Kubernetes agent. Get the order wrong and you debug `modprobe` failures; get versions wrong and a fleet silently runs at half speed; skip validation and the first sign of a bad node is a failed 64-node training job. Ansible's job here is to make node bring-up, upgrade and repair **deterministic, ordered, verified and repeatable** across hundreds or thousands of machines.

## Prerequisites and outcomes

Needs 4.3 to 4.16 and Linux/GPU basics from Parts 1, 9 and 10 (details of drivers, CUDA and NVLink appear there). After this chapter you can:

- Describe the dependency order of a GPU node stack and encode it in roles and playbooks with correct reboot points.
- Write roles for kernel/OS prerequisites, MLNX_OFED/DOCA, NVIDIA driver (package and runfile paths), Fabric Manager, DCGM, container toolkit, MIG, persistence mode, clocks/power, hugepages/NUMA/IRQ tuning, and monitoring agents.
- Handle reboots, long installs (`async`), package pinning/holds, DKMS vs precompiled modules, and rollback safely.
- Validate nodes (GPU count, NVLink/NVSwitch state, ECC, PCIe link width/speed, IB link state, DCGM diagnostics, burn-in, NCCL tests) and gate scheduling on the result.
- Implement drain → patch → validate → resume workflows for Slurm and Kubernetes, canary rollouts, and fleet-wide diagnostics.
- Recognise and avoid the classic incidents: interactive `dpkg` prompts, "green but dead" services, secrets leaking to logs, precedence surprises, kernel/driver mismatches.

## 1. The node bring-up dependency graph

```mermaid
flowchart TB
  F["Firmware & BIOS\n(virtualisation/IOMMU, SR-IOV, NPS, power profile, PCIe settings)"] --> OS["OS install / image\n(kernel, headers, base packages, time sync, users)"]
  OS --> K["Kernel params & tuning\n(hugepages, IOMMU, isolcpus, sysctl, limits)"]
  K --> OFED["MLNX_OFED / DOCA\n(RDMA, ConnectX/BlueField drivers)"]
  OFED --> R1(("reboot / module reload"))
  R1 --> DRV["NVIDIA driver\n(open or proprietary; DKMS or precompiled)"]
  DRV --> R2(("reboot / reload"))
  R2 --> FM["Fabric Manager\n(NVSwitch systems)"]
  DRV --> PM["nvidia-persistenced\npersistence mode, clocks, power cap, MIG"]
  DRV --> PEER["nvidia-peermem / GDRCopy\n(GPUDirect RDMA)"]
  FM --> DCGM["DCGM + exporter\n(telemetry, health)"]
  PM --> DCGM
  PEER --> CT["Container toolkit\n(runtime config)"]
  DCGM --> VAL["Validation & burn-in\n(DCGM diag, NCCL tests)"]
  CT --> VAL
  VAL --> SCH["Scheduler / Kubernetes agent\n(slurmd, kubelet, GPU Operator parts)"]
  SCH --> OK["Node released to workloads"]
```

Rules distilled from the graph: install RDMA stack **before** the GPU driver whose peer-memory module binds to it; reboot or reload modules at each boundary where kernel modules change; start Fabric Manager only after a matching driver is loaded and before CUDA workloads run; validate **before** the scheduler sees the node; register with the scheduler last. If you use the GPU Operator on Kubernetes, it can manage the driver container, toolkit and DCGM itself (Part 11), and Ansible's role narrows to OS, kernel, OFED, and kubelet.

## 2. Project structure

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

A single bring-up playbook should read like the graph:

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

## 3. Roles in detail

### 3.1 gpu_facts: know the hardware before changing it

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

Compare the discovered count with the inventory's intended `expected_gpus`: a mismatch (a GPU fallen off the bus after a failed power cycle) must stop the bring-up and raise a hardware ticket rather than continue.

### 3.2 base_os and kernel_tuning

- Time sync (`chrony`), consistent users/UIDs (SSSD/LDAP or static), SSH hardening, package repos (internal mirrors), `unattended-upgrades` disabled or controlled (a competing apt process caused the incident in section 7), kernel version pinned (`dpkg_selections hold` or `versionlock`) and **matching headers** installed for DKMS (`linux-headers-$(uname -r)`).
- Kernel parameters via GRUB drop-ins (`GRUB_CMDLINE_LINUX_DEFAULT`): `intel_iommu=on iommu=pt`/`amd_iommu=on`, `default_hugepagesz=1G hugepagesz=1G hugepages=N` where used, `isolcpus`/`nohz_full` only if justified, `numa_balancing=disable` (sysctl), `transparent_hugepage=madvise`, `pci=realloc` situations, `processor.max_cstate`; apply with `update-grub`/`grub2-mkconfig` and a controlled reboot. Sysctls for networking and memory (`net.core.rmem_max`, `vm.max_map_count`, `vm.swappiness=1`), `limits.d` (memlock unlimited for RDMA, nofile high), tuned/`cpupower` governors, IRQ affinity (`irqbalance` policy or explicit pinning for NICs), `ulimit` in systemd units, disable unneeded services, and consistent `/dev/shm` sizes for NCCL/PyTorch. (Details in Parts 1, 9, 12.)

### 3.3 mofed (MLNX_OFED / DOCA-Host)

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

Considerations: the installer replaces in-box kernel networking drivers, so version pinning, kernel matching (`--add-kernel-support` rebuilds for a running kernel), and a rollback path matter; firmware updates (`mlxfwmanager`, `--without-fw-update`) are a separate, carefully staged workflow (Part 9); the idempotency guard should compare installed versus requested (`ofed_info -s`) so version bumps re-run the installer; DOCA-Host (the successor bundle for ConnectX/BlueField) uses repository packages (`doca-ofed`) which are easier to automate than the ISO/tarball installer.

The reboot handler:

```yaml
- name: reboot node
  ansible.builtin.reboot:
    msg: "Ansible: loading new kernel/RDMA modules"
    pre_reboot_delay: 10
    reboot_timeout: 1800            # GPU servers can take 10+ minutes to POST
    post_reboot_delay: 60
    test_command: "uptime"
```

Servers with many GPUs and NICs have slow POST and memory training; set generous timeouts and verify the BMC for stuck boots (Part 7).

### 3.4 nvidia_driver

Decisions encoded as variables: **branch** (production/LTS vs new feature), **flavour** (open kernel modules, required on Blackwell and recommended for recent data-centre GPUs, vs proprietary), **install method** (distribution/NVIDIA repo packages with DKMS or precompiled kernel modules; `.run` file only for special cases), **version pin**, and **holds**.

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

Real-world details: package names differ across distributions and NVIDIA repository layouts; DKMS builds need headers and can fail after kernel updates (hence the kernel pin and hold); upgrades must unload dependent modules (`nvidia_uvm`, `nvidia_peermem`, `nvidia_drm`), stop services using the GPUs (DCGM, persistenced, exporters, containers), install, and reload or reboot; **downgrades** need explicit permission variables. RHEL families use `dnf` modules (`dnf module enable nvidia-driver:550-open`), `versionlock`, and the same cautions. Mixing the driver from the OS and from NVIDIA repos is a classic break.

### 3.5 fabric_manager, GPU tuning, MIG

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

(Fabric Manager's version must exactly match the driver; on NVLink-switch fabrics such as GB200 NVL72 the multi-node NVLink domain uses additional components (IMEX, NVLink management software); see Part 9.)

GPU tuning role tasks: `nvidia-persistenced` enabled (or persistence mode via `nvidia-smi -pm 1`), application clocks / locked clocks if policy dictates (`nvidia-smi -lgc`), power limits (`-pl`; the `gpu_power_limit` module from 4.15), ECC mode, compute mode (`EXCLUSIVE_PROCESS` vs default), **MIG** (`nvidia-smi -mig 1`, create GPU/compute instances with `nvidia-smi mig -cgi ... -C`; changing MIG mode may need GPU reset or reboot and no processes on the GPU), `nvidia-smi topo -m` snapshot for inventory, GDRCopy kernel module, `nvidia-peermem` loaded at boot (`modules-load.d`), and `/etc/udev` rules/permissions for device nodes if non-root runtimes require them.

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

### 3.6 dcgm and telemetry

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

Expose node health to Prometheus (DCGM exporter on 9400, node_exporter), set labels (`cluster`, `rack`, `gpu_model`), and make sure alerts exist for XID errors, ECC, thermal throttling, NVLink errors, PCIe replay counters and missing GPUs (Part 17). `dcgmi diag -r 1|2|3` levels trade time for coverage: level 1 seconds, level 2 minutes, level 3 about 15 to 30 minutes of stress.

### 3.7 container_toolkit and runtimes

Install `nvidia-container-toolkit`, configure the runtime (`nvidia-ctk runtime configure --runtime=containerd|docker|crio`, then restart the runtime), generate CDI specs if used (`nvidia-ctk cdi generate`), and test with a short container running `nvidia-smi`. Keep versions aligned with the driver and with the Kubernetes device plugin (Part 11).

### 3.8 Scheduler and Kubernetes agents

Last: `slurm_client` (munge key, `slurm.conf`, `gres.conf` auto-detect via NVML, cgroups, `slurmd`), or Kubernetes node prerequisites (container runtime, kubelet, `nvidia.com/gpu` device plugin through the GPU Operator, node labels/taints for GPU pools, hugepages and topology manager settings). A node joins the scheduler only after validation succeeds (section 5).

## 4. Reboots, long tasks and idempotent upgrades

- **Where reboots belong**: after kernel/OFED/driver changes that need new modules; use handlers plus `meta: flush_handlers` so the play continues on a clean boot. Detect need instead of rebooting blindly (`/var/run/reboot-required`, `needs-restarting -r`, comparing running vs installed module versions with `modinfo` and `cat /proc/driver/nvidia/version`).
- **Long installs** (OFED, driver DKMS builds, large package sets): `async`/`poll` or `timeout`, and plenty of `forks`/`throttle` awareness for mirror load.
- **Reload instead of reboot** when safe: stop dependent services, unload `nvidia_uvm nvidia_drm nvidia_modeset nvidia` in order, `modprobe` new ones; fall back to reboot if module unload fails (`rmmod: in use`) — find holders with `lsof /dev/nvidia*`, `fuser -v /dev/nvidia*`.
- **Version-aware idempotency**: compare installed and desired versions explicitly; a role that only checks "is any driver present" will never upgrade.
- **Rollback**: keep the previous package versions available in the mirror; use the `block/rescue` pattern from 4.8 to reinstall the previous version, and leave the node drained when validation fails.
- **Package locks and unattended upgrades**: stop or hold `unattended-upgrades` and `apt-daily` timers on GPU nodes (security patches via controlled windows), otherwise dpkg locks and surprise kernel updates will break DKMS.

## 5. Validation and burn-in

Gate a node's entry to production with progressively heavier tests, each as tasks in `gpu_validate`:

| Stage | Checks | Tools | Time |
|---|---|---|---|
| Inventory sanity | GPU count/model, PCIe link width and speed (x16 Gen5), NUMA mapping, NIC count/speed/state, no AER errors in `dmesg` | `nvidia-smi -q`, `lspci -vv`, `nvidia-smi topo -m`, `ibstat`, `ibdev2netdev`, `ethtool`, `dmesg` | seconds |
| Driver/health | No XID errors, ECC clean, retired pages within limits, clocks and temperatures sane, NVLink all active, Fabric Manager healthy | `nvidia-smi -q -d ECC,PAGE_RETIREMENT`, `nvidia-smi nvlink -s`, `journalctl -k \| grep -i xid`, `dcgmi health -c` | seconds |
| DCGM diagnostics | Level 1 to 3 | `dcgmi diag -r 1/2/3` | seconds to 30 min |
| Single-node stress | Thermal/power stability, ECC under load | `gpu-burn`, DCGM level 3, `nvbandwidth`, `dcgmproftester` | 10 to 30 min |
| GPUDirect/P2P | P2P and NVLink bandwidth | `nvbandwidth`, `p2pBandwidthLatencyTest`, `nvidia-smi nvlink` | minutes |
| Network | Link state, RDMA perftest (`ib_write_bw`, `ib_send_lat`) to a peer, GID/RoCE config, MTU | `perftest`, `ibv_devinfo`, `rdma link` | minutes |
| Multi-node collectives | NCCL all-reduce within tolerance of the expected bus bandwidth | `nccl-tests` (`all_reduce_perf`), `mpirun`/`srun` | minutes |

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

(Use your standard burn tool pinned by commit SHA and built into your image; don't compile from a moving branch at test time. Xid errors appear in the kernel log, not in the burn tool's output.)

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

(Bus bandwidth expectations depend on topology, NIC speeds and message sizes; derive baselines from known-good runs and record them.) Store results as artefacts (JSON) with node serials so trends and repeat offenders are visible; failing nodes are tagged `quarantine` and kept out of the scheduler.

## 6. Day-2: drain, patch, validate, resume

Reuse the pattern from 4.8 with GPU-aware checks:

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

Kubernetes equivalent: `kubernetes.core.k8s_drain` (respecting PodDisruptionBudgets), taint with `nvidia.com/gpu=maintenance:NoSchedule`, patch, validate (DCGM/NVML), uncordon. For driver upgrades under the GPU Operator, use its upgrade controller rather than manual host changes (Part 11).

Fleet-wide diagnostics (read-only, safe to run any time):

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

Aggregate the JSON into a report (count nodes with fewer than 8 GPUs, PCIe link degraded below x16, nonzero uncorrected ECC, active throttle reasons); this is a typical first step in an incident when many jobs slow down.

## 7. Incidents that shaped the design

1. **Interactive prompt freezes the fleet.** A package upgrade across 256 GPU nodes stalled forever on a `dpkg` configuration-file prompt (no TTY). Cause: apt run non-interactively without conffile policy, or competing with `unattended-upgrades`. Fix: use the `apt` module with `dpkg_options: force-confold,force-confdef`, `lock_timeout`, `DEBIAN_FRONTEND=noninteractive`, disable unattended upgrades on nodes, and set task `timeout`.
2. **Green but dead.** `systemd` start returned OK while `slurmctld` crashed seconds later on a bad `slurm.conf`. Fix: verify behaviour after every critical start (`sinfo`, `curl /health`) with `until/retries` and validate configs before installing them (4.7).
3. **Secrets in logs.** A `command` task with a database password on the command line printed it into job logs. Fix: `no_log: true`, pass secrets via files/stdin, scan logs (4.12).
4. **Precedence surprise.** A forgotten `host_vars` file pinned one DGX to an old driver version while `group_vars` said otherwise. Fix: inspect with `ansible-inventory --host`, treat `host_vars` as exceptional, and add an assert/report that lists driver versions per node after each run (4.5).
5. **Kernel and driver mismatch.** A kernel update (unattended or by a different team) invalidated the DKMS module build; nodes lost GPUs after reboot. Fix: pin kernel and driver together, hold packages, test updates on a canary, and use precompiled/signed modules where Secure Boot is required (module signing keys managed deliberately).
6. **Silent half-fabric.** A node's ConnectX port came up at a lower speed or one rail was down; training ran at half speed. Fix: validation compares link speed/state per rail with the design; fleet sweeps record `ibstat`/`rdma link` output and flag deviations.
7. **Thundering herd on the mirror.** 1,000 nodes downloading the same driver and OFED at once saturated the mirror. Fix: `throttle`, `serial`, local caches/proxies, preseeded images.
8. **Reboot loops.** A bad GRUB parameter or module config prevented boot; automation retried reboots. Fix: canary first, `max_fail_percentage`, BMC out-of-band access to recover (Part 7), and a rule that automation never retries a reboot without human review when a node fails to return.

## 8. Lab (untested)

If no GPU is available, rehearse with stub `nvidia-smi`, `dcgmi`, `ibstat` scripts on a plain VM so roles, ordering, handlers, reboots and validation logic are exercised; reserve the hardware steps for a real node.

1. **gpu_facts**: implement the role; compare discovered counts with expected; publish `ansible_local.gpu`; test with stubs and on a GPU host.
2. **Ordered bring-up**: write the playbook from the graph with reboot points; run on a fresh VM/node; confirm `--list-tasks` order and that rerun is `changed=0` (apart from validation probes).
3. **Driver role**: pin a branch, hold packages, run non-interactively with `dpkg_options`; simulate a conffile prompt to prove the fix; try an upgrade and a blocked downgrade; test `rescue` rollback.
4. **OFED role**: add async install, checksum, version-aware idempotency, initramfs rebuild and reboot flush; document the rollback.
5. **Reboot handling**: trigger a reboot via handler; verify `post_reboot_delay` and `test_command`; test behaviour when the node fails to return (timeout, failure policy).
6. **Tuning**: persistence daemon, power limit (use the 4.15 module), MIG profile (on a MIG-capable GPU), peermem; verify with `nvidia-smi` and `lsmod`.
7. **Telemetry**: deploy DCGM and the exporter; scrape from Prometheus; create an alert test for a missing GPU (use a metric from a stub).
8. **Validation ladder**: implement quick (seconds), standard (DCGM level 2) and burn (30 min) task files; gate scheduler registration on success; store JSON reports.
9. **NCCL**: run nccl-tests on two or more nodes; record baseline bus bandwidth per message size; assert against the floor; compare with a deliberately degraded NIC (MTU or `NCCL_IB_DISABLE=1`).
10. **Drain/patch/resume**: execute the workflow on a lab Slurm; inject a validation failure and confirm the node stays drained; do the Kubernetes variant with `k8s_drain` and a PDB.
11. **Fleet sweep**: run the health sweep across many (simulated) nodes, aggregate to a table, and flag outliers.
12. **Incident replays**: reproduce the interactive `dpkg` hang, the green-but-dead service and the stale `host_vars` precedence; fix each with the patterns above.
13. **Clean up** nodes/VMs and cloud GPUs.

Mark tested only after execution.

## 9. Common mistakes

- Installing the NVIDIA driver before the RDMA stack, or skipping the reboot/module reload between them.
- Letting packages float (`state: latest`) or letting `unattended-upgrades` change kernels and drivers.
- Mismatched kernel, headers, driver branch, Fabric Manager and DCGM versions.
- Treating "service started" as "node healthy"; skipping burn-in and collectives tests.
- Hard-coded package names across distributions; roles that fail halfway and leave a node half-configured but visible to the scheduler.
- Rolling to the whole fleet without a canary; no `max_fail_percentage`; reboot retries on non-returning nodes.
- Compiling tools from moving branches at test time; unpinned benchmark versions.
- No record of results, so repeat-offender nodes and slow regressions go unnoticed.
- Secrets in command lines; verbose logs with credentials.
- Applying Ansible driver changes underneath the GPU Operator, creating two managers for the same component.

## 10. Interview angles

- "Walk through bringing up a new DGX/HGX node with Ansible from bare OS to schedulable." (order, reboots, validation, scheduler last.)
- "How do you upgrade GPU drivers across a running cluster?" (drain, canary, DKMS/headers, holds, validation, rollback.)
- "Why install MOFED before the NVIDIA driver? What is nvidia-peermem?" 
- "How do you validate a node before releasing it to users?" (DCGM diag levels, burn-in, NVLink/PCIe/IB checks, NCCL test.)
- "A playbook upgrading packages hangs on 200 nodes. Diagnose." (dpkg prompt, locks, unattended upgrades, noninteractive, timeouts.)
- "How do you keep GPU nodes consistent over time?" (golden images, pins, drift checks, scheduled `--check`, fleet sweeps.)
- "How do you coordinate with Slurm/Kubernetes during maintenance?" (drain/cordon, PDBs, resume only after validation.)
- "How do you detect a degraded node whose job is merely slow?" (link speeds, throttle reasons, ECC, NCCL baseline.)

## 11. Checkpoint questions (35)

1. Why install the RDMA stack before the GPU driver? **A:** `nvidia-peermem` binds to the RDMA stack.
2. When is Fabric Manager needed? **A:** NVSwitch (HGX/DGX) systems.
3. Version rule for Fabric Manager? **A:** Must match the driver version.
4. Why hold driver packages? **A:** Prevent drift and DKMS breakage.
5. What does DKMS need? **A:** Matching kernel headers and compilers.
6. What conflicts with a manual driver install? **A:** Mixed OS/NVIDIA repo packages, unattended upgrades.
7. Which module enables GPUDirect RDMA? **A:** `nvidia_peermem`.
8. What does `nvidia-persistenced` do? **A:** Keeps driver state loaded (persistence mode).
9. MIG change prerequisites? **A:** No processes using the GPU; may need reset/reboot.
10. DCGM diag levels? **A:** 1 quick, 2 medium, 3 long stress.
11. What flags avoid dpkg prompts? **A:** `force-confold,force-confdef`, noninteractive frontend.
12. What does `lock_timeout` do? **A:** Fails instead of waiting forever for apt lock.
13. How avoid SSH timeouts during long installs? **A:** `async` with `poll`.
14. Where do reboots belong? **A:** After kernel/OFED/driver changes, via handlers + flush.
15. What is `test_command` in `reboot`? **A:** Command that must succeed to consider the node up.
16. Why high `reboot_timeout` for GPU servers? **A:** Long POST/memory training.
17. How to detect Xid errors? **A:** Kernel log (`journalctl -k`, `dmesg`).
18. Where is ECC info? **A:** `nvidia-smi -q -d ECC`.
19. What checks PCIe link degradation? **A:** `lspci -vv` / `nvidia-smi` pcie link fields.
20. Tool for network bandwidth tests? **A:** perftest (`ib_write_bw`).
21. Tool for collectives? **A:** nccl-tests.
22. Why run mpirun as non-root? **A:** OpenMPI refuses root by default.
23. What gates scheduler registration? **A:** Successful validation.
24. Drain pattern? **A:** Drain, wait for jobs, change, validate, resume.
25. What if validation fails mid-maintenance? **A:** Leave node drained, fail loudly.
26. Why avoid `state: latest` for drivers? **A:** Uncontrolled upgrades.
27. How handle package mirror load? **A:** `throttle`, serial batches, caching.
28. How record validation results? **A:** JSON artefacts with node serial.
29. What breaks after kernel update with DKMS? **A:** Module build/load.
30. Why compare discovered vs expected GPUs? **A:** Detect missing devices early.
31. Who manages drivers under GPU Operator? **A:** The operator (avoid dual management).
32. What is a "green but dead" service? **A:** Started OK then crashed; fix with verification.
33. How verify NVLink? **A:** `nvidia-smi nvlink --status`.
34. What stops reboot loops? **A:** Canary, failure thresholds, human review, BMC recovery.
35. Why store burn tool versions? **A:** Reproducible tests.

## 12. Sources and review notes

**Written in original words.** Principal sources:

- The author's `nvidia-devops` repository, volume 10 chapter 4 (Ansible for infrastructure automation in AI factories): MOFED role and reboot flow, Fabric Manager and DCGM roles, `apt` non-interactive troubleshooting scenario, green-but-dead service scenario, secret-logging scenario, variable precedence scenario, GPU burn and NCCL diagnostic playbooks.
- Rene Moser and Lorin Hochstein, *Ansible: Up and Running*, 3rd edition (for the Ansible mechanics applied here); the AI systems performance engineering book in the study corpus is cross-referenced for NCCL and validation context.
- NVIDIA documentation for the data-centre driver, Fabric Manager, DCGM, container toolkit, MLNX_OFED/DOCA and nccl-tests.
- Examples are the author's constructions; the order and validation ladder are the author's synthesis.

**Flagged for verification before publishing:** package and service names per distribution/repository version, driver branch flavour naming (`-server-open`), OFED installer flags and DOCA-Host replacement steps, `nvidia-ctk` commands, DCGM output strings used in `failed_when`, GB200/NVL72 fabric components, nccl-tests bandwidth expectations, and every code listing; all labs are **untested**.
