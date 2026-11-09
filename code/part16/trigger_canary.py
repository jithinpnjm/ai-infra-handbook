"""Start a canary for a registered version: writes canaryTrafficPercent into a KServe InferenceService manifest."""
import argparse, sys, yaml
import mlplat_local as P

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--model-name", required=True); ap.add_argument("--version", required=True)
    ap.add_argument("--percent", type=int, default=10); ap.add_argument("--out", default="canary_isvc.yaml"); a = ap.parse_args(argv)
    mv = P.get_version(a.model_name, a.version)
    if not mv or mv["stage"] not in ("Staging", "Production"):
        print("CANARY REFUSED: version is not in Staging or Production"); return 1
    doc = {"apiVersion": "serving.kserve.io/v1beta1", "kind": "InferenceService", "metadata": {"name": a.model_name},
           "spec": {"predictor": {"canaryTrafficPercent": a.percent,
                    "model": {"modelFormat": {"name": "sklearn"}, "storageUri": f"s3://mlflow-artifacts/{a.model_name}/{a.version}/model"}}}}
    open(a.out, "w").write(yaml.safe_dump(doc, sort_keys=False)); P.audit("canary_started", model=a.model_name, version=a.version, percent=a.percent)
    print(f"CANARY {a.percent}% -> {a.out}"); return 0

if __name__ == "__main__": sys.exit(main())
