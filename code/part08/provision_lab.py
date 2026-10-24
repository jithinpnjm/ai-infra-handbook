#!/usr/bin/env python3
"""Self-checking lab for chapter 8.4: node provisioning rules from Administrator Manual chapter 5, tested in bcm_provision.py."""
import sys
import bcm_provision as p

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except p.ProvError:
        return True

def main():
    # boot protocol
    b = p.boot_path()
    check("default: TFTP first stage, then HTTP for kernel and ramdisk on x86_64", b["first_stage"] == "tftp" and b["kernel_and_ramdisk"] == "http")
    check("tftp protocol keeps TFTP all the way", p.boot_path("tftp")["kernel_and_ramdisk"] == "tftp")
    check("HTTPS carries the manual's warning", "special hardware" in p.boot_path("https")["note"])
    check("ARMv8 boots over TFTP only, with a GRUB binary", p.boot_path("http", "arm64")["kernel_and_ramdisk"] == "tftp" and "grub" in p.boot_path("http", "arm64")["first_stage"])
    check("an unknown protocol is refused", raises(lambda: p.boot_path("ftp")))

    # install modes
    f = p.install_plan("FULL")
    check("FULL: no disk check, repartitions, full sync, wipes", not f["check_disks"] and f["repartition"] and f["sync"] == "full" and f["wipes"])
    a = p.install_plan("AUTO", partitions_ok=True)
    check("AUTO with healthy partitions: check, then incremental sync, no wipe", a["check_disks"] and a["sync"] == "sync" and not a["wipes"])
    a = p.install_plan("AUTO", partitions_ok=False)
    check("AUTO with a wrong partition size becomes a FULL install", a["sync"] == "full" and a["wipes"] and a["repartition"])
    m = p.install_plan("MAIN")
    check("MAIN: maintenance mode, no check, drive untouched", m["maintenance"] and not m["check_disks"] and m["sync"] == "none" and not m["wipes"])
    n = p.install_plan("NOSYNC", partitions_ok=True)
    check("NOSYNC with healthy partitions: no image sync", n["check_disks"] and n["sync"] == "none" and not n["wipes"])
    n = p.install_plan("NOSYNC", partitions_ok=False)
    check("NOSYNC is NOT data protection: bad partitions trigger a FULL sync (the manual's burn example)", n["sync"] == "full" and n["wipes"])
    s = p.install_plan("SKIP", partitions_ok=False)
    check("SKIP: no check and no sync, even with bad partitions", s["sync"] == "none" and not s["wipes"] and not s["check_disks"])
    check("an unknown install mode is refused", raises(lambda: p.install_plan("QUICK")))
    check("datanode makes a FULL install wait for confirmation", p.install_plan("FULL", datanode=True)["waits_for_confirmation"])
    check("datanode also guards the FULL install that AUTO falls back to", p.install_plan("AUTO", partitions_ok=False, datanode=True)["waits_for_confirmation"])
    check("datanode does not ask when AUTO only needs a sync", not p.install_plan("AUTO", partitions_ok=True, datanode=True)["waits_for_confirmation"])
    check("a confirmed FULL install proceeds", not p.install_plan("FULL", datanode=True, confirmed=True)["waits_for_confirmation"])
    check("datanode is Boolean: category OR node", p.datanode_effective(True, False) and p.datanode_effective(False, True) and not p.datanode_effective(False, False))

    # identification truth table
    table = {1: (False, True, True, None, None, "automatic"), 2: (False, True, False, None, None, "manual"), 3: (False, False, False, None, None, "manual"),
             4: (True, True, True, True, True, "automatic"), 5: (True, True, True, True, False, "manual"), 6: (True, False, False, True, None, "manual"),
             7: (True, True, False, False, None, "automatic")}
    for sc, (known, port, cfg, macport, same, want) in table.items():
        got = p.identify(known, port, cfg, macport, same)
        check(f"identification scenario {sc}: {want}", got == (sc, want), got)
    check("a known node with no switch ports in play is automatic (not in the manual's table)", p.identify(True, False, False, False) == (0, "automatic"))

    # newnodes
    macs = ["...A", "...B", "...C"]
    check("newnodes assigns names in order of arrival", p.newnodes_assign(macs, ["node023", "node024", "node025"]) == {"...A": "node023", "...B": "node024", "...C": "node025"})
    check("newnodes -o 1 skips the first arrival (the manual's example)", p.newnodes_assign(macs, ["node024", "node025"], offset=1) == {"...B": "node024", "...C": "node025"})
    check("newnodes fails when a name is taken, unless forced", raises(lambda: p.newnodes_assign(macs, ["node001"], taken={"node001"})) and p.newnodes_assign(macs, ["node001"], taken={"node001"}, force=True) == {"...A": "node001"})
    check("newnodes refuses more names than waiting nodes", raises(lambda: p.newnodes_assign(macs, ["a", "b", "c", "d"])))

    # node states
    ns = p.NodeState("DOWN")
    for ev in ("power_on", "installer_started", "handover", "cmdaemon_connected"):
        ns.event(ev)
    check("a healthy boot goes BOOTING, INSTALLING, INSTALLER_CALLINGINIT, UP", str(ns) == "UP")
    check("an impossible transition is refused (UP cannot go to INSTALLING)", raises(lambda: ns.event("installer_started")))
    ns.close()
    check("close appends /CLOSED and the node keeps running", str(ns) == "UP/CLOSED" and p.workload_continues(True))
    ns.event("cmdaemon_lost")
    check("a closed node that goes down is DOWN/CLOSED, not DOWN", str(ns) == "DOWN/CLOSED")
    for ev in ("power_on", "installer_started", "handover", "cmdaemon_connected"):
        ns.event(ev)
    check("a closed node stays closed through a whole reboot", str(ns) == "UP/CLOSED")
    ns.open()
    check("open clears CLOSED; OPEN is never printed", str(ns) == "UP")
    check("open on a node that is not closed is refused", raises(ns.open))
    ns.mute()
    check("mute leaves the state alone and adds a note", str(ns) == "UP, muted")
    ns.unmute()
    x = p.NodeState("DOWN"); x.event("power_on"); x.event("installer_started"); x.event("installer_error")
    check("an unrecoverable installer problem ends in INSTALLER_FAILED", str(x) == "INSTALLER_FAILED")
    y = p.NodeState("DOWN"); y.event("power_on"); y.event("installer_started"); y.event("reboot_for_kernel"); y.event("reboot_too_slow")
    check("a kernel reboot that takes too long ends in INSTALLER_FAILED", str(y) == "INSTALLER_FAILED")
    z = p.NodeState("DOWN"); z.event("power_on"); z.event("installer_started"); z.event("installer_ping_lost")
    check("an installer node that stops answering pings is INSTALLER_UNREACHABLE", str(z) == "INSTALLER_UNREACHABLE")

    # scheduler
    head = p.Provisioner("head", slots=2)
    r1 = p.Provisioner("prov-rack-a", slots=3, nodegroups={"rack-a"})
    sch = p.Scheduler([head, r1])
    check("a node in a listed group is served only by a provisioner that lists the group", sch.request("a1", ["rack-a"], "default-image")[0] == "prov-rack-a")
    check("a node in no group is served only by a provisioner with no nodegroups", sch.request("x1", [], "default-image")[0] == "head")
    sch2 = p.Scheduler([p.Provisioner("p1"), p.Provisioner("p2")])
    got = [sch2.request(f"n{i}", [], "default-image")[0] for i in range(4)]
    check("work goes to the provisioner with the fewest started tasks (alternates p1, p2)", got == ["p1", "p2", "p1", "p2"], got)
    sch3 = p.Scheduler([p.Provisioner("p1", slots=1)])
    sch3.request("n1", [], "default-image")
    res = sch3.request("n2", [], "default-image")
    check("when all slots are busy the request is deferred", res[0] is None and "deferred" in res[1])
    done = sch3.finish("n1")
    check("when a task finishes, deferred requests are tried again", done and done[0][1][0] == "p1")
    sch4 = p.Scheduler([p.Provisioner("p1")], locked=["default-image"])
    check("a locked image defers the request", "locked" in sch4.request("n1", [], "default-image")[1])
    sch5 = p.Scheduler([p.Provisioner("p1", slots=10)], max_threads=2)
    sch5.request("a", [], "default-image"); sch5.request("b", [], "default-image")
    check("MaxNumberOfProvisioningThreads limits the whole cluster", "limit" in sch5.request("c", [], "default-image")[1])
    d = p.Provisioner("p1", draining=True); d2 = p.Provisioner("p2")
    check("a draining provisioner takes no new requests", p.Scheduler([d, d2]).request("n", [], "default-image")[0] == "p2")
    stale = p.Provisioner("p1", uptodate=set())
    check("a provisioner without the up-to-date image is skipped", p.Scheduler([stale]).request("n", [], "default-image")[0] is None)
    sch6 = p.Scheduler([p.Provisioner("p1")])
    results = [sch6.failed_transfer("n1") for _ in range(6)]
    check("a failed transfer is retried 5 times and then fails", results == ["retry"] * 5 + ["failed"], results)
    check("a provisioner that lost connectivity keeps its requests for 180 s", p.lost_connectivity_outcome(180) == "still allocated" and p.lost_connectivity_outcome(181) == "failed")
    check("the default slot count is 10", p.Provisioner("x").slots == 10)

    # update timeout
    check("a provisioner update is triggered only if the last one is older than 300 s", p.provisioner_update(301) and not p.provisioner_update(299))
    check("a timeout of 0 disables it", not p.provisioner_update(10000, timeout=0))
    check("an image changed 2 minutes ago, last update 10 minutes ago: update triggered, node gets it", p.node_gets_new_image(120, 600))
    check("the 5-minute trap: image changed 60 s ago, last provisioner update 200 s ago (before the change, younger than 300 s) -> not picked up", p.node_gets_new_image(60, 200) is False)
    check("running updateprovisioners first fixes the trap", p.node_gets_new_image(60, 200, ran_updateprovisioners=True))

    # kernel modules
    check("kernel modules: node list replaces the category list completely", p.effective_kernel_modules(["a", "b"], ["c"], ["d"]) == (["d"], "node"))
    check("kernel modules: category replaces the image list (no merge)", p.effective_kernel_modules(["a", "b"], ["c"]) == (["c"], "category"))
    check("kernel modules: the image list applies when nothing is set below", p.effective_kernel_modules(["a", "b"]) == (["a", "b"], "image"))
    check("a kernel changed by yum/apt needs createramdisk", p.ramdisk_needs_regeneration(True) and not p.ramdisk_needs_regeneration(False))

    # standalone boot
    check("standalone boot needs all four things", len(p.standalone_boot_problems(False, False, False, "BOOTIF")) == 4 and p.standalone_boot_problems(True, True, True, "eth0") == [])

    # exclude lists
    check("update uses excludelistupdate (sync, image to running node)", p.EXCLUDE_LIST["update"][0] == "excludelistupdate" and p.EXCLUDE_LIST["update"][1] == "sync")
    check("grab to a NEW image uses excludelistgrabnew (full); grab to the existing image uses excludelistgrab (sync)", p.EXCLUDE_LIST["grabnew"][1] == "full" and p.EXCLUDE_LIST["grab"][1] == "sync")
    image = {"/etc/a": "img-a", "/etc/b": "img-b", "/opt/new": "img-new", "/data/x": "img-x"}
    node = {"/etc/a": "node-a", "/etc/b": "node-b-changed", "/etc/extra": "only-on-node", "/data/x": "node-x", "/data/y": "node-y"}
    out = p.sync_update(image, node, keep=["/data"], no_new_files=["/opt"])
    check("a path on the first list and on the node stays as it is on the node", out["/data/x"] == "node-x" and out["/data/y"] == "node-y")
    check("a path on neither list is overwritten from the image", out["/etc/a"] == "img-a" and out["/etc/b"] == "img-b")
    check("a node-only file not on any list is lost (the manual: 'not protected from deletion')", "/etc/extra" not in out)
    check("a path on the no-new-files list that is missing on the node is NOT copied", "/opt/new" not in out)
    image2 = dict(image, **{"/data/new": "img-new-data"})
    out2 = p.sync_update(image2, node, keep=["/data"], no_new_files=[])
    check("a path on the first list that is missing on the node IS copied from the image", out2["/data/new"] == "img-new-data")
    out3 = p.sync_update({"/etc/a": "i"}, {"/etc/a": "n", "/mnt/nfs/f": "precious", "/mnt/auto/f": "precious2"}, keep=[], mounts={"/mnt/nfs": "nfs"})
    check("a static NFS mount is skipped automatically", out3["/mnt/nfs/f"] == "precious")
    check("an autofs mount is NOT detected: without an exclude entry it is wiped (the manual's warning)", "/mnt/auto/f" not in out3)

    # Gap pass: 5.3.3 IB provisioning, 5.3.4 VLAN provisioning, 9.6 cm-create-image, 9.7 cm-image & Table 9.1
    check("InfiniBand provisioning passes when IB modules are in ramdisk, provisioninginterface=ib0, and BOOTIF is not duplicated (5.3.3)",
          p.ib_provisioning_problems(["mlx4_ib", "ib_ipoib", "ib_umad"], "ib0", ["eth0"], bootif_underlying="ib0") == [])
    check("InfiniBand provisioning fails if BOOTIF=ib0 is also configured as a separate ib0 interface on the node (5.3.3 p. 258)",
          any("BOOTIF" in x for x in p.ib_provisioning_problems(["ib_ipoib"], "ib0", ["ib0"], bootif_underlying="ib0")))
    check("VLAN provisioning requires VLAN iface, 8021q module in image, BIOS VLANID, and VLANID= in kernelparameters (5.3.4)",
          p.vlan_provisioning_problems(True, ["8021q"], True, "quiet VLANID=89") == [] and
          len(p.vlan_provisioning_problems(False, [], False, "")) == 4)
    check("cm-create-image refuses an existing image name unless --updateimage or -f is set, and requires --imagedir to exist (9.6.2)",
          len(p.cm_create_image_check("rocky9-image", existing_images=["rocky9-image"], imagedir_exists=False)) == 2 and
          p.cm_create_image_check("rocky9-image", existing_images=["rocky9-image"], updateimage=True) == [])
    check("cm-create-image validates the 7 --dgx-type values (dgx_a100, dgx_h100, dgx_h200, dgx_b200, dgx_gb200, dgx_b300, dgx_gb300) (9.6.2 p. 548)",
          len(p.VALID_DGX_TYPES) == 7 and p.cm_create_image_check("dgx", dgx_type="dgx_gb300") == [] and
          p.cm_create_image_check("dgx", dgx_type="dgx_v100") != [])
    check("prior to BCM 11.30.0 on B200/GB200, keeping doca.list in a DGX image makes cm-kubernetes-setup fail at ~22% (9.6.2 p. 550)",
          any("22%" in x for x in p.cm_create_image_check("dgx", dgx_type="dgx_gb200", bcm_version=(11, 25, 8), doca_list_present=True)) and
          p.cm_create_image_check("dgx", dgx_type="dgx_gb200", bcm_version=(11, 30, 0), doca_list_present=True) == [])
    check("Table 9.1 multi-distro/multi-arch: Ubuntu/RHEL support x86_64 and aarch64; SLES15 supports x86_64 only (9.7 p. 554)",
          p.cm_image_supported("ubuntu2204", "x86_64", "rhel9", "aarch64") and
          p.cm_image_supported("ubuntu2204", "aarch64", "sles15", "x86_64") and
          not p.cm_image_supported("ubuntu2204", "x86_64", "sles15", "aarch64"))
    art_u = p.cm_image_create_all_artifacts("ubuntu2404", "x86_64")
    check("cm-image create all builds default-image-<distro>-<arch>, node-installer, /cm/shared-<distro>-<arch> and default-<distro>-<arch> category (9.7.2)",
          art_u["software_image"] == "default-image-ubuntu2404-x86_64" and art_u["category"] == "default-ubuntu2404-x86_64" and
          art_u["recommended_nextinstallmode"] == "FULL")
    art_arm = p.cm_image_create_all_artifacts("rhel8", "aarch64")
    check("ARMv8 (aarch64) images created with cm-image require bootloaderprotocol=tftp and kerneloutputconsole=ttyAMA0 (9.7.3 p. 562)",
          art_arm["arm_settings"] == {"bootloaderprotocol": "tftp", "kerneloutputconsole": "ttyAMA0"})
    nai = p.nodearchosinfo_status("x86_64", "rocky8", "10:00", "x86_64", "ubuntu2404", previous_ts="10:00")
    check("nodearchosinfo flags reported/configured OS mismatch and an unchanged timestamp after a failed reboot (9.7 p. 555)",
          nai["os_mismatch_warning"] and nai["stale_after_reboot"])

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
