#!/usr/bin/env python3
"""Load and validate the 19.14 interview question bank (c14_question_bank.json).

Run: python3 c14_bank.py [bank.json]   (exit 0 when valid, 1 otherwise)
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_BANK = HERE / "c14_question_bank.json"

TOPICS = [
    "linux", "networking", "python_automation", "kubernetes", "gpu_cuda",
    "gpu_on_kubernetes", "ai_networking", "storage", "training", "inference",
    "mlops", "observability_ops", "security", "system_design", "behavioural",
    "slurm_hpc_hardware",
]
LEVELS = ["core", "senior", "stretch"]
REQUIRED_TEXT = ["id", "topic", "difficulty", "question", "chapter", "link",
                 "model_answer", "weak_answer", "follow_up", "basis"]
MIN_QUESTIONS, MAX_QUESTIONS = 150, 200
# A bank entry must never claim that a company asks the question.
FORBIDDEN = ["is asked by", "was asked by", "nebius asks", "nvidia asks",
             "google asks", "will be asked at"]


def load_bank(path: pathlib.Path | str = DEFAULT_BANK) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate(bank: dict, root: pathlib.Path = REPO, strict_counts: bool = True) -> list[str]:
    """Return a list of error strings. An empty list means the bank is valid."""
    errors: list[str] = []
    questions = bank.get("questions")
    chapters = bank.get("chapters", {})
    if not isinstance(questions, list) or not questions:
        return ["bank has no questions list"]
    if strict_counts and not MIN_QUESTIONS <= len(questions) <= MAX_QUESTIONS:
        errors.append(f"question count {len(questions)} outside {MIN_QUESTIONS}-{MAX_QUESTIONS}")
    seen: set[str] = set()
    for q in questions:
        qid = q.get("id", "<no id>")
        if qid in seen:
            errors.append(f"{qid}: duplicate id")
        seen.add(qid)
        for field in REQUIRED_TEXT:
            if not isinstance(q.get(field), str) or not q[field].strip():
                errors.append(f"{qid}: missing or empty {field}")
        if q.get("topic") not in TOPICS:
            errors.append(f"{qid}: unknown topic {q.get('topic')!r}")
        if q.get("difficulty") not in LEVELS:
            errors.append(f"{qid}: difficulty must be one of {LEVELS}")
        strong = q.get("strong_answer_contains")
        if not isinstance(strong, list) or len(strong) < 2 or not all(isinstance(s, str) and s.strip() for s in strong):
            errors.append(f"{qid}: strong_answer_contains needs at least 2 non-empty items")
        link = q.get("link", "")
        if link and not (root / link).is_file():
            errors.append(f"{qid}: link does not resolve to a file: {link}")
        ch = q.get("chapter")
        if ch not in chapters:
            errors.append(f"{qid}: chapter {ch!r} not in chapter registry")
        elif chapters[ch].get("path") != link:
            errors.append(f"{qid}: link differs from registry path for chapter {ch}")
        text = " ".join(str(q.get(f, "")) for f in ("question", "model_answer", "weak_answer", "follow_up")).lower()
        for phrase in FORBIDDEN:
            if phrase in text:
                errors.append(f"{qid}: company-claim wording {phrase!r}")
    for ch, info in chapters.items():
        if not (root / info.get("path", "")).is_file():
            errors.append(f"registry chapter {ch}: path missing")
    if strict_counts:
        have = {q.get("topic") for q in questions}
        for t in TOPICS:
            if t not in have:
                errors.append(f"topic {t} has no questions")
        have_levels = {q.get("difficulty") for q in questions}
        for lv in LEVELS:
            if lv not in have_levels:
                errors.append(f"level {lv} has no questions")
    return errors


def summary(bank: dict) -> str:
    qs = bank["questions"]
    topics = Counter(q["topic"] for q in qs)
    levels = Counter(q["difficulty"] for q in qs)
    lines = [f"{len(qs)} questions, {len(bank['chapters'])} chapters linked"]
    lines += [f"  {t}: {topics[t]}" for t in TOPICS if t in topics]
    lines += [f"  level {lv}: {levels[lv]}" for lv in LEVELS]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else DEFAULT_BANK
    bank = load_bank(path)
    errs = validate(bank)
    print(summary(bank))
    for e in errs:
        print("ERROR:", e)
    print("VALID" if not errs else f"INVALID ({len(errs)} errors)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
