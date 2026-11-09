"""Fail (exit 1) if golden/regression eval results miss thresholds. thresholds.yaml: {golden_min_mean: 3.5, regression_min_mean: 3.0}"""
import argparse, json, sys, yaml

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--golden-results", required=True); ap.add_argument("--regression-results", required=True)
    ap.add_argument("--thresholds", required=True); a = ap.parse_args(argv)
    t = yaml.safe_load(open(a.thresholds)); bad = []
    for name, path, key in (("golden", a.golden_results, "golden_min_mean"), ("regression", a.regression_results, "regression_min_mean")):
        m = json.load(open(path))["mean_score"]
        if m < t[key]: bad.append(f"{name} mean {m:.2f} < {t[key]}")
    print("EVAL GATE FAILED: " + "; ".join(bad) if bad else "EVAL GATE PASSED"); return 1 if bad else 0

if __name__ == "__main__": sys.exit(main())
