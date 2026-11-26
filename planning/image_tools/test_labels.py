import math

labels = [
    "GPUs sit idle in the timeline: seven questions, each answered by a measurement",
    "idle gap (bubble): time between kernels or collectives",
    "Is the data loader the bottleneck? Empty queue, busy workers, a busy iostat, a slow network filesystem",
    "Is the CPU the limiter? Single-thread Python launch overhead, torch ops launching tiny kernels",
    "fix: CUDA graphs or compile",
    "Is host memory pinned, is the PCIe link at x16, is the NUMA placement right?",
    "Is communication exposed, meaning not overlapped with compute?",
    "Is a straggler rank late: thermal throttle, bad link, noisy neighbour?",
    "Is the checkpoint blocking the step?",
    "Is GPU-Util high while SM activity is low? Many small kernels",
    "Outcome metrics to read first",
    "throughput (tokens/s or samples/s per GPU and aggregate)",
    "step time breakdown: data wait, H2D, forward, backward, exposed communication, optimizer, checkpoint",
    "MFU",
    "scaling efficiency = throughput(N) / (N x throughput(1))",
    "goodput = GPU-hours of useful work / GPU-hours paid, excluding restarts, failures, checkpoint stalls, stragglers and idle waiting",
    "cost: USD per million tokens or per training run",
    "Answer each question with a measurement rather than an opinion"
]

for i, l in enumerate(labels):
    print(f"{i+1:2d}. len={len(l):3d}: {l}")
