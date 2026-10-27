---
id: "c02-01"
title: "2.1 What happens when you curl a URL: a packet's journey end to end"
sidebar_label: "2.1 What happens when you curl a URL: a packet's journey end to end"
sidebar_position: 1
description: "What happens when you curl a URL: a packet's journey end to end"
status: "drafted"
tier: "0"
level: "B"
lab_venue: "GCP / GKE"
---

# 2.1 What happens when you curl a URL: a packet's journey end to end

| | |
|---|---|
| Level | Beginner |
| Priority tier | 0 |
| Lab venue | Any Linux VM with Internet access (GCP VM is fine) |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Almost every network problem you will ever debug in an AI cluster is a question about *where in a path something went wrong*. A container image does not pull. A training job cannot reach the dataset bucket. `torchrun` hangs at rendezvous. NCCL falls back from InfiniBand to sockets. A node cannot be reached by SSH after a switch change. A pod resolves a name to the wrong address. Each of these is a failure at a particular step of a journey that starts in a process and ends in another process on another machine.

Interview loops ask the classic question "what happens when you type a URL into a browser (or `curl` it)?" because a candidate who can narrate that journey in detail, with the commands that prove each step, has the mental model needed for everything in this Part: name resolution, routing, ARP/ND, switching, NAT, TCP, TLS, HTTP, and teardown. This chapter is that narrative. It is deliberately a *tour* that touches every layer once; later chapters take each stop in depth (2.2 layers, 2.3 Ethernet, 2.4 IP addressing, 2.5 host routing, 2.6 TCP, 2.7 ICMP and diagnostics, 2.8 DNS, 2.9 DHCP and NAT, 2.10 HTTP/TLS/PKI).

We use `curl https://example.com/` as the running example and finish by showing how the same journey (and its shortcuts) looks for the traffic that matters most in AI clusters: container image pulls, object storage, and NCCL.

## Prerequisites and outcomes

You should be comfortable with a Linux shell (Part 1, chapters 1.1 to 1.9). No prior networking knowledge is needed.

After this chapter you can:

- Narrate, in order and with correct terminology, everything that happens between pressing Enter on `curl https://example.com/` and seeing the response, including every protocol that participates.
- Name the kernel data structures and system calls involved (resolver, `socket`, `connect`, routing table, neighbour table, qdisc, NIC, socket buffers).
- Run commands that expose each step: `strace`, `getent`, `resolvectl`, `dig`, `ip route get`, `ip neigh`, `tcpdump`, `ss`, `openssl s_client`, `curl -w`.
- Break a request's latency into DNS, TCP connect, TLS handshake, time to first byte and transfer, and read a `curl -w` timing report.
- Map a symptom ("connection refused", "no route to host", "certificate verify failed", "timeout") to the layer that produced it.
- Explain what stays inside a host, what crosses a switch, what crosses a router, and what is rewritten by NAT.
- Explain how RDMA/InfiniBand traffic in AI clusters differs from this journey (kernel bypass) and where it is the same.

## 1. The whole journey in one picture

```mermaid
sequenceDiagram
  autonumber
  participant U as curl (user space)
  participant K as Linux kernel (stack)
  participant N as NIC / switch / router path
  participant D as DNS resolver
  participant S as Server (example.com)
  U->>K: getaddrinfo("example.com") - resolver library, /etc/nsswitch.conf, /etc/hosts
  K->>D: DNS query (UDP/53) to configured resolver, via routing + ARP/ND + Ethernet
  D-->>K: A / AAAA records (IP addresses, TTL)
  U->>K: socket(), connect(IP:443)
  K->>K: route lookup (longest prefix), source address, ARP/ND for next hop
  K->>S: TCP SYN
  S-->>K: SYN-ACK
  K->>S: ACK (connection established)
  U->>S: TLS ClientHello (SNI, ALPN)
  S-->>U: ServerHello, certificate chain, key share, Finished
  U->>S: Finished (TLS 1.3: encrypted application data may follow)
  U->>S: HTTP request: GET / HTTP/1.1 (or HTTP/2)
  S-->>U: HTTP response: status, headers, body
  U->>S: FIN / close (or connection reuse)
```

Every arrow between user and server crosses the same physical sequence: process → socket → TCP/IP stack → queueing discipline → NIC driver → wire → switch → router(s) → … → server NIC → stack → process. The next sections follow that path.

## 2. Step 0: the process and the URL

`curl` parses the URL: scheme `https` (default port 443), host `example.com`, path `/`. It uses **libcurl**, which calls the C library for name resolution and the kernel for sockets. Nothing about the network has happened yet.

```bash
curl -v https://example.com/ -o /dev/null        # -v shows the steps curl itself reports
curl -sS -o /dev/null -w 'dns=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total} ip=%{remote_ip} http=%{http_version}\n' https://example.com/
strace -f -tt -e trace=openat,socket,connect,sendto,recvfrom,sendmsg,recvmsg,close curl -s https://example.com/ -o /dev/null 2>&1 | head -80
```

The `strace` output is a powerful teaching tool: you will see `curl` open `/etc/resolv.conf`, `/etc/nsswitch.conf`, `/etc/hosts`, then `socket(AF_INET, SOCK_DGRAM, ...)` for DNS, then `socket(AF_INET6 or AF_INET, SOCK_STREAM, ...)` and `connect(...)` for the TCP connection, and `sendto`/`recvfrom` calls carrying TLS and HTTP bytes.

## 3. Step 1: name resolution (what is the IP address?)

Computers route by numbers (IP addresses); people use names. The C library function `getaddrinfo()` turns `example.com` into one or more addresses. The sequence on a typical Linux system:

