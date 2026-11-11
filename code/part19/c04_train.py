# code/part19/c04_train.py
"""Capstone training script: FSDP2 + DCP checkpoints + signal-safe exit + step-time log.

Launch (any number of nodes), see c04_slurm_train.sh, c04_pytorchjob.yaml, c04_jobset.yaml:
    torchrun --nnodes=N --nproc-per-node=G --rdzv-backend=c10d --rdzv-endpoint=HOST:PORT \
        c04_train.py --ckpt-dir /shared/ckpt --metrics-dir /shared/metrics

What it does each run:
    1. rank 0 finds the newest checkpoint that verifies (c04_checkpoint_manager) and
       broadcasts its step; every rank loads its shard with torch.distributed.checkpoint.
    2. trains; every --ckpt-every steps writes a sharded checkpoint into a staging
       directory, rank 0 commits it (manifest, fsync, atomic rename, keep-N).
    3. SIGUSR1 or SIGTERM sets a flag. All ranks agree on it with an all-reduce at a step
       boundary, write one last checkpoint and exit 0 (see --exit-code-on-signal).
Per-rank step times go to <metrics-dir>/steps-rank<R>.csv: ts,step,rank,host,data_s,compute_s.
compute_s is the optimizer step on local shards, the one stretch of GPU work per step
that contains no collective (my reasoning, see c04_straggler_detector.py).
"""
import argparse
import os
import signal
import socket
import sys
import time
from datetime import timedelta

import torch
import torch.distributed as dist
import torch.distributed.checkpoint as dcp
import torch.nn as nn
from torch.distributed.checkpoint.state_dict import get_state_dict, set_state_dict
from torch.distributed.checkpoint.stateful import Stateful
from torch.distributed.elastic.multiprocessing.errors import record

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c04_checkpoint_manager import CheckpointManager  # noqa: E402
from c04_fsdp_config import ShardConfig, build_mesh, shard_model  # noqa: E402

STOP = {"signal": 0}


def _on_signal(signum, _frame):
    STOP["signal"] = signum


class AppState(Stateful):
    """Model plus optimizer, saved and loaded through the distributed state-dict helpers."""

    def __init__(self, model, optimizer):
        self.model, self.optimizer = model, optimizer

    def state_dict(self):
        m, o = get_state_dict(self.model, self.optimizer)
        return {"model": m, "optim": o}

    def load_state_dict(self, sd):
        set_state_dict(self.model, self.optimizer, model_state_dict=sd["model"], optim_state_dict=sd["optim"])


def build_model(width, depth):
    blocks = [nn.Sequential(nn.Linear(width, width), nn.ReLU()) for _ in range(depth)]
    return nn.Sequential(*blocks), blocks


def args_parser():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt-dir", required=True)
    p.add_argument("--metrics-dir", default="")
    p.add_argument("--steps", type=int, default=20)
    p.add_argument("--ckpt-every", type=int, default=5)
    p.add_argument("--keep", type=int, default=3)
    p.add_argument("--async-ckpt", action="store_true")
    p.add_argument("--strategy", default="full", choices=["full", "shard_grad", "hybrid"])
    p.add_argument("--shard-size", type=int, default=0)
    p.add_argument("--width", type=int, default=64)
    p.add_argument("--depth", type=int, default=4)
    p.add_argument("--timeout-s", type=int, default=600, help="collective timeout (PyTorch default for NCCL is 10 min)")
    p.add_argument("--exit-code-on-signal", type=int, default=0)
    p.add_argument("--fail-at-step", type=int, default=-1, help="fault injection: raise once at this step")
    p.add_argument("--step-sleep-s", type=float, default=0.0)
    return p


def _sync(device):
    if device.type == "cuda":
        torch.cuda.synchronize()


