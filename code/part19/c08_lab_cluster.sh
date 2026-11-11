#!/usr/bin/env bash
# Chapter 19.8 cluster steps. NOT RUN in the handbook: they need MIG-capable GPUs.
# Assumes the GPU Operator is installed with --set mig.strategy=mixed and Kueue v0.20.5 is installed.
# NODE is one 8-GPU H100 node that you are willing to drain.
set -euo pipefail

: "${NODE:?set NODE to the node name}"

# 1. Give MIG Manager the custom layout and point the ClusterPolicy at it
kubectl apply -f c08_mig_config_configmap.yaml
kubectl patch clusterpolicies.nvidia.com/cluster-policy --type='json' \
  -p='[{"op":"replace","path":"/spec/migManager/config/name","value":"c08-custom-mig-config"}]'

# 2. Apply the layout. MIG Manager terminates the GPU pods on the node first.
kubectl label nodes "$NODE" nvidia.com/mig.config=tenant-mix-v1 --overwrite
kubectl get node "$NODE" -L nvidia.com/mig.config,nvidia.com/mig.config.state

# 3. Check what the node now advertises
kubectl get node "$NODE" -o json | jq '.status.allocatable | with_entries(select(.key | startswith("nvidia.com/")))'
kubectl exec -n gpu-operator ds/nvidia-driver-daemonset -- nvidia-smi -L

# 4. Tenants, quotas and queues
kubectl apply -f c08_namespaces_quota.yaml
kubectl apply -f c08_kueue_mig.yaml

# 5. Submit one workload and watch Kueue admit it
kubectl apply -f c08_mig_workload.yaml
kubectl get workloads -n team-chat
kubectl get pods -n team-chat -o wide
