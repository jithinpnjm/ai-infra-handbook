# Voice sample 6: parts part-05-kubernetes, part-17-operations

## FILE docs/part-05-kubernetes/01-containers-from-first-principles-images-layers-registries.md

In June 2015, Docker, CoreOS and other industry leaders formed the Open Container Initiative (`OCI`) under the Linux Foundation. Its job was to standardize container formats across tools (*Production Kubernetes*, Chapter 3). The OCI has three specifications. The Image Spec defines the layout, the manifest, the index, the config and the layer media types. Its manifest media type is `application/vnd.oci.image.manifest.v1+json`, its index media type is `application/vnd.oci.image.index.v1+json`, and its config media type is `application/vnd.oci.image.config.v1+json`. Layers come in types such as `application/vnd.oci.image.layer.v1.tar+gzip` and `+zstd`. The Runtime Spec describes an unpacked bundle, which contains a `rootfs/` directory and a `config.json` file. That file holds `ociVersion`, `process`, `mounts`, `linux.namespaces` and `linux.resources`, and a runtime such as `runc`, `crun` or `kata` executes it. The Distribution Spec defines the HTTP API that registries use. Docker's older formats remain compatible. Chapter 5.2 covers how containerd and CRI-O use these specs.

---

Each OCI image manifest refers to a container image configuration. The configuration records how the app starts. It holds the entry point, the command, the working directory and the environment variables, among other things. The container runtime reads this file when it creates a container from the image. The snippet below shows a configuration with some fields removed for brevity:

---

A registry has three main parts. A server handles the user interface and the API. A blob store holds the image data. A database holds user and image metadata. The OCI standardizes registry operations, so different products interoperate. Storage backends are often configurable, and that choice shapes the registry's design.

---

A container cannot carry a GPU driver. The kernel driver and its device nodes live on the host. The container carries only the userspace libraries it was built with, such as the CUDA runtime, cuDNN and NCCL. The glue between the two is the NVIDIA Container Toolkit. The diagram shows the path a GPU request takes.

---

## FILE docs/part-05-kubernetes/02-container-runtimes-containerd-runc-cri-and-oci.md

Images lead to content blobs, which you find by digest. Blobs become layered snapshots keyed by chain ID. Containers hold metadata that points to a snapshot and an OCI spec. Tasks are the running processes, managed through shims. Leases protect objects from garbage collection while they are in use. CRI sandboxes and containers carry Kubernetes metadata, such as `io.kubernetes.pod.name` and the namespace and uid, and you can see it in `ctr` and `crictl` output.

---

The second is support. Kubernetes distributions such as VMware's Tanzu Kubernetes Grid and RedHat's OpenShift usually ship a specific container runtime. Stick to that choice unless you have an extremely compelling reason not to. If you do switch, make sure you understand the support implications.

---

The third is conformance testing. The Node Special Interest Group, sig-node, in the Kubernetes project defines CRI validation tests and node conformance tests. These run in every Kubernetes release, and some runtimes have more coverage than others. More coverage is better, because issues get caught during the release process. The community publishes all tests and results on the Kubernetes Test Grid. Look at a runtime's conformance tests and how it relates to the wider Kubernetes project.

---

Docker Engine can still run through cri-dockerd. That path adds layers, so teams use it mainly when they need Docker-specific features on nodes. The book also walks through the Docker path in detail, as it worked in the Kubernetes versions it describes. Kubernetes supported Docker Engine through a CRI shim called the dockershim. Docker Engine does not implement the CRI itself, so the shim had to. The shim is built into the kubelet and is a gRPC server that implements the CRI services.

---

## FILE docs/part-05-kubernetes/03-kubernetes-architecture-overview-components-and-what-talks-to-what.md

In chapter 1 of *Kubernetes: Up and Running* (*Introduction*), Brendan Burns, Joe Beda, Kelsey Hightower and Lachlan Evenson trace Kubernetes back to Google's internal **Borg** and **Omega** cluster managers. Google open-sourced these managers in June 2014. In July 2015 they were donated as the seed technology of the Cloud Native Computing Foundation (CNCF). The authors organize the platform's value around five core benefits.

---

The scheduler watches for Pods that have no `spec.nodeName`. For each one, it runs two cycles. The **scheduling cycle** filters out nodes that cannot run the Pod, scores the survivors, and selects one. The **binding cycle** then writes a `Binding` to the API.

---

The last section lists the Pods running on the node. The book shows three, including `kube-dns`, which asks for `260m` of CPU and `140Mi` of memory. Each Pod gets two numbers for each resource: a request and a limit. A request is guaranteed to be present on the node. A limit is the most the Pod can consume. When the limit is higher than the request, the extra is supplied on a best-effort basis and is not guaranteed. Chapter 5 of the book covers this in detail.

---

The DNS server gives names and discovery to the Services in the cluster. It runs as a replicated service, so a large cluster can run more than one copy. A Deployment manages those copies, and its name may be `coredns` or another variant:

---

## FILE docs/part-05-kubernetes/04-bare-metal-kubernetes-from-scratch-with-kubeadm-lab.md

Even if you later move to a managed service, building a cluster by hand once teaches you what each component does. It shows what must be true of a node: kernel modules, sysctls, swap, the runtime and cgroups. It also shows how certificates and kubeconfigs fit together. You will meet the same pieces again when a worker refuses to join or the CNI will not start. This lab is the foundation for the following chapters on the API, controllers, the kubelet, networking, storage and upgrades. It also prepares you for adding GPUs in Part 11.

---

The utility also needs a secure place to store the bootstrap token when initializing, or to fetch it when joining. Those tokens make sure only approved machines join your cluster, so handle them with care. To learn which runtime configs you need, run through a manual install with `kubeadm`, using the official docs. As you go, you will see what your environment requires.

---

With `kubeadm`, which is strongly recommended, the static manifests for the control plane, etcd included, are created when a control plane node is initialized with `kubeadm init`. Pass any flags you need for these components through a `kubeadm` config file. The bootstrap utility can write a templated `kubeadm` config file for you.

---

Expect a long list of components, usually DaemonSets, Deployments or StatefulSets, that add the features your platform needs. If the cluster is registered into a federated system, that registration usually comes first, because the installation definitions often live in a management cluster. Installing add-ons is then a series of calls to the cluster's API server that create the resources each component needs. Those calls can come from inside or outside the cluster.

---

## FILE docs/part-05-kubernetes/05-the-api-server-and-etcd-how-a-request-becomes-cluster-state.md

APF trouble shows up in a few ways that you can spot. Clients receive HTTP 429 responses with `Retry-After`. The metric `apiserver_flowcontrol_request_wait_duration_seconds` rises. Controllers also log "Waited for ... due to client-side throttling" when their client-go QPS and burst limits are too low. The fix for that is to raise `--kube-api-qps` and `--kube-api-burst` on controllers and schedulers in big clusters. For the server side, give critical components dedicated levels, constrain noisy clients such as unfiltered list loops, and add API server capacity.

---

etcd is the database behind every object in a cluster. It is a distributed store. It uses a consensus algorithm to keep one copy of the cluster state on several machines. Consensus depends on reliable network links between the etcd members, and those members need low latency. Two choices shape the deployment. One is whether etcd runs on dedicated machines or shares them with the control plane. The other is whether etcd runs in a container or directly on the host.

---

Each write creates a new revision. A revision is a cluster-wide counter that only goes up. etcd keeps a history of key versions for watches and consistent reads, and the Kubernetes `resourceVersion` comes from that revision. The history grows until compaction discards revisions older than a chosen point. The API server runs compaction every 5 minutes by default, controlled by `--etcd-compaction-interval`. Compaction frees logical space, but the bbolt file does not shrink until defragmentation runs. Run `etcdctl defrag` one member at a time, because it briefly blocks that member. The database quota, set by `--quota-backend-bytes`, defaults to 2 GiB and is recommended up to 8 GiB. When the database exceeds the quota, etcd raises a `NOSPACE` alarm and becomes read-only until you free space. Compact, defragment and disarm the alarm, in that order.

---

This shows two important points. First, `login1` is not encrypted. Only new or altered Secrets use the active key. Second, when an unencrypted object passes back through the kube-apiserver, there is no provider or key mapping, so no decryption is attempted.

---

## FILE docs/part-05-kubernetes/06-controllers-and-the-reconcile-loop-how-kubernetes-thinks.md

You delete a pod that belongs to a Deployment, and a replacement appears within moments. Nobody typed a command to create it. That behavior comes from the controller pattern, and it is the idea behind everything else in this chapter.

---

Pods tolerate those taints for `tolerationSeconds`, which defaults to 300 s. The `DefaultTolerationSeconds` admission plugin adds that toleration automatically. When the period ends, taint-based eviction deletes the pods, so controllers can recreate them elsewhere. The NoExecute manager carries out this eviction.

---

The namespace controller deletes all content when a namespace is deleted. That is why a namespace can stay stuck in `Terminating` when finalizers or unavailable APIs block it. The garbage collector deletes dependents whose owners are gone, following `ownerReferences` and `blockOwnerDeletion`. TTL-after-finished removes completed Jobs and Pods.

---

The third mechanic is node-label driven DaemonSet reconciliation, from *Kubernetes: Up and Running*, Chapter 11. Instead of using pod anti-affinity hacks on a `ReplicaSet` to place one agent per node, a DaemonSet such as `fluentd`, `nvidia-device-plugin` or `dcgm-exporter` reconciles node additions and label changes on its own. Suppose a DaemonSet specifies `nodeSelector: { ssd: "true" }`, or `nvidia.com/gpu.present: "true"`. Labeling a node with `kubectl label nodes node01 ssd=true` makes the DaemonSet controller schedule the daemon pod onto that node right away. Removing the label terminates the pod.

---

## FILE docs/part-05-kubernetes/07-pods-and-workloads-deployments-statefulsets-daemonsets-and-jobs.md

Avoid using the Kubernetes API server as a general-purpose database. Annotations suit small pieces of data that closely belong to one resource. If data has no obvious object to attach to, store it in a database built for that purpose.

---

Submit it with `kubectl apply -f kuard-pod.yaml`. The API server receives the manifest, the scheduler picks a healthy node, and the `kubelet` on that node watches over the Pod. Writing it out may feel like more work than a single command. The written record is still the better habit for large teams with many applications.

---

A `DaemonSet` makes sure a copy of a Pod runs across a set of nodes. Teams use DaemonSets to deploy system daemons such as log collectors and monitoring agents. These daemons typically have to run on every node. DaemonSets and ReplicaSets share a lot of behavior. Both create Pods that are expected to run for a long time, and both keep the desired state and the observed state in agreement.

---

Four application-level contracts with Kubernetes come from *Production Kubernetes*, Chapter 14 (*Application Considerations*). Josh Rosso and his co-authors describe them. The first is propagating cgroup limits through the Downward API. Runtimes such as older JVMs, or multi-worker Python and C++ allocators, can read the host `/proc/meminfo` rather than the cgroup limits. They may then allocate beyond the container's limit and get `OOMKilled`. To prevent that, expose `resources.limits.memory` as `MEM_LIMIT` through the Downward API, using `resourceFieldRef: { containerName: my-app, resource: limits.memory }`.

