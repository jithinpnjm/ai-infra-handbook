---
id: "c06-23"
title: "6.23 xCAT, Warewulf and cluster managers compared with BCM"
sidebar_label: "6.23 xCAT, Warewulf and cluster managers compared with BCM"
sidebar_position: 23
description: "Cluster management systems compared: xCAT (architecture, object model, key commands, current project status), Warewulf 4 (nodes.conf, images, overlays, wwctl), Confluent, Canonical MAAS and Foreman, and NVIDIA Base Command Manager (head node, software images, categories, cmsh), with a selection matrix for GPU clusters"
status: "reviewed"
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
| Status | Drafted from the projects' own documentation: Warewulf (warewulf/warewulf commit `324c0bc`, 2026-10-21, `userdocs`), xCAT (xcat2/xcat-core commit `56a009b`, 2026-10-23, README and docs tree; version file 2.20.0), BCM 11 manuals (corpus) and the Supercomputers for Linux SysAdmins book. Nothing was installed or run. MAAS, Foreman and Confluent are described from general knowledge: **unverified**. Labs **untested** |

## Why this matters for AI infrastructure

Picture a new GPU node arriving at the data center on a Tuesday morning. Someone has to record its MAC address, which is the hardware address its network card uses on the local network. That person then has to give the node a boot image, power it on and confirm that it comes up healthy. Chapter 6.22 explained the mechanisms behind that work. These include DHCP (Dynamic Host Configuration Protocol), which hands out network addresses, and TFTP (Trivial File Transfer Protocol), which serves the first small boot files. A cluster manager packages those mechanisms into one tool. It covers the node database, the DHCP, TFTP and HTTP (HyperText Transfer Protocol) services, image build and distribution, power and console control, discovery, health, user and software management, and integration with Slurm or Kubernetes.

The manager you pick decides your daily workflows, how the cluster gets upgraded and who you call when something breaks. AI clusters from NVIDIA ship with Base Command Manager. Research clusters often run Warewulf, legacy sites run xCAT, and cloud-style fleets use MAAS or Foreman. In practice you will usually inherit one of these tools rather than choose it from a blank page. So the goal is to operate whichever manager is in front of you, and to explain its trade-offs clearly to the people who make the decisions.

## Prerequisites and outcomes

Before you start, review 6.2 and 6.22. You also need a working picture of the baseboard management controller (BMC), the small computer inside a server that handles remote power and console access, and of Redfish, the standard web API for that same hardware. Part 7 covers both in more depth.

This chapter walks through the architecture and object model of xCAT, Warewulf 4 and BCM, and it shows how their concepts map onto each other. It then runs the core workflows in each tool, which means defining nodes, building and assigning images, provisioning, controlling power and running commands across nodes. It also states where each project stands today, including xCAT's recent change of course and the successor it recommends. The chapter closes with a comparison on scalability, GPU fit, extensibility, support model and lock-in, so that you can choose one manager and explain why.

## 1. Common model

Imagine you join a team that runs two clusters, one built with xCAT and one with Warewulf. The first person you ask talks about a node object. The second talks about a node in a YAML file. A vendor slide deck shows a device in a database. All three describe the same physical machine. The vocabulary changes from tool to tool, but the jobs behind it stay the same. Once you see the common model, you can move between these tools without starting from zero each time.

Each manager has its own vocabulary, so the same job can look different from one tool to the next. The diagram below shows how each one is organized. You will find the database, the node record and the image in every design, but the names change.

```mermaid
flowchart TB
  subgraph xCAT["xCAT (Relational Tables + Objects)"]
    X1["xcatd + Service Nodes<br/>tabdump / chdef / nodeset / rpower"]
    X2["statelite: NFS root + litefile tmpfs"]
    X1 --> X2
  end
  subgraph WW4["Warewulf 4 (GitOps + OCI)"]
    W1["warewulfd + nodes.conf (YAML)<br/>wwctl configure / node / image"]
    W2["Container Chroot + System/Runtime Overlays (.ww)"]
    W1 --> W2
  end
  subgraph BCM["NVIDIA Base Command Manager"]
    B1["Head Node CMDaemon + Provisioning Nodes<br/>cmsh / Base View / JSON-RPC"]
    B2["/cm/images + Categories + Node Installer"]
    B1 --> B2
  end
```

Read the diagram from top to bottom. Each box holds a central service, such as a daemon or a database. The arrow shows which piece depends on which, so the service at the top of each box hands work down to the image layer beneath it.

All managers implement the same abstractions under different names. The table lines up the matching concept in each manager, so you can translate a task from one tool to another. Read down a column to see how one manager handles a job. Read across a row to compare all the managers on the same job.

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

A good habit when you read a table like this is to ask what the concept does for the cluster first, and only then look for its name in the tool in front of you. Take the out-of-band control row. It describes how you turn a node on, off or reset it even when its operating system is down, and that work usually goes through the BMC. Once you know the job, the different names become easy to remember. PXE (Preboot Execution Environment) appears in the MAAS row. It is the network boot method that most of these tools rely on.

Here is a worked translation. Suppose a colleague asks you to power off a node named gpu042 from the management server. In xCAT, you reach for the out-of-band row and use the power command from that row. In Warewulf, the node already carries its IPMI settings, so the power command goes through the BMC with those settings. In BCM, the built-in power control covers the same job. The request never changes, only the tool and its vocabulary do. If you keep asking "what is the job here," the right command is usually easy to find in any of these tools.

## 2. xCAT

Suppose your site inherited a large cluster from a research group that has since moved on. The documentation is decent and the naming is consistent. Then you open a terminal and find xCAT commands everywhere. Before you change anything, it helps to know where the tool came from and what it was built to do.

xCAT stands for Extreme Cloud Administration Toolkit. IBM started it, and Lenovo later supported it. You can use it to deploy and administer clusters of all sizes. For many large HPC systems, it has been the standard tool. The project README describes it this way.

### Architecture (from the overview docs)

Before you run a single command, you need to know the roles. Each role has one job in the system. Think of them as a chain of command. One central server holds the truth, and helpers carry the work out to the racks and nodes.

- The management node is the single point of control. It runs `xcatd`, the node database and the network services. A daemon is simply a background service, and `xcatd` is the one that answers every xCAT command.
- Service nodes are optional servers under the management node. They take over DHCP, TFTP, HTTP and installation load for a rack or a group, which keeps large systems scalable. A small cluster rarely needs them. A large one does, because a single server would otherwise be busy answering every boot request at once.
- Compute nodes are the managed targets.
- The service processor (BMC, IMM or FSP) is the hardware controller that gives you out-of-band hardware control. Vendors use different names for the same kind of controller.

The networks split into four roles. A management network handles OS installs. A service network gives access to the BMC. An application network carries MPI traffic. A site network is the public one. Keeping these apart means a flood of boot requests on the management network never slows the MPI traffic that your jobs depend on. xCAT also offers a REST API for integration.

