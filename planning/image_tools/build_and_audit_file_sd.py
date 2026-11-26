#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Two rendered outputs: Prometheus file_sd targets and YAML from data</title>
  <desc>Visual comparison showing how Jinja2 filter pipelines build Prometheus file-based service discovery targets and valid formatted Kubernetes YAML without fragile manual indentation.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 1 2 L 16 9 L 1 16 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title (48px bold, wrapped into 2 tspans for conservative width compliance) -->
  <text x="800" y="50" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Two rendered outputs: Prometheus file_sd targets</tspan>
    <tspan x="800" dy="54">and YAML from data</tspan>
  </text>

  <!-- ==================== LEFT PANEL: Prometheus file_sd targets ==================== -->
  <g id="panel-file-sd">
    <!-- Panel Container -->
    <rect x="40" y="145" width="740" height="945" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Panel Header Icon (Radar / Target, 56x56, stroke 4, green) -->
    <g transform="translate(68, 162)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="24" />
      <circle cx="28" cy="28" r="14" stroke-width="3" />
      <circle cx="28" cy="28" r="4" fill="#207448" />
      <line x1="28" y1="4" x2="28" y2="52" />
      <line x1="4" y1="28" x2="52" y2="28" />
    </g>

    <!-- Panel Title -->
    <text x="142" y="200" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Prometheus file_sd targets</text>

    <!-- Pipeline Step 1: groups[gpu] -->
    <rect x="75" y="236" width="670" height="54" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="410" y="271" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">groups[gpu]</text>

    <!-- Arrow 1: Step 1 -> Step 2 -->
    <line x1="410" y1="290" x2="410" y2="314" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

    <!-- Pipeline Step 2: map(extract, hostvars, ansible_host) -->
    <rect x="75" y="314" width="670" height="54" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="410" y="349" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">map(extract, hostvars, ansible_host)</text>

    <!-- Arrow 2: Step 2 -> Step 3 -->
    <line x1="410" y1="368" x2="410" y2="392" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

    <!-- Pipeline Step 3: map(regex_replace, $, :9400) appends port 9400, where the DCGM exporter listens for GPU metrics -->
    <rect x="75" y="392" width="670" height="124" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="410" y="428" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="410" dy="0" font-family="monospace" font-weight="bold">map(regex_replace, $, :9400)</tspan>
      <tspan x="410" dy="32">appends port 9400, where the DCGM exporter</tspan>
      <tspan x="410" dy="32">listens for GPU metrics</tspan>
    </text>

    <!-- Arrow 3: Step 3 -> Step 4 -->
    <line x1="410" y1="516" x2="410" y2="540" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

    <!-- Pipeline Step 4: list -->
    <rect x="75" y="540" width="670" height="54" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="410" y="575" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">list</text>

    <!-- Arrow 4: Step 4 -> Container (targets) -->
    <line x1="410" y1="594" x2="410" y2="618" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

    <!-- Pipeline Step 5: Container wrapping 'targets' with 'labels: job dcgm, cluster {{ cluster_name }}' -->
    <rect x="75" y="618" width="670" height="152" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    
    <!-- targets key -->
    <rect x="95" y="626" width="630" height="50" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <text x="410" y="659" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">targets</text>

    <!-- labels item -->
    <rect x="95" y="682" width="630" height="80" rx="6" fill="#f5f8f5" stroke="#b8d5c4" stroke-width="1.5" />
    <text x="410" y="716" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="410" dy="0">labels: job dcgm,</tspan>
      <tspan x="410" dy="30">cluster {{ cluster_name }}</tspan>
    </text>

    <!-- Arrow 5: Container -> Step 6 (to_nice_json) -->
    <line x1="410" y1="770" x2="410" y2="794" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

    <!-- Pipeline Step 6: to_nice_json -->
    <rect x="75" y="794" width="670" height="54" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="410" y="829" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">to_nice_json</text>

    <!-- Note Card at bottom of Panel 1 -->
    <rect x="75" y="876" width="670" height="190" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    
    <!-- Note Icon (Clock / Refresh Schedule, 36x36, stroke 3, green, placed centered at top) -->
    <g transform="translate(392, 888)" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="18" cy="18" r="14" />
      <polyline points="18 9 18 18 25 18" />
    </g>

    <!-- Note Text -->
    <text x="410" y="946" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="410" dy="0">file_sd means file-based service</tspan>
      <tspan x="410" dy="32">discovery: Prometheus re-reads the file</tspan>
      <tspan x="410" dy="32">on its own schedule, so a new node added</tspan>
      <tspan x="410" dy="32">to the file is scraped without a restart</tspan>
    </text>
  </g>

  <!-- ==================== RIGHT PANEL: YAML from data ==================== -->
  <g id="panel-yaml">
    <!-- Panel Container -->
    <rect x="820" y="145" width="740" height="945" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Panel Header Icon (Document / Structured YAML, 56x56, stroke 4, green) -->
    <g transform="translate(848, 162)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 6 L 36 6 L 46 16 L 46 50 L 10 50 Z" />
      <polyline points="36 6 36 16 46 16" />
      <line x1="18" y1="26" x2="38" y2="26" stroke-width="3" />
      <line x1="24" y1="34" x2="38" y2="34" stroke-width="3" />
      <line x1="24" y1="42" x2="38" y2="42" stroke-width="3" />
    </g>

    <!-- Panel Title -->
    <text x="922" y="200" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">YAML from data</text>

    <!-- Card 1: Key Item (Orange) - {{ k8s_values | to_nice_yaml(indent=2) | indent(4) }} -->
    <rect x="855" y="240" width="670" height="150" rx="10" fill="#fff9f2" stroke="#db8129" stroke-width="3" />
    
    <!-- Code Brackets Icon (Orange, 36x36, stroke 3, centered at top) -->
    <g transform="translate(1172, 252)" fill="none" stroke="#db8129" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="12 8 4 18 12 28" />
      <polyline points="24 8 32 18 24 28" />
      <line x1="20" y1="6" x2="16" y2="30" />
    </g>

    <text x="1190" y="322" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#db8129">
      <tspan x="1190" dy="0">{{ k8s_values | to_nice_yaml(indent=2)</tspan>
      <tspan x="1190" dy="42">| indent(4) }}</tspan>
    </text>

    <!-- Card 2: Fragile explanation -->
    <rect x="855" y="415" width="670" height="350" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    
    <!-- Shield / Stability Icon (56x56, stroke 4, green, centered at top) -->
    <g transform="translate(1162, 430)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 L 48 28 C 48 40 28 50 28 50 C 28 50 8 40 8 28 L 8 14 Z" />
      <line x1="28" y1="18" x2="28" y2="30" />
      <circle cx="28" cy="38" r="2" fill="#207448" />
    </g>

    <text x="1190" y="522" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1190" dy="0">hand-indented YAML is fragile, one space</tspan>
      <tspan x="1190" dy="34">in the wrong place changes the meaning</tspan>
      <tspan x="1190" dy="34">of the whole file; to_nice_yaml builds</tspan>
      <tspan x="1190" dy="34">the structure correctly every time and</tspan>
      <tspan x="1190" dy="34">indent(4) moves the block to the right</tspan>
      <tspan x="1190" dy="34">depth inside the surrounding template</tspan>
    </text>

    <!-- Card 3: Validation step -->
    <rect x="855" y="795" width="670" height="271" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    
    <!-- Checkmark Badge Icon (56x56, stroke 4, green, centered at top) -->
    <g transform="translate(1162, 815)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="18 28 25 35 38 20" />
    </g>

    <text x="1190" y="920" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1190" dy="0">then validate with yamllint or</tspan>
      <tspan x="1190" dy="36">kubeconform so a mistake is caught</tspan>
      <tspan x="1190" dy="36">before it reaches a cluster</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1115" width="1520" height="60" rx="10" fill="#207448" />
    <text x="800" y="1154" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Let filters build the structure, validate the result</text>
  </g>
</svg>
'''

with open('candidate_file_sd.svg', 'w') as f:
    f.write(svg_content)

print("Updated candidate_file_sd.svg!")
