#!/usr/bin/env python3
import pathlib

svg_grid_compact = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 950" width="1600" height="950">
  <title>TTFT doubled while GPU utilisation is flat: four checks</title>
  <desc>Four-step investigation for p99 TTFT doubling over ten minutes with utilisation flat: waiting queue and KV usage, prefix hit rate, ready replicas, and per-tenant token rates.</desc>

  <!-- Background -->
  <rect width="1600" height="950" fill="#f5f8f5"/>

  <!-- Title -->
  <text x="800" y="60" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">TTFT doubled while GPU utilisation is flat: four checks</text>

  <!-- Header / Subtitle Panel -->
  <rect x="60" y="90" width="1480" height="64" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="800" y="131" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">Four-step investigation for p99 TTFT doubling over ten minutes with utilisation flat.</text>

  <!-- Check 1 (Top-Left: Orange highlight - single most important check) -->
  <g id="check-1">
    <rect x="60" y="185" width="720" height="260" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3"/>
    <!-- Icon: Memory chip with queue slots (56x56) -->
    <g transform="translate(95, 215)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="48" height="48" rx="8"/>
      <line x1="6" y1="22" x2="54" y2="22"/>
      <line x1="22" y1="22" x2="22" y2="54"/>
      <line x1="38" y1="22" x2="38" y2="54"/>
      <circle cx="14" cy="14" r="3" fill="#db8129"/>
      <line x1="16" y1="2" x2="16" y2="6"/>
      <line x1="30" y1="2" x2="30" y2="6"/>
      <line x1="44" y1="2" x2="44" y2="6"/>
      <line x1="16" y1="54" x2="16" y2="58"/>
      <line x1="30" y1="54" x2="30" y2="58"/>
      <line x1="44" y1="54" x2="44" y2="58"/>
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="180" y="235" font-size="30" font-weight="bold">1 Waiting queue and</tspan>
      <tspan x="180" y="273" font-size="30" font-weight="bold">KV usage per replica:</tspan>
      <tspan x="95" y="340" font-size="25">near-full KV means long contexts</tspan>
      <tspan x="95" y="378" font-size="25">are evicting or queueing requests</tspan>
    </text>
  </g>

  <!-- Check 2 (Top-Right) -->
  <g id="check-2">
    <rect x="820" y="185" width="720" height="260" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Router / branching cache tree (56x56) -->
    <g transform="translate(855, 215)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="30" r="10"/>
      <circle cx="44" cy="16" r="8"/>
      <circle cx="44" cy="44" r="8"/>
      <line x1="26" y1="25" x2="36" y2="19"/>
      <line x1="26" y1="35" x2="36" y2="41"/>
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="940" y="255" font-size="30" font-weight="bold">2 Prefix hit rate:</tspan>
      <tspan x="855" y="325" font-size="24">if it dropped, a router or cache change</tspan>
      <tspan x="855" y="362" font-size="24">happened; cache drops are an alert</tspan>
      <tspan x="855" y="399" font-size="24">in the public case study</tspan>
    </text>
  </g>

  <!-- Check 3 (Bottom-Left) -->
  <g id="check-3">
    <rect x="60" y="485" width="720" height="260" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Replicas / cluster pods (56x56) -->
    <g transform="translate(95, 515)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="20" height="20" rx="4"/>
      <rect x="34" y="8" width="20" height="20" rx="4"/>
      <rect x="6" y="34" width="20" height="20" rx="4"/>
      <rect x="34" y="34" width="20" height="20" rx="4" stroke-dasharray="4 3"/>
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="180" y="535" font-size="30" font-weight="bold">3 Ready replicas</tspan>
      <tspan x="180" y="573" font-size="30" font-weight="bold">against desired:</tspan>
      <tspan x="95" y="640" font-size="25">a silent shrink explains it</tspan>
      <tspan x="95" y="678" font-size="25">without any error</tspan>
    </text>
  </g>

  <!-- Check 4 (Bottom-Right) -->
  <g id="check-4">
    <rect x="820" y="485" width="720" height="260" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Tenant token meter / gauge (56x56) -->
    <g transform="translate(855, 515)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="30" cy="30" r="24"/>
      <path d="M 14 36 A 18 18 0 1 1 46 36"/>
      <line x1="30" y1="30" x2="42" y2="20"/>
      <circle cx="30" cy="30" r="3" fill="#207448"/>
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="940" y="535" font-size="30" font-weight="bold">4 Per-tenant</tspan>
      <tspan x="940" y="573" font-size="30" font-weight="bold">token rates:</tspan>
      <tspan x="855" y="640" font-size="25">one tenant sending</tspan>
      <tspan x="855" y="678" font-size="25">long prompts</tspan>
    </text>
  </g>

  <!-- Takeaway Bar -->
  <g id="takeaway-bar">
    <rect x="60" y="785" width="1480" height="120" rx="16" fill="#207448"/>
    <text font-family="sans-serif" font-size="25" fill="#ffffff" text-anchor="middle">
      <tspan x="800" y="834" font-size="25" font-weight="bold">a green GPU graph and a red latency graph: utilisation is a poor signal because batching</tspan>
      <tspan x="800" y="872" font-size="25" font-weight="bold">keeps a GPU busy while queues grow; scale on queue depth and KV pressure</tspan>
    </text>
  </g>
</svg>"""

pathlib.Path("candidate_grid_compact.svg").write_text(svg_grid_compact)
print("Saved candidate_grid_compact.svg")
