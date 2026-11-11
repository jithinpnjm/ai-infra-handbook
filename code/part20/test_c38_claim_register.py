import copy
from datetime import date

import pytest

from c38_claim_register import (count_by_tag, load_register, main, validate_entry,
                                validate_register)

TODAY = date(2026, 11, 11)
GOOD = {
    "id": "x1", "claim": "a claim", "source_url": "https://example.com/a",
    "date": "2026-11-11", "tag": "official",
}
GOOD_VENDOR = dict(GOOD, id="x2", tag="vendor", workload="agent trajectories, 3 replicas")


def test_good_entries_pass():
    assert validate_entry(GOOD, TODAY) == []
    assert validate_entry(GOOD_VENDOR, TODAY) == []


@pytest.mark.parametrize("field", ["id", "claim", "source_url", "date", "tag"])
def test_missing_required_field_fails(field):
    bad = copy.deepcopy(GOOD)
    del bad[field]
    assert any(f"missing {field}" in p for p in validate_entry(bad, TODAY))


@pytest.mark.parametrize("field", ["source_url", "date", "tag"])
def test_blank_required_field_fails(field):
    bad = dict(GOOD, **{field: "   "})
    assert validate_entry(bad, TODAY)


def test_unknown_tag_fails():
    assert any("unknown tag" in p for p in validate_entry(dict(GOOD, tag="rumour"), TODAY))


def test_bad_and_future_dates_fail():
    assert any("YYYY-MM-DD" in p for p in validate_entry(dict(GOOD, date="11/11/2026"), TODAY))
    assert any("future" in p for p in validate_entry(dict(GOOD, date="2026-12-01"), TODAY))


def test_url_must_be_https():
    assert validate_entry(dict(GOOD, source_url="http://example.com"), TODAY)
    assert validate_entry(dict(GOOD, source_url="nebius blog"), TODAY)


@pytest.mark.parametrize("tag", ["vendor", "third-party", "report"])
def test_workload_required_for_marketing_style_tags(tag):
    bad = dict(GOOD, tag=tag)
    assert any("requires a workload" in p for p in validate_entry(bad, TODAY))
    assert validate_entry(dict(bad, workload="w"), TODAY) == []


def test_official_needs_no_workload():
    assert validate_entry(GOOD, TODAY) == []


def test_quote_length_limit():
    assert validate_entry(dict(GOOD, quote="one two three"), TODAY) == []
    long_quote = " ".join(["w"] * 16)
    assert any("quote" in p for p in validate_entry(dict(GOOD, quote=long_quote), TODAY))


def test_entry_must_be_object():
    assert validate_entry("text", TODAY) == ["entry is not an object"]


def test_register_shape_and_duplicates():
    assert validate_register([], TODAY)
    assert validate_register({"entries": []}, TODAY)
    dup = {"entries": [GOOD, dict(GOOD)]}
    assert any("duplicate id" in p for p in validate_register(dup, TODAY))
    assert validate_register({"entries": [GOOD, GOOD_VENDOR]}, TODAY) == []


def test_shipped_register_is_valid():
    data = load_register()
    assert validate_register(data, TODAY) == []
    assert len(data["entries"]) >= 40


def test_shipped_register_covers_the_evidence_classes():
    counts = count_by_tag(load_register())
    for tag in ("official", "vendor", "source-code", "third-party"):
        assert counts.get(tag, 0) >= 1


def test_every_vendor_claim_names_a_workload():
    for entry in load_register()["entries"]:
        if entry["tag"] == "vendor":
            assert entry["workload"].strip(), entry["id"]


def test_main_exit_codes(tmp_path):
    good = tmp_path / "good.json"
    good.write_text('{"entries": [{"id": "a", "claim": "c", "source_url": "https://x.io", '
                    '"date": "2026-01-01", "tag": "official"}]}')
    bad = tmp_path / "bad.json"
    bad.write_text('{"entries": [{"id": "a", "claim": "c", "tag": "official"}]}')
    assert main(["prog", str(good)]) == 0
    assert main(["prog", str(bad)]) == 1
