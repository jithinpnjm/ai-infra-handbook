# Checkpoint rewrite report, agent B (Part 16, chapters 07-12)

All six chapters: 20 questions before and after. Mix per chapter: 6 scenario, 5 mechanism, 4 trade-off, 3 numbers, 2 debugging-order. chain_gate 0.0 to 0.6 per 1000 words. No question dropped for lack of support. Kept as-is: none (old questions were all definition or recall type, so all 20 replaced per chapter, 120 total).

Errors noticed elsewhere (not fixed):
- 07: Section 4.2 Seldon YAML lists retriever and generator as two entries under `predictors`, which are alternatives, not a chain; `modelUri` inside `graph` is unverified. Section 1.1 table says the platform team owns scaling while the model team writes it in the InferenceService.
- 08: Lab 7.3 `helm install vllm vllm/vllm` and `--set model.name` are unverified. Section 6.2 fix says return a 429 with no partial answer, while the table in 5.2 says the iteration cap returns a partial answer.
- 09: Section 4.2 says the safety filter is LLM-as-judge but the code is a rule-based stand-in. Section 5.3 paragraph on the regression set pass rate is muddled. Lab 7.7 uses a 2024-q4 file name.
- 10: Section 6.5 says the trigger cannot fire, then says to fire the drift trigger right away. Section 7.5 `drift-magnitude` is in standard deviations while thresholds are PSI units.
- 11: Section 1.1 says Vertex AI runs Pipelines on GKE but the following text says you do not operate a GKE cluster. Managed staffing is 2-3 engineers in the intro, 2-5 in the table. Lab 6.4 pipeline uses a cluster-internal MLflow address that a Google-managed pipeline may not reach. `gcloud ai pipelines run` is unverified.
- 12: Lab secret names differ between 3.1 (`ngc-secret`, `ngc-api-secret`) and 8.2 and 8.4 (`ngc-api-key`, `ngc-pull-secret`). Section 7.3 treats `OOMKilled` as GPU memory, but it is a host memory kill. Section 7.5 attributes the failure to a data format mismatch without support. The NIM Helm lab image tag 1.0.0 differs from the NIMService example.
