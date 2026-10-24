---
id: "c02-25"
title: "2.25 Linux networking IV: namespaces, veth, bridges and container networking"
sidebar_label: "2.25 Linux networking IV: namespaces, veth, bridges and container networking"
sidebar_position: 25
description: "Network namespaces, veth, bridges, macvlan/ipvlan, Docker networking, CNI, Multus and pod networking for GPU clusters"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 2.25 Linux networking IV: namespaces, veth, bridges and container networking

| | |
|---|---|
| Level | Intermediate to advanced |
| Priority tier | 0 |
| Lab venue | Linux VM with root; Docker/containerd; kind for CNI exercises |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Every containerised GPU workload gets its networking from a handful of kernel primitives: a network namespace per pod or container, a veth pair into the host, a bridge or routed path, and NAT or an overlay between nodes. When a training pod cannot reach the parameter server, when NCCL picks the pod's `eth0` instead of the RDMA interface, when throughput inside a pod is a fraction of the host's, or when a CNI upgrade breaks pod-to-pod traffic, you debug these primitives. GPU clusters add a twist: multi-NIC pods that need secondary RDMA interfaces (Multus, SR-IOV, macvlan), host networking for collective libraries, and CNIs chosen for performance rather than convenience. This chapter builds container networking from first principles (namespaces, veth, bridge, routing, NAT), then covers Docker's network modes, the CNI specification and common plugins, how Kubernetes pod networking works across nodes, and how to design and debug networking for GPU pods.

## Prerequisites and outcomes

You should know IP routing and forwarding (2.5), VLAN/bridging (2.11), netfilter and NAT (2.23), overlays (2.17), and cgroups/namespaces (Part 1, chapters 1.18 to 1.20).

After this chapter you can:

- Create, inspect and debug network namespaces; connect them with veth pairs, Linux bridges, routing, macvlan and ipvlan; give them NAT and DNS.
- Explain what a container's network is: its own interfaces, routes, conntrack, iptables rules, and `/etc/resolv.conf`.
- Describe Docker's network modes (bridge, host, none, overlay, macvlan, container) and the container network model (sandbox, endpoint, network).
- Explain CNI: the plugin interface (ADD/DEL/CHECK, JSON config), IPAM plugins, chained plugins, and how kubelet/containerd invoke it; compare Flannel, Calico, Cilium, AWS VPC CNI, Antrea, Multus.
- Trace pod-to-pod traffic on one node and across nodes (bridge, routed, overlay), pod-to-service and pod-to-external flows.
- Design pod networking for GPU workloads: host network vs CNI, secondary networks with Multus, SR-IOV VFs and RDMA, MTU, NUMA/topology alignment, NetworkPolicy.
- Debug container networking with `nsenter`, `ip netns`, `crictl`, `tcpdump` inside namespaces, and by following hops.

## 1. Network namespaces

A **network namespace** is a complete, independent copy of the network stack: its own network interfaces, IP addresses, routing tables, ARP/ND neighbour tables, netfilter rules, conntrack table, `/proc/net`, sockets, port numbers, and sysctls under `net.*`. Processes inside a namespace see only that namespace. This is why two containers can each run a server on port 8080 on the same host: each has its own port space. It also solves the "one TCP/IP stack per OS" problem that motivated hypervisors, without a separate kernel.

```bash
sudo ip netns add red                             # creates /run/netns/red (a bind mount to the namespace)
ip netns list
sudo ip netns exec red ip link                    # run any command inside; initially only a down loopback
sudo ip -n red link set lo up                     # '-n' is shorthand for netns exec for ip commands
sudo ip netns exec red bash                       # a shell inside the namespace
sudo ip netns del red
lsns -t net                                       # all network namespaces and their processes
sudo nsenter -t <pid> -n ip addr                  # enter a process's (container's) namespace by PID, run host tools inside
ls -l /proc/<pid>/ns/net                          # identity of a process's netns (compare inode numbers)
```

Container runtimes create anonymous namespaces (not under `/run/netns`); to inspect them, find the container's PID (`docker inspect -f '{{.State.Pid}}'`, `crictl inspectp`, `kubectl` + node access) and use `nsenter -t PID -n`. A **pod** in Kubernetes shares one namespace among its containers (created by the pause/sandbox container), so containers in a pod talk via `localhost`.

### Interfaces across namespaces

