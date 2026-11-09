# Plan-only tests with a mocked provider: no credentials, nothing is created.
mock_provider "nebius" {}

variables {
  name        = "demo"
  parent_id   = "project-e00demo"
  subnet_id   = "vpcsubnet-e00demo"
  k8s_version = "1.31"
  node_pools = {
    gpu = {
      platform         = "gpu-h100-sxm"
      preset           = "8gpu-128vcpu-1600gb"
      fixed_node_count = 4
    }
  }
}

run "valid_fixed_pool" {
  command = plan

  assert {
    condition     = output.pool_summary["gpu"].mode == "fixed"
    error_message = "A pool with fixed_node_count must report mode fixed."
  }
}

run "rejects_fixed_and_autoscaling_together" {
  command = plan

  variables {
    node_pools = {
      gpu = {
        platform         = "gpu-h100-sxm"
        preset           = "8gpu-128vcpu-1600gb"
        fixed_node_count = 4
        min_node_count   = 1
        max_node_count   = 4
      }
    }
  }

  expect_failures = [var.node_pools]
}

run "rejects_stuck_upgrade_strategy" {
  command = plan

  variables {
    node_pools = {
      gpu = {
        platform              = "gpu-h100-sxm"
        preset                = "8gpu-128vcpu-1600gb"
        fixed_node_count      = 4
        max_unavailable_count = 0
        max_surge_count       = 0
      }
    }
  }

  expect_failures = [var.node_pools]
}

run "rejects_floating_version" {
  command = plan

  variables {
    k8s_version = "latest"
  }

  expect_failures = [var.k8s_version]
}
