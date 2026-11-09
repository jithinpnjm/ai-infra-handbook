import argparse, sys
import seclib as S

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--node", required=True); ap.add_argument("--expected-version", required=True); ap.add_argument("--component", default="gpu_driver_fw"); a = ap.parse_args(argv)
    inv = S.load_json(f"nodes/{a.node}/firmware.json", {}); got = inv.get(a.component)
    ok = got == a.expected_version; print(f"{a.node} {a.component}: " + ("verified " + got if ok else f"EXPECTED {a.expected_version} BUT FOUND {got}")); return 0 if ok else 1

if __name__ == "__main__": sys.exit(main())
