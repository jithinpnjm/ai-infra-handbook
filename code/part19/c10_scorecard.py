"""Assessment scorecard for chapter 19.10.

Every score needs a short piece of evidence. A score without evidence is
rejected, because an assessment that says "2" without saying why cannot be
challenged by the customer or re-checked by the next engineer.

    python3 c10_scorecard.py c10_scores_larkfield.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_scorecard(path: str | Path | None = None) -> dict:
    path = Path(path) if path else HERE / "c10_scorecard.json"
    doc = json.loads(path.read_text())
    ids = [c["id"] for c in doc["criteria"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate criterion id")
    return doc


def evaluate(doc: dict, scores: dict, targets: dict | None = None) -> dict:
    """scores: {criterion_id: {"score": 0..3, "evidence": "..."}}.
    targets: optional per-criterion target level, default from the scorecard."""
    scores = {k: v for k, v in scores.items() if not k.startswith("_")}
    targets = targets or {}
    by_id = {c["id"]: c for c in doc["criteria"]}
    for cid, entry in scores.items():
        if cid not in by_id:
            raise ValueError(f"unknown criterion: {cid}")
        s = entry.get("score")
        if isinstance(s, bool) or not isinstance(s, int) or not 0 <= s <= 3:
            raise ValueError(f"{cid}: score must be an integer 0..3, got {s!r}")
        if not str(entry.get("evidence", "")).strip():
            raise ValueError(f"{cid}: evidence is required for every score")
    for cid, t in targets.items():
        if cid not in by_id:
            raise ValueError(f"target for unknown criterion: {cid}")
        if not isinstance(t, int) or not 0 <= t <= 3:
            raise ValueError(f"{cid}: target must be an integer 0..3")
    default_target = doc["default_target"]
    categories: dict[str, dict] = {}
    gaps = []
    not_assessed = []
    for c in doc["criteria"]:
        cat = categories.setdefault(c["category"], {"weighted": 0, "weights": 0, "assessed": 0, "total": 0})
        cat["total"] += 1
        if c["id"] not in scores:
            not_assessed.append(c["id"])
            continue
        s = scores[c["id"]]["score"]
        cat["assessed"] += 1
        cat["weighted"] += s * c["weight"]
        cat["weights"] += c["weight"]
        gap = targets.get(c["id"], default_target) - s
        if gap > 0:
            gaps.append({"id": c["id"], "category": c["category"], "score": s,
                         "target": targets.get(c["id"], default_target),
                         "priority": gap * c["weight"], "evidence": scores[c["id"]]["evidence"]})
    out_cats = {}
    for name, cat in categories.items():
        complete = cat["assessed"] == cat["total"]
        maturity = round(cat["weighted"] / cat["weights"], 2) if cat["weights"] else None
        out_cats[name] = {"maturity": maturity, "complete": complete,
                          "assessed": cat["assessed"], "total": cat["total"]}
    gaps.sort(key=lambda g: (-g["priority"], g["id"]))
    return {"categories": out_cats, "gaps": gaps, "not_assessed": not_assessed,
            "assessment_complete": not not_assessed}


def render(result: dict) -> str:
    lines = ["Category maturity (0 to 3, weighted):"]
    for name, c in result["categories"].items():
        m = "n/a" if c["maturity"] is None else f"{c['maturity']:.2f}"
        note = "" if c["complete"] else f"  INCOMPLETE {c['assessed']}/{c['total']}"
        lines.append(f"  {name:<15} {m}{note}")
    lines.append("Gaps by priority (weight x distance to target):")
    if not result["gaps"]:
        lines.append("  none")
    for g in result["gaps"]:
        lines.append(f"  {g['priority']:>2}  {g['id']:<20} score {g['score']} target {g['target']}")
    if result["not_assessed"]:
        lines.append("Not assessed: " + ", ".join(result["not_assessed"]))
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: c10_scorecard.py scores.json", file=sys.stderr)
        return 2
    payload = json.loads(Path(argv[1]).read_text())
    try:
        result = evaluate(load_scorecard(), payload["scores"], payload.get("targets"))
    except ValueError as exc:
        print(f"invalid scores: {exc}", file=sys.stderr)
        return 2
    print(render(result))
    return 0 if result["assessment_complete"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