A physical NIC lives in exactly one namespace. A virtual interface can be moved (`ip link set X netns Y`). Namespaces are connected using virtual devices:

| Device | What it is |
|---|---|
| **veth pair** | Two linked virtual NICs: what goes in one end comes out the other, even across namespaces: a virtual patch cable |
| **bridge** | Software L2 switch joining several interfaces (veths, physical NICs, VXLAN devices) |
| **macvlan** | Sub-interface of a parent NIC with its own MAC; packets go straight to the wire; container appears as a separate host on the parent's LAN |
| **ipvlan** | Sub-interface sharing the parent's MAC with its own IP (L2 or L3 mode); good when switches limit MACs per port |
| **dummy / tun / tap / wireguard / vxlan / vrf** | Special devices used by VPNs, overlays, VMs, routing isolation |
| **SR-IOV VF** | Hardware virtual function placed directly into a namespace |

## 2. Building container networking by hand

Container networking is these primitives assembled by software. Doing it manually once is the best way to understand it.

```bash
# 1. Two "containers" (namespaces) connected through a bridge on the host, with NAT to the outside
sudo ip link add br0 type bridge ; sudo ip addr add 10.10.0.1/24 dev br0 ; sudo ip link set br0 up
for n in c1 c2; do
  sudo ip netns add $n
  sudo ip link add veth-$n type veth peer name eth0-$n          # host end, container end
  sudo ip link set eth0-$n netns $n                              # move the container end into the namespace
  sudo ip link set veth-$n master br0 ; sudo ip link set veth-$n up
  sudo ip -n $n link set lo up ; sudo ip -n $n link set eth0-$n name eth0 ; sudo ip -n $n link set eth0 up
done
sudo ip -n c1 addr add 10.10.0.11/24 dev eth0 ; sudo ip -n c2 addr add 10.10.0.12/24 dev eth0
sudo ip -n c1 route add default via 10.10.0.1 ; sudo ip -n c2 route add default via 10.10.0.1
sudo ip netns exec c1 ping -c2 10.10.0.12                     # container to container via the bridge (L2 switching)
# 2. Outbound access: forwarding + masquerade for the container subnet
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -s 10.10.0.0/24 ! -o br0 -j MASQUERADE
sudo iptables -I FORWARD -i br0 -j ACCEPT ; sudo iptables -I FORWARD -o br0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo ip netns exec c1 ping -c2 8.8.8.8
# 3. Inbound port publishing: host:8080 -> c1:80 (DNAT)
sudo iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.10.0.11:80
sudo iptables -t nat -A OUTPUT -p tcp -d 127.0.0.1 --dport 8080 -j DNAT --to-destination 10.10.0.11:80     # for local clients
# 4. DNS inside: per-namespace resolv.conf under /etc/netns/<ns>/resolv.conf
sudo mkdir -p /etc/netns/c1 && echo "nameserver 1.1.1.1" | sudo tee /etc/netns/c1/resolv.conf
```

This is almost literally what Docker's default bridge network does: create `docker0`, a veth per container, an IPAM-assigned address from a private pool, a default route via the bridge, masquerade for outbound, DNAT for published ports, and a bind-mounted `/etc/resolv.conf`.

