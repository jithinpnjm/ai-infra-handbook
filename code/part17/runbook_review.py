import argparse, sys
import opslib as O

def main(argv=None, now=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--staleness-threshold-days", type=int, default=90); a = ap.parse_args(argv)
    rb = O.load_yaml("runbooks.yaml", []); have = {r["failure_mode"] for r in rb if r.get("failure_mode")}
    modes = {m["id"] for m in O.load_yaml("catalogue.yaml", [])}
    print("stale:", [r["url"] for r in O.stale(rb, a.staleness_threshold_days, now=now)]); print("missing runbook for:", sorted(modes - have)); print("runbook without catalogue entry:", sorted(have - modes)); return 0

if __name__ == "__main__": sys.exit(main())
