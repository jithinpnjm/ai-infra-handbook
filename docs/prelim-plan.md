---
id: prelim-plan
title: "TEMPORARY: Preliminary interview plan (27 Nov - 9 Dec)"
sidebar_label: "Prelim interview plan (temporary)"
sidebar_position: 0
---

:::caution Temporary page
Delete `docs/prelim-plan.md` after the interview (source: planning/nebius_plan/PRELIM_PLAN.md).
:::

# Prelims plan: Fri 27 Nov to Wed 9 Dec morning

Format: 90 min. First 60 min experience + general Linux/networking/DevOps questions; last 30 min one LeetCode-style problem.

| Every day | Min | What |
|---|---|---|
| Recall | 10 | Aloud, no notes: 2 cards each from yesterday, 3 days ago, 7 days ago |
| Speak + cards | 10 | Explain the day's 3 biggest ideas; write 6 flashcards |

Marks: [MUST] [SHOULD] [IF TIME]. Never cut Recall, Coding, Python.

## Day 1, Fri 27 Nov

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | [1.1](./part-01-linux/01-the-linux-big-picture-kernel-userspace-distributions.md) big picture [SHOULD]; [1.2](./part-01-linux/02-the-command-line-shells-commands-pipes-and-redirection.md) command line [MUST] | Pipes, redirection, `man` |
| Networking (25) | [2.1](./part-02-networking/01-what-happens-when-you-curl-a-url-a-packet-s-journey-end-to-end.md) what happens when you curl a URL [MUST] | `curl -v` |
| Platform (30) | [5.1](./part-05-kubernetes/01-containers-from-first-principles-images-layers-registries.md) containers [MUST] | Run a container, `docker ps`, `docker exec` |
| Coding (30) | Reverse string, palindrome, FizzBuzz | Timed 25 min |
| Python (30) | Types, list/dict/set/tuple, f-strings | Program: word count, top 5 words in a file |
| Shell (15) | `wc`, `sort`, `uniq` | `sort \| uniq -c \| sort -rn \| head` |
| Setup | Ubuntu VM or container; install strace, lsof, tcpdump, dnsutils, iproute2, kind | Folders `py/` and `sh/` |

## Day 2, Sat 28 Nov

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | [1.6](./part-01-linux/06-users-groups-permissions-acls-sudo-and-user-environments.md) permissions/sudo [MUST]; [1.3](./part-01-linux/03-files-and-the-directory-hierarchy-paths-links-inodes.md) files, inodes, links [MUST] | chmod, chown, umask, `df -i` |
| Networking (25) | [2.2](./part-02-networking/02-how-networks-work-layers-encapsulation-the-tcp-ip-model.md) layers [MUST]; [2.4](./part-02-networking/04-ip-addressing-subnetting-and-cidr-ipv4-and-ipv6-with-practice.md) subnetting/CIDR [MUST] | 5 subnet sums by hand |
| Platform (30) | [5.3](./part-05-kubernetes/03-kubernetes-architecture-overview-components-and-what-talks-to-what.md) Kubernetes architecture [MUST] | Draw control plane vs node |
| Coding (30) | Run-length encode `AABBBCCCCCDEFF` to `A2B3C5D1E1F2`; decode; character frequency | Timed |
| Python (30) | Loops, comprehensions, `Counter`, `defaultdict` | Program: top 10 IPs and status codes from a log |
| Shell (15) | `awk`, `sort`, `uniq` | Same top-IPs job in one pipeline |

## Day 3, Sun 29 Nov

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | [1.8](./part-01-linux/08-processes-signals-and-job-control.md) processes/signals [MUST] | `ps`, `top`, `kill`, zombie demo |
| Networking (25) | [2.5](./part-02-networking/05-routing-on-a-host-routing-tables-default-gateways-and-forwarding.md) routing [MUST]; [2.3](./part-02-networking/03-ethernet-and-l2-frames-mac-addresses-switching-arp-and-ndp.md) Ethernet/ARP [SHOULD] | `ip route get`; 5 new subnet sums |
| Platform (30) | [5.5](./part-05-kubernetes/05-the-api-server-and-etcd-how-a-request-becomes-cluster-state.md) API server/etcd, kubeconfig (cluster URL+CA, user, context) [MUST] | `kubectl get pods -v=8` |
| Coding (30) | Valid anagram, first non-repeating char, remove duplicates | Timed |
| Python (30) | Functions, default args, mutability | Program: `argparse` CLI, 10 largest files in a directory |
| Shell (15) | `find -size +10M` | `du -xh --max-depth=1 \| sort -h` |

