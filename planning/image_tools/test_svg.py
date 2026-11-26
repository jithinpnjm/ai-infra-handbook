import re
import xml.etree.ElementTree as ET

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Drill 11: control plane slow while serving is fine</title>
  <desc>Infographic explaining why Kubernetes control plane slows down while data plane serving remains fine due to cross-region etcd member latency.</desc>

  <defs>
    <marker id="arrow-green" markerWidth="14" markerHeight="14" refX="10" refY="7" orient="auto">
      <path d="M 1,1 L 11,7 L 1,13 Z" fill="#207448" />
    </marker>
    <marker id="arrow-orange" markerWidth="14" markerHeight="14" refX="10" refY="7" orient="auto">
      <path d="M 1,1 L 11,7 L 1,13 Z" fill="#db8129" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Main Title -->
  <text x="50" y="65" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Drill 11: control plane slow while serving is fine</text>

  <!-- ==================== CONTROL PLANE SIDE ==================== -->
  <g id="control-plane-zone">
    <!-- Zone Outer Container -->
    <rect x="40" y="100" width="990" height="570" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Zone Header Banner -->
    <path d="M 40,112 A 12,12 0 0,1 52,100 L 1018,100 A 12,12 0 0,1 1030,112 L 1030,165 L 40,165 Z" fill="#e8f1ea" />
    
    <!-- Zone Header Icon (Control Plane / Helm / Nodes) -->
    <g transform="translate(60, 110)">
      <circle cx="22" cy="22" r="18" fill="none" stroke="#207448" stroke-width="3" />
      <circle cx="22" cy="22" r="6" fill="#207448" />
      <line x1="22" y1="4" x2="22" y2="40" stroke="#207448" stroke-width="3" />
      <line x1="4" y1="22" x2="40" y2="22" stroke="#207448" stroke-width="3" />
    </g>
    <text x="120" y="145" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Control plane side</text>

    <!-- Sub-container: etcd cluster -->
    <rect x="60" y="180" width="950" height="230" rx="8" fill="#f9fbf9" stroke="#c2dac8" stroke-width="1.5" />
    
    <!-- 3 etcd members title & icon -->
    <g transform="translate(80, 192)">
      <ellipse cx="14" cy="8" rx="12" ry="5" fill="none" stroke="#207448" stroke-width="2.5" />
      <path d="M 2,8 v 12 c 0,3 5.4,5 12,5 s 12,-2 12,-5 v -12" fill="none" stroke="#207448" stroke-width="2.5" />
      <ellipse cx="28" cy="18" rx="12" ry="5" fill="none" stroke="#207448" stroke-width="2.5" />
      <path d="M 16,18 v 12 c 0,3 5.4,5 12,5 s 12,-2 12,-5 v -12" fill="none" stroke="#207448" stroke-width="2.5" />
    </g>
    <text x="135" y="220" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">3 etcd members</text>

    <!-- Member 1 & 2 Box (Local datacenter) -->
    <rect x="80" y="245" width="450" height="145" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Node icon -->
    <g transform="translate(95, 260)">
      <rect x="0" y="0" width="38" height="26" rx="4" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <line x1="6" y1="8" x2="14" y2="8" stroke="#207448" stroke-width="2.5" />
      <circle cx="28" cy="13" r="3" fill="#207448" />
      <rect x="12" y="32" width="38" height="26" rx="4" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <line x1="18" y1="40" x2="26" y2="40" stroke="#207448" stroke-width="2.5" />
      <circle cx="40" cy="45" r="3" fill="#207448" />
    </g>
    <text x="160" y="300" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="160" dy="0">two near each other with</tspan>
      <tspan x="160" dy="34">round trips under 1 ms</tspan>
    </text>

    <!-- Connecting Latency Arrow (WAN link to Region B) -->
    <line x1="530" y1="318" x2="570" y2="318" stroke="#db8129" stroke-width="3" stroke-dasharray="6,4" marker-end="url(#arrow-orange)" />

    <!-- Member 3 Box (Remote region - single orange focal point) -->
    <rect x="575" y="245" width="415" height="145" rx="6" fill="#fdf6ee" stroke="#db8129" stroke-width="3" />
    <!-- Remote Server / WAN Icon -->
    <g transform="translate(590, 260)">
      <rect x="0" y="10" width="38" height="28" rx="4" fill="#ffffff" stroke="#db8129" stroke-width="2.5" />
      <circle cx="28" cy="24" r="3" fill="#db8129" />
      <path d="M 6,24 h 14" stroke="#db8129" stroke-width="2.5" />
      <path d="M 12,6 A 14,14 0 0,1 28,6" fill="none" stroke="#db8129" stroke-width="2" />
    </g>
    <text x="645" y="295" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="645" dy="0">one rebuilt yesterday in</tspan>
      <tspan x="645" dy="32">another region with about</tspan>
      <tspan x="645" dy="32">60 ms round trip</tspan>
    </text>

    <!-- Lower Section: Disk and Symptoms -->
    <!-- Disk Panel (Left) -->
    <rect x="60" y="430" width="455" height="220" rx="8" fill="#f9fbf9" stroke="#c2dac8" stroke-width="1.5" />
    <!-- Disk Icon -->
    <g transform="translate(80, 450)">
      <ellipse cx="24" cy="12" rx="20" ry="8" fill="none" stroke="#207448" stroke-width="3" />
      <path d="M 4,12 v 16 c 0,4.4 9,8 20,8 s 20,-3.6 20,-8 v -16" fill="none" stroke="#207448" stroke-width="3" />
      <path d="M 4,28 v 16 c 0,4.4 9,8 20,8 s 20,-3.6 20,-8 v -16" fill="none" stroke="#207448" stroke-width="3" />
    </g>
    <text x="145" y="475" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="145" dy="0">disk is fast local SSD on all</tspan>
      <tspan x="145" dy="34">members so disk is not</tspan>
      <tspan x="145" dy="34">the cause</tspan>
    </text>

    <!-- Symptoms Panel (Right) -->
    <rect x="535" y="430" width="475" height="220" rx="8" fill="#f9fbf9" stroke="#c2dac8" stroke-width="1.5" />
    <!-- Activity / Alert Icon -->
    <g transform="translate(555, 450)">
      <circle cx="22" cy="22" r="18" fill="none" stroke="#207448" stroke-width="3" />
      <polyline points="22,12 22,24 30,24" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" />
    </g>
    <text x="615" y="480" font-family="sans-serif" font-size="24" fill="#303a36">leader changed twice in the last hour</text>
    <text x="555" y="540" font-size="24" fill="#303a36">
      <tspan font-family="monospace">kubectl</tspan><tspan font-family="sans-serif"> commands take ten seconds</tspan>
    </text>
    <text x="555" y="600" font-family="sans-serif" font-size="24" fill="#303a36">writes and reads slow and rising</text>
  </g>

  <!-- ==================== DATA PLANE SIDE ==================== -->
  <g id="data-plane-zone">
    <!-- Zone Outer Container -->
    <rect x="1070" y="100" width="490" height="570" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Zone Header Banner -->
    <path d="M 1070,112 A 12,12 0 0,1 1082,100 L 1548,100 A 12,12 0 0,1 1560,112 L 1560,165 L 1070,165 Z" fill="#e8f1ea" />
    
    <!-- Zone Header Icon (Application / Pod window) -->
    <g transform="translate(1090, 110)">
      <rect x="2" y="4" width="40" height="34" rx="4" fill="none" stroke="#207448" stroke-width="3" />
      <line x1="2" y1="14" x2="42" y2="14" stroke="#207448" stroke-width="2.5" />
      <circle cx="9" cy="9" r="2.5" fill="#207448" />
      <circle cx="16" cy="9" r="2.5" fill="#207448" />
    </g>
    <text x="1150" y="145" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Data plane side</text>

    <!-- Data plane visual card -->
    <rect x="1095" y="180" width="440" height="470" rx="8" fill="#f9fbf9" stroke="#c2dac8" stroke-width="1.5" />

    <!-- Pod cluster visual graphic -->
    <g transform="translate(1120, 210)">
      <!-- Pod 1 -->
      <rect x="10" y="10" width="110" height="75" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <circle cx="35" cy="40" r="12" fill="none" stroke="#207448" stroke-width="2" />
      <circle cx="35" cy="40" r="4" fill="#207448" />
      <line x1="60" y1="35" x2="105" y2="35" stroke="#207448" stroke-width="2" />
      <line x1="60" y1="48" x2="95" y2="48" stroke="#207448" stroke-width="2" />

      <!-- Pod 2 -->
      <rect x="140" y="10" width="110" height="75" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <circle cx="165" cy="40" r="12" fill="none" stroke="#207448" stroke-width="2" />
      <circle cx="165" cy="40" r="4" fill="#207448" />
      <line x1="190" y1="35" x2="235" y2="35" stroke="#207448" stroke-width="2" />
      <line x1="190" y1="48" x2="225" y2="48" stroke="#207448" stroke-width="2" />

      <!-- Pod 3 -->
      <rect x="270" y="10" width="110" height="75" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <circle cx="295" cy="40" r="12" fill="none" stroke="#207448" stroke-width="2" />
      <circle cx="295" cy="40" r="4" fill="#207448" />
      <line x1="320" y1="35" x2="365" y2="35" stroke="#207448" stroke-width="2" />
      <line x1="320" y1="48" x2="355" y2="48" stroke="#207448" stroke-width="2" />

      <!-- Traffic Ingress Flow -->
      <line x1="65" y1="120" x2="65" y2="95" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
      <line x1="195" y1="120" x2="195" y2="95" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
      <line x1="325" y1="120" x2="325" y2="95" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
      <line x1="30" y1="120" x2="360" y2="120" stroke="#207448" stroke-width="3" />
    </g>

    <!-- Data Plane Description Text -->
    <text x="1115" y="420" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1115" dy="0">serving pods have no</tspan>
      <tspan x="1115" dy="40">dependency on the</tspan>
      <tspan x="1115" dy="40">Kubernetes API so they</tspan>
      <tspan x="1115" dy="40">keep answering</tspan>
    </text>
  </g>

  <!-- ==================== LOWER THREE CARDS ==================== -->
  <!-- Card 1: Cause note -->
  <g id="cause-note-card">
    <rect x="40" y="695" width="480" height="395" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Header bar -->
    <path d="M 40,705 A 10,10 0 0,1 50,695 L 510,695 A 10,10 0 0,1 520,705 L 520,755 L 40,755 Z" fill="#e8f1ea" />
    <!-- Icon -->
    <g transform="translate(60, 706)">
      <polygon points="18,4 34,34 2,34" fill="none" stroke="#207448" stroke-width="2.5" />
      <line x1="18" y1="15" x2="18" y2="23" stroke="#207448" stroke-width="2.5" />
      <circle cx="18" cy="28" r="1.5" fill="#207448" />
    </g>
    <text x="110" y="738" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Cause note</text>
    
    <text x="65" y="795" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="65" dy="0">etcd defaults assume one</tspan>
      <tspan x="65" dy="36">datacenter; test round trips</tspan>
      <tspan x="65" dy="36">and tune heartbeat interval and</tspan>
      <tspan x="65" dy="36">election timeout if you must</tspan>
      <tspan x="65" dy="36">span; etcd across regions is</tspan>
      <tspan x="65" dy="36">strongly discouraged</tspan>
    </text>
  </g>

  <!-- Card 2: Fix -->
  <g id="fix-card">
    <rect x="550" y="695" width="500" height="395" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Header bar -->
    <path d="M 550,705 A 10,10 0 0,1 560,695 L 1040,695 A 10,10 0 0,1 1050,705 L 1050,755 L 550,755 Z" fill="#e8f1ea" />
    <!-- Icon (Wrench / Fix) -->
    <g transform="translate(570, 706)">
      <path d="M 28,6 A 10,10 0 0,0 16,18 L 6,28 A 4,4 0 0,0 12,34 L 22,24 A 10,10 0 0,0 34,12 Z" fill="none" stroke="#207448" stroke-width="2.5" />
    </g>
    <text x="625" y="738" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Fix</text>

    <text x="575" y="795" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="575" dy="0">bring the member back close, or</tspan>
      <tspan x="575" dy="36">remove it and add one in the</tspan>
      <tspan x="575" dy="36">same datacenter; one membership</tspan>
      <tspan x="575" dy="36">change at a time; snapshot first;</tspan>
      <tspan x="575" dy="36">do not defragment a live member</tspan>
      <tspan x="575" dy="36">as a reflex; do not roll the whole</tspan>
      <tspan x="575" dy="36">control plane at once</tspan>
    </text>
  </g>

  <!-- Card 3: Prevention -->
  <g id="prevention-card">
    <rect x="1080" y="695" width="480" height="395" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Header bar -->
    <path d="M 1080,705 A 10,10 0 0,1 1090,695 L 1550,695 A 10,10 0 0,1 1560,705 L 1560,755 L 1080,755 Z" fill="#e8f1ea" />
    <!-- Icon (Shield) -->
    <g transform="translate(1100, 706)">
      <path d="M 18,4 L 32,9 V 19 C 32,27 26,33 18,36 C 10,33 4,27 4,19 V 9 Z" fill="none" stroke="#207448" stroke-width="2.5" />
      <polyline points="11,18 16,23 25,14" fill="none" stroke="#207448" stroke-width="2.5" />
    </g>
    <text x="1155" y="738" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Prevention</text>

    <text x="1105" y="795" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1105" dy="0">members in one low-latency</tspan>
      <tspan x="1105" dy="36">domain with an odd count;</tspan>
      <tspan x="1105" dy="36">alert on leader changes and</tspan>
      <tspan x="1105" dy="36">request latency</tspan>
    </text>
  </g>

  <!-- ==================== TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="40" y="1115" width="1520" height="65" rx="8" fill="#207448" />
    <text x="800" y="1156" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle">running pods are fine means the API layer is slow, not the data plane</text>
  </g>
