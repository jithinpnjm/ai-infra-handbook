mig_semantic_lines = [
    "Many small inference or dev jobs, isolation required: MIG; hardware partition of A100 or H100 into up",
    "to seven isolated instances, each with own SMs, memory and bandwidth; Slurm treats each instance as a",
    "GPU with cgroup isolation and task binding; config example Gres=gpu:a100:1,gpu:a100_3g.20gb:2 with",
    "AccountingStorageTRES gres/gpu:a100_3g.20gb; Slurm does not partition the GPU: create instances with",
    "nvidia-smi mig or the GPU Operator MIG manager before slurmd starts; no dynamic MIG partitioning;",
    "static and fragmenting, a 3g.20gb instance cannot be merged; no NVLink or multi-GPU use;",
    "AutoDetect=nvml is the only mode that handles MIG"
]

full_mig = "Many small inference or dev jobs, isolation required: MIG; hardware partition of A100 or H100 into up to seven isolated instances, each with own SMs, memory and bandwidth; Slurm treats each instance as a GPU with cgroup isolation and task binding; config example Gres=gpu:a100:1,gpu:a100_3g.20gb:2 with AccountingStorageTRES gres/gpu:a100_3g.20gb; Slurm does not partition the GPU: create instances with nvidia-smi mig or the GPU Operator MIG manager before slurmd starts; no dynamic MIG partitioning; static and fragmenting, a 3g.20gb instance cannot be merged; no NVLink or multi-GPU use; AutoDetect=nvml is the only mode that handles MIG"

joined = " ".join(mig_semantic_lines)
assert joined == full_mig, f"Mismatch!\nExpected: {full_mig}\nGot:      {joined}"
print("MIG matches perfectly across 7 lines!")
for i, l in enumerate(mig_semantic_lines, 1):
    print(f"  Line {i} ({len(l):2d} chars, width={len(l)*14.88:.1f}px): {l}")
