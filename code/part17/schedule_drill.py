import argparse, sys
import opslib as O

def main(argv=None):
    ap = argparse.ArgumentParser(); [ap.add_argument(f"--{k}", required=True) for k in ("date", "time", "scenario")]; a = ap.parse_args(argv)
    O.check_date(a.date); O.outbox("dr_drill", date=a.date, time=a.time, scenario=a.scenario); print(f"scheduled DR drill {a.scenario} on {a.date} {a.time}"); return 0

if __name__ == "__main__": sys.exit(main())
