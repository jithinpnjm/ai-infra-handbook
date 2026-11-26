import xml.etree.ElementTree as ET
import re

spec_labels = [
    "GPU scheduling symptoms and first checks",
    "symptom",
    "likely cause",
    "check",
    "Invalid generic resource (gres) specification",
    "type or name not in GresTypes or node Gres",
    "scontrol show node, slurmd -G, typo in type",
    "Pending Resources or ReqNodeNotAvail",
    "request not satisfiable (type, count, memory per GPU, sockets with enforce-binding) or nodes drained",
    "scontrol show job, sinfo -o %N %G %t",
    "Node DRAIN gres/gpu count too low (0 < 8)",
    "NVML or driver failed to load, GPU missing",
    "nvidia-smi, slurmd log, slurmd -G, dmesg Xid",
    "CUDA_VISIBLE_DEVICES empty",
    "no File= or device constraint config, --gres not requested, --gpu-bind=none",
    "gres.conf, scontrol show job TresPerNode",
    "Job sees all GPUs",
    "ConstrainDevices=no",
    "cgroup.conf",
    "Two ranks use one GPU",
    "no per-task binding, --gpus-per-task missing, sharing configured",
    "gpu_env_check.py per rank",
    "Slow host-device copies",
    "CPUs on the wrong NUMA node",
    "--gres-flags=enforce-binding, Cores=, taskset, nvidia-smi topo -m",
    "NVLink-poor pairs allocated",
    "Links missing",
    "slurmd -G, --gres-flags=enforce-links",
    "MIG count wrong after reboot",
    "layout not recreated before slurmd",
    "systemd ordering, nvidia-smi -L",
    "bring a recovered test node back with scontrol update NodeName=node[6-7] State=RESUME; drain a node when a GPU reports Xid, ECC or NVLink faults"
]

print("Total expected labels:", len(spec_labels))
for i, l in enumerate(spec_labels, 1):
    print(f"{i:2d}. {l}")
