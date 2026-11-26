#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Let's test the text content and line wrapping
labels = [
    "Start-up phases and the remedy that attacks each one",
    "Pull image (vLLM v0.32.0 amd64 image is about 9.2 GB on Docker Hub, not under 5 GB as the book says): pin the tag or digest and use IfNotPresent so a node that has the image does not pull again; pre-pull",
    "Fetch and mount model: weights on a PVC, an OCI image or node-local NVMe instead of downloading from Hugging Face on every start",
    "Start runtime: a second or less per the book",
    "Load weights to GPU: bounded by I/O into GPU memory; faster loader such as Run:ai Model Streamer with --load-format runai_streamer, no repackaging",
    "Warm-up: allocate KV pool, profile, compile and capture CUDA graphs: reuse the torch.compile cache under VLLM_CACHE_ROOT, set VLLM_FORCE_AOT_LOAD=1 to fail loudly on a cache miss, pass --kv-cache-memory to skip profiling",
    "API opens: /health 200",
    "book says these together can cut scale-up from many minutes to tens of seconds depending on model size; --enforce-eager and -O0 make boot fast but decode slower, use them in development only; most time goes to model download and weight load; measure each phase on your own cluster"
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels):
    print(f"{i}: len={len(l)} | {l[:60]}...")
