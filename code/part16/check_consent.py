"""Show a customer's consent record. Store: $MLPLAT_HOME/consent.json {customer_id: {fields: [...], granted_at}}"""
import argparse, sys
import mlplat_local as P

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--customer-id", required=True); a = ap.parse_args(argv)
    rec = P.load("consent.json", {}).get(a.customer_id)
    if not rec: print("NO CONSENT RECORD"); return 1
    print("consented fields:", ", ".join(rec["fields"])); return 0

if __name__ == "__main__": sys.exit(main())
