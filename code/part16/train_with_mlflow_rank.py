import os, mlflow
rank = int(os.environ["RANK"])
world_size = int(os.environ["WORLD_SIZE"])
mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
mlflow.set_experiment("churn")
with mlflow.start_run(run_name=f"churn-rank-{rank}-of-{world_size}") as run:
    mlflow.set_tag("rank", str(rank))
    mlflow.set_tag("world_size", str(world_size))
    mlflow.set_tag("data_hash", os.environ["DATA_HASH"])
    mlflow.set_tag("code_commit", os.environ["CODE_COMMIT"])
    # ... train ...
