"""Correlate a vendor advisory feed (JSON file: [{id, component, fixed_in, severity}]) with every node's BOM. --webhook is recorded, not called."""
import argparse, json, sys
from pathlib import Path
import seclib as S

def vkey(v): return tuple(int(x) for x in v.split("."))

def correlate(feed, nodes):
    hits = []
    for n, inv in nodes.items():
        for adv in feed:
            cur = inv.get(adv["component"])
            if cur and vkey(cur) < vkey(adv["fixed_in"]): hits.append({"node": n, "cve": adv["id"], "severity": adv["severity"], "have": cur, "fixed_in": adv["fixed_in"]})
    return hits

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--vendor", required=True); ap.add_argument("--feed", required=True); ap.add_argument("--webhook"); a = ap.parse_args(argv)
    nodes = {p.parent.name: json.loads(p.read_text()) for p in (S.home() / "nodes").glob("*/firmware.json")}
    hits = correlate(json.load(open(a.feed)), nodes)
    for h in hits: print(f"{h['severity']:8} {h['cve']} {h['node']}: {h['have']} < {h['fixed_in']}")
    if a.webhook and hits: S.save_json("webhook_outbox.json", {"url": a.webhook, "payload": hits})
    return 1 if hits else 0

if __name__ == "__main__": sys.exit(main())
