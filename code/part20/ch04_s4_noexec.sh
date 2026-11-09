#!/usr/bin/env bash
# Scenario 4: a script has mode 755 but "Permission denied" when run. The mount is noexec.
# Run as a normal user on Linux: bash ch04_s4_noexec.sh   (answer key: ... answer)
# Safe: private tmpfs inside a throwaway user and mount namespace.
set -u
if [ "${1:-}" = answer ]; then
  cat <<'KEY'
Cause: the filesystem is mounted noexec, so execve() of any file on it fails with EACCES
       before the mode bits matter. chmod +x cannot help.
Proof: findmnt (or /proc/self/mountinfo) lists noexec for that mount; strace shows
       execve(...) = -1 EACCES. Running "sh file" works because sh only READS the file.
Not the cause: the file's mode, owner or ACL.
Fix now: run the program from a mount without noexec, or remount with exec if policy allows.
Fix for good: ship binaries in the image or a normal mount; keep noexec on /tmp and data volumes.
KEY
  exit 0
fi
[ "$(uname -s)" = Linux ] || { echo "Linux only. Use a Linux VM or container." >&2; exit 2; }
[ "$(id -u)" -ne 0 ] || { echo "Run as a normal user, not root." >&2; exit 2; }
command -v unshare >/dev/null || { echo "unshare not found" >&2; exit 77; }
unshare -Urm true 2>/dev/null || { echo "Unprivileged user namespaces are not available here. Skipping." >&2; exit 77; }
W=$(mktemp -d "${TMPDIR:-/tmp}/ch04-s4.XXXXXX") || exit 1
trap 'rm -rf "$W"' EXIT
mkdir "$W/mnt"
unshare -Urm bash -c '
  M=$1
  mount -t tmpfs -o size=1m,noexec tmpfs "$M" || exit 1
  printf "#!/bin/sh\necho it ran\n" > "$M/run.sh"
  chmod 755 "$M/run.sh"
  ls -l "$M/run.sh"
  echo "--- 1. execute it"
  "$M/run.sh"; echo "exit status: $?"
  echo "--- 2. the mount options"
  grep " $M " /proc/self/mountinfo | cut -d" " -f5-6
  echo "--- 3. reading is fine, so an interpreter can still run it"
  sh "$M/run.sh"
  echo "--- 4. remount with exec and try again"
  # A plain "remount,exec" fails here with EINVAL (tmpfs rejects the uid= and gid= options that
  # mount(8) re-sends). A bind remount changes only the per-mount flag, which is what we want.
  mount -o remount,bind,exec "$M" && "$M/run.sh"
' _ "$W/mnt"
