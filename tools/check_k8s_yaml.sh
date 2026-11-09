#!/usr/bin/env bash
# kubeconform over every manifest that has a kind (core Kubernetes types). CRD kinds are skipped here and covered by
# tools/check_code_yaml.sh; config files (Prometheus, Alertmanager, OTel) are covered by promtool/amtool in the lab.
cd "$(dirname "$0")/.." || exit 1
files=$(grep -lE '^kind:' $(find code/part1[6-8] -name '*.yaml') )
kubeconform -summary -strict -ignore-missing-schemas -skip PodGroup,InferenceService,Workflow,ClusterQueue,LocalQueue,RayCluster,PyTorchJob,Experiment,Rollout,SeldonDeployment,ClusterPolicy,ConstraintTemplate,ExternalSecret,NIMService,NIMCache,Schedule,Job,ModelStage $files
