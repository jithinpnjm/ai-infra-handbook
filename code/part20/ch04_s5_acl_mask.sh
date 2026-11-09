#!/usr/bin/env bash
# Scenario 5: an ACL grants a service write access, but a later chmod silently cancelled it.
# Run as a normal user on Linux with the acl package: bash ch04_s5_acl_mask.sh   (key: ... answer)
# Safe: one file in a temp dir. The "service" user is a made-up numeric ID, nobody logs in as it.
set -u
if [ "${1:-}" = answer ]; then
  cat <<'KEY'
Cause: with an ACL present, the group bits of the mode ARE the ACL mask. chmod 640 set the mask
       to r--, and the mask caps every named user and group entry, so user:12345:rw- became
       effectively read-only.
Proof: getfacl prints "#effective:r--" next to the entry. ls -l shows a "+" after the mode.
Not the cause: the named entry itself, which still says rw-.
Fix now: setfacl -m m::rw FILE (or chmod g+w FILE) to widen the mask again.
Fix for good: set ACLs after chmod in deploy scripts, and check effective rights, not entries.
KEY
  exit 0
fi
[ "$(uname -s)" = Linux ] || { echo "Linux only. Use a Linux VM or container." >&2; exit 2; }
[ "$(id -u)" -ne 0 ] || { echo "Run as a normal user, not root." >&2; exit 2; }
command -v setfacl >/dev/null && command -v getfacl >/dev/null || { echo "Install the acl package. Skipping." >&2; exit 77; }
W=$(mktemp -d "${TMPDIR:-/tmp}/ch04-s5.XXXXXX") || exit 1
trap 'rm -rf "$W"' EXIT
F="$W/svc.conf"
echo "key=value" > "$F"
setfacl -m u:12345:rw "$F" 2>"$W/err" || { echo "ACLs not supported on this filesystem: $(cat "$W/err"). Set TMPDIR to an ext4 or xfs directory." >&2; exit 77; }
echo "--- 1. service user 12345 was granted rw"
getfacl -p "$F" 2>/dev/null
echo "--- 2. somebody 'tightens' the file with chmod"
chmod 640 "$F"
ls -l "$F"
echo "--- 3. the entry still says rw-, the effective right does not"
getfacl -p "$F" 2>/dev/null
echo "--- 4. fix: widen the mask"
setfacl -m m::rw "$F"
getfacl -p "$F" 2>/dev/null
