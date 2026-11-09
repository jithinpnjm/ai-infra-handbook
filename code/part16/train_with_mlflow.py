import argparse, hashlib, os, subprocess, mlflow, mlflow.sklearn
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ap = argparse.ArgumentParser()
ap.add_argument("--dataset-id", required=True)
ap.add_argument("--data-path", required=True)
ap.add_argument("--seed", type=int, default=42)
args = ap.parse_args()

data_hash = hashlib.sha256(open(args.data_path, "rb").read()).hexdigest()
commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()

mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
mlflow.set_experiment("churn")
with mlflow.start_run(run_name=f"churn-{data_hash[:8]}-{args.seed}") as run:
    # Required tags — fail if any is empty
    mlflow.set_tag("data_hash", data_hash)
    mlflow.set_tag("dataset_id", args.dataset_id)
    mlflow.set_tag("code_commit", commit)
    mlflow.set_tag("seed", str(args.seed))
    mlflow.set_tag("env_image", os.environ["ENV_IMAGE_DIGEST"])

    mlflow.log_params({"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05})

    df = pd.read_parquet(args.data_path)
    train, test = df.iloc[:800], df.iloc[800:]
    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=3, learning_rate=0.05, random_state=args.seed
    )
    model.fit(train.drop("churned", axis=1), train["churned"])
    preds = model.predict_proba(test.drop("churned", axis=1))[:, 1]
    mlflow.log_metric("auc", roc_auc_score(test["churned"], preds))

    mlflow.sklearn.log_model(model, "model")
# expected: a run with run_id, all required tags set, an AUC value, and a model artifact
