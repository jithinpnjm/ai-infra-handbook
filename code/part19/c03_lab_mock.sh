#!/usr/bin/env bash
# Chapter 19.3: exercise the load generator and the go/no-go rule against the local mock server.
# Runs on a laptop. The mock is not a model: it only proves the harness finds a saturation knee.
set -euo pipefail
cd "$(dirname "$0")"
OUT="${OUT:-/tmp/c03_sweep.json}"
PORT=18080

python3 c03_mock_server.py --port "${PORT}" --ttft-ms 20 --itl-ms 5 --slots 4 >/dev/null 2>&1 &
MOCK_PID=$!
trap 'kill "${MOCK_PID}" 2>/dev/null || true' EXIT
sleep 1

python3 c03_loadgen.py --url "http://127.0.0.1:${PORT}" --mode closed \
  --concurrency 1 2 4 8 16 --duration 4 \
  --prompt-mean 20 --prompt-std 2 --max-tokens 64 \
  --slo-ttft-ms 100 --slo-tpot-ms 10 --out "${OUT}" >/dev/null

# Exit status 1 means NO-GO, which is a valid outcome, so do not stop the script on it.
python3 c03_decision.py "${OUT}" --slo-ttft-ms 100 --slo-tpot-ms 10 \
  --peak-rps 5 --max-replicas 2 || true
