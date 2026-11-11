#!/usr/bin/env bash
# Point the GPU Operator's DCGM exporter at the capstone counters file (chapter 19.6).
# Not run here: needs a cluster with the GPU Operator. The two commands follow the
# "Install DCGM Exporter" page; the operator namespace and ClusterPolicy name are the
# ones its getting-started page shows (gpu-operator, cluster-policy).
# The ConfigMap key must be dcgm-metrics.csv. The file replaces the shipped counters,
# so c06_dcgm_counters.csv lists every field the alert rules use.
set -euo pipefail

NAMESPACE="${NAMESPACE:-gpu-operator}"
POLICY="${POLICY:-cluster-policy}"

kubectl create configmap custom-dcgm-metrics \
    --namespace "${NAMESPACE}" \
    --from-file=dcgm-metrics.csv=c06_dcgm_counters.csv

kubectl patch clusterpolicy "${POLICY}" --type merge \
    --patch '{"spec":{"dcgmExporter":{"config":{"name":"custom-dcgm-metrics"}}}}'

# The exporter pods carry the label app=nvidia-dcgm-exporter.
kubectl get pods --all-namespaces --selector app=nvidia-dcgm-exporter
