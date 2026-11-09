"""Wrap a collective in a span, with NCCL debug logging on. Requires GPUs and torchrun: syntax-checked only."""
import os
os.environ["NCCL_DEBUG"] = "INFO"
os.environ["NCCL_DEBUG_SUBSYS"] = "INIT,COLL"      # ALL is extremely verbose; INIT and COLL are enough for most hangs

import torch
import torch.distributed as dist
from opentelemetry import trace

dist.init_process_group(backend="nccl")
tracer = trace.get_tracer(__name__)
tensor = torch.ones(1024, device="cuda")
with tracer.start_as_current_span("all-reduce"):
    dist.all_reduce(tensor)
