import argparse, re, sys
import opslib as O

TEMPLATE = """# Post-mortem {iid}

Date of incident: {date}
Status: DRAFT (blameless; fill every section before the review)

## Summary
## Impact
## Timeline (UTC)
## Root cause
## What went well
## What went badly
## Action items (owner, due date)
"""

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--incident-id", required=True); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    m = re.fullmatch(r"INC-(\d{4}-\d{2}-\d{2})-\d{3}", a.incident_id)
    if not m: print("REFUSED: incident id must look like INC-2024-03-15-001"); return 1
    open(a.output, "w").write(TEMPLATE.format(iid=a.incident_id, date=m[1])); print(f"wrote {a.output}"); return 0

if __name__ == "__main__": sys.exit(main())
