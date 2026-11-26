import xml.etree.ElementTree as ET
import re

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1020" viewBox="0 0 1600 1020">
  <title>Capacity left after a spine fails</title>
  <desc>Visual infographic explaining capacity left after a spine switch fails, showing the formula capacity kept = (S-1)/S of uplink capacity, comparing 32 spines at 96.9% against 4 spines at 75%, with a leaf switch uplink diagram.</desc>

  <!-- Background -->
  <rect width="1600" height="1020" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Capacity left after a spine fails</text>

  <!-- Formula Card (Monospace) -->
  <rect x="50" y="100" width="1500" height="85" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  <g transform="translate(80, 115)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="4" width="46" height="46" rx="8" />
    <path d="M 16 27 L 24 27 M 30 27 L 38 27" />
    <path d="M 27 18 L 27 36" />
    <path d="M 16 38 L 38 16" />
  </g>
  <text x="800" y="153" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36">capacity kept = (S-1)/S of uplink capacity</text>

  <!-- Left Panel: Leaf Switch with Uplinks (One Greyed Out) -->
  <rect x="50" y="215" width="480" height="535" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  
  <!-- Switch Icon for Left Card -->
  <g transform="translate(262, 235)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="8" width="48" height="40" rx="6" />
    <line x1="4" y1="28" x2="52" y2="28" />
    <circle cx="16" cy="18" r="3" fill="#207448" />
    <circle cx="28" cy="18" r="3" fill="#207448" />
    <circle cx="40" cy="18" r="3" fill="#207448" />
    <circle cx="16" cy="38" r="3" fill="#207448" />
    <circle cx="28" cy="38" r="3" fill="#207448" />
    <circle cx="40" cy="38" r="3" fill="#207448" />
  </g>

  <!-- 4 Spine Switches at Top -->
  <!-- Spine 1 -->
  <rect x="85" y="325" width="80" height="50" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <circle cx="105" cy="350" r="4" fill="#207448" />
  <circle cx="125" cy="350" r="4" fill="#207448" />
  <circle cx="145" cy="350" r="4" fill="#207448" />

  <!-- Spine 2 -->
  <rect x="185" y="325" width="80" height="50" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <circle cx="205" cy="350" r="4" fill="#207448" />
  <circle cx="225" cy="350" r="4" fill="#207448" />
  <circle cx="245" cy="350" r="4" fill="#207448" />

  <!-- Spine 3 -->
  <rect x="285" y="325" width="80" height="50" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <circle cx="305" cy="350" r="4" fill="#207448" />
  <circle cx="325" cy="350" r="4" fill="#207448" />
  <circle cx="345" cy="350" r="4" fill="#207448" />

  <!-- Spine 4 (Failed / Inactive) -->
  <rect x="385" y="325" width="80" height="50" rx="8" fill="#f5f8f5" stroke="#a0b0a5" stroke-width="2.5" stroke-dasharray="6 4" />
  <line x1="413" y1="338" x2="437" y2="362" stroke="#a0b0a5" stroke-width="3.5" stroke-linecap="round" />
  <line x1="437" y1="338" x2="413" y2="362" stroke="#a0b0a5" stroke-width="3.5" stroke-linecap="round" />

  <!-- Uplinks from Leaf to Spines -->
  <line x1="125" y1="565" x2="125" y2="375" stroke="#207448" stroke-width="4.5" />
  <line x1="225" y1="565" x2="225" y2="375" stroke="#207448" stroke-width="4.5" />
  <line x1="325" y1="565" x2="325" y2="375" stroke="#207448" stroke-width="4.5" />
  <!-- Uplink 4: Greyed Out Link -->
  <line x1="425" y1="565" x2="425" y2="375" stroke="#a0b0a5" stroke-width="4.5" stroke-dasharray="8 6" />
  <circle cx="425" cy="470" r="14" fill="#f5f8f5" stroke="#a0b0a5" stroke-width="2.5" />
  <line x1="417" y1="462" x2="433" y2="478" stroke="#a0b0a5" stroke-width="3" stroke-linecap="round" />
  <line x1="433" y1="462" x2="417" y2="478" stroke="#a0b0a5" stroke-width="3" stroke-linecap="round" />

  <!-- Leaf Switch Chassis -->
  <rect x="85" y="565" width="410" height="65" rx="10" fill="#ffffff" stroke="#207448" stroke-width="3.5" />
  <!-- Ports on Leaf Switch -->
  <circle cx="125" cy="580" r="4.5" fill="#207448" />
  <circle cx="225" cy="580" r="4.5" fill="#207448" />
  <circle cx="325" cy="580" r="4.5" fill="#207448" />
  <circle cx="425" cy="580" r="4.5" fill="#a0b0a5" />

  <circle cx="135" cy="615" r="4" fill="#207448" />
  <circle cx="195" cy="615" r="4" fill="#207448" />
  <circle cx="255" cy="615" r="4" fill="#207448" />
  <circle cx="315" cy="615" r="4" fill="#207448" />
  <circle cx="375" cy="615" r="4" fill="#207448" />
  <circle cx="435" cy="615" r="4" fill="#207448" />

  <!-- Downlinks to Endpoints -->
  <line x1="135" y1="630" x2="135" y2="685" stroke="#207448" stroke-width="3.5" />
  <line x1="195" y1="630" x2="195" y2="685" stroke="#207448" stroke-width="3.5" />
  <line x1="255" y1="630" x2="255" y2="685" stroke="#207448" stroke-width="3.5" />
  <line x1="315" y1="630" x2="315" y2="685" stroke="#207448" stroke-width="3.5" />
  <line x1="375" y1="630" x2="375" y2="685" stroke="#207448" stroke-width="3.5" />
  <line x1="435" y1="630" x2="435" y2="685" stroke="#207448" stroke-width="3.5" />

  <!-- Endpoint blocks -->
  <rect x="115" y="685" width="40" height="22" rx="4" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <rect x="175" y="685" width="40" height="22" rx="4" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <rect x="235" y="685" width="40" height="22" rx="4" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <rect x="295" y="685" width="40" height="22" rx="4" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <rect x="355" y="685" width="40" height="22" rx="4" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <rect x="415" y="685" width="40" height="22" rx="4" fill="#ffffff" stroke="#207448" stroke-width="2" />

  <!-- ==================== RIGHT COLUMN: TWO BARS ==================== -->
  <!-- Top Bar: S = 32 Spines -->
  <rect x="560" y="215" width="990" height="250" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  <g transform="translate(590, 235)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="44" rx="4" />
    <line x1="4" y1="20" x2="52" y2="20" />
    <line x1="4" y1="34" x2="52" y2="34" />
    <circle cx="12" cy="13" r="2.5" fill="#207448" />
    <circle cx="20" cy="13" r="2.5" fill="#207448" />
    <circle cx="12" cy="27" r="2.5" fill="#207448" />
    <circle cx="20" cy="27" r="2.5" fill="#207448" />
    <circle cx="12" cy="41" r="2.5" fill="#207448" />
    <circle cx="20" cy="41" r="2.5" fill="#207448" />
  </g>
  <text x="668" y="272" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">S = 32 spines, one down: 96.9%</text>

  <!-- 32-Spines Bar Track (900 px wide) -->
  <rect x="600" y="330" width="910" height="72" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
  <!-- Filled 96.9% = 31/32 = 881.56 px -->
  <rect x="600" y="330" width="882" height="72" rx="12" fill="#207448" />
  <!-- Dividing tick lines for 32 spines (every 28.4375 px) -->
  <line x1="628" y1="330" x2="628" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="657" y1="330" x2="657" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="685" y1="330" x2="685" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="714" y1="330" x2="714" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="742" y1="330" x2="742" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="770" y1="330" x2="770" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="799" y1="330" x2="799" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="827" y1="330" x2="827" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="856" y1="330" x2="856" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="884" y1="330" x2="884" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="913" y1="330" x2="913" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="941" y1="330" x2="941" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="969" y1="330" x2="969" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="998" y1="330" x2="998" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1026" y1="330" x2="1026" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1055" y1="330" x2="1055" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1083" y1="330" x2="1083" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1112" y1="330" x2="1112" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1140" y1="330" x2="1140" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1168" y1="330" x2="1168" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1197" y1="330" x2="1197" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1225" y1="330" x2="1225" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1254" y1="330" x2="1254" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1282" y1="330" x2="1282" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1311" y1="330" x2="1311" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1339" y1="330" x2="1339" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1367" y1="330" x2="1367" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1396" y1="330" x2="1396" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1424" y1="330" x2="1424" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <line x1="1453" y1="330" x2="1453" y2="402" stroke="#ffffff" stroke-width="1.5" opacity="0.35" />
  <!-- Lost 1/32 slice: 3.1% -->
  <line x1="1482" y1="330" x2="1482" y2="402" stroke="#a0b0a5" stroke-width="2" stroke-dasharray="4 3" />
  <line x1="1487" y1="335" x2="1505" y2="397" stroke="#a0b0a5" stroke-width="1.5" stroke-linecap="round" />

  <!-- Bottom Bar: S = 4 Spines (Orange - Single Most Important Item) -->
  <rect x="560" y="500" width="990" height="250" rx="16" fill="#e8f1ea" stroke="#db8129" stroke-width="3" />
  <g transform="translate(590, 520)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="44" rx="4" />
    <line x1="4" y1="20" x2="52" y2="20" />
    <line x1="4" y1="34" x2="52" y2="34" />
    <circle cx="12" cy="13" r="2.5" fill="#207448" />
    <circle cx="20" cy="13" r="2.5" fill="#207448" />
    <circle cx="12" cy="27" r="2.5" fill="#207448" />
    <circle cx="20" cy="27" r="2.5" fill="#207448" />
    <circle cx="12" cy="41" r="2.5" fill="#207448" />
    <circle cx="20" cy="41" r="2.5" fill="#207448" />
  </g>
  <text x="668" y="557" font-family="sans-serif" font-size="30" font-weight="bold" fill="#db8129">S = 4 spines, one down: 75%</text>

  <!-- 4-Spines Bar Track (910 px wide) -->
  <rect x="600" y="615" width="910" height="72" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
  <!-- Filled 75% = 3/4 = 682.5 px -->
  <rect x="600" y="615" width="682" height="72" rx="12" fill="#db8129" />
  <!-- Dividing lines for 4 spines (every 227.5 px) -->
  <line x1="828" y1="615" x2="828" y2="687" stroke="#ffffff" stroke-width="3" />
  <line x1="1055" y1="615" x2="1055" y2="687" stroke="#ffffff" stroke-width="3" />
  <!-- Lost 1/4 slice: 25% empty track with hatching -->
  <line x1="1282" y1="615" x2="1282" y2="687" stroke="#a0b0a5" stroke-width="2.5" stroke-dasharray="6 4" />
  <!-- Diagonal hatch marks across the lost 25% section -->
  <line x1="1300" y1="687" x2="1340" y2="615" stroke="#a0b0a5" stroke-width="2" opacity="0.4" />
  <line x1="1340" y1="687" x2="1380" y2="615" stroke="#a0b0a5" stroke-width="2" opacity="0.4" />
  <line x1="1380" y1="687" x2="1420" y2="615" stroke="#a0b0a5" stroke-width="2" opacity="0.4" />
  <line x1="1420" y1="687" x2="1460" y2="615" stroke="#a0b0a5" stroke-width="2" opacity="0.4" />
  <line x1="1460" y1="687" x2="1500" y2="615" stroke="#a0b0a5" stroke-width="2" opacity="0.4" />

  <!-- ==================== FOOTER CARD ==================== -->
  <rect x="50" y="785" width="1500" height="85" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  <g transform="translate(80, 800)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 27 6 L 46 14 L 46 28 C 46 40 27 48 27 48 C 27 48 8 40 8 28 L 8 14 Z" />
    <line x1="27" y1="18" x2="27" y2="30" />
    <circle cx="27" cy="38" r="2.5" fill="#207448" />
  </g>
  <text x="800" y="838" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">A 1:1 design stays oversubscribed until the failure is repaired</text>

  <!-- ==================== TAKEAWAY BOTTOM BAR ==================== -->
  <rect x="50" y="895" width="1500" height="80" rx="14" fill="#207448" />
  <text x="800" y="944" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Work out what survives losing one spine, one leaf and one rail group</text>
</svg>'''

from test_n18_failure import test_svg_string
test_svg_string(svg_code)

with open("test_n18_failure.svg", "w") as f:
    f.write(svg_code)

print("Saved test_n18_failure.svg!")
