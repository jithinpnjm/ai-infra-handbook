# Voice sample 3: parts part-02-networking, part-16-mlops-llmops

## FILE docs/part-02-networking/01-what-happens-when-you-curl-a-url-a-packet-s-journey-end-to-end.md

Each route pairs a destination prefix with a way to reach it. That way is either directly on a link, as in `dev ens4 scope link`, or through a **gateway**, as in `via 10.0.0.1`. When several routes match, the kernel picks the **longest matching prefix**. The **default route**, `default via 10.0.0.1`, matches anything that no more specific route covers. Its IPv4 form is `0.0.0.0/0`, and its IPv6 form is `::/0`. Ties are broken by metric.

---

As you read the frame layout, keep in mind that the next hop's MAC is the one that goes in it. On the wire, an Ethernet II frame starts with an **8-byte Preamble + Start Frame Delimiter (`SFD`)**, which reads `10101010...10101011`. Next comes the **6-byte Destination MAC**. For traffic that leaves the subnet, this is the next hop's MAC, which is the gateway's, not the final destination's. The **6-byte Source MAC** is this NIC. The **2-byte EtherType** says what is inside: `0x0800` for IPv4, `0x86DD` for IPv6 or `0x0806` for ARP. Then come the **46 to 1,500-byte payload** and a **4-byte Frame Check Sequence (`FCS`)**, which is a CRC trailer.

---

Step 1: the router checks the destination against its **routing table**, using a longest prefix match in the FIB. Step 2: it decrements the **TTL**, also called the hop limit, and recomputes the header checksum for IPv4. If the TTL reaches zero, the router drops the packet and sends back an ICMP **Time Exceeded** message. That is how `traceroute` works.

---

On the server, a `listen()` socket keeps a SYN queue and an accept queue, which is the backlog. `accept()` returns a new socket for each connection. TCP then provides a reliable, ordered byte stream. It uses sequence numbers, acknowledgements and retransmission timers. Flow control runs through the receiver's advertised window, and congestion control runs through the sender's congestion window. That window goes through slow start, then congestion avoidance with CUBIC or BBR. Chapter 2.6 covers all of this.

---

## FILE docs/part-02-networking/02-how-networks-work-layers-encapsulation-the-tcp-ip-model.md

When a web page loads slowly, you need to know which part of the stack to blame. A protocol stack model gives you the map. It groups protocols by purpose and shows how the pieces fit together. Each layer talks to the layer above and below it through a well-defined interface. For example, the socket API sits between the application and the transport. Each layer also talks to its peer layer on the other machine, using a protocol.

---

Start with a standard 1500-byte MTU, the largest IP packet on ordinary Ethernet. A TCP/IPv4 segment can carry at most 1500 bytes minus 20 bytes of IP header and 20 bytes of TCP header. That leaves a maximum segment size, or MSS, of 1460 bytes of data. With the TCP timestamp option, the payload drops to 1448 bytes.

---

AI fabrics are a deliberate, controlled violation of layering. RDMA transport hardware is tightly integrated with link-layer flow control and a specific fabric design. The payoff is microsecond latency and zero CPU overhead. When you read a design, look for each layer violation and ask what it buys and what it costs.

---

Stretch makes this concrete. Stretch is the difference between the shortest physical path and the path traffic actually takes. Any policy, such as traffic engineering or PBR, increases stretch. The extra state and interaction needed to implement that policy is the price.

---

## FILE docs/part-02-networking/03-ethernet-and-l2-frames-mac-addresses-switching-arp-and-ndp.md

Read the counters this way. A rising `carrier_changes` means the link is flapping, which points to a cable, an optic, a transceiver seating, a switch port or power. Non-zero `rx_crc_errors` or uncorrected FEC means a marginal signal. `rx_discards` and `rx_out_of_buffer` mean the host cannot drain traffic fast enough, or that switch or NIC buffers overflow. `rx_pause` and `tx_pause` show that flow control is active. A NIC running at the wrong speed, such as a 400G NIC at 100G, points to a cable, an optic, a lane problem or a switch configuration.

---

Port-to-port latency in data-centre switches is on the order of 300 ns to 1 µs with cut-through, rising to several µs. At microsecond scales this matters for latency-sensitive workloads, and for multi-hop collectives that may cross 3 to 5 hops in a Clos fabric. Serialisation delay is the time it takes to put a frame on the wire. It equals frame size divided by link rate. A 1500-byte frame takes 120 ns at 100 Gb/s, and 12 µs at 1 Gb/s. A store-and-forward hop adds that delay every time.

---

Three implementation paths exist, from slowest to fastest. In **process switching**, the device interrupts its general-purpose CPU, which schedules a process to handle the packet. That is the slow path. In **interrupt-context switching**, the interrupt handler switches the packet itself, which is moderate. In **ASIC or NPU hardware switching**, a dedicated packet-processing chip uses specialised memory such as TCAM, SRAM and HBM, along with pipelines and recirculation. It runs at line rate, which is 12.8 to 51.2 Tb/s per chip.

---

Start by scanning. `iw dev wlp1s0 scan` lists the networks the radio can see. The interface must be up first. If it is not, run `ip link set wlp1s0 up`. You do not need an IP address yet, because scanning belongs to the physical layer. Once joined, `iw dev wlp1s0 link` shows the access point you are talking to. The MAC address in that output belongs to the access point.

---

## FILE docs/part-02-networking/04-ip-addressing-subnetting-and-cidr-ipv4-and-ipv6-with-practice.md

Going the other way is simpler. Add the weights of the bits that are 1. Some mask octets come up again and again, so memorise them: `0`, `128`, `192`, `224`, `240`, `248`, `252`, `254` and `255`. The non-zero values are runs of 1 to 8 leading ones.

---

In a normal subnet, two host numbers cannot go to a host. The all-zeros host part is the network address, which is the name of the subnet. The all-ones host part is the directed broadcast address. So a subnet with *h* host bits has 2^h − 2 usable addresses.

---

The block-size method works for a prefix between /24 and /30, where the split falls inside the last octet. The block size equals 256 minus the mask octet, which is also 2^(32 − p). Subnets start at multiples of the block size. The network address is the largest multiple of the block size that is at or below the host octet. The broadcast address is the next network minus 1.

---

Two addresses share a subnet when `(A AND mask) == (B AND mask)`. Here is a check you can run in your head. Take `10.20.37.130` and the prefix `10.20.36.0/22`. The mask's third octet is 252, so the block size is 4. The network covers third-octet values 36 to 39, which means 10.20.36.0 to 10.20.39.255. The third octet 37 falls inside that range, so the address is in the subnet. The address `10.20.40.1` has third octet 40, which is outside it.

---

## FILE docs/part-02-networking/05-routing-on-a-host-routing-tables-default-gateways-and-forwarding.md

Picture a storage mount that goes over the management network and saturates it. The fault sits in the routing table, not in the storage. A GPU server is a router in miniature. It has a routing table that decides which NIC every packet leaves by, and a default gateway for the world beyond its subnet. It often has several NICs on several networks: management, front-end, storage, and one NIC per GPU for the back-end fabric. In Kubernetes it also forwards packets for pods.

---

Read the rules from the top. They send lookups to `local`, then `main`, then `default`, in that order. Custom rules with a lower number have higher priority, and they add source-based routing. For example, `ip rule add from 10.100.1.45/32 table 101` followed by `ip route add default via 10.100.1.1 dev ens2f0 table 101` makes traffic sourced from that address use its own default gateway. Chapter 2.24 covers this in more depth. The kernel's routing cache was removed in 3.6, so lookups use the FIB trie directly, and each route carries its own attributes.

---

Suppose two links lead to the same destination, and both cost the same. A multipath route lets the host use both. A route can have several equal-cost next hops. The kernel picks one next hop per flow, using a hash, so that the packets of a flow stay in order.

---

If you see one of the following symptoms on your own server, the fixes below apply. Three symptoms show up. Lustre traffic uses the management NIC. NCCL occasionally uses the wrong interface. Some rail pings fail in one direction. The fixes follow.

---

## FILE docs/part-02-networking/06-tcp-in-depth-handshake-windows-congestion-control-retransmission.md

Why three packets? Each side has to prove it can both send and receive. Each side also has to agree on its starting sequence number. Two messages cannot do both things in both directions, so TCP needs three. The initial sequence numbers, or ISNs, are unpredictable. RFC 6528 describes a hash of the 4-tuple plus a secret. That stops off-path attackers from injecting data or forging connections. It also stops stale segments from an older connection on the same 4-tuple from being taken as new data.

---

TCP asks little of an application. The program only opens, reads from, writes to and closes a connection. To the program, the connection looks like a file with incoming and outgoing streams. Behind the scenes, TCP splits the outgoing stream into packets. It also reassembles incoming packets in order, even when they arrive out of order.

---

The second trigger is fast retransmit, and it is much cheaper. When the receiver gets segments beyond a gap, it repeats the ACK for the last in-order byte. That repeat is a duplicate ACK. After three duplicate ACKs, the sender retransmits the missing segment straight away, without waiting for the timer. It then enters fast recovery. The sender halves its window and keeps the pipe full, instead of restarting slow start. RACK can also trigger a retransmit on time, when a later segment is acknowledged beyond a time threshold.

---

