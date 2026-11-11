#!/usr/bin/env bash
# Chapter 19.3: smoke request and one benchmark run against the vLLM predictor.
# Not run: needs the running InferenceService. The vllm bench flags were read from the v0.32.0 source.
set -euo pipefail
NS=inference
SVC=llama31-8b-predictor

kubectl -n "${NS}" port-forward "svc/${SVC}" 8080:80 >/dev/null 2>&1 &
PF=$!
trap 'kill "${PF}" 2>/dev/null || true' EXIT
sleep 3

# The served model name equals the InferenceService name.
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"llama31-8b","messages":[{"role":"user","content":"Reply with the word ok."}],"max_tokens":16}'
echo

# Open-loop arrivals at 2 requests per second, random prompts near the production length.
# --goodput takes milliseconds. The allowed keys are ttft, tpot and e2el.
vllm bench serve \
  --backend openai-chat --endpoint /v1/chat/completions \
  --base-url http://127.0.0.1:8080 --model llama31-8b \
  --dataset-name random --random-input-len 1024 --random-output-len 256 \
  --num-prompts 200 --request-rate 2 --burstiness 1.0 \
  --percentile-metrics ttft,tpot,itl,e2el --metric-percentiles 50,95,99 \
  --goodput ttft:200 tpot:25
