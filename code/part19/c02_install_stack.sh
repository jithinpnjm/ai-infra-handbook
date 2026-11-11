#!/usr/bin/env bash
# Chapter 19.2 steps 3 and 4: driver installer, GPU Operator, Kueue, KAI Scheduler. Not run here.
# Versions are the ones the chapter's YAML was validated against (see the chapter's verification log).
set -euo pipefail
GPU_OPERATOR_VERSION="${GPU_OPERATOR_VERSION:-v26.7.2}"
KUEUE_VERSION="${KUEUE_VERSION:-0.20.5}"
KAI_VERSION="${KAI_VERSION:-v0.18.7}"
HERE="$(cd "$(dirname "$0")" && pwd)"

# Google driver installer for Container-Optimized OS (manifest named on the NVIDIA GKE page).
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml

kubectl create namespace gpu-operator --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n gpu-operator -f "$HERE/c02_gpu_operator_quota.yaml"
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update
helm upgrade --install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator --version "$GPU_OPERATOR_VERSION" \
  -f "$HERE/c02_gpu_operator_values.yaml" --wait --timeout 15m

helm upgrade --install kueue oci://registry.k8s.io/kueue/charts/kueue \
  --version "$KUEUE_VERSION" --namespace kueue-system --create-namespace \
  -f "$HERE/c02_kueue_values.yaml" --wait

helm upgrade --install kai-scheduler oci://ghcr.io/kai-scheduler/kai-scheduler/kai-scheduler \
  --namespace kai-scheduler --create-namespace --version "$KAI_VERSION" --wait
