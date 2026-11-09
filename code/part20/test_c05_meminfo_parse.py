import pytest
from c05_meminfo_parse import parse_meminfo, memory_view, verdict

# Built from the free -m output in Systems Performance 2nd ed, chapter 8:
# total 1950, used 568, free 163, buff/cache 1218, available 1187 (MiB) -> kB.
# Only the shape of /proc/meminfo is real. AnonPages and Mlocked are invented.
BOOK = """\
MemTotal:        1996800 kB
MemFree:          166912 kB
MemAvailable:    1215488 kB
Buffers:           86016 kB
Cached:          1160192 kB
SwapTotal:             0 kB
SwapFree:              0 kB
AnonPages:        500000 kB
Mlocked:               0 kB
HugePages_Total:       0
"""

PRESSURE = BOOK.replace("MemAvailable:    1215488", "MemAvailable:      90000")
SWAPPING = BOOK.replace("SwapTotal:             0", "SwapTotal:       1048576").replace(
    "SwapFree:              0", "SwapFree:         524288")


def test_parse_handles_lines_without_unit():
    info = parse_meminfo(BOOK)
    assert info["MemTotal"] == 1996800
    assert info["HugePages_Total"] == 0


def test_free_is_small_but_available_is_large():
    view = memory_view(parse_meminfo(BOOK))
    assert view["free_pct"] == pytest.approx(8.36, abs=0.01)
    assert view["available_pct"] == pytest.approx(60.87, abs=0.01)
    assert view["cache_kb"] == 86016 + 1160192


def test_verdict_calls_book_host_healthy():
    assert verdict(memory_view(parse_meminfo(BOOK))).startswith("healthy")


def test_verdict_low_available():
    assert verdict(memory_view(parse_meminfo(PRESSURE))).startswith("LOW available")


def test_verdict_swap_in_use():
    view = memory_view(parse_meminfo(SWAPPING))
    assert view["swap_used_kb"] == 524288
    assert "swap is in use" in verdict(view)
