#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import json

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1100" width="1600" height="1100">
  <title>How the kernel walks /home/alice/train.py one name at a time</title>
  <desc>Technical diagram illustrating how the Linux kernel resolves a file path component by component through directory tables to the inode and data blocks.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 14 14" refX="11" refY="7" markerWidth="14" markerHeight="14" orient="auto-start-reverse">
      <path d="M 1 2 L 11 7 L 1 12 Z" fill="#207448" />
    </marker>
    <filter id="shadow" x="-3%" y="-4%" width="106%" height="110%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#000" flood-opacity="0.06" />
    </filter>
  </defs>

  <rect width="1600" height="1100" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="60" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">How the kernel walks /home/alice/train.py </tspan><tspan x="800" dy="54">one name at a time</tspan>
  </text>

  <!-- Path string container -->
  <g filter="url(#shadow)">
    <rect x="420" y="150" width="760" height="96" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <text x="800" y="196" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#303a36">/home/alice/train.py</text>
    <!-- Component underlines for matching steps -->
    <!-- Under home (step 1) -->
    <rect x="630" y="212" width="76" height="6" rx="3" fill="#207448" />
    <!-- Under alice (step 2) -->
    <rect x="726" y="212" width="95" height="6" rx="3" fill="#207448" />
    <!-- Under train.py (step 3) -->
    <rect x="841" y="212" width="152" height="6" rx="3" fill="#207448" />
  </g>

  <!-- Table 1: Root directory / -->
  <g filter="url(#shadow)">
    <rect x="40" y="285" width="240" height="295" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />
    <!-- Folder icon with root slash -->
    <g transform="translate(132, 305)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 4 12 L 20 12 L 26 18 L 52 18 L 52 48 L 4 48 Z" />
      <line x1="22" y1="40" x2="34" y2="24" stroke-width="3.5" />
    </g>
    <text x="160" y="385" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">
      <tspan x="160" dy="0">Root </tspan><tspan x="160" dy="32">directory /</tspan>
    </text>
    <!-- Inner directory table row -->
    <rect x="55" y="465" width="210" height="90" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <line x1="55" y1="510" x2="265" y2="510" stroke="#207448" stroke-width="1" stroke-dasharray="4,4" />
    <text x="160" y="500" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="160" dy="0">home -&gt; </tspan><tspan x="160" dy="36">inode A</tspan>
    </text>
  </g>

  <!-- Arrow 1: look up home -->
  <line x1="280" y1="432" x2="343" y2="432" stroke="#207448" stroke-width="4" />
  <line x1="392" y1="432" x2="453" y2="432" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />
  <circle cx="367" cy="432" r="24" fill="#207448" />
  <text x="367" y="441" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
  <text x="367" y="365" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="367" dy="0">look up </tspan><tspan x="367" dy="30">home</tspan>
  </text>

  <!-- Table 2: Directory /home (inode A) -->
  <g filter="url(#shadow)">
    <rect x="455" y="285" width="240" height="295" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />
    <!-- Folder icon -->
    <g transform="translate(547, 305)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 4 12 L 20 12 L 26 18 L 52 18 L 52 48 L 4 48 Z" />
    </g>
    <text x="575" y="380" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">
      <tspan x="575" dy="0">Directory </tspan><tspan x="575" dy="30">/home </tspan><tspan x="575" dy="28" font-size="24">(inode A)</tspan>
    </text>
    <!-- Inner directory table row -->
    <rect x="470" y="465" width="210" height="90" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <line x1="470" y1="510" x2="680" y2="510" stroke="#207448" stroke-width="1" stroke-dasharray="4,4" />
    <text x="575" y="500" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="575" dy="0">alice -&gt; </tspan><tspan x="575" dy="36">inode B</tspan>
    </text>
  </g>

  <!-- Arrow 2: look up alice -->
  <line x1="695" y1="432" x2="758" y2="432" stroke="#207448" stroke-width="4" />
  <line x1="807" y1="432" x2="868" y2="432" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />
  <circle cx="782" cy="432" r="24" fill="#207448" />
  <text x="782" y="441" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
  <text x="782" y="365" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="782" dy="0">look up </tspan><tspan x="782" dy="30">alice</tspan>
  </text>

  <!-- Table 3: Directory /home/alice (inode B) -->
  <g filter="url(#shadow)">
    <rect x="870" y="285" width="250" height="295" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />
    <!-- Folder icon -->
    <g transform="translate(967, 305)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 4 12 L 20 12 L 26 18 L 52 18 L 52 48 L 4 48 Z" />
    </g>
    <text x="995" y="380" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">
      <tspan x="995" dy="0">Directory </tspan><tspan x="995" dy="30">/home/alice </tspan><tspan x="995" dy="28" font-size="24">(inode B)</tspan>
    </text>
    <!-- Inner directory table row -->
    <rect x="885" y="465" width="220" height="90" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <line x1="885" y1="510" x2="1105" y2="510" stroke="#207448" stroke-width="1" stroke-dasharray="4,4" />
    <text x="995" y="500" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="995" dy="0">train.py -&gt; </tspan><tspan x="995" dy="36">inode C</tspan>
    </text>
  </g>

  <!-- Arrow 3: look up train.py -->
  <line x1="1120" y1="432" x2="1185" y2="432" stroke="#207448" stroke-width="4" />
  <line x1="1234" y1="432" x2="1298" y2="432" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />
  <circle cx="1210" cy="432" r="24" fill="#207448" />
  <text x="1210" y="441" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
  <text x="1210" y="365" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="1210" dy="0">look up </tspan><tspan x="1210" dy="30">train.py</tspan>
  </text>

  <!-- Final box: Inode C -->
  <g filter="url(#shadow)">
    <rect x="1300" y="285" width="260" height="340" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />
    <!-- Index card / metadata icon -->
    <g transform="translate(1402, 305)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="42" rx="4" />
      <line x1="14" y1="18" x2="42" y2="18" />
      <line x1="14" y1="28" x2="34" y2="28" />
      <line x1="14" y1="38" x2="26" y2="38" />
    </g>
    <text x="1430" y="385" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1430" dy="0" font-weight="bold" fill="#207448">Inode C: type, </tspan><tspan x="1430" dy="32">permissions, </tspan><tspan x="1430" dy="32">owner, size, </tspan><tspan x="1430" dy="32">times, </tspan><tspan x="1430" dy="32">link count, </tspan><tspan x="1430" dy="32">pointers to </tspan><tspan x="1430" dy="32">data blocks</tspan>
    </text>
  </g>

  <!-- Arrow 4: read the inode and its data -->
  <line x1="1430" y1="625" x2="1430" y2="671" stroke="#207448" stroke-width="4" />
  <line x1="1430" y1="720" x2="1430" y2="763" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />
  <circle cx="1430" cy="695" r="24" fill="#207448" />
  <text x="1430" y="704" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
  <text x="1390" y="683" text-anchor="end" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="1390" dy="0">read the inode </tspan><tspan x="1390" dy="30">and its data</tspan>
  </text>

  <!-- Stack: Data blocks on the device -->
  <g filter="url(#shadow)">
    <rect x="1300" y="765" width="260" height="175" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />
    <!-- Stack of disk cylinder blocks icon -->
    <g transform="translate(1402, 782)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="12" rx="22" ry="7" />
      <path d="M 6 12 v 10 c 0 4 10 7 22 7 s 22 -3 22 -7 v -10" />
      <path d="M 6 22 v 10 c 0 4 10 7 22 7 s 22 -3 22 -7 v -10" />
      <path d="M 6 32 v 10 c 0 4 10 7 22 7 s 22 -3 22 -7 v -10" />
    </g>
    <text x="1430" y="878" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="1430" dy="0">Data blocks </tspan><tspan x="1430" dy="32">on the device</tspan>
    </text>
  </g>

  <!-- Callout in orange under table 3 -->
  <g filter="url(#shadow)">
    <rect x="805" y="650" width="380" height="230" rx="14" fill="#fffaf5" stroke="#db8129" stroke-width="3.5" />
    <!-- Bookmark / record card icon in orange -->
    <g transform="translate(967, 670)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 6 L 44 6 L 44 48 L 28 36 L 12 48 Z" />
    </g>
    <text x="995" y="745" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">
      <tspan x="995" dy="0">The name lives </tspan><tspan x="995" dy="32">in the directory; </tspan><tspan x="995" dy="32">everything else </tspan><tspan x="995" dy="32">lives in the </tspan><tspan x="995" dy="32">inode</tspan>
    </text>
  </g>

  <!-- Small note at the bottom -->
  <g filter="url(#shadow)">
    <rect x="40" y="990" width="1520" height="68" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="800" y="1033" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">rename = change one table row, so it is instant on one filesystem</text>
  </g>
</svg>'''

with open("test_candidate_p3_0103.svg", "w") as f:
    f.write(svg_code)

print("Saved test_candidate_p3_0103.svg")