Here is what a boot request looks like in plain words. A new node powers on, and its network card asks the network for an address. The DHCP service replies with an address and the name of a boot file. The node downloads that file over TFTP, starts the installer, and then fetches its image from the network. Each step depends on the one before it. So when a node fails to boot, walk this chain from the top, and find the first step that did not happen. That order keeps you from blaming the image for a problem that started with the address.

### Object model and commands

Picture an operator who has to find out which nodes sit in the rack that just failed. In xCAT, the answer comes from objects, not from a spreadsheet. Everything in xCAT is a typed object, such as a node, a group, a network, an osimage, a site or a policy. Each object carries attributes. Once you know the object types, the commands follow a simple pattern.

The manual pages in the docs tree list the main tools. You define and inspect objects with `mkdef`, `chdef`, `lsdef` and `rmdef`. You work with nodes using `nodels`, `nodech`, `noderm`, `nodeimport` and `nodechmac`. Discovery runs through `nodediscoverstart/ls/stop`. Service configuration uses `getmacs`, `makedhcp`, `makedns` and `makentp`. For media and images, you use `copycds` to import installation media, and `genimage`, `packimage` and `liteimg` to create stateless and statelite images. A stateless node loads its whole image into memory at each boot, and a statelite node mounts a read-only root over NFS. Day-to-day control comes from `nodeset` for boot state, `rpower` for power, `rinv` for inventory, `xdsh` for distributed shell, and `rinstall`.

A typical stateless flow looks like this. It comes from the docs structure and common usage, so verify it against your release. Read it as a checklist, not as a script to paste. First, `copycds` the distribution media. Then `mkdef` the nodes and groups with their MACs, IPs and BMC details. Next, build the stateless image with `genimage` and `packimage`, and run `makedhcp -n` and `makedns -n`. Finally, point the nodes at the image with `nodeset <noderange> osimage=...`, power them on with `rpower <noderange> boot`, and check the result with `nodestat` and `xdsh`.

The noderange syntax is xCAT's lasting contribution to cluster tooling. A noderange is a compact way to name a set of nodes. You can write `n[001-200]`, name a group, or use a regular expression. That one idea saves you from typing every hostname, and it keeps your commands short even when the cluster is large. A useful habit is to name nodes after what they do, such as their rack or their role, and to let the noderange carry the rest. Then a single command can reach every GPU node in a rack without a long list of names.

### xCAT installation, database tables, and statelite recipe

Imagine a fresh management server in a rack, a list of node MAC addresses in a spreadsheet, and a deadline for Monday. The next hour is about installing xCAT and learning where its state lives. This section follows the recipe in Chapters 26 and 28 of Supercomputers for Linux SysAdmins.

xCAT installs on a Red Hat or CentOS management server. You point the package manager at the `xCAT-core.repo` and `xCAT-dep.repo` files under `/etc/yum.repos.d/`. Those files tell the package manager where to find xCAT and its dependencies. Then you run `yum install -y xCAT` and `source /etc/profile.d/xcat.sh`, which puts the `/opt/xcat` binaries in your `PATH`. The source line loads the environment into your current shell, so the xCAT commands are found without typing their full paths.

Back up first. When its service-generation commands run, xCAT overwrites `/etc/exports`, along with the DHCP, Apache, DNS and TFTP configuration files. Keep a copy of anything you care about before you run them. This is the warning that people skip most often. A site that has hand-edited its exports file learns the hard way that the generator replaces it.

#### Database tables vs logical objects

Suppose a colleague asks why a node's IP address changed after a maintenance window. In xCAT, the answer lives in a table, not in one plain file. Knowing which table holds which value saves a lot of searching.

xCAT keeps all of its state in relational tables. Run `tabdump` to see the list of tables. Add the `-d` parameter, as in `tabdump -d`, and the same list comes with explanations in English. To edit a table, open it in `$EDITOR` with `tabedit <table>`. You can replace a table with `tabrestore`, or update it in a scripted way with `chtab`.

One logical object often spans several tables, so the object-level commands keep those tables consistent with each other. Those commands are `lsdef`, `mkdef`, `chdef` and `rmdef`, plus `nodech` for nodes. You can also export an object stanza and import it again. For example, `lsdef -z node01 > /tmp/n01.stanza` saves the stanza, and `cat /tmp/n01.stanza | mkdef -z` loads it back. A stanza is a block of attributes for one object, and it is an easy way to back up a single node's definition before you edit it.

The main logical object types are `site` for the cluster or clusters, `node`, `group` for a group of nodes, `network` for a subnetwork, `osdistro` for an OS distribution, `osimage` for an OS image, and `route` for a routing description. There are more types beyond these: `auditlog`, `boottarget`, `eventlog`, `firmware`, `kit`, `kitcomponent`, `kitrepo`, `monitoring`, `notification`, `pdu`, `policy`, `rack`, `taskstate` and `zone`. Run `lsdef node1` on a configured node, and it shows the attributes gathered from all of its tables.

```text
# lsdef node1 output
Object name: node1
    arch=x86_64
    bmc=10.1.1.3
    bmcpassword=admin
    bmcusername=ADMIN
    groups=all,compute
    mac=00:10:30:30:40:03
    mgt=ipmi
    netboot=pxe
    postbootscripts=otherpkgs
    postscripts=syslog,remoteshell,syncfiles
```

The key tables are the ones you will open most often. Each bullet names a table and gives the kind of value it holds.

- `site` holds the cluster-wide settings: `domain`, `installdir` set to `/install`, `tftpdir` set to `/tftpboot`, `xcatconfdir` set to `/etc/xcat`, `master`, `nameservers`, `forwarders`, `timezone`, `ipmiretries`, `ipmitimeout`, `SNsyncfiledir` and `nodesyncfiledir`. For example, `chtab key=tftpdir site.value=/tftpboot` or `chdef -t site -o clustersite domain=mycluster` sets values there.
- `hosts` maps hostnames to IP addresses. Its regular-expression rules mean you do not have to type each node's IP by hand.
- `mac` stores node MAC addresses, for example through `chdef -t node node1 mac=xx:xx:xx:xx:xx:xx`.
- `noderes` holds boot and network resources for each node or group, such as `netboot=pxe`, `tftpserver`, `nfsserver`, `installnic=eth0` and `primarynic=eth0`.
- `nodelist` and `nodegroup` hold node names, group memberships such as `groups=all,compute`, and status.
- `nodetype` holds the OS, architecture, profile and node type, for example `nodetype.os=rhel76`, `nodetype.arch=x86_64`, `nodetype.profile=compute` and `nodetype.nodetype=osi`.
- `networks` defines subnets and their dynamic DHCP ranges, as in `chtab netname=main_vlan networks.dynamicrange="10.0.0.200-10.0.0.254"`.
- `passwd` stores default credentials, set with `chtab key=system passwd.username=root passwd.password=cluster`.
- `policy` holds access control rules for non-root and remote administrators.
- `litefile`, `litetree` and `statelite` cover writable tmpfs paths, directory trees and persistent state paths for `statelite` nodes, which have a read-only NFS root.
- `postscripts` lists scripts from `/install/postscripts` that run during or after node boot.

