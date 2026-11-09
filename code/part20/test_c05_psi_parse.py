import pytest
from c05_psi_parse import parse_psi, trend, verdict

# Fixtures: Systems Performance 2nd ed, chapters 6, 7 and 9 (PSI examples).
CPU = "some avg10=50.00 avg60=50.00 avg300=49.70 total=1031438206\n"
MEM = ("some avg10=2.84 avg60=1.23 avg300=0.32 total=1468344\n"
       "full avg10=1.85 avg60=0.66 avg300=0.16 total=702578\n")
IO = ("some avg10=63.11 avg60=32.18 avg300=8.62 total=667212021\n"
      "full avg10=60.76 avg60=31.13 avg300=8.35 total=622722632\n")
# Kernel docs idle example.
IDLE = ("some avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
        "full avg10=0.00 avg60=0.00 avg300=0.00 total=0\n")


def test_parse_cpu_two_cpus_three_threads():
    psi = parse_psi(CPU)
    assert psi["some"]["avg10"] == 50.0
    assert psi["some"]["total"] == 1031438206
    assert "full" not in psi


def test_parse_io_has_full():
    psi = parse_psi(IO)
    assert psi["full"]["avg300"] == 8.35


def test_trend_rising_for_book_io_example():
    assert trend(parse_psi(IO)["some"]) == "rising"


def test_trend_steady_for_cpu_example():
    assert trend(parse_psi(CPU)["some"]) == "steady"


def test_verdict_idle():
    assert verdict(parse_psi(IDLE)).startswith("no meaningful stall")


def test_verdict_io_says_all_tasks():
    assert verdict(parse_psi(IO)).startswith("ALL non-idle")


def test_verdict_memory_is_quiet_with_default_threshold():
    assert verdict(parse_psi(MEM)).startswith("no meaningful stall")


def test_bad_line_rejected():
    with pytest.raises(ValueError):
        parse_psi("avg10=1 something else here ok\n")
