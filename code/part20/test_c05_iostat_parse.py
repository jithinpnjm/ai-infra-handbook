from c05_iostat_parse import parse_iostat, notes

# Systems Performance 2nd ed, chapter 9: iostat -sxz 1 sample.
SHORT = """\
avg-cpu: %user %nice %system %iowait %steal %idle
15.82 0.00 10.71 31.63 1.53 40.31
Device tps kB/s rqm/s await aqu-sz areq-sz %util
nvme0n1 1642.00 9064.00 664.00 0.44 0.00 5.52 100.00
"""
# Invented row in the same layout: a slow, busy disk.
SLOW = """\
Device tps kB/s rqm/s await aqu-sz areq-sz %util
sda 120.00 15360.00 0.00 38.50 4.60 128.00 99.00
"""


def test_parse_short_layout():
    rows = parse_iostat(SHORT)
    assert len(rows) == 1
    assert rows[0]["device"] == "nvme0n1"
    assert rows[0]["await"] == 0.44
    assert rows[0]["%util"] == 100.0


def test_cpu_line_is_not_a_device():
    assert all(r["device"] != "15.82" for r in parse_iostat(SHORT))


def test_book_nvme_is_busy_but_fast_and_random_and_merged():
    flags = notes(parse_iostat(SHORT)[0])
    assert any("busy but fast" in f for f in flags)
    assert any("small requests" in f for f in flags)
    assert any("merging" in f for f in flags)


def test_slow_disk_flagged():
    flags = notes(parse_iostat(SLOW)[0])
    assert flags == ["slow: await 38.50 ms"]


def test_wide_layout_uses_r_await():
    text = "Device r/s r_await w_await wareq-sz %util\nsdb 10 25.0 1.0 64 20\n"
    row = parse_iostat(text)[0]
    assert "slow: await 25.00 ms" in notes(row)


# Real iostat -sxz 1 3 output, ubuntu:24.04 container on a Docker VM (kernel 6.18.37-0-virt):
# the first report is an average since boot and must not be judged as a live interval.
REAL_THREE = """\
Device             tps      kB/s    rqm/s   await  areq-sz  aqu-sz  %util
vda             121.53  94950.10   166.83    1.14   781.31    0.15   2.80

Device             tps      kB/s    rqm/s   await  areq-sz  aqu-sz  %util
vda            5854.00  54928.00  7878.00    0.14     9.38    1.12  80.60

Device             tps      kB/s    rqm/s   await  areq-sz  aqu-sz  %util
vda            6015.00  56140.00  8020.00    0.14     9.33    1.11  77.90
"""


def test_first_report_is_skipped_on_request():
    assert len(parse_iostat(REAL_THREE)) == 3
    live = parse_iostat(REAL_THREE, skip_first=True)
    assert [r["tps"] for r in live] == [5854.0, 6015.0]


def test_single_report_is_kept_even_when_skipping():
    assert len(parse_iostat(SHORT, skip_first=True)) == 1
