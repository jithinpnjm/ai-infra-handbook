import argparse, sys, json
import opslib as O

def main(argv=None):
    ap = argparse.ArgumentParser(); [ap.add_argument(f"--{k}", required=True) for k in ("date", "time", "scenario", "participants")]; a = ap.parse_args(argv)
    O.check_date(a.date); people = [p for p in a.participants.split(",") if p]
    if not people: print("REFUSED: no participants"); return 1
    O.outbox("game_day", date=a.date, time=a.time, scenario=a.scenario, participants=people); print(f"scheduled {a.scenario} on {a.date} {a.time} for {', '.join(people)}"); return 0

if __name__ == "__main__": sys.exit(main())
