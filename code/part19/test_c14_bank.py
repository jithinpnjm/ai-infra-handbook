import copy
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import c14_bank  # noqa: E402


@pytest.fixture(scope="module")
def bank():
    return c14_bank.load_bank()


def test_shipped_bank_is_valid(bank):
    assert c14_bank.validate(bank) == []


def test_size_topics_and_levels(bank):
    qs = bank["questions"]
    assert 150 <= len(qs) <= 200
    assert {q["topic"] for q in qs} == set(c14_bank.TOPICS)
    assert {q["difficulty"] for q in qs} == set(c14_bank.LEVELS)


def test_every_link_resolves(bank):
    for q in bank["questions"]:
        assert (c14_bank.REPO / q["link"]).is_file(), q["id"]


def test_ids_unique(bank):
    ids = [q["id"] for q in bank["questions"]]
    assert len(ids) == len(set(ids))


def test_no_company_claims(bank):
    text = json.dumps(bank).lower()
    for phrase in c14_bank.FORBIDDEN:
        assert phrase not in text


def test_volume20_pointer_resolves(bank):
    base = c14_bank.REPO / bank["volume20_drills"]["path"]
    assert base.is_dir()
    for prefix in bank["volume20_drills"]["chapters"]:
        assert list(base.glob(prefix + "-*.md")), prefix


@pytest.mark.parametrize("field", ["topic", "difficulty", "model_answer", "follow_up", "weak_answer", "link"])
def test_missing_field_is_reported(bank, field):
    bad = copy.deepcopy(bank)
    bad["questions"][0][field] = ""
    errs = c14_bank.validate(bad)
    assert any(bad["questions"][0]["id"] in e for e in errs)


def test_unknown_topic_and_level_rejected(bank):
    bad = copy.deepcopy(bank)
    bad["questions"][0]["topic"] = "cooking"
    bad["questions"][1]["difficulty"] = "easy"
    errs = c14_bank.validate(bad)
    assert any("unknown topic" in e for e in errs)
    assert any("difficulty" in e for e in errs)


def test_broken_link_rejected(bank):
    bad = copy.deepcopy(bank)
    bad["questions"][0]["link"] = "docs/part-01-linux/99-does-not-exist.md"
    errs = c14_bank.validate(bad)
    assert any("does not resolve" in e for e in errs)


def test_duplicate_id_and_company_claim_rejected(bank):
    bad = copy.deepcopy(bank)
    bad["questions"][1]["id"] = bad["questions"][0]["id"]
    bad["questions"][2]["model_answer"] += " Nebius asks this."
    errs = c14_bank.validate(bad)
    assert any("duplicate id" in e for e in errs)
    assert any("company-claim" in e for e in errs)


def test_count_gate(bank):
    small = copy.deepcopy(bank)
    small["questions"] = small["questions"][:20]
    assert any("question count" in e for e in c14_bank.validate(small))
    assert c14_bank.validate(small, strict_counts=False) == []


def test_main_exit_codes(tmp_path, bank, capsys):
    assert c14_bank.main(["c14_bank.py"]) == 0
    bad = copy.deepcopy(bank)
    bad["questions"][0]["follow_up"] = ""
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad))
    assert c14_bank.main(["c14_bank.py", str(p)]) == 1


def test_worked_numbers_quoted_in_answers():
    """Arithmetic quoted in the bank, recomputed here."""
    assert 10e9 / 8 * 0.070 / 1e6 == pytest.approx(87.5)             # BDP in MB
    assert 4 / 0.070 == pytest.approx(57.1, abs=0.1)                  # MB/s for a 4 MB window
    assert 13e9 * 2 / 1e9 == 26.0 and 26 / 3350 * 1000 == pytest.approx(7.76, abs=0.01)
    tau = (2 * 28800 * 180) ** 0.5
    assert round(tau) == 3220 and round(tau - 180) == 3040
    assert 100000 * 0.4 * 0.8 == 32000
    per_hour = 2100 * 3600 / 1e6
    full_cost = 12.40 / per_hour
    assert full_cost == pytest.approx(1.64, abs=0.01)
    assert full_cost / 4.00 == pytest.approx(0.41, abs=0.005)
    assert per_hour * 24 * (full_cost / 4.0) == pytest.approx(74.4, abs=0.2)
    assert 28.8e6 / (464 * 3 + 60 * 2 + 100) == pytest.approx(17866, abs=1)
    assert 28 / 40 == 0.70 and 28 / 32 == 0.875
    assert 12 * 70 == 840 and 140 + 140 / 8 + 560 / 8 == pytest.approx(227.5)
