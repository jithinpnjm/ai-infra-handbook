"""Write a model card from the registry entry: model, metrics, training data, fairness slice gaps (if recorded)."""
import argparse, sys
import mlplat_local as P

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True, help="name-vN, e.g. churn-model-v6"); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    name, _, v = a.model.rpartition("-v"); mv = P.get_version(name, v)
    if not mv: print("unknown model version"); return 1
    fair = mv.get("fairness", {}); gap = max(fair.values()) - min(fair.values()) if fair else None
    txt = [f"# Model card: {name} v{v}", "", f"Run: {mv['run_id']}  Stage: {mv['stage']}", "", "## Evaluation"] + [f"- {k}: {x}" for k, x in sorted(mv["metrics"].items())]
    txt += ["", "## Training data", f"- dataset: {mv.get('dataset_id', 'NOT RECORDED')}", "", "## Fairness"]
    txt += [f"- {k}: {x}" for k, x in sorted(fair.items())] + [f"- max gap: {gap:.3f}"] if fair else ["- NOT AUDITED"]
    open(a.output, "w").write("\n".join(txt) + "\n"); print(f"wrote {a.output}"); return 0

if __name__ == "__main__": sys.exit(main())
