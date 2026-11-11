#!/usr/bin/env bash
# Chapter 19.2 step 1: zonal GKE Standard cluster plus an H100 pool set up for the GPU Operator path.
# Flags checked against gcloud 592.0.0 --help (2026-11-10). Needs GPU quota; not run here.
set -euo pipefail
: "${PROJECT:?set PROJECT}"
ZONE="${ZONE:-us-central1-a}"
CLUSTER="${CLUSTER:-ml-platform}"

# System pool: CPU only. GKE adds the nvidia.com/gpu=present:NoSchedule taint to GPU nodes
# only when the cluster already has a non-GPU pool, so keep this pool.
gcloud container clusters create "$CLUSTER" \
  --project "$PROJECT" --zone "$ZONE" \
  --release-channel regular \
  --num-nodes 1 --machine-type e2-standard-4 \
  --workload-pool "${PROJECT}.svc.id.goog" \
  --enable-managed-prometheus \
  --monitoring SYSTEM

# GPU pool: the node label turns off the GKE device plugin and gpu-driver-version=disabled
# turns off the automatic driver, as the NVIDIA GPU Operator GKE page requires when the
# Operator owns the device plugin. The Google driver installer is applied separately.
gcloud container node-pools create h100-pool \
  --project "$PROJECT" --cluster "$CLUSTER" --zone "$ZONE" \
  --machine-type a3-highgpu-8g \
  --accelerator type=nvidia-h100-80gb,count=8,gpu-driver-version=disabled \
  --num-nodes 2 \
  --node-labels pool=h100,gke-no-default-nvidia-gpu-device-plugin=true \
  --placement-type COMPACT

gcloud container clusters get-credentials "$CLUSTER" --project "$PROJECT" --zone "$ZONE"
