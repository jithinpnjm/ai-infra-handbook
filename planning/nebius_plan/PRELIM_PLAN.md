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
| Linux (30) | 1.1 big picture [SHOULD]; 1.2 command line [MUST] | Pipes, redirection, `man` |
| Networking (25) | 2.1 what happens when you curl a URL [MUST] | `curl -v` |
| Platform (30) | 5.1 containers [MUST] | Run a container, `docker ps`, `docker exec` |
| Coding (30) | Reverse string, palindrome, FizzBuzz | Timed 25 min |
| Python (30) | Types, list/dict/set/tuple, f-strings | Program: word count, top 5 words in a file |
| Shell (15) | `wc`, `sort`, `uniq` | `sort \| uniq -c \| sort -rn \| head` |
| Setup | Ubuntu VM or container; install strace, lsof, tcpdump, dnsutils, iproute2, kind | Folders `py/` and `sh/` |

## Day 2, Sat 28 Nov

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | 1.6 permissions/sudo [MUST]; 1.3 files, inodes, links [MUST] | chmod, chown, umask, `df -i` |
| Networking (25) | 2.2 layers [MUST]; 2.4 subnetting/CIDR [MUST] | 5 subnet sums by hand |
| Platform (30) | 5.3 Kubernetes architecture [MUST] | Draw control plane vs node |
| Coding (30) | Run-length encode `AABBBCCCCCDEFF` to `A2B3C5D1E1F2`; decode; character frequency | Timed |
| Python (30) | Loops, comprehensions, `Counter`, `defaultdict` | Program: top 10 IPs and status codes from a log |
| Shell (15) | `awk`, `sort`, `uniq` | Same top-IPs job in one pipeline |

## Day 3, Sun 29 Nov

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | 1.8 processes/signals [MUST] | `ps`, `top`, `kill`, zombie demo |
| Networking (25) | 2.5 routing [MUST]; 2.3 Ethernet/ARP [SHOULD] | `ip route get`; 5 new subnet sums |
| Platform (30) | 5.5 API server/etcd, kubeconfig (cluster URL+CA, user, context) [MUST] | `kubectl get pods -v=8` |
| Coding (30) | Valid anagram, first non-repeating char, remove duplicates | Timed |
| Python (30) | Functions, default args, mutability | Program: `argparse` CLI, 10 largest files in a directory |
| Shell (15) | `find -size +10M` | `du -xh --max-depth=1 \| sort -h` |

## Day 4, Mon 30 Nov

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | 1.17 memory/OOM [MUST]; 1.4 grep/sed/awk [MUST] | `free -m`, `vmstat 1`, `dmesg -T \| tail` |
| Networking (25) | 2.6 TCP states, TIME_WAIT/CLOSE_WAIT [MUST] | `ss -tan`, `ss -ltnp` |
| Platform (30) | 5.7 workloads [MUST]; 5.8 life of a pod [MUST] | Kind: deploy, scale, delete a pod |
| Coding (30) | Two-sum, contains-duplicate, majority element | Timed |
| Python (30) | Files, `with`, exceptions | Program: parse a log, skip bad lines, count failures |
| Shell (15) | `pgrep -f`, `nohup`, `jobs` | `nohup cmd &`, `kill %1` |

## Day 5, Tue 1 Dec

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | 1.12 disks/filesystems [MUST]; 1.11 syscalls/strace [MUST] | `df -h` vs `df -i`, `strace -f -e trace=file ls` |
| Networking (25) | 2.7 ICMP/ping/traceroute [MUST]; 2.8 DNS [MUST] | `dig +trace`, `/etc/resolv.conf` |
| Platform (30) | 5.9 kubelet, probes, evictions [MUST] | Break a pod with a bad probe and a low memory limit |
| Coding (30) | Valid parentheses, merge two sorted lists, binary search | Timed |
| Python (30) | `subprocess.run`, exit codes | Program: run `df -h`, exit non-zero if any filesystem over 80% |
| Shell (15) | `for` loop, `ping -c1` | Ping 3 hosts, print up/down |

## Day 6, Wed 2 Dec

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | 1.15 systemd/journald [MUST]; 1.16 logs/cron [SHOULD] | Crashing unit: `systemctl status`, `journalctl -u -e` |
| Networking (25) | 2.10 HTTP/TLS [MUST]; 2.9 DHCP/NAT [SHOULD] | `openssl s_client -connect host:443` |
| Platform (30) | 5.10 Services/kube-proxy [MUST]; 5.11 CoreDNS [MUST] | Kind: Service with wrong selector, find why no endpoints |
| Coding (30) | Isomorphic strings, group anagrams, top-K frequent | Timed |
| Python (30) | `deque`, `heapq` | Program: top-K slowest requests from a log |
| Shell (15) | `awk` sums, `cut` | `awk '{s+=$NF} END {print s}'`, `cut -d, -f2` |

