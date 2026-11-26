#!/usr/bin/env python3
import pathlib
import xml.etree.ElementTree as ET
import re
import subprocess

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1080" viewBox="0 0 1600 1080">
  <title>Planned exits versus failures</title>
  <desc>A table-like comparison of Ansible control flow primitives: meta end_host, meta end_play, end_batch, fail, and meta clear_host_errors.</desc>

  <!-- Background -->
  <rect width="1600" height="1080" fill="#f5f8f5"/>

  <!-- Title: 48px bold -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Planned exits versus failures</text>

  <!-- ==================== GROUP 1: Clean planned exit ==================== -->
  <g id="group-clean-exit">
    <!-- Group Container -->
    <rect x="40" y="96" width="1520" height="369" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>

    <!-- Group Heading -->
    <text x="68" y="145" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Clean planned exit</text>

    <!-- end_batch Badge -->
    <rect x="440" y="116" width="190" height="42" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="535" y="145" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">end_batch</text>

    <!-- Row 1: meta end_host -->
    <!-- Col 1: Control & Icon -->
    <rect x="60" y="175" width="380" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Server / Host Icon (56px) -->
    <g transform="translate(222, 185)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="18" rx="3"/>
      <line x1="14" y1="15" x2="16" y2="15"/>
      <rect x="6" y="28" width="44" height="18" rx="3"/>
      <line x1="14" y1="37" x2="16" y2="37"/>
    </g>
    <text x="250" y="278" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#207448">meta end_host</text>

    <!-- Col 2: Action -->
    <rect x="460" y="175" width="270" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="595" y="247" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">stop this host</text>

    <!-- Col 3: Status -->
    <rect x="750" y="175" width="410" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="955" y="247" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">no failure</text>

    <!-- Col 4: Condition -->
    <rect x="1180" y="175" width="360" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="1360" y="247" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">when skip_this_host</text>

    <!-- Row 2: meta end_play -->
    <!-- Col 1: Control & Icon -->
    <rect x="60" y="320" width="380" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Play / Multi-host Flag Icon (56px) -->
    <g transform="translate(222, 330)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="10" y1="6" x2="10" y2="50"/>
      <path d="M 10 10 L 44 22 L 10 34 Z"/>
    </g>
    <text x="250" y="423" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#207448">meta end_play</text>

    <!-- Col 2: Action -->
    <rect x="460" y="320" width="270" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="595" y="377" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="595" dy="0">end the play </tspan>
      <tspan x="595" dy="30">for everyone</tspan>
    </text>

    <!-- Col 3: Status -->
    <rect x="750" y="320" width="410" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="955" y="392" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">not a failure</text>

    <!-- Col 4: Condition -->
    <rect x="1180" y="320" width="360" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="1360" y="392" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">when dry_run_only</text>
  </g>

  <!-- ==================== GROUP 2: Explicit stop (Orange on fail row only) ==================== -->
  <g id="group-explicit-stop">
    <!-- Group Container: Orange stroke -->
    <rect x="40" y="505" width="1520" height="235" rx="14" fill="#e8f1ea" stroke="#db8129" stroke-width="3"/>

    <!-- Group Heading -->
    <text x="68" y="554" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Explicit stop</text>

    <!-- Row 3: fail -->
    <!-- Col 1: Control & Icon -->
    <rect x="60" y="584" width="380" height="136" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2.5"/>
    <!-- Stop Sign Octagon Icon (56px) in Orange -->
    <g transform="translate(222, 594)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="18,6 38,6 48,16 48,36 38,46 18,46 8,36 8,16"/>
      <line x1="20" y1="26" x2="36" y2="26"/>
    </g>
    <text x="250" y="694" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#db8129">fail</text>

    <!-- Col 2: Action -->
    <rect x="460" y="584" width="270" height="136" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="1.5"/>
    <text x="595" y="660" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">explicit stop</text>

    <!-- Col 3: Status / Message -->
    <rect x="750" y="584" width="410" height="136" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="1.5"/>
    <text x="955" y="632" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="955" dy="0">msg Refusing to run </tspan>
      <tspan x="955" dy="30">in production without </tspan>
      <tspan x="955" dy="30">change ticket</tspan>
    </text>

    <!-- Col 4: Condition -->
    <rect x="1180" y="584" width="360" height="136" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="1.5"/>
    <text x="1360" y="647" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="1360" dy="0">when env is prod and </tspan>
      <tspan x="1360" dy="30">no change_ticket</tspan>
    </text>
  </g>

  <!-- ==================== GROUP 3: Use rarely ==================== -->
  <g id="group-use-rarely">
    <!-- Group Container -->
    <rect x="40" y="780" width="1520" height="235" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>

    <!-- Group Heading -->
    <text x="68" y="829" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Use rarely</text>

    <!-- Row 4: meta clear_host_errors -->
    <!-- Col 1: Control & Icon -->
    <rect x="60" y="859" width="380" height="136" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Reset / Undo Loop Icon (56px) -->
    <g transform="translate(222, 869)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 26 A 16 16 0 1 1 20 40"/>
      <polyline points="6,24 12,26 14,32"/>
    </g>
    <text x="250" y="969" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">meta clear_host_errors</text>

    <!-- Col 2: Action -->
    <rect x="460" y="859" width="270" height="136" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="595" y="923" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="595" dy="0">resets </tspan>
      <tspan x="595" dy="30">failed hosts</tspan>
    </text>

    <!-- Col 3: Status -->
    <rect x="750" y="859" width="410" height="136" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="955" y="937" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">rare</text>

    <!-- Col 4: Consequence -->
    <rect x="1180" y="859" width="360" height="136" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="1360" y="937" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">hides the reason</text>
  </g>
</svg>'''

pathlib.Path("test_output.svg").write_text(svg_content)
print("Updated test_output.svg")
