"""Generate STRIDE threats for every asset. Each threat gets an id, likelihood and impact (1-5) from the data class; output is markdown."""
import argparse, sys, yaml

STRIDE = {"model": ["Tampering", "Information disclosure"], "dataset": ["Information disclosure", "Tampering"], "credential": ["Spoofing", "Elevation of privilege"],
          "node": ["Tampering", "Denial of service"], "service": ["Spoofing", "Denial of service"], "pipeline": ["Tampering", "Elevation of privilege"]}
IMPACT = {"public": 1, "internal": 2, "confidential": 4, "restricted": 5}

def build(assets):
    out = []; n = 0
    for x in assets:
        for cat in STRIDE[x["kind"]]:
            n += 1; out.append({"id": f"T-{n:03d}", "asset": x["name"], "stride": cat, "impact": IMPACT.get(x.get("data_class", "internal"), 2), "likelihood": 3, "mitigation": ""})
    return out

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--scope", required=True); ap.add_argument("--asset-inventory", required=True); ap.add_argument("--attack-surface"); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    ts = build(yaml.safe_load(open(a.asset_inventory))["assets"])
    open(a.output, "w").write(f"# Threat catalogue: {a.scope}\n\n| id | asset | STRIDE | likelihood | impact | mitigation |\n|---|---|---|---|---|---|\n" + "".join(f"| {t['id']} | {t['asset']} | {t['stride']} | {t['likelihood']} | {t['impact']} | {t['mitigation'] or 'TODO'} |\n" for t in ts)); print(f"{len(ts)} threats"); return 0

if __name__ == "__main__": sys.exit(main())
