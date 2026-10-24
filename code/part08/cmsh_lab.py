#!/usr/bin/env python3
"""Self-checking lab for chapter 8.5: cmsh behaviour from Administrator Manual section 2.5, tested in cmsh_sim.py."""
import sys
import cmsh_sim as c

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except c.CmshError:
        return True

def main():
    E = c.expand_nodelist
    check("adhoc list with commas", E("node001,node003,node005,node006") == ["node001", "node003", "node005", "node006"])
    check("adhoc list with spaces", E("node001 node003") == ["node001", "node003"])
    check("sequential with two dots", E("node001..node004") == ["node001", "node002", "node003", "node004"])
    check("sequential with brackets is the same", E("node00[1-4]") == E("node001..node004"))
    check("short right-hand side: node001..024 means node001 to node024", E("node001..024")[-1] == "node024" and len(E("node001..024")) == 24)
    check("extended expansion node[001-002]s[001-005] gives 10 names", len(E("node[001-002]s[001-005]")) == 10 and E("node[001-002]s[001-005]")[:2] == ["node001s001", "node001s002"])
    check("rack-based r[1-2]n[01-03]", E("r[1-2]n[01-03]") == ["r1n01", "r1n02", "r1n03", "r2n01", "r2n02", "r2n03"])
    check("rack-based rack[1-2]node0[1-3]", E("rack[1-2]node0[1-3]")[-1] == "rack2node03" and len(E("rack[1-2]node0[1-3]")) == 6)
    check("exclusion: node001..node005,-node002..node003", E("node001..node005,-node002..node003") == ["node001", "node004", "node005"])
    check("stride: node00[1..7:2]", E("node00[1..7:2]") == ["node001", "node003", "node005", "node007"])
    check("mixed list r1n001..r1n003,r2n003", E("r1n001..r1n003,r2n003") == ["r1n001", "r1n002", "r1n003", "r2n003"])
    check("mixed list r2n003,r[3-5]n0[01-03] has 10 names", len(E("r2n003,r[3-5]n0[01-03]")) == 10 and E("r2n003,r[3-5]n0[01-03]")[1] == "r3n001")
    e = E("node[001-100],-node[004-100:4]")
    check("every node except every fourth: 100 - 25 = 75", len(e) == 75 and "node004" not in e and "node005" in e and "node100" not in e)
    check("comma inside brackets: test0[1,2,5-7]", E("test0[1,2,5-7]") == ["test01", "test02", "test05", "test06", "test07"])
    check("a ^file path reads a list from a file", E("^/x", read_file=lambda p: "node001..node002,node009") == ["node001", "node002", "node009"])
    check("brackets and two dots in one argument are refused", raises(lambda: E("node[1-3]..node5")))
    check("duplicates are dropped, order kept", E("node002,node001,node002") == ["node002", "node001"])
    names = E("node001..node003,node007")
    check("groupingsyntax auto/dot output: node001..node003,node007", c.format_nodelist(names) == "node001..node003,node007")
    check("groupingsyntax bracket output: node[001-003],node007", c.format_nodelist(names, "bracket") == "node[001-003],node007")

    # rename
    check("rename node001..node003 test -> test1, test2, test3 (numbering restarts at 1)", [t for _, t in c.rename_targets(E("node001..node003"), "test")] == ["test1", "test2", "test3"])
    check("rename ten nodes pads to two digits: test01 .. test10", [t for _, t in c.rename_targets(E("node[001-010]"), "test")][::9] == ["test01", "test10"])
    check("rename with test%04d", [t for _, t in c.rename_targets(E("node[001-003]"), "test%04d")] == ["test0001", "test0002", "test0003"])
    check("rename exact mapping test0[1,2,5-7]", [t for _, t in c.rename_targets(E("node[001-005]"), "test0[1,2,5-7]")] == ["test01", "test02", "test05", "test06", "test07"])
    check("rename to people names", c.rename_targets(E("node[001-004]"), "alice,bob,charlie,dave")[2] == ("node003", "charlie"))
    check("rename with mismatched sizes is refused", raises(lambda: c.rename_targets(E("node[001-004]"), "a,b")))
    pairs = c.rename_targets(E("node[001-100:2]"), "left[001-050]")
    check("rename every second node: node001->left001, node003->left002, node099->left050", pairs[0] == ("node001", "left001") and pairs[1] == ("node003", "left002") and pairs[-1] == ("node099", "left050"))

    # format
    check("format width [10-14] fits the text between 10 and 14", c.column_width("[10-14]", ["apc01", "node001"]) == 10 and c.column_width("[10-14]", ["largenamefornode"]) == 14)
    check("a text longer than the maximum is cut with + as the last character (largenamefornode -> largenameforn+)", c.fit("largenamefornode", 14) == "largenameforn+")
    check("width 0 means the widest entry", c.column_width("0", ["a", "abcdef"]) == 6)
    check("a fixed width is a fixed width", c.column_width("14", ["a"]) == 14)

    # session: the manual's add / commit / remove example
    s = c.Session("mycluster")
    s.enter("device")
    steps = s.script("add physicalnode node100 10.141.0.100; commit; category add test-category; commit; remove test-category; commit")
    prompts = [p for _, p in steps]
    check("add drops into the new object with asterisks: [mycluster->device*[node100*]]%", prompts[0] == "[mycluster->device*[node100*]]%", prompts[0])
    check("commit removes the asterisks: [mycluster->device[node100]]%", prompts[1] == "[mycluster->device[node100]]%", prompts[1])
    check("'category add' from device mode drops into the category object", prompts[2] == "[mycluster->category*[test-category*]]%", prompts[2])
    check("remove moves up a level and keeps the asterisk until commit", prompts[4] == "[mycluster->category*]%", prompts[4])
    check("commit after remove clears it", prompts[5] == "[mycluster->category]%", prompts[5])
    check("the category really is gone after commit", "test-category" not in s.db["category"])

    s = c.Session("mycluster"); s.enter("device")
    s.script("add physicalnode node100 10.141.0.100; commit")
    s.enter("category")
    s.run_line("device remove node100")
    check("a mode-prefixed command does not change the current mode", s.mode == "category" and s.prompt() == "[mycluster->category]%", s.prompt())
    check("...but the change is pending in device mode", ("-", "device", "node100") in s.modified())
    s.enter("device")
    check("entering device mode then shows the asterisk", s.prompt() == "[mycluster->device*]%", s.prompt())
    s.commit()
    check("commit executes the removal whichever mode it runs in", "node100" not in s.db["device"])

    # modified, refresh, clear, booleans
    s = c.Session(); s.enter("device")
    s.script("add physicalnode node100 10.141.0.100; commit; clone node100 node101")
    check("clone drops into the new object", s.obj == "node101")
    check("clone with the same base name takes the matching IP: node101 -> 10.141.0.101", s.get("ip", "node101") == "10.141.0.101", s.get("ip", "node101"))
    check("modified shows '+' for a new object", ("+", "device", "node101") in s.modified())
    s.commit()
    s.use("node101"); s.set("category", "other-cat")
    check("modified shows a blank State for a changed object", ("", "device", "node101") in s.modified())
    s.refresh()
    check("refresh undoes the uncommitted change", s.get("category") == "default" and not s.modified())
    s.set("mac", "00:11:22:33:44:55"); s.commit()
    s.clear("mac")
    check("clear on a MAC address gives 00:00:00:00:00:00", s.get("mac") == "00:00:00:00:00:00")
    for v in ("yes", "1", "ON", "True"):
        s.set("datanode", v)
        assert s.get("datanode") == "yes"
    s.set("datanode", "Off")
    check("Boolean spellings yes/1/on/true and no/0/off/false are case-insensitive", s.get("datanode") == "no")
    check("a non-Boolean for a Boolean property is refused", raises(lambda: s.set("datanode", "maybe")))
    s.commit()
    s2 = c.Session(); s2.db["category"]["mydefaultimage"] = {"bootloaderprotocol": "HTTP"}
    s2.enter("device"); s2.add("physicalnode", "node001"); s2.set("category", "mydefaultimage"); s2.commit()
    check("get shows an inherited value with the source in brackets: HTTP (mydefaultimage)", s2.get("bootloaderprotocol", "node001") == "HTTP (mydefaultimage)")
    s2.set("bootloaderprotocol", "tftp", "node001"); s2.commit()
    check("a node value replaces the inherited one", s2.get("bootloaderprotocol", "node001") == "tftp")

    # foreach
    s = c.Session(); s.enter("device")
    s.script("add physicalnode node001 10.141.0.1; commit")
    s.run_line("foreach --clone node001 -n node022..node024 ()")
    check("foreach --clone node001 -n node022..node024: IPs follow the numbers (.22, .23, .24)", [s.get("ip", f"node0{n}") for n in (22, 23, 24)] == ["10.141.0.22", "10.141.0.23", "10.141.0.24"])
    s.commit()
    s.run_line("foreach -n node022..node024 (set revision test)")
    check("foreach -n list (set revision test) changes all three", all(s.get("revision", f"node0{n}") == "test" for n in (22, 23, 24)))
    s.commit()
    s.run_line("foreach -c default (set datanode yes)")
    check("foreach -c default reaches every node in the category", all(s.get("datanode", n) == "yes" for n in ("node001", "node022", "node023", "node024")))

    s = c.Session(); s.enter("device")
    s.script("add physicalnode node001 10.141.0.1; commit")
    out = s.foreach(E("node[02-04]"), [], clone_from="node001")
    check("clone with a different digit count (node02 from node001) warns and leaves the IP alone", out.count("Base name mismatch, IP settings will not be modified!") == 3 and s.get("ip", "node02") == "10.141.0.1")
    s = c.Session(); s.enter("device")
    s.script("add physicalnode node001 10.141.0.1; commit")
    s.foreach(E("node[02-04]"), [], clone_from="node001", next_ip=True)
    check("--next-ip picks the next free address anyway (.2, .3, .4)", [s.get("ip", n) for n in ("node02", "node03", "node04")] == ["10.141.0.2", "10.141.0.3", "10.141.0.4"])

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
