#!/usr/bin/env python3
"""Mock-interview simulator for chapter 19.15: timed rounds, random draw, rubric, log.

Questions come from c14_question_bank.json (chapter 19.14) when that file exists and has a
usable shape, otherwise from the built-in set below. A bank entry may use the keys
question/q/prompt, topic, id, key_points/keywords and source. Entries without key points
are asked but scored on structure and time only, and the report says so.

The rubric is a keyword heuristic. It checks that your answer mentions the points, says a
number with a unit, names a trade-off, opens with a clarifying step or an assumption, and
stays inside the time limit. It does not judge whether the answer is right. Use it to
rehearse the order of your speech, then check content against the cheat sheet.

Usage:
  c15_simulate_interview.py [--rounds 3] [--seconds 120] [--seed 1] [--topic NAME]
                            [--answers FILE.json] [--log FILE.jsonl] [--bank FILE]
With --answers (a JSON object of question id to answer text) the run is non-interactive.
Otherwise type each answer and finish with an empty line.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass, field, asdict

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BANK = os.path.join(HERE, "c14_question_bank.json")

WEIGHTS = {"coverage": 50, "number": 10, "tradeoff": 10, "opening": 10, "time": 20}
TRADEOFF_WORDS = ("trade-off", "tradeoff", "instead of", "at the cost", "but ", "however", "versus", " vs ")
OPENING_WORDS = ("assume", "assuming", "first i would ask", "clarify", "what is the", "before i answer", "requirements")
NUMBER_RE = re.compile(r"\d[\d,.]*\s?(gb/s|tb/s|gbps|gb|tb|ms|s\b|seconds|minutes?|min\b|hours?|h\b|days?|percent|%|x\b|tokens|gpus?|nodes?|bytes?|b\b)", re.I)

BUILTIN = [
    {"id": "b01", "topic": "linux", "question": "A GPU node has high load but the CPUs are idle. What do you check?",
     "key_points": [["uninterruptible", "d state", "disk"], ["iostat", "await"], ["vmstat", "pressure", "psi"]], "source": "20.5"},
    {"id": "b02", "topic": "linux", "question": "A container exits with code 137. What happened and how do you confirm?",
     "key_points": [["kill", "sigkill", "128"], ["oom", "memory"], ["dmesg", "last state", "constraint_memcg"]], "source": "20.7"},
    {"id": "b03", "topic": "networking", "question": "A training job is far slower on a new fabric. How do you find the layer at fault?",
     "key_points": [["tier", "layer", "ladder"], ["ib_write_bw", "perftest"], ["nccl", "all_reduce_perf", "busbw"], ["socket", "ib_disable", "baseline"]], "source": "19.5"},
    {"id": "b04", "topic": "kubernetes", "question": "A pod is Pending. Walk me through the debug order.",
     "key_points": [["events", "describe"], ["allocatable", "resources", "gpu"], ["taint", "toleration"]], "source": "20.23"},
    {"id": "b05", "topic": "gpu", "question": "How do you split an H100 80 GB with MIG and what does it isolate?",
     "key_points": [["1g.10gb", "profile"], ["seven", "7", "instances"], ["isolat", "hardware"], ["time-slicing", "time slicing"]], "source": "19.8"},
    {"id": "b06", "topic": "training", "question": "How long does it take to train a 70B model on 100B tokens on 128 H100 GPUs?",
     "key_points": [["6", "parameters", "tokens"], ["4.2e22", "flops"], ["mfu", "40"], ["9.6", "days"]], "source": "9.10"},
    {"id": "b07", "topic": "training", "question": "How often should a large job checkpoint?",
     "key_points": [["young", "daly", "sqrt", "square root"], ["mtbf", "interruption"], ["cost", "write", "blocking"], ["async"]], "source": "19.4"},
    {"id": "b08", "topic": "inference", "question": "How much KV cache memory does one request need and how many fit?",
     "key_points": [["2", "layers", "heads", "head dim"], ["bytes per token", "per token"], ["weights", "overhead", "0.9", "usable"]], "source": "20.12"},
    {"id": "b09", "topic": "observability", "question": "Design the alerts for a 99.9 percent token API.",
     "key_points": [["burn"], ["14.4"], ["short window", "5 min", "long window", "1 h"], ["ticket"]], "source": "20.19"},
    {"id": "b10", "topic": "failure", "question": "Xid 79 appears on three nodes at once. What do you do?",
     "key_points": [["catalog", "restart"], ["pattern", "shared cause", "rollout", "driver"], ["cordon", "drain"], ["rate", "breaker", "limit"]], "source": "19.6"},
    {"id": "b11", "topic": "design", "question": "Design a multi-tenant LLM inference API in 45 minutes.",
     "key_points": [["requirements", "estimate"], ["gateway", "token limit"], ["router", "cache"], ["autoscal"], ["observab", "rollout"]], "source": "20.13"},
    {"id": "b12", "topic": "behavioural", "question": "Tell me about a production incident you led.",
     "key_points": [["situation", "impact"], ["action", "mitigat", "rollback", "roll back"], ["result", "measured", "minutes"], ["learn", "changed", "post-mortem"]], "source": "20.27"},
]


@dataclass
class Question:
    id: str
    topic: str
    text: str
    key_points: list[list[str]]
    source: str = ""


def _norm_points(raw) -> list[list[str]]:
    pts: list[list[str]] = []
    for item in raw or []:
        if isinstance(item, str):
            pts.append([item.lower()])
        elif isinstance(item, (list, tuple)):
            pts.append([str(x).lower() for x in item if str(x).strip()])
    return [p for p in pts if p]


def load_bank(path: str | None = None) -> tuple[list[Question], str]:
    """Return the questions and a label saying where they came from."""
    path = path or DEFAULT_BANK
    if os.path.exists(path):
        try:
            data = json.load(open(path, encoding="utf-8"))
            if isinstance(data, dict):
                for key in ("questions", "items", "bank"):
                    if isinstance(data.get(key), list):
                        data = data[key]
                        break
            out = []
            for i, e in enumerate(data if isinstance(data, list) else []):
                if not isinstance(e, dict):
                    continue
                text = e.get("question") or e.get("q") or e.get("prompt")
                if not text:
                    continue
                out.append(Question(str(e.get("id", f"q{i}")), str(e.get("topic", "general")), str(text),
                                    _norm_points(e.get("key_points") or e.get("keywords")), str(e.get("source", ""))))
            if out:
                return out, f"bank:{os.path.basename(path)}"
        except (OSError, ValueError):
            pass
    return [Question(b["id"], b["topic"], b["question"], _norm_points(b["key_points"]), b["source"]) for b in BUILTIN], "built-in"


def draw(questions: list[Question], n: int, seed: int | None = None, topic: str | None = None) -> list[Question]:
    pool = [q for q in questions if topic is None or q.topic == topic]
    if not pool:
        raise ValueError(f"no questions for topic {topic!r}")
    rng = random.Random(seed)
    return rng.sample(pool, min(n, len(pool)))


@dataclass
class Score:
    coverage: float
    number: float
    tradeoff: float
    opening: float
    time: float
    total: float
    missed: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def score_answer(q: Question, answer: str, elapsed: float, limit: float) -> Score:
    low = " " + answer.lower() + " "
    notes: list[str] = []
    missed: list[str] = []
    if q.key_points:
        hit = 0
        for group in q.key_points:
            if any(k in low for k in group):
                hit += 1
            else:
                missed.append(group[0])
        cov = WEIGHTS["coverage"] * hit / len(q.key_points)
    else:
        cov = 0.0
        notes.append("no key points for this question: coverage not scored")
    num = WEIGHTS["number"] if NUMBER_RE.search(answer) else 0.0
    if not num:
        notes.append("no number with a unit")
    trade = WEIGHTS["tradeoff"] if any(w in low for w in TRADEOFF_WORDS) else 0.0
    if not trade:
        notes.append("no trade-off named")
    opening = WEIGHTS["opening"] if any(w in low[:300] for w in OPENING_WORDS) else 0.0
    if not opening:
        notes.append("no clarifying step or assumption at the start")
    if elapsed <= limit:
        tm = float(WEIGHTS["time"])
    elif elapsed <= 1.5 * limit:
        tm = WEIGHTS["time"] / 2
        notes.append("over time")
    else:
        tm = 0.0
        notes.append("far over time")
    if not answer.strip():
        cov = num = trade = opening = 0.0
        notes.append("empty answer")
    total = cov + num + trade + opening + tm
    return Score(cov, num, trade, opening, tm, total, missed, notes)


def run_session(questions, get_answer, limit=120.0, clock=time.monotonic, log_path=None, source="built-in", out=print):
    """Ask each question. get_answer(q) returns the answer text. Returns the session record."""
    results = []
    for i, q in enumerate(questions, start=1):
        out(f"\nRound {i} [{q.topic}] ({int(limit)} s): {q.text}")
        t0 = clock()
        answer = get_answer(q)
        elapsed = clock() - t0
        sc = score_answer(q, answer, elapsed, limit)
        rec = {"id": q.id, "topic": q.topic, "source": q.source, "elapsed_s": round(elapsed, 1),
               "limit_s": limit, "score": round(sc.total, 1), "parts": {k: v for k, v in asdict(sc).items() if k in WEIGHTS},
               "missed": sc.missed, "notes": sc.notes, "answer_words": len(answer.split())}
        results.append(rec)
        out(f"  score {rec['score']}/100, {rec['elapsed_s']} s, missed: {', '.join(sc.missed) or 'none'}")
        for n in sc.notes:
            out(f"  note: {n}")
    mean = sum(r["score"] for r in results) / len(results) if results else 0.0
    session = {"when": time.strftime("%Y-%m-%dT%H:%M:%S"), "bank": source, "rounds": results, "mean": round(mean, 1)}
    if log_path:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(session) + "\n")
    out(f"\nSession mean {session['mean']}/100 over {len(results)} rounds")
    return session


def interactive_answer(q: Question) -> str:
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--seconds", type=float, default=120.0)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--topic")
    ap.add_argument("--answers")
    ap.add_argument("--log", default="c15_session_log.jsonl")
    ap.add_argument("--bank")
    a = ap.parse_args(argv)
    questions, source = load_bank(a.bank)
    picked = draw(questions, a.rounds, a.seed, a.topic)
    print(f"Question source: {source}")
    if a.answers:
        answers = json.load(open(a.answers, encoding="utf-8"))
        get = lambda q: answers.get(q.id, "")  # noqa: E731
    else:
        get = interactive_answer
    run_session(picked, get, a.seconds, log_path=a.log, source=source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
