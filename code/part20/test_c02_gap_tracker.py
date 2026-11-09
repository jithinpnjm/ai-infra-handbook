import pytest
from c02_gap_tracker import (Row, count_lines, main, parse_confidence, parse_table,
                             render, study_order, warnings)

TABLE = """Some intro text.

| Skill | Posting lines | Confidence (1-5) | Evidence | Chapter to study |
| --- | --- | --- | --- | --- |
| Terraform | R4, Q1 | 2 | used it a year | 20.24 |
| SLOs | R1, R6, Q3 | 2 | | 20.19 |
| Bash | R6, Q2 | 5 | wrote the deploy tool | 20.7 |
| vLLM | R1, R3, Q5 | | | 20.22 |

Text after the table.
"""


def test_count_lines_list_number_and_empty():
    assert count_lines("R3, Q1, R8") == 3
    assert count_lines("R3;Q1") == 2
    assert count_lines("4") == 4
    assert count_lines("") == 1
    assert count_lines("0") == 1


def test_parse_confidence_blank_and_valid():
    assert parse_confidence("", "x") is None
    assert parse_confidence("?", "x") is None
    assert parse_confidence(" 3 ", "x") == 3


@pytest.mark.parametrize("bad", ["0", "6", "high", "3.5"])
def test_parse_confidence_rejects(bad):
    with pytest.raises(ValueError, match="1 to 5"):
        parse_confidence(bad, "x")


def test_parse_table_skips_separator_and_stops_at_text():
    rows = parse_table(TABLE)
    assert [r.skill for r in rows] == ["Terraform", "SLOs", "Bash", "vLLM"]
    assert rows[0].lines == 2 and rows[1].lines == 3
    assert rows[3].confidence is None


def test_parse_table_without_table_raises():
    with pytest.raises(ValueError, match="no table"):
        parse_table("just text\n| a | b |\n| - | - |\n")


def test_parse_table_bad_confidence_raises():
    bad = TABLE.replace("| 2 | used", "| 9 | used")
    with pytest.raises(ValueError):
        parse_table(bad)


def test_priority_is_gap_times_lines():
    assert Row("a", 2, 3, "", "").priority == 9
    assert Row("a", 5, 3, "", "").priority == 0
    assert Row("a", None, 3, "", "").priority == 0


def test_study_order_weights_by_lines_and_excludes_unrated():
    order = study_order(parse_table(TABLE))
    assert [r.skill for r in order] == ["SLOs", "Terraform", "Bash"]
    assert [r.priority for r in order] == [9, 6, 0]


def test_study_order_tie_breaks_on_lower_confidence_then_name():
    rows = [Row("b", 3, 2, "", ""), Row("a", 3, 2, "", ""), Row("c", 1, 1, "", "")]
    # priorities: b=4, a=4, c=4 -> lower confidence first, then name
    assert [r.skill for r in study_order(rows)] == ["c", "a", "b"]


def test_warnings_for_unrated_and_unevidenced_high_confidence():
    w = warnings(parse_table(TABLE))
    assert "not rated: vLLM" in w
    assert not any("Bash" in x for x in w)
    rows = [Row("Go", 4, 1, "", "")]
    assert warnings(rows) == ["confidence 4 without evidence: Go"]


def test_render_lines_and_warnings():
    out = render(parse_table(TABLE)).splitlines()
    assert out[0].startswith(" 1. SLOs | priority 9 (5-2)x3 | study: 20.19")
    assert out[-1] == "warning: not rated: vLLM"


def test_main_prints_order(tmp_path, capsys):
    f = tmp_path / "a.md"
    f.write_text(TABLE)
    assert main(["prog", str(f)]) == 0
    assert "SLOs" in capsys.readouterr().out


def test_main_errors(tmp_path, capsys):
    f = tmp_path / "a.md"
    f.write_text("nothing here")
    assert main(["prog", str(f)]) == 1
    assert "error:" in capsys.readouterr().err
    assert main(["prog"]) == 2


def test_template_parses_and_is_unrated():
    import pathlib
    text = (pathlib.Path(__file__).parent / "c02_assessment_template.md").read_text()
    rows = parse_table(text)
    assert len(rows) == 16
    assert all(r.confidence is None for r in rows)
    assert study_order(rows) == []
