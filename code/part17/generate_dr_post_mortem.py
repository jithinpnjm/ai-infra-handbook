import argparse, re, sys

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--drill-id", required=True); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    if not re.fullmatch(r"DR-\d{4}-\d{2}-\d{2}", a.drill_id): print("REFUSED: drill id must look like DR-2024-03-15"); return 1
    open(a.output, "w").write(f"# DR drill report {a.drill_id}\n\n## Scenario\n## Measured RTO and RPO (from measure_rto.py, measure_rpo.py)\n## Gaps found\n## Actions\n"); print(f"wrote {a.output}"); return 0

if __name__ == "__main__": sys.exit(main())