---

## FILE docs/part-05-kubernetes/08-the-life-of-a-pod-end-to-end-including-what-the-kernel-does.md

1. **Admission on the node.** The kubelet checks again that the pod fits. It looks at allocatable resources, node selectors, host ports, tolerations, pod security sysctls, topology manager alignment and device availability. If the check fails, the pod is set to `Failed` with reasons such as `OutOfcpu`, `OutOfnvidia.com/gpu`, `NodeAffinity` or `TopologyAffinityError`. The last one is a classic cause of GPU pods that fail after scheduling, when the Topology Manager `restricted/single-numa-node` policy cannot align the devices.
2. **Cgroup hierarchy.** The kubelet computes the QoS class and creates the pod-level cgroup under the QoS parent, at `kubepods.slice/kubepods-<qos>.slice/kubepods-<qos>-pod<uid>.slice`. It sets pod-level limits when that is enabled.
3. **Pod directories.** The kubelet creates the pod's data directories under `/var/lib/kubelet/pods/<uid>/`, including `volumes/`, `plugins/`, `etc-hosts` and the container directories.
4. **Volumes.** The volume manager waits until every volume in the spec is mounted. An `emptyDir` becomes a directory or a tmpfs mount. A `configMap`, `secret`, `projected` or `downwardAPI` volume is a tmpfs filled with data from the API. A PVC takes three steps. The cloud attach/detach controller attaches the block device to the node. The kubelet then calls the CSI `NodeStageVolume` to format and mount the device at a global staging path. Finally it calls `NodePublishVolume` to bind-mount that path into the pod directory. A `hostPath` volume only has its path checked. Until every mount succeeds, you see the pod stay in `ContainerCreating`, with events such as `FailedMount` or `FailedAttachVolume`. Details are in 5.17.
5. **Pull secrets.** The kubelet resolves `imagePullSecrets`, the ServiceAccount's secrets and kubelet credential providers.
6. **Device plugin allocation.** For extended resource requests, the kubelet's device manager calls the plugin's `Allocate` RPC over its gRPC socket in `/var/lib/kubelet/device-plugins/`. The response lists environment variables such as `NVIDIA_VISIBLE_DEVICES=GPU-uuid...`, device nodes, mounts, annotations and CDI device names. Those values are merged into the CRI container config. The CPU manager's static policy assigns exclusive CPUs, and the memory and topology managers choose NUMA nodes.
7. **Sandbox and containers.** Last, the kubelet calls `RunPodSandbox` over CRI, then creates the containers.

---

Several changes speed up AI clusters. Pre-pull images with a DaemonSet, and consider lazy-pulling snapshotters, registry mirrors or P2P distribution (5.1). Keep CNI IPAM fast with preallocated IP blocks. Avoid slow CSI attaches for scratch space by using local NVMe or `emptyDir`. Avoid init containers that download large data on every start, and use shared caches or pre-staged volumes instead. Minimise admission webhook latency, and keep the node's disk fast. Use `imagePullPolicy: IfNotPresent` with digests, and set `serializeImagePulls: false` carefully.

---

Treating GPU allocation as "magic" leaves you stuck when a container cannot see its GPU. Check the device plugin health, the runtime configuration and the cgroup device filters. Finally, running image pulls and CSI attaches serially at scale, without pre-staging, is a mistake to avoid.

---

1. Trace the 20-step pod lifecycle from `kubectl apply` to a running process, and then to `DELETE`. Use the Section 1 sequence diagram. Walk through `kube-apiserver`, `kube-scheduler`, `kubelet` (`syncPod`), `DevicePlugin` (`Allocate`), CSI (`NodeStageVolume` and `NodePublishVolume`), containerd (`RunPodSandbox`, then `PullImage`, `CreateContainer` and `StartContainer`), CNI (`ADD`), and `runc` with the kernel. Name the observable status condition or event at each boundary.
2. You should explain how the kubelet's pod worker goroutines and PLEG drive `syncPod`. Then explain why a pod that already passed `kube-scheduler` can still be rejected at node admission with `TopologyAffinityError` or `OutOfnvidia.com/gpu`. Finish with how `/var/lib/kubelet/pods/<uid>/` works, and how CSI `NodeStageVolume` followed by `NodePublishVolume` works.
3. This exercise draws on *Networking and Kubernetes* Chapters 3 and 4, and on *Production Kubernetes* Chapter 5. Using `verify_pod_namespace_inodes()` in `code/part05/pod_lifecycle_kernel_trace.py`, explain which namespaces an application container shares with the `pause` container (`net`, `ipc`, `uts`, `cgroup`), and which it keeps isolated (`mnt`, `pid`). Then trace how `CNI_COMMAND=ADD` wires the `veth` pair, how the IPAM JSON response comes back, how `/etc/resolv.conf` is set, and how `readinessGates` apply.
4. Using `verify_gpu_cgroup_device_isolation()` in `code/part05/pod_lifecycle_kernel_trace.py`, you trace how the kubelet's device manager calls `Allocate` on `/var/lib/kubelet/device-plugins/`. Trace how the runtime injects `/dev/nvidia*` and `libcuda.so.*`, and how the cgroup v2 eBPF device allow-list stops a container from reaching unallocated GPUs on the same host. Cover RDMA attachment as well.
5. For 64-node GPU jobs, use `compute_pod_startup_intervals()` in `code/part05/pod_lifecycle_kernel_trace.py` to explain how to compute `scheduling`, `initialization`, `container_start`, `readiness_probe`, and `kubelet_pod_start_sli_duration_seconds`, which excludes image pull time. Then list 6 concrete optimizations that would cut a 12-minute cold start down to under 90 seconds.
6. Trace the 5 steps of pod termination. Start at `deletionTimestamp`. Next, `EndpointSlice` removal and `preStop` run in parallel. Then `SIGTERM`, then `SIGKILL`, then `CNI DEL` with CSI `NodeUnpublishVolume`, and finally the delete with `gracePeriod 0`. Explain why a process stuck in kernel `D` state on a dead NFS or Lustre mount ignores `SIGKILL` and keeps the pod in `Terminating`.

---

## FILE docs/part-05-kubernetes/09-the-kubelet-and-the-node-cri-cgroups-qos-classes-probes-and-eviction.md

`kubectl describe node` shows Capacity, Allocatable and Allocated resources, where Allocated is the sum of requests and limits. Reserve generously on GPU nodes. DCGM, the device plugin, CNI agents, log shippers, storage clients and the GPU driver stack all need CPU and memory. An unreserved node can die in surprising ways. The kernel OOM killer may take out kubelet or containerd, or SSH stops responding.

---

The effect shows up as latency that comes and goes. The application looks fine on average, but requests that arrive late in a period wait longer. Keep this in mind when you set a low CPU limit on a multithreaded service, and test its latency under load before you ship it.

---

Every probe type uses one of three mechanisms. The `exec` probe runs a command inside the container. It succeeds when the command returns exit code zero. Any other code marks the container unhealthy. The HTTP probe sends a request to an endpoint in the Pod. Any response code from 200 up to, but not including, 400 counts as success. The `tcpSocket` probe opens a TCP connection to a port you choose. The container counts as healthy if the connection succeeds.

---

Liveness and readiness serve different purposes, so they should check different things. A failed liveness probe makes the kubelet restart the Pod. A failed readiness probe only stops traffic from reaching the Pod. Because the two outcomes differ, most apps should use separate endpoints or commands for each.

---

## FILE docs/part-05-kubernetes/10-services-endpoints-and-kube-proxy-the-life-of-a-service.md

Old DNS habits cause real trouble here. Many systems, Java by default, resolve a name once and then keep the answer. A client holding a stale answer keeps calling an IP that no longer serves the app. A short TTL (time-to-live) and a careful client help. A lag before the client sees a change still remains.

---

Now return to your browser and click `Fail` on the readiness check. The server starts returning errors in the 500 range. After three of these, the server is removed from the endpoints for the Service. Click `Succeed`, and after a single good check, the endpoint is added back.

---

You now have the basics. Labels pick out the pods you care about, and the API gives you their IP addresses. Keeping the right labels in sync is tricky, though. That is why the Service object was created, so you do not have to keep label queries up to date by hand.

---

nftables is the modern kernel packet filter, and `kube-proxy` supports it as a mode that is stable in recent releases. It programs a single `kube-proxy` table with maps and verdict maps. That gives O(1) Service lookup and incremental updates, because each `nft -f` transaction changes only the deltas. It scales and updates better than iptables, and it avoids IPVS's extra dependencies. Check availability in your Kubernetes and kernel version. Coexistence with other iptables-based tooling needs care, since legacy `iptables` front-ends that sit over the nft backend can conflict. Inspect it with `nft list table ip kube-proxy` and `nft list chain ip kube-proxy services`.

---

## FILE docs/part-05-kubernetes/11-dns-and-service-discovery-with-coredns.md

Here is the problem in plain words. `ndots:5` means that if a name has fewer than 5 dots, the resolver tries the search domains first. Take a lookup of `api.example.com` from namespace `ml`. That name has 2 dots, so the resolver tries the search domains before it tries the name as written. Each name below gets an A query and an AAAA query, so you can count them:

---

As a rule of thumb, CoreDNS handles about 10-20k QPS per CPU core when caching is on. Its pods hold no state, so you add capacity by adding replicas. Defaults ship with 2 replicas. The recommendation is replicas ≈ nodes/100 to nodes/20, with a minimum of 3 for high availability. Spread the replicas across nodes and zones with anti-affinity, and protect them with a PDB, such as `minAvailable: 1` or 50%.

---

Negative caching can slow a startup. A lookup that returned NXDOMAIN for a peer, before that peer's pod existed, can stay in the cache for the negative TTL. That TTL defaults to the SOA minimum of 30 s in CoreDNS `cache denial` settings. Workers should therefore retry with backoff and bounded timeouts. Applications should also avoid caching failures. The JVM has the `networkaddress.cache.negative.ttl` setting for this. Python's `socket.getaddrinfo` does not cache, but some libraries do.

---

External dependencies such as object stores, registries and model hubs are a risk too. Pin them to IP-addressed mirrors or internal resolvers for stability, and consider a local caching proxy. When external DNS fails, the symptom is a training job that hangs at startup. Add DNS health to your preflight checks in Part 17.

---

## FILE docs/part-05-kubernetes/12-ingress-load-balancers-and-the-gateway-api.md

You can terminate at the L4 load balancer for passthrough, or at the gateway. End-to-end encryption to pods with mTLS in a mesh is covered in 5.28. SNI routing with TLS passthrough suits backends that must keep their own certificates.

---

kube-vip provides a VIP for the control plane and for Services, using ARP or BGP, and it is lightweight. Cilium LB IPAM, with its BGP Control Plane or with L2 announcements, is integrated with the CNI. It can use Maglev hashing and DSR with an eBPF datapath. Calico advertises Service and cluster IPs through BGP.

---

