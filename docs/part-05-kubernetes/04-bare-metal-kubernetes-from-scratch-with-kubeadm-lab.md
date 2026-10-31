---
id: "c05-04"
title: "5.4 Bare-metal Kubernetes from scratch with kubeadm (lab)"
sidebar_label: "5.4 Bare-metal Kubernetes from scratch with kubeadm (lab)"
sidebar_position: 4
description: "Build a multi-node Kubernetes cluster by hand with kubeadm: node preparation (kernel, swap, sysctls, runtime), control plane bootstrap, CNI, joining workers, HA control plane, verifying, kubectl usage, adding a GPU worker, and a catalogue of installation failures"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 5.4 Bare-metal Kubernetes from scratch with kubeadm (lab)

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | 3 VMs minimum (1 control plane, 2 workers) with 2 vCPU/4 GB each; 5 VMs for the HA variant; internet access or a mirror; optional GPU node |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Suppose you inherit a GPU cluster and nobody left a runbook. You need to know what a healthy node looks like before you can say what is wrong with one. Many GPU clusters leave you to work that out yourself. On-premises DGX and HGX systems, colocation sites and some GPU clouds are not managed Kubernetes. You install and operate Kubernetes yourself, often with kubeadm, Kubespray, BCM or a vendor distribution.

Even if you later move to a managed service, building a cluster by hand once teaches you what each component does. It shows what must be true of a node: kernel modules, sysctls, swap, the runtime and cgroups. It also shows how certificates and kubeconfigs fit together. You will meet the same pieces again when a worker refuses to join or the CNI will not start. This lab is the foundation for the following chapters on the API, controllers, the kubelet, networking, storage and upgrades. It also prepares you for adding GPUs in Part 11.

## Prerequisites and outcomes

This lab builds on chapters 5.1 to 5.3, on Linux administration from Part 1 and on networking from Part 2. Those skills let you read the output of each step instead of copying it. When you finish, you should be able to:

- Prepare each node with its OS settings, kernel modules, sysctls, swap, time, hostname, firewall and container runtime, and explain why each step is needed.
- Install `kubeadm`, `kubelet` and `kubectl` at matching versions and run `kubeadm init` with a config file. Explain every phase and artefact it produces: certificates, kubeconfigs, static pod manifests, bootstrap tokens, and the CoreDNS and kube-proxy add-ons.
- Install a CNI, join workers, label and taint nodes, deploy a test application and Service, and verify cluster health.
- Build a highly available control plane with 3 API servers behind a virtual IP or load balancer, using stacked etcd, and add or remove control-plane nodes.
- Add a GPU node and verify GPU scheduling, which previews Part 11.
- Troubleshoot the common failure modes of kubeadm clusters.

## 1. Plan the cluster

Imagine the cluster is running and a team asks for a bigger pod network. Some settings are hard to change later, so the plan has to be right before you install anything. Start with the machines and the role each one plays. The table shows the minimum set for this lab.

| Role | Hostname | Spec (lab) | Notes |
|---|---|---|---|
| Control plane | `cp1` (and `cp2`, `cp3` for HA) | 2 vCPU, 4 GB, 40 GB SSD | etcd stacked; static IPs |
| Workers | `w1`, `w2` | 2 vCPU, 4 GB | CPU workers |
| GPU worker (optional) | `gpu1` | NVIDIA GPU, driver installed, 8+ vCPU | Added in section 9 |
| API VIP (HA) | `k8s-api.lab.local` / `10.0.0.100` | kube-vip or HAProxy+keepalived | `controlPlaneEndpoint` |

The GPU worker is optional, and you add it later in section 9. Everything else is needed from the start. Some of the choices below are hard to change once the cluster exists, so settle them before you run any install command.

**Kubernetes version.** Use one minor version consistently for `kubeadm`, `kubelet` and `kubectl`. The skew policy allows kubelet to be up to 3 minor versions older than the API server in recent releases, and kubectl to be ±1 version away.

**Pod CIDR and Service CIDR.** The pod CIDR (for example `10.244.0.0/16`) and the Service CIDR (`10.96.0.0/12`) must not overlap with node networks, VPNs or each other. Size the pod CIDR for the largest cluster you expect. A `/16` gives 256 nodes of `/24` each, so it covers a cluster of 256 nodes.

**CNI choice.** Pick Calico, Cilium or Flannel, as covered in 5.13 to 5.15. Some CNIs require specific pod CIDRs or kernel features, so check them against the CIDR plan above.

**Runtime.** Use containerd with the systemd cgroup driver, as covered in 5.2.

**Control plane endpoint.** Set `--control-plane-endpoint` at init if you will ever add control-plane nodes. Changing it later is painful.

**Network.** Every node must reach the others on the ports listed below. Each node also needs a unique hostname, MAC address and `product_uuid` (`/sys/class/dmi/id/product_uuid`), plus DNS or `/etc/hosts` entries.

The table below lists the ports you need to open. Each row gives a direction, a port and what uses it.

| Direction | Port | Purpose |
|---|---|---|
| Control plane inbound | 6443 | Kubernetes API (all) |
| | 2379-2380 | etcd (control plane nodes only) |
| | 10250 | kubelet API (control plane/self) |
| | 10259, 10257 | scheduler, controller-manager (local) |
| Worker inbound | 10250 | kubelet API |
| | 30000-32767 | NodePort Services |
| All nodes | CNI-specific | VXLAN UDP 4789/8472, BGP TCP 179, Wireguard UDP 51820, etc. |

Notice that only the control plane nodes need the etcd ports. Workers need the kubelet port and the NodePort range, and the CNI row applies to every node.

### Bare metal versus virtualized

You may wonder whether a virtual machine layer is needed at all, since containers do much the same job. The answer is not necessarily. Kubernetes works well on bare metal and on virtualized hosts. Choose the medium by the problems each technology solves, and by your team's maturity with it.

Virtualization changed how infrastructure gets provisioned. Older teams PXE booted hosts, configured servers by hand and attached storage to servers one piece at a time. Modern virtual environments put all of that behind APIs. You can create, change and delete resources without knowing what the hardware looks like.

Virtual machines also let you clone machines and run several operating systems on one server. You can size resources to each application and change settings without disrupting the server. Upgrading one host does not touch the others on the same hardware.

Virtualization has trade-offs. Running further from the metal adds overhead, and the virtualization stack itself adds more. Latency-sensitive applications, such as trading, may prefer bare metal. Telcos running 5G networks at the edge may want to work directly against the hardware.

Kubernetes pushes the point of interaction higher still. An operator sees the machines as a sea of compute. Workloads declare what they need, and the scheduler places them. The underlying computers still matter, though. Clusters integrate with infrastructure at several points. Many use CSI drivers to reach storage providers. Infrastructure management projects can request new hosts and join them to the cluster. Most often, organizations rely on Cloud Provider Integrations, or CPIs. These do extra work, such as provisioning load balancers outside the cluster to route traffic in.

Leaving virtualization behind means losing conveniences that Kubernetes does not solve by itself. Still, projects and integration points for bare metal keep improving. Major cloud providers now offer bare metal options, and bare metal IaaS services are gaining share. Success on bare metal still brings its own challenges:

- **Significantly larger nodes:** Larger nodes usually run more Pods, and with thousands of Pods per node, operations get harder. Draining a node for an in-place upgrade can trigger 1000+ rescheduling events.
- **Dynamic scaling:** You need new nodes up quickly as workload or traffic changes.
- **Image provisioning:** You bake and distribute machine images quickly, so cluster nodes stay as immutable as possible.
- **Lack of load balancer API:** You must route ingress traffic from outside the cluster to the Pod network inside it.
- **Less sophisticated storage integration:** Getting network-attached storage to Pods takes more work.
- **Multitenant security concerns:** With hypervisors, security-sensitive containers can run on dedicated hypervisors. You can slice a physical server any arbitrary way and make scheduling decisions from there.

These challenges can be solved. Load balancer gaps can be handled with projects such as kube-vip or MetalLB, and storage can come from integrating with a Ceph cluster. Still, containers are not a new kind of virtualization. In most implementations, they use Linux kernel primitives to make processes feel isolated from others on the same host.

Choosing among cloud virtual machines, on-premises virtualization and bare metal comes down to two things: what your workloads need, and what your team already knows how to run. If you are weighing Kubernetes as a stand-in for a virtualization stack, first pin down what Kubernetes actually fixes for you. Learning to run Kubernetes is already a big effort, and changing the infrastructure underneath it adds engineering effort and risk.

### Compute infrastructure

A Kubernetes cluster needs machines, and managing pools of them is the core job. Early on, you choose the machine types: how many cores, how much memory, how much local storage, what grade of network interface, and whether you need specialized devices such as GPUs. The software you plan to run drives these answers. If your workloads fit a general-purpose machine's compute-to-memory ratio and their demand is steady, the job is simple. Diverse software makes it harder. Consider these machine types:

- **etcd machines (optional):** Only needed if you run a dedicated etcd cluster for your Kubernetes clusters. These machines should prioritize disk read and write performance, so never use old spinning disk hard drives. Give etcd its own storage disk, so it does not compete with the OS or other programs. Consider network proximity too, to reduce latency between etcd machines.
- **Control plane nodes (required):** These machines run only control plane components. Use general-purpose machines, sized and numbered for the expected cluster size and your failure tolerance. A larger cluster means the API server has more clients and more traffic. You can add compute to each machine or add more machines. The scheduler and controller-manager each have only one active leader at a time, so adding replicas does not raise their capacity. If they starve, scale them vertically with more compute per machine. If you colocate etcd on these machines, the same etcd considerations apply.
- **Worker nodes (required):** General-purpose machines that host everything that is not control plane.
- **Memory-optimized nodes (optional):** For workloads whose memory profile does not suit general-purpose nodes. Take AWS general-purpose `M5` instances, with a CPU-to-memory ratio of `1CPU:4GiB`. A workload that consumes `1CPU:8GiB` leaves CPU unused when its resources are reserved at that ratio. `R5` instances, at `1CPU:8GiB`, overcome that inefficiency.
- **Compute-optimized nodes (optional):** For workloads that fit a compute-optimized shape, such as the `C5` instance type at `1CPU:2GiB`. Adding a node pool with these types improves efficiency.
- **Specialized hardware nodes (optional):** GPUs are the most common request. If machine learning workloads need specialized hardware, add a node pool and target those nodes for those workloads.

