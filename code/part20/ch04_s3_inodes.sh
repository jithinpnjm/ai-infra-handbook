#!/usr/bin/env bash
# Scenario 3: "No space left on device" while df -h shows free space. The inodes ran out.
# Run as a normal user on Linux: bash ch04_s3_inodes.sh   (answer key: ... answer)
# Safe: a private tmpfs with a tiny inode limit, mounted inside a throwaway user and
# mount namespace. It disappears when the script exits and never touches a real mount.
set -u
if [ "${1:-}" = answer ]; then
  cat <<'KEY'
Cause: every file needs one inode. This filesystem was created with a fixed inode pool and the
       pool is empty, although plenty of data blocks are free.
Proof: df -h shows free space, df -i shows IUse% = 100%. touch fails with ENOSPC.
Not the cause: deleted-but-open files (those hold blocks, not a fixed inode pool in this case).
Fix now: delete or archive the millions of tiny files (find DIR -xdev -type f | head to find the
         directory). Fix for good: stop writing tiny files, or create the filesystem with more inodes.
KEY
  exit 0
fi
[ "$(uname -s)" = Linux ] || { echo "Linux only. Use a Linux VM or container." >&2; exit 2; }
[ "$(id -u)" -ne 0 ] || { echo "Run as a normal user, not root." >&2; exit 2; }
command -v unshare >/dev/null || { echo "unshare not found" >&2; exit 77; }
unshare -Urm true 2>/dev/null || {
  echo "Unprivileged user namespaces are not available here. Skipping." >&2
  echo "Run it in a disposable Linux VM instead, as root, with: mount -t tmpfs -o size=8m,nr_inodes=40 tmpfs /mnt" >&2
  exit 77
}
W=$(mktemp -d "${TMPDIR:-/tmp}/ch04-s3.XXXXXX") || exit 1
trap 'rm -rf "$W"' EXIT
mkdir "$W/mnt"
unshare -Urm bash -c '
  M=$1; E=$2
  mount -t tmpfs -o size=8m,nr_inodes=40 tmpfs "$M" || exit 1
  i=0
  while : 2>"$E" >"$M/f$i"; do i=$((i + 1)); done
  echo "--- created $i files, then: $(cat "$E")"
  echo "--- df -h (bytes): plenty free"
  df -h "$M" | sed -n "1,2p"
  echo "--- df -i (inodes): none free"
  df -i "$M" | sed -n "1,2p"
' _ "$W/mnt" "$W/err.txt"