1. **`/etc/nsswitch.conf`** (line `hosts:`) defines the lookup order, usually `files dns` (older) or `files mdns4_minimal [NOTFOUND=return] resolve [!UNAVAIL=return] dns` (systemd systems). `files` means `/etc/hosts` first.
2. **`/etc/hosts`**: static overrides (`127.0.0.1 localhost`). A match ends the lookup. Keep it short; entries that DNS can serve do not belong there.
3. **The stub resolver / local cache**: on systemd distributions `/etc/resolv.conf` often points at `127.0.0.53` (the `systemd-resolved` stub) or a local caching daemon (`dnsmasq`, `unbound`, `nscd`). `resolvectl status` shows the real upstream servers per interface and per-link DNS domains.
4. **`search` domains and `ndots`**: names with fewer dots than `ndots` (default 1; Kubernetes sets 5) are tried with each `search` suffix first. A bare `myhost` may become `myhost.corp.example.com`.
5. **The DNS query** itself: the resolver sends a UDP datagram to port 53 of the configured name server (retrying, and switching to TCP when the answer is truncated or large). Modern resolvers ask for both **A** (IPv4) and **AAAA** (IPv6) records in parallel. The question travels through the same routing/ARP/Ethernet steps as any packet (sections 4 and 5).
6. **The recursive resolver** (your ISP, cloud, or an internal server) either answers from cache or walks the DNS hierarchy: root → `.com` TLD servers → `example.com` authoritative servers, caching each answer for its **TTL**.
7. **Answer selection**: `getaddrinfo` orders addresses by RFC 6724 rules (IPv6 preferred if usable), and many clients implement "Happy Eyeballs" (try IPv6 and IPv4 with a small head start) to avoid long IPv6 black-hole timeouts.

```bash
getent hosts example.com                    # what the C library (nsswitch order) returns
getent ahosts example.com                   # all addresses with socket types, in sorted order
cat /etc/nsswitch.conf | grep ^hosts ; cat /etc/resolv.conf ; resolvectl status | head -30
resolvectl query example.com                # through systemd-resolved, shows cache/transport/source
dig example.com A +noall +answer +ttlid     # direct query, TTL visible (use @server to choose resolver)
dig example.com AAAA +short ; dig +trace example.com | head -40     # walk the hierarchy from the root
time getent hosts example.com               # first call vs repeated call: cache effect
```

What goes wrong here (details in chapter 2.8): wrong resolver in `/etc/resolv.conf` or by DHCP; split-horizon DNS giving internal vs external answers; stale cache after a change (TTL); `search`/`ndots` multiplying queries (Kubernetes pods); IPv6 AAAA answers for hosts you cannot reach over IPv6; firewalls blocking UDP/53 or TCP/53; DNSSEC failures; slow first lookup due to timeouts to a dead first resolver. Symptom: `Could not resolve host` (curl exit code 6), `Temporary failure in name resolution`, or a long pause before anything else happens (`time_namelookup` large).

## 4. Step 2: the socket, the route and the source address

With an IP address (say 93.184.216.34), `curl` calls:

```c
fd = socket(AF_INET, SOCK_STREAM, 0);      // or AF_INET6; creates a TCP socket (a kernel object with send/receive buffers)
connect(fd, {93.184.216.34, port 443});    // triggers the whole connection setup
```

`connect()` asks the kernel to deliver a packet to that destination, so the kernel first answers the question **"where do I send it?"** with a **routing table lookup**:

```bash
ip route show                                 # the host's table
ip route get 93.184.216.34                    # the decision for THIS destination: next hop, device, chosen source address
# example output:  93.184.216.34 via 10.0.0.1 dev ens4 src 10.0.0.15 uid 1000 \ cache
ip -6 route get 2606:2800:220:1:248:1893:25c8:1946
```

The rules (chapter 2.5 in depth):

- Each route is a destination prefix plus how to reach it: directly on a link (`dev ens4 scope link`) or via a **gateway** (`via 10.0.0.1`). The kernel picks the **longest matching prefix**; the **default route** `default via 10.0.0.1` (`0.0.0.0/0` in IPv4, `::/0` in IPv6) matches anything not covered by something more specific. Ties are broken by metric.
- If the destination is inside a connected subnet (for example 10.0.0.0/24), the host sends directly to it; otherwise it sends to the gateway ("the router") and lets the rest of the Internet worry about the destination.
- The kernel also chooses the **source IP**: the primary address of the outgoing interface in the same subnet as the next hop (or a configured `src`). The **source port** is an **ephemeral port** chosen from `net.ipv4.ip_local_port_range` (default 32768 to 60999). The connection is then uniquely identified by the 5-tuple (protocol, source IP, source port, destination IP, destination port).
- Policy routing (rules, multiple tables), VRFs, VPN interfaces, and container networks can change the answer; `ip rule show` and `ip route show table all` reveal them.

Failures: `Network is unreachable` (`ENETUNREACH`): no route at all (no default gateway). `No route to host` (`EHOSTUNREACH`): the route exists but the next hop could not be resolved (ARP failed) or an ICMP unreachable came back. A route that sends traffic out the wrong interface or with the wrong source address (asymmetric routing, multiple NICs) is a classic cause of connections that work in one direction only.

## 5. Step 3: from IP to Ethernet (ARP or NDP) and out of the NIC

An IP packet needs a link-layer destination to be placed in an Ethernet frame. The next hop's IP address (the gateway 10.0.0.1, or the destination itself if on-link) must be mapped to a **MAC address**:

- **IPv4: ARP** (Address Resolution Protocol): the host broadcasts "who has 10.0.0.1? tell 10.0.0.15" to `ff:ff:ff:ff:ff:ff`; the owner replies unicast with its MAC. The result is cached in the **neighbour table** (`ip neigh`), states `REACHABLE`, `STALE`, `DELAY`, `PROBE`, `FAILED`.
- **IPv6: NDP** (Neighbor Discovery): neighbour solicitation to a solicited-node multicast address, neighbour advertisement in reply.

```bash
ip neigh show                      # IP -> MAC mappings and their states
ip neigh flush dev ens4            # force re-resolution (careful on production hosts)
sudo tcpdump -nn -e -i ens4 arp or icmp6        # watch ARP/NDP with Ethernet headers (-e)
arping -I ens4 10.0.0.1            # active ARP probe (also detects duplicate addresses)
```

