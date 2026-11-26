import re
import xml.etree.ElementTree as ET

with open("output.svg") as f:
    svg_content = f.read()

# 1. Parse XML
root = ET.fromstring(svg_content)

# Extract viewBox
vb = root.attrib.get('viewBox', '').split()
assert len(vb) == 4, "Invalid viewBox"
min_x, min_y, width, height = map(float, vb)
print(f"Canvas size: {width} x {height}")
assert width == 1600
assert height <= 1200

# 2. Check title and desc are first children
first_child = root[0].tag.split('}')[-1]
second_child = root[1].tag.split('}')[-1]
print(f"First children: <{first_child}>, <{second_child}>")
assert first_child == 'title'
assert second_child == 'desc'

# 3. Check exact source labels:
expected_labels = [
    "br0 (10.10.0.1/24)",
    "c1 (10.10.0.11)",
    "c2 (10.10.0.12)",
    "uplink NIC",
    "host",
    "c1 to c2 on the same bridge",
    "c1's own stack routes the packet because both share a subnet, ARP finds c2, the packet leaves c1's eth0 (veth peer), enters the host-side veth, the bridge learns the MAC and forwards the frame to c2's veth and eth0",
    "br_netfilter and net.bridge.bridge-nf-call-iptables=1 let iptables see bridged traffic; Kubernetes requires it so kube-proxy rules apply",
    "c1 to the Internet",
    "default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD then POSTROUTING masquerade, leaves through the NIC with the host's address; return traffic is un-NATed by conntrack and delivered back through the bridge; the outside world only talks to the host",
    "sysctl -w net.ipv4.ip_forward=1",
    "iptables -t nat -A POSTROUTING -s 10.10.0.0/24 ! -o br0 -j MASQUERADE",
    "iptables -I FORWARD -i br0 -j ACCEPT",
    "iptables -I FORWARD -o br0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
    "host:8080 to c1:80",
    "iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.10.0.11:80",
    "iptables -t nat -A OUTPUT -p tcp -d 127.0.0.1 --dport 8080 -j DNAT ... for local clients",
    "DNS inside: mkdir /etc/netns/c1 and write nameserver 1.1.1.1 to /etc/netns/c1/resolv.conf",
    "almost literally what the default bridge network does: docker0, a veth per container, an IPAM address from a private pool, a default route via the bridge, masquerade, DNAT for published ports, a bind-mounted /etc/resolv.conf",
    "A container is only a namespace plus a cable"
]

# Extract all text content
all_texts = [el.text for el in root.iter() if el.text and el.tag.split('}')[-1] in ('text', 'tspan')]
joined_text = " ".join(all_texts)

for label in expected_labels:
    # Check if words appear
    # Normalize spaces
    clean_label = " ".join(label.split())
    # Count occurrences of key unique phrases
    found = clean_label in joined_text
    print(f"Check '{clean_label[:40]}...': {found}")
    assert found, f"Missing label: {clean_label}"

# 4. Check for forbidden style words printed as text
forbidden = ["monospace", "bold", "orange", "grey", "arrow"]
for text in all_texts:
    for f_word in forbidden:
        # Check whole word
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        assert f_word not in words, f"Forbidden style instruction word '{f_word}' found in text: '{text}'"

print("All labels checked and verified!")
