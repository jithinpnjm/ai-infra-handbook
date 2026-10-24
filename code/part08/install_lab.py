#!/usr/bin/env python3
"""Self-checking lab for chapter 8.2: the planning numbers in the BCM 11 Installation Manual, reproduced."""
import datetime as dt, os, sys
import bcm_plan as p
import burn_config as bc
import license_check as lc

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def main():
    for n, (_, cmd_ram, disk) in p.OBSERVED.items():
        r, dsk = p.head_node_ram_gb(n), p.head_node_disk_gb(n)
        check(f"manual's observed table, {n} nodes: formula gives CMDaemon RAM {r:.1f} GB (observed {cmd_ram}) and disk {dsk:.0f} GB (observed {disk})",
              abs(r - cmd_ram) <= 0.12 * cmd_ram + 0.1 and abs(dsk - 5 - disk) <= 0.01 * disk + 0.01, (r, dsk))
    check("each extra 100 metrics adds about 1 MB per device (1000 devices, 200 metrics: +1 GB)", abs(p.head_node_ram_gb(1000, metrics_per_device=200) - p.head_node_ram_gb(1000)) - 1.0 < 0.01)
    check("regular node RAM: 50 MB + 10 kB per node (1000 nodes -> about 0.06 GB)", abs(p.regular_node_ram_gb(1000) - 0.06) < 0.001, p.regular_node_ram_gb(1000))
    check("the manual's >1000-node head node advice (128 GB RAM) is far above the formula, as it says extra RAM caches the filesystem", p.head_node_ram_gb(2000) < 8)

    names = p.node_names(32)
    check("default naming gives node001 ... node032", names[0] == "node001" and names[-1] == "node032" and len(names) == 32)
    check("three digits allow at most node999 (1000 nodes starting at 1 do not fit)", p.node_names(999)[-1] == "node999" and not _ok(lambda: p.node_names(1000)))
    check("start number and base name are respected (dgx-005 ...)", p.node_names(3, "dgx-", 5, 3) == ["dgx-005", "dgx-006", "dgx-007"])

    boot = p.interface_addresses("10.141.0.0/16", 10)
    check("default addressing starts after the network base address in steps of 1 (10.141.0.1 ... 10.141.0.10)", boot[0] == "10.141.0.1" and boot[-1] == "10.141.0.10", boot)
    ipmi = p.interface_addresses("10.141.0.0/16", 10, "0.0.0.20")
    check("the manual's example: IPMI offset 0.0.0.20 gives 10.141.0.21 ... 10.141.0.30", ipmi[0] == "10.141.0.21" and ipmi[-1] == "10.141.0.30", ipmi)
    check("BOOTIF and IPMI addresses then do not overlap", p.overlap(boot, ipmi) == [])
    same = p.interface_addresses("10.141.0.0/16", 10)
    check("without an offset both interfaces get the same addresses on one network: the overlap the manual calls confusing", len(p.overlap(boot, same)) == 10)
    check("too many nodes for a small network is refused", not _ok(lambda: p.interface_addresses("10.141.0.0/28", 20)))

    n, parts = p.default_head_layout(400)
    check("a drive below about 500 GB gets one big partition", n == "master-one-big-partition.xml" and parts[-1] == ("/", "rest"))
    n, parts = p.default_head_layout(960)
    check("a drive of 500 GB or more gets the standard layout with /tmp (20G) and /var (180G)", n == "master-standard.xml" and ("/var", "180G") in parts and ("/tmp", "20G") in parts)

    here = os.path.dirname(os.path.abspath(__file__))
    text = open(os.path.join(here, "sample_licenseinfo.txt")).read()
    d, days, problems = lc.check(text, dt.date(2025, 3, 1))
    check("license sample: parsed edition, nodes and expiry", d["Edition"] == "NVIDIA Mission Control" and days == 85, (d.get("Edition"), days))
    check("with 85 days left a 3-month warning fires", any("expires in 85 days" in x for x in problems), problems)
    d, days, problems = lc.check(text, dt.date(2025, 6, 1))
    check("after the end date it reports EXPIRED (CMDaemon refuses to start)", any(x.startswith("EXPIRED") for x in problems), problems)
    d, days, problems = lc.check(text.replace("56 / 8192", "9000 / 8192"), dt.date(2025, 3, 1), 0)
    check("nodes in use above the licensed number are flagged", any("exceeds licensed" in x for x in problems), problems)
    d, days, problems = lc.check(text.replace("56 / 8192", "8000 / 8192"), dt.date(2025, 3, 1), 0)
    check("nodes above 90 percent of the license are flagged early", any("above 90 percent" in x for x in problems), problems)
    block = "Common name:                 basecm11\nExpiration date:             25/Sep/2025\nLicensed tokens:             8192\nLicense type:                Free\nEdition:                     NVIDIA Mission Control\n".replace(":  ", "  ")
    d2, days2, _ = lc.check("Edition                      NVIDIA Mission Control\nExpiration date              25/Sep/2025\nLicense type                 Free\n", dt.date(2025, 6, 24))
    check("verify-license info style dates (25/Sep/2025) are understood: 93 days from 24 Jun 2025", days2 == 93, days2)

    simple = """<?xml version="1.0"?><burnconfig><mail><address>root@master</address></mail><pre-install>
<phase name="01-hwinfo"><test name="hwinfo"/><test name="hwdiff"/><test name="sleep" args="10"/></phase>
<phase name="02-disks"><test name="disktest" args="30"/><test name="mce_check" endless="1"/></phase></pre-install>
<post-install><phase name="03-hpl"><test name="hpl"/><test name="mce_check" endless="1"/></phase>
<phase name="04-compile"><test name="compile" args="6"/><test name="mce_check" endless="1"/></phase></post-install></burnconfig>"""
    check("the manual's simple burn configuration passes", bc.check(simple) == [], bc.check(simple))
    check("phases out of order are flagged", any("alphanumeric" in x for x in bc.check(simple.replace("01-hwinfo", "05-hwinfo"))))
    check("a repeated phase name is flagged", any("twice" in x for x in bc.check(simple.replace("04-compile", "03-hpl"))))
    only_endless = "<burnconfig><post-install><phase name=\"01-x\"><test name=\"mce_check\" endless=\"1\"/></phase></post-install></burnconfig>"
    check("a phase with only endless tests is flagged (it never ends)", any("never finishes" in x for x in bc.check(only_endless)))
    check("memtest86 gets the manual's warning", any("memtest86" in x for x in bc.check(simple.replace("hwinfo\"/>", "hwinfo\"/><test name=\"memtest86\"/>", 1))))
    check("post-burn-install must be AUTO/FULL/MAIN/NOSYNC", any("post-burn-install" in x for x in bc.check(simple.replace("</burnconfig>", "<post-burn-install>RESYNC</post-burn-install></burnconfig>"))) and not any("post-burn-install" in x for x in bc.check(simple.replace("</burnconfig>", "<post-burn-install>NOSYNC</post-burn-install></burnconfig>"))))
    check("an empty config (no sections) is flagged", bool(bc.check("<burnconfig/>")))
    st = bc.parse_status("node001 (00000000a000) - W(0) phase 02-disks 00:02:58 (D:H:M) FAILED, mce_check (SP), disktest (SF,61), kmon (SP)")
    check("the manual's burn status line is read: disktest started+failed with custom value 61", st["state"] == "FAILED" and st["tests"]["disktest"]["failed"] and st["tests"]["disktest"]["custom"] == "61" and not st["tests"]["kmon"]["failed"], st)

    check("topology 1 defines externalnet+internalnet, 2 only internalnet, 3 internalnet+managementnet (3.3.13)",
          p.TOPOLOGIES[1]["networks"] == ["externalnet", "internalnet"] and p.TOPOLOGIES[2]["networks"] == ["internalnet"] and p.TOPOLOGIES[3]["networks"] == ["internalnet", "managementnet"])
    check("only topology 3 always needs a DHCP relay (layer 3 between head and nodes)", p.TOPOLOGIES[3]["head_dhcp_relay_needed"] is True and p.TOPOLOGIES[1]["head_dhcp_relay_needed"] is False)

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0


def _ok(fn):
    try:
        fn(); return True
    except ValueError:
        return False


if __name__ == "__main__":
    sys.exit(main())