When an on-call page says users see errors, start with the status code. Each code points at a different layer of the request path. A request travels from DNS to an LB IP, through a node or load balancer, into a gateway pod, then to a Service and its endpoints, and finally to an app pod.

---

Running one gateway replica, or running without a PDB, leaves you no graceful drain. DNS TTLs that are too long also slow failover. Not allowing the gateway namespace in NetworkPolicies, or not restricting backends to gateway-only ingress, is another gap.

---

## FILE docs/part-05-kubernetes/13-pod-networking-under-the-hood-veth-bridges-routes-and-cni-plugins.md

This chapter builds on 5.8, 5.10 and Part 2. From Part 2 you need Ethernet, IP routing, network namespaces (2.25), Linux networking (2.22 to 2.24) and VLANs and bridges (2.11). The rest of the chapter assumes these, so review them first. When you finish, you should be able to do the following.

---

This is what the simple `bridge` CNI plugin does for a single node. The table below lists each primitive and its role. Notice that the bridge handles traffic between local pods, while routing and overlay devices take over once pods on different nodes must talk.

---

1. **Overlay**, using Flannel VXLAN, Calico VXLAN or IPIP, Cilium VXLAN or Geneve, or Weave. It works on any L3 network. The cost is encapsulation overhead. VXLAN adds 50 bytes, which reduces the MTU. Encapsulation and decapsulation also take CPU, though modern NICs can offload that work. Overlays make traffic harder to see.
2. **Routed (L3, no encapsulation)**. Nodes learn pod CIDR routes in one of three ways: BGP, from Calico, Cilium BGP or kube-router; static routes; or cloud route tables. The `host-gw` option in Flannel works only when nodes share L2. This design gives the best performance and clean traceability. It does require control of the underlay, or BGP peering with ToR switches. It fits leaf-spine fabrics that run BGP to hosts, as covered in 2.15 and 2.16.
3. **VPC-native or underlay IPs**. Pods get routable IPs straight from the fabric. Examples are the AWS VPC CNI with ENI secondary IPs, GKE alias IPs, Azure CNI, and SR-IOV or macvlan on a physical NIC. There is no overlay and no NAT. The limits are NIC and IP quotas, and how far IPAM scales.

---

When a pod cannot reach something, work outward from the pod. Find its network namespace first. Then check the interfaces, routes and rules on each side of the veth pair, and trace the packets as they leave the node. The block below follows that order.

---

## FILE docs/part-05-kubernetes/14-overlay-versus-routed-pod-networking-vxlan-bgp-with-calico-ebpf-with-c.md

Before you start, you need chapter 5.13, plus BGP and VXLAN from Part 2 (2.15 to 2.17), and the Linux networking and eBPF material from Part 1 and Part 2. By the end of this chapter, you will be able to:

---

Imagine the fabric could route straight to pod addresses. Then no packet would need an outer header. Without encapsulation, each node advertises its pod CIDR(s) to the fabric, or the fabric learns the routes from the nodes over BGP. Pod traffic is then plain IP on the wire, and pod IPs stay visible from end to end.

---

Cluster Mesh connects several clusters, with global services, cross-cluster policy and shared identities. Chapter 5.35 covers it. Cilium also offers a sidecar-free service mesh, a Gateway API implementation, an Ingress controller, BGP and L2 announcements with LB IPAM, and an egress gateway. The egress gateway gives each namespace or pod a stable egress IP, which helps when you allow-list GPU job traffic to external storage.

---

1. Start with overlay encapsulation and native routing, which cover VXLAN, Geneve, IPIP and WireGuard. This topic draws on Production Kubernetes chapter 5 and Networking and Kubernetes chapters 4 to 5. Trace the Section 2 sequence diagram for a packet from `Pod A` (`10.244.1.5` on `Node A` `192.168.0.11`) to `Pod B` (`10.244.2.9` on `Node B` `192.168.0.12`) over VXLAN (UDP port `4789`, 24-bit VNI, FDB/neighbor lookup). Then use `select_calico_cross_subnet_mode()` in `code/part05/overlay_bgp_cilium_planner.py` to explain how Calico `CrossSubnet` combines native intra-rack routing with cross-rack encapsulation.
2. Next, cover routed BGP designs with Calico, which involve `Felix`, `BIRD`, `Typha`, `/26` `IPPool` blocks and BGP topologies. Using `compute_bgp_session_counts()` in `code/part05/overlay_bgp_cilium_planner.py`, calculate the total BGP session count for 500 nodes under three designs. The first is a Node-to-Node Full Mesh, which gives `124,750` sessions. The second uses 3 Route Reflectors, which gives `1,494` sessions. The third is eBGP Peering with Dual ToR Switches, which gives `1,000` sessions. Then trace the `BGPConfiguration`, `BGPPeer` and `IPPool` manifests in Section 3.
3. Then study Cilium's eBPF datapath, covering label-based security identities, BPF maps, the `tc`, `XDP` and `cgroup` hooks, and `netkit`. Using `compare_policy_scaling_ip_vs_identity()` in `code/part05/overlay_bgp_cilium_planner.py`, explain how Cilium derives numeric Security Identities from Pod labels. Explain why identity-based BPF policy maps stay `O(label sets)`, using `2` entries instead of `500,000` IP pairs across `1,000 x 500` Pods. Then explain how `bpf.hostRouting=true` and `netkit` bypass the host `iptables` stack.
4. Next is Cilium's `kubeProxyReplacement`, Direct Server Return (`DSR`), Maglev consistent hashing and the BGP Control Plane. Trace the two Helm installation profiles in Section 4. One is tunnel VXLAN mode. The other is native routing with the BGP Control Plane, `loadBalancer.mode=dsr` and `loadBalancer.algorithm=maglev`. Explain how DSR eliminates the return-path node hop for external `NodePort` and `LoadBalancer` traffic, and what MTU reservation DSR requires.
5. Then look at selecting and hardening the primary CNI on multi-homed bare-metal GPU clusters. Using `select_primary_cni_node_interface()` in `code/part05/overlay_bgp_cilium_planner.py`, explain why multi-homed GPU nodes break CNI IP autodetection. These nodes have 1 management NIC, 1 storage NIC and 8 RDMA `ens1f*`/`ib*` NICs. Autodetection stays broken unless `IP_AUTODETECTION_METHOD=interface=eth0` (Calico) or `--set devices=eth0` (Cilium) and `kubelet --node-ip` are pinned explicitly.
6. Finally, cover benchmarking, observability with `Hubble`, `Tetragon` and `calicoctl`, and safe live CNI migration. Design the Section 7 benchmark matrix with `iperf3`, `netperf TCP_RR`, `mpstat` and `ethtool -k` offloads across 100 to 10,000 Services. Then outline how to safely migrate a cluster from Flannel or Calico to Cilium without a cluster-wide outage.

---

## FILE docs/part-05-kubernetes/15-networkpolicy-and-the-kernel-netfilter-conntrack-and-ebpf.md

NetworkPolicy is the baseline control for this problem. You use it to segment tenants and workloads into inference, training, data services and system components. You also use it to constrain egress to approved storage and registries, and to meet compliance requirements.

---

A `NetworkPolicy` belongs to one namespace. It is additive, and it works from an allow-list. A policy selects pods with `podSelector` in its own namespace. A pod that no policy selects for a given direction is non-isolated in that direction, so all of its traffic is allowed. Once at least one policy selects the pod and lists that direction in `policyTypes`, the pod becomes isolated in that direction. From then on, only the union of all applicable policies gets through. In plain terms, a flow passes if any one policy allows it.

---

Policies are additive. There are no deny rules and no ordering, so the allowed set is the union of all matching rules. Policies are also stateful. Reply traffic for an allowed connection is automatically allowed, through connection tracking. A policy describes the direction in which the connection is initiated.

---

Selectors become ipsets, and ipsets update incrementally. A membership change is just an `ipset add` or `ipset del`, which is cheap. The number of rules grows with policies times ports, not with the number of pods. Calico's eBPF dataplane replaces these chains with BPF programs and maps. To inspect the result, run `iptables-save | grep cali-`, `ipset list | head`, `calicoctl get networkpolicy -A -o wide` and `calicoctl get globalnetworkpolicy`. The last command, `calicoctl get workloadendpoint -n ns pod -o yaml`, shows the applied profiles.

---

## FILE docs/part-05-kubernetes/16-configuration-secrets-and-rbac.md

The file name becomes the key, `my-config.txt`, and the file contents become its value. The `|` marker keeps the multi-line text together as one block. The literal values appear as plain keys next to it. Kubernetes fills in metadata such as `creationTimestamp`, `resourceVersion` and `uid` for you. Use `-o yaml` to confirm the real contents before you blame the application.

---

Secrets are easier to understand with a real case. Suppose the `kuard` app needs a TLS certificate and key to serve HTTPS. You should not bake those files into the image. Keeping them out of the image keeps the image portable, so it can run in any environment. You store the files in a Secret and mount them at run time instead.

---

Receiving services still verify the token with TokenReview. With a PSAT, the review also checks that the TTL has not expired. It returns extra data about the calling pod, including its name and UID. That scope is tighter than an ordinary token, which only names the account:

---

Kubernetes has no group object. The `ops-team` group is a set of attributes that the identity carries, such as an x509 certificate field or an OIDC claim. Because of that, the three steps above work with whatever identity method you chose. Give every team the same shape: a group, a read-only view role, and a separate admin user that only members can impersonate. This removes many costly mistakes. Impersonation also shows up in the audit log. You can see the original user log in, impersonate `cluster-admin`, and then act. That gives you a trail of who actually did what.

---

## FILE docs/part-05-kubernetes/17-storage-internals-volumes-pv-and-pvc-csi-and-mounts.md

A block device is the layer underneath the file system. You can skip the file system and give the application the raw block device instead. Every file system adds some overhead to writes. Most workloads never notice it, but a workload that needs raw blocks can use storage systems that support them.

---

Volume modes are `Filesystem`, the default, and `Block`. In `Filesystem` mode the kubelet and CSI format and mount the volume. In `Block` mode the raw device appears as `/dev/xxx` through `volumeDevices`. Databases, direct I/O and GPUDirect Storage experiments often use `Block` mode.

---

Snapshots and clones use the `VolumeSnapshot`, `VolumeSnapshotClass` and `VolumeSnapshotContent` objects, managed by external-snapshotter. A claim's `dataSource` can restore from a snapshot or clone from another PVC. These snapshots are crash-consistent unless the application quiesces itself first. Volume populators, set through `dataSourceRef`, fill a new volume from other sources such as an object store or an OCI image. That is useful for pre-seeding datasets and model weights.

---

Fix any of these in your own cluster before the data matters. Most of these mistakes come from one assumption: that storage behaves the same way whatever its class, access mode or location. Check each one against the troubleshooting table in section 6 before you ship.

---

## FILE docs/part-05-kubernetes/18-scheduling-in-depth-kube-scheduler-affinity-taints-priority-and-preemp.md

Other failures are just as costly. The default scheduler can put a latency-sensitive inference service onto the same failing node. It can fragment the cluster so that no node has 8 free GPUs, even though 40 are free. It can let background jobs hold GPUs that production inference needs. It can also put two GPUs of one pod across NUMA nodes, which halves their bandwidth.

