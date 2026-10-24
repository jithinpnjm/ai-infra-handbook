#!/usr/bin/env python3
"""Mission Control, Run:ai, DGX Cloud and autonomous-recovery rules from the BCM 11 Containerization Manual (6.11 and B.2.8),
the BCM 11 Administrator Manual (1.3, 2.4, 3.7.11, 4.3, 6.4.5, 6.5, 7, 14.5, 15.1), and the DGX GB300 SuperPOD Reference Architecture
(pages 11-14, 32-34), plus the checkpoint-resume calculation from nvidia-zero-to-hero volume 21 chapter 7.

Not BCM, not Mission Control, and not Run:ai. Each function names the source section it follows. Where I derive something it is labelled.
"""
import re


class MissionControlError(ValueError):
    pass


# ---- 1. GB300 Reference Architecture (pp. 32-33): five-layer Mission Control stack (unordered in the prose) -----------------
# The prose names a "five-layer architecture that builds from foundational system health and diagnostics to advanced NVIDIA DGX
# SuperPOD cluster management operations" and describes these five roles, without numbering them 1..5 in the text (Figure 17 was
# not read). Four layers are named or described directly; the fifth is inferred from the prose separatingBCM cluster management
# from Slurm/Kubernetes+Run:ai workload orchestration.
MC_PROSE_COMPONENTS = {
    "system_health_and_diagnostics": {
        "stated_in_text": "foundational system health and diagnostics",
        "explicit_layer_name": False,  # phrased as the starting point of the five-layer architecture
    },
    "telemetry_and_observability": {
        "stated_in_text": "The Telemetry and Observability layer leverages proprietary diagnostic tools and health-checks for system insights",
        "explicit_layer_name": True,
    },
    "validation_and_diagnostics": {
        "stated_in_text": "the Validation and Diagnostics layer supports the built-in autonomous recovery engine that ensures rapid failure recovery and system restoration with minimal time to recovery",
        "explicit_layer_name": True,
    },
    "cluster_management_operations": {
        "stated_in_text": "advanced NVIDIA DGX SuperPOD cluster management operations; seamlessly cooperating NVIDIA Base Command Manager (BCM) technology for coordinating cluster provisioning & operations",
        "explicit_layer_name": False,  # described as the advanced operations endpoint and BCM cooperation
    },
    "workload_orchestration": {
        "stated_in_text": "leverages NVIDIA Base Command Manager (BCM) technology and NVIDIA Run:ai functionality to provide scheduler access with SLURM and Kubernetes for AI and HPC workload orchestration",
        "explicit_layer_name": False,  # described indirectly through scheduler access with Slurm and Kubernetes/Run:ai
    },
}

MC_VALUE_CLAIMS = {
    "automated_failure_detection_and_self_recovery": "automated failure detection and recovery mechanisms minimize downtime compared to manual interventions",
    "optimized_workload_migration_and_resource_allocation": "workloads are continuously reassigned to healthy nodes, preventing idle GPU time",
    "unified_diagnostics": "combines infrastructure and application-level diagnostics to reduce troubleshooting time",
    "in_memory_checkpointing": "restarts failed processes/ranks from the most recent valid checkpoint",
}


def mc_stack_summary():
    """Returns the five roles from pp. 32-33 and which ones carry an explicit '... layer' phrase in the prose."""
    explicit = sorted(k for k, v in MC_PROSE_COMPONENTS.items() if v["explicit_layer_name"])
    indirect = sorted(k for k, v in MC_PROSE_COMPONENTS.items() if not v["explicit_layer_name"])
    return {"total": len(MC_PROSE_COMPONENTS), "explicit": explicit, "indirect": indirect}


# ---- 2. BCM Administrator Manual 6.5, 15.1, 6.4.5, 14.5, 3.7.11: profiles, HA database, Keycloak, license, leak ------------
PRECONFIGURED_PROFILES = {
    "admin": ("all tasks", False),
    "autonomous-hardware-recovery": ("autonomous hardware recovery tasks", True),
    "autonomous-job-recovery": ("autonomous job recovery tasks", True),
    "bootstrap": ("bootstrap tasks", True),
    "cmhealth": ("health-related prejob tasks", True),
    "cmpam": ("BCM PAM tasks", True),
    "litenode": ("CMDaemon Lite (section 2.6.7) tasks", True),
    "monitoringpush": ("pushing raw monitoring data to CMDaemon via a JSON POST", True),
    "mqtt": ("MQTT tasks", True),
    "node": ("node-related tasks, for example by the nodeinstaller", True),
    "portal": ("user portal viewing", False),
    "power": ("device power", True),
    "prs": ("PRS tasks", True),
    "readonly": ("view-only", False),
}


