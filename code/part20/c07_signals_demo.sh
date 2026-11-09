#!/usr/bin/env bash
# SIGTERM versus SIGKILL, and a zombie. Safe: starts short-lived children of its own
# and cleans them up. Works on macOS and Linux. Prints "name: value" lines.
set -u
cleanup() { kill -KILL "${P1:-0}" "${P2:-0}" "${P3:-0}" 2>/dev/null; wait 2>/dev/null; }
trap cleanup EXIT

# A: handles TERM, exits 0 after cleanup.
bash -c 'trap "exit 0" TERM; while :; do sleep 0.1; done' & P1=$!
sleep 0.5; kill -TERM "$P1"; wait "$P1"; echo "A_handles_TERM: exit=$?"

# B: ignores TERM. TERM does nothing, KILL cannot be ignored (128+9=137).
bash -c 'trap "" TERM; while :; do sleep 0.1; done' & P2=$!
sleep 0.5; kill -TERM "$P2"; sleep 0.5
if kill -0 "$P2" 2>/dev/null; then echo "B_ignores_TERM: still_running=yes"; fi
kill -KILL "$P2"; wait "$P2"; echo "B_after_KILL: exit=$?"

# C: no handler at all. The default action of TERM ends it (128+15=143).
bash -c 'while :; do sleep 0.1; done' & P3=$!
sleep 0.5; kill -TERM "$P3"; wait "$P3"; echo "C_default_TERM: exit=$?"

# D: a zombie. The parent execs sleep, which never calls wait, so the dead child stays.
bash -c 'sleep 0.2 & exec sleep 3' & P4=$!
sleep 1
Z="$(ps -A -o pid=,ppid=,stat=,comm= | awk -v p="$P4" '$2 == p && $3 ~ /^Z/')"
echo "D_zombie_row: $Z"
echo "D_zombie_count: $(printf "%s" "$Z" | grep -c .)"
echo "D_parent_pid_matches: $([ "$(echo "$Z" | awk '{print $2}')" = "$P4" ] && echo yes || echo no)"
kill -KILL "$P4" 2>/dev/null; wait "$P4" 2>/dev/null
exit 0