### Networking infrastructure

Networking is easy to brush off as an implementation detail, but it can change your deployment model. Design for these elements.

**Routability.** You almost never want cluster nodes exposed to the public internet, because the convenience rarely justifies the threat. A well-secured bastion host or jump box that allows SSH is a low-cost way in. The private network raises deeper questions. Storage arrays, internal container registries, CI/CD systems, internal DNS and private NTP servers all need connectivity. Your cluster still usually needs public resources, such as public container registries, even if that path runs through an outbound proxy.

If outbound internet access is out of the question, open source container images and system packages must reach the cluster some other way. Prefer simple, consistent and effective systems. Avoid mindless mandates, and avoid human approval steps for infrastructure that cluster deployments depend on.

**Redundancy.** Availability zones (AZs) help keep uptime high. An AZ is a datacenter with its own power source and backup, and its own connection to the public internet. Two subnets in one datacenter sharing a single power supply do not make two AZs. Two distinct datacenters close together, joined by a low-latency, high-bandwidth link, do. Two AZs is good, and three is better. Beyond that, the number depends on how big a disaster you need to prepare for.

Datacenters do go down. Simultaneous outages across a region are possible but rare. Decide where redundancy matters most, for your workloads or for the cluster control plane. Running etcd across AZs is acceptable, but revisit the network considerations if you do. Spreading control plane nodes across AZs gives the cluster a backup for its own management. If your workloads do not lean on the control plane, and they should not, a control plane failure leaves them running. What it blocks is change, because you cannot easily alter software that is already running. Treat it as a serious incident, but understand that it differs from an outage that customers can see.

**Load balancing.** You need a load balancer in front of the Kubernetes API servers. If you can provision one programmatically, create and configure it as part of control plane deployment. Think through the access policies for the API and the firewalls the load balancer sits behind. You almost certainly will not expose it to the public internet, and remote access to the control plane is usually done through a VPN into the cluster's local network. Publicly exposed workloads need a separate load balancer connected to the cluster ingress. One ingress load balancer serves most incoming requests, so adding one per workload adds little value. With a dedicated etcd cluster, skip the load balancer between the API servers and etcd, because the API's built-in etcd client manages those connections itself.

Settle the CIDRs, the control plane endpoint and the zone layout before you run `kubeadm init`. These are the choices you cannot easily undo.

## 2. Prepare every node

Every node needs the same base before Kubernetes goes on it. Work through this preparation on each machine, as root or with sudo. The names and versions below are examples, so verify them against current docs.

```bash
# 1. Hostnames and name resolution
sudo hostnamectl set-hostname cp1
cat <<EOF | sudo tee -a /etc/hosts
10.0.0.11 cp1
10.0.0.12 cp2
10.0.0.13 cp3
10.0.0.21 w1
10.0.0.22 w2
10.0.0.100 k8s-api.lab.local
EOF

# 2. Time sync (certificates and etcd need accurate clocks)
sudo apt-get update && sudo apt-get install -y chrony && sudo systemctl enable --now chrony

# 3. Disable swap (kubelet refuses to start with swap enabled by default)
sudo swapoff -a
sudo sed -i.bak '/\sswap\s/ s/^/#/' /etc/fstab
# (Swap support exists as a feature gate (NodeSwap); keep it off for GPU/ML nodes unless you have a reason.)

# 4. Kernel modules
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
sudo modprobe overlay && sudo modprobe br_netfilter

# 5. Sysctls
cat <<EOF | sudo tee /etc/sysctl.d/99-k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
fs.inotify.max_user_watches         = 524288
fs.inotify.max_user_instances       = 8192
vm.max_map_count                    = 262144
EOF
sudo sysctl --system

# 6. Verify cgroup v2 and unique identifiers
stat -fc %T /sys/fs/cgroup           # cgroup2fs
cat /sys/class/dmi/id/product_uuid
ip link show | grep link/ether       # MACs unique across nodes

# 7. Firewall: either allow the ports above or disable ufw/firewalld in a lab
sudo ufw disable 2>/dev/null || true
```

Each step in that block exists for a reason, and the reasons matter when a node misbehaves. The `br_netfilter` module and the bridge sysctls let iptables see bridged pod traffic, which Services and NetworkPolicy depend on. `ip_forward` lets the node route pod traffic. Swap breaks the memory accounting that scheduling and QoS assume, so the block turns it off. The `overlay` module is the container filesystem. The inotify limits prevent "too many open files" errors for the kubelet and for log shippers on busy nodes. Accurate clocks prevent certificate and Raft problems.

### Container runtime (containerd)

The runtime is the piece that actually starts containers. Install it, switch it to the systemd cgroup driver, and point `crictl` at its socket.

```bash
sudo apt-get install -y containerd             # or from Docker's repo for newer versions
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml >/dev/null
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
# Optionally set sandbox_image to your mirror, e.g. registry.k8s.io/pause:3.9
sudo systemctl enable containerd && sudo systemctl restart containerd
sudo crictl config --set runtime-endpoint=unix:///run/containerd/containerd.sock
```

### Kubernetes packages

Install the three Kubernetes packages from the official repository. Then pin them, so an ordinary system update cannot move the cluster to a new version without you choosing to.

```bash
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl      # prevent surprise upgrades (upgrades are deliberate, 5.20)
sudo systemctl enable --now kubelet              # it will crash-loop until kubeadm init/join provides config: expected
```

Match the repository minor version to the one you intend to run, because the URL embeds it. The old `apt.kubernetes.io` repositories are deprecated.

### What to install on each machine

Start with the obvious. You need an operating system. Pick a Linux distribution that the community commonly runs Kubernetes on and tests against, because that is the safe choice. RHEL, CentOS and Ubuntu are easy picks. Enterprise support for another distribution, or a strong preference for one, also works, as long as you invest time in testing it. A distribution designed for containers, such as Flatcar Container Linux, earns extra points.

Next, you need a container runtime, such as `docker` or `containerd`. When you run containers, you must have one.

Then comes the `kubelet`, the interface between Kubernetes and the containers it orchestrates. You install it on each machine. Kubernetes itself runs in containers, but the `kubelet` runs as a regular binary on the host. Some people have tried running the `kubelet` in a container. That only complicates things, so avoid it. Put the `kubelet` on the host and run everything else in containers. Your mental model stays clear, and the practical steps still hold up.

So far you have a Linux OS, a container runtime and an interface between Kubernetes and that runtime. The `kubelet` can start containers, but without a control plane it does not know which Pods to run. This is where `kubeadm` and static Pods come in. Other tools can bootstrap the control plane too, but `kubeadm` is widely adopted and runs in many enterprise production systems. It is a command-line program that writes, in part, the static Pod manifests needed to bring Kubernetes up. The `kubelet` can watch a directory on the host and run any Pod manifest it finds there. `kubeadm` configures the `kubelet` and deposits the manifests. That bootstraps the core control plane components: etcd, `kube-apiserver`, `kube-scheduler` and `kube-controller-manager`.

After that, the `kubelet` takes further instructions from Pod manifests submitted to the Kubernetes API. `kubeadm` also generates bootstrap tokens, which let you join other nodes to the new cluster securely.

Last, you need a bootstrap utility. The Cluster API project uses custom resources and controllers for this. A command-line program installed on the host also works well. Its main job is to call `kubeadm` and manage runtime configuration.

When the machine boots, arguments tell the utility how to bootstrap Kubernetes. In AWS, for example, you can use user data to run the utility with arguments that set which flags go to the `kubeadm` command or what goes into a `kubeadm` config file. At a minimum, its runtime config must say whether to create a new cluster with `kubeadm init` or join an existing one with `kubeadm join`.

The utility also needs a secure place to store the bootstrap token when initializing, or to fetch it when joining. Those tokens make sure only approved machines join your cluster, so handle them with care. To learn which runtime configs you need, run through a manual install with `kubeadm`, using the official docs. As you go, you will see what your environment requires.

### Containerized control plane components

The static manifests used to start a cluster should include the essential control plane components: etcd, `kube-apiserver`, `kube-scheduler` and `kube-controller-manager`. Custom Pod manifests are allowed, but keep that list short. Include only Pods that must run before the API is up, or before the cluster joins a federated system. Anything that can wait for the API should be installed through it. Pods created from static manifests can be managed only by editing those manifests on the machine's disk. That is much less accessible and much harder to automate.

With `kubeadm`, which is strongly recommended, the static manifests for the control plane, etcd included, are created when a control plane node is initialized with `kubeadm init`. Pass any flags you need for these components through a `kubeadm` config file. The bootstrap utility can write a templated `kubeadm` config file for you.

Avoid customizing the static Pod manifests directly with your bootstrap utility. If you really need to, you can split manifest creation and cluster initialization into separate `kubeadm` steps, which gives you a chance to inject customization. Do that only when the change matters and cannot be expressed in the `kubeadm` config. A simpler bootstrap of the control plane is more robust, faster, and far less likely to break with Kubernetes version upgrades.

`kubeadm` also generates self-signed TLS assets that secure connections between control plane components. Leave those alone. If your security requirements demand your corporate CA as the source of trust, you can use it, but you must then be able to automate getting the intermediate authority. If your cluster bootstrapping systems are secure, the self-signed CA stays trustworthy. It is valid only for the control plane of a single cluster.

Keep the static manifest list short, and send anything that can wait for the API through the API.

## 3. Initialise the first control-plane node