#### Delegating access: `setup-local-client.sh` and the `policy` table

Picture a junior operator who needs to check power status on a handful of nodes, but who should never be able to power anything off. By default, only `root` on the management server can run xCAT commands. To let another user run them, you take two steps. Suppose you want `xadmin`, a user already listed in `/etc/passwd`, to connect over TLS. You generate client certificates for that user, and you add a rule to the `policy` table. TLS is the encryption layer that protects the connection. Remote clients also need `XCATHOST=<xCAT-server>:3001` set.

```bash
# Generate ~xadmin/.xcat/{ca.pem,client-cert.pem,client-cred.pem,client-key.pem,client-req.pem}
/opt/xcat/share/xcat/scripts/setup-local-client.sh xadmin

# Allow xadmin to run 'rpower stat' only on nodes h02-h05 at priority 7
mkdef -t policy -o 7 name=xadmin commands=rpower \
  parameters=stat noderange=h02-h05 rule=allow
```

Open the table with `tabedit policy`. Its header reads `#priority,name,host,commands,noderange,parameters,time,rule,comments`. xCAT checks the rules in ascending numeric `priority` order, and dotted priorities such as `6.1` or `7.012` are allowed. The first matching rule wins. That ordering matters. A broad deny at a low priority number will block a narrow allow that sits further down, so place your specific rules first.

```csv
#priority,name,host,commands,noderange,parameters,time,rule,comments
"1","root",,,,,,"allow",
"2","xadmin","*","nodels",,,,"allow",
```

#### Loading and Controlling: Step-by-step `statelite` provisioning workflow (Chapters 26 and 28)

Imagine a whole rack of compute nodes that must come up before a Monday training run. The workflow below is the path from blank nodes to running machines.

xCAT offers three provisioning modes. In statefull mode, the OS is installed onto local disk, which is typical for service nodes. In stateless mode, the whole image is unpacked into RAM. In statelite mode, the root filesystem is mounted read-only over NFS. Specific writable files and directories are mounted in RAM with `tmpfs`, as listed in `litefile`, and optional persistent state can live in `statelite`. The steps below combine the recipes from Chapters 26 and 28 of Supercomputers for Linux SysAdmins.

1. Start by importing the OS media and defining the nodes.

   ```bash
   copycds CentOS-7.6-x86_64-bin-DVD1.iso
   mkdef -t node node[1-100] groups=all,compute arch=x86_64 mgt=ipmi netboot=pxe
   ```

2. Next, let xCAT assign IP addresses with a regex rule in `hosts.ip`. The rule reads each node's name, pulls out the number, and adds a fixed offset to it, so the addresses follow the names automatically.

   ```bash
   # Strip non-digits (\D+), capture the node number (\d+) as $1, and add 10
   # For example, node15 receives 10.0.0.25
   chtab node=compute hosts.ip='|\D+(\d+)|10.0.0.(10+$1)|'
   ```

3. Generate and customize the `statelite` image. Package lists live in `/opt/xcat/share/xcat/netboot/centos/compute.rhel7.pkglist`. Extra RPMs go in `/install/post/otherpkgs` and `/install/custom/install/centos/compute.rhel7.otherpkgs.pkglist`. Install templates live in `/opt/xcat/share/xcat/install/centos/compute.rhel7.tmpl`. Then build the image and assign it to the `compute` group.

   ```bash
   genimage
   chdef compute provmethod=centos7.6-x86_64-statelite-compute
   ```

4. Populate `litefile` with writable RAM paths using `tabedit litefile`. The NFS root is read-only, so services still need a place to write their runtime state. Think of each `litefile` line as a sticky note that says, "this path gets its own writable space in RAM." Add at least these 15 entries, so services can write to `tmpfs`:

   ```csv
   #image,file,options,comments,disable
   "ALL","/etc/adjtime",,,
   "ALL","/etc/inittab",,,
   "ALL","/etc/ntp.conf",,,
   "ALL","/etc/ntp.conf.predhclient",,,
   "ALL","/etc/resolv.conf",,,
   "ALL","/etc/resolv.conf.predhclient",,,
   "ALL","/etc/ssh/",,,
   "ALL","/etc/sysconfig/",,,
   "ALL","/etc/sysconfig/network-scripts/",,,
   "ALL","/etc/udev/",,,
   "ALL","/opt/xcat/",,,
   "ALL","/root/.ssh/",,,
   "ALL","/tmp/",,,
   "ALL","/var/",,,
   "ALL","/xcatpost/",,,
   ```

5. Inject SSH keys, `/etc/passwd` entries and postscripts, then finalize the image. The Chapter 28 recipe uses helper scripts that copy SSH keys and passwd entries into the image root. Run them before `liteimg` packs the image. If you skip this step, the nodes boot without the keys and accounts they need to log in.

   ```bash
   cd /opt/xcat/share/xcat/netboot/add-on/statelite
   ./add_ssh /install/netboot/centos7.6/x86_64/compute/rootimg/
   ./add_passwd /install/netboot/centos7.6/x86_64/compute/rootimg/
   liteimg centos7.6-x86_64-statelite-compute
   ```

   For customization at first boot or after it, put your scripts in `/install/postscripts/`, for example `/install/postscripts/mypost`. Attach a script to a node with `chdef node1 -p postbootscripts=mypost`, which stores it in the `postscripts` table. xCAT then renders `/tftpboot/mypostscripts/mypostscript.<node_name>` from `/opt/xcat/share/xcat/mypostscript/mypostscript.tmpl`.

6. Last, generate the `/etc/hosts`, DHCP, DNS and TFTP configuration and boot the nodes. This is the step where the services start answering the nodes, so check each one before you power anything on.

   ```bash
   makehosts
   makedhcp compute
   systemctl restart dhcpd
   makenamed.conf
   makedns compute
   nodeset compute osimage=centos7.6-x86_64-statelite-compute
   rpower node[1-100] boot
   ```

The `rpower` command covers the IPMI power actions, such as `rpower compute stat`, `rpower node1 off`, `rpower node1 cycle`, `rpower node[1-100] on` and `rpower node1 reset`. IPMI (Intelligent Platform Management Interface) is the older standard that many BMCs speak. To run commands across many nodes at once, use `psh compute uname -n` for parallel execution. Use `pscp /tmp/myfile all:/tmp` for copying a file across node groups.

xCAT also has practical limits. Strict OS version support is one. You cannot snapshot an already-installed disk node straight into an image. Custom DNS and DHCP zones get overwritten. And xCAT has no built-in historical telemetry, so you need a separate monitoring stack to see how the cluster behaved last week.

### Status

Imagine a planning meeting where someone asks whether xCAT is still safe to build on. The honest answer comes from the project's own README, not from memory or from a blog post written years ago.

The 2026 repository README says the earlier announced sunset "has changed course." The xCAT Consortium and participating companies, including VersatusHPC, keep up the upstream development. Enterprise Linux 10 support is planned. Development continues "while there is community and user demand." The Consortium recommends Confluent for new deployments. Confluent lives at github.com/xcat2/confluent. It is a newer Python-based tool from the same community and the long-term successor.

