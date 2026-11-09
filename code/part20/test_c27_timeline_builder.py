import pathlib

import pytest

import c27_timeline_builder as tb

HERE = pathlib.Path(__file__).parent
NOTES = (HERE / "c27_notes.txt").read_text(encoding="utf-8")


def test_metrics_from_fixture():
    m = tb.compute_metrics(tb.parse_notes(NOTES))
    assert m == {"time_to_detect": 19, "time_to_mitigate": 40, "time_to_resolve": 113}


def test_timeline_matches_post_mortem_fixture():
    good = (HERE / "c27_pm_good.md").read_text(encoding="utf-8")
    assert tb.build_timeline(NOTES).rstrip("\n") in good


def test_events_are_sorted():
    text = "2026-01-01 10:10 UTC - later [resolved]\n2026-01-01 10:00 UTC - first [started]\n"
    events = tb.parse_notes(text)
    assert [e[1] for e in events] == ["first", "later"]


def test_missing_tags_give_not_recorded():
    text = "2026-01-01 10:00 - begin [started]\n2026-01-01 10:07 - page [detected]\n"
    out = tb.build_timeline(text)
    assert "Time to detect: 7 min" in out
    assert "Time to mitigate: not recorded" in out


def test_started_tag_required():
    with pytest.raises(tb.NoteError, match="started"):
        tb.compute_metrics(tb.parse_notes("2026-01-01 10:00 - page [detected]"))


def test_duplicate_tag_rejected():
    text = "2026-01-01 10:00 - a [started]\n2026-01-01 10:01 - b [started]\n"
    with pytest.raises(tb.NoteError, match="twice"):
        tb.compute_metrics(tb.parse_notes(text))


def test_tags_out_of_order_rejected():
    text = "2026-01-01 10:00 - a [started]\n2026-01-01 10:05 - b [resolved]\n2026-01-01 10:09 - c [mitigated]\n"
    with pytest.raises(tb.NoteError, match="before"):
        tb.compute_metrics(tb.parse_notes(text))


def test_bad_line_and_unknown_tag():
    with pytest.raises(tb.NoteError, match="line 1"):
        tb.parse_notes("garbage")
    with pytest.raises(tb.NoteError, match="unknown tag"):
        tb.parse_notes("2026-01-01 10:00 - x [fixed]")


def test_crossing_midnight():
    text = "2026-01-01 23:50 UTC - a [started]\n2026-01-02 00:20 UTC - b [mitigated]\n"
    assert tb.compute_metrics(tb.parse_notes(text))["time_to_mitigate"] == 30


def test_main(tmp_path, capsys):
    f = tmp_path / "n.txt"
    f.write_text(NOTES)
    assert tb.main(["x", str(f)]) == 0
    assert "Time to resolve: 113 min" in capsys.readouterr().out
    f.write_text("bad")
    assert tb.main(["x", str(f)]) == 1
    assert tb.main(["x"]) == 2
