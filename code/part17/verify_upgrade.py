"""Check the SLO over the post-upgrade window from a metrics file ($OPS_HOME/slo.json: {"availability":0.9995,"p99_ms":820}) against targets."""
import argparse, json, sys
import opslib as O

TARGETS = {"availability": (">=", 0.999), "p99_ms": ("<=", 1000)}

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--change", required=True); ap.add_argument("--slo-window", default="24h"); a = ap.parse_args(argv)
    O.parse_duration(a.slo_window); m = json.loads((O.home() / "slo.json").read_text()); bad = []
    for k, (op, t) in TARGETS.items():
        ok = m[k] >= t if op == ">=" else m[k] <= t
        if not ok: bad.append(f"{k}={m[k]} violates {op} {t}")
    print("UPGRADE VERIFIED" if not bad else "UPGRADE FAILED SLO: " + "; ".join(bad) + " -> roll back"); return 1 if bad else 0

if __name__ == "__main__": sys.exit(main())
