"""Sharded checkpoint with torch.distributed.checkpoint (DCP): save with W ranks, load with a different W'.
Run via fake_srun.py (gloo, CPU). Phase is selected by env PHASE=save|load; CKPT dir by CKPT."""
import os
import sys

import torch
import torch.distributed as dist
import torch.distributed.checkpoint as dcp
from torch.distributed.device_mesh import init_device_mesh
from torch.distributed.tensor import Shard, distribute_tensor

from slurm_dist_init import dist_env

os.environ.update(dist_env())
dist.init_process_group("gloo", init_method="env://")
world, rank = dist.get_world_size(), dist.get_rank()
mesh = init_device_mesh("cpu", (world,))
ckpt = os.environ.get("CKPT", "/tmp/dcp_demo")
phase = os.environ.get("PHASE", "save")

full = torch.arange(24, dtype=torch.float32).reshape(8, 3)          # the "model weight"
if phase == "save":
    w = distribute_tensor(full, mesh, [Shard(0)])                    # each rank owns 8/world rows
    dcp.save({"w": w}, checkpoint_id=ckpt)
    local = w.to_local().shape
    print(f"rank {rank}/{world}: saved shard {tuple(local)}", flush=True)
else:
    w = distribute_tensor(torch.zeros_like(full), mesh, [Shard(0)])
    dcp.load({"w": w}, checkpoint_id=ckpt)
    ok = torch.equal(w.full_tensor(), full)
    print(f"rank {rank}/{world}: loaded shard {tuple(w.to_local().shape)} reassembled_equal={ok}", flush=True)
dist.barrier()
dist.destroy_process_group()
