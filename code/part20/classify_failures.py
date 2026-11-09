# code/part20/classify_failures.py
"""Usage: python3 classify_failures.py readings.json [--top N]
readings.json: {"current": {...}, "baseline": {...}} using the keys in failure_rules.py."""
import argparse
import json

from failure_model import rank
from failure_rules import RULES


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--top", type=int, default=3)
    args = p.parse_args(argv)
    data = json.load(open(args.path))
    found = rank(RULES, data["current"], data.get("baseline"))[: args.top]
    if not found:
        print("No signature matched. Collect more readings.")
        return 1
    for i, h in enumerate(found, 1):
        print(f"{i}. {h.cause}  score={h.score}")
        print(f"   evidence: {'; '.join(h.evidence)}")
        print(f"   confirm: {h.confirm}")
        print(f"   now: {h.mitigate_now}")
        print(f"   later: {h.fix_later}")
        if h.unknown:
            print(f"   not measured: {'; '.join(h.unknown)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