Put the choices in a configuration file. That makes each one explicit, and you can review the file and store it in Git.

```yaml
# kubeadm-config.yaml
apiVersion: kubeadm.k8s.io/v1beta4
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 10.0.0.11
  bindPort: 6443
nodeRegistration:
  criSocket: unix:///run/containerd/containerd.sock
  name: cp1
  kubeletExtraArgs:
    - name: node-ip
      value: 10.0.0.11
---
apiVersion: kubeadm.k8s.io/v1beta4
kind: ClusterConfiguration
kubernetesVersion: v1.30.4
clusterName: lab
controlPlaneEndpoint: "k8s-api.lab.local:6443"     # use cp1:6443 for a single control plane you won't expand
networking:
  podSubnet: 10.244.0.0/16
  serviceSubnet: 10.96.0.0/12
  dnsDomain: cluster.local
apiServer:
  certSANs: ["k8s-api.lab.local", "10.0.0.100", "10.0.0.11"]
  extraArgs:
    - name: audit-log-path
      value: /var/log/kubernetes/audit.log
etcd:
  local:
    dataDir: /var/lib/etcd
---
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
cgroupDriver: systemd
serverTLSBootstrap: true             # kubelet serving certs via CSR (approve them; see 5.21)
```

Pull the control-plane images first, then run `kubeadm init` against the file and log its output. The last lines copy the admin kubeconfig into your home directory, so `kubectl` can reach the cluster as your user.

```bash
sudo kubeadm config images pull --config kubeadm-config.yaml        # pre-pull control-plane images
sudo kubeadm init --config kubeadm-config.yaml --upload-certs 2>&1 | tee kubeadm-init.log
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config && sudo chown $(id -u):$(id -g) $HOME/.kube/config
kubectl get nodes         # cp1 NotReady until a CNI is installed
```

On a fresh install, `kubectl get nodes` shows cp1 as NotReady. That is expected until you install a CNI in section 4.

### What `kubeadm init` did (phases)

The diagram traces the phases in order. The table after it says what each phase leaves behind.

```mermaid
flowchart TD
    P1["1. preflight & certs<br/>Validate swap/modules/ports;<br/>generate CAs, certs & SA keys in<br/>/etc/kubernetes/pki"] --> P2["2. kubeconfig & kubelet-start<br/>Write admin.conf, kubelet.conf,<br/>controller-manager.conf, scheduler.conf;<br/>start local kubelet"]
    P2 --> P3["3. control-plane & etcd<br/>Write static pod YAML manifests in<br/>/etc/kubernetes/manifests;<br/>kubelet boots etcd & kube-apiserver"]
    P3 --> P4["4. upload-config/certs, mark-control-plane,<br/>bootstrap-token, addon<br/>Taint NoSchedule; CoreDNS & kube-proxy"]
    P4 --> P5["5. Install CNI (Calico / Cilium)<br/>Configures /etc/cni/net.d;<br/>CoreDNS starts; cp1 becomes Ready"]
    P5 --> P6["6. kubeadm join (workers & cp2/cp3)<br/>Verify CA hash, TLS bootstrap CSR,<br/>write /etc/kubernetes/kubelet.conf"]
```

| Phase | Result |
|---|---|
| `preflight` | Checks: root, ports free, swap off, runtime reachable, kernel modules, cgroup driver |
| `certs` | Cluster CA, API server serving cert (with SANs), kubelet client, front-proxy CA/cert, etcd CA/server/peer certs, service-account key pair in `/etc/kubernetes/pki` (valid 1 year for leaf certs by default, CA 10 years) |
| `kubeconfig` | `admin.conf`, `super-admin.conf`, `kubelet.conf`, `controller-manager.conf`, `scheduler.conf` in `/etc/kubernetes` |
| `kubelet-start` | Writes `/var/lib/kubelet/config.yaml` and flags, starts the kubelet |
| `control-plane` | Writes **static pod manifests** `kube-apiserver.yaml`, `kube-controller-manager.yaml`, `kube-scheduler.yaml` in `/etc/kubernetes/manifests`; the kubelet runs them |
| `etcd` | Static pod manifest for the local etcd member |
| `upload-config` / `upload-certs` | Stores ClusterConfiguration in a ConfigMap (`kube-system/kubeadm-config`); optionally encrypts control-plane certs in a Secret for joining other control-plane nodes (valid 2 hours) |
| `mark-control-plane` | Labels `node-role.kubernetes.io/control-plane` and taints `NoSchedule` |
| `bootstrap-token` | Creates a bootstrap token Secret for workers to join; RBAC for TLS bootstrapping and CSR auto-approval |
| `addon` | Installs **CoreDNS** (Deployment) and **kube-proxy** (DaemonSet) |

Two numbers in that table are worth remembering. Leaf certificates last 1 year by default, while the CA lasts 10 years. The uploaded control-plane certificates expire after 2 hours.

Look at what `kubeadm init` produced before you move on. Each command below shows one set of artefacts.

```bash
ls /etc/kubernetes /etc/kubernetes/manifests /etc/kubernetes/pki
sudo cat /etc/kubernetes/manifests/kube-apiserver.yaml | head -60       # flags: authorization-mode, admission plugins, etcd servers, certs
sudo kubeadm certs check-expiration
kubectl -n kube-system get pods -o wide
kubectl -n kube-system get cm kubeadm-config -o yaml | head -40
kubectl -n kube-system get cm kubelet-config -o yaml | head -30
```

Keep `kubeadm-config.yaml` under version control, so you can review the choices later.

## 4. Install a CNI

After init, `cp1` is up but still reports NotReady. The missing piece is the network plugin. Nodes stay NotReady until a CNI configures `/etc/cni/net.d`. This example uses Calico, which is operator-based. Cilium and Flannel are alternatives, covered in 5.13 to 5.14.

```bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/tigera-operator.yaml
cat <<EOF | kubectl create -f -
apiVersion: operator.tigera.io/v1
kind: Installation
metadata: { name: default }
spec:
  calicoNetwork:
    ipPools:
      - blockSize: 26
        cidr: 10.244.0.0/16
        encapsulation: VXLANCrossSubnet
        natOutgoing: Enabled
        nodeSelector: all()
EOF
kubectl get pods -A -w          # wait for calico-system, coredns Running
kubectl get nodes               # cp1 Ready
```

Match the CNI's pod pool to `podSubnet` in the `kubeadm` config. If you choose Cilium instead, install it with `cilium install --set ipam.operator.clusterPoolIPv4PodCIDRList=10.244.0.0/16`, and optionally replace kube-proxy at the same time. Then verify the network with `cilium connectivity test`, or by having two pods ping each other across nodes.

Wait until `cp1` reports Ready and the system pods are running before you go on.

## 5. Join workers

The control plane is ready, so the next step is to bring workers in. On `cp1`, create a join command. The token is valid for 24 h by default.

```bash
kubeadm token create --print-join-command
# or build it: token + CA cert hash
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex | sed 's/^.* //'
```

On each worker, run the join after finishing the preparation in section 2.

```bash
sudo kubeadm join k8s-api.lab.local:6443 --token abcdef.0123456789abcdef \
  --discovery-token-ca-cert-hash sha256:<hash> --node-name w1
```

You can also put the same settings in a JoinConfiguration file, which is repeatable. It holds `discovery.bootstrapToken`, `nodeRegistration` and `kubeletExtraArgs`. The `--discovery-token-ca-cert-hash` flag pins the cluster CA. That stops a worker from being tricked into joining a rogue API server.

Here is what happens next. The kubelet performs **TLS bootstrapping**. It uses the bootstrap token to submit a CSR for a client certificate. The controller manager's CSR approver signs it. Then the kubelet writes `/etc/kubernetes/kubelet.conf` and registers the Node object.

Serving certificates are different. With `serverTLSBootstrap: true`, kubelet *serving* CSRs need manual approval, using `kubectl get csr` and `kubectl certificate approve <name>`. Without that approval, `kubectl logs/exec` fail certificate verification.

```bash
kubectl get nodes -o wide
kubectl label node w1 node-role.kubernetes.io/worker=
kubectl get csr
```

Approve the serving certificate requests and label each worker before you consider the join done.

## 6. Verify the cluster

Before you call the cluster finished, run a set of checks that cover nodes, system pods, DNS and networking. The commands below deploy a small test workload and then probe it.

```bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get --raw='/readyz?verbose'
kubectl run nginx --image=nginx:1.27 --port=80
kubectl expose pod nginx --port=80 --type=NodePort
kubectl get svc nginx
curl http://<any-node-ip>:<nodeport>
kubectl create deployment web --image=nginx:1.27 --replicas=4
kubectl get pods -o wide                                   # spread across workers
kubectl run -it --rm dns --image=busybox:1.36 --restart=Never -- nslookup kubernetes.default
kubectl run -it --rm net --image=nicolaka/netshoot --restart=Never -- curl -s web.default.svc.cluster.local
kubectl top nodes                                          # needs metrics-server (install it, section 10)
```

Turn these into smoke tests you can rerun: all nodes Ready; all kube-system pods Running; DNS resolves; pod-to-pod across nodes; Service ClusterIP and NodePort reachable; and a PVC binds, after you install a storage provisioner (5.17).

### Everyday `kubectl` context, `last-applied-configuration`, `attach`, and shell completion

Once `$HOME/.kube/config` is in place, *Kubernetes: Up and Running* (3rd edition, Chapter 4) describes four `kubectl` workflows that save time on a new cluster. They are untested here.

- **Contexts (`set-context` and `use-context`)**: Instead of typing `--namespace` on every command, save a context that binds a default namespace in `$HOME/.kube/config`. You can also bind `--users` or `--clusters` to it. Then switch to the context:

```bash
kubectl config set-context my-context --namespace=mystuff
kubectl config use-context my-context
```

