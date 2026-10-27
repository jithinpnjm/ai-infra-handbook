---
id: "c02-24"
title: "2.24 Linux networking III: policy routing, VRF, bonding, MTU, NIC and stack tuning"
sidebar_label: "2.24 Linux networking III: policy routing, VRF, bonding, MTU, NIC and stack tuning"
sidebar_position: 24
description: "Policy routing, VRF, bonding operations, MTU design, NIC tuning (rings, RSS, IRQ, offloads), TCP stack tuning and kernel bypass"
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 2.24 Linux networking III: policy routing, VRF, bonding, MTU, NIC and stack tuning

| | |
|---|---|
| Level | Advanced |
| Priority tier | 0 |
| Lab venue | Linux VMs / namespaces; NIC tuning needs real hardware |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

A GPU server is a multi-homed machine with several NICs on several networks (management, front-end, storage, compute rails), a 100 to 800 Gb/s capability that a default Linux configuration will not deliver, and workloads (collective communication, checkpoint writes, dataset reads) that expose every inefficiency in the packet path. Getting the last 50% of bandwidth and the last 50 microseconds of latency means understanding how packets leave and enter the host: which routing table is consulted for which source address, how interrupts and queues map to cores and NUMA nodes, which offloads are on, how big the rings and buffers are, what the MTU is end to end, and which TCP knobs matter. The same knowledge diagnoses classic failures: replies leaving the wrong NIC, a single core pegged in softirq, drops at the NIC ring that never reach `tcpdump`, a 100G link delivering 25G to one flow, or a stack tuned for the wrong round-trip time. This chapter covers policy routing and VRFs, bonding operations, MTU design, NIC and kernel tuning, congestion control and buffers, and kernel-bypass options, with a method for tuning safely.

## Prerequisites and outcomes

You should know routing on a host (2.5), TCP (2.6), `ip`/`ethtool`/counters (2.22), netfilter (2.23) and LAG/ECMP (2.12).

After this chapter you can:

- Build and verify source-based, mark-based and interface-based policy routing; fix asymmetric routing on multi-homed servers; persist rules in Netplan/NetworkManager/networkd.
- Use VRFs for L3 isolation on Linux, run processes inside a VRF, and leak routes where needed.
- Operate and troubleshoot Linux bonds (modes, LACP state, hash policy, failover tests) and decide where bonding is the wrong tool (compute rails).
- Design MTU end to end (jumbo, overlays, MSS clamping), verify with DF pings, and persist it.
- Trace the receive and transmit paths (NIC, DMA, ring, hardirq, NAPI/softirq, XDP, skb, tc, netfilter, socket) and tune each stage: ring sizes, interrupt coalescing, RSS/RPS/RFS/XPS, IRQ affinity, NUMA locality, offloads (TSO, GSO, GRO, LRO), PCIe.
- Tune the TCP/IP stack: buffers, backlogs, congestion control and qdisc, TIME_WAIT/ports, keepalives, window scaling/SACK/timestamps, conntrack, busy polling and zero-copy; justify each change with measurement.
- Choose among kernel-stack, XDP/eBPF, SR-IOV, DPDK and RDMA data paths.
- Apply a tuning methodology (baseline, one change, measure, revert) and a safe rollout.

## 1. Policy routing

Standard Linux routing consults the table by **destination** (chapter 2.5). **Policy-based routing (PBR)** adds selectors: the kernel first evaluates a prioritised list of **rules** (`ip rule`) that choose *which routing table* to use based on source address, destination, input interface, TOS/DSCP, fwmark, UID/GID range, IP protocol and ports, and then does the longest-prefix lookup in that table.

```bash
ip rule show
# 0:      from all lookup local
# 32766:  from all lookup main
# 32767:  from all lookup default
cat /etc/iproute2/rt_tables              # name ↔ number map for tables (255 local, 254 main, 253 default) ; add your own
```

Rule fields: `from`, `to`, `iif`, `oif`, `tos`, `fwmark`, `uidrange`, `ipproto`, `sport`, `dport`; actions: `lookup <table>`, `blackhole`, `unreachable`, `prohibit`, `goto`; `priority N` (lower evaluated first). Rules are evaluated in order until one yields a route.

### Fixing multi-homed asymmetric routing

A server has `eth0` 10.0.0.5/24 (default gateway 10.0.0.1) and `eth1` 192.168.1.5/24 (storage; its gateway 192.168.1.1 reaches other storage subnets). A client from a remote storage subnet connects to 192.168.1.5; the request arrives on `eth1`, but the reply is routed by destination: the main table's default route points out `eth0` with source 192.168.1.5. The upstream router at 10.0.0.1 sees a packet from 192.168.1.5 on the wrong VLAN and drops it (unicast reverse path forwarding), or the client drops a reply that arrives from an unexpected path. Fix by giving each NIC its own routing table and selecting it by **source address**:

```bash
echo "200 storage" | sudo tee -a /etc/iproute2/rt_tables
sudo ip route add 192.168.1.0/24 dev eth1 src 192.168.1.5 table storage          # connected route in the table
sudo ip route add default via 192.168.1.1 dev eth1 table storage                  # that table's own default
sudo ip rule add from 192.168.1.5/32 lookup storage priority 1000
ip route get 10.50.0.9 from 192.168.1.5 iif lo          # verify: shows via 192.168.1.1 dev eth1
```

Also: set `rp_filter` to loose (2) or 0 for multi-NIC servers (chapter 2.5), and configure `arp_ignore=1`/`arp_announce=2` so each NIC answers ARP only for its own addresses. For **one table per rail** on a GPU node with eight NICs, script the table and rule creation from inventory (table = 100 + rail index).

### Netplan / NetworkManager / networkd persistence

```yaml
# netplan
network:
  version: 2
  ethernets:
    eth1:
      addresses: [192.168.1.5/24]
      routes:
        - to: default
          via: 192.168.1.1
          table: 200
        - to: 192.168.1.0/24
          scope: link
          table: 200
      routing-policy:
        - from: 192.168.1.5
          table: 200
          priority: 1000
```

```bash
# NetworkManager
nmcli connection modify eth1 ipv4.routes "0.0.0.0/0 192.168.1.1 table=200" ipv4.routing-rules "priority 1000 from 192.168.1.5 table 200"
# systemd-networkd:  [RoutingPolicyRule] From=192.168.1.5  Table=200  Priority=1000   and   [Route] Gateway=... Table=200
```

### fwmark-based and UID-based routing

Mark packets with netfilter/nftables (or `SO_MARK` in the application), then select a table by mark. Uses: send traffic from a particular process/container/user through a VPN or a specific uplink, steer storage traffic to a dedicated NIC, implement transparent proxies.

```bash
sudo nft add table inet mangle_t
sudo nft 'add chain inet mangle_t out { type route hook output priority mangle; }'
sudo nft add rule inet mangle_t out meta skuid 1001 meta mark set 0x64     # all packets of uid 1001 get mark 100
sudo ip rule add fwmark 0x64 lookup 100 priority 900
sudo ip rule add uidrange 1001-1001 lookup 100 priority 910              # alternative without marking
```

(`type route` chains re-run the routing decision after the mark is set; a `filter` hook in output would not re-route.) The routing cache no longer exists in modern kernels, so rule changes take effect for new lookups immediately; `ip route flush cache` is a no-op. `ip route get ... mark 0x64 uid 1001 from <src> iif <dev>` simulates the lookup.

### Common PBR patterns in clusters

| Use | Rule | Notes |
|---|---|---|
| Per-NIC replies (storage, rails) | `from <nic ip> lookup <table>` | Each NIC has its own default and connected routes |
| Per-tenant/VRF | `iif <dev> lookup <table>` or VRF device | Combine with namespaces |
| Egress through proxy/VPN | `fwmark` / `uidrange` | Per-process egress policy |
| Kubernetes pods with multiple NICs (Multus) | Pod-level rules in the pod namespace | Each secondary interface needs return routes |
| Source-specific routing for IPv6 | `from <prefix> lookup <table>` | Multi-prefix hosts (SADR) |
| Blackhole abuse sources | `from <addr> blackhole` | Cheap emergency block |

