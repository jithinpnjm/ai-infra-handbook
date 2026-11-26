#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

def build_svg():
    H = 1200
    
    # Coordinates:
    # Canvas: 1600 x 1200
    # Left margin: 40, Right margin: 40 (1600 - 1560)
    # Left panel: x=40, y=140, w=740, h=1020
    # Panel gap: 40 (780 to 820)
    # Right panel: x=820, y=140, w=740, h=1020
    # Bottom margin: 1200 - 1160 = 40
    
    # Cards inside panels:
    # Left cards: x=64, w=692 (right edge = 756, panel pad = 24)
    # Right cards: x=844, w=692 (right edge = 1536, panel pad = 24)
    
    # Left Card 1: y=216, h=210
    # Left Card 2: y=456, h=678
    
    # Right Cards:
    # Item 1 (requirements): ry=216, rh=98, ty=259, icon_y=245
    # Item 2 (capacity-type): ry=324, rh=68, ty=368, icon_y=336
    # Item 3 (zones): ry=402, rh=68, ty=446, icon_y=414
    # Item 4 (taints): ry=480, rh=98, ty=523, icon_y=509
    # Item 5 (nodeClassRef): ry=588, rh=68, ty=632, icon_y=600
    # Item 6 (expireAfter): ry=666, rh=68, ty=710, icon_y=678
    # Item 7 (limits): ry=744, rh=98, ty=787, icon_y=773
    # Item 8 (disruption): ry=852, rh=166, ty=897, icon_y=913
    # Item 9 (warning): ry=1028, rh=108, ty=1074, icon_y=1060
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">
  <title>Karpenter versus node groups, and the NodePool rules</title>
  <desc>Technical infographic comparing Cluster Autoscaler fixed node group menu versus Karpenter just-in-time chef provisioning, beside an annotated Karpenter NodePool manifest for gpu-inference with requirements, taints, limits, and disruption policies.</desc>

  <!-- Background -->
  <rect width="1600" height="{H}" fill="#f5f8f5" />

  <!-- Diagram Title (48px bold, split on 2 lines, &lt;= 40 chars/line) -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Karpenter versus node groups,</tspan>
    <tspan x="800" dy="54">and the NodePool rules</tspan>
  </text>

  <!-- ==================== LEFT PANEL: menu versus chef ==================== -->
  <g id="left-panel">
    <!-- Panel Container -->
    <rect x="40" y="140" width="740" height="1020" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Left Panel Header Icon: Chef Hat (56px) -->
    <g transform="translate(68, 150)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 44 h 36 v 8 h -36 z" />
      <path d="M 12 44 c -8 -4 -8 -16 0 -22 c -4 -10 6 -18 16 -14 c 6 -8 18 -8 24 0 c 10 -4 20 4 16 14 c 8 6 8 18 0 22" />
      <line x1="18" y1="48" x2="38" y2="48" stroke-width="2.5" />
    </g>

    <!-- Left Panel Title (32px bold) -->
    <text x="144" y="188" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">menu versus chef</text>

    <!-- Card 1: Cluster Autoscaler (Fixed Menu) -->
    <g id="ca-card">
      <rect x="64" y="216" width="692" height="210" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
      
      <!-- Icon: Fixed Menu / Grid (56px) -->
      <g transform="translate(86, 293)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="48" height="44" rx="4" />
        <line x1="4" y1="18" x2="52" y2="18" />
        <line x1="16" y1="26" x2="40" y2="26" />
        <line x1="16" y1="34" x2="40" y2="34" />
        <line x1="16" y1="42" x2="30" y2="42" />
        <circle cx="10" cy="12" r="2" fill="#207448" />
        <circle cx="16" cy="12" r="2" fill="#207448" />
      </g>

      <!-- Label 3: Cluster Autoscaler description -->
      <text x="160" y="285" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="160" dy="0">Cluster Autoscaler orders from a fixed</tspan>
        <tspan x="160" dy="42">menu of node groups, each with one</tspan>
        <tspan x="160" dy="42">shape</tspan>
      </text>
    </g>

    <!-- Card 2: Karpenter (Chef / Just-In-Time) -->
    <g id="karpenter-card">
      <rect x="64" y="456" width="692" height="678" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />

      <!-- Icon: Smart Batching / Engine (56px) -->
      <g transform="translate(86, 767)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="14" />
        <path d="M 28 6 v 8 M 28 42 v 8 M 6 28 h 8 M 42 28 h 8 M 12 12 l 6 6 M 38 38 l 6 6 M 12 44 l 6 -6 M 38 18 l 6 -6" />
        <circle cx="28" cy="28" r="5" fill="#207448" />
      </g>

      <!-- Label 4: Karpenter description -->
      <text x="160" y="605" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="160" dy="0">Karpenter watches Pending pods,</tspan>
        <tspan x="160" dy="54">batches them, computes the best set of</tspan>
        <tspan x="160" dy="54">instance types that satisfy their</tspan>
        <tspan x="160" dy="54">constraints, and provisions just in</tspan>
        <tspan x="160" dy="54">time; bin-packing, spot handling with</tspan>
        <tspan x="160" dy="54">interruption notices, automatic</tspan>
        <tspan x="160" dy="54">rotation and drift correction</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== RIGHT PANEL: annotated NodePool gpu-inference ==================== -->
  <g id="right-panel">
    <!-- Panel Container -->
    <rect x="820" y="140" width="740" height="1020" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Right Panel Header Icon: Manifest / NodePool (56px) -->
    <g transform="translate(848, 150)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="6" width="40" height="44" rx="5" />
      <path d="M 18 18 h 20 M 18 26 h 20 M 18 34 h 12" />
      <circle cx="14" cy="18" r="1.5" fill="#207448" />
      <circle cx="14" cy="26" r="1.5" fill="#207448" />
      <circle cx="14" cy="34" r="1.5" fill="#207448" />
    </g>

    <!-- Right Panel Title: annotated NodePool gpu-inference (30px bold) -->
    <text x="922" y="188" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">annotated NodePool gpu-inference</text>

    <!-- Item 1: requirements instance-family In g6, g6e, p5 -->
    <g id="item-requirements">
      <rect x="844" y="216" width="692" height="98" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(862, 245)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="34" height="32" rx="4" />
        <line x1="4" y1="16" x2="38" y2="16" />
        <circle cx="12" cy="26" r="2" fill="#207448" />
        <circle cx="21" cy="26" r="2" fill="#207448" />
        <circle cx="30" cy="26" r="2" fill="#207448" />
      </g>
      <text x="922" y="259" font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="922" dy="0">requirements instance-family</tspan>
        <tspan x="922" dy="32">In g6, g6e, p5</tspan>
      </text>
    </g>

    <!-- Item 2: capacity-type On-demand -->
    <g id="item-capacity">
      <rect x="844" y="324" width="692" height="68" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(862, 336)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="21" cy="22" r="15" />
        <polyline points="15,22 19,26 28,17" />
      </g>
      <text x="922" y="368" font-family="monospace" font-size="24" fill="#303a36">capacity-type On-demand</text>
    </g>

    <!-- Item 3: zones us-east-1a and us-east-1b -->
    <g id="item-zones">
      <rect x="844" y="402" width="692" height="68" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(862, 414)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="15" cy="22" r="9" />
        <circle cx="27" cy="22" r="9" />
      </g>
      <text x="922" y="446" font-family="monospace" font-size="24" fill="#303a36">zones us-east-1a and us-east-1b</text>
    </g>

    <!-- Item 4: taints nvidia.com/gpu=present NoSchedule (keeps ordinary pods off) -->
    <g id="item-taints">
      <rect x="844" y="480" width="692" height="98" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(862, 509)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 21 6 L 36 12 V 25 C 36 34 21 40 21 40 C 21 40 6 34 6 25 V 12 Z" />
        <line x1="15" y1="23" x2="27" y2="23" />
      </g>
      <text x="922" y="523" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="922" dy="0" font-family="monospace">taints nvidia.com/gpu=present</tspan>
        <tspan x="922" dy="32">NoSchedule (keeps ordinary pods off)</tspan>
      </text>
    </g>

    <!-- Item 5: nodeClassRef EC2NodeClass gpu -->
    <g id="item-nodeclass">
      <rect x="844" y="588" width="692" height="68" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(862, 600)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="30" height="26" rx="3" />
        <line x1="6" y1="17" x2="36" y2="17" />
        <line x1="21" y1="34" x2="21" y2="40" />
        <line x1="12" y1="40" x2="30" y2="40" />
      </g>
      <text x="922" y="632" font-family="monospace" font-size="24" fill="#303a36">nodeClassRef EC2NodeClass gpu</text>
    </g>

    <!-- Item 6: expireAfter 720h -->
    <g id="item-expire">
      <rect x="844" y="666" width="692" height="68" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(862, 678)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="21" cy="22" r="15" />
        <polyline points="21,13 21,22 28,22" />
      </g>
      <text x="922" y="710" font-family="monospace" font-size="24" fill="#303a36">expireAfter 720h</text>
    </g>

    <!-- Item 7: limits nvidia.com/gpu 64 (cap on total GPUs) -->
    <g id="item-limits">
      <rect x="844" y="744" width="692" height="98" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(862, 773)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <line x1="6" y1="36" x2="36" y2="36" />
        <line x1="21" y1="10" x2="21" y2="36" />
        <polyline points="10,17 21,10 32,17" />
      </g>
      <text x="922" y="787" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="922" dy="0" font-family="monospace">limits nvidia.com/gpu 64</tspan>
        <tspan x="922" dy="32">(cap on total GPUs)</tspan>
      </text>
    </g>

    <!-- Item 8: disruption consolidationPolicy WhenEmptyOrUnderutilized, consolidateAfter 10m, budgets nodes 10 percent -->
    <g id="item-disruption">
      <rect x="844" y="852" width="692" height="166" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
      <g transform="translate(862, 913)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 34 18 A 14 14 0 1 0 36 28" />
        <polyline points="28,11 36,18 29,25" />
      </g>
      <text x="922" y="897" font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="922" dy="0">disruption consolidationPolicy</tspan>
        <tspan x="922" dy="32">WhenEmptyOrUnderutilized,</tspan>
        <tspan x="922" dy="32">consolidateAfter 10m,</tspan>
        <tspan x="922" dy="32">budgets nodes 10 percent</tspan>
      </text>
    </g>

    <!-- Item 9: Warning (orange #db8129) -->
    <g id="item-warning">
      <rect x="844" y="1028" width="692" height="108" rx="12" fill="#fff5ea" stroke="#db8129" stroke-width="2.5" />
      <!-- Warning Triangle Icon (Orange #db8129) -->
      <g transform="translate(862, 1060)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 21 6 L 38 38 H 4 Z" />
        <line x1="21" y1="18" x2="21" y2="27" />
        <circle cx="21" cy="33" r="1.5" fill="#db8129" stroke="none" />
      </g>
      <text x="922" y="1074" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">
        <tspan x="922" dy="0">consolidation can remove a node under a</tspan>
        <tspan x="922" dy="34">training job: set do-not-disrupt</tspan>
      </text>
    </g>
  </g>
</svg>'''
    return svg

if __name__ == '__main__':
    svg = build_svg()
    pathlib.Path("test_karpenter_perfect.svg").write_text(svg)
    print("Generated test_karpenter_perfect.svg")
