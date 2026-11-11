"""Drives c04_slurm_train.sh with fake srun and scontrol to prove the signal logic.

Not a Slurm test: no scheduler is involved. It proves that SIGUSR1 to the batch shell is
turned into SIGTERM for the step, that the job is requeued once, that the restart cap
stops the loop, and that a normal exit code is passed through.
"""
import os
import signal
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "c04_slurm_train.sh")

FAKE_SRUN = """#!/bin/bash
# stands in for srun torchrun: exits 1 on SIGTERM like torchrun after a signal
trap 'echo step-got-TERM >> "$FAKE_LOG"; kill $SP; exit 1' TERM
if [ -n "${FAKE_SRUN_EXIT:-}" ]; then exit "$FAKE_SRUN_EXIT"; fi
sleep 30 & SP=$!
wait $SP
"""
FAKE_SCONTROL = """#!/bin/bash
if [ "$1" = "show" ]; then echo node-a; echo node-b; exit 0; fi
echo "scontrol $*" >> "$FAKE_LOG"
"""


def setup(tmp_path):
    b = tmp_path / "bin"
    b.mkdir()
    for name, body in (("srun", FAKE_SRUN), ("scontrol", FAKE_SCONTROL)):
        p = b / name
        p.write_text(body)
        p.chmod(0o755)
    env = dict(os.environ, PATH=f"{b}:{os.environ['PATH']}", FAKE_LOG=str(tmp_path / "log"),
               SLURM_JOB_ID="4242", SLURM_NNODES="4", SLURM_JOB_NODELIST="node-[a-b]")
    return env, tmp_path / "log"


def run_with_usr1(env):
    p = subprocess.Popen(["bash", SCRIPT], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(1.5)
    p.send_signal(signal.SIGUSR1)
    out, _ = p.communicate(timeout=20)
    return p.returncode, out


def test_usr1_forwards_term_and_requeues(tmp_path):
    env, log = setup(tmp_path)
    rc, out = run_with_usr1(env)
    assert rc == 0
    text = log.read_text()
    assert "step-got-TERM" in text
    assert "scontrol requeue 4242" in text


def test_restart_cap_stops_requeue_loop(tmp_path):
    env, log = setup(tmp_path)
    env["SLURM_RESTART_COUNT"] = "5"
    rc, out = run_with_usr1(env)
    assert rc == 1  # exit code of the stopped step is passed through
    assert "scontrol requeue" not in log.read_text()
    assert "restart limit reached" in out


def test_normal_failure_is_not_requeued_and_code_is_passed_through(tmp_path):
    env, log = setup(tmp_path)
    env["FAKE_SRUN_EXIT"] = "7"
    p = subprocess.run(["bash", SCRIPT], env=env, capture_output=True, text=True, timeout=20)
    assert p.returncode == 7
    assert not log.exists() or "requeue" not in log.read_text()
