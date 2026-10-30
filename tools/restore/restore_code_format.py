#!/usr/bin/env python3
"""Re-wrap in backticks commands/options/paths/identifiers that lost code format. Usage: restore_code_format.py OLD NEW"""
import re, sys
PRODUCT={'NVLink','RoCE','InfiniBand','STREAM','MLPerf','SPEC','TTFT','TPOT','NVSwitch','DCGM','NCCL','MIG','GPUDirect','QEMU','IOMMU','VFIO','OVMF','VMCS','VMCB','KubeVirt','KVM','SR-IOV','SRIOV','BlueField','ConnectX','DOCA','Slurm','Kubernetes','Ansible','Terraform','Prometheus','Grafana','Lustre','BeeGFS','GPFS','Redfish','IPMI','BMC','PyTorch','NumPy','DeepSpeed','vLLM','SGLang','TensorRT','Triton','Dynamo','CoreDNS','OpenMPI','BIND','OpenSSH','NetworkManager','Cilium','Calico','Istio','Envoy','FRRouting','Containerlab','WireGuard','VXLAN','EVPN','OpenSM','UFM','NetBox','SONiC','Cumulus','FRR','NVUE','ONIE','NetQ','Netplan','Vagrant','Docker','Podman','Helm','Argo','RoCEv2','AllReduce','AllGather','ReduceScatter','AllToAll','LACP','MLAG','Flux','Kueue','Volcano','Jupyter','TensorBoard','Hydra'}
o, n = open(sys.argv[1], encoding='utf8').read(), open(sys.argv[2], encoding='utf8').read()
strip = lambda s: re.sub(r'```.*?```', '', s, flags=re.S)
cs = lambda s: set(re.findall(r'`([^`\n]{3,40})`', strip(s)))
dem = [x for x in cs(o)-cs(n) if re.match(r'^(-{1,2}[\w-]+|/[\w./-]+|[A-Z][A-Za-z]+(?:[A-Z]\w+)+|\w+_\w+)$', x) and x not in PRODUCT and (not re.match(r'^[A-Z][A-Za-z0-9]+(?:[A-Z]\w+)+$', x) or x in ''.join(re.findall(r'```.*?```', n, flags=re.S))) and not re.match(r'^[A-Z0-9+-]+$', x) and x in re.sub(r'`[^`\n]*`','',strip(n))]
parts = re.split(r'(```.*?```|`[^`\n]*`)', n, flags=re.S)
cnt = 0
for i in range(0, len(parts), 2):
    for x in dem:
        parts[i], k = re.subn(r'(?<![\w`-])' + re.escape(x) + r'(?![\w`])', '`' + x + '`', parts[i]); cnt += k
open(sys.argv[2], 'w', encoding='utf8').write(''.join(parts)); print('re-wrapped', cnt, 'occurrences of', len(dem), 'terms')