Practically, xCAT is maintained, but new designs should not start there. If you run an old cluster, plan a migration. Check the OS support matrix before you upgrade distributions, because a new OS release is the most common moment when an older xCAT setup breaks.

## 3. Warewulf 4

Imagine a research group that wants every compute node rebuilt from a clean image each morning. That way, no leftover file from yesterday's experiment can cause a mystery bug. That idea sits at the heart of Warewulf.

Warewulf has been around since 2001. The README calls it "a stateless, network-boot cluster provisioning system designed primarily for use in HPC clusters." Stateless here means a node keeps nothing across a reboot. The v4 documentation lists its design tenets. Warewulf aims to be lightweight, simple, flexible and agnostic, running on x86 and ARM across many distributions. It is secure, with SELinux supported, and it is open source.

### Architecture

When a Warewulf node fails to boot, you go looking for the file that controls it. The layout is worth learning early, because most problems come down to one of a few files. You run a Warewulf server that contains `warewulfd` and the `wwctl` CLI, where CLI means command-line interface.

- The Warewulf server runs the `warewulfd` daemon and the `wwctl` CLI. The server config is `/etc/warewulf/warewulf.conf`. The node database is `/etc/warewulf/nodes.conf`, a YAML file. Image roots sit under `/var/lib/warewulf/chroots/`. Distribution overlays live under `/usr/share/warewulf/overlays/`, and site overlays under `/var/lib/warewulf/overlays/`. Built per-node overlay images go to `/var/lib/warewulf/provision/`. The docs keep these paths in a quick-reference list.
- Nodes carry their network configuration, IPMI settings, kernel arguments, and image and overlay assignments. Profiles apply settings shared by many nodes. You can use hostlist syntax, such as `n[1-10]`, in commands, so one command can touch a whole block of nodes.
- Images are bootable OS root filesystems, managed with container tooling. You can import one from a registry such as Docker Hub or a private registry, or build one from a Dockerfile in CI/CD. By default, an image runs entirely in memory, so a reboot returns the node to a known-good state.
- Overlays are collections of files and `.ww` templates. Warewulf renders each template for each node from the node registry, so `nodes.conf` becomes a rich metadata store. Overlays are applied over the image at boot, as system overlays, and periodically at runtime, as runtime overlays. Core functions such as `hosts`, `fstab`, `ssh`, network config, `dhcpd` and `nfsd` are overlays too. Run `wwctl overlay blame <node>` to see which overlay contributes each file. That single command answers the question "where did this file come from?" which is the first question in most debugging sessions.
- Services are set up by `wwctl configure --all`, which configures DHCP, TFTP, NFS, SSH and the hosts file. The `warewulf.conf` file sets the address ranges and the iPXE binary for each architecture. The quickstart config maps the architecture code `00:00` to `undionly.kpxe`. It maps `00:07` and `00:09` to the x64 EFI iPXE binary, and `00:0B` to the arm64 binary. These codes match the DHCP option-93 values from 6.22. The same file also lists NFS exports, `/home` and `/opt`, and `image mounts`.

### Commands (from the quick reference)

The quick reference is short enough to keep beside you while you work. The comment on each line says what the command does, so you can read the block as a set of small, separate actions.

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

The image import line is the docs' own example, and it is only one of the formats the import accepts. The same command takes a .tar file, a .sif file or a plain directory, so you can start from whatever image your team already has.

A chroot, short for change root, is a directory tree that looks like a complete Linux root filesystem. Warewulf unpacks an image into that tree and then packs it for the node to load. Because the tree is an ordinary directory, you can open any file in it with normal Linux tools before you boot a single node. That habit catches a missing package long before it becomes a boot failure.

A typical workflow starts by installing the RPM or DEB package. Next, you edit `warewulf.conf` and run `wwctl configure --all`. Then you import an image. Drivers, Slurm and the GPU stack go into the image when you build your own. Add the nodes with their MACs, power them on, and watch them boot with `wwctl node status`. Finally, adjust the overlays for Slurm, munge and Lmod. Munge is the authentication service that Slurm uses between its daemons, and Lmod is the module system that loads software environments.

Warewulf's strengths are its simplicity, its openness and its container-native images. It has a small footprint and scales to thousands of nodes. It also fits GitOps, because `nodes.conf` and the images can live in version control, and a change becomes a reviewed commit rather than a command typed on a console.

Its limits matter just as much. Warewulf only provisions. It has no built-in monitoring, health checks or user management, and its power control goes no further than IPMI settings. You assemble the rest yourself, including Slurm, monitoring and LDAP. GPU stack integration happens in your image build. Commercial support comes from CIQ and others. Choose Warewulf when you are ready to assemble the rest of the stack yourself, and when your team enjoys owning that assembly.

## 4. Confluent, MAAS, Foreman (general knowledge, verify)

Not every fleet is an HPC cluster. Picture a team that has a few hundred bare-metal servers, a request to feed a Kubernetes platform, and no appetite for a large in-house provisioning project. Some tools in this section were built for that kind of job. The notes below come from general knowledge, so verify each one against the current documentation before you rely on it.

- Confluent comes from the xCAT Consortium. It is a Python-based successor to xCAT with an asynchronous design. It offers a web API and a CLI, with commands such as `nodedeploy`, `nodeconfig`, `nodeshell`... It handles hardware discovery and OS deployment, including Redfish-driven deployment. The xCAT project recommends it for new deployments, as the xCAT README says.
- Canonical MAAS stands for Metal as a Service. It treats physical servers, along with KVM and LXD virtual machines, as an API-driven cloud. The minimum hardware for a MAAS server is as follows. You need SSD drives in RAID-1 with over `120 GB` of disk space. The CPU must be a dual-core over `2 GHz` with virtualization enabled. You also need `2 GB` of RAM and a `1 Gb/s` NIC. You install MAAS via `ppa:maas/3.2`, using the `maas` and `maas-region-controller` packages. You then manage it at `http://<MAAS_IP>:5240/MAAS`. MAAS splits a central **region controller** from distributed **rack controllers**, which gives you scale and high availability.

  A physical server moves through three states. In `New`, its MAC and BMC/IPMI settings are registered with the `LAN_2_0` or Redfish power driver. In `Commission`, it PXE-boots a temporary environment that inventories its NICs, disks and hardware. In `Deploy`, it installs Ubuntu, CentOS 7/8, Oracle Linux, Windows or ESXi. Custom images require Ubuntu Pro. Once a node is deployed, its IP cannot be changed in MAAS. Do not enable direct public repository updates on compute nodes, because kernel upgrades can break Mellanox/NVIDIA drivers. A kernel that updates itself overnight can leave a GPU node with a driver that no longer matches it.
- Foreman works with Katello, Puppet, Ansible or Salt. It manages the lifecycle of bare-metal servers, VMs on KVM and VMware, Docker, and clouds such as OpenStack, EC2, Azure and GCE. A single Foreman server does not scale horizontally on its own. **Smart-proxies** spread DHCP, TFTP, DNS and provisioning across large installations, so each network segment gets a helper close to its nodes.

