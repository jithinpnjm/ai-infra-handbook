"""Group the inventory's assets into four attack surfaces and write a markdown map."""
import argparse, sys, yaml

SURFACES = {"hardware and firmware": {"node"}, "software supply chain": {"pipeline"}, "data and models": {"model", "dataset"}, "access and identity": {"credential", "service"}}

def surface_of(kind): return next(s for s, k in SURFACES.items() if kind in k)

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--platform", required=True); ap.add_argument("--inventory", default="asset_inventory.yaml"); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    inv = yaml.safe_load(open(a.inventory)); by = {s: [] for s in SURFACES}
    for x in inv["assets"]: by[surface_of(x["kind"])].append(x["name"])
    open(a.output, "w").write(f"# Attack surface: {a.platform}\n\n" + "".join(f"## {s}\n" + "".join(f"- {n}\n" for n in names) + ("- (none recorded)\n" if not names else "") + "\n" for s, names in by.items())); print({s: len(v) for s, v in by.items()}); return 0

if __name__ == "__main__": sys.exit(main())
