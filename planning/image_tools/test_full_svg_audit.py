#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1060" width="1600" height="1060">
  <title>The six-step estimation chain from weights to GPUs</title>
  <desc>Visual infographic explaining the six-step estimation chain from weights memory to GPUs, finishing at cost per million tokens.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1060" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="68" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">The six-step estimation chain from weights to GPUs</text>

  <!-- ==================== ROW 1: MEMORY SIZING ==================== -->

  <!-- Box 1: Weights memory -->
  <g id="box-1">
    <rect x="50" y="125" width="460" height="310" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Number circle 1 -->
    <circle cx="88" cy="165" r="24" fill="#207448" />
    <text x="88" y="174" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">1</text>
    <!-- Memory Module Icon -->
    <g transform="translate(130, 137)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="40" rx="4" />
      <line x1="4" y1="20" x2="52" y2="20" stroke-width="2.5" />
      <rect x="10" y="26" width="10" height="14" rx="2" stroke-width="2" />
      <rect x="23" y="26" width="10" height="14" rx="2" stroke-width="2" />
      <rect x="36" y="26" width="10" height="14" rx="2" stroke-width="2" />
      <line x1="12" y1="48" x2="12" y2="52" stroke-width="3" />
      <line x1="20" y1="48" x2="20" y2="52" stroke-width="3" />
      <line x1="28" y1="48" x2="28" y2="52" stroke-width="3" />
      <line x1="36" y1="48" x2="36" y2="52" stroke-width="3" />
      <line x1="44" y1="48" x2="44" y2="52" stroke-width="3" />
    </g>
    <!-- Title -->
    <text x="280" y="235" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Weights memory</text>
    <!-- Monospace input panel -->
    <rect x="70" y="275" width="420" height="140" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="280" y="335" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="280" dy="0">parameters x bytes</tspan>
      <tspan x="280" dy="40">per parameter</tspan>
    </text>
  </g>

  <!-- Arrow 1 -> 2 -->
  <line x1="510" y1="280" x2="570" y2="280" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />

  <!-- Box 2: KV cache per request -->
  <g id="box-2">
    <rect x="570" y="125" width="460" height="310" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Number circle 2 -->
    <circle cx="608" cy="165" r="24" fill="#207448" />
    <text x="608" y="174" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">2</text>
    <!-- Cache Blocks Icon -->
    <g transform="translate(650, 137)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="14" rx="3" />
      <rect x="6" y="22" width="44" height="14" rx="3" />
      <rect x="6" y="38" width="44" height="14" rx="3" />
      <line x1="16" y1="6" x2="16" y2="20" stroke-width="2.5" />
      <line x1="30" y1="6" x2="30" y2="20" stroke-width="2.5" />
      <line x1="20" y1="22" x2="20" y2="36" stroke-width="2.5" />
      <line x1="34" y1="22" x2="34" y2="36" stroke-width="2.5" />
      <line x1="14" y1="38" x2="14" y2="52" stroke-width="2.5" />
      <line x1="28" y1="38" x2="28" y2="52" stroke-width="2.5" />
    </g>
    <!-- Title -->
    <text x="800" y="235" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">KV cache per request</text>
    <!-- Monospace input panel -->
    <rect x="590" y="275" width="420" height="140" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="800" y="335" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="800" dy="0">KV bytes per token x</tspan>
      <tspan x="800" dy="40">(prompt + output tokens)</tspan>
    </text>
  </g>

  <!-- Arrow 2 -> 3 -->
  <line x1="1030" y1="280" x2="1090" y2="280" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />

  <!-- Box 3: Requests that fit on one GPU (Orange Outline) -->
  <g id="box-3">
    <rect x="1090" y="125" width="460" height="310" rx="16" fill="#e8f1ea" stroke="#db8129" stroke-width="4" />
    <!-- Number circle 3 -->
    <circle cx="1128" cy="165" r="24" fill="#207448" />
    <text x="1128" y="174" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">3</text>
    <!-- GPU Chip Icon -->
    <g transform="translate(1170, 137)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="36" height="36" rx="4" />
      <rect x="18" y="18" width="20" height="20" rx="2" fill="#207448" />
      <line x1="18" y1="2" x2="18" y2="10" stroke-width="3" />
      <line x1="28" y1="2" x2="28" y2="10" stroke-width="3" />
      <line x1="38" y1="2" x2="38" y2="10" stroke-width="3" />
      <line x1="18" y1="46" x2="18" y2="54" stroke-width="3" />
      <line x1="28" y1="46" x2="28" y2="54" stroke-width="3" />
      <line x1="38" y1="46" x2="38" y2="54" stroke-width="3" />
      <line x1="2" y1="18" x2="10" y2="18" stroke-width="3" />
      <line x1="2" y1="28" x2="10" y2="28" stroke-width="3" />
      <line x1="2" y1="38" x2="10" y2="38" stroke-width="3" />
      <line x1="46" y1="18" x2="54" y2="18" stroke-width="3" />
      <line x1="46" y1="28" x2="54" y2="28" stroke-width="3" />
      <line x1="46" y1="38" x2="54" y2="38" stroke-width="3" />
    </g>
    <!-- Title -->
    <text x="1320" y="215" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="1320" dy="0">Requests that fit</tspan>
      <tspan x="1320" dy="38">on one GPU</tspan>
    </text>
    <!-- Monospace input panel -->
    <rect x="1110" y="275" width="420" height="140" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="1320" y="315" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="1320" dy="0">GPU memory x 0.9</tspan>
      <tspan x="1320" dy="35">minus weights, divided by</tspan>
      <tspan x="1320" dy="35">KV per request</tspan>
    </text>
  </g>

  <!-- Arrow 3 -> 4 (Connector between rows) -->
  <path d="M 1320 435 V 467 A 12 12 0 0 1 1308 479 H 229 A 12 12 0 0 0 217 491 V 520" stroke="#207448" stroke-width="4" fill="none" marker-end="url(#arrow)" />

  <!-- ==================== ROW 2: THROUGHPUT, SCALING & COST ==================== -->

  <!-- Box 4: Decode tokens per second -->
  <g id="box-4">
    <rect x="50" y="520" width="335" height="330" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Number circle 4 -->
    <circle cx="88" cy="560" r="24" fill="#207448" />
    <text x="88" y="569" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">4</text>
    <!-- Clock / Timer Icon -->
    <g transform="translate(125, 532)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="28,14 28,28 38,28" />
      <line x1="28" y1="2" x2="28" y2="6" stroke-width="3" />
      <line x1="50" y1="28" x2="54" y2="28" stroke-width="3" />
      <line x1="28" y1="50" x2="28" y2="54" stroke-width="3" />
      <line x1="2" y1="28" x2="6" y2="28" stroke-width="3" />
    </g>
    <!-- Title -->
    <text x="217" y="612" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="217" dy="0">Decode tokens</tspan>
      <tspan x="217" dy="38">per second</tspan>
    </text>
    <!-- Monospace input panel -->
    <rect x="68" y="675" width="299" height="155" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="217" y="742" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="217" dy="0">batch size and</tspan>
      <tspan x="217" dy="40">decode rate</tspan>
    </text>
  </g>

  <!-- Arrow 4 -> 5 -->
  <line x1="385" y1="685" x2="438" y2="685" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />

  <!-- Box 5: Requests per second per GPU -->
  <g id="box-5">
    <rect x="438" y="520" width="335" height="330" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Number circle 5 -->
    <circle cx="476" cy="560" r="24" fill="#207448" />
    <text x="476" y="569" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">5</text>
    <!-- Gear Icon -->
    <g transform="translate(513, 532)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="14" />
      <path d="M 28 6 V 14 M 28 42 V 50 M 6 28 H 14 M 42 28 H 50 M 12 12 L 18 18 M 38 38 L 44 44 M 12 44 L 18 38 M 38 18 L 44 12" stroke-width="3.5" />
      <circle cx="28" cy="28" r="5" fill="#207448" />
    </g>
    <!-- Title -->
    <text x="605" y="612" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="605" dy="0">Requests per</tspan>
      <tspan x="605" dy="38">second per GPU</tspan>
    </text>
    <!-- Monospace input panel combining prefill tokens per second and decode tokens per second -->
    <rect x="456" y="675" width="299" height="155" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="605" y="712" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="605" dy="0">prefill tokens</tspan>
      <tspan x="605" dy="32">per second</tspan>
    </text>
    <text x="605" y="778" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="605" dy="0">decode tokens</tspan>
      <tspan x="605" dy="32">per second</tspan>
    </text>
  </g>

  <!-- Arrow 5 -> 6 -->
  <line x1="773" y1="685" x2="826" y2="685" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />

  <!-- Box 6: GPUs for QPS, plus headroom and N+1 -->
  <g id="box-6">
    <rect x="826" y="520" width="335" height="330" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Number circle 6 -->
    <circle cx="864" cy="560" r="24" fill="#207448" />
    <text x="864" y="569" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">6</text>
    <!-- Server Rack Icon with N+1 badge -->
    <g transform="translate(901, 532)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="14" rx="2" />
      <rect x="6" y="26" width="44" height="14" rx="2" />
      <circle cx="12" cy="15" r="2" fill="#207448" />
      <circle cx="18" cy="15" r="2" fill="#207448" />
      <circle cx="12" cy="33" r="2" fill="#207448" />
      <circle cx="18" cy="33" r="2" fill="#207448" />
      <line x1="26" y1="15" x2="42" y2="15" stroke-width="2" />
      <line x1="26" y1="33" x2="42" y2="33" stroke-width="2" />
      <circle cx="42" cy="45" r="9" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
      <line x1="42" y1="40" x2="42" y2="50" stroke-width="2.5" />
      <line x1="37" y1="45" x2="47" y2="45" stroke-width="2.5" />
    </g>
    <!-- Title -->
    <text x="993" y="594" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="993" dy="0">GPUs for QPS,</tspan>
      <tspan x="993" dy="36">plus headroom</tspan>
      <tspan x="993" dy="36">and N+1</tspan>
    </text>
    <!-- Monospace input panel -->
    <rect x="844" y="675" width="299" height="155" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="993" y="730" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="993" dy="0">demand divided by</tspan>
      <tspan x="993" dy="35">requests per</tspan>
      <tspan x="993" dy="35">second per GPU</tspan>
    </text>
  </g>

  <!-- Arrow 6 -> Cost card (A final small arrow) -->
  <line x1="1161" y1="685" x2="1214" y2="685" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />

  <!-- Cost Card: Cost per million tokens -->
  <g id="cost-card">
    <rect x="1214" y="520" width="336" height="330" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Price Tag Icon -->
    <g transform="translate(1354, 550)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 12 H 28 L 48 32 L 32 48 L 12 28 Z" />
      <circle cx="22" cy="22" r="3" fill="#207448" />
      <path d="M 28 32 C 28 30 30 28 32 28 C 34 28 36 29 36 31 C 36 34 30 34 30 37 C 30 39 32 40 34 40" stroke-width="2.5" />
      <line x1="33" y1="26" x2="33" y2="42" stroke-width="2" />
    </g>
    <!-- Cost card label -->
    <rect x="1232" y="675" width="300" height="155" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="1382" y="742" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="1382" dy="0">Cost per</tspan>
      <tspan x="1382" dy="40">million tokens</tspan>
    </text>
  </g>

  <!-- ==================== TAKEAWAY BAR & CAPTION ==================== -->

  <!-- Takeaway bar under the chain -->
  <g id="takeaway-bar">
    <rect x="50" y="885" width="1500" height="80" rx="14" fill="#207448" />
    <text x="800" y="935" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Each box is a ceiling, not a measurement</text>
  </g>

  <!-- Caption -->
  <text x="800" y="1020" text-anchor="middle" font-family="sans-serif" font-size="26" font-style="italic" fill="#303a36">Work forward from the inputs, never backward from the answer you want.</text>
</svg>'''

with open("test_candidate_v2.svg", "w") as f:
    f.write(svg_content)

print("SVG written to test_candidate_v2.svg")
