#!/usr/bin/env bash
# Task 11: crontab entries that contain an unescaped percent sign.
# Portable: runs with BSD (macOS) and GNU tools. Fixture is synthetic (see c07_make_fixtures.py).
set -euo pipefail
F="${1:-$(dirname "$0")/c07_fixtures/crontab.txt}"
# In a crontab, an unescaped % in the command becomes a newline and the rest goes to stdin.
# Skip comments, blanks and NAME=value lines. A @daily line has its command from field 2,
# an ordinary line from field 6.
awk '
  /^[[:space:]]*(#|$)/ {next}
  /^[A-Za-z_][A-Za-z0-9_]*=/ {next}
  { s = ($1 ~ /^@/) ? 2 : 6
    cmd = $s; for (i=s+1; i<=NF; i++) cmd = cmd " " $i
    if (cmd ~ /(^|[^\\])%/) print "line " NR }' "$F"
