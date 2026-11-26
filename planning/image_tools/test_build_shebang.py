import xml.etree.ElementTree as ET
import re
import subprocess

def build_svg():
    H = 1030
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">
  <title>The same #!/bin/sh line runs different shells on different distributions</title>
  <desc>Visual infographic explaining how the same shebang line #!/bin/sh executes dash on Debian and Ubuntu causing bashisms to fail, while executing bash in POSIX mode on RHEL where bash extensions still work.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="{H}" fill="#f5f8f5"/>

  <!-- Diagram Title -->
  <text x="800" y="56" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">The same <tspan font-family="monospace">#!/bin/sh</tspan> line runs different shells</tspan>
    <tspan x="800" dy="58">on different distributions</tspan>
  </text>

  <!-- ==================== LEFT PANEL: Debian and Ubuntu ==================== -->
  <g id="panel-debian-ubuntu">
    <rect x="60" y="165" width="710" height="520" rx="18" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="415" y="212" text-anchor="middle" font-family="sans-serif" font-size="34" font-weight="bold" fill="#207448">Debian and Ubuntu</text>

    <!-- Top Box: Script starts with #!/bin/sh -->
    <rect x="90" y="240" width="650" height="84" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- File icon (56px) -->
    <g transform="translate(116, 254)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 4 L 32 4 L 46 18 L 46 52 L 6 52 Z"/>
      <path d="M 32 4 L 32 18 L 46 18"/>
      <line x1="14" y1="28" x2="38" y2="28"/>
      <line x1="14" y1="38" x2="30" y2="38"/>
    </g>
    <text x="188" y="293" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan font-family="sans-serif">Script starts with </tspan><tspan font-family="monospace">#!/bin/sh</tspan>
    </text>

    <!-- Arrow down to Box 2 -->
    <line x1="415" y1="324" x2="415" y2="368" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

    <!-- Middle Box: /bin/sh is dash -->
    <rect x="90" y="370" width="650" height="84" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Terminal icon (56px) -->
    <g transform="translate(116, 384)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="42" rx="6"/>
      <polyline points="14,22 24,27 14,32"/>
      <line x1="28" y1="32" x2="40" y2="32"/>
    </g>
    <text x="188" y="423" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan font-family="monospace">/bin/sh</tspan><tspan font-family="sans-serif"> is </tspan><tspan font-family="monospace">dash</tspan>
    </text>

    <!-- Connecting line with no arrowhead (grouped together) -->
    <line x1="415" y1="454" x2="415" y2="495" stroke="#207448" stroke-width="3" stroke-dasharray="6 6"/>

    <!-- Bottom Box: Small POSIX shell... -->
    <rect x="90" y="495" width="650" height="165" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="116" y="534" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="116" dy="0">Small POSIX shell: no <tspan font-family="monospace">[[ ]]</tspan>, arrays,</tspan>
      <tspan x="116" dy="32"><tspan font-family="monospace">${{var//x/y}}</tspan> or process substitution</tspan>
    </text>
    <!-- Red-outline cross labelled bashisms fail -->
    <rect x="116" y="594" width="230" height="46" rx="8" fill="#fdf2f2" stroke="#d32f2f" stroke-width="2"/>
    <g transform="translate(126, 603)" fill="none" stroke="#d32f2f" stroke-width="2.5" stroke-linecap="round">
      <circle cx="14" cy="14" r="12" fill="#ffffff"/>
      <line x1="9" y1="9" x2="19" y2="19"/>
      <line x1="19" y1="9" x2="9" y2="19"/>
    </g>
    <text x="164" y="626" font-family="sans-serif" font-size="24" font-weight="bold" fill="#d32f2f">bashisms fail</text>
  </g>

  <!-- ==================== RIGHT PANEL: RHEL family ==================== -->
  <g id="panel-rhel">
    <rect x="830" y="165" width="710" height="520" rx="18" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="1185" y="212" text-anchor="middle" font-family="sans-serif" font-size="34" font-weight="bold" fill="#207448">RHEL family</text>

    <!-- Top Box: Script starts with #!/bin/sh -->
    <rect x="860" y="240" width="650" height="84" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- File icon (56px) -->
    <g transform="translate(886, 254)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 4 L 32 4 L 46 18 L 46 52 L 6 52 Z"/>
      <path d="M 32 4 L 32 18 L 46 18"/>
      <line x1="14" y1="28" x2="38" y2="28"/>
      <line x1="14" y1="38" x2="30" y2="38"/>
    </g>
    <text x="958" y="293" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan font-family="sans-serif">Script starts with </tspan><tspan font-family="monospace">#!/bin/sh</tspan>
    </text>

    <!-- Arrow to Box 2 -->
    <line x1="1185" y1="324" x2="1185" y2="368" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

    <!-- Middle Box: /bin/sh is bash in POSIX mode -->
    <rect x="860" y="370" width="650" height="84" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Terminal icon (56px) -->
    <g transform="translate(886, 384)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="42" rx="6"/>
      <polyline points="14,22 24,27 14,32"/>
      <line x1="28" y1="32" x2="40" y2="32"/>
    </g>
    <text x="958" y="423" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan font-family="monospace">/bin/sh</tspan><tspan font-family="sans-serif"> is </tspan><tspan font-family="monospace">bash</tspan><tspan font-family="sans-serif"> in POSIX mode</tspan>
    </text>

    <!-- Connecting line with no arrowhead (grouped together) -->
    <line x1="1185" y1="454" x2="1185" y2="495" stroke="#207448" stroke-width="3" stroke-dasharray="6 6"/>

    <!-- Bottom Box: bash extensions still work with a tick -->
    <rect x="860" y="495" width="650" height="165" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Tick icon -->
    <g transform="translate(900, 552)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="24" cy="24" r="22" fill="#e8f1ea"/>
      <polyline points="14,24 21,31 34,17" stroke-width="4"/>
    </g>
    <text x="970" y="586" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">bash extensions still work</text>
  </g>

  <!-- ==================== SHARED RULE BOX (Orange Outline) ==================== -->
  <g id="rule-box">
    <rect x="60" y="725" width="1480" height="90" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3"/>
    <text x="800" y="780" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">
      <tspan font-family="sans-serif">Rule: if you use any bash feature, write </tspan><tspan font-family="monospace">#!/usr/bin/env bash</tspan><tspan font-family="sans-serif"> or </tspan><tspan font-family="monospace">#!/bin/bash</tspan><tspan font-family="sans-serif">.</tspan>
    </text>
  </g>

  <!-- Small note under the rule -->
  <text x="800" y="855" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan font-family="sans-serif">If you write </tspan><tspan font-family="monospace">#!/bin/sh</tspan><tspan font-family="sans-serif">, keep to POSIX and test with </tspan><tspan font-family="monospace">dash</tspan><tspan font-family="sans-serif">.</tspan>
  </text>

  <!-- Caption / Green takeaway bar -->
  <g id="caption-bar">
    <rect x="60" y="900" width="1480" height="65" rx="12" fill="#207448"/>
    <text x="800" y="942" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Same shebang, different shell, so the script fails on one family only.</text>
  </g>
</svg>"""
    return svg

if __name__ == "__main__":
    s = build_svg()
    with open("test_shebang.svg", "w") as f:
        f.write(s)
    print("Wrote test_shebang.svg")
