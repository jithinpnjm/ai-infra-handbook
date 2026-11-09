import argparse, sys
import seclib as S

REQUIRED_ROLES = ("platform", "security")

def main(argv=None):
    ap = argparse.ArgumentParser(); [ap.add_argument(f"--{k}", required=True) for k in ("date", "time", "scope", "participants")]; a = ap.parse_args(argv)
    from datetime import datetime; datetime.strptime(a.date, "%Y-%m-%d"); ps = a.participants.split(",")
    miss = [r for r in REQUIRED_ROLES if not any(r in p for p in ps)]
    if miss: print("REFUSED: threat-model workshop needs", ", ".join(miss), "represented"); return 1
    S.audit("workshop_scheduled", date=a.date, scope=a.scope, participants=ps); print(f"scheduled {a.scope} workshop {a.date} {a.time}"); return 0

if __name__ == "__main__": sys.exit(main())
