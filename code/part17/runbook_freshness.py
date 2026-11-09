"""CI gate: exit 1 if any runbook in $OPS_HOME/runbooks.yaml ([{url, last_reviewed}]) is older than the threshold."""
import argparse, sys
import opslib as O

def main(argv=None, now=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--staleness-threshold-days", type=int, default=90); a = ap.parse_args(argv)
    st = O.stale(O.load_yaml("runbooks.yaml", []), a.staleness_threshold_days, now=now)
    for r in st: print("STALE", r["url"], r["last_reviewed"])
    return 1 if st else 0

if __name__ == "__main__": sys.exit(main())
