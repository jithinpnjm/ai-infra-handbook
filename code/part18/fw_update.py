import argparse, sys
import seclib as S

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--node", required=True); ap.add_argument("--version", required=True); ap.add_argument("--component", default="gpu_driver_fw"); a = ap.parse_args(argv)
    inv = S.load_json(f"nodes/{a.node}/firmware.json"); hist = S.load_json(f"nodes/{a.node}/history.json", [])
    if inv is None or a.component not in inv: print("unknown node or component"); return 1
    if inv[a.component] == a.version: print("already at that version"); return 0
    hist.append({"component": a.component, "from": inv[a.component], "to": a.version}); inv[a.component] = a.version
    S.save_json(f"nodes/{a.node}/firmware.json", inv); S.save_json(f"nodes/{a.node}/history.json", hist); S.audit("fw_update", node=a.node, component=a.component, version=a.version)
    print(f"{a.node}: {a.component} -> {a.version} (reboot required)"); return 0

if __name__ == "__main__": sys.exit(main())
