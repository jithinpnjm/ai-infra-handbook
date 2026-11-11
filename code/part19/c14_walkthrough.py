#!/usr/bin/env python3
"""Present a random mixed set of N questions by topic and level from the 19.14 bank.

The set is spread over topics in round-robin order, so a short set still touches many
topics. Levels follow the weights (core 40, senior 45, stretch 15 percent) unless you
filter with --level. The same --seed gives the same set.

Run: python3 c14_walkthrough.py --n 10 [--topic linux --topic storage] [--level senior] [--seed 1] [--answers]
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import defaultdict

import c14_bank

LEVEL_WEIGHTS = {"core": 0.40, "senior": 0.45, "stretch": 0.15}


def pick_set(bank: dict, n: int, topics=None, levels=None, seed=None) -> list[dict]:
    if n < 1:
        raise ValueError("n must be at least 1")
    rng = random.Random(seed)
    pool = [q for q in bank["questions"]
            if (not topics or q["topic"] in topics) and (not levels or q["difficulty"] in levels)]
    if n > len(pool):
        raise ValueError(f"asked for {n} questions but only {len(pool)} match the filters")
    by_topic = defaultdict(list)
    for q in pool:
        by_topic[q["topic"]].append(q)
    for lst in by_topic.values():
        rng.shuffle(lst)
    order = sorted(by_topic)
    rng.shuffle(order)
    # Level targets: weights over the levels that are allowed, as whole numbers summing to n.
    allowed = [lv for lv in c14_bank.LEVELS if not levels or lv in levels]
    total_w = sum(LEVEL_WEIGHTS[lv] for lv in allowed)
    target = {lv: int(n * LEVEL_WEIGHTS[lv] / total_w) for lv in allowed}
    for lv in sorted(allowed, key=lambda x: -LEVEL_WEIGHTS[x]):
        if sum(target.values()) >= n:
            break
        target[lv] += 1
    chosen: list[dict] = []
    counts = defaultdict(int)
    # Pass 1 honours the level targets, pass 2 fills any gap from whatever is left.
    for enforce in (True, False):
        progress = True
        while len(chosen) < n and progress:
            progress = False
            for t in order:
                if len(chosen) >= n:
                    break
                for i, q in enumerate(by_topic[t]):
                    if enforce and counts[q["difficulty"]] >= target.get(q["difficulty"], 0):
                        continue
                    chosen.append(by_topic[t].pop(i))
                    counts[q["difficulty"]] += 1
                    progress = True
                    break
    rng.shuffle(chosen)
    return chosen


def render(q: dict, number: int, answers: bool = False) -> str:
    lines = [f"{number}. [{q['id']}] {q['topic']} / {q['difficulty']}", f"   {q['question']}",
             f"   Chapter: {q['link']}"]
    if answers:
        lines += [f"   Model answer: {q['model_answer']}",
                  "   Strong answer contains: " + "; ".join(q["strong_answer_contains"]),
                  f"   Weak answer: {q['weak_answer']}", f"   Follow-up: {q['follow_up']}"]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank", default=str(c14_bank.DEFAULT_BANK))
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--topic", action="append", choices=c14_bank.TOPICS)
    ap.add_argument("--level", action="append", choices=c14_bank.LEVELS)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--answers", action="store_true")
    a = ap.parse_args(argv)
    bank = c14_bank.load_bank(a.bank)
    try:
        qs = pick_set(bank, a.n, a.topic, a.level, a.seed)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for i, q in enumerate(qs, 1):
        print(render(q, i, a.answers))
    return 0


if __name__ == "__main__":
    sys.exit(main())
