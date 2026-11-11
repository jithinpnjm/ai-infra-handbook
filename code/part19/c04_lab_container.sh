#!/bin/bash
# code/part19/c04_lab_container.sh
# CPU smoke test in a throwaway container: 2 processes, gloo backend, FSDP2 and DCP. No GPU needed.
# Run from the repository root with Docker running. Downloads PyTorch 2.15.0 (CPU wheel).
set -eu
docker run -d --name c04lab python:3.12-slim sleep 3600
docker exec c04lab pip install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
docker exec c04lab pip install --no-cache-dir numpy pytest
docker exec c04lab mkdir /w
docker cp code/part19 c04lab:/w/part19

# Run the CPU smoke tests: failure injection, async save, corrupt checkpoint, 2-to-1 reshard, SIGTERM
docker exec c04lab sh -c "cd /w/part19 && python -m pytest test_c04_train_smoke.py -q -p no:cacheprovider"

# Or drive it by hand: train 12 steps, inject a failure at step 6, watch the resume
docker exec c04lab sh -c "cd /w/part19 && python -m torch.distributed.run --nproc-per-node=2 --max-restarts=3 \
    c04_train.py --ckpt-dir /w/ck --steps 12 --ckpt-every 4 --fail-at-step 6 2>&1 | grep -E 'resumed|done'"

docker rm -f c04lab
