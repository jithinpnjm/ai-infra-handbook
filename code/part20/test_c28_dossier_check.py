import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import c28_dossier_check as d  # noqa: E402

HERE = os.path.dirname(__file__)

GOOD = """# Dossier

## Context
- Why: the old deploy took 40 minutes and broke twice a week.

## My role and the team
- I owned the pipeline, with 3 other engineers.

## Constraints
- Zero downtime allowed during 2 business hours.

## Numbers
- 120 services
- 35 deploys a day
- Error rate 0.8 percent before

## Architecture
- A commit builds an image, a controller rolls it out.

## Decisions

### Decision: canary rollout
- Chosen: 10 percent canary
- Alternatives considered:
  - blue green
  - big bang
- Why: blast radius of 10 percent of traffic
- Cost accepted: slower deploys by 5 minutes

### Decision: shared runners
- Chosen: shared pool
- Alternatives considered: dedicated runners; per team runners
- Why: cost
- Cost accepted: noisy neighbours

### Decision: store state in git
- Chosen: git
- Alternatives considered:
  - database
  - object store
- Why: audit trail
- Cost accepted: slow reads

## Failures

### Failure: bad config rollout
- What broke: 5 percent of requests failed
- How it was detected: alert after 7 minutes
- Root cause: missing schema check
- What changed afterwards: validation in CI

## What I would change
- Add progressive checks.

## Metrics of success
- Deploy time 40 minutes before, 12 after
- Error rate 0.8 before, 0.3 after
"""


def kinds(text):
    return {f["kind"] for f in d.check(text)}


def test_good_dossier_is_clean():
    assert d.check(GOOD) == []


def test_blank_template_reports_everything_unfilled():
    text = open(os.path.join(HERE, "c28_dossier_template.md")).read()
    k = kinds(text)
    assert "placeholder" in k and "empty_section" in k
    assert "decision_no_alternatives" in k


def test_missing_section_named():
    text = GOOD.replace("## What I would change\n- Add progressive checks.\n", "")
    found = d.check(text)
    assert any(f["kind"] == "missing_section" and "change" in f["message"]
               for f in found)


def test_decision_with_one_alternative_flagged():
    text = GOOD.replace("  - blue green\n", "")
    found = [f for f in d.check(text) if f["kind"] == "decision_no_alternatives"]
    assert len(found) == 1 and "canary" in found[0]["message"]


def test_decision_without_alternatives_line_flagged():
    text = GOOD.replace("- Alternatives considered: dedicated runners; "
                        "per team runners\n", "")
    assert "decision_no_alternatives" in kinds(text)


def test_inline_semicolon_alternatives_count_as_two():
    found = d.check(GOOD)
    assert not [f for f in found if "runners" in f["message"]]


def test_unquantified_claim_flagged_and_quantified_not():
    bad = GOOD.replace("- Add progressive checks.",
                       "- Make it much faster and a lot more reliable.")
    found = [f for f in d.check(bad) if f["kind"] == "unquantified"]
    assert len(found) == 1
    ok = GOOD.replace("- Add progressive checks.", "- Cut deploy time by 70 percent.")
    assert "unquantified" not in kinds(ok)


def test_too_few_numbers_in_numbers_section():
    text = GOOD.replace("- 120 services\n- 35 deploys a day\n", "- many services\n")
    assert "too_few_numbers" in kinds(text)


def test_failure_missing_root_cause_flagged():
    text = GOOD.replace("- Root cause: missing schema check\n", "")
    found = [f for f in d.check(text) if f["kind"] == "entry_incomplete"]
    assert found and "root cause" in found[0]["message"]


def test_html_comments_ignored_and_line_numbers_kept():
    text = "<!-- much faster\nTODO -->\n" + GOOD
    assert d.check(text) == []


def test_main_exit_codes(tmp_path, capsys):
    good = tmp_path / "good.md"
    good.write_text(GOOD)
    assert d.main(["x", str(good)]) == 0
    bad = tmp_path / "bad.md"
    bad.write_text("# Empty\n")
    assert d.main(["x", str(bad), "--json"]) == 1
    assert "missing_section" in capsys.readouterr().out
