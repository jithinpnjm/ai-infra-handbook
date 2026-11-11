import os
import sys

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import c15_sheet_validator as val  # noqa: E402

DOCS = val.DEFAULT_DOCS
SHEET = open(val.DEFAULT_SHEET, encoding="utf-8").read()


def test_real_sheet_is_valid():
    rep = val.validate(SHEET, DOCS)
    assert rep.problems == []
    assert rep.rows >= 100


def test_every_row_has_a_resolvable_source():
    for row in val.parse_sheet(SHEET):
        assert row.ids, row.text
        for cid in row.ids:
            assert val.chapter_path(cid, DOCS), (cid, row.text)


def test_every_section_is_present():
    sections = {r.section.split(".")[0] for r in val.parse_sheet(SHEET)}
    assert sections >= set("ABCDEFGHIJKL")


def test_most_rows_carry_anchors():
    rows = val.parse_sheet(SHEET)
    assert sum(1 for r in rows if r.anchors) == len(rows)


def test_row_without_source_fails():
    bad = "| Fact | Source |\n|---|---|\n| A claim with no source | |\n"
    rep = val.validate(bad, DOCS)
    assert any("no source id" in p for p in rep.problems)


def test_row_with_unresolvable_id_fails():
    bad = "| Fact | Source |\n|---|---|\n| A claim | 99.9 |\n"
    assert any("does not resolve" in p for p in val.validate(bad, DOCS).problems)


def test_row_with_malformed_id_fails():
    bad = "| Fact | Source |\n|---|---|\n| A claim | see chapter 5 |\n"
    assert any("not a chapter id" in p for p in val.validate(bad, DOCS).problems)


def test_anchor_missing_from_chapter_fails():
    bad = "| Fact | Source |\n|---|---|\n| A claim | 20.3 | <!--a: zzz-not-in-chapter-zzz-->\n"
    assert any("anchor" in p for p in val.validate(bad, DOCS).problems)


def test_anchor_present_passes():
    ok = "| Fact | Source |\n|---|---|\n| A claim | 20.3 | <!--a: dmesg -T | tail-->\n"
    assert val.validate(ok, DOCS).ok


def test_unverified_word_is_rejected():
    bad = "| Fact | Source |\n|---|---|\n| Unverified claim | 20.3 |\n"
    assert any("unverified" in p for p in val.validate(bad, DOCS).problems)


def test_empty_sheet_fails():
    assert not val.validate("no tables here", DOCS).ok


def test_strip_anchors_removes_comments():
    assert "<!--" not in val.strip_anchors(SHEET)
    assert "| 20.3 |" in val.strip_anchors(SHEET)


@pytest.mark.parametrize("cid,expected", [("20.3", True), ("19.15", True), ("5.9", True), ("0.1", True), ("77.1", False), ("x", False)])
def test_chapter_path(cid, expected):
    assert bool(val.chapter_path(cid, DOCS)) is expected
