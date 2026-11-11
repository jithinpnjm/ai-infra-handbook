import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import c05_nccl_parse as P  # noqa: E402
import c05_worked_example as W  # noqa: E402

FIX = os.path.join(os.path.dirname(__file__), "c05_fixtures")


def read(name):
    return open(os.path.join(FIX, name)).read()


def table(rows, n=16, wrong=0, redop="sum"):
    """Synthetic all_reduce table: rows are (size, busbw GB/s). Times are derived."""
    f = P.busbw_factor("all_reduce", n)
    out = ["#       size         count      type   redop    root     time   algbw   busbw #wrong"]
    for size, bus in rows:
        t = size / (bus / f * 1e9) * 1e6
        a = size / (t * 1e-6) / 1e9
        h = f"{t:.1f} {a:.2f} {a * f:.2f} {wrong}"
        out.append(f"{size} {size // 4} float {redop} -1 {h} {h}")
    return "\n".join(out)


HEALTHY = [(8 << 20, 20), (32 << 20, 33), (128 << 20, 41), (512 << 20, 44.5), (1 << 30, 45)]


# ---- factors and arithmetic (PERFORMANCE.md) ----
def test_factors():
    assert P.busbw_factor("all_reduce", 8) == pytest.approx(1.75)
    assert P.busbw_factor("all_reduce", 64) == pytest.approx(1.96875)
    assert P.busbw_factor("all_gather", 8) == pytest.approx(0.875)
    assert P.busbw_factor("alltoall", 8) == pytest.approx(0.875)
    assert P.busbw_factor("broadcast", 8) == 1.0
    assert P.busbw_factor("reduce", 64) == 1.0


def test_worked_rows_match_chapter():
    r = W.row("all_reduce", 8, 64 << 20, 1653.1)
    assert r["algbw"] == pytest.approx(40.60, abs=0.01)
    assert r["busbw"] == pytest.approx(71.05, abs=0.02)
    r = W.row("all_reduce", 16, 1 << 30, 44739.2, link_gbps=400)
    assert (r["algbw"], r["busbw"], r["efficiency"]) == (24.0, 45.0, 0.9)
    r = W.row("all_reduce", 64, 1 << 30, 46970.0, link_gbps=400)
    assert r["algbw"] == pytest.approx(22.86, abs=0.01)
    assert r["busbw"] == pytest.approx(45.0, abs=0.02)
    r = W.row("all_reduce", 64, 1 << 30, 93940.0, link_gbps=400)
    assert r["efficiency"] == pytest.approx(0.45, abs=0.002)


# ---- real fixture: a table copied from the BCM 11 administrator manual ----
def test_real_fixture_parses_older_layout():
    run = P.parse(read("c05_fixture_bcm_socket.txt"))
    assert len(run.rows) == 13
    assert run.rows[0].root is None
    assert run.rows[0].size == 1048576
    assert run.rows[0].oop.time_us == 1491.5
    assert run.rows[-1].inplace.busbw == 0.79
    assert run.avg_busbw == pytest.approx(0.810575)
    assert run.oob_values == 0


def test_real_fixture_arithmetic_holds_for_two_ranks():
    # n=2 gives factor 1, so busbw == algbw, and algbw == size/time with GB = 1e9
    run = P.parse(read("c05_fixture_bcm_socket.txt"))
    assert P.check_arithmetic(run, 2, "all_reduce") == []


def test_real_fixture_flags_socket_fallback():
    run = P.parse(read("c05_fixture_bcm_socket.txt"))
    assert run.transport == "Socket"
    assert run.ib_disabled_by_env is True
    summary, flags = P.analyse(run, ranks=2, link_gbps=400)
    assert "SOCKET_TRANSPORT" in flags
    assert "PLATEAU_BELOW_LINK_RATE" in flags
    assert "WRONG_NONZERO" not in flags
    assert summary["efficiency_vs_link"] < 0.05


# ---- synthetic fixtures (modern layout with root and #wrong) ----
def test_healthy_synthetic_file_passes():
    run = P.parse(read("c05_fixture_synth_healthy.txt"))
    assert len(run.rows) == 5 and run.rows[0].root == -1
    summary, flags = P.analyse(run, ranks=16, link_gbps=400)
    assert flags == []
    assert summary["efficiency_vs_link"] == pytest.approx(0.87, abs=0.002)


def test_wrong_nonzero_flag():
    run = P.parse(table(HEALTHY, wrong=3))
    _, flags = P.analyse(run, 16, 400)
    assert "WRONG_NONZERO" in flags


def test_na_wrong_is_not_a_failure():
    text = table(HEALTHY).replace(" 0 ", " N/A ")
    run = P.parse(text)
    _, flags = P.analyse(run, 16, 400)
    assert "WRONG_NONZERO" not in flags


def test_out_of_bounds_summary_line_flags():
    text = table(HEALTHY) + "\n# Out of bounds values : 4 FAILED\n"
    _, flags = P.analyse(P.parse(text), 16, 400)
    assert "WRONG_NONZERO" in flags


def test_plateau_below_link_rate():
    slow = [(s, b * 0.5) for s, b in HEALTHY]  # half-rate link, for example a downtrained width
    summary, flags = P.analyse(P.parse(table(slow)), 16, 400)
    assert "PLATEAU_BELOW_LINK_RATE" in flags
    assert summary["efficiency_vs_link"] == pytest.approx(0.435, abs=0.002)


def test_efficiency_threshold_is_a_parameter():
    slow = [(s, b * 0.85) for s, b in HEALTHY]
    run = P.parse(table(slow))
    assert "PLATEAU_BELOW_LINK_RATE" in P.analyse(run, 16, 400, min_eff=0.8)[1]
    assert "PLATEAU_BELOW_LINK_RATE" not in P.analyse(run, 16, 400, min_eff=0.7)[1]


