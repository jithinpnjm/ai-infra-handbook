---
id: "c04-24"
title: "4.24 Terraform on GCP and Nebius: networks, GPU VMs and GKE"
sidebar_label: "4.24 Terraform on GCP and Nebius: networks, GPU VMs and GKE"
sidebar_position: 24
description: "Provisioning GPU infrastructure with Terraform: GCP VPCs and subnets, firewall and NAT, GPU VM families and capacity (reservations, DWS, spot), GKE clusters and GPU node pools, storage and IAM, plus the Nebius provider model for GPU clusters, InfiniBand fabrics, Kubernetes and Slurm-style environments"
status: "drafted"
tier: "1"
level: "I"
lab_venue: "GCP / GKE"
---

# 4.24 Terraform on GCP and Nebius: networks, GPU VMs and GKE

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Terraform/OpenTofu, `gcloud`, GCP project with GPU quota (or CPU-only rehearsal); optional Nebius account and CLI |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

GPU capacity is where AI platforms spend most of their budget, and it lives in clouds and GPU clouds with very different shapes. Hyperscalers such as GCP give you rich primitives (VPC, IAM, GKE, managed storage, reservations) around a limited set of GPU machine families; GPU-focused providers such as Nebius, CoreWeave or Lambda expose clusters with InfiniBand fabrics, shared filesystems and Kubernetes or Slurm layers, often with simpler but different APIs. A platform engineer needs to express both as code: the network, the capacity, the clusters, the storage and the identity, with the guardrails of 4.23. This chapter works through a representative GCP stack end to end and then maps the same design onto a Nebius-style GPU cloud, so you can reason about which concepts transfer and which are provider-specific. (Products and APIs change quickly; every identifier here must be verified against current provider documentation.)

## Prerequisites and outcomes

Needs 4.18 to 4.23 and networking basics (Part 2). After this chapter you can:

- Design and code a GCP landing zone for AI: projects, VPC/subnets, private access, firewall, Cloud NAT, service accounts and workload identity, KMS, storage buckets for datasets and checkpoints.
- Provision GPU VMs (A2/A3/A4-class families, G2/L4) and GKE clusters with GPU node pools, taints/labels, autoscaling, and driver installation options; understand capacity options (on-demand, reservations, spot, DWS flex/calendar) and quotas.
- Configure high-performance networking for multi-node training on GCP (multiple VPCs/NICs, jumbo MTU, compact placement, GPUDirect-TCPX/RDMA variants) at a conceptual and Terraform level.
- Describe Nebius's resource model (tenants/projects, networks and subnets, compute instances with GPU platforms, GPU clusters with InfiniBand fabrics, shared filesystems, managed Kubernetes and Slurm options, service accounts) and how its Terraform provider is used; compare with GCP and CoreWeave.
- Structure multi-cloud modules around a common interface and keep provider-specific details inside.

## 1. Designing the landing zone (GCP)

```mermaid
flowchart TB
  ORG["Organisation / folders"] --> PRJ["Projects: ai-shared, ai-dev, ai-prod\n(billing, quotas, IAM boundary)"]
  PRJ --> NET["VPC: custom subnets\nprivate Google access, Cloud NAT, firewall"]
  NET --> GKE["GKE cluster (private nodes)\nsystem pool + GPU pools"]
  NET --> VMS["GPU VMs / Slurm cluster\n(compact placement, multi-NIC)"]
  PRJ --> ST["GCS buckets: datasets, checkpoints\nCMEK, versioning, uniform access"]
  PRJ --> IAM["Service accounts + Workload Identity\nno JSON keys"]
  PRJ --> AR["Artifact Registry (images)"]
  PRJ --> MON["Cloud Monitoring/Logging,\nbudgets & alerts"]
```

Decisions to make before writing code:

- **Project and environment structure**: separate projects per environment and a shared-services project (registry, DNS, logging); quotas, billing and IAM boundaries follow project boundaries. Create projects with Terraform in a `global` stack using a service account with organisation-level permissions (kept tightly controlled).
- **Regions and zones for GPUs**: GPU families exist only in specific zones; capacity varies; check `gcloud compute accelerator-types list`, `gcloud compute machine-types list --filter="name~a3"` and quota pages. Plan for zones where you actually have quota/reservations; multi-region fallbacks have cost and data gravity implications.
- **Identity**: workload identity federation for CI (4.22), service accounts per workload, no long-lived keys, organisation policies (`iam.disableServiceAccountKeyCreation`).
- **Data and checkpoints**: buckets colocated with compute (same region) for throughput and egress cost; CMEK; versioning and retention; consider Filestore, Parallelstore, Managed Lustre or GCS FUSE/Anywhere Cache for training IO (Part 13).

## 2. Network

```hcl
resource "google_compute_network" "train" {
  name                    = "${local.prefix}-train"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
  mtu                     = 8896                        # up to 8896 supported; match on NICs/pods
}

resource "google_compute_subnetwork" "nodes" {
  name                     = "${local.prefix}-nodes"
  region                   = var.region
  network                  = google_compute_network.train.id
  ip_cidr_range            = "10.30.0.0/20"
  private_ip_google_access = true
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.32.0.0/14"
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.36.0.0/20"
  }
  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.1
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_router" "nat" {
  name    = "${local.prefix}-router"
  region  = var.region
  network = google_compute_network.train.id
}
resource "google_compute_router_nat" "egress" {
  name                               = "${local.prefix}-nat"
  router                             = google_compute_router.nat.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

resource "google_compute_firewall" "internal" {
  name      = "${local.prefix}-allow-internal"
  network   = google_compute_network.train.name
  direction = "INGRESS"
  allow { protocol = "tcp" }
  allow { protocol = "udp" }
  allow { protocol = "icmp" }
  source_ranges = ["10.30.0.0/20", "10.32.0.0/14"]
}
resource "google_compute_firewall" "iap_ssh" {
  name          = "${local.prefix}-allow-iap-ssh"
  network       = google_compute_network.train.name
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["35.235.240.0/20"]          # Identity-Aware Proxy range: SSH via `gcloud compute ssh --tunnel-through-iap`
}
```

Notes: GCP VPCs are global with regional subnets; firewall rules are stateful and applied by tags/service accounts (prefer service-account-based targets); use Cloud NAT instead of public IPs on nodes; enable Private Google Access; avoid overlapping ranges with on-prem; size pod/service ranges for the largest cluster (GKE needs large alias ranges); VPC flow logs cost money, sample them. For **multi-node GPU training on A3-class machines** Google documents multi-NIC designs: several additional VPC networks (one per GPU NIC), each with its own subnet, MTU 8244/8896 as documented, and firewall rules allowing all traffic within; the main NIC for general traffic and the extra NICs for GPU-to-GPU network traffic (GPUDirect-TCPX or newer GPUDirect-RDMA variants for A3 Ultra/A4 using RoCE VPCs). Follow the current "create GPU VMs with high-performance networking" documents because machine type, image (e.g. Container-Optimized OS or Ubuntu with the NCCL plugin), and network topology details change between generations.

## 3. GPU virtual machines