1. Start with transport problems and flow control. Use chapters 2 and 3 of *Computer Networking Problems and Solutions* as your reference. (a) Contrast the three digital marshaling grammars: fixed-length fields, Type-Length-Value (TLV), and shared schemas or dictionaries. Then say where TCP uses the first two. (b) Distinguish flow control (`rwnd`) from congestion control (`cwnd`). State the formula for the most bytes a TCP sender may have in flight at any instant.
2. Work through the handshake, the server queues and the close states. (a) Explain why TCP needs a three-way handshake with unpredictable Initial Sequence Numbers (`RFC 6528`). Then explain how Linux's two listen queues cause connect stalls of 1 s, 3 s and 7 s when the `accept()` loop is slow. Use `tcp_max_syn_backlog`, `tcp_syncookies` and `min(backlog, net.core.somaxconn)` in your answer, and check `ListenOverflows` in `nstat`. (b) Contrast a server with 20,000 sockets in `TIME_WAIT` with one that has 20,000 sockets in `CLOSE_WAIT`.
3. Work through reliability, Nagle and delayed ACK. (a) Use `compute_jacobson_rto_ms()` in `code/part02/tcp_in_depth.py` to compute the RTO for a datacenter path (`SRTT = 0.2 ms, RTTVAR = 0.05 ms`) and for a WAN path (`SRTT = 150 ms, RTTVAR = 30 ms`). Then explain how Fast Retransmit (`3` dup ACKs), `SACK` (`RFC 2018`) and `RACK-TLP` avoid the `200 ms` `TCP_RTO_MIN` penalty. (b) Why does an RPC client that calls `write(header)` followed by `write(body)` suffer `~40 ms` latency spikes? Name the two fixes.
4. Compute the window and the BDP. (a) Using `compute_bdp_and_window_scale()`, compute the BDP in MB and the minimum window-scale shift for `100 Gb/s x 1 ms`, `10 Gb/s x 70 ms`, and `25 Gb/s x 40 ms`. (b) Using `compute_window_limited_throughput_mbps()`, calculate the maximum single-stream throughput of a `4 MB` window over `70 ms` RTT (`~457.1 Mb/s`) and over `80 ms` RTT (`400.0 Mb/s`). Then explain why calling `setsockopt(SO_RCVBUF)` in application code is an anti-pattern on Linux.
5. Compare congestion-control algorithms and AI incast. Using `simulate_congestion_loss_event()`, compare the new `ssthresh` and `cwnd` after 3 duplicate ACKs with those after an RTO, starting from `cwnd = 100 MSS`, under Tahoe, Reno and `CUBIC` (`β = 0.7`). Then contrast `CUBIC`, BBR (`fq` pacing) and `DCTCP` (`ECN`). Finally, explain why synchronized many-to-one AI collective bursts (**incast**) break loss-based TCP.
6. Diagnose TCP flows and compare QUIC. (a) How do `ss -ti` (`cwnd_limited`, `rwnd_limited`, `sndbuf_limited`, `retrans`) and `tcpdump` tell apart network packet loss, a slow receiving application (`win 0`), and a small send buffer? (b) List five architectural improvements that `QUIC` (`RFC 9000`, over UDP) makes over TCP plus TLS.

---

## FILE docs/part-02-networking/07-udp-icmp-and-the-diagnostic-tools-ping-traceroute-mtr.md

A training job has hung, or an inference endpoint has suddenly slowed down. The first question is whether the network is the problem, and if it is, where. A small toolkit built on UDP and ICMP answers that. You use `ping` to check reachability and latency. You use `traceroute` or `mtr` to see the path and the loss at each hop. For path MTU, `tracepath` and `ping -M do` do the work, and for UDP behaviour you reach for `nc -u` and `iperf3 -u`.

---

Hosts and routers also limit how fast they generate ICMP. On Linux, that is controlled by `net.ipv4.icmp_ratelimit` and `icmp_ratemask`. Routers deprioritise ICMP that they handle on the control plane. This changes how you read a traceroute. A hop that shows `* * *`, or high latency at one hop with normal latency after it, is usually control-plane rate limiting. It is not a real problem.

---

Now suppose the ICMP error is blocked. The sender never learns the limit. The TCP handshake still succeeds, because its packets are tiny, and small requests pass as well. But any packet above the path MTU is dropped silently and retransmitted forever. So large transfers hang. TLS handshakes with big certificates (the ServerHello flight), SSH key exchange and `scp` of big files hang the same way. Watch for these symptoms: `ssh` connects but hangs after `SSH2_MSG_KEXINIT`, `curl https://...` hangs after `Connected`, a website loads only partly, `git clone` stalls, or a small `ping` works while `ping -s 1472 -M do` fails.

---

`hping3` and `nping` let you test one specific TCP or UDP port path with custom flags and TTLs. They help with firewall debugging, and with traceroute through firewalls that block ICMP. Use them only on networks you own or are authorised to test.

---

## FILE docs/part-02-networking/08-dns-in-depth-resolution-records-resolvers-and-caching.md

`/etc/resolv.conf` holds `nameserver` lines, of which up to 3 are used. It also holds `search` domains for unqualified names, the `domain` line, and `options` such as `ndots:N`, `timeout:`, `attempts:`, `rotate` and `edns0`. The file is often a symlink managed by systemd-resolved (`/run/systemd/resolve/stub-resolv.conf`), NetworkManager, `resolvconf` or cloud-init. Hand edits are overwritten, so configure the manager instead, through netplan `nameservers`, `nmcli` or `resolved.conf`.

---

The nameserver is the **CoreDNS** service, called `kube-dns`. It resolves `<service>.<namespace>.svc.cluster.local` to ClusterIPs. For **headless** services, which StatefulSets and distributed training frameworks use, it returns pod IPs instead, such as `worker-0.trainer.ns.svc.cluster.local`. It forwards everything else to the node's upstream resolvers.

---

Alpine and musl have historically handled search lists and TCP fallback differently from glibc. Their `ndots` and parallel behaviour has also differed. Behaviour changes by image and version, so run your DNS tests inside the same image the pod uses.

---

Testing only with `dig` bypasses `/etc/hosts`, nsswitch and the search path, so a clean `dig` does not prove that DNS is fine. Editing a managed `/etc/resolv.conf` by hand is another trap, and running two managers that fight over the file is worse.

---

## FILE docs/part-02-networking/09-dhcp-nat-and-pat.md

You have two fixes. You can also SNAT, or masquerade, such traffic on the way, using `-s 10.0.0.0/24 -d 10.0.0.20 -j MASQUERADE`. Or you can use split DNS, so inside clients resolve the server's inside address. Split DNS is usually the better choice.

---

Most of what you learn here applies to these systems, with some changes. Embedded firmware usually uses BusyBox, a single program that offers limited versions of many Unix commands, such as the shell, `ls`, `grep`, `cat` and `more`. BusyBox saves memory. Its boot-time init is also simpler. In practice, custom firmware usually includes a web administration page, so you may rarely use the command line.

---

Counters tell you what the gateway actually did. Run `conntrack -S` to see the insert_failed, drop and early_drop counters, and `dmesg | grep conntrack` for kernel messages. `ss -s` gives a summary of sockets. `iptables -t nat -L -v -n` shows packet counters on each rule, and `nft list ruleset` shows counters too. Run `tcpdump -ni any host X` on both interfaces to compare what goes in and what comes out.

---

The first group of mistakes you will meet is about DHCP. Two DHCP servers on one segment, or a lab router left on, cause trouble. So do pools that overlap static addresses. Short leases for servers and reliance on one DHCP instance are mistakes too. A routed VLAN without a relay (`helper-address`), or a relay that points at the wrong server, leaves clients with no answer.

---

## FILE docs/part-02-networking/10-http-tls-and-pki-basics.md

The first line of each message matters most, so read it first when you debug. It holds the method and target in a request, and the status in a response. The table below lists the parts of a message. Methods matter most when you retry a call, because `GET`, `PUT` and `DELETE` are idempotent and `POST` is not.

---

Public CAs, such as Let's Encrypt, DigiCert and Google Trust Services, issue certificates for names that the Internet can reach. They check control of the domain, using DV (domain validation) through a DNS or HTTP challenge. OV and EV certificates add organisation checks. ACME (RFC 8555) automates issuance and renewal. Tools include certbot, acme.sh, Caddy and cert-manager. Let's Encrypt certificates last 90 days, and the industry is moving toward even shorter lifetimes. Automation is therefore mandatory.

---

Ingress and Gateway controllers, such as nginx, Envoy and cloud load balancers, can handle TLS in three ways. Terminating at the edge is simple, but the traffic is plaintext inside. You can re-encrypt to the backends. Or you can pass TLS through at layer 4, so the backend terminates it. Passthrough is needed for end-to-end mTLS.

---

Expiry is the next group. If you have no expiry monitoring or automated renewal, cluster certificates are forgotten for a year. Servers that omit the intermediate certificate break many clients, and certificates without a SAN fail name checks. Wildcard certificates copied everywhere have a large blast radius.

---

## FILE docs/part-02-networking/11-vlans-trunking-and-spanning-tree.md

