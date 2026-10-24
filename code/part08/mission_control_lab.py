#!/usr/bin/env python3
"""Self-checking lab for chapter 8.16: Mission Control, Run:ai (6.11 and B.2.8), DGX Cloud Topograph rules,
nonuser recovery profiles (6.5) and HA MySQL replication (15.1), tested in bcm_mission_control.py."""
import sys
import bcm_mission_control as mc

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond)
    fail_count += not cond
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def raises(fn):
    try:
        fn()
        return False
    except mc.MissionControlError:
        return True


def main():
    # 1. GB300 RA pp. 32-33: five-layer prose description
    s = mc.mc_stack_summary()
    check("GB300 prose describes five Mission Control stack roles, only two named with the literal word 'layer'",
          s["total"] == 5 and s["explicit"] == ["telemetry_and_observability", "validation_and_diagnostics"])
    check("Validation and Diagnostics is the role that supports the built-in autonomous recovery engine",
          "autonomous recovery engine" in mc.MC_PROSE_COMPONENTS["validation_and_diagnostics"]["stated_in_text"])
    check("Telemetry and Observability uses proprietary diagnostic tools and health-checks",
          "proprietary diagnostic tools" in mc.MC_PROSE_COMPONENTS["telemetry_and_observability"]["stated_in_text"])
    check("Four business-value claims are stated (automated failure detection, workload migration, unified diagnostics, in-memory checkpointing)",
          len(mc.MC_VALUE_CLAIMS) == 4 and "checkpoint" in mc.MC_VALUE_CLAIMS["in_memory_checkpointing"])

    # 2. Administrator Manual 6.5: preconfigured profiles & nonuser rule
    check("14 preconfigured profiles are listed in the 6.5 table; only admin, readonly and portal are user profiles",
          len(mc.PRECONFIGURED_PROFILES) == 14 and
          {k for k, v in mc.PRECONFIGURED_PROFILES.items() if not v[1]} == {"admin", "readonly", "portal"})
    check("autonomous-hardware-recovery allows 'autonomous hardware recovery tasks' and is a nonuser profile",
          mc.profile_tasks_and_nonuser("autonomous-hardware-recovery") == ("autonomous hardware recovery tasks", True))
    check("autonomous-job-recovery allows 'autonomous job recovery tasks' and is a nonuser profile",
          mc.profile_tasks_and_nonuser("autonomous-job-recovery") == ("autonomous job recovery tasks", True))
    check("modifying or disabling autonomous-hardware-recovery is forbidden (nonuser profile)",
          raises(lambda: mc.validate_profile_operation("autonomous-hardware-recovery", "modify_tokens")) and
          raises(lambda: mc.validate_profile_operation("autonomous-hardware-recovery", "disable")))
    check("assigning autonomous-job-recovery to a human user is forbidden; assigning readonly is allowed",
          raises(lambda: mc.validate_profile_operation("autonomous-job-recovery", "assign_to_user", "conner")) and
          mc.validate_profile_operation("readonly", "assign_to_user", "conner") == "allowed")

    # 3. Administrator Manual 15.1: HA MySQL replication scope and third-party databases (e.g. ajr)
    r_default = mc.mysql_dbs_after_failover(["cmdaemon", "slurm_acct_db", "ajr", "mysql"])
    check("by default HA MySQL replicates only cmdaemon and slurm_acct_db; a third-party database (e.g. ajr) is missing after failover",
          r_default == {"replicated": ["cmdaemon", "slurm_acct_db"], "missing": ["ajr"]})
    r_extra = mc.mysql_dbs_after_failover(["cmdaemon", "slurm_acct_db", "ajr"], extradbclone=["ajr"])
    check("listing a third-party database in extradbclone.xml preserves it across a failover",
          r_extra["missing"] == [] and "ajr" in r_extra["replicated"])
    r_all = mc.mysql_dbs_after_failover(["cmdaemon", "slurm_acct_db", "ajr", "mysql", "sys"], bcm_version=(11, 34, 0), replicate_all_non_system=True)
    check("from BCM 11.34.0, replicate_all_non_system clones all non-system databases while still excluding system schemas (mysql, sys)",
          r_all["replicated"] == ["ajr", "cmdaemon", "slurm_acct_db"] and r_all["missing"] == [])
    check("replicate_all_non_system is not available before BCM 11.34.0",
          raises(lambda: mc.mysql_dbs_after_failover(["cmdaemon", "ajr"], bcm_version=(11, 33, 0), replicate_all_non_system=True)))

    # 4. Administrator Manual 6.4.5, 14.5, 3.7.11: Keycloak federation, firmware license, leak detection suffix
    kc_ok = mc.keycloak_mc_federation_check(
        "ubuntu24.04", (11, 34, 0), mc_on_head_node=False, firewall_open_ports=[9443],
        supplied_fields={"keycloak_url": "https://head.cm.cluster:9443", "realm_name": "head.cm.cluster",
                         "admin_credentials": "admin/secret", "tls_certificate": "/opt/kc.crt"})
    check("Keycloak Mission Control federation on Ubuntu 24.04 (BCM 11.34) with port 9443 open passes", kc_ok == [], kc_ok)
    kc_bad = mc.keycloak_mc_federation_check(
        "rhel9", (11, 33, 0), mc_on_head_node=False, firewall_open_ports=[],
        supplied_fields={"keycloak_url": "http://head:8080"})
    check("Keycloak on RHEL, pre-11.34, wrong URL port, missing fields and closed 9443 are all flagged", len(kc_bad) == 5, kc_bad)
    check("Base View GB300 firmware flash fails without an active Mission Control license and rejects 11.34.0 Dry Run",
          len(mc.base_view_firmware_flash_check("gb300", has_mc_license=False, bcm_version=(11, 34, 0), action="dry_run", num_packages=2, narrow_targets=True)) == 4 and
          mc.base_view_firmware_flash_check("gb300", has_mc_license=True, bcm_version=(11, 35, 0), action="dry_run") == [])
    check("disabling leak detection appends 'leak:disabled' to the device status line; enabled shows no suffix",
          mc.leak_status_suffix(True) == "" and mc.leak_status_suffix(False) == "leak:disabled")

    # 5. Containerization Manual 6.11 & B.2.8: Run:ai installation workflow and plugin package
    check("before BCM 11.33 Run:ai installs inside cm-kubernetes-setup; from 11.33 it is decoupled into cm-runai-setup",
          not mc.runai_install_workflow((11, 32, 0))["decoupled"] and mc.runai_install_workflow((11, 33, 0))["decoupled"])
    check("cm-runai-setup is in cm-setup, but fails in air-gap without the separate cm-setup-runai-bcm11 plugin package",
          not mc.can_run_cm_runai_setup(True, False, False, "ubuntu24.04", skip_packages=True)[0] and
          mc.can_run_cm_runai_setup(True, True, False, "ubuntu24.04", skip_packages=True)[0])
    check("on an internet-connected cluster cm-setup-runai-bcm11 is installed automatically unless --skip-packages is set",
          mc.can_run_cm_runai_setup(True, False, True, "ubuntu24.04", skip_packages=False)[0] and
          not mc.can_run_cm_runai_setup(True, False, True, "ubuntu24.04", skip_packages=True)[0])
    check("Run:ai lists 12 required dependency operators and 2 optional ones (Network Operator, NIM Operator)",
          len(mc.RUNAI_REQUIRED_OPERATORS) == 12 and mc.RUNAI_OPTIONAL_OPERATORS == {"Network Operator", "NIM Operator"})

    # 6. Containerization Manual 6.11.1 & 6.11.2: wizard validation checks
    v_ok = mc.runai_wizard_validation(
        "self-hosted", jfrog_or_reg_creds="base64tok", cp_fqdn="runai.example.com", k8s_fqdn="k8s.example.com",
        cert_path="/cm/shared/runai/cert.pem", key_path="/cm/shared/runai/key.pem",
        local_ca_path="/cm/shared/runai/ca.crt", custom_ca_enabled_in_helm=True,
        dns_resolves_to="10.0.0.50", cert_verify_ok=True, cert_san_patterns=["*.example.com"],
        ip_routable_to_cluster=False, using_metallb=True)
    check("valid self-hosted config with wildcard SAN and MetalLB (which disables the IP routability check) has no errors or warnings",
          v_ok == {"errors": [], "warnings": []}, v_ok)
    v_ca_mismatch = mc.runai_wizard_validation(
        "self-hosted", jfrog_or_reg_creds="tok", cp_fqdn="runai.example.com", k8s_fqdn="k8s.example.com",
        cert_path="c.pem", key_path="k.key", local_ca_path="/ca.crt", custom_ca_enabled_in_helm=False,
        dns_resolves_to="10.0.0.50", cert_san_patterns=["runai.example.com"])
    check("providing a local CA without enabling custom CA in Helm values aborts setup (consistency check since 11.25.08)",
          any("setup aborts" in e for e in v_ca_mismatch["errors"]))
    v_same_fqdn = mc.runai_wizard_validation(
        "self-hosted", jfrog_or_reg_creds="tok", cp_fqdn="cluster.example.com", k8s_fqdn="cluster.example.com",
        cert_path="c.pem", key_path="k.key", dns_resolves_to="10.0.0.50", cert_san_patterns=["cluster.example.com"],
        ip_routable_to_cluster=False, using_metallb=False)
    check("control plane FQDN equal to Kubernetes FQDN is an error, and unroutable IP without MetalLB is a warning",
          len(v_same_fqdn["errors"]) == 1 and len(v_same_fqdn["warnings"]) == 1, v_same_fqdn)
    check("SaaS mode requires tenant_name, app_secret, admin_user, admin_password, hostname, cert_path and key_path",
          len(mc.runai_wizard_validation("saas", saas_creds={"tenant_name": "t"})["errors"]) == 6)

    # 7. Containerization Manual B.2.8 & 6.11.3: password policy, air-gap Run:ai prechecks, DRA on MNNVL
    check("Tenants Manager password policy enforces >=8 chars, digit, uppercase and special character",
          mc.tenants_manager_password_ok("Runai#2026") and not mc.tenants_manager_password_ok("runai#2026") and
          not mc.tenants_manager_password_ok("Runai2026") and not mc.tenants_manager_password_ok("R#1a"))
    ag_ok = mc.airgap_runai_precheck(
        "ubuntu24.04", "2.25.11", "2.25.11",
        reserved_ips=["10.0.0.10", "10.0.0.11", "10.0.0.12"],
        metallb_pool_ips=[f"10.0.0.{i}" for i in range(10, 20)],
        preallocated_in_pool=[],
        dns_records=["runai.example.com", "*.runai.example.com", "*.runai-inference.example.com"],
        cp_fqdn="runai.example.com", ngc_api_key="nvapi-xxx",
        bcm_version=(11, 33, 0), single_run_deploy=False)
    check("air-gapped Run:ai 2.25.11 on Ubuntu with 3 free MetalLB IPs, both wildcards, NGC key and Save & Exit passes",
          ag_ok == [], ag_ok)
    ag_bad = mc.airgap_runai_precheck(
        "rhel9", "2.23.0", "2.25.11",
        reserved_ips=["10.0.0.10", "10.0.0.99"],
        metallb_pool_ips=["10.0.0.10"],
        preallocated_in_pool=["10.0.0.10"],
        dns_records=["runai.example.com"],
        cp_fqdn="runai.example.com", ngc_api_key="",
        bcm_version=(11, 33, 0), single_run_deploy=True)
    check("air-gap precheck catches RHEL, version <2.23.60, tarball/operator mismatch, <3 IPs, small MetalLB range, pre-pooled IPs, missing wildcards, missing NGC key and 11.33 single-run bug",
          len(ag_bad) == 9, ag_bad)
    check("NVIDIA DRA driver (nvidia-dra-driver-gpu) is required on Multi-Node NVLink systems (B200, GB200, B300, GB300)",
          mc.mnnvl_dra_required("GB300") and mc.mnnvl_dra_required("DGX B200") and not mc.mnnvl_dra_required("DGX H100"))

    # 8. Administrator Manual ch. 7 (pp. 417-418) & Volume 21 ch. 7 (2.1): AWS Topograph (DGX Cloud) & checkpoint math
    check("AWS Topograph accepts running p5.48xlarge (used by DGX Cloud) with ec2:DescribeInstanceTopology and Pass cloud credentials=yes",
          mc.aws_topograph_check(True, "p5.48xlarge", ["ec2:DescribeInstanceTopology"], True) == [] and
          len(mc.aws_topograph_check(False, "g5.xlarge", [], False)) == 4)
    ckpt = mc.checkpoint_resume_loss(5243, 500)
    check("Volume 21 ch. 7 worked example: failure at step 5243 with 500-step interval resumes from 5001 (step-5000) and loses 243 steps (<=500)",
          ckpt == {"last_checkpoint_step": 5000, "resume_from_step": 5001, "lost_steps": 243, "max_lost_steps": 500})

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
