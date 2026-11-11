#!/usr/bin/env bash
# Chapter 19.2 lab checks, run after c02_install_stack.sh. Not run here (needs a GPU cluster).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "== node plane: allocatable GPUs and the execution-path check"
kubectl get nodes -L cloud.google.com/gke-accelerator
kubectl get nodes -l pool=h100 -o custom-columns=NAME:.metadata.name,ALLOC:.status.allocatable.nvidia\\.com/gpu
kubectl apply -f "$HERE/c02_smoke_pod.yaml"
kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/nvidia-smi-check --timeout=5m
kubectl logs nvidia-smi-check
kubectl delete -f "$HERE/c02_smoke_pod.yaml"

echo "== teams, priorities and queues"
for ns in team-data-science team-research team-ml-platform; do
  kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f -
done
kubectl apply -f "$HERE/c02_priority_classes.yaml"
kubectl apply -f "$HERE/c02_kueue_queues.yaml"
kubectl apply -f "$HERE/c02_kai_queues.yaml"
kubectl apply -f "$HERE/c02_kai_topology.yaml"
kubectl get clusterqueues
kubectl get queues.scheduling.run.ai

echo "== single-GPU job through Kueue"
kubectl apply -f "$HERE/c02_kueue_job.yaml"
kubectl get workloads -n team-data-science

echo "== two-node gang through Kueue and KAI"
kubectl apply -f "$HERE/c02_pytorchjob.yaml"
kubectl get podgroups.scheduling.run.ai -n team-data-science
kubectl get bindrequests.scheduling.run.ai -n team-data-science
kubectl get pods -n team-data-science -o wide

echo "== serving group and reclaim"
kubectl apply -f "$HERE/c02_lws.yaml"
kubectl get workloads -A

echo "== health gate: exporter pods, Xid series, cordon"
kubectl apply -f "$HERE/c02_dcgm_podmonitoring.yaml"
kubectl get pods -n gpu-operator -l app=nvidia-dcgm-exporter -o wide
POD=$(kubectl get pods -n gpu-operator -l app=nvidia-dcgm-exporter -o name | head -1)
kubectl port-forward -n gpu-operator "$POD" 9400:9400 &
PF=$!
sleep 3
curl -s localhost:9400/metrics | grep DCGM_FI_DEV_XID_ERRORS || true
kill "$PF"
NODE=$(kubectl get nodes -l pool=h100 -o name | head -1)
kubectl cordon "$NODE"
kubectl get "$NODE"
kubectl uncordon "$NODE"
