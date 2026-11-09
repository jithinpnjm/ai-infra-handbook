"""Recommend GPU counts from a utilisation file ($OPS_HOME/utilisation.json: [{workload, gpus, avg_util}])."""
import argparse, json, math, sys
import opslib as O

def recommend(rows, target=0.7):
    out = []
    for r in rows:
        want = max(1, math.ceil(r["gpus"] * r["avg_util"] / target))
        out.append({**r, "recommended": min(want, r["gpus"]), "action": "shrink" if want < r["gpus"] else "keep"})
    return out

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--cluster", required=True); ap.add_argument("--output", required=True); ap.add_argument("--target-util", type=float, default=0.7); a = ap.parse_args(argv)
    rows = recommend(json.loads((O.home() / "utilisation.json").read_text()), a.target_util)
    with open(a.output, "w") as f:
        f.write(f"# Right-sizing for {a.cluster}\n\n| workload | GPUs | util | recommended | action |\n|---|---|---|---|---|\n")
        f.writelines(f"| {r['workload']} | {r['gpus']} | {r['avg_util']:.0%} | {r['recommended']} | {r['action']} |\n" for r in rows)
    print(f"{sum(r['action'] == 'shrink' for r in rows)} of {len(rows)} workloads can shrink"); return 0

if __name__ == "__main__": sys.exit(main())
