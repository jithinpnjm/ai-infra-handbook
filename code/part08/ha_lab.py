#!/usr/bin/env python3
"""Self-checking lab for chapter 8.12: head node HA rules from Administrator Manual chapter 15, tested in bcm_ha.py."""
import sys
import bcm_ha as h

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except h.HaError:
        return True

def main():
    p = h.HeadPair()
    check("at the start the primary is active and the secondary passive", p.mode == {"primary": "ACTIVE", "secondary": "PASSIVE"})
    p.makeactive("secondary")
    check("after makeactive on the secondary: the secondary is active; the primary is still called primary and is now passive", p.mode == {"primary": "PASSIVE", "secondary": "ACTIVE"} and p.single_active())
    check("exactly one head is ever active", all((p.makeactive(n), p.single_active())[1] for n in ("primary", "secondary", "primary")))
    check("eight head node states exist", len(h.STATES) == 8 and "UNABLETOBECOMEACTIVE" in h.STATES)

    ok = {"failoverping": "OK", "ping": "OK", "status": "OK", "mysql": "OK"}
    check("all four OK: healthy", h.classify_active(ok) == "healthy")
    check("ping, failoverping and status all failed: all dead", h.classify_active({"failoverping": "FAIL", "ping": "FAIL", "status": "FAIL", "mysql": "FAIL"}) == "all dead")
    check("only status failed: mostly dead (slightly alive)", h.classify_active(dict(ok, status="FAIL")) == "mostly dead")
    check("only failoverping failed (cable?): mostly dead, not dead", h.classify_active(dict(ok, failoverping="FAIL")) == "mostly dead")
    check("mysql replication failing alone is reported but is not a failover trigger", "mysql" in h.classify_active(dict(ok, mysql="FAIL")) and h.classify_active(dict(ok, mysql="FAIL")).startswith("healthy"))

    check("quorum: 6 of 10 responding nodes cannot reach the active -> proceed", h.quorum_agrees(6, 10))
    check("quorum: exactly half is not enough", not h.quorum_agrees(5, 10))
    check("quorum: nodes that do not answer in time are not counted (3 of 4 responders)", h.quorum_agrees(3, 4, total_nodes=100))
    check("...but counting against all 100 nodes, 3 is nowhere near half (the manual's wording is ambiguous)", not h.quorum_agrees(3, 4, total_nodes=100, use_total=True))

    check("a graceful shutdown or reboot of the active does nothing on the passive", h.failover_decision("all dead", "graceful shutdown").startswith("nothing") and h.failover_decision("all dead", "reboot").startswith("nothing"))
    check("a healthy active: nothing", h.failover_decision("healthy").startswith("nothing"))
    check("a mostly dead active: nothing automatic (an administrator decides)", "mostly dead" in h.failover_decision("mostly dead"))
    check("all dead, power control and quorum ok: fence, STONITH, become active", h.failover_decision("all dead").startswith("fence"))
    check("automatic failover disabled: manual", h.failover_decision("all dead", auto_enabled=False).startswith("manual"))
    check("no power control: manual", h.failover_decision("all dead", power_control_ok=False).startswith("manual"))
    check("BMC unreachable (cable pulled): manual, not automatic", "BMC" in h.failover_decision("all dead", bmc_reachable=False))
    check("quorum says no: the passive may be the isolated one, so it does not power the active off", h.failover_decision("all dead", quorum_ok=False).startswith("nothing"))
    check("test outcomes: power off fails over, pulling the cable does not, graceful shutdown does not, sysrq crash does", "happens" in h.test_outcome("power off") and h.test_outcome("pull power cable").startswith("no automatic") and h.test_outcome("graceful shutdown").startswith("no failover") and "happens" in h.test_outcome("kernel crash (echo c > /proc/sysrq-trigger)"))

    check("timers: 3 s silent is ok, 7 s warn, 11 s dead (warn 5, dead 10)", [h.silence_level(s) for s in (3, 7, 11)] == ["ok", "warn", "dead"])
    check("at start-up Init dead (30 s) replaces Dead time: 11 s silent is only a warning", h.silence_level(11, just_started=True) == "warn" and h.silence_level(31, just_started=True) == "dead")
    check("with a dedicated failover network there are 3 heartbeat checks", h.heartbeat_checks(True) == 3)

    dbs = ["cmdaemon", "slurm_acct_db", "ajr", "mysql", "sys", "information_schema"]
    check("by default only cmdaemon and slurm_acct_db are replicated", h.replicated_databases(dbs) == ["cmdaemon", "slurm_acct_db"])
    check("a third-party database (ajr) is missing after a failover by default", h.missing_after_failover(dbs) == ["ajr"])
    check("extradbclone adds named databases", h.replicated_databases(dbs, extradbclone=["ajr"]) == ["ajr", "cmdaemon", "slurm_acct_db"])
    check("'replicate all' (11.34+) covers all non-system databases and never the system ones", h.replicated_databases(dbs, replicate_all=True) == ["ajr", "cmdaemon", "slurm_acct_db"] and h.missing_after_failover(dbs, replicate_all=True) == [])
    check("services on both heads: CMDaemon, DHCP, TFTP, LDAP, MySQL, NTP, DNS", h.SERVICES_ON_BOTH == ["CMDaemon", "DHCP", "TFTP", "LDAP", "MySQL", "NTP", "DNS"])
    check("services that migrate include NFS, the user portal and slurmdbd", {"NFS", "User Portal", "slurmdbd"} <= set(h.SERVICES_THAT_MIGRATE))
    check("shared by default: /home and /cm/shared", h.SHARED_DIRS == ["/home", "/cm/shared"])
    check("an unmount script that returns 0 despite a problem is flagged (double-mount risk)", not h.storage_script_ok(0, True)[0] and h.storage_script_ok(1, True)[0] and h.storage_script_ok(0, False)[0])
    check("the passive head shows the old local contents of the shared directories", h.passive_shows_old_contents())

    check("a clean HA setup has no problems", h.ha_setup_problems(2, True, True, "direct cable", "NAS") == [])
    bad = h.ha_setup_problems(1, False, False, "switch", "DAS")
    check("single-MAC license, DHCP external, no power control, switched heartbeat and DAS are all flagged", len(bad) == 5, bad)
    check("update order: cmdaemon and mysql go active first, confirm, then passive", h.update_order("cmdaemon") == ["active", "confirm cmha status OK", "passive"])
    check("update order: NFS goes passive first, then makeactive, then the former active", h.update_order("nfs") == ["passive", "cmha makeactive on the passive", "former active"])
    check("update order: DHCP, LDAP, NTP, DNS in any order", h.update_order("dns") == ["both at about the same time"])
    check("an unmodelled package is refused", raises(lambda: h.update_order("postfix")))
    check("things to sync by hand include RPM installs and /cm/node-installer files", any("RPM" in x for x in h.things_to_sync_by_hand()) and any("node-installer" in x for x in h.things_to_sync_by_hand()))
    d = h.regular_node_ha_differences()
    check("regular node HA: failover groups, several passive nodes, no failover network", d["config submode"] == "failovergroups" and "several" in d["passive nodes"] and "no failover network" in d["heartbeat"])

    # Gap pass: 15.3 express cmha-setup, 15.4.8 clone exclude lists, 15.5.4 regular node failover sequence, 15.6 job continuation
    cmds = h.cmha_express_commands(mysql_password="secret", replicate_all_dbs=True, finalize_reboot=True, storage_type="nas")
    check("cmha-setup -x express sequence runs -i (initialize), cm-clone-install --failover, -f -r (finalize+reboot), and -s nas (15.3.2, 15.3.3)",
          len(cmds) == 4 and "-x" in cmds[0] and "-i" in cmds[0] and "-a" in cmds[0] and "-f -r" in cmds[2] and cmds[3].endswith("-s nas"))
    check("cmha-setup -x recommended XML path is /cm/local/apps/cluster-tools/ha/conf/failoverconf.xml (15.3.2 p. 816)",
          h.EXPRESS_DEFAULT_CONFIG == "/cm/local/apps/cluster-tools/ha/conf/failoverconf.xml")
    check("cm-clone-install uses /cm/excludelistfailover with --failover and /cm/excludelistnormal without it (15.4.8 p. 828)",
          h.clone_install_exclude_file(True) == "/cm/excludelistfailover" and h.clone_install_exclude_file(False) == "/cm/excludelistnormal")
    seq_ok = h.regular_node_failover_sequence(unmount_exit_code=0, stonith_triggered=False)
    check("regular node HA makeactive runs pre-failover, active stop/umount/IP/passive, passive stop/mount/IP/start, post-failover (15.5.4 p. 834)",
          seq_ok["completed"] and seq_ok["steps"][0] == "all: run pre-failover script" and seq_ok["steps"][-1] == "all: run post-failover script")
    seq_err = h.regular_node_failover_sequence(unmount_exit_code=1, stonith_triggered=False)
    check("regular node HA skips all remaining actions if the active umount script returns non-zero (15.5.4 p. 834)",
          seq_err["aborted_on_umount_error"] and not seq_err["completed"])
    seq_st = h.regular_node_failover_sequence(unmount_exit_code=0, stonith_triggered=True)
    check("regular node HA aborts the old-active sequence on STONITH and completes passive takeover (15.5.4 p. 834)",
          seq_st["completed"] and "active: aborted by STONITH power-off" in seq_st["steps"])
    check("WLM jobs continue across failover when WLM was set up via cm-wlm-setup, storage is NAS (Slurm/LSF), and job tolerates brief NFS pause (15.6)",
          h.wlm_jobs_continue_across_failover(True, "NAS", "slurm", True) and
          h.wlm_jobs_continue_across_failover(True, "NAS", "lsf", True))
    check("WLM job continuation fails if any of the 3 conditions is not met (e.g. non-NAS storage or job crashes on brief NFS pause) (15.6)",
          not h.wlm_jobs_continue_across_failover(False, "NAS", "slurm", True) and
          not h.wlm_jobs_continue_across_failover(True, "DAS", "slurm", True) and
          not h.wlm_jobs_continue_across_failover(True, "NAS", "slurm", False))

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
