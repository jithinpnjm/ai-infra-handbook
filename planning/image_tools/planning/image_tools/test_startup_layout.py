#!/usr/bin/env python3
import re

# Font metrics rules from prompt:
# sans: 0.60 * font-size per character
# monospace: 0.62 * font-size per character
# Every text line must fit inside its box with at least 16 px padding.
# Box width = 480 px.
# With at least 16px padding on both sides, max text width <= 480 - 32 = 448 px.
# Let's aim for max text width <= 430 px (>= 25px padding on each side!).

def text_width(line_parts):
    # line_parts is a list of (text, is_mono, font_size)
    w = 0.0
    for text, is_mono, fs in line_parts:
        rate = 0.62 if is_mono else 0.60
        w += len(text) * rate * fs
    return w

# The 6 items:
# 1. 'Pull image (vLLM v0.32.0 amd64 image is about 9.2 GB on Docker Hub, not under 5 GB as the book says): pin the tag or digest and use IfNotPresent so a node that has the image does not pull again; pre-pull'
# 2. 'Fetch and mount model: weights on a PVC, an OCI image or node-local NVMe instead of downloading from Hugging Face on every start'
# 3. 'Start runtime: a second or less per the book'
# 4. 'Load weights to GPU: bounded by I/O into GPU memory; faster loader such as Run:ai Model Streamer with --load-format runai_streamer, no repackaging'
# 5. 'Warm-up: allocate KV pool, profile, compile and capture CUDA graphs: reuse the torch.compile cache under VLLM_CACHE_ROOT, set VLLM_FORCE_AOT_LOAD=1 to fail loudly on a cache miss, pass --kv-cache-memory to skip profiling'
# 6. 'API opens: /health 200'
# Footer: 'book says these together can cut scale-up from many minutes to tens of seconds depending on model size; --enforce-eager and -O0 make boot fast but decode slower, use them in development only; most time goes to model download and weight load; measure each phase on your own cluster'

print("Ready to analyze line wraps.")