---

Fragmentation is the subtle one. Take a cluster with 64 GPUs free, spread as 4 per node. No single node can run an 8-GPU pod, even though 64 GPUs are free in total. Several fixes help. You can use a bin-packing profile (`MostAllocated`) for GPU nodes and keep node pools homogeneous in size. You can schedule large jobs first with priority, and reserve whole nodes for multi-GPU jobs using taints or labels. Descheduling by preemption or consolidation can defragment the cluster, and gang or queue systems can admit big jobs once capacity exists. Size GPU pools so that your largest job fits on one node.

---

JobSet is an API from Kubernetes SIG Apps/Batch for groups of Jobs. It provides success and failure policies, startup order, and DNS through a headless Service. It is the base for multi-slice and multi-host training, and it integrates with Kueue.

---

1. Start with the pools, because queues, quotas and placement rules all refer to them. You can lay out `gpu-h100-training` as a tainted, labeled pool of homogeneous 8-GPU nodes. Add a `gpu-l4-inference` pool, a `cpu-system` pool and a `spot-experimental` pool. Workloads select these through labels and Kueue ResourceFlavors, so users do not write node selectors themselves.

---

## FILE docs/part-05-kubernetes/19-cluster-deployment-models-and-day-2-operations.md

Training jobs need more care than web workloads. The platform should first ask the job to checkpoint, using a signal or an annotation. Only after the checkpoint completes should it drain the node, and then the operator restarts the job elsewhere. Sequence the drains by rack or failure domain, and keep capacity headroom. Never drain more than N% of a pool at once. Node maintenance operators, cluster-autoscaler hooks or CAPI rolling updates can automate this. If you want evictions to follow toleration seconds, use `NoExecute` taint-based maintenance (`node.example.com/maintenance:NoExecute`).

---

Use queue wait times and utilisation trends to justify the next purchase. Look at the queue as well as the nodes, because you need both to see why a job waits. Keep a capacity model that links nodes to GPUs and then to the expected job mix.

---

1. Run a node lifecycle drill. Join a worker with a validating taint, run a validation Job, and then remove the taint. Cordon, drain and uncordon the node while a Deployment with a PDB and a StatefulSet keep running. Watch the PDB block a drain, fix the problem, and time the full cycle.
2. Test a drain with checkpointing. Run a training stub that checkpoints on SIGTERM, then drain its node. Confirm that the checkpoint is written and the job resumes on another node. Then set the grace period too short and see what you lose.
3. Inject failures. Stop the kubelet, unplug the network, kill the container runtime, or fill the disk. Document the symptoms, the timings (NotReady, taints, evictions) and the recovery. Compare the results with a graceful shutdown (5.9).
4. Build a capacity report. Write PromQL queries, or scripts, for allocatable, requested and used GPUs per namespace and pool. Add idle-allocated GPUs, queue wait time, and a fragmentation metric (the largest free block per node pool), then turn them into a dashboard.
5. Design quotas. Create namespaces for three teams, each with a ResourceQuota on GPUs, and put their Kueue ClusterQueues in a cohort. Simulate bursts, check that the limits hold and that borrowing works, and document the policy.
6. Build an add-on matrix. Pick your Kubernetes, GPU Operator and driver versions, and build a compatibility table from the vendor docs. Encode it as a CI check, for example a script that fails when chart versions diverge from the table.
7. Practise GitOps promotion. Put the cluster add-ons in a repository with overlays. Promote a CoreDNS or ingress controller version through staging and then a production-like cluster, and roll back by reverting the commit.
8. Try Cluster API, if you want to. Create a Docker-provider workload cluster with CAPI and perform a rolling upgrade of a MachineDeployment. Enable a `MachineHealthCheck`, kill a node, and watch the auto-remediation.
9. Write a runbook and run a game day. Write the NotReady and GPU-fault runbook. Then inject a GPU fault, simulated through a failing DCGM health check or a fake Xid event, and practise cordon, drain and escalation. Record the time to recovery and the gaps you find.
10. Define SLOs and alerts. Set two SLOs, one for job start latency and one for inference availability. Implement recording rules and burn-rate alerts, and test them with a synthetic failure.
11. Check audit and compliance. Run kube-bench and kubescape, triage the findings, record any accepted exceptions, and schedule recurring scans.
12. Clean up.

---

Start by looking at the managed services and existing installers you could use, whether free or licensed, before you build anything. Keep automation as the guiding principle for every system you build. Work through the architecture and topology questions, especially the uncommon requirements. Map the infrastructure dependencies and fold them into your deployment process. Decide how you will manage the machines that make up your clusters, and understand the containerized components that form the control plane. Build consistent patterns for installing add-ons. Version your platform, and set up day-2 management and upgrade paths before production workloads arrive.

---

## FILE docs/part-05-kubernetes/20-upgrades-etcd-backup-and-restore-and-disaster-recovery.md

Skew is the version gap between components that talk to each other, and the skew policy sets the limits (verify the current doc). HA `kube-apiserver` instances may differ by one minor during a rolling upgrade, with the newest at `n` and the oldest at `n-1`. The `kube-controller-manager`, `kube-scheduler` and `cloud-controller-manager` must not be newer than the API server, and they may be up to one minor older. The `kubelet` may be up to three minors older than the API server, but never newer, in recent releases (two before 1.28). `kube-proxy` follows the same rule as the `kubelet`. `kubectl` may sit one minor version away from the API server in either direction.

---

Give your critical applications, and everything they depend on, a disaster recovery plan of their own. Stateful, distributed applications are harder. Restoring their data and Kubernetes objects is not enough, because restore order and dependencies matter. Brainstorm every failure mode you can think of, build automated recovery for each one, and test it. For the most critical workloads and their dependencies, consider standby clusters ready to fail over to. Automate and test those failovers where possible.

---

Three strategies cover most platform upgrades: cluster replacement, node replacement and in-place upgrades. They range from the highest cost with the lowest risk to the lowest cost with the highest risk. No single strategy fits everyone. Costs, benefits, budget and risk tolerance decide the trade-off. Within each strategy, the degree of automation and testing depends on engineering budget, risk tolerance and how often you upgrade.

---

1. Review the compatibility of the NVIDIA GPU Operator, driver, toolkit, device plugin, DCGM and MIG manager with the target Kubernetes version, the OS and the kernel.
2. Upgrade the operators and CRDs that work with both the old and the new Kubernetes first. Use Helm chart upgrades through GitOps, and handle CRDs as described in 4.25.
3. Upgrade the control plane, then the node pools.
4. For driver upgrades, use the operator's upgrade controller when the operator manages the drivers. The `ClusterPolicy.spec.driver.upgradePolicy` settings include `autoUpgrade`, `maxParallelUpgrades`, `drain` options, `waitForCompletion`, and the pod deletion or eviction policy. The controller cordons each node, drains its GPU pods, reloads the driver and validates the result, then uncordons the node, one node at a time. If you install drivers on the host, use Ansible `serial` flows (4.17) instead. Coordinate with training. Plan checkpoint-and-drain windows and quotas for in-flight jobs, and set a fail-safe for failed validation that keeps the node cordoned.
5. Kernel and OS upgrades require a reboot and a DKMS or precompiled driver rebuild. Pin and test the combinations, and roll them out by rack.
6. Validate after each batch. Check that each node is Ready, that `nvidia.com/gpu` allocatable is correct, and that the DCGM exporter is up. Run an `nvidia-smi` pod test and an NCCL smoke test across the upgraded batch (4.17). Confirm that the secondary networks from the network operator are present.
7. Afterwards, upgrade `kubectl`, the CI/CD tools, client libraries, and any controllers built with an older client-go. Operators compiled against removed APIs need new versions.

---

## FILE docs/part-05-kubernetes/21-certificates-identity-admission-control-and-policy.md

Suppose a new engineer asks for cluster access on the first day. Who vouches for that person, and how do you revoke access when they leave? Authentication methods are covered in 5.16. In production, identity usually follows the patterns below.

---

Kubernetes does not serve a `.well-known` OIDC endpoint natively. You must publish the cluster's discovery information at a public location, such as a static S3 bucket. AWS IAM can then verify the token against Kubernetes' public service account signing key. Once verified, IAM exchanges the PSAT for the role's credentials. The setup is clunky, but its security model is the best of the pod-role approaches, and mapping service accounts to IAM roles is easy to understand. The main downside is that IRSA is harder to deploy outside Amazon Elastic Kubernetes Service (EKS). Newer Kubernetes features, such as exposing the cluster itself as an OIDC provider, reduce that work.

---

Every registration object is either a `MutatingWebhookConfiguration` or a `ValidatingWebhookConfiguration`. Its `rules` set the operations and the apiGroups, versions and resources it matches. Its `clientConfig` names a service or a URL, together with a `caBundle`. The `failurePolicy` is `Fail` or `Ignore`, and `timeoutSeconds` should stay at 30 or below, ideally 10 or less. Other fields narrow the scope further: `matchPolicy`, `namespaceSelector`, `objectSelector`, and `matchConditions`, which are CEL pre-filters. `sideEffects` takes `None` or `NoneOnDryRun`. `admissionReviewVersions` lists the supported versions, and a mutating webhook also sets `reinvocationPolicy`.

---

3. **Gatekeeper `Assign` mutation (`mutations.gatekeeper.sh/v1alpha1`)**: When Gatekeeper's mutating webhook is enabled, an `Assign` resource can set default or enforced field values before the validating constraints run. In the book's example (*Kubernetes: Up and Running*, Chapter 20, untested here), an `Assign` object sets `imagePullPolicy: Always` on every container in all Pods outside the `system` namespace:

---

## FILE docs/part-05-kubernetes/22-multitenancy-and-platform-services.md

Picture two teams on the same cluster. One team's job reserves every GPU it can reach, and the other team's notebook never starts. Quotas and RBAC exist to prevent that kind of squatting. The building blocks in this section keep each tenant inside its own namespace.

---

Not every developer needs to see Kubernetes, and how much you hide is a real decision. Some people argue that if application developers know they run on Kubernetes, you have failed. That idea suits a product where the orchestrator means nothing to the user. Picture a database system that runs its shards on Kubernetes, Bosh or Mesos. Its users probably do not care which one.

---

Some companies run more than one orchestrator. A Mesos footprint may sit beside a Kubernetes one. They then build an abstraction that picks where each workload lands, so developers do not have to choose. This also avoids lock-in, but the cost is effort. You must build on two systems that work differently. Developers then learn a company-specific system instead of a shared one, and many resist learning systems that do not carry over between organizations. Another pitfall is an obsession with abstraction. If you hide everything, you cannot expose key Kubernetes features. Keeping up with the project becomes a cat-and-mouse game, and your abstraction can end up as complex as the system it hides.

---

