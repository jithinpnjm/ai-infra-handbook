import argparse, sys
import opslib as O

def main(argv=None):
    ap = argparse.ArgumentParser(); [ap.add_argument(f"--{k}", required=True) for k in ("incident-id", "date", "attendees")]; a = ap.parse_args(argv)
    O.check_date(a.date); O.outbox("post_incident_review", incident=a.incident_id, date=a.date, attendees=a.attendees.split(",")); print(f"review of {a.incident_id} on {a.date}"); return 0

if __name__ == "__main__": sys.exit(main())
