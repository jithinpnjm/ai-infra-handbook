#!/usr/bin/env python3
"""Self-checking lab for chapter 8.3: rules from Administrator Manual chapter 3, as tested by bcm_netconf.py."""
import sys
import bcm_netconf as n

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn, exc=n.ConfError):
    try:
        fn(); return False
    except exc:
        return True

def main():
    # networks
    inet = n.Network("internalnet", "10.141.0.0", 16, dyn_start="10.141.128.0", dyn_end="10.141.143.255")
    check("internalnet defaults from the manual build (10.141.0.0/16, dynamic range 10.141.128.0-10.141.143.255)", str(inet.net) == "10.141.0.0/16")
    check("a node address inside the DHCP dynamic range is flagged", n.Network.check_static(inet, ["10.141.0.1", "10.141.130.5"]) == [("10.141.130.5", "inside the dynamic DHCP range")])
    check("a node address outside the network is flagged", n.Network.check_static(inet, ["10.142.0.1"])[0][1] == "outside network")
    check("a gateway outside the network is refused", raises(lambda: n.Network("x", "10.141.0.0", 16, gateway="192.168.1.1")))
    check("a dynamic range that runs backwards is refused", raises(lambda: n.Network("x", "10.141.0.0", 16, dyn_start="10.141.9.0", dyn_end="10.141.1.0")))
    check("a network base address with host bits is refused (base address must be the network address)", raises(lambda: n.Network("x", "10.141.0.1", 16), ValueError))
    s = n.Network("sipcalc", "192.168.0.0", 28)
    check("sipcalc example: 192.168.0.1/28 has 16 addresses, usable .1 to .14", s.net.num_addresses == 16 and str(list(s.net.hosts())[0]) == "192.168.0.1" and str(list(s.net.hosts())[-1]) == "192.168.0.14")
    check("layer3 default is /31 and /30 is allowed (DataDirect switches)", inet.layer3_prefix() == 31 and inet.layer3_prefix(30) == 30 and raises(lambda: inet.layer3_prefix(29)))

    # default gateway order
    check("no gateway anywhere: nodes get the head node alias 10.141.255.254", n.default_gateway() == ("10.141.255.254", "head node (DHCP default)"))
    check("network gateway used when set", n.default_gateway(network_gateway="10.141.0.254") == ("10.141.0.254", "network"))
    check("category gateway overrides the network gateway", n.default_gateway(category_gateway="10.141.9.1", network_gateway="10.141.0.254") == ("10.141.9.1", "category"))
    check("category gateway of 0.0.0.0 counts as unset", n.default_gateway(category_gateway="0.0.0.0", network_gateway="10.141.0.254")[1] == "network")

    # search domains
    used, dropped = n.search_domains("cm.cluster", ["eth.cluster", "ib.cluster"], ["cat.example.com"], ["example.com:1", "domain.test:6"])
    check("search domains: indexed ones sort first by index (example.com:1 then domain.test:6)", used[:2] == ["example.com", "domain.test"])
    check("only the 6 lowest are written; the rest are dropped", len(used) == 6 and len(dropped) == 0, (used, dropped))
    used, dropped = n.search_domains("cm.cluster", [f"n{i}.cluster" for i in range(5)], ["c.example.com"], ["p.example.com"])
    check("eight sources: six written, two dropped (older glibc limit)", len(used) == 6 and len(dropped) == 2, (used, dropped))

    # interface priority and ipaddresses --check
    check("name resolution prefers a bridge (80) over a physical interface (60)", n.name_resolution_interface([{"name": "eth0", "type": "physical"}, {"name": "br0", "type": "bridge"}]) == "br0")
    check("onnetworkpriority can override the type default", n.name_resolution_interface([{"name": "eth0", "type": "physical", "onnetworkpriority": 100}, {"name": "br0", "type": "bridge"}]) == "eth0")
    rows, code = n.ipaddresses_check({"eth0": "10.141.0.1", "eth1": "10.141.128.1", "eth2": "10.141.255.2"}, {"eth0": "10.141.0.1", "eth1": "10.141.128.99", "eth3": "10.2.0.5"})
    st = {r[0]: r[3] for r in rows}
    check("ipaddresses --check reproduces the manual's four states", st == {"eth0": "OK", "eth1": "Mismatch", "eth2": "Not detected", "eth3": "Not configured"}, st)
    check("exit code is non-zero when any interface is not OK", code == 1 and n.ipaddresses_check({"eth0": "1.1.1.1"}, {"eth0": "1.1.1.1"})[1] == 0)
    check("a DHCP interface with a detected address is OK", n.ipaddresses_check({"eth0": "dhcp"}, {"eth0": "10.0.0.7"})[1] == 0)
    check("cm-iperf pairs: 4 nodes -> 6 pairs (the manual's example)", n.iperf_pairs(4) == 6)
    check("cm-iperf default run for 1000 nodes takes about 2 months (manual) -> about 58 days", 55 < n.iperf_days(1000) < 60, n.iperf_days(1000))
    check("with 64 parallel threads the same run is under a day", n.iperf_days(1000, parallel=64) < 1)

    # interfaces
    ok = [{"name": "eth0", "type": "physical", "ip": "10.141.0.1", "network": "internalnet", "provisioning": True},
          {"name": "eth1", "type": "physical"}, {"name": "eth2", "type": "physical"},
          {"name": "bond0", "type": "bond", "mode": 1, "options": "miimon=100", "members": ["eth1", "eth2"], "ip": "10.141.128.1", "network": "internalnet"}]
    check("a bond of two spare NICs with miimon passes", n.validate_interfaces(ok) == [], n.validate_interfaces(ok))
    bad = [dict(i) for i in ok]; bad[1]["provisioning"] = True
    check("the provisioning interface cannot be a bond member", any("provisioning interface" in p for p in n.validate_interfaces(bad)))
    bad = [dict(i) for i in ok]; bad[3]["options"] = "mode=4 miimon=100"
    check("setting mode as an option is refused (use the mode property)", any("mode property" in p for p in n.validate_interfaces(bad)))
    bad = [dict(i) for i in ok]; bad[3]["options"] = ""
    check("active-backup without miimon is flagged (miimon is off by default)", any("miimon" in p for p in n.validate_interfaces(bad)))
    bad = [dict(i) for i in ok]; bad[3]["mode"] = 9
    check("bonding mode 9 does not exist", any("not one of 0-6" in p for p in n.validate_interfaces(bad)))
    check("the seven modes are named as in the manual", n.BOND_MODES[4] == "802.3ad" and len(n.BOND_MODES) == 7)
    br = [{"name": "eth1", "type": "physical", "ip": "10.141.9.9", "network": "internalnet"}, {"name": "br0", "type": "bridge", "members": ["eth1"]}]
    check("bridge members must have empty IP and network", any("empty IP" in p for p in n.validate_interfaces(br)))
    check("bridge names must look like br0", any("br<number>" in p for p in n.validate_interfaces([{"name": "mybridge", "type": "bridge", "members": []}])))
    check("a VLAN interface without a network is flagged", any("needs a network" in p for p in n.validate_interfaces([{"name": "BOOTIF.1", "type": "vlan"}])))

    # disk, mounts, image files
    check("disk layout: node value wins over category", n.disksetup_for("<xml node>", "<xml cat>") == ("<xml node>", "node"))
    check("disk layout: after clear on the node the category layout applies", n.disksetup_for(None, "<xml cat>") == ("<xml cat>", "category"))
    m = n.merged_mounts({"/home": "basecm11:/home", "/cm/shared": "master:/cm/shared"}, {"/home/examples": "basecm11:/cm/shared/examples"})
    check("a node lists category mounts and its own", set(m) == {"/home", "/cm/shared", "/home/examples"} and m["/home"][1] == "category" and m["/home/examples"][1] == "node")
    check("a category mount cannot be removed from the node", n.can_remove_mount(m, "/home")[0] is False and n.can_remove_mount(m, "/home/examples")[0] is True)
    present = {"/cm/images/default-image/cm/conf/category/gpu/etc/motd", "/cm/images/default-image/cm/conf/node/node001/etc/motd"}
    check("image file: node-level file beats category-level", n.image_file_source("default-image", "/etc/motd", node="node001", category="gpu", present=present).endswith("/node/node001/etc/motd"))
    check("image file: other nodes in the category get the category file", n.image_file_source("default-image", "/etc/motd", node="node002", category="gpu", present=present).endswith("/category/gpu/etc/motd"))
    check("image file: MAC address form uses dashes", n.image_file_source("default-image", "/a", mac="00:AA:BB:CC:DD:EE", present={"/cm/images/default-image/cm/conf/node/00-aa-bb-cc-dd-ee/a"}) is not None)
    check("image file: nothing placed gives None", n.image_file_source("default-image", "/etc/none", node="node001", category="gpu", present=present) is None)

    # racks
    r = n.Rack("rack2")
    check("a rack is 42U by default", r.height == 42)
    r.place("node001", 1); r.place("chassis1", 2, height=6)
    check("a 6U chassis at position 2 occupies U2-U7", all(r.slots.get(u) == "chassis1" for u in range(2, 8)))
    check("overlapping a used slot is refused without --force", raises(lambda: r.place("node002", 5)))
    r.place("node002", 5, force=True)
    check("--force allows the overlap", r.slots[5] == "node002")
    check("a device that does not fit is refused", raises(lambda: n.Rack("tiny", 4).place("big", 3, height=4)))
    r2 = n.Rack("rack3"); r2.place("pdu", 2)
    r2.add_positions([f"node{i:03d}" for i in range(1, 5)], start=1)
    check("addrackposition fills the first free slots, skipping used ones", [r2.slots[u] for u in (1, 3, 4, 5)] == ["node001", "node002", "node003", "node004"], r2.slots)

    # GPUs
    check("GPU range 'all' and '*' mean every GPU", n.parse_gpu_range("all", 8) == n.parse_gpu_range("*", 8) == list(range(8)))
    check("GPU ranges: '3', '0-2', '1,3-5'", n.parse_gpu_range("3", 8) == [3] and n.parse_gpu_range("0-2", 8) == [0, 1, 2] and n.parse_gpu_range("1,3-5", 8) == [1, 3, 4, 5])
    check("a GPU slot that does not exist is refused", raises(lambda: n.parse_gpu_range("0-9", 8)))
    cat = [("all", {"eccmode": "enabled", "powerlimit": "max"})]
    node = [("1", {"powerlimit": 300})]
    check("GPU setting: node overrides category for GPU 1", n.effective_gpu_setting(cat, node, 1, "powerlimit") == (300, "node"))
    check("GPU setting: other GPUs use the category", n.effective_gpu_setting(cat, node, 0, "powerlimit") == ("max", "category"))
    check("GPU setting: unset means hardware default", n.effective_gpu_setting(cat, node, 0, "computemode") == (None, "hardware default"))
    check("power limit must be min, max, default or between min and max", n.power_limit_ok("max", 100, 400) and n.power_limit_ok(300, 100, 400) and not n.power_limit_ok(500, 100, 400))

    check("file-max rule of thumb: 128 GB of memory -> 1,280,000", n.file_max_rule_of_thumb(128) == 1280000)

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
