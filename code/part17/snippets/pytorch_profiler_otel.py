"""Name the exported profile after the current trace id, so the profile can be found from a trace (see correlate_profile.py)."""
import os
import torch
from torch.profiler import profile, ProfilerActivity, record_function
from opentelemetry import trace

def export(prof):
    tid = format(trace.get_current_span().get_span_context().trace_id, "032x")
    os.makedirs("./profiles", exist_ok=True)
    prof.export_chrome_trace(f"./profiles/trace-{tid}.json")

model = torch.nn.Linear(64, 64)
with profile(activities=[ProfilerActivity.CPU], on_trace_ready=export) as prof:
    for step in range(5):
        with record_function(f"step_{step}"):
            model(torch.randn(32, 64)).sum().backward()
        prof.step()
