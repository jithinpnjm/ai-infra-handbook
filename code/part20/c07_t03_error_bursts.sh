#!/usr/bin/env bash
# Task 3: the three busiest minutes of 5xx responses.
# Portable: runs with BSD (macOS) and GNU tools. Fixture is synthetic (see c07_make_fixtures.py).
set -euo pipefail
F="${1:-$(dirname "$0")/c07_fixtures/access.log}"
# $4 looks like [12/Mar/2026:10:42:07 so characters 2..18 are the date and the minute.
# $9 is the status. The regex ^5 matches 500 to 599 and nothing else.
awk '$9 ~ /^5/ {print substr($4,2,17)}' "$F" | sort | uniq -c | awk '{print $2, $1}' | sort -k2,2nr -k1,1 | awk 'NR<=3'
