#!/usr/bin/env bash
# Chapter 19.2 section 8: GPU Operator upgrade on one canary node, with an evidence archive. Not run here.
set -euo pipefail
: "${TARGET_VERSION:?set TARGET_VERSION, for example v26.7.2}"
: "${CANARY_NODE:?set CANARY_NODE to a node name from kubectl get nodes}"
HERE="$(cd "$(dirname "$0")" && pwd)"
EVID=gpu-upgrade-evidence
mkdir -p "$EVID"

helm history gpu-operator -n gpu-operator > "$EVID/helm-history-before.txt"
helm get values gpu-operator -n gpu-operator -a > "$EVID/values-before.yaml"
helm get manifest gpu-operator -n gpu-operator > "$EVID/manifest-before.yaml"
kubectl get node "$CANARY_NODE" -o yaml > "$EVID/canary-before.yaml"

kubectl cordon "$CANARY_NODE"
kubectl drain "$CANARY_NODE" --ignore-daemonsets --delete-emptydir-data --grace-period=120 --timeout=20m
helm upgrade gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator --version "$TARGET_VERSION" \
  -f "$HERE/c02_gpu_operator_values.yaml" --wait --timeout 20m

kubectl get node "$CANARY_NODE" \
  -o jsonpath='{.status.capacity.nvidia\.com/gpu}{" capacity\n"}{.status.allocatable.nvidia\.com/gpu}{" allocatable\n"}'
kubectl apply -f "$HERE/c02_upgrade_validation.yaml"
kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/gpu-upgrade-validation --timeout=5m
kubectl delete -f "$HERE/c02_upgrade_validation.yaml"
kubectl uncordon "$CANARY_NODE"
