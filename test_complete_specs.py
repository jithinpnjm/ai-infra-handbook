import xml.etree.ElementTree as ET
import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1140" width="1600" height="1140">
  <title>The Ansible CI workflow: lint gates the Molecule matrix</title>
  <desc>Visual infographic explaining the Ansible CI workflow where lint gates the Molecule test matrix and hardware GPU tests run conditionally.</desc>

  <defs>
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerWidth="18" markerHeight="18" orient="auto">
      <polygon points="0,3 16,9 0,15" fill="#db8129"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1140" fill="#f5f8f5"/>

  <!-- Title -->
  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">The Ansible CI workflow: </tspan>
    <tspan x="800" dy="60">lint gates the Molecule matrix</tspan>
  </text>

  <!-- Large Container: ansible-ci workflow -->
  <rect x="40" y="165" width="1520" height="920" rx="16" fill="#ffffff" stroke="#207448" stroke-width="3"/>
  <rect x="40" y="165" width="1520" height="65" rx="16" fill="#e8f1ea"/>
  <rect x="40" y="210" width="1520" height="20" fill="#e8f1ea"/>
  <line x1="40" y1="230" x2="1560" y2="230" stroke="#207448" stroke-width="2"/>
  <text x="800" y="210" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#207448">ansible-ci workflow</text>

  <!-- ==================== JOB BOX 1: lint ==================== -->
  <g id="job-lint">
    <rect x="70" y="265" width="380" height="520" rx="12" fill="#f5f8f5" stroke="#207448" stroke-width="2.5"/>

    <!-- Shield Icon -->
    <g transform="translate(232, 285)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 4 L 50 14 V 30 C 50 44 28 52 28 52 C 28 52 6 44 6 30 V 14 Z"/>
      <polyline points="20 28 26 34 38 20"/>
    </g>

    <text x="260" y="380" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">lint</text>

    <!-- Sub-card: runs-on -->
    <rect x="90" y="415" width="340" height="120" rx="8" fill="#e8f1ea" stroke="#cfded2" stroke-width="1.5"/>
    <text x="260" y="465" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="260" dy="0">runs-on </tspan>
      <tspan x="260" dy="34">ubuntu-latest</tspan>
    </text>

    <!-- Sub-card: step -->
    <rect x="90" y="565" width="340" height="185" rx="8" fill="#e8f1ea" stroke="#cfded2" stroke-width="1.5"/>
    <text x="260" y="640" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="260" dy="0">yamllint . &amp;&amp; </tspan>
      <tspan x="260" dy="38">ansible-lint</tspan>
    </text>
  </g>

  <!-- ==================== ARROW: lint -> molecule ==================== -->
  <g id="arrow-lint-molecule">
    <line x1="450" y1="525" x2="610" y2="525" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)"/>
    <text x="530" y="460" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#db8129">
      <tspan x="530" dy="0">needs: </tspan>
      <tspan x="530" dy="34">lint</tspan>
    </text>
  </g>

  <!-- ==================== JOB BOX 2: molecule ==================== -->
  <g id="job-molecule">
    <rect x="610" y="265" width="380" height="520" rx="12" fill="#f5f8f5" stroke="#207448" stroke-width="2.5"/>

    <!-- Gear Icon -->
    <g transform="translate(772, 285)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="12"/>
      <path d="M 28 6 L 28 12 M 28 44 L 28 50 M 6 28 L 12 28 M 44 28 L 50 28 M 12.5 12.5 L 16.7 16.7 M 39.3 39.3 L 43.5 43.5 M 12.5 43.5 L 16.7 39.3 M 39.3 16.7 L 43.5 12.5"/>
    </g>

    <text x="800" y="380" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">molecule</text>

    <!-- Sub-card: matrix role -->
    <rect x="630" y="415" width="340" height="150" rx="8" fill="#e8f1ea" stroke="#cfded2" stroke-width="1.5"/>
    <text x="800" y="448" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="800" dy="0">role: </tspan>
      <tspan x="800" dy="30">kernel_tuning, </tspan>
      <tspan x="800" dy="30">chrony_client, </tspan>
      <tspan x="800" dy="30">dcgm_exporter</tspan>
    </text>

    <!-- Sub-card: matrix distro -->
    <rect x="630" y="580" width="340" height="110" rx="8" fill="#e8f1ea" stroke="#cfded2" stroke-width="1.5"/>
    <text x="800" y="614" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="800" dy="0">distro: </tspan>
      <tspan x="800" dy="30">ubuntu2204, </tspan>
      <tspan x="800" dy="30">rockylinux9</tspan>
    </text>

    <!-- Sub-card: step -->
    <rect x="630" y="705" width="340" height="65" rx="8" fill="#e8f1ea" stroke="#cfded2" stroke-width="1.5"/>
    <text x="800" y="746" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">molecule test</text>
  </g>

  <!-- Note under molecule box -->
  <g id="note-molecule">
    <rect x="610" y="825" width="380" height="110" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="800" y="872" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="800" dy="0">a broken file never </tspan>
      <tspan x="800" dy="34">starts a container</tspan>
    </text>
  </g>

  <!-- ==================== JOB BOX 3: gpu-hw ==================== -->
  <g id="job-gpu-hw">
    <rect x="1150" y="265" width="380" height="520" rx="12" fill="#f5f8f5" stroke="#207448" stroke-width="2.5"/>

    <!-- Chip Icon -->
    <g transform="translate(1312, 285)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="12" y="12" width="32" height="32" rx="4"/>
      <rect x="20" y="20" width="16" height="16" rx="2" fill="#e8f1ea"/>
      <line x1="20" y1="4" x2="20" y2="12"/>
      <line x1="28" y1="4" x2="28" y2="12"/>
      <line x1="36" y1="4" x2="36" y2="12"/>
      <line x1="20" y1="44" x2="20" y2="52"/>
      <line x1="28" y1="44" x2="28" y2="52"/>
      <line x1="36" y1="44" x2="36" y2="52"/>
      <line x1="4" y1="20" x2="12" y2="20"/>
      <line x1="4" y1="28" x2="12" y2="28"/>
      <line x1="4" y1="36" x2="12" y2="36"/>
      <line x1="44" y1="20" x2="52" y2="20"/>
      <line x1="44" y1="28" x2="52" y2="28"/>
      <line x1="44" y1="36" x2="52" y2="36"/>
    </g>

    <text x="1340" y="380" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">gpu-hw</text>

    <!-- Sub-card: runs-on -->
    <rect x="1170" y="415" width="340" height="120" rx="8" fill="#e8f1ea" stroke="#cfded2" stroke-width="1.5"/>
    <text x="1340" y="465" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="1340" dy="0">runs-on </tspan>
      <tspan x="1340" dy="34">self-hosted, gpu</tspan>
    </text>

    <!-- Sub-card: step -->
    <rect x="1170" y="565" width="340" height="185" rx="8" fill="#e8f1ea" stroke="#cfded2" stroke-width="1.5"/>
    <text x="1340" y="640" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="1340" dy="0">molecule test </tspan>
      <tspan x="1340" dy="38">-s gpu_hw</tspan>
    </text>
  </g>

  <!-- Note under gpu-hw box -->
  <g id="note-gpu-hw">
    <rect x="1150" y="825" width="380" height="225" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="1340" y="865" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1340" dy="0">runs on schedule </tspan>
      <tspan x="1340" dy="34">(nightly cron </tspan>
      <tspan x="1340" dy="34">0 4 * * *) or </tspan>
      <tspan x="1340" dy="34">when a pull request </tspan>
      <tspan x="1340" dy="34">has the test-gpu label</tspan>
    </text>
  </g>
</svg>"""

with open("output.svg", "w") as f:
    f.write(svg_content.strip())
print("Saved output.svg")