Decide which of these three fits your fleet before you choose a manager. A fleet that looks like a cloud usually points toward MAAS or Foreman. A fleet that looks like a supercomputer usually points toward xCAT, Warewulf or BCM.

Ask three questions to narrow the field. Does the fleet need to behave like a cloud, with servers that users or teams request on their own? Does it need HPC scheduling and a GPU stack built in from the start? Does your team already run Puppet or Ansible, and want the manager to fit into that work? The answers usually point to one tool quickly. Confluent fits best where a team already knows xCAT and wants the successor the xCAT project recommends.

## 5. NVIDIA Base Command Manager (BCM)

Picture a DGX cluster that arrives with its management software already installed. The vendor expects you to run it from the first day. That is the situation BCM is built for.

BCM, formerly Bright Cluster Manager, is NVIDIA's cluster management product. It comes bundled with DGX systems and is sold for AI clusters. There is a free licence tier for clusters of up to `16` nodes and `16` GPUs or fewer. Part 8 covers BCM in depth. This section keeps only the model that matters for this comparison, taken from the BCM 11 administrator and installation manuals.

- The head node is the centre of the system. It holds the head copy of the software images under `/cm/images/<image>`. On a fresh install, that image is `default-image`. It also runs CMDaemon, the daemon that manages devices, provisioning and monitoring. Nodes boot from the network and receive a *known good state* from the head node. A diskless node gets the image copied into memory (tmpfs). A diskful node has its local disk contents checked against the image, and any differing content is corrected.
- A software image is the root file system. A category groups nodes and sets their software image, disk layout, services and parameters. Each individual node, called a device, belongs to a category and can override some settings. To make some nodes behave differently, you clone a category, point the clone at a modified image, and move the nodes into it with `cmsh`. The manual's example runs `category; clone default categorytwo; set softwareimage imagetwo; commit`. Then it runs `device; use node099; set category categorytwo; commit`. A `foreach` loop over a range does the same for many nodes.

The reason for a known good state is drift. Over months, a node picks up hand edits, half-finished upgrades and forgotten fixes. When the node reboots and checks itself against the image, those differences are corrected. That keeps two nodes that should match from quietly becoming two different machines, which is the kind of mismatch that causes the hardest bugs to find.
- Large clusters designate provisioning nodes, which serve images to other nodes. Run `updateprovisioners` from `softwareimage` mode to push head-copy changes to them. It also runs automatically when changes go through CMDaemon. If a node is lost while a provisioning request is pending, the request is retried after a timeout. The manual cites 180 seconds for that timeout.
- The node installer is an early boot phase on each node. It identifies the node, partitions the disks and syncs the image, then hands over to the OS. Finalize scripts customise the result. For example, SELinux initialisation happens at the very end of the node-installer phase on BCM-provisioned nodes.
- `cmsh` is a shell with modes such as `device`, `category`, `softwareimage` and `partition`. Base View is the web UI. A JSON-RPC API and `cm-` utilities are also available. Configuration and monitoring share one database, so a change you make in the shell shows up in the web view as well.

Integration covers Slurm, PBS, Kubernetes, Jupyter, GPU and DCGM monitoring, health checks, Redfish power, and NVIDIA-validated reference architectures such as DGX BasePOD and SuperPOD. DCGM is NVIDIA's Data Center GPU Manager, the tool that reports GPU health and telemetry. Licensing is per node, and support comes from NVIDIA.

The trade-off is clear. BCM comes with batteries included, is vendor-validated, gives you a single support path, and carries deep GPU-system knowledge. In return, you pay a license cost and accept a closed core. Its cluster workflows are BCM's own, so you get less pure GitOps, though you can still script it with `cmsh` or the API. Weigh that support path against the license cost before you choose BCM.

## 6. Selection matrix

A procurement form lands on your desk next week, and one of its lines asks which cluster manager you plan to use. Answering that line well means comparing the managers on the criteria that matter to your site, not on a general sense of which one is popular. The matrix below compares the six managers on the same criteria. Each row is one question you would ask about a manager, such as how far it scales or how well it fits GPU systems.

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

Start with the decision in front of you. If you are buying DGX or HGX systems with NVIDIA support, or you need integrated monitoring, choose BCM. If you are building an open-source HPC cluster with your own automation, choose Warewulf and bring Ansible, Prometheus and Slurm along. If you already run xCAT, stay put and plan a move to Confluent. For a cloud-style GPU fleet that feeds Kubernetes, look at MAAS or the provider's tooling. A mixed site often needs a different answer for each part. A DGX partition may take BCM, while a research partition built on commodity servers may take Warewulf. Be careful about running two managers on the same network, because each one wants to answer DHCP and PXE requests. Give each network segment exactly one owner.

Whichever you pick, ask who will operate it at 3 a.m.

## 7. Operating practices that carry across managers

Imagine the head node fails on a Friday evening, and the only copy of the cluster design lives in one engineer's memory. The cluster may run for weeks, but nobody can rebuild it. Good practice keeps the design outside the manager, so that any of these tools can be replaced or restored.

Your inventory belongs in version control. Keep it as CSV or YAML, or export it on a regular schedule from the manager's database. The manager's database is not a backup of your design. It records what the manager knows, which is not always what you intended.

Back up the manager state as well. For xCAT, that means a database dump. For Warewulf, it means `nodes.conf` and the chroots. For BCM, it means the head-node backup and `cmsh` exports. Protect the head or management node with high availability too. BCM has head-node failover, Warewulf can run on replicated hosts, and xCAT uses service nodes and backups.

Roll out image changes in stages, using canary categories or profiles. A canary is a small group of nodes that receives a change first, so a bad image hurts a few nodes instead of the whole fleet. Let Slurm drain and reboot nodes automatically as part of that rollout, so jobs finish before a node goes down.

Document the node replacement procedure before you need it. Update the MAC address in your inventory, reprovision the node, verify it, and then resume it. Secure the management plane as well, with network isolation, rotated BMC credentials, TLS, auditing and restricted access. The management plane is the set of networks and services that can power nodes on and off, so it deserves stricter rules than the compute network.

Treat the cluster definition as code. A change to a node, an image or an overlay should arrive as a reviewed commit with a message that says why it was made. When you read that history six months later, it tells you what changed and who approved it. A manager's database alone cannot give you that story, because it only shows the current state.

## 8. Lab (self-checking xCAT/Warewulf/BCM lab tested; VM cluster parts untested)

Start with the self-checking Python lab at `code/part06/cluster_mgr_lab.py`, and run it on your own machine. It checks the xCAT `hosts.ip` regex rule, `|\D+(\d+)|10.0.0.(10+$1)|`, and the other values in the table below, so you can compare each result against what the lab expects.

