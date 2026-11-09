"""List commitments (from $OPS_HOME/commitments.yaml [{name, level, expires: YYYY-MM-DD}]) by expiry date."""
import argparse, sys
import opslib as O

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--cluster", required=True); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    rows = sorted(O.load_yaml("commitments.yaml", []), key=lambda r: str(r["expires"]))
    open(a.output, "w").write(f"# Renewals for {a.cluster}\n\n| expires | commitment | level |\n|---|---|---|\n" + "".join(f"| {r['expires']} | {r['name']} | {r['level']} |\n" for r in rows)); print(f"{len(rows)} commitments"); return 0

if __name__ == "__main__": sys.exit(main())
