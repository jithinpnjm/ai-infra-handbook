#!/usr/bin/env bash
# Compare the counters taken before and after the sweeps and show only what moved,
# leaving out the data and packet counters that climb under any load.
# Usage: c05_diff_counters.sh BEFORE AFTER
# Exit status is 1 when a line other than data or packet counters changed.
set -euo pipefail
before="${1:?usage: c05_diff_counters.sh BEFORE AFTER}"
after="${2:?usage: c05_diff_counters.sh BEFORE AFTER}"

moved="$(diff "$before" "$after" | grep -E '^[<>]' | grep -v -E 'port_(rcv|xmit)_(data|packets)|unicast|multicast' || true)"
if [ -z "$moved" ]; then
  echo "error counters flat"
else
  echo "$moved"
  exit 1
fi