def profile_tasks_and_nonuser(name):
    """Administrator Manual 6.5 table (p. 340): returns (default_tasks_allowed, is_nonuser)."""
    if name not in PRECONFIGURED_PROFILES:
        raise MissionControlError(f"unknown preconfigured profile: {name}")
    return PRECONFIGURED_PROFILES[name]


def validate_profile_operation(profile_name, action, target_user=None):
    """Administrator Manual 6.5 (p. 340-341): most preconfigured profiles are nonuser profiles, used by cluster manager clients,
    and should never be modified by the cluster administrator. Only admin, readonly, and portal are available to human users."""
    if profile_name not in PRECONFIGURED_PROFILES:
        raise MissionControlError(f"unknown profile {profile_name}")
    _, nonuser = PRECONFIGURED_PROFILES[profile_name]
    if action in ("modify_tokens", "delete", "disable") and nonuser:
        raise MissionControlError(f"{profile_name} is a nonuser profile used by cluster manager clients and must never be modified")
    if action == "assign_to_user" and nonuser:
        raise MissionControlError(f"{profile_name} is a nonuser profile; only admin, readonly, and portal are available to human users")
    return "allowed"


SYSTEM_MYSQL_DBS = {"mysql", "information_schema", "performance_schema", "sys"}
DEFAULT_HA_MYSQL_DBS = {"cmdaemon", "slurm_acct_db"}


def mysql_dbs_after_failover(dbs_on_primary, extradbclone=(), bcm_version=(11, 34, 0), replicate_all_non_system=False):
    """Administrator Manual 15.1 (p. 802): by default head node MySQL HA clones and replicates only cmdaemon and slurm_acct_db.
    Third-party application databases not listed in extradbclone.xml, such as the AJR database, are not cloned and are missing
    after a failover. From 11.34.0 onwards, cmha-setup can optionally replicate all non-system MySQL databases (--replicate-all-databases);
    system databases (mysql, information_schema, performance_schema, sys) are never replicated."""
    if replicate_all_non_system and bcm_version < (11, 34, 0):
        raise MissionControlError("Replicate all non-system MySQL databases requires BCM 11.34.0 or later")
    present = set(dbs_on_primary) - SYSTEM_MYSQL_DBS
    if replicate_all_non_system:
        replicated = present
    else:
        replicated = present & (DEFAULT_HA_MYSQL_DBS | set(extradbclone))
    missing = sorted(present - replicated)
    return {"replicated": sorted(replicated), "missing": missing}


def keycloak_mc_federation_check(head_os, bcm_version, mc_on_head_node, firewall_open_ports, supplied_fields):
    """Administrator Manual 6.4.1 & 6.4.5 (pp. 338-339): Keycloak scripts require BCM 11.34+, Ubuntu 24.04 or 26.04 on the head
    node (not supported on RHEL or Rocky), ports 9443 (HTTPS) and 9999 (HTTP) free. To connect Mission Control to Keycloak,
    provide the Keycloak URL (https://<head-fqdn>:9443), realm name, administrator credentials, and Keycloak TLS certificate;
    if Mission Control is not running on the head node, port 9443/tcp must be open in the head node firewall."""
    problems = []
    if bcm_version < (11, 34, 0):
        problems.append("Keycloak setup scripts require BCM 11.34 or later")
    if head_os.lower() not in ("ubuntu24.04", "ubuntu26.04"):
        problems.append("cm-setup-keycloak.py uses apt and requires Ubuntu 24.04 or 26.04 (not supported on RHEL or Rocky)")
    required = {"keycloak_url", "realm_name", "admin_credentials", "tls_certificate"}
    missing = sorted(required - set(supplied_fields))
    if missing:
        problems.append(f"missing Mission Control federation fields: {missing}")
    url = supplied_fields.get("keycloak_url", "")
    if url and not (url.startswith("https://") and url.endswith(":9443")):
        problems.append("Keycloak URL for Mission Control must be https://<head-fqdn>:9443")
    if not mc_on_head_node and 9443 not in set(firewall_open_ports):
        problems.append("Mission Control is not on the head node: port 9443/tcp must be open in the head node firewall")
    return problems


