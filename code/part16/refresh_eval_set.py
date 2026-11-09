"""Split production samples (jsonl: {question, ground_truth, flagged}) into a golden set (reviewed, unflagged) and a regression set (flagged failures)."""
import argparse, json, sys

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--production-sample", required=True); ap.add_argument("--golden-output", required=True); ap.add_argument("--regression-output", required=True); a = ap.parse_args(argv)
    rows = [json.loads(l) for l in open(a.production_sample) if l.strip()]
    gold = [r for r in rows if not r.get("flagged")]; reg = [r for r in rows if r.get("flagged")]
    for path, rs in ((a.golden_output, gold), (a.regression_output, reg)):
        with open(path, "w") as f: f.writelines(json.dumps(r) + "\n" for r in rs)
    print(f"golden={len(gold)} regression={len(reg)}"); return 0

if __name__ == "__main__": sys.exit(main())
