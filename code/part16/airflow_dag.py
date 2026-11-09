from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime, timedelta

with DAG(
    dag_id="churn_training",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@weekly",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
) as dag:
    prepare = KubernetesPodOperator(
        name="prepare",
        image="python:3.11",
        cmds=["python", "prepare.py"],
        arguments=["--dataset-id", "churn-v3"],
    )
    train = KubernetesPodOperator(
        name="train",
        image="nvidia/cuda:12.2.0-runtime-ubuntu22.04",
        cmds=["python", "train.py"],
        arguments=["--dataset-id", "churn-v3", "--seed", "42"],
    )
    prepare >> train