1. **Stage 1, command-line tooling and local UIs (no API abstraction):** Developers use raw `kubectl`, helped by shell tools. `kubectx` switches contexts, `kubens` switches namespaces, and other plug-ins tail logs or handle SSO credentials. Workstation clients such as Octant and Lens render cluster state from the developer's local `kubeconfig`. This stage gives full flexibility. The price is that every developer needs RBAC, admission guardrails and Kubernetes knowledge.
2. **Stage 2, templating with Helm and Kustomize:** Platform engineers package the roughly ten underlying objects a typical service needs (`Deployment`, `StatefulSet`, `Service`, PVC, `ConfigMap`, `Secret`) into a Helm chart. It exposes a small `Values.yaml` interface, which can be piped into Kustomize, or into a web UI generator such as Ambassador's K8s Initializer, to patch fields the chart did not template. Developers still apply native Kubernetes objects. That keeps the upstream community documentation and debugging familiarity.
3. **Stage 3, abstracting Kubernetes primitives with custom workload CRDs (`PinterestService`):** The platform team defines a high-level custom resource and an operator that wraps several native resources and external integrations, such as internal DNS registration. In the book's example from Pinterest (`PinterestService`, untested here), a 25-line custom resource replaces more than 350 lines of raw `Deployment`, `Service`, `Ingress`, IAM role and sidecar YAML:

---

## FILE docs/part-05-kubernetes/23-autoscaling-hpa-vpa-keda-and-the-cluster-autoscaler.md

Unlike the HPA, the CPA does not read any metrics API. It needs no Metrics Server and no Prometheus Adapter. You do not write a Kubernetes resource for it either. You configure it with flags that name the target workload, plus a ConfigMap that holds the scaling rules.

---

Many apps reach production before anyone knows how much CPU and memory they really use. Deadlines leave little time for load testing and profiling. Teams then request generous amounts as a safety margin, and the cluster ends up poorly utilized.

---

Create a priority class with a negative value, for example `value: -1` as in the book (the lab below uses `-10`; any value below zero works), and apply it to the overprovisioner Deployment. Every other workload then outranks these pods by default. When a real pod needs the room, the overprovisioner pod is evicted immediately. The evicted pod goes Pending, which triggers the Cluster Autoscaler to provision a new node to stand by.

---

1. Start with the HPAv2 algorithm and the metric APIs (`Resource`, `ContainerResource`, `Pods`, `Object`, `External`) and with behavior tuning (Production Kubernetes Chapter 13). Use `compute_hpa_desired_replicas()` in `code/part05/autoscaling_hpa_ca_simulator.py` to trace the `embeddings` `HorizontalPodAutoscaler` manifest in Section 2. Explain how HPA evaluates multiple metrics, and why a $\pm 10\%$ tolerance band applies. Then explain how the `scaleUp` settings (`Percent: 100` and `Pods: 4`, with `selectPolicy: Max`) and the `scaleDown` setting (`stabilizationWindowSeconds: 600`) prevent overshoot and flapping. Finish by explaining why missing `resources.requests` causes `<unknown>` utilization.
2. Explain why CPU utilization and raw `DCGM_FI_DEV_GPU_UTIL` make poor primary autoscaling signals for LLM serving. Compare them with `vllm:num_requests_waiting` (queue depth), in-flight concurrency, and `vllm:gpu_cache_usage_perc` (KV-cache utilization). This covers the choice of signals for `vLLM`, `Triton` and `TGI`. Then trace the `prometheus-adapter` custom and external rules in Section 2.
3. Compare the VPA update modes (`Off`, `Initial`, `Recreate`/`Auto`, `InPlaceOrRecreate`) and the components that serve them (Production Kubernetes Chapter 13). Explain why `Off` mode with Goldilocks is the safest way to right-size requests. Then explain why running VPA in `Auto` and HPA on the same CPU or memory metric causes an oscillation loop.
4. Trace the `batch-embed` `ScaledObject`, which combines `kafka`, `prometheus` and business-hours `cron` triggers, along with the `transcribe-job` `ScaledJob`, both from Section 4. Then explain how Knative and KServe, with their activator request buffering, differ from KEDA when an inference endpoint scales from `0 -> 1`.
5. Use `evaluate_ca_node_scale_down()` and `simulate_overprovisioning_pause_pods()` in `code/part05/autoscaling_hpa_ca_simulator.py`. Explain how the Cluster Autoscaler's scale-up expanders and scale-down checks work. Then explain how Karpenter's `NodePool` consolidation works, using `WhenEmptyOrUnderutilized` and `do-not-disrupt`. Finish by explaining, in your own words, how negative-priority `pause` pods (Production Kubernetes Chapter 13, `Figures 13-6` and `13-7`) hide the 10-minute GPU node boot delays.
6. Explain why reactive, pod-by-pod Cluster Autoscaler scale-up fails for 16-node synchronous training jobs. Then explain how `ProvisioningRequest` (`autoscaling.x-k8s.io`) with a Kueue `AdmissionCheck` guarantees all-or-nothing node provisioning. Finally, list 5 techniques that could cut 70B model cold-start times from 12 minutes to under 60 seconds, and say which one you would try first.

---

## FILE docs/part-05-kubernetes/24-observability-for-kubernetes.md

Labels are powerful, but they carry a warning. Too many labels can make your Prometheus servers too expensive to run. Learn what high cardinality does to metrics before you add many labels. The instrumentation guide in the Prometheus docs is a good place to start.

---

Picture a workload with dozens of replicas. A user reports an error, and you must find the one log line behind it. Opening each replica's logs by hand is slow, and it is easy to miss the line. A central collection point lets you search every replica at once.

---

Logs come in two styles. Unstructured logs are plain strings with no fixed format. They need no planning, which is why they are so common. Structured logs have fixed fields that you fill in every time, usually as JSON lines or key-value pairs. A structured line can look like `time="2015-08-09T03:41:12-03:21" msg="hello world!" thread="13" batchId="5"`. Machines can query structured logs far more easily, while people often find them harder to read. Pick the style that fits how your team works.

---

When a request arrives, the service must read the span context the previous service sent. In an HTTP service, that context travels in headers. The handler extracts it and starts a child span. The tracer from the previous step must be in scope:

---

## FILE docs/part-05-kubernetes/25-troubleshooting-kubernetes-from-the-node-crictl-nsenter-tcpdump-and-ip.md

Before you start, you should have worked through the whole of Part 5 so far, especially 5.8, 5.9, 5.10 and 5.13, along with the Linux and networking material in Parts 1 and 2. When you finish, you will be able to apply a layered method. It runs from symptom to layer to hypothesis to test. You will also know which troubleshooting traps to avoid. For diagnosis, you will use kubectl, including `describe`, events, `logs`, `get -o yaml`, `jsonpath`, `top`, `debug`, `auth can-i`, `explain`, `diff`, `rollout` and `get --raw`.

---

1. Start with `kubectl describe pod` and read the `FailedScheduling` message, which counts the nodes by reason.
2. Resource: if it says `Insufficient nvidia.com/gpu`, check `kubectl describe nodes | grep -A8 Allocated`, fragmentation, taints, device plugin health (`kubectl get nodes -o json | jq ... allocatable`) and pending Kueue admission (`kubectl get workload`).
3. Placement: relax affinity, selectors, taints or topology spread, or fix the labels.
4. Volume: an unbound PVC, a zone conflict or attach limits (5.17).
5. Quota: `exceeded quota` at creation means the pod is rejected, not Pending. A Kueue job that is not admitted leaves the pod Pending with no pods.
6. Scheduler: check its logs with `kubectl logs`, the leader lease and API latency.

---

On the API side, check `deletionTimestamp` and `finalizers` in `kubectl get pod -o yaml`. On the node, check whether the container still runs with `crictl ps`, and look for a D-state process through `/proc/PID/stack` and `wchan`, where NFS and Lustre hangs usually appear. Check stuck unmounts with `lsof +D` and `fuser -vm`. Also look for an unresponsive kubelet (NotReady), a hung runtime shim, or failing CNI DEL. To mitigate, fix the underlying I/O, then restart kubelet or the runtime. If the node is gone, delete the node object with `kubectl delete node`. Use `--force --grace-period=0` only as a last resort, and only after you confirm that no process can still write to RWO storage.

---

Playbooks only earn trust when they have been run against real faults, so test them in staging first. You can kill pods and nodes, delay or drop packets with `tc netem` or Chaos Mesh NetworkChaos, and fill disks. You can also corrupt DNS, stop kubelet, break CNI, throttle CPU, and inject GPU Xid events through simulators where those are available. In a lab, you can expire a certificate, revoke registry credentials, or take down an etcd member. Measure time-to-detect and time-to-recover for each fault, then update runbooks and alerts to match (5.19, 5.24).

---

## FILE docs/part-05-kubernetes/26-how-kubernetes-uses-the-linux-kernel-a-complete-map.md

Suppose a container on a GPU node is killed with exit 137, or a pod sees only some of its GPUs. Your first look usually goes to Kubernetes, but the cause often sits lower. Kubernetes does not isolate, schedule or limit anything by itself. It asks the Linux kernel to do that work. So every behaviour you debug on a GPU node is a kernel mechanism that shows up through a Kubernetes API.

---

A throttled data loader, pods that cannot connect after a rule update, and memory that seems to disappear all come from this layer. So do an RDMA NIC that is unusable inside a pod and a kernel upgrade that breaks the GPU driver. This chapter maps each Kubernetes concept to its kernel feature. It also covers the kernel parameters, versions and failure modes that matter for GPU hosts. It consolidates Parts 1 and 2 (Linux and networking) with Part 5.

---

Start from the Kubernetes side when you debug a symptom. The diagram groups Kubernetes concepts on one side and the kernel features they rely on in the other. The table after it works as a lookup: find the feature you care about, read its kernel mechanism, then run the command in the last column.

---

Many cgroups carry a cost of their own. With tens of thousands of them, `cat memory.stat` and cAdvisor scans slow down. Dead cgroups can also linger until the page cache drains, which is called a cgroup leak. The symptoms are high kernel CPU in `mem_cgroup_*` and a growing `nr_dying_descendants` in `cgroup.stat`.

---

## FILE docs/part-05-kubernetes/27-software-supply-chain-security.md

Every service with its own Dockerfile is one more file for a developer to write and maintain. Buildpacks skip that step. They read the source code and decide how to build it, so developers never write a Dockerfile. Heroku and Cloud Foundry have used buildpacks for years. Cloud Native Buildpacks, or CNB, brings the idea to containers, packaging the app into an OCI image that runs on Kubernetes.

---

Keep training pipelines as code, with reviews. Track artefact lineage with MLflow, W&B or OpenLineage. A reproducible run needs the image digest, lockfile, data hash, config and seed, and together those form the run ID. Protect experiment trackers and registries with RBAC, and guard evaluation sets against tampering.

---

Supply-chain controls fail eventually, so you need to limit the blast radius (5.15, 5.21). Start with least privilege at runtime. Run as non-root, use a read-only root filesystem, drop capabilities, apply seccomp, and avoid host namespaces. Give the workload a minimal ServiceAccount, and grant cloud credentials only through workload identity with narrow scopes.

---

Run the command above first, because you need its result before the cluster work. The cluster exercises come next. They need a cluster with BuildKit, `cosign`, `syft`, `trivy` or `grype`, and Kyverno. Every interactive shell step below is `untested here`, so treat those steps as a plan until you have run them.

