"""Check that no store still holds the customer."""
import argparse, sys
import mlplat_local as P

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--customer-id", required=True); a = ap.parse_args(argv)
    left = [s for s in ("warehouse.json", "features.json", "consent.json") if a.customer_id in P.load(s, {})]
    print("ERASURE INCOMPLETE: " + ", ".join(left) if left else "ERASURE VERIFIED"); return 1 if left else 0

if __name__ == "__main__": sys.exit(main())
