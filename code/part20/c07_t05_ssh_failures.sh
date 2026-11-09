#!/usr/bin/env bash
# Task 5: top 3 source IPs of failed SSH logins.
# Portable: runs with BSD (macOS) and GNU tools. Fixture is synthetic (see c07_make_fixtures.py).
set -euo pipefail
F="${1:-$(dirname "$0")/c07_fixtures/auth.log}"
# 'invalid user' lines have extra words, so field numbers shift. Match on the text
# after the word "from" instead of counting fields.
grep 'Failed password' "$F" | sed -E 's/.* from ([0-9.]+) port .*/\1/' | sort | uniq -c | awk '{print $2, $1}' | sort -k2,2nr -k1,1 | awk 'NR<=3'