---

## FILE docs/part-05-kubernetes/28-service-mesh.md

That limit explains where the mesh APIs come from. Ingress brings HTTP traffic from outside into your cluster, and it has to work with infrastructure built long before Kubernetes. Inside the cluster, a mesh does not carry that burden. Its APIs can be written for cloud native applications, so they can offer richer networking. Those extra features bring complexities of their own, which is the trade-off the rest of this chapter weighs. Most mesh implementations add three general capabilities: network encryption and authorization, traffic shaping, and observability.

---

Istio's control plane is a component called `istiod`. It has three parts. Pilot is the Envoy configuration server. It implements the xDS APIs and streams configuration to every sidecar. Citadel manages certificates, minting the identities and certificates that mTLS uses. Galley reads configuration from Kubernetes and translates it for the other parts.

---

Strict mTLS affects traffic that is not in the mesh. It breaks kubelet health checks, which Istio avoids by rewriting probes through the sidecar on port `15021` or with `rewriteAppHTTPProbe`. It also breaks Prometheus scrapes, which you can fix with metrics merging or port exclusions. External clients and other namespaces outside the mesh are affected too.

---

Multi-cluster setups add their own complexity. You need cross-cluster identities with a shared root CA, endpoint discovery through remote secrets, east-west gateways, and DNS names such as `clusterset.local` or `.global`. Latency and failure domains also change, as chapter 5.35 covers.

---

## FILE docs/part-05-kubernetes/29-extending-kubernetes-crds-and-operators.md

Kubernetes sorts its resources into API groups. `kubectl` users rarely notice this, but you can see the group in the `apiVersion` field of a YAML file. When you program against the API, the grouping matters, because each group often has its own client class. For example, a Deployment lives in the `apps/v1` group. To work with Deployments, you create an `AppsV1Api` object, which knows how to handle every resource in the `apps/v1` group and version. In Java, that is `new AppsV1Api()`.

---

Here is the idea for raising a Deployment to three replicas. In Python you set `deployment.spec.replicas = 3` and then call `patch_namespaced_deployment`. In Java the JSON Patch body is `[{"op":"replace","path":"/spec/replicas","value":3}]`, and `PatchUtils.patch` sends it. The .NET sample uses the same JSON Patch body. In each sample, the Deployment ends up with three replicas.

---

Each of these examples connects port 8080 in the Pod to port 8080 in your program. The code gets back the byte streams for that channel, and you use those streams to send and receive messages. Because these samples are untested here, run them against your own cluster before you rely on them.

---

Failure modes to plan for include a webhook outage that blocks CR creation, finalizer deadlocks, and reconcile hot loops. Unbounded retries can hammer external APIs. Two controllers can manage the same child. Leaked external resources appear when finalizers are missing. Stale caches can cause duplicate creates, and huge status growth can hurt. CRD conversion bugs can corrupt data, and an operator can crash-loop after a schema change. A CR deleted before its operator was installed gets no cleanup at all.

---

## FILE docs/part-05-kubernetes/30-go-for-kubernetes-engineers.md

The rest of the `sync` family covers the other cases. `sync.WaitGroup` waits for a set of goroutines, `sync.Once` runs something exactly once, and `sync/atomic` handles single values. `sync.Map` is rare. `errgroup.Group` from `golang.org/x/sync/errgroup` combines waiting, the first error, context cancellation and `SetLimit`.

---

Use `select` to wait on several channel operations at once. A `default` case makes the wait non-blocking, and a timeout or `ctx.Done()` case stops it when time runs out. Avoid `time.After` inside loops, because it leaked timers before Go 1.23. Use `time.NewTimer` instead.

---

The second is the scheme and the `RESTMapper` (*Kubernetes Programming with Go*, Chapter 5). `runtime.Scheme` is an in-memory registry. It maps Go `reflect.Type` structs $\leftrightarrow$ `schema.GroupVersionKind` (`GVK`, via `AddKnownTypes`, `ObjectKinds`, `New`), and it performs defaulting (`Default`) and version conversion (`Convert`).

---

Table-driven tests use `t.Run`, and you can add `t.Parallel()` and `t.Helper()` where they fit. Helpers can take `testing.TB`. `cmp.Diff` from go-cmp compares values, and `testify` with `require` and `assert` is optional. Run the suite with `go test -race -cover ./...`. Fuzzing uses `func FuzzParse(f *testing.F)`, and benchmarks use `func BenchmarkX(b *testing.B)`.

---

## FILE docs/part-05-kubernetes/31-operators-in-go-controller-runtime-and-kubebuilder.md

Consider Metacontroller when you want to use several languages and expect to deploy many in-house operators. Engineers sometimes prototype with it and then build the final project with Kubebuilder once the design is settled. Its strength is speed after the add-on is installed. It does not help with creating CRDs, though, so you must write those yourself. This is where Kubebuilder has a significant advantage.

---

The request contains only a name, so you re-read the world each time. This is the level-triggered design from 5.6. You are told that something relevant changed, not what changed. One code path therefore handles creation, updates, a resync after a crash and missed events.

---

The book also notes a companion controller that runs in the cluster. That controller keeps the external state reconciled, so the system does not depend only on the state seen at admission time. If your webhook changes or depends on external state, plan for that controller too. It adds complexity, but it protects you from drift.

---

Start with the self-checking Python lab. You can run it locally with the command below, and it will tell you whether each check passes. It verifies three behaviors. The first is the `controller-runtime` `GenerationChangedPredicate` and the custom Node heartbeat predicate filter, which is `evaluate_watch_predicates` in Kubernetes Programming with Go, chapter 10. The second is the `meta.SetStatusCondition` transition-time preservation and the no-op status write guard, `set_status_condition_and_check_noop` from chapter 11 of the same book. The third is the Kubebuilder hub-and-spoke `ConvertTo` and `ConvertFrom` multi-version converter, `convert_myresource_spoke_to_hub_and_back`, from chapter 13.

---

## FILE docs/part-05-kubernetes/32-project-a-gpu-node-health-operator.md

The decisions are where remediators go wrong, so this project keeps them in three pure functions. Each one takes data in and returns an answer, with no I/O. `Judge` classifies one node, `Budget` turns the budget into a node count, and `Plan` picks the nodes to act on. Because none of them touches the cluster, you can test them with ordinary table tests.

---

The `cordon` function sets the unschedulable flag and the three annotations in one patch, then records a Warning event. Next, the controller's watches decide when a node change should trigger a reconcile at all. `policiesForNode` returns every policy whose selector matches the node's labels, **or** that owns a cordon on it, so a node that lost its label is still released. When you read `policiesForNode`, notice its second condition. It is what keeps a released node tracked. `nodeChanged` ignores Node updates unless `unschedulable`, labels, annotations or a condition's type, status, reason or transition time changed, because kubelets update heartbeat fields constantly.

---

The drain path needs three helpers from `code/gpuhealth/internal/controller/gpuhealthpolicy_controller.go`. `releaseAll` walks every node and uncordons the ones this policy owns. `drain` lists the pods on one node and asks the eviction subresource to remove each evictable one. A pod that is already terminating is counted but not evicted again. `evictable` decides which pods are eligible in the first place.

---

Start with the self-checking Python lab. Run it locally to confirm the pure logic before you touch a cluster. It checks the `judge_node` state machine across all 6 condition states, `compute_budget` with `plan_remediation` (which counts human maintenance cordons against `maxUnavailableNodes`), and `is_pod_evictable`, which skips `DaemonSet`, mirror and terminal pods.

---

## FILE docs/part-05-kubernetes/33-reading-the-gpu-operator-and-network-operator-source.md

Suppose a new GPU node joins the cluster and never becomes schedulable. The answer is almost always in how the GPU Operator sequences its operands: driver, container toolkit, device plugin, validator, DCGM exporter, GFD and MIG manager. When RDMA fails to appear on a Pod, look at the Network Operator's OFED, device-plugin and secondary-network states.

---

The tooling supports each step. Use `git clone --depth 1`, then `rg` or `grep -rn` to search for kind names, label keys and condition strings. Use `go doc` as well, and run `git log -S"some string" -- path` to see why a line exists; that last command needs a full clone. Start with logs and CR status so you can form a hypothesis, then confirm it in the code.

---

The GPU Operator lives in the repository `github.com/NVIDIA/gpu-operator`, which is licensed under Apache 2.0. Before you open any file, know where each kind of code sits. The table below lists the directories that matter most. If you are looking for the Helm chart, you want `deployments/gpu-operator`.

---

`init` (`state_manager.go`, `ClusterPolicyController.init`) does the setup before any state runs. It discovers GPU nodes by labels and reads OS and kernel information from NFD labels. It detects the container runtime from node info and sets Pod Security labels on the operator namespace. Then it registers the states with `addState` in a fixed order: pre-requisites, operator metrics, driver, container toolkit, operator validation, device plugin, MPS control daemon, DCGM, DCGM exporter, GPU feature discovery, MIG manager and node status exporter. The vGPU, sandbox, VFIO, Kata and confidential-computing states come after those.

---

## FILE docs/part-05-kubernetes/34-gke-for-gpu-workloads-setup-node-pools-and-quotas.md

The first decision is who manages the nodes. In Standard, you create and size the node pools yourself, and you get wide control over host settings. In Autopilot, Google provisions nodes from the resource requests in your Pods, and the customisation you can do is restricted. The table below compares the two.

---

If something goes wrong, the Google Cloud Platform documentation has the complete steps. The GPU node pools in the sections below build on a cluster like this one. For any Pod that talks to GCS, Artifact Registry or other Google APIs, use Workload Identity rather than node service account keys, as covered in 5.21 on security.

---

The first two rows need different fixes, so read the message before you act. A quota error means your project has asked for more than its allowance. A stockout means the allowance is there and the hardware is not. The commands below check quota through the API.

---

NCCL network plugins depend on the generation. Older A3 shapes use a GPUDirect-TCPX/TCPXO approach with a sidecar and an NCCL plugin. Newer shapes use RDMA over RoCE with NCCL's native IB verbs path. Pod specs need the right annotations, the right NCCL environment variables, and sometimes an installer DaemonSet. This comes from documentation and is version-specific.

---

## FILE docs/part-05-kubernetes/35-multicluster-and-fleet-management.md

The third pressure is trust between teams. Namespaces, RBAC and node pools separate users inside one cluster. A node pool is a group of nodes set up for a particular capability or workload. Even so, the cluster is largely one shared space. Some teams decide that the risk of another team hurting them by accident is not worth it. They accept the extra work of running several clusters.

---

A management cluster is a Kubernetes cluster that manages other clusters. As usage grows and the cluster count climbs, organizations need software to keep operations smooth. They often run that software on Kubernetes-based platforms too. Cluster API is a popular project for this job. It bundles operators that rely on custom resources, such as `Cluster` and `Machine`, to describe other clusters and their parts. A common pattern deploys the Cluster API components to a management cluster. That management cluster then deploys and manages the infrastructure for the workload clusters.

