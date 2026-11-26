import xml.etree.ElementTree as ET
import re

def generate_svg():
    title_text = "Ten things to decide for a GPU or HPC pod's network"
    bottom_bar_text = "Decide the rails before you write the pod spec"

    # Row 1 (2 lines, h=82)
    # Line 1: "1 Primary versus data plane: " (title) + "eth0 for control, secondary RDMA"
    # Line 2: "NICs for GPU and storage traffic"
    r1_tspans = [
        (116, 40, 30, True, "1 Primary versus data plane: "),
        (116 + 29*18, 40, 24, False, "eth0 for control, secondary RDMA"),
        (116, 66, 24, False, "NICs for GPU and storage traffic")
    ]

    # Row 2 (2 lines, h=82)
    # Line 1: "2 NCCL interface selection: " (title) + "NCCL_SOCKET_IFNAME, NCCL_IB_HCA,"
    # Line 2: "NCCL_IB_GID_INDEX set explicitly"
    r2_tspans = [
        (116, 40, 30, True, "2 NCCL interface selection: "),
        (116 + 28*18, 40, 24, False, "NCCL_SOCKET_IFNAME, NCCL_IB_HCA,"),
        (116, 66, 24, False, "NCCL_IB_GID_INDEX set explicitly")
    ]

    # Row 3 (6 lines, h=184) in w=760
    # Line 1: "3 Host networking:"
    # Line 2: "hostNetwork true with dnsPolicy"
    # Line 3: "ClusterFirstWithHostNet; simplest"
    # Line 4: "high-performance option; costs port"
    # Line 5: "conflicts, less isolation, no per-pod"
    # Line 6: "NetworkPolicy"
    r3_tspans = [
        (116, 40, 30, True, "3 Host networking:"),
        (116, 66, 24, False, "hostNetwork true with dnsPolicy"),
        (116, 92, 24, False, "ClusterFirstWithHostNet; simplest"),
        (116, 118, 24, False, "high-performance option; costs port"),
        (116, 144, 24, False, "conflicts, less isolation, no per-pod"),
        (116, 170, 24, False, "NetworkPolicy")
    ]

    # Side note (5 lines, h=184) in w=740 (x=820 to 1560)
    # Line 1: "hostNetwork pods share the node's IP and port"
    # Line 2: "space and skip the CNI; node agents such as"
    # Line 3: "kube-proxy, the CNI daemon, node-exporter and"
    # Line 4: "the DCGM exporter run this way; check for port"
    # Line 5: "conflicts before scheduling"
    sn_tspans = [
        (856, 38, 24, False, "hostNetwork pods share the node's IP and port"),
        (856, 64, 24, False, "space and skip the CNI; node agents such as"),
        (856, 90, 24, False, "kube-proxy, the CNI daemon, node-exporter and"),
        (856, 116, 24, False, "the DCGM exporter run this way; check for port"),
        (856, 142, 24, False, "conflicts before scheduling")
    ]

    # Row 4 (4 lines, h=134)
    # Line 1: "4 Overlay costs: " (title) + "small packets, many connections and large flows suffer crossing a"
    # Line 2: "veth, a bridge and an overlay (CPU softirq and a smaller MTU); prefer native routing CNIs"
    # Line 3: "or eBPF host routing for TCP-heavy services; overlay MTU is underlay minus 50 for"
    # Line 4: "VXLAN; verify with ping -M do"
    r4_tspans = [
        (116, 40, 30, True, "4 Overlay costs: "),
        (116 + 17*18, 40, 24, False, "small packets, many connections and large flows suffer crossing a"),
        (116, 66, 24, False, "veth, a bridge and an overlay (CPU softirq and a smaller MTU); prefer native routing CNIs"),
        (116, 92, 24, False, "or eBPF host routing for TCP-heavy services; overlay MTU is underlay minus 50 for"),
        (116, 118, 24, False, "VXLAN; verify with ping -M do")
    ]

    # Row 5 (3 lines, h=108)
    # Line 1: "5 Topology alignment: " (title) + "kubelet Topology Manager single-numa-node or"
    # Line 2: "best-effort with the CPU Manager and device plugins keeps GPU, NIC VF and CPUs"
    # Line 3: "on the same NUMA node or PCIe root; verify with nvidia-smi topo -m and ibdev2netdev"
    r5_tspans = [
        (116, 40, 30, True, "5 Topology alignment: "),
        (116 + 22*18, 40, 24, False, "kubelet Topology Manager single-numa-node or"),
        (116, 66, 24, False, "best-effort with the CPU Manager and device plugins keeps GPU, NIC VF and CPUs"),
        (116, 92, 24, False, "on the same NUMA node or PCIe root; verify with nvidia-smi topo -m and ibdev2netdev")
    ]

    # Row 6 (2 lines, h=82)
    # Line 1: "6 MTU consistency: " (title) + "pod MTU is node MTU minus encapsulation; secondary rails"
    # Line 2: "often 9000 and the CNI mtu must match the fabric"
    r6_tspans = [
        (116, 40, 30, True, "6 MTU consistency: "),
        (116 + 19*18, 40, 24, False, "pod MTU is node MTU minus encapsulation; secondary rails"),
        (116, 66, 24, False, "often 9000 and the CNI mtu must match the fabric")
    ]

    # Row 7 (3 lines, h=108, Orange)
    # Line 1: "7 Isolation and policy: " (title) + "NetworkPolicy with default deny per namespace"
    # Line 2: "covers the primary network; secondary SR-IOV and macvlan interfaces bypass host"
    # Line 3: "policy: isolate with VLANs, VRFs or IB partitions at the switch"
    r7_tspans = [
        (116, 40, 30, True, "7 Isolation and policy: "),
        (116 + 24*18, 40, 24, False, "NetworkPolicy with default deny per namespace"),
        (116, 66, 24, False, "covers the primary network; secondary SR-IOV and macvlan interfaces bypass host"),
        (116, 92, 24, False, "policy: isolate with VLANs, VRFs or IB partitions at the switch")
    ]

    # Row 8 (2 lines, h=82)
    # Line 1: "8 IPAM: " (title) + "size the pod CIDR against nodes and pods per node; a /24 per node gives"
    # Line 2: "254 pods; secondary networks may use whereabouts or static ranges, one per rail"
    r8_tspans = [
        (116, 40, 30, True, "8 IPAM: "),
        (116 + 8*18, 40, 24, False, "size the pod CIDR against nodes and pods per node; a /24 per node gives"),
        (116, 66, 24, False, "254 pods; secondary networks may use whereabouts or static ranges, one per rail")
    ]

    # Row 9 (2 lines, h=82)
    # Line 1: "9 Observability: " (title) + "Hubble or Cilium flow logs, Calico flow logs, kube-state and"
    # Line 2: "CNI metrics, ethtool -S for VFs, RDMA counters, nsenter into a pod's namespace"
    r9_tspans = [
        (116, 40, 30, True, "9 Observability: "),
        (116 + 17*18, 40, 24, False, "Hubble or Cilium flow logs, Calico flow logs, kube-state and"),
        (116, 66, 24, False, "CNI metrics, ethtool -S for VFs, RDMA counters, nsenter into a pod's namespace")
    ]

    # Row 10 (2 lines, h=82)
    # Line 1: "10 Upgrades: " (title) + "CNI changes can reset pod networks; stage them, drain nodes, canary"
    # Line 2: "clusters first; keep /opt/cni/bin and /etc/cni/net.d consistent"
    r10_tspans = [
        (116, 40, 30, True, "10 Upgrades: "),
        (116 + 13*18, 40, 24, False, "CNI changes can reset pod networks; stage them, drain nodes, canary"),
        (116, 66, 24, False, "clusters first; keep /opt/cni/bin and /etc/cni/net.d consistent")
    ]

    row_configs = [
        (1, 82, r1_tspans, False),
        (2, 82, r2_tspans, False),
        (3, 188, r3_tspans, False), # Row 3
        (4, 134, r4_tspans, False),
        (5, 108, r5_tspans, False),
        (6, 82, r6_tspans, False),
        (7, 108, r7_tspans, True),  # Orange!
        (8, 82, r8_tspans, False),
        (9, 82, r9_tspans, False),
        (10, 82, r10_tspans, False),
    ]

    gap = 4
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    lines.append(f'  <title>{title_text}</title>')
    lines.append('  <desc>A numbered table with ten decisions and rules for a GPU or HPC pod network</desc>')
    lines.append('')
    lines.append('  <!-- Background -->')
    lines.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    lines.append('')
    lines.append('  <!-- Title -->')
    lines.append(f'  <text x="800" y="46" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">{title_text}</text>')
    lines.append('')

    cur_y = 68
    for row_num, h, tspans, is_orange in row_configs:
        stroke_color = "#db8129" if is_orange else "#207448"
        stroke_w = "3" if is_orange else "2"
        fill_color = "#e8f1ea"

        if row_num == 3:
            # Row 3 (w=760, x=40 to 800)
            lines.append(f'  <!-- Row 3: Host networking -->')
            lines.append(f'  <g id="row-3">')
            lines.append(f'    <rect x="40" y="{cur_y}" width="760" height="{h}" rx="8" fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_w}"/>')
            # Icon
            ic_y = cur_y + 16
            lines.append(f'    <g stroke="{stroke_color}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none">')
            lines.append(f'      <rect x="54" y="{ic_y}" width="44" height="28" rx="4"/>')
            lines.append(f'      <line x1="62" y1="{ic_y + 14}" x2="72" y2="{ic_y + 14}"/>')
            lines.append(f'      <circle cx="88" cy="{ic_y + 14}" r="2" fill="{stroke_color}"/>')
            lines.append(f'    </g>')
            # Text
            lines.append(f'    <text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">')
            for tx, ty_rel, fs, is_bold, txt in tspans:
                bold_attr = ' font-weight="bold"' if is_bold else ''
                lines.append(f'      <tspan x="{tx}" y="{cur_y + ty_rel}" font-size="{fs}"{bold_attr}>{txt}</tspan>')
            lines.append(f'    </text>')
            lines.append(f'  </g>')
            lines.append('')

            # Side note (w=740, x=820 to 1560)
            lines.append(f'  <!-- Side note -->')
            lines.append(f'  <g id="side-note">')
            lines.append(f'    <rect x="820" y="{cur_y}" width="740" height="{h}" rx="8" fill="{fill_color}" stroke="#207448" stroke-width="2" stroke-dasharray="6,4"/>')
            # Icon for side note
            sn_ic_y = cur_y + 16
            lines.append(f'    <g stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none">')
            lines.append(f'      <circle cx="840" cy="{sn_ic_y + 14}" r="12"/>')
            lines.append(f'      <line x1="840" y1="{sn_ic_y + 12}" x2="840" y2="{sn_ic_y + 20}"/>')
            lines.append(f'      <circle cx="840" cy="{sn_ic_y + 8}" r="1.5" fill="#207448"/>')
            lines.append(f'    </g>')
            lines.append(f'    <text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">')
            for tx, ty_rel, fs, is_bold, txt in sn_tspans:
                lines.append(f'      <tspan x="{tx}" y="{cur_y + ty_rel}" font-size="{fs}">{txt}</tspan>')
            lines.append(f'    </text>')
            lines.append(f'  </g>')
            lines.append('')

        else:
            # Full width row (w=1520)
            lines.append(f'  <!-- Row {row_num} -->')
            lines.append(f'  <g id="row-{row_num}">')
            lines.append(f'    <rect x="40" y="{cur_y}" width="1520" height="{h}" rx="8" fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_w}"/>')
            
            # Icons
            ic_y = cur_y + 14
            lines.append(f'    <g stroke="{stroke_color}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none">')
            if row_num == 1:
                lines.append(f'      <rect x="54" y="{ic_y}" width="44" height="28" rx="4"/>')
                lines.append(f'      <line x1="64" y1="{ic_y + 9}" x2="72" y2="{ic_y + 9}"/>')
                lines.append(f'      <line x1="64" y1="{ic_y + 19}" x2="72" y2="{ic_y + 19}"/>')
                lines.append(f'      <circle cx="86" cy="{ic_y + 9}" r="2" fill="{stroke_color}"/>')
                lines.append(f'      <circle cx="86" cy="{ic_y + 19}" r="2" fill="{stroke_color}"/>')
            elif row_num == 2:
                lines.append(f'      <rect x="54" y="{ic_y}" width="44" height="28" rx="4"/>')
                lines.append(f'      <path d="M 64,{ic_y+7} L 88,{ic_y+21} M 88,{ic_y+7} L 64,{ic_y+21}"/>')
            elif row_num == 4:
                lines.append(f'      <rect x="54" y="{ic_y + 4}" width="44" height="34" rx="4"/>')
                lines.append(f'      <rect x="62" y="{ic_y + 11}" width="28" height="20" rx="2"/>')
                lines.append(f'      <line x1="76" y1="{ic_y + 15}" x2="76" y2="{ic_y + 27}"/>')
            elif row_num == 5:
                lines.append(f'      <rect x="58" y="{ic_y + 2}" width="36" height="36" rx="4"/>')
                lines.append(f'      <circle cx="76" cy="{ic_y + 20}" r="6"/>')
                lines.append(f'      <line x1="58" y1="{ic_y + 14}" x2="52" y2="{ic_y + 14}"/>')
                lines.append(f'      <line x1="58" y1="{ic_y + 26}" x2="52" y2="{ic_y + 26}"/>')
                lines.append(f'      <line x1="94" y1="{ic_y + 14}" x2="100" y2="{ic_y + 14}"/>')
                lines.append(f'      <line x1="94" y1="{ic_y + 26}" x2="100" y2="{ic_y + 26}"/>')
            elif row_num == 6:
                lines.append(f'      <rect x="54" y="{ic_y}" width="44" height="28" rx="4"/>')
                lines.append(f'      <line x1="62" y1="{ic_y + 14}" x2="90" y2="{ic_y + 14}"/>')
                lines.append(f'      <polyline points="66,{ic_y+10} 62,{ic_y+14} 66,{ic_y+18}"/>')
                lines.append(f'      <polyline points="86,{ic_y+10} 90,{ic_y+14} 86,{ic_y+18}"/>')
            elif row_num == 7:
                lines.append(f'      <path d="M 76,{ic_y+2} L 96,{ic_y+9} L 96,{ic_y+23} C 96,{ic_y+33} 76,{ic_y+40} 76,{ic_y+40} C 76,{ic_y+40} 56,{ic_y+33} 56,{ic_y+23} L 56,{ic_y+9} Z"/>')
                lines.append(f'      <line x1="76" y1="{ic_y+14}" x2="76" y2="{ic_y+26}"/>')
                lines.append(f'      <circle cx="76" cy="{ic_y+20}" r="2" fill="{stroke_color}"/>')
            elif row_num == 8:
                lines.append(f'      <rect x="54" y="{ic_y}" width="44" height="28" rx="4"/>')
                lines.append(f'      <line x1="68" y1="{ic_y}" x2="68" y2="{ic_y + 28}"/>')
                lines.append(f'      <line x1="82" y1="{ic_y}" x2="82" y2="{ic_y + 28}"/>')
                lines.append(f'      <line x1="54" y1="{ic_y + 14}" x2="98" y2="{ic_y + 14}"/>')
            elif row_num == 9:
                lines.append(f'      <path d="M 56,{ic_y+26} A 20,20 0 1,1 96,{ic_y+26}"/>')
                lines.append(f'      <line x1="76" y1="{ic_y+26}" x2="88" y2="{ic_y+14}"/>')
                lines.append(f'      <circle cx="76" cy="{ic_y+26}" r="3" fill="{stroke_color}"/>')
            elif row_num == 10:
                lines.append(f'      <path d="M 94,{ic_y+14} A 18,18 0 1,0 76,{ic_y+32}"/>')
                lines.append(f'      <polyline points="94,{ic_y+6} 94,{ic_y+14} 86,{ic_y+14}"/>')
            lines.append(f'    </g>')

            # Text
            lines.append(f'    <text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">')
            for tx, ty_rel, fs, is_bold, txt in tspans:
                bold_attr = ' font-weight="bold"' if is_bold else ''
                lines.append(f'      <tspan x="{tx}" y="{cur_y + ty_rel}" font-size="{fs}"{bold_attr}>{txt}</tspan>')
            lines.append(f'    </text>')
            lines.append(f'  </g>')
            lines.append('')

        cur_y += h + gap

    # Bottom bar
    bb_y = cur_y + 6
    bb_h = 52
    lines.append('  <!-- Bottom takeaway bar -->')
    lines.append('  <g id="bottom-bar">')
    lines.append(f'    <rect x="40" y="{bb_y}" width="1520" height="{bb_h}" rx="8" fill="#207448"/>')
    lines.append(f'    <text x="800" y="{bb_y + 36}" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle">{bottom_bar_text}</text>')
    lines.append('  </g>')
    lines.append('</svg>')

    return "\n".join(lines)

svg_str = generate_svg()
with open("test_output2.svg", "w", encoding="utf-8") as f:
    f.write(svg_str)
print("Saved test_output2.svg successfully!")
