#!/usr/bin/env bash
# Task 10: count error codes in a JSON-lines log that ends in a half-written line.
# Portable: runs with BSD (macOS) and GNU tools. Fixture is synthetic (see c07_make_fixtures.py).
set -euo pipefail
F="${1:-$(dirname "$0")/c07_fixtures/app.jsonl}"
# fromjson? silently drops a line that does not parse, so the truncated last line does
# not abort the run. // "unknown" names the errors that have no code field.
jq -Rr 'fromjson? | select(.level=="error") | (.code // "unknown")' "$F" | sort | uniq -c | awk '{print $2, $1}' | sort -k2,2nr -k1,1
