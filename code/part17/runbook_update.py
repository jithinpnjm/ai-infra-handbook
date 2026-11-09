import argparse, datetime, sys
import opslib as O

def main(argv=None):
    ap = argparse.ArgumentParser(); [ap.add_argument(f"--{k}", required=True) for k in ("runbook-url", "incident-id", "new-mitigation")]; a = ap.parse_args(argv)
    rb = O.load_yaml("runbooks.yaml", []); r = next((x for x in rb if x["url"] == a.runbook_url), None)
    if r is None: print("REFUSED: unknown runbook url"); return 1
    r.setdefault("mitigations", []).append({"text": a.new_mitigation, "from_incident": a.incident_id}); r["last_reviewed"] = datetime.date.today().isoformat()
    O.save_yaml("runbooks.yaml", rb); print(f"updated {a.runbook_url} from {a.incident_id}"); return 0

if __name__ == "__main__": sys.exit(main())
