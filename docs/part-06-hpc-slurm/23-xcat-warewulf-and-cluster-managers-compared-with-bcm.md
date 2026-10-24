---
id: "c06-23"
title: "6.23 xCAT, Warewulf and cluster managers compared with BCM"
sidebar_label: "6.23 xCAT, Warewulf and cluster managers compared with BCM"
sidebar_position: 23
description: "Cluster management systems compared: xCAT (architecture, object model, key commands, current project status), Warewulf 4 (nodes.conf, images, overlays, wwctl), Confluent, Canonical MAAS and Foreman, and NVIDIA Base Command Manager (head node, software images, categories, cmsh), with a selection matrix for GPU clusters"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.23 xCAT, Warewulf and cluster managers compared with BCM

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 2 |
| Lab venue | Warewulf on a VM head node with 2 to 3 VM compute nodes |
| Part | Part 6: HPC and Slurm |
| Status | Drafted from the projects' own documentation: Warewulf (warewulf/warewulf commit `324c0bc`, 2026-10-21, `userdocs`), xCAT (xcat2/xcat-core commit `56a009b`, 2026-10-23, README and docs tree; version file 2.20.0), BCM 11 manuals (corpus) and the SCL book. Nothing was installed or run. MAAS, Foreman and Confluent are described from general knowledge: **unverified**. Labs **untested** |

## Why this matters for AI infrastructure

6.22 explained the mechanisms; a cluster manager packages them: node database, DHCP/TFTP/HTTP services, image build and distribution, power and console control, discovery, health, user and software management, and integration with Slurm or Kubernetes. Which manager a site uses determines its workflows, its upgrade story and who supports it. AI clusters from NVIDIA come with **Base Command Manager**; research clusters often use **Warewulf**; legacy sites run **xCAT**; cloud-style fleets use **MAAS** or **Foreman**. An infrastructure engineer should be able to operate whichever is in front of them and explain the trade-offs.

## Prerequisites and outcomes

Needs 6.2, 6.22 and Part 7 awareness (BMC/Redfish). After this chapter you can:

- Describe the architecture and object model of xCAT, Warewulf 4 and BCM and map their concepts onto each other.
- Run the core workflows in each: define nodes, build and assign images, provision, power control, run commands across nodes.
- State the current status and positioning of each project, including xCAT's recent change of course and its recommended successor.
- Compare managers on scalability, GPU-cluster fit, extensibility, support model and lock-in; choose and justify.

## 1. Common model

All managers implement the same abstractions under different names:

| Abstraction | xCAT | Warewulf 4 | BCM | MAAS | Foreman |
|---|---|---|---|---|---|
| Node record | node object (`mkdef`) | node in `nodes.conf` (`wwctl node`) | device (node) in CMDaemon database | machine | host |
| Group/template | node group | profile | category | tags/pods | host group |
| OS image | osimage (`genimage`, `packimage`) | image (container/chroot) | software image under `/cm/images` | image/stream deployed | provisioning template + media |
| Per-node customisation | postscripts, synclists | overlays (templated files) | node-installer scripts, finalize scripts, config overlays | cloud-init user data | templates, Puppet/Ansible |
| Services | DHCP, TFTP, DNS, HTTP, NTP configured by xCAT | DHCP, TFTP, NFS, hosts configured via `wwctl configure` | provisioning, DHCP, DNS, NTP, LDAP, monitoring | DHCP, DNS, TFTP, PXE proxy | smart proxies for DHCP/TFTP/DNS |
| Out-of-band control | `rpower`, `rcons`, BMC plugins | IPMI settings on node (`wwctl node ... ipmi`) | built-in power control and BMC mgmt | BMC power drivers | BMC via plugins |
| Remote command | `xdsh` | `wwctl`-driven or `pdsh` | `pdsh`/`cmsh` | `maas` CLI | remote execution (Ansible) |
| Database | tables (SQLite, MySQL, PostgreSQL) | YAML file | embedded/MySQL database | PostgreSQL | PostgreSQL |