def base_view_firmware_flash_check(platform, has_mc_license, bcm_version, action="flash", num_packages=1, narrow_targets=False):
    """Administrator Manual 14.5 (p. 757): Base View firmware flashing for GB200, GB300, and DGX fails without an active
    NVIDIA Mission Control license. Only one firmware package can be selected at a time. For 11.34.0, Dry Run does not work
    correctly on these platforms (fixed in 11.35.0; use Flash directly). Narrowing to named component targets (--targets) is
    only available via cmsh, not Base View."""
    problems = []
    if platform.lower() in ("gb200", "gb300", "dgx"):
        if not has_mc_license:
            problems.append("flashing fails without an active NVIDIA Mission Control license")
        if num_packages != 1:
            problems.append("only one firmware package can be selected at a time on GB200, GB300, and DGX")
        if action == "dry_run" and bcm_version == (11, 34, 0):
            problems.append("in BCM 11.34.0 Dry Run does not work correctly on GB200/GB300/DGX (fixed in 11.35.0); use Flash directly")
        if narrow_targets:
            problems.append("Base View cannot narrow a flash to named component targets (--targets); use cmsh firmware")
    return problems


def leak_status_suffix(leak_detection_enabled):
    """Administrator Manual 3.7.11 (p. 122): a device with leak detection enabled (the default) shows no leak: suffix on its
    status line; a device with leak detection disabled shows 'leak:disabled' appended to its status line."""
    return "" if leak_detection_enabled else "leak:disabled"


# ---- 3. Containerization Manual 6.11 and B.2.8: Run:ai Operator and cm-runai-setup -----------------------------------------
RUNAI_REQUIRED_OPERATORS = {
    "NVIDIA GPU Operator", "Grafana Operator", "Kgateway", "Knative Operator",
    "Kubeflow Training Operator", "Kubernetes Metrics Server", "Kubernetes MPI Operator",
    "Kubernetes State Metrics", "LeaderWorkerSet Operator", "MetalLB",
    "Prometheus Adapter", "Prometheus Operator Stack",
}
RUNAI_OPTIONAL_OPERATORS = {"Network Operator", "NIM Operator"}


def runai_install_workflow(bcm_version):
    """Containerization Manual 6.11 (p. 144): prior to BCM 11.33, Run:ai is installed inside cm-kubernetes-setup. From BCM 11.33
    onwards, Run:ai is deployed in two sequential steps: cm-kubernetes-setup first (with operator dependencies), then cm-runai-setup."""
    if bcm_version < (11, 33, 0):
        return {"steps": ["cm-kubernetes-setup (select Run:ai SaaS or self-hosted at the operator screen)"], "decoupled": False}
    return {"steps": ["cm-kubernetes-setup (select Run:ai dependency operators)", "cm-runai-setup"], "decoupled": True}


def can_run_cm_runai_setup(cm_setup_installed, plugin_deb_installed_on_active, internet_access, distro, skip_packages=False):
    """Containerization Manual B.2.8 (pp. 200-202): the cm-runai-setup command is part of cm-setup and is present on a head node
    by default, so checking whether the command exists does NOT tell you whether Run:ai can be deployed. The plugin that implements
    it is in cm-setup-runai-bcm11. On internet-connected clusters it is installed automatically when cm-runai-setup or
    cm-mission-control-setup runs (unless --skip-packages is passed). On air-gapped clusters --skip-packages is required and
    disables package installation, so cm-setup-runai-bcm11 (.deb only, Ubuntu only) must be pre-installed."""
    if not cm_setup_installed:
        return False, "cm-setup is not installed"
    if plugin_deb_installed_on_active:
        return True, "cm-setup-runai-bcm11 plugin is installed"
    if internet_access and not skip_packages:
        return True, "plugin will be installed automatically over the internet"
    if not distro.lower().startswith("ubuntu"):
        return False, "cm-setup-runai-bcm11 is published only as a .deb; air-gapped Run:ai on RHEL is not supported in this release"
    return False, "main component not installed: cm-runai-setup exists in cm-setup, but cm-setup-runai-bcm11 is missing and --skip-packages prevents auto-install"


