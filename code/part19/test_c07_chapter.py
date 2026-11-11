"""Every yaml, json, bash and python block in chapter 19.7 must equal a file in code/part19."""
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
CHAPTER = HERE.parent.parent / "docs" / "part-19-capstone" / "07-capstone-an-observability-platform.md"


def blocks():
    return re.findall(r"^```(yaml|json|bash|python|sh)\n(.*?)\n```", CHAPTER.read_text(), re.S | re.M)


def test_every_code_block_equals_a_file():
    files = {p.name: p.read_text().rstrip("\n") for p in HERE.glob("c07_*") if p.is_file()}
    bodies = set(files.values())
    bs = blocks()
    assert len(bs) >= 4
    for lang, body in bs:
        assert body in bodies, f"{lang} block does not equal a code/part19/c07_* file: {body[:60]!r}"


def test_chapter_names_every_file_it_shows():
    text = CHAPTER.read_text()
    for name in ("c07_values_kps.yaml", "c07_stack_rules.yaml", "c07_alertmanager.yaml", "c07_values_otel.yaml"):
        assert name in text