</svg>
"""

# Verify XML
root = ET.fromstring(svg_content)
print("XML is valid.")

# Check all font sizes
font_sizes = re.findall(r'font-size="(\d+)"', svg_content)
for fs in font_sizes:
    if int(fs) < 24:
        print(f"ERROR: Font size {fs} is smaller than 24!")
print(f"All {len(font_sizes)} font sizes >= 24: {set(font_sizes)}")

# Check exact required labels:
labels = [
    "Drill 11: control plane slow while serving is fine",
    "Control plane side",
    "3 etcd members",
    "two near each other with round trips under 1 ms",
    "one rebuilt yesterday in another region with about 60 ms round trip",
    "leader changed twice in the last hour",
    "kubectl commands take ten seconds",
    "writes and reads slow and rising",
    "disk is fast local SSD on all members so disk is not the cause",
    "Data plane side",
    "serving pods have no dependency on the Kubernetes API so they keep answering",
    "running pods are fine means the API layer is slow, not the data plane",
    "Cause note",
    "etcd defaults assume one datacenter; test round trips and tune heartbeat interval and election timeout if you must span; etcd across regions is strongly discouraged",
    "Fix",
    "bring the member back close, or remove it and add one in the same datacenter; one membership change at a time; snapshot first; do not defragment a live member as a reflex; do not roll the whole control plane at once",
    "Prevention",
    "members in one low-latency domain with an odd count; alert on leader changes and request latency"
]

# Extract all text in order from SVG
def extract_text(element):
    res = ""
    if element.text:
        res += element.text
    for child in element:
        res += " " + extract_text(child)
    if element.tail:
        res += " " + element.tail
    return res

full_text = " ".join(extract_text(root).split())
print("\nExtracted normalized text length:", len(full_text))

for label in labels:
    # normalize spaces
    norm_label = " ".join(label.split())
    if norm_label in full_text:
        print(f"MATCH: {norm_label[:40]}...")
    else:
        print(f"MISSING: {norm_label}")
