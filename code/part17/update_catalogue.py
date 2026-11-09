import argparse, sys
import opslib as O

def main(argv=None):
    ap = argparse.ArgumentParser(); [ap.add_argument(f"--{k}", required=True) for k in ("incident-id", "failure-mode", "runbook-url", "last-incident")]; a = ap.parse_args(argv)
    O.check_date(a.last_incident); cat = O.load_yaml("catalogue.yaml", []); m = next((c for c in cat if c["id"] == a.failure_mode), None)
    if m is None: m = {"id": a.failure_mode, "count": 0, "incidents": []}; cat.append(m)
    m["count"] += 1; m["incidents"].append(a.incident_id); m["runbook"] = a.runbook_url; m["last_incident"] = a.last_incident
    O.save_yaml("catalogue.yaml", cat); print(f"{a.failure_mode}: {m['count']} incident(s)"); return 0

if __name__ == "__main__": sys.exit(main())
