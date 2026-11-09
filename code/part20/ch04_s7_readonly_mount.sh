#!/usr/bin/env bash
# Scenario 7: mode 777, owner is you, and still "Read-only file system". The mount is read-only.
# Same idea as readOnlyRootFilesystem: true in a Kubernetes pod (see ch04_ro_rootfs_pod.yaml).
# Run as a normal user on Linux: bash ch04_s7_readonly_mount.sh   (answer key: ... answer)
# Safe: a bind mount inside a throwaway user and mount namespace.
set -u
if [ "${1:-}" = answer ]; then
  cat <<'KEY'
Cause: the mount is read-only, so any write returns EROFS before ownership or mode is checked.
Proof: the error text is "Read-only file system" (not "Permission denied"); findmnt or
       /proc/self/mountinfo shows ro. Even root gets the same error.
Not the cause: ownership, ACLs or capabilities.
Fix now: write somewhere else (an emptyDir or tmpfs mounted for scratch), or remount rw if allowed.
Fix for good: keep the root read-only on purpose and mount writable volumes only where the app
       writes: /tmp, caches, sockets.
Detail: a read-only BIND mount makes only that mount read-only. The original directory stays
       writable (mount(8)).
KEY
  exit 0
fi
[ "$(uname -s)" = Linux ] || { echo "Linux only. Use a Linux VM or container." >&2; exit 2; }
[ "$(id -u)" -ne 0 ] || { echo "Run as a normal user, not root." >&2; exit 2; }
command -v unshare >/dev/null || { echo "unshare not found" >&2; exit 77; }
unshare -Urm true 2>/dev/null || { echo "Unprivileged user namespaces are not available here. Skipping." >&2; exit 77; }
W=$(mktemp -d "${TMPDIR:-/tmp}/ch04-s7.XXXXXX") || exit 1
trap 'rm -rf "$W"' EXIT
mkdir "$W/data" && chmod 777 "$W/data"
unshare -Urm bash -c '
  D=$1
  echo "--- 1. before: writable"
  echo one > "$D/a.txt" && echo "write ok"
  mount --bind "$D" "$D" && mount -o remount,bind,ro "$D" || { echo "bind remount failed"; exit 1; }
  echo "--- 2. after the read-only bind mount"
  echo two > "$D/b.txt"; echo "exit status: $?"
  rm "$D/a.txt"; echo "rm exit status: $?"
  echo "--- 3. the mount flags"
  grep " $D " /proc/self/mountinfo | cut -d" " -f5-6
  echo "--- 4. reading still works"
  cat "$D/a.txt"
' _ "$W/data"
echo "--- 5. outside the namespace the original directory is still writable"
echo three > "$W/data/c.txt" && echo "write ok"
