import xml.etree.ElementTree as ET
import re
import pathlib

H_CANVAS = 1160

# Column widths and coordinates:
# Margins: 40px left, 40px right -> Total width = 1520 px.
# Col 1 (Workload): x=40, w=420, end=460
# Col 2 (Pod scaling): x=476, w=490, end=966
# Col 3 (Node scaling): x=982, w=578, end=1560

rows_data = [
    {
        "id": "row-1",
        "h": 156,
        "c1": ["LLM online inference", "(vLLM, Triton, TGI)"],
        "c2": [
            "HPA or KEDA on queue depth,",
            "concurrency, KV-cache;",
            "min 1 to 2; slow scale-down"
        ],
        "c3": [
            "fixed reserved GPU pool plus burst",
            "autoscaled pool, overprovision",
            "pause pods, pre-pulled images;",
            "replica start 2 to 15 min"
        ],
        "orange": True,
        "icon": "chip"
    },
    {
        "id": "row-2",
        "h": 100,
        "c1": ["Embedding and", "reranker services"],
        "c2": [
            "HPA on CPU or GPU",
            "concurrency, smaller replicas"
        ],
        "c3": ["autoscaled L4 or L40S pool"],
        "orange": False,
        "icon": "layers"
    },
    {
        "id": "row-3",
        "h": 100,
        "c1": ["Batch inference"],
        "c2": [
            "KEDA on queue backlog,",
            "Jobs with parallelism"
        ],
        "c3": [
            "cluster autoscaler or Karpenter on",
            "Pending, spot allowed; scale to zero"
        ],
        "orange": False,
        "icon": "stack"
    },
    {
        "id": "row-4",
        "h": 130,
        "c1": ["Training"],
        "c2": [
            "not HPA-based, fixed job size,",
            "elastic training can scale",
            "workers within min and max"
        ],
        "c3": [
            "admit with Kueue, provision nodes",
            "atomically; scale events trigger",
            "rendezvous restarts"
        ],
        "orange": False,
        "icon": "cluster"
    },
    {
        "id": "row-5",
        "h": 100,
        "c1": ["Data processing", "(Spark, Ray)"],
        "c2": [
            "operator-driven dynamic",
            "allocation"
        ],
        "c3": [
            "Ray autoscaler talks to Kubernetes",
            "through KubeRay"
        ],
        "orange": False,
        "icon": "gear"
    },
    {
        "id": "row-6",
        "h": 100,
        "c1": ["Interactive", "notebooks"],
        "c2": ["none per user"],
        "c3": [
            "pool scaling plus idle culling,",
            "quotas cap spend"
        ],
        "orange": False,
        "icon": "window"
    },
    {
        "id": "row-7",
        "h": 90,
        "c1": ["Gateways and ingress"],
        "c2": ["HPA on CPU, RPS or connections"],
        "c3": ["keep at least 3 for HA"],
        "orange": False,
        "icon": "shield"
    }
]

y_header = 90
h_header = 58
gap_row = 12

row_positions = []
cur_y = y_header + h_header + 14
for r in rows_data:
    row_positions.append((r, cur_y))
    cur_y += r["h"] + gap_row

y_rule = cur_y + 10
h_rule = 92

# Generate SVG
svg_parts = []
svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H_CANVAS}" width="1600" height="{H_CANVAS}">')
svg_parts.append('  <title>Autoscaling patterns per AI workload</title>')
svg_parts.append('  <desc>Visual comparison table of Kubernetes autoscaling patterns across seven AI workloads showing pod scaling and node scaling choices followed by a multi-metric safety rule strip.</desc>')
svg_parts.append(f'  <rect width="1600" height="{H_CANVAS}" fill="#f5f8f5"/>')
svg_parts.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Autoscaling patterns per AI workload</text>')

# Table Column Headers
svg_parts.append('  <!-- ==================== TABLE COLUMN HEADERS ==================== -->')
svg_parts.append(f'  <rect x="40" y="{y_header}" width="1520" height="{h_header}" rx="10" fill="#207448"/>')
svg_parts.append(f'  <text x="250" y="{y_header + 39}" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Workload</text>')
svg_parts.append(f'  <text x="721" y="{y_header + 39}" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Pod scaling</text>')
svg_parts.append(f'  <text x="1271" y="{y_header + 39}" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Node scaling</text>')