- **Inspecting and editing `kubectl apply` state (`view-last-applied`, `edit-last-applied`, `set-last-applied`)**: `kubectl apply` stores the previous declarative configuration in the `kubectl.kubernetes.io/last-applied-configuration` annotation on each object. It uses that record to compute three-way merges on future applies. You can inspect or manipulate the recorded state directly:

```bash
kubectl apply -f myobj.yaml view-last-applied
kubectl apply -f myobj.yaml edit-last-applied
kubectl apply -f myobj.yaml set-last-applied
```

- **Attaching to a running container process (`kubectl attach`)**: A minimal container may have no `/bin/sh` or `bash` for `kubectl exec` to use. In that case, `kubectl attach -it <pod-name>` attaches your terminal directly to PID 1's standard input and output streams. Think of it as `kubectl logs -f` plus `stdin`.
- **Bash tab completion (`kubectl completion bash`)**: Install the `bash-completion` package first, using `apt-get install bash-completion`, `yum install bash-completion` or `brew install bash-completion`. Then enable tab completion for commands and resource names. You can enable it for the current shell or persist it in `${HOME}/.bashrc`:

```bash
source <(kubectl completion bash)
echo "source <(kubectl completion bash)" >> ${HOME}/.bashrc
```

Pick the context you will use for the rest of the lab, and switch to it before you run more commands.

## 7. High-availability control plane (stacked etcd)

An HA control plane needs two things from the start: a stable API endpoint, meaning a VIP or load balancer referenced as `controlPlaneEndpoint`, and three control-plane nodes.

### kube-vip (static pod on control-plane nodes)

```bash
# On cp1, before kubeadm init (or after, with a fixed IP), generate the manifest:
export VIP=10.0.0.100 INTERFACE=eth0
sudo ctr image pull ghcr.io/kube-vip/kube-vip:v0.8.0
sudo ctr run --rm --net-host ghcr.io/kube-vip/kube-vip:v0.8.0 vip /kube-vip manifest pod \
  --interface $INTERFACE --address $VIP --controlplane --arp --leaderElection | sudo tee /etc/kubernetes/manifests/kube-vip.yaml
```

HAProxy with keepalived is the classic alternative. You can run it on dedicated nodes or on colocated nodes. Cloud-hosted VMs can use a cloud load balancer instead. Note that kube-vip on kubeadm 1.29+ needs the `super-admin.conf` workaround during the first init. Follow the project's current docs for the details.

### Join additional control-plane nodes

Join the other two control-plane nodes with a certificate key from the init, or create a new key.

```bash
# From cp1, output of `kubeadm init --upload-certs` included a certificate key; or regenerate:
sudo kubeadm init phase upload-certs --upload-certs        # prints a new certificate key
kubeadm token create --print-join-command                  # base join command

# On cp2 and cp3 (prepared like all nodes):
sudo kubeadm join k8s-api.lab.local:6443 --token <t> --discovery-token-ca-cert-hash sha256:<h> \
  --control-plane --certificate-key <key> --apiserver-advertise-address 10.0.0.12
```

Verify etcd membership and API availability with the commands below. The last comment describes a failover test you can run.

```bash
kubectl get nodes
kubectl -n kube-system get pods -l component=etcd -o wide
kubectl -n kube-system exec etcd-cp1 -- etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/peer.crt --key=/etc/kubernetes/pki/etcd/peer.key \
  member list -w table
# failover test: power off cp1 and run `kubectl get nodes` against the VIP; the VIP should move; leader election elects new scheduler/controller leaders (kubectl get lease -n kube-system)
```

Running HA day to day comes down to a few rules. Keep an odd number of control-plane nodes. Never run two control-plane nodes, because two are worse than one for quorum. Spread the nodes across failure domains, and back up etcd, as covered in 5.20.

When an etcd member fails, replace it. Use `etcdctl member remove/add` and `kubeadm join --control-plane`. Alternatively, run `kubeadm reset` and join the node again.

Control-plane nodes carry a `NoSchedule` taint. You may remove it only in labs, using `kubectl taint nodes --all node-role.kubernetes.io/control-plane-`. Decide your control-plane count now, and keep it odd.

## 8. Alternatives to kubeadm for bare metal (for context)

Kubeadm is not the only way to build a bare-metal cluster. The table lists the main alternatives and the situation each one suits.

| Tool | Approach | When |
|---|---|---|
| **kubeadm** | Minimal bootstrapper, you assemble everything else | Learning, custom builds, clear control; basis for others |
| **Kubespray** | Ansible-driven kubeadm-based installer with HA, CNI choices, addons | Bare-metal fleets with Ansible expertise (4.3 to 4.17) |
| **RKE2/K3s (Rancher)** | Packaged distributions, simple single-binary installs, secure defaults | Edge/small clusters, quick HA, FIPS (RKE2) |
| **Talos Linux** | Immutable API-managed OS for Kubernetes | Declarative node management, no SSH |
| **OpenShift** | Opinionated platform with operators, registry, auth | Enterprise platforms |
| **Cluster API (CAPI)** | Declarative clusters as Kubernetes objects (with providers: metal3, vSphere, cloud) | Fleet automation (5.35) |
| **NVIDIA Base Command Manager (BCM) / DeepOps** | Cluster management with Kubernetes and Slurm deployment for DGX/HGX | NVIDIA reference environments (Part 8) |
| **Managed services** | GKE/EKS/AKS, provider-managed Kubernetes on GPU clouds | When you do not want to run the control plane (5.34) |

Read the When column first, because it ties each tool to a situation.

The authors of *Production Kubernetes* (Josh Rosso, Rich Lander, Alexander Brand and John Harris) frame this choice in Chapters 1 and 2, *Path to Production* and *Deployment Models*. They use two architectural analogies.

- **Kubernetes is the foundation, not the finished house.** The book describes Kubernetes as "the engine", the foundation, rather than the finished house, which it calls "the driveable car" (*Production Kubernetes*, Chapter 1). Core `kubernetes/kubernetes` focuses on container orchestration. It exposes plug-in interfaces for the runtime (**CRI**), networking (**CNI**), storage (**CSI**) and cloud integrations (**CPI**, the Cloud Provider Interface, which moves historical "in-tree" cloud integrations out-of-tree). Service routing, observability, secret management, CI/CD and multi-tenancy are left to the surrounding **application platform** that you assemble on top.
- **Managed Services vs. Prebuilt Installers vs. Roll Your Own, and Bare Metal vs. Virtualization** (*Production Kubernetes*, Chapter 2). The book compares the options this way:
  1. *Managed Services (GKE, EKS, AKS):* These carry the lowest operational burden for the control plane. The cost is provider-imposed limits on control-plane flags, Kubernetes versions and custom hardware topologies.
  2. *Prebuilt Installers (Kubespray, RKE2, OpenShift, Cluster API) vs. Roll Your Own (`kubeadm` + Packer + Ansible):* Rolling your own, or using bare metal, gives total control over kernel parameters, custom GPUDirect RDMA and InfiniBand fabrics, and control-plane flags. The price is that you must automate what virtualization used to give you for free. That includes PXE booting through **Matchbox**, **MAAS**, **Tinkerbell** or **BCM**; out-of-band IPMI or Redfish power management; BGP or L2 load balancing through **MetalLB** or **kube-vip**; and building immutable node images with **Packer + Ansible**.
  3. *Environment tiers (`Development`, `Testing` with automated `< 1 week` TTL reapers, `Staging`, and `Production`) and Cluster Sizing (`Few Large` vs. `Many Small`, Production Kubernetes Chapter 2):* Fewer large clusters reduce control-plane overhead and improve bin-packing. You can use tainted **node pools** for GPU or high-memory hardware. Many smaller clusters, by contrast, reduce blast radius and control-plane scaling bottlenecks, which Chapter 5.19 details.

### Start on a cloud or a laptop first

Bare metal teaches a lot, but it is slow for a first cluster. The book suggests starting with a cloud service unless that truly does not fit your situation. Running a cluster is complicated, so for most people it makes sense to hand that job to the cloud. Many clouds offer the management service for free, though cloud resources still cost money and need an active network connection.

GKE, AKS and EKS each give you a working cluster with a few commands. For GKE, you need a Google Cloud Platform account with billing enabled and the `gcloud` tool installed. Set a default zone, then create a three-node cluster and fetch its credentials:

```
$ gcloud config set compute/zone us-west1-a
$ gcloud container clusters create kuar-cluster --num-nodes=3
$ gcloud container clusters get-credentials kuar-cluster
```

For AKS, the Azure Cloud Shell already has the `az` tool set up. You can open it from the shell icon in the upper-right toolbar of the Azure portal. Create a resource group and a cluster, then fetch the credentials:

```
$ az group create --name=kuar --location=westus
$ az aks create --resource-group=kuar --name=kuar-cluster
$ az aks get-credentials --resource-group=kuar --name=kuar-cluster
```

If `kubectl` is missing, `az aks install-cli` installs it. For EKS, the `eksctl` tool creates the cluster with `eksctl create cluster`. Run `eksctl create cluster --help` to see options such as node size. The install already sets up the configuration that `kubectl` needs.

### Local clusters: minikube, Docker Desktop, and kind

Sometimes you need a cluster on your own machine, or you do not want to pay for cloud resources. `minikube` gives you a simple single-node cluster. If you already have Docker Desktop, it bundles a single-machine Kubernetes too. Both are good for learning and experiments. A single VM is not as reliable as a distributed cluster, though, and some features need a cloud provider.

`minikube` needs a hypervisor first. On Linux and macOS, that is generally VirtualBox. On Windows, Hyper-V is the default choice. Install the hypervisor before you run `minikube`. Then start the cluster, stop its VM when you are done, or delete it entirely:

```
$ minikube start
$ minikube stop
$ minikube delete
```

`minikube start` creates a local VM, provisions Kubernetes, and writes a `kubectl` configuration that points to that cluster. `minikube stop` shuts down the VM. `minikube delete` removes the cluster.

