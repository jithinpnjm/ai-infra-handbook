# code/part19/c04_fsdp_config.py
"""FSDP2 (fully_shard) configuration for the capstone training job.

Sharding choices expressed with the FSDP2 API (PyTorch 2.15 documentation):
    "full"        1D mesh, reshard_after_forward=True   -> like FSDP1 FULL_SHARD
    "shard_grad"  1D mesh, reshard_after_forward=False  -> like FSDP1 SHARD_GRAD_OP
    "hybrid"      2D mesh (replicate, shard)            -> like FSDP1 HYBRID_SHARD
The mapping from FSDP1 names is my reading of the two docs pages, not a statement
from the PyTorch documentation.
"""
from dataclasses import dataclass

import torch
from torch.distributed.device_mesh import init_device_mesh
from torch.distributed.fsdp import MixedPrecisionPolicy, fully_shard


@dataclass
class ShardConfig:
    strategy: str = "full"          # full | shard_grad | hybrid
    shard_size: int = 0             # hybrid only: ranks per shard group (usually GPUs per node)
    param_dtype: str = "bfloat16"   # "float32" disables mixed precision
    reduce_dtype: str = "float32"


def build_mesh(device_type, world_size, cfg):
    if cfg.strategy == "hybrid":
        if cfg.shard_size < 2 or world_size % cfg.shard_size:
            raise ValueError("hybrid needs shard_size >= 2 that divides world_size")
        return init_device_mesh(
            device_type, (world_size // cfg.shard_size, cfg.shard_size),
            mesh_dim_names=("replicate", "shard"))
    return init_device_mesh(device_type, (world_size,), mesh_dim_names=("shard",))


def mixed_precision(cfg):
    if cfg.param_dtype == "float32":
        return MixedPrecisionPolicy()
    return MixedPrecisionPolicy(
        param_dtype=getattr(torch, cfg.param_dtype),
        reduce_dtype=getattr(torch, cfg.reduce_dtype))


def shard_model(model, mesh, cfg, blocks):
    """Apply fully_shard bottom-up: every block first, then the root.

    blocks is the list of submodules that each get their own all-gather group.
    """
    kwargs = {"mesh": mesh, "mp_policy": mixed_precision(cfg)}
    if cfg.strategy == "shard_grad":
        kwargs["reshard_after_forward"] = False
    for block in blocks:
        fully_shard(block, **kwargs)
    fully_shard(model, **kwargs)
    return model
