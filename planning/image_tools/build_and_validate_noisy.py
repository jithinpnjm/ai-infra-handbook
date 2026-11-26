#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import subprocess
import os

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1140" width="1600" height="1140">
  <title>Eleven long requests leave room for five normal ones</title>
  <desc>KV cache arithmetic and multi-tenant noisy-neighbour control comparing normal request capacity of 137 against GPU capacity collapse to 5 requests when 11 long requests run.</desc>

  <rect width="1600" height="1140" fill="#f5f8f5"/>

  <!-- Title (48px bold) -->
  <text x="800" y="70" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Eleven long requests leave room for five normal ones</text>

  <!-- ==================== LEFT COLUMN: KV Arithmetic and Capacity Bars ==================== -->
  <rect x="50" y="115" width="730" height="770" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

  <!-- Left Card 1: KV Arithmetic Assumptions -->
  <g id="kv-arithmetic-assumptions">
    <rect x="70" y="135" width="690" height="120" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Processor chip / arithmetic unit (56x56) -->
    <g transform="translate(90, 167)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="36" height="36" rx="4"/>
      <rect x="18" y="18" width="20" height="20" rx="2"/>
      <line x1="18" y1="3" x2="18" y2="10"/>
      <line x1="28" y1="3" x2="28" y2="10"/>
      <line x1="38" y1="3" x2="38" y2="10"/>
      <line x1="18" y1="46" x2="18" y2="53"/>
      <line x1="28" y1="46" x2="28" y2="53"/>
      <line x1="38" y1="46" x2="38" y2="53"/>
      <line x1="3" y1="18" x2="10" y2="18"/>
      <line x1="3" y1="28" x2="10" y2="28"/>
      <line x1="3" y1="38" x2="10" y2="38"/>
      <line x1="46" y1="18" x2="53" y2="18"/>
      <line x1="46" y1="28" x2="53" y2="28"/>
      <line x1="46" y1="38" x2="53" y2="38"/>
    </g>
    <text x="165" y="173" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">
      <tspan x="165" dy="0">KV arithmetic with 147,456 B per token</tspan>
      <tspan x="165" dy="36">and a 50.6 GB KV budget (assumed)</tspan>
    </text>
  </g>

  <!-- Left Card 2: One normal request -->
  <g id="request-normal">
    <rect x="70" y="270" width="690" height="85" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <!-- Icon: Single compact request document (40x40) -->
    <g transform="translate(95, 292)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="4" width="24" height="32" rx="3"/>
      <line x1="14" y1="12" x2="26" y2="12"/>
      <line x1="14" y1="20" x2="26" y2="20"/>
      <line x1="14" y1="28" x2="20" y2="28"/>
    </g>
    <text x="165" y="322" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">One normal request: 2,500 tokens = 0.37 GB</text>
  </g>

  <!-- Left Card 3: One long request -->
  <g id="request-long">
    <rect x="70" y="370" width="690" height="85" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <!-- Icon: Stacked long-request documents (40x40) -->
    <g transform="translate(95, 392)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="12" y="8" width="24" height="28" rx="3"/>
      <path d="M8 30 V8 A3 3 0 0 1 11 5 H30"/>
      <line x1="18" y1="16" x2="30" y2="16"/>
      <line x1="18" y1="24" x2="30" y2="24"/>
    </g>
    <text x="165" y="422" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">One long request: 30,000 tokens = 4.42 GB</text>
  </g>

  <!-- Left Card 4: Bar A - Normal requests alone -->
  <g id="bar-a">
    <rect x="70" y="470" width="690" height="120" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="95" y="508" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">normal requests alone: 50.6 / 0.369 = 137 fit</text>
    <!-- Visual Bar A: Full capacity for 137 normal requests -->
    <rect x="95" y="530" width="640" height="38" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <rect x="95" y="530" width="640" height="38" rx="6" fill="#207448"/>
  </g>

  <!-- Left Card 5: Bar B - Long requests fill GPU -->
  <g id="bar-b">
    <rect x="70" y="605" width="690" height="120" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="95" y="643" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">long requests that fill the GPU: 50.6 / 4.42 = 11</text>
    <!-- Visual Bar B: 11 long requests take 48.66 GB of 50.6 GB (96.2%) -->
    <rect x="95" y="665" width="640" height="38" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <rect x="95" y="665" width="615" height="38" rx="6" fill="#207448"/>
  </g>

  <!-- Left Card 6: Bar C - Left for others (Orange Highlight) -->
  <g id="bar-c">
    <rect x="70" y="740" width="690" height="125" rx="12" fill="#fbeee2" stroke="#db8129" stroke-width="3"/>
    <text x="95" y="778" font-family="sans-serif" font-size="25" font-weight="bold" fill="#db8129">left for others when 11 long run: 50.6 - 48.7 = 1.94 GB = 5 requests</text>
    <!-- Visual Bar C: Only 1.94 GB left (3.8% of capacity = 25px out of 640px) -->
    <rect x="95" y="800" width="640" height="38" rx="6" fill="#ffffff" stroke="#db8129" stroke-width="1.5"/>
    <rect x="95" y="800" width="25" height="38" rx="4" fill="#db8129"/>
  </g>

  <!-- ==================== RIGHT COLUMN: Mitigations & Protection ==================== -->
  <rect x="820" y="115" width="730" height="770" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

  <!-- Right Card 1: Per-Tenant Cap at 25% -->
  <g id="card-cap">
    <rect x="840" y="135" width="690" height="225" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Shield with quota ceiling (56x56) -->
    <g transform="translate(865, 175)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M28 8 L48 16 C48 36 28 50 28 50 C28 50 8 36 8 16 Z"/>
      <line x1="16" y1="28" x2="40" y2="28"/>
      <circle cx="28" cy="20" r="3" fill="#207448"/>
      <path d="M22 38 L28 33 L34 38"/>
    </g>
    <text x="945" y="210" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">
      <tspan x="945" dy="0">cap at 25 percent of KV:</tspan>
      <tspan x="945" dy="38">12.65 / 4.42 = 2 long requests</tspan>
    </text>
    <!-- Visual: 25% Cap Bar preserving 75% for others -->
    <rect x="945" y="280" width="555" height="40" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <rect x="945" y="280" width="139" height="40" rx="6" fill="#207448"/>
  </g>

  <!-- Right Card 2: Failure Line / Router Trap -->
  <g id="card-failure">
    <rect x="840" y="380" width="690" height="235" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Router / network node warning (56x56) -->
    <g transform="translate(865, 430)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <line x1="28" y1="16" x2="28" y2="30"/>
      <circle cx="28" cy="38" r="2.5" fill="#207448"/>
      <path d="M12 16 L20 20 L12 24"/>
      <path d="M44 32 L36 36 L44 40"/>
    </g>
    <text x="945" y="435" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">
      <tspan x="945" dy="0">cap is per replica but the router</tspan>
      <tspan x="945" dy="36">sends all of the tenant's long requests</tspan>
      <tspan x="945" dy="36">to one replica: the cap must hold</tspan>
      <tspan x="945" dy="36">across the pool</tspan>
    </text>
  </g>

  <!-- Right Card 3: Isolation Tiers -->
  <g id="card-isolation">
    <rect x="840" y="635" width="690" height="230" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Tiered isolation layers (56x56) -->
    <g transform="translate(865, 680)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="10" width="40" height="10" rx="3"/>
      <rect x="8" y="24" width="40" height="10" rx="3"/>
      <rect x="8" y="38" width="40" height="10" rx="3"/>
      <circle cx="15" cy="15" r="2" fill="#207448"/>
      <circle cx="15" cy="29" r="2" fill="#207448"/>
      <circle cx="15" cy="43" r="2" fill="#207448"/>
    </g>
    <text x="945" y="700" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">
      <tspan x="945" dy="0">shared pool, long-context pool,</tspan>
      <tspan x="945" dy="38">dedicated endpoint</tspan>
    </text>
    <!-- Visual: 3 isolation tier badges -->
    <g transform="translate(945, 770)">
      <rect x="0" y="0" width="160" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <rect x="180" y="0" width="180" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <rect x="380" y="0" width="175" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    </g>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="takeaway-headline">
    <rect x="50" y="925" width="1500" height="165" rx="14" fill="#207448" stroke="#185635" stroke-width="2"/>
    <!-- Icon: Key finding / lightbulb (56x56) -->
    <g transform="translate(85, 960)" stroke="#ffffff" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M16 26 A14 14 0 1 1 40 26 C40 31 35 34 35 39 H21 C21 34 16 31 16 26 Z"/>
      <line x1="21" y1="45" x2="35" y2="45"/>
      <line x1="24" y1="51" x2="32" y2="51"/>
      <line x1="28" y1="4" x2="28" y2="8"/>
      <line x1="10" y1="12" x2="14" y2="15"/>
      <line x1="46" y1="12" x2="42" y2="15"/>
    </g>
    <text x="170" y="990" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">
      <tspan x="170" dy="0">eleven long requests take capacity from 137 down to 5 for everyone else:</tspan>
      <tspan x="170" dy="48" fill="#e8f1ea">the case for charging by cost (tokens x context), not request count</tspan>
    </text>
  </g>
</svg>
"""

with open("test_candidate_noisy.svg", "w") as f:
    f.write(svg_content.strip())

print("Saved test_candidate_noisy.svg")