def test_mid_curve_collapse():
    bad = [(8 << 20, 20), (32 << 20, 40), (128 << 20, 41), (512 << 20, 15), (1 << 30, 44)]
    _, flags = P.analyse(P.parse(table(bad)), 16, 400)
    assert "MID_CURVE_COLLAPSE" in flags
    assert "MID_CURVE_COLLAPSE" not in P.analyse(P.parse(table(HEALTHY)), 16, 400)[1]


def test_small_message_latency_flag_needs_a_threshold():
    run = P.parse(table(HEALTHY))
    summary, flags = P.analyse(run, 16, 400)
    assert "HIGH_SMALL_MESSAGE_LATENCY" not in flags   # no threshold given
    _, flags = P.analyse(run, 16, 400, max_small_us=100)
    assert "HIGH_SMALL_MESSAGE_LATENCY" in flags       # 8 MiB row takes hundreds of us
    _, flags = P.analyse(run, 16, 400, max_small_us=5000)
    assert "HIGH_SMALL_MESSAGE_LATENCY" not in flags


def test_arithmetic_mismatch_flag():
    text = table(HEALTHY)
    lines = text.splitlines()
    parts = lines[-1].split()
    parts[7] = "99.00"   # corrupt out-of-place busbw
    lines[-1] = " ".join(parts)
    run = P.parse("\n".join(lines))
    _, flags = P.analyse(run, 16, 400)
    assert "ARITHMETIC_MISMATCH" in flags


def test_wrong_rank_count_is_caught_by_arithmetic():
    run = P.parse(table(HEALTHY, n=16))
    assert P.check_arithmetic(run, 8, "all_reduce")  # told 8 ranks, table was made for 16


def test_baseline_regression():
    base = P.parse(table(HEALTHY))
    worse = P.parse(table([(s, b * 0.7) for s, b in HEALTHY]))
    summary, flags = P.analyse(worse, 16, 400, min_eff=0.8, baseline=base)
    assert "BELOW_BASELINE" in flags
    assert summary["ratio_vs_baseline"] == pytest.approx(0.7, abs=0.01)
    _, flags = P.analyse(base, 16, 400, baseline=base)
    assert "BELOW_BASELINE" not in flags


def test_slow_member_detection():
    got = P.find_slow_members({"n1": 44.8, "n2": 45.1, "n3": 23.0, "n4": 44.9})
    assert got == ["n3"]
    assert P.find_slow_members({"a": 45, "b": 45, "c": 44}) == []
    with pytest.raises(ValueError):
        P.find_slow_members({"a": 1, "b": 2})


def test_no_rows():
    assert P.analyse(P.parse("garbage\n# comment"), 16, 400)[1] == ["NO_ROWS"]


def test_log_lines_and_noise_are_ignored():
    text = "node1:1:1 [0] NCCL INFO Using network IB\nsome 12 text\n" + table(HEALTHY)
    run = P.parse(text)
    assert run.transport == "IB" and len(run.rows) == 5
    assert "SOCKET_TRANSPORT" not in P.analyse(run, 16, 400)[1]


# ---- CLI ----
def test_cli_exit_codes(tmp_path, capsys):
    good = os.path.join(FIX, "c05_fixture_synth_healthy.txt")
    assert P.main([good, "--ranks", "16", "--link-gbps", "400"]) == 0
    bad = os.path.join(FIX, "c05_fixture_bcm_socket.txt")
    assert P.main([bad, "--ranks", "2", "--link-gbps", "400", "--json"]) == 1
    assert "SOCKET_TRANSPORT" in capsys.readouterr().out
    assert P.main([str(tmp_path / "missing.txt"), "--ranks", "2", "--link-gbps", "400"]) == 2


def test_link_rate_check_can_be_skipped():
    run = P.parse(table([(s, b * 0.1) for s, b in HEALTHY]))
    summary, flags = P.analyse(run, 16, None)
    assert "PLATEAU_BELOW_LINK_RATE" not in flags
    assert summary["efficiency_vs_link"] is None


def test_socket_on_any_rank_wins():
    text = ("n1:1:1 [0] NCCL INFO Using network IB\n"
            "n2:1:1 [0] NCCL INFO Using network Socket\n"
            "n1:1:1 [0] NCCL INFO Using network IB\n") + table(HEALTHY)
    run = P.parse(text)
    assert run.transport == "Socket"
    assert "SOCKET_TRANSPORT" in P.analyse(run, 16, 400)[1]


# ---- the counter-diff script ----
def _diff(tmp_path, before, after):
    import subprocess
    b, a = tmp_path / "b.txt", tmp_path / "a.txt"
    b.write_text(before)
    a.write_text(after)
    script = os.path.join(os.path.dirname(__file__), "c05_diff_counters.sh")
    return subprocess.run(["bash", script, str(b), str(a)], capture_output=True, text=True)


BEFORE = ("### /sys/class/infiniband/mlx5_0/ports/1/counters\n"
          "/x/port_xmit_data:100\n/x/symbol_error:0\n/x/link_error_recovery:0\n")


def test_diff_script_ignores_data_counters(tmp_path):
    r = _diff(tmp_path, BEFORE, BEFORE.replace("port_xmit_data:100", "port_xmit_data:999999"))
    assert r.returncode == 0 and "flat" in r.stdout


def test_diff_script_fails_when_an_error_counter_moves(tmp_path):
    r = _diff(tmp_path, BEFORE, BEFORE.replace("symbol_error:0", "symbol_error:12"))
    assert r.returncode == 1 and "symbol_error:12" in r.stdout
