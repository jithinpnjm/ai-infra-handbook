"""Record answers for each active checklist item. Answers come from $OPS_HOME/answers.yaml {ID: yes|no}; a missing answer counts as no."""
import argparse, sys
import opslib as O

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--cluster", required=True); a = ap.parse_args(argv)
    items = [i for i in O.load_yaml("checklist.yaml", []) if i.get("status", "active") == "active"]; ans = O.load_yaml("answers.yaml", {})
    for i in items: print(f"{i['id']:8} {ans.get(i['id'], 'no'):3}  {i['name']}")
    return 0

if __name__ == "__main__": sys.exit(main())
