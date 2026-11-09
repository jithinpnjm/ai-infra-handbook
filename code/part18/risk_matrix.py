"""Likelihood x impact grid from a threat catalogue table, plus the top threats by score (likelihood * impact)."""
import argparse, sys

def parse(path):
    rows = []
    for l in open(path):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) >= 6 and c[0].startswith("T-"): rows.append({"id": c[0], "asset": c[1], "likelihood": int(c[3]), "impact": int(c[4])})
    return rows

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--threat-catalogue", required=True); ap.add_argument("--output", required=True); ap.add_argument("--top", type=int, default=10); a = ap.parse_args(argv)
    rows = parse(a.threat_catalogue); grid = {(l, i): [] for l in range(1, 6) for i in range(1, 6)}
    for r in rows: grid[(r["likelihood"], r["impact"])].append(r["id"])
    top = sorted(rows, key=lambda r: -r["likelihood"] * r["impact"])[:a.top]
    with open(a.output, "w") as f:
        f.write("# Risk matrix (rows: likelihood 5..1, columns: impact 1..5)\n\n| L \\ I | 1 | 2 | 3 | 4 | 5 |\n|---|---|---|---|---|---|\n")
        for l in range(5, 0, -1): f.write(f"| {l} | " + " | ".join(",".join(grid[(l, i)]) for i in range(1, 6)) + " |\n")
        f.write("\n## Top threats\n" + "".join(f"- {r['id']} {r['asset']} (score {r['likelihood'] * r['impact']})\n" for r in top))
    print(f"{len(rows)} threats; top score {top[0]['likelihood'] * top[0]['impact'] if top else 0}"); return 0

if __name__ == "__main__": sys.exit(main())
