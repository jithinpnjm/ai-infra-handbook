import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import c04_straggler_detector as sd  # noqa: E402

FIX = os.path.join(HERE, "c04_fixtures")


def run(name, **kw):
    return sd.analyze(sd.load(os.path.join(FIX, name + ".csv")), **kw)


def test_healthy_job_is_clean():
    r = run("healthy")
    assert r["straggler_rank"] == [] and r["straggler_host"] == []
    assert r["global_slowdown"] is False


def test_one_slow_gpu_is_named_with_its_host():
    r = run("slow_gpu")
    assert [(x["rank"], x["host"], x["kind"]) for x in r["straggler_rank"]] == [(19, "trainer-2", "compute")]
    assert r["straggler_host"] == []  # one rank is not a host problem


def test_slow_host_data_stall_flags_the_host_not_just_ranks():
    r = run("slow_host")
    assert r["straggler_host"] == ["trainer-1"]
    assert {x["rank"] for x in r["straggler_rank"]} == set(range(8, 16))
    assert all(x["kind"] == "data" for x in r["straggler_rank"])


def test_short_spike_is_not_flagged():
    r = run("spike")
    assert r["straggler_rank"] == []


def test_global_slowdown_is_not_blamed_on_one_rank():
    r = run("global_slowdown")
    assert r["global_slowdown"] is True
    assert r["straggler_rank"] == [] and r["straggler_host"] == []
    assert r["recent_compute_s"] > 1.3 * r["baseline_compute_s"]


def test_too_few_steps_gives_no_verdict():
    rows = sd.load(os.path.join(FIX, "slow_gpu.csv"))
    short = [r for r in rows if r["step"] < 5]
    assert sd.analyze(short)["note"] == "not enough steps for a verdict"


def test_stall_detection_uses_the_newest_timestamp():
    rows = sd.load(os.path.join(FIX, "healthy.csv"))
    last = max(r["ts"] for r in rows)
    assert sd.check_stall(rows, now=last + 30, stale_s=60)["stalled"] is False
    assert sd.check_stall(rows, now=last + 600, stale_s=60)["stalled"] is True


def test_committed_fixtures_match_the_generator(tmp_path):
    sd.write_fixtures(str(tmp_path))
    for name in os.listdir(tmp_path):
        assert open(tmp_path / name).read() == open(os.path.join(FIX, name)).read()


def test_cli_exit_codes(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["x", os.path.join(FIX, "healthy.csv")])
    assert sd.main() == 0
    monkeypatch.setattr(sys, "argv", ["x", os.path.join(FIX, "slow_gpu.csv")])
    assert sd.main() == 1
    monkeypatch.setattr(sys, "argv", ["x", os.path.join(FIX, "healthy.csv"), "--stale-seconds", "60"])
    assert sd.main() == 2  # fixture timestamps are in 2023, so the log is stale
