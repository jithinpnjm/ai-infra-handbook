#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1100" width="1600" height="1100">
  <title>Averaging percentiles weights a ten-request server the same as a thousand-request server.</title>
  <desc>Averaging two p99 values gives 55; the true fleet p99 is 12</desc>

  <defs>
    <!-- Standard green arrowhead (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect width="100%" height="100%" fill="#f5f8f5"/>

  <!-- Main Title (48px bold) -->
  <text x="800" y="58" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Averaging percentiles weights a ten-request</tspan>
    <tspan x="800" dy="56">server the same as a thousand-request server.</tspan>
  </text>

  <!-- ==================== LEFT COLUMN: TWO SERVER BOXES STACKED ==================== -->
  
  <!-- TOP SERVER BOX: quiet server -->
  <g id="quiet-server-box">
    <rect x="40" y="150" width="450" height="380" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    
    <!-- Outline icon: Server rack (56px, stroke 4, #207448) -->
    <g transform="translate(65, 172)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="48" height="48" rx="5" fill="#f5f8f5"/>
      <line x1="4" y1="20" x2="52" y2="20"/>
      <line x1="4" y1="36" x2="52" y2="36"/>
      <circle cx="14" cy="12" r="2.5" fill="#207448"/>
      <circle cx="22" cy="12" r="2.5" fill="#207448"/>
      <circle cx="14" cy="28" r="2.5" fill="#207448"/>
      <circle cx="22" cy="28" r="2.5" fill="#207448"/>
      <circle cx="14" cy="44" r="2.5" fill="#207448"/>
      <circle cx="22" cy="44" r="2.5" fill="#207448"/>
      <line x1="34" y1="12" x2="44" y2="12"/>
      <line x1="34" y1="28" x2="44" y2="28"/>
      <line x1="34" y1="44" x2="44" y2="44"/>
    </g>
    
    <!-- Title: quiet server -->
    <text x="140" y="212" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">quiet server</text>
    
    <!-- Inner card for chart & tag -->
    <rect x="65" y="248" width="400" height="258" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    
    <!-- Label: 1,000 requests -->
    <text x="90" y="288" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">1,000 requests</text>
    
    <!-- Small bar chart showing 1,000 requests (densely clustered at fast latency 2-10ms) -->
    <g transform="translate(90, 305)">
      <!-- Baseline -->
      <line x1="0" y1="90" x2="350" y2="90" stroke="#207448" stroke-width="2"/>
      <!-- Latency bars -->
      <rect x="10" y="5" width="22" height="85" fill="#207448" rx="2"/>
      <rect x="38" y="15" width="22" height="75" fill="#207448" rx="2"/>
      <rect x="66" y="28" width="22" height="62" fill="#207448" rx="2"/>
      <rect x="94" y="45" width="22" height="45" fill="#207448" rx="2"/>
      <rect x="122" y="65" width="22" height="25" fill="#207448" rx="2"/>
      <rect x="150" y="76" width="22" height="14" fill="#207448" rx="2"/>
      <rect x="178" y="82" width="22" height="8" fill="#207448" rx="2"/>
      <rect x="206" y="85" width="22" height="5" fill="#207448" rx="2"/>
      <rect x="234" y="87" width="22" height="3" fill="#207448" rx="2"/>
      <!-- p99 threshold guide line at 10 ms -->
      <line x1="161" y1="10" x2="161" y2="90" stroke="#207448" stroke-width="2" stroke-dasharray="4 3"/>
    </g>
    
    <!-- Tag: p99 of 10 ms -->
    <rect x="90" y="435" width="240" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="210" y="468" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36"><tspan font-family="monospace" font-weight="bold">p99</tspan> of 10 ms</text>
  </g>

  <!-- BOTTOM SERVER BOX: busy server -->
  <g id="busy-server-box">
    <rect x="40" y="560" width="450" height="380" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    
    <!-- Outline icon: Server rack (56px, stroke 4, #207448) -->
    <g transform="translate(65, 582)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="48" height="48" rx="5" fill="#f5f8f5"/>
      <line x1="4" y1="20" x2="52" y2="20"/>
      <line x1="4" y1="36" x2="52" y2="36"/>
      <circle cx="14" cy="12" r="2.5" fill="#207448"/>
      <circle cx="22" cy="12" r="2.5" fill="#207448"/>
      <circle cx="14" cy="28" r="2.5" fill="#207448"/>
      <circle cx="22" cy="28" r="2.5" fill="#207448"/>
      <circle cx="14" cy="44" r="2.5" fill="#207448"/>
      <circle cx="22" cy="44" r="2.5" fill="#207448"/>
      <line x1="34" y1="12" x2="44" y2="12"/>
      <line x1="34" y1="28" x2="44" y2="28"/>
      <line x1="34" y1="44" x2="44" y2="44"/>
    </g>
    
    <!-- Title: busy server -->
    <text x="140" y="622" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">busy server</text>
    
    <!-- Inner card for chart & tag -->
    <rect x="65" y="658" width="400" height="258" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    
    <!-- Label: 10 requests -->
    <text x="90" y="698" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">10 requests</text>
    
    <!-- Small bar chart showing 10 requests (sparse distribution reaching high latency 100ms) -->
    <g transform="translate(90, 715)">
      <!-- Baseline -->
      <line x1="0" y1="90" x2="350" y2="90" stroke="#207448" stroke-width="2"/>
      <!-- Sparse bars representing 10 requests -->
      <rect x="30" y="65" width="22" height="25" fill="#207448" rx="2"/>
      <rect x="90" y="75" width="22" height="15" fill="#207448" rx="2"/>
      <rect x="170" y="70" width="22" height="20" fill="#207448" rx="2"/>
      <rect x="250" y="60" width="22" height="30" fill="#207448" rx="2"/>
      <rect x="310" y="80" width="22" height="10" fill="#207448" rx="2"/>
      <!-- p99 threshold guide line at 100 ms -->
      <line x1="321" y1="10" x2="321" y2="90" stroke="#207448" stroke-width="2" stroke-dasharray="4 3"/>
    </g>
    
    <!-- Tag: p99 of 100 ms -->
    <rect x="90" y="845" width="250" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="215" y="878" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36"><tspan font-family="monospace" font-weight="bold">p99</tspan> of 100 ms</text>
  </g>

  <!-- ==================== ARROWS: MEETING AT CENTRE BOX ==================== -->
  <!-- Arrow 1: quiet server -> average of the two p99s -->
  <path d="M 490 340 C 530 340, 530 460, 568 460" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)"/>
  
  <!-- Arrow 2: busy server -> average of the two p99s -->
  <path d="M 490 750 C 530 750, 530 630, 568 630" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)"/>

  <!-- ==================== MIDDLE COLUMN: CENTRE BOX ==================== -->
  <g id="centre-box">
    <rect x="570" y="240" width="460" height="610" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    
    <!-- Calculator / Average Icon (56px, stroke 4, #207448) -->
    <g transform="translate(772, 260)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="4" width="44" height="48" rx="6" fill="#f5f8f5"/>
      <line x1="14" y1="16" x2="42" y2="16"/>
      <line x1="16" y1="28" x2="22" y2="28"/>
      <line x1="34" y1="28" x2="40" y2="28"/>
      <line x1="16" y1="38" x2="22" y2="38"/>
      <line x1="34" y1="38" x2="40" y2="38"/>
    </g>
    
    <!-- Label: average of the two p99s -->
    <text x="800" y="348" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">average of the two <tspan font-family="monospace">p99s</tspan></text>
    
    <!-- Result 55 in an orange outline -->
    <rect x="710" y="380" width="180" height="92" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="4"/>
    <text x="800" y="446" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="52" font-weight="bold" fill="#303a36">55</text>
    
    <!-- Red cross stamp labelled wrong -->
    <rect x="700" y="495" width="200" height="64" rx="10" fill="#ffffff" stroke="#c53030" stroke-width="3"/>
    <g stroke="#c53030" stroke-width="4" stroke-linecap="round">
      <line x1="722" y1="515" x2="742" y2="539"/>
      <line x1="742" y1="515" x2="722" y2="539"/>
    </g>
    <text x="815" y="539" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#c53030">wrong</text>
    
    <!-- Inner Card: gives a weight of one request to each server regardless of size -->
    <rect x="590" y="582" width="420" height="245" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    
    <!-- Balance scale graphic illustrating 1:1 distorted weighting -->
    <g transform="translate(800, 620)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round">
      <line x1="0" y1="0" x2="0" y2="32"/>
      <line x1="-20" y1="32" x2="20" y2="32"/>
      <line x1="-50" y1="8" x2="50" y2="8"/>
      <line x1="-50" y1="8" x2="-62" y2="24"/>
      <line x1="-50" y1="8" x2="-38" y2="24"/>
      <line x1="-66" y1="24" x2="-34" y2="24"/>
      <line x1="50" y1="8" x2="38" y2="24"/>
      <line x1="50" y1="8" x2="62" y2="24"/>
      <line x1="34" y1="24" x2="66" y2="24"/>
    </g>
    
    <!-- Label: gives a weight of one request to each server regardless of size -->
    <text x="800" y="695" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="800" dy="0">gives a weight of one</tspan>
      <tspan x="800" dy="38">request to each server</tspan>
      <tspan x="800" dy="38">regardless of size</tspan>
    </text>
  </g>

  <!-- ==================== RIGHT COLUMN: COMBINED CHART & TWO-STEP STRIP ==================== -->
  <g id="right-column">
    <rect x="1110" y="150" width="450" height="790" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    
    <!-- Header: all 1,010 requests merged -->
    <text x="1335" y="202" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="1335" dy="0">all 1,010 requests</tspan>
      <tspan x="1335" dy="38">merged</tspan>
    </text>
    
    <!-- Inner Card: Combined Histogram -->
    <rect x="1135" y="260" width="400" height="340" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    
    <!-- Merged histogram bars -->
    <g transform="translate(1160, 310)">
      <!-- Baseline -->
      <line x1="0" y1="160" x2="350" y2="160" stroke="#207448" stroke-width="2"/>
      
      <!-- 1,000 requests from quiet server dominate the low-latency bins -->
      <rect x="10" y="10" width="22" height="150" fill="#207448" rx="2"/>
      <rect x="38" y="25" width="22" height="135" fill="#207448" rx="2"/>
      <rect x="66" y="45" width="22" height="115" fill="#207448" rx="2"/>
      <rect x="94" y="75" width="22" height="85" fill="#207448" rx="2"/>
      <rect x="122" y="110" width="22" height="50" fill="#207448" rx="2"/>
      <rect x="150" y="130" width="22" height="30" fill="#207448" rx="2"/>
      <rect x="178" y="145" width="22" height="15" fill="#207448" rx="2"/>
      
      <!-- 10 requests from busy server add tiny tail at high latency -->
      <rect x="220" y="156" width="18" height="4" fill="#207448" rx="1"/>
      <rect x="260" y="156" width="18" height="4" fill="#207448" rx="1"/>
      <rect x="300" y="157" width="18" height="3" fill="#207448" rx="1"/>
      <rect x="325" y="158" width="18" height="2" fill="#207448" rx="1"/>

      <!-- Marker at the top one percent (at 12 ms) -->
      <line x1="172" y1="30" x2="172" y2="160" stroke="#207448" stroke-width="3" stroke-dasharray="5 3"/>
      <polygon points="172,30 166,16 178,16" fill="#207448"/>
    </g>

    <!-- Marker label badge: true p99 at 12 ms with green check mark -->
    <rect x="1160" y="520" width="350" height="58" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <g stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 1180 549 L 1192 561 L 1210 537"/>
    </g>
    <text x="1350" y="559" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">true <tspan font-family="monospace">p99</tspan> at 12 ms</text>

    <!-- Two-step strip under the merged chart -->
    <!-- Step 1 Card -->
    <rect x="1135" y="625" width="400" height="135" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <circle cx="1178" cy="692" r="24" fill="#207448"/>
    <text x="1178" y="701" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <text x="1225" y="678" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="1225" dy="0">merge the histograms</tspan>
      <tspan x="1225" dy="36">or the raw samples</tspan>
    </text>

    <!-- Step 2 Card -->
    <rect x="1135" y="780" width="400" height="135" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <circle cx="1178" cy="847" r="24" fill="#207448"/>
    <text x="1178" y="856" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <text x="1225" y="833" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="1225" dy="0">then take the</tspan>
      <tspan x="1225" dy="36">percentile</tspan>
    </text>
  </g>

  <!-- ==================== GREEN TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="40" y="975" width="1520" height="65" rx="12" fill="#207448"/>
    <!-- Spark / Key takeaway icon in white -->
    <g transform="translate(68, 988)" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 19 2 A 17 17 0 0 0 6 27 C 9 31 11 34 11 38 L 27 38 C 27 34 29 31 32 27 A 17 17 0 0 0 19 2 Z"/>
      <line x1="13" y1="38" x2="25" y2="38"/>
      <line x1="15" y1="42" x2="23" y2="42"/>
    </g>
    <!-- Takeaway Text -->
    <text x="815" y="1016" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">To combine servers, merge the histograms or the raw samples, then take the percentile.</text>
  </g>
</svg>'''

open("test_p99_candidate.svg", "w").write(svg_content)
print("Wrote test_p99_candidate.svg successfully.")