## Day 4, Mon 30 Nov

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | [1.17](./part-01-linux/17-memory-management-virtual-memory-numa-huge-pages-oom.md) memory/OOM [MUST]; [1.4](./part-01-linux/04-text-processing-essentials-grep-sed-awk-find-xargs-sort.md) grep/sed/awk [MUST] | `free -m`, `vmstat 1`, `dmesg -T \| tail` |
| Networking (25) | [2.6](./part-02-networking/06-tcp-in-depth-handshake-windows-congestion-control-retransmission.md) TCP states, TIME_WAIT/CLOSE_WAIT [MUST] | `ss -tan`, `ss -ltnp` |
| Platform (30) | [5.7](./part-05-kubernetes/07-pods-and-workloads-deployments-statefulsets-daemonsets-and-jobs.md) workloads [MUST]; [5.8](./part-05-kubernetes/08-the-life-of-a-pod-end-to-end-including-what-the-kernel-does.md) life of a pod [MUST] | Kind: deploy, scale, delete a pod |
| Coding (30) | Two-sum, contains-duplicate, majority element | Timed |
| Python (30) | Files, `with`, exceptions | Program: parse a log, skip bad lines, count failures |
| Shell (15) | `pgrep -f`, `nohup`, `jobs` | `nohup cmd &`, `kill %1` |

## Day 5, Tue 1 Dec

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | [1.12](./part-01-linux/12-disks-partitions-and-filesystems.md) disks/filesystems [MUST]; [1.11](./part-01-linux/11-how-a-program-runs-system-calls-libraries-elf-strace-and-ldd.md) syscalls/strace [MUST] | `df -h` vs `df -i`, `strace -f -e trace=file ls` |
| Networking (25) | [2.7](./part-02-networking/07-udp-icmp-and-the-diagnostic-tools-ping-traceroute-mtr.md) ICMP/ping/traceroute [MUST]; [2.8](./part-02-networking/08-dns-in-depth-resolution-records-resolvers-and-caching.md) DNS [MUST] | `dig +trace`, `/etc/resolv.conf` |
| Platform (30) | [5.9](./part-05-kubernetes/09-the-kubelet-and-the-node-cri-cgroups-qos-classes-probes-and-eviction.md) kubelet, probes, evictions [MUST] | Break a pod with a bad probe and a low memory limit |
| Coding (30) | Valid parentheses, merge two sorted lists, binary search | Timed |
| Python (30) | `subprocess.run`, exit codes | Program: run `df -h`, exit non-zero if any filesystem over 80% |
| Shell (15) | `for` loop, `ping -c1` | Ping 3 hosts, print up/down |

## Day 6, Wed 2 Dec

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | [1.15](./part-01-linux/15-systemd-units-targets-timers-journald.md) systemd/journald [MUST]; [1.16](./part-01-linux/16-logging-time-synchronisation-cron-and-batch-jobs.md) logs/cron [SHOULD] | Crashing unit: `systemctl status`, `journalctl -u -e` |
| Networking (25) | [2.10](./part-02-networking/10-http-tls-and-pki-basics.md) HTTP/TLS [MUST]; [2.9](./part-02-networking/09-dhcp-nat-and-pat.md) DHCP/NAT [SHOULD] | `openssl s_client -connect host:443` |
| Platform (30) | [5.10](./part-05-kubernetes/10-services-endpoints-and-kube-proxy-the-life-of-a-service.md) Services/kube-proxy [MUST]; [5.11](./part-05-kubernetes/11-dns-and-service-discovery-with-coredns.md) CoreDNS [MUST] | Kind: Service with wrong selector, find why no endpoints |
| Coding (30) | Isomorphic strings, group anagrams, top-K frequent | Timed |
| Python (30) | `deque`, `heapq` | Program: top-K slowest requests from a log |
| Shell (15) | `awk` sums, `cut` | `awk '{s+=$NF} END {print s}'`, `cut -d, -f2` |