`kind` takes a different route. It stands for Kubernetes IN Docker, and it uses Docker containers to stand in for nodes instead of virtual machines. `kind` is still pre-1.0, but many people use it for fast testing. A related Docker-in-Docker approach can run a multinode cluster on one machine. The book notes that this project is still in beta, so you may hit unexpected issues.

```
$ kind create cluster --wait 5m
$ export KUBECONFIG="$(kind get kubeconfig-path)"
$ kubectl cluster-info
$ kind delete cluster
```

Install `kind` from the project site for your platform first. The book's appendix covers a bare-metal option too. It builds a cluster from Raspberry Pi boards with `kubeadm`, and the steps can be adapted to other machines.

Pick the option that matches your situation, and keep the rest of this lab on bare metal.

## 9. Adding a GPU worker (preview of Part 11)

Prepare the node the same way as any worker, then add the GPU stack. The steps run in this order.

1. Install the NVIDIA driver on the host, covered in 4.17 and Part 10, and verify it with `nvidia-smi`.
2. Install the NVIDIA Container Toolkit. Configure containerd with `nvidia-ctk runtime configure --runtime=containerd`, then restart it, as covered in 5.2.
3. Run `kubeadm join` to add the node as a worker.
4. Install the NVIDIA device plugin. You can use the GPU Operator with `driver.enabled=false` instead.

Run the device plugin with Helm. Then check that the node advertises a GPU, and run a smoke test pod that calls `nvidia-smi`.

```bash
helm repo add nvdp https://nvidia.github.io/k8s-device-plugin && helm repo update
helm upgrade -i nvdp nvdp/nvidia-device-plugin -n nvidia-device-plugin --create-namespace --version 0.16.2 \
  --set gfd.enabled=true
kubectl get nodes -o json | jq '.items[] | {name:.metadata.name, gpu:.status.allocatable["nvidia.com/gpu"]}'
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata: { name: gpu-smoke }
spec:
  restartPolicy: Never
  containers:
    - name: cuda
      image: nvcr.io/nvidia/cuda:12.4.1-base-ubuntu22.04
      command: ["nvidia-smi"]
      resources: { limits: { nvidia.com/gpu: 1 } }
EOF
kubectl logs gpu-smoke
```

Taint the GPU node with `kubectl taint node gpu1 nvidia.com/gpu=present:NoSchedule`. Then add a matching toleration to GPU workloads, so CPU-only pods stay off the node, as covered in 5.18. Run the GPU smoke test before you schedule any real work on `gpu1`.

## 10. Day-1 add-ons

The commands below add metrics, a storage provisioner and an ingress path to the lab cluster. Each one is a lab choice, as the comments explain.

```bash
# metrics-server (kubectl top, HPA); on kubeadm labs add --kubelet-insecure-tls only if you did not approve kubelet serving CSRs
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# a storage provisioner for labs (local-path); production uses CSI (5.17)
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.28/deploy/local-path-storage.yaml
kubectl patch storageclass local-path -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
# ingress controller + load balancer for bare metal: MetalLB (L2/BGP) + ingress-nginx (5.12)
```

Commit the manifests and values to Git, and reconcile them with GitOps (4.26), rather than applying them by hand.

### How add-ons get installed

Once kubeadm finishes, the cluster is still not a production platform. Add-ons turn a raw Kubernetes cluster into a production-ready, developer-friendly platform. Plan add-ons as part of the deployment model. Installing them is usually the final phase of a cluster deployment. Manage and version them together with the cluster, and treat Kubernetes plus its add-ons as one package that is tested and released together. Components depend on each other's versions and configuration, so the set moves as a unit.

Kubeadm installs the "required" add-ons needed to pass the Kubernetes conformance tests. Those include cluster DNS and kube-proxy, which implements Kubernetes Service resources. Many more critical components must be applied after kubeadm finishes. The most obvious is a container network interface (CNI) plug-in, since a cluster is not much use without a Pod network.

Expect a long list of components, usually DaemonSets, Deployments or StatefulSets, that add the features your platform needs. If the cluster is registered into a federated system, that registration usually comes first, because the installation definitions often live in a management cluster. Installing add-ons is then a series of calls to the cluster's API server that create the resources each component needs. Those calls can come from inside or outside the cluster.

One approach uses a continuous delivery pipeline built on an existing tool such as Jenkins. The "continuous" part matters less here, because the trigger is a new target for installation, not a software update. The pipeline usually has the installation capabilities you need. All you add is a call to run the pipeline when a new cluster is created, along with the variables for a proper installation.

A more Kubernetes-native approach uses an operator. It extends the API with one or more custom resources that define the add-on components and their versions. It also includes controller logic that installs the add-ons from the spec in those resources. This gives you a clear, central source of truth for a cluster's add-ons, and it lets you manage their ongoing life cycle in code.

The drawback is the complexity of building and maintaining that software. Take on that complexity only if you will use it for day-2 upgrades and ongoing management. If you stop at day-1 installation, you pay a large software engineering cost for little ongoing benefit. Operators offer the most value in ongoing operations, because their watch on desired state keeps working after the cluster is built.

The two approaches often work together. You might use a CD pipeline to install the operator and the add-on custom resources, then let the operator take over. The operator may also need to fetch manifests, perhaps from a code repository that holds templated Kubernetes manifests for the add-ons. Using an operator this way reduces external dependencies and improves reliability. You cannot remove external dependencies altogether, though.

Use an operator for add-ons only when your engineers know the operator pattern well and have experience with it. Otherwise, stick with the tools your team knows, and grow the team's experience over time.

## 11. Troubleshooting kubeadm clusters

When a kubeadm cluster misbehaves, start with the symptom. The table maps each symptom to its likely cause and the commands to check first.

| Symptom | Likely cause | Commands |
|---|---|---|
| `kubeadm init` hangs at "waiting for the kubelet to boot up the control plane" | Kubelet crash-looping: swap on, cgroup driver mismatch, runtime not running, wrong CRI socket, images not pulled | `journalctl -u kubelet -f`, `crictl ps -a`, `systemctl status containerd`, `swapon --show` |
| Control-plane pods CrashLoopBackOff | Wrong `advertiseAddress`, port in use, etcd data dir stale from a previous install | `crictl logs`, `kubeadm reset` + `rm -rf /var/lib/etcd` and re-init |
| `node NotReady`, `network plugin is not ready: cni config uninitialized` | CNI not installed or failing | `ls /etc/cni/net.d`, CNI pod logs, pod CIDR mismatch |
| Worker `join` fails: "couldn't validate the identity of the API server" | CA hash wrong, token expired, endpoint unreachable/DNS | recreate token, check `curl -k https://k8s-api:6443/healthz`, firewall |
| `x509: certificate is valid for ..., not <name>` | API cert SANs missing the address you use | Re-generate with `certSANs`, or use the right name |
| `kubectl logs/exec` fail with TLS errors | Kubelet serving CSRs unapproved (serverTLSBootstrap) | `kubectl get csr`, approve; or install an approver |
| CoreDNS Pending/CrashLoop | No CNI yet; `/etc/resolv.conf` loops (127.0.0.53) | `kubectl -n kube-system logs deploy/coredns`, set kubelet `resolvConf` to `/run/systemd/resolve/resolv.conf` |
| Pods cannot reach Services | `br_netfilter`/sysctl missing, kube-proxy mode, CNI policy | `sysctl net.bridge.bridge-nf-call-iptables`, `iptables-save \| grep KUBE-SVC`, kube-proxy logs |
| Pod-to-pod across nodes fails | Overlay port blocked, MTU mismatch, wrong pod CIDR | `tcpdump`, `ping -M do -s`, CNI status |
| Time skew errors, certificate "not yet valid" | NTP broken | `chronyc tracking` |
| Join of control-plane fails: "certificate key not found" | `--upload-certs` secret expired (2 h) | `kubeadm init phase upload-certs --upload-certs` |
| `etcdserver: request timed out` | Slow disk, CPU starvation, network | etcd metrics, `iostat`, move etcd to SSD |
| Stuck node after `kubeadm reset` | Leftover CNI config, iptables, etcd data, kubelet state | `sudo kubeadm reset -f; rm -rf /etc/cni/net.d ~/.kube; iptables -F; ipvsadm --clear; reboot` |

Read each row as a starting point, not a final answer. Most rows point at one layer: the kubelet, the CNI, DNS, certificates, time or etcd.

To start over on a node, run this reset sequence.

```bash
sudo kubeadm reset -f
sudo rm -rf /etc/cni/net.d /var/lib/etcd /var/lib/kubelet/* $HOME/.kube
sudo iptables -F && sudo iptables -t nat -F && sudo iptables -t mangle -F && sudo iptables -X
sudo systemctl restart containerd
```

Run the reset only on a lab node, because it removes the cluster state on that machine.

## 12. Automation and reproducibility

Building a cluster by hand is a good way to learn, and a poor way to repeat the work. For repeatable clusters, work through these six steps.

1. Bake the preparation steps into an Ansible role or image, as covered in 4.11 and 4.17.
2. Keep your `kubeadm` config files in Git.
3. Use Terraform to create the VMs (4.20 and 4.27) and output an inventory.
4. Consider Kubespray or Cluster API.
5. Pin versions, and mirror packages and images.
6. Write a validation playbook, covered in 5.25 and 4.17.

```yaml
# sketch: Ansible tasks for node prep
- name: Kernel modules
  community.general.modprobe: { name: "{{ item }}", state: present, persistent: present }
  loop: [overlay, br_netfilter]
- name: Sysctls
  ansible.posix.sysctl: { name: "{{ item.k }}", value: "{{ item.v }}", sysctl_file: /etc/sysctl.d/99-k8s.conf, reload: true }
  loop:
    - { k: net.bridge.bridge-nf-call-iptables, v: 1 }
    - { k: net.ipv4.ip_forward, v: 1 }
- name: Disable swap
  ansible.builtin.command: swapoff -a
  when: ansible_swaptotal_mb > 0
- ansible.posix.mount: { name: swap, fstype: swap, state: absent }
```

