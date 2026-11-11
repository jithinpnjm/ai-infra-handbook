#!/usr/bin/env bash
# Validate the chapter 19.13 files. Needs helm, kubeconform and python3 with jsonschema and PyYAML.
# Kueue CRDs (v0.20.5) are fetched into a temp dir for the CRD check.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
helm repo add jupyterhub https://hub.jupyter.org/helm-chart/ >/dev/null
helm repo update >/dev/null
helm template hub jupyterhub/jupyterhub --version 4.4.5 -f "$HERE/c13_jupyterhub_values.yaml" > "$TMP/hub.yaml"
kubeconform -strict -summary -ignore-missing-schemas "$TMP/hub.yaml"
kubeconform -strict -summary "$HERE/c13_mlflow.yaml" "$HERE/c13_notebook_quota.yaml"
for n in clusterqueues localqueues resourceflavors; do
  curl -sfL "https://raw.githubusercontent.com/kubernetes-sigs/kueue/v0.20.5/config/components/crd/bases/kueue.x-k8s.io_$n.yaml" -o "$TMP/$n.yaml"
done
python3 "$HERE/../../tools/check_crd_yaml.py" "$TMP"/clusterqueues.yaml "$TMP"/localqueues.yaml "$TMP"/resourceflavors.yaml -- "$HERE/c13_research_queues.yaml"
