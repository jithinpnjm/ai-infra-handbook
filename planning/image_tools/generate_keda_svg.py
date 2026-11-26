import re
import xml.etree.ElementTree as ET

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1180" width="1600" height="1180">
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
  <text x="800" y="60" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">KEDA: the switch and the dimmer</text>

  <!-- ==================== STAGE A & STAGE B ROW ==================== -->
  <!-- Stage A: The Switch -->
  <g id="stage-a-container">
    <rect x="40" y="95" width="710" height="225" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <!-- Switch Icon (56px) -->
    <g transform="translate(65, 110)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="10" width="48" height="28" rx="14" fill="#ffffff"/>
      <circle cx="18" cy="24" r="8" fill="#207448"/>
      <line x1="28" y1="24" x2="44" y2="24"/>
    </g>
    <!-- Stage A Title -->
    <text x="135" y="146" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Stage A</text>

    <!-- Stage A Inner White Card -->
    <rect x="58" y="165" width="674" height="140" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="76" y="196" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="76" dy="0">zero to one: the switch, handled by</tspan>
      <tspan x="76" dy="28">KEDA operator (a plain HPA cannot</tspan>
      <tspan x="76" dy="28">scale to zero because the formula</tspan>
      <tspan x="76" dy="28">multiplies by zero)</tspan>
    </text>
  </g>

  <!-- Connecting Arrow from Stage A to Stage B -->
  <line x1="750" y1="207" x2="840" y2="207" stroke="#207448" stroke-width="3" marker-end="url(#arrow)"/>

  <!-- Stage B: The Dimmer -->
  <g id="stage-b-container">
    <rect x="850" y="95" width="710" height="225" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <!-- Dimmer Dial Icon (56px) -->
    <g transform="translate(875, 110)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="20" fill="#ffffff"/>
      <circle cx="28" cy="28" r="8" fill="#207448"/>
      <line x1="28" y1="12" x2="28" y2="20"/>
      <line x1="40" y1="16" x2="34" y2="22"/>
      <line x1="44" y1="28" x2="36" y2="28"/>
    </g>
    <!-- Stage B Title -->
    <text x="945" y="146" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Stage B</text>

    <!-- Stage B Inner White Card -->
    <rect x="868" y="165" width="674" height="140" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="886" y="196" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="886" dy="0">one to N: the dimmer, handled by the</tspan>
      <tspan x="886" dy="28">HPA that KEDA creates, fed by KEDA</tspan>
      <tspan x="886" dy="28">metrics adapter on the</tspan>
      <tspan x="886" dy="28">External Metrics API</tspan>
    </text>
  </g>

  <!-- ==================== SCALEDOBJECT BATCH-EMBED MAIN CONTAINER ==================== -->
  <g id="scaledobject-section">
    <rect x="40" y="340" width="1520" height="425" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2"/>

    <!-- ScaledObject Header Icon & Title -->
    <g transform="translate(65, 355)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="26" cy="26" r="10"/>
      <path d="M26 6 v6 M26 40 v6 M6 26 h6 M40 26 h6 M12 12 l4 4 M36 36 l4 4 M12 40 l4 -4 M36 12 l4 -4"/>
    </g>
    <text x="135" y="392" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">ScaledObject batch-embed</text>

    <!-- Configuration Knobs / Settings (Left Column) -->
    <!-- Row 1: minReplicaCount 0, maxReplicaCount 50, pollingInterval 15 -->
    <rect x="65" y="420" width="225" height="56" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="177" y="456" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">minReplicaCount 0</text>

    <rect x="306" y="420" width="235" height="56" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="423" y="456" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">maxReplicaCount 50</text>

    <rect x="557" y="420" width="225" height="56" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="669" y="456" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">pollingInterval 15</text>

    <!-- Row 2: cooldownPeriod 300 (quiet time before one to zero) -->
    <rect x="65" y="492" width="717" height="84" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5"/>
    <text x="85" y="527" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="85" dy="0">cooldownPeriod 300</tspan>
      <tspan x="85" dy="30">(quiet time before one to zero)</tspan>
    </text>

    <!-- Row 3: scaleDown stabilizationWindowSeconds 600 -->
    <rect x="65" y="592" width="717" height="66" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5"/>
    <text x="85" y="634" font-family="monospace" font-size="24" fill="#303a36">scaleDown stabilizationWindowSeconds 600</text>

    <!-- Triggers (Right Column) -->
    <!-- Trigger 1: kafka lagThreshold 200 -->
    <g id="card-kafka">
      <rect x="808" y="420" width="727" height="62" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <g transform="translate(826, 432)" stroke="#207448" stroke-width="2.5" fill="none">
        <circle cx="10" cy="18" r="6" fill="#ffffff"/>
        <circle cx="28" cy="18" r="6" fill="#ffffff"/>
        <line x1="16" y1="18" x2="22" y2="18"/>
      </g>
      <text x="874" y="459" font-family="sans-serif" font-size="24" fill="#303a36">kafka lagThreshold 200</text>
    </g>

    <!-- Trigger 2: prometheus query sum vllm:num_requests_waiting threshold 5 -->
    <g id="card-prometheus">
      <rect x="808" y="498" width="727" height="78" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <g transform="translate(826, 514)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 6 32 L 14 18 L 22 26 L 30 10 L 36 20"/>
      </g>
      <text x="874" y="533" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="874" dy="0">prometheus query sum</tspan>
        <tspan x="874" dy="28">vllm:num_requests_waiting threshold 5</tspan>
      </text>
    </g>

    <!-- Trigger 3: cron 0 8 to 0 20 Monday to Friday desiredReplicas 4 (pre-warm business hours) -->
    <g id="card-cron">
      <rect x="808" y="592" width="727" height="84" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <g transform="translate(826, 608)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round">
        <circle cx="18" cy="20" r="14" fill="#ffffff"/>
        <polyline points="18,12 18,20 25,20"/>
      </g>
      <text x="874" y="627" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="874" dy="0">cron 0 8 to 0 20 Monday to Friday</tspan>
        <tspan x="874" dy="28">desiredReplicas 4 (pre-warm business hours)</tspan>
      </text>
    </g>

    <!-- Rule Bar inside ScaledObject -->
    <g id="rule-bar">
      <rect x="65" y="694" width="1470" height="54" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <text x="800" y="730" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">the largest desired count across active triggers wins, so cron acts as a floor in business hours</text>
    </g>
  </g>

  <!-- ==================== CONTRAST SECTION: ScaledJob vs ScaledObject ==================== -->
  <!-- ScaledJob transcribe-job -->
  <g id="card-scaledjob">
    <rect x="40" y="785" width="730" height="195" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <g transform="translate(65, 802)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="36" height="40" rx="4"/>
      <polyline points="14,24 20,30 32,18"/>
    </g>
    <text x="125" y="838" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">ScaledJob transcribe-job</text>
    <text x="65" y="884" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="65" dy="0">one short Job per queued message,</tspan>
      <tspan x="65" dy="30">aws-sqs-queue queueLength 1,</tspan>
      <tspan x="65" dy="30">maxReplicaCount 20, strategy accurate</tspan>
    </text>
  </g>

  <!-- ScaledObject (Contrast card) -->
  <g id="card-scaledobject-contrast">
    <rect x="830" y="785" width="730" height="195" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <g transform="translate(855, 802)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="10" width="40" height="36" rx="4"/>
      <line x1="6" y1="20" x2="46" y2="20"/>
      <circle cx="14" cy="15" r="2" fill="#207448"/>
      <circle cx="22" cy="15" r="2" fill="#207448"/>
    </g>
    <text x="915" y="838" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">ScaledObject</text>
    <text x="855" y="888" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="855" dy="0">keeps a long-running Deployment</tspan>
      <tspan x="855" dy="32">and changes its size</tspan>
    </text>
  </g>

  <!-- ==================== WARNING CALLOUT STRIP (Single Orange #db8129) ==================== -->
  <g id="warning-strip">
    <rect x="40" y="1000" width="1520" height="140" rx="14" fill="#fff5ea" stroke="#db8129" stroke-width="3"/>
    <!-- Warning Icon (Orange #db8129) -->
    <g transform="translate(68, 1038)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 50 44 H 6 Z"/>
      <line x1="28" y1="20" x2="28" y2="30"/>
      <circle cx="28" cy="37" r="1.8" fill="#db8129" stroke="none"/>
    </g>
    <text x="140" y="1058" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">
      <tspan x="140" dy="0">scale-to-zero on a GPU service costs a cold start; fine for a nightly batch job,</tspan>
      <tspan x="140" dy="34">painful for a person typing in chat</tspan>
    </text>
  </g>
</svg>
'''

with open("test_keda_candidate.svg", "w", encoding="utf-8") as f:
    f.write(svg_content.strip())

print("Saved test_keda_candidate.svg successfully!")
