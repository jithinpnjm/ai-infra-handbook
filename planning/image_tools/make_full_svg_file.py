import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>What the kubelet does</title>
  <desc>Architecture and control flow of the Kubernetes kubelet node agent, including pod sources, per-pod sync workers, managers, runtime CRI integration, probers, and status reporting.</desc>

  <defs>
    <marker id="arrow" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
      <path d="M 2 2 L 10 6 L 2 10 z" fill="#207448" />
    </marker>
    <filter id="shadow" x="-2%" y="-4%" width="104%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.05" />
    </filter>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="58" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">What the kubelet does</text>

  <!-- ==================== ROW 1 ==================== -->

  <!-- Node Lease -->
  <g id="node-LEASE">
    <rect x="40" y="95" width="350" height="160" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- Heartbeat Icon -->
    <rect x="58" y="145" width="64" height="60" rx="6" fill="none" stroke="#207448" stroke-width="3.5" />
    <path d="M 64 175 h 10 l 7 -18 l 10 32 l 9 -22 l 7 8 h 9" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />
    <!-- Text -->
    <text x="140" y="145" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Node lease +</text>
    <text x="140" y="180" font-family="sans-serif" font-size="24" fill="#303a36">node status</text>
    <text x="140" y="214" font-family="sans-serif" font-size="24" fill="#303a36">heartbeats</text>
  </g>

  <!-- Pod sources Subgraph Container -->
  <g id="container-Sources">
    <rect x="415" y="95" width="1145" height="160" rx="10" fill="#f0f6f1" stroke="#207448" stroke-width="2.5" stroke-dasharray="8 6" />
    <text x="440" y="125" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Pod sources</text>

    <!-- Subgraph Node: API -->
    <g id="node-API">
      <rect x="435" y="135" width="390" height="110" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" filter="url(#shadow)" />
      <!-- Cloud Server Icon -->
      <rect x="450" y="144" width="44" height="30" rx="4" fill="none" stroke="#207448" stroke-width="3" />
      <line x1="458" y1="162" x2="466" y2="162" stroke="#207448" stroke-width="3" stroke-linecap="round" />
      <circle cx="482" cy="162" r="2" fill="#207448" />
      <path d="M 472 174 v 6 m -10 0 h 20" stroke="#207448" stroke-width="3" stroke-linecap="round" />
      <!-- API Text -->
      <text x="508" y="168" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">API server</text>
      <text x="630" y="205" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">(watch pods with</text>
      <text x="630" y="233" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">spec.nodeName=this node)</text>
    </g>

    <!-- Subgraph Node: FILE -->
    <g id="node-FILE">
      <rect x="845" y="135" width="335" height="110" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" filter="url(#shadow)" />
      <!-- Folder Icon -->
      <path d="M 865 155 h 18 l 7 8 h 23 a 4 4 0 0 1 4 4 v 26 a 4 4 0 0 1 -4 4 h -48 a 4 4 0 0 1 -4 -4 v -34 a 4 4 0 0 1 4 -4 z" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round" />
      <text x="930" y="175" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Static pod</text>
      <text x="930" y="215" font-family="sans-serif" font-size="26" fill="#303a36">manifests dir</text>
    </g>

    <!-- Subgraph Node: HTTP -->
    <g id="node-HTTP">
      <rect x="1200" y="135" width="345" height="110" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" filter="url(#shadow)" />
      <!-- Globe Icon -->
      <circle cx="1232" cy="188" r="22" fill="none" stroke="#207448" stroke-width="3" />
      <ellipse cx="1232" cy="188" rx="9" ry="22" fill="none" stroke="#207448" stroke-width="2" />
      <line x1="1210" y1="188" x2="1254" y2="188" stroke="#207448" stroke-width="2" />
      <text x="1275" y="174" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">HTTP manifest</text>
      <text x="1275" y="212" font-family="sans-serif" font-size="26" fill="#303a36">URL (rare)</text>
    </g>
  </g>

  <!-- ==================== ROW 2 ==================== -->

  <!-- cAdvisor -->
  <g id="node-CAD">
    <rect x="40" y="285" width="440" height="135" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- Bar chart metrics icon -->
    <rect x="237" y="295" width="46" height="38" rx="4" fill="none" stroke="#207448" stroke-width="3" />
    <line x1="247" y1="324" x2="247" y2="314" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />
    <line x1="257" y1="324" x2="257" y2="304" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />
    <line x1="267" y1="324" x2="267" y2="310" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />
    <text x="260" y="366" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">cAdvisor/cgroup stats</text>
    <text x="260" y="400" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">→ /metrics, /stats/summary</text>
  </g>

  <!-- Pod Manager -->
  <g id="node-PM">
    <rect x="580" y="285" width="440" height="135" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- Merge icon -->
    <circle cx="782" cy="305" r="5" fill="none" stroke="#207448" stroke-width="3" />
    <circle cx="782" cy="327" r="5" fill="none" stroke="#207448" stroke-width="3" />
    <circle cx="810" cy="316" r="5" fill="none" stroke="#207448" stroke-width="3" />
    <path d="M 787 307 c 10 3 14 7 18 9 M 787 325 c 10 -3 14 -7 18 -9" fill="none" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
    <text x="800" y="366" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">Pod manager</text>
    <text x="800" y="400" font-family="sans-serif" font-size="26" fill="#303a36" text-anchor="middle">/ config merge</text>
  </g>

  <!-- Image GC -->
  <g id="node-IMG">
    <rect x="1120" y="285" width="440" height="135" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- Trash / GC icon -->
    <path d="M 1322 304 h 36 m -24 0 v -6 h 12 v 6 m -15 7 l 3 24 h 18 l 3 -24" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
    <line x1="1335" y1="316" x2="1335" y2="328" stroke="#207448" stroke-width="2.5" />
    <line x1="1345" y1="316" x2="1345" y2="328" stroke="#207448" stroke-width="2.5" />
    <text x="1340" y="366" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">Image GC /</text>
    <text x="1340" y="402" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">container GC</text>
  </g>

  <!-- ==================== ROW 3 ==================== -->

  <!-- Eviction Manager -->
  <g id="node-EV">
    <rect x="40" y="450" width="440" height="135" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- Shield Alert icon -->
    <path d="M 242 468 l 18 -7 l 18 7 v 18 c 0 13 -18 22 -18 22 c 0 0 -18 -9 -18 -22 z" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round" />
    <line x1="260" y1="477" x2="260" y2="489" stroke="#207448" stroke-width="3" stroke-linecap="round" />
    <circle cx="260" cy="497" r="1.5" fill="#207448" />
    <text x="260" y="534" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">Eviction manager</text>
    <text x="260" y="568" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">(node pressure)</text>
  </g>

  <!-- Per-Pod Workers (syncPod) - SINGLE ORANGE ACCENT NODE -->
  <g id="node-PW">
    <rect x="560" y="450" width="480" height="135" rx="10" fill="#fffdfa" stroke="#db8129" stroke-width="4" filter="url(#shadow)" />
    <!-- Gear icon in orange -->
    <circle cx="800" cy="486" r="14" fill="none" stroke="#db8129" stroke-width="3.5" />
    <path d="M 800 466 v 6 m 0 28 v 6 m -20 -20 h 6 m 28 0 h 6 m -18 -12 l 4 4 m 14 14 l 4 4 m -22 0 l 4 -4 m 14 -14 l 4 -4" stroke="#db8129" stroke-width="3" stroke-linecap="round" />
    <circle cx="800" cy="486" r="5" fill="#db8129" />
    <text x="800" y="534" font-family="sans-serif" font-size="32" font-weight="bold" fill="#db8129" text-anchor="middle">Per-pod workers</text>
    <text x="800" y="568" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36" text-anchor="middle">(syncPod)</text>
  </g>

  <!-- CRI Client -->
  <g id="node-CRI">
    <rect x="1120" y="450" width="440" height="135" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- Shipping Container 3D box icon -->
    <path d="M 1320 472 l 20 -8 l 20 8 v 22 l -20 8 l -20 -8 z" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round" />
    <line x1="1340" y1="464" x2="1340" y2="502" stroke="#207448" stroke-width="2.5" />
    <line x1="1320" y1="472" x2="1340" y2="483" stroke="#207448" stroke-width="2" />
    <line x1="1360" y1="472" x2="1340" y2="483" stroke="#207448" stroke-width="2" />
    <text x="1340" y="534" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">CRI client →</text>
    <text x="1340" y="568" font-family="monospace" font-size="26" fill="#303a36" text-anchor="middle">containerd/CRI-O</text>
  </g>

  <!-- ==================== ROW 4 ==================== -->

  <!-- Volume Manager -->
  <g id="node-VM">
    <rect x="40" y="620" width="440" height="135" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- Cylinder icon -->
    <ellipse cx="80" cy="648" rx="20" ry="7" fill="none" stroke="#207448" stroke-width="3" />
    <path d="M 60 648 v 12 c 0 3.8 9 7 20 7 s 20 -3.2 20 -7 v -12" fill="none" stroke="#207448" stroke-width="3" />
    <path d="M 60 660 v 12 c 0 3.8 9 7 20 7 s 20 -3.2 20 -7 v -12" fill="none" stroke="#207448" stroke-width="3" />
    <!-- VM Text -->
    <text x="125" y="658" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Volume manager</text>
    <text x="260" y="698" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">(CSI, emptyDir,</text>
    <text x="260" y="728" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">configmap...)</text>
  </g>

  <!-- PLEG -->
  <g id="node-PLEG">
    <rect x="1120" y="620" width="440" height="135" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- PLEG loop / reload cycle icon -->
    <path d="M 1324 490 a 16 16 0 1 1 28 8" transform="translate(0, 168)" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" />
    <path d="M 1354 664 l -2 8 l -8 -3" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
    <circle cx="1340" cy="658" r="3.5" fill="#207448" />
    <text x="1340" y="704" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">PLEG: relist container</text>
    <text x="1340" y="738" font-family="sans-serif" font-size="26" fill="#303a36" text-anchor="middle">states → events</text>
  </g>

  <!-- ==================== ROW 5 ==================== -->

  <!-- Resource Managers -->
  <g id="node-DM">
    <rect x="40" y="785" width="440" height="135" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- CPU Chip icon -->
    <rect x="62" y="805" width="38" height="38" rx="4" fill="none" stroke="#207448" stroke-width="3" />
    <rect x="71" y="814" width="20" height="20" rx="2" fill="none" stroke="#207448" stroke-width="2" />
    <line x1="71" y1="800" x2="71" y2="805" stroke="#207448" stroke-width="2.5" />
    <line x1="81" y1="800" x2="81" y2="805" stroke="#207448" stroke-width="2.5" />
    <line x1="91" y1="800" x2="91" y2="805" stroke="#207448" stroke-width="2.5" />
    <line x1="71" y1="843" x2="71" y2="848" stroke="#207448" stroke-width="2.5" />
    <line x1="81" y1="843" x2="81" y2="848" stroke="#207448" stroke-width="2.5" />
    <line x1="91" y1="843" x2="91" y2="848" stroke="#207448" stroke-width="2.5" />
    <!-- Text -->
    <text x="125" y="825" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Resource managers</text>
    <text x="260" y="865" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">CPU / memory /</text>
    <text x="260" y="898" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">topology / device</text>
  </g>

  <!-- Prober -->
  <g id="node-PR">
    <rect x="580" y="785" width="440" height="135" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- Sensor probe / Stethoscope pulse icon -->
    <circle cx="792" cy="810" r="11" fill="none" stroke="#207448" stroke-width="3" />
    <path d="M 792 821 v 9 a 6 6 0 0 0 12 0 v -14" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" />
    <circle cx="810" cy="816" r="3.5" fill="#207448" />
    <text x="800" y="868" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">Prober</text>
    <text x="800" y="904" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">(startup/readiness/liveness)</text>
  </g>

  <!-- Status Manager -->
  <g id="node-SM">
    <rect x="1120" y="785" width="440" height="135" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- Checklist icon -->
    <rect x="1322" y="798" width="36" height="44" rx="4" fill="none" stroke="#207448" stroke-width="3" />
    <line x1="1332" y1="812" x2="1348" y2="812" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
    <line x1="1332" y1="822" x2="1348" y2="822" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
    <line x1="1332" y1="832" x2="1344" y2="832" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
    <text x="1340" y="868" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">Status manager</text>
    <text x="1340" y="904" font-family="sans-serif" font-size="26" fill="#303a36" text-anchor="middle">→ API server</text>
  </g>

  <!-- ==================== ROW 6 ==================== -->

  <!-- Kubelet HTTPS Server -->
  <g id="node-KAPI">
    <rect x="150" y="960" width="1300" height="150" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" filter="url(#shadow)" />
    <!-- HTTPS Security lock icon -->
    <rect x="190" y="1014" width="48" height="50" rx="6" fill="none" stroke="#207448" stroke-width="3.5" />
    <path d="M 202 1014 v -12 a 12 12 0 0 1 24 0 v 12" fill="none" stroke="#207448" stroke-width="3.5" />
    <circle cx="214" cy="1038" r="3.5" fill="#207448" />
    <line x1="214" y1="1042" x2="214" y2="1052" stroke="#207448" stroke-width="3" />
    <text x="750" y="1018" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">Kubelet HTTPS server :10250</text>
    <text x="750" y="1068" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">(logs, exec, attach, port-forward, metrics, pods)</text>
  </g>

  <!-- ==================== ARROWS (EXACTLY 13) ==================== -->

  <!-- 1. LEASE --> API -->
  <path d="M 390 190 L 435 190" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- 2. Sources container --> PM -->
  <path d="M 800 255 L 800 285" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- 3. CAD --> EV -->
  <path d="M 260 420 L 260 450" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- 4. PM --> PW -->
  <path d="M 800 420 L 800 450" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- 5. IMG --> CRI -->
  <path d="M 1340 420 L 1340 450" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- 6. EV --> PW -->
  <path d="M 480 517 L 560 517" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- 7. PW --> CRI -->
  <path d="M 1040 495 L 1120 495" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- 8. CRI --> PLEG -->
  <path d="M 1340 585 L 1340 620" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- 9. PLEG --> PW -->
  <path d="M 1120 687 L 1075 687 L 1075 545 L 1040 545" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round" marker-end="url(#arrow)" />

  <!-- 10. PW --> VM -->
  <path d="M 640 585 L 640 687 L 480 687" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round" marker-end="url(#arrow)" />

  <!-- 11. PW --> DM -->
  <path d="M 720 585 L 720 760 L 260 760 L 260 785" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round" marker-end="url(#arrow)" />

  <!-- 12. PW --> PR -->
  <path d="M 800 585 L 800 785" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

  <!-- 13. PW --> SM -->
  <path d="M 880 585 L 880 760 L 1340 760 L 1340 785" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round" marker-end="url(#arrow)" />

</svg>"""

with open("kubelet.svg", "w") as f:
    f.write(svg_content)

print("Generated kubelet.svg successfully.")
