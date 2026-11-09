#!/usr/bin/env bash
# Scenario 6: the file is readable by everyone but open() says "Permission denied".
# The directory above it has no search (x) permission. chmod on the FILE cannot help.
# Run as a normal user on Linux: bash ch04_s6_dir_search.sh   (answer key: ... answer)
# Safe: temp dir only.
set -u
if [ "${1:-}" = answer ]; then
  cat <<'KEY'
Cause: opening a path needs search (x) permission on every directory on the way down. The
       directory had r-- but no x, so the kernel stops at that directory with EACCES.
Proof: strace -e trace=%file shows openat(...) = -1 EACCES. namei -l (if installed) shows the
       directory with no x. ls DIR works (read) while stat DIR/file fails (search).
Not the cause: the file's own mode.
Fix now: chmod u+x (or the right class) on the directory. Check EVERY parent, not only the last.
Fix for good: give directories 755 or 750 by default; use setgid directories for shared groups.
KEY
  exit 0
fi
[ "$(uname -s)" = Linux ] || { echo "Linux only. Use a Linux VM or container." >&2; exit 2; }
[ "$(id -u)" -ne 0 ] || { echo "Run as a normal user, not root." >&2; exit 2; }
W=$(mktemp -d "${TMPDIR:-/tmp}/ch04-s6.XXXXXX") || exit 1
trap 'chmod -R u+rwx "$W" 2>/dev/null; rm -rf "$W"' EXIT
mkdir "$W/secret"
echo "token" > "$W/secret/app.conf"
chmod 644 "$W/secret/app.conf"
chmod 600 "$W/secret"            # r and w for the owner, but no x
echo "--- 1. the file looks fine"
ls -ld "$W/secret"
echo "--- 2. open it"
cat "$W/secret/app.conf"; echo "exit status: $?"
echo "--- 3. chmod on the file does nothing for this"
chmod 777 "$W/secret/app.conf" 2>&1 | head -1
cat "$W/secret/app.conf" 2>&1 | head -1
echo "--- 4. reading the directory works, searching it does not"
ls "$W/secret" 2>&1 | head -2
echo "--- 5. the walk, if namei and strace exist"
command -v namei >/dev/null && namei -l "$W/secret/app.conf" 2>&1 | tail -3
command -v strace >/dev/null && strace -e trace=%file cat "$W/secret/app.conf" 2>&1 | grep -E 'EACCES' | head -2
echo "--- 6. fix"
chmod 700 "$W/secret"
cat "$W/secret/app.conf"
