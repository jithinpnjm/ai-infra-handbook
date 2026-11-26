# Preliminary round plan by topic (Fri 27 Nov to Wed 9 Dec morning; interview Wed 9 Dec)

## Confirmed format (from you): 90 minutes total
- First 60 min: conversation about YOUR experience, mixed with general Linux, networking and basic DevOps-stack questions (breadth and clear explanation, not a deep lab).
- Last 30 min: ONE LeetCode-style problem, solved live.
What this changes: (1) prepare a crisp experience story (day 12) and 6-8 concrete incidents/projects you can talk about with numbers; (2) answer general questions in 1-2 minutes: definition, how it works, one real tool/command, one failure example; (3) practise solving one problem in 30 minutes end to end: clarify (3 min), brute force and complexity (3), better approach (4), code (12), test with examples (5), complexity recap (3); (4) the daily program and TYPE hour stay, but the long troubleshooting drills are practice for explaining, not for a console task.

## 3-hour-a-day budget (supersedes the 4 h shape below; you work, so about 3 h max)
Each day (180 min): TOPIC 90 min (read only the MUST sections that fit, and type the commands in the same sitting: 50 read + 40 type) | PYTHON 60 min (15 refresh, 25 interview-style problem timed, 20 for the daily program, which you shrink to a 20-minute version or finish over two days if it overruns) | SPEAK 20 min (explain the day's topic aloud, 3 flashcards) | 10 min buffer.
Priority when time is short (cut from the bottom): 1. Linux triage tools and concepts, 2. networking flow, TCP, DNS, subnetting, 3. Python problems (never cut), 4. Kubernetes request path and pod troubleshooting, 5. GPU/AI cluster tour, 6. Terraform/Ansible/CI-CD concepts (only definitions and trade-offs), 7. data-centre networking (SR-IOV, BGP, VXLAN: one paragraph each).
If both weekends give you more than 3 h (Sat 28, Sun 29 Nov, Sat 5, Sun 6 Dec), use the extra time on the days marked as heavy: day 4 (triage), day 7 (networking debugging), day 9 (K8s/IaC), day 10 (GPU day). Day 10 can be read in 2 sittings if needed.
Reading rule: in each chapter read only the section headings listed MUST in map/NN-NN.md; skip everything else. Do not start a new chapter on days 11-12 except for gaps.

Goal: rebuild the fundamentals the first technical screening tests. Not question-hunting: every day is a topic block with reading, hands-on typing, one coding block, and a spoken recap. Per nebius.com/engineering-interviews and /careers/interviews/sre the screen covers Linux and console tools, networks, common service/operations issues, Kubernetes and core DevOps, practical coding (Python/Go, algorithms and data structures), explaining your thinking. System design, Slurm, Nebius architecture: after 9 Dec.
Chapter refs: 1.x Linux, 2.x networking, 3.x Python, 4.x Ansible, 5.x Kubernetes, 9.x NVIDIA systems, 10.x GPU/CUDA, 11.x GPU on Kubernetes, 12.x AI networking, 13.x AI storage, 15.x inference, 20.x interview volume. Which sections to read in each: STUDY_PLAN.md and map/NN-NN.md.

Daily shape (about 4 h): READ 1.5 h (MUST sections) | TYPE 1 h (commands in a Linux VM; kind cluster for K8s) | CODE 45 min (timer, Python) | SPEAK 20 min (explain the day's topic aloud, simple words) | 5 min: 3 flashcards.
Coding thread through all days (20.8 to 20.11): hashmaps/sets, strings, sorting, two pointers, stacks/queues, intervals, trees and BFS/DFS, graphs, heaps/top-K, sliding window; always say complexity, brute force first.

## Importance marks used below (nothing is cut; use the marks to decide what to do first)
[MUST] = core, read it fully and type the commands. [SHOULD] = strengthens your answers, read it after the MUSTs of the same day. [IF TIME] = skim or skip if the day runs out. Daily order: all [MUST] first, then Python, then [SHOULD], then [IF TIME].
Day-level importance: Linux days 1-4 HIGH; networking days 5-6 HIGH, day 7 MEDIUM; Kubernetes day 8 HIGH, day 9 MEDIUM; GPU day 10 MEDIUM (one-hour overview is enough for a first screen); Python HIGH every day (never cut); experience story day 12 HIGH.

## Python thread: refresh plus one program every day (adds about 45 min/day; trim the TYPE hour if needed)
Rules: write the program yourself from a blank file, run it, test it with 3 inputs including an edge case, then read it once for naming and errors. No AI. Save as `py/dayNN_name.py` in one folder; each day first re-run yesterday's program. Refresh chapters (read only MUST sections): 3.1 core, 3.3 idioms, 3.5 errors/files/subprocess, 3.6 concurrency, 3.9 testing (short).

| Day | Python to refresh (15 min read) | Program to write today (45 min) |
|---|---|---|
| 1 | variables, types, list/dict/set/tuple, f-strings, functions, mutability | Read a text file, print line count, word count, 5 most common words |
| 2 | loops, comprehensions, `collections.Counter/defaultdict`, sorting with `key=` | Parse an nginx/auth log: count requests per IP and status code, print top 10 |
| 3 | files, `with`, `pathlib`, `os`, `argparse` | CLI tool: given a directory, list the 10 largest files, and sum size per extension |
| 4 | exceptions (`try/except/finally`), `subprocess.run`, exit codes, `logging` | Run `df -h` and `systemctl is-active X` via subprocess, parse output, exit non-zero if disk over 80% or service down |
| 5 | modules, `if __name__ == "__main__"`, venv/pip, `ipaddress` module | Given a CIDR, print network, broadcast, usable host count, and check whether an IP is inside it; split into /26s |
| 6 | `socket`, `requests`/`urllib`, JSON, timeouts and retries with backoff | Health checker: GET a list of URLs with timeout and 3 retries (exponential backoff), print status and latency |
| 7 | generators, iterators, `itertools`, `heapq` | Stream a large log with a generator and report top-K slowest requests using a heap |
| 8 | classes, `dataclasses`, typing, `__repr__` | Model Pod/Node as dataclasses; write a function that finds unschedulable pods given node free CPU/memory |
| 9 | `json`/`yaml`, regex (`re`), string parsing | Read a Kubernetes-style YAML/JSON, validate required fields (image, resources.limits), report problems per resource |
| 10 | threads vs processes vs asyncio, `concurrent.futures`, GIL in one sentence | Query 20 hosts' port 22 concurrently with a thread pool and a bounded worker count; print which are open |
| 11 | decorators, context managers, `functools` (`lru_cache`) | Write a `@retry` decorator and a `timer` context manager; apply both to the day-6 health checker |
| 12 | `pytest` basics, `unittest.mock` | Write 6 pytest tests for any two of your earlier programs including an edge case and a failure case |

Also practise one-liners you should write without thinking: reading a file line by line, `dict.get`, `sorted(d.items(), key=lambda x: x[1], reverse=True)`, `enumerate`, `zip`, slicing, `try/except` with a specific exception, `subprocess.run([...], capture_output=True, text=True, check=False)`.

## Phase 1: Linux (days 1-4)
**Day 1, Fri 27 Nov: system and files.** Set up an Ubuntu VM or container with strace, lsof, tcpdump, dnsutils, iproute2. Read 1.1 big picture [SHOULD], 1.2 command line [MUST], 1.3 files/inodes/links [MUST], 1.6 permissions/sudo [MUST]. Type: pipes/redirection, `ls -li`, hard vs symlink, chmod/chown/umask, delete an open file and find it with `lsof +L1`. Code: Python refresh (3.1), 2 easy problems.
**Day 2, Sat 28 Nov: text tools, processes, scripting.** Read 1.4 grep/sed/awk/sort/uniq/xargs [MUST], 1.8 processes/signals/job control [MUST], 1.9 shell scripting (exit codes, quoting, strict mode) [SHOULD], 1.5 SSH (keys, port forwarding) [SHOULD]. Type: log summarising pipelines, zombie/orphan demo, `kill -TERM/-KILL`, SSH `-L`. Code: strings + hashmaps; read 3.3 (comprehensions, generators).
**Day 3, Sun 29 Nov: memory, syscalls, disks.** Read 1.17 memory/swap/OOM [MUST], 1.11 syscalls/strace/ldd [MUST], 1.12 disks/filesystems/mount [MUST]. Type: `free -m`, `vmstat 1`, trigger an OOM kill in a memory-limited container and find it in `dmesg`, `strace -f -e trace=file`, `df -h` vs `df -i`, `du -xh --max-depth=1`. Code: sorting, sets, two pointers.
**Day 4, Mon 30 Nov: services, logs, the triage method.** Read 20.3 triage method [MUST, most important Linux chapter], 1.15 systemd/journald [MUST], 20.4 fds/syscalls/permissions [MUST], 20.5 CPU/mem/disk [MUST], 1.16 logs/cron/time [SHOULD], 1.18 CPU and cgroups (skim) [IF TIME]. Type: write a unit that crashes and debug with `systemctl status` + `journalctl -u -e`; break the VM five ways (full disk, runaway process, OOM, port in use, bad permission) and triage each with the 60-second checklist (`uptime`, `dmesg -T | tail`, `vmstat 1`, `mpstat -P ALL`, `pidstat`, `iostat -x 1`, `free -m`, `ss -s`, `top`). Code: stacks/queues, intervals.

## Phase 2: Networking (days 5-7)
**Day 5, Tue 1 Dec: layers, addressing, routing.** Read 2.1 packet journey [MUST], 2.2 layers/encapsulation [MUST], 2.3 Ethernet/ARP [SHOULD], 2.4 subnetting/CIDR (work 15 sums by hand) [MUST], 2.5 routing [MUST]. Type: `ip a`, `ip route`, `ip route get`, `ip neigh`, `curl -v`. Code: trees, BFS/DFS.
**Day 6, Wed 2 Dec: transport and name resolution.** Read 2.6 TCP (handshake, states, retransmits, TIME_WAIT/CLOSE_WAIT) [MUST], 2.7 UDP/ICMP/ping/traceroute/mtr [MUST], 2.8 DNS [MUST], 2.10 HTTP/TLS [MUST], 2.9 DHCP/NAT [SHOULD]. Type: `ss -tan`, `ss -ltnp`, `nc -vz`, `dig +trace`, `openssl s_client -connect host:443`, capture a handshake and a DNS query with `tcpdump -nn`. Code: graphs.
**Day 7, Thu 3 Dec: debugging method, load balancing, data-centre networking basics.** Read 20.6 network debugging [MUST], 2.30 troubleshooting method [MUST], 2.20 load balancing (L4/L7, ECMP, proxies) [MUST], 2.22 ip/ss counters [MUST], 2.26 packet capture [SHOULD], 2.32 cloud load balancers [SHOULD], 2.11 VLANs (skim) [IF TIME], 2.16-2.18 (BGP in the DC, VXLAN, leaf-spine, skim) [IF TIME]. Type: MTU test `ping -M do -s 1472`, `iptables -L -n -v` or `nft list ruleset`, nginx as L7 reverse proxy with two backends. Also read about SR-IOV vs virtio/bridge/DPDK (2.24, 2.25 mentions; 11.10) so you can compare them [SHOULD, one paragraph]. Code: heap/top-K.

## Phase 3: Kubernetes and DevOps (days 8-9)
**Day 8, Fri 4 Dec: Kubernetes core.** Read 5.3 architecture [MUST], 5.5 API server and etcd [MUST], 5.8 life of a pod [MUST], 5.7 workloads [MUST], 5.9 kubelet/probes/QoS/evictions [MUST], 5.6 controllers/reconcile [SHOULD], 5.16 config/secrets/RBAC [SHOULD] (and how a kubeconfig is built [MUST]: cluster URL+CA, user credentials, context). Type (kind cluster): `kubectl config view`, `kubectl get pods -v=8`, `kubectl auth can-i`, `describe`, `logs --previous`, `get events`; draw the control-plane request path on paper. Code: sliding window.
**Day 9, Sat 5 Dec: Kubernetes networking, troubleshooting, IaC and delivery.** Read 5.10 Services/kube-proxy [MUST], 5.11 CoreDNS [MUST], 5.25 troubleshooting from the node [MUST], 20.23 failure drills [MUST], 5.12 ingress/gateway [SHOULD], 5.13 pod networking/CNI [SHOULD], 5.15 NetworkPolicy (skim) [IF TIME]; DevOps concepts: deployment strategies (rolling/canary/blue-green, rollback) [MUST], Terraform (20.24: plan/apply, state/locking, drift, modules) [SHOULD], SLI/SLO/error budgets (20.19) [SHOULD], Ansible basics (4.3, 4.6: inventory, idempotency, handlers) [SHOULD]. Type: break pods five ways (bad image, bad command, low memory, failing readiness, Service selector typo) and fix each. Code: 2 timed problems.

## Phase 4: GPU and AI cluster basics (day 10)
**Day 10, Sun 6 Dec: how an AI cluster works.** Goal: be able to explain each piece in plain words and say what breaks.
- GPU basics: 10.1 why GPUs [MUST], 10.3 memory hierarchy (HBM vs host RAM) [MUST], 10.8 operating GPU nodes (`nvidia-smi`, `nvidia-smi topo -m`, clocks, throttling, ECC/XID errors) [MUST], 10.9 driver/CUDA/container toolkit stack [MUST], 10.2 execution model (threads/warps/SMs, skim) [IF TIME], 10.4 tensor cores/precision (FP16/BF16/FP8, skim) [SHOULD].
- GPU interconnect: 10.6 PCIe, NVLink, NVSwitch [MUST]; 9.2 inside a DGX/HGX 8-GPU node [SHOULD].
- AI networking: 12.1 collective traffic (all-reduce, incast, elephant flows) [MUST], 12.2 RDMA basics [MUST], 12.12 Ethernet vs InfiniBand [MUST], 12.13 fabric design (leaf-spine, oversubscription, rails) [SHOULD], 12.3 RoCEv2/PFC/ECN (concepts) [SHOULD], 12.6 InfiniBand basics [IF TIME].
- AI storage: 13.1 data path from storage to GPU [MUST], 13.7 checkpoints [MUST], 13.2 local NVMe staging [SHOULD], 13.5 parallel/object storage (Lustre/WEKA/VAST/object: what each is for) [SHOULD], 13.3 GPUDirect Storage (idea) [SHOULD].
- GPUs on Kubernetes: 11.1 and 11.2 device plugin and container toolkit [MUST], 11.4 GPU Operator [SHOULD], 11.6 scheduling GPUs [SHOULD], 11.10 SR-IOV/Multus/RDMA secondary networks [IF TIME].
- Inference basics: 15.1 anatomy of an inference request (prefill vs decode, KV cache) [MUST], 15.2 batching/KV cache/quantization [SHOULD]; Nebius 20.18 how LLM serving fails [SHOULD] and 20.34 hardware and the GPU fleet [SHOULD].
- Type: on any GPU machine (or read sample outputs): `nvidia-smi`, `nvidia-smi topo -m`, `nvidia-smi -q -d ECC,TEMPERATURE`; on a laptop use the sample outputs in 10.8. Code: 1 timed problem only.
- Speak: a 5-minute tour "a training job reads data from storage, GPUs compute, gradients all-reduce over the network, checkpoints go back to storage; here is what slows or breaks at each step".

## Phase 5: consolidation (days 11-12 and morning of day 13)
**Day 11, Mon 7 Dec: console and coding practice.** Do all 12 tasks of 20.7 hands-on, timed. Then three timed coding problems (30 min each, matching the real 30-minute slot; include isomorphic strings, a sliding-window substring problem, and an O(1) insert/delete/get-random set) in Python, no AI, thinking aloud; review complexity (20.10). Write down the 5 weakest topics.
**Day 12, Tue 8 Dec: mocks and gaps.** Full 90-minute mock, recorded if possible: first 60 min = 10 min telling your experience, then 50 min of general questions from this plan (Linux, networking, Kubernetes, IaC/CI-CD, GPU cluster basics; use the section headings as a question list, answer each in under 2 minutes); last 30 min = one new medium LeetCode problem with the 30-minute structure above, aloud, no AI. Then fix the weak topics. Write your experience story: 6-8 projects/incidents (problem, your role, what you did, trade-offs, failures, measurable result). Stop by evening; sleep early.
**Wed 9 Dec morning: light only.** Re-read the 60-second triage checklist (20.3), the networking layer-by-layer symptom table (2.1 section 12), your Kubernetes request-path drawing, and the GPU-cluster tour. One easy coding problem. No new material.

## If you fall behind
Keep Linux (days 1-4), networking days 5-6, Kubernetes day 8 and the GPU day's first two bullets plus AI networking and storage overviews. Cut Day 7 depth to load-balancing and the troubleshooting method, and Day 9 to the node-level troubleshooting plus Terraform/SLO concepts.

## Python practice list (daily: 15 min refresh, ONE interview-style problem timed 25 min, then the daily program above; days 11-12 are timed 30-min problems only)
The interview-style problem is the real test (30 min, easy/medium). Solve brute force first, say complexity, test with 3 inputs.
| Day | Interview-style problem (LeetCode-style) |
|---|---|
| 1 | Reverse a string; palindrome check; FizzBuzz |
| 2 | Run-length compress "AABBBCCCCCDEFF" -> A2B3C5D1E1F2; decode it back; character frequency |
| 3 | Valid anagram; first non-repeating character; remove duplicates keeping order |
| 4 | Two sum (hashmap); contains duplicate; majority element |
| 5 | Valid parentheses (stack); merge two sorted lists; binary search |
| 6 | Isomorphic strings; group anagrams; top-K frequent elements (heap or sort) |
| 7 | Longest substring without repeating characters (sliding window); max subarray sum |
| 8 | Merge intervals; meeting rooms (can one person attend all); insert interval |
| 9 | Design O(1) insert/delete/get-random set (list + dict); LRU cache (OrderedDict) |
| 10 | BFS/DFS on a grid (number of islands); binary tree level-order and max depth |
| 11 | Three fresh timed problems (pick unseen easy/mediums), 30 min each |
| 12 | One full mock problem in the 90-minute mock; review mistakes |
Order inside each problem: restate, examples/edge cases, brute force + complexity, better approach, code, dry-run, complexity recap.
