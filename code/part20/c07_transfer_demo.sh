#!/usr/bin/env bash
# tar, rsync and curl one-liners on temp files and a local HTTP server. Safe: everything
# lives in one temp directory removed on exit. Works with BSD (macOS) and GNU tools.
set -euo pipefail
W="$(mktemp -d)"; SRV=""
trap '[ -n "$SRV" ] && kill "$SRV" 2>/dev/null; rm -rf "$W"' EXIT
mkdir -p "$W/src/sub dir" "$W/dst" "$W/www"
echo one > "$W/src/a.txt"; echo two > "$W/src/sub dir/b.txt"

# tar: -C changes directory first, so the archive holds relative paths.
tar -czf "$W/src.tgz" -C "$W" src
echo "tar_list:"; tar -tzf "$W/src.tgz" | sort
mkdir "$W/restore"; tar -xzf "$W/src.tgz" -C "$W/restore"
echo "tar_roundtrip_equal: $(diff -r "$W/src" "$W/restore/src" >/dev/null && echo yes || echo no)"

# rsync: the trailing slash on the source means "the contents of src".
rsync -a "$W/src/" "$W/dst/"
echo "rsync_first_copy: $(find "$W/dst" -type f | wc -l | tr -d ' ') files"
echo three > "$W/src/c.txt"
echo "rsync_dry_run_new_file:"; rsync -a --dry-run --itemize-changes "$W/src/" "$W/dst/" | grep c.txt | sed 's/^/  /'

# curl against a local server: -f turns HTTP 4xx/5xx into exit 22, -w prints timings.
echo hello > "$W/www/ok.txt"
python3 -u -m http.server 0 --bind 127.0.0.1 --directory "$W/www" >"$W/srv.log" 2>&1 & SRV=$!; disown
for _ in $(seq 50); do PORT="$(sed -nE 's/.*port ([0-9]+).*/\1/p' "$W/srv.log" | head -1)"; [ -n "$PORT" ] && break; sleep 0.1; done
U="http://127.0.0.1:$PORT"
echo "curl_ok: $(curl -sS -o /dev/null -w '%{http_code}' "$U/ok.txt")"
echo "curl_404_without_f: $(curl -sS -o /dev/null -w '%{http_code}' "$U/missing")"
rc=0; curl -sSf -o /dev/null "$U/missing" 2>/dev/null || rc=$?
echo "curl_404_with_f_exit: $rc"
echo "curl_timing_fields: $(curl -sS -o /dev/null -w 'connect=%{time_connect} total=%{time_total}' "$U/ok.txt" | sed -E 's/[0-9]+\.[0-9]+/N/g')"
