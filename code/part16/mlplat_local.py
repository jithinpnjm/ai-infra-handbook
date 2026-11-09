"""Tiny local stand-in for the platform services Part 16 talks about.

Everything is plain files under $MLPLAT_HOME (default ./.mlplat): a registry,
an append-only hash-chained audit log, a feature store, a consent store and a
vector index. It lets every script in this directory run and be tested with no
cluster, cloud account or API key. A mock LLM replaces the hosted model.
It does not model MLflow, Feast, Milvus or a real LLM; the chapters say where
the real services differ.
"""
from __future__ import annotations
import hashlib, json, os, re, math, time
from pathlib import Path

def home() -> Path:
    p = Path(os.environ.get("MLPLAT_HOME", ".mlplat")); p.mkdir(parents=True, exist_ok=True); return p

def load(name: str, default):
    f = home() / name
    return json.loads(f.read_text()) if f.exists() else default

def save(name: str, obj) -> None:
    (home() / name).write_text(json.dumps(obj, indent=2, sort_keys=True))

# ---- audit log: each line carries the hash of the previous line -------------
def audit(event: str, **fields) -> str:
    f = home() / "audit.log"
    prev = "0" * 64
    if f.exists() and f.read_text().strip():
        prev = json.loads(f.read_text().strip().splitlines()[-1])["hash"]
    rec = {"ts": round(time.time(), 3), "event": event, **fields, "prev": prev}
    rec["hash"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    with f.open("a") as fh: fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec["hash"]

def verify_audit() -> bool:
    f = home() / "audit.log"; prev = "0" * 64
    for line in (f.read_text().splitlines() if f.exists() else []):
        rec = json.loads(line); h = rec.pop("hash")
        if rec["prev"] != prev or hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest() != h:
            return False
        prev = h
    return True

# ---- registry ---------------------------------------------------------------
def register(name, version, run_id, metrics, stage="none", **extra):
    reg = load("registry.json", {})
    reg.setdefault(name, {})[str(version)] = {"run_id": run_id, "metrics": metrics, "stage": stage, **extra}
    save("registry.json", reg)

def get_version(name, version):
    return load("registry.json", {}).get(name, {}).get(str(version))

def set_stage(name, version, stage):
    reg = load("registry.json", {}); reg[name][str(version)]["stage"] = stage; save("registry.json", reg)

# ---- mock LLM and PII -------------------------------------------------------
KB = {"lifecycle": "The MLOps lifecycle runs from data to training to registry to production serving and monitoring.",
      "failure": "Typical failure modes are data drift, silent pipeline breaks and unreviewed promotion to production.",
      "registry": "The model registry records every version with its run, metrics and stage."}
REFUSE = ("ignore previous instructions", "home address", "social security")
PII = [re.compile(p) for p in (r"[\w.+-]+@[\w-]+\.[\w.]+", r"\b\d{3}-\d{2}-\d{4}\b", r"\b\d{10}\b")]

def contains_pii(text: str) -> bool:
    return any(p.search(text) for p in PII)

class MockLLM:
    """Deterministic: answers from KB by keyword, refuses unsafe asks."""
    def complete(self, prompt: str) -> str:
        low = prompt.lower()
        if any(r in low for r in REFUSE):
            return "I can't help with that request."
        hits = [v for k, v in KB.items() if k in low]
        return " ".join(hits) if hits else "I do not have enough information to answer."

# ---- vector index (bag-of-words cosine; stands in for an embedding model) ----
def embed(text: str) -> dict:
    v: dict = {}
    for w in re.findall(r"[a-z]+", text.lower()): v[w] = v.get(w, 0) + 1
    n = math.sqrt(sum(x * x for x in v.values())) or 1.0
    return {k: x / n for k, x in v.items()}

def cosine(a: dict, b: dict) -> float:
    return sum(x * b.get(k, 0.0) for k, x in a.items())
