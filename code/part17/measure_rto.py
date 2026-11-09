import argparse, sys
import opslib as O

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--incident-start", required=True); ap.add_argument("--incident-end", required=True); ap.add_argument("--target", default="1h"); a = ap.parse_args(argv)
    r = O.parse_ts(a.incident_end) - O.parse_ts(a.incident_start)
    if r.total_seconds() < 0: print("REFUSED: end before start"); return 2
    ok = r <= O.parse_duration(a.target); print(f"RTO is {O.fmt_td(r)}; " + ("within" if ok else "OUTSIDE") + f" the {a.target} target"); return 0 if ok else 1

if __name__ == "__main__": sys.exit(main())
