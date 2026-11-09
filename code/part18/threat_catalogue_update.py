import argparse, re, sys
import seclib as S

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--threat-id", required=True); ap.add_argument("--new-mitigation", required=True); ap.add_argument("--catalogue", default="threat_catalogue.md"); a = ap.parse_args(argv)
    lines = open(a.catalogue).read().splitlines(); hit = False
    for i, l in enumerate(lines):
        if l.startswith(f"| {a.threat_id} |"):
            cells = l.strip("|").split("|"); cells[-1] = f" {a.new_mitigation} "; lines[i] = "|" + "|".join(cells) + "|"; hit = True
    if not hit: print("REFUSED: unknown threat id"); return 1
    open(a.catalogue, "w").write("\n".join(lines) + "\n"); S.audit("threat_mitigation_updated", threat=a.threat_id); print(f"{a.threat_id} updated"); return 0

if __name__ == "__main__": sys.exit(main())