### Machine images versus configuration management

A machine has to come up with an operating system, certain packages and configuration. Something must also determine the variable values, apply them and start the Kubernetes containerized components. Two broad strategies are common: configuration management tools and machine images.

Configuration management tools such as Ansible, Chef, Puppet and Salt became popular when software was installed on virtual machines and run directly on the host. They automate the configuration of many remote machines. You describe how a machine must look, and the tool applies that description. These tools establish machine consistency well, and their recipes or playbooks live in version control, which is a positive solution.

Where they fall short for Kubernetes is the speed and reliability of bringing nodes online. If joining a new worker runs package installs that pull assets over the network, the join takes significantly longer. Configuration can also fail. Temporarily unavailable package repositories, or missing or incorrect variables, can stop a node from joining. On a resource-constrained autoscaled cluster, that can prolong an availability problem.

Machine images are the better choice. Install every required package into the image ahead of time, and the software is ready to run as soon as the machine boots. No package install depends on the network or an available package repository. Machine images make the node join more reliable and shorten the time before the node can accept traffic.

You can often still use the configuration tools your team knows to build the images. For example, with Packer from HashiCorp, you can use Ansible to build an Amazon Machine Image that is ready to apply to your instances whenever you need them. An error in an Ansible playbook that builds an image is a small setback. The same error during a worker's join could cause a serious production incident.

You should still keep the build assets in version control. Installs stay declarative and clear to anyone who inspects the repository. When upgrades or security patches arrive, update the assets, commit them, and ideally let a pipeline run the build automatically once the change merges. Some decisions involve hard trade-offs, and some are obvious. For most teams, prebuilt machine images are the obvious choice.

## 13. Lab checklist

Start by running the self-checking Python lab, `code/part05/kubeadm_bootstrap_validator_lab.py`, on your own machine. It tests two things. The first is the node preflight and CIDR non-overlap validator, `validate_node_preflight_and_cidrs`. It checks `swapoff -a`, the `overlay` and `br_netfilter` kernel modules, the bridge and forwarding sysctls, `systemd` cgroup driver alignment, and whether `node_cidr`, `pod_subnet` and `service_subnet` stay non-overlapping and match the CNI pool. The second is the `kubeadm join` credential verifier, `verify_kubeadm_join_credentials`. It checks the `[a-z0-9]{6}.[a-z0-9]{16}` bootstrap token format, the `--discovery-token-ca-cert-hash` pinning, and the 2-hour `--upload-certs` key expiry.

```bash
python3 code/part05/kubeadm_bootstrap_validator_lab.py
```

Next, work through this checklist on your lab VMs. All the interactive shell steps are `untested here`.

1. Provision the VMs and prepare them as in section 2. Write down the version matrix and CIDRs, then verify prerequisites with a script.
2. Install containerd with `SystemdCgroup = true`, then verify it with `crictl info`.
3. Install `kubeadm`, `kubelet` and `kubectl` pinned to their versions, and write `kubeadm-config.yaml`. Then run `kubeadm init`. Inspect the `/etc/kubernetes` artefacts, the certificates (`openssl x509 -in apiserver.crt -noout -text | grep -A1 'Subject Alternative'`) and the static pod manifests.
4. Install the CNI and watch the nodes become Ready. Join two workers, and approve CSRs if you use serving-cert bootstrap.
5. Deploy an nginx Deployment, a Service and a NodePort. Test from outside, test DNS and cross-node pod networking, and run a `netshoot` debugging pod.
6. Practice the failure cases. Stop containerd on a worker, stop the kubelet, break the pod CIDR, use the wrong cgroup driver, expire a token and rejoin, and introduce time skew. Read the symptoms and fix each one.
7. Convert to HA. Add kube-vip or HAProxy, join cp2 and cp3, then kill cp1 and verify API continuity and leader election.
8. Take an etcd snapshot and test a restore on a spare VM (5.20).
9. Add a GPU node, or simulate one with a fake extended resource via `kubectl patch node ... --subresource=status`. Install the device plugin and run the smoke pod.
10. Rebuild the whole cluster from your Ansible role and config in under an hour, and record the timings.
11. Tear the cluster down with `kubeadm reset`, and verify that nothing remains.

Keep the timings from step 10, since they are the measure of how fast your rebuild is.

## 14. Common mistakes

Each mistake below can be avoided by reading the earlier sections of this lab.

- Skipping `SystemdCgroup`, swap-off or the kernel modules leads you to debug kubelet crash loops.
- Forgetting `controlPlaneEndpoint` before the first init makes the HA conversion painful.
- A pod CIDR that overlaps the node or corporate network is a mistake. So is a CNI pod CIDR that does not match the one kubeadm uses.
- Mixing Kubernetes versions beyond the skew policy is a mistake, and so is leaving packages unheld so they upgrade automatically.
- Joining nodes with expired tokens or the wrong CA hash, then "fixing" it with `--discovery-token-unsafe-skip-ca-verification`, removes the protection the hash gives you.
- Leaving the control plane schedulable in production, or putting workloads on etcd nodes.
- Not approving kubelet serving CSRs, and then using insecure kubelet TLS flags everywhere.
- Treating a single control plane as production, with no etcd backups.
- Pulling images from the Internet on every node with no mirror, which brings rate limits and outages.

Review your build against this list before you call the cluster production-ready.

## 15. Interview angles

You may be asked to explain this chapter out loud, so practise the answers below.

- Walk me through bootstrapping a cluster with kubeadm. What do the phases do, and which files and certificates do they create?
- Why must swap be off, and what are the prerequisite sysctls and modules?
- How does a worker join securely, and what are the token and the CA hash for?
- How do you build an HA control plane with kubeadm? Why an odd number of etcd members?
- A node is NotReady with "cni config uninitialized". What do you check?
- How do you rotate certificates, and what expires after a year? (5.21)
- kubeadm vs Kubespray vs managed Kubernetes for a GPU cluster: which would you choose?

Practise until you can explain each answer in your own words.

## Exercises

1. Start with the network plan. This exercise draws on *Kubernetes: Up and Running*, Chapter 3 and Appendix A. Using `validate_node_preflight_and_cidrs()` in `code/part05/kubeadm_bootstrap_validator.py`, explain why `podSubnet` (`10.244.0.0/16`), `serviceSubnet` (`10.96.0.0/12`) and the host network (`10.0.0.0/24`) must never overlap. Explain why `controlPlaneEndpoint` (`k8s-api.lab.local:6443`) must be set before `kubeadm init`. Then explain why each step in Section 2 (`swapoff -a`, `overlay` & `br_netfilter`, `bridge-nf-call-iptables = 1`, `ip_forward = 1`, `SystemdCgroup = true`, `apt-mark hold`) is required.
2. Trace the 11 phases of `kubeadm init`. Follow `KUBEADM_INIT_PHASES` in `code/part05/kubeadm_bootstrap_validator.py` (`preflight -> certs -> kubeconfig -> kubelet-start -> control-plane -> etcd -> upload-config -> upload-certs -> mark-control-plane -> bootstrap-token -> addon`). List the exact files each phase creates in `/etc/kubernetes/pki/`, `/etc/kubernetes/manifests/` and `/etc/kubernetes/*.conf`.
3. Work through the CNI and secure worker TLS bootstrapping. Using `verify_kubeadm_join_credentials()` in `code/part05/kubeadm_bootstrap_validator.py`, explain why `cp1` stays `NotReady` and `coredns` stays `Pending` until a CNI is installed. Explain how `--token` (`[a-z0-9]{6}.[a-z0-9]{16}`) and `--discovery-token-ca-cert-hash sha256:<hex>` prevent a rogue API server MITM attack during `kubeadm join`. Then explain how `serverTLSBootstrap: true` affects `kubectl logs` and `exec`.
4. Build the highly available control plane with `kube-vip` or `HAProxy`, `--control-plane` and `--upload-certs`. Trace how `kube-vip` provides a floating ARP/BGP virtual IP (`10.0.0.100`) as a static pod on `cp1..cp3`. Explain how `--upload-certs` encrypts control-plane PKI keys into a short-lived (2-hour) Secret for `kubeadm join --control-plane --certificate-key <key>`. Then verify the 3-member `etcd` cluster and the leader failover when `cp1` is powered off.
5. Add the GPU worker and practise the everyday `kubectl` commands. Trace the four-step sequence in Section 9 to join `gpu1` (`nvidia-smi` -> `nvidia-ctk runtime configure --runtime=containerd` -> `kubeadm join` -> `nvidia-device-plugin` + `nvidia.com/gpu=present:NoSchedule` taint). Then write the commands from *Kubernetes: Up and Running*, Chapter 4 for `kubectl config set-context` and `use-context`, `kubectl apply view-last-applied`, `edit-last-applied` and `set-last-applied`, `kubectl attach`, and `kubectl completion bash`.
6. Compare the deployment models. Set Managed Kubernetes, Prebuilt Installers (`Kubespray`, `RKE2`, `Cluster API`, `BCM`) and `kubeadm` + Packer/Ansible against each other, across control, toil and bare-metal requirements. Use *Production Kubernetes*, Chapters 1 and 2, as your source. Then diagnose three classic failures from Section 11: (a) `kubeadm init` hanging while it waits for `kubelet`, (b) CoreDNS crash-looping on `/etc/resolv.conf` `127.0.0.53`, and (c) dirty state left behind after `kubeadm reset`.

Pick the exercise that covers the part of the cluster you understand least, and start there. Work through it on your own lab VMs, so you can check each answer against real output.

## Checkpoint questions (20)

<details>
<summary>1. Why must `swap` be disabled (`swapoff -a`), and why are the `overlay` and `br_netfilter` kernel modules plus `net.bridge.bridge-nf-call-iptables = 1` required on every node?</summary>

