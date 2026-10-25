#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.14: Cloud GPU platforms: DGX Cloud, CoreWeave, Nebius and GCP A3 and A4."""

from __future__ import annotations

import sys

from cloud_gpu_platforms import (
    GCP_GPU_CATALOG,
    OCI_TOPOGRAPH_REQUIRED_INSPECT_RESOURCES,
    audit_cloud_gpu_cluster_spec,
    validate_bcm_topograph_cloud_config,
)


def run_checks() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label} -- {detail}")

    print("=== Chapter 9.14 Lab: Cloud GPU Platforms (DGX Cloud, CoreWeave, Nebius, GCP A3/A4) ===")

    # 1. BCM Topograph Cloud Topology Service checks (bcm11-admin Section 7.5 pp. 413-419)
    aws_dgx_cloud_ok = {
        "topology_plugin": "tree",
        "package_installed": "topograph4",
        "version4_setting": True,
        "systemd_daemon_reloaded": True,
        "separate_topograph_and_slurm_nodes": False,
        "nodes_running": True,
        "cloud_provider": "AWS",
        "pass_cloud_credentials": True,
        "has_ec2_describe_instance_topology": True,
    }
    res_aws = validate_bcm_topograph_cloud_config(aws_dgx_cloud_ok)
    check(
        "BCM 11 pp.414-418: Valid AWS (DGX Cloud p5.48xlarge) Topograph 4 config passes on port 49021",
        res_aws["valid_topograph"] is True and res_aws["default_http_port"] == 49021,
        f"got {res_aws}",
    )

    aws_imds_ok = dict(
        aws_dgx_cloud_ok,
        pass_cloud_credentials=False,
        has_imds_instance_profile_role=True,
    )
    check(
        "BCM 11 p.418: AWS Topograph with Pass cloud credentials=no passes when EC2 IMDS profile role is attached",
        validate_bcm_topograph_cloud_config(aws_imds_ok)["valid_topograph"] is True,
    )

    aws_no_perm = dict(aws_dgx_cloud_ok, has_ec2_describe_instance_topology=False)
    check(
        "BCM 11 p.417: Flags missing ec2:DescribeInstanceTopology (AmazonEC2ReadOnlyAccess) on AWS",
        any("missing_aws_permission" in e for e in validate_bcm_topograph_cloud_config(aws_no_perm)["errors"]),
    )

    v4_mismatch_1 = dict(aws_dgx_cloud_ok, package_installed="topograph4", version4_setting=False)
    v4_mismatch_2 = dict(aws_dgx_cloud_ok, package_installed="topograph", version4_setting=True)
    check(
        "BCM 11 p.417: Flags Topograph 4 mismatch if package and version4=true setting do not match",
        any("topograph4_mismatch" in e for e in validate_bcm_topograph_cloud_config(v4_mismatch_1)["errors"])
        and any("topograph4_mismatch" in e for e in validate_bcm_topograph_cloud_config(v4_mismatch_2)["errors"]),
    )

    no_reload = dict(aws_dgx_cloud_ok, systemd_daemon_reloaded=False)
    check(
        "BCM 11 p.417: Flags missing systemctl daemon-reload after installing topograph4",
        any("missing_systemd_daemon_reload" in e for e in validate_bcm_topograph_cloud_config(no_reload)["errors"]),
    )

    sep_node_bad = dict(
        aws_dgx_cloud_ok,
        separate_topograph_and_slurm_nodes=True,
        shared_certs_and_update_topology_token=False,
    )
    check(
        "BCM 11 p.414: Flags separate Topograph node missing /cm/shared certs and UPDATE_TOPOLOGY_TOKEN",
        any("missing_shared_certs_or_token" in e for e in validate_bcm_topograph_cloud_config(sep_node_bad)["errors"]),
    )

    stopped_nodes = dict(aws_dgx_cloud_ok, nodes_running=False)
    check(
        "BCM 11 p.413: Flags stopped/non-existent cloud nodes during Topograph generation",
        any("cloud_nodes_not_running" in e for e in validate_bcm_topograph_cloud_config(stopped_nodes)["errors"]),
    )

    oci_ok = dict(
        aws_dgx_cloud_ok,
        cloud_provider="OCI",
        pass_cloud_credentials=False,
        oci_dynamic_group_resources=OCI_TOPOGRAPH_REQUIRED_INSPECT_RESOURCES,
    )
    check(
        "BCM 11 p.418: OCI Topograph passes when dynamic group grants all 5 inspect resource policies",
        validate_bcm_topograph_cloud_config(oci_ok)["valid_topograph"] is True
        and len(OCI_TOPOGRAPH_REQUIRED_INSPECT_RESOURCES) == 5,
    )

    oci_missing = dict(
        oci_ok,
        oci_dynamic_group_resources=("compute-bare-metal-hosts",),
    )
    check(
        "BCM 11 p.418: Flags missing OCI dynamic group inspect permissions (hpc-islands, network-blocks, etc.)",
        any("missing_oci_dynamic_group_permissions" in e for e in validate_bcm_topograph_cloud_config(oci_missing)["errors"]),
    )

    gcp_topo_ok = dict(aws_dgx_cloud_ok, cloud_provider="GCP", gcp_placement_policy="COMPACT")
    gcp_topo_bad = dict(aws_dgx_cloud_ok, cloud_provider="GCP", gcp_placement_policy="SPREAD")
    check(
        "BCM 11 p.418: GCP Topograph requires COMPACT placement policy and rejects SPREAD",
        validate_bcm_topograph_cloud_config(gcp_topo_ok)["valid_topograph"] is True
        and any("missing_gcp_compact_placement" in e for e in validate_bcm_topograph_cloud_config(gcp_topo_bad)["errors"]),
    )

    bad_plugin = dict(aws_dgx_cloud_ok, topology_plugin="3d_torus")
    check(
        "BCM 11 p.418: Topograph supports only tree and block plugins (rejects 3d_torus)",
        any("unsupported_topograph_plugin" in e for e in validate_bcm_topograph_cloud_config(bad_plugin)["errors"]),
    )

    # 2. GCP GPU Machine Family Catalog checks (G2, A2, A3, A3-Ultra, A4, A4X)
    check(
        "GCP A3 uses 8x H100 with GPUDirect-TCPX, while A3-Ultra (8x H200) and A4 (8x B200) use GPUDirect-RDMA (RoCEv2)",
        GCP_GPU_CATALOG["A3"].inter_node_gpu_transport == "GPUDirect-TCPX"
        and "GPUDirect-RDMA" in GCP_GPU_CATALOG["A3-Ultra"].inter_node_gpu_transport
        and "GPUDirect-RDMA" in GCP_GPU_CATALOG["A4"].inter_node_gpu_transport,
    )
    check(
        "GCP A4X provides 72 Blackwell GPUs + 36 Grace CPUs (GB200 NVL72) with 1.8 TB/s NVLink 5",
        GCP_GPU_CATALOG["A4X"].gpus_per_vm == 72 and "NVLink 5" in GCP_GPU_CATALOG["A4X"].inter_node_gpu_transport,
    )
    check(
        "GCP G2 (L4) does not require multi-NIC GPU VPCs, whereas A3/A3-Ultra/A4/A4X require multi-NIC + MTU 8896",
        GCP_GPU_CATALOG["G2"].requires_multi_nic_vpcs is False
        and all(GCP_GPU_CATALOG[k].requires_multi_nic_vpcs and GCP_GPU_CATALOG[k].recommended_mtu == 8896 for k in ("A3", "A3-Ultra", "A4", "A4X")),
    )

    # 3. Cloud GPU Cluster Specification Auditor checks (GCP, Nebius, CoreWeave)
    gcp_good = {
        "platform": "GCP",
        "machine_family": "A4",
        "on_host_maintenance": "TERMINATE",
        "multi_node_training": True,
        "placement_collocation": "COLLOCATED",
        "multi_nic_gpu_vpcs_configured": True,
        "vpc_mtu": 8896,
        "is_gke_node_pool": True,
        "max_surge": 0,
        "quota_or_reservation_tight": True,
        "both_gke_driver_installer_and_gpu_operator_driver_enabled": False,
    }
    check(
        "Properly configured GCP A4 GKE node pool (TERMINATE, COLLOCATED, multi-NIC MTU 8896, max_surge=0) passes",
        audit_cloud_gpu_cluster_spec(gcp_good)["passes_cloud_audit"] is True,
    )

    gcp_migrate = dict(gcp_good, on_host_maintenance="MIGRATE")
    check(
        "Ch 4.24: Flags on_host_maintenance=MIGRATE on GPU VMs (must be TERMINATE)",
        any("invalid_host_maintenance" in i for i in audit_cloud_gpu_cluster_spec(gcp_migrate)["issues"]),
    )

    gcp_no_colloc = dict(gcp_good, placement_collocation="UNSPECIFIED")
    check(
        "Ch 4.24: Flags missing COLLOCATED compact placement policy on multi-node GCP training",
        any("missing_compact_placement" in i for i in audit_cloud_gpu_cluster_spec(gcp_no_colloc)["issues"]),
    )

    gcp_no_multinic = dict(gcp_good, multi_nic_gpu_vpcs_configured=False, vpc_mtu=1460)
    check(
        "Ch 4.24: Flags missing multi-NIC GPU VPCs and standard 1460 MTU on A3/A4 multi-node training",
        len(audit_cloud_gpu_cluster_spec(gcp_no_multinic)["issues"]) == 2,
    )

    gcp_surge = dict(gcp_good, max_surge=1, quota_or_reservation_tight=True)
    check(
        "Ch 4.24: Flags GKE max_surge > 0 on tight GPU reservation pools",
        any("gke_surge_upgrade_starvation_risk" in i for i in audit_cloud_gpu_cluster_spec(gcp_surge)["issues"]),
    )

    gcp_dup_drv = dict(gcp_good, both_gke_driver_installer_and_gpu_operator_driver_enabled=True)
    check(
        "Ch 4.24: Flags enabling both GKE driver installer and GPU Operator driver container simultaneously",
        any("duplicate_driver_managers" in i for i in audit_cloud_gpu_cluster_spec(gcp_dup_drv)["issues"]),
    )

    nebius_good = {
        "platform": "Nebius",
        "multi_node_training": True,
        "all_nodes_in_same_gpu_cluster_fabric": True,
    }
    nebius_bad = dict(nebius_good, all_nodes_in_same_gpu_cluster_fabric=False)
    check(
        "Ch 4.24 §7: Nebius multi-node training passes when all instances join the same gpu_cluster IB fabric and fails otherwise",
        audit_cloud_gpu_cluster_spec(nebius_good)["passes_cloud_audit"] is True
        and any("nebius_fabric_mismatch" in i for i in audit_cloud_gpu_cluster_spec(nebius_bad)["issues"]),
    )

    cw_good = {"platform": "CoreWeave", "uses_virtualized_nics_without_sriov_iommu": False}
    cw_bad = {"platform": "CoreWeave", "uses_virtualized_nics_without_sriov_iommu": True}
    check(
        "V09 Q2: CoreWeave/cloud RDMA passes with bare-metal or SR-IOV + IOMMU and flags emulated vSwitch NICs",
        audit_cloud_gpu_cluster_spec(cw_good)["passes_cloud_audit"] is True
        and any("emulated_vswitch_overhead" in i for i in audit_cloud_gpu_cluster_spec(cw_bad)["issues"]),
    )

    try:
        validate_bcm_topograph_cloud_config(dict(aws_dgx_cloud_ok, cloud_provider="UnknownCloud"))
        check("Rejects unsupported cloud provider in Topograph validator", False)
    except ValueError:
        check("Rejects unsupported cloud provider in Topograph validator", True)

    try:
        audit_cloud_gpu_cluster_spec({"platform": "GCP", "machine_family": "Z99"})
        check("Rejects unknown GCP machine family", False)
    except KeyError:
        check("Rejects unknown GCP machine family", True)

    try:
        audit_cloud_gpu_cluster_spec({"platform": "UnknownPlatform"})
        check("Rejects unsupported cloud platform in cluster auditor", False)
    except ValueError:
        check("Rejects unsupported cloud platform in cluster auditor", True)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
