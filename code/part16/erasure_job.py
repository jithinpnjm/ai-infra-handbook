"""GDPR erasure: remove a customer from the warehouse, feature store and consent store, queue retraining, write the audit log."""
import argparse, sys
import mlplat_local as P

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--customer-id", required=True); ap.add_argument("--reason", required=True); a = ap.parse_args(argv)
    removed = {}
    for store in ("warehouse.json", "features.json", "consent.json"):
        d = P.load(store, {}); removed[store] = d.pop(a.customer_id, None) is not None; P.save(store, d)
    q = P.load("retrain_queue.json", []); q.append({"reason": f"erasure of {a.customer_id}"}); P.save("retrain_queue.json", q)
    P.audit("erasure", customer=a.customer_id, reason=a.reason, removed=removed)   # id kept for the audit trail; no personal fields
    print("erased:", removed); return 0

if __name__ == "__main__": sys.exit(main())
