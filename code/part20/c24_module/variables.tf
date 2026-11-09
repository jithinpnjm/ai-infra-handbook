variable "name" {
  description = "Cluster name. Also the prefix for every node group."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,30}$", var.name))
    error_message = "name must be 2-31 characters: lowercase letters, digits and dashes, starting with a letter."
  }
}

variable "parent_id" {
  description = "Nebius project ID that owns the cluster."
  type        = string
}

variable "subnet_id" {
  description = "Subnet for the control plane. It is also the default subnet for node groups."
  type        = string
}

variable "k8s_version" {
  description = "Kubernetes minor version in major.minor form, for example 1.31. Pin it. Never let it float."
  type        = string

  validation {
    condition     = can(regex("^[0-9]+\\.[0-9]+$", var.k8s_version))
    error_message = "k8s_version must look like 1.31 (major.minor)."
  }
}

variable "etcd_cluster_size" {
  description = "Number of etcd instances. Three is the highly available setting."
  type        = number
  default     = 3

  validation {
    condition     = var.etcd_cluster_size == 3
    error_message = "Resilient clusters use etcd_cluster_size = 3. Change this rule on purpose, in review."
  }
}

variable "public_endpoint_cidrs" {
  description = "CIDRs allowed to reach the public API endpoint. Empty list means no public endpoint."
  type        = list(string)
  default     = []
}

variable "node_pools" {
  description = <<-EOT
    Node pools keyed by a short stable name. The key becomes part of the Terraform
    address, so renaming a key replaces the pool unless you add a moved block.
    Give each pool either a fixed size or an autoscaling range, never both.
    GPU pools should usually have a fixed size: see the chapter for why.
  EOT
  type = map(object({
    platform              = string
    preset                = string
    fixed_node_count      = optional(number)
    min_node_count        = optional(number)
    max_node_count        = optional(number)
    max_unavailable_count = optional(number, 1)
    max_surge_count       = optional(number, 0)
    drain_timeout         = optional(string, "10m")
    labels                = optional(map(string), {})
    taints = optional(list(object({
      key    = string
      value  = string
      effect = string
    })), [])
  }))

  validation {
    condition = alltrue([
      for p in values(var.node_pools) :
      (p.fixed_node_count != null) != (p.min_node_count != null || p.max_node_count != null)
    ])
    error_message = "Each pool needs either fixed_node_count or min_node_count with max_node_count, not both."
  }

  validation {
    condition = alltrue([
      for p in values(var.node_pools) :
      p.min_node_count == null ? true : (p.max_node_count != null ? p.min_node_count <= p.max_node_count : false)
    ])
    error_message = "Autoscaling pools need min_node_count <= max_node_count."
  }

  validation {
    condition = alltrue([
      for p in values(var.node_pools) :
      p.max_unavailable_count + p.max_surge_count > 0
    ])
    error_message = "max_unavailable_count and max_surge_count cannot both be 0, or an upgrade can never move."
  }
}
