# code/part19/c04_checkpoint_manager.py
"""Checkpoint manager: atomic publish, checksum manifest, keep-N, resume-latest-valid.

Plain Python, standard library only. A checkpoint is a directory of files.
Writers put files into a staging directory, then commit() writes a manifest
(size and sha256 of every file), flushes it to disk and renames the staging
directory to its final name. A rename inside one directory is atomic on a
POSIX file system, so a reader never sees a half-written checkpoint under the
final name.

Layout under root:
    step_00000100/            committed checkpoint
        MANIFEST.json         written last; its presence marks "complete"
        <payload files>
    step_00000200.tmp/        staging directory (ignored by readers)
"""
import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field

MANIFEST = "MANIFEST.json"
PREFIX = "step_"
TMP_SUFFIX = ".tmp"
CORRUPT_SUFFIX = ".corrupt"


def _sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _fsync_path(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _step_name(step):
    return f"{PREFIX}{step:08d}"


def _parse_step(name):
    if not name.startswith(PREFIX):
        return None
    body = name[len(PREFIX):]
    return int(body) if body.isdigit() else None


@dataclass
class Verdict:
    ok: bool
    step: int
    problems: list = field(default_factory=list)


class CheckpointManager:
    def __init__(self, root, keep=3):
        if keep < 1:
            raise ValueError("keep must be at least 1")
        self.root = root
        self.keep = keep
        os.makedirs(root, exist_ok=True)

    # ---- writing -------------------------------------------------------
    def begin(self, step):
        """Create and return an empty staging directory for this step."""
        tmp = os.path.join(self.root, _step_name(step) + TMP_SUFFIX)
        if os.path.exists(tmp):
            shutil.rmtree(tmp)  # leftover from a crash of the same step
        os.makedirs(tmp)
        return tmp

    def commit(self, step, meta=None):
        """Write the manifest, flush everything, rename into place, prune."""
        tmp = os.path.join(self.root, _step_name(step) + TMP_SUFFIX)
        final = os.path.join(self.root, _step_name(step))
        if not os.path.isdir(tmp):
            raise FileNotFoundError(f"no staging directory for step {step}")
        if os.path.exists(final):
            raise FileExistsError(f"step {step} is already committed")
        files = {}
        for dirpath, _, names in os.walk(tmp):
            for n in sorted(names):
                full = os.path.join(dirpath, n)
                rel = os.path.relpath(full, tmp)
                if rel == MANIFEST:
                    continue
                _fsync_path(full)
                files[rel] = {"size": os.path.getsize(full), "sha256": _sha256(full)}
        manifest = {"step": step, "meta": meta or {}, "files": files}
        mpath = os.path.join(tmp, MANIFEST)
        with open(mpath, "w") as f:
            json.dump(manifest, f, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        _fsync_path(tmp)
        os.rename(tmp, final)
        _fsync_path(self.root)
        self.prune()
        return final

    def save_files(self, step, files, meta=None):
        """Convenience for single-process use: files maps name -> bytes."""
        tmp = self.begin(step)
        for name, data in files.items():
            with open(os.path.join(tmp, name), "wb") as f:
                f.write(data)
        return self.commit(step, meta)

    # ---- reading -------------------------------------------------------
    def committed_steps(self):
        steps = []
        for name in os.listdir(self.root):
            s = _parse_step(name)
            if s is not None and os.path.isdir(os.path.join(self.root, name)):
                steps.append(s)
        return sorted(steps)

    def path_for(self, step):
        return os.path.join(self.root, _step_name(step))

    def verify(self, step, full=True):
        """Check one committed checkpoint. full=False skips the sha256 pass."""
        d = self.path_for(step)
        problems = []
        mpath = os.path.join(d, MANIFEST)
        if not os.path.isfile(mpath):
            return Verdict(False, step, ["manifest missing"])
        try:
            with open(mpath) as f:
                manifest = json.load(f)
        except (OSError, ValueError) as e:
            return Verdict(False, step, [f"manifest unreadable: {e}"])
        if manifest.get("step") != step:
            problems.append("manifest step does not match directory name")
        files = manifest.get("files")
        if not isinstance(files, dict) or not files:
            problems.append("manifest lists no files")
            files = {}
        for rel, info in files.items():
            p = os.path.join(d, rel)
            if not os.path.isfile(p):
                problems.append(f"missing file {rel}")
                continue
            if os.path.getsize(p) != info["size"]:
                problems.append(f"size mismatch {rel}")
                continue
            if full and _sha256(p) != info["sha256"]:
                problems.append(f"checksum mismatch {rel}")
        return Verdict(not problems, step, problems)

    def latest_valid(self, full=True, quarantine=False):
        """Return (step, path, skipped) for the newest checkpoint that verifies.

        skipped lists (step, problems) for newer checkpoints that failed.
        Returns (None, None, skipped) when nothing is usable.
        """
        skipped = []
        for step in reversed(self.committed_steps()):
            v = self.verify(step, full=full)
            if v.ok:
                return step, self.path_for(step), skipped
            skipped.append((step, v.problems))
            if quarantine:
                src = self.path_for(step)
                os.rename(src, src + CORRUPT_SUFFIX)
        return None, None, skipped

    def manifest_meta(self, step):
        with open(os.path.join(self.path_for(step), MANIFEST)) as f:
            return json.load(f).get("meta", {})

    # ---- housekeeping --------------------------------------------------
    def prune(self):
        """Keep the newest self.keep committed checkpoints that verify cheaply.

        A corrupt newest checkpoint must not push the last good one out, so
        pruning counts only checkpoints that pass the size check.
        """
        good = [s for s in self.committed_steps() if self.verify(s, full=False).ok]
        for step in good[:-self.keep]:
            shutil.rmtree(self.path_for(step))
        for name in os.listdir(self.root):
            if name.endswith(TMP_SUFFIX):
                s = _parse_step(name[: -len(TMP_SUFFIX)])
                # stale staging directories older than the newest good step
                if s is not None and good and s < good[-1]:
                    shutil.rmtree(os.path.join(self.root, name))