## Day 7, Thu 3 Dec (review day: recall 25 min on Days 1-6)

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | [20.3](./part-20-nebius-sre-interview/03-triage-method-for-a-sick-linux-box.md) triage checklist [MUST] | Run it from memory on your VM |
| Networking (25) | [2.22](./part-02-networking/22-linux-networking-inspecting-state-with-ip-ss-and-counters.md) `ip`/`ss` [MUST]; [2.26](./part-02-networking/26-packet-capture-from-scratch-tcpdump-tshark-and-wireshark.md) tcpdump [SHOULD] | Capture a handshake and a DNS query |
| Platform (30) | Deployment strategies (rolling, canary, blue-green), rollback, CI/CD stages [MUST]; [20.19](./part-20-nebius-sre-interview/19-slis-slos-and-alerts-for-token-apis.md) SLI/SLO/error budget [SHOULD] | Explain each aloud |
| Coding (30) | Longest substring without repeating characters, max subarray | Timed |
| Python (30) | `json`, `re` | Program: count errors per service from JSON lines |
| Shell (15) | `sed -i`, `grep -rn`, `tar` | `tar czf` and `tar xzf` |

## Day 8, Fri 4 Dec

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | [20.4](./part-20-nebius-sre-interview/04-files-descriptors-syscalls-and-permissions.md) fds/syscalls/permissions [MUST]; [1.19](./part-01-linux/19-namespaces-the-kernel-feature-behind-containers.md) namespaces, [1.18](./part-01-linux/18-cpu-scheduling-and-cgroups-v1-and-v2.md) cgroups [SHOULD] | `lsof -p`, `/proc/<pid>/limits` |
| Networking (25) | [20.6](./part-20-nebius-sre-interview/06-network-debugging-from-socket-to-switch.md) network debugging scenarios [MUST] | MTU test `ping -M do -s 1472` |
| Platform (30) | Terraform basics [20.24](./part-20-nebius-sre-interview/24-terraform-for-resilient-gpu-clusters.md) [SHOULD]: plan/apply, state, locking, drift; Ansible [4.3](./part-04-automation/03-ansible-from-zero-what-it-is-how-it-works-installation-and-ad-hoc-comm.md), [4.6](./part-04-automation/06-ansible-playbooks-tasks-modules-idempotency-and-check-mode.md) [SHOULD]: inventory, idempotency | Explain each aloud |
| Coding (30) | Merge intervals, meeting rooms, insert interval | Timed |
| Python (30) | `ipaddress`, `socket`, retry with backoff | Program: CIDR tool (network, broadcast, host count, contains) |
| Shell (15) | `xargs -P 4`, `curl -w` | `curl -s -o /dev/null -w "%{http_code}"` over a URL list |

## Day 9, Sat 5 Dec

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | [20.5](./part-20-nebius-sre-interview/05-cpu-memory-disk-and-the-scheduler.md) CPU/mem/disk [MUST]; [20.7](./part-20-nebius-sre-interview/07-the-console-round-text-tools-systemd-and-everyday-operations.md) console tasks 1-4 [MUST] | Do the tasks in your VM |
| Networking (25) | [2.20](./part-02-networking/20-load-balancing-l4-l7-ecmp-hashing-and-proxies.md) load balancing L4/L7/ECMP [MUST]; [2.32](./part-02-networking/32-cloud-networking-vpc-peering-load-balancers-and-gcp-specifics.md) cloud LBs [SHOULD] | Nginx reverse proxy with 2 backends |
| Platform: GPU 1 (30) | [10.1](./part-10-gpu-cuda/01-why-gpus-cpu-versus-gpu-and-throughput-design.md) why GPUs [MUST]; [10.3](./part-10-gpu-cuda/03-the-gpu-memory-hierarchy.md) memory hierarchy [MUST]; [10.8](./part-10-gpu-cuda/08-operating-gpu-nodes-nvidia-smi-topology-clocks-and-throttling.md) nvidia-smi, topology [MUST] | Read the sample outputs |
| Coding (30) | O(1) insert/delete/get-random set, LRU cache | Timed |
| Python (30) | Classes, `dataclasses` | Program: nodes and pods, find pods that fit no node |
| Shell (15) | Script basics | Args, `set -euo pipefail`, a function, `trap` cleanup |