def render_icon(icon_name, icon_y, is_orange):
    color = "#db8129" if is_orange else "#207448"
    bg = "#fff5ec" if is_orange else "#e8f1ea"
    if icon_name == "chip":
        return f'''<g transform="translate(56, {icon_y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="36" height="36" rx="6" fill="{bg}"/>
      <rect x="18" y="18" width="20" height="20" rx="3" fill="{color}"/>
      <line x1="18" y1="3" x2="18" y2="10"/>
      <line x1="28" y1="3" x2="28" y2="10"/>
      <line x1="38" y1="3" x2="38" y2="10"/>
      <line x1="18" y1="46" x2="18" y2="53"/>
      <line x1="28" y1="46" x2="28" y2="53"/>
      <line x1="38" y1="46" x2="38" y2="53"/>
      <line x1="3" y1="18" x2="10" y2="18"/>
      <line x1="3" y1="28" x2="10" y2="28"/>
      <line x1="3" y1="38" x2="10" y2="38"/>
      <line x1="46" y1="18" x2="53" y2="18"/>
      <line x1="46" y1="28" x2="53" y2="28"/>
      <line x1="46" y1="38" x2="53" y2="38"/>
    </g>'''
    elif icon_name == "layers":
        return f'''<g transform="translate(56, {icon_y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 50 17 L 28 28 L 6 17 Z" fill="{bg}"/>
      <path d="M 6 29 L 28 40 L 50 29"/>
      <path d="M 6 41 L 28 52 L 50 41"/>
    </g>'''
    elif icon_name == "stack":
        return f'''<g transform="translate(56, {icon_y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="12" rx="3" fill="{bg}"/>
      <rect x="8" y="23" width="40" height="12" rx="3" fill="{bg}"/>
      <rect x="8" y="38" width="40" height="12" rx="3" fill="{bg}"/>
      <line x1="16" y1="14" x2="26" y2="14"/>
      <line x1="16" y1="29" x2="26" y2="29"/>
      <line x1="16" y1="44" x2="26" y2="44"/>
    </g>'''
    elif icon_name == "cluster":
        return f'''<g transform="translate(56, {icon_y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="20" height="16" rx="3" fill="{bg}"/>
      <rect x="30" y="8" width="20" height="16" rx="3" fill="{bg}"/>
      <rect x="18" y="32" width="20" height="16" rx="3" fill="{bg}"/>
      <line x1="16" y1="24" x2="28" y2="32"/>
      <line x1="40" y1="24" x2="28" y2="32"/>
      <circle cx="16" cy="16" r="2" fill="{color}"/>
      <circle cx="40" cy="16" r="2" fill="{color}"/>
      <circle cx="28" cy="40" r="2" fill="{color}"/>
    </g>'''
    elif icon_name == "gear":
        return f'''<g transform="translate(56, {icon_y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="14" fill="{bg}"/>
      <circle cx="28" cy="28" r="5" fill="{color}"/>
      <line x1="28" y1="6" x2="28" y2="14"/>
      <line x1="28" y1="42" x2="28" y2="50"/>
      <line x1="6" y1="28" x2="14" y2="28"/>
      <line x1="42" y1="28" x2="50" y2="28"/>
      <line x1="12" y1="12" x2="18" y2="18"/>
      <line x1="38" y1="38" x2="44" y2="44"/>
      <line x1="12" y1="44" x2="18" y2="38"/>
      <line x1="38" y1="18" x2="44" y2="12"/>
    </g>'''
    elif icon_name == "window":
        return f'''<g transform="translate(56, {icon_y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="6" fill="{bg}"/>
      <line x1="6" y1="18" x2="50" y2="18" stroke-width="3"/>
      <circle cx="13" cy="13" r="1.5" fill="{color}"/>
      <circle cx="19" cy="13" r="1.5" fill="{color}"/>
      <path d="M 14 28 L 22 34 L 14 40" stroke-width="3.5"/>
      <line x1="26" y1="40" x2="36" y2="40" stroke-width="3.5"/>
    </g>'''
    elif icon_name == "shield":
        return f'''<g transform="translate(56, {icon_y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 28 C 48 40 28 50 28 50 C 28 50 8 40 8 28 V 14 Z" fill="{bg}"/>
      <path d="M 28 14 V 42"/>
      <path d="M 18 26 H 38"/>
    </g>'''

def calc_base_y(n_lines, fs, dy, box_y, box_h):
    text_h = (n_lines - 1) * dy + fs
    top_pad = (box_h - text_h) / 2
    return box_y + top_pad + 0.76 * fs

