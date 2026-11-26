#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

def generate_svg():
    H = 1120
    
    # Left panel bounds:
    # x=40, y=110, w=730, h=970
    # Right panel bounds:
    # x=830, y=110, w=730, h=970
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">
  <title>Karpenter versus node groups, and the NodePool rules</title>
  <desc>Technical infographic comparing Cluster Autoscaler fixed node group menu versus Karpenter just-in-time chef provisioning, beside an annotated Karpenter NodePool manifest for gpu-inference with requirements, taints, limits, and disruption policies.</desc>

  <!-- Background -->
  <rect width="1600" height="{H}" fill="#f5f8f5" />

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Karpenter versus node groups, and the NodePool rules</text>

  <!-- ==================== LEFT PANEL: menu versus chef ==================== -->
  <g id="left-panel">
    <!-- Panel Container -->
    <rect x="40" y="110" width="730" height="970" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Left Panel Header Icon: Chef Hat / Menu (56px) -->
    <g transform="translate(68, 130)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 44 h 32 v 8 h -32 z" />
      <path d="M 14 44 c -8 -4 -8 -16 0 -22 c -4 -10 6 -18 14 -14 c 6 -8 18 -8 24 0 c 8 -4 18 4 14 14 c 8 6 8 18 0 22" />
      <line x1="20" y1="48" x2="36" y2="48" stroke-width="2.5" />
    </g>

    <!-- Left Panel Title (32px bold) -->
    <text x="142" y="168" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">menu versus chef</text>

    <!-- Card 1: Cluster Autoscaler (Fixed Menu) -->
    <g id="ca-card">
      <rect x="68" y="210" width="674" height="230" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
      
      <!-- Icon: Fixed Menu / Grid (56px) -->
      <g transform="translate(92, 234)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="48" height="44" rx="4" />
        <line x1="4" y1="18" x2="52" y2="18" />
        <line x1="16" y1="26" x2="40" y2="26" />
        <line x1="16" y1="34" x2="40" y2="34" />
        <line x1="16" y1="42" x2="30" y2="42" />
        <circle cx="10" cy="12" r="2" fill="#207448" />
        <circle cx="16" cy="12" r="2" fill="#207448" />
      </g>

      <!-- Label 3: Cluster Autoscaler description -->
      <text x="166" y="260" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="166" dy="0">Cluster Autoscaler orders from a fixed</tspan>
        <tspan x="166" dy="36">menu of node groups, each with one</tspan>
        <tspan x="166" dy="36">shape</tspan>
      </text>
    </g>

    <!-- Card 2: Karpenter (Chef / Just-In-Time) -->
    <g id="karpenter-card">
      <rect x="68" y="465" width="674" height="585" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />

      <!-- Icon: Smart Batching / Engine (56px) -->
      <g transform="translate(92, 495)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="14" />
        <path d="M 28 6 v 8 M 28 42 v 8 M 6 28 h 8 M 42 28 h 8 M 12 12 l 6 6 M 38 38 l 6 6 M 12 44 l 6 -6 M 38 18 l 6 -6" />
        <circle cx="28" cy="28" r="5" fill="#207448" />
      </g>

      <!-- Label 4: Karpenter description -->
      <text x="166" y="525" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="166" dy="0">Karpenter watches Pending pods,</tspan>
        <tspan x="166" dy="38">batches them, computes the best set of</tspan>
        <tspan x="166" dy="38">instance types that satisfy their</tspan>
        <tspan x="166" dy="38">constraints, and provisions just in</tspan>
        <tspan x="166" dy="38">time; bin-packing, spot handling with</tspan>
        <tspan x="166" dy="38">interruption notices, automatic</tspan>
        <tspan x="166" dy="38">rotation and drift correction</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== RIGHT PANEL: annotated NodePool gpu-inference ==================== -->
  <g id="right-panel">
    <!-- Panel Container -->
    <rect x="830" y="110" width="730" height="970" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Right Panel Header Icon: Manifest / NodePool (56px) -->
    <g transform="translate(858, 130)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="6" width="40" height="44" rx="5" />
      <path d="M 18 18 h 20 M 18 26 h 20 M 18 34 h 12" />
      <circle cx="14" cy="18" r="1.5" fill="#207448" />
      <circle cx="14" cy="26" r="1.5" fill="#207448" />
      <circle cx="14" cy="34" r="1.5" fill="#207448" />
    </g>

    <!-- Right Panel Title: annotated NodePool gpu-inference (30px bold) -->
    <text x="932" y="168" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">annotated NodePool gpu-inference</text>

    <!-- Item 1: requirements instance-family -->
    <g id="item-requirements">
      <rect x="858" y="210" width="674" height="74" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(876, 224)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="32" height="32" rx="4" />
        <line x1="4" y1="16" x2="36" y2="16" />
        <circle cx="12" cy="26" r="2" fill="#207448" />
        <circle cx="20" cy="26" r="2" fill="#207448" />
        <circle cx="28" cy="26" r="2" fill="#207448" />
      </g>
      <text x="932" y="244" font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="932" dy="0">requirements instance-family</tspan>
        <tspan x="932" dy="30">In g6, g6e, p5</tspan>
      </text>
    </g>

    <!-- Item 2: capacity-type On-demand -->
    <g id="item-capacity">
      <rect x="858" y="294" width="674" height="56" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(876, 303)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="20" cy="20" r="14" />
        <polyline points="14,20 18,24 26,16" />
      </g>
      <text x="932" y="331" font-family="monospace" font-size="24" fill="#303a36">capacity-type On-demand</text>
    </g>

    <!-- Item 3: zones us-east-1a and us-east-1b -->
    <g id="item-zones">
      <rect x="858" y="360" width="674" height="56" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(876, 369)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="14" cy="20" r="8" />
        <circle cx="26" cy="20" r="8" />
      </g>
      <text x="932" y="397" font-family="monospace" font-size="24" fill="#303a36">zones us-east-1a and us-east-1b</text>
    </g>

    <!-- Item 4: taints nvidia.com/gpu=present NoSchedule (keeps ordinary pods off) -->
    <g id="item-taints">
      <rect x="858" y="426" width="674" height="78" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(876, 442)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 20 6 L 34 12 V 24 C 34 32 20 38 20 38 C 20 38 6 32 6 24 V 12 Z" />
        <line x1="14" y1="22" x2="26" y2="22" />
      </g>
      <text x="932" y="458" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="932" dy="0" font-family="monospace">taints nvidia.com/gpu=present</tspan>
        <tspan x="932" dy="30">NoSchedule (keeps ordinary pods off)</tspan>
      </text>
    </g>

    <!-- Item 5: nodeClassRef EC2NodeClass gpu -->
    <g id="item-nodeclass">
      <rect x="858" y="514" width="674" height="56" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(876, 523)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="28" height="24" rx="3" />
        <line x1="6" y1="16" x2="34" y2="16" />
        <line x1="20" y1="32" x2="20" y2="38" />
        <line x1="12" y1="38" x2="28" y2="38" />
      </g>
      <text x="932" y="551" font-family="monospace" font-size="24" fill="#303a36">nodeClassRef EC2NodeClass gpu</text>
    </g>

    <!-- Item 6: expireAfter 720h -->
    <g id="item-expire">
      <rect x="858" y="580" width="674" height="56" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(876, 589)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="20" cy="20" r="14" />
        <polyline points="20,12 20,20 26,20" />
      </g>
      <text x="932" y="617" font-family="monospace" font-size="24" fill="#303a36">expireAfter 720h</text>
    </g>

    <!-- Item 7: limits nvidia.com/gpu 64 (cap on total GPUs) -->
    <g id="item-limits">
      <rect x="858" y="646" width="674" height="78" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(876, 662)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <line x1="6" y1="34" x2="34" y2="34" />
        <line x1="20" y1="10" x2="20" y2="34" />
        <polyline points="10,16 20,10 30,16" />
      </g>
      <text x="932" y="678" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="932" dy="0" font-family="monospace">limits nvidia.com/gpu 64</tspan>
        <tspan x="932" dy="30">(cap on total GPUs)</tspan>
      </text>
    </g>

    <!-- Item 8: disruption consolidationPolicy WhenEmptyOrUnderutilized, consolidateAfter 10m, budgets nodes 10 percent -->
    <g id="item-disruption">
      <rect x="858" y="734" width="674" height="175" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(876, 755)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 32 18 A 12 12 0 1 0 34 26" />
        <polyline points="26,12 34,18 28,24" />
      </g>
      <text x="932" y="768" font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="932" dy="0">disruption consolidationPolicy</tspan>
        <tspan x="932" dy="34">WhenEmptyOrUnderutilized,</tspan>
        <tspan x="932" dy="34">consolidateAfter 10m,</tspan>
        <tspan x="932" dy="34">budgets nodes 10 percent</tspan>
      </text>
    </g>

    <!-- Item 9: Warning (orange #db8129) -->
    <g id="item-warning">
      <rect x="858" y="920" width="674" height="130" rx="12" fill="#fff5ea" stroke="#db8129" stroke-width="2.5" />
      <!-- Warning Triangle Icon (Orange #db8129) -->
      <g transform="translate(876, 946)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 20 6 L 36 34 H 4 Z" />
        <line x1="20" y1="16" x2="20" y2="24" />
        <circle cx="20" cy="29" r="1.5" fill="#db8129" stroke="none" />
      </g>
      <text x="932" y="964" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">
        <tspan x="932" dy="0">consolidation can remove a node under a</tspan>
        <tspan x="932" dy="34">training job: set do-not-disrupt</tspan>
      </text>
    </g>
  </g>
</svg>'''
    return svg

def audit(svg_str):
    root = ET.fromstring(svg_str)
    
    # 1. First children check: <title> and <desc>
    children = list(root)
    tag1 = children[0].tag.split('}')[-1]
    tag2 = children[1].tag.split('}')[-1]
    print(f"1. Children: <{tag1}>, <{tag2}>")
    assert tag1 == "title", "First child must be title"
    assert tag2 == "desc", "Second child must be desc"
    
    # 2. Dimensions
    w = root.get('width')
    vb = root.get('viewBox')
    h = root.get('height')
    print(f"2. Dimensions: width={w}, height={h}, viewBox={vb}")
    assert w == "1600"
    vb_parts = [float(x) for x in vb.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200
    assert int(h) == int(vb_parts[3])
    
    # 3. Check font-size >= 24 on all text and tspans
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = "".join(elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        fs = elem.attrib.get('font-size')
        assert fs is not None, f"Missing font-size on text '{full_text}'"
        fs_val = float(fs.replace('px', ''))
        assert fs_val >= 24, f"Text '{full_text}' font-size {fs_val} < 24!"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                tfs_val = float(tfs.replace('px', ''))
                assert tfs_val >= 24, f"tspan font-size {tfs_val} < 24 in '{full_text}'"
        text_elements.append((full_text, fs_val))

    print(f"\n3. Total text elements: {len(text_elements)} (all >= 24px)")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels
    expected_labels = [
        "Karpenter versus node groups, and the NodePool rules",
        "menu versus chef",
        "Cluster Autoscaler orders from a fixed menu of node groups, each with one shape",
        "Karpenter watches Pending pods, batches them, computes the best set of instance types that satisfy their constraints, and provisions just in time; bin-packing, spot handling with interruption notices, automatic rotation and drift correction",
        "annotated NodePool gpu-inference",
        "requirements instance-family In g6, g6e, p5",
        "capacity-type On-demand",
        "zones us-east-1a and us-east-1b",
        "taints nvidia.com/gpu=present NoSchedule (keeps ordinary pods off)",
        "nodeClassRef EC2NodeClass gpu",
        "expireAfter 720h",
        "limits nvidia.com/gpu 64 (cap on total GPUs)",
        "disruption consolidationPolicy WhenEmptyOrUnderutilized, consolidateAfter 10m, budgets nodes 10 percent",
        "consolidation can remove a node under a training job: set do-not-disrupt"
    ]

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")
    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in found_texts if t not in expected_labels]
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("\n6. Forbidden words check: PASS!")

    # 6. Check orange count
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check colors
    for c in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
        assert c in svg_str, f"Missing color {c}"
    print("8. Color palette check: PASS!")

    # 8. Check arrows
    arrows = [e for e in root.iter() if 'marker-end' in e.attrib]
    print(f"\n9. Total arrows: {len(arrows)}")
    assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"
    print("   Arrows count check: PASS (0 arrows, matches source)!")

    # 9. No external resources
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    print("10. External resources check: PASS!")

if __name__ == '__main__':
    svg = generate_svg()
    audit(svg)
    p = pathlib.Path("test_karpenter.svg")
    p.write_text(svg)
    print(f"\nWrote {p}")
