import re
import xml.etree.ElementTree as ET

svg_text = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900">
  <title>The linear strategy makes every host wait at each task</title>
  <desc>Visual infographic explaining how Ansible's linear strategy executes tasks across hosts in lockstep, dropping failed hosts and waiting at each barrier.</desc>

  <!-- Background -->
  <rect width="1600" height="900" fill="#f5f8f5"/>

  <!-- Title -->
  <text x="800" y="65" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">The linear strategy makes every host wait at each task</text>

  <!-- ==================== LANE 1: gpu01 ==================== -->
  <g id="lane-gpu01">
    <!-- Lane background track -->
    <rect x="60" y="210" width="1480" height="155" rx="14" fill="#ffffff" stroke="#cfded2" stroke-width="2"/>

    <!-- Host Node Box: gpu01 -->
    <g id="node-gpu01">
      <rect x="80" y="225" width="190" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <!-- Host outline icon -->
      <g transform="translate(147, 237)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="48" height="42" rx="4"/>
        <line x1="4" y1="18" x2="52" y2="18" stroke-width="2.5"/>
        <line x1="4" y1="32" x2="52" y2="32" stroke-width="2.5"/>
        <circle cx="12" cy="11" r="2" fill="#207448"/>
        <circle cx="12" cy="25" r="2" fill="#207448"/>
        <circle cx="12" cy="39" r="2" fill="#207448"/>
        <line x1="22" y1="11" x2="42" y2="11" stroke-width="2.5"/>
        <line x1="22" y1="25" x2="42" y2="25" stroke-width="2.5"/>
        <line x1="22" y1="39" x2="42" y2="39" stroke-width="2.5"/>
      </g>
      <text x="175" y="325" text-anchor="middle" font-family="'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace" font-size="28" font-weight="bold" fill="#207448">gpu01</text>
    </g>

    <!-- Task 1: ok -->
    <g id="gpu01-task1">
      <rect x="310" y="225" width="190" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <g transform="translate(377, 237)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="25" r="22"/>
        <polyline points="18,25 25,32 38,18"/>
      </g>
      <text x="405" y="325" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">ok</text>
    </g>

    <!-- Task 2: ok -->
    <g id="gpu01-task2">
      <rect x="540" y="225" width="190" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <g transform="translate(607, 237)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="25" r="22"/>
        <polyline points="18,25 25,32 38,18"/>
      </g>
      <text x="635" y="325" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">ok</text>
    </g>

    <!-- Task 3: ok -->
    <g id="gpu01-task3">
      <rect x="850" y="225" width="190" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <g transform="translate(917, 237)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="25" r="22"/>
        <polyline points="18,25 25,32 38,18"/>
      </g>
      <text x="945" y="325" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">ok</text>
    </g>
  </g>

  <!-- ==================== LANE 2: gpu02 ==================== -->
  <g id="lane-gpu02">
    <!-- Lane background track -->
    <rect x="60" y="385" width="1480" height="155" rx="14" fill="#ffffff" stroke="#cfded2" stroke-width="2"/>

    <!-- Host Node Box: gpu02 -->
    <g id="node-gpu02">
      <rect x="80" y="400" width="190" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <g transform="translate(147, 412)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="48" height="42" rx="4"/>
        <line x1="4" y1="18" x2="52" y2="18" stroke-width="2.5"/>
        <line x1="4" y1="32" x2="52" y2="32" stroke-width="2.5"/>
        <circle cx="12" cy="11" r="2" fill="#207448"/>
        <circle cx="12" cy="25" r="2" fill="#207448"/>
        <circle cx="12" cy="39" r="2" fill="#207448"/>
        <line x1="22" y1="11" x2="42" y2="11" stroke-width="2.5"/>
        <line x1="22" y1="25" x2="42" y2="25" stroke-width="2.5"/>
        <line x1="22" y1="39" x2="42" y2="39" stroke-width="2.5"/>
      </g>
      <text x="175" y="500" text-anchor="middle" font-family="'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace" font-size="28" font-weight="bold" fill="#207448">gpu02</text>
    </g>

    <!-- Task 1: ok -->
    <g id="gpu02-task1">
      <rect x="310" y="400" width="190" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <g transform="translate(377, 412)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="25" r="22"/>
        <polyline points="18,25 25,32 38,18"/>
      </g>
      <text x="405" y="500" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">ok</text>
    </g>

    <!-- Task 2: failed (Red outline, orange highlight) -->
    <g id="gpu02-task2">
      <!-- Orange highlight outline -->
      <rect x="534" y="394" width="202" height="137" rx="16" fill="none" stroke="#db8129" stroke-width="4"/>
      <!-- Main red-outline box -->
      <rect x="540" y="400" width="190" height="125" rx="12" fill="#fff5eb" stroke="#d32f2f" stroke-width="3"/>
      <g transform="translate(607, 412)" stroke="#d32f2f" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="25" r="22"/>
        <line x1="18" y1="15" x2="38" y2="35"/>
        <line x1="38" y1="15" x2="18" y2="35"/>
      </g>
      <text x="635" y="500" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#d32f2f">failed</text>
    </g>

    <!-- Dropped from later tasks: grey box after barrier -->
    <g id="gpu02-dropped">
      <rect x="850" y="400" width="330" height="125" rx="12" fill="#f0f2f1" stroke="#738079" stroke-width="2.5" stroke-dasharray="6 4"/>
      <g transform="translate(987, 412)" stroke="#738079" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="25" r="22"/>
        <line x1="12" y1="9" x2="44" y2="41"/>
      </g>
      <text x="1015" y="500" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="#55605a">dropped from later tasks</text>
    </g>

    <!-- Far right recap label: failed in the recap -->
    <g id="gpu02-recap">
      <rect x="1220" y="400" width="300" height="125" rx="12" fill="#fff5f5" stroke="#d32f2f" stroke-width="2.5"/>
      <g transform="translate(1342, 412)" stroke="#d32f2f" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="8" y="4" width="40" height="42" rx="4"/>
        <line x1="16" y1="16" x2="40" y2="16"/>
        <line x1="16" y1="26" x2="40" y2="26"/>
        <line x1="16" y1="36" x2="30" y2="36"/>
      </g>
      <text x="1370" y="500" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="#d32f2f">failed in the recap</text>
    </g>
  </g>

  <!-- ==================== LANE 3: gpu03 ==================== -->
  <g id="lane-gpu03">
    <!-- Lane background track -->
    <rect x="60" y="560" width="1480" height="155" rx="14" fill="#ffffff" stroke="#cfded2" stroke-width="2"/>

    <!-- Host Node Box: gpu03 -->
    <g id="node-gpu03">
      <rect x="80" y="575" width="190" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <g transform="translate(147, 587)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="48" height="42" rx="4"/>
        <line x1="4" y1="18" x2="52" y2="18" stroke-width="2.5"/>
        <line x1="4" y1="32" x2="52" y2="32" stroke-width="2.5"/>
        <circle cx="12" cy="11" r="2" fill="#207448"/>
        <circle cx="12" cy="25" r="2" fill="#207448"/>
        <circle cx="12" cy="39" r="2" fill="#207448"/>
        <line x1="22" y1="11" x2="42" y2="11" stroke-width="2.5"/>
        <line x1="22" y1="25" x2="42" y2="25" stroke-width="2.5"/>
        <line x1="22" y1="39" x2="42" y2="39" stroke-width="2.5"/>
      </g>
      <text x="175" y="675" text-anchor="middle" font-family="'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace" font-size="28" font-weight="bold" fill="#207448">gpu03</text>
    </g>

    <!-- Task 1: ok -->
    <g id="gpu03-task1">
      <rect x="310" y="575" width="190" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <g transform="translate(377, 587)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="25" r="22"/>
        <polyline points="18,25 25,32 38,18"/>
      </g>
      <text x="405" y="675" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">ok</text>
    </g>

    <!-- Task 2: ok -->
    <g id="gpu03-task2">
      <rect x="540" y="575" width="190" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <g transform="translate(607, 587)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="25" r="22"/>
        <polyline points="18,25 25,32 38,18"/>
      </g>
      <text x="635" y="675" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">ok</text>
    </g>

    <!-- Task 3: ok -->
    <g id="gpu03-task3">
      <rect x="850" y="575" width="190" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
      <g transform="translate(917, 587)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="25" r="22"/>
        <polyline points="18,25 25,32 38,18"/>
      </g>
      <text x="945" y="675" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">ok</text>
    </g>
  </g>

  <!-- ==================== VERTICAL BARRIER (OVER LANES) ==================== -->
  <!-- Dashed vertical barrier line across all lanes -->
  <line x1="790" y1="181" x2="790" y2="725" stroke="#207448" stroke-width="4" stroke-dasharray="10 8"/>

  <!-- Barrier banner with label and step circle 1 -->
  <g id="barrier-banner">
    <rect x="415" y="115" width="750" height="66" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Step number circle 1 on the barrier -->
    <circle cx="460" cy="148" r="24" fill="#207448"/>
    <text x="460" y="157" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>

    <!-- Clock / Wait Outline Icon -->
    <g transform="translate(502, 120)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <polyline points="28,14 28,28 38,28"/>
    </g>

    <!-- Barrier Label -->
    <text x="580" y="157" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="#207448">linear: wait until every host finishes this task</text>
  </g>

  <!-- ==================== CAPTION / TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="60" y="755" width="1480" height="85" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <g transform="translate(90, 770)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <line x1="28" y1="20" x2="28" y2="38"/>
      <circle cx="28" cy="14" r="2" fill="#207448"/>
    </g>
    <text x="800" y="808" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#207448">One slow or failing host can hold up the whole run.</text>
  </g>
</svg>"""

with open("test_linear.svg", "w") as f:
    f.write(svg_text)
print("Updated test_linear.svg")
