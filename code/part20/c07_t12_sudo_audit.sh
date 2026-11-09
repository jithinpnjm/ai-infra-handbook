#!/usr/bin/env bash
# Task 12: who can sudo, and who else has UID 0?
# Usage: c07_t12_sudo_audit.sh [PASSWD GROUP]    Fixtures are synthetic.
# Portable: runs with BSD (macOS) and GNU tools.
set -euo pipefail
D="$(dirname "$0")/c07_fixtures"
P="${1:-$D/passwd.txt}"
G="${2:-$D/group.txt}"
# Colon-separated files. In group, field 4 is a comma list of members.
# A real login user has UID >= 1000 and a shell that does not end in nologin or false.
awk -F: 'NR==FNR { if ($3 >= 1000 && $7 !~ /(nologin|false)$/) ok[$1]=1; next }
         $1 == "sudo" || $1 == "wheel" { n=split($4, m, ","); for (i=1; i<=n; i++) if (m[i] in ok) s[m[i]]=1 }
         END { for (u in s) print u }' "$P" "$G" | sort | awk 'BEGIN{printf "sudo:"} {printf " %s", $0} END{printf "\n"}'
awk -F: '$3 == 0 && $1 != "root" {printf "uid0: %s\n", $1}' "$P"
