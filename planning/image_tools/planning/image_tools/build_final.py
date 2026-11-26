#!/usr/bin/env python3
import pathlib

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1180" width="1600" height="1180">
  <title>Which API each HPA metric type reads</title>
  <desc>Table comparing Kubernetes HPA metric types, their source APIs, providers, and example use cases, followed by key scaling rules.</desc>

  <!-- Background -->
  <rect width="1600" height="1180" fill="#f5f8f5"/>

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="65" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Which API each HPA metric type reads</text>

  <!-- ==================== TABLE COLUMN HEADERS ==================== -->
  <g id="table-headers">
    <!-- Col 1: Type -->
    <rect x="40" y="100" width="285" height="56" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="182" y="138" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">Type</text>

    <!-- Col 2: Source API -->
    <rect x="337" y="100" width="380" height="56" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="527" y="138" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">Source API</text>

    <!-- Col 3: Provider -->
    <rect x="729" y="100" width="398" height="56" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="928" y="138" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">Provider</text>

    <!-- Col 4: Example -->
    <rect x="1139" y="100" width="421" height="56" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="1349" y="138" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">Example</text>
  </g>

  <!-- ==================== ROW 1: Resource ==================== -->
  <g id="row-1">
    <!-- Row outer card container -->
    <rect x="40" y="170" width="1520" height="118" rx="14" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>

    <!-- Col 1: Type (Resource) -->
    <rect x="48" y="176" width="269" height="106" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <!-- CPU Chip Icon (44px) -->
    <g transform="translate(160, 186)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="7" y="7" width="30" height="30" rx="4"/>
      <line x1="14" y1="1" x2="14" y2="7"/>
      <line x1="22" y1="1" x2="22" y2="7"/>
      <line x1="30" y1="1" x2="30" y2="7"/>
      <line x1="14" y1="37" x2="14" y2="43"/>
      <line x1="22" y1="37" x2="22" y2="43"/>
      <line x1="30" y1="37" x2="30" y2="43"/>
      <line x1="1" y1="14" x2="7" y2="14"/>
      <line x1="1" y1="22" x2="7" y2="22"/>
      <line x1="1" y1="30" x2="7" y2="30"/>
      <line x1="37" y1="14" x2="43" y2="14"/>
      <line x1="37" y1="22" x2="43" y2="22"/>
      <line x1="37" y1="30" x2="43" y2="30"/>
      <rect x="14" y="14" width="16" height="16" rx="2" fill="#207448"/>
    </g>
    <text x="182" y="266" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#207448">Resource</text>

    <!-- Col 2: Source API -->
    <rect x="337" y="176" width="380" height="106" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.2"/>
    <text x="527" y="238" text-anchor="middle" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#207448">metrics.k8s.io</text>

    <!-- Col 3: Provider -->
    <rect x="729" y="176" width="398" height="106" rx="10" fill="#ffffff"/>
    <text x="747" y="226" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="747" dy="0">metrics-server from </tspan>
      <tspan x="747" dy="32">kubelet and cAdvisor</tspan>
    </text>

    <!-- Col 4: Example -->
    <rect x="1139" y="176" width="421" height="106" rx="10" fill="#ffffff"/>
    <text x="1159" y="210" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="1159" dy="0">CPU or memory average </tspan>
      <tspan x="1159" dy="28">utilisation relative to </tspan>
      <tspan x="1159" dy="28">requests, or average value</tspan>
    </text>
  </g>

  <!-- ==================== ROW 2: ContainerResource ==================== -->
  <g id="row-2">
    <!-- Row outer card container -->
    <rect x="40" y="302" width="1520" height="118" rx="14" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>

    <!-- Col 1: Type (ContainerResource) -->
    <rect x="48" y="308" width="269" height="106" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <!-- Container App Window Icon (44px) -->
    <g transform="translate(160, 318)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="5" width="36" height="34" rx="5"/>
      <rect x="10" y="13" width="24" height="20" rx="3" fill="#207448"/>
      <line x1="4" y1="14" x2="40" y2="14"/>
    </g>
    <text x="182" y="396" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">ContainerResource</text>

    <!-- Col 2: Source API -->
    <rect x="337" y="308" width="380" height="106" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.2"/>
    <text x="527" y="354" text-anchor="middle" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="527" dy="0">metrics.k8s.io </tspan>
      <tspan x="527" dy="32" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="normal" fill="#303a36">per container</tspan>
    </text>

    <!-- Col 3: Provider (empty) -->
    <rect x="729" y="308" width="398" height="106" rx="10" fill="#ffffff"/>
    <line x1="908" y1="361" x2="948" y2="361" stroke="#c4d5c9" stroke-width="2.5" stroke-linecap="round"/>

    <!-- Col 4: Example -->
    <rect x="1139" y="308" width="421" height="106" rx="10" fill="#ffffff"/>
    <text x="1159" y="354" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="1159" dy="0">scale on the app container </tspan>
      <tspan x="1159" dy="32">only, ignoring sidecars</tspan>
    </text>
  </g>

  <!-- ==================== ROW 3: Pods ==================== -->
  <g id="row-3">
    <!-- Row outer card container -->
    <rect x="40" y="434" width="1520" height="118" rx="14" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>

    <!-- Col 1: Type (Pods) -->
    <rect x="48" y="440" width="269" height="106" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <!-- Pods Icon (44px) -->
    <g transform="translate(160, 450)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="22,3 40,13 40,31 22,41 4,31 4,13"/>
      <circle cx="22" cy="22" r="7" fill="#207448"/>
    </g>
    <text x="182" y="530" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#207448">Pods</text>

    <!-- Col 2: Source API -->
    <rect x="337" y="440" width="380" height="106" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.2"/>
    <text x="527" y="500" text-anchor="middle" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448">custom.metrics.k8s.io</text>

    <!-- Col 3: Provider -->
    <rect x="729" y="440" width="398" height="106" rx="10" fill="#ffffff"/>
    <text x="747" y="486" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="747" dy="0">via Prometheus Adapter, </tspan>
      <tspan x="747" dy="32">KEDA or vendor adapters</tspan>
    </text>

    <!-- Col 4: Example -->
    <rect x="1139" y="440" width="421" height="106" rx="10" fill="#ffffff"/>
    <text x="1159" y="486" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="1159" dy="0">per-pod requests_in_flight </tspan>
      <tspan x="1159" dy="32">or queue_length_per_pod</tspan>
    </text>
  </g>

  <!-- ==================== ROW 4: Object ==================== -->
  <g id="row-4">
    <!-- Row outer card container -->
    <rect x="40" y="566" width="1520" height="118" rx="14" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>

    <!-- Col 1: Type (Object) -->
    <rect x="48" y="572" width="269" height="106" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <!-- Object Ingress Routing Gateway Icon (44px) -->
    <g transform="translate(160, 582)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="5" y="5" width="34" height="34" rx="8"/>
      <circle cx="22" cy="16" r="4" fill="#207448"/>
      <path d="M 22 20 L 22 27 M 14 34 L 22 27 L 30 34"/>
      <circle cx="14" cy="34" r="2.5" fill="#207448"/>
      <circle cx="30" cy="34" r="2.5" fill="#207448"/>
    </g>
    <text x="182" y="662" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#207448">Object</text>

    <!-- Col 2: Source API -->
    <rect x="337" y="572" width="380" height="106" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.2"/>
    <text x="527" y="618" text-anchor="middle" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="527" dy="0">custom.metrics.k8s.io </tspan>
      <tspan x="527" dy="32" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="normal" fill="#303a36">for one object</tspan>
    </text>

    <!-- Col 3: Provider (empty) -->
    <rect x="729" y="572" width="398" height="106" rx="10" fill="#ffffff"/>
    <line x1="908" y1="625" x2="948" y2="625" stroke="#c4d5c9" stroke-width="2.5" stroke-linecap="round"/>

    <!-- Col 4: Example -->
    <rect x="1139" y="572" width="421" height="106" rx="10" fill="#ffffff"/>
    <text x="1159" y="618" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="1159" dy="0">Ingress </tspan>
      <tspan x="1159" dy="32">requests_per_second</tspan>
    </text>
  </g>

  <!-- ==================== ROW 5: External ==================== -->
  <g id="row-5">
    <!-- Row outer card container -->
    <rect x="40" y="698" width="1520" height="118" rx="14" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>

    <!-- Col 1: Type (External) -->
    <rect x="48" y="704" width="269" height="106" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <!-- Cloud Queue Broker Icon (44px) -->
    <g transform="translate(160, 714)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 11 32 A 7 7 0 0 1 11 19 A 11 11 0 0 1 31 14 A 9 9 0 0 1 38 25 A 7 7 0 0 1 34 32 Z"/>
      <circle cx="17" cy="25" r="2" fill="#207448"/>
      <circle cx="23" cy="25" r="2" fill="#207448"/>
      <circle cx="29" cy="25" r="2" fill="#207448"/>
    </g>
    <text x="182" y="794" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#207448">External</text>

    <!-- Col 2: Source API -->
    <rect x="337" y="704" width="380" height="106" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.2"/>
    <text x="527" y="764" text-anchor="middle" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448">external.metrics.k8s.io</text>

    <!-- Col 3: Provider -->
    <rect x="729" y="704" width="398" height="106" rx="10" fill="#ffffff"/>
    <text x="747" y="750" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="747" dy="0">via KEDA, Prometheus </tspan>
      <tspan x="747" dy="32">Adapter or cloud adapters</tspan>
    </text>

    <!-- Col 4: Example -->
    <rect x="1139" y="704" width="421" height="106" rx="10" fill="#ffffff"/>
    <text x="1159" y="750" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="1159" dy="0">SQS queue length, Pub/Sub </tspan>
      <tspan x="1159" dy="32">backlog, global QPS</tspan>
    </text>
  </g>

  <!-- ==================== FOOTER RULES ==================== -->
  <g id="footer-rules">
    <!-- Rule 1: utilisation metrics -->
    <g id="footer-rule-1">
      <rect x="40" y="850" width="1520" height="76" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <!-- Checklist Requirement Icon -->
      <g transform="translate(60, 866)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="6" width="32" height="32" rx="6"/>
        <polyline points="13,23 19,29 31,15"/>
      </g>
      <text x="124" y="896" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">utilisation metrics need requests on all containers or the metric is unavailable</text>
    </g>

    <!-- Rule 2: memory scaling warning (Orange Alert Box) -->
    <g id="footer-rule-2">
      <rect x="40" y="940" width="1520" height="76" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="3"/>
      <!-- Warning Alert Icon in Orange -->
      <g transform="translate(60, 956)" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="22,5 40,38 4,38" stroke="#db8129" stroke-width="3.5" fill="none"/>
        <line x1="22" y1="17" x2="22" y2="27" stroke="#db8129" stroke-width="3.5"/>
        <circle cx="22" cy="33" r="2.5" fill="#db8129"/>
      </g>
      <text x="124" y="986" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">memory is a poor scaling signal because it does not fall after load drops</text>
    </g>

    <!-- Rule 3: freshness delay -->
    <g id="footer-rule-3">
      <rect x="40" y="1030" width="1520" height="114" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <!-- Clock Freshness Timer Icon -->
      <g transform="translate(60, 1065)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="22" cy="22" r="18"/>
        <polyline points="22,11 22,22 31,22"/>
      </g>
      <text x="124" y="1076" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
        <tspan x="124" dy="0">freshness delay: metrics-server scrapes kubelets about every 15 s, </tspan>
        <tspan x="124" dy="34">custom metrics add the Prometheus scrape interval of 15 to 30 s plus the adapter</tspan>
      </text>
    </g>
  </g>
</svg>'''

with open("p3_0523_metric_types_apis.svg", "w") as f:
    f.write(svg_code)
print("Saved p3_0523_metric_types_apis.svg")