```hcl
resource "google_compute_instance" "gpu_login" {
  name         = "${local.prefix}-gpu-test"
  zone         = var.zone
  machine_type = var.gpu_machine_type             # e.g. "g2-standard-8" (1x L4) for rehearsal; "a3-highgpu-8g" for H100 x8
  tags         = ["gpu-node"]

  boot_disk {
    initialize_params {
      image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"
      size  = 500
      type  = "pd-ssd"
    }
  }

  # For N1/A2/G2 families, accelerators attach via guest_accelerator or are bundled in the machine type (A2/A3/G2 bundle GPUs)
  scheduling {
    on_host_maintenance = "TERMINATE"
    automatic_restart   = false
    provisioning_model  = var.use_spot ? "SPOT" : "STANDARD"
    instance_termination_action = var.use_spot ? "STOP" : null
  }

  network_interface {
    subnetwork = google_compute_subnetwork.nodes.id
  }

  service_account {
    email  = google_service_account.node.email
    scopes = ["cloud-platform"]                  # restrict via IAM roles on the SA, not scopes
  }

  shielded_instance_config {
    enable_secure_boot          = false          # NVIDIA driver modules need signing if Secure Boot is on
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  metadata = {
    enable-oslogin = "TRUE"
    startup-script = file("${path.module}/scripts/bootstrap.sh")    # keep minimal; configure with Ansible (4.17)
  }
  labels = local.labels

  lifecycle {
    ignore_changes = [metadata["ssh-keys"]]
  }
}
```

Considerations:

- **Machine families**: A2 (A100), A3 (H100: `a3-highgpu-8g`, `a3-megagpu-8g`, `a3-edgegpu`), A3 Ultra (H200), A4 (B200), A4X (GB200 NVL72) and G2 (L4) have GPUs bundled into the machine type; N1 uses attached accelerators. Machine types, GPU counts, networking and availability differ by zone and change over time; verify with `gcloud compute machine-types list` and the accelerator documentation.
- **Capacity**: on-demand quota per GPU family and region; **reservations** (`google_compute_reservation`, shared across projects), **future reservations**, **Dynamic Workload Scheduler** flex-start and calendar mode (for large short jobs), **Spot/preemptible** with termination handling (checkpoint frequently), committed use discounts. Treat reservations as code with owners and expiry (4.23).
- **Boot images and drivers**: Deep Learning VM images (drivers preinstalled), Container-Optimized OS with the GPU driver installer, or your own golden image built with Packer + Ansible (4.2, 4.17); Secure Boot requires signed modules.
- **Compact placement** (`resource_policies` with a `COMPACT` `group_placement_policy`) for low-latency collectives; **maintenance policies** and host maintenance events (live migration is unsupported for GPU VMs: `TERMINATE` or scheduled maintenance windows).
- **Disks**: local SSD for scratch (A3 includes), Hyperdisk/PD for persistent; mount options and filesystem choices in Part 13.
- **OS Login and IAP** for SSH; no public IPs.
- **Instance templates and managed instance groups** (MIGs) for homogeneous worker pools (with update policies for rolling replacement, 4.21), or `google_compute_instance` per node for Slurm-style static clusters with deterministic names.

```hcl
resource "google_compute_resource_policy" "compact" {
  name   = "${local.prefix}-compact"
  region = var.region
  group_placement_policy {
    collocation  = "COLLOCATED"
    vm_count     = var.node_count
  }
}
# attach with: resource_policies = [google_compute_resource_policy.compact.id] on the instances
```

## 4. GKE clusters and GPU node pools