@record
def main():
    a = args_parser().parse_args()
    backend = os.environ.get("C04_BACKEND", "nccl" if torch.cuda.is_available() else "gloo")
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    device = torch.device("cuda", local_rank) if backend == "nccl" else torch.device("cpu")
    if device.type == "cuda":
        torch.cuda.set_device(device)
    dist.init_process_group(backend, timeout=timedelta(seconds=a.timeout_s))
    rank, world = dist.get_rank(), dist.get_world_size()
    ckpt_pg = dist.new_group(backend="gloo")  # checkpoint control traffic stays off the NCCL group
    signal.signal(signal.SIGUSR1, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    cfg = ShardConfig(strategy=a.strategy, shard_size=a.shard_size,
                      param_dtype="bfloat16" if device.type == "cuda" else "float32")
    torch.manual_seed(0)
    model, blocks = build_model(a.width, a.depth)
    model.to(device)
    shard_model(model, build_mesh(device.type, world, cfg), cfg, blocks)
    optim = torch.optim.AdamW(model.parameters(), lr=1e-3)
    state = {"app": AppState(model, optim)}
    mgr = CheckpointManager(a.ckpt_dir, keep=a.keep)

    # ---- resume ------------------------------------------------------
    pick = [None]
    if rank == 0:
        step, path, skipped = mgr.latest_valid(quarantine=True)
        for s, problems in skipped:
            print(f"[resume] skipped step {s}: {problems}", flush=True)
        pick[0] = (step, path)
    dist.broadcast_object_list(pick, src=0)
    start = 0
    if pick[0] and pick[0][0] is not None:
        dcp.load(state, checkpoint_id=pick[0][1], process_group=ckpt_pg)
        start = pick[0][0]
        print(f"[rank {rank}] resumed from step {start}, restart_count="
              f"{os.environ.get('TORCHELASTIC_RESTART_COUNT', '0')}", flush=True)
    dist.barrier()

    log = None
    if a.metrics_dir:
        os.makedirs(a.metrics_dir, exist_ok=True)
        log = open(os.path.join(a.metrics_dir, f"steps-rank{rank}.csv"), "a", buffering=1)
    host = socket.gethostname()
    pending = {"future": None, "step": None}

    def finish_pending():
        if pending["future"] is not None:
            pending["future"].result()
            dist.barrier(group=ckpt_pg)
            if rank == 0:
                mgr.commit(pending["step"], meta={"world_size": world})
            dist.barrier(group=ckpt_pg)
            pending["future"] = None

    def save(step):
        finish_pending()
        tmp = os.path.join(a.ckpt_dir, f"step_{step:08d}.tmp")
        if rank == 0:
            mgr.begin(step)
        dist.barrier(group=ckpt_pg)
        if a.async_ckpt:
            pending["future"] = dcp.async_save(state, checkpoint_id=tmp, process_group=ckpt_pg)
            pending["step"] = step
            return
        dcp.save(state, checkpoint_id=tmp, process_group=ckpt_pg)
        dist.barrier(group=ckpt_pg)
        if rank == 0:
            mgr.commit(step, meta={"world_size": world})
        dist.barrier(group=ckpt_pg)

    # ---- train -------------------------------------------------------
    gen = torch.Generator().manual_seed(1234 + rank)
    t_prev = time.time()
    step = start
    while step < a.steps:
        flag = torch.tensor([1 if STOP["signal"] else 0], device=device)
        dist.all_reduce(flag)
        if flag.item() > 0:
            save(step)
            finish_pending()
            if rank == 0:
                print(f"[signal] checkpointed step {step}, exiting", flush=True)
            dist.destroy_process_group()
            sys.exit(a.exit_code_on_signal)
        if a.fail_at_step == step and os.environ.get("TORCHELASTIC_RESTART_COUNT", "0") == "0":
            raise RuntimeError(f"injected failure at step {step}")
        x = torch.randn(8, a.width, generator=gen).to(device)
        t_data = time.time()
        loss = model(x).pow(2).mean()
        loss.backward()
        _sync(device)
        t_c0 = time.time()
        optim.step()
        optim.zero_grad(set_to_none=True)
        _sync(device)
        t_c1 = time.time()
        step += 1
        if a.step_sleep_s:
            time.sleep(a.step_sleep_s)
        if log:
            log.write(f"{t_c1:.3f},{step},{rank},{host},{t_data - t_prev:.5f},{t_c1 - t_c0:.5f}\n")
        if step % a.ckpt_every == 0:
            save(step)
        t_prev = time.time()
    finish_pending()
    if rank == 0:
        print(f"[done] step {step}", flush=True)
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
