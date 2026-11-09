# code/part20/test_c29_flashcards.py
import csv
import datetime as dt

from c29_flashcards import chapter_id, collect, main, parse_drills

FRONT = '---\nid: "c20-77"\ntitle: "20.77 Fixture"\n---\n'

SHAPE_A = FRONT + """# t
## Core
<details><summary>1. Not a drill?</summary>
ignore me
</details>

## Drill questions

Answer each.

<details><summary>1. Why A?</summary>

Because A.

</details>

<details><summary>2. Why `B`?</summary>
Because B.
Second line.
</details>

## Common mistakes
<details><summary>9. After the section?</summary>x</details>
"""

SHAPE_B = FRONT + """## Drill questions

<details>
<summary>1. First?</summary>
One.
</details>

<details>
<summary>2. Second?</summary>
Two.
</details>
"""

SHAPE_C = FRONT + """## Drill questions

1. What is C?

<details><summary>Answer</summary>

It is C.

</details>

2. What is D?
<details><summary>Answer</summary>
It is D.
</details>
"""


def test_shape_a_and_section_boundaries():
    cards = parse_drills(SHAPE_A)
    assert [c[0] for c in cards] == [1, 2]
    assert cards[1][1] == "Why `B`?"
    assert cards[1][2] == "Because B.\nSecond line."


def test_shape_b_multiline_details():
    cards = parse_drills(SHAPE_B)
    assert [(c[0], c[1], c[2]) for c in cards] == [(1, "First?", "One."), (2, "Second?", "Two.")]


def test_shape_c_numbered_line_then_answer():
    cards = parse_drills(SHAPE_C)
    assert [(c[0], c[1]) for c in cards] == [(1, "What is C?"), (2, "What is D?")]
    assert cards[0][2] == "It is C."


def test_no_drill_section_gives_nothing():
    assert parse_drills(FRONT + "## Other\ntext\n") == []


def test_chapter_id():
    assert chapter_id(FRONT) == "20.77"
    assert chapter_id("no front matter") is None


def test_collect_and_csv(tmp_path):
    (tmp_path / "03-a.md").write_text(SHAPE_A, encoding="utf-8")
    (tmp_path / "04-b.md").write_text(SHAPE_C.replace("c20-77", "c20-4"), encoding="utf-8")
    (tmp_path / "_category_.json").write_text("{}")
    (tmp_path / "notes.md").write_text(SHAPE_A, encoding="utf-8")  # not numbered, skipped
    out = tmp_path / "cards.csv"
    main([str(tmp_path), str(out), "--start", "2026-11-09"])
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert [r["card_id"] for r in rows] == ["20.77-Q1", "20.77-Q2", "20.4-Q1", "20.4-Q2"]
    assert all(r["box"] == "1" and r["due"] == "2026-11-09" for r in rows)
    assert "answer" not in rows[0]


def test_answers_flag(tmp_path):
    (tmp_path / "03-a.md").write_text(SHAPE_A, encoding="utf-8")
    rows = collect(tmp_path, with_answers=True, start=dt.date(2026, 1, 1))
    assert rows[1]["answer"] == "Because B. Second line."
