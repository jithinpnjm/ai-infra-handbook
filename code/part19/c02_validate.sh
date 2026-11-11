#!/usr/bin/env bash
# Re-run the chapter 19.2 manifest validation. UPSTREAM is a directory holding shallow clones of
# kueue, KAI-Scheduler, gpu-operator, training-operator, lws and prometheus-engine at the tags listed
# in the chapter's verification log. Run from the handbook root.
set -euo pipefail
: "${UPSTREAM:?set UPSTREAM to the directory with the upstream clones}"
U="$UPSTREAM"
python3 tools/check_crd_yaml.py \
  "$U/kueue/config/components/crd/bases/kueue.x-k8s.io_clusterqueues.yaml" \
  "$U/kueue/config/components/crd/bases/kueue.x-k8s.io_resourceflavors.yaml" \
  "$U/kueue/config/components/crd/bases/kueue.x-k8s.io_localqueues.yaml" \
  "$U/KAI-Scheduler/deployments/kai-scheduler/crds/scheduling.run.ai_queues.yaml" \
  "$U/KAI-Scheduler/deployments/kai-scheduler/crds/kai.scheduler_topologies.yaml" \
  "$U/training-operator/manifests/base/crds/kubeflow.org_pytorchjobs.yaml" \
  "$U/lws/config/crd/bases/leaderworkerset.x-k8s.io_leaderworkersets.yaml" \
  "$U/prometheus-engine/charts/operator/crds/monitoring.googleapis.com_podmonitorings.yaml" \
  -- code/part19/c02_*.yaml
kubeconform -summary -strict -ignore-missing-schemas \
  code/part19/c02_priority_classes.yaml code/part19/c02_smoke_pod.yaml \
  code/part19/c02_upgrade_validation.yaml code/part19/c02_gpu_operator_quota.yaml \
  code/part19/c02_kueue_job.yaml
# Render the GPU Operator chart with the values file and check the ClusterPolicy it produces.
helm template gpu-operator "$U/gpu-operator/deployments/gpu-operator" -n gpu-operator \
  -f code/part19/c02_gpu_operator_values.yaml > "${TMPDIR:-/tmp}/c02-rendered-op.yaml"
python3 tools/check_crd_yaml.py "$U/gpu-operator/deployments/gpu-operator/crds/nvidia.com_clusterpolicies.yaml" \
  -- "${TMPDIR:-/tmp}/c02-rendered-op.yaml"
# Render the Kueue chart with the values file.
helm template kueue "$U/kueue/charts/kueue" -n kueue-system -f code/part19/c02_kueue_values.yaml > /dev/null
