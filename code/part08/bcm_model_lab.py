#!/usr/bin/env python3
"""Self-checking lab for chapter 8.1: does my understanding of the BCM object model match the manual?
Every check names the manual section. This tests the MODEL (my reading of the manual), not a real BCM."""
import sys
from bcm_model import Cluster, BcmError, CATEGORY_PRIORITY, NODE_PRIORITY, cmdaemon_port_config, cm_scale_repurpose

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def raises(fn):
    try:
        fn()
    except BcmError as e:
        return str(e)
    return None


def main():
    c = Cluster()
    c.add_category("dgx", softwareimage="default-image", values={"kernelparameters": "iommu=pt"}, flags={"datanode": False})
    c.add_category("login", softwareimage="default-image")
    c.add_node("node001"); c.add_node("dgx-01", "dgx"); c.add_node("dgx-02", "dgx")

    check("a new node lands in the partition's default category (2.1.3)", c.nodes["node001"].category == "default")
    c.move_node("node001", "login")
    check("a node is in exactly one category: moving it replaces the old one (2.1.3)", c.nodes["node001"].category == "login")
    check("several categories can use the same software image (2.1.3)", c.image_of("node001") == c.image_of("dgx-01") == "default-image")
    c.partition["defaultcategory"] = "dgx"
    c.add_node("new-node")
    check("changing defaultcategory in the partition changes where new nodes land (2.1.3)", c.nodes["new-node"].category == "dgx")

    v, src = c.value("dgx-01", "kernelparameters")
    check("a non-Boolean value is inherited from the category (2.1.3)", (v, src) == ("iommu=pt", "category dgx"), (v, src))
    c.nodes["dgx-01"].values["kernelparameters"] = "iommu=pt numa_balancing=0"
    v, src = c.value("dgx-01", "kernelparameters")
    check("a value set on the node overrules the category value (2.1.3)", v.endswith("numa_balancing=0") and src == "node dgx-01", (v, src))
    check("the other node in the category still inherits", c.value("dgx-02", "kernelparameters")[1] == "category dgx")
    check("a setting nobody set falls back to the built-in default (newnodeinstallmode is FULL)", c.value("dgx-02", "newnodeinstallmode") == ("FULL", "built-in default"))

    c.categories["dgx"].flags["datanode"] = True
    c.nodes["dgx-01"].flags["datanode"] = False
    res, nv, cv = c.flag("dgx-01", "datanode")
    check("Booleans are NOT inherited: category OR node, so a node cannot switch off a category 'true' (2.1.3)", res is True and nv is False and cv is True, (res, nv, cv))
    c.categories["dgx"].flags["datanode"] = False
    c.nodes["dgx-01"].flags["datanode"] = True
    check("...and a node 'true' wins over a category 'false' (OR)", c.flag("dgx-01", "datanode")[0] is True)
    check("both false gives false", c.flag("dgx-02", "datanode")[0] is False)

    msg = raises(lambda: c.assign_role("node", "dgx-01", "mycustomrole"))
    check("custom roles cannot be created, only existing roles assigned (2.1.5)", msg and "custom roles cannot be created" in msg, msg)
    c.assign_role("category", "dgx", "slurmclient", queues="gpu", gpus=8)
    r = c.roles_of("dgx-01")["slurmclient"]
    check("a role assigned to a category applies to its nodes with priority 250 (2.1.5)", r.priority == CATEGORY_PRIORITY and r.params["gpus"] == 8 and r.source == "category dgx", r)
    c.assign_role("node", "dgx-01", "slurmclient", queues="gpu,debug", gpus=4)
    r = c.roles_of("dgx-01")["slurmclient"]
    check("the same role on the node (priority 750) overrides the category's parameters (2.1.5)", r.priority == NODE_PRIORITY and r.params["gpus"] == 4, r)
    check("the other node in the category keeps the category's parameters", c.roles_of("dgx-02")["slurmclient"].params["gpus"] == 8)

    c.add_overlay("slurm-client-ov", roles={"slurmclient": {"queues": "overlay", "gpus": 8}}, nodes={"dgx-02"})
    r = c.roles_of("dgx-02")["slurmclient"]
    check("a configuration overlay (default priority 500) beats the category (250) (2.1.6)", r.priority == 500 and r.source == "overlay slurm-client-ov", r)
    r = c.roles_of("dgx-01")["slurmclient"]
    check("a node-level role (750) still beats an overlay at the default priority (2.1.6)", r.source == "node dgx-01")
    c.add_overlay("high", priority=900, roles={"slurmclient": {"queues": "high"}}, nodes={"dgx-02"})
    check("an overlay with a higher priority (900) wins over the default overlay (500) (2.1.6)", c.roles_of("dgx-02")["slurmclient"].source == "overlay high")
    c.assign_role("node", "dgx-02", "slurmclient", queues="node", gpus=2)
    check("my reading: an overlay above 750 would outrank a node-level role (the numbers say so, the manual gives no example)", c.roles_of("dgx-02")["slurmclient"].source == "overlay high")
    c.nodes["dgx-02"].roles.clear()
    c.overlays["high"].priority = -1
    check("an overlay with priority -1 is ignored (2.1.6)", c.roles_of("dgx-02")["slurmclient"].source == "overlay slurm-client-ov")
    c.add_overlay("wide", priority=100, roles={"login": {}}, categories={"dgx"})
    check("an overlay assigned to a category applies to every node in it, with its own priority", c.roles_of("dgx-02")["login"].priority == 100 and c.roles_of("dgx-01")["login"].source == "overlay wide")

    check("overlay priority 250 is forbidden (2.1.6)", raises(lambda: c.add_overlay("bad250", priority=250)))
    check("overlay priority 750 is forbidden (2.1.6)", raises(lambda: c.add_overlay("bad750", priority=750)))
    check("overlay priority above 1000 is refused (2.1.6)", raises(lambda: c.add_overlay("bad2000", priority=2000)))
    check("overlay priority -1 is allowed (ignored overlay) and 0 and 1000 are allowed", not raises(lambda: c.add_overlay("m1", priority=-1)) and not raises(lambda: c.add_overlay("z", priority=0)) and not raises(lambda: c.add_overlay("t", priority=1000)))

    c.add_to_group("rack5", "dgx-01", "dgx-02"); c.add_to_group("brokenhardware", "dgx-02")
    in_groups = [g for g, m in c.groups.items() if "dgx-02" in m]
    check("a node may be in many node groups at once (2.1.4)", sorted(in_groups) == ["brokenhardware", "rack5"], in_groups)
    check("a group holds member names only: it carries no configuration (2.1.4)", all(isinstance(m, set) for m in c.groups.values()))

    c.nodes["dgx-01"].state = "DOWN"; c.nodes["dgx-02"].state = "CLOSED(DOWN)"
    check("DOWN is a failure but CLOSED(DOWN) is a deliberate shutdown, not a failure (2.1.1)", c.failures() == ["dgx-01"], c.failures())
    check("CLOSED devices are mostly ignored by monitoring but state is still tracked (2.1.1)", Cluster.state_meaning("CLOSED(DOWN)") == ("down", "mostly ignored", "tracked"))
    check("UP and DOWN devices are monitored (2.1.1)", Cluster.state_meaning("UP")[1] == "monitored" and Cluster.state_meaning("DOWN")[1] == "monitored")

    # Appendix C (pp. 905-907) & Chapter 8.1 (pp. 467-468) checks added in gap pass
    check("CMDaemon default ports are Port=8080 (HTTP, init only) and SSLPort=8081 (HTTPS, management) with SSLPortOnly=no (App. C)",
          cmdaemon_port_config()["problems"] == [] and cmdaemon_port_config()["http_port"] == 8080 and cmdaemon_port_config()["https_port"] == 8081)
    check("SSLPortOnly=yes is forbidden when bootloaderprotocol is HTTP (App. C p. 906)",
          any("SSLPortOnly" in p for p in cmdaemon_port_config(ssl_port_only=True, bootloaderprotocol="HTTP")["problems"]))
    check("SSLPortOnly=yes is allowed when bootloaderprotocol is TFTP (App. C p. 906)",
          cmdaemon_port_config(ssl_port_only=True, bootloaderprotocol="TFTP")["problems"] == [])
    check("changing CMDaemon ports with cm-cmd-ports requires a manual firewall update (App. C p. 906)",
          any("firewall" in p for p in cmdaemon_port_config(https_port=8082, firewall_updated=False)["problems"]))
    c.add_overlay("k8s-worker", roles={"kubernetesnode": {}}, nodes={"dgx-01"})
    c.add_overlay("slurm-worker", roles={"slurmclient": {"gpus": 8}}, nodes=set())
    rep = cm_scale_repurpose(c, "dgx-01", "k8s-worker", "slurm-worker")
    check("Auto Scaler (cm-scale) repurposes a node between K8s and Slurm by switching overlays without changing its category (8.1.1)",
          rep["category_unchanged"] and "dgx-01" in c.overlays["slurm-worker"].nodes and "dgx-01" not in c.overlays["k8s-worker"].nodes)

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