Switching at layer 2 looks up the destination MAC in the bridge forwarding table. That table fills up through learning, covered in chapter 2.3, or through a control plane. The device finds the egress port and moves the packet from the input queue to that port's output queue without changing it. Routing at layer 3 works differently. It strips or ignores the old L2 header, then looks up the destination IP to find the next hop and egress interface. It consults the ARP or ND table for the next hop's MAC, rewrites the MAC header with new source and destination addresses, decrements the TTL, updates the checksum, and enqueues the packet. A modern "layer-3 switch" is a router whose lookup and rewrite run in hardware. Most data-centre "switches" actually route.

---

NIC offloads can hide tags from captures. For debugging, turn them off with `ethtool -K eth0 rxvlan off txvlan off`. Netplan, NetworkManager and systemd-networkd have VLAN stanzas for persistence. Containers and VMs usually attach to bridges, or to macvlan or ipvlan devices on VLAN sub-interfaces.

---

RSTP (802.1w, now part of 802.1D-2004) converges in about a second. It does this with a proposal and agreement handshake on point-to-point links. It defines the roles root, designated, alternate and backup, and the states discarding, learning and forwarding. Edge ports, which face hosts, go straight to forwarding. Cisco Rapid PVST+ runs RSTP per VLAN.

---

On servers, the link layer shows what a NIC is plugged into. LLDP (IEEE 802.1AB) and Cisco CDP advertise the device name, port ID, capabilities, VLANs and MTU. On Linux, use `lldpd` with `lldpcli show neighbors`, or use `lldptool`. NIC firmware LLDP agents are another source, and you reach them with `ethtool --show-priv-flags`. LLDP answers one question well: which switch port is this NIC plugged into? That is invaluable when you commission hundreds of GPU servers. You can compare the discovered topology with the intended wiring plan automatically. For InfiniBand, use `ibnetdiscover`, which Part 11 covers.

---

## FILE docs/part-02-networking/12-link-aggregation-lacp-and-mlag.md

Suppose you join two switches with two 100G links and expect traffic to split evenly. The obvious approach is round-robin: frame 1 goes on link A, frame 2 on link B, and so on. Round-robin maximises utilisation. The trouble is ordering. Frame 2 can overtake frame 1 on a faster or less congested path, so the receiver has to put them back in order.

---

TCP treats that reordering as loss. The result is duplicate ACKs, spurious fast retransmits and collapsed throughput. A few implementations use round-robin where reordering is tolerated. Linux `balance-rr` is one, and some RDMA fabrics use packet spraying with reordering-aware NICs. Almost everything else uses flow hashing.

---

Link aggregation is standardised as IEEE 802.1AX, which was formerly 802.3ad. It bundles several physical links between two devices into one logical link. Spanning tree and routing see the bundle as a single link, so STP does not block the members. The bundle carries more aggregate bandwidth than one member, and it survives member failures because traffic rehashes onto the remaining members.

---

Under the hood, MLAG relies on a proprietary control protocol. A peer link between the two switches synchronises MAC tables, LACP state, and ARP and ND. Both switches use a common virtual system ID, so the server sees one LACP partner. A keepalive path, often through the management network, detects peer failure and avoids split brain.

---

## FILE docs/part-02-networking/13-ip-routing-static-routes-dynamic-routing-and-convergence.md

Sometimes several sources offer a route to the same prefix. Administrative distance (AD) decides which source wins. The router compares AD first and looks at metrics only afterwards, because metrics from different protocols cannot be compared directly. Defaults vary by vendor. Cisco-style systems use the values in this table.

---

A router does two jobs that look similar but are separate. The data plane forwards packets using tables. The control plane builds those tables. The control plane has six jobs, and they repeat for as long as the network is up.

---

Proactive learning does the opposite. Reachability is distributed as soon as it is known, so every node has what it needs before traffic arrives. Almost everything in this chapter works this way. The hard part, and the one you should watch most closely, is reliable, consistent distribution, because one dropped update can create a permanent loop or blackhole. Protocols therefore use several safeguards. Sequence numbers on packets, or per-item NLRI with acknowledgements, make the distribution reliable. Database descriptions, which are lists or ranges of sequence numbers, are exchanged when a neighbour comes up and periodically after that. Sequence numbers can be paired with hashes so the receiver can verify content. Or a hash can cover a whole block of entries. Neighbours use these summaries to find and repair missing or corrupted entries. OSPF database exchange and the IS-IS CSNP and PSNP messages work this way. Keepalives close the loop. A route learned from a neighbour stays valid only while that neighbour is alive.

---

A loop-free alternate (LFA) is a backup next hop that cannot loop back to you. For a destination D, a neighbour N is a safe backup if N's own shortest path to D does not go back through you. The test is this loop-free condition:

---

## FILE docs/part-02-networking/14-ospf-and-is-is.md

The limits matter once a network grows. A single tree wastes capacity, converges slowly in its classic form, and has no hierarchy. Flat L2 domains also grow their broadcast load. That is why routing protocols took over the scale-out job. When your network outgrows one tree, plan on a routing protocol instead.

---

Choosing a route is simple too, and you can check it by hand. For each destination, a router takes the neighbour that advertises the lowest hop count, adds 1, and installs that route. A route that is not refreshed for 180 s times out. It is flushed after 240 s.

---

You have three ways to remove information. You can originate a newer fragment without the data. You can flood a zero-lifetime purge. Or you can let the lifetime expire, and nodes then re-flood the zero-age LSP. The protocol calls that last case flushing.

---

Start with the neighbour state. When an OSPF neighbour will not form, the state shown by `show ip ospf neighbor` tells you where it gets stuck. The table matches each stuck state to its likely causes and the checks that confirm them.

---

## FILE docs/part-02-networking/15-bgp-fundamentals.md

Suppose you need to know how a Kubernetes pod address reaches the rest of the network. The protocol that does that advertising is BGP. BGP is also the protocol that connects the Internet, and cloud providers use it at their edges. Direct Connect, Cloud Interconnect and ExpressRoute all rely on it. Since RFC 7938, it has carried most hyperscale and AI data-centre fabrics too.

---

BGP is a path-vector protocol. Each advertisement for a prefix carries the list of ASes it has crossed, called the `AS_PATH`. BGP is proactive, so it advertises routes without waiting for traffic. It learns destinations from configuration (`network` statements), from redistribution and from other protocols. It sends only best paths to neighbours, and it relies on TCP instead of a reliability layer of its own.

---

Once TCP is up, each peer sends an OPEN message. OPEN carries the BGP version (4), the sender's AS number, and the hold time. The lower of the two hold times is used. It also carries the BGP identifier (the router ID) and a 4-byte ASN capability. Optional capabilities cover multiprotocol extensions for the IPv4, IPv6, VPN and EVPN address families, route refresh, graceful restart, add-path and extended next hop.

---

Policy tells BGP what you want, and you express it with filters and attribute changes. You apply them inbound or outbound, per neighbour. Each tool either matches something, such as a prefix, an AS path or a community, or sets something, such as LOCAL_PREF. The table lists the common tools.

---

## FILE docs/part-02-networking/16-bgp-in-the-data-center-ebgp-clos-unnumbered-ecmp-anycast.md

This chapter explains the standard design and the reasons behind it. It shows how failure domains and information hiding keep the design stable. It then covers the newer approaches proposed for AI clusters: BGP link-bandwidth, DPF, IS-IS flood reduction and Flex Algo, RIFT, and segment routing.

---

Now suppose the spines had different ASNs. In the same multiple-failure case, the valley path would be installed. Forwarding becomes suboptimal, and latency rises. The path can also saturate the intermediate leaf's uplinks, which is a real concern with elephant flows on 400/800G links. With one spine ASN, the service sees only reduced capacity, or the destination becomes unreachable over that route. Traffic then shifts elsewhere.

---

Consider aggregation on the spine. Each spine advertises `10.10.0.0/16` for all server subnets below it. Suppose leaf3 loses its uplink to spine2, but still has spines 1, 3 and 4. Spine2 can no longer reach leaf3's `10.10.3.0/24`. Yet it keeps advertising the covering `/16` upward, because other leaves still reach other racks through it. Traffic from outside that hashes via spine2 toward leaf3's subnet is black-holed.

---

Start with verification. Every leaf should have N ECMP paths to every remote server prefix. `show ip route 10.10.5.0/24` should show 4 or 64 next hops. Loopbacks must be reachable, and `show bgp summary` should show all sessions Established. Prefix counts should match the design, so a leaf carries roughly the number of racks plus loopbacks. Look for unexpected longer AS-PATHs. From a server, `ip route get` with different source ports should hit different uplinks. Check that the MTU is consistent, with jumbo frames on all links, and that BFD is up on every session.

---

## FILE docs/part-02-networking/17-overlays-vxlan-and-evpn.md

To serve these needs, the IP network must provide an Ethernet-like service. It must do three things. It carries Ethernet frames inside an IP-routable encapsulation between edge routers or hypervisors. It learns which MAC addresses sit at which edge, and it draws traffic into the tunnel. It can optionally copy QoS markings, DSCP and PCP, from the inner header to the outer one. The MAC reachability can ride on a second control plane, or on one that already exists. This service is VXLAN with EVPN.

---

Each tenant gets an IP-VRF with an L3 VNI and import and export route targets. Type 5 routes carry the prefixes, including the default route from a border leaf toward external networks. Route leaking between VRFs happens by importing route targets.

---