- **`swapoff -a`:** By default, `kubelet` refuses to start if swap is active. Kubernetes QoS classes (`Guaranteed`, `Burstable`) and memory eviction thresholds expect deterministic physical RAM accounting (`memory.max`). Swapping a latency-sensitive GPU training process to disk destroys gang-synchronous step times.
- **`overlay` module:** It provides the `overlayfs` union filesystem that `containerd` or `CRI-O` use for container root filesystems.
- **`br_netfilter`, `net.bridge.bridge-nf-call-iptables = 1` and `net.ipv4.ip_forward = 1`:** These make sure L2 bridged Pod traffic passes through the host's `netfilter` and `iptables` chains. That is required for `kube-proxy` `ClusterIP` Service DNAT and CNI `NetworkPolicy` enforcement. They also let the kernel route packets between Pod and host interfaces.
</details>

<details>
<summary>2. Why does `systemctl enable --now kubelet` crash-loop immediately after installing the `kubelet` package, before `kubeadm init` or `kubeadm join` is run?</summary>

This is completely normal and expected. The `kubelet` systemd unit needs `/var/lib/kubelet/config.yaml` and `/etc/kubernetes/kubelet.conf` (or `--bootstrap-kubeconfig`). Those files **do not exist until `kubeadm init` or `kubeadm join` generates them** during the `kubeconfig` and `kubelet-start` phases.
</details>

<details>
<summary>3. Why should you always set `controlPlaneEndpoint: "k8s-api.lab.local:6443"` and `apiServer.certSANs` in `ClusterConfiguration` even if you start with a single control-plane node?</summary>

`controlPlaneEndpoint` sets the canonical DNS name or VIP address. It is written into `kubeadm-config`, `cluster-info` and every node's `kubelet.conf`. Suppose you initialise `cp1` with its raw node IP (`10.0.0.11:6443`) and leave out `controlPlaneEndpoint`. Converting the cluster to a 3-node HA control plane later means regenerating the API server certificates (`certSANs`) by hand, editing ConfigMaps, and rewriting `/etc/kubernetes/kubelet.conf` on every worker node. If you point `controlPlaneEndpoint` at a DNS name or VIP (`10.0.0.100:6443`) from day 1, adding `cp2` and `cp3` becomes a single `kubeadm join --control-plane` command.
</details>

<details>
<summary>4. Walk through the 11 phases of `kubeadm init` and the directories they populate on `cp1`.</summary>

1. **`preflight`:** Checks root privileges, swap off, free ports (`6443`, `2379–2380`, `10250–10259`), kernel modules and CRI socket reachability.
2. **`certs`:** Generates the cluster CA, etcd CA, front-proxy CA, the ServiceAccount keypair (`sa.key`/`sa.pub`) and leaf TLS certificates in **`/etc/kubernetes/pki/`**.
3. **`kubeconfig`:** Generates `admin.conf`, `super-admin.conf`, `kubelet.conf`, `controller-manager.conf` and `scheduler.conf` in **`/etc/kubernetes/`**.
4. **`kubelet-start`:** Writes `/var/lib/kubelet/config.yaml` and starts `kubelet`.
5. **`control-plane`:** Writes static Pod manifests (`kube-apiserver.yaml`, `kube-controller-manager.yaml`, `kube-scheduler.yaml`) into **`/etc/kubernetes/manifests/`**.
6. **`etcd`:** Writes the static Pod manifest **`/etc/kubernetes/manifests/etcd.yaml`** (`dataDir: /var/lib/etcd`).
7. **`upload-config`:** Uploads `ClusterConfiguration` and `KubeletConfiguration` to `kube-system` ConfigMaps (`kubeadm-config`, `kubelet-config`).
8. **`upload-certs`:** When `--upload-certs` is passed, it encrypts control-plane PKI private keys into the `kube-system/kubeadm-certs` Secret, which has a **2-hour TTL**.
9. **`mark-control-plane`:** Applies the label `node-role.kubernetes.io/control-plane` and the taint `node-role.kubernetes.io/control-plane:NoSchedule`.
10. **`bootstrap-token`:** Creates a 24-hour bootstrap token Secret in `kube-system`, along with RBAC rules for node TLS bootstrapping.
11. **`addon`:** Deploys the **`coredns`** Deployment and Service and the **`kube-proxy`** DaemonSet.
</details>

<details>
<summary>5. What are the default lifetimes of the CA certificates and leaf certificates created by `kubeadm` in `/etc/kubernetes/pki`, and how do you check or renew them?</summary>

- **Root CAs (`ca.crt`, `etcd/ca.crt`, `front-proxy-ca.crt`):** Valid for **10 years**.
- **Leaf certificates (`apiserver.crt`, `apiserver-kubelet-client.crt`, `front-proxy-client.crt`, `etcd/server.crt`, `etcd/peer.crt`):** Valid for **1 year**, and renewed automatically during `kubeadm upgrade apply`.
- **Check expiration:** Run `sudo kubeadm certs check-expiration`.
- **Manual renewal:** Run `sudo kubeadm certs renew all`, then restart the control-plane static pods. You can do that with `crictl stopp`, or by moving the manifests out of `/etc/kubernetes/manifests/` and back in.
</details>

<details>
<summary>6. Why does `cp1` remain `NotReady` and `coredns` remain `Pending` right after `kubeadm init` finishes?</summary>

`kubeadm init` intentionally does **not** install a CNI plugin. Until a CNI plugin (Calico, Cilium or Flannel) writes its configuration into `/etc/cni/net.d/`, the kubelet's network readiness check fails with `network plugin is not ready: cni config uninitialized`. That keeps the node condition at `Ready=False`, with the `node.kubernetes.io/not-ready:NoSchedule` taint. The taint in turn stops the `coredns` Deployment pods from being scheduled. Once the CNI DaemonSet writes `/etc/cni/net.d/` and starts, `cp1` turns `Ready` and `coredns` moves to `Running`.
</details>

<details>
<summary>7. How do `--token` and `--discovery-token-ca-cert-hash` work together during `kubeadm join`?</summary>

When a new worker runs `kubeadm join k8s-api.lab.local:6443 --token <id>.<secret> --discovery-token-ca-cert-hash sha256:<hash>`, three things happen.

1. The worker fetches the public `cluster-info` ConfigMap. It contains the cluster's root `ca.crt`, and it is signed with a JWS signature made with the bootstrap `<secret>`.
2. The worker hashes the public key of `ca.crt` with SHA-256 and checks that it equals `--discovery-token-ca-cert-hash`. This is what prevents a Man-in-the-Middle attacker from spoofing the API server.
3. With the now-trusted `ca.crt` and the bootstrap token, which is valid for **24 hours** by default, the `kubelet` connects over TLS to `kube-apiserver`. It submits a **Certificate Signing Request (`CSR`)** for its own unique `system:node:<hostname>` client certificate. The `csrapproving` controller in `kube-controller-manager` signs it, and the kubelet writes **`/etc/kubernetes/kubelet.conf`**.
</details>

<details>
<summary>8. What does `serverTLSBootstrap: true` in `KubeletConfiguration` do, and what happens if you forget to approve the resulting CSRs?</summary>

By default, the `kubelet` generates a **self-signed** serving certificate for its HTTPS API on port `10250`. That means `kube-apiserver` or `metrics-server` cannot verify the kubelet's serving certificate cryptographically, unless you use `--kubelet-insecure-tls`. Setting **`serverTLSBootstrap: true`** tells each `kubelet` to submit a `CertificateSigningRequest` (`kubernetes.io/kubelet-serving`) that the cluster CA signs. Until you approve those CSRs, by running `kubectl get csr && kubectl certificate approve <csr-name>` or `kubelet-csr-approver`, **`kubectl logs`, `kubectl exec`, `kubectl port-forward` and `metrics-server` fail with TLS certificate verification errors**.
</details>

<details>
<summary>9. In *Kubernetes: Up and Running* Chapter 4, how do you create and switch `kubectl` contexts, and how do you inspect the `last-applied-configuration` annotation?</summary>

- **Create and switch contexts:** Run these two commands.

  ```bash
  kubectl config set-context my-context --namespace=mystuff
  kubectl config use-context my-context
  ```

- **Inspect or edit the client-side `kubectl.kubernetes.io/last-applied-configuration` annotation:** Use one of these three commands.
  - `kubectl apply -f myobj.yaml view-last-applied`
  - `kubectl apply -f myobj.yaml edit-last-applied`
  - `kubectl apply -f myobj.yaml set-last-applied`
</details>

<details>
<summary>10. In *Kubernetes: Up and Running* Chapter 4, what is the difference between `kubectl exec` and `kubectl attach`?</summary>

- **`kubectl exec -it <pod> -- /bin/sh`:** Starts a **brand-new process** inside the running container's namespaces and cgroups. It needs a shell or a binary such as `/bin/sh` in the container image, so it fails on `scratch` or `distroless` images.
- **`kubectl attach -it <pod>`:** Attaches your terminal to the `stdin`, `stdout` and `stderr` streams of the **already-running PID 1 main container process**. It does not start a new binary inside the container.
</details>

<details>
<summary>11. How does `kube-vip` provide a highly available control-plane endpoint on bare metal without an external hardware load balancer?</summary>

`kube-vip` runs as a **Static Pod** (`/etc/kubernetes/manifests/kube-vip.yaml`) next to `kube-apiserver` on all 3 control-plane nodes: `cp1`, `cp2` and `cp3`. It uses Kubernetes Lease leader election in ARP/L2 mode, or BGP peering in L3 mode, to pick one leader. The elected leader binds the virtual IP (`10.0.0.100` / `k8s-api.lab.local`) to its network interface, and it answers ARP requests. On failover it sends a gratuitous ARP. If `cp1` goes down, `cp2` or `cp3` wins the Lease within seconds and claims `10.0.0.100` seamlessly.
</details>

<details>
<summary>12. How does joining a second control-plane node (`cp2`) differ from joining a worker node (`w1`), and what happens if `--upload-certs` was run more than 2 hours ago?</summary>

