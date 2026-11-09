"""Promotion gate CLI (local registry). Usage: promote.py --candidate RUN --baseline RUN [--policy policy.json]
Run records live in $MLPLAT_HOME/runs.json: {run_id: {metrics, tags}}."""
import argparse, sys
import mlplat_local as P

REQUIRED_TAGS = ("data_hash", "code_commit", "seed", "env_image")

def gate(cand: dict, base: dict, primary="auc", floors=None):
    reasons = [f"missing required tag {t}" for t in REQUIRED_TAGS if not cand["tags"].get(t)]
    c, b = cand["metrics"].get(primary, 0), base["metrics"].get(primary, 0)
    if c < b: reasons.append(f"{primary} regressed: {c:.4f} < {b:.4f}")
    for m, floor in (floors or {}).items():
        if cand["metrics"].get(m, 0) < floor: reasons.append(f"{m} below floor: {cand['metrics'].get(m, 0)} < {floor}")
    return reasons

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--candidate", required=True); ap.add_argument("--baseline", required=True)
    ap.add_argument("--model-name", default="churn-model"); a = ap.parse_args(argv)
    runs = P.load("runs.json", {})
    reasons = gate(runs[a.candidate], runs[a.baseline])
    if reasons:
        P.audit("promotion_blocked", run=a.candidate, reasons=reasons)
        print("PROMOTION BLOCKED"); [print("  -", r) for r in reasons]; return 1
    v = len(P.load("registry.json", {}).get(a.model_name, {})) + 1
    P.register(a.model_name, v, a.candidate, runs[a.candidate]["metrics"], stage="Staging")
    P.audit("promoted", model=a.model_name, version=v, run=a.candidate, baseline=a.baseline)
    print(f"PROMOTED TO STAGING: {a.model_name} v{v}"); return 0

if __name__ == "__main__": sys.exit(main())
