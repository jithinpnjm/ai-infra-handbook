# code/part16: what is tested and how

Run everything: `python3 code/part16/pipeline_lab.py` (chapter structure checks, then the real checks below).

| Kind | Files | How it was checked |
|---|---|---|
| Runnable scripts (promotion gate, canary, eval, guardrails, RAG index/agent, consent/erasure, model card, drift, retraining) | `promote.py`, `trigger_canary.py`, `run_eval.py`, `check_thresholds.py`, ... | `pytest code/part16/test_part16.py` against the local stand-in services in `mlplat_local.py` |
| MLflow promotion gate | `promotion_gate.py` | Same suite, against a real MLflow (sqlite store) |
| Kubernetes and CRD manifests | `*.yaml` | `tools/check_code_yaml.sh` (upstream CRD schemas for KServe, Kueue, KubeRay, Argo, Volcano, KAI, NIM Operator, ...) and `tools/check_k8s_yaml.sh` (kubeconform) |
| Library usage snippets | `snippets/` | Syntax only. Libraries not installed. |
| Feast repo | `feature_repo/` | Syntax only. Feast not installed. |
| `train_with_mlflow.py`, `kfp_pipeline.py`, `vertex_pipeline.py`, `airflow_dag.py`, ... | | Static checks only; they need scikit-learn (broken in the test Python), Kubeflow, Vertex or Airflow. |

Not tested anywhere: anything that needs a cluster, a GPU, a cloud account, a hosted LLM, Milvus or Feast. The mock LLM, bag-of-words index and local feature store are stand-ins; they check the logic around the services, not the services.
