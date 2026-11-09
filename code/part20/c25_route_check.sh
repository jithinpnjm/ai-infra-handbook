#!/usr/bin/env bash
# Routing checks for c25_alertmanager.yml. Needs amtool on PATH. Exits 1 on any mismatch.
set -u
cfg="$(dirname "$0")/c25_alertmanager.yml"
fail=0
expect() {  # expect <receiver> <label>...
  want=$1; shift
  got=$(amtool config routes test --config.file="$cfg" "$@" 2>/dev/null)
  if [ "$got" = "$want" ]; then echo "ok   $* -> $got"; else echo "FAIL $* -> $got (want $want)"; fail=1; fi
}
expect pager severity=page model=m1 cluster=c1
expect ticket severity=ticket model=m1
expect ticket alertname=Unlabelled
exit $fail
