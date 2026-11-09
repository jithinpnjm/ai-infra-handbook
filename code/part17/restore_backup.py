"""Restore a backup directory ($OPS_HOME/backups/<name>/) into $OPS_HOME/restore/<target>/ and report files and elapsed time. Verifies checksums."""
import argparse, hashlib, json, shutil, sys, time
import opslib as O

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def restore(name, target):
    src = O.home() / "backups" / name; dst = O.home() / "restore" / target
    manifest = json.loads((src / "MANIFEST.json").read_text()); t0 = time.time()
    if dst.exists(): shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for fn, h in manifest["files"].items():
        shutil.copy(src / fn, dst / fn)
        if sha(dst / fn) != h: raise ValueError(f"checksum mismatch for {fn}")
    return {"files": len(manifest["files"]), "seconds": time.time() - t0, "taken_at": manifest["taken_at"]}

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--backup", required=True); ap.add_argument("--target", required=True); a = ap.parse_args(argv)
    if a.target == "production": print("REFUSED: restore to staging first"); return 1
    try: r = restore(a.backup, a.target)
    except ValueError as e: print("RESTORE FAILED:", e); return 1
    print(f"restored {r['files']} files in {r['seconds']:.2f}s"); return 0

if __name__ == "__main__": sys.exit(main())
