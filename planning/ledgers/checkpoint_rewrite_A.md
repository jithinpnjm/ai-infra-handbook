# Checkpoint rewrite report: A (Part 16, chapters 16.1 to 16.6)

All six chapters now have 20 questions (mix: 6 scenario, 5 mechanism, 4 trade-off, 3 numbers, 2 debugging-order). chain_gate passes for all (0.0 to 0.4 per 1000 words). No question was dropped for lack of support. Sources and review notes untouched.

| Chapter | Replaced | Kept |
|---|---|---|
| 16.1 | 19 | 1 (old Q17, log decision before registry write, now Q8) |
| 16.2 | 19 | 1 (old Q3, dataset id not path, now Q7) |
| 16.3 | 20 | 0 |
| 16.4 | 20 | 0 |
| 16.5 | 20 | 0 |
| 16.6 | 20 | 0 |

Old questions removed as definition or recall: 16.2 old Q19 (dataset cataloguing) was not supported by the chapter text anyway.

## Errors noticed elsewhere (not fixed)
16.1
- Lab train.py uses `train[["tier_gold"]]` but the demo CSV has column `tier`, not `tier_gold`. Test rows 800+ are all silver and churned alternates 0/1, so AUC would be degenerate.
- `dvc init --storage.gs` is not a valid dvc init flag; `data/` directory not created before to_csv.
- Helm values say Postgres but `backendStore.url=sqlite`; namespace mlops vs team-data-science in the InferenceService; storageUri is s3 on a GCS lab.
- Lab step 4 runs `code/part16/promote.py` but the code shown is `mlops_promotion_gate.py`.
- LLMOps goals table says "RTO and RTO attainment" (typo).
- Section 8.7 says 5 seconds per answer, old Q20 said 30 seconds; chapter text says 5 s target and 30 s outer limit.
16.2
- Reference MLflow layout header says "Practical MMOps" (typo). IAM role names there (roles/mlflow.*) differ from tracker.writer names in 5.2.
- Section 7 lab calls `train.py` from 16.1 with `--dataset-id`, but the 16.1 train.py has no such argument (train_with_mlflow.py does).
- Section 2.5 says Section 5.3 gives failed runs 30 days, but the Cloud layout in the same chapter says a 90-day lifecycle rule for the failed-runs prefix.
16.3
- Table says Parquet is about 6x less storage than CSV, but the worked example (14 MB vs 6 MB) is about 2.3x.
- Feast feature_view code appears twice in 2.4 (shape-only block and full block).
- Section numbering jumps from 3.7 to 4.1 (no ## 4 heading).
16.4
- Argo retry example puts `retries` and `retryStrategy` together, which is not valid Argo syntax as shown.
- Comparison table cell "None (built-in)" for Airflow caching is ambiguous.
- Lab refers to `code/part16/training_dag.yaml` while the DAG shown is `argo_dag.yaml`.
16.5
- PyTorchJob in 1.3 requests 8 GPUs per pod across 8 pods (64 GPUs), but 2.1 and the Volcano annotation treat the same job as 8 GPUs with min-member 8.
- Table cell "line of work lost on worker death" is unclear. Katib "Autoscaling: Yes (early stopping)" conflates early stopping with autoscaling.
- Section 6.3 says 36 hours of lost work equals "36 node-hours of GPU time", unit is unclear for a multi-node job.
- train_elastic.py builds the model twice (`build_optimiser(build_model())`).
16.6
- Flow in 3.2 says the canary starts after the PR merges and production stage is written, but 1.2 says Staging to Production happens after the canary passes.
- Rollback section says previous model is stage=archived, while the stage table shows rollback as Production to Staging.
- 6.1 fix says serving reads the registry directly, while 4.3 says serving reads a tag the registry updates.
- Section 5.2 says the IAM model mirrors Chapter 16.5 Section 2, but 16.5 Section 2 is gang scheduling.
