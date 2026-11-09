import kfp
from kfp import dsl

@dsl.component(
    base_image="python:3.11",
    packages_to_install=["pandas", "scikit-learn"],
)
def prepare_op(dataset_id: str, output_path: dsl.OutputPath()):
    import pandas as pd
    df = pd.read_parquet(f"data/{dataset_id}.parquet")
    df.to_parquet(output_path)

@dsl.component(
    base_image="nvidia/cuda:12.2.0-runtime-ubuntu22.04",
    packages_to_install=["pandas", "scikit-learn", "mlflow"],
)
def train_op(input_path: dsl.InputPath(), seed: int) -> str:
    import mlflow, pandas as pd
    from sklearn.ensemble import GradientBoostingClassifier
    df = pd.read_parquet(input_path)
    mlflow.set_experiment("churn")
    with mlflow.start_run() as run:
        mlflow.log_param("seed", seed)
        model = GradientBoostingClassifier(random_state=seed)
        model.fit(df.drop("churned", axis=1), df["churned"])
    return run.info.run_id

@dsl.pipeline(name="Churn Training Pipeline")
def training_pipeline(dataset_id: str = "churn-v3", seed: int = 42):
    p = prepare_op(dataset_id=dataset_id)
    t = train_op(input_path=p.output, seed=seed)

if __name__ == "__main__":
    kfp.compiler.Compiler().compile(training_pipeline, "pipeline.yaml")
    kfp.Client().create_run_from_pipeline_package("pipeline.yaml")
