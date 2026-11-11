import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import c15_walkthrough as w  # noqa: E402


def test_walkthrough_runs_and_reports(capsys):
    assert w.main() == 0
    out = capsys.readouterr().out
    assert "0 problems" in out
    assert "685 s, 11.47%" in out
    assert "far over time" in out  # the scripted third round takes 200 s
    assert "Session mean 44.2/100" in out
