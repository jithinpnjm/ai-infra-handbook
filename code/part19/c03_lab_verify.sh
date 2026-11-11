#!/usr/bin/env bash
# Chapter 19.3: verification commands for the GKE lab. Not run: needs the cluster from c03_node_pool.sh.
set -euo pipefail
NS=inference

# Step 3: both GPU nodes advertise one GPU.
kubectl get nodes -l cloud.google.com/gke-accelerator=nvidia-tesla-a100 \
  -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'

# Step 5: the objects exist and the predictor becomes ready.
kubectl -n "${NS}" get servingruntime,inferenceservice
kubectl -n "${NS}" get pods -l serving.kserve.io/inferenceservice=llama31-8b -w

# Step 6: the probes in the running pod match the runtime file.
kubectl -n "${NS}" get pod -l serving.kserve.io/inferenceservice=llama31-8b \
  -o jsonpath='{.items[0].spec.containers[0].startupProbe}{"\n"}'

# Step 6: how long weights took, and what KV cache vLLM actually got.
kubectl -n "${NS}" logs -l serving.kserve.io/inferenceservice=llama31-8b --tail=400 \
  | grep -i -E 'loading model weights took|KV cache|max_num_seqs|gpu_memory_utilization'
