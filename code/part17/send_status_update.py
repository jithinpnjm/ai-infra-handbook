import argparse, sys
import opslib as O

SEVERITIES = ("SEV-1", "SEV-2", "SEV-3", "SEV-4")

def main(argv=None):
    ap = argparse.ArgumentParser(); [ap.add_argument(f"--{k}", required=True) for k in ("incident-id", "severity", "status")]; a = ap.parse_args(argv)
    if a.severity not in SEVERITIES: print(f"REFUSED: severity must be one of {SEVERITIES}"); return 1
    O.outbox("status_update", incident=a.incident_id, severity=a.severity, status=a.status); print(f"[{a.severity}] {a.incident_id}: {a.status}"); return 0

if __name__ == "__main__": sys.exit(main())
