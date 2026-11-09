import os, mlflow
from mlflow.tracking import MlflowClient

run_id = os.environ["MLFLOW_PARENT_RUN_ID"]
client = MlflowClient()
run = client.get_run(run_id)

# Promotion gate from Chapter 16.1
for tag in ("data_hash", "code_commit", "seed", "env_image"):
    if tag not in run.data.tags:
        raise SystemExit(f"PROMOTION BLOCKED: missing {tag}")
if run.data.metrics.get("auc", 0) < 0.90:
    raise SystemExit("PROMOTION BLOCKED: AUC below floor")

# Register
model_uri = f"runs:/{run_id}/model"
mv = client.create_model_version("churn-model", model_uri, run_id)
client.transition_model_version_stage("churn-model", mv.version, stage="Staging")
print(f"PROMOTED churn-model v{mv.version}")
