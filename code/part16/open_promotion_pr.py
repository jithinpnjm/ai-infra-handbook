"""Write the promotion pull-request body (what a GitOps registry repo PR would carry). Offline: writes a markdown file."""
import argparse, sys
import mlplat_local as P

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--model-name", required=True); ap.add_argument("--version", required=True)
    ap.add_argument("--baseline-version", required=True); ap.add_argument("--run-id", required=True); ap.add_argument("--out", default="promotion_pr.md"); a = ap.parse_args(argv)
    new, old = P.get_version(a.model_name, a.version), P.get_version(a.model_name, a.baseline_version)
    if not new or not old: print("unknown version"); return 1
    rows = "\n".join(f"| {m} | {old['metrics'].get(m)} | {new['metrics'][m]} |" for m in sorted(new["metrics"]))
    open(a.out, "w").write(f"# Promote {a.model_name} v{a.version}\n\nRun: {a.run_id}\nBaseline: v{a.baseline_version}\n\n| metric | baseline | candidate |\n|---|---|---|\n{rows}\n")
    P.audit("promotion_pr_written", model=a.model_name, version=a.version); print(f"wrote {a.out}"); return 0

if __name__ == "__main__": sys.exit(main())
