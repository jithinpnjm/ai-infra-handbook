# Prelims plan: Fri 27 Nov to Wed 9 Dec morning

Format: 90 min. First 60 min experience + general Linux/networking/DevOps questions; last 30 min one LeetCode-style problem.

| Every day | Min | What |
|---|---|---|
| Recall | 10 | Aloud, no notes: 2 cards each from yesterday, 3 days ago, 7 days ago |
| Speak + cards | 10 | Explain the day's 3 biggest ideas; write 6 flashcards |

## How Kubernetes runs on a Linux node (memorize this chain)

| Step | What happens | Linux primitive underneath |
|---|---|---|
| 1 | `kubectl` reads kubeconfig, calls the API server over HTTPS | TCP + TLS, client cert or token |
| 2 | API server authenticates, authorizes (RBAC), admits, stores in etcd | HTTP, etcd (Raft) |
| 3 | Scheduler picks a node; kubelet on that node sees the Pod | watch on the API server |
| 4 | kubelet asks containerd (CRI) to create the sandbox and containers | gRPC over a unix socket |
| 5 | containerd + runc start the container process | `clone` with new namespaces (pid, net, mnt, uts, ipc), `pivot_root` |
| 6 | image layers become the container root filesystem | OverlayFS mount |
| 7 | CPU/memory limits are enforced | cgroup v2 (`cpu.max`, `memory.max`); over memory limit = OOM kill |
| 8 | CNI plugin gives the pod an IP | veth pair, bridge or routes, optional VXLAN/BGP |
| 9 | Service virtual IP reaches pods | kube-proxy iptables or IPVS NAT rules + conntrack |
| 10 | Volumes appear in the pod | CSI plugin + `mount` (bind mounts) |
| 11 | GPUs appear in the pod | device plugin + NVIDIA container toolkit (device files, driver libs) |
| 12 | Probes and eviction | kubelet loop; liveness restarts, memory pressure evicts |

Links go to the exact section to read, not the whole chapter. Everything else in a chapter is optional.

## Day 1, Fri 27 Nov