| Check | Expected values |
|---|---|
| xCAT `hosts.ip` regex rule | node1 to 10.0.0.11, node15 to 10.0.0.25, node100 to 10.0.0.110 |
| xCAT `policy` authorization, in ascending numeric priority order | Priority 1 `root`, priority 2 `xadmin nodels`, priority 7 `xadmin rpower stat` on `h02-h05` |
| Other parameters | 15 `litefile` writable tmpfs paths, MAAS port 5240, BCM 180 s provisioning retry, 16-node free tier |

A self-checking lab is a small program that tests itself against answers it already knows. When a check fails, the message names the value that was missed, which tells you exactly which rule to reread. Use it to learn the regex and policy rules before you touch a real cluster, because a wrong regex on a live head node can give a whole rack the wrong addresses.

Run the lab with this command.

```bash
python3 code/part06/cluster_mgr_lab.py
```

The lab checks logic on your own machine. The xCAT, Warewulf and BCM commands in the steps below have not been run on a live cluster, so treat them as your own checklist.

Once the lab passes, work through these five steps on a VM testbed.

1. Install Warewulf on a Rocky or Alma VM by following the quickstart. Import a Rocky image, add two VM nodes with MACs, and boot them. Then check them with `wwctl node status` and `wwctl overlay blame`.
2. Add a Slurm client and munge to the image by building your own image from a Dockerfile. Then add a template overlay that renders each node's `slurm.conf` fragment from tags in `nodes.conf`.
3. Read the xCAT `nodeset`, `genimage` and `packimage` man pages. Write the command sequence for a stateless deployment, then compare it line by line with the Warewulf flow.
4. Read the BCM category and software image sections. Write the `cmsh` commands that create a GPU category with a modified image.
5. Fill in the selection matrix for your own site constraints, and pick one manager.

## 9. Interview angles

These questions are a good way to test your understanding. Answer each one in a few sentences, as if a hiring manager were sitting across from you. For each answer, name the tool, the file or command you would reach for, and one trade-off. Interviewers listen for that pattern, because it shows you have run the tool and not only read about it.

- Compare xCAT, Warewulf and BCM in one minute each.
- What is a Warewulf overlay, and how does it differ from baking a file into the image?
- What are BCM categories and software images? How do you test a new image on a few nodes?
- Why would a site use service nodes in xCAT or provisioning nodes in BCM?
- Which manager would you pick for 4,000 H100 nodes, and why?
- How do you replace a failed node so that it keeps its name and image?
- What does xCAT's current status mean for planning?
- What does a cluster manager not do that Slurm and Kubernetes do?

## Exercises

Work through these six exercises in order. The first one needs only your own machine. The rest ask you to write or trace the commands, and you can check each answer against the chapter.

1. Run `python3 code/part06/cluster_mgr_lab.py` first. Then call `eval_xcat_hosts_ip_regex()` and `eval_xcat_policy()` from the same file. Explain why `chtab node=compute hosts.ip='|\D+(\d+)|10.0.0.(10+$1)|'` gives `node15` the address `10.0.0.25`. Trace how the `policy` table lets `xadmin` run `rpower stat` on `h02-h05` at priority `7`. Then explain why the same table blocks `rpower off` on `h03` and `rpower stat` on `h09`.
2. Write the complete six-step xCAT command sequence for a 100-node `statelite` cluster. Use Chapters 26 and 28 of Supercomputers for Linux SysAdmins as the reference. Start by importing `CentOS-7.6-x86_64-bin-DVD1.iso` with `copycds`. Define `node[1-100]` with `mkdef`. Build `centos7.6-x86_64-statelite-compute`, which uses `genimage`, a `litefile` with 15 writable tmpfs paths, `add_ssh`, `add_passwd` and `liteimg`. Generate `/etc/hosts`, DHCP and DNS with `makehosts`, `makedhcp`, `makenamed.conf` and `makedns`. Finish by booting the nodes with `nodeset` and `rpower`.
3. Write the `wwctl` commands for four jobs. Import an OCI (Open Container Initiative) container image with `wwctl image import`. Register 4 nodes with `wwctl node add`. Find where each file came from with `wwctl overlay blame n1`. Regenerate services with `wwctl configure --all`. Then explain the difference between system overlays and runtime overlays in your `.ww` templates. System overlays are applied once at boot, and runtime overlays are applied periodically while the node is running.
4. Write the `cmsh` command sequence that clones the `default` category into `categorytwo`. Bind that category to a modified software image, `imagetwo` under `/cm/images/imagetwo`. Move `node099` into `categorytwo`. Then propagate the updated image to the provisioning nodes with `updateprovisioners`.
5. Trace the three-stage node lifecycle in Canonical MAAS, `New -> Commission -> Deploy`. Use `http://<MAAS_IP>:5240/MAAS` and the difference between region controllers and rack controllers as your reference points. Explain why Chapter 26 of Supercomputers for Linux SysAdmins warns against enabling automatic public OS repository updates on GPU and InfiniBand compute nodes. Finally, explain how Foreman scales DHCP, TFTP and DNS with `smart-proxies`.
6. Pick the best cluster manager for each of three cases. Choose from NVIDIA BCM, Warewulf 4, Confluent and MAAS. Case one is a 512-node DGX H100 SuperPOD. It needs turnkey DCGM health checks and vendor support. Case two is a 256-node open-source academic cluster. Its team manages it through GitOps and OCI Dockerfiles. Case three is an existing 1,000-node IBM/Lenovo xCAT estate. Its team is planning the next-generation upgrade. Justify each choice in a few sentences.

## Checkpoint

<details>
<summary>1. Map the five core cluster-management abstractions (**Node record**, **Group/template**, **OS image**, **Per-node customization**, and **Remote shell**) across **xCAT**, **Warewulf 4**, and **NVIDIA BCM**.</summary>

- **Node record:** In xCAT, it is the `node` object, managed with `mkdef` and `chdef`. In Warewulf 4, it is a node in `/etc/warewulf/nodes.conf`, managed with `wwctl node`. In BCM, it is a `device` in the CMDaemon database, managed with `cmsh`.
- **Group / template:** In xCAT, it is a `nodegroup`. In Warewulf 4, it is a `profile`. In BCM, it is a `category`.
- **OS image:** In xCAT, it is an `osimage`, built with `genimage`, `packimage` and `liteimg`. In Warewulf 4, it is a container chroot at `/var/lib/warewulf/chroots/`. In BCM, it is a software image at `/cm/images/<name>`.
- **Per-node customization:** In xCAT, it is done with `postscripts` and `synclists`. In Warewulf 4, it is done with `.ww` overlays, both system and runtime. In BCM, it is done with node-installer and finalize scripts.
- **Remote shell:** In xCAT, you use `xdsh` or `psh`. In Warewulf 4, you use `pdsh`. In BCM, you use `pdsh` or `cmsh`.
</details>

<details>
<summary>2. What are the roles of the **Management node**, **Service nodes**, and **Compute nodes** in xCAT?</summary>

