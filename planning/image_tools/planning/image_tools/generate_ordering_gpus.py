#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 960" width="1600" height="960">
  <title>Ordering GPUs against a three-month lead time</title>
  <desc>Capacity planning worked chain showing GPU order calculation against lead time and demand growth.</desc>

  <defs>
    <!-- Arrowhead marker (18px, green) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>

    <!-- Card shadow -->
    <filter id="card-shadow" x="-4%" y="-4%" width="108%" height="108%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#207448" flood-opacity="0.08" />
    </filter>
  </defs>

  <!-- Background -->
  <rect width="1600" height="960" fill="#f5f8f5" />

  <!-- ==================== TITLE ==================== -->
  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Ordering GPUs against a three-month lead time</text>

  <!-- ==================== WORKED CHAIN CONTAINER ==================== -->
  <g id="worked-chain-container">
    <rect x="40" y="110" width="1520" height="510" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Container Header Icon: Chain links (56px) -->
    <g transform="translate(70, 132)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="22" height="34" rx="8" />
      <rect x="18" y="16" width="22" height="34" rx="8" />
      <line x1="15" y1="28" x2="27" y2="28" />
    </g>

    <!-- Container Title -->
    <text x="135" y="172" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Worked chain with assumed inputs</text>

    <!-- Card 1: Inputs & Fleet -->
    <g id="chain-step-1">
      <rect x="90" y="215" width="325" height="375" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" filter="url(#card-shadow)" />
      <!-- Icon 1: GPU cluster / chip (56px) -->
      <g transform="translate(224, 238)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="10" y="10" width="36" height="36" rx="6" />
        <rect x="18" y="18" width="20" height="20" rx="2" fill="#e8f1ea" />
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
      <text x="252" y="328" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="252" dy="0">Fleet 400 GPUs,</tspan>
        <tspan x="252" dy="32">320 in use, demand</tspan>
        <tspan x="252" dy="32">growing 8 percent</tspan>
        <tspan x="252" dy="32">a month, GPU lead</tspan>
        <tspan x="252" dy="32">time 3 months,</tspan>
        <tspan x="252" dy="32">headroom policy</tspan>
        <tspan x="252" dy="32">20 percent</tspan>
      </text>
    </g>

    <!-- Arrow 1 -> 2 -->
    <line x1="417" y1="402" x2="453" y2="402" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

    <!-- Card 2: Demand after lead time -->
    <g id="chain-step-2">
      <rect x="455" y="215" width="325" height="375" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" filter="url(#card-shadow)" />
      <!-- Icon 2: Clock / Lead time (56px) -->
      <g transform="translate(589, 238)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="22" />
        <polyline points="28 14 28 28 38 28" />
        <path d="M 44 10 L 50 16" />
        <path d="M 12 10 L 6 16" />
      </g>
      <text x="617" y="365" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="617" dy="0">Demand after the</tspan>
        <tspan x="617" dy="36">lead time: 320 x</tspan>
        <tspan x="617" dy="36">1.08 cubed = 403.1</tspan>
      </text>
    </g>

    <!-- Arrow 2 -> 3 -->
    <line x1="782" y1="402" x2="818" y2="402" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

    <!-- Card 3: Headroom policy -->
    <g id="chain-step-3">
      <rect x="820" y="215" width="325" height="375" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" filter="url(#card-shadow)" />
      <!-- Icon 3: Shield / Headroom buffer (56px) -->
      <g transform="translate(954, 238)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 28 8 L 48 16 C 48 34 38 46 28 50 C 18 46 8 34 8 16 Z" />
        <path d="M 20 28 L 26 34 L 38 22" />
      </g>
      <text x="982" y="352" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="982" dy="0">GPUs needed with</tspan>
        <tspan x="982" dy="34">headroom: 403.1</tspan>
        <tspan x="982" dy="34">x 1.2, rounded</tspan>
        <tspan x="982" dy="34">up = 484</tspan>
      </text>
    </g>

    <!-- Arrow 3 -> 4 -->
    <line x1="1147" y1="402" x2="1183" y2="402" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

    <!-- Card 4: Order today (Key result, stroke orange #db8129) -->
    <g id="chain-step-4">
      <rect x="1185" y="215" width="325" height="375" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="4" filter="url(#card-shadow)" />
      <!-- Icon 4: Order / Delivery crate (56px) -->
      <g transform="translate(1319, 238)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="8" y="16" width="40" height="34" rx="4" />
        <polyline points="8 26 28 34 48 26" />
        <line x1="28" y1="34" x2="28" y2="50" />
        <path d="M 20 8 L 28 16 L 36 8" />
      </g>
      <text x="1347" y="375" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">
        <tspan x="1347" dy="0">Order today:</tspan>
        <tspan x="1347" dy="42">484 - 400 = 84</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== BOTTOM PANELS ==================== -->
  <!-- Left: Contrast Box -->
  <g id="contrast-box">
    <rect x="40" y="660" width="960" height="250" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" filter="url(#card-shadow)" />
    <!-- Contrast Icon: Balance scales / Direction (56px) -->
    <g transform="translate(75, 757)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="28" y1="8" x2="28" y2="48" />
      <line x1="14" y1="48" x2="42" y2="48" />
      <line x1="10" y1="18" x2="46" y2="18" />
      <polyline points="10 18 4 34 16 34 10 18" />
      <polyline points="46 18 40 34 52 34 46 18" />
    </g>
    <text x="560" y="745" text-anchor="middle" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="560" dy="0" font-weight="bold" fill="#207448">plan against lead time, not today's load:</tspan>
      <tspan x="560" dy="38">today's load tells you what is busy now,</tspan>
      <tspan x="560" dy="38">lead time tells you what you must order now</tspan>
    </text>
  </g>

  <!-- Right: Curveball Box -->
  <g id="curveball-box">
    <rect x="1040" y="660" width="520" height="250" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" filter="url(#card-shadow)" />
    <!-- Curveball Icon: Return loop / Delay turn (56px) -->
    <g transform="translate(1272, 692)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 28 A 16 16 0 1 1 28 44 L 20 44" />
      <polyline points="24 38 18 44 24 50" />
      <line x1="28" y1="18" x2="28" y2="28" />
      <circle cx="28" cy="34" r="1.5" fill="#207448" />
    </g>
    <text x="1300" y="805" text-anchor="middle" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="1300" dy="0" font-weight="bold" fill="#207448">vendor delays 200 GPUs:</tspan>
      <tspan x="1300" dy="40">redo the same chain</tspan>
    </text>
  </g>
</svg>'''

with open("candidate_ordering_gpus.svg", "w") as f:
    f.write(svg_content)

print("Saved candidate_ordering_gpus.svg successfully.")
