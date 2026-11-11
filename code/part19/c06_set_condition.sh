#!/usr/bin/env bash
# Set the GPUHealthy node condition by hand, standing in for the condition agent in the lab
# (chapter 19.6). Usage: c06_set_condition.sh <node> True|False
# Not run here: needs a cluster. The same condition shape is exercised against a real
# kube-apiserver by the envtest suite in code/gpuhealth.
set -euo pipefail

NODE="$1"
STATUS="$2"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

kubectl patch node "${NODE}" --subresource=status --type=strategic --patch "$(cat <<JSON
{"status":{"conditions":[{"type":"GPUHealthy","status":"${STATUS}","reason":"LabInjection","message":"set by c06_set_condition.sh","lastTransitionTime":"${NOW}","lastHeartbeatTime":"${NOW}"}]}}
JSON
)"
