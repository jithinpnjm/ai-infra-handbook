#!/usr/bin/env python3
import sys

labels = [
    "Sizing the tail sampler and what happens at 8,000 traces per second",
    "traces held = new traces per second x decision_wait",
    "Design point",
    "5,000 new traces per second x 30 s = 150,000 traces held",
    "num_traces set to 200,000 gives headroom",
    "with 20 spans of 1 KB each (assumptions, not measurements) = 3 GB of buffered span data before overhead",
    "After a traffic increase",
    "8,000 per second x 30 s = 240,000 needed, which exceeds num_traces 200,000, so traces are dropped and the viewer shows fragments",
    "raise num_traces and memory together",
    "or reduce decision_wait",
    "add sampler replicas",
    "apply a head sample in tier one to cut the rate",
    "alert on refusals",
    "otelcol_receiver_refused_spans non-zero means the memory limiter is shedding load",
    "if the load balancing tier was scaled up, spans of one trace may be split across samplers while the routing pool changes"
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. len={len(l):3d} : '{l}'")
