import re
import xml.etree.ElementTree as ET

# Canvas H = 1180
# 1. Title: y = 58
# 2. Stage A and Stage B:
# Container: y = 90, h = 236.
# Inner white box: rx=58, ry=160, rw=674, rh=150.
# Text line 1: y = 160 + 36 = 196. dy = 28.
# Lines at y = 196, 224, 252, 280.
# Top pad: (196 - 19.2) - 160 = 16.8 px.
# Bottom pad: (160 + 150) - (280 + 4.8) = 310 - 284.8 = 25.2 px. PASS!

# Left: Stage A
# Right: Stage B (rx=868, ry=160, rw=674, rh=150. Text x=886, y=196)

# 3. ScaledObject container: y = 345, h = 425 (ends at 770).
# Knobs (Left column: x = 65 to 782, w = 717):
# - Row 1: minReplicaCount 0 (x=65, y=412, w=345, h=58)
#   Text x=237, y=412+37=449.
# - Row 1: maxReplicaCount 50 (x=435, y=412, w=347, h=58)
#   Text x=608, y=412+37=449.
# - Row 2: pollingInterval 15 (x=65, y=480, w=717, h=56)
#   Text x=423, y=480+36=516.
# - Row 3: cooldownPeriod (2 lines, h=88, y=546)
#   Text x=85, y=546+36=582, dy=28.
#   Top pad: 582-19.2 - 546 = 16.8 px.
#   Bottom pad: (546+88) - (582+28+4.8) = 634 - 614.8 = 19.2 px. PASS!
# - Row 4: scaleDown (1 line, h=56, y=644)
#   Text x=85, y=644+36=680.
#   Top pad: 680-19.2 - 644 = 16.8 px.
#   Bottom pad: (644+56) - (680+4.8) = 700 - 684.8 = 15.2 -> let's make h=58, y=644, text y=680 -> bottom pad = 17.2 px!

# Triggers (Right column: x = 808, w = 727):
# - Trigger 1: kafka (1 line, h=58, y=412)
#   Text x=874, y=412+37=449.
# - Trigger 2: prometheus (2 lines, h=88, y=480)
#   Text x=874, y=480+36=516, dy=28.
# - Trigger 3: cron (2 lines, h=88, y=578)
#   Text x=874, y=578+36=614, dy=28.

# - Rule bar: (1 line, h=58, y=680, w=1470)
#   Text x=800, y=680+37=717.
#   Top pad: 717-19.2 - 680 = 17.8 px.
#   Bottom pad: (680+58) - (717+4.8) = 738 - 721.8 = 16.2 px. PASS!

# 4. Contrast: y = 785, h = 195.
# - ScaledJob: x=40, y=785, w=730, h=195.
#   Title: x=125, y=832.
#   Text 3 lines: x=65, y=878, dy=28 (878, 906, 934).
#   Top of line 1: 878 - 19.2 = 858.8 (> 832 title bottom).
#   Bottom of line 3: 934 + 4.8 = 938.8.
#   Bottom pad: (785 + 195) - 938.8 = 980 - 938.8 = 41.2 px. PASS!
# - ScaledObject: x=830, y=785, w=730, h=195.
#   Title: x=915, y=832.
#   Text 2 lines: x=855, y=888, dy=30 (888, 918).
#   Bottom pad: 980 - (918 + 4.8) = 57.2 px. PASS!

# 5. Warning: y = 1000, h = 140, w = 1520.
#   Text 2 lines: x=140, y=1054, dy=32 (1054, 1086).
#   Top pad: 1054 - 19.2 - 1000 = 34.8 px.
#   Bottom pad: (1000 + 140) - (1086 + 4.8) = 1140 - 1090.8 = 49.2 px. PASS!

