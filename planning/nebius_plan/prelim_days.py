#!/usr/bin/env python3
"""Rebuilds the day tables of PRELIM_PLAN.md with section-level deep links (keeps the tail from '## Possible gaps' on)."""
import re,glob,os,sys
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
vol={int(os.path.basename(d.rstrip('/')).split('-')[1]):d.rstrip('/') for d in glob.glob(f'{root}/docs/part-*/')}
cache={}
def chap(ch):
    v,c=map(int,ch.split('.'));f=glob.glob(f'{vol[v]}/{c:02d}-*.md')[0]
    if f not in cache:
        H=[];seen={}
        for l in open(f):
            m=re.match(r'^(#{2,4}) (.+?)\s*$',l)
            if m:
                t=re.sub(r'[`*]','',m.group(2));t=re.sub(r'\[([^\]]*)\]\([^)]*\)',r'\1',t)
                s=re.sub(r'[^\w\s-]','',t.lower(),flags=re.U).strip().replace(' ','-')
                n=seen.get(s,0);seen[s]=n+1
                H.append((t,s if n==0 else f'{s}-{n}'))
        cache[f]=(f,H)
    return cache[f]
def L(ch,*keys):
    f,H=chap(ch);out=[]
    for k in keys:
        kk=re.sub(r'[`#]','',k).strip().lower()
        hit=[h for h in H if h[0].lower().startswith(kk)]
        if not hit: print('MISSING',ch,k);continue
        t,s=hit[0];lab=t if len(t)<=58 else t[:55]+'...'
        out.append(f"[{ch} {lab}](./{os.path.basename(os.path.dirname(f))}/{os.path.basename(f)}#{s})")
    return '<br />'.join(out)