## Day 10, Sun 6 Dec

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | [20.7](./part-20-nebius-sre-interview/07-the-console-round-text-tools-systemd-and-everyday-operations.md) console tasks 5-12 [MUST] | One triage drill on a deliberately broken VM |
| Networking (25) | [2.30](./part-02-networking/30-network-troubleshooting-method-and-case-studies.md) troubleshooting method [MUST]; SR-IOV vs virtio, BGP in the data centre, VXLAN [IF TIME]: [2.16](./part-02-networking/16-bgp-in-the-data-center-ebgp-clos-unnumbered-ecmp-anycast.md), [2.17](./part-02-networking/17-overlays-vxlan-and-evpn.md), [11.10](./part-11-gpu-kubernetes/10-secondary-networks-multus-sr-iov-device-plugin-and-rdma-device-plugin.md) | One paragraph each |
| Platform: GPU 2 (30) | [10.6](./part-10-gpu-cuda/06-gpu-interconnects-pcie-nvlink-nvswitch-and-nvlink-c2c.md) PCIe/NVLink/NVSwitch [MUST]; [12.1](./part-12-ai-networking/01-ai-traffic-collectives-incast-and-elephant-flows.md) collective traffic [MUST]; [12.2](./part-12-ai-networking/02-rdma-fundamentals-verbs-queue-pairs-and-memory-registration.md) RDMA [MUST]; [12.12](./part-12-ai-networking/12-ethernet-versus-infiniband-a-design-decision-guide.md) Ethernet vs InfiniBand [SHOULD] | Draw an 8-GPU node |
| Coding (30) | Number of islands (BFS/DFS), tree level-order, max depth | Timed |
| Python (30) | Generators, decorators | Program: `@retry` decorator and timer context manager |
| Shell (15) | Health check | `nc -z` port, `systemctl is-active`, `df`, exit code |

## Day 11, Mon 7 Dec (review day: recall 25 min on Days 1-10)

| Block | Study | Hands-on |
|---|---|---|
| Linux + Networking (55) | [2.1](./part-02-networking/01-what-happens-when-you-curl-a-url-a-packet-s-journey-end-to-end.md) symptom table [MUST]; triage checklist from memory | One timed 30-min Linux mock |
| Platform: GPU 3 (30) | [13.1](./part-13-ai-storage/01-the-ai-data-path-from-storage-to-gpu.md) storage path to GPU [MUST]; [13.7](./part-13-ai-storage/07-checkpoint-architecture-and-recovery.md) checkpoints [MUST]; [15.1](./part-15-inference/01-the-anatomy-of-an-inference-request.md) inference request, prefill/decode, KV cache [MUST]; [11.1](./part-11-gpu-kubernetes/01-why-kubernetes-needs-a-gpu-platform-layer.md), [11.2](./part-11-gpu-kubernetes/02-device-plugin-container-toolkit-cdi-and-runtime-classes.md) GPUs on Kubernetes [SHOULD] | Explain the full AI-cluster path aloud |
| Coding (30) | Three fresh problems, 30 min each | Timed |
| Python (30) | `pytest` | Program: 6 tests for two earlier programs, one failure case |
| Shell (15) | All one-liners from Days 1-10 | From memory |

## Day 12, Tue 8 Dec

| Block | Study | Hands-on |
|---|---|---|
| Mock (90) | 10 min your experience; 50 min general questions (Linux, networking, Kubernetes, DevOps, GPU basics; under 2 min each); 30 min a new medium problem aloud, no AI | Record if possible |
| Story (30) | 6-8 projects/incidents: problem, role, actions, trade-offs, failures, results with numbers | Write it down |
| Gaps (30) | Fix weak topics only |  |

## Wed 9 Dec morning

| Block | Study | Hands-on |
|---|---|---|
| Light recall | [20.3](./part-20-nebius-sre-interview/03-triage-method-for-a-sick-linux-box.md) triage checklist, [2.1](./part-02-networking/01-what-happens-when-you-curl-a-url-a-packet-s-journey-end-to-end.md) symptom table, Kubernetes request-path drawing, GPU-cluster tour | One easy problem |
