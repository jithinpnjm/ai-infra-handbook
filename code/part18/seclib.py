"""Shared helpers for the Part 18 scripts. State under $SEC_HOME (default ./.sec). Nothing contacts a network, a TPM or a vendor feed;
inputs are local files that stand in for them (node inventories, advisory feeds). Chapters say where the real system differs."""
import hashlib, hmac, json, os
from datetime import datetime, timezone
from pathlib import Path

def home():
    p = Path(os.environ.get("SEC_HOME", ".sec")); p.mkdir(parents=True, exist_ok=True); return p

def load_json(name, default=None):
    f = home() / name
    return json.loads(f.read_text()) if f.exists() else default

def save_json(name, obj):
    f = home() / name; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(json.dumps(obj, indent=2, sort_keys=True))

def audit(event, **kw):
    f = home() / "audit.log"; prev = "0" * 64
    if f.exists() and f.read_text().strip(): prev = json.loads(f.read_text().strip().splitlines()[-1])["hash"]
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **kw, "prev": prev}
    rec["hash"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    with f.open("a") as fh: fh.write(json.dumps(rec, sort_keys=True) + "\n")

def verify_audit():
    f = home() / "audit.log"; prev = "0" * 64
    for line in (f.read_text().splitlines() if f.exists() else []):
        r = json.loads(line); h = r.pop("hash")
        if r["prev"] != prev or hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest() != h: return False
        prev = h
    return True

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def extend(pcr: str, measurement: str) -> str:
    """TPM-style extend: new = SHA256(old || measurement)."""
    return sha(bytes.fromhex(pcr) + bytes.fromhex(measurement))

def sign(key: bytes, payload: str) -> str: return hmac.new(key, payload.encode(), "sha256").hexdigest()

def attest_key() -> bytes:
    """Local stand-in for a TPM attestation key. A real AK never leaves the TPM."""
    f = home() / "ak.key"
    if not f.exists(): f.write_bytes(os.urandom(32))
    return f.read_bytes()
