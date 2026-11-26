import xml.etree.ElementTree as ET
import re, subprocess, pathlib

def build_test_svg():
    H = 1140
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">
  <title></title>
  <desc></desc>

  <defs>
    <!-- Arrowhead markers (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>

    <!-- Terminal / CLI Icon (56x56) -->
    <g id="icon-terminal">
      <rect x="0" y="3" width="56" height="50" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
      <line x1="0" y1="17" x2="56" y2="17" stroke="#207448" stroke-width="2"/>
      <circle cx="10" cy="10" r="2.5" fill="#207448"/>
      <circle cx="18" cy="10" r="2.5" fill="#207448"/>
      <circle cx="26" cy="10" r="2.5" fill="#207448"/>
      <path d="M 10 28 L 18 34 L 10 40" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="24" y1="40" x2="36" y2="40" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
    </g>

    <!-- Clock / Timer Icon (56x56) -->
    <g id="icon-clock">
      <circle cx="28" cy="28" r="24" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
      <polyline points="28,14 28,28 38,28" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
    </g>

    <!-- Chip / GPU Icon (56x56) -->
    <g id="icon-chip">
      <rect x="10" y="10" width="36" height="36" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
      <rect x="18" y="18" width="20" height="20" rx="3" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <line x1="16" y1="3" x2="16" y2="10" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="28" y1="3" x2="28" y2="10" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="40" y1="3" x2="40" y2="10" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="16" y1="46" x2="16" y2="53" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="28" y1="46" x2="28" y2="53" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="40" y1="46" x2="40" y2="53" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="3" y1="16" x2="10" y2="16" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="3" y1="28" x2="10" y2="28" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="3" y1="40" x2="10" y2="40" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="46" y1="16" x2="53" y2="16" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="46" y1="28" x2="53" y2="28" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="46" y1="40" x2="53" y2="40" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
    </g>

    <!-- Shield / Taint Icon (56x56) -->
    <g id="icon-shield">
      <path d="M 28 6 L 48 14 V 28 C 48 40 38 48 28 52 C 18 48 8 40 8 28 V 14 Z" fill="#e8f1ea" stroke="#207448" stroke-width="3" stroke-linejoin="round"/>
      <line x1="28" y1="20" x2="28" y2="32" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
      <circle cx="28" cy="38" r="2" fill="#207448"/>
    </g>

    <!-- Tag / Selector Icon (56x56) -->
    <g id="icon-tag">
      <path d="M 10 26 L 26 10 L 46 10 L 46 30 L 30 46 Z" fill="#e8f1ea" stroke="#207448" stroke-width="3" stroke-linejoin="round"/>
      <circle cx="38" cy="18" r="3" fill="#207448"/>
      <line x1="16" y1="36" x2="22" y2="42" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
    </g>

    <!-- Node / Server Icon (56x56) -->
    <g id="icon-node">
      <rect x="6" y="8" width="44" height="16" rx="4" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <circle cx="14" cy="16" r="2" fill="#207448"/>
      <line x1="22" y1="16" x2="42" y2="16" stroke="#207448" stroke-width="2"/>
      <rect x="6" y="28" width="44" height="16" rx="4" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <circle cx="14" cy="36" r="2" fill="#207448"/>
      <line x1="22" y1="36" x2="42" y2="36" stroke="#207448" stroke-width="2"/>
    </g>

    <!-- Gear / Plugin Icon (56x56) -->
    <g id="icon-gear">
      <circle cx="28" cy="28" r="10" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
      <path d="M 28 6 L 28 12 M 28 44 L 28 50 M 6 28 L 12 28 M 44 28 L 50 28 M 12 12 L 17 17 M 39 39 L 44 44 M 12 44 L 17 39 M 39 17 L 44 12" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
    </g>

    <!-- Meter / Quota Icon (56x56) -->
    <g id="icon-quota">
      <path d="M 8 38 A 22 22 0 1 1 48 38 Z" fill="#e8f1ea" stroke="#207448" stroke-width="3" stroke-linejoin="round"/>
      <line x1="28" y1="38" x2="38" y2="24" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
      <circle cx="28" cy="38" r="3" fill="#207448"/>
    </g>
  </defs>

  <!-- Canvas Background -->
  <rect width="1600" height="{H}" fill="#f5f8f5"/>

  <!-- ==================== MAIN TITLE (48px bold) ==================== -->
  <text x="800" y="75" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">A Pending GPU pod: read the scheduler's reason, </tspan>
    <tspan x="800" dy="54">then take one of three branches</tspan>
  </text>

  <!-- ==================== TOP BOX: FailedScheduling event (Orange Highlight) ==================== -->
  <g transform="translate(100, 160)">
    <!-- Box background and orange highlight border -->
    <rect width="960" height="145" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3.5"/>
    
    <!-- Icon -->
    <use href="#icon-terminal" x="25" y="45"/>

    <!-- Sans label with FailedScheduling in monospace (30px bold) -->
    <text x="105" y="48" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      Read the <tspan font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace">FailedScheduling</tspan> event
    </text>

    <!-- Monospace command (26px) -->
    <text x="105" y="88" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="26" font-weight="bold" fill="#207448">
      kubectl describe pod
    </text>

    <!-- Note: The scheduler's own reason (24px sans) -->
    <text x="105" y="122" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#607068">
      The scheduler's own reason
    </text>
  </g>

  <!-- ==================== PENDING BOX ==================== -->
  <g transform="translate(150, 350)">
    <rect width="860" height="90" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <use href="#icon-clock" x="24" y="17"/>
    <text x="96" y="55" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      Pending means the scheduler has not placed it
    </text>
  </g>

  <!-- ==================== DOWNWARD ARROW 1 ==================== -->
  <!-- Downward arrow leading to three branch boxes side by side -->
  <line x1="580" y1="440" x2="580" y2="485" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)"/>

  <!-- ==================== CONTAINER: THREE BRANCHES ==================== -->
  <rect x="50" y="485" width="1060" height="590" rx="18" fill="#ffffff" stroke="#207448" stroke-width="2" stroke-dasharray="8,6"/>

  <!-- ==================== BRANCH 1 ==================== -->
  <g transform="translate(75, 515)">
    <!-- Branch 1 Box -->
    <rect width="310" height="185" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <use href="#icon-chip" x="127" y="16"/>
    
    <text x="155" y="98" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="155" dy="0">Insufficient </tspan>
      <tspan x="155" dy="34" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="26" fill="#207448">nvidia.com/gpu</tspan>
    </text>

    <text x="155" y="160" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="155" dy="0">No node has a free </tspan>
      <tspan x="155" dy="28">GPU in its Allocatable</tspan>
    </text>
  </g>

  <!-- Sub-box under Branch 1: Allocatable is zero on a GPU node -->
  <g transform="translate(75, 745)">
    <rect width="310" height="115" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <use href="#icon-node" x="127" y="12"/>
    <text x="155" y="82" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#303a36">
      <tspan x="155" dy="0">Allocatable is zero </tspan>
      <tspan x="155" dy="30">on a GPU node</tspan>
    </text>
  </g>

  <!-- Arrow from Sub-box to Suspect label -->
  <line x1="230" y1="860" x2="230" y2="905" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)"/>

  <!-- Label box under Branch 1: Device plugin is the suspect -->
  <g transform="translate(75, 905)">
    <rect width="310" height="145" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <use href="#icon-gear" x="127" y="18"/>
    <text x="155" y="98" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">
      <tspan x="155" dy="0">Device plugin is </tspan>
      <tspan x="155" dy="32">the suspect</tspan>
    </text>
  </g>

  <!-- ==================== BRANCH 2 ==================== -->
  <g transform="translate(425, 515)">
    <rect width="310" height="185" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <use href="#icon-shield" x="127" y="16"/>

    <text x="155" y="102" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      Untolerated taint
    </text>

    <text x="155" y="152" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      Pod needs a toleration
    </text>
  </g>

  <!-- ==================== BRANCH 3 ==================== -->
  <g transform="translate(775, 515)">
    <rect width="310" height="185" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <use href="#icon-tag" x="127" y="16"/>

    <text x="155" y="102" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      Selector mismatch
    </text>

    <text x="155" y="152" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      Labels do not match
    </text>
  </g>

  <!-- ==================== SEPARATE BOX: ResourceQuota is hit ==================== -->
  <g transform="translate(1150, 485)">
    <rect width="400" height="590" rx="18" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <use href="#icon-quota" x="172" y="45"/>

    <text x="200" y="150" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="200" dy="0">ResourceQuota </tspan>
      <tspan x="200" dy="38">is hit</tspan>
    </text>

    <text x="200" y="245" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="200" dy="0">API server returns 403, </tspan>
      <tspan x="200" dy="36">so no Pod exists and </tspan>
      <tspan x="200" dy="36">the ReplicaSet records </tspan>
      <tspan x="200" dy="36">the failure</tspan>
    </text>
  </g>
</svg>'''
    return svg

open("candidate_pending.svg", "w").write(build_test_svg())
print("Saved candidate_pending.svg (updated)")
