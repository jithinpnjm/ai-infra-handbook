# Part 11 Code and Self-Checking Labs: GPUs on Kubernetes, Scheduling and Virtualization

All labs in this directory use Python 3 standard library only and run with `python3 -B code/part11/<lab_file>.py`.

| Chapter | Model file | Lab file | Self-checks | Status |
|---|---|---|---|---|
| 11.1 Why Kubernetes needs a GPU platform layer | `gpu_platform_layer.py` | `gpu_platform_layer_lab.py` | 25 | PASS (25/25) |
| 11.2 Device plugin, container toolkit, CDI and runtime classes | `device_plugin_toolkit_cdi.py` | `device_plugin_toolkit_cdi_lab.py` | 26 | PASS (26/26) |
| 11.3 Node Feature Discovery and GPU Feature Discovery | `nfd_and_gfd.py` | `nfd_and_gfd_lab.py` | 26 | PASS (26/26) |
| 11.4 GPU Operator architecture and operands | `gpu_operator_and_operands.py` | `gpu_operator_and_operands_lab.py` | 25 | PASS (25/25) |
| 11.5 GPU Operator installation, configuration and upgrades | `gpu_operator_upgrades.py` | `gpu_operator_upgrades_lab.py` | 25 | PASS (25/25) |
| 11.6 Scheduling GPUs: requests, Topology Manager, CPU and NUMA alignment | `gpu_scheduling_and_topology.py` | `gpu_scheduling_and_topology_lab.py` | 25 | PASS (25/25) |
| 11.7 Multi-node jobs: why a pod cannot span nodes, and gang scheduling concepts | `multi_node_and_gang_scheduling.py` | `multi_node_and_gang_scheduling_lab.py` | 25 | PASS (25/25) |
| 11.8 Kueue, Volcano and scheduler plugins | `kueue_volcano_and_plugins.py` | `kueue_volcano_and_plugins_lab.py` | 25 | PASS (25/25) |
| 11.9 JobSet, LeaderWorkerSet, PyTorchJob and the MPI Operator | `jobset_lws_pytorch_mpi.py` | `jobset_lws_pytorch_mpi_lab.py` | 25 | PASS (25/25) |
| 11.10 Secondary networks: Multus, SR-IOV device plugin and RDMA device plugin | `secondary_networks_multus_sriov_rdma.py` | `secondary_networks_multus_sriov_rdma_lab.py` | 25 | PASS (25/25) |
| 11.11 NVIDIA Network Operator | `nvidia_network_operator.py` | `nvidia_network_operator_lab.py` | 25 | PASS (25/25) |
| 11.12 Dynamic Resource Allocation (DRA) | `dynamic_resource_allocation_dra.py` | `dynamic_resource_allocation_dra_lab.py` | 25 | PASS (25/25) |
| 11.13 KAI Scheduler: why default scheduling is not enough | `kai_why_default_not_enough.py` | `kai_why_default_not_enough_lab.py` | 25 | PASS (25/25) |
| 11.14 KAI Scheduler architecture and resources | `kai_architecture_and_resources.py` | `kai_architecture_and_resources_lab.py` | 25 | PASS (25/25) |
| 11.15 KAI queues, quotas and fair sharing | `kai_queues_quotas_fair_sharing.py` | `kai_queues_quotas_fair_sharing_lab.py` | 25 | PASS (25/25) |
| 11.16 KAI gang scheduling and topology-aware placement | `kai_gang_and_topology.py` | `kai_gang_and_topology_lab.py` | 25 | PASS (25/25) |
| 11.17 KAI GPU sharing and fractions | `kai_gpu_sharing_and_fractions.py` | `kai_gpu_sharing_and_fractions_lab.py` | 25 | PASS (25/25) |
| 11.18 KAI operations and troubleshooting | `kai_operations_and_troubleshooting.py` | `kai_operations_and_troubleshooting_lab.py` | 25 | PASS (25/25) |
| 11.19 The Run:ai platform view | `run_ai_platform_view.py` | `run_ai_platform_view_lab.py` | 25 | PASS (25/25) |
| 11.20 Scheduler comparison guide: KAI, Kueue, Volcano, YuniKorn and Slurm | `scheduler_comparison_guide.py` | `scheduler_comparison_guide_lab.py` | 25 | PASS (25/25) |
| 11.21 PCIe, IOMMU, VFIO and device passthrough | `pcie_iommu_vfio_passthrough.py` | `pcie_iommu_vfio_passthrough_lab.py` | 25 | PASS (25/25) |
| 11.22 SR-IOV for NICs and GPUs | `sriov_for_nics_and_gpus.py` | `sriov_for_nics_and_gpus_lab.py` | 25 | PASS (25/25) |
| 11.23 NVIDIA vGPU: architecture, profiles and licensing | `nvidia_vgpu_architecture_licensing.py` | `nvidia_vgpu_architecture_licensing_lab.py` | 25 | PASS (25/25) |
| 11.24 MIG in depth | `mig_in_depth.py` | `mig_in_depth_lab.py` | 25 | PASS (25/25) |
| 11.25 Time-slicing, MPS and oversubscription | `time_slicing_mps_oversubscription.py` | `time_slicing_mps_oversubscription_lab.py` | 25 | PASS (25/25) |
| 11.26 Choosing a GPU sharing model | `choosing_gpu_sharing_model.py` | `choosing_gpu_sharing_model_lab.py` | 25 | PASS (25/25) |
| 11.27 Virtual machines on Kubernetes: KubeVirt, Kata and GPU passthrough | `vms_on_k8s_kubevirt_kata_gpu.py` | `vms_on_k8s_kubevirt_kata_gpu_lab.py` | 25 | PASS (25/25) |
| 11.28 DPUs, BlueField and DOCA | `dpus_bluefield_and_doca.py` | `dpus_bluefield_and_doca_lab.py` | 25 | PASS (25/25) |
| 11.29 Multi-tenancy, quotas, fault tolerance and health on GPU clusters | `multi_tenancy_quotas_fault_tolerance_health.py` | `multi_tenancy_quotas_fault_tolerance_health_lab.py` | 25 | PASS (25/25) |
| 11.30 Lab: multi-node GPU Kubernetes on GKE and Nebius | `multi_node_gke_and_nebius.py` | `multi_node_gke_and_nebius_lab.py` | 25 | PASS (25/25) |
