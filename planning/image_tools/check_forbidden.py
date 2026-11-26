#!/usr/bin/env python3
import re

labels = [
    "Where facts about a GPU host come from, and how to read each safely",
    "Source",
    "How to read",
    "Care",
    "nvidia-smi",
    "nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,ecc.errors.uncorrected.volatile.total --format=csv,noheader,nounits: one CSV line per GPU; nvidia-smi -q -x for XML",
    "parse with csv module; treat [N/A] and [Not Supported] as missing; each call initialises NVML and can take a second on a busy host",
    "NVML bindings",
    "pynvml and nvidia-ml-py: nvmlDeviceGetTemperature, nvmlDeviceGetUtilizationRates, nvmlDeviceGetMemoryInfo, nvmlDeviceGetPowerUsage; throttling reasons and XID events",
    "continuous monitoring",
    "DCGM",
    "Python bindings for health checks and diagnostics; dcgmi diag -r 1|2|3 as a subprocess",
    "-",
    "/proc and /sys",
    "/proc/meminfo, /proc/pressure/*, /sys/class/infiniband/*/ports/*/counters/*, /sys/class/net/*/statistics/*",
    "dependency-free; files can vanish between listing and reading",
    "argument list, timeout=, check=False so you handle the return code, capture stderr, never shell=True with uncontrolled input; subprocess.run timeout kills the child but not its descendants: start_new_session=True then os.killpg; in long-running agents call wait() to avoid zombies",
    "wrap each source in a function returning a typed result such as a dataclass, so the CLI, exporter and agent share one collection layer and tests feed canned output",
    "Read in a way that survives odd output, slow tools and vanishing files"
]

forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']

found_forbidden = False
for i, l in enumerate(labels):
    words = re.findall(r'\b[a-zA-Z]+\b', l.lower())
    for f in forbidden:
        if f in words:
            print(f"WARNING: Forbidden word '{f}' in label {i}: {l}")
            found_forbidden = True

if not found_forbidden:
    print("NO forbidden words found in any label! All clean.")