A central controller or orchestrator distributes policy and reachability. Edges measure path quality, meaning loss, latency and jitter, with probes. They then steer applications by policy. Voice might take the best path while bulk traffic takes the cheap one. Zero-touch provisioning brings the edges up, so you do not configure each one by hand.

---

Underneath, the same ideas apply: encapsulation, a reachability control plane, often an overlay BGP or OMP, and policy-driven path selection. For this chapter, the relevance is that multi-site GPU clouds, hybrid cloud connectivity and edge inference sites often use SD-WAN or its cloud-native equivalents. Those equivalents are cloud routers, transit gateways and Cloud Interconnect.

---

## FILE docs/part-02-networking/18-data-center-topologies-clos-leaf-spine-oversubscription-failure-domain.md

The disadvantages are real, though. A leaf failure isolates whole servers. Per-rail traffic isolation inside the leaf needs extra features, such as deterministic path forwarding or colored fabrics, which chapter 2.16 covers. Latency between servers on different leaves is two hops for everything.

---

The benefits follow from that design. Link utilisation stays near perfect, because cell spraying removes ECMP imbalance. The ingress keeps a virtual output queue for each egress port, and it holds those queues across the whole fabric. A scheduler grants credits, so the fabric is never oversubscribed, and contention is avoided before it happens. That approaches non-contending behaviour. Tail latency drops, and congestion is simpler to handle than with DCQCN alone.

---

A quick recap of VOQ helps here, because the rest of the section depends on it. Each input keeps a virtual queue for each output port. Congestion at one output therefore does not block traffic headed to the others, which removes head-of-line blocking. With a fabric-wide VOQ, the same principle extends across the whole network.

---

Availability is usually stated in nines. 99.9%, three nines, allows about 8.8 hours of downtime per year. 99.99% allows about 52.6 minutes per year. The source describes this as about an hour. 99.999% allows about 5.3 minutes per year. Define what counts as down before you quote a number. It might be the whole network, a service, a tenant, a rail, or a percentage of capacity. For AI, a degraded fabric such as 7/8 rails may be available for a job but still fail the SLO.

---

## FILE docs/part-02-networking/19-queuing-qos-ecn-pfc-and-dcb-basics.md

Several common DSCP values have a familiar job. EF (46) is expedited forwarding for low-latency traffic such as voice. The AF classes are assured forwarding, with 4 classes and 3 drop precedences each. CS6 and CS7 carry network control. CS3 and CS4 carry signalling and streaming. DF or CS0 is best effort.

---

Deployments differ on where PFC runs. Some configure it only on leaves and NICs, and others configure it on all nodes. Some run ECN-only, with no PFC, and rely on good load balancing and NIC loss recovery. The ECN-only option depends especially on newer NICs that tolerate loss. The right answer depends on the SLA, the hardware and your measurements.

---

NIC-side parameters are vendor-specific. They include the initial rate, the rate-increase timers and steps, the alpha update gain, the rate-decrease factor, the CNP generation interval (for example 50 µs), the minimum time between CNPs, the ECN marking trust (DSCP), and the CNP priority or DSCP. Misconfigured NIC parameters are a classic cause of poor performance, even when the switch configuration is correct. Check the NIC parameters with the same care as the switch settings.

---

To apply DCB, start by defining 8 priorities. Next, assign each traffic type to a priority by DSCP, PCP or port. Then mark which priorities are lossless, with PFC enabled, and set the ETS weights. Last, choose how DCBX runs. You can set willing or non-willing modes consistently. Or you can disable DCBX and push the configuration explicitly through automation. The second option is common in AI clusters, where it avoids surprises.

---

## FILE docs/part-02-networking/20-load-balancing-l4-l7-ecmp-hashing-and-proxies.md

1. Where is the decision made: on the client, in DNS, in the network with ECMP, on a dedicated L4 device, on an L7 proxy, or on the server?
2. What identifies a unit of work: a packet, a flow or connection, an HTTP request, a gRPC stream, or a token-generation job?
3. How is a backend chosen, by which algorithm and with what state?
4. How does the reply return: through the LB as a proxy or NAT, or directly as DSR?
5. How are failures detected and handled, through health checks, outlier detection, retries and draining?

---

Picture two backends behind one address and a stream of requests of very different sizes. The balancer must choose a backend for each request, and the rule it uses decides how evenly the work spreads. The table compares the common rules, what each one looks at, and where each one breaks.

---

In step 2, a node fails or is drained. Its BGP session drops, and BFD makes that happen in under a second. The router removes the node from the ECMP set, so flows that hashed to it get remapped. With plain modulo hashing, all flows may be rehashed, and existing connections break. With resilient or consistent hashing in the router, only the flows of the failed node move.

---

HTTP/2 and gRPC put many requests on one connection. At L4, balancing happens per connection, so all streams from one client connection go to one backend. That is connection pinning. You can fix it in three ways. Use an L7 proxy that balances per request or per stream, such as nginx `grpc_pass`, Envoy, HAProxy with `proto h2`, or ALB for gRPC. Balance on the client side with `round_robin` across resolved addresses, or with xDS. Or cap the connection age with `MAX_CONNECTION_AGE`, so clients reconnect and rebalance.

---

## FILE docs/part-02-networking/21-network-security-firewalls-tls-and-zero-trust.md

Use MFA for administrative access and VPNs, because it combines something you know, something you have and something you are. Hardware keys (FIDO2) resist phishing well. Pair MFA with least privilege and just-in-time access. Keep admin accounts separate, and avoid shared accounts.

---

Run scans from at least two vantage points, the host itself and another network, ideally one outside your perimeter. That shows what the firewall really blocks. Scan only networks you own or have written permission to test. Scans get logged, they can disrupt fragile devices, and they may break policy or the law.

---

There are two main types of vulnerability: direct attacks and cleartext password sniffing. A direct attack tries to take over a machine without subtlety. A common start is an unprotected service, such as an administrator account with no password. Once an intruder controls one service, the intruder can try to compromise the whole system.

---

Keep secrets out of images and environment dumps. Use Kubernetes Secrets with encryption at rest, backed by an external store such as Vault or KMS, and issue short-lived credentials. Rotate tokens, and use workload identity in place of long-lived cloud keys on nodes.

---

## FILE docs/part-02-networking/22-linux-networking-inspecting-state-with-ip-ss-and-counters.md

The Netplan file below gives one server three different kinds of interface. One is a DHCP link, one is a static fabric NIC with a 9000 MTU, and the third is a VLAN on top of the first link. Apply it with `sudo netplan try`, as the comment in the file says.

---

Read the `NAME` column first. A path such as `/var/run/mysqld/mysqld.sock` names a socket file. The word `socket` marks an unnamed socket. Many applications use unnamed sockets, so the list can be long. Look for the program name you care about.

---

Break latency into parts, and find the part that grows. Name resolution (DNS) can time out for tens of seconds. Ping and RTT show the path. TCP connection latency is the handshake, and first-byte latency is the server's think time plus the RTT. Connection life span matters too, because short-lived connections multiply the handshake cost. Per-request latency comes from the application itself. The tools for this are `curl -w` timing variables, `dig +stats`, `tcpconnlat`, `tcpdump` timestamps, the `rtt` field from `ss -ti`, `mtr`, and application tracing. Compare what you measure against expected values. Rack-local 100G traffic should take tens of microseconds, same-DC traffic 0.2 to 0.6 ms, and cross-continent traffic 40 to 180 ms.

---

Capturing at full line rate is impractical on a fast network. Filter narrowly, and truncate the packets with `-s 128`. Use ring buffers (`-C`, `-W`), capture on the NIC with hardware timestamps, or sample with sFlow, IPFIX or `tcpdump -c`.

---

## FILE docs/part-02-networking/23-linux-networking-netfilter-nftables-conntrack-and-nat.md

Many components add rules to that same path. kube-proxy installs thousands of NAT rules, and container runtimes add masquerade and port-publish rules. CNIs add policy chains, cloud agents add their own, and the host firewall sits underneath all of them.

---

Test every change with `nft -c -f` first, and keep a second session open. When you edit a remote firewall, add a safety timer, such as `sleep 60 && nft flush ruleset &` or `at`, so that a lockout clears itself.

---

Watch for asymmetric routing, because it also breaks conntrack. If you run several gateways, requests and replies may take different paths. If requests and replies take different paths through different gateways, the second gateway sees replies without a flow and marks them INVALID. Design NAT gateways with symmetric paths, or share state with `conntrackd`.

---

Some traffic never reaches netfilter at all. Cilium attaches eBPF programs at the XDP and TC hooks, so it performs load balancing and policy before netfilter. It can run many flows without conntrack, because it keeps its own maps. For GPU and RDMA traffic, the fast path uses the NIC and bypasses the kernel stack entirely, as RoCE does. Host netfilter never sees that traffic, so apply isolation at the switch or the NIC instead (chapter 2.21).

---

## FILE docs/part-02-networking/24-linux-networking-policy-routing-bonding-mtu-nic-and-stack-tuning.md

Getting the last 50% of bandwidth and the last 50 microseconds of latency means understanding how packets leave and enter the host. You need to know which routing table applies to which source address. You also need to know how interrupts and queues map to cores and NUMA nodes, which offloads are on, how big the rings and buffers are, what the MTU is end to end, and which TCP knobs matter.

---