The kernel then builds the packet through each layer's **Protocol Data Unit (PDU)** (`NK` Chapter 1, where standards are defined by **ISO/IEC 7498-1..4** for the 7-layer OSI model and **IETF RFCs**—such as `RFC 1122` for the 4-layer TCP/IP model, progressing from *Proposed Standard* to *Internet Standard*): application **Data** → TCP **Segment** (with source/destination ports) → IP **Packet** (with source/destination IP and TTL) → Ethernet **Frame** → physical **Bits** on the wire. On the wire, an Ethernet II frame begins with an **8-byte Preamble + Start Frame Delimiter (`SFD`)** (`10101010...10101011`), followed by the **6-byte Destination MAC** (the **next hop's MAC**, which for off-subnet traffic is the *gateway's*, not the final destination's), **6-byte Source MAC** (this NIC), **2-byte EtherType** (`0x0800` for IPv4, `0x86DD` for IPv6, `0x0806` for ARP), the **46 to 1,500-byte payload**, and a **4-byte Frame Check Sequence (`FCS`)** CRC trailer. This detail trips up many beginners: **MAC addresses change at every router hop; IP addresses (absent NAT) stay the same end to end.**

The frame passes through the egress **queueing discipline (qdisc)** (`tc qdisc show dev ens4`; default `fq_codel` or `fq`/`mq`), to the NIC driver, into a transmit ring in DMA-able memory; the NIC reads it, may compute checksums (offload), segments large TCP chunks (TSO/GSO), and serialises the bits onto the medium. On a VM, the "NIC" is a virtual device (virtio-net or a cloud-specific NIC) and the next hop is the cloud's virtual network (chapter 2.32).

## 6. Step 4: the switch, the router, NAT and the Internet

**A switch** (layer 2) receives the frame on a port, **learns** that the source MAC lives on that port (MAC address table), and forwards it to the port where the destination MAC was learned, or **floods** it to all ports (except the ingress) if unknown or broadcast. Switches do not look at IP addresses (for plain L2 switching); they define the **broadcast domain**: ARP broadcasts reach every host in the VLAN/subnet (chapters 2.3, 2.11).

**The default gateway (a router)** receives the frame addressed to its own MAC, strips the Ethernet header, examines the IP header, and:

1. Checks the destination against its **routing table** (longest prefix match in the FIB).
2. Decrements the **TTL** (hop limit) and recomputes the header checksum (IPv4); if TTL reaches zero it drops the packet and sends back an ICMP **Time Exceeded** (this is how `traceroute` works).
3. Chooses the egress interface and next hop, resolves the next hop's MAC (ARP/ND), builds a new Ethernet header, and forwards the frame.
4. If the packet exceeds the egress MTU: fragments it (IPv4, if DF is not set) or drops it and sends ICMP **Fragmentation Needed / Packet Too Big** (Path MTU Discovery; blackholed ICMP breaks it).

At the **edge of a private network** (home router, corporate firewall, cloud NAT gateway), **NAT/PAT** rewrites the source address (and port) of outgoing packets from a private address (RFC 1918: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) to a public one, keeps a translation table (connection tracking), and reverses it for replies. The server therefore sees the NAT's public IP, not your private address (chapter 2.9).

Across the **Internet**, each router along the path (typically 8 to 20 hops) repeats the lookup-and-forward step using tables built by routing protocols: OSPF/IS-IS inside networks and **BGP** between them (chapters 2.13 to 2.16). Large services are often reached through **anycast** (the same IP announced from many locations; BGP delivers you to the nearest) and CDNs, load balancers and reverse proxies (chapter 2.20), so "the server" you reach is typically a front end, not the machine that finally generates the page.

```bash
traceroute -n example.com            # or: mtr -n -c 20 --report example.com   (hops via TTL expiry)
ping -c 4 example.com                # ICMP echo: reachability and RTT
ip -s link show dev ens4             # TX/RX packets, errors, drops on the first hop
```

## 7. Step 5: TCP connection establishment

`connect()` on a TCP socket triggers the **three-way handshake**:

1. **SYN**: client → server, with the client's initial sequence number and options: MSS (maximum segment size, typically MTU minus 40, e.g. 1460), window scale, SACK permitted, timestamps, optionally ECN.
2. **SYN-ACK**: server → client, acknowledging and carrying the server's own sequence number and options. If no process is listening on port 443, the server's kernel answers **RST** instead: the client sees `Connection refused` immediately. If a firewall silently drops the SYN, the client gets nothing and retries (1 s, 2 s, 4 s … backoff): `Connection timed out`.
3. **ACK**: client → server. The connection is **ESTABLISHED** on both sides; `connect()` returns.

The server side: a `listen()` socket has a SYN queue and an accept queue (backlog); `accept()` returns a new socket for the connection. TCP then provides a reliable, ordered byte stream using sequence numbers, acknowledgements, retransmission timers, flow control (the receiver's advertised window) and congestion control (the sender's congestion window, slow start, then congestion avoidance with CUBIC or BBR). Chapter 2.6 covers all of this.

```bash
sudo tcpdump -nn -i any 'host 93.184.216.34 and tcp' -c 20      # watch SYN, SYN-ACK, ACK, TLS bytes, FIN
ss -tni dst 93.184.216.34                                       # per-connection info: rtt, cwnd, mss, retrans, bytes
ss -s ; ss -ltnp                                                # summary; listening sockets with owning processes
```

`time_connect` in `curl -w` equals about one round-trip time (RTT) to the server (plus DNS time before it). Intra-datacentre RTTs are about 0.05 to 0.5 ms; across continents 100 ms or more, which is why connection reuse and fewer round trips matter.

## 8. Step 6: TLS handshake (HTTPS)

For `https://`, the client and server now establish an encrypted, authenticated channel on top of the TCP connection:

1. **ClientHello**: supported TLS versions and cipher suites, a random value, key share (TLS 1.3: the client guesses a key-exchange group and sends its public key), **SNI** (Server Name Indication: `example.com` in clear text so a shared front end can pick the right certificate), **ALPN** (application protocols offered: `h2`, `http/1.1`).
2. **ServerHello + certificate chain + key share + Finished**: the server selects parameters, proves its identity with an X.509 certificate chain (leaf → intermediate → root), signs the handshake (CertificateVerify), and both sides derive the session keys (ephemeral Diffie-Hellman gives forward secrecy). In TLS 1.3 this costs **one round trip** before application data (0-RTT resumption can send data earlier with replay caveats); TLS 1.2 needs two.
3. The client **verifies** the chain against its trust store (`/etc/ssl/certs`, a CA bundle), the hostname (SAN must match `example.com`), validity period, key usage, and revocation (OCSP stapling / CRLs, often soft-fail).

