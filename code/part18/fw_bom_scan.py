"""Write the firmware bill of materials for a node from its inventory ($SEC_HOME/nodes/<node>/firmware.json {component: version})."""
import argparse, sys, yaml
import seclib as S

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--node", required=True); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    inv = S.load_json(f"nodes/{a.node}/firmware.json")
    if inv is None: print("unknown node"); return 1
    import os; os.makedirs(os.path.dirname(a.output) or ".", exist_ok=True)
    open(a.output, "w").write(yaml.safe_dump({"node": a.node, "components": [{"name": k, "version": v} for k, v in sorted(inv.items())]}, sort_keys=False)); print(f"{len(inv)} components -> {a.output}"); return 0

if __name__ == "__main__": sys.exit(main())
