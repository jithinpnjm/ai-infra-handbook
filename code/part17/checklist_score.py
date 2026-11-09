import argparse, collections, sys
import opslib as O

def score(items, ans):
    cat = collections.defaultdict(lambda: [0, 0]); missing = []
    for i in items:
        if i.get("status", "active") != "active": continue
        ok = ans.get(i["id"]) == "yes"; cat[i["category"]][1] += 1; cat[i["category"]][0] += ok
        if not ok: missing.append(i["id"])
    return dict(cat), missing

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--cluster", required=True); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    cat, missing = score(O.load_yaml("checklist.yaml", []), O.load_yaml("answers.yaml", {}))
    with open(a.output, "w") as f:
        f.write(f"# Checklist score for {a.cluster}\n\n" + "".join(f"- {c}: {y}/{n} ({y / n:.0%})\n" for c, (y, n) in sorted(cat.items())) + "\n## Items not satisfied\n" + "".join(f"- {m}\n" for m in missing))
    print(f"{sum(y for y, _ in cat.values())}/{sum(n for _, n in cat.values())} items satisfied"); return 0

if __name__ == "__main__": sys.exit(main())