- **Management node:** It runs `xcatd`, holds the central configuration database and orchestrates the cluster.
- **Service nodes:** They are hierarchical relay servers, deployed per rack or pod. They take DHCP, TFTP, HTTP, DNS and image serving off the management node on clusters of several thousand nodes.
- **Compute nodes:** They are the worker nodes that get provisioned and controlled through IPMI or Redfish, using `rpower` and `rcons`.
</details>

<details>
<summary>3. In xCAT, what is the difference between table-level commands (`tabdump`, `tabedit`, `chtab`) and object-level commands (`lsdef`, `mkdef`, `chdef`, `rmdef`) (Supercomputers for Linux SysAdmins book, Chapter 26)?</summary>

- **Table-level commands (`tabdump`, `tabdump -d`, `tabedit`, `tabrestore`, `chtab`):** They read and write individual relational database tables directly, such as `site`, `hosts`, `mac`, `noderes`, `nodelist`, `nodetype`, `policy` and `litefile`.
- **Object-level commands (`lsdef`, `mkdef`, `chdef`, `rmdef`, `nodech`):** They work on logical objects such as `node`, `group`, `osimage`, `network`, `site` and `policy`. Each object spans several tables, so these commands keep the tables consistent with each other. You can also export and import stanzas with `lsdef -z` and `mkdef -z`.
</details>

<details>
<summary>4. What IP address does the xCAT regex rule `chtab node=compute hosts.ip='|\D+(\d+)|10.0.0.(10+$1)|'` assign to `node15`, and how does it work (Supercomputers for Linux SysAdmins book, Chapters 26 and 28)?</summary>

It assigns **`10.0.0.25`**. The regex `\D+(\d+)` strips the non-digit prefix, `node`, and captures the numeric suffix, `15`, as `$1`. The replacement then computes `10 + 15 = 25` for the fourth octet.
</details>

<details>
<summary>5. How do you grant a non-root user (`xadmin`) permission to run specific xCAT commands on a subset of nodes (Supercomputers for Linux SysAdmins book, Chapter 26)?</summary>

1. Run `/opt/xcat/share/xcat/scripts/setup-local-client.sh xadmin` to generate TLS client certificates in `~xadmin/.xcat/`.
2. Add an `allow` rule to the **`policy`** table. xCAT checks the rules in ascending numeric `priority` order, and the first match wins: `mkdef -t policy -o 7 name=xadmin commands=rpower parameters=stat noderange=h02-h05 rule=allow`. For example, that rule lets `xadmin` run `rpower stat` on `h02-h05` and nothing else in that table.
</details>

<details>
<summary>6. Compare xCAT's `statefull`, `stateless`, and `statelite` provisioning modes, and what is the role of the `litefile` table (Supercomputers for Linux SysAdmins book, Chapter 26)?</summary>

- **`statefull`:** It installs the OS permanently onto the node's local disk.
- **`stateless`:** It downloads and unpacks the entire root image (`packimage`) into RAM (`tmpfs`) on every boot.
- **`statelite`:** It mounts the root filesystem read-only over NFS (`liteimg`). Specific writable paths sit in RAM as `tmpfs`, such as `/etc/resolv.conf`, `/etc/ssh/`, `/tmp/`, `/var/` and `/root/.ssh/`. The **`litefile`** table decides which paths those are, and it has 15 or more entries.
</details>

<details>
<summary>7. What is the current upstream status of **xCAT**, and what is its recommended successor?</summary>

The xCAT Consortium, working with VersatusHPC, changed course on the earlier sunset. It keeps maintaining `xcat-core`, and it plans Enterprise Linux 10 support. It still recommends **Confluent** for new deployments. Confluent is `xcat2/confluent`, a modern Python-based provisioning system from the same community.
</details>

<details>
<summary>8. Where does **Warewulf 4** store its server configuration, node inventory, container chroots, and overlays?</summary>

- **Server config:** `/etc/warewulf/warewulf.conf`
- **Node and profile database:** `/etc/warewulf/nodes.conf`, a plain YAML file that suits GitOps well.
- **Unpacked OS container chroots:** `/var/lib/warewulf/chroots/`
- **Overlays:** `/usr/share/warewulf/overlays/` holds the distribution defaults, and `/var/lib/warewulf/overlays/` holds the site customizations.
- **Built per-node overlay archives:** `/var/lib/warewulf/provision/`
</details>

<details>
<summary>9. How do Warewulf 4 **system overlays** and **runtime overlays** work, and what does `wwctl overlay blame <node>` show?</summary>

An overlay is a directory of files and `.ww` Go templates. The templates take their values from per-node attributes in `nodes.conf`. Overlays sit on top of the base container image, and they do not change the image itself.

- **System overlays:** They are applied once during early boot (`initramfs`).
- **Runtime overlays:** They are fetched and applied periodically while the node runs (`wwclient`).

`wwctl overlay blame <node>` lists every overlaid file on the node, and it shows which overlay contributed each one.
</details>

<details>
<summary>10. What does `wwctl configure --all` do in Warewulf 4?</summary>

It reads `/etc/warewulf/warewulf.conf` and `/etc/warewulf/nodes.conf`. Then it writes or updates the host's `/etc/hosts`, DHCP (`dhcpd.conf` or `dnsmasq`), TFTP, NFS (`/etc/exports`), SSH keys and TLS certificates. For TFTP, it copies the iPXE binaries for BIOS `00:00`, x64 EFI `00:07` and `00:09`, and ARM64 `00:0B`.
</details>

<details>
<summary>11. Describe the architecture of **NVIDIA Base Command Manager (BCM)** (`Head node`, `CMDaemon`, `/cm/images`, `Categories`, and `Provisioning nodes`).</summary>

- **Head node and `CMDaemon`:** The head node runs `CMDaemon`, the central management server. You configure it with `cmsh`, the Base View web UI or JSON-RPC. It stores the master software images under **`/cm/images/<image>`**.
- **Categories:** They group nodes and bind a **software image**, a disk partitioning layout, network roles and service configurations to the member devices.
- **Provisioning nodes:** They are scale-out relay nodes. They mirror software images from the head node through `updateprovisioners`, so they can provision large compute fleets.
</details>

<details>
<summary>12. How do you safely test a modified OS image on a canary node in NVIDIA BCM using `cmsh`?</summary>

Clone `default-image` to `imagetwo`, then modify `/cm/images/imagetwo`. Clone the category with `category; clone default categorytwo; set softwareimage imagetwo; commit`. Assign the canary node to the new category with `device; use node099; set category categorytwo; commit`, and then reboot `node099`.
</details>

<details>
<summary>13. What happens during BCM's **node-installer** boot phase on diskless versus diskful compute nodes?</summary>

When a BCM node boots over PXE or HTTP, it enters the **node-installer** environment. There it identifies the device, configures the hardware and disks, and syncs the category's software image.

- **Diskless node:** It downloads the software image and unpacks it straight into RAM, which is `tmpfs`.
- **Diskful node:** It compares its local disk with the head node's software image using an `rsync`-style delta sync, and it corrects any drifted files. Then it runs finalize scripts, such as SELinux labeling, and pivots into the OS.
</details>