def runai_wizard_validation(
    mode,
    jfrog_or_reg_creds="",
    cp_fqdn="",
    k8s_fqdn="",
    cert_path="",
    key_path="",
    local_ca_path="",
    custom_ca_enabled_in_helm=False,
    dns_resolves_to=None,
    cert_verify_ok=True,
    cert_san_patterns=(),
    ip_routable_to_cluster=True,
    using_metallb=False,
    bcm_version=(11, 33, 0),
    saas_creds=None,
):
    """Containerization Manual 6.11.1 & 6.11.2 (pp. 144-148): validation checks during Run:ai setup.
    Returns {'errors': [...], 'warnings': [...]}."""
    errors, warnings = [], []
    if mode == "saas":
        saas_creds = saas_creds or {}
        for k in ("tenant_name", "app_secret", "admin_user", "admin_password", "hostname", "cert_path", "key_path"):
            if not saas_creds.get(k):
                errors.append(f"SaaS prerequisite missing: {k}")
        return {"errors": errors, "warnings": warnings}

    if mode != "self-hosted":
        raise MissionControlError(f"unknown Run:ai mode: {mode}")

    # Required field validation (6.11.1)
    if not jfrog_or_reg_creds:
        errors.append("Run:ai registry/JFrog credentials must not be empty")
    if not cp_fqdn:
        errors.append("Run:ai control plane domain name (FQDN) must not be empty")
    if cp_fqdn and k8s_fqdn and cp_fqdn == k8s_fqdn:
        errors.append("Run:ai control plane FQDN must differ from the Kubernetes FQDN (6.11.2)")
    if not cert_path or not key_path:
        errors.append("Run:ai domain certificate (.crt/.pem) and private key (.key) paths must not be empty")

    # Consistency validation (since BCM 11.25.08): aborts setup
    if bcm_version >= (11, 25, 8):
        if bool(local_ca_path) and not custom_ca_enabled_in_helm:
            errors.append("local CA certificate provided, but custom CA is not enabled in Helm values: setup aborts")
        if not bool(local_ca_path) and custom_ca_enabled_in_helm:
            errors.append("local CA certificate NOT provided, but custom CA is enabled in Helm values: setup aborts")

    # Question phase validation (6.11.1)
    if not dns_resolves_to:
        warnings.append("domain name resolution failed")
    if local_ca_path and not cert_verify_ok:
        warnings.append("openssl verify against local CA failed")
    if cp_fqdn and not _fqdn_matches_san(cp_fqdn, cert_san_patterns):
        warnings.append("domain FQDN is not present in the certificate Subject Alternative Name (SAN) list")
    if bcm_version >= (11, 25, 8) and not using_metallb and not ip_routable_to_cluster:
        warnings.append("resolved IP address is not routable to a node in the BCM cluster")

    return {"errors": errors, "warnings": warnings}


def _fqdn_matches_san(fqdn, san_patterns):
    for pat in san_patterns:
        if pat == fqdn:
            return True
        if pat.startswith("*.") and fqdn.endswith(pat[1:]) and "." not in fqdn[: -len(pat[1:])]:
            return True
    return False


def tenants_manager_password_ok(pw):
    """Containerization Manual B.2.8 (p. 201): at least 8 characters, including at least one digit, one uppercase letter,
    and one special character."""
    if len(pw) < 8:
        return False
    has_digit = any(c.isdigit() for c in pw)
    has_upper = any(c.isupper() for c in pw)
    has_special = any(not c.isalnum() for c in pw)
    return has_digit and has_upper and has_special