def M(*parts): return '<br />'.join(p for p in parts if p)
K8S="[kubeconfig docs (kubernetes.io)](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)"
D=[
("Day 1, Fri 27 Nov",[
("Linux (30)",M(L('1.1','2. The three layers','3. What the kernel does'),L('1.2','6. Standard streams','7. Exit status')),"Pipes, redirection, `man`"),
("Networking (25)",L('2.1','1. The whole journey','3. Step 1: name resolution','7. Step 5: TCP','8. Step 6: TLS'),"`curl -v`"),
("Platform: Kubernetes (30)",M(L('5.1','1. What a container is','2. Images: layers'),L('5.2','1. The stack','2. containerd in depth')),"Run a container, `docker ps`, `docker exec`; on a kind node `crictl ps`"),
("Coding (30)","Reverse string, palindrome, FizzBuzz","Timed 25 min"),
("Python (30)",M('Refresh:',L('3.1','4. Strings and bytes','5. Core collections')),"Program: word count, top 5 words in a file"),
("Shell (15)","`wc`, `sort`, `uniq`","`sort \\| uniq -c \\| sort -rn \\| head`"),
("Setup","Ubuntu VM or container; strace, lsof, tcpdump, dnsutils, iproute2, kind","Folders `py/` and `sh/`")]),
("Day 2, Sat 28 Nov",[
("Linux (30)",M(L('1.6','3. File permissions','Changing permissions'),L('1.3','4. Inodes','5. Links')),"chmod, chown, umask, `df -i`"),
("Networking (25)",M(L('2.2','3. Layered models','4. Encapsulation'),L('2.4','2. IPv4 addresses and masks','Fast subnetting')),"5 subnet sums by hand"),
("Platform: Kubernetes (30)",L('5.3','1. The big picture','2. Control plane components','3. Node components'),"Create a kind cluster; draw control plane vs node and say what each component does"),
("Coding (30)","Run-length encode `AABBBCCCCCDEFF` to `A2B3C5D1E1F2`; decode; character frequency","Timed"),
("Python (30)",M('Refresh:',L('3.3','7. Comprehensions','3. Mappings and sets')),"Program: top 10 IPs and status codes from a log"),
("Shell (15)","`awk`, `sort`, `uniq`","Same top-IPs job in one pipeline")]),
("Day 3, Sun 29 Nov",[
("Linux (30)",M(L('1.8','2. What a process is','Zombies and orphans','4. Signals','5. Shell job control'),L('1.18','Run queues, time sharing','Nice values and weights')),"`ps`, `top`, `kill`, zombie demo"),
("Networking (25)",L('2.5','1. The routing decision','2. Reading the routing table'),"`ip route get`; 5 new subnet sums"),
("Platform: Kubernetes (30)",M(L('5.5','2. The request pipeline'),L('5.3','6. From `kubectl apply`'),L('5.6','1. The controller pattern','2. The machinery'),K8S+' (kubeconfig: cluster URL+CA, user, context)'),"`kubectl config view`, `kubectl get pods -v=8`"),
("Coding (30)","Valid anagram, first non-repeating char, remove duplicates","Timed"),
("Python (30)",M('Refresh:',L('3.1','8. Functions','2. Objects, names and references')),"Program: `argparse` CLI, 10 largest files in a directory"),
("Shell (15)","`find -size +10M`","`du -xh --max-depth=1 \\| sort -h`")]),
("Day 4, Mon 30 Nov",[
("Linux (30)",M(L('1.17','Translation: page tables','Demand paging, page faults','Swap','5. The OOM killer','The summary view'),L('1.4','3. grep','6. awk')),"`free -m`, `vmstat 1`, `dmesg -T \\| tail`"),
("Networking (25)",L('2.6','4. The handshake','5. Reliability'),"`ss -tan`, `ss -ltnp`"),
("Platform: Kubernetes (30)",M(L('5.7','3. Workload controllers'),L('5.8','1. Timeline overview','3. The kubelet takes over')),"Kind: deploy, scale, delete a pod"),
("Coding (30)","Two-sum, contains-duplicate, majority element","Timed"),
("Python (30)",M('Refresh:',L('3.5','1. Exceptions','3. Files and paths')),"Program: parse a log, skip bad lines, count failures"),
("Shell (15)","`pgrep -f`, `nohup`, `jobs`","`nohup cmd &`, `kill %1`")]),
("Day 5, Tue 1 Dec",[
("Linux (30)",M(L('1.12','6. Inside a traditional filesystem','8. Files, file descriptors and the read path','Capacity: df, du, inodes'),L('1.11','4. System calls','6. Watching a program')),"`df -h` vs `df -i`, `strace -f -e trace=file ls`"),
("Networking (25)",M(L('2.7','3. ping','4. traceroute'),L('2.8','2. How a lookup','4. Tools')),"`dig +trace`, `/etc/resolv.conf`"),
("Platform: Kubernetes (30)",M(L('5.9','1. What the kubelet does','5. Probes','6. Node-pressure eviction'),L('5.2','7. Cgroup drivers')),"Break a pod with a bad probe and a low memory limit; find its cgroup under `/sys/fs/cgroup`"),
("Coding (30)","Valid parentheses, merge two sorted lists, binary search","Timed"),
("Python (30)",M('Refresh:',L('3.5','6. Running external programs')),"Program: run `df -h`, exit non-zero if a filesystem is over 80%"),
("Shell (15)","`for` loop, `ping -c1`","Ping 3 hosts, print up/down")]),
("Day 6, Wed 2 Dec",[
("Linux (30)",L('1.15','3. Operating systemd','12. Journald'),"Crashing unit: `systemctl status`, `journalctl -u -e`"),
("Networking (25)",L('2.10','1. HTTP in practice','The handshake (TLS 1.3)','6. Troubleshooting'),"`openssl s_client -connect host:443`"),
("Platform: Kubernetes (30)",M(L('5.10','3. kube-proxy','7. Debugging Services'),L('5.11','2. Resolver behaviour','7. Debugging method')),"Kind: Service with wrong selector, find why no endpoints"),
("Coding (30)","Isomorphic strings, group anagrams, top-K frequent","Timed"),
("Python (30)",M('Refresh:',L('3.3','2. Sequences','3. Mappings and sets'),'(`deque`, `heapq` in the stdlib docs)'),"Program: top-K slowest requests from a log"),
("Shell (15)","`awk` sums, `cut`","`awk '{s+=$NF} END {print s}'`, `cut -d, -f2`")]),
("Day 7, Thu 3 Dec (review day: recall 25 min on Days 1-6)",[
("Linux (30)",L('20.3','### 3. The first 60 seconds','### 4. Reading load','### 6. The USE method'),"Run the 60-second checklist from memory on your VM"),
("Networking (25)",M(L('2.22','2. The `ip` command family','5. Counters'),L('2.26','2. tcpdump')),"Capture a handshake and a DNS query"),
("Platform: Kubernetes (30)",L('5.13','1. The Kubernetes network model','2. Building pod networking by hand','7. Inspecting pod networking'),"Kind: `kubectl exec` into a pod, `ip a`; on the kind node find its veth (`docker exec <node> ip a`) and `iptables-save \\| grep <svc>`"),
("Coding (30)","Longest substring without repeating characters, max subarray","Timed"),
("Python (30)",M('Refresh:',L('3.5','5. Data formats')),"Program: count errors per service from JSON lines"),
("Shell (15)","`sed -i`, `grep -rn`, `tar`","`tar czf` and `tar xzf`")]),
("Day 8, Fri 4 Dec",[
("Linux (30)",M(L('20.4','### 4. strace: how to read','### 5. Blocks, inodes','### 6. Permission checks'),L('1.19','2. The namespace types'),L('1.18','5. Control groups: the idea','7. The CPU controller')),"`lsof -p`, `/proc/<pid>/limits`"),
("Networking (25)",L('20.6','### 1. Refused, timed out','### 3. Reading ss','### 4. SYN backlog','### 5. TIME_WAIT'),"MTU test `ping -M do -s 1472`"),
("Platform: Kubernetes under the hood (30)",L('5.26','1. The master map','3. cgroups v2 in depth','6. Networking in the kernel'),"On a kind node: `crictl ps`, `lsns`, `nsenter -t <pid> -n ip a`; build a container by hand: "+L('1.20','Step 3. Namespaces with unshare')),
("Coding (30)","Merge intervals, meeting rooms, insert interval","Timed"),
("Python (30)",M('Refresh:',L('3.5','7. Interacting with the operating system'),'(`ipaddress`, `socket` in the stdlib docs)'),"Program: CIDR tool (network, broadcast, host count, contains)"),
("Shell (15)","`xargs -P 4`, `curl -w`","`curl -s -o /dev/null -w \"%{http_code}\"` over a URL list")]),
("Day 9, Sat 5 Dec",[
("Linux (30)",M(L('20.5','### 1. Load average','### 3. CPU throttling','### 7. The OOM killer'),L('20.7','### 1. Build every pipeline','### 5. Reading journald'),'[IF TIME]',L('1.13','4. NVMe in depth'),L('1.17','UMA versus NUMA')),"Do the pipelines in your VM"),
("Networking (25)",L('2.20','2. Algorithms','3. Health checks','4. ECMP'),"Nginx reverse proxy with 2 backends"),
("Platform: Kubernetes troubleshooting (30)",M(L('5.25','1. Method','3. Node-level toolkit','4. Failure playbooks'),L('5.18','1. The scheduler','3. Placement constraints','8. Debugging scheduling')),"Break 5 pods (Pending, CrashLoop, ImagePullBackOff, OOMKilled, bad probe) and diagnose each"),
("Coding (30)","O(1) insert/delete/get-random set, LRU cache","Timed"),
("Python (30)",M('Refresh:',L('3.4','1. Classes and objects','3. Data class builders')),"Program: nodes and pods, find pods that fit no node"),
("Shell (15)","Script basics","Args, `set -euo pipefail`, a function, `trap` cleanup")]),
("Day 10, Sun 6 Dec",[
("Linux (30)",L('20.7','### 6. Processes, signals','### 7. cron and logrotate','### 10. Bash that survives'),"One triage drill on a deliberately broken VM"),
("Networking (25)",M(L('2.30','4. A practical workflow','5. The diagnostic kit'),'[IF TIME] SR-IOV vs virtio, BGP in the data centre, VXLAN: one paragraph each'),"Draw the decision tree for \"A cannot reach B\""),
("Platform: Linux internals, packet path (30)",M(L('2.24','5. The packet path','6. TCP/IP stack tuning'),L('2.23','1. Netfilter architecture','2. Connection tracking'),L('2.25','1. Network namespaces','2. Building container networking by hand'),L('2.22','Unix domain sockets')),"Trace one packet: app `write()` -> socket -> TCP -> IP -> netfilter -> qdisc -> NIC; use `ss -i`, `conntrack -L`, `tc qdisc show`, `ip netns add` + veth pair"),
("Coding (30)","Number of islands (BFS/DFS), tree level-order, max depth","Timed"),
("Python (30)",M('Refresh:',L('3.3','8. Iterables, iterators and generators','6. Functions as objects')),"Program: `@retry` decorator and timer context manager"),
("Shell (15)","Health check","`nc -z` port, `systemctl is-active`, `df`, exit code")]),
("Day 11, Mon 7 Dec (review day: recall 25 min on Days 1-10)",[
("Linux + Networking (55)",M(L('2.1','12. A map from symptom to layer'),L('20.3','### 3. The first 60 seconds')),"One timed 30-min Linux mock"),
("Platform: GPU, PCIe, NUMA, RDMA on Linux (30)",M(L('10.9','1. The Seven-Layer NVIDIA','3. Containerizing the GPU'),L('1.22','4. The NVIDIA driver stack','7. Troubleshooting flow'),L('10.6','1. PCIe, PCIe Switches','2. NVLink, NVSwitch'),L('1.17','7. NUMA in practice'),L('12.2','1. Why TCP/IP Stalls','2. The Verbs Object Hierarchy'),L('13.1','3. Traditional bounce-buffer'),L('1.10','8. Hardware inventory')),"`lspci -tv`, `nvidia-smi topo -m`, `numactl -H`, `lsmod \\| grep nvidia`, `ibv_devinfo` if available; draw CPU - PCIe - GPU - NIC - NVMe with NUMA nodes"),
("Coding (30)","Three fresh problems, 30 min each","Timed"),
("Python (30)",M('Refresh:',L('3.9','2. pytest essentials','3. Isolating dependencies')),"Program: 6 tests for two earlier programs, one failure case"),
("Shell (15)","All one-liners from Days 1-10","From memory")]),
("Day 12, Tue 8 Dec (catch-up and gaps; revisit the weakest 3 topics from the recall cards)",[
("Linux (30)",M('[IF TIME] items you skipped:',L('1.12','6. Inside a traditional filesystem','8. Files, file descriptors and the read path'),L('1.13','4. NVMe in depth'),L('1.17','4. How Linux frees memory','8. Huge pages')),"Re-run one triage drill from memory"),
("Networking (25)",M('[IF TIME] SR-IOV vs virtio, BGP in the data centre, VXLAN, one paragraph each:',L('2.16','1.'),L('2.17','1.'),L('11.10','1.')),"Explain a packet leaving a pod to the internet, hop by hop"),
("Platform (30)",M('Read only: SRE basics',L('20.19','5. Error budgets','6. Burn rate'),'; deployment strategies (rolling, canary, blue-green), rollback, CI/CD stages; Terraform',L('20.24','2. Remote state','4. Safe changes'),'; Ansible',L('4.3','1. What Ansible is','2. How Ansible executes')),"Explain each aloud in 1-2 minutes"),
("Coding (30)","Three fresh problems, 10 min each, aloud","Timed"),
("Python + Shell (45)","Re-run all your programs and one-liners; fix any that fail","From memory")]),
("Day 13, Wed 9 Dec (review day: recall 25 min on Days 1-12)",[
("Mock A (60)","10 min your experience; 50 min general questions (Linux, networking, Kubernetes, DevOps, GPU basics; under 2 min each)","Record if possible"),
("Coding mock (30)","One new medium problem aloud, no AI: clarify, brute force, better approach, code, test, complexity","Timed 30 min"),
("Story (30)","6-8 projects/incidents: problem, role, actions, trade-offs, failures, results with numbers","Write it down"),
("Fix (30)","Fix the weak topics found in the mock","")]),
("Day 14, Thu 10 Dec",[
("Full mock (90)","Same format as the real interview: 60 min discussion + 30 min coding, aloud, no AI","Record if possible"),
("Gaps (30)","Fix only what failed in the mock","One easy problem to stay warm"),
("Light recall (30)",M(L('20.3','### 3. The first 60 seconds'),L('2.1','12. A map from symptom to layer'),'Kubernetes request-path drawing; the 12-step table'),"Stop by evening, sleep early")]),
("Fri 11 Dec morning (interview day)",[
("Light recall",M('Triage checklist, networking symptom table, Kubernetes request path, your project story'),"No new material")]),
]
o=["# Prelims plan: Fri 27 Nov to Fri 11 Dec morning (interview 11 Dec)","",
"Format: 90 min. First 60 min experience + general Linux/networking/DevOps questions; last 30 min one LeetCode-style problem.","",
"| Every day | Min | What |","|---|---|---|",
"| Recall | 10 | Aloud, no notes: 2 cards each from yesterday, 3 days ago, 7 days ago |",
"| Speak + cards | 10 | Explain the day's 3 biggest ideas; write 6 flashcards |","",
"## How Kubernetes runs on a Linux node (memorize this chain)","",
"| Step | What happens | Linux primitive underneath |","|---|---|---|",
"| 1 | `kubectl` reads kubeconfig, calls the API server over HTTPS | TCP + TLS, client cert or token |",
"| 2 | API server authenticates, authorizes (RBAC), admits, stores in etcd | HTTP, etcd (Raft) |",
"| 3 | Scheduler picks a node; kubelet on that node sees the Pod | watch on the API server |",
"| 4 | kubelet asks containerd (CRI) to create the sandbox and containers | gRPC over a unix socket |",
"| 5 | containerd + runc start the container process | `clone` with new namespaces (pid, net, mnt, uts, ipc), `pivot_root` |",
"| 6 | image layers become the container root filesystem | OverlayFS mount |",
"| 7 | CPU/memory limits are enforced | cgroup v2 (`cpu.max`, `memory.max`); over memory limit = OOM kill |",
"| 8 | CNI plugin gives the pod an IP | veth pair, bridge or routes, optional VXLAN/BGP |",
"| 9 | Service virtual IP reaches pods | kube-proxy iptables or IPVS NAT rules + conntrack |",
"| 10 | Volumes appear in the pod | CSI plugin + `mount` (bind mounts) |",
"| 11 | GPUs appear in the pod | device plugin + NVIDIA container toolkit (device files, driver libs) |",
"| 12 | Probes and eviction | kubelet loop; liveness restarts, memory pressure evicts |","",
"## Linux internals map (nothing skipped; basic first, advanced marked)","",
"| Area | Basic (must) | Advanced (if time) | Days |","|---|---|---|---|",
"| CPU and scheduling | "+L('1.18','Run queues, time sharing')+" | "+L('1.18','Interrupts and softirqs','7. The CPU controller')+" | 3, 8 |",
"| Memory | "+L('1.17','Demand paging, page faults','Swap','5. The OOM killer')+" | "+L('1.17','4. How Linux frees memory','8. Huge pages')+" | 4, 9 |",
"| Storage path and filesystems | "+L('1.12','8. Files, file descriptors and the read path')+" | "+L('1.13','4. NVMe in depth')+" | 5, 9 |",
"| Packet path in the kernel | "+L('2.24','5. The packet path')+" | "+L('2.23','2. Connection tracking')+" | 10 |",
"| Namespaces and cgroups (containers) | "+L('1.19','2. The namespace types')+" | "+L('5.26','3. cgroups v2 in depth')+" | 8 |",
"| PCIe, devices, NUMA | "+L('1.10','8. Hardware inventory')+" | "+L('10.6','1. PCIe, PCIe Switches')+" | 11 |",
"| GPU and NVIDIA on Linux | "+L('10.9','1. The Seven-Layer NVIDIA')+" | "+L('10.10','1. NVLink Domains')+" | 11 |",
"| RDMA and GPUDirect | "+L('12.2','1. Why TCP/IP Stalls')+" | "+L('10.10','3. From the NVLink Domain')+" | 11 |",
"| Kubernetes on Linux | "+L('5.26','1. The master map')+" | "+L('5.13','2. Building pod networking by hand')+" | 1-9 |","",
"Links go to the exact section to read, not the whole chapter. Everything else in a chapter is optional.",""]
for t,rows in D:
    o+=[f"## {t}","","| Block | Read these sections | Hands-on |","|---|---|---|"]
    o+=[f"| {a} | {b} | {c} |" for a,b,c in rows]; o.append("")
p=f'{root}/planning/nebius_plan/PRELIM_PLAN.md';old=open(p).read()
tail=old[old.index('## Possible gaps'):]
open(p,'w').write('\n'.join(o)+'\n'+tail);print('ok')
