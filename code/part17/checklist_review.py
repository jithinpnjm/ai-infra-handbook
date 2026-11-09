import argparse, sys
import opslib as O

def main(argv=None, now=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--staleness-threshold-days", type=int, default=90); a = ap.parse_args(argv)
    items = O.load_yaml("checklist.yaml", [])
    st = O.stale([i for i in items if i.get("status", "active") == "active"], a.staleness_threshold_days, now=now)
    print("stale:", [i["id"] for i in st]); print("unimplemented:", [i["id"] for i in items if i.get("status") == "unimplemented"]); print("retired:", [i["id"] for i in items if i.get("status") == "retired"])
    return 1 if st else 0

if __name__ == "__main__": sys.exit(main())
