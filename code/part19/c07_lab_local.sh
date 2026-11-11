#!/usr/bin/env bash
# Runs on a laptop with promtool, amtool, helm and Docker. No cluster, no GPU.
set -euo pipefail
cd "$(dirname "$0")"

python3 c07_acceptance.py                                     # offline checks, seconds
python3 -m pytest test_c07_observability.py test_c07_stack.py -q
C07_E2E_TMP="${C07_E2E_TMP:-$PWD}" python3 c07_e2e.py         # Docker, a few minutes
