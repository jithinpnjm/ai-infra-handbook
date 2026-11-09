#!/usr/bin/env bash
# Scenario 3: a container is OOM killed while the node has plenty of free memory.
# Needs Docker on Linux. The container has a 100 MiB limit and tries to hold 300 MiB.
set -euo pipefail
command -v docker >/dev/null || { echo "docker not found"; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
NAME=c05_oom_demo
trap 'docker rm -f "$NAME" >/dev/null 2>&1 || true' EXIT

docker run -d --name "$NAME" --memory=100m --memory-swap=100m python:3.12-slim \
  python -c "x = b'x' * (300 * 1024 * 1024); print(len(x))" >/dev/null
docker wait "$NAME" >/dev/null
echo "== OOMKilled flag and exit code"
docker inspect -f 'OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}}' "$NAME"
echo "== host memory is not the problem"
free -m
echo "== kernel log (may need sudo; this prints nothing if dmesg is restricted)"
if dmesg 2>/dev/null | tail -n 200 > /tmp/c05_s3_dmesg.txt && [ -s /tmp/c05_s3_dmesg.txt ]; then
  python3 "$HERE/c05_oom_parse.py" < /tmp/c05_s3_dmesg.txt
else
  echo "dmesg unavailable: rerun with sudo or read: journalctl -k | grep -i oom"
fi
rm -f /tmp/c05_s3_dmesg.txt
