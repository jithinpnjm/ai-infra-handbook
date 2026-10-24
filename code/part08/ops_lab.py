#!/usr/bin/env python3
"""Self-checking lab for chapter 8.13: day-2 operations rules from Administrator Manual chapters 9 and 14, tested in bcm_ops.py."""
import sys
import bcm_ops as o

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except (o.OpsError, KeyError):
        return True

def main():
    check("10.23.09 is a calendar point release (2023, September)", o.parse_point_release("10.23.09")["scheme"] == "calendar")
    check("11.25.08 is the last calendar release of the 11 series", o.parse_point_release("11.25.08")["scheme"] == "calendar")
    check("11.30.0 and 11.34.0 are semantic releases", o.parse_point_release("11.30.0")["scheme"] == "semantic" and o.parse_point_release("11.34.0")["scheme"] == "semantic")
    check("a letter suffix is a hotfix: 10.23.02a", o.parse_point_release("10.23.02a")["hotfix"] == "a" and o.parse_point_release("11.31.0")["hotfix"] is None)
    check("a non-BCM version string is refused", raises(lambda: o.parse_point_release("12.1")))
    check("RHEL8 to RHEL9 under BCM is not supported (reinstall BCM); updates within RHEL9 are", not o.os_change_supported("RHEL8", "RHEL9") and o.os_change_supported("RHEL9", "RHEL9"))
    check("head update commands per distro", o.head_update_commands("ubuntu") == ["apt update", "apt upgrade"] and o.head_update_commands("sles") == ["zypper refresh", "zypper up"])

    # Gap pass: 9.1 & 9.2 package filename structure, device packages -a scale, GPG key, /cm/shared layout
    rpm_info = o.parse_bcm_package_filename("cmdaemon-11.0-152061_cm11.0_ec0ea0f4d1.x86_64.rpm")
    deb_info = o.parse_bcm_package_filename("cmdaemon_11.0-152061-cm11.0-ec0ea0f4d1_amd64.deb")
    check("9.1 RPM and DEB package filenames carry package, version, revision, cm11.0, developer hash and arch",
          rpm_info["is_bcm"] and rpm_info["hash"] == "ec0ea0f4d1" and rpm_info["arch"] == "x86_64" and
          deb_info["is_bcm"] and deb_info["hash"] == "ec0ea0f4d1" and deb_info["arch"] == "amd64")
    check("a distribution package without _cm / -cm is identified as non-BCM (9.1 p. 522)",
          not o.parse_bcm_package_filename("gzip-1.9-9.el8.x86_64.rpm")["is_bcm"])
    check("device 'packages -a' returns ~100 KB per node, so 1000 nodes produce ~100 MB (use -f <pkg> instead) (9.1.1 p. 523)",
          o.device_packages_all_output_mb(1000) == 100.0)
    check("Bright Computing GPG key ID is 0x5D849C16 (9.2.1 p. 528)", o.BCM_GPG_KEY_ID == "0x5D849C16")
    check("non-RPM/DEB software under /cm/shared uses the 6 standard subdirectories (apps, docs, etc, examples, licenses, modulefiles) (9.2.2 p. 529)",
          len(o.CM_SHARED_SUBDIRS) == 6 and "modulefiles" in o.CM_SHARED_SUBDIRS)

    check("default genders: all, category=default, computenode, headnode", set(o.GENDERS) == {"all", "category=default", "computenode", "headnode"})
    check("restarting CMDaemon on many regular nodes needs pdsh, not pexec", o.choose_parallel_tool("restart cmd on regular nodes") == "pdsh")
    check("power operations go through cmsh device power, with its delay", "cmsh device power" in o.choose_parallel_tool("power reset"))
    check("pdsh -v skips down nodes; -A would try everything", o.pdsh_flags() == ["-v"])
    check("a per-node cmsh loop for 127 nodes costs 127 cmsh runs; a single pipe costs 1", o.cmsh_calls(127, "loop") == 127 and o.cmsh_calls(127, "pipe") == 1)
    sc = o.bulk_category_script(["node129", "node130"], "newbunch")
    check("the bulk script is one device session with one commit", sc == ["device", "set node129 category newbunch", "set node130 category newbunch", "commit"])

    check("cm-diagnose defaults: 50 MB log limit and 60 s timeout", o.CM_DIAGNOSE_DEFAULTS == {"limit_mb": 50, "timeout_s": 60})
    check("large clusters get --limit 100 --timeout 240", o.cm_diagnose_args(500) == ["--limit", "100", "--timeout", "240"] and o.cm_diagnose_args(10) == [])
    check("support portal: Software, and 'Base Command Manager' for 10 and later", o.support_case(11) == {"product_type": "Software", "product_category": "Base Command Manager"} and o.support_case(9)["product_category"] == "Bright Cluster Manager")

    check("seven rotating local backups, backup-<Day>.sql.gz", o.local_backup_names() == [f"backup-{d}.sql.gz" for d in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")] and o.BACKUP_DIR == "/var/spool/cmd/backup")
    check("cmdaemon-backup without argument overwrites the day's backup", o.cmdaemon_backup_name(day="Wed") == "backup-Wed.sql.gz")
    check("cmdaemon-backup manual gives manual-<timestamp>_<Day>.sql.gz (the manual's example)", o.cmdaemon_backup_name("manual", "24-08-28_13-19-59", "Wed") == "manual-24-08-28_13-19-59_Wed.sql.gz")
    sc = o.backup_scope()
    check("BCM has no backup facility; raw monitoring data is not backed up locally", sc["BCM provides a backup facility"] is False and "raw monitoring data" in sc["not backed up locally"][0])
    check("restore with HA: cmha dbreclone, monitoring data not cloned", "dbreclone" in o.restore_path(True) and "not cloned" in o.restore_path(True))
    check("restore without HA: the local backup into MySQL", "backup-<Day>.sql.gz" in o.restore_path(False))
    check("if MySQL cannot start, CMDaemon cannot start", "CMDaemon cannot start" in o.restore_path(False, mysql_starts=False))
    check("four corruption symptoms are listed", len(o.corruption_symptoms()) == 4)

    check("Btrfs for images: not on RHEL 8 or 9 (removed), fine on SLES", not o.btrfs_ok_for("rhel9") and o.btrfs_ok_for("sles15"))
    check("a new revision of default-image 3 is default-image@3 in /cm/images/default-image-3", o.revision_name("default-image", 3) == ("default-image@3", "/cm/images/default-image-3"))
    ref = {"cpus": 2, "gpus": 8, "mem": 2048}
    res = o.hardware_match(ref, {"n1": dict(ref), "n2": dict(ref), "n3": dict(ref, gpus=7)})
    check("hardware match: the node with 7 GPUs is the mismatch; the reference is fine", res == {"mismatched": ["n3"], "reference_suspect": False})
    res = o.hardware_match(ref, {"n1": dict(ref, gpus=4), "n2": dict(ref, gpus=4), "n3": dict(ref)})
    check("if most nodes mismatch, suspect the reference node", res["reference_suspect"])
    check("hardware profiles live under /cm/shared/apps/cmd/hardware-profiles; check every 600 s", o.HW_PROFILE["interval_s"] == 600 and "hardware-profiles" in o.HW_PROFILE["reference saved under"])

    check("replacing a node with a known MAC: set mac, commit", o.node_replacement_steps(True) == ["device use <node>", "set mac <new mac>", "commit"])
    check("unknown MAC: clear mac, commit, and name it at the node installer", o.node_replacement_steps(False)[1] == "clear mac" and any("node installer" in x for x in o.node_replacement_steps(False)))
    check("a different disk size needs the disk layout checked", any("disk layout" in x for x in o.node_replacement_steps(True, same_disk_size=False)))
    check("the Ansible collection for BCM 11 is brightcomputing.bcm110", o.ansible_collection("11.0") == "brightcomputing.bcm110")
    check("MySQL HA failover command; --force when the primary crashed", o.mysql_failover_command("node001") == "cm-slurm-mysql-ha --config /root/mysql-ha-config.conf failover --host node001" and o.mysql_failover_command("node002", True).endswith("--force"))
    check("after a forced failover remediate the old primary as a replica of the new one", o.mysql_remediate_command("node002", "node001") == "cm-slurm-mysql-ha --config /root/mysql-ha-config.conf remediate --host node002 --target node001")

    check("every runbook starts by writing down the undo and taking a named DB backup", all(o.change_runbook(k)[:2] == ["write down what you will change and how to undo it", "cmdaemon-backup before-change (a named DB backup)"] for k in ("image", "head package", "bios or firmware")))
    check("the image runbook uses a dry run before -w and updateprovisioners first", "updateprovisioners" in o.change_runbook("image") and any("dry run" in x for x in o.change_runbook("image")))
    check("the head package runbook orders active before passive", any("active first" in x for x in o.change_runbook("head package")))
    check("the firmware runbook includes the AC power cycle", any("AC power cycle" in x for x in o.change_runbook("bios or firmware")))
    check("an unknown runbook kind is refused", raises(lambda: o.change_runbook("kernel")))

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
