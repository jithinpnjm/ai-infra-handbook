---
id: "c02-26"
title: "2.26 Packet capture from scratch: tcpdump, tshark, Wireshark and BPF-based tracing"
sidebar_label: "2.26 Packet capture from scratch: tcpdump, tshark, Wireshark and BPF-based tracing"
sidebar_position: 26
description: "How capture works, capture filters, tcpdump and tshark, Wireshark analysis, capture at scale, and BCC/bpftrace networking tools"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 2.26 Packet capture from scratch: tcpdump, tshark, Wireshark and BPF-based tracing

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Any Linux VM (root); Wireshark on a laptop |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Counters tell you *that* something is wrong; packets tell you *what*. A capture settles arguments: did the SYN leave, did the reply arrive, was the MSS clamped, did a middlebox strip window scaling, who sent the RST, are PFC pause frames flooding a rail, is the RoCE traffic actually marked with the right DSCP, did the CNP get generated? On GPU clusters, capture is also the hardest to do right: 100/400 Gb/s links cannot be captured with naive `tcpdump`, RDMA traffic bypasses the kernel entirely, containers hide interfaces in namespaces, and overlays double-wrap packets. This chapter explains how capture works in Linux, how to write precise capture filters, how to use `tcpdump`, `tshark` and Wireshark effectively (including TLS decryption, VXLAN and RoCE decoding), how to capture at scale and from containers and switches, how to read common protocol traces, and how eBPF tools (BCC, bpftrace) complement captures by tracing the kernel's view of packets and sockets.

## Prerequisites and outcomes

You should know TCP/IP (2.4 to 2.7), Linux interfaces and counters (2.22), and have root access to a Linux host.

After this chapter you can:

- Explain how a capture works: libpcap, AF_PACKET, BPF filters in the kernel, promiscuous mode, ring buffers, snaplen, timestamps, and why captures drop packets or show impossible packets (offloads).
- Write capture filters (primitives, qualifiers, operators, byte-offset tests, TCP flags, VLAN, tunnels) and display filters; choose the capture point.
- Use `tcpdump` options (`-i -n -nn -c -w -r -s -e -v -vvv -X -A -tttt -B -C -W -G -Z`) and `tshark` for scripting and statistics.
- Analyse traces in Wireshark: Expert Information, conversations, stream graphs, I/O graphs, follow stream, decode-as, TLS decryption with a key log, VXLAN/GRE/GENEVE, RoCEv2 (BTH), PFC, LLDP, DHCP, DNS.
- Read a TCP trace: handshake, options, retransmissions, duplicate ACKs, zero windows, resets, MTU/MSS problems, delayed ACK.
- Capture at high rates and in containers/Kubernetes (ring buffers, truncation, NIC timestamping, AF_XDP/DPDK tools, port mirroring, TAPs, `kubectl debug`, `nsenter`).
- Use BCC and bpftrace networking tools and write simple bpftrace programs for TCP, sockets and packet drops.
- Handle captures responsibly (privacy, retention, authorisation).

## 1. How packet capture works

```mermaid
flowchart LR
  W["Wire"] --> N["NIC (promiscuous mode optional)"]
  N --> D["Driver / NAPI → sk_buff"]
  D --> T["AF_PACKET tap (before/after netfilter and tc depending on hook)"]
  T --> F["Kernel BPF filter (classic/eBPF): drop non-matching early"]
  F --> R["Ring buffer / socket buffer (PACKET_MMAP, TPACKET_V3)"]
  R --> L["libpcap"]
  L --> A["tcpdump / tshark / Wireshark / Zeek / Suricata"]
  D --> S["Normal stack (routing, netfilter, sockets)"]
```

