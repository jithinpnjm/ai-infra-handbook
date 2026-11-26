#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1150" width="1600" height="1150">
  <title>Route by the endpoint's region, never by nearest</title>
  <desc>Visual infographic explaining regional routing versus nearest routing for data residency, showing prompt and log containment in the EU region and striping of metering data.</desc>

  <defs>
    <!-- Green arrow marker (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
    <!-- Red arrow marker (18px) -->
    <marker id="arrow-red" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#c53030" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1150" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="88" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Route by the endpoint's region, never by nearest</text>

  <!-- ==================== GLOBAL BAND ==================== -->
  <g id="control-plane-band">
    <rect x="60" y="138" width="1480" height="76" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Global / Network Icon (56px) -->
    <g transform="translate(85, 148)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <ellipse cx="28" cy="28" rx="10" ry="22" />
      <line x1="6" y1="28" x2="50" y2="28" />
      <path d="M 12 14 Q 28 20 44 14" />
      <path d="M 12 42 Q 28 36 44 42" />
    </g>
    <text x="160" y="186" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">Control plane: metadata only, global</text>
  </g>

  <!-- ==================== EUROPEAN CUSTOMER ==================== -->
  <g id="node-customer">
    <rect x="60" y="264" width="425" height="94" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Person Icon (56px) -->
    <g transform="translate(85, 283)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="16" r="12" />
      <path d="M 8 48 C 8 36 17 34 28 34 C 39 34 48 36 48 48" />
    </g>
    <text x="160" y="323" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">European customer</text>
  </g>

  <!-- ==================== GREEN ARROW (ROUTED BY ENDPOINT REGION) ==================== -->
  <line x1="250" y1="358" x2="250" y2="448" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />
  <text x="280" y="410" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">Routed by endpoint region</text>

  <!-- ==================== RED DASHED ARROW (NEAREST REGION) ==================== -->
  <line x1="485" y1="311" x2="1117" y2="311" stroke="#c53030" stroke-width="4" stroke-dasharray="10 8" marker-end="url(#arrow-red)" />
  <text x="750" y="258" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#c53030">
    <tspan x="750" dy="0">Nearest region: breaks the promise</tspan>
    <tspan x="750" dy="32">without an error</tspan>
  </text>

  <!-- Red Cross with Orange Outline -->
  <g id="red-cross" transform="translate(1070, 311)">
    <!-- Circle badge with orange outline -->
    <circle cx="0" cy="0" r="26" fill="#ffffff" stroke="#db8129" stroke-width="4" />
    <!-- Red cross -->
    <line x1="-12" y1="-12" x2="12" y2="12" stroke="#c53030" stroke-width="5" stroke-linecap="round" />
    <line x1="12" y1="-12" x2="-12" y2="12" stroke="#c53030" stroke-width="5" stroke-linecap="round" />
  </g>

  <!-- ==================== US REGION PANEL ==================== -->
  <g id="panel-us-region">
    <rect x="1135" y="264" width="405" height="400" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Datacenter / Cloud Icon (56px) -->
    <g transform="translate(1160, 289)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="4" />
      <line x1="6" y1="22" x2="50" y2="22" />
      <line x1="6" y1="34" x2="50" y2="34" />
      <circle cx="16" cy="15" r="2" fill="#207448" stroke="none" />
      <circle cx="16" cy="28" r="2" fill="#207448" stroke="none" />
      <circle cx="16" cy="41" r="2" fill="#207448" stroke="none" />
    </g>
    <text x="1235" y="327" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="#207448">US region</text>
  </g>

  <!-- ==================== EU REGION PANEL ==================== -->
  <g id="panel-eu-region">
    <rect x="60" y="450" width="960" height="545" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    
    <!-- Region / Map Pin Icon (56px) -->
    <g transform="translate(85, 472)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="22" r="14" />
      <path d="M 28 36 L 28 50" />
      <circle cx="28" cy="22" r="4" fill="#207448" stroke="none" />
    </g>
    <text x="155" y="510" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="#207448">EU region (promised region)</text>

    <!-- Inside EU Panel: 1. Gateway Box -->
    <g id="box-gateway">
      <rect x="90" y="545" width="430" height="185" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Gateway / Portal Icon (56px) -->
      <g transform="translate(115, 575)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="10" width="44" height="38" rx="6" />
        <path d="M 18 48 V 26 H 38 V 48" />
        <circle cx="33" cy="37" r="2" fill="#207448" stroke="none" />
        <path d="M 28 10 V 4" />
      </g>
      <text x="190" y="615" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">Gateway</text>
    </g>

    <!-- Inside EU Panel: 2. Replica Group -->
    <g id="box-replica-group">
      <rect x="560" y="545" width="430" height="185" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Chip / Replica Group Icon (56px) -->
      <g transform="translate(585, 575)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="10" y="10" width="36" height="36" rx="4" />
        <rect x="18" y="18" width="20" height="20" rx="2" />
        <line x1="18" y1="4" x2="18" y2="10" />
        <line x1="28" y1="4" x2="28" y2="10" />
        <line x1="38" y1="4" x2="38" y2="10" />
        <line x1="18" y1="46" x2="18" y2="52" />
        <line x1="28" y1="46" x2="28" y2="52" />
        <line x1="38" y1="46" x2="38" y2="52" />
        <line x1="4" y1="18" x2="10" y2="18" />
        <line x1="4" y1="28" x2="10" y2="28" />
        <line x1="4" y1="38" x2="10" y2="38" />
        <line x1="46" y1="18" x2="52" y2="18" />
        <line x1="46" y1="28" x2="52" y2="28" />
        <line x1="46" y1="38" x2="52" y2="38" />
      </g>
      <text x="660" y="615" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">Replica group</text>
    </g>

    <!-- Inside EU Panel: 3. Log Store -->
    <g id="box-log-store">
      <rect x="90" y="765" width="430" height="200" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Green Lock Icon (56px) -->
      <g transform="translate(115, 785)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="10" y="20" width="36" height="28" rx="4" />
        <path d="M 18 20 V 12 A 10 10 0 0 1 38 12 V 20" />
        <circle cx="28" cy="32" r="3" fill="#207448" stroke="none" />
        <path d="M 28 35 V 40" />
      </g>
      <text x="190" y="825" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">Log store</text>
      <!-- Label with green lock icon -->
      <text x="115" y="885" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
        <tspan x="115" dy="0">Prompts, completions and</tspan>
        <tspan x="115" dy="34">logs stay in region</tspan>
      </text>
    </g>

    <!-- Inside EU Panel: 4. Metering Box -->
    <g id="box-metering">
      <rect x="560" y="765" width="430" height="200" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Gauge / Counter Icon (56px) -->
      <g transform="translate(585, 785)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="8" y="10" width="40" height="36" rx="4" />
        <path d="M 16 36 A 14 14 0 0 1 40 36" />
        <line x1="28" y1="36" x2="35" y2="24" />
        <circle cx="28" cy="36" r="2.5" fill="#207448" stroke="none" />
      </g>
      <text x="660" y="825" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">Metering</text>
    </g>
  </g>

  <!-- ==================== DASHED LINE LEAVING EU PANEL ==================== -->
  <line x1="990" y1="905" x2="1160" y2="905" stroke="#207448" stroke-width="4" stroke-dasharray="10 8" marker-end="url(#arrow-green)" />
  <text x="1045" y="840" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="1045" dy="0">Metering events leave only</tspan>
    <tspan x="1045" dy="32">after content is stripped</tspan>
  </text>

  <!-- ==================== BOTTOM NOTE TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="60" y="1035" width="1480" height="74" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <text x="800" y="1081" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">Cross-region failover is off by default for residency-bound tenants.</text>
  </g>
</svg>
'''

with open("test_candidate.svg", "w") as f:
    f.write(svg_code.strip())

print("Wrote updated test_candidate.svg")
