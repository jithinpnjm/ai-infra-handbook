import argparse, sys
import seclib as S

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--node", required=True); ap.add_argument("--previous-version", required=True); ap.add_argument("--component", default="gpu_driver_fw"); a = ap.parse_args(argv)
    inv = S.load_json(f"nodes/{a.node}/firmware.json"); hist = S.load_json(f"nodes/{a.node}/history.json", [])
    if inv is None: print("unknown node"); return 1
    if not any(h["component"] == a.component and h["from"] == a.previous_version for h in hist): print("REFUSED: that version was never installed on this node"); return 1
    inv[a.component] = a.previous_version; S.save_json(f"nodes/{a.node}/firmware.json", inv); S.audit("fw_rollback", node=a.node, component=a.component, version=a.previous_version)
    print(f"{a.node}: rolled back {a.component} to {a.previous_version}"); return 0

if __name__ == "__main__": sys.exit(main())