## 2. xCAT

xCAT (Extreme Cloud Administration Toolkit) is an IBM-originated, later Lenovo-supported toolkit for deployment and administration of clusters of all sizes (README). It has been the standard on many large HPC systems.

### Architecture (from the overview docs)

- **Management node**: the single point of control; runs `xcatd`, the node database, and network services.
- **Service nodes**: optional "slave" servers under the management node that take over DHCP/TFTP/HTTP and installation load for racks or groups, for scale.
- **Compute nodes**: the managed targets.
- **Service processor (BMC, IMM, FSP)**: out-of-band hardware control.
- **Networks**: management network (OS installs), service network (BMC access), application network (MPI), site (public) network.
- **REST API** for integration.

### Object model and commands

Everything is a typed **object** (node, group, network, osimage, site, policy) with attributes. The manual pages in the docs tree list the main tools: `mkdef`, `chdef`, `lsdef`, `rmdef` (define and inspect objects), `nodels`, `nodech`, `noderm`, `nodeimport`, `nodechmac`, `nodediscoverstart/ls/stop` (discovery), `getmacs`, `makedhcp`, `makedns`, `makentp` (services), `copycds` (import installation media), `genimage`, `packimage`, `liteimg` (stateless and statelite image creation), `nodeset` (set the boot state of nodes), `rpower` (power), `rinv` (inventory), `xdsh` (distributed shell), `rinstall`. A typical stateless flow (from the docs structure and common usage; verify against your release): `copycds` the distribution media; `mkdef` nodes and groups with MACs, IPs and BMC details; `genimage`/`packimage` the stateless image; `makedhcp -n` and `makedns -n`; `nodeset <noderange> osimage=...`; `rpower <noderange> boot`; check with `nodestat` and `xdsh`. The **noderange** syntax (`n[001-200]`, groups, regular expressions) is xCAT's lasting contribution to cluster tooling.

### xCAT installation and initial setup (outline)

From the xCAT documentation structure and the SCL book's walk-through (commands vary by release; verify): prepare the management node (static IP on the management network, hostname and FQDN resolving, SELinux/firewall policy, time sync); add the xCAT repositories (core and dependencies) and install the `xCAT` package, then `source /etc/profile.d/xcat.sh`; `tabdump site` and `chtab`/`chdef -t site` to set the domain, DNS forwarders and DHCP interfaces; `copycds <distribution.iso>` to create an osimage; `mkdef` nodes (or `nodeimport`, `nodediscoverstart` for MAC discovery) with BMC details; `makehosts`, `makedns -n`, `makedhcp -n`; `genimage` + `packimage` for stateless or `nodeset ... osimage=... ` for diskful installs; then `rpower ... boot`. The book's "One-Two-Three instructions" chapter condenses this sequence for a first cluster.

### Status

The repository README (2026) states that the earlier announced sunset "has changed course": the xCAT Consortium and participating companies (VersatusHPC) continue upstream development, Enterprise Linux 10 support is planned, and development continues "while there is community and user demand"; the Consortium recommends **Confluent** (github.com/xcat2/confluent, a newer Python-based tool from the same community, the long-term successor) for new deployments. Practical reading: xCAT is maintained but not where new designs should start; plan migrations for old clusters; check the OS support matrix before upgrading distributions.

## 3. Warewulf 4

Warewulf (since 2001) is "a stateless, network-boot cluster provisioning system designed primarily for use in HPC clusters" (README). The v4 documentation describes its design tenets: lightweight, simple, flexible, agnostic (x86 and ARM, many distributions), secure (SELinux supported), open source.

### Architecture