Joining a control-plane node needs **`--control-plane --certificate-key <64-char-hex-key>`**, on top of `--token` and `--discovery-token-ca-cert-hash`. `kubeadm` uses the certificate key to download and decrypt the cluster CA private key (`ca.key`), the `etcd/ca.key` and the ServiceAccount key (`sa.key`) from the `kube-system/kubeadm-certs` Secret. That lets `cp2` mint its own local static pod certificates and join the stacked `etcd` Raft cluster. For security, `kubeadm` deletes the `kubeadm-certs` Secret automatically after **2 hours**. If it has expired, run **`sudo kubeadm init phase upload-certs --upload-certs`** on `cp1` to generate a fresh 2-hour key.
</details>

<details>
<summary>13. Why does `coredns` enter `CrashLoopBackOff` with `loop ... detected` on Ubuntu nodes running `systemd-resolved`, and how does `kubeadm` / `kubelet` handle it?</summary>

On Ubuntu hosts that run `systemd-resolved`, `/etc/resolv.conf` points to the local stub resolver, **`nameserver 127.0.0.53`**. When `coredns` pods inherit that file from the node to forward external DNS queries, `127.0.0.53` inside the pod's own network namespace points back at the `coredns` pod itself. That creates an endless forwarding loop, which CoreDNS's `loop` plugin catches. The fix is to set `resolvConf: /run/systemd/resolve/resolv.conf` in `KubeletConfiguration`. `kubeadm` detects this automatically when `systemd-resolved` is active at init time.
</details>

<details>
<summary>14. Why must every node in a Kubernetes cluster have a unique hostname, MAC address, and `/sys/class/dmi/id/product_uuid`?</summary>

The `kubelet` and cloud or network plugins use the hostname, the primary interface MAC address and the SMBIOS `product_uuid` to identify each `Node` object. They use these values to allocate per-node Pod CIDR blocks and to track volume attachments. Suppose two VMs are cloned from the same template without regenerating the MAC addresses, `product_uuid` and `/etc/machine-id` (or hostnames). The second node then overwrites the first node's registration in `kube-apiserver`. The result is erratic `Ready`/`NotReady` flapping and broken Pod routing.
</details>

<details>
<summary>15. Why must `apt-mark hold kubelet kubeadm kubectl` be run immediately after installing the Kubernetes packages?</summary>

Without `apt-mark hold`, an unattended `apt-get upgrade` or a security patching job can silently upgrade `kubelet` and `kubeadm` to the latest patch or minor version in the repository. That breaks Kubernetes's version skew policy, which says `kubelet` must never be newer than `kube-apiserver`. It can also restart `kubelet` outside a controlled maintenance drain.
</details>

<details>
<summary>16. What are the exact steps to add a bare-metal GPU worker node (`gpu1`) to a `kubeadm` cluster and protect it from CPU-only pods?</summary>

1. Prepare the OS prerequisites: disable swap, load `overlay` and `br_netfilter`, set the sysctls, install chrony, and configure `containerd` with `SystemdCgroup = true`.
2. Install the host **NVIDIA GPU driver** and confirm that `nvidia-smi` works. Install the **NVIDIA Container Toolkit**, then run `sudo nvidia-ctk runtime configure --runtime=containerd` and restart `containerd`.
3. Run `sudo kubeadm join ...` to join the cluster.
4. Taint the node with **`kubectl taint node gpu1 nvidia.com/gpu=present:NoSchedule`**.
5. Deploy the **NVIDIA Device Plugin**, or the GPU Operator with `driver.enabled=false`. Then verify that `status.allocatable["nvidia.com/gpu"]` reports the expected GPU count.
</details>

<details>
<summary>17. In *Production Kubernetes* Chapters 1 and 2, why is Kubernetes described as an \"engine\" or \"foundation\" rather than a finished PaaS like Heroku or Cloud Foundry?</summary>

Prebuilt PaaS offerings such as `Heroku` and `Cloud Foundry` give developers a "move-in-ready apartment" for 12-factor web apps. They break down once you need custom GPU scheduling, RDMA networking, DaemonSets or stateful distributed operators. Kubernetes instead gives you a modular **foundation**, with standardized plug-in interfaces (**CRI, CNI, CSI, CPI, Device Plugins, Webhooks, CRDs**). Platform engineers can then build a custom application or AI platform that fits their exact hardware and organizational needs.
</details>

<details>
<summary>18. In *Production Kubernetes* Chapter 2, what virtualization conveniences do you lose when running Kubernetes on bare metal, and what tools replace them?</summary>

On bare metal, you lose cloud and hypervisor APIs for instant VM cloning, virtual networks, cloud load balancers (`Service type=LoadBalancer`) and elastic block storage. You replace them with these tools.

- **PXE and image provisioning, with BMC control:** NVIDIA Base Command Manager (`BCM`), Canonical MAAS, Tinkerbell, Matchbox or Metal3 (`Cluster API Provider Metal3`), driving IPMI or Redfish.
- **OS and node consistency:** Immutable golden images built with **Packer + Ansible**, or Talos Linux or Flatcar.
- **Service load balancing:** **MetalLB**, **Cilium BGP or L2 announcements**, or **kube-vip**.
- **Storage:** Local NVMe CSI (`topolvm`, `openebs-localpv`), plus distributed or parallel filesystems (`Ceph-CSI`, `Lustre`, `WEKA`, `VAST`).
</details>

<details>
<summary>19. Why is running `sudo kubeadm reset -f` alone NOT sufficient to completely clean a node before re-initializing or switching CNI plugins?</summary>

`kubeadm reset -f` stops `kubelet`, removes the static Pod containers, and cleans `/etc/kubernetes` and `/var/lib/kubelet`. It does **not** delete `/etc/cni/net.d/*`, the CNI virtual interfaces (`cali*`, `cilium_*`, `flannel.1`, `cni0`), or the `iptables` and IPVS rules. Leftover `/etc/cni/net.d/10-calico.conflist` files or stale `KUBE-SVC-*` iptables chains will break the next install. So always follow `kubeadm reset -f` with `rm -rf /etc/cni/net.d /var/lib/etcd $HOME/.kube`, flush `iptables` and `ipvsadm`, and restart `containerd` or reboot the node.
</details>

<details>
<summary>20. How do you replace a permanently failed control-plane node (`cp2`) in a 3-node stacked-etcd `kubeadm` cluster?</summary>

2 of 3 `etcd` members (`cp1` and `cp3`) are still alive, so the cluster keeps Raft quorum at `2/3`. Replace `cp2` in three steps.

1. Delete the dead Kubernetes Node object with `kubectl delete node cp2`.
2. Connect to `etcd-cp1` and run `etcdctl member list` to find the dead `cp2` member ID. Then remove that member from the Raft cluster with **`etcdctl member remove <cp2-member-id>`**. On older versions, also clean up its entry in the `kubeadm-config` `ClusterStatus`, if one is present.
3. Provision a fresh replacement host. Run `sudo kubeadm init phase upload-certs --upload-certs` on `cp1`, then join the new node with `sudo kubeadm join ... --control-plane --certificate-key <key>`.
</details>

## Sources and review notes

- **Sources read in full:**
  - `kubernetes-up-and-running-3rd-edition` — Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, *Kubernetes: Up and Running*, 3rd ed., **Chapter 3: Deploying a Kubernetes Cluster** (cluster setup, `kubectl version`, `get/describe nodes`, `kube-system` components), **Chapter 4: Common kubectl Commands** (read in full: namespaces, contexts `set-context`/`use-context`, `kubectl get/describe`, `kubectl apply` and `view-last-applied`/`edit-last-applied`/`set-last-applied`, `kubectl delete`, labels, `logs`/`exec`/`attach`/`cp`/`port-forward`, `kubectl top`, and `kubectl completion bash`), and **Appendix A: Building a Raspberry Pi Kubernetes Cluster** (bare-metal cluster assembly).
  - `production-kubernetes` — Josh Rosso, Rich Lander, Alexander Brand & John Harris, *Production Kubernetes*, **Chapter 1: Path to Production** and **Chapter 2: Deployment Models** (read in full: Chapter 2 bare-metal versus virtualized infrastructure, compute and networking planning, containerized control plane components, and add-on installation; core Kubernetes components, CRI/CNI/CSI/CPI plug-in interfaces, in-tree vs out-of-tree providers, and building an application platform on Kubernetes) and **Chapter 2: Deployment Models** (read in full: Managed Services vs Prebuilt Installers vs Roll Your Own, bare-metal vs virtualization trade-offs, HA control plane and etcd topologies, Dev/Testing/Staging/Prod cluster tiers, and Packer + Ansible machine image automation).
- **Run here:** `python3 code/part05/kubeadm_bootstrap_validator_lab.py` (2 passed, 0 failed).
- **Explicitly labelled inferences:** The `validate_node_preflight_and_cidrs` (`SystemdCgroup=true`) and `verify_kubeadm_join_credentials` models in `code/part05/kubeadm_bootstrap_validator.py` and the `kubeadm-config.yaml` (`v1beta3` / `v1beta4`), Calico `Installation`, `kube-vip`, and Ansible node-prep snippets are the author's constructions synthesizing `KUR` Chapters 3–4, `PK` Chapters 1–2, and upstream `kubeadm` documentation (plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, and 35).
- **Not verified on live hardware:** Live `kubeadm init`, `kubeadm join`, Calico/Cilium, `kube-vip`, and NVIDIA device plugin executions (`v1.30.4`, `10.0.0.11..100`, `10.244.0.0/16`, `10.96.0.0/12`, `524288`, `8192`, `262144`, `v3.28.0`, `blockSize: 26`, `v0.8.0`, `0.16.2`, `v0.0.28`, `127.0.0.53`, `24 h` token, `2 h` upload-certs, `1 year` leaf certs, `10 years` CA) are marked (`untested here`) where not executed by `kubeadm_bootstrap_validator_lab.py`.
