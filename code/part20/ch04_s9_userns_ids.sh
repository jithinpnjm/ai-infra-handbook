#!/usr/bin/env bash
# Bonus: why "root" inside a container cannot touch a host file. IDs are mapped, not shared.
# Run as a normal user on Linux: bash ch04_s9_userns_ids.sh   (answer key: ... answer)
# Safe: read-only. It only prints IDs and runs test -w. It never writes outside a temp dir.
set -u
if [ "${1:-}" = answer ]; then
  cat <<'KEY'
Cause: in a user namespace only the IDs listed in uid_map exist. Files owned by an unmapped ID
       show up as the overflow ID (65534 by default), and the namespace's root has capabilities
       only for objects the namespace owns.
Proof: /proc/self/uid_map shows one line, "0 <your uid> 1". A file owned by real root shows
       owner 65534 inside. test -w on it fails.
Lesson: "I am root in the container" is not "I am root on the node". Check the mapping and the
       capability sets before blaming chmod.
KEY
  exit 0
fi
[ "$(uname -s)" = Linux ] || { echo "Linux only. Use a Linux VM or container." >&2; exit 2; }
[ "$(id -u)" -ne 0 ] || { echo "Run as a normal user, not root." >&2; exit 2; }
unshare -Ur true 2>/dev/null || { echo "Unprivileged user namespaces are not available here. Skipping." >&2; exit 77; }
W=$(mktemp -d "${TMPDIR:-/tmp}/ch04-s9.XXXXXX") || exit 1
trap 'rm -rf "$W"' EXIT
echo mine > "$W/mine.txt"
echo "--- outside: id, owner of a root-owned file, my own file"
id -u; stat -c '%u' /etc/hostname; stat -c '%u' "$W/mine.txt"
unshare -Ur bash -c '
  echo "--- inside: id, mapping, owners"
  id -u
  cat /proc/self/uid_map
  stat -c "root-owned file now owned by: %u" /etc/hostname
  stat -c "my own file now owned by: %u" "$1/mine.txt"
  test -w /etc/hostname && echo "can write /etc/hostname" || echo "cannot write /etc/hostname"
  grep -E "^(CapEff|CapBnd)" /proc/self/status
' _ "$W"