## 2. VRF on Linux

A **VRF** (virtual routing and forwarding) device gives a group of interfaces their own routing table, isolated from the default one, lighter than a network namespace (processes still share sockets, files, and other stack state). They are central to multi-tenant leaf switches (Cumulus/SONiC-like) and useful on hosts.

```bash
sudo ip link add vrf-blue type vrf table 10
sudo ip link set vrf-blue up
sudo ip link set eth2 master vrf-blue ; sudo ip addr add 10.9.0.5/24 dev eth2 ; sudo ip link set eth2 up
ip -br link show type vrf ; ip -vrf vrf-blue route show ; ip vrf show
sudo ip vrf exec vrf-blue ping 10.9.0.1               # run a command bound to the VRF (sockets bound via SO_BINDTODEVICE)
sudo ip vrf exec vrf-blue ssh 10.9.0.9
ss -tn --vrf vrf-blue ; ss -tlnp   # services: sysctl net.ipv4.tcp_l3mdev_accept=1 lets one listener accept in any VRF
```

Route leaking between VRFs: `ip route add 10.9.0.0/24 dev vrf-blue table main` style entries or a veth pair connecting VRFs (`ip link add v1 type veth peer name v2`; place each end in a different VRF), or BGP route targets in FRR (chapter 2.17). Caveats: services must be started inside the VRF or be VRF-aware (`tcp_l3mdev_accept`, `udp_l3mdev_accept`, `ip vrf exec`), DNS and NTP lookups depend on resolvers reachable in the VRF, and `ip route get` needs `oif vrf-blue`.

## 3. Bonding operations

Mode choices and hashing are in chapter 2.12; here is the operational view.

```bash
cat /proc/net/bonding/bond0                       # authoritative state: mode, hash policy, MII status, slaves, aggregator IDs, LACP partner
ip -d link show bond0 ; ip -br link show master bond0
ethtool bond0 ; ethtool ens1f0 ; ethtool ens1f1   # speeds must match
sudo ip link set ens1f0 down ; ping -i 0.1 <peer>  # failover test: count lost pings, then bring it back
tcpdump -ni ens1f0 ether proto 0x8809              # LACPDUs (slow protocols)
watch -n1 "cat /sys/class/net/bond0/bonding/ad_aggregator; cat /sys/class/net/bond0/bonding/slaves"
```

Verification checklist after changes: all slaves in the same **Aggregator ID** with non-zero **partner MAC**; `lacp_rate fast`; `xmit_hash_policy layer3+4` (or encap variants for tunnels); `min_links` set; MTU identical on bond and slaves (set on the bond; slaves inherit); `miimon 100`; the switch shows the port-channel up with all members `bundled`; a throughput test with many flows shows traffic on all members (`sar -n DEV 1` or `ip -s link`); a failover test (pull cables, reboot a switch) meets the recovery objective.

**Bonding and RDMA**: one RDMA flow (one queue pair) cannot be split across two links by LACP; for compute fabrics use **independent rails** (each NIC its own IP/subnet) and let NCCL/MPI stripe across NICs; some NICs offer **hardware LAG** (mlx5 `lag_mode`) that keeps RoCE working across a bond for the management/storage plane. Never bond the GPU compute rails.

## 4. MTU design

MTU must be a deliberate, **end-to-end consistent** property of each network, and every device on a layer-2 segment must agree: hosts, switch ports, VLAN interfaces, bonds, bridges, virtual switches, overlays.

| Network | Typical MTU | Notes |
|---|---|---|
| Management / Internet-facing | 1500 | Default; compatible with everything |
| Storage (NFS, Lustre, object, NVMe/TCP) | 9000 | Fewer packets per byte; needs every hop to support jumbo |
| RoCE compute fabric | 9000 on Ethernet, RDMA MTU 4096 | Eth headers + 4096 payload fits; configured per NIC (`ibv_devinfo` active_mtu) |
| Overlays (VXLAN/Geneve) | underlay − 50 (e.g. 8950/9000 or 1450/1500) | Chapter 2.17 |
| Kubernetes pod network | node MTU − overlay overhead | CNI config; mismatches cause "small works, large hangs" |
| Cloud VPC | cloud-specific (e.g. 1460 GCP default, configurable; 9001 AWS inside VPC) | Check per path |

```bash
sudo ip link set eth1 mtu 9000                                  # runtime
ip -d link show eth1 | grep mtu ; cat /sys/class/net/eth1/mtu
ping -M do -s 8972 -c 3 <peer>                                  # 9000 − 28 bytes of IP/ICMP header
tracepath -n <peer>                                             # discovers the path MTU hop by hop
# persistence: netplan 'mtu: 9000', nmcli 802-3-ethernet.mtu 9000, networkd [Link] MTUBytes=9000
sudo iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu     # MSS clamping on gateways
sysctl net.ipv4.tcp_mtu_probing                                 # 1: probe after black-hole detection ; 2: always probe
```

Remember TCP MSS derives from interface MTU (1460/8960), UDP applications may fragment (avoid), PMTUD needs ICMP (chapter 2.7), and offloads (TSO/GSO/GRO) mean the stack handles 64 KB super-packets that are segmented at the NIC, so a captured packet can be larger than the MTU. Throughput gain from jumbo frames is smaller on offload-capable NICs but CPU and interrupt cost still drop; 9000 is the usual choice for storage and RoCE.

## 5. The packet path and where to tune it

```mermaid
flowchart TD
  W["Wire → NIC PHY/MAC (FCS check, RSS hash, flow steering)"] --> D["DMA into RX ring (host RAM)"]
  D --> H["Hard IRQ (per queue, MSI-X) → NAPI scheduled"]
  H --> S["NET_RX softirq: driver poll() up to netdev_budget packets"]
  S --> X["XDP program (optional, before skb)"]
  X --> B["Build sk_buff, GRO merge, RPS (optional steering to other CPUs)"]
  B --> T["tc ingress → netfilter prerouting → routing"]
  T --> L["Local: netfilter input → TCP/UDP → socket receive buffer"]
  L --> A["Application wakeup (epoll) → copy_to_user"]
  A -. "TX path" .-> Q["send() → socket send buffer → TCP segmentation (TSO/GSO) → qdisc (fq/pacing) → driver TX ring → DMA → wire (XPS selects queue)"]
```

### 5.1 Know the limits first (static tuning)

Before changing anything, record: NIC model/firmware/driver; link speed and FEC; PCIe generation/width and the NUMA node of the NIC (`cat /sys/class/net/eth0/device/numa_node`, `lspci -vv -s <bus> | grep -E 'LnkSta|LnkCap'`, `nvidia-smi topo -m` for GPU-NIC affinity); CPU model, core count per NUMA node, SMT; kernel version; current ring sizes/coalescing/offloads/queues; IRQ distribution; firewall rules; MTU; congestion control; and the workload (flows, packet sizes, request rates). A PCIe Gen4 x16 slot (about 252 Gb/s usable) caps a 400G NIC; a NIC on the remote NUMA node adds latency and halves bandwidth because traffic crosses the inter-socket link.

### 5.2 Rings, interrupts and coalescing

```bash
ethtool -g eth0                        # ring sizes: RX/TX current and pre-set maximums
sudo ethtool -G eth0 rx 4096 tx 4096   # bigger rings absorb microbursts (costs memory and latency under overload)
ethtool -c eth0 ; sudo ethtool -C eth0 adaptive-rx on adaptive-tx on      # or fixed: rx-usecs 50 rx-frames 20
```

