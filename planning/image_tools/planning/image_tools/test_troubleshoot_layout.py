import re

# Conservatively estimate text width
def text_width(text, font_size, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * factor * font_size

rows = [
    {
        "symptom": ("Invalid generic resource", "(gres) specification"),
        "cause": ("type or name not in", "GresTypes or node Gres"),
        "check": ("scontrol show node, slurmd -G,", "typo in type"),
    },
    {
        "symptom": ("Pending Resources or", "ReqNodeNotAvail"),
        "cause": ("request not satisfiable", "(type, count, memory per GPU,", "sockets with enforce-binding)", "or nodes drained"),
        "check": ("scontrol show job,", "sinfo -o %N %G %t"),
    },
    {
        "symptom": ("Node DRAIN gres/gpu", "count too low (0 < 8)"),
        "cause": ("NVML or driver failed to load,", "GPU missing"),
        "check": ("nvidia-smi, slurmd log,", "slurmd -G, dmesg Xid"),
    },
    {
        "symptom": ("CUDA_VISIBLE_DEVICES", "empty"),
        "cause": ("no File= or device constraint", "config, --gres not requested,", "--gpu-bind=none"),
        "check": ("gres.conf,", "scontrol show job TresPerNode"),
    },
    {
        "symptom": ("Job sees all GPUs",),
        "cause": ("ConstrainDevices=no",),
        "check": ("cgroup.conf",),
    },
    {
        "symptom": ("Two ranks use one GPU",),
        "cause": ("no per-task binding,", "--gpus-per-task missing,", "sharing configured"),
        "check": ("gpu_env_check.py per rank",),
    },
    {
        "symptom": ("Slow host-device copies",),
        "cause": ("CPUs on the wrong NUMA node",),
        "check": ("--gres-flags=enforce-binding,", "Cores=, taskset,", "nvidia-smi topo -m"),
    },
    {
        "symptom": ("NVLink-poor pairs", "allocated"),
        "cause": ("Links missing",),
        "check": ("slurmd -G,", "--gres-flags=enforce-links"),
    },
    {
        "symptom": ("MIG count wrong", "after reboot"),
        "cause": ("layout not recreated", "before slurmd"),
        "check": ("systemd ordering,", "nvidia-smi -L"),
    },
]

col1_w = 480
col2_w = 520
col3_w = 520

print("=== CHECKING HORIZONTAL PADDINGS ===")
for i, r in enumerate(rows, 1):
    print(f"\nRow {i}:")
    for line in r["symptom"]:
        w = text_width(line, 30, is_mono=False)
        pad = (col1_w - w) / 2
        print(f"  Col 1 (30px sans): '{line}' -> {w:.1f}px (remains {col1_w - w:.1f}px, left/right pad {pad:.1f}px)")
        assert col1_w - w >= 32, f"Line '{line}' overflow!"

    for line in r["cause"]:
        w = text_width(line, 24, is_mono=False)
        pad = (col2_w - w) / 2
        print(f"  Col 2 (24px sans): '{line}' -> {w:.1f}px (remains {col2_w - w:.1f}px, left/right pad {pad:.1f}px)")
        assert col2_w - w >= 32, f"Line '{line}' overflow!"

    for line in r["check"]:
        w = text_width(line, 24, is_mono=True)
        pad = (col3_w - w) / 2
        print(f"  Col 3 (24px mono): '{line}' -> {w:.1f}px (remains {col3_w - w:.1f}px, left/right pad {pad:.1f}px)")
        assert col3_w - w >= 32, f"Line '{line}' overflow!"

print("\nALL LINES HAVE AT LEAST 16PX PADDING!")