---

1. **No pod-to-pod connectivity.** Clusters talk through public or internal load balancers and DNS. This is the safest option, and it is often enough for APIs and inference endpoints.
2. **VPC peering or VPN plus routable Pod CIDRs** needs non-overlapping Pod and Service CIDRs across the fleet. Decide that at the start, because overlapping ranges are painful to fix.
3. **Cilium ClusterMesh** connects Cilium clusters for global services and cross-cluster policy. It needs unique cluster IDs and routable or tunnelled connectivity. See 5.15.
4. **Submariner** provides cross-cluster Pod and Service connectivity with service discovery. It does not depend on a particular CNI.
5. **Service mesh multi-cluster**, as offered by Istio and others, gives you shared trust, locality-aware load balancing and failover. See 5.28.
6. The **Multi-Cluster Services (MCS) API** defines standard `ServiceExport` and `ServiceImport` resources for cross-cluster service discovery. Implementations vary.

---

The order of regions matters too. Start with a low-traffic region, so early problems touch few customers. Early problems are often the most severe, because they show up quickly. Next, roll out to one high-traffic region to check the release at real scale. After it works in both, you may be confident enough to roll out everywhere. If regions behave differently, test slowly across more geographies before a wider push.

---

## FILE docs/part-17-operations/01-observability-foundations-metrics-logs-and-traces.md

A log line that says a step finished is easy to write and hard to query. A structured log carries the same event as named fields. That lets you filter by model, by run, or by severity without parsing free text.

---

A trace follows one request through every service it touches. Each step in the trace is a span, with a name, a start time, an end time, a parent span, and attributes. The OpenTelemetry trace format is widely used for this, and the tree below shows what one request looks like.

---

Watch the data loader as closely as you watch the GPUs. A slow loader leaves the GPUs waiting, and you pay for hardware that does nothing. *AI Systems Performance Engineering*, Chapter 16, names the DCGM field behind the SM utilisation row: `DCGM_FI_DEV_GPU_UTIL`. Use that field when you build the panel on the exporter side.

---

1. **Add a high-cardinality label test.** Add a metric with a label that has 10000 unique values. Watch how Prometheus behaves, then remove the label. *Solution sketch:* an exporter that emits `http_requests_total{user_id=...}`; watch the `prometheus_tsdb_head_series` metric.
2. **Add a structured log schema.** Define a JSON schema for your logs. Emit it from the application, then query Loki by the schema fields. *Solution sketch:* a Pydantic model in Python that emits structured JSON; Loki's label extraction from JSON.
3. **Add trace context propagation.** Verify that the trace context moves from the HTTP handler into the LLM inference. *Solution sketch:* a Python test that asserts the trace ID in the HTTP handler matches the trace ID in the LLM inference.
4. **Add a model quality signal.** Send the live accuracy signal from Chapter 16.10 to Prometheus. Then alert when the signal drops. *Solution sketch:* a sidecar that emits the live accuracy metric, and a Prometheus alert on that metric.
5. **Add a cardinality budget alert.** Configure an alert that fires when a metric's cardinality passes a limit you choose. The chapter's 1,000-value rule of thumb from Section 2.2 is a reasonable starting point. *Solution sketch:* a recording rule that computes `count by (__name__) (up{job=~".+"})`, with an alert on the recording rule.
6. **Add a unified Grafana dashboard.** Build a dashboard that shows the metrics, logs, and traces for a single request. *Solution sketch:* a Grafana dashboard with the panels from Section 7.7, where the data source links metrics to logs and traces.

---

## FILE docs/part-17-operations/02-prometheus-and-grafana.md

Prometheus cannot read a GPU by itself. An exporter reads the hardware or software and publishes the numbers in the Prometheus format. Each exporter answers a different question. The DCGM exporter shows what the GPUs are doing, and cAdvisor shows what each container uses.

---

The kube-prometheus project is a good place to start. It provides manifests for a complete metrics stack, along with Grafana dashboards. Treat it as a starting point, though. Learn what each component does, then change the configuration to fit your needs. Only then can you be confident that your metrics and alerting cover your systems.

---

Showback describes how much of the cluster an organizational unit or its workloads use. Chargeback attaches a cost to that use. Both turn raw metrics into numbers a team can act on. Without them, Kubernetes capacity is easy to over-request, and clusters sprawl with poor utilization.

---

Chargeback becomes possible once showback exists, because you then have a value to price. Cloud machine costs are usually straightforward. Your own hardware takes more work, but you still need two values. The first is the cost per unit of time for CPU, and the second is the cost per unit of time for memory. Apply those costs to the showback value, and you have a model for charging your platform tenants.

---

## FILE docs/part-17-operations/03-logging-with-loki-and-tracing-with-opentelemetry.md

Centralizing log collection creates a single point of failure for each node, or for the whole cluster if you use a cluster-wide aggregator. A node agent that is overloaded by one noisy workload can stop collecting logs for every other workload on that node. A Fluentd aggregator that runs as a Deployment buffers logs in the ephemeral storage of its Pod. If the Pod is killed before it flushes the buffer, those logs are lost. Running the aggregator as a StatefulSet keeps the buffered logs safe when the Pod goes down.

---

The Kubernetes API exposes Events, so you could write automation that watches for specific Events and reacts to them. In practice, few teams do this. Another option is an Event exporter, which turns Events into metrics. The exporters section of the Prometheus material explains how those metrics are scraped.

---

Application logs describe how your software behaves. They matter most when an unexpected failure needs investigation. Patterns in the logs often reveal what comes before a problem. If you want an alert based on a logged event, consider metrics first. Expose a metric that represents the behavior, then write the alerting rule against that metric. Log messages change more often than metrics do, and a small edit to the text can silently break an alert.

---

Think about access to the logs in your backend, too. You may not want production API server audit logs visible to everyone. Some systems hold information that only privileged users should see. Restricting access can change how you tag logs, and it may require several backends. That changes the forwarding configuration.

---

## FILE docs/part-17-operations/04-dcgm-exporter-and-interpreting-gpu-metrics.md

Suppose you want the temperature, memory use and error count of every GPU in a cluster. Running `nvidia-smi` by hand works on one machine, but nobody can do it all day on every node. The Data Center GPU Manager (DCGM) is NVIDIA's library for doing this continuously. It runs on every GPU node and reports each GPU's health, utilisation and performance, so other tools can read those numbers.

---

Three more facts from the release notes matter for queries. `DCGM_FI_DEV_FB_CAPACITY_BYTES` (total framebuffer, in bytes) is now collected by default. For Kubernetes pods the exporter adds up per-process GPU utilisation and memory and emits them under the new names and the old names, and a pod's utilisation ratio can be above 1.0. `dcp-metrics-included.csv` and `1.x-compatibility-metrics.csv` are deprecated, and `default-counters.csv` replaces them. The rest of this chapter uses the 4.9.0 names. A 4.8.x exporter still emits the old names, so rules that must run on both can join the two forms with `or`, as `code/part17/gpu_alerts.yaml` does.

---

The table is built from `etc/default-counters.csv` at the 4.8.4 and 4.9.0 tags of the dcgm-exporter repository, row by row. The unit factors for clocks, energy, utilisation and memory match the conversions in the exporter's own signal catalog. The NVLink factor is not stated anywhere I could confirm: the release notes say only "MB/s to bytes per second", so the helper refuses to scale it.

---

The draft treats a single double-bit error as critical and calls for replacing the GPU. It warns on single-bit errors and says the GPU should be scheduled for replacement once that rate stays high. The example rate in the draft is 100 per hour, so treat it as a starting value.

---

## FILE docs/part-17-operations/05-distributed-observability-and-profiling.md

Each profiler answers a different question, so start broad and go deeper only when the broad view points at a cause. PyTorch Profiler shows which operations are slow. Nsight Systems shows the timeline, including the gaps where the GPU sits idle. Nsight Compute explains why one kernel is slow. The NCCL Profiler shows which collective holds up a multi-node job.

---

The profile file name now carries the trace ID. Any tool that can search the profile folder can find the profile for a given trace. Test the link once in a staging run before you rely on it during an incident.

---

Nothing adds the trace ID to the range name for you. You choose that convention. AI Systems Performance Engineering, chapter 13, notes that NVTX markers have very low overhead when no profiler is attached, so you can leave them in production code.

---

Treat the thresholds in this table as starting points, not standards. AI Systems Performance Engineering, chapter 16, notes that production teams cannot run heavy profilers all the time. They watch lightweight metrics such as SM utilization and tail latency instead.

---

## FILE docs/part-17-operations/06-alerting-slos-and-health-checks-for-gpu-clusters.md

Imagine each piece is missing. Without alerting, the on-call learns about an outage from a customer. Without SLOs, nobody can say which alerts the business cares about most. Without health checks, Kubernetes keeps sending requests to a pod that cannot answer them.

---

A single network fault can make many alerts fire in the same minute, and the on-call should not receive them one by one. Alertmanager is the router that stands between Prometheus and the on-call. It receives the alerts, removes duplicates, groups related ones, and sends each group to the right receiver.

---

Every alert should carry a runbook_url annotation, so the page links straight to its steps. The on-call opens the link and follows the runbook from there. Production Kubernetes, chapter 9, makes the same point: alert annotations should give enough context to act on, including links to runbooks.

---

1. What is the current Alertmanager latency p99?
2. What is the current alert firing rate?
3. What is the current error budget remaining?
4. What is the current SLO compliance per service?
5. What is the most recent critical alert, and what was the runbook URL?

---

## FILE docs/part-17-operations/07-failure-modes-and-detection.md

A 5xx error means the object storage service failed to answer. The training job asks for the next batch of data and gets an error back instead. The detection signal is the `s3_errors_total` metric, and the query below counts the 5xx rate over five minutes.

---

The example alert fires below 10 percent free space, which is a starting point. A node that writes large checkpoints may need more margin. When the alert fires, find the workload that is filling the disk, clean up its logs, resize the disk, and drain the node only if you cannot free enough space safely.

---

The command below reads the ECC counters on the GPU. It does not create an error, so it checks what the detector sees rather than producing a fault. A non-zero count means ECC errors exist, and in that case the alert should fire.

---

1. **Add a new failure mode to the catalogue.** Pick the last incident you handled and add it to the catalogue. Then add its detection signal, alert, and runbook. *Solution sketch:* the YAML fields from Section 7.1, the post-mortem, the alert rule, and the runbook.
2. **Add a cascade detection.** Detect when one failure spreads across several failure modes, and alert when that happens. *Solution sketch:* a Prometheus alert that matches several failure modes at once, with critical severity.
3. **Add a failure isolation pattern.** Configure the platform to drain a node when its GPU fails. Then check that the workload reschedules onto a healthy node. *Solution sketch:* a Kubernetes controller that watches GPU health, drains the node when the GPU is unhealthy, and lets the workload reschedule.
4. **Add a runbook freshness check.** Set up a CI step that fails when a runbook has not changed in 30 days. The 30-day window is only an example. *Solution sketch:* the CI step reads the runbook's Git history and fails when the last change is older than the window.
5. **Add a catalogue review report.** Generate a quarterly report that lists stale failure modes, repeated ones, and new ones from the latest vendor releases. You will use the report to plan your next review. *Solution sketch:* a Python script that reads the catalogue and writes the report, which the platform team reviews.
6. **Add a per-team failure mode view.** Build a dashboard that shows each team its own failure modes. The dashboard becomes the team's view of cluster health. *Solution sketch:* a Grafana dashboard that filters alerts by team, with one panel per view and a data source behind each panel.

