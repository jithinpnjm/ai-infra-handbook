#!/usr/bin/env python3
"""Voice gate. Usage: voice_gate.py OLD.md NEW.md   (also usable on section files)
Content must be preserved; voice must measurably improve."""
import sys, re, subprocess
PRODUCT={'NVLink','RoCE','InfiniBand','STREAM','MLPerf','SPEC','TTFT','TPOT','NVSwitch','DCGM','NCCL','MIG','GPUDirect','QEMU','IOMMU','VFIO','OVMF','VMCS','VMCB','KubeVirt','KVM','SR-IOV','SRIOV','BlueField','ConnectX','DOCA','Slurm','Kubernetes','Ansible','Terraform','Prometheus','Grafana','Lustre','BeeGFS','GPFS','Redfish','IPMI','BMC','PyTorch','NumPy','DeepSpeed','vLLM','SGLang','TensorRT','Triton','Dynamo','CoreDNS','OpenMPI','BIND','OpenSSH','NetworkManager','Cilium','Calico','Istio','Envoy','FRRouting','Containerlab','WireGuard','VXLAN','EVPN','OpenSM','UFM','NetBox','SONiC','Cumulus','FRR','NVUE','ONIE','NetQ','Netplan','Vagrant','Docker','Podman','Helm','Argo','RoCEv2','AllReduce','AllGather','ReduceScatter','AllToAll','LACP','MLAG','Flux','Kueue','Volcano','Jupyter','TensorBoard','Hydra'}
old, new = sys.argv[1], sys.argv[2]
o, n = open(old,encoding='utf8').read(), open(new,encoding='utf8').read()
ok = True
def say(good, msg):
    global ok; ok &= bool(good); print(('PASS ' if good else 'FAIL ')+msg)
r = subprocess.run(['python3','tools/loss_check.py',old,new,'--list'],capture_output=True,text=True).stdout
m = re.search(r'technical terms lost: (\d+) of \d+ \| numbers lost: (\d+)', r)
ABBR={'SCL','HLW','SP','ASP','LP','AF','HPC1','ADC','CN','NK','NPA','AIP','GAI','LLMOps1','AUR','EAS','FA','PM','FP','PK','NK1','PMO','DDIA'}
lt=re.search(r"LOST TERMS: \[(.*?)\]", r, re.S); lost=[x.strip(" '\"") for x in (lt.group(1).split(',') if lt and lt.group(1).strip() else [])]
real=[x for x in lost if x and x not in ABBR]
say(m and not real and m.group(2)=='0', f'content loss_check terms lost (excluding spelled-out source abbreviations): {real}, numbers lost {m.group(2) if m else "?"}')
if m and (m.group(1)!='0' or m.group(2)!='0'): print('   ', ' '.join(r.split('\n')[2:4])[:400])
cnt = lambda t,s: t.count(s)
say(cnt(n,'```')%2==0, 'fences balanced')
say(cnt(n,'```')==cnt(o,'```'), f'code blocks same ({cnt(o,"```")//2})')
say(len([l for l in n.split('\n') if l.startswith('|')])>=len([l for l in o.split('\n') if l.startswith('|')]), 'table rows kept')
say(cnt(n,'<summary>')==cnt(o,'<summary>') and cnt(n,'</details>')==cnt(o,'</details>'), f'questions kept ({cnt(o,"<summary>")})')
hd = lambda t:[x.strip() for x in t.split('\n') if x.startswith('#') and not x.startswith('# ')]
say(len(hd(n))>=len(hd(o)), f'headings {len(hd(o))} -> {len(hd(n))}')
say(cnt(n,'```mermaid')==cnt(o,'```mermaid'), 'diagrams kept')
say('&lt;strong>' not in n and n.split('---',2)[1]==o.split('---',2)[1] if o.startswith('---') else True, 'front matter / no escaped html')
w0, w1 = len(o.split()), len(n.split())
say(0.85*w0 <= w1 <= 1.6*w0, f'words {w0} -> {w1} (allowed 85%..160%)')
src = open('tools/validate_chapter.py').read()
ns = {}; exec('import re\n'+src[src.index('def readability'):src.index('r = readability')], ns)
a, b = ns['readability'](o), ns['readability'](n)
lim = dict(spans=4.0, nums=6.0, avg=22.0, long=3.0, paren=0.5)
for k in lim:
    say(b[k] <= lim[k] or b[k] < a[k]*(0.9 if k=='spans' else 0.8), f'{k}: {a[k]:.1f} -> {b[k]:.1f} (limit {lim[k]})')
body = re.sub(r'```.*?```',' ',n,flags=re.S)
cues = len(re.findall(r'\b(you|your|imagine|suppose|picture|consider|let\'s|we)\b', body, re.I))
say(cues/max(1,len(body.split()))*100 >= 0.6, f'reader-address cues per 100 words: {cues/max(1,len(body.split()))*100:.1f} (need >= 0.6)')
ex = len(re.findall(r'\b(for example|for instance|suppose|imagine|picture|consider|say you|a team|an engineer|on-call|one night)\b', body, re.I))
say(ex >= 2 or w1 < 1500, f'scenario/example markers: {ex}')
strip = lambda s: re.sub(r'```.*?```','',s,flags=re.S)
cs = lambda s: set(re.findall(r'`([^`\n]{3,40})`', strip(s)))
dem = [x for x in cs(o)-cs(n) if re.match(r'^(-{1,2}[\w-]+|/[\w./-]+|[A-Z][A-Za-z]+(?:[A-Z]\w+)+|\w+_\w+)$', x) and x not in PRODUCT and (not re.match(r'^[A-Z][A-Za-z0-9]+(?:[A-Z]\w+)+$', x) or x in ''.join(re.findall(r'```.*?```', n, flags=re.S))) and not re.match(r'^[A-Z0-9+-]+$', x) and x in re.sub(r'`[^`\n]*`','',strip(n))]
say(not dem, f'commands/options/paths still in code format (demoted: {dem[:8]})')
print('RESULT','PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