```hcl
resource "google_container_cluster" "main" {
  name     = "${local.prefix}-gke"
  location = var.region                                  # regional control plane; or a zone for a zonal cluster
  network    = google_compute_network.train.id
  subnetwork = google_compute_subnetwork.nodes.id

  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection      = true

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = var.admin_cidr
      display_name = "admin"
    }
  }
  workload_identity_config { workload_pool = "${var.project_id}.svc.id.goog" }
  release_channel { channel = "REGULAR" }
  datapath_provider = "ADVANCED_DATAPATH"                 # Dataplane V2 (eBPF/Cilium)
  logging_config { enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"] }
  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS"]
    managed_prometheus { enabled = true }
  }
}

resource "google_container_node_pool" "system" {
  name       = "system"
  cluster    = google_container_cluster.main.name
  location   = var.region
  node_count = 1
  node_config {
    machine_type    = "e2-standard-8"
    service_account = google_service_account.node.email
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]
    workload_metadata_config { mode = "GKE_METADATA" }
  }
}

resource "google_container_node_pool" "gpu" {
  for_each   = var.gpu_pools
  name       = each.key
  cluster    = google_container_cluster.main.name
  location   = var.region
  node_locations = each.value.zones
  autoscaling {
    min_node_count = each.value.min_nodes
    max_node_count = each.value.max_nodes
    location_policy = "ANY"
  }
  management {
    auto_repair  = true
    auto_upgrade = false                               # control upgrades yourself for training pools
  }
  upgrade_settings {
    strategy        = "SURGE"
    max_surge       = 0
    max_unavailable = 1
  }
  node_config {
    machine_type    = each.value.machine_type
    service_account = google_service_account.node.email
    disk_size_gb    = 500
    disk_type       = "pd-ssd"
    labels          = { pool = each.key, accelerator = each.value.gpu_type }
    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }
    guest_accelerator {
      type  = each.value.gpu_type                       # e.g. "nvidia-l4"; for A3 the GPUs come with the machine type
      count = each.value.gpu_count
      gpu_driver_installation_config { gpu_driver_version = "LATEST" }
    }
    workload_metadata_config { mode = "GKE_METADATA" }
    reservation_affinity {
      consume_reservation_type = each.value.reservation == null ? "NO_RESERVATION" : "SPECIFIC_RESERVATION"
      key    = each.value.reservation == null ? null : "compute.googleapis.com/reservation-name"
      values = each.value.reservation == null ? null : [each.value.reservation]
    }
  }
  lifecycle { ignore_changes = [initial_node_count] }
}
```

Practical points:

