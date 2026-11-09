import argparse, json, sys
from datetime import datetime, timezone
import opslib as O, restore_backup as R

def main(argv=None, now=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--backup", required=True); ap.add_argument("--expected-rto", required=True); ap.add_argument("--expected-rpo", required=True); a = ap.parse_args(argv)
    try: r = R.restore(a.backup, "verify")
    except ValueError as e: print("BACKUP INVALID:", e); return 1
    age = (now or datetime.now(timezone.utc)) - O.parse_ts(r["taken_at"]); bad = []
    if r["seconds"] > O.parse_duration(a.expected_rto).total_seconds(): bad.append("restore slower than RTO")
    if age > O.parse_duration(a.expected_rpo): bad.append(f"backup is {O.fmt_td(age)} old, beyond the RPO")
    print("BACKUP OK" if not bad else "BACKUP FAILS TARGETS: " + "; ".join(bad)); return 1 if bad else 0

if __name__ == "__main__": sys.exit(main())