The data path for container A → container B on the same bridge: A's stack (routing: same subnet, ARP for B) → A's `eth0` (veth peer) → host-side veth → bridge (MAC learning, forwards to B's veth) → B's `eth0`. Netfilter hooks in the bridge path (`br_netfilter`, `net.bridge.bridge-nf-call-iptables=1`) let iptables see bridged traffic; Kubernetes requires this setting so kube-proxy rules apply to pod-to-pod traffic through bridges. For A → external: A's default route via the bridge IP → host IP stack → FORWARD → POSTROUTING masquerade → out the NIC with the host's address; return traffic is un-NATed by conntrack and delivered back through the bridge.

```mermaid
flowchart LR
  subgraph NS1["netns c1 (10.10.0.11)"]
    E1["eth0"]
  end
  subgraph NS2["netns c2 (10.10.0.12)"]
    E2["eth0"]
  end
  subgraph HOST["host netns"]
    V1["veth-c1"] --- BR["br0 10.10.0.1\n(L2 bridge + L3 gateway)"] --- V2["veth-c2"]
    BR --> RT["IP stack: routing, netfilter (FORWARD, MASQUERADE)"] --> NIC["eth0 (host IP)"]
  end
  E1 --- V1
  E2 --- V2
  NIC --> W["Network"]
```

Alternatives to bridge+NAT: **routed veth** (no bridge: one /32 route per container pointing at its veth host end, with proxy ARP or routing protocol; Calico's model), **macvlan** (container on the physical LAN with its own MAC; host-to-container communication on the same parent doesn't work without a macvlan sub-interface on the host), **ipvlan L3** (container IPs routed through the parent; no MAC explosion), **host networking** (no namespace), and **SR-IOV/DPDK** (hardware or user-space bypass).

```bash
# macvlan: container directly on the LAN (bridge mode among macvlans on the same parent)
sudo ip link add mv0 link eth0 type macvlan mode bridge ; sudo ip link set mv0 netns c1
sudo ip -n c1 addr add 192.168.1.60/24 dev mv0 ; sudo ip -n c1 link set mv0 up
# ipvlan L3: shared MAC, routed
sudo ip link add ipv0 link eth0 type ipvlan mode l3 ; sudo ip link set ipv0 netns c2
```

## 3. Docker networking

Containers originated in LXC (cgroups + namespaces) and were popularised by Docker with a friendly image format, registry and runtime, later standardised by the Open Container Initiative (OCI: composable, decentralised, minimalist specs; runc is the reference runtime; containerd and CRI-O are the container runtimes used by Kubernetes). Docker's network model, libnetwork's **container network model (CNM)**, has three concepts: **sandbox** (a container's network namespace configuration), **endpoint** (a container's attachment point to a network, typically a veth), and **network** (a group of endpoints that can communicate). Drivers: *local* drivers (bridge, host, none, macvlan, ipvlan) are per-host; *global* drivers (overlay) need a distributed key-value store for coordination.

| Mode | Behaviour | Use |
|---|---|---|
| **bridge** (default `docker0`; or user-defined bridges) | Private subnet, veth per container, NAT outbound, `-p` publishes via DNAT; user-defined bridges add DNS-based container name resolution and isolation | Single-host development, simple services |
| **host** (`--network host`) | Container shares the host namespace; no isolation, no NAT, best performance, ports conflict with host | NCCL/HPC containers, performance-critical, packet capture tools |
| **none** | Only loopback | Isolation, custom networking (CNI-like setups), batch jobs without network |
| **container:NAME** | Shares another container's namespace | Sidecars (this is how a Kubernetes pod works) |
| **overlay** | VXLAN across Docker hosts (Swarm) | Multi-host before Kubernetes |
| **macvlan / ipvlan** | Container on the physical network | Legacy apps needing LAN addresses |

```bash
docker network ls ; docker network inspect bridge
docker run -d --name web -p 8080:80 nginx ; iptables -t nat -S DOCKER ; ip -br link | grep -E 'docker0|veth'
docker run --rm --network host nicolaka/netshoot ss -tulpn          # debug container with a toolbox
docker run --rm --network container:web nicolaka/netshoot tcpdump -ni eth0     # sniff inside another container's netns
bridge link ; bridge fdb show br docker0 ; cat /proc/sys/net/bridge/bridge-nf-call-iptables
```

Docker's published ports bypass host firewalls managed by ufw/firewalld because Docker inserts its own NAT/FORWARD rules (chapter 2.23); restrict with `DOCKER-USER` or bind addresses. Docker's default subnet (172.17.0.0/16) may overlap with corporate or VPN ranges: set `default-address-pools` in `/etc/docker/daemon.json`. In production GPU clusters, Docker's network features are rarely used directly; Kubernetes with CNI replaces them.

## 4. CNI: the Container Network Interface

Kubernetes did not adopt the CNM; it uses **CNI**, a simpler specification from CoreOS (now CNCF): a CNI **plugin** is an executable that, given a JSON network configuration and environment variables describing the container, configures networking for it. It needs no daemon and is cross-platform.

### How it works

1. The container runtime (containerd, CRI-O) creates the pod sandbox (a network namespace, usually held by the `pause` container).
2. The runtime reads the CNI configuration (`/etc/cni/net.d/*.conf|*.conflist`) and executes the plugin binary from `/opt/cni/bin/` with environment variables `CNI_COMMAND` (`ADD`, `DEL`, `CHECK`, `VERSION`), `CNI_CONTAINERID`, `CNI_NETNS` (path of the namespace), `CNI_IFNAME` (e.g. `eth0`), `CNI_ARGS`, `CNI_PATH`, with the network config on stdin.
3. The plugin creates interfaces (veth, macvlan, ...), moves one end into the namespace, calls an **IPAM plugin** (`host-local`, `dhcp`, `static`, or a CNI-specific allocator) for an address, sets routes, and returns a JSON result (IPs, routes, DNS).
4. On pod deletion, the runtime calls `DEL` to clean up. Plugins may be **chained** (a `.conflist` runs several in order: e.g. `bridge` → `portmap` → `bandwidth` → `tuning`).

```json
{
  "cniVersion": "1.0.0",
  "name": "mynet",
  "plugins": [
    { "type": "bridge", "bridge": "cni0", "isGateway": true, "ipMasq": true, "mtu": 1450,
      "ipam": { "type": "host-local", "subnet": "10.244.1.0/24", "routes": [ { "dst": "0.0.0.0/0" } ] } },
    { "type": "portmap", "capabilities": { "portMappings": true } },
    { "type": "bandwidth", "capabilities": { "bandwidth": true } }
  ]
}
```

Reference plugins (containernetworking/plugins): *main* (`bridge`, `ptp`, `macvlan`, `ipvlan`, `host-device`, `vlan`, `loopback`, `dummy`), *ipam* (`host-local`, `dhcp`, `static`), *meta* (`tuning` for sysctls, `portmap`, `bandwidth`, `firewall`, `sbr` for source-based routing, `vrf`). Test a plugin manually: create a netns and run `CNI_COMMAND=ADD CNI_CONTAINERID=x CNI_NETNS=/run/netns/test CNI_IFNAME=eth0 CNI_PATH=/opt/cni/bin /opt/cni/bin/bridge < config.json`, or use `cnitool`.

### Kubernetes network model (requirements)

Kubernetes assumes: every pod gets its own IP; **all pods can communicate with all other pods without NAT** (across nodes); agents on a node (kubelet) can reach all pods on that node; pods see their own IP as others see it. How the cluster satisfies this is the CNI's job: overlay (VXLAN/Geneve/IPIP), routed (BGP, host routes), or cloud-native (VPC-assigned pod IPs).

### Common CNI implementations

| CNI | Data path | Notes |
|---|---|---|
| **Flannel** | Simple L3 overlay (VXLAN default; host-gw routed mode) using Kubernetes API/etcd for allocations | Minimal; no NetworkPolicy by itself |
| **Calico** | Routed (BGP via BIRD or Felix), optional IPIP/VXLAN overlay, eBPF dataplane; iptables/ipsets policy | Strong NetworkPolicy; no overlay needed with BGP; scales; integrates with fabric BGP (chapter 2.16) |
| **Cilium** | eBPF datapath replacing kube-proxy/iptables, identity-based policy L3-L7, optional VXLAN/Geneve or native routing, Hubble observability, BGP control plane | High performance; requires modern kernels |
| **AWS VPC CNI / GKE native / Azure CNI** | Pod IPs are VPC/subnet addresses (ENIs, alias IPs) | No overlay; pod IPs routable in the cloud network; IP exhaustion and per-node ENI limits |
| **Antrea** | Open vSwitch-based, Geneve/VXLAN, policy | OVS offload options |
| **Weave, Canal, kube-router, Kube-OVN** | Various | |
| **Multus** | **Meta-plugin** that attaches multiple CNI interfaces to a pod (NetworkAttachmentDefinition CRDs) | Required for secondary RDMA/SR-IOV interfaces |
| **SR-IOV CNI + device plugin**, **macvlan/ipvlan/host-device CNI** | Moves a VF/NIC into the pod's namespace | RDMA/GPUDirect data plane for AI |

## 5. Kubernetes pod networking walkthrough

### Same node, bridge-based CNI (e.g. bridge/Flannel host-gw)

Pod A → A's `eth0` (veth) → host-side `vethXXX` on bridge `cni0` → pod B's veth → B. The pod CIDR for the node (e.g. 10.244.1.0/24) is local; the node has the bridge IP as gateway. With routed CNIs (Calico), each pod has a /32 route on the host pointing to its veth (`10.244.1.5 dev caliXXXX scope link`) and proxy ARP answers the pod's ARP for its default gateway (169.254.1.1); pod-to-pod on the same node goes pod → veth → host routing → veth → pod, with no bridge.

### Different nodes

- **Overlay (VXLAN/IPIP/Geneve)**: pod A (10.244.1.5) → host → route says 10.244.2.0/24 via the tunnel device (`flannel.1`, `tunl0`, `vxlan.calico`) → encapsulated in UDP (or IP-in-IP) to node 2's IP → decapsulated → delivered to pod B (10.244.2.7). Costs: MTU, CPU, hidden pod IPs from the fabric. Debug: `ip route | grep 10.244`, `bridge fdb show dev flannel.1`, `tcpdump -ni eth0 udp port 8472` (Flannel/Cilium VXLAN) or `4789`.
- **Routed (BGP/host-gw)**: node 1 has `10.244.2.0/24 via <node2 IP>` (installed by static config, BIRD, or the CNI daemon); no encapsulation; requires L2 adjacency between nodes (host-gw) or a fabric that learns pod prefixes via BGP. Best performance; pod IPs visible in the fabric (easy firewalling and monitoring).
- **Cloud-native**: pod IPs allocated from the VPC subnet; fabric routes natively.

### Pod to service and to the outside

Pod → ClusterIP: kube-proxy (iptables/IPVS) or eBPF DNATs to a backend pod (chapter 2.20/2.23); pod → external: masquerade (SNAT to node IP) unless pod IPs are routable and `ipMasq` is off; external → pod: NodePort/LoadBalancer/Ingress.

### Host networking, pause containers, DNS

`hostNetwork: true` pods share the node's namespace (no CNI, host ports, host DNS config `dnsPolicy: ClusterFirstWithHostNet`): used by node agents (kube-proxy, CNI daemon, node-exporter, DCGM exporter) and by performance-critical workloads like NCCL over sockets. Every pod normally has a `pause` container that owns the namespace and keeps it alive across container restarts. The kubelet writes `/etc/resolv.conf` pointing at CoreDNS with search domains and `ndots:5` (chapter 2.8). Kubernetes `Service` and `NetworkPolicy` semantics are covered in Part 5.

## 6. Networking for GPU and HPC pods

1. **Primary network vs data plane.** The primary CNI interface (`eth0`) carries control traffic, service access, logs, and perhaps NCCL bootstrap. The high-bandwidth GPU-to-GPU and storage traffic needs **secondary interfaces**: RDMA-capable NICs (ConnectX in RoCE or IB mode) exposed to the pod via the **NVIDIA Network Operator**, **Multus** (NetworkAttachmentDefinition), **SR-IOV device plugin + SR-IOV CNI** (VFs placed into the pod), **host-device/macvlan/ipvlan CNI**, and the **RDMA shared device plugin** (`rdma/hca_shared_devices_a`). The pod requests resources (`nvidia.com/gpu: 8`, `nvidia.com/rdma_shared_device_a: 1` or `nvidia.com/sriov_net: 8`) and annotations (`k8s.v1.cni.cncf.io/networks: rail0,rail1,...`).

```yaml
# NetworkAttachmentDefinition for a macvlan RDMA rail (illustrative)
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata: { name: rail0, namespace: training }
spec:
  config: |
    { "cniVersion": "0.3.1", "type": "macvlan", "master": "ens1f0", "mode": "bridge", "mtu": 9000,
      "ipam": { "type": "whereabouts", "range": "10.100.0.0/24" } }
---
apiVersion: v1
kind: Pod
metadata:
  name: trainer-0
  namespace: training
  annotations: { k8s.v1.cni.cncf.io/networks: rail0 }
spec:
  containers:
  - name: pytorch
    image: nvcr.io/nvidia/pytorch:24.xx-py3
    resources: { limits: { nvidia.com/gpu: 1, rdma/hca_shared_devices_a: 1 } }
    securityContext: { capabilities: { add: ["IPC_LOCK"] } }       # RDMA memory registration
```

2. **NCCL interface selection.** NCCL picks network interfaces by name/pattern (`NCCL_SOCKET_IFNAME` for bootstrap and socket transport, `NCCL_IB_HCA` for RDMA devices, `NCCL_IB_GID_INDEX` for RoCE GIDs); inside a pod, `eth0` may be the overlay interface, so set these explicitly (e.g. `NCCL_SOCKET_IFNAME=net1`, `NCCL_IB_HCA=mlx5_0,mlx5_1`) or use hostNetwork for the job.
3. **Host networking for training jobs.** Simplest high-performance option: `hostNetwork: true` + `dnsPolicy: ClusterFirstWithHostNet`, with the caveats of port conflicts, less isolation, and no per-pod NetworkPolicy; common in single-tenant clusters and MPI/Slurm-on-Kubernetes setups.
4. **Pod overlay costs.** Small packets, many connections and large flows suffer through veth + bridge + overlay (CPU on softirq, MTU reduction). For TCP-heavy services (inference APIs, data loaders) prefer native routing CNIs or eBPF host routing; keep overlay MTU correct (underlay − 50 for VXLAN) and verify with `ping -M do`.
5. **Topology alignment.** Use the kubelet **Topology Manager** (`single-numa-node` or `best-effort` policies) with CPU Manager and device plugins so the GPU, its NIC VF/RDMA device and CPUs sit on the same NUMA node/PCIe root; verify with `nvidia-smi topo -m` and `ibdev2netdev`.
6. **MTU consistency**: pod MTU = node MTU − encapsulation; jumbo (9000) on secondary RDMA rails; the CNI config `mtu` must match the fabric.
7. **Isolation and policy**: NetworkPolicy (default deny per namespace) for the primary network; secondary SR-IOV/macvlan interfaces bypass host policy: isolate them with VLANs/VRFs/IB partitions at the switch (chapter 2.21).
8. **IPAM**: pod CIDR size vs node count and pods per node (a /24 per node = 254 pods); secondary networks may use `whereabouts` or static ranges per rail.
9. **Observability**: Hubble/Cilium flow logs, Calico flow logs, kube-state/CNI metrics, node-level `ethtool -S` for VFs, RDMA counters; per-pod netns inspection with `nsenter`.
10. **Upgrades**: CNI changes can reset pod networks; stage them, drain nodes, and test on canary clusters; keep `/opt/cni/bin` and `/etc/cni/net.d` consistent.

## 7. Debugging container networking

```bash
# Find the pod's netns on the node
crictl pods --name trainer-0 ; crictl inspectp <pod-id> | jq .info.pid         # or: crictl inspect <ctr> | jq .info.pid
sudo nsenter -t <pid> -n ip -br addr ; sudo nsenter -t <pid> -n ip route ; sudo nsenter -t <pid> -n ss -tulpn
sudo nsenter -t <pid> -n tcpdump -ni eth0 -c 20 port 8080                      # capture inside the pod's namespace
# Map pod veth to host veth: ifindex pairing
sudo nsenter -t <pid> -n ethtool -S eth0 | grep peer_ifindex ; ip -o link | grep "^<ifindex>:"
# Ephemeral debug container
kubectl debug -it trainer-0 --image=nicolaka/netshoot --target=pytorch
kubectl exec trainer-0 -- cat /etc/resolv.conf ; kubectl exec trainer-0 -- ip route
# Node-side
ip route | grep -E 'cali|cni|flannel|vxlan|tunl' ; bridge fdb show ; iptables-save | grep -E 'KUBE-|cali-'
cat /etc/cni/net.d/* ; ls /opt/cni/bin ; journalctl -u containerd | grep -i cni ; kubectl -n kube-system logs <cni-pod>
```

Systematic path for "pod A can't reach pod B": (1) both pods have IPs and routes (`ip route` in each ns); (2) A can reach its gateway/host (ARP, veth up, host-side interface up); (3) host forwarding/rp_filter/`bridge-nf-call-iptables`; (4) cross-node: route or tunnel to B's node exists, node-to-node connectivity (underlay ping, MTU, UDP 8472/4789 or BGP 179 allowed in security groups/firewalls); (5) NetworkPolicy/iptables rules (counters, `conntrack -L`); (6) destination listening on the right address (`ss -tulpn` inside B, not bound to localhost); (7) DNS if names are involved; (8) capture on A's veth, node uplink, B's node uplink, B's veth to find where the packet stops.

## 8. Lab: build container networking and a mini-CNI (untested)

1. **Manual bridge network** from section 2: two namespaces, bridge, NAT, port publish; verify with `ping`, `nc`, `conntrack -L`, `tcpdump` at each hop (veth, bridge, uplink).
2. **Routed veth (Calico style)**: remove the bridge; give the host `/32` routes per veth; enable `proxy_arp` on the host-side veths; set the pod default route via `169.254.1.1 dev eth0 onlink`; compare packet paths.
3. **macvlan and ipvlan**: attach namespaces; observe host-to-container isolation on the same parent; add a host macvlan sub-interface to reach them; compare MAC visibility with ipvlan L3 (`bridge fdb` / switch view).
4. **Overlay across two VMs**: VXLAN between hosts with bridges and namespaces (chapter 2.17); check MTU, `tcpdump udp port 4789`.
5. **Write a CNI plugin in shell/Python**: a script that reads JSON from stdin and `CNI_*` env vars, creates a veth, moves one end into `CNI_NETNS`, assigns an IP from a file-based allocator, adds a default route and prints the result JSON; invoke it manually with `CNI_COMMAND=ADD`; add DEL and CHECK.
6. **Docker modes**: run the same web server in bridge, host, none, and `container:` modes; compare `ss`, `ip addr`, iptables changes, and port behaviour; inspect `docker0`, veths, and NAT rules.
7. **kind + CNI**: create a kind cluster with the default CNI, then Calico or Cilium; inspect `/etc/cni/net.d`, pod routes, tunnel devices, and policies; trace pod-to-pod across nodes with `tcpdump` on node containers.
8. **Multus**: install Multus on kind, attach a macvlan secondary interface (dummy parent) to a pod; verify `net1`, routes, and `k8s.v1.cni.cncf.io/network-status` annotation; set NCCL-style env to use `net1`.
9. **Performance**: `iperf3` pod-to-pod same node and cross node, hostNetwork vs overlay vs macvlan; record throughput, CPU softirq, and MTU effects.
10. **Break and fix**: introduce an MTU mismatch, remove `ip_forward`, add a policy blocking DNS, delete the CNI binary; diagnose each from the checklist.
11. **Clean up** namespaces, bridges, iptables rules.

Mark tested only after execution.

## 9. Common mistakes

- Forgetting `lo up` inside a namespace; forgetting `ip_forward` or masquerade; overlapping container subnets with host/VPN ranges.
- Assuming bridged traffic is visible to iptables without `br_netfilter` settings (Kubernetes requires them).
- Using `eth0` inside GPU pods for NCCL and wondering why traffic uses the overlay.
- Overlay MTU not reduced; jumbo only on some nodes.
- Debugging with tools only in the host namespace (use `nsenter`).
- macvlan host-to-container connectivity expectations; ipvlan/macvlan on cloud networks that filter MACs/IPs.
- Treating NetworkPolicy as covering SR-IOV/RDMA secondary interfaces.
- Changing CNI configuration without draining nodes; leaving stale `/etc/cni/net.d` files from an old CNI (the lexically first one wins).

## 10. Interview angles

- "What is a network namespace? What is isolated? How do two containers on a host talk?"
- "Explain veth pairs and bridges; walk a packet from container A to the internet."
- "How does Docker publish a port? What is `docker0`?"
- "What is CNI? Describe ADD/DEL, IPAM, chained plugins. How does kubelet call it?"
- "Compare Flannel, Calico and Cilium: data path, policy, performance."
- "Pod-to-pod traffic across nodes: overlay vs routed; what changes in the fabric?"
- "How do you give a training pod RDMA NICs? What are Multus and SR-IOV for?"
- "NCCL in Kubernetes uses the wrong interface: why and how do you fix it?"
- "How would you debug a pod that cannot reach another pod?"
- "hostNetwork vs CNI: trade-offs for GPU jobs."

## 11. Checkpoint questions (40)

1. What does a network namespace isolate? **A:** Interfaces, addresses, routes, ARP, netfilter, conntrack, sockets/ports, net sysctls.
2. How do you run a command in a namespace? **A:** `ip netns exec` or `nsenter -t PID -n`.
3. What is a veth pair? **A:** Two linked virtual NICs, a virtual cable.
4. How do you move an interface into a namespace? **A:** `ip link set X netns Y`.
5. What does a bridge do? **A:** Software L2 switch with MAC learning.
6. How do containers reach the Internet on a bridge network? **A:** Default route via bridge, forwarding, masquerade.
7. How are ports published? **A:** DNAT rules (PREROUTING/OUTPUT) to the container IP.
8. Why `bridge-nf-call-iptables`? **A:** So iptables sees bridged traffic.
9. macvlan vs ipvlan? **A:** Own MAC per interface vs shared MAC with own IP.
10. Why can't the host reach a macvlan child on the same parent? **A:** Parent and children don't loop back; add a host macvlan.
11. Docker's default bridge? **A:** `docker0`, 172.17.0.0/16.
12. Docker `--network host` effect? **A:** Shares host namespace; no isolation/NAT.
13. What is `none`? **A:** Loopback only.
14. CNM components? **A:** Sandbox, endpoint, network.
15. Local vs global Docker drivers? **A:** Per-host vs cross-host needing a KV store.
16. What is OCI? **A:** Open Container Initiative image/runtime specifications.
17. What is runc? **A:** Reference low-level OCI runtime.
18. Name high-level runtimes. **A:** containerd, CRI-O.
19. What is CNI? **A:** Plugin interface to configure container networking.
20. CNI commands? **A:** ADD, DEL, CHECK, VERSION.
21. Where are CNI configs and binaries? **A:** `/etc/cni/net.d`, `/opt/cni/bin`.
22. What is IPAM? **A:** Address allocation plugin (host-local, dhcp, static).
23. What is a chained plugin config? **A:** `.conflist` running plugins in sequence.
24. Kubernetes network model requirements? **A:** Pod IPs, pod-to-pod without NAT, node-to-pod reachability.
25. What does Flannel do? **A:** Simple L3 overlay (VXLAN) or host-gw.
26. What distinguishes Calico? **A:** Routed BGP datapath and strong policy.
27. What distinguishes Cilium? **A:** eBPF datapath, identity-based L3-L7 policy, kube-proxy replacement.
28. What does AWS VPC CNI do? **A:** Assigns VPC IPs to pods via ENIs; no overlay.
29. What is Multus? **A:** Meta-CNI attaching multiple interfaces per pod.
30. Why SR-IOV for GPU pods? **A:** VFs give near-native NIC/RDMA access in the pod.
31. What is the pause container? **A:** Holds the pod's namespace.
32. What does `hostNetwork: true` change? **A:** Pod uses node's namespace and IP.
33. Which dnsPolicy with hostNetwork? **A:** `ClusterFirstWithHostNet`.
34. How to find a pod's PID on a node? **A:** `crictl inspect`/`inspectp`.
35. How to capture in a pod's namespace from the host? **A:** `nsenter -t PID -n tcpdump`.
36. Which NCCL variables select interfaces? **A:** `NCCL_SOCKET_IFNAME`, `NCCL_IB_HCA`, `NCCL_IB_GID_INDEX`.
37. Which capability does RDMA need in pods? **A:** `IPC_LOCK` (and a memlock limit).
38. Overlay MTU for VXLAN? **A:** Underlay − 50.
39. Topology Manager purpose? **A:** Align CPUs, GPUs and NICs on one NUMA node.
40. Where does NetworkPolicy not apply? **A:** Secondary SR-IOV/macvlan/RDMA interfaces.

## 12. Sources and review notes

**Written in original words.** Principal sources:

- *Networking and Kubernetes* (Strong and Reddy), chapter 3 ("Container Networking Basics"): why containers (applications, hypervisors, container terms, OCI, LXC, runC, containerd, CRI-O), the Docker networking model (CNM: sandbox, endpoint, network; bridge, host, none, macvlan, ipvlan, overlay), overlay networking with VXLAN, CNI and common CNI implementations (Cilium, Flannel, Calico, AWS VPC CNI), container connectivity examples; plus chapter 2 for Linux interfaces and bridges.
- The author's own `nvidia-devops` repository, volume 01 networking masterclass: network namespaces deep dive, veth, the veth CPU bottleneck scenario, SR-IOV and DPDK, Cilium/eBPF.
- *Production Kubernetes* chapter 5 (pod networking) is the main source for the Part 5 Kubernetes networking chapters, which extend this chapter.
- Walkthroughs, tables and GPU-pod guidance are the author's synthesis from the CNI specification, Multus and NVIDIA Network Operator documentation, and kernel documentation.

**Flagged for verification before publishing:** CNI spec version fields, Multus/whereabouts/SR-IOV resource names and annotations, NVIDIA Network Operator resource names, NCCL variable behaviour per version, and the manual iptables commands against your distribution's nft/legacy backend; all labs are **untested**.