Imagine two groups of interfaces that both use 10.9.0.0/24. A VRF gives each group its own routing table, so the two networks stay apart. A **VRF** (virtual routing and forwarding) device is that kind of group. It is lighter than a network namespace, because processes still share sockets, files and other stack state. VRFs are central to multi-tenant leaf switches, the kind that run Cumulus or SONiC, and they are useful on hosts too.

---

`MSG_ZEROCOPY` and `sendfile()`/`splice()` avoid user-space copies. A static file, for example, is DMAed from the page cache to the NIC with no CPU copy. That saves two copies and context switches. Set socket options in the application that owns the socket, and only where a measurement justifies them.

---

The default `fq_codel` or `mq` qdisc is fine for most hosts. The `fq` qdisc gives per-flow pacing, which BBR required on older kernels, and it is useful alongside `SO_MAX_PACING_RATE`. The `mq` qdisc creates one qdisc per TX queue, which avoids lock contention. Check drops and requeues with `tc -s qdisc show dev eth0`. Heavy shaping with `htb` on 100G links costs a lot of CPU, so prefer NIC rate limits or switch policing.

---

## FILE docs/part-02-networking/25-linux-networking-namespaces-veth-bridges-and-container-networking.md

A **network namespace** is a complete, independent copy of the network stack. Each copy has its own network interfaces, IP addresses, routing tables, ARP and ND neighbour tables, netfilter rules, conntrack table, `/proc/net`, sockets, port numbers, and sysctls under `net.*`. Processes inside a namespace see only that namespace. The namespace also solves the "one TCP/IP stack per OS" problem that motivated hypervisors, and it does so without a separate kernel.

---

Kubernetes does not use Docker's CNM. It uses CNI, a simpler specification that came from CoreOS and now belongs to the CNCF. A CNI **plugin** is an executable. You give it a JSON network configuration and some environment variables that describe the container, and it configures networking for that container. CNI needs no daemon, and it is cross-platform.

---

You can test a plugin by hand before you trust it. Create a namespace, then run `CNI_COMMAND=ADD CNI_CONTAINERID=x CNI_NETNS=/run/netns/test CNI_IFNAME=eth0 CNI_PATH=/opt/cni/bin /opt/cni/bin/bridge < config.json`, or use `cnitool`. Run `ADD` first, because that call creates the interface and the address. Then run `DEL` to check the cleanup.

---

5. Topology alignment. Use the kubelet Topology Manager, with its `single-numa-node` or `best-effort` policy, together with the CPU Manager and the device plugins. That keeps the GPU, its NIC VF or RDMA device, and the CPUs on the same NUMA node or PCIe root. Verify the layout with `nvidia-smi topo -m` and `ibdev2netdev`.

---

## FILE docs/part-02-networking/26-packet-capture-from-scratch-tcpdump-tshark-and-wireshark.md

You can run `tcpdump` on the host where the problem shows up. The commands below cover the common cases, from listing interfaces to rotating files. Each line keeps the flags you need and a short note on what it does.

---

A capture filter is an expression built from primitives. Each primitive can carry a qualifier, such as a type (`host`, `net`, `port` or `portrange`), a direction (`src`, `dst` or `src or dst`) and a protocol (`ether`, `ip`, `ip6`, `arp`, `tcp`, `udp`, `icmp`, `icmp6` or `vlan`). You join the pieces with `and`/`&&`, `or`/`||` and `not`/`!`, and group them with parentheses when the order matters.

---

Wireshark offers more analysis than the command line does. Its Statistics menu covers conversations, endpoints, protocol hierarchy, IO graphs and TCP stream graphs. The Analyze menu opens Expert Information, which flags retransmissions, duplicate ACKs, zero windows, out-of-order segments, full windows and resets. TCP stream graphs show the time-sequence view, throughput, RTT and window scaling. Follow TCP, UDP or TLS stream reassembles a conversation for reading. Decode As maps a port to a dissector, so you can treat UDP 4791 as RoCE or a custom port as VXLAN or GENEVE. To decrypt your own TLS in a lab, set `SSLKEYLOGFILE` in the client, for example `SSLKEYLOGFILE=/tmp/keys.log curl ...`, and point `Edit → Preferences → Protocols → TLS → (Pre)-Master-Secret log filename` at the same file. Setting the time display to the time since the previous displayed packet reveals gaps, and coloring rules, packet comments, exported objects and `File → Export Specified Packets` help you share only the evidence you need.

---

Options matter as well. If one side's SYN has no window scale and the other side's does, a middlebox may be stripping options, and throughput is then limited to 64 KB per RTT. Retransmissions come in three kinds: normal, fast and spurious. Three duplicate ACKs trigger a fast retransmit, and SACK blocks show which ranges actually arrived. A zero window means the receiving application is slow to read. A window full result means the sender is limited by the receive window, while bytes in flight below the cwnd means the application itself is the limit.

---

## FILE docs/part-02-networking/27-lab-build-network-topologies-with-namespaces-frr-and-containerlab.md

containerlab runs `exec` commands after a node starts. To build `br0` on each leaf, add `exec: [ "ip link add br0 type bridge", "ip link set eth3 master br0", "ip link set eth4 master br0", "ip link set br0 up", "ip link set eth3 up", "ip link set eth4 up" ]` to each leaf node. A start-up script or the `kind: linux` `cmd` option does the same job in practice. Timing matters here. FRR reads `frr.conf` at startup, so create `br0` before FRR starts. If that is not possible, restart FRR after `exec` runs, with `docker exec clab-fabric-leaf1 /usr/lib/frr/frrinit.sh restart`.

---

1. Build two sites, in namespaces `s1` and `s2`, and join them with a router called `core`. Build GRE, IPIP, VXLAN and WireGuard tunnels between `s1` and `s2`, and assign overlay addresses. Ping through each tunnel. Then capture traffic on the core, and compare the outer and inner headers.
2. Compute the usable MTU of each tunnel, and verify it with `ping -M do -s N`. Compare your results with the table in chapter 2.17. Clamp the MSS, and then test a large `iperf3` transfer.
3. Compare the throughput and CPU use of plain routing with the tunnels. Use `mpstat` to measure the CPU. Expect the WireGuard crypto cost to show up here, and test with VXLAN offloads turned off.
4. Show ECMP entropy by sending many flows over a two-path core. GRE and IPIP flows share one path, unless inner-header hashing is enabled with `sysctl net.ipv4.fib_multipath_hash_policy=2`. VXLAN and WireGuard flows spread across both paths by their outer UDP port.
5. Try a segment routing mini-demo. For SRv6, run `ip route add 10.9.9.0/24 encap seg6 mode encap segs fc00:2::1,fc00:3::1 dev eth0` across IPv6 routers that have `seg6_enabled` set. For MPLS, load the modules with `modprobe mpls_router mpls_iptunnel`, and then run `ip route add 10.9.9.0/24 encap mpls 100/200 via inet 10.0.0.2`.

---

1. On the Lab 3 fabric, run nginx or a small HTTP server on h11 and h12. On another host, add an L4 load balancer node, either HAProxy or IPVS in DR mode. Announce its VIP to the leaf over BGP from FRR. Then verify that remote hosts reach several LB nodes through ECMP.
2. From h41, run `wrk` or `hey` against the VIP. Kill one LB node and one backend, then measure the error rates and the recovery time.
3. Test connection pinning with `grpcurl` or `ghz` against a simple gRPC server, first through L4 and then through L7.
4. Add delay and loss to a leaf-spine link with `tc netem`. Then observe the BGP and BFD behaviour, the TCP throughput with `ss -ti`, and any ECMP imbalance.
5. Finish with a failure matrix. Cover each failure (link, spine, leaf, host NIC, LB node, backend) and each observer (ping, TCP flow, HTTP request). Record the packet loss, the recovery time and what recovered the service.

---

Run the harness in CI. A GitHub Actions job works, as long as the runner can run Docker and containerlab. A self-hosted runner also works. The job deploys the fabric, runs `python3 validate.py`, runs the failure tests, and then destroys the fabric. You can extend the job with three kinds of check. Convergence budgets assert how many pings a link failure may lose. Configuration-drift diffs compare `vtysh -c 'show running-config'` with the generated files. Pcap-based assertions catch anything unexpected, such as an ICMP error that should not appear. For network automation and CI/CD patterns, see chapters 2.28 and 2.29. For Ansible and Terraform integration, see Part 4.

---

## FILE docs/part-02-networking/28-network-automation-fundamentals-apis-yang-netconf-gnmi-sdn-templates.md

Keep two kinds of content apart. A **document** is text written for people, with free layout that is meant to be read. **Data** is made of typed fields that a program can query, validate and combine. Data formats fall into two groups. Text formats such as YAML, JSON, XML, TOML, INI and CSV are readable and easy to diff. Binary formats such as Protocol Buffers, Apache Thrift, FlatBuffers, BSON, MessagePack, CBOR and Python pickle are compact and fast.

---

Data then flows to collectors such as gNMIc, Telegraf's `gnmi` input, Cisco Pipeline, and Juniper JTI with Telegraf or OpenNTI. From there it reaches time-series stores such as Prometheus through exporters, InfluxDB or VictoriaMetrics. Dashboards and alerts come last, and chapter 2.31 covers them.

---