- **Warewulf server** with `warewulfd` and the CLI `wwctl`. State lives in plain files: `/etc/warewulf/warewulf.conf` (server), `/etc/warewulf/nodes.conf` (node database, YAML), image roots under `/var/lib/warewulf/chroots/`, overlays under `/usr/share/warewulf/overlays/` (distribution) and `/var/lib/warewulf/overlays/` (site), built per-node overlay images under `/var/lib/warewulf/provision/` (quick-reference paths).
- **Nodes** carry network configuration, IPMI settings, kernel arguments, image and overlay assignments; **profiles** apply shared settings; hostlist syntax (`n[1-10]`) works in commands.
- **Images** (OS images) are bootable root file systems managed with container tooling: import from a registry (Docker Hub, private registries) or build from a Dockerfile in CI/CD; they run entirely in memory by default so a reboot returns the node to a known-good state.
- **Overlays**: collections of files and `.ww` **templates** rendered per node from the node registry (so `nodes.conf` becomes an expressive metadata store) and applied over the image, at boot (system overlays) and periodically at runtime (runtime overlays). Core functions (`hosts`, `fstab`, `ssh`, network config, `dhcpd`, `nfsd`) are themselves overlays; `wwctl overlay blame <node>` shows which overlay contributes each file.
- **Services**: `wwctl configure --all` (re)configures DHCP, TFTP, NFS, SSH and hosts file; `warewulf.conf` defines the ranges and the iPXE binary per architecture (the quickstart config maps architecture codes `00:00` to `undionly.kpxe`, `00:07` and `00:09` to the x64 EFI iPXE binary, `00:0B` to the arm64 binary, matching the DHCP option-93 values in 6.22), plus NFS exports (`/home`, `/opt`), and `image mounts`.

### Commands (from the quick reference)

```bash
wwctl configure --all                              # DHCP, TFTP, NFS, SSH, hosts, TLS
wwctl image import docker://ghcr.io/warewulf/warewulf-rockylinux:8 rockylinux-8   # the docs' own example; also .tar, .sif, or a directory
wwctl node add n[2-4] --ipaddr=10.0.2.2            # IP auto-increments across the range
wwctl node add n1 --ipaddr=10.0.2.1 --netdev=eno1 --hwaddr=00:00:00:00:00:01 --image=rockylinux-8 --profile=default
wwctl node list --net ; wwctl node list --all n1 ; wwctl node status
wwctl profile list default --all
wwctl overlay list --all ; wwctl overlay blame n1
journalctl -u warewulfd
```

Typical workflow: install the RPM/DEB, edit `warewulf.conf`, `wwctl configure --all`, import an image (add drivers/Slurm/GPU stack by building your own image), add nodes with MACs, power them on, `wwctl node status` to watch them boot, adjust overlays for Slurm/munge/Lmod.

Strengths: simplicity, fully open, container-native images, small footprint, scales to thousands of nodes, fits GitOps (nodes.conf and images in version control). Limits: provisioning only (no built-in monitoring, health, user management, power orchestration beyond IPMI settings); you assemble the rest (Slurm, monitoring, LDAP); GPU stack integration is your image build; commercial support from CIQ and others.

## 4. Confluent, MAAS, Foreman (general knowledge, verify)

- **Confluent** (xCAT Consortium): Python-based successor to xCAT with asynchronous design, web API/CLI (`nodedeploy`, `nodeconfig`, `nodeshell`...), hardware discovery and OS deployment (including Redfish-driven), recommended by the xCAT project for new deployments (per the xCAT README).
- **Canonical MAAS** (Metal as a Service): treats physical servers as an API-driven cloud: discovers machines (PXE + BMC), commissions them (hardware inventory, tests), then deploys Ubuntu/other images with cloud-init user data; supports resource pools, tags, networks/VLANs, IPAM; pairs with Juju or Terraform providers. Strong for fleets and cloud-like workflows, less HPC-specific (no noderange habits, no Slurm integration out of the box), but widely used for GPU fleets and Kubernetes bare-metal.
- **Foreman** (with Katello, Puppet/Ansible): lifecycle management for mixed fleets: provisioning templates (Kickstart, preseed), compliance, content/repo management, host groups, reporting. Fits enterprise estates, less so tightly coupled HPC clusters.

## 5. NVIDIA Base Command Manager (BCM)