```bash
openssl s_client -connect example.com:443 -servername example.com -tls1_3 </dev/null 2>/dev/null | egrep 'Protocol|Cipher|Verify|subject|issuer'
openssl s_client -connect example.com:443 -servername example.com -showcerts </dev/null | less     # whole chain
curl -v --tlsv1.3 https://example.com/ -o /dev/null 2>&1 | egrep 'TLS|ALPN|subject|issuer|expire'
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | openssl x509 -noout -dates -subject -ext subjectAltName
```

Typical failures (chapter 2.10): `certificate verify failed: unable to get local issuer certificate` (missing intermediate or CA bundle in a minimal container image), expired certificate, hostname mismatch (using an IP, or the wrong SNI), TLS interception by a corporate proxy with an unknown CA, clock skew making a valid certificate look "not yet valid", protocol/cipher mismatch with old servers. `time_appconnect - time_connect` is the TLS cost (one RTT plus crypto).

## 9. Step 7: the HTTP request and response

Inside the encrypted channel:

- **HTTP/1.1** (text): `GET / HTTP/1.1`, `Host: example.com`, `User-Agent`, `Accept`, optional `Authorization`, and a blank line; the response is a status line (`HTTP/1.1 200 OK`), headers (`Content-Type`, `Content-Length` or `Transfer-Encoding: chunked`, caching headers, `Set-Cookie`), a blank line, and the body. Persistent connections (keep-alive) reuse the TCP+TLS connection for multiple requests.
- **HTTP/2** (binary, over TLS with ALPN `h2`): multiplexes many request/response streams on one connection, with header compression; head-of-line blocking now occurs at the TCP level.
- **HTTP/3** (over **QUIC**, which runs on UDP/443 and includes TLS 1.3): per-stream loss recovery, faster connection setup, connection migration. `curl --http3` if supported.
- A **redirect** (301/302/307/308) causes a new request (maybe a new connection); `curl -L` follows them. Proxies, CDNs and load balancers may terminate TLS, rewrite headers (`X-Forwarded-For`), cache, and retry.

`time_starttransfer` (time to first byte, TTFB) = DNS + connect + TLS + server think time + one RTT for the response to start arriving; `time_total` adds the body transfer, which depends on size, bandwidth, the TCP congestion window and loss.

```bash
curl -sS -D - -o /dev/null https://example.com/                 # response headers only
curl -sS --http1.1 -I https://example.com/ ; curl -sS --http2 -I https://example.com/
curl -sS -w '\nhttp=%{http_version} code=%{http_code} size=%{size_download} speed=%{speed_download}\n' -o /dev/null https://example.com/
curl --resolve example.com:443:93.184.216.34 https://example.com/ -o /dev/null -v     # bypass DNS: test a specific backend
curl -H 'Host: example.com' http://93.184.216.34/ -I                                  # virtual hosting check without DNS
```

## 10. Step 8: transfer, acknowledgements and teardown

The response body arrives as TCP segments; the receiver's kernel reassembles them in order into the socket receive buffer, sends **ACKs** (often every second segment, with delayed ACK timers), advertises its **window**, and `curl` reads the data with `recv`. Loss triggers fast retransmit (three duplicate ACKs / SACK) or a retransmission timeout; the congestion window collapses and regrows. When both sides are done, TCP closes with **FIN/ACK** exchanges (or **RST** on abort); the side that closes first keeps the connection in **TIME_WAIT** (about 60 seconds on Linux) so late packets cannot corrupt a new connection using the same 5-tuple. Thousands of short connections can exhaust ephemeral ports or fill the table with `TIME_WAIT` (chapter 2.6, and tuning in 1.22).

## 11. Timing: reading `curl -w`

```bash
cat > curl-format.txt <<'EOF'
     namelookup:  %{time_namelookup}s
        connect:  %{time_connect}s
     appconnect:  %{time_appconnect}s   (TLS done)
    pretransfer:  %{time_pretransfer}s
  starttransfer:  %{time_starttransfer}s   (first byte)
          total:  %{time_total}s
      remote_ip:  %{remote_ip}   local_ip: %{local_ip}   http: %{http_version}   connects: %{num_connects}
EOF
curl -sS -o /dev/null -w @curl-format.txt https://example.com/
```

All values are cumulative from the start. Subtract successive values to get each phase: DNS = namelookup; TCP = connect − namelookup; TLS = appconnect − connect; request + server time + first byte = starttransfer − pretransfer; transfer = total − starttransfer. Interpretation by phase: large DNS → resolver problem or search-domain explosion; large TCP → distance, loss (SYN retransmit adds 1 s), or an overloaded accept queue; large TLS → distance, certificate chain/OCSP fetch, CPU on a busy terminator; large TTFB → the server/application or backend; large transfer → bandwidth, loss, window limits, or response size.

## 12. A map from symptom to layer

| Symptom (curl) | Exit code / message | Layer and likely cause | First tools |
|---|---|---|---|
| `Could not resolve host` | 6 | Name resolution: wrong/dead resolver, NXDOMAIN, firewall on port 53, nsswitch | `getent`, `resolvectl`, `dig @server`, `/etc/resolv.conf` |
| Long pause, then success | | DNS timeout to a dead first resolver, IPv6 fallback delay, slow ARP | `strace -tt`, `curl -w`, `tcpdump port 53` |
| `Network is unreachable` | 7 | Routing: no route/default gateway | `ip route`, `ip route get` |
| `No route to host` | 7 | ARP/ND failure, ICMP unreachable | `ip neigh`, `tcpdump arp` |
| `Connection refused` | 7 | Transport: server reachable, no listener (RST), or firewall REJECT | `ss -ltn` on server, `nc -vz`, `tcpdump` |
| `Connection timed out` / `Operation timed out` | 28/7 | Packet loss or firewall DROP, security group, wrong route/NAT, asymmetric routing | `tcpdump` both ends, `mtr`, firewall logs |
| `SSL: certificate problem`, `certificate verify failed` | 60 | TLS/PKI: chain, expiry, hostname, interception, clock | `openssl s_client`, `date`, CA bundle |
| `SSL_ERROR_SYSCALL`/`wrong version number` | 35 | TLS vs plain-HTTP port mismatch, middlebox reset | `tcpdump`, `openssl s_client` |
| `HTTP 4xx/5xx` | 22 with `-f` | Application layer: auth, routing rules, backend down, rate limit | `curl -v`, server logs, load balancer logs |
| Works for small, stalls for big transfers | | MTU/PMTUD blackhole (ICMP filtered), TCP window/loss | `ping -M do -s 1472`, `tracepath`, `ss -ti`, `tcpdump` |
| Works from A, fails from B | | Different route, firewall, DNS view, proxy settings (`HTTP(S)_PROXY`) | `curl -v` from both, `env \| grep -i proxy` |

