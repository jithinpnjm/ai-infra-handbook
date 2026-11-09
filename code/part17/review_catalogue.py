import argparse, sys
import opslib as O

def main(argv=None, now=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--catalogue"); ap.add_argument("--staleness-threshold-days", type=int, default=90); a = ap.parse_args(argv)
    cat = O.load_yaml("catalogue.yaml", []) if not a.catalogue else __import__("yaml").safe_load(open(a.catalogue))
    stale = O.stale([c for c in cat if c.get("last_incident")], a.staleness_threshold_days, key="last_incident", now=now)
    rep = [c["id"] for c in cat if c.get("count", 0) >= 3]
    print("not seen for a long time (candidates to retire):", [c["id"] for c in stale]); print("repeated (3+ incidents):", rep); return 0

if __name__ == "__main__": sys.exit(main())