- **libpcap** is the portable capture library; it opens an `AF_PACKET` socket on Linux (or `AF_XDP`/DPDK in specialised tools), compiles the user's **capture filter** into BPF bytecode and attaches it to the socket so non-matching packets are discarded in the kernel (cheap), and reads packets from a memory-mapped ring buffer.
- **Promiscuous mode** makes the NIC accept frames not addressed to its MAC (needed to see other hosts' traffic on a hub, mirror port or TAP); on a switched network without mirroring you see only your own, broadcast and multicast traffic.
- **Snaplen** (`-s`) is the number of bytes captured per packet (modern tcpdump default 262144, i.e. full). Truncating (`-s 96` or `-s 128`) captures headers only: far lighter, no payload privacy exposure, and usually enough.
- **Timestamps** come from the kernel at receive time (microsecond or nanosecond), or from hardware NIC timestamps (`tcpdump -j adapter`, `--time-stamp-precision=nano`) which are far more accurate for latency measurements; `ethtool -T eth0` lists support.
- **Capture point semantics**: on RX, the tap is before most of the stack (but after GRO merging by default); on TX, the tap occurs before the NIC (so checksum offload makes outgoing packets show bad checksums and TSO makes them appear larger than the MTU). Therefore captures taken *on the sending host* are not byte-exact copies of what hits the wire. Disable offloads temporarily when exact wire frames matter (`ethtool -K eth0 tso off gso off gro off rx off tx off`), or capture on a mirror port/TAP.
- **Drops**: "N packets dropped by kernel" means the capture socket's buffer overflowed (increase `-B`, narrow the filter, write to fast storage, truncate). "N packets dropped by interface" is the NIC. Capturing is best-effort and itself consumes CPU.

### Capture points

| Where | Sees | Notes |
|---|---|---|
| On the host (interface) | Traffic of that interface (post-GRO RX, pre-offload TX) | Easiest; offload artefacts |
| `-i any` | All interfaces, "cooked" (SLL) headers without L2 detail | Convenient; loses VLAN/ordering details; do not use for exact timing |
| Inside a container/pod namespace | That namespace's veth view | `nsenter -t PID -n tcpdump` |
| On a bridge/veth host-side | Traffic crossing between namespaces | Compare both ends of a veth |
| Switch port mirror (SPAN), ERSPAN, TAP | Copy of a link, independent of host stack | Truth source for the wire; mirrored traffic can be dropped under congestion |
| NIC/DPU embedded capture | Hardware-accelerated capture | For RDMA: `tcpdump -i mlx5_0` with `rdma-core` supports RoCE mirror via the NIC; `ibdump` |
| In the kernel (tracepoints, `kfree_skb`, `pwru`) | Packet's path and drop locations without copying | Complements, doesn't replace, pcap |

## 2. tcpdump

```bash
sudo tcpdump -D                                   # list capture interfaces
sudo tcpdump -ni eth0                             # -n no DNS ; -nn no port names either ; -i interface
sudo tcpdump -ni eth0 -c 100 'tcp port 443'       # stop after 100 packets
sudo tcpdump -nni eth0 -s 96 -w /tmp/c.pcap 'host 10.0.0.5 and tcp'      # write truncated capture to a file (preferred over live reading)
sudo tcpdump -nr /tmp/c.pcap                      # read ; add -tttt (date+time), -ttt (delta), -q (brief), -vvv (verbose), -e (link layer), -X / -XX (hex+ASCII), -A (ASCII)
sudo tcpdump -nn -i eth0 -tttt -e vlan and host 10.0.0.5      # show Ethernet header + VLAN tags
sudo tcpdump -ni eth0 -B 4096 -w - 'port 80' | gzip > /tmp/c.pcap.gz     # kernel buffer 4096 KiB; stream out
sudo tcpdump -ni any -C 100 -W 10 -w /var/tmp/ring.pcap          # ring buffer: 10 files of 100 MB (-C MB, -W count)
sudo tcpdump -ni eth0 -G 300 -w '/var/tmp/%Y%m%d-%H%M%S.pcap'     # rotate every 300 s (time-based)
sudo tcpdump -ni eth0 -Z tcpdump -w /tmp/c.pcap                   # drop privileges after opening
sudo tcpdump -ni eth0 --time-stamp-precision nano -j adapter_unsynced -w /tmp/hw.pcap      # NIC hardware timestamps
sudo tcpdump -d 'tcp port 22'                     # show the compiled BPF bytecode of a filter (-dd/-ddd variants)
```

### Capture filter syntax (pcap-filter)

A filter is an expression of **primitives**, each optionally with **qualifiers** (type `host|net|port|portrange`, direction `src|dst|src or dst`, protocol `ether|ip|ip6|arp|tcp|udp|icmp|icmp6|vlan`), combined with `and`/`&&`, `or`/`||`, `not`/`!` and parentheses.

| Goal | Filter |
|---|---|
| One host / either direction | `host 10.0.0.5` ; `src host 10.0.0.5` ; `dst net 10.0.0.0/24` |
| TCP/UDP port or range | `port 443` ; `tcp dst port 22` ; `portrange 5000-5100` |
| Not SSH noise | `not port 22` (essential when capturing over SSH) |
| ICMP / ICMPv6 | `icmp` ; `icmp6` ; `icmp[icmptype] == icmp-unreach` |
| ARP / non-IP | `arp` ; `ether proto 0x8809` (LACP) ; `ether proto 0x88cc` (LLDP) |
| TCP SYN only | `tcp[tcpflags] & tcp-syn != 0` ; SYN without ACK: `tcp[tcpflags] & (tcp-syn\|tcp-ack) == tcp-syn` |
| TCP RST/FIN | `tcp[tcpflags] & (tcp-rst\|tcp-fin) != 0` |
| Large packets / MTU test | `greater 1400` ; `ip[6:2] & 0x2000 != 0` (more fragments) |
| DNS | `udp port 53 or tcp port 53` |
| DHCP | `udp port 67 or udp port 68` |
| VLAN tagged | `vlan` ; `vlan 100` (filter after `vlan` keyword shifts offsets) |
| VXLAN | `udp port 4789` (outer); inner filtering needs Wireshark/tshark or `udp[8:2]` offsets |
| RoCEv2 | `udp dst port 4791` |
| PFC pause frames | `ether proto 0x8808` |
| TTL low | `ip[8] < 5` |
| DSCP EF | `ip[1] & 0xfc == 0xb8` ; ECN CE: `ip[1] & 0x3 == 3` |
| Specific flow | `host 10.0.0.5 and host 10.0.0.9 and tcp port 443` |

TCP flag text decoding in output: `S` SYN, `S.` SYN-ACK, `.` ACK, `P.` PSH-ACK, `F.` FIN-ACK, `R`/`R.` RST. Typical line: `10:00:00.123456 IP 10.0.0.2.51234 > 10.0.0.5.443: Flags [S], seq 1000, win 64240, options [mss 1460,sackOK,TS val 1 ecr 0,nop,wscale 7], length 0`.

**Rules of thumb**: capture to a file, filter narrowly, truncate, exclude your SSH session, note the clock (sync NTP/PTP across hosts when correlating captures), and capture at *both ends* to see what each side saw. Always record the exact command and host/interface in the case notes.

## 3. tshark and Wireshark

`tshark` is Wireshark's command-line version, with full dissectors, display filters and statistics: excellent for scripting and for headless servers. Wireshark (GUI) is best for interactive analysis of files copied from the host.

```bash
tshark -r c.pcap -q -z io,stat,1                              # packets and bytes per second
tshark -r c.pcap -q -z conv,tcp                               # TCP conversations (bytes, duration)
tshark -r c.pcap -q -z endpoints,ip ; -z http,tree ; -z dns,tree ; -z expert
tshark -r c.pcap -Y 'tcp.analysis.retransmission' -T fields -e frame.time_relative -e ip.src -e ip.dst -e tcp.seq
tshark -r c.pcap -Y 'tcp.stream eq 5' -T fields -e frame.time_delta_displayed -e tcp.flags.str -e tcp.len     # follow one stream
tshark -r c.pcap -qz follow,tcp,ascii,5                       # reconstruct stream 5 content
tshark -i eth0 -f 'port 443' -a duration:30 -w /tmp/t.pcapng  # capture filter (-f) vs display filter (-Y)
tshark -r c.pcap -o tls.keylog_file:/tmp/keys.log -Y http2 -T fields -e http2.headers.path    # decrypt TLS with a key log
editcap -c 100000 big.pcap part.pcap ; mergecap -w all.pcap a.pcap b.pcap ; capinfos c.pcap ; editcap -A "2026-01-01 10:00:00" -B "2026-01-01 10:05:00" in.pcap out.pcap
```

**Display filters** (richer than capture filters): `ip.addr == 10.0.0.5`, `tcp.port == 443`, `tcp.flags.syn == 1 && tcp.flags.ack == 0`, `tcp.analysis.retransmission`, `tcp.analysis.fast_retransmission`, `tcp.analysis.duplicate_ack`, `tcp.analysis.zero_window`, `tcp.analysis.window_full`, `tcp.analysis.lost_segment`, `tcp.window_size_value == 0`, `http.request.method == "POST"`, `dns.flags.rcode != 0`, `tls.handshake.type == 1` (ClientHello), `tls.alert_message`, `vxlan.vni == 10100`, `icmp.type == 3 && icmp.code == 4`, `eth.type == 0x8808` (PFC), `lldp`, `dhcp`, `ib.bth.opcode` / `infiniband` (RoCE: dissector `roce`/`infiniband`), `frame.time_delta > 0.2`.

**Wireshark features worth knowing:** Statistics → Conversations/Endpoints/Protocol Hierarchy/IO Graphs; **Analyze → Expert Information** (warnings for retransmissions, dup ACKs, zero window, out-of-order, window full, RST); **Statistics → TCP Stream Graphs** (time-sequence (Stevens), throughput, RTT, window scaling); **Follow TCP/UDP/TLS stream**; **Analyze → Decode As** (map a port to a dissector, e.g. UDP 4791 to RoCE or a custom port to VXLAN/GENEVE); **Edit → Preferences → Protocols → TLS → (Pre)-Master-Secret log filename** (set `SSLKEYLOGFILE` in the client, e.g. `SSLKEYLOGFILE=/tmp/keys.log curl ...`, to decrypt your own TLS in labs); **Time display format** (since previous displayed packet) to see gaps; coloring rules; packet comments and exported objects; and `File → Export Specified Packets` to share minimal evidence.

**Reading TCP in Wireshark/tshark:**

- Three-way handshake: SYN (options MSS, SACK permitted, timestamps, window scale), SYN-ACK, ACK; missing SYN-ACK = dropped/blocked/no route; RST instead of SYN-ACK = closed port.
- Options in the SYN: absent window scale on one side = a middlebox stripping options (throughput limited to 64 KB/RTT).
- **Retransmission** vs **fast retransmission** vs **spurious retransmission**; **dup ACK** counts (3 triggers fast retransmit); SACK blocks show which ranges arrived.
- **Zero window** (receiver app slow), **window update**, **window full** (sender limited by receive window) vs **bytes in flight < cwnd** (application limited).
- **Delayed ACK** gaps of 40 ms (Nagle interplay), **RTO** gaps of 200 ms+ doubling.
- **MSS/MTU**: look for segments larger than the path MTU with DF set followed by ICMP "fragmentation needed" (type 3 code 4); or large packets repeatedly retransmitted with no ICMP (black hole).
- **Resets**: who sent it (TTL/IP ID/timing differ from the peer's normal packets = middlebox injection), on which event (after idle: NAT/LB timeout; after data: application close with unread data).
- **Checksums**: "bad checksum" in captures on the sending host is usually offload; ignore unless seen on the receiving side.

## 4. Decoding the protocols you meet in AI infrastructure

| Protocol | Capture hints |
|---|---|
| **DNS** | `udp port 53`; look for repeated queries, NXDOMAIN storms (ndots search expansion: `svc.cluster.local` suffix queries), 5 s retransmit gaps, truncated (TC) responses followed by TCP, EDNS size |
| **DHCP** | `udp port 67 or 68`; DORA sequence; options (PXE: option 66/67, vendor class `PXEClient`), relay `giaddr`, rogue server offers |
| **ARP/NDP** | `arp or icmp6`; who-has/is-at, duplicate IP (two MACs for one IP), gratuitous ARP after failover |
| **ICMP** | Unreachables, time exceeded, redirects, PMTU (`icmp[icmptype] == 3`) |
| **TLS** | ClientHello (SNI, ALPN, versions), ServerHello, certificate (visible in TLS 1.2; encrypted in 1.3), alerts, handshake time; decrypt with key logs |
| **HTTP/2, gRPC** | Decrypted frames: HEADERS, DATA, RST_STREAM, GOAWAY; stream concurrency; window updates; `grpc-status` trailers |
| **VXLAN/Geneve/GRE** | Outer headers (VTEP IPs, UDP source port entropy), inner frame; decode-as for non-standard ports; compare inner/outer TTL, DSCP; MTU of inner vs outer |
| **LACP / LLDP** | `ether proto 0x8809` / `0x88cc`: partner state, port ID, VLAN/MTU TLVs |
| **PFC pause** | `ether proto 0x8808`: class-enable vector and quanta; rate of pauses per priority |
| **RoCEv2** | `udp dst port 4791`; BTH opcode (RC SEND/RDMA WRITE/READ, ACK, CNP = 0x81), PSN, destination QP; DSCP/ECN bits in IP header; **NIC-level capture is needed** for traffic the kernel doesn't see (`tcpdump -i mlx5_0` on rdma-core builds, `ibdump`, or switch mirror) |
| **BGP/OSPF/BFD** | `tcp port 179`, `proto 89`, `udp port 3784`; OPEN/UPDATE/KEEPALIVE/NOTIFICATION; BFD control packets, detect times |
| **NCCL bootstrap/sockets** | TCP between ranks; `NCCL_DEBUG=INFO` logs correlate IPs/ports with captures |
| **NFS/iSCSI/NVMe-oF TCP** | RPC XIDs, retransmissions, window sizes, `nconnect` multiple streams |

## 5. Capturing at scale and in awkward places

**High-rate links.** A 100 Gb/s link with 1500-byte frames is ~8 million packets per second: default `tcpdump` + libpcap cannot keep up. Options, in increasing power: (1) capture **only what you need** (tight filter, `-s 96`); (2) bigger kernel buffer (`-B 65536`), write to RAM disk or NVMe striped storage, avoid `-v` parsing, avoid name resolution; (3) capture **per queue / per flow** (RSS splits traffic; steer a flow of interest to one queue with `ethtool -N` flow rules); (4) use PF_RING/AF_XDP/DPDK-based capture tools (n2disk, Suricata, `dpdk-pdump`, `xdpdump`, `bpftool` + XDP capture programs); (5) **hardware**: switch-based mirror/ERSPAN to a dedicated capture server with specialised NICs, or NIC/DPU filtering and timestamping; (6) **sample** instead of capturing everything (sFlow/IPFIX/`tcpdump -c`, 1:1000 sampling), or capture only headers of selected flows; (7) trigger-based ring capture: keep a rolling buffer (`-C -W`) and stop on an event (`-G`, `inotify`, or a script that kills tcpdump when an alert fires), so you have the packets *before* the fault.

**RDMA/GPU fabrics.** Kernel `tcpdump` does not see RoCE traffic that bypasses the stack. Use the NIC vendor's capture path (Mellanox/NVIDIA `tcpdump` with the RDMA sniffer capability and a dedicated device, `ibdump` for IB/RoCE), switch mirror sessions, or telemetry (counters, INT). For GPU Direct, packets still appear on the wire/switch, not in the host kernel. Always capture on a *different* host or at the switch when diagnosing a host's NIC.

**Containers and Kubernetes.** From the node: `sudo nsenter -t <pid> -n tcpdump -ni eth0 -w /tmp/pod.pcap`; capture on the host-side veth (`ip -o link | grep veth`) or the CNI bridge; with `kubectl debug node/<node> -it --image=nicolaka/netshoot` (host namespaces) or `kubectl debug -it <pod> --image=nicolaka/netshoot --target=<container>` (ephemeral container sharing the pod's network namespace; requires permissions, capabilities `NET_RAW`/`NET_ADMIN`); `kubectl sniff` (ksniff plugin) streams a pod capture into Wireshark. Remember overlays: capture on the pod veth (inner), the tunnel device (inner, after decap), and the uplink (outer, encapsulated).

**Mirroring and TAPs.** SPAN (local mirror), RSPAN (VLAN-carried), ERSPAN (GRE-encapsulated mirror to a remote IP), sFlow/IPFIX sampling. Be aware: mirror ports can drop under oversubscription; mirrored frames may be altered (VLAN tags stripped/added); mirror both directions; TAPs (optical splitters) are lossless and passive. Linux can mirror too: `tc qdisc add dev eth0 ingress; tc filter add dev eth0 parent ffff: protocol all matchall action mirred egress mirror dev dummy0` (then capture on `dummy0` or send it elsewhere).

**Synchronised captures.** For one-way delay and ordering, capture at both ends with synchronised clocks (PTP with hardware timestamps; NTP only to ~ms) and align in Wireshark by merging (`mergecap -a`) or by comparing timestamps of the same packet (match by IP ID/TCP seq).

**Privacy and law.** Packet captures can contain credentials, tokens, personal data and model prompts. Capture only on systems and networks you are authorised to monitor; prefer header-only captures; protect and delete files according to policy; scrub or anonymise before sharing (tcprewrite, `editcap`, Wireshark masks); never post raw captures publicly.

## 6. BPF-based tracing for networking (BCC and bpftrace)

Packet capture shows packets on the wire or at an interface. BPF tracing shows what the **kernel and applications** do with them: which process opened which connection, how long handshakes take, which function dropped a packet, retransmits with socket state, per-process TCP throughput. BPF programs run sandboxed in the kernel, are verified for safety, and attach to probes: **kprobes/kretprobes** (kernel function entry/return), **uprobes/uretprobes** (user-space functions), **tracepoints** (stable kernel events such as `tcp:tcp_retransmit_skb`, `sock:inet_sock_set_state`, `skb:kfree_skb`, `net:net_dev_xmit`), **USDT** (static user probes in runtimes), and **perf events/timers**. Output is aggregated in-kernel into **maps** (counts, histograms, stacks) so overhead stays low.

### BCC and bpftrace

- **BCC** (BPF Compiler Collection): Python (or Lua/C++) front-end with embedded C BPF programs, plus a large collection of ready-made tools under `/usr/share/bcc/tools` (or `*-bpfcc` on Debian/Ubuntu). Good for complex tools with argument parsing and custom output. **Single-purpose tools** (`tcplife`, `tcpconnect`, `tcpaccept`, `tcpretrans`, `tcpdrop`, `tcpstates`, `tcpconnlat`, `tcptop`, `solisten`, `sockstat`, `biolatency`, `runqlat`, `execsnoop`, `opensnoop`) and **multi-purpose tools** (`trace`, `argdist`, `funccount`, `stackcount`, `funclatency`) that you point at any function. Install: `apt install bpfcc-tools linux-headers-$(uname -r)` or `dnf install bcc-tools`; modern **libbpf-tools** (CO-RE, no compiler on the target) are lighter. Example multi-purpose usage: `sudo funccount 'tcp_*'`, `sudo trace 'tcp_retransmit_skb "skb=%p"'`, `sudo argdist -H 'r::tcp_sendmsg():int:$retval'` (histogram of bytes sent), `sudo stackcount -P tcp_drop` (who triggers drops).
- **bpftrace**: a high-level language for one-liners and short scripts (awk-like: `probe /filter/ { action }`). Excellent for ad hoc questions.

```bash
sudo bpftrace -l 'tracepoint:tcp:*'                         # list available probes ; -lv to see arguments
sudo bpftrace -e 'tracepoint:tcp:tcp_retransmit_skb { @[ntop(args->daddr)] = count(); }'          # retransmits per destination
sudo bpftrace -e 'tracepoint:sock:inet_sock_set_state /args->newstate == 1/ { @connect[comm] = count(); }'     # new established TCP by process
sudo bpftrace -e 'kprobe:tcp_sendmsg { @send_bytes[comm] = hist(arg2); }'                          # send size distribution
sudo bpftrace -e 'kretprobe:tcp_recvmsg /retval > 0/ { @recv[comm] = sum(retval); }'               # bytes received per process
sudo bpftrace -e 'tracepoint:skb:kfree_skb { @[args->location] = count(); }' | head               # where packets are freed/dropped (resolve addresses with ksym())
sudo bpftrace -e 'kprobe:tcp_v4_connect { @start[tid] = nsecs; } kretprobe:tcp_v4_connect /@start[tid]/ { @us = hist((nsecs - @start[tid]) / 1000); delete(@start[tid]); }'
sudo bpftrace -e 'tracepoint:net:netif_receive_skb { @pkts[args->name] = count(); } interval:s:1 { print(@pkts); clear(@pkts); }'
sudo bpftrace -e 'uprobe:/usr/lib/x86_64-linux-gnu/libssl.so.3:SSL_write { @[comm] = count(); }'       # TLS writes per process (uprobe)
```

Program structure in bpftrace: **probe** (what event), optional **filter** (`/ cond /`), **action block** with built-in variables (`pid`, `tid`, `comm`, `nsecs`, `arg0..argN`, `retval`, `args->field` for tracepoints), **maps** (`@name[key] = count()|sum()|avg()|min()|max()|hist()|lhist()|stats()`), `printf`, `ntop()` for IP addresses, `ksym()/usym()` for symbols, `kstack`/`ustack`, and `BEGIN`/`END`/`interval` probes. Scripts live in `.bt` files with a shebang. **Caveats**: kprobe function names and arguments change across kernel versions (prefer tracepoints, which are stable); lots of events per second add overhead (aggregate in-kernel, avoid printing per event); needs root (or CAP_BPF/CAP_PERFMON) and `CONFIG_DEBUG_INFO_BTF` for CO-RE; in containers, access the host's debugfs/tracefs and use host PID namespace.

### Using BPF tools in network investigations

| Question | Tool |
|---|---|
| Which processes make/accept connections, and where? | `tcpconnect`, `tcpaccept`, `sockstat` |
| How long do TCP sessions live, how much do they transfer? | `tcplife` |
| Which flows retransmit, with state? | `tcpretrans` |
| Why were packets dropped (call stack)? | `tcpdrop`, `bpftrace` on `kfree_skb` (drop reasons on newer kernels via `skb:kfree_skb` `reason` field) |
| Handshake (connect) latency per destination | `tcpconnlat` |
| TCP state machine behaviour (TIME_WAIT, SYN_RECV durations) | `tcpstates` |
| Top bandwidth consumers by process | `tcptop` |
| Listening backlog problems | `solisten`, `tcpaccept`, `nstat` ListenOverflows |
| Softirq/hardirq time in the receive path | `softirqs`, `hardirqs` |
| Scheduler delays affecting network apps | `runqlat` |
| Custom: how often is function X called, how slow is it? | `funccount`, `funclatency`, `stackcount` |

BPF also underpins **XDP** programs (packet filtering/forwarding in the driver), **tc BPF** (classifiers at ingress/egress), **socket filters** (`SO_ATTACH_BPF`, which is how capture filters work), **CNI datapaths** (Cilium), and tools such as `pwru` (packet-where-are-you: traces an skb through the kernel functions for a given 5-tuple), `bpftool` (inspect loaded programs and maps), and `xdpdump`. Treat them as essential complements to pcap.

## 7. A capture-driven troubleshooting workflow

1. **State the question precisely** ("Does the SYN reach the server? Where is it dropped?").
2. **Choose capture points** (client, server, both sides of a firewall/NAT/LB, switch mirror).
3. **Write the narrowest filter** that answers it; exclude your management session; capture to file with a ring buffer if the event is intermittent.
4. **Reproduce** and note exact times, addresses and the application's log lines.
5. **Open the files together**: align by time; follow one connection; compare what left A vs what arrived at B (differences point to the device between them: NAT rewriting, MSS clamping, dropped options, injected resets, MTU).
6. **Confirm with counters and BPF tools** (`nstat`, `ss -ti`, `tcpretrans`, `tcpdrop`, `conntrack`, firewall counters).
7. **Fix and re-capture** to verify the symptom is gone.

Common patterns: SYN seen at the server but no SYN-ACK back = server firewall/listen queue; SYN-ACK seen at server but not client = return path/asymmetric/NAT; data sent but repeated retransmissions without ICMP = MTU black hole or stateful device dropping; duplicate ACKs and SACK = loss on the path; RST from a different TTL = middlebox; long idle then reset = timeout; large gaps of exactly 200 ms/1 s = RTO or delayed ACK; DNS answers arriving after 5 s = resolver timeout; ClientHello followed by nothing = TLS interception/MTU issue with large hello (post-quantum key shares make ClientHellos large); pause frames at multi-kHz on one priority = PFC storm; CNP absence while ECN-marked packets arrive = NIC DCQCN misconfiguration.

## 8. Lab: capture, read, decode (untested)

Use two namespaces/VMs with a veth pair (chapter 2.5/2.25 setup) and a lab web server.

1. **Handshake and teardown**: capture `curl` to a local nginx; label SYN/SYN-ACK/ACK/FIN; note options; export a stream with `tshark -z follow`.
2. **Filters**: write and test five capture filters (SYN only, RST, port range, DSCP EF, VLAN); verify with `tcpdump -d` and hit counts; write the same as Wireshark display filters.
3. **Retransmissions and loss**: `tc qdisc add dev veth1 root netem loss 2%`; capture; identify retransmissions, fast retransmit, dup ACKs and SACK blocks; plot the Stevens time-sequence graph; compare with 0% loss.
4. **MTU black hole**: set a smaller MTU on a router namespace, drop ICMP type 3 code 4, send a large transfer; capture to see repeated retransmission of full-size segments; fix with MSS clamping and compare.
5. **Zero window**: server that sleeps before reading; capture the window shrinking to zero and window probes.
6. **TLS**: `SSLKEYLOGFILE=/tmp/keys.log curl https://localhost`; open the capture with the key log and read the decrypted HTTP/2 frames; observe SNI/ALPN in the ClientHello.
7. **Offload artefacts**: capture on the sender with TSO/checksum offload on and off; observe "bad checksum" and 64 KB segments.
8. **Overlay**: build a VXLAN link (chapter 2.17); capture outer and inner; use Decode As for a custom port; compare DSCP/TTL.
9. **Ring buffer and trigger**: run `tcpdump -C 10 -W 5` and a script that stops it when a ping loss threshold is crossed; verify you have the packets before the event.
10. **BPF tools**: run `tcplife`, `tcpconnect`, `tcpretrans`, `tcpdrop`; write three bpftrace one-liners (retransmits per destination, send size histogram, connect latency); correlate with your pcap.
11. **Container capture**: run a container, find its PID, capture with `nsenter`, and with `docker run --network container:NAME nicolaka/netshoot tcpdump`.
12. **Clean up and delete captures.**

Mark tested only after execution.

## 9. Common mistakes

- Running `tcpdump` live over SSH without excluding the SSH port (feedback loop), or with name resolution on.
- Reading outbound packets' bad checksums or giant frames as network faults (offloads).
- Capturing on the same host that is overloaded and trusting the drop-free result; ignoring "dropped by kernel".
- Using `-i any` for timing analysis; forgetting VLAN/L2 details it hides.
- Capturing only one side; comparing captures from unsynchronised clocks.
- Missing the RDMA traffic because the kernel never sees it.
- Decrypting TLS in production or sharing raw captures that contain secrets.
- Treating Wireshark's expert warnings as faults without context (e.g. "out of order" from multi-queue capture).
- Running heavy bpftrace probes (per-packet printf) on busy production hosts.

## 10. Interview angles

- "How does `tcpdump` work? What's a BPF filter and where does it run?"
- "You see a packet with a bad checksum in a capture. Is it a problem?"
- "How would you capture traffic on a busy 100G host without dropping packets?"
- "A connection works for small requests but hangs for large ones; what would the capture show?"
- "How do you read retransmissions, duplicate ACKs, SACK, zero window, RTO in a trace?"
- "How do you capture inside a Kubernetes pod? How about RoCE traffic?"
- "What is the difference between a capture filter and a display filter?"
- "When would you use BCC/bpftrace instead of tcpdump? Give three examples."
- "How do you decrypt TLS in a lab capture?"

## 11. Checkpoint questions (40)

1. What library underlies tcpdump? **A:** libpcap.
2. What Linux socket type does capture use? **A:** `AF_PACKET` (also AF_XDP in specialised tools).
3. Where does the capture filter run? **A:** In the kernel, as BPF attached to the socket.
4. What does promiscuous mode do? **A:** NIC accepts frames not addressed to it.
5. What is snaplen? **A:** Bytes captured per packet.
6. Why do outgoing packets show bad checksums? **A:** Checksum offload: computed after the tap.
7. Why do captured packets exceed the MTU? **A:** TSO/GSO/GRO super-packets.
8. What does "dropped by kernel" mean? **A:** Capture buffer overflow.
9. Why avoid `-i any` for timing? **A:** Cooked headers and mixed interfaces lose detail.
10. Option for no name resolution? **A:** `-n` / `-nn`.
11. Option to write a file? **A:** `-w`; read with `-r`.
12. Ring buffer options? **A:** `-C size -W count`.
13. Filter for SYN-only packets? **A:** `tcp[tcpflags] & (tcp-syn|tcp-ack) == tcp-syn`.
14. Filter excluding SSH? **A:** `not port 22`.
15. RoCEv2 UDP port? **A:** 4791.
16. PFC EtherType? **A:** 0x8808.
17. LLDP EtherType? **A:** 0x88cc.
18. LACP EtherType? **A:** 0x8809 (slow protocols).
19. Display vs capture filter? **A:** Wireshark's richer post-capture filter vs kernel BPF filter.
20. How to see the compiled BPF? **A:** `tcpdump -d`.
21. How to follow a stream in tshark? **A:** `-z follow,tcp,ascii,N`.
22. How to decrypt TLS in a lab? **A:** `SSLKEYLOGFILE` + key-log setting in Wireshark.
23. What is Decode As? **A:** Map a port/protocol to a different dissector.
24. What does Expert Information show? **A:** Anomalies like retransmissions, dup ACKs, zero window.
25. Sign of a stripped window-scale option? **A:** Missing wscale in SYN/SYN-ACK and low throughput.
26. Sign of an MTU black hole? **A:** Large segments retransmit repeatedly with no ICMP.
27. What causes 200 ms gaps? **A:** RTO minimum or delayed ACK interactions.
28. RST with different TTL implies? **A:** Likely a middlebox.
29. Why capture both ends? **A:** To find what the path between changed or dropped.
30. How to capture a pod's traffic? **A:** `nsenter -t PID -n tcpdump` or an ephemeral debug container.
31. How to capture RDMA traffic? **A:** NIC-level capture, `ibdump`, or switch mirror.
32. SPAN vs TAP? **A:** Switch mirror (can drop) vs passive lossless splitter.
33. How to mirror with Linux tc? **A:** `matchall` filter with `mirred egress mirror`.
34. What is ERSPAN? **A:** GRE-encapsulated mirror to a remote IP.
35. What hardware helps timing accuracy? **A:** NIC hardware timestamps with PTP.
36. What are BCC tools? **A:** Prebuilt BPF-based tracing utilities (tcplife, tcpretrans...).
37. bpftrace program structure? **A:** probe, filter, action; maps for aggregation.
38. Why prefer tracepoints to kprobes? **A:** Stability across kernel versions.
39. Which tool shows drop call stacks? **A:** `tcpdrop` / `kfree_skb` tracing.
40. What must you consider legally? **A:** Authorisation, privacy, retention of captured data.

## 12. Sources and review notes

**Written in original words.** Principal sources:

- Brian Ward, *How Linux Works*, 3rd ed., chapter 10: diagnostic tools (tcpdump output, filters with primitives and operators, port scanning context), plus the caution about snooping.
- Brendan Gregg, *Systems Performance*, 2nd ed., chapter 10 (packet sniffing methodology, tcpdump and Wireshark, TCP analysis) and chapter 15 (BPF: BCC installation, tool coverage, single- and multi-purpose tools, one-liners, BCC versus bpftrace, bpftrace tools, one-liners, programming, reference).
- The author's own `nvidia-devops` networking masterclass (advanced tcpdump/tshark usage, bpftrace latency one-liners, dropwatch and perf for drop analysis, ethtool counters).
- Filter tables, workflows and RDMA/Kubernetes capture guidance are the author's synthesis from `pcap-filter(7)`, `tcpdump(1)`, `tshark(1)`, the Wireshark user guide and the bpftrace/BCC documentation.

**Flagged for verification before publishing:** bpftrace tracepoint argument names per kernel, BCC tool names per distribution (`-bpfcc` suffix), NVIDIA RDMA capture tool names and syntax per MLNX_OFED/DOCA version, `kubectl debug`/ksniff availability, and Wireshark RoCE dissector field names; all labs are **untested**.