| Block | Read these sections | Hands-on |
|---|---|---|
| Linux (30) | [1.1 2. The three layers](./part-01-linux/01-the-linux-big-picture-kernel-userspace-distributions.md#2-the-three-layers)<br />[1.1 3. What the kernel does: four jobs](./part-01-linux/01-the-linux-big-picture-kernel-userspace-distributions.md#3-what-the-kernel-does-four-jobs)<br />[1.2 6. Standard streams, redirection and pipes](./part-01-linux/02-the-command-line-shells-commands-pipes-and-redirection.md#6-standard-streams-redirection-and-pipes)<br />[1.2 7. Exit status and combining commands](./part-01-linux/02-the-command-line-shells-commands-pipes-and-redirection.md#7-exit-status-and-combining-commands) | Pipes, redirection, `man` |
| Networking (25) | [2.1 1. The whole journey in one picture](./part-02-networking/01-what-happens-when-you-curl-a-url-a-packet-s-journey-end-to-end.md#1-the-whole-journey-in-one-picture)<br />[2.1 3. Step 1: name resolution (what is the IP address?)](./part-02-networking/01-what-happens-when-you-curl-a-url-a-packet-s-journey-end-to-end.md#3-step-1-name-resolution-what-is-the-ip-address)<br />[2.1 7. Step 5: TCP connection establishment](./part-02-networking/01-what-happens-when-you-curl-a-url-a-packet-s-journey-end-to-end.md#7-step-5-tcp-connection-establishment)<br />[2.1 8. Step 6: TLS handshake (HTTPS)](./part-02-networking/01-what-happens-when-you-curl-a-url-a-packet-s-journey-end-to-end.md#8-step-6-tls-handshake-https) | `curl -v` |
| Platform: Kubernetes (30) | [5.1 1. What a container is](./part-05-kubernetes/01-containers-from-first-principles-images-layers-registries.md#1-what-a-container-is)<br />[5.1 2. Images: layers, content addressing and the OCI formats](./part-05-kubernetes/01-containers-from-first-principles-images-layers-registries.md#2-images-layers-content-addressing-and-the-oci-formats)<br />[5.2 1. The stack](./part-05-kubernetes/02-container-runtimes-containerd-runc-cri-and-oci.md#1-the-stack)<br />[5.2 2. containerd in depth](./part-05-kubernetes/02-container-runtimes-containerd-runc-cri-and-oci.md#2-containerd-in-depth) | Run a container, `docker ps`, `docker exec`; on a kind node `crictl ps` |
| Coding (30) | Reverse string, palindrome, FizzBuzz | Timed 25 min |
| Python (30) | Refresh:<br />[3.1 4. Strings and bytes](./part-03-python/01-python-core-types-control-flow-functions.md#4-strings-and-bytes)<br />[3.1 5. Core collections](./part-03-python/01-python-core-types-control-flow-functions.md#5-core-collections) | Program: word count, top 5 words in a file |
| Shell (15) | `wc`, `sort`, `uniq` | `sort \| uniq -c \| sort -rn \| head` |
| Setup | Ubuntu VM or container; strace, lsof, tcpdump, dnsutils, iproute2, kind | Folders `py/` and `sh/` |

## Day 2, Sat 28 Nov

| Block | Read these sections | Hands-on |
|---|---|---|
| Linux (30) | [1.6 3. File permissions: read, write, execute](./part-01-linux/06-users-groups-permissions-acls-sudo-and-user-environments.md#3-file-permissions-read-write-execute)<br />[1.6 Changing permissions: chmod, chown, chgrp](./part-01-linux/06-users-groups-permissions-acls-sudo-and-user-environments.md#changing-permissions-chmod-chown-chgrp)<br />[1.3 4. Inodes: what a file really is](./part-01-linux/03-files-and-the-directory-hierarchy-paths-links-inodes.md#4-inodes-what-a-file-really-is)<br />[1.3 5. Links: hard and symbolic](./part-01-linux/03-files-and-the-directory-hierarchy-paths-links-inodes.md#5-links-hard-and-symbolic) | chmod, chown, umask, `df -i` |
| Networking (25) | [2.2 3. Layered models](./part-02-networking/02-how-networks-work-layers-encapsulation-the-tcp-ip-model.md#3-layered-models)<br />[2.2 4. Encapsulation and decapsulation](./part-02-networking/02-how-networks-work-layers-encapsulation-the-tcp-ip-model.md#4-encapsulation-and-decapsulation)<br />[2.4 2. IPv4 addresses and masks](./part-02-networking/04-ip-addressing-subnetting-and-cidr-ipv4-and-ipv6-with-practice.md#2-ipv4-addresses-and-masks)<br />[2.4 Fast subnetting: the block-size method](./part-02-networking/04-ip-addressing-subnetting-and-cidr-ipv4-and-ipv6-with-practice.md#fast-subnetting-the-block-size-method) | 5 subnet sums by hand |
| Platform: Kubernetes (30) | [5.3 1. The big picture](./part-05-kubernetes/03-kubernetes-architecture-overview-components-and-what-talks-to-what.md#1-the-big-picture)<br />[5.3 2. Control plane components](./part-05-kubernetes/03-kubernetes-architecture-overview-components-and-what-talks-to-what.md#2-control-plane-components)<br />[5.3 3. Node components](./part-05-kubernetes/03-kubernetes-architecture-overview-components-and-what-talks-to-what.md#3-node-components) | Create a kind cluster; draw control plane vs node and say what each component does |
| Coding (30) | Run-length encode `AABBBCCCCCDEFF` to `A2B3C5D1E1F2`; decode; character frequency | Timed |
| Python (30) | Refresh:<br />[3.3 7. Comprehensions](./part-03-python/03-idiomatic-python-the-data-model-comprehensions-generators.md#7-comprehensions)<br />[3.3 3. Mappings and sets](./part-03-python/03-idiomatic-python-the-data-model-comprehensions-generators.md#3-mappings-and-sets) | Program: top 10 IPs and status codes from a log |
| Shell (15) | `awk`, `sort`, `uniq` | Same top-IPs job in one pipeline |

## Day 3, Sun 29 Nov

| Block | Read these sections | Hands-on |
|---|---|---|
| Linux (30) | [1.8 2. What a process is](./part-01-linux/08-processes-signals-and-job-control.md#2-what-a-process-is)<br />[1.8 Zombies and orphans](./part-01-linux/08-processes-signals-and-job-control.md#zombies-and-orphans)<br />[1.8 4. Signals](./part-01-linux/08-processes-signals-and-job-control.md#4-signals)<br />[1.8 5. Shell job control](./part-01-linux/08-processes-signals-and-job-control.md#5-shell-job-control) | `ps`, `top`, `kill`, zombie demo |
| Networking (25) | [2.5 1. The routing decision](./part-02-networking/05-routing-on-a-host-routing-tables-default-gateways-and-forwarding.md#1-the-routing-decision)<br />[2.5 2. Reading the routing table](./part-02-networking/05-routing-on-a-host-routing-tables-default-gateways-and-forwarding.md#2-reading-the-routing-table) | `ip route get`; 5 new subnet sums |
| Platform: Kubernetes (30) | [5.5 2. The request pipeline](./part-05-kubernetes/05-the-api-server-and-etcd-how-a-request-becomes-cluster-state.md#2-the-request-pipeline)<br />[5.3 6. From kubectl apply to a running container](./part-05-kubernetes/03-kubernetes-architecture-overview-components-and-what-talks-to-what.md#6-from-kubectl-apply-to-a-running-container)<br />[5.6 1. The controller pattern](./part-05-kubernetes/06-controllers-and-the-reconcile-loop-how-kubernetes-thinks.md#1-the-controller-pattern)<br />[5.6 2. The machinery: informers and work queues](./part-05-kubernetes/06-controllers-and-the-reconcile-loop-how-kubernetes-thinks.md#2-the-machinery-informers-and-work-queues)<br />[kubeconfig docs (kubernetes.io)](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) (kubeconfig: cluster URL+CA, user, context) | `kubectl config view`, `kubectl get pods -v=8` |
| Coding (30) | Valid anagram, first non-repeating char, remove duplicates | Timed |
| Python (30) | Refresh:<br />[3.1 8. Functions](./part-03-python/01-python-core-types-control-flow-functions.md#8-functions)<br />[3.1 2. Objects, names and references](./part-03-python/01-python-core-types-control-flow-functions.md#2-objects-names-and-references) | Program: `argparse` CLI, 10 largest files in a directory |
| Shell (15) | `find -size +10M` | `du -xh --max-depth=1 \| sort -h` |

## Day 4, Mon 30 Nov

| Block | Read these sections | Hands-on |
|---|---|---|
| Linux (30) | [1.17 5. The OOM killer](./part-01-linux/17-memory-management-virtual-memory-numa-huge-pages-oom.md#5-the-oom-killer)<br />[1.17 The summary view: free and /proc/meminfo](./part-01-linux/17-memory-management-virtual-memory-numa-huge-pages-oom.md#the-summary-view-free-and-procmeminfo)<br />[1.4 3. grep: filter lines](./part-01-linux/04-text-processing-essentials-grep-sed-awk-find-xargs-sort.md#3-grep-filter-lines)<br />[1.4 6. awk: the Swiss army knife for columns](./part-01-linux/04-text-processing-essentials-grep-sed-awk-find-xargs-sort.md#6-awk-the-swiss-army-knife-for-columns) | `free -m`, `vmstat 1`, `dmesg -T \| tail` |
| Networking (25) | [2.6 4. The handshake, data transfer and teardown](./part-02-networking/06-tcp-in-depth-handshake-windows-congestion-control-retransmission.md#4-the-handshake-data-transfer-and-teardown)<br />[2.6 5. Reliability: ACKs, retransmission and the RTO](./part-02-networking/06-tcp-in-depth-handshake-windows-congestion-control-retransmission.md#5-reliability-acks-retransmission-and-the-rto) | `ss -tan`, `ss -ltnp` |
| Platform: Kubernetes (30) | [5.7 3. Workload controllers: choosing](./part-05-kubernetes/07-pods-and-workloads-deployments-statefulsets-daemonsets-and-jobs.md#3-workload-controllers-choosing)<br />[5.8 1. Timeline overview](./part-05-kubernetes/08-the-life-of-a-pod-end-to-end-including-what-the-kernel-does.md#1-timeline-overview)<br />[5.8 3. The kubelet takes over](./part-05-kubernetes/08-the-life-of-a-pod-end-to-end-including-what-the-kernel-does.md#3-the-kubelet-takes-over) | Kind: deploy, scale, delete a pod |
| Coding (30) | Two-sum, contains-duplicate, majority element | Timed |
| Python (30) | Refresh:<br />[3.5 1. Exceptions](./part-03-python/05-errors-files-text-and-bytes-subprocess-and-system-scripting.md#1-exceptions)<br />[3.5 3. Files and paths](./part-03-python/05-errors-files-text-and-bytes-subprocess-and-system-scripting.md#3-files-and-paths) | Program: parse a log, skip bad lines, count failures |
| Shell (15) | `pgrep -f`, `nohup`, `jobs` | `nohup cmd &`, `kill %1` |

## Day 5, Tue 1 Dec

| Block | Read these sections | Hands-on |
|---|---|---|
| Linux (30) | [1.12 Capacity: df, du, inodes, reserved blocks](./part-01-linux/12-disks-partitions-and-filesystems.md#capacity-df-du-inodes-reserved-blocks)<br />[1.11 4. System calls](./part-01-linux/11-how-a-program-runs-system-calls-libraries-elf-strace-and-ldd.md#4-system-calls)<br />[1.11 6. Watching a program: strace and ltrace in practice](./part-01-linux/11-how-a-program-runs-system-calls-libraries-elf-strace-and-ldd.md#6-watching-a-program-strace-and-ltrace-in-practice) | `df -h` vs `df -i`, `strace -f -e trace=file ls` |
| Networking (25) | [2.7 3. ping](./part-02-networking/07-udp-icmp-and-the-diagnostic-tools-ping-traceroute-mtr.md#3-ping)<br />[2.7 4. traceroute, tracepath and mtr](./part-02-networking/07-udp-icmp-and-the-diagnostic-tools-ping-traceroute-mtr.md#4-traceroute-tracepath-and-mtr)<br />[2.8 2. How a lookup actually works](./part-02-networking/08-dns-in-depth-resolution-records-resolvers-and-caching.md#2-how-a-lookup-actually-works)<br />[2.8 4. Tools: dig and friends](./part-02-networking/08-dns-in-depth-resolution-records-resolvers-and-caching.md#4-tools-dig-and-friends) | `dig +trace`, `/etc/resolv.conf` |
| Platform: Kubernetes (30) | [5.9 1. What the kubelet does](./part-05-kubernetes/09-the-kubelet-and-the-node-cri-cgroups-qos-classes-probes-and-eviction.md#1-what-the-kubelet-does)<br />[5.9 5. Probes](./part-05-kubernetes/09-the-kubelet-and-the-node-cri-cgroups-qos-classes-probes-and-eviction.md#5-probes)<br />[5.9 6. Node-pressure eviction](./part-05-kubernetes/09-the-kubelet-and-the-node-cri-cgroups-qos-classes-probes-and-eviction.md#6-node-pressure-eviction)<br />[5.2 7. Cgroup drivers and cgroup v2](./part-05-kubernetes/02-container-runtimes-containerd-runc-cri-and-oci.md#7-cgroup-drivers-and-cgroup-v2) | Break a pod with a bad probe and a low memory limit; find its cgroup under `/sys/fs/cgroup` |
| Coding (30) | Valid parentheses, merge two sorted lists, binary search | Timed |
| Python (30) | Refresh:<br />[3.5 6. Running external programs: subprocess](./part-03-python/05-errors-files-text-and-bytes-subprocess-and-system-scripting.md#6-running-external-programs-subprocess) | Program: run `df -h`, exit non-zero if a filesystem is over 80% |
| Shell (15) | `for` loop, `ping -c1` | Ping 3 hosts, print up/down |

## Day 6, Wed 2 Dec

| Block | Read these sections | Hands-on |
|---|---|---|
| Linux (30) | [1.15 3. Operating systemd: systemctl](./part-01-linux/15-systemd-units-targets-timers-journald.md#3-operating-systemd-systemctl)<br />[1.15 12. Journald and journalctl](./part-01-linux/15-systemd-units-targets-timers-journald.md#12-journald-and-journalctl) | Crashing unit: `systemctl status`, `journalctl -u -e` |
| Networking (25) | [2.10 1. HTTP in practice](./part-02-networking/10-http-tls-and-pki-basics.md#1-http-in-practice)<br />[2.10 The handshake (TLS 1.3)](./part-02-networking/10-http-tls-and-pki-basics.md#the-handshake-tls-13)<br />[2.10 6. Troubleshooting TLS and HTTP](./part-02-networking/10-http-tls-and-pki-basics.md#6-troubleshooting-tls-and-http) | `openssl s_client -connect host:443` |
| Platform: Kubernetes (30) | [5.10 3. kube-proxy](./part-05-kubernetes/10-services-endpoints-and-kube-proxy-the-life-of-a-service.md#3-kube-proxy)<br />[5.10 7. Debugging Services](./part-05-kubernetes/10-services-endpoints-and-kube-proxy-the-life-of-a-service.md#7-debugging-services)<br />[5.11 2. Resolver behaviour inside pods](./part-05-kubernetes/11-dns-and-service-discovery-with-coredns.md#2-resolver-behaviour-inside-pods)<br />[5.11 7. Debugging method](./part-05-kubernetes/11-dns-and-service-discovery-with-coredns.md#7-debugging-method) | Kind: Service with wrong selector, find why no endpoints |
| Coding (30) | Isomorphic strings, group anagrams, top-K frequent | Timed |
| Python (30) | Refresh:<br />[3.3 2. Sequences](./part-03-python/03-idiomatic-python-the-data-model-comprehensions-generators.md#2-sequences)<br />[3.3 3. Mappings and sets](./part-03-python/03-idiomatic-python-the-data-model-comprehensions-generators.md#3-mappings-and-sets)<br />(`deque`, `heapq` in the stdlib docs) | Program: top-K slowest requests from a log |
| Shell (15) | `awk` sums, `cut` | `awk '{s+=$NF} END {print s}'`, `cut -d, -f2` |

## Day 7, Thu 3 Dec (review day: recall 25 min on Days 1-6)

| Block | Read these sections | Hands-on |
|---|---|---|
| Linux (30) | [20.3 3. The first 60 seconds, command by command](./part-20-nebius-sre-interview/03-triage-method-for-a-sick-linux-box.md#3-the-first-60-seconds-command-by-command)<br />[20.3 4. Reading load, run queue and pressure correctly](./part-20-nebius-sre-interview/03-triage-method-for-a-sick-linux-box.md#4-reading-load-run-queue-and-pressure-correctly)<br />[20.3 6. The USE method as a sweep](./part-20-nebius-sre-interview/03-triage-method-for-a-sick-linux-box.md#6-the-use-method-as-a-sweep) | Run the 60-second checklist from memory on your VM |
| Networking (25) | [2.22 2. The ip command family](./part-02-networking/22-linux-networking-inspecting-state-with-ip-ss-and-counters.md#2-the-ip-command-family)<br />[2.22 5. Counters: where packets disappear](./part-02-networking/22-linux-networking-inspecting-state-with-ip-ss-and-counters.md#5-counters-where-packets-disappear)<br />[2.26 2. tcpdump](./part-02-networking/26-packet-capture-from-scratch-tcpdump-tshark-and-wireshark.md#2-tcpdump) | Capture a handshake and a DNS query |
| Platform: Kubernetes (30) | [5.13 1. The Kubernetes network model](./part-05-kubernetes/13-pod-networking-under-the-hood-veth-bridges-routes-and-cni-plugins.md#1-the-kubernetes-network-model)<br />[5.13 2. Building pod networking by hand](./part-05-kubernetes/13-pod-networking-under-the-hood-veth-bridges-routes-and-cni-plugins.md#2-building-pod-networking-by-hand)<br />[5.13 7. Inspecting pod networking on a node](./part-05-kubernetes/13-pod-networking-under-the-hood-veth-bridges-routes-and-cni-plugins.md#7-inspecting-pod-networking-on-a-node) | Kind: `kubectl exec` into a pod, `ip a`; on the kind node find its veth (`docker exec <node> ip a`) and `iptables-save \| grep <svc>` |
| Coding (30) | Longest substring without repeating characters, max subarray | Timed |
| Python (30) | Refresh:<br />[3.5 5. Data formats](./part-03-python/05-errors-files-text-and-bytes-subprocess-and-system-scripting.md#5-data-formats) | Program: count errors per service from JSON lines |
| Shell (15) | `sed -i`, `grep -rn`, `tar` | `tar czf` and `tar xzf` |

## Day 8, Fri 4 Dec

| Block | Read these sections | Hands-on |
|---|---|---|
| Linux (30) | [20.4 4. strace: how to read what it prints](./part-20-nebius-sre-interview/04-files-descriptors-syscalls-and-permissions.md#4-strace-how-to-read-what-it-prints)<br />[20.4 5. Blocks, inodes, and files that are deleted but still...](./part-20-nebius-sre-interview/04-files-descriptors-syscalls-and-permissions.md#5-blocks-inodes-and-files-that-are-deleted-but-still-open)<br />[20.4 6. Permission checks beyond the mode bits](./part-20-nebius-sre-interview/04-files-descriptors-syscalls-and-permissions.md#6-permission-checks-beyond-the-mode-bits)<br />[1.19 2. The namespace types](./part-01-linux/19-namespaces-the-kernel-feature-behind-containers.md#2-the-namespace-types)<br />[1.18 5. Control groups: the idea](./part-01-linux/18-cpu-scheduling-and-cgroups-v1-and-v2.md#5-control-groups-the-idea)<br />[1.18 7. The CPU controller: weight, quota and throttling](./part-01-linux/18-cpu-scheduling-and-cgroups-v1-and-v2.md#7-the-cpu-controller-weight-quota-and-throttling) | `lsof -p`, `/proc/<pid>/limits` |
| Networking (25) | [20.6 1. Refused, timed out, reset: three different stories](./part-20-nebius-sre-interview/06-network-debugging-from-socket-to-switch.md#1-refused-timed-out-reset-three-different-stories)<br />[20.6 3. Reading ss: states and the two numbers](./part-20-nebius-sre-interview/06-network-debugging-from-socket-to-switch.md#3-reading-ss-states-and-the-two-numbers)<br />[20.6 4. SYN backlog and accept queue](./part-20-nebius-sre-interview/06-network-debugging-from-socket-to-switch.md#4-syn-backlog-and-accept-queue)<br />[20.6 5. TIME_WAIT and ephemeral ports](./part-20-nebius-sre-interview/06-network-debugging-from-socket-to-switch.md#5-time_wait-and-ephemeral-ports) | MTU test `ping -M do -s 1472` |
| Platform: Kubernetes under the hood (30) | [5.26 1. The master map](./part-05-kubernetes/26-how-kubernetes-uses-the-linux-kernel-a-complete-map.md#1-the-master-map)<br />[5.26 3. cgroups v2 in depth](./part-05-kubernetes/26-how-kubernetes-uses-the-linux-kernel-a-complete-map.md#3-cgroups-v2-in-depth)<br />[5.26 6. Networking in the kernel](./part-05-kubernetes/26-how-kubernetes-uses-the-linux-kernel-a-complete-map.md#6-networking-in-the-kernel) | On a kind node: `crictl ps`, `lsns`, `nsenter -t <pid> -n ip a`; build a container by hand: [1.20 Step 3. Namespaces with unshare](./part-01-linux/20-lab-build-a-container-by-hand-with-unshare-chroot-cgroups-and-overlayf.md#step-3-namespaces-with-unshare) |
| Coding (30) | Merge intervals, meeting rooms, insert interval | Timed |
| Python (30) | Refresh:<br />[3.5 7. Interacting with the operating system](./part-03-python/05-errors-files-text-and-bytes-subprocess-and-system-scripting.md#7-interacting-with-the-operating-system)<br />(`ipaddress`, `socket` in the stdlib docs) | Program: CIDR tool (network, broadcast, host count, contains) |
| Shell (15) | `xargs -P 4`, `curl -w` | `curl -s -o /dev/null -w "%{http_code}"` over a URL list |

## Day 9, Sat 5 Dec

| Block | Read these sections | Hands-on |
|---|---|---|
| Linux (30) | [20.5 1. Load average, utilisation and saturation](./part-20-nebius-sre-interview/05-cpu-memory-disk-and-the-scheduler.md#1-load-average-utilisation-and-saturation)<br />[20.5 3. CPU throttling from cgroup limits in containers](./part-20-nebius-sre-interview/05-cpu-memory-disk-and-the-scheduler.md#3-cpu-throttling-from-cgroup-limits-in-containers)<br />[20.5 7. The OOM killer and how to read its log](./part-20-nebius-sre-interview/05-cpu-memory-disk-and-the-scheduler.md#7-the-oom-killer-and-how-to-read-its-log)<br />[20.7 1. Build every pipeline in four moves](./part-20-nebius-sre-interview/07-the-console-round-text-tools-systemd-and-everyday-operations.md#1-build-every-pipeline-in-four-moves)<br />[20.7 5. Reading journald and systemd units](./part-20-nebius-sre-interview/07-the-console-round-text-tools-systemd-and-everyday-operations.md#5-reading-journald-and-systemd-units) | Do the pipelines in your VM |
| Networking (25) | [2.20 2. Algorithms](./part-02-networking/20-load-balancing-l4-l7-ecmp-hashing-and-proxies.md#2-algorithms)<br />[2.20 3. Health checks, failure handling and draining](./part-02-networking/20-load-balancing-l4-l7-ecmp-hashing-and-proxies.md#3-health-checks-failure-handling-and-draining)<br />[2.20 4. ECMP, anycast and scaling out the L4 tier](./part-02-networking/20-load-balancing-l4-l7-ecmp-hashing-and-proxies.md#4-ecmp-anycast-and-scaling-out-the-l4-tier) | Nginx reverse proxy with 2 backends |
| Platform: Kubernetes troubleshooting (30) | [5.25 1. Method](./part-05-kubernetes/25-troubleshooting-kubernetes-from-the-node-crictl-nsenter-tcpdump-and-ip.md#1-method)<br />[5.25 3. Node-level toolkit](./part-05-kubernetes/25-troubleshooting-kubernetes-from-the-node-crictl-nsenter-tcpdump-and-ip.md#3-node-level-toolkit)<br />[5.25 4. Failure playbooks](./part-05-kubernetes/25-troubleshooting-kubernetes-from-the-node-crictl-nsenter-tcpdump-and-ip.md#4-failure-playbooks)<br />[5.18 1. The scheduler's job and model](./part-05-kubernetes/18-scheduling-in-depth-kube-scheduler-affinity-taints-priority-and-preemp.md#1-the-schedulers-job-and-model)<br />[5.18 3. Placement constraints](./part-05-kubernetes/18-scheduling-in-depth-kube-scheduler-affinity-taints-priority-and-preemp.md#3-placement-constraints)<br />[5.18 8. Debugging scheduling](./part-05-kubernetes/18-scheduling-in-depth-kube-scheduler-affinity-taints-priority-and-preemp.md#8-debugging-scheduling) | Break 5 pods (Pending, CrashLoop, ImagePullBackOff, OOMKilled, bad probe) and diagnose each |
| Coding (30) | O(1) insert/delete/get-random set, LRU cache | Timed |
| Python (30) | Refresh:<br />[3.4 1. Classes and objects](./part-03-python/04-classes-dataclasses-typing-and-protocols.md#1-classes-and-objects)<br />[3.4 3. Data class builders](./part-03-python/04-classes-dataclasses-typing-and-protocols.md#3-data-class-builders) | Program: nodes and pods, find pods that fit no node |
| Shell (15) | Script basics | Args, `set -euo pipefail`, a function, `trap` cleanup |

## Day 10, Sun 6 Dec

| Block | Read these sections | Hands-on |
|---|---|---|
| Linux (30) | [20.7 6. Processes, signals, zombies and PID 1](./part-20-nebius-sre-interview/07-the-console-round-text-tools-systemd-and-everyday-operations.md#6-processes-signals-zombies-and-pid-1)<br />[20.7 7. cron and logrotate gotchas](./part-20-nebius-sre-interview/07-the-console-round-text-tools-systemd-and-everyday-operations.md#7-cron-and-logrotate-gotchas)<br />[20.7 10. Bash that survives production](./part-20-nebius-sre-interview/07-the-console-round-text-tools-systemd-and-everyday-operations.md#10-bash-that-survives-production) | One triage drill on a deliberately broken VM |
| Networking (25) | [2.30 4. A practical workflow](./part-02-networking/30-network-troubleshooting-method-and-case-studies.md#4-a-practical-workflow)<br />[2.30 5. The diagnostic kit](./part-02-networking/30-network-troubleshooting-method-and-case-studies.md#5-the-diagnostic-kit)<br />[IF TIME] SR-IOV vs virtio, BGP in the data centre, VXLAN: one paragraph each | Draw the decision tree for "A cannot reach B" |
| Platform: Linux internals, packet path (30) | [2.24 5. The packet path and where to tune it](./part-02-networking/24-linux-networking-policy-routing-bonding-mtu-nic-and-stack-tuning.md#5-the-packet-path-and-where-to-tune-it)<br />[2.24 6. TCP/IP stack tuning](./part-02-networking/24-linux-networking-policy-routing-bonding-mtu-nic-and-stack-tuning.md#6-tcpip-stack-tuning)<br />[2.23 1. Netfilter architecture](./part-02-networking/23-linux-networking-netfilter-nftables-conntrack-and-nat.md#1-netfilter-architecture)<br />[2.23 2. Connection tracking (conntrack)](./part-02-networking/23-linux-networking-netfilter-nftables-conntrack-and-nat.md#2-connection-tracking-conntrack)<br />[2.25 1. Network namespaces](./part-02-networking/25-linux-networking-namespaces-veth-bridges-and-container-networking.md#1-network-namespaces)<br />[2.25 2. Building container networking by hand](./part-02-networking/25-linux-networking-namespaces-veth-bridges-and-container-networking.md#2-building-container-networking-by-hand)<br />[2.22 Unix domain sockets](./part-02-networking/22-linux-networking-inspecting-state-with-ip-ss-and-counters.md#unix-domain-sockets) | Trace one packet: app `write()` -> socket -> TCP -> IP -> netfilter -> qdisc -> NIC; use `ss -i`, `conntrack -L`, `tc qdisc show`, `ip netns add` + veth pair |
| Coding (30) | Number of islands (BFS/DFS), tree level-order, max depth | Timed |
| Python (30) | Refresh:<br />[3.3 8. Iterables, iterators and generators](./part-03-python/03-idiomatic-python-the-data-model-comprehensions-generators.md#8-iterables-iterators-and-generators)<br />[3.3 6. Functions as objects, closures, decorators and desig...](./part-03-python/03-idiomatic-python-the-data-model-comprehensions-generators.md#6-functions-as-objects-closures-decorators-and-design-patterns) | Program: `@retry` decorator and timer context manager |
| Shell (15) | Health check | `nc -z` port, `systemctl is-active`, `df`, exit code |

## Day 11, Mon 7 Dec (review day: recall 25 min on Days 1-10)

| Block | Read these sections | Hands-on |
|---|---|---|
| Linux + Networking (55) | [2.1 12. A map from symptom to layer](./part-02-networking/01-what-happens-when-you-curl-a-url-a-packet-s-journey-end-to-end.md#12-a-map-from-symptom-to-layer)<br />[20.3 3. The first 60 seconds, command by command](./part-20-nebius-sre-interview/03-triage-method-for-a-sick-linux-box.md#3-the-first-60-seconds-command-by-command) | One timed 30-min Linux mock |
| Platform: DevOps + GPU overview (30) | SRE basics, read only (10 min, no practice needed):<br />[20.19 5. Error budgets: do the arithmetic](./part-20-nebius-sre-interview/19-slis-slos-and-alerts-for-token-apis.md#5-error-budgets-do-the-arithmetic)<br />[20.19 6. Burn rate and the multiwindow alert](./part-20-nebius-sre-interview/19-slis-slos-and-alerts-for-token-apis.md#6-burn-rate-and-the-multiwindow-alert)<br />[IF TIME] GPU overview:<br />[10.8 2. The three misleading metrics](./part-10-gpu-cuda/08-operating-gpu-nodes-nvidia-smi-topology-clocks-and-throttling.md#2-the-three-misleading-metrics)<br />[12.1 2. RDMA, RoCEv2 (UDP 4791), Elephant Flows, Flowlets, a...](./part-12-ai-networking/01-ai-traffic-collectives-incast-and-elephant-flows.md#2-rdma-rocev2-udp-4791-elephant-flows-flowlets-and-incast)<br />[15.1 3. Prefill vs. Decode Mechanics, Arithmetic Intensity, ...](./part-15-inference/01-the-anatomy-of-an-inference-request.md#3-prefill-vs-decode-mechanics-arithmetic-intensity-and-the-roofline-model) | Explain rolling/canary/blue-green, rollback, CI/CD stages aloud; one-minute GPU story: storage feeds GPUs, NVLink/RDMA move gradients, checkpoints go back to storage |
| Coding (30) | Three fresh problems, 30 min each | Timed |
| Python (30) | Refresh:<br />[3.9 2. pytest essentials](./part-03-python/09-testing-quality-and-ci-for-python-tooling.md#2-pytest-essentials)<br />[3.9 3. Isolating dependencies: fakes, stubs and mocks](./part-03-python/09-testing-quality-and-ci-for-python-tooling.md#3-isolating-dependencies-fakes-stubs-and-mocks) | Program: 6 tests for two earlier programs, one failure case |
| Shell (15) | All one-liners from Days 1-10 | From memory |

## Day 12, Tue 8 Dec

| Block | Read these sections | Hands-on |
|---|---|---|
| Mock (90) | 10 min your experience; 50 min general questions (Linux, networking, Kubernetes, DevOps, GPU basics; under 2 min each); 30 min a new medium problem aloud, no AI | Record if possible |
| Story (30) | 6-8 projects/incidents: problem, role, actions, trade-offs, failures, results with numbers | Write it down |
| Gaps (30) | Fix weak topics. [Read only, IF TIME] Terraform:<br />[20.24 2. Remote state, locking and why the state is the crown...](./part-20-nebius-sre-interview/24-terraform-for-resilient-gpu-clusters.md#2-remote-state-locking-and-why-the-state-is-the-crown-jewel)<br />[20.24 4. Safe changes: read the plan, guard the stateful thin...](./part-20-nebius-sre-interview/24-terraform-for-resilient-gpu-clusters.md#4-safe-changes-read-the-plan-guard-the-stateful-things-keep-history)<br />Ansible (read only):<br />[4.3 1. What Ansible is](./part-04-automation/03-ansible-from-zero-what-it-is-how-it-works-installation-and-ad-hoc-comm.md#1-what-ansible-is)<br />[4.3 2. How Ansible executes a task](./part-04-automation/03-ansible-from-zero-what-it-is-how-it-works-installation-and-ad-hoc-comm.md#2-how-ansible-executes-a-task) | Explain plan/apply, state, locking, drift, idempotency aloud |

## Wed 9 Dec morning

| Block | Read these sections | Hands-on |
|---|---|---|
| Light recall | [20.3 3. The first 60 seconds, command by command](./part-20-nebius-sre-interview/03-triage-method-for-a-sick-linux-box.md#3-the-first-60-seconds-command-by-command)<br />[2.1 12. A map from symptom to layer](./part-02-networking/01-what-happens-when-you-curl-a-url-a-packet-s-journey-end-to-end.md#12-a-map-from-symptom-to-layer)<br />Kubernetes request-path drawing; GPU-cluster tour | One easy problem |

## Possible gaps (not yet in the day tables; add if time)
| Topic | Why it may come up | Where |
|---|---|---|
| SSH keys, config, port forward | daily access path; "can't log in" questions | 1.5 |
| Boot process, systemd targets | "server won't boot", recovery | 1.14, 1.15 |
| Packages (apt/yum), repos | install, versions, broken dependencies | 1.7 |
| LVM, RAID, mounts, fstab | disk full, grow a volume | 1.12, 1.13 |
| Firewall: iptables/nftables, conntrack | "port open but blocked", NAT | 2.23 |
| Git basics, branching, rollback | DevOps staple | not in handbook; do `git log`, `branch`, `rebase`, `revert` |
| Monitoring and alerts: metrics, logs, traces, Prometheus basics | SRE core, SLO alerts | 20.19, 20.25, 5.24 |
| Incident response, on-call, post-mortem | experience discussion | 20.27 |
| Docker commands and image layers | container basics | 5.1, 5.2 |
| Databases basics (replication, backups, indexes) | page says OS/DB experience is discussed | not in handbook; prepare one example from your work |
| High availability, failover, SPOF, RTO/RPO | basic DevOps/SRE concepts | 20.33, 5.19, 5.20 |
| Cloud basics: VPC, subnets, security groups, IAM | cloud questions | 2.32, 20.31 |

## Python topic map (topic, subtopics, where to read, day)
| Topic | Subtopics | Read | Day |
|---|---|---|---|
| Types and strings | int/float/bool, str methods, slicing, f-strings, bytes vs str | 3.1 sections 3-4 | 1 |
| Collections | list, dict, set, tuple, sorting with `key=`, `sorted` | 3.1 section 5, 3.3 sections 2-3 | 1-2 |
| Counting and grouping | `Counter`, `defaultdict`, `deque`, `heapq`, `bisect` | 3.3 section 3 and stdlib docs | 2, 6 |
| Comprehensions | list/dict/set comprehensions, conditions | 3.3 section 7 | 2 |
| Functions | args, defaults, `*args`, `**kwargs`, scope, return | 3.1 section 8 | 3 |
| References and mutability | copy vs deepcopy, mutable defaults, aliasing | 3.1 section 2, 3.3 section 5 | 3 |
| Idioms | `enumerate`, `zip`, unpacking, EAFP, truthiness | 3.3 section 9 | 3 |
| Exceptions | try/except/else/finally, raise, custom errors | 3.5 section 1 | 4 |
| Files and paths | `with open`, `pathlib`, reading line by line | 3.5 section 3 | 3-4 |
| Logging | levels, format, `logging.getLogger` | 3.5 section 2 | 4 |
| subprocess and OS | `subprocess.run`, exit codes, env vars, `sys.exit`, signals | 3.5 sections 6-7 | 5 |
| Data formats | JSON, CSV, YAML | 3.5 section 5 | 7 |
| Text and regex | `re` basics, encodings | 3.5 section 4 | 7 |
| CLI scripts | `argparse`, robust script template | 3.5 section 8, 3.8 | 3, 5 |
| Network helpers | `ipaddress`, `socket`, retry/backoff | 3.1, 3.5 and stdlib docs | 8 |
| Classes | class, `__init__`, `__repr__`, `dataclass` | 3.4 | 9 |
| Iterators and generators | `yield`, generator pipelines, `itertools` | 3.3 section 8 | 6, 10 |
| Decorators and closures | wrapper, `functools.wraps`, retry decorator | 3.3 section 6 | 10 |
| Concurrency (low priority) | threads, processes, asyncio, thread pool | 3.6 sections 2-5 | optional |
| Testing | pytest, fixtures, mocks | 3.9 sections 2-3 | 11 |
| Interview angles | common questions and mistakes | 3.1 section 13, 3.3 section 13, 3.5 section 11 | any |

## Shell practice (type every one; one or two lines each)
### Navigate and inspect files
| Command | Use when | Example | Alternative / note |
|---|---|---|---|
| `ls -lah` | list with sizes and hidden files | `ls -lah /var/log` | `ls -lt` newest first; `tree` |
| `ls -li` | see inode numbers (hard links) | `ls -li file` | `stat file` |
| `stat` | full metadata, times, inode | `stat /etc/passwd` | `file` for type |
| `find` | locate files by name, size, age | `find /var/log -name "*.log" -mtime -1` | `locate` (indexed, fast but stale) |
| `du` | find what fills a disk | `du -xh --max-depth=1 / \| sort -h` | `ncdu` (interactive) |
| `df` | free space per mount | `df -h` and `df -i` (inodes) | `lsblk`, `findmnt` |
| `ln -s` | symlink to latest release | `ln -sfn /srv/app/rel42 /srv/app/current` | hard link `ln` has no `-s` |
| `chmod`, `chown` | fix permissions/ownership | `chmod 640 f; chown app:app f` | `setfacl` for ACLs |

### Read and search text
| Command | Use when | Example | Alternative / note |
|---|---|---|---|
| `cat`, `less` | read files, page long output | `less +F app.log` (follow) | `tail -f`, `bat` |
| `head`, `tail` | first/last lines, follow live | `tail -n 100 -f app.log` | `journalctl -f` for systemd |
| `grep` | find lines | `grep -rniE "error\|timeout" /var/log/app` | `rg` (ripgrep, faster) |
| `grep -c`, `-v`, `-A/-B` | count, invert, context | `grep -B2 -A2 "OOM" log` | |
| `wc` | count lines/words | `wc -l *.log` | |
| `sort`, `uniq` | rank frequency | `sort file \| uniq -c \| sort -rn \| head` | needs sorted input for `uniq` |
| `cut` | pick delimited columns | `cut -d: -f1 /etc/passwd` | `awk -F:` is more flexible |
| `awk` | columns, sums, filters | `awk '{print $1}' access.log` ; `awk '{s+=$NF} END {print s}' f` | Python for complex logic |
| `sed` | substitute, delete lines | `sed -i 's/old/new/g' f` ; `sed -n '10,20p' f` | `-i.bak` keeps a backup |
| `tr` | translate/delete characters | `tr 'a-z' 'A-Z'` ; `tr -d '\r'` | |
| `xargs` | build commands from a list | `find . -name "*.tmp" \| xargs rm` | `-P 4` parallel; `-0` with `find -print0` |
| `jq` | JSON on the command line | `curl -s url \| jq '.items[].name'` | Python `json` |
| `diff` | compare files | `diff -u old new` | `vimdiff`, `git diff --no-index` |
| `tee` | save and show output | `cmd \| tee out.log` | `-a` append |

### Processes and resources
| Command | Use when | Example | Alternative / note |
|---|---|---|---|
| `ps` | snapshot of processes | `ps aux --sort=-%mem \| head` | `ps -ef`, `pgrep -af name` |
| `top`, `htop` | live CPU/mem view | `top -o %MEM` | `htop` is friendlier; `pidstat 1` |
| `kill`, `pkill` | stop a process | `kill -TERM 1234`, then `kill -KILL 1234` last | `pkill -f name` |
| `jobs`, `bg`, `fg`, `nohup` | background work | `nohup ./job.sh > job.log 2>&1 &` | `tmux`/`screen`, systemd unit |
| `free`, `vmstat` | memory and run queue | `free -m`; `vmstat 1 5` | `/proc/meminfo` |
| `iostat`, `iotop` | disk busy/latency | `iostat -x 1 3` | `sar -d` |
| `uptime`, `nproc` | load vs core count | `uptime; nproc` | load above cores means queueing |
| `lsof` | open files/ports/deleted files | `lsof -i :8080` ; `lsof +L1` | `ss -ltnp` for ports |
| `strace` | see system calls | `strace -f -e trace=file -p 1234` | `ltrace`, `perf trace` |
| `dmesg` | kernel messages (OOM, disk errors) | `dmesg -T \| tail -50` | `journalctl -k` |
| `ulimit` | file descriptor limit | `ulimit -n` | `/proc/<pid>/limits` |

### Services, logs, time
| Command | Use when | Example | Alternative / note |
|---|---|---|---|
| `systemctl` | manage services | `systemctl status nginx` ; `systemctl restart nginx` | `service nginx status` (old) |
| `journalctl` | read service logs | `journalctl -u nginx -e --since "1 hour ago"` | `-p err` errors only |
| `crontab -e` | schedule jobs | `*/5 * * * * /opt/check.sh` | systemd timers |
| `date`, `timedatectl` | time and timezone | `timedatectl status` | `chronyc tracking` for NTP |
| `logrotate` | stop logs filling disks | `logrotate -d /etc/logrotate.conf` (dry run) | |

### Networking commands
| Command | Use when | Example | Alternative / note |
|---|---|---|---|
| `ip a`, `ip r` | addresses and routes | `ip a` ; `ip route get 8.8.8.8` | `ifconfig`/`route` are old |
| `ss` | sockets and listeners | `ss -ltnp` ; `ss -s` | `netstat` is old |
| `ping`, `traceroute`, `mtr` | reachability and path | `mtr -rw host` | `tracepath` |
| `dig`, `nslookup` | DNS | `dig +short A example.com` ; `dig +trace example.com` | `host` |
| `curl` | HTTP checks | `curl -sS -o /dev/null -w "%{http_code} %{time_total}\n" URL` | `wget`, `httpie` |
| `nc` | test a TCP port | `nc -vz host 443` | `telnet`, bash `/dev/tcp` |
| `tcpdump` | packet capture | `tcpdump -nn -i any port 53` | `tshark` |
| `openssl s_client` | check TLS cert | `openssl s_client -connect host:443 -servername host` | `curl -v` |
| `ssh` | remote access, tunnels | `ssh -L 8080:localhost:80 host` | `~/.ssh/config`, `scp`, `rsync` |
| `iptables`/`nft` | view firewall | `iptables -L -n -v` ; `nft list ruleset` | `ufw status` |

### Archive, copy, transfer
| Command | Use when | Example | Alternative / note |
|---|---|---|---|
| `tar` | archive/compress | `tar czf b.tgz dir/` ; `tar xzf b.tgz` | `zip` |
| `rsync` | copy with resume/diff | `rsync -avz --progress src/ host:/dst/` | `scp` for single files |
| `cp`, `mv`, `rm` | basic file ops | `cp -a src dst` | `rm -i`; never `rm -rf $VAR/` unquoted |
| `mktemp` | safe temp files | `tmp=$(mktemp)` | |

### Small scripts to write from memory
| Goal | Script |
|---|---|
| Top 10 IPs in a log | `awk '{print $1}' access.log \| sort \| uniq -c \| sort -rn \| head` |
| Requests per status code | `awk '{print $9}' access.log \| sort \| uniq -c` |
| Disk over 80 percent | `df -h \| awk 'NR>1 && $5+0>80 {print $6, $5}'` |
| Biggest 10 files | `find . -type f -printf '%s %p\n' \| sort -rn \| head` |
| Kill by name safely | `pgrep -af myapp` then `pkill -TERM -f myapp` |
| Loop over hosts | `for h in a b c; do ping -c1 -W1 $h >/dev/null && echo "$h up" \|\| echo "$h down"; done` |
| Read file line by line | `while IFS= read -r line; do echo "$line"; done < file` |
| Check a service and exit code | `systemctl is-active --quiet nginx \|\| { echo "down"; exit 1; }` |
| Port check | `nc -z -w2 host 443 && echo open \|\| echo closed` |
| Retry 3 times | `for i in 1 2 3; do curl -fsS URL && break; sleep 2; done` |
| Safe script header | `#!/usr/bin/env bash` then `set -euo pipefail` |
| Cleanup on exit | `trap 'rm -f "$tmp"' EXIT` |
| Parallel run | `cat hosts \| xargs -P 4 -I{} ssh {} uptime` |
| Count errors per hour | `grep ERROR app.log \| cut -c1-13 \| sort \| uniq -c` |
| Replace in many files | `grep -rl old . \| xargs sed -i 's/old/new/g'` |
| Find deleted-but-open files | `lsof +L1` |
| Who listens on a port | `ss -ltnp \| grep :8080` |
| Quick HTTP latency | `curl -o /dev/null -s -w "%{time_namelookup} %{time_connect} %{time_total}\n" URL` |
Where to read: 1.2, 1.4, 1.8, 1.9 (scripting), 20.7 (console tasks).
