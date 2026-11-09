import argparse, sys
import opslib as O

def main(argv=None):
    ap = argparse.ArgumentParser(); [ap.add_argument(f"--{k}", required=True) for k in ("change", "reason", "impact")]; a = ap.parse_args(argv)
    O.outbox("rollback_announcement", change=a.change, reason=a.reason, impact=a.impact); print(f"rollback announced: {a.change} ({a.reason})"); return 0

if __name__ == "__main__": sys.exit(main())
