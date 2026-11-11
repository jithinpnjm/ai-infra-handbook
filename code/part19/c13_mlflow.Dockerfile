# MLflow tracking server image for the research platform.
# The upstream image at v3.18.0 only runs `pip install mlflow==$VERSION`, so it has no
# PostgreSQL driver and no S3 client. This adds both. Build:
#   docker build -f c13_mlflow.Dockerfile -t registry.research.example.com/research/mlflow:3.18.0 .
FROM ghcr.io/mlflow/mlflow:v3.18.0
RUN pip install --no-cache-dir psycopg2-binary==2.9.13 boto3==1.44.0