<details>
<summary>14. What free license tier does Supercomputers for Linux SysAdmins book, Chapter 26, note for NVIDIA Base Command Manager?</summary>

BCM has a free license tier for small clusters. It covers up to **`16` nodes and `16` GPUs**, or fewer.
</details>

<details>
<summary>15. How does **Canonical MAAS** structure its controllers, and what are the three lifecycle states when onboarding a bare-metal server (Supercomputers for Linux SysAdmins book, Chapter 26)?</summary>

MAAS splits its controllers into a central **region controller**, found at `http://<MAAS_IP>:5240/MAAS`, and distributed **rack controllers**. The rack controllers handle local DHCP, TFTP, HTTP images and BMC power. A server goes through three steps when it is onboarded:

1. **`New`:** Its node MAC and BMC, the `LAN_2_0` IPMI or Redfish settings, are registered.
2. **`Commission`:** It PXE-boots an ephemeral image that inventories the CPU, RAM, NICs, LLDP and disks, and that runs hardware tests.
3. **`Deploy`:** The target OS image is installed onto the node.
</details>

<details>
<summary>16. Why does Supercomputers for Linux SysAdmins book, Chapter 26, warn against enabling automatic public repository updates on MAAS-deployed HPC/GPU compute nodes?</summary>

An unattended `apt upgrade` or `dnf update` from a public repository can install a new Linux kernel. That kernel can break ABI compatibility with the installed NVIDIA GPU driver or the Mellanox OFED InfiniBand stack. It can also cause software drift between nodes.
</details>

<details>
<summary>17. How does **Foreman** (with Katello) scale bare-metal provisioning across multiple network segments (Supercomputers for Linux SysAdmins book, Chapter 26)?</summary>

A single Foreman server does not scale horizontally on its own. So Foreman deploys **`smart-proxies`**, which run as `foreman-proxy`, on each subnet or rack. For example, each subnet or rack gets its own proxy, and each one handles local DHCP, DNS and TFTP, runs Puppet or Ansible, and handles content caching with `Katello`/`Pulp`.
</details>

<details>
<summary>18. Which of the six cluster managers (xCAT, Warewulf 4, Confluent, MAAS, Foreman, BCM) include built-in GPU/DCGM telemetry, health checks, and native Slurm/Kubernetes deployment?</summary>

**NVIDIA Base Command Manager (BCM)** includes these out of the box. It has integrated DCGM GPU monitoring, automated health checks, and turnkey Slurm and Kubernetes deployment. With Warewulf 4, xCAT, Confluent, MAAS or Foreman, the operator adds Slurm, DCGM with Prometheus, and health checks through images, overlays, or Ansible or Puppet.
</details>

<details>
<summary>19. Regardless of which cluster manager you use, why must you export and version-control your node inventory and image definitions in Git?</summary>

A cluster manager's database, whether SQLite, MySQL or PostgreSQL, holds runtime state. It is not a design audit trail. Keep the canonical node inventory in Git, with MACs, IPs, rack and U locations, and roles. Keep the image build recipes there too, including `Dockerfile`s, package lists and overlays. With both in Git, you get deterministic disaster recovery, peer-reviewed changes, and migration between cluster managers.
</details>

<details>
<summary>20. Walk through the standard operational procedure for replacing a failed bare-metal compute node (`gpu042`) under any cluster manager.</summary>

1. Drain `gpu042` in Slurm with `scontrol update NodeName=gpu042 State=drain Reason="motherboard swap INC456"`.
2. Swap the node or motherboard physically, and record the new host NIC and BMC MAC addresses. You can also discover them through switch port LLDP or DHCP.
3. Update `gpu042`'s MAC address in your version-controlled inventory and in the cluster manager. Use `chdef`, `wwctl node set` or `cmsh`, depending on the manager.
4. Boot `gpu042` over the network with `rpower gpu042 boot`. It then gets the same hostname, IP and golden OS image as before.
5. Run the acceptance and health checks, such as `node_health.sh`, DCGM and the IB link check. Then resume the node in Slurm with `scontrol update NodeName=gpu042 State=resume`.
</details>

## Sources and review notes

- Book source (`supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to-hardware`, *Supercomputers for Linux Sysadmins*):
  - Chapter 26 ("26. Cluster Management Systems – xCAT and Others", read in full): xCAT installation, logical object types (`site`, `node`, `group`, `network`, `osdistro`, `osimage`, `route`, `auditlog`, `boottarget`, `eventlog`, `firmware`, `kit`, `kitcomponent`, `kitrepo`, `monitoring`, `notification`, `pdu`, `policy`, `rack`, `taskstate`, `zone`), database tables (`site`, `hosts`, `mac`, `noderes`, `nodelist`, `nodetype`, `networks`, `passwd`, `policy`, `litefile`, `litetree`, `statelite`, `postscripts`), `tabdump`/`tabdump -d`/`tabedit`/`tabrestore`/`chtab` vs `lsdef`/`mkdef`/`chdef`/`rmdef`/`nodech`, `lsdef node1` output, `setup-local-client.sh` and `policy` table authorization, regex IP rule `chtab node=compute hosts.ip='|\D+(\d+)|10.0.0.(10+$1)|'`, `litefile` 15 entries and `liteimg`, `rpower` Table 26-1, `psh`/`pscp`, Canonical MAAS (`ppa:maas/3.2`, port `5240/MAAS`, `New` → `Commission` → `Deploy`, rack controllers), Foreman (`smart-proxies`), and NVIDIA Base Command Manager (`16` nodes / `16` GPUs free tier).
  - Chapter 28 ("28. One-Two-Three Instructions", read in full): xCAT 100-node `statelite` recipe (`copycds`, `mkdef`, `chtab`, `genimage`, `litefile`, `add_ssh`, `add_passwd`, `liteimg`, `makehosts`, `makedhcp`, `makenamed.conf`, `makedns`, `nodeset`, `rpower`).
- xCAT architecture and commands: `xcat-core` README and docs tree (overview/architecture, admin guide manual pages) at commit `56a009b`; positioning text paraphrased from the README ("sunset ... changed course", Confluent recommendation).
- Warewulf: `warewulf/userdocs` (introduction, EL quickstart, quick reference, overlays) at commit `324c0bc`.
- BCM: `bcm11-admin`, `bcm11-install`, and `bcm11-containerization` manuals in the corpus (software images, categories, provisioning, `180` s retry, node installer); see Part 8.
- Run here: `python3 code/part06/cluster_mgr_lab.py` (3 passed, 0 failed).
- Explicitly labelled inferences: `eval_xcat_hosts_ip_regex` and `eval_xcat_policy` in `code/part06/cluster_mgr_lab.py` are deterministic Python models of xCAT's `hosts.ip` regex substitution and `policy` table priority evaluation from *Supercomputers for Linux Sysadmins* Chapter 26.
- Not verified on live hardware: Confluent CLI commands, MAAS and Foreman live deployments, and live `xcatd` / `warewulfd` / `CMDaemon` daemon execution (`untested here`).
