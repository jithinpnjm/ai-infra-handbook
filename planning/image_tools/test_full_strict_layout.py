import re
import xml.etree.ElementTree as ET

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>From a vLLM metric to an HPA decision</title>
  <desc>Visual infographic explaining the pipeline from vLLM and Kafka metrics through Prometheus Adapter to Kubernetes Custom and External Metrics APIs, leading to HPA autoscaling decisions and troubleshooting checks.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerWidth="14" markerHeight="14" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">From a vLLM metric to an HPA decision</text>

  <!-- ==================== COLUMN 1: METRIC SOURCES ==================== -->

  <!-- Node 1: vLLM pod exposes vllm:num_requests_waiting -->
  <g id="node-vllm">
    <rect x="40" y="100" width="450" height="145" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Pod / Container Window Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(60, 112)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="44" rx="8" />
      <line x1="4" y1="20" x2="52" y2="20" />
      <circle cx="12" cy="13" r="2.5" fill="#207448" />
      <circle cx="20" cy="13" r="2.5" fill="#207448" />
      <path d="M 18 34 L 26 42 L 40 28" />
    </g>
    <text x="60" y="192" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36"><tspan x="60" dy="0">vLLM pod exposes </tspan><tspan x="60" dy="32" font-family="monospace">vllm:num_requests_waiting</tspan></text>
  </g>

  <!-- Arrow 1: vLLM pod -> Prometheus scrapes it (Vertical Down) -->
  <line x1="265" y1="245" x2="265" y2="265" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Node 2: Prometheus scrapes it -->
  <g id="node-prometheus">
    <rect x="40" y="265" width="450" height="145" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Clock / Scraper Timer Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(60, 278)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="28,14 28,28 38,28" />
      <path d="M 14 8 L 10 4 M 42 8 L 46 4" />
    </g>
    <text x="60" y="358" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36"><tspan x="60" dy="0">Prometheus </tspan><tspan x="60" dy="32">scrapes it</tspan></text>
  </g>

  <!-- Node 6: kafka_consumergroup_lag topic embed -->
  <g id="node-kafka">
    <rect x="40" y="855" width="450" height="145" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Storage / Queue Cylinder Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(60, 868)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="20" ry="6" />
      <path d="M 8 14 v 14 c 0 3.3 9 6 20 6 s 20 -2.7 20 -6 v -14" />
      <path d="M 8 28 v 14 c 0 3.3 9 6 20 6 s 20 -2.7 20 -6 v -14" />
    </g>
    <text x="60" y="948" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36"><tspan x="60" dy="0" font-family="monospace">kafka_consumergroup_lag </tspan><tspan x="60" dy="32">topic embed</tspan></text>
  </g>

  <!-- ==================== COLUMN 2: PROMETHEUS-ADAPTER RULES ==================== -->

  <!-- Arrow 2: Prometheus scrapes it -> prometheus-adapter rule (Horizontal Right) -->
  <line x1="490" y1="337" x2="520" y2="337" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Node 3: prometheus-adapter rule -->
  <g id="node-adapter-rule">
    <rect x="520" y="100" width="500" height="425" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Gear / Service Translation Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(545, 114)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="10" />
      <path d="M 28 6 L 28 12 M 28 44 L 28 50 M 6 28 L 12 28 M 44 28 L 50 28 M 12 12 L 17 17 M 39 39 L 44 44 M 12 44 L 17 39 M 39 17 L 44 12" />
    </g>
    <text x="545" y="196" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="545" dy="0" font-weight="bold" fill="#207448">prometheus-adapter rule: </tspan><tspan x="545" dy="31">seriesQuery </tspan><tspan x="545" dy="31">vllm:num_requests_waiting </tspan><tspan x="545" dy="31">with namespace and pod labels; </tspan><tspan x="545" dy="31">resources overrides map </tspan><tspan x="545" dy="31">namespace and pod; </tspan><tspan x="545" dy="31">name as vllm_requests_waiting; </tspan><tspan x="545" dy="31">metricsQuery sum by group</tspan></text>
  </g>

  <!-- Node 7: rule name kafka_lag -->
  <g id="node-rule-kafka">
    <rect x="520" y="855" width="500" height="145" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Rule Configuration Sliders Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(545, 870)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="10" y1="16" x2="46" y2="16" />
      <circle cx="20" cy="16" r="4" fill="#207448" />
      <line x1="10" y1="28" x2="46" y2="28" />
      <circle cx="36" cy="28" r="4" fill="#207448" />
      <line x1="10" y1="40" x2="46" y2="40" />
      <circle cx="24" cy="40" r="4" fill="#207448" />
    </g>
    <text x="545" y="958" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">rule name kafka_lag</text>
  </g>

  <!-- Arrow 5: kafka_consumergroup_lag -> rule name kafka_lag (Horizontal Right) -->
  <line x1="490" y1="927" x2="520" y2="927" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- ==================== COLUMN 3: K8S METRICS APIS & HPA ==================== -->

  <!-- Arrow 3: prometheus-adapter rule -> custom.metrics.k8s.io API (Horizontal Right) -->
  <line x1="1020" y1="150" x2="1050" y2="150" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Node 4: custom.metrics.k8s.io API -->
  <g id="node-custom-api">
    <rect x="1050" y="100" width="500" height="105" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- API Gateway Server Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(1075, 110)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="6" />
      <line x1="6" y1="22" x2="50" y2="22" />
      <circle cx="14" cy="15" r="2.5" fill="#207448" />
      <line x1="16" y1="34" x2="40" y2="34" />
      <circle cx="40" cy="34" r="3" fill="#207448" />
    </g>
    <text x="1075" y="186" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">custom.metrics.k8s.io API</text>
  </g>

  <!-- Command under Custom API -->
  <g id="cmd-custom-api">
    <rect x="1050" y="215" width="500" height="150" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
    <text x="1070" y="247" font-family="monospace" font-size="24" fill="#303a36"><tspan x="1070" dy="0">kubectl get --raw </tspan><tspan x="1070" dy="30">/apis/custom.metrics.k8s.io/</tspan><tspan x="1070" dy="30">v1beta1/namespaces/serving/</tspan><tspan x="1070" dy="30">pods/*/vllm_requests_waiting</tspan></text>
  </g>

  <!-- Arrow 4: custom.metrics.k8s.io API -> HPA reads it and decides (Bypass Around Command Box) -->
  <path d="M 1550 152 L 1572 152 L 1572 430 L 1550 430" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Node 5: HPA reads it and decides -->
  <g id="node-hpa">
    <rect x="1050" y="375" width="500" height="115" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Scale Balancer Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(1075, 385)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="28" y1="8" x2="28" y2="48" />
      <line x1="12" y1="18" x2="44" y2="18" />
      <path d="M 12 18 L 6 36 L 18 36 Z" />
      <path d="M 44 18 L 38 36 L 50 36 Z" />
    </g>
    <text x="1075" y="460" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36"><tspan x="1075" dy="0">HPA reads it </tspan><tspan x="1075" dy="30">and decides</tspan></text>
  </g>

  <!-- Command under HPA -->
  <g id="cmd-hpa">
    <rect x="1050" y="500" width="500" height="85" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
    <text x="1070" y="532" font-family="monospace" font-size="24" fill="#303a36"><tspan x="1070" dy="0">kubectl describe hpa </tspan><tspan x="1070" dy="30">vllm -n serving</tspan></text>
  </g>

  <!-- Conditions Box under HPA command -->
  <g id="box-conditions">
    <rect x="1050" y="595" width="500" height="250" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="1070" y="628" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="1070" dy="0" font-weight="bold">AbleToScale: </tspan><tspan x="1070" dy="25">can the HPA change </tspan><tspan x="1070" dy="25">the count at all</tspan></text>
    <text x="1070" y="705" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="1070" dy="0" font-weight="bold">ScalingActive: </tspan><tspan x="1070" dy="25">can it read the metrics</tspan></text>
    <text x="1070" y="760" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="1070" dy="0" font-weight="bold">ScalingLimited: </tspan><tspan x="1070" dy="25">has a minimum or maximum </tspan><tspan x="1070" dy="25">capped the result</tspan></text>
  </g>

  <!-- Arrow 6: rule name kafka_lag -> external.metrics.k8s.io (Horizontal Right) -->
  <line x1="1020" y1="915" x2="1050" y2="915" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Node 8: external.metrics.k8s.io -->
  <g id="node-external-api">
    <rect x="1050" y="855" width="500" height="105" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- External Network Globe Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(1075, 865)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <ellipse cx="28" cy="28" rx="10" ry="22" />
      <line x1="6" y1="28" x2="50" y2="28" />
    </g>
    <text x="1075" y="942" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">external.metrics.k8s.io</text>
  </g>

  <!-- Command under External API -->
  <g id="cmd-external-api">
    <rect x="1050" y="970" width="500" height="120" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
    <text x="1070" y="998" font-family="monospace" font-size="24" fill="#303a36"><tspan x="1070" dy="0">kubectl get --raw </tspan><tspan x="1070" dy="29">/apis/external.metrics.k8s.io/</tspan><tspan x="1070" dy="29">v1beta1/namespaces/serving/</tspan><tspan x="1070" dy="29">kafka_lag</tspan></text>
  </g>

  <!-- ==================== BOTTOM NOTE (SINGLE ORANGE HIGHLIGHT) ==================== -->

  <g id="box-note">
    <rect x="40" y="1105" width="1510" height="70" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="3" />
    <text x="795" y="1149" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">if the first command returns nothing, no amount of tuning helps</text>
  </g>
</svg>'''

with open("test_generated.svg", "w") as f:
    f.write(svg_code)

print("Saved test_generated.svg. Running strict checks...")
