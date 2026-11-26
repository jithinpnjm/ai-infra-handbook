#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, subprocess, os, pathlib

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000">
  <title>Free is small, available is large: the page cache is reclaimable</title>
  <desc>Visual infographic contrasting small free memory with large available memory in Linux free -m output, showing how the kernel reclaims page cache on demand.</desc>

  <defs>
    <!-- Green arrowhead for the single arrow (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>
  </defs>

  <!-- ==================== BACKGROUND ==================== -->
  <rect width="100%" height="100%" fill="#f5f8f5"/>

  <!-- ==================== TITLE (48px bold) ==================== -->
  <text x="800" y="76" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Free is small, available is large: </tspan>
    <tspan x="800" dy="56">the page cache is reclaimable</tspan>
  </text>

  <!-- ==================== TOTAL BAR LABEL ==================== -->
  <text x="800" y="192" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#303a36">total 1950 MB</text>

  <!-- ==================== HORIZONTAL STACKED BAR ==================== -->
  <!-- Outer boundary container -->
  <rect x="50" y="238" width="1500" height="90" rx="12" fill="none" stroke="#207448" stroke-width="3"/>

  <!-- Segment 1: Small white block at the far left (free 163 MB) -->
  <path d="M 62 238 L 280 238 L 280 328 L 62 328 A 12 12 0 0 1 50 316 L 50 250 A 12 12 0 0 1 62 238 Z" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="165" y="292" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan font-family="ui-monospace, SFMono-Regular, Menlo, monospace">free</tspan><tspan font-family="system-ui, -apple-system, sans-serif"> 163 MB</tspan>
  </text>

  <!-- Segment 2: Light green block (page cache, buffers and reclaimable) -->
  <rect x="280" y="238" width="740" height="90" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="650" y="292" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">page cache, buffers and reclaimable</text>

  <!-- Segment 3: Dark green block on right (used by applications) -->
  <path d="M 1020 238 L 1538 238 A 12 12 0 0 1 1550 250 L 1550 316 A 12 12 0 0 1 1538 328 L 1020 328 Z" fill="#207448" stroke="#207448" stroke-width="2"/>
  <text x="1285" y="292" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">used by applications</text>

  <!-- ==================== AVAILABLE BRACKET ==================== -->
  <!-- Bracket spanning from start of free block (x=50) to end of cache block (x=1020) -->
  <path d="M 50 340 L 50 360 L 515 360 L 535 376 L 555 360 L 1020 360 L 1020 340" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Bracket Label Pill -->
  <rect x="360" y="388" width="350" height="48" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
  <text x="535" y="421" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">
    <tspan font-family="ui-monospace, SFMono-Regular, Menlo, monospace">available</tspan><tspan font-family="system-ui, -apple-system, sans-serif"> 1187 MB</tspan>
  </text>

  <!-- ==================== ARROW FROM CACHE BLOCK TO AVAILABLE BRACKET ==================== -->
  <!-- Thin arrow from cache block (x=800, y=340) down to available bracket label (x=718, y=412) -->
  <path d="M 800 340 L 800 412 L 720 412" fill="none" stroke="#207448" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow-green)"/>
  
  <!-- Arrow Label -->
  <text x="820" y="388" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="820" dy="0">the kernel gives it back to </tspan>
    <tspan x="820" dy="28">applications on demand</tspan>
  </text>

  <!-- ==================== CARD 1 (LEFT): FREE ==================== -->
  <g id="card-free">
    <rect x="50" y="485" width="720" height="340" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>

    <!-- Warning / Alert Meter Icon (56x56, green stroke 4) -->
    <g transform="translate(70, 508)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 46 A 24 24 0 1 1 50 46" />
      <line x1="28" y1="36" x2="16" y2="20" />
      <circle cx="28" cy="36" r="4" fill="#207448" />
      <line x1="10" y1="42" x2="16" y2="40" />
      <line x1="28" y1="12" x2="28" y2="18" />
      <line x1="46" y1="42" x2="40" y2="40" />
    </g>

    <!-- Card 1 Title (30px bold) -->
    <text x="138" y="547" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan font-family="ui-monospace, SFMono-Regular, Menlo, monospace">free</tspan><tspan font-family="system-ui, -apple-system, sans-serif">, the column that looks scary</tspan>
    </text>

    <!-- Card 1 Value Display -->
    <rect x="75" y="585" width="670" height="95" rx="12" fill="#f5f8f5" stroke="#cfded2" stroke-width="1.5"/>
    <text x="410" y="651" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="52" font-weight="bold" fill="#303a36">163 MB</text>

    <!-- Orange Note Box (Single orange highlight in infographic) -->
    <rect x="75" y="705" width="670" height="85" rx="12" fill="#fff5eb" stroke="#db8129" stroke-width="2.5"/>
    <g transform="translate(90, 722)" stroke="#db8129" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="22,6 42,42 2,42" fill="#ffe9d4"/>
      <line x1="22" y1="18" x2="22" y2="28"/>
      <circle cx="22" cy="35" r="1.5" fill="#db8129"/>
    </g>
    <text x="435" y="757" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#db8129">free looks low, but that is not a problem.</text>
  </g>

  <!-- ==================== CARD 2 (RIGHT): AVAILABLE ==================== -->
  <g id="card-available">
    <rect x="830" y="485" width="720" height="340" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>

    <!-- Reading / Check Shield Icon (56x56, green stroke 4) -->
    <g transform="translate(850, 508)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 C 48 34 28 48 28 48 C 28 48 8 34 8 14 Z" fill="#e8f1ea"/>
      <path d="M 18 26 L 25 33 L 38 19"/>
    </g>

    <!-- Card 2 Title (30px bold) -->
    <text x="918" y="547" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan font-family="ui-monospace, SFMono-Regular, Menlo, monospace">available</tspan><tspan font-family="system-ui, -apple-system, sans-serif">, the number to read</tspan>
    </text>

    <!-- Card 2 Value Display -->
    <rect x="855" y="585" width="670" height="95" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="1190" y="651" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="52" font-weight="bold" fill="#207448">1187 MB</text>

    <!-- Visual reassurance panel: 60.9% of memory is reclaimable/available -->
    <rect x="855" y="705" width="670" height="85" rx="12" fill="#f5f8f5" stroke="#cfded2" stroke-width="1.5"/>
    <rect x="875" y="733" width="630" height="30" rx="8" fill="#e8f1ea"/>
    <rect x="875" y="733" width="384" height="30" rx="8" fill="#207448"/>
  </g>

  <!-- ==================== GREEN TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="50" y="875" width="1500" height="75" rx="14" fill="#207448"/>
    <text x="800" y="922" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Read available, not free.</text>
  </g>
</svg>'''

with open("candidate.svg", "w") as f:
    f.write(svg_code)

print("Updated candidate.svg with font sizes >= 30 for card titles successfully!")
