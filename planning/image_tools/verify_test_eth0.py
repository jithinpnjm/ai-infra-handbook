import xml.etree.ElementTree as ET
import re

tree = ET.parse('test_host_eth0.svg')
root = tree.getroot()

required = [
    "Find the host side of a pod's eth0",
    'PID=$(crictl inspect $CTR | jq -r .info.pid)',
    'gives the pod network namespace',
    'crictl pods --name trainer-0 -q',
    'then',
    'crictl inspectp',
    'for the netns path',
    'nsenter -t $PID -n ip link show eth0',
    '2: eth0@if47:',
    'BROADCAST,MULTICAST,UP,LOWER_UP',
    'the number after @if is the peer index 47',
    'On the host:',
    'ip link | grep ^47:',
    '47: cali8a9b1c2d@if2',
    '(or a veth or lxc name)',
    'pod namespace',
    'eth0@if47',
    'host namespace',
    'cali8a9b1c2d@if2',
    'veth pair',
    'Result:',
    "tcpdump -i cali8a9b1c2d -nn captures only that pod's traffic",
]

svg_raw = open('test_host_eth0.svg').read()
missing = [r for r in required if r not in svg_raw]
print('Missing strings:', missing)

# Check colors used
colors = set(re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}', svg_raw))
print('Colors used:', colors)
