#!/usr/bin/env python3
"""Self-checking lab for chapter 8.8: Slurm-under-BCM rules from Administrator Manual chapter 7, tested in bcm_slurm.py."""
import sys
import bcm_slurm as s

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except s.WlmError:
        return True

def main():
    # usernodelogin
    check("usernodelogin always (default): anyone can ssh to a node", s.user_may_ssh_to_node("always", "alice", False))
    check("never: only root", s.user_may_ssh_to_node("never", "root", False) and not s.user_may_ssh_to_node("never", "alice", True))
    check("onlywhenjob: allowed while the user has a job on the node, refused otherwise", s.user_may_ssh_to_node("onlywhenjob", "alice", True) and not s.user_may_ssh_to_node("onlywhenjob", "alice", False))
    check("onlywhenjob: a user in pam_allow.conf is allowed anyway", s.user_may_ssh_to_node("onlywhenjob", "diag", False, in_pam_allow=True))
    check("an invalid usernodelogin value is refused", raises(lambda: s.user_may_ssh_to_node("sometimes", "a", False)))

    # HA
    check("slurmctldstartpolicy default: TAKEOVER on HA, ALWAYS on a single head", s.default_start_policy(True) == "TAKEOVER" and s.default_start_policy(False) == "ALWAYS")
    check("WLM servers on two head nodes are fine", s.server_nodes_ok(["head1", "head2"], {"head1", "head2"}))
    check("WLM servers on two compute nodes are fine", s.server_nodes_ok(["n1", "n2"], {"head1"}))
    check("one head node and one compute node is refused", raises(lambda: s.server_nodes_ok(["head1", "n1"], {"head1", "head2"})))
    check("TAKEOVER on two compute nodes is configured automatically only when both are in a failover group", s.compute_takeover_configured(True) and not s.compute_takeover_configured(False))
    check("the takeover script path is slurm.takeover.sh", s.TAKEOVER_SCRIPT.endswith("scripts/slurm.takeover.sh"))
    check("the active head node and the active Slurm server need not be the same", s.active_head_is_slurm_primary_independent())

    # cm-wlm-setup
    check("a WLM object cannot be created from cmsh", any("cm-wlm-setup" in x for x in s.cm_wlm_setup_check("slurm", new_object_from_cmsh=True)))
    check("LSF needs --archives-location", any("archives" in x for x in s.cm_wlm_setup_check("lsf")) and not s.cm_wlm_setup_check("lsf", archives_location="/x"))
    check("--nvidia-gpus A100:4 is accepted; 'A100' alone is not", not s.cm_wlm_setup_check("slurm", nvidia_gpus="A100:4") and s.cm_wlm_setup_check("slurm", nvidia_gpus="A100"))
    check("--min-reboot-timeout below 300 is refused", s.cm_wlm_setup_check("slurm", min_reboot_timeout=120))
    check("a clean slurm setup has no problems", s.cm_wlm_setup_check("slurm") == [])
    n = s.wlm_overlay_names("slurm")
    check("default overlay names are <wlm>-server, -client, -submit, -accounting, -client-gpu", n["server"] == "slurm-server" and n["client"] == "slurm-client" and n["gpu client"] == "slurm-client-gpu")
    check("default priorities: 500 for roles, 450 for the GPU client, 600 for the head node submit overlay", s.CM_WLM_DEFAULTS["overlay_priority"] == 500 and s.CM_WLM_DEFAULTS["gpu_overlay_priority"] == 450 and s.CM_WLM_DEFAULTS["head_submit_overlay_priority"] == 600)

    # accounting
    a = s.accounting_plan(["head1", "head2"], {"head1", "head2"})
    check("two head accounting nodes: slurmdbd HA, 'use accounting node' offered", a["ha"] and "use accounting node" in a["database_options"] and a["backup"] == "head2")
    check("mixed head and compute accounting nodes are rejected", raises(lambda: s.accounting_plan(["head1", "n1"], {"head1"})))
    c = s.accounting_plan(["n1"], {"head1"}, mysql_overlay_exists=False, mysql_on_several_nodes=True)
    check("compute accounting nodes need a BCM MySQL overlay (cm-mysql-setup first)", any("cm-mysql-setup" in x for x in c["steps"]) and "select cluster node" in c["database_options"])
    check("mysql-router is added when MySQL runs on several nodes", any("mysql-router" in x for x in c["steps"]))
    check("three accounting nodes are refused", raises(lambda: s.accounting_plan(["a", "b", "c"], set())))

    # GPU overlay priority trap
    cl = s.wlm_cluster()
    r = cl.roles_of("gpu001")["slurmclient"]
    check("a GPU node in category gpu gets the GPU client overlay (450) when only that overlay applies", r.params["gpu"] is True and r.priority == 450)
    cl.nodes["gpu001"].category = "gpu"
    cl.overlays["slurm-client"].nodes.add("gpu001")
    r = cl.roles_of("gpu001")["slurmclient"]
    check("THE TRAP: if the same node is also in the 500 slurm-client overlay, the non-GPU client wins and the GPU settings are lost", r.params["gpu"] is False and r.priority == 500)
    check("so only non-GPU nodes belong in slurm-client (the manual's instruction)", cl.roles_of("node001")["slurmclient"].params["gpu"] is False)

    # gres autodetect
    check("GPU auto detect nvml/rsmi/oneapi/nrt/off map to AutoDetect=<value>", [s.gres_autodetect_line(v) for v in ("nvml", "rsmi", "oneapi", "nrt", "off")] == ["AutoDetect=nvml", "AutoDetect=rsmi", "AutoDetect=oneapi", "AutoDetect=nrt", "AutoDetect=off"])
    check("none writes no AutoDetect line; bcm lets BCM write the vendor and count", s.gres_autodetect_line("none") is None and "BCM" in s.gres_autodetect_line("bcm"))
    check("seven GPU auto detect values exist", len(s.GPU_AUTODETECT) == 7 and raises(lambda: s.gres_autodetect_line("cuda")))

    # nodesets
    ln = s.slurm_conf_lines(["node001"], nodesets="ns1")
    check("nodesets ns1 on node001 gives NodeSet=ns1 Nodes=node001 (the manual's example)", "NodeSet=ns1 Nodes=node001" in ln)
    ln = s.slurm_conf_lines(["node001"], nodeset_features=["bigmem"])
    check("a nodeset feature is added to the node's Features and as NodeSet=bigmem Feature=bigmem", "NodeName=node001 Features=bigmem" in ln and "NodeSet=bigmem Feature=bigmem" in ln)
    check("a queue with nodesets set uses only those (the Compute nodes parameter is not added)", s.queue_nodes(nodesets=["ns1"], compute_nodes=["node009"]) == "Nodes=ns1")
    res = {("category", "default"): ["node001", "node002"], ("overlay", "ov"): ["node002", "node003"]}
    check("without nodesets a queue is the union of overlays, categories, node groups and compute nodes", s.queue_nodes(overlays=["ov"], categories=["default"], compute_nodes=["node009"], resolve=res) == ["node001", "node002", "node003", "node009"])

    # Pyxis
    check("unshared Pyxis cache: the prolog makes a per-UID directory", s.pyxis_cache_plan(False)["uid_subdir"])
    p = s.pyxis_cache_plan(True, cache_dir_exists=False)
    check("a shared cache is created with 00777 and no per-UID directory", p["mode"] == "00777" and not p["uid_subdir"])
    check("restricting the shared cache to a Pyxis group uses 00770", s.pyxis_cache_plan(True, group_restricted=True)["mode"] == "00770")
    check("Enroot defaults: runtime/cache/data paths under /run/enroot/.../$(id -u), home mounted", s.ENROOT_CONF_DEFAULTS["ENROOT_CACHE_PATH"] == "/run/enroot/cache/$(id -u)" and s.ENROOT_CONF_DEFAULTS["ENROOT_MOUNT_HOME"] == "yes")
    check("the container options all start with --container or --no-container", all(o.startswith(("--container", "--no-container")) for o in s.srun_container_options()))

    # upgrade
    u = s.upgrade_plan("25.05", "25.11", uses_pyxis=True, images=("default-image", "gpu-image"))
    check("upgrade: drain first, stop slurmctld and slurmdbd, remove old packages from the head and every image", u["steps"][0].startswith("drain") and "stop slurmctld" in u["steps"][1] and sum("remove slurm25.05" in x for x in u["steps"]) == 3)
    check("upgrade: Pyxis must be reinstalled after a Slurm upgrade", any("Pyxis" in x for x in u["steps"]))
    check("upgrade: skipping a major version gets the one-at-a-time advice", s.upgrade_plan("24.05", "25.11")["advice"] == "one major version at a time" and s.upgrade_plan("25.05", "25.11")["advice"] == "")
    check("downgrades are refused", raises(lambda: s.upgrade_plan("25.11", "25.05")))

    # cgroups
    check("Slurm's three cgroup plugins are on by default", len(s.CGROUP_PLUGINS) == 3)
    cg = s.cgroup_conf({"ConstrainCores": True, "ConstrainRAMSpace": True, "ConstrainDevices": True, "AllowedRAMSpace": 100})
    check("cgroup.conf lines: yes/no for booleans, numbers as given", cg == ["ConstrainCores=yes", "ConstrainRAMSpace=yes", "ConstrainDevices=yes", "AllowedRAMSpace=100"])
    check("ConstrainDevices is what confines jobs to their allocated GPUs", s.devices_constrained({"ConstrainDevices": True}) and not s.devices_constrained({"ConstrainCores": True}))
    check("an unknown cgroup parameter is refused", raises(lambda: s.cgroup_conf({"Nonsense": 1})))

    # drain
    nd = s.SlurmNode("node001"); nd.running = ["job1"]
    nd.drain(["reboot"])
    check("a drained node starts no new jobs but lets the running one finish", not nd.can_start_job() and nd.running == ["job1"])
    check("with the reboot drain action the node reboots when the last job ends", nd.job_finished("job1") == "reboot")
    nd.undrain()
    check("undrain lets jobs start again", nd.can_start_job())

    # Gap pass: 7.4.3, 7.5, 7.6-7.9, 7.11 checks
    check("FreezeChangesToSlurmConfig and FreezeChangesToLSFConfig directives format (7.5 p. 387)",
          s.freeze_wlm_config_directive("slurm", True) == "FreezeChangesToSlurmConfig = true" and
          s.freeze_wlm_config_directive("lsf", False) == "FreezeChangesToLSFConfig = false")
    check("wlmjobpowerusagesettings defaults: Job age 5m, Timeout 30s, Disabled no (7.7.2 p. 448)",
          s.WLM_JOB_POWER_DEFAULTS == {"job_age": "5m", "timeout": "30s", "disabled": False})
    check("JobInformationKeepCount defaults to 8192 (max 65536) and JobInformationKeepDuration defaults to 28 days (7.7.2 p. 452)",
          s.JOB_INFO_DIRECTIVE_DEFAULTS["JobInformationKeepCount"] == 8192 and
          s.JOB_INFO_DIRECTIVE_DEFAULTS["JobInformationKeepCount_max"] == 65536 and
          s.JOB_INFO_DIRECTIVE_DEFAULTS["JobInformationKeepDuration_days"] == 28 and
          raises(lambda: s.JobCache(70000)))
    jc = s.JobCache(); jc.add(1); jc.add(10); jc.mark_persistent(10); jc.expire_old()
    check("persistent keeps job 10 in the cache past normal expiry while non-persistent job 1 expires (7.7.2 p. 452)",
          10 in jc.jobs and 1 not in jc.jobs)
    jc.forget(10)
    check("forget removes a job from the cache immediately even if it is marked persistent (7.7.2 p. 452)",
          10 not in jc.jobs)
    check("setting prejob=yes on a health check when no WLM has enableprejob=yes triggers the manual's warning (7.8.2 p. 460)",
          "Prejob is selected, but no WLM has prejob" in s.prejob_check_status(True, False)["warning"])
    pj_fail = s.prejob_check_status(True, True, check_result="FAIL", drain_on_fail=True)
    check("a failing prejob check blocks the job (preventing Black Hole Node Syndrome), drains the node, and never auto-undrains (7.8.2 p. 459)",
          pj_fail["runs"] and not pj_fail["job_allowed"] and pj_fail["drained"] and not pj_fail["auto_undrain"])
    check("nodecustomizations in Slurm append KEY=VALUE (e.g. BcastExclude=/dev/shm) when enabled and remove it when disabled (7.11 pp. 465-466)",
          s.apply_node_customization("slurm", "BcastExclude", "/dev/shm", True) == "BcastExclude=/dev/shm" and
          s.apply_node_customization("slurm", "BcastExclude", "/dev/shm", False) == "")
    check("nodecustomizations in LSF write VALUE when enabled and replace with () when disabled or removed (7.11 p. 466)",
          s.apply_node_customization("lsf", "MAX_JOBS", "8", True) == "8" and
          s.apply_node_customization("lsf", "MAX_JOBS", "8", False) == "()")
    check("drain action chaining: draining with powerreset and undrain leaves both actions queued on the node (7.7.4 p. 456)",
          nd.drain(["powerreset", "undrain"]) is None and nd.actions == ["powerreset", "undrain"])

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
