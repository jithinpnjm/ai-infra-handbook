"""Tests for triage_parse and triage_findings.

Every fixture is text printed in a book. The source is named above each one.
"""
import os
import tempfile

import triage_findings as f
import triage_parse as p
import triage_report as r

# Systems Performance 2nd ed, Chapter 16, section 16.1.3 (serverA and serverB).
UPTIME_A = "22:07:23 up 15 days, 5:01, 1 user, load average: 85.09, 89.25, 91.26"
UPTIME_B = "22:06:24 up 91 days, 23:52, 1 user, load average: 17.94, 16.92, 16.62"
MPSTAT_A = """Linux 4.4.0-130-generic (...) 07/18/2019 _x86_64_ (48 CPU)
10:07:55 PM CPU %usr %nice %sys %iowait %irq %soft %steal %guest %gnice %idle
10:08:05 PM all 89.72 0.00 7.84 0.00 0.00 0.04 0.00 0.00 0.00 2.40
10:08:15 PM all 88.60 0.00 9.18 0.00 0.00 0.05 0.00 0.00 0.00 2.17
Average: all 89.49 0.00 8.47 0.00 0.00 0.05 0.00 0.00 0.00 1.99
"""

# Systems Performance 2nd ed, Chapter 4, section 4.2.1 (vmstat 1 3).
VMSTAT_3 = """$ vmstat 1 3
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
r b swpd free buff cache si so bi bo in cs us sy id wa st
4 0 1446428 662012 142100 5644676 1 4 28 152 33 1 29 8 63 0 0
4 0 1446428 665988 142116 5642272 0 0 0 284 4957 4969 51 0 48 0 0
4 0 1446428 685116 142116 5623676 0 0 0 0 4488 5507 52 0 48 0 0
"""

# Systems Performance 2nd ed, Chapter 7, exercises (the swapping output).
VMSTAT_SWAP = """procs -----------memory-------- ---swap-- -----io---- --system-- -----cpu-----
r b swpd free buff cache si so bi bo in cs us sy id wa st
2 0 413344 62284 72 6972 0 0 17 12 1 1 0 0 100 0 0
2 0 418036 68172 68 3808 0 4692 4520 4692 1060 1939 61 38 0 1 0
2 0 418232 71272 68 1696 0 196 23924 196 1288 2464 51 38 0 11 0
1 0 418308 67296 76 3936 0 0 1060 0 1020 1843 53 47 0 0 0
"""

# How Linux Works 3rd ed, Chapter 8, section 8.5.5 (vmstat 2 on a quiet system).
VMSTAT_QUIET = """$ vmstat 2
procs -----------memory---------- ---swap-- -----io---- -system-- ----cpu----
r b swpd free buff cache si so bi bo in cs us sy id wa
2 0 320416 3027696 198636 1072568 0 0 1 1 2 0 15 2 83 0
2 0 320416 3027288 198636 1072564 0 0 0 1182 407 636 1 0 99 0
1 0 320416 3026792 198640 1072572 0 0 0 58 281 537 1 0 99 0
0 0 320416 3024932 198648 1074924 0 0 0 308 318 541 0 0 99 1
"""

# Systems Performance 2nd ed, Chapter 8, section 8.6.2 (free -m).
FREE = """$ free -m
total used free shared buff/cache available
Mem: 1950 568 163 0 1218 1187
Swap: 0 0 0
"""

# Systems Performance 2nd ed, Chapter 9, section 9.6.1 (iostat -sxz 1).
IOSTAT_S = """$ iostat -sxz 1
[...]
avg-cpu: %user %nice %system %iowait %steal %idle
15.82 0.00 10.71 31.63 1.53 40.31
Device tps kB/s rqm/s await aqu-sz areq-sz %util
nvme0n1 1642.00 9064.00 664.00 0.44 0.00 5.52 100.00
[...]
"""

# Systems Performance 2nd ed, Chapter 6, section 6.6.1 and Chapter 7, 7.5.2.
PSI_CPU = "some avg10=50.00 avg60=50.00 avg300=49.70 total=1031438206"
PSI_MEM = """some avg10=2.84 avg60=1.23 avg300=0.32 total=1468344
full avg10=1.85 avg60=0.66 avg300=0.16 total=702578"""


def test_uptime_trend_and_load_per_cpu():
    a, b = p.parse_uptime(UPTIME_A), p.parse_uptime(UPTIME_B)
    assert a == {"load1": 85.09, "load5": 89.25, "load15": 91.26}
    fa, fb = f.load_findings(a, 48), f.load_findings(b, 64)
    assert any(x.kind == "S" for x in fa)       # 85.09 / 48 is above 1
    assert not any(x.kind == "S" for x in fb)   # 17.94 / 64 is below 1
    assert "falling" in fa[-1].message and "rising" in fb[-1].message


