"""PyTorch profiler with a schedule. Runs on CPU too (CUDA activity is skipped when no GPU is present)."""
import torch
from torch.profiler import profile, ProfilerActivity, record_function

acts = [ProfilerActivity.CPU] + ([ProfilerActivity.CUDA] if torch.cuda.is_available() else [])
model = torch.nn.Linear(64, 64)

with profile(
    activities=acts,
    schedule=torch.profiler.schedule(wait=1, warmup=1, active=3, repeat=1),
    on_trace_ready=torch.profiler.tensorboard_trace_handler("./profiles"),
    record_shapes=True,
    profile_memory=True,
    with_stack=True,
) as prof:
    for step in range(5):
        with record_function(f"step_{step}"):
            model(torch.randn(32, 64)).sum().backward()
        prof.step()
