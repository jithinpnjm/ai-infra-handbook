import argparse, mlflow
from mlflow.tracking import MlflowClient

ap = argparse.ArgumentParser()
ap.add_argument("--run-id", required=True)
ap.add_argument("--model-name", required=True)
ap.add_argument("--baseline-run-id", required=False)
args = ap.parse_args()

client = MlflowClient()
candidate = client.get_run(args.run_id)

# 1. Check required tags are present
for tag in ("data_hash", "code_commit", "seed", "env_image", "dataset_id"):
    if tag not in candidate.data.tags:
        raise SystemExit(f"PROMOTION BLOCKED: missing required tag {tag}")

# 2. Compare against baseline if provided
if args.baseline_run_id:
    baseline = client.get_run(args.baseline_run_id)
    cand_auc = candidate.data.metrics["auc"]
    base_auc = baseline.data.metrics["auc"]
    if cand_auc < base_auc:
        raise SystemExit(
            f"PROMOTION BLOCKED: AUC regressed ({cand_auc:.4f} < {base_auc:.4f})"
        )

# 3. Register the model (staging stage)
model_uri = f"runs:/{args.run_id}/model"
mv = client.create_model_version(args.model_name, model_uri, args.run_id)
client.transition_model_version_stage(
    args.model_name, mv.version, stage="Staging"
)
print(f"PROMOTED {args.model_name} v{mv.version} to Staging")
