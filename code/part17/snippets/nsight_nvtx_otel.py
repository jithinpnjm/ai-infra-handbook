import torch
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("training-step"):
    span = trace.get_current_span()
    trace_id = format(span.get_span_context().trace_id, "032x")
    torch.cuda.nvtx.range_push(f"step-{trace_id}")
    # ... training step ...
    torch.cuda.nvtx.range_pop()
