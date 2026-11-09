"""Shift a feature view's values by N standard deviations to simulate drift (local feature store)."""
import argparse, statistics, sys
import mlplat_local as P

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--feature-view", default="user_features"); ap.add_argument("--feature", default="x"); ap.add_argument("--drift-magnitude", type=float, required=True); a = ap.parse_args(argv)
    rows = P.load("features.json", {}); vals = [r[a.feature] for r in rows.values() if a.feature in r]
    sd = statistics.pstdev(vals) or 1.0
    for r in rows.values():
        if a.feature in r: r[a.feature] += a.drift_magnitude * sd
    P.save("features.json", rows); print(f"shifted {a.feature} by {a.drift_magnitude} sd ({a.drift_magnitude * sd:.4f})"); return 0

if __name__ == "__main__": sys.exit(main())
