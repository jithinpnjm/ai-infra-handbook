#!/usr/bin/env bash
# Scenario 8: even root cannot change or delete a file. The immutable attribute is set.
# Needs root or passwordless sudo, and a filesystem that supports chattr (ext4 or XFS, not tmpfs).
# Run on Linux: bash ch04_s8_immutable.sh   (answer key: ... answer)
# Safe: touches one temp file only and clears the flag again on exit. Skips if it cannot.
set -u
if [ "${1:-}" = answer ]; then
  cat <<'KEY'
Cause: the file has the immutable inode flag (chattr +i). It cannot be modified, deleted,
       renamed or linked, and most metadata changes are refused, for every user including root.
Proof: lsattr shows an "i" in the flags; ls -l does not show it. Errors are EPERM
       ("Operation not permitted"), which is different from EACCES.
Not the cause: mode, owner or ACL. chmod fails because of the flag, not because of the bits.
Fix now: chattr -i FILE as root (needs CAP_LINUX_IMMUTABLE). Find out who set it and why first.
Fix for good: if a hardening tool sets it on purpose, change the file through that tool.
KEY
  exit 0
fi
[ "$(uname -s)" = Linux ] || { echo "Linux only. Use a Linux VM or container." >&2; exit 2; }
if [ "$(id -u)" -eq 0 ]; then S=""
elif command -v sudo >/dev/null && sudo -n true 2>/dev/null; then S="sudo"
else echo "Needs root or passwordless sudo. Skipping." >&2; exit 77; fi
command -v chattr >/dev/null && command -v lsattr >/dev/null || { echo "chattr or lsattr missing. Skipping." >&2; exit 77; }
W=$(mktemp -d "${TMPDIR:-/tmp}/ch04-s8.XXXXXX") || exit 1
F="$W/protected.conf"
trap '$S chattr -i "$F" 2>/dev/null; rm -rf "$W"' EXIT
echo "v1" > "$F"
$S chattr +i "$F" 2>"$W/err" || { echo "chattr +i not supported here: $(cat "$W/err"). Use an ext4 or xfs directory." >&2; exit 77; }
echo "--- 1. ls -l shows nothing unusual"
ls -l "$F"
echo "--- 2. every change is refused"
echo "v2" >> "$F"
chmod 666 "$F"
rm -f "$F"
$S rm -f "$F"
echo "--- 3. lsattr shows the flag"
lsattr "$F"
echo "--- 4. fix"
$S chattr -i "$F" && echo "v2" >> "$F" && cat "$F"
