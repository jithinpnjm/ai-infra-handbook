#!/usr/bin/env python3
import os

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>Three checks before a template reaches a server</title>
  <desc>A left to right pipeline of three gates for template verification: rendering offline with realistic data, diffing against a golden file, and validating with the target parser before deploying to production.</desc>

  <defs>
    <!-- Arrowhead marker (18px) for pipeline transition arrows -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1080" fill="#f5f8f5" />

  <!-- Main Title (48px bold) -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Three checks before a template reaches a server</text>

  <!-- Story Strip -->
  <rect x="40" y="102" width="1520" height="92" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <g transform="translate(62, 120)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="44" rx="6" />
    <line x1="4" y1="18" x2="52" y2="18" />
    <circle cx="12" cy="12" r="2" fill="#207448" />
    <circle cx="20" cy="12" r="2" fill="#207448" />
    <line x1="16" y1="32" x2="40" y2="32" />
    <line x1="16" y1="40" x2="30" y2="40" />
  </g>
  <text x="138" y="142" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="138" dy="0">the render succeeds, the service refuses to start, and</tspan>
    <tspan x="138" dy="32">the log says the config is malformed on line 14</tspan>
  </text>

  <!-- Pipeline Arrows connecting the three gates -->
  <line x1="520" y1="578" x2="560" y2="578" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />
  <line x1="1040" y1="578" x2="1080" y2="578" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- ==================== GATE 1 ==================== -->
  <rect x="40" y="236" width="480" height="684" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Gate 1 Icon: Terminal window -->
  <g transform="translate(60, 256)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="44" rx="6" />
    <line x1="4" y1="18" x2="52" y2="18" />
    <polyline points="12,28 18,34 12,40" />
    <line x1="24" y1="40" x2="36" y2="40" />
  </g>

  <!-- Gate 1 Title -->
  <text x="132" y="286" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="132" dy="0">render offline with</tspan>
    <tspan x="132" dy="36">realistic data</tspan>
  </text>

  <!-- Gate 1 Item 1 Card -->
  <rect x="56" y="352" width="448" height="96" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
  <text x="76" y="392" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="76" dy="0">jinja2 Python API with</tspan>
    <tspan x="76" dy="32">a fixtures file</tspan>
  </text>

  <!-- Gate 1 Item 2 Card: ansible localhost template command -->
  <rect x="56" y="464" width="448" height="206" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
  <text x="76" y="502" font-family="monospace" font-size="24" fill="#303a36">
    <tspan x="76" dy="0">ansible localhost -m</tspan>
    <tspan x="76" dy="32">ansible.builtin.template</tspan>
    <tspan x="76" dy="32">-a "src=nccl.conf.j2</tspan>
    <tspan x="76" dy="32">dest=/tmp/out"</tspan>
    <tspan x="76" dy="32">-e @vars.yml --diff</tspan>
  </text>

  <!-- Gate 1 Item 3 Card: one-task playbook -->
  <rect x="56" y="686" width="448" height="74" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
  <text x="76" y="732" font-family="sans-serif" font-size="24" fill="#303a36">one-task playbook</text>

  <!-- Gate 1 Item 4 Card: debug msg -->
  <rect x="56" y="776" width="448" height="118" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
  <text x="76" y="822" font-family="monospace" font-size="24" fill="#303a36">
    <tspan x="76" dy="0">ansible -m debug</tspan>
    <tspan x="76" dy="34">-a "msg={{ ... }}"</tspan>
  </text>

  <!-- ==================== GATE 2 ==================== -->
  <rect x="560" y="236" width="480" height="684" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Gate 2 Icon: Golden file check -->
  <g transform="translate(580, 256)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 8 6 L 34 6 L 46 18 L 46 50 L 8 50 Z" />
    <polyline points="34,6 34,18 46,18" />
    <polyline points="18,34 26,42 38,26" />
  </g>

  <!-- Gate 2 Title -->
  <text x="652" y="286" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="652" dy="0">compare with</tspan>
    <tspan x="652" dy="36">the golden file</tspan>
  </text>

  <!-- Gate 2 Body Card -->
  <rect x="576" y="352" width="448" height="542" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
  <text x="596" y="394" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="596" dy="0">render representative data</tspan>
    <tspan x="596" dy="38">including empty lists and</tspan>
    <tspan x="596" dy="38">missing optional keys;</tspan>
    <tspan x="596" dy="38">the expected file is</tspan>
    <tspan x="596" dy="38">reviewed once and committed;</tspan>
    <tspan x="596" dy="38">any template change shows</tspan>
    <tspan x="596" dy="38">as a diff; stress inputs:</tspan>
    <tspan x="596" dy="38">an empty list, a missing</tspan>
    <tspan x="596" dy="38">optional key, a host with</tspan>
    <tspan x="596" dy="38">zero GPUs; snapshot tests</tspan>
    <tspan x="596" dy="38">catch stray whitespace</tspan>
  </text>

  <!-- ==================== GATE 3 (ORANGE) ==================== -->
  <rect x="1080" y="236" width="480" height="684" rx="16" fill="#fff9f2" stroke="#db8129" stroke-width="2.5" />

  <!-- Gate 3 Icon: Security validator shield -->
  <g transform="translate(1100, 256)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 28 6 L 48 14 C 48 34 28 48 28 48 C 28 48 8 34 8 14 Z" />
    <polyline points="19,26 25,32 37,20" />
  </g>

  <!-- Gate 3 Title -->
  <text x="1172" y="286" font-family="sans-serif" font-size="30" font-weight="bold" fill="#db8129">
    <tspan x="1172" dy="0">validate with the</tspan>
    <tspan x="1172" dy="36">target's own parser</tspan>
  </text>

  <!-- Gate 3 Body Card -->
  <rect x="1096" y="352" width="448" height="542" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="1.8" />
  <text x="1116" y="440" font-family="monospace" font-size="24" fill="#303a36">
    <tspan x="1116" dy="0">nginx -t, visudo -cf,</tspan>
    <tspan x="1116" dy="48">sshd -t, slurmd -C or</tspan>
    <tspan x="1116" dy="48">scontrol checks,</tspan>
    <tspan x="1116" dy="48">kubeconform, promtool</tspan>
    <tspan x="1116" dy="48">check rules, python -c</tspan>
    <tspan x="1116" dy="48">import yaml;</tspan>
    <tspan x="1116" dy="48">yaml.safe_load(...)</tspan>
  </text>

  <!-- ==================== BOTTOM BAR ==================== -->
  <rect x="40" y="960" width="1520" height="72" rx="14" fill="#207448" />
  <text x="800" y="1005" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">A surprise on Monday becomes a failed test on Friday</text>
</svg>
'''

with open("test_candidate_three_checks.svg", "w", encoding="utf-8") as f:
    f.write(svg_content.strip() + "\n")

print("Generated test_candidate_three_checks.svg")