# Render Rows
for r, ry in row_positions:
    rh = r["h"]
    is_orange = r["orange"]
    border_color = "#db8129" if is_orange else "#207448"
    border_width = "3" if is_orange else "1.5"
    row_bg = "#ffffff"
    
    svg_parts.append(f'  <!-- ==================== {r["id"].upper()} ==================== -->')
    svg_parts.append(f'  <g id="{r["id"]}">' )
    # Row card
    svg_parts.append(f'    <rect x="40" y="{ry}" width="1520" height="{rh}" rx="12" fill="{row_bg}" stroke="{border_color}" stroke-width="{border_width}"/>')
    
    # Col 1: Workload panel (x=46, w=416, h=rh-12)
    # Using subtle panel fill
    c1_bg = "#fff5ec" if is_orange else "#e8f1ea"
    c1_stroke = "#db8129" if is_orange else "#207448"
    svg_parts.append(f'    <rect x="46" y="{ry + 6}" width="416" height="{rh - 12}" rx="8" fill="{c1_bg}" stroke="{c1_stroke}" stroke-width="1.2"/>')
    
    # Icon
    icon_y = ry + (rh - 56) // 2
    svg_parts.append(f'    {render_icon(r["icon"], icon_y, is_orange)}')
    
    # Col 1 Text
    c1_fs = 26 if len(r["c1"]) == 1 else 24
    c1_dy = 30
    c1_base_y = calc_base_y(len(r["c1"]), c1_fs, c1_dy, ry + 6, rh - 12)
    svg_parts.append(f'    <text x="124" y="{c1_base_y:.1f}" font-family="sans-serif" font-size="{c1_fs}" font-weight="bold" fill="#303a36">')
    for idx, line in enumerate(r["c1"]):
        dy_attr = f' dy="{c1_dy}"' if idx > 0 else ' dy="0"'
        svg_parts.append(f'      <tspan x="124"{dy_attr}>{line}</tspan>')
    svg_parts.append('    </text>')
    
    # Col 2: Pod scaling panel (x=472, w=496, h=rh-12)
    svg_parts.append(f'    <rect x="472" y="{ry + 6}" width="496" height="{rh - 12}" rx="8" fill="#fdfdfd" stroke="#c4d5c9" stroke-width="1"/>')
    c2_fs = 24
    c2_dy = 28
    c2_base_y = calc_base_y(len(r["c2"]), c2_fs, c2_dy, ry + 6, rh - 12)
    svg_parts.append(f'    <text x="492" y="{c2_base_y:.1f}" font-family="sans-serif" font-size="{c2_fs}" fill="#303a36">')
    for idx, line in enumerate(r["c2"]):
        dy_attr = f' dy="{c2_dy}"' if idx > 0 else ' dy="0"'
        svg_parts.append(f'      <tspan x="492"{dy_attr}>{line}</tspan>')
    svg_parts.append('    </text>')
    
    # Col 3: Node scaling panel (x=978, w=576, h=rh-12)
    svg_parts.append(f'    <rect x="978" y="{ry + 6}" width="576" height="{rh - 12}" rx="8" fill="#fdfdfd" stroke="#c4d5c9" stroke-width="1"/>')
    c3_fs = 24
    c3_dy = 28
    c3_base_y = calc_base_y(len(r["c3"]), c3_fs, c3_dy, ry + 6, rh - 12)
    svg_parts.append(f'    <text x="998" y="{c3_base_y:.1f}" font-family="sans-serif" font-size="{c3_fs}" fill="#303a36">')
    for idx, line in enumerate(r["c3"]):
        dy_attr = f' dy="{c3_dy}"' if idx > 0 else ' dy="0"'
        svg_parts.append(f'      <tspan x="998"{dy_attr}>{line}</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

# Rule Strip at bottom
rule_lines = [
    "multi-metric safety: scale up on queue depth OR latency,",
    "scale down only when both are low over a long window"
]
rule_fs = 24
rule_dy = 30
rule_base_y = calc_base_y(len(rule_lines), rule_fs, rule_dy, y_rule, h_rule)

svg_parts.append('  <!-- ==================== RULE STRIP ==================== -->')
svg_parts.append('  <g id="rule-strip">')
svg_parts.append(f'    <rect x="40" y="{y_rule}" width="1520" height="{h_rule}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
svg_parts.append(f'    <text x="800" y="{rule_base_y:.1f}" text-anchor="middle" font-family="sans-serif" font-size="{rule_fs}" font-weight="bold" fill="#207448">')
for idx, line in enumerate(rule_lines):
    dy_attr = f' dy="{rule_dy}"' if idx > 0 else ' dy="0"'
    svg_parts.append(f'      <tspan x="800"{dy_attr}>{line}</tspan>')
svg_parts.append('    </text>')
svg_parts.append('  </g>')

svg_parts.append('</svg>')

svg_content = "\n".join(svg_parts)
pathlib.Path("test_autoscaling_patterns.svg").write_text(svg_content)
print("Generated test_autoscaling_patterns.svg successfully!")
