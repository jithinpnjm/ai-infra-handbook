# History of renames. Keep every block: removing one makes old callers plan a destroy.
# Version 1.x of this module had a single group called "gpu". Version 2.x keyed pools.
moved {
  from = nebius_mk8s_v1_node_group.gpu
  to   = nebius_mk8s_v1_node_group.pool["gpu"]
}