BCM (formerly Bright Cluster Manager) is NVIDIA's cluster management product, bundled with DGX systems and sold for AI clusters. Part 8 covers it in depth; the model relevant to this comparison, from the BCM 11 administrator and installation manuals:

- **Head node** is the centre: it holds the **head copy of the software images** (under `/cm/images/<image>`, `default-image` on a fresh install) and runs **CMDaemon**, the daemon that manages devices, provisioning and monitoring. Nodes boot from the network and receive a *known good state* from the head node (diskless: image copied into memory/tmpfs; diskful: local disk contents checked against the image, differing content corrected).
- **Software images, categories, nodes**: a **software image** is the root file system; a **category** groups nodes and sets their software image, disk layout, services, and parameters; individual nodes ("devices") belong to a category (and can override). To make nodes behave differently, you clone a category, point it at a modified image and move nodes to it with `cmsh` (the manual's example: `category; clone default categorytwo; set softwareimage imagetwo; commit`, then `device; use node099; set category categorytwo; commit`, or a `foreach` loop over a range).
- **Provisioning roles and nodes**: large clusters designate **provisioning nodes** that serve images to others; `updateprovisioners` (from `softwareimage` mode) propagates head-copy changes to them, and runs automatically when changes go through CMDaemon; provisioning requests lost with a node are retried after a timeout (the manual cites 180 seconds).
- **Node installer**: an early boot phase on each node that identifies the node, partitions disks, syncs the image, then hands over to the OS; finalize scripts customise the result (SELinux initialisation, for instance, occurs at the very end of the node-installer phase in BCM-provisioned nodes).
- **Interfaces**: `cmsh` (shell, modes such as `device`, `category`, `softwareimage`, `partition`), Base View (web UI), a JSON-RPC API, `cm-` utilities; configuration and monitoring in one database.
- **Integration**: Slurm, PBS, Kubernetes, Jupyter, GPU and DCGM monitoring, health checks, Redfish power, NVIDIA-validated reference architectures (DGX BasePOD/SuperPOD). Licensing per node; support from NVIDIA.

Trade-offs: batteries included and vendor-validated, single support path, deep GPU-system knowledge; costs licence and a closed core, and the cluster workflows are BCM's (less pure GitOps, though it can be scripted via `cmsh`/API).

## 6. Selection matrix

| Criterion | xCAT | Warewulf 4 | Confluent | MAAS | Foreman | BCM |
|---|---|---|---|---|---|---|
| Licence/cost | Open source (EPL) | Open source (BSD-style) | Open source | Open source + support | Open source + support | Commercial per node |
| Core strength | Large-scale HPC deployment, noderange, hierarchy | Simple stateless images, overlays | Modern successor to xCAT | Cloud-like bare metal | Enterprise lifecycle/compliance | Integrated AI cluster management |
| Stateless images | Yes | Yes (default) | Yes | Mostly stateful deploys | Mostly stateful | Yes and stateful |
| Monitoring/health | Basic | None built-in | Limited | Hardware tests | Reporting | Built in, GPU-aware |
| Slurm/K8s integration | Manual | Manual | Manual | Manual (Juju/Terraform) | Manual | Built in |
| GPU-system knowledge | Manual | Manual (your image) | Manual | Some | Manual | Strong (DGX) |
| Scale | Very large (service nodes) | Large | Large | Large | Large | Large (provisioning nodes) |
| Project status (as read) | Maintained, successor recommended | Active | Active | Active | Active | Active (NVIDIA) |
| Best fit | Existing xCAT estates | Research HPC, GitOps-minded teams | New xCAT-style clusters | Mixed fleets/K8s bare metal | Enterprise Linux estates | NVIDIA GPU clusters, SuperPOD |

Decision flow: buying DGX/HGX with NVIDIA support, or needing integrated monitoring: BCM. Building an open-source HPC cluster with your own automation: Warewulf (plus Ansible, Prometheus, Slurm). Existing xCAT: stay, plan Confluent. Cloud-style GPU fleet feeding Kubernetes: MAAS or the provider's tooling. Always consider who will operate it at 3 a.m.

## 7. Operating practices that carry across managers

- Inventory in version control (CSV/YAML) or exported regularly from the manager's database; the manager's database is not a backup of your design.
- Back up the manager state (xCAT database dump, `nodes.conf` and chroots, BCM head-node backup and `cmsh` exports).
- HA for the head/management node (BCM has head-node failover; Warewulf can run on replicated hosts; xCAT uses service nodes and backups).
- Staged rollouts of images (canary categories/profiles), automatic drain/reboot via Slurm.
- Document the node replacement procedure (update MAC in inventory, reprovision, verify, resume).
- Secure the management plane: network isolation, BMC credentials rotation, TLS, auditing, restricted access.

## 8. Lab (untested)

1. Install Warewulf on a Rocky/Alma VM following the quickstart; import a Rocky image; add two VM nodes with MACs; boot them; use `wwctl node status`, `wwctl overlay blame`.
2. Add a Slurm client and munge to the image (build your own image from a Dockerfile) and a template overlay that renders each node's `slurm.conf` fragment from tags in `nodes.conf`.
3. Read the xCAT `nodeset`, `genimage`, `packimage` man pages and write the command sequence for a stateless deployment; compare line by line with the Warewulf flow.
4. Read BCM's category and software image sections; write the `cmsh` commands to create a GPU category with a modified image.
5. Fill the selection matrix for your own site constraints and pick one manager.

## 9. Interview angles

- Compare xCAT, Warewulf and BCM in one minute each.
- What is a Warewulf overlay and how does it differ from baking a file into the image?
- What are BCM categories and software images? How do you test a new image on a few nodes?
- Why would a site use service nodes in xCAT or provisioning nodes in BCM?
- Which manager would you pick for 4,000 H100 nodes and why?
- How do you replace a failed node so that it keeps its name and image?
- What does xCAT's current status mean for planning?
- What does a cluster manager not do that Slurm and Kubernetes do?

## 10. Checkpoint questions (25)

1. List the abstractions all managers share.
2. What are xCAT's management, service and compute nodes?
3. Name six xCAT commands and their purposes.
4. What is a noderange?
5. What is the xCAT project's recommended successor and what is the current status statement?
6. What files hold Warewulf's server and node configuration?
7. What is a Warewulf profile? An overlay?
8. How does `wwctl overlay blame` help?
9. What does `wwctl configure --all` do?
10. How does Warewulf choose the iPXE binary per architecture?
11. Where are BCM software images kept?
12. What is CMDaemon?
13. What is a BCM category?
14. What does `updateprovisioners` do?
15. What is the node-installer phase?
16. What do MAAS and Foreman each emphasise?
17. What does Confluent aim to replace?
18. Which managers include monitoring and health?
19. How do licence models differ?
20. What should be in version control regardless of manager?
21. How do you test a new image safely?
22. Why isolate the management network?
23. How does service-node hierarchy scale provisioning?
24. How do you decide between BCM and Warewulf?
25. What happens to node identity on hardware replacement?

## 11. Sources and review notes

- xCAT architecture and commands: `xcat-core` README and docs tree (overview/architecture, admin guide manual pages) at commit `56a009b`; positioning text quoted/paraphrased from the README ("sunset ... changed course", Confluent recommendation). Chapter-level survey (xCAT installation, architecture, node management, loading and controlling, MAAS, Foreman, BCM) and the "One-Two-Three" xCAT instructions: *Supercomputers for Linux SysAdmins* chapters 26 and 28, restated.
- Warewulf: `warewulf/userdocs` (introduction, EL quickstart, quick reference, overlays) at commit `324c0bc`.
- BCM: BCM 11 administrator and installation manuals in the corpus (software images, categories, provisioning, node installer); see Part 8.
- Original: the comparison tables and decision flow.
- Unverified: Confluent details, MAAS and Foreman feature descriptions, licences, scale claims, any command not shown in the cited docs.
