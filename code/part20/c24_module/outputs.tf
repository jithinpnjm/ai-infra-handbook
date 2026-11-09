output "cluster_id" {
  description = "ID of the managed Kubernetes cluster."
  value       = nebius_mk8s_v1_cluster.this.id
}

output "node_group_ids" {
  description = "Node group IDs keyed by the pool key."
  value       = { for k, g in nebius_mk8s_v1_node_group.pool : k => g.id }
}

output "pool_summary" {
  description = "Plain facts per pool, for review and for other modules."
  value = {
    for k, p in var.node_pools : k => {
      platform = p.platform
      preset   = p.preset
      mode     = p.fixed_node_count != null ? "fixed" : "autoscaling"
      size     = p.fixed_node_count != null ? p.fixed_node_count : p.max_node_count
    }
  }
}