svg_template = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1180" width="1600" height="1180">
  <title>KEDA: the switch and the dimmer</title>
  <desc>Infographic explaining KEDA autoscaling: Stage A switch from zero to one by KEDA operator, Stage B dimmer from one to N by HPA, ScaledObject batch-embed triggers and settings, ScaledJob transcribe-job contrast, and scale-to-zero warning.</desc>

  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#207448"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1180" fill="#f5f8f5"/>

  <!-- Main Diagram Title (48px bold) -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">KEDA: the switch and the dimmer</text>

  <!-- Stage A: The Switch -->
  <g id="stage-a-container">
    <rect x="40" y="90" width="710" height="236" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <g transform="translate(65, 104)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="10" width="48" height="28" rx="14" fill="#ffffff"/>
      <circle cx="18" cy="24" r="8" fill="#207448"/>
      <line x1="28" y1="24" x2="44" y2="24"/>
    </g>
    <text x="135" y="142" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Stage A</text>

    <rect x="58" y="160" width="674" height="150" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="76" y="196" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="76" dy="0">zero to one: the switch, handled by</tspan>
      <tspan x="76" dy="28">KEDA operator (a plain HPA cannot</tspan>
      <tspan x="76" dy="28">scale to zero because the formula</tspan>
      <tspan x="76" dy="28">multiplies by zero)</tspan>
    </text>
  </g>

  <!-- Connecting Arrow from Stage A to Stage B -->
  <line x1="750" y1="208" x2="840" y2="208" stroke="#207448" stroke-width="3" marker-end="url(#arrow)"/>

  <!-- Stage B: The Dimmer -->
  <g id="stage-b-container">
    <rect x="850" y="90" width="710" height="236" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <g transform="translate(875, 104)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="20" fill="#ffffff"/>
      <circle cx="28" cy="28" r="8" fill="#207448"/>
      <line x1="28" y1="12" x2="28" y2="20"/>
      <line x1="40" y1="16" x2="34" y2="22"/>
      <line x1="44" y1="28" x2="36" y2="28"/>
    </g>
    <text x="945" y="142" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Stage B</text>

    <rect x="868" y="160" width="674" height="150" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="886" y="196" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="886" dy="0">one to N: the dimmer, handled by the</tspan>
      <tspan x="886" dy="28">HPA that KEDA creates, fed by KEDA</tspan>
      <tspan x="886" dy="28">metrics adapter on the</tspan>
      <tspan x="886" dy="28">External Metrics API</tspan>
    </text>
  </g>

  <!-- ScaledObject batch-embed Main Container -->
  <g id="scaledobject-section">
    <rect x="40" y="342" width="1520" height="422" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2"/>

    <g transform="translate(65, 357)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="26" cy="26" r="10"/>
      <path d="M26 6 v6 M26 40 v6 M6 26 h6 M40 26 h6 M12 12 l4 4 M36 36 l4 4 M12 40 l4 -4 M36 12 l4 -4"/>
    </g>
    <text x="135" y="394" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">ScaledObject batch-embed</text>

    <!-- Configuration Knobs -->
    <rect x="65" y="412" width="345" height="58" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="237" y="449" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">minReplicaCount 0</text>

    <rect x="435" y="412" width="347" height="58" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="608" y="449" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">maxReplicaCount 50</text>

    <rect x="65" y="480" width="717" height="58" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="423" y="516" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">pollingInterval 15</text>

    <rect x="65" y="546" width="717" height="88" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5"/>
    <text x="85" y="582" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="85" dy="0">cooldownPeriod 300</tspan>
      <tspan x="85" dy="28">(quiet time before one to zero)</tspan>
    </text>

    <rect x="65" y="644" width="717" height="58" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5"/>
    <text x="85" y="681" font-family="monospace" font-size="24" fill="#303a36">scaleDown stabilizationWindowSeconds 600</text>

    <!-- Triggers -->
    <g id="card-kafka">
      <rect x="808" y="412" width="727" height="58" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <g transform="translate(826, 423)" stroke="#207448" stroke-width="2.5" fill="none">
        <circle cx="10" cy="18" r="6" fill="#ffffff"/>
        <circle cx="28" cy="18" r="6" fill="#ffffff"/>
        <line x1="16" y1="18" x2="22" y2="18"/>
      </g>
      <text x="874" y="449" font-family="sans-serif" font-size="24" fill="#303a36">kafka lagThreshold 200</text>
    </g>

    <g id="card-prometheus">
      <rect x="808" y="480" width="727" height="88" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <g transform="translate(826, 502)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 6 30 L 14 18 L 22 26 L 30 10 L 36 20"/>
      </g>
      <text x="874" y="516" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="874" dy="0">prometheus query sum</tspan>
        <tspan x="874" dy="28">vllm:num_requests_waiting threshold 5</tspan>
      </text>
    </g>

    <g id="card-cron">
      <rect x="808" y="578" width="727" height="88" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <g transform="translate(826, 600)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round">
        <circle cx="18" cy="20" r="14" fill="#ffffff"/>
        <polyline points="18,12 18,20 25,20"/>
      </g>
      <text x="874" y="614" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="874" dy="0">cron 0 8 to 0 20 Monday to Friday</tspan>
        <tspan x="874" dy="28">desiredReplicas 4 (pre-warm business hours)</tspan>
      </text>
    </g>

    <!-- Rule Bar -->
    <g id="rule-bar">
      <rect x="65" y="678" width="1470" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <text x="800" y="716" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">the largest desired count across active triggers wins, so cron acts as a floor in business hours</text>
    </g>
  </g>

  <!-- Contrast Section -->
  <g id="card-scaledjob">
    <rect x="40" y="785" width="730" height="195" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <g transform="translate(65, 802)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="36" height="40" rx="4"/>
      <polyline points="14,24 20,30 32,18"/>
    </g>
    <text x="125" y="836" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">ScaledJob transcribe-job</text>
    <text x="65" y="880" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="65" dy="0">one short Job per queued message,</tspan>
      <tspan x="65" dy="30">aws-sqs-queue queueLength 1,</tspan>
      <tspan x="65" dy="30">maxReplicaCount 20, strategy accurate</tspan>
    </text>
  </g>

  <g id="card-scaledobject-contrast">
    <rect x="830" y="785" width="730" height="195" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <g transform="translate(855, 802)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="10" width="40" height="36" rx="4"/>
      <line x1="6" y1="20" x2="46" y2="20"/>
      <circle cx="14" cy="15" r="2" fill="#207448"/>
      <circle cx="22" cy="15" r="2" fill="#207448"/>
    </g>
    <text x="915" y="836" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">ScaledObject</text>
    <text x="855" y="888" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="855" dy="0">keeps a long-running Deployment</tspan>
      <tspan x="855" dy="32">and changes its size</tspan>
    </text>
  </g>

  <!-- Warning Callout Strip -->
  <g id="warning-strip">
    <rect x="40" y="1000" width="1520" height="140" rx="14" fill="#fff5ea" stroke="#db8129" stroke-width="3"/>
    <g transform="translate(68, 1038)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 50 44 H 6 Z"/>
      <line x1="28" y1="20" x2="28" y2="30"/>
      <circle cx="28" cy="37" r="1.8" fill="#db8129" stroke="none"/>
    </g>
    <text x="140" y="1054" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">
      <tspan x="140" dy="0">scale-to-zero on a GPU service costs a cold start; fine for a nightly batch job,</tspan>
      <tspan x="140" dy="34">painful for a person typing in chat</tspan>
    </text>
  </g>
</svg>
'''

with open("p3_0523_keda_switch_dimmer.svg", "w", encoding="utf-8") as f:
    f.write(svg_template.strip())

print("Saved p3_0523_keda_switch_dimmer.svg")