---

## FILE docs/part-17-operations/08-performance-engineering-methodology-and-decision-trees.md

The model caps performance with two lines. One is the compute peak. The other rises with intensity and is set by memory bandwidth. Where they meet is the ridge point. A kernel left of the ridge waits on memory, and a kernel right of it waits on arithmetic.

---

The model counts GPUs, not busy GPU hours, so the 80 percent utilisation in the first line does not change the result. If utilisation is low, the count alone will overstate the order. AI Systems Performance Engineering, chapter 16, suggests watching how latency rises as load rises. The load where tail latency climbs sharply shows the practical limit, which is a better basis for the order than the raw count.

---

1. Add a per-team USE dashboard. Build one USE dashboard per team, with the metrics filtered by a team label. *Solution sketch:* a Grafana dashboard template with a team filter, so each team sees its own USE view.
2. Add a roofline analysis script. Build a Python script that reads a PyTorch profile and computes the roofline for each kernel. *Solution sketch:* the script reads the profile, computes the intensity, compares it with the ridge point and prints the bottleneck.
3. Add a decision tree integration test. Replay past incidents through the tree and check that it reaches the recorded root cause. *Solution sketch:* a Python test that takes an incident, runs the tree and asserts that the bottleneck matches the root cause.
4. Add a cost-vs-latency trade-off dashboard. Build a Grafana dashboard that shows the trade-off for each team. *Solution sketch:* one page with the current cost, the current latency, the options and the recommended fix.
5. Add a capacity planning script. Build a Python script that reads the current pool utilisation and prints the next-quarter forecast. *Solution sketch:* the script reads the metrics, applies the forecast model and prints the GPU count and cost.
6. Add a performance engineering playbook. Write a short playbook that covers the USE method, the roofline, the decision tree, the trade-off and capacity planning. *Solution sketch:* a Markdown document the team can follow during an incident.

---

Start with exercise 3 if you have past incidents on hand. A decision tree that has never been tested against real incidents is still a guess, and you will not know its gaps until you try it. Pick one exercise you can finish this month.

---

## FILE docs/part-17-operations/09-the-ai-systems-performance-checklist-master.md

Suppose you are the on-call engineer. The cluster looks busy, but a training run is slower than it was last week. You need one list of questions to work through, not a new guess each time. This master checklist is that list. It ties together the components covered in Part 17 and in most of Parts 10, 11, 14, and 15.

---

Hardware sets the ceiling for speed and cost. No software change can make a starved GPU run faster than the data and links that feed it. Plan for goodput, which means useful work per dollar and per watt, instead of raw peak math throughput.

---

Thread block clusters keep data close and cut relaunch overhead. On Blackwell, up to 16 thread blocks can form a cluster, after you raise the non-portable limit. Use cluster-aware synchronization and shared-memory residency for persistent designs. Profile the trade-off between occupancy and residency before you adopt them.

---

Pack jobs deliberately. On a 4-GPU node, two 2-GPU jobs that use little CPU can share the node. If both sit inside one NVLink-enabled rack, they can use NVLink for communication. Avoid placing jobs together when they exceed the node's memory or I/O capacity. The goal is high utilization without contention.

---

## FILE docs/part-17-operations/10-cluster-lifecycle-upgrades-and-change-management.md

A canary sends the new version a small share of traffic first. You watch the SLO while only a small group of users sees the new version. If the SLO holds, you widen the share step by step. If it does not, you stop the rollout while the damage is still small.

---

Business changes are the fourth reason. The organisation evolves, and those changes can call for software changes too. Maintenance is the work that answers all four reasons. The book names four types of maintenance, and each type has a different trigger.

---

The lifecycle stack needs its own access rules, because not everyone should be able to start an upgrade. The table shows one possible split of duties. These role names are a design sketch for your platform. They are not built-in GKE roles.

---

Track the process itself, not only the cluster. The table lists lifecycle metrics with example alert thresholds, so tune those thresholds to your own history. The change request failure rate and the rollback rate matter most. A high failure rate suggests the changes are not well tested, and a high rollback rate suggests they are not safe to ship.

---

## FILE docs/part-17-operations/11-incident-response-and-game-days.md

1. Incident response is owned by the platform team. When an alert pages someone, the on-call follows the runbook and escalates to the Incident Commander, who keeps the response coordinated.
2. Game days are a platform-team deliverable. Someone has to plan the failure, schedule the drill, and check that the runbook still matches the cluster.
3. Post-mortems are a platform-team artefact. Each one should end with a runbook or alert change. Otherwise the same incident will come back.

---

Picture a page at night. An alert fires, and within minutes someone has to decide what to do next. The process gives every incident the same path, so the on-call does not have to invent one. It has six stages, shown in the diagram: detection, triage, mitigation, resolution, communication, and post-mortem. The diagram adds one final step: updating the runbook.

---

Keep configurations and benchmarks in source control, so you can trace a regression back to the change that caused it. Run the performance checks inside your CI/CD pipeline, not only by hand. The appendix checklist of AI Systems Performance Engineering recommends both. In the example above, that is the difference between a memory leak test that runs on every release and one that depends on someone remembering it.

---

Access during an incident should follow the role, not the person. The roles below decide who can be paged, who can declare an incident, and who can join the response. Keep the roles narrow, so a single engineer cannot change everything alone.

---

## FILE docs/part-17-operations/12-capacity-planning-and-cost-optimisation.md

Picture a platform team that has just bought a rack of GPUs. A few months later, finance asks why the GPU bill keeps rising, and nobody can explain it. Part 17 so far has taught you to keep the cluster running. This chapter teaches you to pay for it on purpose.

---

Capacity planning and cost optimisation are two views of one problem. Capacity planning looks forward and asks how many GPUs the team will need next quarter. Cost optimisation looks back and asks how many GPUs the team used, and what they cost. Both views meet in the FinOps dashboard, which is the platform team's picture of the cluster's economics.

---

The model produces two numbers: the target fleet for next quarter, and the order, which is how many GPUs to add to reach it. The script below prints both and writes them to a file. A person should read the script and its output before anyone signs the order.

---

Four components make up the stack. Kubecost or OpenCost collects the cost data, Grafana draws the dashboards, and BigQuery answers the chargeback query. The table lists where each one runs and the latency target it should meet. The targets are examples, so measure your own system first and then set targets that match what your team needs.

---

## FILE docs/part-17-operations/13-reliability-engineering-for-ai-infrastructure.md

Suppose a platform team is asked how reliable its AI factory is. The honest answer is often "we hope it stays up." Reliability engineering replaces that hope with measurements, budgets and drills that show the service really does stay up. This chapter explains how to build that discipline on top of the observability work from Part 17.

---

Customers do not care how many GPUs your cluster has or how it is wired. They care whether the service answers when they call it. An AI factory without reliability engineering depends on luck. An AI factory with it knows its uptime, because the targets are measured, the budget is tracked and the failure drills are run.

---

Chaos engineering means breaking things on purpose, in a controlled way, to learn whether the system holds. A team that never breaks anything learns its weak spots during a real outage. The principles below keep each experiment safe and useful.

---

Failover takes time, because the secondary region has to start and then take traffic. Active-active avoids that delay by serving inference from two regions at the same time. A load balancer sends each request to the nearest region, and if one region fails, the other already handles the traffic.

---

## FILE docs/part-17-operations/14-disaster-recovery-and-data-resilience.md

A disaster is any event that takes the cluster down beyond what the normal recovery steps can handle. It might be a regional outage, a ransomware attack, or a hardware failure that takes out a whole zone. When that happens, the disaster recovery plan is what your team follows, because the usual playbook no longer works.

---

1. Set RTO and RPO targets for critical, standard, and development workloads.
2. Build a backup strategy with full backups, incremental backups, and point-in-time recovery.
3. Set up multi-region replication for object storage, the distributed filesystem, and the model registry.
4. Defend against ransomware with immutable backups, object lock, and an audit log.
5. Run a disaster recovery drill from scenario to post-mortem.
6. Operate disaster recovery on GKE with reliable backups, tested replication, and verified drills.

---

Put the two targets side by side, and the deployment pattern usually becomes clear. A tight RTO with a tight RPO points toward a multi-region setup. A loose RTO and a loose RPO can often run from a single region with cold backups.

---

An air gap is a boundary the attacker cannot cross from the cluster. A bucket that the cluster's own account can write to is not truly air-gapped, because the same credentials may reach it. The example below copies a backup, but that step alone does not create the gap.

---

## FILE docs/part-17-operations/15-on-call-runbooks.md

Start with one paragraph that explains what the alert detects and why it matters. Without it, the on-call engineer has to guess whether the page is serious. Production Kubernetes, chapter 9, makes a related point about alerts: add a description and a link to the runbook, so the page itself gives context.

---

A rotation answers one question for every week: who gets paged. Publish it early, so people can plan around it. The YAML below alternates a primary and a secondary each week. A weekly cadence is only an example. A larger or smaller team may choose a different length.

---

Production Kubernetes, chapter 9, adds one alert that every team needs: a dead man's switch. It is an alert that fires on a schedule, and when it stops firing, the on-call hears that metrics or alerting have failed. PagerDuty offers an integration for this, called Dead Man's Snitch.

---

The on-call gets paged, opens the runbook link, and finds nothing there. The likely cause is that nobody wrote a runbook for this alert, or that the link points to the wrong place. Create the runbook, check the link, and make a runbook part of creating every new alert.

---

## FILE docs/part-17-operations/16-ai-assisted-operations-and-scaling-toward-very-large-clusters.md

Picture a training job that fails halfway through a three-month run. Someone must read the error logs, the device statistics, and perhaps memory dumps. They must decide whether the cause was a hardware fault, a numerical overflow, or a networking hiccup. That search is slow, and it depends on what one engineer remembers.

---

The push toward automation reaches the cluster itself. Training and inference clusters run many jobs and requests at once, and they need resource-sharing strategies that change with conditions. Today's orchestrators, such as Kubernetes and SLURM, still rely on static heuristics and simple resource requests. Adaptive scheduling is the next step.

---

The book covers 3D, 4D, and 5D parallelism, which combine data, tensor, model, expert, and context or sequence parallelism. These techniques still depend on human judgment and experience. Expert guides such as Hugging Face's Ultra-Scale Playbook describe them today. The hope is that compilers, libraries, and frameworks will absorb them soon.

---

Agent-4 is a hypothetical self-rewriting, superhuman researcher. It can rewrite its own code to improve itself, which the book calls the AGI scenario. It uses mechanistic interpretability to make its internal decisions clearer. The scenario describes it as a turning point that starts a virtuous cycle of discovery.

---

