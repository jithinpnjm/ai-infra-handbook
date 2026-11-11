#!/usr/bin/env python3
"""Reproducibility checklist runner for research runs (chapter 19.13). Standard library only.

A run manifest is a JSON file written when a run starts. `check` returns one result per rule.
A run is reproducible-in-principle when every `required` rule passes. Warnings never fail a run.
Nothing here proves bit-identical results. It proves that the inputs needed to try are recorded.

  python3 c13_repro_checklist.py MANIFEST.json     exit 0 if all required rules pass, 1 otherwise
  python3 c13_repro_checklist.py --capture DIR     print a manifest skeleton from a git checkout
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass

SHA40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
# MLflow's own tag key for the source commit (mlflow/utils/mlflow_tags.py, v3.18.0).
MLFLOW_GIT_COMMIT_TAG = "mlflow.source.git.commit"


@dataclass
class Result:
    rule: str
    ok: bool
    required: bool
    detail: str


def _get(m, dotted, default=None):
    cur = m
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def check(m: dict) -> list[Result]:
    out: list[Result] = []

    def rule(name, ok, detail, required=True):
        out.append(Result(name, bool(ok), required, detail))

    commit = _get(m, "code.git_commit", "")
    rule("code commit recorded", isinstance(commit, str) and SHA40.match(commit), f"git_commit={commit!r}")
    rule("working tree clean", _get(m, "code.git_dirty") is False, f"git_dirty={_get(m, 'code.git_dirty')!r}")
    image = _get(m, "environment.image", "")
    rule("image pinned by digest", isinstance(image, str) and DIGEST.search(image), f"image={image!r}")
    lock = _get(m, "environment.lockfile_sha256", "")
    rule("lockfile hash recorded", isinstance(lock, str) and SHA256.match(lock), f"lockfile_sha256={lock!r}")
    ds = _get(m, "data.datasets", None)
    ok = isinstance(ds, list) and len(ds) > 0 and all(
        isinstance(d, dict) and d.get("name") and d.get("version") and SHA256.match(str(d.get("content_sha256", ""))) for d in ds)
    rule("every dataset pinned (name, version, content hash)", ok, f"datasets={ds!r}")
    seed = _get(m, "randomness.seed", None)
    rule("seed recorded", isinstance(seed, int) and not isinstance(seed, bool), f"seed={seed!r}")
    rule("command recorded", bool(_get(m, "run.command")), f"command={_get(m, 'run.command')!r}")
    rule("tracking run id recorded", bool(_get(m, "run.mlflow_run_id")), f"mlflow_run_id={_get(m, 'run.mlflow_run_id')!r}")
    rule("hardware recorded (gpu model, driver)", bool(_get(m, "hardware.gpu_model")) and bool(_get(m, "hardware.driver")),
         f"hardware={_get(m, 'hardware')!r}")
    rule("determinism setting stated", isinstance(_get(m, "randomness.deterministic_algorithms"), bool),
         f"deterministic_algorithms={_get(m, 'randomness.deterministic_algorithms')!r}", required=False)
    rule("image is not tagged latest", "latest" not in str(image).split("@")[0].split(":")[-1:], f"image={image!r}", required=False)
    rule("config file stored as artifact", bool(_get(m, "run.config_artifact")), f"config_artifact={_get(m, 'run.config_artifact')!r}", required=False)
    return out


def passed(results: list[Result]) -> bool:
    return all(r.ok for r in results if r.required)


def to_mlflow_tags(m: dict) -> dict[str, str]:
    """Tags to set on the MLflow run. Only the git commit key is an MLflow system tag. The rest are my names."""
    tags = {}
    if _get(m, "code.git_commit"):
        tags[MLFLOW_GIT_COMMIT_TAG] = m["code"]["git_commit"]
    if _get(m, "environment.image"):
        tags["research.image"] = m["environment"]["image"]
    for d in _get(m, "data.datasets", []) or []:
        tags[f"research.dataset.{d['name']}"] = f"{d['version']}:{d['content_sha256']}"
    return tags


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def capture(repo: str, lockfile: str | None = None) -> dict:
    """Skeleton manifest from a git checkout. Fields that need the job (image digest, datasets) stay empty."""
    def git(*args):
        return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout.strip()
    commit = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--porcelain"))
    m = {"code": {"git_commit": commit, "git_dirty": dirty},
         "environment": {"image": "", "lockfile_sha256": ""},
         "data": {"datasets": []},
         "randomness": {"seed": None, "deterministic_algorithms": None},
         "run": {"command": "", "mlflow_run_id": "", "config_artifact": ""},
         "hardware": {"gpu_model": "", "driver": ""}}
    if lockfile:
        m["environment"]["lockfile_sha256"] = file_sha256(pathlib.Path(repo) / lockfile)
    return m


def main(argv):
    if len(argv) == 3 and argv[1] == "--capture":
        print(json.dumps(capture(argv[2]), indent=2))
        return 0
    if len(argv) != 2:
        print(__doc__)
        return 2
    results = check(json.loads(pathlib.Path(argv[1]).read_text()))
    for r in results:
        print(f"{'PASS' if r.ok else ('FAIL' if r.required else 'WARN')}  {r.rule}")
    ok = passed(results)
    print("RESULT:", "reproducible in principle" if ok else "NOT reproducible: fix the FAIL lines")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
