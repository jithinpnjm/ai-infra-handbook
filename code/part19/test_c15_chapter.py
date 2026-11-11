import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import c15_sheet_validator as val  # noqa: E402

HERE = os.path.dirname(__file__)
CHAPTER = os.path.join(HERE, "..", "..", "docs", "part-19-capstone", "15-interview-cheat-sheet.md")
TEXT = open(CHAPTER, encoding="utf-8").read()


def test_chapter_embeds_the_sheet_verbatim():
    sheet = val.strip_anchors(open(val.DEFAULT_SHEET, encoding="utf-8").read()).replace("\n## ", "\n### ")
    sheet = "#" + sheet if sheet.startswith("## ") else sheet
    assert sheet.strip() in TEXT


def test_lab_block_equals_file():
    block = re.search(r"```bash\n(.*?)```", TEXT, re.S).group(1)
    assert block == open(os.path.join(HERE, "c15_lab.sh"), encoding="utf-8").read()


def test_exactly_twenty_checkpoint_questions():
    assert len(re.findall(r"<details><summary>\d+\. ", TEXT)) == 20
    assert TEXT.count("<summary>") == 20


def test_required_sections_in_order():
    heads = [h for h in re.findall(r"^## (.+)$", TEXT, re.M)]
    for a, b in (("Why this matters for AI infrastructure", "Prerequisites and outcomes"),
                 ("Hands-on lab", "How to answer out loud"), ("How to answer out loud", "Exercises"),
                 ("Exercises", "Checkpoint questions"), ("Checkpoint questions", "Sources and review notes")):
        ia = next(i for i, h in enumerate(heads) if a in h)
        ib = next(i for i, h in enumerate(heads) if b in h)
        assert ia < ib, (a, b)


def test_meta_checker_words():
    assert "capstone" in TEXT.lower() and "nvidia-devops" in TEXT and "not run" in TEXT.lower()


def test_no_exclamation_marks_in_prose():
    prose = re.sub(r"```.*?```", "", TEXT, flags=re.S)
    assert "!" not in prose


def test_numbers_quoted_in_chapter_match_script():
    import c15_numbers as n
    block = re.search(r"```text\n(.*?)```", TEXT, re.S).group(1)
    expected = "".join(f"{k:42s} {v}\n" for k, v in n.table())
    assert block == expected
