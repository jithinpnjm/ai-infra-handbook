#!/usr/bin/env bash
# NOT RUN. Needs a Kubernetes cluster with GPU nodes and a GPU Feature Discovery label.
# The Helm values it uses were rendered with helm template and checked, nothing more.
# Secrets come from your secret manager. Nothing secret is in this repository.
set -euo pipefail
cd "$(dirname "$0")"

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add gpu-helm-charts https://nvidia.github.io/dcgm-exporter/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update
kubectl create namespace monitoring

# Secrets. Create the three receiver files first, each readable only by you (mode 0400).
kubectl -n monitoring create secret generic grafana-admin \
  --from-literal=admin-user=admin --from-literal=admin-password="${GRAFANA_ADMIN_PASSWORD:?set it}"
kubectl -n monitoring create secret generic alertmanager-gpu-platform \
  --from-file=alertmanager.yaml=c07_alertmanager.yaml
kubectl -n monitoring create secret generic alertmanager-receivers \
  --from-file=pagerduty-routing-key=./secrets/pagerduty-routing-key \
  --from-file=ticket-webhook-url=./secrets/ticket-webhook-url \
  --from-file=deadman-url=./secrets/deadman-url

# The stack, then the exporters and agents.
helm install kps prometheus-community/kube-prometheus-stack --version 93.1.1 \
  -n monitoring -f c07_values_kps.yaml
helm install loki grafana/loki --version 7.5.0 -n monitoring -f c07_values_loki.yaml
helm install dcgm-exporter gpu-helm-charts/dcgm-exporter --version 4.9.0 \
  -n monitoring -f c07_values_dcgm.yaml
helm install otel-agent open-telemetry/opentelemetry-collector --version 0.178.2 \
  -n monitoring -f c07_values_otel.yaml

# Rules as code: wrap the tested rule files. The Part 20 cause alerts are left out
# because they contain a second Watchdog and the stack already has one.
python3 c07_prometheusrule.py c07_stack_rules.yaml c07-stack-rules | kubectl apply -f -
python3 c07_prometheusrule.py ../part20/slo_recording_rules.yaml c07-slo-recording | kubectl apply -f -
python3 c07_prometheusrule.py ../part20/slo_burn_alerts_availability.yaml c07-slo-burn | kubectl apply -f -

# Dashboard as code: the Grafana sidecar loads ConfigMaps that carry this label.
kubectl -n monitoring create configmap gpu-platform-dashboard \
  --from-file=gpu-platform.json=c07_dashboard_gpu_platform.json
kubectl -n monitoring label configmap gpu-platform-dashboard grafana_dashboard=1
