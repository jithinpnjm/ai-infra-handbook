#!/usr/bin/env bash
# Task 1: top 5 client IPs by request count in an access log.
# Portable: runs with BSD (macOS) and GNU tools. Fixture is synthetic (see c07_make_fixtures.py).
set -euo pipefail
F="${1:-$(dirname "$0")/c07_fixtures/access.log}"
# awk keeps only the first field. sort groups equal IPs. uniq -c counts runs of equal lines.
# The final sort orders by count, then IP, so ties are stable. awk (not head) cuts to 5
# because head closes the pipe early and pipefail can then report exit 141.
awk '{print $1}' "$F" | sort | uniq -c | awk '{print $2, $1}' | sort -k2,2nr -k1,1 | awk 'NR<=5'
