#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, pathlib, subprocess

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1180" width="1600" height="1180">
  <title>From a MAC address to the IPv6 neighbour address: a worked derivation</title>
  <desc>Visual derivation of an IPv6 neighbour address and solicited-node multicast MAC from a MAC address using modified EUI-64 and ICMPv6 mechanisms.</desc>

  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1180" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">From a MAC address to the</tspan>
    <tspan x="800" dy="56" fill="#207448">IPv6 neighbour address: a worked derivation</tspan>
  </text>

  <!-- ==================== LEFT COLUMN: DERIVATION ==================== -->

  <!-- Row 1: MAC address -->
  <g id="row-1">
    <rect x="40" y="145" width="960" height="90" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Icon: Network card / MAC outline -->
    <g transform="translate(65, 162)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="12" width="48" height="32" rx="4" />
      <line x1="12" y1="44" x2="12" y2="52" />
      <line x1="20" y1="44" x2="20" y2="52" />
      <line x1="28" y1="44" x2="28" y2="52" />
      <line x1="36" y1="44" x2="36" y2="52" />
      <circle cx="16" cy="28" r="4" fill="#207448" />
      <circle cx="28" cy="28" r="4" fill="#207448" />
      <circle cx="40" cy="28" r="4" fill="#207448" />
    </g>
    <text x="145" y="200" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan x="145" dy="0" fill="#207448">MAC</tspan>
      <tspan dx="12" font-family="monospace">01:23:45:67:89:ab</tspan>
    </text>
  </g>

  <!-- Arrow 1 -> 2 -->
  <line x1="520" y1="235" x2="520" y2="275" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- Row 2: EUI-64 -->
  <g id="row-2">
    <rect x="40" y="275" width="960" height="150" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Icon: Bit-shift / insert transformation -->
    <g transform="translate(65, 322)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="20" height="44" rx="4" />
      <rect x="32" y="6" width="20" height="44" rx="4" />
      <line x1="16" y1="28" x2="40" y2="28" />
      <polyline points="24,20 32,28 24,36" />
    </g>
    <text x="145" y="335" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="145" dy="0" font-weight="bold" fill="#207448">Flip the U/L bit and insert ff:fe in the middle:</tspan>
      <tspan x="145" dy="38" font-weight="bold">modified EUI-64</tspan>
      <tspan dx="10" font-family="monospace" font-weight="bold" fill="#207448">0323:45ff:fe67:89ab</tspan>
    </text>
  </g>

  <!-- Arrow 2 -> 3 -->
  <line x1="520" y1="425" x2="520" y2="465" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- Row 3: Link-local address -->
  <g id="row-3">
    <rect x="40" y="465" width="960" height="130" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Icon: Network host link-local address -->
    <g transform="translate(65, 502)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <path d="M 6 28 H 50" />
      <path d="M 28 6 C 36 14 40 22 40 28 C 40 34 36 42 28 50 C 20 42 16 34 16 28 C 16 22 20 14 28 6 Z" />
    </g>
    <text x="145" y="522" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="145" dy="0" font-weight="bold" fill="#207448">Link-local address fe80::/64 plus the interface ID:</tspan>
      <tspan x="145" dy="38" font-family="monospace" font-weight="bold">fe80::323:45ff:fe67:89ab</tspan>
    </text>
  </g>

  <!-- Arrow 3 -> 4 -->
  <line x1="520" y1="595" x2="520" y2="635" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- Row 4: Solicited-node multicast + Ethernet destination -->
  <g id="row-4-multicast">
    <rect x="40" y="635" width="560" height="265" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Icon: Multicast group propagation -->
    <g transform="translate(65, 665)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="28" r="6" fill="#207448" />
      <path d="M 26 16 A 16 16 0 0 1 26 40" />
      <path d="M 34 8 A 26 26 0 0 1 34 48" />
      <path d="M 42 0 A 36 36 0 0 1 42 56" />
    </g>
    <text x="145" y="685" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="145" dy="0" font-weight="bold" fill="#207448">Solicited-node multicast:</tspan>
      <tspan x="145" dy="36" font-family="monospace" font-weight="bold">ff02::1:ff67:89ab,</tspan>
      <tspan x="145" dy="34">from the last 24 bits</tspan>
      <tspan x="145" dy="34">(67:89:ab) of the address</tspan>
    </text>
  </g>

  <!-- Arrow to Ethernet destination -->
  <line x1="600" y1="765" x2="660" y2="765" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- Ethernet destination (orange) -->
  <g id="row-4-ethernet">
    <rect x="660" y="635" width="340" height="265" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="3" />
    <!-- Icon: Ethernet destination target (orange) -->
    <g transform="translate(802, 665)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="34" rx="6" />
      <line x1="16" y1="42" x2="16" y2="48" />
      <line x1="40" y1="42" x2="40" y2="48" />
      <circle cx="28" cy="25" r="7" />
    </g>
    <text x="830" y="755" text-anchor="middle" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="830" dy="0" font-weight="bold" fill="#db8129">Ethernet destination</tspan>
      <tspan x="830" dy="38" font-family="monospace" font-weight="bold">33:33:ff:67:89:ab</tspan>
    </text>
  </g>

  <!-- ==================== RIGHT COLUMN: PANELS ==================== -->

  <!-- Right Panel: Why this beats ARP -->
  <g id="panel-why-beats-arp">
    <rect x="1040" y="145" width="520" height="410" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <path d="M 1040 157 A 12 12 0 0 1 1052 145 L 1548 145 A 12 12 0 0 1 1560 157 L 1560 215 L 1040 215 Z" fill="#e8f1ea" />
    <text x="1300" y="190" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Why this beats ARP</text>

    <!-- Icon: Filtered unicast vs broadcast -->
    <g transform="translate(1065, 230)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="6,8 50,8 34,30 34,48 22,42 22,30" />
    </g>

    <text x="1135" y="252" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1135" dy="0">only hosts whose</tspan>
      <tspan x="1135" dy="32" font-weight="bold" fill="#207448">address ends in those</tspan>
      <tspan x="1135" dy="32" font-weight="bold" fill="#207448">24 bits receive the</tspan>
      <tspan x="1135" dy="32">solicitation, instead</tspan>
      <tspan x="1135" dy="32">of every host hearing</tspan>
      <tspan x="1135" dy="32">a broadcast: a question</tspan>
      <tspan x="1135" dy="32" font-weight="bold" fill="#207448">sent to one block, not</tspan>
      <tspan x="1135" dy="32">shouted across a stadium</tspan>
    </text>
  </g>

  <!-- Side note: RFC 7217 -->
  <g id="side-note">
    <rect x="1040" y="580" width="520" height="320" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Icon: Privacy shield / lock -->
    <g transform="translate(1065, 615)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 28 C 48 42 28 50 28 50 C 28 50 8 42 8 28 V 14 Z" />
      <circle cx="28" cy="26" r="4" fill="#207448" />
      <path d="M 28 30 V 38" />
    </g>
    <text x="1135" y="635" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1135" dy="0">Modern systems may use a</tspan>
      <tspan x="1135" dy="34" font-weight="bold" fill="#207448">random stable privacy ID</tspan>
      <tspan x="1135" dy="34">(RFC 7217) instead; the</tspan>
      <tspan x="1135" dy="34">Linux setting is</tspan>
      <tspan x="1135" dy="34" font-family="monospace" font-weight="bold" fill="#207448">addr_gen_mode</tspan>
    </text>
  </g>

  <!-- ==================== BELOW: ICMPv6 TYPES ==================== -->
  <g id="icmpv6-strip">
    <rect x="40" y="930" width="1520" height="120" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Icon: Packet list / protocol messages -->
    <g transform="translate(65, 962)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="5" />
      <line x1="14" y1="20" x2="42" y2="20" />
      <line x1="14" y1="28" x2="42" y2="28" />
      <line x1="14" y1="36" x2="32" y2="36" />
    </g>
    <text x="145" y="980" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="145" dy="0" font-weight="bold" fill="#207448">ICMPv6 types: 133 Router Solicitation (to ff02::2), 134 Router Advertisement,</tspan>
      <tspan x="145" dy="36">135 Neighbor Solicitation, 136 Neighbor Advertisement, 137 Redirect</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1075" width="1520" height="75" rx="10" fill="#207448" />
    <text x="800" y="1122" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">IPv6 has no broadcast, so it uses ICMPv6 messages to multicast addresses</text>
  </g>
</svg>'''

with open('test_eui64.svg', 'w') as f:
    f.write(svg_content)

print("Saved test_eui64.svg")
