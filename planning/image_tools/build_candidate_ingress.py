#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, subprocess, pathlib

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000">
  <title>Service ships built in, Ingress needs a controller</title>
  <desc>A Service works out of the box through kube-proxy, while an Ingress object does nothing until a controller such as ingress-nginx or Contour implements it.</desc>

  <defs>
    <!-- Green arrowhead (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
    <!-- Orange arrowhead (18px) -->
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1000" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Service ships built in, Ingress needs a controller</text>

  <!-- ==================== LEFT COLUMN: Service: built into core ==================== -->
  <rect x="50" y="95" width="720" height="770" rx="18" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Left Column Header -->
  <g transform="translate(85, 118)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="6" y="6" width="44" height="44" rx="8" />
    <circle cx="28" cy="28" r="10" />
    <line x1="28" y1="6" x2="28" y2="14" />
    <line x1="28" y1="42" x2="28" y2="50" />
    <line x1="6" y1="28" x2="14" y2="28" />
    <line x1="42" y1="28" x2="50" y2="28" />
  </g>
  <text x="430" y="152" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Service: built into core</text>

  <!-- Green Note: Works on a fresh cluster -->
  <g id="note-fresh-cluster">
    <rect x="90" y="175" width="640" height="54" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <circle cx="130" cy="202" r="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <path d="M 123 202 L 128 207 L 137 197" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
    <text x="420" y="211" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Works on a fresh cluster</text>
  </g>

  <!-- Service Box with VIP Icon -->
  <g id="box-service">
    <rect x="90" y="255" width="640" height="115" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Virtual IP Globe / Network Icon -->
    <g transform="translate(180, 284)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="24" />
      <ellipse cx="28" cy="28" rx="12" ry="24" />
      <line x1="4" y1="28" x2="52" y2="28" />
    </g>
    <!-- VIP Badge -->
    <rect x="255" y="291" width="80" height="42" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="295" y="322" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">VIP</text>
    <!-- Service Title -->
    <text x="375" y="325" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Service</text>
  </g>

  <!-- Arrow: Service -> kube-proxy -->
  <line x1="410" y1="370" x2="410" y2="415" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- kube-proxy Box -->
  <g id="box-kube-proxy">
    <rect x="90" y="415" width="640" height="115" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Host daemon gear icon -->
    <g transform="translate(120, 444)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="10" width="40" height="36" rx="6" />
      <circle cx="28" cy="28" r="8" />
      <line x1="20" y1="4" x2="20" y2="10" />
      <line x1="36" y1="4" x2="36" y2="10" />
      <line x1="20" y1="46" x2="20" y2="52" />
      <line x1="36" y1="46" x2="36" y2="52" />
    </g>
    <text x="430" y="468" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan x="430" dy="0">kube-proxy</tspan>
      <tspan x="430" dy="34">programs each host</tspan>
    </text>
  </g>

  <!-- Arrow: kube-proxy -> Pod boxes -->
  <line x1="410" y1="530" x2="410" y2="590" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Two Pod Boxes Container -->
  <g id="group-pods">
    <rect x="90" y="590" width="640" height="155" rx="14" fill="#f5f8f5" stroke="#207448" stroke-width="2" stroke-dasharray="6,4" />
    <!-- Pod Box 1 -->
    <g id="pod-1">
      <rect x="120" y="612" width="265" height="112" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <!-- Pod Cube Icon -->
      <g transform="translate(225, 640)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="6" width="44" height="44" rx="8" />
        <line x1="6" y1="20" x2="50" y2="20" />
        <circle cx="16" cy="13" r="3" fill="#207448" />
        <circle cx="26" cy="13" r="3" fill="#207448" />
        <rect x="16" y="28" width="24" height="14" rx="3" stroke-width="2.5" />
      </g>
    </g>
    <!-- Pod Box 2 -->
    <g id="pod-2">
      <rect x="435" y="612" width="265" height="112" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <!-- Pod Cube Icon -->
      <g transform="translate(540, 640)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="6" width="44" height="44" rx="8" />
        <line x1="6" y1="20" x2="50" y2="20" />
        <circle cx="16" cy="13" r="3" fill="#207448" />
        <circle cx="26" cy="13" r="3" fill="#207448" />
        <rect x="16" y="28" width="24" height="14" rx="3" stroke-width="2.5" />
      </g>
    </g>
  </g>

  <!-- ==================== RIGHT COLUMN: Ingress: only a contract ==================== -->
  <rect x="830" y="95" width="720" height="770" rx="18" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Right Column Header -->
  <g transform="translate(865, 118)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 12 8 L 36 8 L 48 20 L 48 48 L 12 48 Z" />
    <polyline points="36,8 36,20 48,20" />
    <line x1="20" y1="28" x2="38" y2="28" />
    <line x1="20" y1="36" x2="38" y2="36" />
  </g>
  <text x="1210" y="152" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Ingress: only a contract</text>

  <!-- Ingress Object Box -->
  <g id="box-ingress-object">
    <rect x="870" y="175" width="640" height="135" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Contract document icon -->
    <g transform="translate(905, 215)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 6 L 34 6 L 46 18 L 46 50 L 10 50 Z" />
      <polyline points="34,6 34,18 46,18" />
      <line x1="18" y1="28" x2="38" y2="28" />
      <line x1="18" y1="36" x2="32" y2="36" />
    </g>
    <text x="985" y="228" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Ingress object</text>
    <text x="985" y="262" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="985" dy="0">Creating it by itself</tspan>
      <tspan x="985" dy="32">does nothing</tspan>
    </text>
  </g>

  <!-- Empty Dashed Arrow: Ingress object -> No controller callout -->
  <line x1="1190" y1="310" x2="1190" y2="355" stroke="#db8129" stroke-width="3.5" stroke-dasharray="6,4" marker-end="url(#arrow-orange)" />

  <!-- Callout: No controller: the Ingress does nothing (Orange outline) -->
  <g id="callout-no-controller">
    <rect x="870" y="355" width="640" height="92" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3.5" />
    <!-- Question mark badge with orange outline -->
    <g transform="translate(905, 373)">
      <circle cx="28" cy="28" r="22" fill="#fff9f2" stroke="#db8129" stroke-width="3" />
      <path d="M 23 20 C 23 15, 33 15, 33 21 C 33 25, 28 26, 28 30" fill="none" stroke="#db8129" stroke-width="3.5" stroke-linecap="round" />
      <circle cx="28" cy="37" r="2.5" fill="#db8129" />
    </g>
    <text x="1220" y="393" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#db8129">
      <tspan x="1220" dy="0">No controller:</tspan>
      <tspan x="1220" dy="32">the Ingress does nothing</tspan>
    </text>
  </g>

  <!-- Controller 1: ingress-nginx -->
  <g id="box-ingress-nginx">
    <rect x="870" y="475" width="640" height="115" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Proxy router icon -->
    <g transform="translate(905, 504)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="10" width="44" height="36" rx="6" />
      <line x1="16" y1="20" x2="40" y2="20" />
      <line x1="16" y1="28" x2="30" y2="28" />
      <line x1="16" y1="36" x2="36" y2="36" />
      <circle cx="10" cy="28" r="1.5" fill="#207448" />
    </g>
    <text x="1220" y="525" text-anchor="middle" font-family="sans-serif" font-size="27" font-weight="bold" fill="#303a36">
      <tspan x="1220" dy="0">ingress-nginx:</tspan>
      <tspan x="1220" dy="34">writes NGINX config for Pods</tspan>
    </text>
  </g>

  <!-- Controller 2: Contour -->
  <g id="box-contour">
    <rect x="870" y="620" width="640" height="115" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Envoy controller icon -->
    <g transform="translate(905, 649)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <path d="M 18 28 L 28 18 L 38 28 L 28 38 Z" />
      <circle cx="28" cy="28" r="4" fill="#207448" />
    </g>
    <text x="1220" y="670" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan x="1220" dy="0">Contour:</tspan>
      <tspan x="1220" dy="34">programs Envoy</tspan>
    </text>
  </g>

  <!-- Arrows from both Controller boxes pointing at the same Pod boxes -->
  <path d="M 870 532 L 800 532 L 800 635 L 735 635" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <line x1="870" y1="677" x2="735" y2="677" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- ==================== BOTTOM NOTE / TAKEAWAY BAR ==================== -->
  <rect x="50" y="895" width="1500" height="75" rx="14" fill="#207448" />
  <text x="800" y="942" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Many APIs take the plug-in route, such as Ingress and NetworkPolicy.</text>
</svg>'''

pathlib.Path("output_ingress.svg").write_text(svg_content)
print("Saved clean output_ingress.svg")
