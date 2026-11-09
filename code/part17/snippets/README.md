# Snippets: need GPUs, PyTorch, Prophet, an OTLP exporter or a live service

Syntax-checked only. They have NOT been run here. The test environment has no GPU, no PyTorch,
no Prophet and no collector. `nccl_timeout.py` and `pytorch_profiler*.py` were corrected against
the PyTorch API (the chapter draft used an `NCCL_TIMEOUT` variable that PyTorch ignores).