Bigger rings reduce `rx_missed`/`rx_out_of_buffer` drops when the CPU cannot poll fast enough; they do not fix a permanently overloaded CPU. **Interrupt coalescing** delays interrupts to batch packets: lower CPU use and higher throughput at the cost of latency. Throughput/storage NICs: adaptive or moderate coalescing; latency-critical NICs (kernel-path MPI/NCCL sockets, trading): minimal or none (RDMA NICs bypass this entirely). Verify with `/proc/interrupts` rates and `sar -I` while testing.

### 5.3 Queues, RSS, RPS, RFS, XPS

A single core cannot process 100 Gb/s; traffic must be spread over many queues and cores while keeping each flow on one core (ordering and cache locality).

- **RSS (receive-side scaling, hardware)**: the NIC hashes packet fields (Toeplitz over IPs and ports) to select one of N receive queues, each with its own interrupt. `ethtool -l eth0` (channels), `sudo ethtool -L eth0 combined 32`, `ethtool -x eth0` (indirection table and hash key), `sudo ethtool -X eth0 equal 32`, hash fields via `ethtool -N eth0 rx-flow-hash tcp4 sdfn`. Set queues to the number of cores on the **NIC's NUMA node** (not necessarily all cores). Note that overlay traffic (VXLAN) hashes only on the outer headers unless the NIC supports inner-header RSS.
- **IRQ affinity**: each queue's IRQ should run on a core local to the NIC. `grep eth0 /proc/interrupts`, `cat /proc/irq/<n>/smp_affinity_list`, `echo <cpu> | sudo tee /proc/irq/<n>/smp_affinity_list`; vendor scripts (`set_irq_affinity_bynode.sh <node> eth0`, `mlnx_affinity`) do this; stop `irqbalance` (or exclude the NIC) when pinning manually; align with the application's CPU placement (the thread that consumes the data should ideally run on the same NUMA node/cache domain).
- **RPS (receive packet steering, software)**: spreads packet processing after the interrupt to other CPUs when the NIC lacks enough queues (`echo ffff > /sys/class/net/eth0/queues/rx-0/rps_cpus`; `net.core.rps_sock_flow_entries`); **RFS** steers packets toward the CPU where the consuming application thread runs (`/sys/class/net/eth0/queues/rx-0/rps_flow_cnt`); **aRFS** does the same in hardware. Useful on virtual NICs and single-queue devices; modern multi-queue NICs usually rely on RSS.
- **XPS (transmit packet steering)**: maps CPUs to TX queues (`/sys/class/net/eth0/queues/tx-0/xps_cpus`) to avoid lock contention and cross-NUMA transmits.
- **Verification**: `mpstat -P ALL 1` (are `%soft` and `%irq` spread, or is one core at 100%?), `perf top`, `/proc/softirqs` NET_RX per CPU, `ethtool -S eth0 | grep -E 'rx_queue_.*_packets'` (per-queue balance), `cat /proc/net/softnet_stat` (drops, squeezes).

### 5.4 Offloads

| Offload | What | Notes |
|---|---|---|
| **Checksum offload** (rx/tx) | NIC computes/validates L4 checksums | Capture on the sender shows "bad cksum" (benign) |
| **TSO / GSO** | Send 64 KB buffers; NIC (TSO) or kernel late (GSO) segments into MTU-sized frames | Big CPU saver; enable |
| **GRO** | Merge received packets of a flow into larger skbs before the stack | Big CPU saver; may hurt forwarding/bridges/latency; disable on routers/VXLAN gateways (use `rx-gro-hw`/`gro` per case) |
| **LRO** | Hardware merge on receive | Breaks forwarding (headers lost); avoid on routers/bridges/hypervisors |
| **Tunnel segmentation** (`tx-udp_tnl-segmentation`), VLAN offload, `rx-vlan-offload` | Offload for VXLAN/Geneve and VLAN tags | Check with `ethtool -k` |
| **Scatter-gather, TX checksum, rxhash** | Zero-copy-ish transmit; hardware hash | Keep on |
| **Flow control (802.3x pause)** | Link-level pause | Usually off in modern DCs; PFC instead (chapter 2.19) |
| **TLS/IPsec/MACsec offload** | NIC encrypts | Reduces CPU for encrypted traffic (kTLS, ESP) |

```bash
ethtool -k eth0 | egrep 'rx-checksumming|tx-checksumming|scatter-gather|tcp-segmentation|generic-segmentation|generic-receive|large-receive|rx-vlan|tx-udp_tnl|hw-tc-offload'
sudo ethtool -K eth0 tso on gso on gro on lro off
```

### 5.5 Kernel queues, budget and backlog

```bash
sysctl net.core.netdev_budget net.core.netdev_budget_usecs net.core.netdev_max_backlog net.core.dev_weight
sudo sysctl -w net.core.netdev_budget=600 net.core.netdev_max_backlog=10000     # more work per softirq, bigger per-CPU backlog (RPS)
cat /proc/net/softnet_stat       # col2 drops (backlog overflow), col3 time_squeeze (budget exhausted) → raise budget or add queues
```

If `time_squeeze` increases, softirq is cut off before draining the ring: raise `netdev_budget`(`_usecs`) or spread load. If `dropped` increases, the per-CPU backlog queue (RPS path) overflowed. If the ring itself overflows (`rx_missed`), the CPU isn't polling fast enough: more queues/cores, bigger ring, fewer per-packet costs (disable expensive netfilter, use XDP).

### 5.6 Busy polling and low latency

`net.core.busy_poll`/`busy_read` (microseconds) let sockets spin-poll the NIC queue instead of sleeping, trading CPU for microseconds of latency; `SO_BUSY_POLL`/`epoll` busy poll per socket; isolate cores (`isolcpus`, `nohz_full`, `rcu_nocbs`), disable C-states (`tuned` profile `network-latency`, `intel_idle.max_cstate=1`), set CPU governor `performance`, and use `tuned-adm profile network-throughput|network-latency` as a baseline. For microsecond-class work use RDMA or DPDK instead.

## 6. TCP/IP stack tuning

Rule: **measure first**; most defaults are sane and the stack autotunes. Tune for your bandwidth-delay product, connection rates and memory (chapter 2.6 explains the mechanisms).

| Goal | Settings (starting points; validate) |
|---|---|
| Long-fat-pipe throughput | `net.core.rmem_max/wmem_max=134217728`, `net.ipv4.tcp_rmem="4096 131072 134217728"`, `tcp_wmem="4096 65536 134217728"`, `tcp_window_scaling=1`, `tcp_sack=1`, `tcp_timestamps=1`, `tcp_moderate_rcvbuf=1` |
| Short-RTT DC 100G | Buffers 16 to 64 MB max; keep defaults for min/default; avoid huge defaults that waste memory |
| Congestion control + pacing | `net.core.default_qdisc=fq`, `net.ipv4.tcp_congestion_control=bbr` (WAN/edge) or `cubic` (default), DCTCP+ECN in controlled fabrics (`tcp_ecn=1`) |
| Accept bursts | `net.core.somaxconn=4096..65535`, `tcp_max_syn_backlog=8192`, application backlog; `tcp_syncookies=1` |
| Many outbound connections / NCCL bootstrap | `ip_local_port_range="10240 65535"` (or a dedicated range such as `net.ipv4.ip_local_port_range="50000 51000"` in `/etc/sysctl.conf` / `/proc/sys/net/ipv4/ip_local_port_range` paired with `NCCL_SOCKET_IFNAME` and `MASTER_PORT` to prevent TCP port exhaustion during `NCCL` out-of-band bootstrap handshakes; for socket/TCP transport paths, `NCCL_NSOCKS_PERTHREAD` × `NCCL_SOCKET_NTHREADS` cannot exceed `64` sockets total per communicator), `tcp_tw_reuse=1`, connection pooling, spread over destination addresses |
| Idle connection hygiene | `tcp_keepalive_time/intvl/probes` (e.g. 300/30/5), `tcp_slow_start_after_idle=0` for persistent bursty connections |
| Fail-fast clients | `tcp_syn_retries=2..3`, `tcp_retries2` lower (e.g. 8) for dead peer detection, `TCP_USER_TIMEOUT` per socket |
| PMTUD black holes | `tcp_mtu_probing=1` |
| Low latency | `tcp_notsent_lowat=131072`, `TCP_NODELAY`, `tcp_low_latency` obsolete; busy poll |
| UDP receivers (StatsD, syslog, telemetry) | `rmem_max` larger, `SO_RCVBUF`, `net.core.netdev_max_backlog`, `net.ipv4.udp_mem`; watch `UdpRcvbufErrors` |
| Conntrack | `nf_conntrack_max`, hashsize, timeouts (chapter 2.23) |
| Forwarding / multi-homing | `ip_forward=1` (only where needed), `rp_filter=2`, `arp_ignore=1`, `arp_announce=2`, `accept_redirects=0` |
| File descriptors | `fs.file-max`, `ulimit -n` (LimitNOFILE) for servers with many sockets |