A centralised control plane is, at heart, a distributed database problem. During a network partition, you cannot have both consistency and availability. This is the **CAP theorem**, and partitions are unavoidable, so you must choose. The **subsidiarity principle** gives a practical rule. Make each decision at the lowest level that can make it correctly, and centralise only what truly needs a global view.

---

In practice, keep fast, local and safety-critical reactions in the distributed layer. Failure detection, ECMP rerouting and fast reroute belong there. Centralise slow-changing, global policy such as traffic engineering, intent and segmentation. Finally, make sure the network keeps forwarding if the controller disappears. Fail static, or fall back to the distributed control plane.

---

## FILE docs/part-02-networking/29-network-automation-in-practice-ansible-nornir-and-ci-cd-for-networks.md

Variables follow a precedence order. In simplified form, from lowest to highest, it runs through role defaults, then inventory group variables (`all`, then the parent group, then the child group), then inventory host variables, playbook variables, `vars_files`, role variables, task variables, and finally extra variables passed with `-e`. Keep per-group variables in `group_vars/<group>.yml` and per-host variables in `host_vars/<host>.yml`. Put design constants in `group_vars/all`.

---

Automation reduces the interaction surface between humans and devices. It does not reduce complexity in general. The complexity moves into the toolchain, the data models, the templates and the pipeline. Use the state, optimisation and surface lens to see where it went. Automation can add state, through the source of truth, caches and pipeline artefacts. It can reduce optimisation, because abstractions hide device-specific tuning. It can reduce or move interaction surfaces, which means fewer typing mistakes but more integration points. Plan for the new failure modes: bad data, template bugs at scale, pipeline outages, credential compromise of the automation system, and skill concentration. The automation system is a very high-value target, so protect it as carefully as the network itself. If you have not found the trade-off yet, you have not looked hard enough.

---

Costs and trade-offs come in several forms. Software datapaths limit throughput, and you can improve it with DPDK, SR-IOV, kernel bypass, NIC offloads, XDP, DPUs, CPU pinning, NUMA and hugepages. Stateful functions need failover and state sync. Generic hardware gives up the optimisation that ASICs offer. There are also more layers to operate, from hypervisor to vSwitch to orchestrator, and licensing and operations add to the bill.

---

Choosing a tool before you define the data model, source of truth and process is a common error. Pushing to every device at once, with no canary, no automatic rollback and no out-of-band access, leaves nothing safe to fall back on.

---

## FILE docs/part-02-networking/30-network-troubleshooting-method-and-case-studies.md

1. Map the path of the signal through the system. The signal is something you can test: a flow's packets, a neighbour adjacency, jitter at one point, the completeness of a stream, or a request.
2. Split the path roughly in half.
3. Test the signal at the midpoint. Is it correct?
4. If it is incorrect, move toward the source. If it is correct, move toward the destination.
5. Repeat on the remaining half.

---

At each test, ask two questions. What is the actual state of the system and the signal here? What should normal look like? The method forces you to look and compare with the baseline. It also keeps you tied to the larger context, so you do not dive into a plausible component that is only a symptom. The method fits networks well. Choose the path of the failing flow with `traceroute`, `ip route get` or an ECMP-aware `mtr`. Capture at the midpoint with a packet capture or counters, and then bisect.

---

Read the diagram as a set of questions. A refusal (RST) points to a firewall reject or a wrong port or address. A timeout means a packet was lost somewhere, so you half-split the path and capture at the midpoint and both ends. If the connection works, the problem sits higher up, in DNS, TLS, authentication or the application itself.

---

For each fault, you write the symptom as the application sees it. Then list the hypotheses, ranked by likelihood. Record the half-split points you chose and the evidence that confirmed the cause. Finish with the immediate and permanent fixes, and name the alert or test that would have caught the fault earlier.

---

## FILE docs/part-02-networking/31-network-monitoring-and-telemetry.md

Once the collectors run, a handful of metric families carry most of the signal. Traffic and error counts come from `node_network_receive_bytes_total`, `node_network_transmit_bytes_total`, `node_network_receive_errs_total` and `node_network_receive_drop_total`. Link state and speed come from `node_network_up`, `node_network_speed_bytes` and `node_network_mtu_bytes`. TCP retransmits and softirq pressure come from `node_netstat_Tcp_RetransSegs`, `node_netstat_TcpExt_*`, `node_softnet_dropped_total` and `node_softnet_times_squeezed_total`. Conntrack usage comes from `node_nf_conntrack_entries` and `_limit`. Driver counters, including PFC and discard counters, appear as `node_ethtool_*`. InfiniBand traffic and errors come from `node_infiniband_port_data_transmitted_bytes_total` and `node_infiniband_*_errors_total`. Congestion counters such as `node_infiniband_port_transmit_wait` vary in name by version, so verify them on your build.

---

Each packet carries the L2 and L3 headers, then the **IFA header** (version, namespace, protocol type, flags, max length), then the original L4 header. After that come the **IFA metadata header** (action, hop limit) and the **metadata stack**, which follows `draft-kumar-ippm-ifa-08`. The fabric MTU has to absorb the extra bytes, and jumbo frames normally do.

---

Some problems cannot be fixed instantly, such as congestion that lasts microseconds. Monitoring still tells you the origin and size of the problem, so you can make a sound decision. Ask whether the loss is constant or periodic. Ask whether it sits on one interface or many, on one switch or several, and whether it lines up with a job phase. Depending on severity, the worst-case decisions include shutting down the server at the origin of congestion, restarting the learning process at the scheduler, or evacuating to a site with better capacity. Know which of these your applications can tolerate, such as the checkpoint cadence or elastic training.

---

The monitoring path must not share fate with what it monitors. Put it on an out-of-band management network, run redundant Prometheus pairs, and remote-write to a second site. Add a watchdog alert that always fires, which proves the alert pipeline works. Then monitor the monitors.

---

## FILE docs/part-02-networking/32-cloud-networking-vpc-peering-load-balancers-and-gcp-specifics.md

A typical setup looks like this. Training bursts run on rented H100/H200/B200 nodes, inference endpoints sit in several regions, and datasets live in object storage. Checkpoints are replicated across sites, managed Kubernetes (GKE, EKS, AKS) hosts the serving layer, and private links connect everything to corporate data centres.

---

5. Security in the cloud has several parts. Protecting data over public transport uses IPsec or WireGuard VPNs, TLS, MACsec on dedicated links, and HA VPN over Interconnect. Managing secure connections means handling the key lifecycle, certificates and tunnel monitoring. The shared responsibility model splits the work: the provider secures the cloud, and you secure what you put in it, which means identity, configuration and data. Add least-privilege IAM, private access paths so traffic to cloud services stays off the Internet, and firewalls at several layers.

---

Newer generations, such as A3 Ultra and A4, move to RDMA over Converged Ethernet (RoCE). They use dedicated RDMA VPC networks and many 400G NICs per node. Check the current documentation for three things: the exact network profile, which for these is the `RDMA` profile, the MTU requirements, and the NCCL plugin and driver versions you need.

---

Start with the Python lab, which you can run for free. It runs on your own machine at zero cloud cost, and it checks the capacity arithmetic and the rules from this chapter. The lab covers three things. First, GKE VPC-native capacity: a `/20` node subnet plus a `/14` pod range gives `1,024` maximum nodes and `4,096` Services. Second, VPC Network Peering non-transitivity and CIDR overlap checks. Third, validation of the load balancer health-check firewall ranges, `35.191.0.0/16` and `130.211.0.0/22`.

---

## FILE docs/part-16-mlops-llmops/01-mlops-foundations-and-lifecycle.md

1. The cluster you built is where MLOps errors show up. When a model silently degrades, the symptom looks like a queue spike or a burst of 5xx errors. That alert pages you, the platform engineer, not the person who trained the model. You need to read the lineage and the metric history without paging five teams.
2. ML workloads stress GPU clusters in ways the earlier parts did not. A misconfigured notebook can submit a job that runs for two weeks and blocks the queue. Checkpoint writes can drain a parallel file system. A large model can be pulled into GPU memory and never evicted. Lifecycle discipline stops these mistakes before they reach the cluster.
3. LLMOps, the focus of Part 16, is MLOps plus new failure modes. Fine-tunes, retrieval pipelines, agent loops and prompt regressions are all machine learning system problems at heart. The MLOps foundations come first, because the LLMOps details only make sense on top of them.

---

In the experimentation phase, the data scientist moves fast. Every step is a hypothesis, the code can be messy, and the run time is whatever the laptop allows. The deliverable is a metric on a held-out set. In the development, staging and production phase, every step is an artifact. The training script is the same script, the data is a frozen snapshot, and the environment is a fixed container image. The output is a model bound to a registry entry and a deployment record.

---

This lab runs on GCP and GKE. It walks you through experiment tracking (Capability 1) and data versioning (Capability 2), from start to finish. The lab is **untested** in the sense that the cluster is not yet provisioned in this repository. The structure and commands are a working template. When you run it on a real GKE cluster, follow the steps in order, and check each `expected` line before you move on.

---

Last, deploy the staged model behind KServe. The InferenceService below points at a model file, and KServe serves it over HTTP. The resource requests and limits are example values for a small model, so size them from your own load tests.

---

## FILE docs/part-16-mlops-llmops/02-data-versioning-and-experiment-tracking-dvc-mlflow-weights-and-biases.md

