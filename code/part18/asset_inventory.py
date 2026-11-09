"""Write an asset inventory for a platform from $SEC_HOME/platform.json {assets: [{name, kind, data_class, owner}]}; refuses assets without an owner."""
import argparse, sys, yaml
import seclib as S

KINDS = {"model", "dataset", "credential", "node", "service", "pipeline"}

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--platform", required=True); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    assets = S.load_json("platform.json", {"assets": []})["assets"]; bad = [x["name"] for x in assets if not x.get("owner") or x.get("kind") not in KINDS]
    if bad: print("REFUSED: missing owner or unknown kind for:", ", ".join(bad)); return 1
    open(a.output, "w").write(yaml.safe_dump({"platform": a.platform, "assets": assets}, sort_keys=False)); print(f"{len(assets)} assets"); return 0

if __name__ == "__main__": sys.exit(main())
