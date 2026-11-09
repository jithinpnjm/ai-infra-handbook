locals {
  public_endpoint = length(var.public_endpoint_cidrs) > 0 ? {
    public_endpoint = { allowed_cidrs = var.public_endpoint_cidrs }
  } : null
}

resource "nebius_mk8s_v1_cluster" "this" {
  name      = var.name
  parent_id = var.parent_id

  control_plane = {
    subnet_id         = var.subnet_id
    version           = var.k8s_version
    etcd_cluster_size = var.etcd_cluster_size
    endpoints         = local.public_endpoint
  }

  # The cluster holds the control plane and every node group under it.
  # prevent_destroy turns an accidental replacement into a plan-time error.
  # Removing this resource block from the code still destroys it, so review that too.
  lifecycle {
    prevent_destroy = true
  }
}

resource "nebius_mk8s_v1_node_group" "pool" {
  for_each = var.node_pools

  parent_id = nebius_mk8s_v1_cluster.this.id
  name      = "${var.name}-${each.key}"
  version   = var.k8s_version

  fixed_node_count = each.value.fixed_node_count

  autoscaling = each.value.min_node_count == null ? null : {
    min_node_count = each.value.min_node_count
    max_node_count = each.value.max_node_count
  }

  template = {
    resources = {
      platform = each.value.platform
      preset   = each.value.preset
    }
    metadata = {
      labels = each.value.labels
    }
    taints = each.value.taints
  }

  strategy = {
    drain_timeout   = each.value.drain_timeout
    max_unavailable = { count = each.value.max_unavailable_count }
    max_surge       = { count = each.value.max_surge_count }
  }

  lifecycle {
    # The pool is rebuilt node by node by the strategy above. Terraform must
    # never destroy the group object as a side effect of a typo.
    prevent_destroy = true
  }
}
