import argparse, sys
import opslib as O

def rpo(last_backup, disaster):
    return O.parse_ts(disaster) - O.parse_ts(last_backup)

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--last-backup", required=True); ap.add_argument("--disaster-time", required=True); ap.add_argument("--target", default="1m"); a = ap.parse_args(argv)
    r = rpo(a.last_backup, a.disaster_time)
    if r.total_seconds() < 0: print("REFUSED: backup is after the disaster"); return 2
    ok = r <= O.parse_duration(a.target); print(f"RPO is {O.fmt_td(r)}; " + ("within" if ok else "OUTSIDE") + f" the {a.target} target"); return 0 if ok else 1

if __name__ == "__main__": sys.exit(main())