The method (chapter 2.30): test each layer from the bottom up (link, address, route, ARP, ping the gateway, ping the destination, DNS, TCP port, TLS, HTTP), or bisect from the middle (can I reach the gateway? can I reach an IP on the Internet? can I resolve names?).

## 13. The same journey in AI infrastructure

- **Container image pulls**: `containerd`/Docker resolves the registry name (DNS), connects over TLS (often through a corporate proxy or mirror), authenticates, and downloads layers over HTTP/2 or HTTP/1.1. Slow pulls are DNS, TLS chain/proxy issues, MTU black holes on cloud overlays, rate limits, or a congested NAT gateway.
- **Object storage (GCS/S3)**: HTTPS with many parallel connections; throughput is limited per connection by RTT and window, per instance by the NIC and cloud caps, and per prefix/bucket by service quotas. Private connectivity and DNS (private endpoints) change the path entirely.
- **Cluster bootstrap**: `torchrun`/MPI/NCCL rendezvous uses ordinary TCP connections over the management or front-end network (hostnames, DNS, `/etc/hosts`, `NCCL_SOCKET_IFNAME`), then the bulk transfers use RDMA verbs (InfiniBand or RoCE), **bypassing the kernel TCP/IP stack**: user-space libraries post work requests directly to the NIC, which does its own segmentation, reliability and memory access (GPUDirect RDMA reads GPU memory without CPU copies). The "journey" is shorter (no routing table, qdisc or TCP in the kernel), but the lower layers still exist (Ethernet or IB addressing, switches, routing in the fabric), and the control plane (connection setup) still uses TCP/IP.
- **Kubernetes**: a pod's request adds more steps: CoreDNS lookups with `ndots:5`, service virtual IPs translated by kube-proxy/eBPF (DNAT), CNI-managed veth/bridge or overlay (VXLAN) encapsulation, NetworkPolicy, then the node's normal path (chapters 2.23, 2.25, Part 5).
- **Cloud**: the "router" and "switch" are virtual; VPC routing, firewall rules, NAT gateways, load balancers and peering decide what happens (chapter 2.32).

## 14. Hands-on lab: trace one request end to end

First, run the self-checking Python lab (`code/part02/curl_packet_journey_lab.py`) locally. It verifies `curl -w` cumulative phase subtraction (DNS, TCP connect, TLS handshake, TTFB wait, body transfer), hop-by-hop L2 MAC rewrites vs constant L3 IP and decrementing `TTL`, and `curl` exit-code (`6`, `7`, `22`, `28`, `35`, `60`) layer diagnostics.

```bash
python3 code/part02/curl_packet_journey_lab.py
```

Next, on a disposable Linux VM with `curl`, `dig`, `tcpdump`, `strace`, `openssl`, `iproute2`, and `mtr` installed (all interactive VM commands below are `untested here`), work through these steps:

1. **Record your configuration**: `ip -br addr`, `ip route`, `ip neigh`, `cat /etc/resolv.conf`, `resolvectl status`, `cat /etc/nsswitch.conf | grep hosts`. Draw your host's view: interface, address, gateway, resolver.
2. **Narrate with strace**: run the `strace` command from section 2; list in order the files opened, sockets created, and addresses connected. Identify the DNS query socket and the TCP socket.
3. **Capture everything**: in one terminal `sudo tcpdump -nn -i any -w curl.pcap 'port 53 or host <example.com IP>'`; in another `curl -sS -o /dev/null https://example.com/`; stop the capture; read it with `tcpdump -nn -r curl.pcap | head -60` (or Wireshark). Label each packet: DNS query/response, SYN, SYN-ACK, ACK, ClientHello, ServerHello/Certificate, application data, FIN.
4. **Route and neighbour**: `ip route get <server IP>`; flush the gateway neighbour (`sudo ip neigh flush dev <if>`) and repeat the capture including `arp or icmp6` to see ARP/NDP.
5. **Timing**: run the `curl -w` report five times; then add `--resolve` to skip DNS; then try `--http1.1` versus `--http2`; compare phases. Try an HTTP (non-TLS) URL to see TLS time disappear.
6. **Break it on purpose** (one at a time, undo each): (a) point `/etc/resolv.conf` at an unused IP (use a copy, restore afterwards) and observe the delay and error; (b) `sudo ip route del default` and observe `Network is unreachable` (restore with the original `ip route add default via ...`; do this only on a VM with console access); (c) `curl http://<server IP>:81/` (closed port) vs a port blocked with `iptables -A OUTPUT -p tcp --dport 81 -j DROP` (timeout vs refused); (d) `curl https://example.com --cacert /dev/null` or an expired-cert test host (`https://expired.badssl.com/`) and read the TLS error.
7. **Path**: `traceroute -n` and `mtr -n -c 30 --report` to the server; note hop count, RTT growth, and where it increases; compare with `ping`'s RTT and with `time_connect`.
8. **AI-cluster variant** (optional, GPU VM): `ss -tnp` while a PyTorch distributed job rendezvous runs; compare to `rdma link`/`ibv_devinfo` and note which traffic is TCP and which is RDMA.

## 15. Common mistakes

- Treating "the network" as one thing instead of a path with layers.
- Forgetting DNS (or `search`/`ndots`, or IPv6 AAAA) when "the network is slow".
- Believing the destination MAC is the final server's MAC; forgetting that NAT hides your address.
- Testing with `ping` only (ICMP may be filtered, and it says nothing about TCP ports, TLS or HTTP).
- Using the IP in place of the name for HTTPS and being surprised by certificate errors; omitting SNI.
- Ignoring MTU and ICMP filtering.
- Reading `time_total` without the phase breakdown.
- Assuming that the client's problem is the server's problem (proxy variables, split DNS, different routes from different hosts).
- In AI clusters, assuming RDMA traffic is visible to `tcpdump`/`iptables`/`ss` (it is not; use RDMA tools and NIC counters).

