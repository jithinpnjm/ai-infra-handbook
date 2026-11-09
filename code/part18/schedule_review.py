import argparse, sys
from datetime import datetime
import seclib as S

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--threat-model", required=True); ap.add_argument("--date", required=True); a = ap.parse_args(argv)
    datetime.strptime(a.date, "%Y-%m-%d"); S.audit("threat_model_review_scheduled", model=a.threat_model, date=a.date); print(f"review of {a.threat_model} on {a.date}"); return 0

if __name__ == "__main__": sys.exit(main())