1. Explain why data versioning needs content-addressed storage and a metadata layer. Show how DVC, lakeFS, Pachyderm and Delta Lake each supply that layer.
2. Run a training job that opens an experiment run as its first action. The job writes the run record, the data hash, the commit hash and the artifact before it prints a metric.
3. Compare runs on one metric, on a group of metrics, on a per-segment metric and on a parallel-coordinates plot.
4. Hand a run to a model registry, sign the artifact, and refuse unsigned artifacts at the cluster boundary.
5. Choose among DVC, MLflow and Weights and Biases for a given team, and know when to combine them.
6. Operate the tracking server and the artifact store on GKE, with a backup policy, an SLO and an access model that survives a change of staff.

---

The `dataset_id` is the address. The `content_hash` is the proof that the bytes at that address are the bytes the training script saw. A script that resolves a `dataset_id` through the metadata database cannot drift silently. A script that reads a raw path can.

---

1. **The backing store.** MLflow needs a metadata database, which this chapter takes to be Postgres, and an artifact store such as S3, GCS or MinIO. Both get backups and SLOs. Both get access policies that separate the people who write artifacts from the people who read them.
2. **The access model.** Training service accounts can write to an experiment. Data scientists can read their own experiments and the shared ones. The promotion pipeline can write to the registry, and auditors can read everything.
3. **The retention policy.** Run records are kept indefinitely. Artifacts are kept for a set window. Section 5.3 gives one example policy. Failed runs are kept for 30 days, and promoted runs are kept indefinitely. Artifacts are soft-deleted, never overwritten.
4. **The SLO.** The tracker sits on the hot path of every training job, so a slow tracker can time out the job itself. The chapter's example targets are a p99 under 200 ms to open a run, under 500 ms to log a metric, and under 5 s to put an artifact. These are example values. Measure your own baseline before you commit to any target.

---

DVC and MLflow work well together. DVC drives the pipeline stages, and MLflow logs what each stage did. The `.dvc` files carry the data hash. The MLflow run carries the same hash as a tag, so both records point to the same content.

---

## FILE docs/part-16-mlops-llmops/03-data-pipelines-and-feature-stores.md

The previous chapter gave the training script and its dataset permanent addresses. This chapter builds the pipeline that produces those artifacts. A run record is only as reproducible as the pipeline that fed it the bytes. A feature store lets two teams share one feature definition instead of rewriting it from scratch.

---

Every stage follows one pattern: an artifact, a hash, and a gate. The gate is a check that runs without a person deciding anything. The hash proves what the artifact contains, and the next stage uses the artifact's address to find it.

---

Practical MLOps Chapter 5 covers AutoML and KaizenML. Designing Machine Learning Systems Chapter 10 walks through the integration patterns. The pattern that holds is the one from Chapter 16.2: every artifact has an ID, every stage has a gate, and every gate is mechanical. Check all three before you connect an orchestrator.

---

The parity check matters most. It runs hourly, samples random pairs of entity ID and timestamp, reads both views, and checks that the values match bit for bit. Any drift is urgent, because every model trained on the offline view depends on it.

---

## FILE docs/part-16-mlops-llmops/04-pipeline-orchestration-kubeflow-pipelines-argo-flyte-airflow.md

Your team has a notebook that trains a model. Now the model must retrain on a schedule, with a record of every run. Four orchestrators are common answers to that need. They look different on the surface, but they share one conceptual model.

---

Suppose your team already runs Kubernetes and wants pipelines without learning a new framework. Argo Workflows is built for that case. You write each DAG in YAML, and each stage runs as a Kubernetes pod. Argo has no Python layer and no hidden services, which keeps the stack small.

---

Flyte's type system and its first-class support for `pandas.DataFrame`, `numpy.ndarray`, and structured types make it a strong fit for data-heavy ML. *Practical MLOps* Chapter 5 describes Flyte's origin at Lyft and its growth into an open-source project under the Linux Foundation.

---

1. What orchestrator is the cluster running?
2. What is the namespace and service account for the team's pipelines?
3. What is the freshness check that the DAG runs first?
4. Where do the DAG's artefacts land (object store URI, lifecycle policy)?
5. What is the gang scheduler that the multi-GPU DAG uses?

---

## FILE docs/part-16-mlops-llmops/05-distributed-compute-for-ml-ray-kuberay-training-operator-and-katib.md

Suppose your feature code runs fine on a laptop, but the dataset no longer fits there. You want the same Python to run on many machines without a rewrite. That is the problem Ray is built for. Ray gives you a small set of primitives: tasks, actors and objects. Libraries sit on top of those primitives, and each one targets a specific ML job.

---

The Training Operator fits jobs with a fixed topology and a known run time. You declare the topology at submit time, so the operator does not autoscale mid-job. It gang-schedules through Volcano or KAI, and it retries through the standard pod retry policy.

---

Some jobs need fast links between their GPUs. If one job spans two NVLink domains, its high-bandwidth collectives may not finish inside the NCCL timeout. Topology binding prevents that. A node affinity rule pins all the pods to one NVLink domain.

---

This lab installs KubeRay, the Kubeflow Training Operator and Katib on GKE. It then runs a distributed training job and a hyperparameter sweep. The lab is **untested** in this repository, so treat the commands and YAML as a working template. You run each step in order, and each step names the output you should expect.

---

## FILE docs/part-16-mlops-llmops/06-model-registry-ci-cd-and-gitops-for-models.md

Suppose an auditor asks, a year from now, which data and code produced the model version that made a bad decision. If the registry cannot answer, the team has a model with no history. *Designing Machine Learning Systems* Chapter 9 and *Practical MLOps* Chapter 4 agree on what the registry must store. A registered model is a model version plus the metadata that makes it reproducible, auditable, and ready to roll back. The contract stays the same across MLflow Registry, Vertex AI Model Registry, SageMaker Model Registry, and Weights and Biases Registry.

---

Treat the training image as the supply chain boundary. Its CUDA version, cuDNN version, and Python packages shape every model trained from it. If you cannot prove what went into the image, you cannot prove what went into the model. *Practical MLOps* Chapter 4 asks for a simple discipline. Build the image once, sign it once, and store it where the cluster can verify it. The promotion pipeline should refuse to start a training job from an unsigned image.

---

The diagram shows the situation. Git asks for v7 in staging and v6 in production. The reconciler reads both sides and writes the registry to match. A pull request that moves `version: 7` into `production.yaml` is the only way to promote v7.

---

Large language models follow the same registry, canary, and rollback patterns as classical models. Two things change. The artifact is much larger, so a rollback takes longer. The model is also often served across several nodes instead of one pod. The promotion gate changes too, because the evaluation suite from Chapter 16.9 and a prompt regression test join the checks.

---

## FILE docs/part-16-mlops-llmops/07-model-serving-platforms-kserve-seldon-and-bentoml.md

Seldon Core predates KServe. It defines its own CRD, `SeldonDeployment`, and it uses Istio for traffic routing. Its main strength is the `graph` field, which chains models, ensembles, and routers. That matters for a RAG pipeline, where a retriever and a generator must work as one unit.

---

Consider a model that gets only a handful of requests a day. Keeping a GPU reserved for it all day wastes most of that hardware. *Generative AI on Kubernetes* Chapter 1 makes the case for scale-to-zero, and KServe supports it with `minReplicas: 0`.

---

The price is the cold start. The first request after the replicas go away waits seconds, not milliseconds. *Production Kubernetes*, chapter 13, adds a warning here. Workloads with container images over 1 GB and startup scripts that run for minutes respond slowly to scaling events, so they are poor candidates for autoscaling.

---

KServe does not judge the canary itself. Your pipeline, or a tool such as Argo Rollouts, watches the SLO and then raises the percentage or sets it to 0. Earlier drafts of this section had the canary field layout wrong. The layout above was checked against the upstream KServe repository.

---

## FILE docs/part-16-mlops-llmops/08-llmops-rag-vector-databases-and-agents.md

Treat the prompt template as an artifact, as Chapter 16.1 Section 5.2 describes. Keep it in Git, so every change has an author and a diff. The eval suite from Chapter 16.9 then checks that a template change does not lower accuracy.

---

Treat the loop as a pipeline with two brakes. The iteration cap is the maximum number of tool calls per request. The cost cap is the maximum number of tokens one request may burn. Both caps are structural, which means the agent runtime refuses to go past either one.

---

Every LLM request costs money, and the bill arrives at the end of the month. To control that bill, you first need to see which parts of a request cost what. *LLMOps* Chapter 6 walks through the cost model. Several parts add up to the cost of one request.

---

Fix: Tie the index snapshot id to the corpus snapshot id, so each answer shows how old its index is. Alert when the index age passes the freshness SLO. Add a check in the retrieval pipeline that refuses to serve when the index is older than the policy window. This is the same fix as Chapter 16.3 Section 7.5.

---

## FILE docs/part-16-mlops-llmops/09-llm-evaluation-and-guardrails.md

The golden set is the most expensive part. Hand-labelling a golden set takes weeks, even at the small end of the size range above. Invest in it once, then reuse it for every prompt and model change. It is also your audit trail. It records that the LLM gave correct answers on these inputs, at this prompt version and this model version.

---