## 16. Interview angles

- "Walk me through what happens when you run `curl https://example.com`." (The sections of this chapter, in order, with a command per step.)
- "How does a packet get from your laptop to a server in another continent? What changes at each hop?" (MAC rewrite and TTL decrement per hop; IP constant; NAT at edge.)
- "Difference between 'connection refused' and 'timed out'?" (RST vs silence.)
- "How would you debug 'works from my machine, not from the pod'?" (Resolver, route, NAT, policy, proxy.)
- "What is a three-way handshake and why? What are SYN cookies?"
- "What does the TLS handshake do? How does the client know it is talking to the right server?"
- "Where does TCP end up in AI training traffic, and where does it not?"
- "A download is fast for small files and stalls for large ones. Why?" (MTU/PMTUD, window/loss.)

## Exercises

1. **End-to-End `curl` Sequence and `strace` Verification:** List the 9 ordered stages of `curl https://example.com/` from URL parsing to `FIN`/`ACK` (`TIME_WAIT`), and state which system calls (`openat`, `socket`, `connect`, `sendto`, `recvfrom`, `close`) in `strace` correspond to `/etc/nsswitch.conf` / `/etc/hosts` lookup, the UDP/53 DNS query, and the TCP/443 connection.
2. **Name Resolution (`nsswitch.conf`, `systemd-resolved`, and Kubernetes `ndots:5`):** (a) Explain how `getent ahosts example.com`, `resolvectl query example.com`, and `dig +trace example.com` differ in what they test; (b) why does setting `ndots:5` in a Kubernetes Pod's `/etc/resolv.conf` multiply DNS queries when looking up `example.com`?
3. **Routing Lookup, ARP vs. Off-Subnet Gateway MAC, and Hop-by-Hop Rewrites:** Given a host `10.0.0.15/24` with default gateway `10.0.0.1` (`bb:bb:bb:00:00:01`) sending a packet to `93.184.216.34`: (a) what does `ip route get 93.184.216.34` return, and whose MAC address is placed in the outgoing Ethernet frame's Destination MAC field? (b) Using `simulate_router_hop_headers()` in `code/part02/curl_packet_journey.py`, trace which header fields change and which stay constant across three router hops.
4. **TCP 3-Way Handshake, `Connection refused` vs. `Connection timed out`, and PMTUD Blackholes:** (a) At the packet level (`tcpdump`), what is the difference between connecting to a host where no process is listening on port 443 (`Connection refused`) versus where a firewall drops the `SYN` (`Connection timed out`)? (b) Why does filtering ICMP `Fragmentation Needed` / `Packet Too Big` allow `curl` handshakes and tiny responses to succeed while large container layer downloads stall, and how does `ping -M do -s 1472` test it?
5. **Decomposing `curl -w` Timings and Diagnosing `curl` Exit Codes:** (a) Given `curl -w` output `namelookup=0.012s, connect=0.032s, appconnect=0.072s, pretransfer=0.073s, starttransfer=0.123s, total=0.153s`, use `decompose_curl_timings()` to compute the exact duration of the DNS, TCP connect, TLS handshake, server TTFB wait, and body transfer phases; (b) map `curl` exit codes `6`, `7`, `22`, `28`, `35`, and `60` (`diagnose_curl_exit_code()`) to their exact network layers and first diagnostic commands.
6. **TCP/IP vs. Kernel-Bypass RDMA in AI Clusters:** Contrast the path of a `torchrun`/`NCCL` TCP bootstrap connection (`getaddrinfo` -> `socket` -> routing table -> ARP -> `qdisc` -> NIC) with an InfiniBand or RoCEv2 **GPUDirect RDMA** collective transfer, and explain why `tcpdump`, `ss`, and `iptables` do not see RDMA data-plane packets.

## Checkpoint questions (20)

<details>
<summary>1. Which C library function resolves a hostname in Linux, and how do `/etc/nsswitch.conf`, `/etc/hosts`, and `/etc/resolv.conf` interact?</summary>

Applications call `getaddrinfo()`, which reads the `hosts:` line in `/etc/nsswitch.conf` (typically `files resolve dns` or `files dns`). It checks `/etc/hosts` (`files`) first, then queries the local stub resolver (`systemd-resolved` at `127.0.0.53`) or the DNS nameservers listed in `/etc/resolv.conf`.
</details>

<details>
<summary>2. Why do modern resolvers query both `A` and `AAAA` records in parallel, and what is \"Happy Eyeballs\" (RFC 6724 / RFC 8305)?</summary>

Resolvers request both IPv4 (`A`) and IPv6 (`AAAA`) records so dual-stack clients can prefer IPv6. Under Happy Eyeballs, the client initiates an IPv6 connection first and starts a parallel IPv4 fallback attempt if IPv6 does not complete within a few tens of milliseconds, preventing broken IPv6 paths from causing multi-second hangs.
</details>

<details>
<summary>3. What do `search` domains and `ndots` in `/etc/resolv.conf` do, and why does `ndots:5` in Kubernetes matter?</summary>

Any hostname containing fewer dots than `ndots` (default `1` on Linux, `5` in Kubernetes Pods) is first queried with each `search` suffix appended before being queried as an absolute name. In Kubernetes, looking up `api.openai.com` (`2` dots `< 5`) triggers `A` and `AAAA` queries for `api.openai.com.<ns>.svc.cluster.local`, `api.openai.com.svc.cluster.local`, and `api.openai.com.cluster.local` before finally querying `api.openai.com.`.
</details>

<details>
<summary>4. What does `ip route get 93.184.216.34` show, and how does the Linux kernel choose between multiple matching routes?</summary>

`ip route get` queries the kernel's Forwarding Information Base (FIB) and prints the exact route, next-hop gateway (`via 10.0.0.1`), outgoing interface (`dev ens4`), and source IP address (`src 10.0.0.15`) the kernel will use for that destination. The kernel always picks the **longest matching prefix** (most specific subnet mask, e.g., `/24` beats `/16` beats default `0.0.0.0/0`), breaking ties by route `metric`.
</details>

<details>
<summary>5. How is a TCP connection uniquely identified in the kernel, and where does the client's source port come from?</summary>