## Day 7, Thu 3 Dec (review day: recall 25 min on Days 1-6)

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | 20.3 triage checklist [MUST] | Run it from memory on your VM |
| Networking (25) | 2.22 `ip`/`ss` [MUST]; 2.26 tcpdump [SHOULD] | Capture a handshake and a DNS query |
| Platform (30) | Deployment strategies (rolling, canary, blue-green), rollback, CI/CD stages [MUST]; 20.19 SLI/SLO/error budget [SHOULD] | Explain each aloud |
| Coding (30) | Longest substring without repeating characters, max subarray | Timed |
| Python (30) | `json`, `re` | Program: count errors per service from JSON lines |
| Shell (15) | `sed -i`, `grep -rn`, `tar` | `tar czf` and `tar xzf` |

## Day 8, Fri 4 Dec

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | 20.4 fds/syscalls/permissions [MUST]; 1.19 namespaces, 1.18 cgroups [SHOULD] | `lsof -p`, `/proc/<pid>/limits` |
| Networking (25) | 20.6 network debugging scenarios [MUST] | MTU test `ping -M do -s 1472` |
| Platform (30) | Terraform basics 20.24 [SHOULD]: plan/apply, state, locking, drift; Ansible 4.3, 4.6 [SHOULD]: inventory, idempotency | Explain each aloud |
| Coding (30) | Merge intervals, meeting rooms, insert interval | Timed |
| Python (30) | `ipaddress`, `socket`, retry with backoff | Program: CIDR tool (network, broadcast, host count, contains) |
| Shell (15) | `xargs -P 4`, `curl -w` | `curl -s -o /dev/null -w "%{http_code}"` over a URL list |

## Day 9, Sat 5 Dec

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | 20.5 CPU/mem/disk [MUST]; 20.7 console tasks 1-4 [MUST] | Do the tasks in your VM |
| Networking (25) | 2.20 load balancing L4/L7/ECMP [MUST]; 2.32 cloud LBs [SHOULD] | Nginx reverse proxy with 2 backends |
| Platform: GPU 1 (30) | 10.1 why GPUs [MUST]; 10.3 memory hierarchy [MUST]; 10.8 nvidia-smi, topology [MUST] | Read the sample outputs |
| Coding (30) | O(1) insert/delete/get-random set, LRU cache | Timed |
| Python (30) | Classes, `dataclasses` | Program: nodes and pods, find pods that fit no node |
| Shell (15) | Script basics | Args, `set -euo pipefail`, a function, `trap` cleanup |

## Day 10, Sun 6 Dec

| Block | Study | Hands-on |
|---|---|---|
| Linux (30) | 20.7 console tasks 5-12 [MUST] | One triage drill on a deliberately broken VM |
| Networking (25) | 2.30 troubleshooting method [MUST]; SR-IOV vs virtio, BGP in the data centre, VXLAN [IF TIME]: 2.16, 2.17, 11.10 | One paragraph each |
| Platform: GPU 2 (30) | 10.6 PCIe/NVLink/NVSwitch [MUST]; 12.1 collective traffic [MUST]; 12.2 RDMA [MUST]; 12.12 Ethernet vs InfiniBand [SHOULD] | Draw an 8-GPU node |
| Coding (30) | Number of islands (BFS/DFS), tree level-order, max depth | Timed |
| Python (30) | Generators, decorators | Program: `@retry` decorator and timer context manager |
| Shell (15) | Health check | `nc -z` port, `systemctl is-active`, `df`, exit code |

## Day 11, Mon 7 Dec (review day: recall 25 min on Days 1-10)

| Block | Study | Hands-on |
|---|---|---|
| Linux + Networking (55) | 2.1 symptom table [MUST]; triage checklist from memory | One timed 30-min Linux mock |
| Platform: GPU 3 (30) | 13.1 storage path to GPU [MUST]; 13.7 checkpoints [MUST]; 15.1 inference request, prefill/decode, KV cache [MUST]; 11.1, 11.2 GPUs on Kubernetes [SHOULD] | Explain the full AI-cluster path aloud |
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
| Light recall | 20.3 triage checklist, 2.1 symptom table, Kubernetes request-path drawing, GPU-cluster tour | One easy problem |

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
