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
("Platform (30)",L('5.1','1. What a container is','2. Images: layers'),"Run a container, `docker ps`, `docker exec`"),
("Coding (30)","Reverse string, palindrome, FizzBuzz","Timed 25 min"),
("Python (30)",M('Refresh:',L('3.1','4. Strings and bytes','5. Core collections')),"Program: word count, top 5 words in a file"),
("Shell (15)","`wc`, `sort`, `uniq`","`sort \\| uniq -c \\| sort -rn \\| head`"),
("Setup","Ubuntu VM or container; strace, lsof, tcpdump, dnsutils, iproute2, kind","Folders `py/` and `sh/`")]),
("Day 2, Sat 28 Nov",[
("Linux (30)",M(L('1.6','3. File permissions','Changing permissions'),L('1.3','4. Inodes','5. Links')),"chmod, chown, umask, `df -i`"),
("Networking (25)",M(L('2.2','3. Layered models','4. Encapsulation'),L('2.4','2. IPv4 addresses and masks','Fast subnetting')),"5 subnet sums by hand"),
("Platform (30)",L('5.3','1. The big picture','2. Control plane components'),"Draw control plane vs node"),
("Coding (30)","Run-length encode `AABBBCCCCCDEFF` to `A2B3C5D1E1F2`; decode; character frequency","Timed"),
("Python (30)",M('Refresh:',L('3.3','7. Comprehensions','3. Mappings and sets')),"Program: top 10 IPs and status codes from a log"),
("Shell (15)","`awk`, `sort`, `uniq`","Same top-IPs job in one pipeline")]),
("Day 3, Sun 29 Nov",[
("Linux (30)",L('1.8','2. What a process is','Zombies and orphans','4. Signals','5. Shell job control'),"`ps`, `top`, `kill`, zombie demo"),
("Networking (25)",L('2.5','1. The routing decision','2. Reading the routing table'),"`ip route get`; 5 new subnet sums"),
("Platform (30)",M(L('5.5','2. The request pipeline'),L('5.3','6. From `kubectl apply`'),K8S+' (kubeconfig: cluster URL+CA, user, context)'),"`kubectl config view`, `kubectl get pods -v=8`"),
("Coding (30)","Valid anagram, first non-repeating char, remove duplicates","Timed"),
("Python (30)",M('Refresh:',L('3.1','8. Functions','2. Objects, names and references')),"Program: `argparse` CLI, 10 largest files in a directory"),
("Shell (15)","`find -size +10M`","`du -xh --max-depth=1 \\| sort -h`")]),
("Day 4, Mon 30 Nov",[
("Linux (30)",M(L('1.17','5. The OOM killer','The summary view'),L('1.4','3. grep','6. awk')),"`free -m`, `vmstat 1`, `dmesg -T \\| tail`"),
("Networking (25)",L('2.6','4. The handshake','5. Reliability'),"`ss -tan`, `ss -ltnp`"),
("Platform (30)",M(L('5.7','3. Workload controllers'),L('5.8','1. Timeline overview','3. The kubelet takes over')),"Kind: deploy, scale, delete a pod"),
("Coding (30)","Two-sum, contains-duplicate, majority element","Timed"),
("Python (30)",M('Refresh:',L('3.5','1. Exceptions','3. Files and paths')),"Program: parse a log, skip bad lines, count failures"),
("Shell (15)","`pgrep -f`, `nohup`, `jobs`","`nohup cmd &`, `kill %1`")]),
("Day 5, Tue 1 Dec",[
("Linux (30)",M(L('1.12','Capacity: df, du, inodes'),L('1.11','4. System calls','6. Watching a program')),"`df -h` vs `df -i`, `strace -f -e trace=file ls`"),
("Networking (25)",M(L('2.7','3. ping','4. traceroute'),L('2.8','2. How a lookup','4. Tools')),"`dig +trace`, `/etc/resolv.conf`"),
("Platform (30)",L('5.9','5. Probes','6. Node-pressure eviction'),"Break a pod with a bad probe and a low memory limit"),
("Coding (30)","Valid parentheses, merge two sorted lists, binary search","Timed"),
("Python (30)",M('Refresh:',L('3.5','6. Running external programs')),"Program: run `df -h`, exit non-zero if a filesystem is over 80%"),
("Shell (15)","`for` loop, `ping -c1`","Ping 3 hosts, print up/down")]),
("Day 6, Wed 2 Dec",[
("Linux (30)",L('1.15','3. Operating systemd','12. Journald'),"Crashing unit: `systemctl status`, `journalctl -u -e`"),
("Networking (25)",L('2.10','1. HTTP in practice','The handshake (TLS 1.3)','6. Troubleshooting'),"`openssl s_client -connect host:443`"),
("Platform (30)",M(L('5.10','3. kube-proxy','7. Debugging Services'),L('5.11','2. Resolver behaviour','7. Debugging method')),"Kind: Service with wrong selector, find why no endpoints"),
("Coding (30)","Isomorphic strings, group anagrams, top-K frequent","Timed"),
("Python (30)",M('Refresh:',L('3.3','2. Sequences','3. Mappings and sets'),'(`deque`, `heapq` in the stdlib docs)'),"Program: top-K slowest requests from a log"),
("Shell (15)","`awk` sums, `cut`","`awk '{s+=$NF} END {print s}'`, `cut -d, -f2`")]),
("Day 7, Thu 3 Dec (review day: recall 25 min on Days 1-6)",[
("Linux (30)",L('20.3','### 3. The first 60 seconds','### 4. Reading load','### 6. The USE method'),"Run the 60-second checklist from memory on your VM"),
("Networking (25)",M(L('2.22','2. The `ip` command family','5. Counters'),L('2.26','2. tcpdump')),"Capture a handshake and a DNS query"),
("Platform (30)",M(L('5.7','3. Workload controllers'),L('20.19','5. Error budgets','6. Burn rate')),"Explain rolling, canary, blue-green, rollback, CI/CD stages aloud"),
("Coding (30)","Longest substring without repeating characters, max subarray","Timed"),
("Python (30)",M('Refresh:',L('3.5','5. Data formats')),"Program: count errors per service from JSON lines"),
("Shell (15)","`sed -i`, `grep -rn`, `tar`","`tar czf` and `tar xzf`")]),
("Day 8, Fri 4 Dec",[
("Linux (30)",M(L('20.4','### 4. strace: how to read','### 5. Blocks, inodes','### 6. Permission checks'),L('1.19','2. The namespace types')),"`lsof -p`, `/proc/<pid>/limits`"),
("Networking (25)",L('20.6','### 1. Refused, timed out','### 3. Reading ss','### 4. SYN backlog','### 5. TIME_WAIT'),"MTU test `ping -M do -s 1472`"),
("Platform (30)",M(L('20.24','2. Remote state','4. Safe changes'),L('4.3','1. What Ansible is','2. How Ansible executes')),"Explain plan/apply, state, locking, drift, idempotency aloud"),
("Coding (30)","Merge intervals, meeting rooms, insert interval","Timed"),
("Python (30)",M('Refresh:',L('3.5','7. Interacting with the operating system'),'(`ipaddress`, `socket` in the stdlib docs)'),"Program: CIDR tool (network, broadcast, host count, contains)"),
("Shell (15)","`xargs -P 4`, `curl -w`","`curl -s -o /dev/null -w \"%{http_code}\"` over a URL list")]),
("Day 9, Sat 5 Dec",[
("Linux (30)",M(L('20.5','### 1. Load average','### 3. CPU throttling','### 7. The OOM killer'),L('20.7','### 1. Build every pipeline','### 5. Reading journald')),"Do the pipelines in your VM"),
("Networking (25)",L('2.20','2. Algorithms','3. Health checks','4. ECMP'),"Nginx reverse proxy with 2 backends"),
("Platform: GPU 1 (30)",M(L('10.1','2. CPU latency design','4. Anatomy of an LLM'),L('10.3','1. The seven-tier'),L('10.8','2. The three misleading metrics','3. Clocks, power caps')),"Read the sample `nvidia-smi` outputs"),
("Coding (30)","O(1) insert/delete/get-random set, LRU cache","Timed"),
("Python (30)",M('Refresh:',L('3.4','1. Classes and objects','3. Data class builders')),"Program: nodes and pods, find pods that fit no node"),
("Shell (15)","Script basics","Args, `set -euo pipefail`, a function, `trap` cleanup")]),
("Day 10, Sun 6 Dec",[
("Linux (30)",L('20.7','### 6. Processes, signals','### 7. cron and logrotate','### 10. Bash that survives'),"One triage drill on a deliberately broken VM"),
("Networking (25)",M(L('2.30','4. A practical workflow','5. The diagnostic kit'),'[IF TIME] SR-IOV vs virtio, BGP in the data centre, VXLAN: one paragraph each'),"Draw the decision tree for \"A cannot reach B\""),
("Platform: GPU 2 (30)",M(L('10.6','1. PCIe, PCIe Switches','2. NVLink, NVSwitch'),L('12.1','1. AI Workloads','2. RDMA, RoCEv2'),L('12.12','1. Workload-backward design')),"Draw an 8-GPU node"),
("Coding (30)","Number of islands (BFS/DFS), tree level-order, max depth","Timed"),
("Python (30)",M('Refresh:',L('3.3','8. Iterables, iterators and generators','6. Functions as objects')),"Program: `@retry` decorator and timer context manager"),
("Shell (15)","Health check","`nc -z` port, `systemctl is-active`, `df`, exit code")]),
("Day 11, Mon 7 Dec (review day: recall 25 min on Days 1-10)",[
("Linux + Networking (55)",M(L('2.1','12. A map from symptom to layer'),L('20.3','### 3. The first 60 seconds')),"One timed 30-min Linux mock"),
("Platform: GPU 3 (30)",M(L('13.1','1. Why AI storage is different','2. The AI storage hierarchy'),L('13.7','1. How many bytes','2. Where the time goes'),L('15.1','2. The Nine-Stage','3. Prefill vs. Decode','4. KV Cache Memory'),L('11.1','1. CPU-Era Kubernetes','2. Why an Integer Count')),"Explain the full AI-cluster path aloud (storage, GPU, network, checkpoint)"),
("Coding (30)","Three fresh problems, 30 min each","Timed"),
("Python (30)",M('Refresh:',L('3.9','2. pytest essentials','3. Isolating dependencies')),"Program: 6 tests for two earlier programs, one failure case"),
("Shell (15)","All one-liners from Days 1-10","From memory")]),
("Day 12, Tue 8 Dec",[
("Mock (90)","10 min your experience; 50 min general questions (Linux, networking, Kubernetes, DevOps, GPU basics; under 2 min each); 30 min a new medium problem aloud, no AI","Record if possible"),
("Story (30)","6-8 projects/incidents: problem, role, actions, trade-offs, failures, results with numbers","Write it down"),
("Gaps (30)","Fix weak topics only","")]),
("Wed 9 Dec morning",[
("Light recall",M(L('20.3','### 3. The first 60 seconds'),L('2.1','12. A map from symptom to layer'),'Kubernetes request-path drawing; GPU-cluster tour'),"One easy problem")]),
]
o=["# Prelims plan: Fri 27 Nov to Wed 9 Dec morning","",
"Format: 90 min. First 60 min experience + general Linux/networking/DevOps questions; last 30 min one LeetCode-style problem.","",
"| Every day | Min | What |","|---|---|---|",
"| Recall | 10 | Aloud, no notes: 2 cards each from yesterday, 3 days ago, 7 days ago |",
"| Speak + cards | 10 | Explain the day's 3 biggest ideas; write 6 flashcards |","",
"Links go to the exact section to read, not the whole chapter. Everything else in a chapter is optional.",""]
for t,rows in D:
    o+=[f"## {t}","","| Block | Read these sections | Hands-on |","|---|---|---|"]
    o+=[f"| {a} | {b} | {c} |" for a,b,c in rows]; o.append("")
p=f'{root}/planning/nebius_plan/PRELIM_PLAN.md';old=open(p).read()
tail=old[old.index('## Possible gaps'):]
open(p,'w').write('\n'.join(o)+'\n'+tail);print('ok')
