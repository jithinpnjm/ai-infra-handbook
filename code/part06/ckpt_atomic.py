#!/usr/bin/env python3
"""Crash-safe checkpoint commit protocol on a POSIX file system.

1. every rank writes its shard into  step-N.tmp/   (fsync each file)
2. each shard has a sha256 recorded in its manifest line
3. rank 0 waits for all shards (here: a barrier is simulated by the caller), writes MANIFEST.json, fsyncs
4. rank 0 renames step-N.tmp -> step-N   (atomic on the same file system) and fsyncs the parent directory
5. rank 0 atomically updates 'latest' (write latest.tmp, rename over latest)
Readers only trust directories named step-N that contain MANIFEST.json and whose shard hashes verify.
Run this file to execute the self-test with simulated crashes at each step.
"""
import hashlib
import json
import os
import shutil
import tempfile


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fsync_dir(d):
    fd = os.open(d, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_shard(root, step, rank, payload: bytes):
    tmp = os.path.join(root, f"step-{step}.tmp")
    os.makedirs(tmp, exist_ok=True)
    p = os.path.join(tmp, f"shard-{rank}.bin")
    with open(p, "wb") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    return p


def commit(root, step, ranks, crash_at=None):
    tmp, final = os.path.join(root, f"step-{step}.tmp"), os.path.join(root, f"step-{step}")
    manifest = {"step": step, "shards": {f"shard-{r}.bin": sha(os.path.join(tmp, f"shard-{r}.bin")) for r in range(ranks)}}
    mp = os.path.join(tmp, "MANIFEST.json")
    with open(mp, "w") as f:
        json.dump(manifest, f)
        f.flush()
        os.fsync(f.fileno())
    if crash_at == "before_rename":
        raise RuntimeError("simulated crash")
    os.rename(tmp, final)
    fsync_dir(root)
    if crash_at == "before_latest":
        raise RuntimeError("simulated crash")
    lt = os.path.join(root, "latest.tmp")
    with open(lt, "w") as f:
        f.write(f"step-{step}")
        f.flush()
        os.fsync(f.fileno())
    os.rename(lt, os.path.join(root, "latest"))
    fsync_dir(root)


def newest_valid(root):
    """What a restarting job should load: newest step-N dir with a manifest whose hashes verify."""
    best = None
    for name in sorted((n for n in os.listdir(root) if n.startswith("step-") and not n.endswith(".tmp")),
                       key=lambda n: int(n.split("-")[1])):
        d = os.path.join(root, name)
        mp = os.path.join(d, "MANIFEST.json")
        if not os.path.exists(mp):
            continue
        m = json.load(open(mp))
        if all(os.path.exists(os.path.join(d, s)) and sha(os.path.join(d, s)) == h for s, h in m["shards"].items()):
            best = name
    return best


if __name__ == "__main__":
    root = tempfile.mkdtemp()
    ranks = 4
    for step, crash in ((100, None), (200, "before_rename"), (300, "before_latest"), (400, None)):
        for r in range(ranks):
            write_shard(root, step, r, os.urandom(1 << 16))
        try:
            commit(root, step, ranks, crash)
            outcome = "committed"
        except RuntimeError:
            outcome = f"CRASH ({crash})"
        latest = open(os.path.join(root, "latest")).read() if os.path.exists(os.path.join(root, "latest")) else None
        print(f"step {step}: {outcome:24s} latest pointer={latest}  newest_valid={newest_valid(root)}")
    # corrupt one shard of step-400 (bit rot / torn write) and show verification catches it
    bad = os.path.join(root, "step-400", "shard-2.bin")
    with open(bad, "r+b") as f:
        f.write(b"\x00\x00\x00\x00")
    print(f"after corrupting step-400/shard-2: newest_valid={newest_valid(root)}")
    shutil.rmtree(root)
