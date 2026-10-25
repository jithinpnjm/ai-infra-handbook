# Part 10 Code and Self-Checking Labs: The GPU and CUDA

All labs in this directory use Python 3 standard library only and run with `python3 -B code/part10/<lab_file>.py`.

| Chapter | Model file | Lab file | Self-checks | Status |
|---|---|---|---|---|
| 10.1 Why GPUs: CPU versus GPU and throughput design | `why_gpus.py` | `why_gpus_lab.py` | 30 | PASS (30/30) |
| 10.2 The execution model: threads, warps, blocks and SMs | `execution_model.py` | `execution_model_lab.py` | 25 | PASS (25/25) |
| 10.3 The GPU memory hierarchy | `gpu_memory_hierarchy.py` | `gpu_memory_hierarchy_lab.py` | 25 | PASS (25/25) |
| 10.4 Tensor cores and numerical precision | `tensor_cores_precision.py` | `tensor_cores_precision_lab.py` | 25 | PASS (25/25) |
| 10.5 The roofline model and performance modelling | `roofline_model.py` | `roofline_model_lab.py` | 25 | PASS (25/25) |
| 10.6 GPU interconnects: PCIe, NVLink, NVSwitch and NVLink-C2C | `gpu_interconnects.py` | `gpu_interconnects_lab.py` | 25 | PASS (25/25) |
| 10.7 GPU generations and product line | `gpu_generations.py` | `gpu_generations_lab.py` | 25 | PASS (25/25) |
| 10.8 Operating GPU nodes: nvidia-smi, topology, clocks and throttling | `gpu_node_ops.py` | `gpu_node_ops_lab.py` | 41 | PASS (41/41) |
| 10.9 The NVIDIA software stack: driver, CUDA toolkit, container toolkit, compatibility | `nvidia_software_stack.py` | `nvidia_software_stack_lab.py` | 30 | PASS (30/30) |
| 10.10 Fabric Manager, NVSM and NVLink domains | `fabric_manager_nvlink.py` | `fabric_manager_nvlink_lab.py` | 25 | PASS (25/25) |
| 10.11 CUDA programming basics: kernels, indexing and memory | `cuda_programming_basics.py` | `cuda_programming_basics_lab.py` | 25 | PASS (25/25) |
| 10.12 Streams, events, asynchronous copies and pinned memory | `streams_events_pinned.py` | `streams_events_pinned_lab.py` | 25 | PASS (25/25) |
| 10.13 Memory access patterns and profiling | `memory_access_patterns.py` | `memory_access_patterns_lab.py` | 25 | PASS (25/25) |
| 10.14 Occupancy, warp efficiency and instruction-level parallelism | `occupancy_warp_ilp.py` | `occupancy_warp_ilp_lab.py` | 25 | PASS (25/25) |
| 10.15 Kernel efficiency and arithmetic intensity | `kernel_efficiency.py` | `kernel_efficiency_lab.py` | 25 | PASS (25/25) |
| 10.16 Intra-kernel pipelining, warp specialization and thread block clusters | `intra_kernel_pipelining.py` | `intra_kernel_pipelining_lab.py` | 25 | PASS (25/25) |
| 10.17 Inter-kernel pipelining, synchronization and stream-ordered allocation | `inter_kernel_pipelining.py` | `inter_kernel_pipelining_lab.py` | 25 | PASS (25/25) |
| 10.18 Dynamic scheduling, CUDA graphs and device-initiated orchestration | `dynamic_scheduling_graphs.py` | `dynamic_scheduling_graphs_lab.py` | 25 | PASS (25/25) |
| 10.19 Triton language and compilers: OpenAI Triton, torch.compile, XLA | `triton_and_compilers.py` | `triton_and_compilers_lab.py` | 25 | PASS (25/25) |
| 10.20 Profiling tools: Nsight Systems, Nsight Compute, PyTorch profiler | `profiling_tools.py` | `profiling_tools_lab.py` | 25 | PASS (25/25) |
| 10.21 GPU health: DCGM, ECC, row remapping and Xid | `gpu_health_dcgm_xid.py` | `gpu_health_dcgm_xid_lab.py` | 25 | PASS (25/25) |
| 10.22 GPU troubleshooting scenarios | `gpu_troubleshooting_scenarios.py` | `gpu_troubleshooting_scenarios_lab.py` | 25 | PASS (25/25) |
