import xml.etree.ElementTree as ET
import re
import sys

def audit_svg(svg_path):
    print(f"Auditing {svg_path}...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

    # 2. Dimensions
    width = root.get('width')
    viewBox = root.get('viewBox')
    height = root.get('height')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"Expected width 1600, got {width}"
    assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
    assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"

    # 3. Check font-size >= 24 on all text and tspans
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = "".join(elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        fs = elem.attrib.get('font-size')
        assert fs is not None, f"Missing font-size on text '{full_text}'"
        size = float(fs)
        assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
        text_elements.append((full_text, size))

    print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels
    expected_labels = [
        "Ten things to decide for a GPU or HPC pod's network",
        "1 Primary versus data plane: eth0 for control, secondary RDMA NICs for GPU and storage traffic",
        "2 NCCL interface selection: NCCL_SOCKET_IFNAME, NCCL_IB_HCA, NCCL_IB_GID_INDEX set explicitly",
        "3 Host networking: hostNetwork true with dnsPolicy ClusterFirstWithHostNet; simplest high-performance option; costs port conflicts, less isolation, no per-pod NetworkPolicy",
        "4 Overlay costs: small packets, many connections and large flows suffer crossing a veth, a bridge and an overlay (CPU softirq and a smaller MTU); prefer native routing CNIs or eBPF host routing for TCP-heavy services; overlay MTU is underlay minus 50 for VXLAN; verify with ping -M do",
        "5 Topology alignment: kubelet Topology Manager single-numa-node or best-effort with the CPU Manager and device plugins keeps GPU, NIC VF and CPUs on the same NUMA node or PCIe root; verify with nvidia-smi topo -m and ibdev2netdev",
        "6 MTU consistency: pod MTU is node MTU minus encapsulation; secondary rails often 9000 and the CNI mtu must match the fabric",
        "7 Isolation and policy: NetworkPolicy with default deny per namespace covers the primary network; secondary SR-IOV and macvlan interfaces bypass host policy: isolate with VLANs, VRFs or IB partitions at the switch",
        "8 IPAM: size the pod CIDR against nodes and pods per node; a /24 per node gives 254 pods; secondary networks may use whereabouts or static ranges, one per rail",
        "9 Observability: Hubble or Cilium flow logs, Calico flow logs, kube-state and CNI metrics, ethtool -S for VFs, RDMA counters, nsenter into a pod's namespace",
        "10 Upgrades: CNI changes can reset pod networks; stage them, drain nodes, canary clusters first; keep /opt/cni/bin and /etc/cni/net.d consistent",
        "hostNetwork pods share the node's IP and port space and skip the CNI; node agents such as kube-proxy, the CNI daemon, node-exporter and the DCGM exporter run this way; check for port conflicts before scheduling",
        "Decide the rails before you write the pod spec"
    ]

    found_texts = [t for t, fs in text_elements]

    print(f"\n4. Checking {len(expected_labels)} expected labels:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in found_texts if t not in expected_labels]
    print(f"\nExtra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"

    print("\n5. No forbidden words found! (PASS)")

    # 6. Check orange count
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("\n8. All required colors present! (PASS)")

    # 9. Check text bounds & paddings
    print("\n9. Checking text bounds & paddings...")
    # Check each group
    groups = [
        "row-1", "row-2", "row-3", "side-note", "row-4", "row-5",
        "row-6", "row-7", "row-8", "row-9", "row-10", "bottom-bar"
    ]
    for gid in groups:
        g = root.find(f".//*[@id='{gid}']")
        assert g is not None, f"Group {gid} not found"
        rect = g.find('{http://www.w3.org/2000/svg}rect')
        rx = float(rect.attrib['x'])
        ry = float(rect.attrib['y'])
        rw = float(rect.attrib['width'])
        rh = float(rect.attrib['height'])

        # Check texts inside g
        for text in g.findall('{http://www.w3.org/2000/svg}text'):
            base_fs = float(text.attrib.get('font-size', 24))
            tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
            if not tspans:
                tspans = [text]
            for tsp in tspans:
                t = (tsp.text or "").strip()
                if not t: continue
                fs = float(tsp.attrib.get('font-size', base_fs))
                w = len(t) * 0.60 * fs
                anchor = tsp.attrib.get('text-anchor', text.attrib.get('text-anchor', 'start'))
                tx = float(tsp.attrib.get('x', text.attrib.get('x', 0)))
                ty = float(tsp.attrib.get('y', text.attrib.get('y', 0)))
                if anchor == 'middle':
                    x_left = tx - w / 2
                    x_right = tx + w / 2
                elif anchor == 'end':
                    x_left = tx - w
                    x_right = tx
                else:
                    x_left = tx
                    x_right = tx + w

                # Padding checks: at least 16px padding
                pad_l = x_left - rx
                pad_r = (rx + rw) - x_right
                pad_t = (ty - fs * 0.8) - ry
                pad_b = (ry + rh) - ty

                assert pad_l >= 15.9, f"Left padding violation in {gid}: {pad_l:.1f}px < 16px (text='{t}')"
                assert pad_r >= 15.9, f"Right padding violation in {gid}: {pad_r:.1f}px < 16px (text='{t}')"
                assert pad_t >= 15.9, f"Top padding violation in {gid}: {pad_t:.1f}px < 16px (text='{t}')"
                assert pad_b >= 15.9, f"Bottom padding violation in {gid}: {pad_b:.1f}px < 16px (text='{t}')"

    print("\n9. All text elements fit within boxes with >= 16px padding! (PASS)")
    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "test_output.svg"
    audit_svg(target)