The system prompt is the most effective jailbreak defence you have. It declares what the LLM may and may not do, and the LLM is fine-tuned to follow it. The classifier is the second line of defence, and the system prompt is the first.

---

1. What is the current golden set pass rate?
2. What is the current regression set pass rate?
3. What is the safety filter false-positive rate?
4. What is the jailbreak filter false-negative rate?
5. When was the last eval-set refresh?

---

1. Add a regression test for a new failure mode. Find a recent production failure you have seen, add it to the regression set, and confirm the test catches it. *Solution sketch:* a JSON entry in `eval/regression-v4.jsonl`, and a CI step that runs the new entry.
2. Reduce LLM-as-judge bias. Switch the judge to a different model family, then check whether the bias drops. *Solution sketch:* change the `judge-model` config to another family, rerun the suite, and compare scores.
3. Add a factuality filter to a RAG application. Wire the filter into your RAG pipeline, and check that it rejects hallucinations. *Solution sketch:* a middleware in the RAG InferenceService that calls the factuality judge and rejects answers below the threshold.
4. Build a jailbreak regression set. Collect 50 published jailbreak attempts, add them to the regression set, and confirm the classifier catches them. *Solution sketch:* a JSONL file with 50 prompts and an expected refusal, plus a CI step that asserts the model refuses.
5. Log PII detections. Wire the PII filter into your InferenceService, and write every detection to the audit log. *Solution sketch:* a middleware that calls the PII detector and writes each detection to the audit log.
6. Schedule the eval-set refresh. Run the refresh as a Kubernetes CronJob. *Solution sketch:* a CronJob that runs `refresh_eval_set.py` on the first day of each quarter.

---

## FILE docs/part-16-mlops-llmops/10-monitoring-drift-and-continual-learning.md

Use the ground truth as soon as it arrives. While you wait, a proxy signal can stand in for it. A proxy is an estimate, not a measurement, so treat it as an early warning rather than a verdict. Fast proxies give feedback in minutes to hours, and the ground truth confirms or corrects them later.

---

A new model is ready, but you are not yet sure it is safe for every user. Four mechanisms let you compare it with the live model while you limit the risk. *Designing Machine Learning Systems* Chapter 9 introduces shadow mode and A/B testing for this job.

---

A noisy drift detector can fire every hour. The cluster then spends its time retraining, and no new model reaches production. A cooldown prevents this. It stops the trigger from firing again until a set time has passed since the last run.

---

1. Add a feature-drift detector. Use Evidently to compute the KS statistic for each feature, and alert when it exceeds 0.1. *Solution sketch:* a CronJob runs Evidently on the last hour of features, writes the result to Prometheus, and raises an alert on the metric.
2. Add a performance-triggered retraining. Fire the retraining DAG when live accuracy drops below the threshold. *Solution sketch:* a metric computes live accuracy, and an alert fires the DAG on a threshold breach.
3. Add a retraining cooldown. Make your trigger refuse to fire until 24 hours have passed since the last fire. *Solution sketch:* a Postgres table records the last fire time, and the trigger checks that table before it fires.
4. Add a proxy-signal evaluator. Use a proxy, such as a cancellation page view for churn, to fire the performance trigger before the ground truth arrives. *Solution sketch:* a metric reads the proxy signal from the feature store, and an alert fires when the proxy's correlation with actual churn drops.
5. Add a production shadow stage. Run the new model on 100% of traffic in shadow for 24 hours before the canary. *Solution sketch:* a Knative route sends all traffic to the canary, the canary's responses are discarded, and its metrics are compared with the live model's.
6. Add a drift dashboard. You build a Grafana dashboard that shows drift score per feature, prediction drift per class, live accuracy, and retraining trigger history. *Solution sketch:* export the dashboard as a JSON file, import it into Grafana, and pin it to the team's home dashboard.

---

## FILE docs/part-16-mlops-llmops/11-cloud-mlops-platforms-vertex-ai-sagemaker-and-azure-ml.md

Three managed stacks cover this ground today: Vertex AI on GCP, SageMaker on AWS, and Azure Machine Learning on Azure. Each one bundles a studio (a notebook and IDE), a pipeline orchestrator, a feature store, a model registry, and an endpoint service for serving models. You get all five from one vendor, under one bill.

---

Vertex AI is the most Kubernetes-friendly of the three. Vertex AI runs custom training jobs, pipelines and endpoints as Google-managed services; you do not operate a GKE cluster for them. If your platform team already runs GKE, you have a head start. A team on EKS or AKS can still use Vertex AI, but it pays for cross-cloud networking.

---

SageMaker is the most AWS-native of the three, and that comes with a trade-off. Studio is opinionated, and its pipelines do not carry over cleanly to other clouds. In return, IAM, the VPC, KMS, and observability all use AWS's own services. If you already run on AWS, most of the identity and networking work is familiar.

---

Managed compute usually costs more per hour than self-hosted GPU capacity, and that gap is why the hybrid split exists. The managed stack buys convenience, and self-hosted capacity buys a lower unit price. Your job is to find the point where the convenience is worth the difference.

---

## FILE docs/part-16-mlops-llmops/12-nvidia-enterprise-stack-ai-enterprise-ngc-and-licensing.md

The subscription is priced per GPU, per year. The price depends on the GPU class and the length of the commitment. Your job is to track the per-GPU license, because finance will see it as a line item. Ask for the GPU class and commitment length behind any quote before you sign.

---

If every node pulls the same large image from NGC, you waste bandwidth and depend on NGC being reachable at all times. The cluster therefore does not pull directly from NGC. It pulls through a proxy that your platform team runs, and the proxy does four jobs.

---

Suppose a product team needs a chat model in production by the end of the week. They could download the weights, pick an inference engine, and tune it themselves. NIM is NVIDIA's packaged answer to that work. It is a Docker image that bundles a model, an inference engine such as TensorRT-LLM, vLLM, or Triton, and the runtime. NVIDIA signs the image, licenses it, and supports it.

---

An LLM app can answer a question it should refuse, or repeat personal data from its context. Guardrails are the rules that stop those answers. NeMo Guardrails is the runtime safety layer, and you write its rules as programmable steps the model must follow.

---

## FILE docs/part-16-mlops-llmops/13-governance-privacy-and-compliance-for-ml-platforms.md

The regimes overlap, so one control can serve several of them. A consent record satisfies GDPR and CCPA. An audit log satisfies HIPAA, SOC2, and SR 11-7. A model card satisfies the EU AI Act and SR 11-7. When you design a control, list every regime it serves, because that list shows how much work the control saves you.

---

Your promotion gate must refuse a model whose card is missing or out of date. The gate from Chapter 16.1, Section 4.3, enforces that rule. A model card written after launch records the model, but it does not control the model.

---

Picture a customer who asks a company to delete everything it holds about them. GDPR Article 17, the right to erasure, requires the controller to erase that data "without undue delay". The erasure reaches the warehouse, the feature store, and the training data. It also touches the model, which is a derived artefact. Model weights are not personal data per se, but the training data is.

---

Next, make the training pipeline write a lineage edge for each model it trains. The helper below emits one edge, from the dataset to the model. Run it after each training job, so the edge exists before anyone asks for it.

---

## FILE docs/part-16-mlops-llmops/14-platform-design-multi-tenant-ai-factory-quotas-and-chargeback.md

1. Design a multi-tenant primitive for every shared resource.
2. Enforce per-team GPU quotas with Kueue or Volcano, at admission time.
3. Build a FinOps dashboard that shows cost per team, per model, and per month.
4. Feed the dashboard's cost data into chargeback.
5. Let a team request a namespace, a GPU quota, a model registry, and a serving endpoint in minutes.
6. Run the platform on GKE with IAM, network policies, observability, and SLOs that match the business.

---

Kubernetes assumes that every Pod can reach every other Pod. On a shared platform, that assumption lets one tenant's workload talk to another tenant's services. A default deny-all policy reverses it. Tenants are isolated the moment they join, and each connection they need must be declared.

---

Picture two teams. One runs exploratory notebooks on spare capacity. The other runs a production model that cannot wait in line. One tier for both would serve neither well. Tiers match each team's use case and budget to a quota.

---

An SLO becomes useful when you turn it into a budget. Suppose a team promises a p99 latency of 200 ms, an example value. p99 means 99 percent of requests finish within that target. The error budget is the share of requests allowed to miss it, and the team can spend that share.

---

## FILE docs/part-16-mlops-llmops/15-lab-end-to-end-mlops-on-gke.md

Training is where cost and risk meet. It takes a GPU pool, real data, and a seed, and it produces the model you will later defend to a regulator. The Argo Workflow below makes each run repeatable, and MLflow records what that run used.

---

The function below makes two checks before it registers anything. First, it refuses a run that lacks any of four required tags. Second, it refuses a run whose AUC is below the baseline's AUC. A blocked run returns 1, which lets the caller fail the stage.

---

The lab forces drift on purpose, so you can see the trigger fire without waiting for real drift. The sleep is a crude wait. In practice, you would watch the trigger's logs instead. The threshold in the example output, 0.2, is an example value. Choose your own threshold after you tune it on your production traffic.

---

The capstone is also the integration test for the MLOps stack. A change to a chart, a policy, or an onboarding file can break a path that only the full run exercises. Running the capstone in CI catches that before it reaches production.

---

