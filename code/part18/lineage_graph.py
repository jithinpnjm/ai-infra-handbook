"""Write the lineage of a model: model <- dataset <- (raw source). Registry: $SEC_HOME/lineage.json {model: {dataset, run, code_commit}}, datasets: {dataset: {sources: []}}."""
import argparse, sys, yaml
import seclib as S

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--dataset", required=True); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    reg = S.load_json("lineage.json", {"models": {}, "datasets": {}}); m = reg["models"].get(a.model)
    if not m: print("UNKNOWN MODEL: no lineage recorded"); return 1
    if m["dataset"] != a.dataset: print(f"MISMATCH: {a.model} was trained on {m['dataset']}, not {a.dataset}"); return 1
    g = {"model": a.model, "trained_on": a.dataset, "run": m["run"], "code_commit": m["code_commit"], "dataset_sources": reg["datasets"].get(a.dataset, {}).get("sources", [])}
    open(a.output, "w").write(yaml.safe_dump(g, sort_keys=False)); S.audit("lineage_exported", model=a.model); print("lineage written"); return 0

if __name__ == "__main__": sys.exit(main())
