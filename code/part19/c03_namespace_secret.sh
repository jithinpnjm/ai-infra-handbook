#!/usr/bin/env bash
# Chapter 19.3: namespace and secrets. Tokens come from your shell, never from a file in git.
# HF_TOKEN : a Hugging Face read token that has accepted the Llama 3.1 licence.
# NGC_API_KEY : an NGC API key, only needed for the NIM section of the lab.
set -euo pipefail
: "${HF_TOKEN:?export HF_TOKEN first}"

kubectl create namespace inference --dry-run=client -o yaml | kubectl apply -f -

kubectl -n inference create secret generic hf-token \
  --from-literal=token="${HF_TOKEN}" \
  --dry-run=client -o yaml | kubectl apply -f -

if [ -n "${NGC_API_KEY:-}" ]; then
  # Pull secret for nvcr.io. The username is the literal string $oauthtoken.
  kubectl -n inference create secret docker-registry ngc-secret \
    --docker-server=nvcr.io \
    --docker-username='$oauthtoken' \
    --docker-password="${NGC_API_KEY}" \
    --dry-run=client -o yaml | kubectl apply -f -
  # Key the operator reads for model downloads.
  kubectl -n inference create secret generic ngc-api-secret \
    --from-literal=NGC_API_KEY="${NGC_API_KEY}" \
    --dry-run=client -o yaml | kubectl apply -f -
fi
