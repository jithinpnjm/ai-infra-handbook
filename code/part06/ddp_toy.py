"""Tiny DDP job driven by Slurm variables: all-reduce check, one DDP step, rank-0 checkpoint, resume.
Backend gloo on CPU so it runs anywhere; on a GPU cluster use nccl and device_ids=[local_rank]."""
import os
import sys

import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

from slurm_dist_init import dist_env

os.environ.update(dist_env())
rank, world = int(os.environ["RANK"]), int(os.environ["WORLD_SIZE"])
backend = os.environ.get("BACKEND", "gloo")
dist.init_process_group(backend=backend, init_method="env://")

t = torch.tensor([float(rank + 1)])
dist.all_reduce(t)                                    # sum over ranks
assert t.item() == world * (world + 1) / 2, t

torch.manual_seed(0)                                  # identical initial weights on every rank
model = DDP(torch.nn.Linear(4, 1))
opt = torch.optim.SGD(model.parameters(), lr=0.1)
ckpt = os.environ.get("CKPT", "/tmp/ddp_toy.pt")
start = 0
if os.path.exists(ckpt):                              # resume path
    state = torch.load(ckpt, map_location="cpu")
    model.module.load_state_dict(state["model"]); start = state["step"]
x = torch.full((2, 4), float(rank + 1))               # different data per rank
loss = model(x).pow(2).mean()
loss.backward()                                       # gradients are averaged across ranks here
opt.step()
w = model.module.weight.detach().clone().flatten()
gathered = [torch.zeros_like(w) for _ in range(world)]
dist.all_gather(gathered, w)
same = all(torch.equal(g, gathered[0]) for g in gathered)
if rank == 0:
    torch.save({"model": model.module.state_dict(), "step": start + 1}, ckpt)
dist.barrier()
print(f"rank {rank}/{world} local={os.environ['LOCAL_RANK']} master={os.environ['MASTER_ADDR']}:{os.environ['MASTER_PORT']} "
      f"allreduce_ok weights_identical={same} start_step={start}", flush=True)
dist.destroy_process_group()
sys.exit(0)
