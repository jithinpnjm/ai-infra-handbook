#!/usr/bin/env bash
# Task 2: the 5 slowest requests (request_time is the last field).
# Portable: runs with BSD (macOS) and GNU tools. Fixture is synthetic (see c07_make_fixtures.py).
set -euo pipefail
F="${1:-$(dirname "$0")/c07_fixtures/access.log}"
# $NF is the last field, so spaces inside the user-agent do not matter.
# sort -rn is numeric. A text sort would put 9.5 above 61.004.
awk '{print $NF, $9, $7}' "$F" | sort -k1,1nr | awk 'NR<=5'
