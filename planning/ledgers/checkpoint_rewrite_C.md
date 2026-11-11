# Checkpoint rewrite, worker C

All 7 chapters: 20 questions each, 20 replaced, 0 kept (old ones were definition or recall questions). chain_gate all under 0.5 per 1000 words. No question dropped for lack of support, though a few "trade-off" answers lean on chapter statements that are brief.

## Errors noticed (not fixed)
- 16.13: homomorphic encryption "10-100x" overhead has no source (chapter says so). Old Q1 title said "four regimes" but table has seven.
- 16.14: Exercise 4 / 7.2 describe Kueue caps as spend caps; chapter 7.2 correctly says Kueue limits GPUs not money, so the exercise wording in ch 16.15 Exercise 2 ("ClusterQueue should refuse new Jobs once the limit is reached") conflicts with it.
- 16.15: section 4 calls the UCI Adult dataset a "churn" dataset; it is an income dataset. 13.3 error text "cluster binding not found" does not match a storage permission fault. Metrics pipeline in the OTel-style config is not in this chapter, but lab MLflow uses a sqlite backend store on a Helm deploy.
- 17.01: gpu_uuid with 8000 values is marked "Yes (with care)" while the rule of thumb says under 1,000. The `--storage.tsdb.max-label-values-per-label-name` flag is cited as a series limit, which looks doubtful.
- 17.02: retention table is labelled "storage per series per year" yet 1 day = 1 MB; the unit looks wrong. Section 4.3 refers to "Chapter 13" for storage pattern. Exercise 2 PromQL counts all series and is expensive.
- 17.03: the Collector config sends the metrics pipeline to the Tempo exporter (a trace backend). Propagation rate metric in 4.3 is not defined anywhere.
- 17.04: Section 2.1 PromQL uses old name `DCGM_FI_DEV_GPU_UTIL` while the chapter says it uses 4.9.0 names. A "draft" voice remains in sections 2.1 to 2.6 ("The draft's example values").
