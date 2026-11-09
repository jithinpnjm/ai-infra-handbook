# A root module for one environment. One folder, one state, one blast radius.
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    nebius = {
      source  = "nebius/nebius"
      version = ">= 0.6.23"
    }
  }

  # Partial configuration: bucket, key and credentials come from -backend-config
  # at init time, so this file is identical for every environment.
  backend "s3" {}
}

provider "nebius" {}

module "gpu_cluster" {
  # In real use, pin a released tag of the modules repository, for example
  # github.com/<org>/<modules-repo>//gpu-cluster?ref=v2.1.0
  source = "../.."

  name        = "inference-eu"
  parent_id   = "project-e00example"
  subnet_id   = "vpcsubnet-e00example"
  k8s_version = "1.31"

  node_pools = {
    cpu = {
      platform         = "cpu-d3"
      preset           = "4vcpu-16gb"
      fixed_node_count = 3
    }
    gpu = {
      platform              = "gpu-h100-sxm"
      preset                = "8gpu-128vcpu-1600gb"
      fixed_node_count      = 6
      max_unavailable_count = 1
      max_surge_count       = 0
      taints                = [{ key = "nvidia.com/gpu", value = "present", effect = "NO_SCHEDULE" }]
    }
  }
}

output "cluster_id" {
  value = module.gpu_cluster.cluster_id
}
