#!/usr/bin/env bash
# Seven bash robustness pitfalls, each run in its own child shell so one failure
# does not stop the demo. Safe: only temp files. Works with bash 3.2 (macOS) and 5.x.
# Output format: "name: exit=N out=..." so a test can check it.
run() { # run NAME SCRIPT
  local out rc
  out="$(bash -c "$2" 2>&1)" && rc=0 || rc=$?
  printf '%s: exit=%s out=%s\n' "$1" "$rc" "$(printf '%s' "$out" | tr '\n' '|')"
}

run if_hides_e      'set -e; f(){ false; echo after-false; }; if f; then echo ok; fi'
run pipefail_off    'false | true; echo status=$?'
run pipefail_on     'set -o pipefail; false | true; echo status=$?'
run unset_var       'set -u; echo "$MISSING_VAR"; echo not-reached'
run local_masks     'set -e; f(){ local x=$(false); echo reached; }; f'
run arith_zero      'set -e; i=0; ((i++)); echo not-reached'
run quote_split     'f="my file.log"; set -- $f; echo unquoted=$#; set -- "$f"; echo quoted=$#'
run trap_cleanup    'set -e; t=$(mktemp); trap "rm -f $t; echo cleaned" EXIT; false; echo not-reached'
