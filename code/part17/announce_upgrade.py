"""Write an upgrade announcement. Refuses a change window in the past or without a rollback criterion."""
import argparse, sys
from datetime import date
import opslib as O

def main(argv=None, today=None):
    ap = argparse.ArgumentParser(); [ap.add_argument(f"--{k}", required=True) for k in ("date", "time", "change", "rollback")]; a = ap.parse_args(argv)
    d = O.check_date(a.date)
    if d < (today or date.today()): print("REFUSED: change window is in the past"); return 1
    O.outbox("upgrade_announcement", date=a.date, time=a.time, change=a.change, rollback=a.rollback)
    print(f"announced {a.change} on {a.date} {a.time}; rollback: {a.rollback}"); return 0

if __name__ == "__main__": sys.exit(main())