def test_mpstat_all_rows_give_busy_percent():
    rows = p.parse_mpstat(MPSTAT_A)
    assert [x["CPU"] for x in rows] == ["all"] * 3
    assert rows[-1]["%usr"] == 89.49
    assert "98.0 percent" in f.mpstat_findings(rows)[0].message


def test_vmstat_first_row_is_marked_and_ignored():
    rows = p.parse_vmstat(VMSTAT_3)
    assert len(rows) == 3 and rows[0]["since_boot"] and not rows[1]["since_boot"]
    assert rows[0]["so"] == 4
    kinds = [(x.resource, x.kind) for x in f.vmstat_findings(rows, 8)]
    assert ("memory", "S") not in kinds         # the so=4 is in the since-boot row


def test_vmstat_swapping_is_memory_saturation():
    rows = p.parse_vmstat(VMSTAT_SWAP)
    assert len(rows) == 4 and rows[2]["so"] == 196
    found = f.vmstat_findings(rows, 4)
    assert ("memory", "S") in [(x.resource, x.kind) for x in found]


def test_vmstat_quiet_system_has_no_saturation():
    rows = p.parse_vmstat(VMSTAT_QUIET)
    assert len(rows) == 4 and "st" not in rows[0]
    assert not [x for x in f.vmstat_findings(rows, 4) if x.kind == "S"]


def test_free_uses_available_not_free():
    parsed = p.parse_free(FREE)
    assert parsed["mem"]["available"] == 1187 and parsed["swap"]["used"] == 0
    out = f.free_findings(parsed)
    assert out[0].kind == "U" and "61 percent" in out[0].message
    assert f.free_findings(parsed, min_available_pct=70)[0].kind == "S"


def test_iostat_busy_is_not_saturated():
    parsed = p.parse_iostat(IOSTAT_S)
    assert parsed["cpu"]["iowait"] == 31.63
    disk = parsed["disks"][0]
    assert disk["device"] == "nvme0n1" and disk["%util"] == 100.0
    found = f.iostat_findings(parsed)
    assert any("busy 100" in x.message for x in found)
    assert not any(x.kind == "S" for x in found)   # aqu-sz is 0.00


def test_psi_rising_only_when_avg10_above_avg300():
    assert f.psi_findings("memory", p.parse_psi(PSI_MEM))
    assert p.parse_psi(PSI_MEM)["full"]["avg300"] == 0.16
    assert f.psi_findings("cpu", p.parse_psi(PSI_CPU))   # 50.00 above 49.70


def test_find_oom_uses_the_book_search_words():
    text = "[1] Out of memory: Kill process 99 (java)\n[2] eth0 link up"
    assert p.find_oom(text) == ["[1] Out of memory: Kill process 99 (java)"]


def test_report_reads_a_directory_and_flags_missing_files():
    with tempfile.TemporaryDirectory() as d:
        for name, text in [("nproc.txt", "48\n"), ("uptime.txt", UPTIME_A),
                           ("vmstat.txt", VMSTAT_SWAP), ("free.txt", FREE)]:
            with open(os.path.join(d, name), "w") as fh:
                fh.write(text)
        out = r.report(d)
    assert ("known-unknown", "E") in [(x.resource, x.kind) for x in out]
    assert ("memory", "S") in [(x.resource, x.kind) for x in out]
    assert [x.kind for x in out] == sorted((x.kind for x in out), key="ESU".index)


def test_report_survives_a_file_written_for_a_missing_tool():
    with tempfile.TemporaryDirectory() as d:
        for name, text in [("nproc.txt", "2\n"), ("free.txt", "missing tool: free\n")]:
            with open(os.path.join(d, name), "w") as fh:
                fh.write(text)
        out = r.report(d)
    assert any("free.txt not readable: missing tool: free" in x.message for x in out)


def test_report_flags_a_dmesg_that_could_not_be_read():
    # Real text from ubuntu:24.04 in a Docker container (dmesg is not permitted there).
    text = "dmesg: read kernel buffer failed: Operation not permitted\nexit 1 from: dmesg -T\n"
    with tempfile.TemporaryDirectory() as d:
        for name, body in [("nproc.txt", "2\n"), ("dmesg.txt", text)]:
            with open(os.path.join(d, name), "w") as fh:
                fh.write(body)
        out = r.report(d)
    assert any("dmesg.txt not readable" in x.message for x in out)
