#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, subprocess, pathlib

# Let's generate the SVG string cleanly
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>resourceVersion versus generation versus observedGeneration</title>
  <desc>Worked example comparing metadata.resourceVersion, metadata.generation, and status.observedGeneration across four Kubernetes API events.</desc>

  <rect width="1600" height="1080" fill="#f5f8f5"/>

  <!-- Title -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">resourceVersion versus generation</tspan>
    <tspan x="800" dy="56">versus observedGeneration</tspan>
  </text>

  <!-- COLUMN HEADERS -->
  <!-- Col 0: Events Header -->
  <rect x="50" y="145" width="300" height="235" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
  <g transform="translate(175, 170)" stroke="#207448" stroke-width="3.5" fill="none">
    <circle cx="25" cy="24" r="18"/>
    <polyline points="25,12 25,24 34,29" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
  <line x1="70" y1="240" x2="330" y2="240" stroke="#207448" stroke-width="1.5" stroke-dasharray="6 4"/>
  <path d="M 200 260 L 200 350" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
  <polygon points="193,346 200,362 207,346" fill="#207448"/>

  <!-- Col 1 Header: metadata.resourceVersion -->
  <rect x="365" y="145" width="395" height="235" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
  <g transform="translate(537, 160)" stroke="#207448" stroke-width="3" fill="none">
    <ellipse cx="25" cy="11" rx="22" ry="7"/>
    <path d="M 3 11 V 23 C 3 29, 47 29, 47 23 V 11"/>
    <path d="M 3 23 V 35 C 3 41, 47 41, 47 35 V 23"/>
  </g>
  <text x="562" y="235" text-anchor="middle" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448">metadata.resourceVersion</text>
  <text x="562" y="278" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="562" dy="0">resourceVersion</tspan>
    <tspan x="562" dy="28">changes on every write</tspan>
    <tspan x="562" dy="28">(metadata, spec</tspan>
    <tspan x="562" dy="28">or status)</tspan>
  </text>

  <!-- Col 2 Header: metadata.generation -->
  <rect x="775" y="145" width="345" height="235" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
  <g transform="translate(922, 160)" stroke="#207448" stroke-width="3" fill="none">
    <rect x="4" y="5" width="42" height="34" rx="4"/>
    <line x1="4" y1="14" x2="46" y2="14"/>
    <circle cx="10" cy="9.5" r="1.5" fill="#207448"/>
    <circle cx="15" cy="9.5" r="1.5" fill="#207448"/>
    <line x1="12" y1="22" x2="26" y2="22"/>
    <line x1="12" y1="28" x2="36" y2="28"/>
  </g>
  <text x="947" y="235" text-anchor="middle" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448">metadata.generation</text>
  <text x="947" y="285" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="947" dy="0">generation increments</tspan>
    <tspan x="947" dy="32">only when</tspan>
    <tspan x="947" dy="32">spec changes</tspan>
  </text>

  <!-- Col 3 Header: status.observedGeneration -->
  <rect x="1135" y="145" width="415" height="235" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
  <g transform="translate(1317, 160)" stroke="#207448" stroke-width="3" fill="none">
    <circle cx="25" cy="22" r="8"/>
    <path d="M 25 6 V 10 M 25 34 V 38 M 9 22 H 13 M 37 22 H 41 M 14 11 L 17 14 M 33 30 L 36 33 M 14 33 L 17 30 M 33 14 L 36 11" stroke-linecap="round"/>
  </g>
  <text x="1342" y="235" text-anchor="middle" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448">status.observedGeneration</text>
  <text x="1342" y="278" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1342" dy="0">observedGeneration is</tspan>
    <tspan x="1342" dy="28">written by the controller</tspan>
    <tspan x="1342" dy="28">to record the generation</tspan>
    <tspan x="1342" dy="28">it last reconciled</tspan>
  </text>

  <!-- ROW 1: spec edit -->
  <rect x="50" y="395" width="300" height="110" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <circle cx="95" cy="450" r="24" fill="#207448"/>
  <text x="95" y="458" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
  <text x="215" y="458" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">spec edit</text>

  <!-- Row 1, Col 1: RV updates -->
  <rect x="365" y="395" width="395" height="110" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <g transform="translate(537, 432)" stroke="#207448" stroke-width="3" fill="none">
    <path d="M 5 18 A 18 18 0 1 1 35 30" stroke-linecap="round"/>
    <polyline points="29,32 37,31 38,23" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="25" cy="18" r="4" fill="#207448"/>
  </g>

  <!-- Row 1, Cols 2 & 3: controller has not caught up (RED) -->
  <rect x="775" y="395" width="775" height="110" rx="10" fill="#fff5f5" stroke="#c53030" stroke-width="2.5"/>
  <!-- Vector glyphs for generation 7 and observedGeneration 6 -->
  <g transform="translate(850, 439)" stroke="#c53030" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 0 0 L 16 0 L 7 24"/>
  </g>
  <path d="M 900 451 L 930 451" stroke="#c53030" stroke-width="2.5" stroke-dasharray="4 4"/>
  <g transform="translate(960, 439)" stroke="#c53030" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 14 3 C 4 3, 2 9, 2 15 C 2 19, 5 24, 11 24 C 16 24, 17 19, 17 15 C 17 11, 13 9, 8 9"/>
  </g>
  <text x="1235" y="458" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#c53030">controller has not caught up</text>

  <!-- ROW 2: label edit -->
  <rect x="50" y="520" width="300" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <circle cx="95" cy="567" r="24" fill="#207448"/>
  <text x="95" y="575" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
  <text x="215" y="575" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">label edit</text>

  <!-- Row 2, Col 1: RV updates -->
  <rect x="365" y="520" width="395" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <g transform="translate(537, 550)" stroke="#207448" stroke-width="3" fill="none">
    <path d="M 5 18 A 18 18 0 1 1 35 30" stroke-linecap="round"/>
    <polyline points="29,32 37,31 38,23" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="25" cy="18" r="4" fill="#207448"/>
  </g>

  <!-- Row 2, Col 2: Generation stays 7 -->
  <rect x="775" y="520" width="345" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <g transform="translate(939, 555)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 0 0 L 16 0 L 7 24"/>
  </g>

  <!-- Row 2, Col 3: Observed stays 6 -->
  <rect x="1135" y="520" width="415" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <g transform="translate(1334, 555)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 14 3 C 4 3, 2 9, 2 15 C 2 19, 5 24, 11 24 C 16 24, 17 19, 17 15 C 17 11, 13 9, 8 9"/>
  </g>

  <!-- ROW 3: status write by controller -->
  <rect x="50" y="630" width="300" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <circle cx="95" cy="677" r="24" fill="#207448"/>
  <text x="95" y="685" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
  <text x="215" y="667" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="215" dy="0">status write</tspan>
    <tspan x="215" dy="28">by controller</tspan>
  </text>

  <!-- Row 3, Col 1: RV updates -->
  <rect x="365" y="630" width="395" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <g transform="translate(537, 660)" stroke="#207448" stroke-width="3" fill="none">
    <path d="M 5 18 A 18 18 0 1 1 35 30" stroke-linecap="round"/>
    <polyline points="29,32 37,31 38,23" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="25" cy="18" r="4" fill="#207448"/>
  </g>

  <!-- Row 3, Col 2: Generation stays 7 -->
  <rect x="775" y="630" width="345" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <g transform="translate(939, 665)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 0 0 L 16 0 L 7 24"/>
  </g>

  <!-- Row 3, Col 3: Observed stays 6 -->
  <rect x="1135" y="630" width="415" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <g transform="translate(1334, 665)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 14 3 C 4 3, 2 9, 2 15 C 2 19, 5 24, 11 24 C 16 24, 17 19, 17 15 C 17 11, 13 9, 8 9"/>
  </g>

  <!-- ROW 4: controller finishes reconcile -->
  <rect x="50" y="740" width="300" height="110" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <circle cx="95" cy="795" r="24" fill="#207448"/>
  <text x="95" y="803" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
  <text x="215" y="780" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="215" dy="0">controller</tspan>
    <tspan x="215" dy="28">finishes</tspan>
    <tspan x="215" dy="28">reconcile</tspan>
  </text>

  <!-- Row 4, Col 1: RV updates -->
  <rect x="365" y="740" width="395" height="110" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <g transform="translate(537, 777)" stroke="#207448" stroke-width="3" fill="none">
    <path d="M 5 18 A 18 18 0 1 1 35 30" stroke-linecap="round"/>
    <polyline points="29,32 37,31 38,23" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="25" cy="18" r="4" fill="#207448"/>
  </g>

  <!-- Row 4, Cols 2 & 3: status reflects the latest spec (GREEN) -->
  <rect x="775" y="740" width="775" height="110" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
  <!-- Vector glyphs for generation 7 == observedGeneration 7 -->
  <g transform="translate(845, 784)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 0 0 L 16 0 L 7 24"/>
  </g>
  <g transform="translate(895, 792)" stroke="#207448" stroke-width="3" stroke-linecap="round">
    <line x1="0" y1="0" x2="20" y2="0"/>
    <line x1="0" y1="8" x2="20" y2="8"/>
  </g>
  <g transform="translate(945, 784)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 0 0 L 16 0 L 7 24"/>
  </g>
  <text x="1235" y="803" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">status reflects the latest spec</text>

  <!-- SIDE NOTES / BOTTOM CARDS -->
  <!-- Card 1: resourceVersion is opaque... -->
  <rect x="50" y="880" width="520" height="160" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g transform="translate(68, 930)" stroke="#207448" stroke-width="3" fill="none">
    <path d="M 20 4 L 4 10 V 22 C 4 30, 20 36, 20 36 C 20 36, 36 30, 36 22 V 10 Z" stroke-linejoin="round"/>
  </g>
  <text x="122" y="922" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="122" dy="0">resourceVersion is opaque,</tspan>
    <tspan x="122" dy="30">compare only for equality,</tspan>
    <tspan x="122" dy="30">derived from the</tspan>
    <tspan x="122" dy="30">etcd mod_revision</tspan>
  </text>

  <!-- Card 2: uid identifies one instance... -->
  <rect x="590" y="880" width="460" height="160" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g transform="translate(608, 930)" stroke="#207448" stroke-width="3" fill="none">
    <rect x="6" y="5" width="28" height="34" rx="4"/>
    <circle cx="20" cy="16" r="5"/>
    <path d="M 11 31 C 11 26, 15 25, 20 25 C 25 25, 29 26, 29 31" stroke-linecap="round"/>
  </g>
  <text x="660" y="938" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="660" dy="0">uid identifies</tspan>
    <tspan x="660" dy="32">one instance; a recreated</tspan>
    <tspan x="660" dy="32">object gets a new uid</tspan>
  </text>

  <!-- Card 3: kubectl rollout status uses this (ORANGE HIGHLIGHT) -->
  <rect x="1070" y="880" width="480" height="160" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="3"/>
  <g transform="translate(1090, 932)" stroke="#207448" stroke-width="3" fill="none">
    <rect x="4" y="6" width="38" height="30" rx="4"/>
    <polyline points="11,15 17,21 11,27" stroke-linecap="round" stroke-linejoin="round"/>
    <line x1="21" y1="27" x2="31" y2="27" stroke-linecap="round"/>
  </g>
  <text x="1150" y="948" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="1150" dy="0">kubectl rollout status</tspan>
    <tspan x="1150" dy="34">uses this</tspan>
  </text>
</svg>'''

pathlib.Path("candidate.svg").write_text(svg)
print("Saved candidate.svg")
