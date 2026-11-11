#!/usr/bin/env bash
# Chapter 19.3: GKE Standard cluster and one A100 40 GB node pool.
# Not run: needs a GCP project with A100 quota. Check machine type and flags against
# https://docs.cloud.google.com/kubernetes-engine/docs/how-to/gpus before you run it.
set -euo pipefail

CLUSTER="${CLUSTER:-ai-serving}"
ZONE="${ZONE:-us-central1-a}"

# One small CPU pool for system pods. GKE adds the nvidia.com/gpu=present:NoSchedule
# taint to GPU nodes only when a non-GPU pool exists in the cluster.
gcloud container clusters create "${CLUSTER}" \
  --location="${ZONE}" \
  --num-nodes=1 \
  --machine-type=e2-standard-4

# a2-highgpu-1g is the A2 machine type with one A100 40 GB GPU.
# count must equal the GPU count of the machine type.
# gpu-driver-version=default installs the default driver for the node GKE version.
gcloud container node-pools create a100-pool \
  --cluster="${CLUSTER}" \
  --location="${ZONE}" \
  --node-locations="${ZONE}" \
  --num-nodes=2 \
  --machine-type=a2-highgpu-1g \
  --accelerator="type=nvidia-tesla-a100,count=1,gpu-driver-version=default"

gcloud container clusters get-credentials "${CLUSTER}" --location="${ZONE}"

# Both GPU nodes must report one allocatable GPU before you deploy anything.
kubectl get nodes \
  -l cloud.google.com/gke-accelerator=nvidia-tesla-a100 \
  -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'