- **Layering**: create the cluster and node pools in the cluster stack; install add-ons (GPU operator or GKE's device plugin and drivers, Kueue/JobSet, Prometheus, ingress, Argo CD) in a separate stack/Helm layer (4.25, 4.26).
- **Drivers**: GKE can install drivers for supported GPU types (`gpu_driver_installation_config`), or you can run the NVIDIA GPU Operator with `driver.enabled=false`/true depending on node images (Part 11); do not run two managers for the same driver.
- **Taints and labels**: taint GPU pools so only GPU workloads land there; label for node selection and cost reporting. GKE adds `cloud.google.com/gke-accelerator` labels automatically.
- **Autoscaling**: GPU pools scaling from zero (min 0) save money but depend on capacity availability; use `location_policy = "ANY"` to prefer available zones; for tightly coupled multi-node jobs consider fixed-size, compact-placement pools or **GKE multi-host TPU/GPU** features, and use Kueue with ProvisioningRequest/DWS to acquire capacity atomically.
- **Upgrades**: surge upgrades with `max_surge` consume extra GPUs that may not exist; `max_unavailable` > 0 with drains is typical; schedule maintenance windows; disable auto-upgrade for pools with reservations if you need control (balance with security patch policy).
- **Workload Identity** binds Kubernetes service accounts to Google service accounts for access to buckets without keys:

```hcl
resource "google_service_account" "trainer" {
  account_id = "trainer"
}
resource "google_service_account_iam_member" "wi" {
  service_account_id = google_service_account.trainer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[training/trainer-ksa]"
}
resource "google_storage_bucket_iam_member" "rw" {
  bucket = google_storage_bucket.checkpoints.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.trainer.email}"
}
```

- **Deletion protection** (`deletion_protection = true`) plus `prevent_destroy` for clusters (4.21); node pool replacement is expected, cluster replacement is not.

## 5. Storage, KMS and IAM building blocks

```hcl
resource "google_kms_key_ring" "ml" {
  name     = "${local.prefix}-ml"
  location = var.region
}
resource "google_kms_crypto_key" "ckpt" {
  name            = "checkpoints"
  key_ring        = google_kms_key_ring.ml.id
  rotation_period = "7776000s"                       # 90 days
  lifecycle { prevent_destroy = true }
}

resource "google_storage_bucket" "checkpoints" {
  name                        = "${var.project_id}-${local.prefix}-ckpt"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  versioning { enabled = true }
  encryption { default_kms_key_name = google_kms_crypto_key.ckpt.id }
  lifecycle_rule {
    condition {
      age        = 30
      with_state = "ARCHIVED"
    }
    action { type = "Delete" }
  }
  lifecycle { prevent_destroy = true }
}
```

(Bucket service agent needs `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the key.) For training IO consider regional buckets in the same region as compute, hierarchical namespace buckets, GCS FUSE CSI driver on GKE, Anywhere Cache, and parallel file systems (Parallelstore/Managed Lustre/Filestore) for datasets and checkpoints (Part 13). Budgets and alerts:

```hcl
resource "google_billing_budget" "gpu" {
  billing_account = var.billing_account
  display_name    = "${local.prefix}-gpu-budget"
  amount {
    specified_amount {
      currency_code = "USD"
      units         = "50000"
    }
  }
  threshold_rules { threshold_percent = 0.5 }
  threshold_rules { threshold_percent = 0.9 }
  all_updates_rule { pubsub_topic = google_pubsub_topic.budget.id }
}
```

## 6. Slurm-style clusters on GCP

For HPC-style users: **Cluster Toolkit** (formerly HPC Toolkit) generates Terraform for Slurm clusters on GCP (controller, login nodes, partitions of GPU VMs, Filestore/Lustre, ephemeral/autoscaled compute with Slurm's cloud scheduling). You can use its blueprints as modules, or build your own: Terraform creates the VMs/instance templates, networks and storage; Ansible or the Slurm GCP images configure Slurm (Part 6); node resume/suspend scripts call the GCP API for elasticity. Keep the same layering and guardrails (4.23): network, storage, controller, partitions as separate stacks or clearly separated modules.

## 7. Nebius: the GPU-cloud model

Nebius AI Cloud (a GPU-focused provider) offers resources aimed at AI training and inference. Names and APIs evolve, so treat the following as the conceptual map and **verify every attribute against the current Nebius Terraform provider documentation**.

| Concern | Typical Nebius building block | GCP analogue |
|---|---|---|
| Tenancy | Tenant → projects (regions are tied to projects); service accounts with authorised keys / federation | Organisation → projects |
| Network | VPC networks and subnets, security groups, static IPs, private endpoints | VPC, subnets, firewall |
| GPU compute | Compute instances using GPU platforms (H100/H200/B200 families) with presets (number of GPUs, CPUs, RAM), boot disks, filesystems attached | GPU VMs (A3/A4) |
| Multi-node fabric | **GPU clusters** (InfiniBand fabric) that instances join so NCCL traffic runs over IB/RDMA | Multi-NIC RDMA VPCs / compact placement |
| Shared storage | Shared filesystems (mounted across instances), object storage (S3-compatible) | Filestore/Lustre, GCS |
| Kubernetes | Managed Kubernetes clusters and node groups (GPU node groups, optionally with GPU clusters/InfiniBand) | GKE |
| Slurm | Managed or Terraform/Helm-deployed Slurm on Kubernetes (Soperator-style) or VM-based Slurm recipes | Cluster Toolkit Slurm |
| Capacity | Reservations/commitments, preemptible options | Reservations, DWS, Spot |
| Observability | Managed Prometheus/Grafana/logging options, DCGM metrics | Cloud Monitoring, GMP |
| IaC | Terraform provider, CLI, SDKs | google provider, gcloud |

A representative Terraform shape (illustrative; resource and attribute names must be checked in the provider docs):

```hcl
terraform {
  required_providers {
    nebius = {
      source  = "terraform-provider.storage.eu-north1.nebius.cloud/nebius/nebius"   # confirm the current registry source
      version = "~> 0.5"
    }
  }
}

provider "nebius" {
  # authentication via the environment/CLI profile or service account credentials;
  # no keys in code (4.22). Parent (project) IDs are passed per resource.
}

resource "nebius_vpc_v1_network" "train" {
  parent_id = var.project_id
  name      = "train-net"
}

resource "nebius_compute_v1_gpu_cluster" "fabric" {            # InfiniBand fabric for multi-node NCCL
  parent_id         = var.project_id
  name              = "h100-fabric-a"
  infiniband_fabric = "fabric-3"                                # fabric name per region/platform
}

resource "nebius_compute_v1_instance" "gpu" {
  for_each  = toset(var.node_names)
  parent_id = var.project_id
  name      = each.key
  gpu_cluster = { id = nebius_compute_v1_gpu_cluster.fabric.id }
  resources = {
    platform = "gpu-h100-sxm"
    preset   = "8gpu-128vcpu-1600gb"
  }
  # boot disk, network interfaces (subnet, public IP: none), cloud-init user data, attached shared filesystem ...
}
```

Design guidance for GPU clouds:

1. **Fabric membership is the key difference**: multi-node jobs need all nodes in the same GPU cluster/fabric; place all nodes of a training pool in one fabric and size fabrics for the largest job; changing membership may require recreation, so plan topology up front.
2. **Immutable images + cloud-init**: build golden images with drivers/NCCL/OFED (4.2, 4.17) and use cloud-init for node identity; Ansible (or the provider's Slurm/Kubernetes automation) for the remainder.
3. **Shared filesystems**: define once, mount across instances; throughput depends on filesystem size/type; treat as stateful with protection and backups (Part 13).
4. **Kubernetes vs Slurm vs bare VMs**: if the provider offers managed Kubernetes with GPU node groups and the GPU Operator integration, Terraform handles cluster + node groups, then a separate layer (Helm/Argo) installs add-ons (4.25, 4.26); for Slurm, either use provider-supplied automation (Helm charts on Kubernetes or Terraform modules) or provision VMs and run Ansible (4.17, Part 6).
5. **Quota and capacity are commercial constructs**: reservations and commitments are negotiated; Terraform should encode what you have (and warn when plans exceed it) rather than assume elasticity (4.23 guardrails).
6. **CoreWeave and other Kubernetes-native GPU clouds** expose clusters where nodes join a managed Kubernetes plane and workloads request GPUs via standard Kubernetes APIs and node labels (instance type, interconnect); Terraform manages the cluster and namespaces, quotas, storage classes and network policies through Kubernetes/Helm providers, with InfiniBand topology exposed through node labels used by schedulers (Part 11).
7. **Abstraction**: expose a common module interface (name, accelerator class, node count, fabric/placement group, storage mounts) and implement provider-specific submodules (`modules/gpu-pool/gcp`, `/nebius`, `/coreweave`) behind it; keep provider differences (fabrics, presets) as explicit variables rather than hiding them.

## 8. Verification after apply

Terraform success does not mean usable GPUs. Verify (and automate with Ansible/CI, 4.17):

- Instances running in the expected zone/fabric; labels/taints applied; reservation consumed.
- `nvidia-smi` shows the expected GPUs and driver; Fabric Manager/IMEX as needed.
- Network: MTU correct end-to-end (`ping -M do -s 8972`), RDMA/IB links up and at speed (`ibstat`, `rdma link`), NCCL tests across nodes meet the bandwidth floor (`all_reduce_perf`).
- Storage mounts present with expected throughput (`fio`), checkpoints bucket reachable with workload identity.
- Kubernetes: nodes Ready, `nvidia.com/gpu` allocatable, GPU Operator/device plugin healthy, a test pod runs `nvidia-smi`; DCGM metrics visible in Prometheus.
- Budgets/alerts attached; labels for cost allocation present.

## 9. Lab (untested)

Run the CPU/L4 rehearsal variants first; only provision large GPU shapes with a budget cap and an immediate destroy plan.

1. **Landing zone**: create a project (or use a sandbox), enable APIs, and write the network stack (VPC, subnet with secondary ranges, router/NAT, firewall, IAP SSH); `plan` and `apply`; verify with `gcloud compute networks describe` and an IAP SSH to a tiny VM.
2. **Identity and storage**: service accounts, workload identity pool binding, KMS key, versioned CMEK bucket with `prevent_destroy`; test access from a VM via the service account without keys.
3. **GPU VM**: provision an L4 (`g2-standard-8`) VM (or A2 if quota allows), install/verify the driver via the image or Ansible (4.17), run `nvidia-smi`; try Spot and observe preemption; destroy.
4. **Capacity objects**: write a `google_compute_reservation` (small, short-lived) and consume it from an instance; add an alert/doc for expiry; delete.
5. **GKE**: create a private regional/zonal cluster, a system pool and an L4 GPU pool (min 0); deploy a GPU test pod with a toleration and node selector; observe scale-up from zero and scale-down; test Workload Identity access to the bucket.
6. **Upgrade behaviour**: change the node pool image or machine type (staging) and read the plan (`-/+`?) and the `upgrade_settings`; trigger a surge upgrade; note GPU capacity needs.
7. **Policy**: run Conftest/Checkov on the plan: deny public IPs on nodes, require labels, cap GPU count, require versioning on buckets (4.23).
8. **Multi-NIC concept**: read Google's current A3/A3 Ultra/A4 networking doc and sketch the Terraform for the additional VPCs, subnets, firewall and instance NIC blocks; implement the network part for a CPU-only dry run if no quota.
9. **Slurm on GCP**: generate or write a minimal Slurm cluster (controller + autoscaled partition) using Cluster Toolkit modules or Terraform + Ansible; submit a trivial job; observe node resume/suspend.
10. **Nebius (optional)**: authenticate the CLI, apply the network + a small instance (and a GPU cluster only with capacity); verify provider resource names against docs; compare steps with GCP; document differences in a table.
11. **Common module interface**: define `modules/gpu-pool` with an interface (`accelerator`, `node_count`, `placement`, `storage`) and two implementations (GCP MIG/GKE pool and a stub for Nebius); test plans for both.
12. **Verification play**: automate the section 8 checks with Ansible/`terraform test`/`check` blocks.
13. **Teardown**: `terraform destroy`, confirm via billing/console that nothing is left; check reservations, disks, static IPs and snapshots.

Mark tested only after execution.

## 10. Common mistakes

- Planning GPU shapes without checking zone availability, quota or reservation; discovering it at apply time.
- Public IPs and wide-open firewall rules on GPU nodes; SSH keys instead of OS Login/IAP.
- Service-account JSON keys in repos/CI; excessive scopes.
- Cluster and node pool in the same stack as Kubernetes add-ons (provider/credential ordering problems, 4.22).
- Auto-upgrades or surge settings that need extra GPUs which do not exist; replacing reserved nodes.
- Forgetting MTU, placement or RDMA NIC configuration, leaving multi-node NCCL at a fraction of expected bandwidth.
- Checkpoint buckets without versioning/CMEK/`prevent_destroy`; buckets in a different region than the compute.
- Assuming spot/preemptible capacity for long runs without checkpointing.
- No budgets or labels, so GPU spend is untraceable.
- Treating one provider's concepts as universal (fabric membership vs placement policies vs node labels).

## 11. Interview angles

- "Design the Terraform for a GKE cluster with GPU node pools and workload identity. What goes in separate stacks?" 
- "How do you secure GPU nodes on GCP?" (private nodes, NAT, IAP/OS Login, shielded VM, SA least privilege, org policies.)
- "A GPU node pool update needs surge capacity that doesn't exist. What now?" (max_unavailable, drains, reservations, DWS.)
- "How would you give 64 H100 nodes high-bandwidth networking on GCP? On a GPU cloud like Nebius?" 
- "How do you manage GPU capacity as code? Reservations, quotas, budgets?" 
- "What's different about InfiniBand-fabric clouds vs hyperscalers?" 
- "How do you keep a multi-cloud module interface clean?" 
- "How do you validate that Terraform-created GPU infrastructure is actually healthy?" 

## 12. Checkpoint questions (30)

1. Scope of a GCP VPC? **A:** Global network with regional subnets.
2. Why Cloud NAT? **A:** Egress without public IPs.
3. What is Private Google Access? **A:** Reach Google APIs from private IPs.
4. Why IAP for SSH? **A:** No public IP/exposed port 22.
5. Do GPU VMs live-migrate? **A:** No; `TERMINATE` on host maintenance.
6. Why `on_host_maintenance = TERMINATE`? **A:** Required for GPU instances.
7. Capacity options on GCP? **A:** Quota, reservations, Spot, DWS flex/calendar, CUDs.
8. What does compact placement give? **A:** Low-latency collocation.
9. Multi-NIC for GPUs why? **A:** Dedicated high-bandwidth GPU networks.
10. GKE private cluster means? **A:** Nodes with private IPs only.
11. Why separate cluster and add-on stacks? **A:** Provider credential/unknown-value ordering.
12. Taint on GPU pool purpose? **A:** Keep non-GPU pods off.
13. `auto_upgrade=false` reason? **A:** Control disruption/capacity for training pools.
14. What is Workload Identity? **A:** KSA to Google SA binding without keys.
15. Bucket protection settings? **A:** Versioning, CMEK, prevent_destroy, force_destroy=false.
16. Why same-region buckets? **A:** Throughput and egress cost.
17. What is DWS? **A:** Dynamic Workload Scheduler for acquiring GPU capacity.
18. What is Cluster Toolkit? **A:** GCP blueprints/modules for HPC/Slurm clusters.
19. Nebius tenancy hierarchy? **A:** Tenant → projects.
20. What is a Nebius GPU cluster? **A:** InfiniBand fabric group for multi-node GPU instances.
21. Why fabric membership matters? **A:** NCCL over IB requires same fabric.
22. GCP analogue of fabric? **A:** RDMA/multi-NIC VPCs + placement.
23. Kubernetes-native GPU cloud example? **A:** CoreWeave.
24. How abstract providers? **A:** Common module interface, provider submodules.
25. Why verify after apply? **A:** Terraform success ≠ working GPUs/network.
26. MTU check command? **A:** `ping -M do -s <size>`.
27. Quick fabric health tool? **A:** `ibstat`, `rdma link`, NCCL tests.
28. Why Spot needs checkpoints? **A:** Preemption.
29. Budget alert resource? **A:** `google_billing_budget`.
30. First thing for cost visibility? **A:** Labels/tags and budgets.

## 13. Sources and review notes

**Written in original words.** Principal sources:

- Yevgeniy Brikman, *Terraform: Up and Running* (applied patterns from the chapters on modules, loops, secrets, multiple providers and team workflows).
- The author's `nvidia-devops` repository, volume 10 chapter 5 (end-to-end AI factory implementation on AWS with VPC, placement group, security groups, checkpoint buckets) adapted to GCP and a GPU-cloud model, and chapter 4 where cross-referenced.
- Provider documentation: Terraform Google provider, GKE and Compute Engine GPU documentation, Cluster Toolkit; Nebius documentation and Terraform provider; CoreWeave documentation for the Kubernetes-native model.
- Examples are the author's constructions.

**Flagged for verification before publishing:** all GCP machine families, accelerator types, driver-installation arguments and multi-NIC networking details (change per generation), GKE resource arguments for the provider version in use, reservation consumption syntax, budget resource schema, Nebius provider source address, resource names and attributes (the Nebius block is illustrative), Cluster Toolkit module names, and every code listing; all labs are **untested** and GPU resources are expensive: set budgets before applying.
