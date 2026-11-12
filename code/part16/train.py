import argparse, hashlib, os, subprocess, mlflow, mlflow.sklearn
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score

ap = argparse.ArgumentParser()
ap.add_argument("--dataset", required=True)
ap.add_argument("--seed", type=int, default=42)
args = ap.parse_args()

df = pd.read_csv(args.dataset)
data_hash = hashlib.sha256(open(args.dataset, "rb").read()).hexdigest()
commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()

mlflow.set_experiment("churn")
with mlflow.start_run(run_name=f"churn-{data_hash[:8]}") as run:
    mlflow.set_tag("data_hash", data_hash)
    mlflow.set_tag("code_commit", commit)
    mlflow.log_param("seed", args.seed)
    mlflow.set_tag("seed", str(args.seed))
    mlflow.set_tag("env_image", os.environ.get("ENV_IMAGE", "local"))

    # Synthetic train/test split for the lab
    train, test = df.iloc[:800], df.iloc[800:]
    model = GradientBoostingClassifier(random_state=args.seed)
    model.fit(train[["tier_gold"]], train["churned"])
    preds = model.predict_proba(test[["tier_gold"]])[:, 1]

    mlflow.log_metric("auc", roc_auc_score(test["churned"], preds))
    mlflow.log_metric("accuracy", accuracy_score(test["churned"], preds > 0.5))
    mlflow.log_metric("f1", f1_score(test["churned"], preds > 0.5))

    mlflow.sklearn.log_model(model, "model")
    mlflow.register_model(f"runs:/{run.info.run_id}/model", "churn-model")
# expected: a registered model version with stage=None
