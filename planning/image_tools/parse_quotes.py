import re

content = """Decision table need to mechanism to config. 'Training, multi-GPU, performance-sensitive: whole GPUs, never share'. 'Many small inference or dev jobs, isolation required: MIG; hardware partition of A100 or H100 into up to seven isolated instances, each with own SMs, memory and bandwidth; Slurm treats each instance as a GPU with cgroup isolation and task binding; config example Gres=gpu:a100:1,gpu:a100_3g.20gb:2 with AccountingStorageTRES gres/gpu:a100_3g.20gb; Slurm does not partition the GPU: create instances with nvidia-smi mig or the GPU Operator MIG manager before slurmd starts; no dynamic MIG partitioning; static and fragmenting, a 3g.20gb instance cannot be merged; no NVLink or multi-GPU use; AutoDetect=nvml is the only mode that handles MIG'. 'Many cooperating small processes, throughput, trusted users: MPS; gres/mps count, Gres=gpu:2,mps:200 means 100 per GPU'. 'Maximum density, trusted workloads, simple: sharding; gres/shard, Gres=gpu:2,shard:64 gives 32 shards per GPU; by default it does not fence the processes or constrain device memory'. 'Fractional GPUs for notebooks and serving across a platform: consider Kubernetes (time-slicing, MIG, DRA)'. Tip 'keep MIG partitions and whole-GPU partitions separate; check with a one-GPU test in each and compare nvidia-smi -L; MIG layout must be recreated before slurmd after reboot'."""

quotes = re.findall(r"'([^']+)'", content)
print(f"Total quotes: {len(quotes)}")
for i, q in enumerate(quotes, 1):
    print(f"[{i}] {q}\n")
