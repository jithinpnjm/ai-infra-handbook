import pathlib
import re

import c27_postmortem_lint as lint

HERE = pathlib.Path(__file__).parent
GOOD = (HERE / "c27_pm_good.md").read_text(encoding="utf-8")
BAD = (HERE / "c27_pm_bad.md").read_text(encoding="utf-8")


def codes(text):
    return [f.code for f in lint.lint(text)]


def test_good_fixture_is_clean():
    assert lint.lint(GOOD) == []


def test_bad_fixture_hits_every_rule_family():
    found = set(codes(BAD))
    assert {"S1", "M1", "I1", "A2", "A3", "A4", "A5", "B1"} <= found


def test_missing_section_is_named():
    text = re.sub(r"## Where we got lucky.*?(?=## Action items)", "", GOOD, flags=re.S)
    assert [f.message for f in lint.lint(text)] == ["missing section: where we got lucky"]


def test_shared_owner_is_rejected():
    text = GOOD.replace("| Luis Ferreira |", "| Luis Ferreira and Mei Tanaka |")
    assert codes(text) == ["A2"]


def test_team_owner_is_rejected():
    assert codes(GOOD.replace("| Mei Tanaka |", "| SRE team |")) == ["A2"]


def test_due_date_must_be_iso():
    assert codes(GOOD.replace("2026-04-04", "next sprint")) == ["A3"]


def test_vague_verb_is_rejected():
    text = GOOD.replace("| Add a per-group TTFT", "| Improve the per-group TTFT")
    assert codes(text) == ["A4"]


def test_measure_needs_a_number():
    text = GOOD.replace("is under 5 min", "is short")
    assert codes(text) == ["A5"]


def test_unknown_type_and_missing_prevent():
    text = GOOD.replace("| prevent |", "| detect |")
    assert codes(text) == ["A7"]
    assert codes(GOOD.replace("| mitigate |", "| fix |")) == ["A6"]


def test_missing_action_column():
    text = GOOD.replace("| Measure |", "| Result |")
    assert codes(text) == ["A1"]


def test_impact_needs_number():
    text = re.sub(r"(## Impact\n\n).*?\n", r"\1Users were unhappy.\n", GOOD, count=1)
    assert codes(text) == ["I1"]


def test_blame_language_is_flagged():
    assert codes(GOOD + "\nThe engineer was careless.\n") == ["B1"]


def test_metadata_line_required():
    assert codes(GOOD.replace("- Owner: Dana Okoye\n", "")) == ["M1"]


def test_main_exit_codes(tmp_path, capsys):
    assert lint.main(["x", str(HERE / "c27_pm_good.md")]) == 0
    assert lint.main(["x", str(HERE / "c27_pm_bad.md")]) == 1
    assert lint.main(["x"]) == 2
    capsys.readouterr()
