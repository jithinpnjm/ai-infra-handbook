import xml.etree.ElementTree as ET
import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>One Slurm NodeName line, field by field, and where each value comes from</title>
  <desc>Field-by-field breakdown of a Slurm NodeName line generated from Ansible inventory hostvars and gathered facts, including fallback defaults.</desc>
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- ==================== TITLE ==================== -->
  <text x="800" y="48" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">One Slurm NodeName line, field by field, </tspan>
    <tspan x="800" dy="52">and where each value comes from</tspan>
  </text>

  <!-- ==================== HEADER LINES CONTAINER ==================== -->
  <rect x="40" y="116" width="1520" height="52" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g transform="translate(54, 122)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="4" width="34" height="28" rx="4"/>
    <line x1="8" y1="13" x2="18" y2="13"/>
    <line x1="8" y1="21" x2="26" y2="21"/>
    <circle cx="28" cy="13" r="2" fill="#207448"/>
  </g>
  <text x="110" y="150" font-family="monospace" font-size="24" fill="#303a36">ClusterName={{ slurm_cluster_name }}</text>
  <text x="790" y="150" font-family="monospace" font-size="24" fill="#303a36">SlurmctldHost={{ groups[slurm_controller][0] }}</text>

  <!-- ==================== TABLE COLUMN HEADERS ==================== -->
  <rect x="40" y="180" width="536" height="42" rx="6" fill="#207448"/>
  <text x="56" y="210" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Field in the line</text>

  <rect x="590" y="180" width="346" height="42" rx="6" fill="#207448"/>
  <text x="606" y="210" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Source</text>

  <rect x="950" y="180" width="610" height="42" rx="6" fill="#207448"/>
  <text x="966" y="210" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Fallback</text>

  <!-- ==================== ROW 1: NodeName ==================== -->
  <rect x="40" y="228" width="536" height="56" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="263" font-family="monospace" font-size="24" fill="#303a36">NodeName={{ h }}</text>

  <rect x="590" y="228" width="346" height="56" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="251" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="606" dy="0">the host name from </tspan><tspan x="606" dy="26">groups[gpu] | sort</tspan></text>

  <rect x="950" y="228" width="610" height="56" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="263" font-family="sans-serif" font-size="24" fill="#303a36">-</text>

  <!-- ==================== ROW 2: NodeAddr ==================== -->
  <rect x="40" y="288" width="536" height="42" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="317" font-family="monospace" font-size="24" fill="#303a36">NodeAddr={{ v.ansible_host }}</text>

  <rect x="590" y="288" width="346" height="42" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="317" font-family="sans-serif" font-size="24" fill="#303a36">hostvars</text>

  <rect x="950" y="288" width="610" height="42" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="317" font-family="sans-serif" font-size="24" fill="#303a36">-</text>

  <!-- ==================== ROW 3: CPUs ==================== -->
  <rect x="40" y="334" width="536" height="56" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="357" font-family="monospace" font-size="24" fill="#303a36"><tspan x="56" dy="0">CPUs={{ v.ansible_facts.</tspan><tspan x="56" dy="26">processor_vcpus }}</tspan></text>

  <rect x="590" y="334" width="346" height="56" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="369" font-family="sans-serif" font-size="24" fill="#303a36">gathered fact</text>

  <rect x="950" y="334" width="610" height="56" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="369" font-family="sans-serif" font-size="24" fill="#303a36">-</text>

  <!-- ==================== ROW 4: Boards=1 (constant) ==================== -->
  <rect x="40" y="394" width="1520" height="40" rx="6" fill="#f0f5f1" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="422" font-family="monospace" font-size="24" fill="#303a36">Boards=1</text>

  <!-- ==================== ROW 5: SocketsPerBoard ==================== -->
  <rect x="40" y="438" width="536" height="56" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="461" font-family="monospace" font-size="24" fill="#303a36"><tspan x="56" dy="0">SocketsPerBoard={{ </tspan><tspan x="56" dy="26">v.sockets | default(2) }}</tspan></text>

  <rect x="590" y="438" width="346" height="56" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="473" font-family="sans-serif" font-size="24" fill="#303a36">host variable</text>

  <rect x="950" y="438" width="610" height="56" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="473" font-family="sans-serif" font-size="24" fill="#303a36">2</text>

  <!-- ==================== ROW 6: CoresPerSocket ==================== -->
  <rect x="40" y="498" width="536" height="80" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="522" font-family="monospace" font-size="24" fill="#303a36"><tspan x="56" dy="0">CoresPerSocket={{ </tspan><tspan x="56" dy="25">v.cores_per_socket | </tspan><tspan x="56" dy="25">default(48) }}</tspan></text>

  <rect x="590" y="498" width="346" height="80" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="545" font-family="sans-serif" font-size="24" fill="#303a36">host variable</text>

  <rect x="950" y="498" width="610" height="80" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="545" font-family="sans-serif" font-size="24" fill="#303a36">48</text>

  <!-- ==================== ROW 7: ThreadsPerCore=1 (constant) ==================== -->
  <rect x="40" y="582" width="1520" height="40" rx="6" fill="#f0f5f1" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="610" font-family="monospace" font-size="24" fill="#303a36">ThreadsPerCore=1</text>

  <!-- ==================== ROW 8: RealMemory (KEY ORANGE HIGHLIGHT) ==================== -->
  <rect x="40" y="626" width="536" height="114" rx="8" fill="#fff9f4" stroke="#db8129" stroke-width="2.5"/>
  <text x="56" y="672" font-family="monospace" font-size="24" font-weight="bold" fill="#db8129"><tspan x="56" dy="0">RealMemory={{ (v.ansible_facts.</tspan><tspan x="56" dy="28">memtotal_mb * 0.95) | int }}</tspan></text>

  <rect x="590" y="626" width="346" height="114" rx="8" fill="#fff9f4" stroke="#db8129" stroke-width="1.5"/>
  <text x="606" y="688" font-family="sans-serif" font-size="24" fill="#303a36">gathered fact</text>

  <rect x="950" y="626" width="610" height="114" rx="8" fill="#fff9f4" stroke="#db8129" stroke-width="1.5"/>
  <text x="966" y="652" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="966" dy="0">leave memory unused: the operating </tspan><tspan x="966" dy="25">system and the Slurm daemon need </tspan><tspan x="966" dy="25">room too, so the scheduler never </tspan><tspan x="966" dy="25">promises every last byte to a job</tspan></text>

  <!-- ==================== ROW 9: Gres ==================== -->
  <rect x="40" y="744" width="536" height="80" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="768" font-family="monospace" font-size="24" fill="#303a36"><tspan x="56" dy="0">Gres=gpu:{{ v.gpu_model | </tspan><tspan x="56" dy="25">default(h100) }}:</tspan><tspan x="56" dy="25">{{ v.gpu_count | default(8) }}</tspan></text>

  <rect x="590" y="744" width="346" height="80" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="791" font-family="sans-serif" font-size="24" fill="#303a36">host variables</text>

  <rect x="950" y="744" width="610" height="80" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="791" font-family="sans-serif" font-size="24" fill="#303a36">h100 and 8</text>

  <!-- ==================== ROW 10: State=UNKNOWN (constant) ==================== -->
  <rect x="40" y="828" width="1520" height="40" rx="6" fill="#f0f5f1" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="856" font-family="monospace" font-size="24" fill="#303a36">State=UNKNOWN</text>

  <!-- ==================== FOOTER LINE PANEL ==================== -->
  <rect x="40" y="876" width="1520" height="106" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g transform="translate(56, 901)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="2" width="36" height="18" rx="3"/>
    <line x1="8" y1="20" x2="8" y2="28"/>
    <line x1="32" y1="20" x2="32" y2="28"/>
    <line x1="2" y1="28" x2="38" y2="28"/>
    <circle cx="20" cy="11" r="3" fill="#207448"/>
  </g>
  <text x="114" y="908" font-family="monospace" font-size="24" fill="#303a36"><tspan x="114" dy="0">PartitionName=gpu Nodes={{ groups[gpu] | sort | join(,) }} </tspan><tspan x="114" dy="28">Default=YES MaxTime=INFINITE State=UP</tspan></text>
  <text x="114" y="968" font-family="sans-serif" font-size="24" fill="#207448">a partition is Slurm&apos;s name for a pool of nodes that a user submits jobs to</text>

  <!-- ==================== TIP STRIP PANEL ==================== -->
  <rect x="40" y="990" width="1520" height="102" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <g transform="translate(56, 1013)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 8 20 A 12 12 0 1 1 28 20 C 26 24 24 26 24 30 L 12 30 C 12 26 10 24 8 20 Z"/>
    <line x1="14" y1="34" x2="22" y2="34"/>
    <line x1="16" y1="38" x2="20" y2="38"/>
  </g>
  <text x="114" y="1022" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="114" dy="0">set v = hostvars[h] gives the long path a short name; </tspan><tspan x="114" dy="28">for large clusters compress the node list into Slurm hostlist syntax </tspan><tspan x="114" dy="28">such as gpu[001-032] with a custom filter or a precomputed variable</tspan></text>

  <!-- ==================== BOTTOM BAR ==================== -->
  <rect x="40" y="1102" width="1520" height="50" rx="8" fill="#207448"/>
  <text x="800" y="1135" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Defaults fill the gaps where data is missing</text>
</svg>'''

with open("candidate_test_node_line.svg", "w") as f:
    f.write(svg_content)

tree = ET.fromstring(svg_content)
print("XML parsing: PERFECT")