def airgap_runai_precheck(
    distro,
    tarball_version,
    operator_default_version,
    reserved_ips,
    metallb_pool_ips,
    preallocated_in_pool,
    dns_records,
    cp_fqdn,
    ngc_api_key,
    bcm_version=(11, 33, 0),
    single_run_deploy=False,
):
    """Containerization Manual B.1 & B.2.8 (pp. 195, 200-202): checks air-gapped Run:ai rules."""
    problems = []
    if not distro.lower().startswith("ubuntu"):
        problems.append("air-gapped Run:ai on RHEL is not supported in this release (.deb only)")
    v_tuple = tuple(int(x) for x in tarball_version.split("."))
    if v_tuple < (2, 23, 60):
        problems.append("minimum Run:ai version 2.23.60 is required (multi-arch support)")
    if tarball_version != operator_default_version:
        problems.append("in air-gapped mode the Run:ai version is taken from operator defaults and must match the tarball version")
    if len(set(reserved_ips)) != 3:
        problems.append("three distinct reserved IP addresses are required (BCM gateway, Run:ai control plane ingress, Run:ai inference/Kourier)")
    if not set(reserved_ips).issubset(set(metallb_pool_ips)):
        problems.append("the MetalLB address range given during cm-kubernetes-setup must cover all three reserved IPs")
    if set(reserved_ips) & set(preallocated_in_pool):
        problems.append("leave the three IPs free rather than placing them in a MetalLB pool beforehand (the wizard creates its own pools)")
    needed_dns = {cp_fqdn, f"*.{cp_fqdn}"}
    if not needed_dns.issubset(set(dns_records)) or not any(d.startswith("*.runai-inference.") or d.startswith("*.") and "inference" in d for d in dns_records):
        problems.append("DNS needs the control plane FQDN, a workspace wildcard (*.<cp-fqdn>), and an inference wildcard (e.g. *.runai-inference.<domain>)")
    if not ngc_api_key:
        problems.append("an NGC API key is required by the wizard even for an air-gapped deployment")
    if bcm_version[:2] == (11, 33) and single_run_deploy:
        problems.append("in BCM 11.33 select Save & Exit first: a wizard bug prevents deploying in a single run")
    return problems


def mnnvl_dra_required(system_model):
    """Containerization Manual 6.11.3 (p. 150): the NVIDIA Dynamic Resource Allocation (DRA) driver (nvidia-dra-driver-gpu) is
    required for secure Internode Memory Exchange on Multi-Node NVLink systems (DGX B200, GB200, B300, and GB300)."""
    return system_model.upper() in {"DGX B200", "B200", "GB200", "DGX B300", "B300", "GB300", "DGX GB300"}


# ---- 4. Administrator Manual ch. 7 (pp. 417-418): Topograph on AWS / DGX Cloud ---------------------------------------------
def aws_topograph_check(nodes_running, instance_flavor, iam_permissions, pass_cloud_credentials):
    """Administrator Manual ch. 7 (pp. 417-418): for AWS clouds managed by BCM, compute nodes must be running (exist) and use a
    flavor that supports the AWS topology API (one supported flavor is p5.48xlarge, currently used by DGX Cloud). IAM identity
    needs ec2:DescribeInstanceTopology (e.g. via AmazonEC2ReadOnlyAccess), and Topograph needs credentials (if Pass cloud
    credentials is yes, BCM sends them on each topology fetch)."""
    SUPPORTED_EXAMPLE_FLAVORS = {"p5.48xlarge"}
    problems = []
    if not nodes_running:
        problems.append("AWS compute nodes must be running (exist) for Topograph")
    if instance_flavor not in SUPPORTED_EXAMPLE_FLAVORS:
        problems.append(f"instance flavor {instance_flavor} is not in the manual's supported example list (p5.48xlarge)")
    if "ec2:DescribeInstanceTopology" not in set(iam_permissions) and "AmazonEC2ReadOnlyAccess" not in set(iam_permissions):
        problems.append("IAM identity needs ec2:DescribeInstanceTopology (or AmazonEC2ReadOnlyAccess)")
    if not pass_cloud_credentials:
        problems.append("Topograph needs cloud credentials (set Pass cloud credentials to yes so BCM sends them on each fetch)")
    return problems


# ---- 5. Volume 21 chapter 7 (Part 2.1): checkpoint-interval lost-work bound ------------------------------------------------
def checkpoint_resume_loss(failure_step, checkpoint_interval):
    """Volume 21 chapter 7 section 2.1 worked example: if a job checkpoints every `checkpoint_interval` steps and fails at
    `failure_step`, it resumes from the latest completed multiple of `checkpoint_interval` (starting at the next step), so lost
    steps are `failure_step - last_checkpoint`, which is at most `checkpoint_interval`."""
    if checkpoint_interval <= 0 or failure_step < 0:
        raise MissionControlError("interval must be positive and failure_step non-negative")
    last_ckpt = (failure_step // checkpoint_interval) * checkpoint_interval
    lost = failure_step - last_ckpt
    return {"last_checkpoint_step": last_ckpt, "resume_from_step": last_ckpt + 1, "lost_steps": lost, "max_lost_steps": checkpoint_interval}
