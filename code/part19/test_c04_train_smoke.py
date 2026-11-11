"""CPU smoke test for c04_train.py: 2-process gloo FSDP2 with DCP checkpoints.

Skipped when torch (and numpy, which broadcast_object_list needs) is not installed.
Needs no GPU. It proves the checkpoint and resume logic, not NCCL or GPU behaviour.
"""
import os
import signal
import subprocess
import sys
import time

import pytest

pytest.importorskip("torch")
pytest.importorskip("numpy")

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "c04_train.py")
sys.path.insert(0, HERE)
from c04_checkpoint_manager import CheckpointManager  # noqa: E402


def torchrun(nproc, *args, restarts=6, timeout=200):
    # Extra restarts absorb an occasional gloo startup race seen in the container: one worker
    # connects before its peer listens and the connection is refused. Not root-caused.
    cmd = [sys.executable, "-m", "torch.distributed.run", f"--nproc-per-node={nproc}",
           f"--max-restarts={restarts}", TRAIN, *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          env=dict(os.environ, C04_BACKEND="gloo"))


def test_sync_run_commits_verified_checkpoints(tmp_path):
    ck = str(tmp_path / "ck")
    p = torchrun(2, "--ckpt-dir", ck, "--steps", "8", "--ckpt-every", "4")
    assert p.returncode == 0, p.stderr[-2000:]
    m = CheckpointManager(ck)
    assert m.committed_steps() == [4, 8]
    assert m.latest_valid()[0] == 8
    assert m.manifest_meta(8)["world_size"] == 2


def test_async_checkpoint_run(tmp_path):
    ck = str(tmp_path / "ck")
    p = torchrun(2, "--ckpt-dir", ck, "--steps", "8", "--ckpt-every", "4", "--async-ckpt")
    assert p.returncode == 0, p.stderr[-2000:]
    assert CheckpointManager(ck).latest_valid()[0] == 8


def test_injected_failure_restarts_and_resumes_from_checkpoint(tmp_path):
    ck = str(tmp_path / "ck")
    p = torchrun(2, "--ckpt-dir", ck, "--steps", "12", "--ckpt-every", "4", "--fail-at-step", "6")
    assert p.returncode == 0, p.stderr[-2000:]
    assert "resumed from step 4" in p.stdout
    assert CheckpointManager(ck).latest_valid()[0] == 12


def test_corrupt_newest_checkpoint_is_skipped_and_quarantined(tmp_path):
    ck = str(tmp_path / "ck")
    assert torchrun(2, "--ckpt-dir", ck, "--steps", "8", "--ckpt-every", "4").returncode == 0
    shard = os.path.join(ck, "step_00000008", "__1_0.distcp")
    data = bytearray(open(shard, "rb").read())
    data[100] ^= 0xFF
    open(shard, "wb").write(bytes(data))
    p = torchrun(2, "--ckpt-dir", ck, "--steps", "12", "--ckpt-every", "4")
    assert p.returncode == 0, p.stderr[-2000:]
    assert "skipped step 8" in p.stdout and "resumed from step 4" in p.stdout
    assert os.path.isdir(os.path.join(ck, "step_00000008.corrupt"))


def test_checkpoint_from_two_ranks_resumes_on_one_rank(tmp_path):
    ck = str(tmp_path / "ck")
    assert torchrun(2, "--ckpt-dir", ck, "--steps", "8", "--ckpt-every", "4").returncode == 0
    p = torchrun(1, "--ckpt-dir", ck, "--steps", "12", "--ckpt-every", "4")
    assert p.returncode == 0, p.stderr[-2000:]
    assert "resumed from step 8" in p.stdout


def test_sigterm_checkpoints_before_exit(tmp_path):
    ck = str(tmp_path / "ck")
    cmd = [sys.executable, "-m", "torch.distributed.run", "--nproc-per-node=2", TRAIN,
           "--ckpt-dir", ck, "--steps", "400", "--ckpt-every", "1000", "--step-sleep-s", "0.1"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         env=dict(os.environ, C04_BACKEND="gloo"))
    time.sleep(15)
    p.send_signal(signal.SIGTERM)
    out, _ = p.communicate(timeout=60)
    assert "[signal] checkpointed step" in out
    step = CheckpointManager(ck).latest_valid()[0]
    assert step is not None and step > 0
