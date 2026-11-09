#!/usr/bin/env bash
# Validate YAML files under code/part16..18 against upstream CRDs. Set CRD_SRC to a dir holding shallow clones
# (kserve kueue kuberay argo-workflows volcano kyverno external-secrets k8s-nim-operator chaos-mesh KAI-Scheduler).
set -u; S="${CRD_SRC:?set CRD_SRC}"; cd "$(dirname "$0")/.."
C=( "$S/kserve/config/crd/full/serving.kserve.io_inferenceservices.yaml"
 "$S/kueue/config/components/crd/bases/kueue.x-k8s.io_clusterqueues.yaml" "$S/kueue/config/components/crd/bases/kueue.x-k8s.io_localqueues.yaml"
 "$S/kuberay/helm-chart/kuberay-operator/crds/ray.io_rayclusters.yaml" "$S/argo-workflows/manifests/base/crds/full/argoproj.io_workflows.yaml"
 "$S/volcano/installer/helm/chart/volcano/crd/bases/batch.volcano.sh_jobs.yaml" "$S/volcano/config/crd/volcano/bases/scheduling.volcano.sh_podgroups.yaml"
 "$S/kyverno/config/crds/kyverno/kyverno.io_clusterpolicies.yaml" "$S/external-secrets/config/crds/bases/external-secrets.io_externalsecrets.yaml"
 "$S/k8s-nim-operator/bundle/manifests/apps.nvidia.com_nimservices.yaml" "$S/k8s-nim-operator/bundle/manifests/apps.nvidia.com_nimcaches.yaml"
 "$S/chaos-mesh/config/crd/bases/chaos-mesh.org_schedules.yaml" "$S/KAI-Scheduler/deployments/kai-scheduler/crds/scheduling.run.ai_podgroups.yaml" )
python3 -I tools/check_crd_yaml.py "${C[@]}" -- $(find code/part1[6-8] -name '*.yaml' | sort)