An example AI-node sysctl baseline (start point only; the originals in the source repository carry the same caveat):

```ini
# /etc/sysctl.d/99-ai-node-network.conf
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr          # use cubic inside the DC if BBR shows unfairness or retransmit issues
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 131072 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 10000
net.core.netdev_budget = 600
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_syncookies = 1
net.ipv4.ip_local_port_range = 10240 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_mtu_probing = 1
net.ipv4.conf.all.rp_filter = 2
net.ipv4.conf.default.rp_filter = 2
net.netfilter.nf_conntrack_max = 2097152         # only if nf_conntrack is loaded
net.netfilter.nf_conntrack_tcp_timeout_established = 3600
```

Production example from the literature (a large streaming operator): `default_qdisc=fq`, `netdev_max_backlog=5000`, `rmem_max/wmem_max=16 MB`, `somaxconn=1024`, `ip_local_port_range=10240 65535`, `tcp_abort_on_overflow=1`, `tcp_congestion_control=bbr`, `tcp_max_syn_backlog=8192`, `tcp_rmem/wmem="4096 12582912 16777216"`, `tcp_slow_start_after_idle=0`, `tcp_syn_retries=2`, `tcp_tw_reuse=1`: fourteen settings, not a recipe, and some values were being revised after regression testing. Lesson: small, evidence-based sets beat 200-line cargo-cult files.

### Socket options (per application)

`SO_RCVBUF`/`SO_SNDBUF` (disables autotuning if set: avoid), `TCP_NODELAY`, `TCP_CORK`/`MSG_MORE`, `TCP_QUICKACK`, `SO_KEEPALIVE` + `TCP_KEEPIDLE/INTVL/CNT`, `TCP_USER_TIMEOUT`, `TCP_CONGESTION` (per socket algorithm), `SO_REUSEPORT` (multi-process listeners with kernel load balancing), `SO_BUSY_POLL`, `SO_MAX_PACING_RATE`, `MSG_ZEROCOPY` and `sendfile()`/`splice()` (avoid user-space copies: a static file is DMAed from the page cache to the NIC with no CPU copy, saving two copies and context switches), `SO_INCOMING_CPU`. Application servers should set these deliberately rather than rely on system-wide changes.

### Qdisc and pacing

Default `fq_codel`/`mq` is fine for most hosts. `fq` provides per-flow pacing (required by BBR on older kernels and useful with `SO_MAX_PACING_RATE`), `mq` creates one qdisc per TX queue to avoid lock contention. Check drops/requeues with `tc -s qdisc show dev eth0`. Heavy shaping (`htb`) on 100G links is CPU intensive; prefer NIC rate limits or switch policing.

## 7. Beyond the kernel stack

| Technology | Idea | When |
|---|---|---|
| **XDP** (eXpress Data Path) | eBPF program in the driver before skb allocation; verdicts PASS/DROP/TX/REDIRECT | DDoS drop at millions of pps, load balancers (Katran), custom forwarding, telemetry |
| **AF_XDP** | Zero-copy path from XDP to user space | High-rate packet apps without full DPDK |
| **eBPF/TC (Cilium)** | Policy and load balancing at tc hooks, skipping netfilter and shortcutting pod-to-pod | Kubernetes at scale |
| **SR-IOV** | NIC exposes Virtual Functions passed into VMs/containers | Near-native NIC performance for pods/VMs; loses host policy visibility and live migration (`echo 4 > /sys/class/net/<pf>/device/sriov_numvfs`) |
| **DPDK** | User-space poll-mode drivers on dedicated cores | Virtual routers, UPF, vSwitches; 100% CPU always; own TCP stack |
| **RDMA (RoCE/IB)** | NIC does transport; kernel bypass; zero copy | GPU collectives, storage (NVMe-oF, Lustre, GPUDirect), see Part 11 |
| **io_uring / kTLS** | Async syscalls batching; TLS in kernel/NIC | Efficient servers |

**veth cost**: container traffic crossing veth pairs and bridges is processed in softirq context of the sending CPU; a single flow can saturate one core (~15 Gb/s class in some kernels/configs). Remedies: host networking for heavy pods, ipvlan/macvlan, SR-IOV, eBPF host routing (Cilium), or RDMA via Multus secondary networks. Kubernetes Topology Manager and CPU Manager can align pod CPUs, NIC VFs and GPUs on the same NUMA node.

## 8. A safe tuning method

1. **Define the goal and metric** (e.g. 8×400G all-reduce bandwidth ≥ 90% of line rate; p99 RPC latency; zero drops at 99th percentile load).
2. **Baseline** with representative tests (`iperf3 -P 16`, `nccl-tests`, `ib_write_bw`, application benchmark) and record configuration (`ethtool -k/-g/-c/-l`, sysctl dump, IRQ map, CPU/NUMA, versions).
3. **Locate the bottleneck** with USE and counters (chapter 2.22): link speed, PCIe, NIC drops, softirq CPU, socket buffers, application CPU.
4. **Change one thing**, measure again with the same test, keep or revert; record the delta.
5. **Prefer structural fixes** (NUMA alignment, more queues, correct MTU, remove conntrack, bypass) over sysctl lore.
6. **Roll out via configuration management** with canaries, persistent files (`/etc/sysctl.d`, udev rules or systemd units for ethtool/IRQ settings), and an audit script that compares actual to intended values (chapter 1.28).
7. **Re-validate** after kernel, driver, firmware or workload changes.

Persisting ethtool/IRQ settings: a `systemd` unit or udev rule or NetworkManager dispatcher/networkd `[Link]` section, e.g. `/etc/systemd/network/10-eth0.link` with `[Link] RxBufferSize=4096 TxBufferSize=4096 GenericReceiveOffload=yes`, or `ethtool` calls in a oneshot unit after `network-online.target`.

## 9. Scenarios

