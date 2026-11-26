import xml.etree.ElementTree as ET
import re

labels = [
    "How much can filesystem tuning buy? Look at the share of the request",
    "Measure the time of file operations at the layer you can reach: application metrics, strace -T, perf trace, or VFS and filesystem tracing",
    "Prefer histograms to averages: cache hits dominate averages and hide outliers",
    "A request takes 200 ms",
    "180 ms blocked in file I/O (90%)",
    "20 ms other work",
    "The filesystem is 90% of the time: removing its latency could give up to a 10x speedup",
    "Same request, only 2 ms in file I/O (1%)",
    "2 ms file I/O",
    "other work 198 ms",
    "The filesystem is irrelevant: look elsewhere",
    "If you can measure only one thing, measure how long the application spends in file operations"
]

print("Total expected labels:", len(labels))