Every TCP connection is uniquely identified by its **5-tuple**: `(protocol=TCP, source IP, source port, destination IP, destination port)`. When `connect()` is called on an unbound client socket, the kernel automatically selects an unused **ephemeral port** from `net.ipv4.ip_local_port_range` (default `32768` to `60999`).
</details>

<details>
<summary>6. How do ARP (IPv4) and NDP (IPv6) resolve the next hop's MAC address, and where does Linux cache the result?</summary>

In IPv4, the host broadcasts an **ARP Request** (`ff:ff:ff:ff:ff:ff`: *"Who has 10.0.0.1? Tell 10.0.0.15"*) and the owner replies unicast with its 6-byte MAC address. In IPv6, **NDP** (*Neighbor Discovery Protocol*) uses ICMPv6 Neighbor Solicitation and Advertisement messages sent to a solicited-node multicast address. Both populate the kernel **neighbour table**, inspected with `ip neigh show` (`REACHABLE`, `STALE`, `DELAY`, `PROBE`, `FAILED`).
</details>

<details>
<summary>7. When a host at `10.0.0.15/24` sends a packet to `93.184.216.34` via gateway `10.0.0.1`, what MAC address is in the Ethernet frame's Destination MAC field?</summary>

The **default gateway's (`10.0.0.1`) MAC address**—never the remote server's MAC address. Ethernet is strictly link-local; the host addresses the frame to its local router on the LAN segment.
</details>

<details>
<summary>8. Name the fields of an Ethernet II frame and the Protocol Data Units (`PDU`s) at each layer of the TCP/IP stack (`NK` Chapter 1).</summary>

The PDUs from top to bottom are: Application **Data** -> Transport **Segment** (TCP) / **Datagram** (UDP) -> Network **Packet** (IP) -> Link **Frame** (Ethernet) -> Physical **Bits**. An Ethernet II frame consists of an `8`-byte Preamble + SFD, `6`-byte Destination MAC, `6`-byte Source MAC, `2`-byte EtherType (`0x0800` IPv4, `0x86DD` IPv6, `0x0806` ARP), `46–1500`-byte Payload, and `4`-byte `FCS` (CRC-32).
</details>

<details>
<summary>9. As a packet traverses 12 routers across the Internet (without NAT), what changes in the headers at each hop and what stays constant?</summary>

At every router hop: (1) the outer **Ethernet source and destination MAC addresses** are stripped and replaced with the MACs for the next link, and (2) the IP header's **`TTL` (IPv4) / `Hop Limit` (IPv6)** is decremented by `1` (and the IPv4 header checksum is recomputed). The **source IP, destination IP, TCP ports, and payload** remain unchanged (except where a NAT gateway rewrites the source IP and port at a private-network boundary).
</details>

<details>
<summary>10. How does a Layer 2 switch decide where to forward an Ethernet frame compared to a Layer 3 router?</summary>

A **Layer 2 switch** inspects the incoming frame's source MAC to learn which port that MAC lives on (MAC address table), then forwards the frame out the single port matching the destination MAC—or **floods** it out all ports in the VLAN if the destination MAC is unknown or broadcast (`ff:ff:ff:ff:ff:ff`). A **Layer 3 router** terminates the Ethernet frame, looks up the destination IP in its routing table (FIB), decrements `TTL`, and encapsulates the packet in a brand-new Ethernet frame for the next hop.
</details>

<details>
<summary>11. Trace the TCP three-way handshake (`SYN`, `SYN-ACK`, `ACK`) and the options negotiated during `SYN`.</summary>

(1) Client sends `SYN` with its Initial Sequence Number (`ISN`) and TCP options: **MSS** (*Maximum Segment Size*, typically `MTU - 40 = 1460` bytes), **Window Scale** factor, **SACK Permitted**, and **Timestamps**; (2) Server replies with `SYN-ACK` containing its own `ISN`, `ACK = client_ISN + 1`, and negotiated options; and (3) Client sends `ACK` (`server_ISN + 1`), placing both sockets in `ESTABLISHED`.
</details>

<details>
<summary>12. At the packet level, what is the difference between `Connection refused` and `Connection timed out`?</summary>

`Connection refused` happens immediately (in 1 RTT) because the packet reached the destination host (or a firewall with `REJECT`), found no socket listening on that port, and received a TCP **`RST`** (Reset) packet back. `Connection timed out` happens after multiple seconds of exponential retries (`1 s, 2 s, 4 s...`) because `SYN` packets were silently dropped by a firewall (`DROP`) or blackholed in routing with no reply.
</details>

<details>
<summary>13. What happens during a TLS 1.3 handshake (`ClientHello` -> `ServerHello`), and what roles do `SNI` and `ALPN` play?</summary>

In TLS 1.3 (which completes in **1 RTT**), the client sends `ClientHello` containing its supported cipher suites, an ephemeral Diffie-Hellman key share, **`SNI`** (*Server Name Indication*, the hostname `example.com` so a multi-tenant server/load balancer selects the right X.509 certificate), and **`ALPN`** (*Application-Layer Protocol Negotiation*, offering `h2` and `http/1.1`). The server replies with `ServerHello`, its key share, its X.509 certificate chain, `CertificateVerify` signature, and `Finished`; the client verifies the certificate chain against `/etc/ssl/certs` and hostname `SAN`s before sending encrypted HTTP data.
</details>

<details>
<summary>14. Compare HTTP/1.1, HTTP/2, and HTTP/3 (QUIC) at the transport layer.</summary>

**HTTP/1.1** sends text requests sequentially over TCP (using keep-alive connection pooling). **HTTP/2** multiplexes multiple binary request/response streams over a single TCP + TLS connection with HPACK header compression, but a single lost TCP packet stalls all streams (**TCP head-of-line blocking**). **HTTP/3** runs over **QUIC** (UDP port `443` with built-in TLS 1.3), providing independent per-stream loss recovery without head-of-line blocking and 1-RTT / 0-RTT connection setup.
</details>

<details>
<summary>15. Given cumulative `curl -w` timings (`time_namelookup`, `time_connect`, `time_appconnect`, `time_pretransfer`, `time_starttransfer`, `time_total`), how do you calculate the time spent in each phase?</summary>

Because all `curl -w` timestamps are cumulative from `t = 0`:
- **DNS lookup** = `time_namelookup`
- **TCP handshake (1 RTT)** = `time_connect - time_namelookup`
- **TLS handshake (1–2 RTTs)** = `time_appconnect - time_connect`
- **Server processing + first byte RTT** = `time_starttransfer - time_pretransfer`
- **Response body download** = `time_total - time_starttransfer`
</details>

