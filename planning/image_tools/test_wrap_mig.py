def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    cur_line = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur_line else 0) <= max_chars:
            cur_line.append(w)
            cur_len += len(w) + (1 if len(cur_line) > 1 else 0)
        else:
            lines.append(" ".join(cur_line))
            cur_line = [w]
            cur_len = len(w)
    if cur_line:
        lines.append(" ".join(cur_line))
    return lines

label_mig = "Many small inference or dev jobs, isolation required: MIG; hardware partition of A100 or H100 into up to seven isolated instances, each with own SMs, memory and bandwidth; Slurm treats each instance as a GPU with cgroup isolation and task binding; config example Gres=gpu:a100:1,gpu:a100_3g.20gb:2 with AccountingStorageTRES gres/gpu:a100_3g.20gb; Slurm does not partition the GPU: create instances with nvidia-smi mig or the GPU Operator MIG manager before slurmd starts; no dynamic MIG partitioning; static and fragmenting, a 3g.20gb instance cannot be merged; no NVLink or multi-GPU use; AutoDetect=nvml is the only mode that handles MIG"

print(f"Total chars: {len(label_mig)}")
lines = wrap_text(label_mig, 95)
print(f"Wrapped into {len(lines)} lines at max 95 chars:")
for i, l in enumerate(lines, 1):
    print(f"  Line {i} ({len(l)} chars): {l}")
