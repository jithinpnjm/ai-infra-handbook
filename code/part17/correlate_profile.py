"""Link a profile file to a trace id so the profile can be found from the trace view. Index: $OPS_HOME/profile_index.json."""
import argparse, json, re, sys
import opslib as O

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--profile", required=True); ap.add_argument("--trace-id", required=True); a = ap.parse_args(argv)
    if not re.fullmatch(r"[0-9a-f]+", a.trace_id): print("REFUSED: trace id must be hex"); return 1
    f = O.home() / "profile_index.json"; idx = json.loads(f.read_text()) if f.exists() else {}
    idx.setdefault(a.trace_id, []).append(a.profile); f.write_text(json.dumps(idx, indent=1)); print(f"trace {a.trace_id} -> {a.profile}"); return 0

if __name__ == "__main__": sys.exit(main())
