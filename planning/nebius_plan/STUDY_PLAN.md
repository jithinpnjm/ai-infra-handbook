# Nebius SRE interview: personalised 14-day plan (25 Nov to 8 Dec 2026, interview 9 Dec)

Built from the section-level maps in `map/` (one file per chapter, written by agents that read the whole chapter). Each map lists every section with level, interview use, priority (MUST/SHOULD/OPTIONAL/SKIP) and minutes. **Daily reading budget = MUST sections only (about 5 h), plus 1-1.5 h hands-on practice and 20 min flashcards.**
For you: beginner in Linux and networking (so these come first, with real terminal work), refresh for Python and Kubernetes, Ansible and Slurm basics added, first Linux-troubleshooting and first system-design interview (design drills from day 11, incident drills from day 12).

How to use a day: open the chapter map, read ONLY the rows marked MUST in order (the sections column lists them), do the hands-on listed in the map, then the day's practice block.


## Day 1 - Wed 25 Nov - MUST reading 5.3 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 20.1 The Nebius loop and how to use this volume (`map/20-01.md`) | 21 | 19 | MUST-READ-FULL, because it is the navigation spine of the volume and sets the think-aloud script (section 5) that every round depends on; about 45 minutes. |
| 20.2 The role in one page: the job posting line by line (`map/20-02.md`) | 25 | 18 | READ-SECTIONS: sections 2 and 4 (line tables), 5 (template), 6 (public Token Factory facts), 9 (gaps), the four "How to answer out loud" questions and Scenarios 1-2; sect |
| 1.1 The Linux big picture: kernel, userspace, distributions (`map/01-01.md`) | 35 | 37 | MUST-READ-FULL. It is the foundation for every later Linux chapter, and the layer-first troubleshooting habit is what R1 and R2 test. |
| 1.2 The command line: shells, commands, pipes and redirectio (`map/01-02.md`) | 41 | 42 | READ-SECTIONS (2, 2.1, 2.2, 3.1, 3.2, 5, 6, 7, 7.1, 8, 10, How it fails) because R1 tests shell and console skills directly and the rest is reference. Skip the trivia and |
| 1.3 Files and the directory hierarchy: paths, links, inodes (`map/01-03.md`) | 18 | 48 | READ-SECTIONS (1, 2 notes, 3, 4, 5 symlinks and atomic latest, 7 find, 8 safe tar use, 9, How it fails 1, 4 and 5) because the inode and deleted-but-open failures are lik |
| 1.4 Text-processing essentials: grep, sed, awk, find, xargs, (`map/01-04.md`) | 24 | 25 | READ-SECTIONS (1, 2, 3, 4 with both pipelines, 6 awk groupings, 7 xargs, 8 machine-readable output, 10 recipes 1, 5, 7, 9, plus How it fails 1, 2, 4, 6). It is the most d |
| 1.5 Working remotely: SSH keys, file transfer, tmux and edit (`map/01-05.md`) | 21 | 36 | READ-SECTIONS (1, 2, 3 running commands/config/port forwarding/debugging, 4.1 rsync, 6, 9, How it fails 1, 2, 3, 5, 7). These match the access path and triage questions m |
| 1.6 Users, groups, permissions, ACLs, sudo and user environm (`map/01-06.md`) | 30 | 53 | READ-SECTIONS (1 intro, 2, 3 all subsections, 4 mask only, 5 sudo and the three-identity distinction, 6 startup pitfalls, 7 limits, 8.1, 8.5, 9, How it fails 1, 2, 4, 5,  |
| 1.8 Processes, signals and job control (`map/01-08.md`) | 55 | 40 | READ-SECTIONS. Read sections 2 (process model), 3 (observation tools), 4 (signals), 5 (job control), 7 (limits), 8 (load, vmstat, memory), 9 (cgroups), 10 and "How it fai |
| 1.9 Shell scripting that survives production (`map/01-09.md`) | 52 | 28 | READ-SECTIONS. Read sections 1 (shape of a script), 2 (quoting and expansion), 3 (exit codes), 4 (tests), 5 (loops), 6 (temp files, heredocs), 8 (strict mode, traps, lock |

Practice: Terminal: set up a Linux VM/WSL/container; type every command from the chapters, do not just read.


## Day 2 - Thu 26 Nov - MUST reading 4.3 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 1.11 How a program runs: system calls, libraries, ELF, strac (`map/01-11.md`) | 36 | 41 | READ-SECTIONS. Read in full: section 1 (startup sequence), section 4 (syscall mechanism and the common-calls table), section 5 (soname and glibc version errors, LD_LIBRAR |
| 1.12 Disks, partitions and filesystems (`map/01-12.md`) | 43 | 54 | READ-SECTIONS. Read in full: section 1 (stack), 2 (disk types table and "How storage is attached"), 4 (filesystem types and the `mkfs` options), 5 (mount options, UUIDs,  |
| 1.15 systemd: units, targets, timers, journald (`map/01-15.md`) | 63 | 30 | READ-SECTIONS. Read in full: section 2 "Service types" and "Common [Service] options" table, section 3 (`systemctl` commands and "Enabling and starting"), section 4 "Depe |
| 1.16 Logging, time synchronisation, cron and batch jobs (`map/01-16.md`) | 50 | 24 | READ-SECTIONS. Read in full: section 2 (the question-to-command table and GPU reading habits), section 3 "Rotating logs" (open-file/inode paragraph and `copytruncate` vs  |
| 1.17 Memory management: virtual memory, NUMA, huge pages, OO (`map/01-17.md`) | 66 | 33 | READ-SECTIONS. Read in full: section 2 "Swap" and "Overcommit" (short), section 3 "NUMA trap" paragraph and "Discover the topology" commands, section 4 (watermarks, `vm.s |

Practice: Terminal: run ps, top, free, df, lsof, strace on your own box; break something small and fix it.


## Day 3 - Fri 27 Nov - MUST reading 4.8 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 1.18 CPU scheduling and cgroups v1 and v2 (`map/01-18.md`) | 70 | 32 | READ-SECTIONS. Read in full: section 2 "Run queues, time sharing" and "Scheduling classes and policies" (table), "Load balancing and migration cost", section 3 "Observing |
| 1.19 Namespaces: the kernel feature behind containers (`map/01-19.md`) | 47 | 20 | MUST-READ-FULL - container internals, PID 1 signal behaviour, overlay copy-up, and `nsenter` debugging are asked directly in troubleshooting rounds and are the basis of m |
| 1.23 Performance methodology: USE, workload characterisation (`map/01-23.md`) | 72 | 23 | READ-SECTIONS (3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 17, 18) - the method, the 60-second checklist, USE/RED and the queueing and capacity sections are what the interviewer |
| 20.3 Triage method for a sick Linux box (`map/20-03.md`) | 57 | 8 | MUST-READ-FULL, because it is the spine of the Linux console round and every later Part-B chapter (20.4 to 20.7) builds on its 60-second checklist and USE sweep; plan abo |
| 20.4 Files, descriptors, syscalls and permissions (`map/20-04.md`) | 44 | 14 | READ-SECTIONS: 1, 2, 3, 4, 5, 6 (the top layers: path, identity, mode class, ACL, mount), How to answer Q1-Q3, Scenarios 1, 2, 3, 6, 8, and the drill questions; SKIM sect |

Practice: Do one full triage on a VM using the 20.3 checklist; write the 60-second USE summary.


## Day 4 - Sat 28 Nov - MUST reading 5.1 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 20.5 CPU, memory, disk and the scheduler (`map/20-05.md`) | 52 | 16 | READ-SECTIONS: intro, 1, 2, 3, 6, 7, 8, 9, 12 (budget arithmetic only), How to answer Q1-Q5, Scenarios 1-5, drill questions; SKIM sections 4, 5, 10 and 11 (steal, NUMA, p |
| 2.1 What happens when you curl a URL: a packet's journey end (`map/02-01.md`) | 55 | 16 | MUST-READ-FULL. It is the spine of the whole Part and the classic "what happens when you curl" question is answered from it; the layer-by-layer symptom table (section 12) |
| 2.2 How networks work: layers, encapsulation, the TCP/IP mod (`map/02-02.md`) | 46 | 21 | READ-SECTIONS. Read sections 3 (DoD/OSI/Comparison), 4 (Encapsulation, MTU/MSS, Demultiplexing), 7 (Linux stack) and the checkpoints; SKIM-FOR-RECALL the rest, because th |
| 2.3 Ethernet and L2: frames, MAC addresses, switching, ARP a (`map/02-03.md`) | 53 | 24 | READ-SECTIONS. Read sections 2, 3, 5 (learning, flooding, loops), 6 (ARP, NDP, Linux multi-NIC ARP), 10 (failure table) and the checkpoints; SKIM-FOR-RECALL the optics na |
| 2.4 IP addressing, subnetting and CIDR (IPv4 and IPv6), with (`map/02-04.md`) | 58 | 18 | READ-SECTIONS. Read sections 2 (IPv4 masks, block-size method, same-subnet check), 3 (VLSM and summarisation), 4 (special ranges), 6 (IPv6 notation, address types, /64 st |
| 2.5 Routing on a host: routing tables, default gateways and  (`map/02-05.md`) | 41 | 24 | READ-SECTIONS. Read sections 1 (routing decision), 2 (reading the table, longest-prefix and metrics, `ip route get`), 4 (source address), 5 (weak host, rp_filter, SSH-on- |

Practice: Terminal: ip, ss, ping, traceroute, dig on your machine; read one tcpdump capture.


## Day 5 - Sun 29 Nov - MUST reading 4.8 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 2.6 TCP in depth: handshake, windows, congestion control, tu (`map/02-06.md`) | 61 | 21 | READ-SECTIONS. Read sections 1 (what transport solves, flow vs congestion control), 4 (handshake, listen queues, error table, TIME_WAIT vs CLOSE_WAIT, TCP states), 5 (RTO |
| 2.7 UDP, ICMP and the diagnostic toolkit: ping, traceroute,  (`map/02-07.md`) | 47 | 9 | READ-SECTIONS. Read sections 1 (UDP header, ECONNREFUSED, UdpRcvbufErrors), 2 (ICMP types, the must-never-block list), 3 and "Reading ping output" (TTL, Host vs Net Unrea |
| 2.8 DNS in depth: resolution, records, resolvers and caching (`map/02-08.md`) | 45 | 11 | READ-SECTIONS. Read 1 (zones, delegation, glue, stub vs recursive vs authoritative), 2 (lookup walk-through, TTL, negative caching, UDP/TCP and response codes), 3 (record |
| 2.10 HTTP, TLS and PKI basics (`map/02-10.md`) | 40 | 17 | READ-SECTIONS. Read 1 ("HTTP in practice" table and status-code paragraph, "Connections and versions" for idle timeouts and streaming, "`curl` as a diagnostic tool"), 2 ( |
| 2.20 Load balancing: L4, L7, ECMP hashing, proxies and infer (`map/02-20.md`) | 46 | 41 | READ-SECTIONS (sections 0, 1, 2, 3, 4, 7, 8, 9, 10, 12, 13). Load balancing and inference routing are the most likely R3 design topic, and the troubleshooting table is R1 |
| 2.22 Linux networking I: inspecting state with ip, ss, count (`map/02-22.md`) | 49 | 18 | READ-SECTIONS (intro, 1, 2, 4, 5, 8, 10, 11, checkpoints 2, 3, 8, 11, 12, 20). This is the most practical chapter for R1. Read the commands in sections 2, 4 and 5 by hear |

Practice: Terminal: curl -v/-w timing; dig +trace; ss -tnp; explain each aloud.


## Day 6 - Mon 30 Nov - MUST reading 5.3 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 2.25 Linux networking IV: namespaces, veth, bridges and cont (`map/02-25.md`) | 51 | 13 | READ-SECTIONS (1, 2 intro and the first script, 3 modes table, 4 ADD/DEL and model, 5 walkthrough, 6 items 1, 2, 4, 5, 7 debugging section 7, 9, 10). The macvlan/ipvlan a |
| 2.26 Packet capture from scratch: tcpdump, tshark, Wireshark (`map/02-26.md`) | 54 | 18 | READ-SECTIONS (intro, 1 capture points table, 2 commands and filter table, 2 "What tcpdump shows", 3 TCP-reading patterns, 4 protocol table, 5 containers and capture-at-s |
| 2.30 Network troubleshooting: method, models and case studie (`map/02-30.md`) | 32 | 19 | READ-SECTIONS (sections 1-4, 5 for the kit concept, 6 all, Cases 2, 3, 8, 13, 14, sections 9 and 10, then skim the rest). The method is the core of an R1/R2 troubleshooti |
| 20.6 Network debugging from socket to switch (`map/20-06.md`) | 58 | 22 | READ-SECTIONS: intro, 1, 2, 3, 4, 5, 7, 11, 12, How to answer out loud, Scenarios 1, 2, 4 and 6, and drill questions; SKIM sections 6 (conntrack), 8 (MTU), 9 (tcpdump) an |
| 20.7 The console round: text tools, systemd and everyday ope (`map/20-07.md`) | 52 | 20 | MUST-READ-FULL. The chapter is the R1 console round itself, and the 12 tasks are the practice set. Skip only the Sources section after a first pass. |
| 3.1 Python core: types, control flow, functions (`map/03-01.md`) | 26 | 30 | READ-SECTIONS (sections 2, 4, 5, 8 parameters, mutable default, LEGB and generators, 7 for-else and retry loops, 10, 11, 13). The object model, mutability, shallow vs dee |
| 3.2 Modules, packages, virtual environments and packaging (`map/03-02.md`) | 19 | 44 | READ-SECTIONS (section 1 import mechanics and `__name__` guard, circular imports, 3 virtual environments, 4 "Declaring dependencies", 5 wheels and tags, 7 GPU driver and  |
| 3.3 Idiomatic Python: the data model, comprehensions, genera (`map/03-03.md`) | 28 | 32 | READ-SECTIONS (context managers, mappings and sets, text vs bytes, references and copies, comprehensions, the iterator protocol, generator functions, pipelines, EAFP, the |

Practice: Network triage drill aloud (20.6). Start the 20.11 coding problems: 3 today.


## Day 7 - Tue 01 Dec - MUST reading 5.4 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 3.4 Classes, dataclasses, typing and protocols (`map/03-04.md`) | 21 | 57 | READ-SECTIONS. A rusty Senior SRE can skip most of the book-digest prose and the operator-overloading and variance material; read the inheritance/MRO rules, composition,  |
| 3.5 Errors, files, text and bytes, subprocess and system scr (`map/03-05.md`) | 64 | 50 | READ-SECTIONS. This is the chapter a Senior SRE most needs to refresh. Skip the Learning Python prose and the exercises' deep material; read exceptions (mechanics, rules, |
| 3.6 Concurrency: threads, processes and asyncio (`map/03-06.md`) | 40 | 58 | READ-SECTIONS. Read the concepts and GIL, the model-choice table, bounded concurrency, the thread queue and futures patterns, `bounded_map`, the asyncio core concepts (ti |
| 3.8 Building CLIs, agents and exporters (`map/03-08.md`) | 23 | 57 | READ-SECTIONS. A rusty Senior SRE can skip the Click/Typer walkthroughs, the Practical MLOps case study, the packaging comparison details and the book-style asides. Read  |
| 3.9 Testing, quality and CI for Python tooling (`map/03-09.md`) | 20 | 42 | READ-SECTIONS. A rusty Senior SRE can skip the Ansible/Molecule walkthrough, the benchmarking section, the Jinja and golden-file material and the Terraform and Kubernetes |
| 20.8 The coding round: what to expect and how to perform (`map/20-08.md`) | 49 | 11 | READ-SECTIONS (1, 2, 4, 5, 7, 11, 12, the "How to answer out loud" block, Scenario 2, Drill questions). SKIM section 9 table and section 13 for recall. SKIP the Go sectio |
| 20.9 Algorithm patterns for SRE-flavoured problems (`map/20-09.md`) | 57 | 22 | READ-SECTIONS (1, 2, 4, 5, 6, 9, 10, 14, the "How to answer out loud" block, Scenarios 1 and 3, Common mistakes table). SHOULD-skim 7, 8, 11, 12, 13. OPTIONAL-skim 3, 15, |
| 20.10 Complexity, latency numbers and measuring your own cod (`map/20-10.md`) | 48 | 6 | READ-SECTIONS (1, 2, 4, 5, 6, 8, 10, "How to answer out loud", Scenarios A and B, Drill questions). SKIM 3, 7 and 9 for recall. SKIP the Sources and Verification log. Rea |

Practice: Coding: 4 problems from 20.11 under a 30-min timer; write one subprocess/log-parsing script.


## Day 8 - Wed 02 Dec - MUST reading 5.1 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 4.3 Ansible from zero: what it is, how it works, installatio (`map/04-03.md`) | 46 | 29 | READ-SECTIONS (sections 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, the checkpoint answers 1, 4, 5, 9, 10, 11, 12, 17); the Vagrant subsection and the install details can be skimmed |
| 4.4 YAML and Jinja2 for infrastructure code (`map/04-04.md`) | 31 | 39 | READ-SECTIONS (1 "YAML essentials" incl. "Rules that bite", 2 "Jinja2 essentials" incl. "Filters" and "Whitespace control", 3 "Jinja2 in Ansible", 4 "Templating elsewhere |
| 4.5 Ansible inventory: hosts, groups, dynamic inventory and  (`map/04-05.md`) | 26 | 34 | READ-SECTIONS (sections 2 Host patterns, 3 incl. "Variable precedence (summary)", 5 incl. "Source of truth for GPU fleets", 6 Designing inventory for GPU clusters, 7 Debu |
| 4.6 Ansible playbooks: tasks, modules, idempotency and check (`map/04-06.md`) | 37 | 30 | READ-SECTIONS (1 "Playbook anatomy" and "Task anatomy and common keywords", 2 "Idempotency, the heart of playbooks", 4 "command, shell, script, raw: when and how", 5 "Che |
| 4.7 Ansible variables, facts, templates and filters (`map/04-07.md`) | 32 | 39 | READ-SECTIONS (1 "Defining variables" incl. "Where and how", "Naming and types", "Scope and lifetime"; 2 "Registered results and set_fact"; 3 "Facts" incl. "Custom (local |
| 4.8 Ansible handlers, conditionals, loops, blocks and error  (`map/04-08.md`) | 38 | 30 | READ-SECTIONS (1 "Handlers" incl. the "lost handler after failure" trap, 2 "Conditionals: when", 3 "Loops" for `until`/`retries` and the list-vs-loop point only, 4 "Error |
| 4.9 A real playbook end to end: deploying an application (`map/04-09.md`) | 22 | 45 | READ-SECTIONS (1 "Target architecture", 3 "Variables", 5 "The application play: release directories and an atomic switch" incl. its "Four release habits" and the two migr |
| 4.10 Debugging Ansible playbooks (`map/04-10.md`) | 27 | 44 | READ-SECTIONS (1 "A layered method", 2 "Verbosity and output" (table and last paragraph), 3 "The debug and assert modules" (first code block and the `stat` + `assert` par |
| 5.1 Containers from first principles: images, layers, regist (`map/05-01.md`) | 46 | 54 | READ-SECTIONS. Sections 1, 2, 4, 7 and 8 carry most of the interview value and must be read; the rest can be skimmed for recall, because the Linux parts repeat Part 1 and |

Practice: Ansible: write inventory + a playbook that installs and configures a service on a VM/container; run with --check, then for real, then again (idempotent). kind/minikube: create a cluster.


## Day 9 - Thu 03 Dec - MUST reading 5.3 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 5.3 Kubernetes architecture overview: components and what ta (`map/05-03.md`) | 49 | 38 | READ-SECTIONS. Sections 1, 2, 3 (Capacity/Allocatable and Conditions only), 5, 6, 7 and 14 are must-reads for R2 and R3. Section 4 (ports) is a recall table. Sections 8 a |
| 5.5 The API server and etcd: how a request becomes cluster s (`map/05-05.md`) | 53 | 34 | READ-SECTIONS. Must-read: section 1 (groups and verbs, one pass), section 2 (request pipeline and admission outage pattern), section 3 (resourceVersion, 409, 410, LIST se |
| 5.6 Controllers and the reconcile loop: how Kubernetes think (`map/05-06.md`) | 46 | 34 | READ-SECTIONS. Must-read: section 1, section 3 (Deployment chain, DaemonSet, Job, node lifecycle), section 4 (ownerReferences and finalizers only), section 6 (symptom tab |
| 5.7 Pods and workloads: Deployments, StatefulSets, DaemonSet (`map/05-07.md`) | 52 | 69 | READ-SECTIONS. Must read: section 1 (pod), containers and init containers, resources and QoS, lifecycle and termination, workload controller choice and the inference Depl |
| 5.8 The life of a pod end to end, including what the kernel  (`map/05-08.md`) | 32 | 33 | READ-SECTIONS. Must read: Section 1 (timeline diagram), Section 2 (admission and scheduling), the kubelet sync loop, the sandbox steps 1 to 3, the image pull, create and  |
| 5.9 The kubelet and the node: CRI, cgroups, QoS classes, pro (`map/05-09.md`) | 26 | 47 | READ-SECTIONS. Must read: section 1 (what the kubelet does), the allocatable and QoS sections, section 5 (probes, all three subsections), section 6 (node-pressure evictio |
| 5.10 Services, endpoints and kube-proxy: the life of a Servi (`map/05-10.md`) | 34 | 50 | READ-SECTIONS. Must read: section 1 (Service types, DNS, readiness), section 2 (EndpointSlices and propagation delay), section 3 (kube-proxy modes, the iptables packet pa |
| 5.11 DNS and service discovery with CoreDNS (`map/05-11.md`) | 26 | 40 | READ-SECTIONS. Must read: section 1 (records table), section 2 (dnsPolicy, ndots:5 problem), the CoreDNS plugin list (skim the table, read the `loop`, `forward` and `fall |

Practice: K8s: deploy, break a pod (ImagePullBackOff, CrashLoop), fix with kubectl describe/logs. Coding: 4 problems.


## Day 10 - Fri 04 Dec - MUST reading 5.4 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 5.15 NetworkPolicy and the kernel: netfilter, conntrack and  (`map/05-15.md`) | 50 | 48 | READ-SECTIONS (1 full, the kuard default-deny test, 2 trap table, 3 netfilter/conntrack and the Calico and Cilium enforcement subsections, 5 zone design rules, 6 testing  |
| 5.16 Configuration, secrets and RBAC (`map/05-16.md`) | 46 | 66 | READ-SECTIONS (ConfigMap update behaviour and immutable; Secrets: the five protection layers and the verbs; Secret consumption choices; the GitOps-safe table; projected v |
| 5.18 Scheduling in depth: kube-scheduler, affinity, taints,  (`map/05-18.md`) | 48 | 44 | READ-SECTIONS (1 scheduling cycle and Filter/Score, 2 resource accounting and fragmentation, 3 all placement rules, 4 priority, preemption and PDBs, 5 the gang problem an |
| 5.23 Autoscaling: HPA, VPA, KEDA and the cluster autoscaler (`map/05-23.md`) | 29 | 45 | READ-SECTIONS (1 layers and the spike walkthrough; 2 algorithm, behaviour tuning, inference scaling signals, metric debugging; 5 CA scale-up/down and blockers, overprovis |
| 5.25 Troubleshooting Kubernetes from the node: crictl, nsent (`map/05-25.md`) | 28 | 39 | MUST-READ-FULL. This is the chapter that matches the R1 "practical Linux console and troubleshooting" task most closely, and the R2 troubleshooting round. Read sections 1 |
| 20.23 Kubernetes failure drills for GPU platforms (`map/20-23.md`) | 27 | 26 | READ-SECTIONS. Read sections 1, 2, 3, the "How to answer out loud" block, Drills 1, 3, 4, 6, 8 and the drill questions in full; skim Drills 2, 5, 9, 10, 11 and 12 (read e |
| 20.24 Terraform for resilient GPU clusters (`map/20-24.md`) | 26 | 34 | READ-SECTIONS. Read sections 1 (module inputs and prevent_destroy only), 2, 4, 5 (the strategy and capacity table), 8 (the test layers), 9, 10, the "How to answer out lou |
| 6.1 What a supercomputer is: TOP500, Linpack, HPC versus AI  (`map/06-01.md`) | 18 | 30 | READ-SECTIONS (4, 5 HA/HTC/HPC subsection, 6 invariants and fleet-CLI subsection, 7 stack) plus SKIM-FOR-RECALL for 1-3 and 8; SKIP the history and facility material. Rea |
| 6.7 Slurm architecture and installation (`map/06-07.md`) | 38 | 43 | READ-SECTIONS (1 workload manager ideas, 2 daemons, 3 life of a job, 5 state and HA, 6 munge, 8 upgrade order, 9 account tree intro, 11 install order and verification, 12 |
| 6.10 Slurm GPU scheduling: GRES, NVML autodetect, MIG and de (`map/06-10.md`) | 13 | 23 | READ-SECTIONS (1 GRES and AutoDetect, 2 request options and what the job sees, 4 isolation, 5 MIG-and-choosing table, 6 GPU accounting, 7 operational drain rules and live |

Practice: K8s: DNS from inside a pod, a Service with no endpoints, a Pending pod (5.25 playbooks). Slurm: read-only today, write the sbatch/srun/squeue/scancel cheat sheet.


## Day 11 - Sat 05 Dec - MUST reading 5.1 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 6.11 Submitting and launching jobs: sbatch, srun, salloc, ar (`map/06-11.md`) | 37 | 22 | READ-SECTIONS (1 allocations, batch and steps; 2 batch script anatomy and env vars and rendezvous; 3 srun with overlap and kill-on-bad-exit; 5 arrays with throttle; 6 dep |
| 6.12 Multi-node training on Slurm: PMIx, torchrun, NCCL envi (`map/06-12.md`) | 22 | 29 | READ-SECTIONS (1 layers, 2 two launch styles, 3 glue, 4 rendezvous gotchas, 5 NCCL minimum variables and baseline, 7 DeepSpeed 127.0.0.1 trap and checkpointing, 8 failure |
| 20.12 Estimation toolkit for inference capacity (`map/20-12.md`) | 61 | 7 | READ-SECTIONS (intro; 1 estimation chain; 3 KV per request; 4 concurrency per GPU; 5 prefill vs decode only the practical formulas; 6 batching table; 8 GPUs for QPS with  |
| 20.13 Design: a multi-tenant LLM inference API (`map/20-13.md`) | 69 | 15 | MUST-READ-FULL. This is the core R3 chapter, and the reader needs the framework (numbers first, then contract, then planes, then failure) more than any single fact. The P |
| 20.14 Design: dedicated endpoints and safe model rollout (`map/20-14.md`) | 50 | 12 | READ-SECTIONS (0, 1, 2, 3, 5, 6, 7, 8, 9, "How to answer out loud", Scenarios A and B). These are the rollout and probe reasoning an SRE will be pushed on. Sections 4, 10 |
| 20.15 Design: an observability pipeline for very high volume (`map/20-15.md`) | 68 | 20 | READ-SECTIONS (0, 1, 2, 3, 4, 5, 6, 7, 9, 10 intro and table, 12, 13, 14, "How to answer out loud", Question 1 to Question 5, Scenarios 1 and 3). Cardinality, metrics ver |

Practice: Slurm: write one sbatch script (GPU request, array, dependency) and explain each line. First system-design drill: pick one prompt in 20.17, 35 min timed, speak aloud.


## Day 12 - Sun 06 Dec - MUST reading 5.4 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 20.16 Design: GPU fleet health and capacity (`map/20-16.md`) | 51 | 21 | READ-SECTIONS (1, 3, 6, 7, 8, 9, 10, "How to answer out loud", Scenarios A and C). These carry the reasoning interviewers push on: why automation needs limits, why spares |
| 20.17 System design drill sheet: twelve prompts (`map/20-17.md`) | 28 | 35 | READ-SECTIONS (0 "How to use the twelve prompts", 2 model inference serving, 4 detecting a failing GPU, 5 SRE variant, "The first five minutes script", "The one-page deci |
| 20.18 How LLM serving fails (`map/20-18.md`) | 67 | 8 | MUST-READ-FULL. This is the incident-round chapter and the reader has no incident experience, so the method (name the full place, protect users, then root cause) matters  |
| 20.19 SLIs, SLOs and alerts for token APIs (`map/20-19.md`) | 42 | 28 | READ-SECTIONS. Read sections 1, 2, 3, 5, 6, 7, 11, the "How to answer out loud" block and Scenarios 1, 2 and 4 in full; read the availability burn YAML and the calculator |
| 20.20 Autoscaling GPU inference (`map/20-20.md`) | 40 | 31 | READ-SECTIONS. Read sections 1, 2, 3, 4, 5, 7, the "How to answer out loud" block, Scenario C and the drills in full; read sections 6, 8 and 9 and Scenarios A, B and D on |
| 20.21 Request routing, retries and overload control (`map/20-21.md`) | 38 | 34 | READ-SECTIONS. Read sections 1, 2, 3, 4, 5, 7, 8, 11, the "How to answer out loud" block, Scenarios A, B and C, and the drills in full; read sections 6, 9, 10 and 12 once |
| 20.22 Operating vLLM, Triton, Ray and TensorRT-LLM (`map/20-22.md`) | 26 | 29 | READ-SECTIONS. Read sections 1, 3, 7, 8, 10, the "How to answer out loud" block, Scenario B and the drills in full; read sections 2, 4, 5, 6, 9 and 11 once each and Scena |
| 20.25 PromQL, Grafana and tracing: the traps interviewers te (`map/20-25.md`) | 29 | 27 | READ-SECTIONS. The query traps (counters, rate, histograms, absent, for) are the likely screen-share question. The YAML, Alertmanager routing and the verification log are |

Practice: Second and third design drills; incident drill #1 (disk-full-node, ch26 script). Coding: 4 problems.


## Day 13 - Mon 07 Dec - MUST reading 2.2 h

| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |
|---|---|---|---|
| 20.26 The stress interview: production incident role-play (`map/20-26.md`) | 59 | 27 | MUST-READ-FULL. This is the chapter the reader most needs to rehearse, and the method (sections 1-5) and the ten incidents are the material. Skip the Python code in secti |
| 20.27 Post-mortems, on-call and incident leadership (`map/20-27.md`) | 30 | 24 | READ-SECTIONS. Read core ideas 1, 2, 4 and 5 and the eight "How to answer out loud" prompts in full, because they are what R4 asks. Skim 3, 8 and 9 for numbers only, and  |
| 20.28 The project deep dive and the final round (`map/20-28.md`) | 42 | 10 | MUST-READ-FULL. Nebius officially confirms only a one-hour final meeting with a team leader; the 90-minute project deep dive is one unverified secondary source. Section 3 |

Practice: Incident drills #2 and #3 (dns-intermittent-failures, bad-config-push). Fill the project dossier (20.28). Then one full mock of each round type (see below).


## Day 13 mocks (after the reading above)
Spoken aloud with a timer: (1) 45-min Linux console triage using 20.3 + the 20.26 drill, (2) 30-min coding (2 problems), (3) 45-min system design from a fresh 20.17 prompt, (4) 20-min project walk-through (20.28).

## Day 14 - Tue 8 Dec: light day, no new material
1 h flashcards, one short incident drill, re-read your own notes and the one-page cheat sheet, check setup (Zoom, camera, quiet room; no AI tools allowed). Sleep early.

## If you fall behind
Drop in this order: 5.23, 3.9, 3.8, 2.20, 4.10, 6.12, 20.22, 20.25. Never drop: 20.3, 20.6, 20.7, 20.13, 20.18, 20.26, 20.28 and the Linux/network terminal practice.

## Not in the core plan (still mapped, read only if ahead)
Best first picks: 17.6, 17.7 (SLOs, failure modes), 4.18, 4.19 (Terraform basics, state), 5.12 (ingress), 6.2 (cluster anatomy), 6.8 and 6.9 (Slurm config, accounting), 20.36 (Soperator). Also: 1.7, 1.10, 1.13, 1.14, 1.20-1.22, 1.24-1.30; 2.9, 2.11-2.12, 2.21, 2.23-2.24, 2.31-2.32; 3.7; 5.2, 5.4, 5.13-5.14, 5.17, 5.19-5.22, 5.24; 17.1-17.3; 4.1, 4.2; 10.21; 11.2. Vol 20 ch30-38 (Nebius architecture) are not mapped yet.