<details>
<summary>16. Why does TCP keep a closed connection in `TIME_WAIT` for ~60 seconds, and which side enters `TIME_WAIT`?</summary>

The side that initiates the active close (sends the first `FIN`) enters `TIME_WAIT` for ~60 seconds after sending the final `ACK`. This prevents delayed duplicate packets from the old connection from being accepted by a new connection reusing the same 5-tuple, and ensures the peer receives a retransmitted `ACK` if the final `ACK` was lost.
</details>

<details>
<summary>17. How does `traceroute` (or `mtr`) discover every router along a path, and how does Path MTU Discovery (`PMTUD`) work?</summary>

`traceroute` sends probe packets with `TTL = 1`, then `TTL = 2`, `TTL = 3`, ... Each Nth router decrements `TTL` to `0`, drops the packet, and replies with an **ICMP Time Exceeded** message from its own IP. **PMTUD** sets the **Don't Fragment (`DF`)** bit on IPv4 packets; if a link along the path has a smaller MTU (e.g., an overlay tunnel at `1450` bytes), the router drops the oversized packet and returns **ICMP Fragmentation Needed** (or IPv6 **Packet Too Big**) with the next-hop MTU so the sender lowers its TCP segment size (`ping -M do -s 1472` tests a 1500-byte path).
</details>

<details>
<summary>18. Map `curl` exit codes `6`, `7`, `22`, `28`, `35`, and `60` to their exact failure layers.</summary>

- `6`: DNS resolution failure (`Could not resolve host`)
- `7`: L3/L4 connect failure (`Connection refused`, `No route to host`, `Network is unreachable`)
- `22`: HTTP 4xx/5xx error (when `-f` / `--fail` is passed)
- `28`: Operation timeout (SYN dropped, read timeout)
- `35`: SSL/TLS handshake error (wrong version, non-TLS server on TLS port, middlebox reset)
- `60`: X.509 PKI verification failure (expired cert, untrusted CA, wrong hostname SAN, skewed system clock)
</details>

<details>
<summary>19. How does distributed training traffic (`torchrun` rendezvous vs. `NCCL` RDMA collectives) use—and bypass—this packet journey?</summary>

Job rendezvous (`torchrun` `c10d` store, MPI launch, and NCCL ring/tree setup) uses the **standard Linux TCP/IP journey** (`getaddrinfo`, routing table, ARP, `qdisc`, TCP sockets). Once initialized, bulk gradient/activation collectives (`AllReduce`, `AllGather`) use **RDMA verbs** over InfiniBand or RoCEv2 (**kernel bypass**): `libnccl`/`libmlx5` posts Work Queue Elements directly to the NIC hardware, which DMAs tensors straight out of GPU `HBM` (`GPUDirect RDMA`) and segments/acknowledges packets in NIC silicon—completely invisible to `tcpdump`, `ss`, and `iptables`.
</details>

<details>
<summary>20. What extra hops are added to a `curl` request when it originates inside a Kubernetes Pod?</summary>

(1) DNS queries go to **CoreDNS** with `ndots:5` search-domain expansion; (2) if the target is a Kubernetes `Service` VIP (`ClusterIP`), **`kube-proxy` (`iptables`/`IPVS`) or `Cilium` eBPF** rewrites the destination IP (DNAT) to a backing Pod endpoint IP; (3) the packet exits the container's network namespace across a **`veth` pair** into the host bridge or CNI router (and is optionally encapsulated in **VXLAN/Geneve**); and (4) **NetworkPolicy** filters check ingress/egress before the packet leaves the node's physical NIC.
</details>

## Sources and review notes

- **Sources read in full:**
  - `how-linux-works-3rd-edition` — Brian Ward, *How Linux Works*, 3rd ed., **Chapter 9: Understanding Your Network and Its Configuration** (packets, network layers, IP addresses, subnets, routes and default gateway, ICMP and DNS tools, Ethernet and kernel interfaces, name resolution via `nsswitch.conf`, `/etc/hosts`, `resolv.conf`, `systemd-resolved`, localhost, TCP ports and connections, UDP, DHCP, NAT, ARP/NDP) and **Chapter 10: Network Applications and Services** (services, `ssh`, `lsof`, `tcpdump`, `netcat`, sockets).
  - `networking-and-kubernetes` — James Strong and Vallery Lancey, *Networking and Kubernetes*, **Chapter 1: Networking Introduction** ("Guilty until proven innocent", IETF RFC states *Proposed Standard* vs *Internet Standard*, `ISO/IEC 7498-1..4` OSI model vs `RFC 1122` TCP/IP model, Protocol Data Units `PDU`s, Ethernet frame `8`-byte Preamble/SFD + `6+6`-byte MACs + `2`-byte EtherType + `4`-byte `FCS`, and the end-to-end `cURL` walkthrough).
  - `computer-networking-problems-and-solutions` — Russ White and Ethan Banks, *Computer Networking Problems and Solutions*, **Chapter 1: Fundamental Concepts** (packet switching, hop-by-hop forwarding, layered models, multiplexing, and interlayer discovery; cross-referenced with Chapters 2.2 to 2.10, 2.13 to 2.20, 2.22 to 2.26, 2.30, and 2.32, plus original study items 21–30).
- **Run here:** `python3 code/part02/curl_packet_journey_lab.py` (16 passed, 0 failed).
- **Explicitly labelled inferences:** The Section 13 AI-infrastructure comparison (container registry pulls, S3/GCS parallel HTTPS streams, `torchrun` TCP rendezvous vs `NCCL` kernel-bypass GPUDirect RDMA, and Kubernetes `ndots:5` + CNI path) connects the classic `curl` packet walkthrough to Part 5, Part 8, and Part 9 GPU cluster networking (plus original study items 23, 26, 27, and 29).
- **Not verified on live hardware:** All interactive VM commands (`curl`, `strace`, `getent`, `resolvectl`, `dig`, `ip route`, `ip neigh`, `tcpdump`, `arping`, `traceroute`, `mtr`, `ss`, `openssl s_client`) are marked (untested here) and should be executed on a disposable Linux VM.