1. **Single flow delivers 25 Gb/s on a 100G link.** Check: one TCP flow is bounded by one core and window/RTT (use `iperf3 -P 8`); softirq on one core (`mpstat`), RSS collisions, GRO off, buffers too small for RTT, MTU 1500 vs 9000, PCIe slot width, NUMA mismatch. Resolution: parallel streams, more queues and correct IRQ pinning, jumbo frames, BDP buffers, local NUMA node.
2. **Drops before `tcpdump` sees them.** `ethtool -S` shows `rx_missed`/`rx_out_of_buffer`: ring overflow. Increase rings, add queues, fix IRQ pinning, shed per-packet overhead.
3. **Softirq saturation on one core** from veth or a single-queue virtual NIC: RPS/RFS, multiqueue virtio (`ethtool -L`), host networking/SR-IOV for hot pods.
4. **Replies leave on the wrong NIC.** Policy routing (section 1).
5. **Jumbo frames partly working.** One hop at 1500; `ping -M do -s 8972` fails; fix MTU consistently, clamp MSS, permit ICMP.
6. **Outbound connection failures at high rates or stalled `NCCL` bootstrap handshakes.** Ephemeral port range too narrow (`net.ipv4.ip_local_port_range` in `/etc/sysctl.conf`, e.g., `"50000 51000"` in the book's example, or `"10240 65535"`, plus explicit `MASTER_PORT` and `NCCL_SOCKET_IFNAME=ib0` so bootstrap handshakes do not land on `eth0`, `docker0`, or `lo`), TIME_WAIT, SNAT exhaustion, conntrack full: pooling, `tcp_tw_reuse`, more source IPs. When tuning `NCCL` socket transport across multiple NICs, `NCCL_NSOCKS_PERTHREAD` × `NCCL_SOCKET_NTHREADS` must not exceed `64` sockets total per communicator.
7. **UDP telemetry loss (StatsD/syslog).** `UdpRcvbufErrors`: raise `rmem_max`, set `SO_RCVBUF`, scale receivers with `SO_REUSEPORT`, check `netdev_max_backlog`.
8. **Latency spikes at idle then burst.** Coalescing and C-states: lower coalescing, `tuned network-latency`, busy poll, pin cores.
9. **Asymmetric ECMP reorder.** Hosts with BGP to two ToRs reorder if paths differ; use consistent hashing and avoid per-packet balancing.
10. **Bond up, throughput low.** Single flow pinned to one member; hash policy `layer2`; use `layer3+4` or multi-flow tests.

## 10. Hands-on lab: policy routing and tuning

First, run the self-checking Python lab (`code/part02/linux_stack_nic_tuning_lab.py`) locally. It verifies NUMA-local RSS queue and IRQ CPU affinity planning (`plan_numa_local_rss_and_irq`), `NCCL` socket-transport limits (`NCCL_NSOCKS_PERTHREAD * NCCL_SOCKET_NTHREADS <= 64`) and bootstrap ephemeral port validation, and BDP-based `rmem_max`/`wmem_max` socket buffer sizing (`16 MiB` vs `128 MiB`).

```bash
python3 code/part02/linux_stack_nic_tuning_lab.py
```

Next, on a disposable Linux VM with `root` (and optional bare-metal NIC hardware for Step 6; all interactive VM commands below are `untested here`), work through these steps:

1. **Multi-homed asymmetric fix**: build two NIC namespaces (a server with `eth0`/`eth1` on different subnets via veths to two routers), reproduce reply-on-wrong-NIC drops with `rp_filter=1` or an upstream uRPF rule, fix with rules/tables; verify with `ip route get ... from ...` and tcpdump.
2. **fwmark/uid routing**: mark a user's traffic and route it through another gateway namespace; confirm with `traceroute`.
3. **VRF**: two VRFs on one namespace with overlapping 10.9.0.0/24 networks; run `ip vrf exec` pings; leak a route via veth.
4. **Bond failover test**: create a bond of two veth pairs between namespaces; measure failover time with `miimon` 100 vs 1000; inspect `/proc/net/bonding`; try `layer2` vs `layer3+4` with many flows.
5. **MTU ladder**: set MTU 9000 on one side, 1500 on a router; show hang; fix with MSS clamp, MTU, ICMP allowed; verify `ping -M do -s 8972`.
6. **Ring/IRQ/RSS experiments (hardware)**: baseline `iperf3 -P 16` on a 25/100G NIC; change queue count, IRQ affinity (local vs remote NUMA), ring sizes, coalescing, GRO/TSO; record throughput and `mpstat` to see each effect.
7. **XDP drop**: attach a small `xdp_drop` program (BCC/libbpf-tools or `ip link set dev eth0 xdp obj ...`) and compare drop rate vs an nft rule using `pktgen`/`hping3` flood on a lab link.
8. **sysctl baseline**: apply the baseline file on a VM, benchmark before/after on a high-BDP emulated path (`tc netem delay 40ms`), and revert one setting at a time to attribute gains.
9. **Zero copy**: compare `sendfile` vs `read/write` file serving (`nginx sendfile on/off`, `wrk`) CPU usage.
10. **Clean up.**

## 11. Common mistakes

- Pasting 100-line sysctl "AI/HPC tuning" files without measurement; setting `SO_RCVBUF` explicitly (kills autotuning).
- Setting MTU on hosts but not on every switch port/bond/VLAN/overlay.
- Pinning IRQs to the wrong NUMA node, or leaving `irqbalance` to undo manual pinning.
- Turning on LRO on a router/bridge/hypervisor; disabling GRO/TSO globally to "fix" captures.
- Tuning a 25G flow problem by changing congestion control when the issue is single-core softirq.
- Forgetting persistence: ethtool/IRQ settings lost at reboot or driver reload.
- Strict `rp_filter` on multi-homed hosts; missing source-based routing.
- Benchmarking with one flow or on loopback and extrapolating.
- Ignoring PCIe/NUMA topology of NIC and GPU.

## 12. Interview angles

- "A multi-homed server answers on the wrong interface. Why and how do you fix it?"
- "Explain `ip rule` vs routing tables vs VRFs vs namespaces."
- "Walk the receive path of a packet from the wire to the application and where drops can occur."
- "How do RSS, IRQ affinity, RPS and RFS differ?"
- "TSO, GSO, GRO, LRO: what are they, when to disable?"
- "A single TCP stream only reaches 25 Gb/s on a 100G NIC. What do you check?"
- "How would you tune a server for long-distance bulk transfers? For low-latency RPC?"
- "Why shouldn't you bond RDMA compute NICs?"
- "What are XDP, AF_XDP, DPDK and SR-IOV and when would you use each?"
- "How do you make tuning changes safe and repeatable?"

## Exercises

1. **Policy-Based Routing (`ip rule`), `fwmark`/`uidrange`, and Linux `VRF`s:** (a) Write the `ip route` and `ip rule` commands (plus Netplan persistence) to fix asymmetric routing on a server with `eth0` (`10.0.0.5/24`, gw `10.0.0.1`) and storage NIC `eth1` (`192.168.1.5/24`, gw `192.168.1.1`, table `200 storage`), and explain why `nft` `type route hook output` is required when marking packets with `meta mark set 0x64` for `fwmark` routing; (b) contrast a Linux **VRF** (`ip link add vrf-blue type vrf table 10`, `ip vrf exec`) with a network namespace.
2. **Bonding Operations and End-to-End `MTU` Design:** (a) List the 7-item operational verification checklist for a Linux `802.3ad` LACP bond (`/proc/net/bonding/bond0`) and explain why GPU compute rails are never bonded; (b) compare the standard MTU values for management (`1500`), storage (`9000`), RoCEv2 (`9000` Ethernet / `4096` IB MTU), and VXLAN overlays (`underlay - 50`), and write the `ping -M do` verification command.
3. **The Linux RX/TX Packet Path: Rings, Coalescing, `NAPI`, `RSS`/`RPS`/`RFS`/`XPS`, and `NUMA` IRQ Affinity:** (a) Trace the receive path from the wire to `copy_to_user` (`Wire -> DMA RX ring -> MSI-X Hard IRQ -> NAPI NET_RX softirq -> XDP -> sk_buff/GRO/RPS -> tc/netfilter/routing -> socket buffer`); (b) using `plan_numa_local_rss_and_irq()` in `code/part02/linux_stack_nic_tuning.py`, explain how to size RSS queues (`ethtool -L`) and pin IRQs (`smp_affinity_list`) to the NIC's local NUMA node (`/sys/class/net/<dev>/device/numa_node`).
4. **Hardware Offloads (`TSO`, `GSO`, `GRO`, `LRO`) and Zero-Copy Syscalls (`sendfile`, `MSG_ZEROCOPY`):** Contrast `TSO`, `GSO`, `GRO`, and `LRO`, explain why `LRO` must be disabled on routers, bridges, and hypervisors, and explain how `sendfile()` and `MSG_ZEROCOPY` save CPU cycles and memory bandwidth when serving large files or checkpoints.
5. **TCP/IP Stack `sysctl` Tuning and `NCCL` Socket/Bootstrap Configuration (`ASP` Chapter 4 & `SP` Chapter 10):** (a) Using `recommend_tcp_max_buffer_bytes()`, compare the recommended `rmem_max`/`wmem_max` socket buffer ceiling for a `100 Gb/s x 0.2 ms` intra-DC path (`16 MiB`) versus a `10 Gb/s x 40 ms` WAN path (`128 MiB`), and explain why applications should not set `SO_RCVBUF` manually; (b) using `validate_nccl_socket_and_port_config()`, validate `NCCL_NSOCKS_PERTHREAD * NCCL_SOCKET_NTHREADS <= 64`, `NCCL_SOCKET_IFNAME`, and `net.ipv4.ip_local_port_range` (`"50000 51000"` or `"10240 65535"`).
6. **Kernel Bypass (`XDP`, `AF_XDP`, `SR-IOV`, `DPDK`, `RDMA`) and the 7-Step Safe Tuning Methodology:** Compare `XDP`, `AF_XDP`, `SR-IOV`, `DPDK`, and `RDMA` (`RoCEv2`/`InfiniBand`), explain why container `veth` pairs can bottleneck a single CPU core in `softirq`, and walk through the 7-step tuning method to diagnose why a single TCP stream reaches only `25 Gb/s` on a `100G` NIC.

## Checkpoint questions (20)

<details>
<summary>1. How does Policy-Based Routing (`ip rule`) extend standard destination-based routing, and what are the three default rules?</summary>
Before looking up a destination IP in a routing table, the kernel walks the prioritized **`ip rule` list** (lowest priority number first), which can match on **source IP (`from`), destination IP (`to`), incoming interface (`iif`), outgoing interface (`oif`), `tos`/`DSCP`, `fwmark`, `uidrange`, IP protocol, and L4 ports (`sport`/`dport`)** to select *which* routing table to query. The three built-in rules are:\n- Priority **`0`**: `from all lookup local` (table `255`, local IPs and broadcast)\n- Priority **`32766`**: `from all lookup main` (table `254`)\n- Priority **`32767`**: `from all lookup default` (table `253`).
</details>

<details>
<summary>2. Walk through the exact commands to fix reply-on-wrong-NIC asymmetric routing for a secondary storage interface `eth1` (`192.168.1.5/24`, gateway `192.168.1.1`).</summary>
(1) Name a dedicated routing table: `echo "200 storage" | sudo tee -a /etc/iproute2/rt_tables`;\n(2) Populate both the connected subnet route and the default gateway inside that table:\n`sudo ip route add 192.168.1.0/24 dev eth1 src 192.168.1.5 table storage`\n`sudo ip route add default via 192.168.1.1 dev eth1 table storage`\n(3) Add a source-based policy rule: `sudo ip rule add from 192.168.1.5/32 lookup storage priority 1000`;\n(4) Set `rp_filter = 2` (loose) and `arp_ignore = 1` / `arp_announce = 2`, and verify with `ip route get 10.50.0.9 from 192.168.1.5 iif lo`.
</details>

<details>
<summary>3. Why must an `nftables` chain that sets a packet mark (`meta mark set 0x64`) for policy routing on locally generated packets use `type route hook output` instead of `type filter hook output`?</summary>
For locally generated packets, the kernel performs the initial routing lookup **before** the `output` hook runs. A standard `type filter hook output` chain can drop or accept the packet, but will **not** re-run the routing lookup if `meta mark` is modified. Declaring the chain as **`type route hook output priority mangle`** instructs the kernel to automatically **re-run the FIB / `ip rule` lookup** whenever the packet's `fwmark` (or IP header) is changed in `output`.
</details>

<details>
<summary>4. How does a Linux `VRF` device (`ip link add vrf-blue type vrf table 10`) differ from a Linux Network Namespace (`ip netns`)?</summary>
A **Network Namespace (`ip netns`)** virtualizes the **entire network stack** (interfaces, loopback, routing tables, `ip rule`s, `nftables`/conntrack, and **all TCP/UDP socket port bindings**), isolating processes cleanly for containers. A **Linux VRF** is a lightweight netdev bound to a specific kernel routing table (`table 10`): interfaces enslaved to `vrf-blue` (`ip link set eth2 master vrf-blue`) use table `10` for L3 routing while **sharing the same host process space, filesystem, and global socket table** (processes run in a VRF via `sudo ip vrf exec vrf-blue <cmd>`, or a single daemon can accept connections across all VRFs when `net.ipv4.tcp_l3mdev_accept = 1`).
</details>

<details>
<summary>5. What are the typical `MTU` settings across the networks of an AI cluster, and why is RoCEv2's RDMA MTU `4096` when the Ethernet interface MTU is `9000`?</summary>
- **Management / Internet**: `1500` bytes;\n- **Storage (`NFS`, `Lustre`, `NVMe/TCP`)**: `9000` bytes;\n- **VXLAN / Geneve overlays**: `underlay_mtu - 50` (`8950` on `9000`, `1450` on `1500`);\n- **RoCEv2 Compute Fabric**: Ethernet interface `MTU = 9000`, InfiniBand/RDMA **`active_mtu = 4096`** (`ibv_devinfo`). The InfiniBand specification defines power-of-two payload MTUs (`256, 512, 1024, 2048, 4096`); a `4096`-byte RDMA payload plus RoCEv2 (`BTH`/`ICRC`), UDP, IP, and Ethernet headers fits comfortably inside a `9000`-byte Ethernet jumbo frame (and allows two 4 KB RDMA packets to coalesce or traverse tunnels without fragmentation).
</details>

<details>
<summary>6. Trace the 8 stages of the Linux kernel Receive (`RX`) path from the physical wire to the user-space application.</summary>
(1) **Wire -> NIC PHY/MAC**: checks FCS CRC, computes Toeplitz **RSS hash**, and selects one of `N` hardware RX queues;\n(2) **DMA to Host RAM**: NIC DMAs the frame into a pre-allocated buffer descriptor in that queue's **RX ring**;\n(3) **Hard IRQ (`MSI-X`)**: NIC raises the queue's CPU interrupt, which disables further hard IRQs on that queue and schedules **NAPI** (`napi_schedule`);\n(4) **`NET_RX_SOFTIRQ` (`net_rx_action`)**: kernel polls the driver (`poll()`) up to `net.core.netdev_budget` packets;\n(5) **`XDP` hook (optional)**: runs eBPF in the driver before allocating an `sk_buff`;\n(6) **`sk_buff` allocation + `GRO` + `RPS`/`RFS`**: builds the `sk_buff`, coalesces same-flow segments via **GRO**, and optionally steers to another CPU;\n(7) **`tc ingress` -> `netfilter prerouting` -> Routing -> `netfilter input` -> TCP/UDP protocol handler**: validates headers/state, sends ACKs, and queues data in the **socket receive buffer**; and\n(8) **Application wakeup (`epoll`) -> `copy_to_user()`**.
</details>

<details>
<summary>7. What is the trade-off when increasing NIC Ring Buffer sizes (`ethtool -G`) and Interrupt Coalescing (`ethtool -C`)?</summary>
- **Larger RX/TX Rings (`ethtool -G eth0 rx 4096 tx 4096`)**: absorb sub-millisecond microbursts without `rx_missed_errors` / `rx_no_buffer` drops while the CPU is briefly busy, at the cost of a larger memory footprint and slightly higher worst-case queueing latency under sustained overload.\n- **Interrupt Coalescing (`ethtool -C eth0 adaptive-rx on` or `rx-usecs 50 rx-frames 20`)**: batches multiple arriving packets into a single hardware interrupt—**reducing CPU interrupt overhead and increasing bulk throughput**, at the cost of **adding microseconds of per-packet latency**. Enable adaptive coalescing on bulk storage/front-end NICs; minimize coalescing on latency-critical sockets.
</details>

<details>
<summary>8. Compare `RSS`, `RPS`, `RFS` (`aRFS`), and `XPS`.</summary>
- **`RSS` (*Receive-Side Scaling*, hardware)**: the NIC hashes the packet's 4-tuple (Toeplitz hash) into one of `N` hardware RX queues, each with its own DMA ring and MSI-X interrupt (`ethtool -l` / `-L`).\n- **`RPS` (*Receive Packet Steering*, software)**: hashes packets in software after the driver interrupt to distribute `sk_buff` protocol processing across multiple CPUs when a NIC has only 1 hardware RX queue (e.g., older virtual NICs).\n- **`RFS` (*Receive Flow Steering*) / `aRFS` (hardware-accelerated)**: steers packets of a flow directly to the **exact CPU core where the application thread calling `recv()` is currently running**, maximizing L1/L2/L3 CPU cache hit rates.\n- **`XPS` (*Transmit Packet Steering*)**: maps each CPU core to a dedicated hardware TX queue (`/sys/class/net/<dev>/queues/tx-*/xps_cpus`) to eliminate cross-core TX lock contention and cross-NUMA DMA reads.
</details>

<details>
<summary>9. Why must a high-speed NIC's `RSS` queues and `IRQ` affinities be pinned strictly to its local `NUMA` node, and how do you check it?</summary>
Every PCIe root complex is physically wired to a specific CPU socket (**NUMA node**, checked via **`cat /sys/class/net/eth0/device/numa_node`** and **`nvidia-smi topo -m`**). If a NIC attached to NUMA Node 1 fires interrupts or DMAs `sk_buff`s to CPU cores on NUMA Node 0, every packet descriptor, `sk_buff`, and payload copy must traverse the inter-socket interconnect (`UPI` / `Infinity Fabric`)—adding latency, wasting interconnect bandwidth, and polluting remote caches. Stop `irqbalance` (or set `IRQBALANCE_BANNED_CPUS`), set RSS queue count (`ethtool -L`) to the core count of the local NUMA node, and pin `/proc/irq/<n>/smp_affinity_list` to local NUMA CPUs.
</details>

<details>
<summary>10. Compare `TSO`, `GSO`, `GRO`, and `LRO`, and explain why `LRO` must be disabled on routers, bridges, and hypervisors.</summary>
- **`TSO` (*TCP Segmentation Offload*)**: the kernel hands a `64 KiB` TCP buffer to the NIC, and the **NIC hardware** slices it into `1460`/`8960`-byte MSS frames on the wire.\n- **`GSO` (*Generic Segmentation Offload*)**: software fallback that delays segmentation in the kernel until right before the driver.\n- **`GRO` (*Generic Receive Offload*)**: lossless software/hardware receive coalescing that merges consecutive segments of the same flow into one `64 KiB` `sk_buff` while preserving enough header metadata to re-segment cleanly if forwarded.\n- **`LRO` (*Large Receive Offload*)**: older hardware receive coalescing that **lossily merges headers** into one giant packet; if enabled on a Linux router, bridge, or hypervisor, forwarded packets lose their original headers/state and break TCP/forwarding (`sudo ethtool -K eth0 lro off`).
</details>

<details>
<summary>11. What do `net.core.netdev_budget`, `netdev_budget_usecs`, and `netdev_max_backlog` tune?</summary>
- **`net.core.netdev_budget` (default `300`, often raised to `600`)** and **`netdev_budget_usecs` (default `2000` µs)**: control the maximum number of packets and microseconds a single `NET_RX_SOFTIRQ` NAPI poll cycle may process before yielding the CPU. Raising them fixes rising **`time_squeeze`** (column 3 of `/proc/net/softnet_stat`).\n- **`net.core.netdev_max_backlog` (default `1000`, often raised to `5000`–`10000`)**: sizes the per-CPU software input queue used by `RPS` and loopback; raising it fixes rising **`dropped`** (column 2 of `/proc/net/softnet_stat`).
</details>

<details>
<summary>12. How do you size `net.core.rmem_max`/`wmem_max` and `net.ipv4.tcp_rmem`/`tcp_wmem`, and why did the `SP` Chapter 10 streaming operator use `16 MB` instead of `128 MB`?</summary>
`tcp_rmem` and `tcp_wmem` take three byte values: `"min default max"`, where `max` (and `net.core.rmem_max`/`wmem_max`) must be at least **`1–2x` the Bandwidth-Delay Product (`BDP = BW * RTT`)** of your longest path (`128 MiB = 134,217,728` bytes for `10–25 Gb/s` cross-continent WAN paths; `16–64 MiB` for intra-DC `100G` paths). The streaming operator in `SP` Chapter 10 capped `rmem_max`/`wmem_max` at **`16 MiB` (`16,777,216`)** because each server handled tens of thousands of concurrent client connections—oversizing per-socket buffers across thousands of sockets risks exhausting host RAM under an attack or slow-reader stall.
</details>

<details>
<summary>13. What TCP port exhaustion and socket-limit issues occur during `NCCL` bootstrap and socket-transport runs, and how do you fix them (`ASP` Chapter 4)?</summary>
(1) During multi-node **`NCCL` out-of-band TCP bootstrap**, ranks open a burst of TCP connections to exchange RDMA queue-pair/ring metadata. If `net.ipv4.ip_local_port_range` is too narrow or ports are consumed in `TIME_WAIT`, bootstrap hangs or fails with `Cannot assign requested address`; configure a dedicated/wide **`net.ipv4.ip_local_port_range`** (e.g., `"50000 51000"` in the book's isolated-port example or `"10240 65535"` with `tcp_tw_reuse = 1`), set **`MASTER_PORT`**, and set **`NCCL_SOCKET_IFNAME=ib0`** (never `lo` or `docker0`).\n(2) When using `NCCL` over IP sockets (`NCCL_SOCKET_NTHREADS` threads × `NCCL_NSOCKS_PERTHREAD` sockets per thread), `NCCL` enforces a hard ceiling of **`64` total sockets per communicator**: **`NCCL_NSOCKS_PERTHREAD * NCCL_SOCKET_NTHREADS <= 64`** (e.g., `4 * 8 = 32`).
</details>

<details>
<summary>14. How do `sendfile()` and `MSG_ZEROCOPY` reduce CPU usage during high-bandwidth data transfers?</summary>
Traditional `read(file_fd, buf)` + `write(sock_fd, buf)` copies data **twice** with the CPU (kernel page cache -> user-space buffer -> kernel socket buffer) and incurs **four user/kernel context switches**. **`sendfile()`** (and `splice()`) transfers data directly from the kernel page cache to the socket descriptor list in a single syscall, and the NIC DMAs the payload straight out of the page cache (**zero CPU copies**). **`MSG_ZEROCOPY`** on `sendmsg()` pins user-space memory pages and DMAs directly from user memory for payloads `>= 10 KB`.
</details>

<details>
<summary>15. Compare `XDP`, `AF_XDP`, `SR-IOV`, `DPDK`, and `RDMA` (`RoCEv2` / `InfiniBand`).</summary>
- **`XDP` (*eXpress Data Path*)**: runs an eBPF program inside the NIC driver **before `sk_buff` allocation** (`XDP_DROP`, `XDP_TX`, `XDP_REDIRECT`, `XDP_PASS`), ideal for `> 10 Mpps/core` DDoS dropping and L4 load balancing (`Katran`) while keeping the Linux stack for normal traffic.\n- **`AF_XDP`**: redirects selected frames from an XDP program into a zero-copy user-space ring (`UMEM`) without taking over the whole NIC.\n- **`SR-IOV`**: partitions one physical PCIe NIC (`PF`) into multiple hardware **Virtual Functions (`VF`s)** passed directly into Pods/VMs (`sriov_numvfs`), bypassing the host software bridge/`veth` tax.\n- **`DPDK`**: unbinds the NIC from the kernel and runs a user-space **poll-mode driver (`PMD`)** spinning at 100% CPU on dedicated cores.\n- **`RDMA` (`RoCEv2` / `InfiniBand`)**: offloads the entire transport protocol (`Queue Pairs`) into the NIC ASIC and DMAs directly to/from GPU HBM (`GPUDirect RDMA`) with `1–3 µs` latency and ~0% CPU.
</details>

<details>
<summary>16. Why can a container `veth` pair become a throughput bottleneck on a `100G` node, and what are the four alternatives?</summary>
When a Pod sends or receives packets through a Linux `veth` pair and software bridge, each packet triggers a softirq transition (`NET_RX_SOFTIRQ`) and traverses `tc`/netfilter hooks twice (inside the pod namespace and on the host), pinning a single high-rate flow to one CPU core (`~15–25 Gb/s` limit per flow). Alternatives for high-bandwidth pods: (1) **`hostNetwork: true`** (shares the host namespace directly), (2) **Cilium eBPF host-routing** (`bpf_redirect_peer` bypassing the host stack between `veth` ends), (3) **`ipvlan` / `macvlan`**, or (4) **`SR-IOV` / `RDMA` VF attachment via Multus**.
</details>

<details>
<summary>17. Why does a single TCP stream (`iperf3 -c host`) often plateau at `15` to `30 Gb/s` on a `100 Gb/s` or `400 Gb/s` NIC even when the network path is idle?</summary>
Because all packets of a single TCP 4-tuple hash to **one RSS queue** and are processed by **a single CPU core** (both in the kernel softirq handler and in the single-threaded user-space `read`/`write` loop). Check `mpstat -P ALL 1`: you will see **one CPU core pinned at 100% (`%soft` + `%usr`/`%sys`)** while 63 other cores sit idle. Fix single-stream speed with **Jumbo MTU (`9000`)**, `TSO`/`GRO` offloads, **NUMA-local CPU pinning** (`numactl`), and larger socket buffers, and use **parallel streams (`iperf3 -P 8` or `-P 16`)** to exercise multiple RSS queues and cores.
</details>

<details>
<summary>18. How do you tune a Linux host specifically for ultra-low-latency RPCs versus bulk throughput?</summary>
- **Ultra-low latency**: set `tuned-adm profile network-latency`, disable deep CPU C-states (`intel_idle.max_cstate=1`, CPU governor `performance`), disable or lower NIC interrupt coalescing (`ethtool -C rx-usecs 0`), enable socket **busy polling** (`net.core.busy_poll = 50`, `net.core.busy_read = 50`), set **`TCP_NODELAY`** on sockets, and cap sender bufferbloat with `net.ipv4.tcp_notsent_lowat = 131072`.\n- **Bulk throughput**: set `MTU = 9000`, enable `TSO`/`GSO`/`GRO` and adaptive interrupt coalescing, size `rmem_max`/`wmem_max` to `>= 2 * BDP`, and use `fq` + `bbr` (WAN) or `cubic`/`dctcp` (DC).
</details>

<details>
<summary>19. How do you persist `ethtool` ring, queue, and offload settings across reboots on modern Linux servers?</summary>
`ethtool -G/-L/-K` commands are volatile and reset on reboot or driver reload. Persist them declaratively using **`systemd-networkd` `.link` files** in `/etc/systemd/network/10-<ifname>.link` (`[Link] RxBufferSize=4096 TxBufferSize=4096 CombinedChannels=32 GenericReceiveOffload=yes LargeReceiveOffload=no`), a NetworkManager dispatcher script in `/etc/NetworkManager/dispatcher.d/`, or a `systemd` oneshot service ordered `After=network-online.target`, managed by Ansible and verified by a boot audit check.
</details>

<details>
<summary>20. Summarize the 7-step Safe Network Tuning Methodology.</summary>
(1) **Define a quantitative target metric** (`nccl-tests` algbw/busbw, `iperf3` goodput, or p99 RPC latency);\n(2) **Record the complete baseline** (hardware/NUMA topology, driver/firmware versions, `ethtool`, `sysctl`, counters, and benchmark score);\n(3) **Locate the active bottleneck using the USE method** (link speed, PCIe gen/width, NIC ring `rx_missed`, `softnet_stat`, `ss -ti` limiter, or CPU core);\n(4) **Change ONE parameter at a time** and re-measure with the identical test;\n(5) **Keep only changes that produce a measurable improvement** (revert no-ops);\n(6) **Prefer structural fixes** (NUMA alignment, MTU 9000, RSS queues, removing `conntrack`) over cargo-cult `sysctl` lists; and\n(7) **Persist in version-controlled configuration management** with automated drift checks.
</details>

## Sources and review notes

- **Sources read in full:**
  - `systems-performance-2nd-edition` — Brendan Gregg, *Systems Performance: Enterprise and the Cloud*, 2nd ed., **Chapter 10: Network** (system-wide tunables and the 14-setting streaming production example `12582912`/`16777216`, socket and TCP buffers, backlog, congestion control, TCP options, device queues, socket options `SO_REUSEPORT` / `MSG_ZEROCOPY` / `sendfile`, static performance tuning, and resource controls).
  - `ai-systems-performance-engineering` — Chris Fregly, *AI Systems Performance Engineering*, **Chapter 4: Tuning Distributed Networking Communication** (host TCP stack and MTU `9000` tuning `rmem_max`/`wmem_max`, `tcp_rmem`/`tcp_wmem`, CUBIC vs BBR, NUMA-local NIC interrupt affinity, `NCCL` bootstrap ephemeral TCP port exhaustion `net.ipv4.ip_local_port_range="50000 51000"` in `/etc/sysctl.conf`, `NCCL_SOCKET_IFNAME`, `MASTER_PORT`, and socket-transport connection limits `NCCL_NSOCKS_PERTHREAD * NCCL_SOCKET_NTHREADS <= 64`).
  - `how-linux-works-3rd-edition` — Brian Ward, *How Linux Works*, 3rd ed., **Chapter 9: Understanding Your Network and Its Configuration** (manual interface and route configuration, network managers, and routers).
  - `nvidia-devops/volume-01/03-linux-networking-masterclass.md` — migrated the packet journey (RX path, NAPI, RSS and interrupt affinity, ring buffers and coalescing, TX path and offloads), policy-based routing and the multi-homed asymmetric routing fix, VRF, bonding and LACP limitations, multi-homing for RoCEv2, SR-IOV and DPDK, eBPF/XDP and Cilium, LFN/TCP window scaling and SACK, the `veth` bottleneck scenario, MTU, and the `sysctl` tuning cheat sheet.
- **Run here:** `python3 code/part02/linux_stack_nic_tuning_lab.py` (10 passed, 0 failed).
- **Explicitly labelled inferences:** The Section 5 RX/TX packet-path Mermaid diagram, `/etc/sysctl.d/99-ai-node-network.conf` baseline, and Section 9 10-scenario troubleshooting guide synthesize the Linux kernel documentation (`ip-sysctl.rst`, `scaling.rst`, `vrf.rst`), `ethtool(8)`, and `ip-rule(8)` (cross-referenced with Chapters 1.28, 2.5, 2.6, 2.7, 2.12, 2.17, 2.19, 2.22, 2.23, and Part 11, plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, and 40).
- **Not verified on live hardware:** All interactive VM and NIC tuning commands (`ip rule`, `ip vrf`, `ethtool -G/-L/-K/-C/-X/-N`, `sysctl`, `mpstat`, `iperf3`) are marked (untested here) and must be executed on a disposable Linux VM or test server.
