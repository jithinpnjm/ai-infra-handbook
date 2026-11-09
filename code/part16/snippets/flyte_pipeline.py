from flytekit import Resources, task, workflow

@task(requests=Resources(cpu="2", mem="4Gi"))
def prepare(dataset_id: str) -> str:
    import pandas as pd
    df = pd.read_parquet(f"data/{dataset_id}.parquet")
    df.to_parquet("/tmp/clean.parquet")
    return "/tmp/clean.parquet"

@task(requests=Resources(cpu="4", mem="16Gi", gpu="1"))
def train(clean_path: str, seed: int) -> str:
    import mlflow, pandas as pd
    from sklearn.ensemble import GradientBoostingClassifier
    df = pd.read_parquet(clean_path)
    mlflow.set_experiment("churn")
    with mlflow.start_run() as run:
        mlflow.log_param("seed", seed)
        model = GradientBoostingClassifier(random_state=seed)
        model.fit(df.drop("churned", axis=1), df["churned"])
    return run.info.run_id

@workflow
def training_pipeline(dataset_id: str = "churn-v3", seed: int = 42) -> str:
    p = prepare(dataset_id=dataset_id)
    t = train(clean_path=p, seed=seed)
    return t
