svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>One Slurm NodeName line, field by field, and where each value comes from</title>
  <desc>Field-by-field breakdown of a Slurm NodeName line generated from Ansible inventory hostvars and gathered facts, including fallback defaults.</desc>
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- ==================== TITLE ==================== -->
  <text x="800" y="48" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">One Slurm NodeName line, field by field, and where each value comes from</text>

  <!-- ==================== HEADER LINES ==================== -->
  <!-- Header line 1: ClusterName -->
  <rect x="40" y="74" width="745" height="54" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g transform="translate(54, 83)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="4" width="34" height="26" rx="4"/>
    <line x1="8" y1="12" x2="16" y2="12"/>
    <line x1="8" y1="18" x2="22" y2="18"/>
    <circle cx="28" cy="15" r="2" fill="#207448"/>
  </g>
  <text x="106" y="109" font-family="monospace" font-size="24" fill="#303a36">ClusterName={{ slurm_cluster_name }}</text>

  <!-- Header line 2: SlurmctldHost -->
  <rect x="815" y="74" width="745" height="54" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g transform="translate(829, 83)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="2" width="34" height="14" rx="3"/>
    <rect x="2" y="18" width="34" height="14" rx="3"/>
    <circle cx="8" cy="9" r="1.5" fill="#207448"/>
    <circle cx="8" cy="25" r="1.5" fill="#207448"/>
  </g>
  <text x="881" y="109" font-family="monospace" font-size="24" fill="#303a36">SlurmctldHost={{ groups[slurm_controller][0] }}</text>

  <!-- ==================== TABLE COLUMN HEADERS ==================== -->
  <rect x="40" y="142" width="536" height="42" rx="6" fill="#207448"/>
  <text x="56" y="172" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Field in the line</text>

  <rect x="590" y="142" width="346" height="42" rx="6" fill="#207448"/>
  <text x="606" y="172" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Source</text>

  <rect x="950" y="142" width="610" height="42" rx="6" fill="#207448"/>
  <text x="966" y="172" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Fallback</text>

  <!-- ==================== ROW 1: NodeName ==================== -->
  <rect x="40" y="190" width="536" height="58" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="226" font-family="monospace" font-size="24" fill="#303a36">NodeName={{ h }}</text>

  <rect x="590" y="190" width="346" height="58" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="214" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="606" dy="0">the host name from </tspan><tspan x="606" dy="26">groups[gpu] | sort</tspan></text>

  <rect x="950" y="190" width="610" height="58" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="226" font-family="sans-serif" font-size="24" fill="#303a36">-</text>

  <!-- ==================== ROW 2: NodeAddr ==================== -->
  <rect x="40" y="252" width="536" height="44" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="282" font-family="monospace" font-size="24" fill="#303a36">NodeAddr={{ v.ansible_host }}</text>

  <rect x="590" y="252" width="346" height="44" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="282" font-family="sans-serif" font-size="24" fill="#303a36">hostvars</text>

  <rect x="950" y="252" width="610" height="44" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="282" font-family="sans-serif" font-size="24" fill="#303a36">-</text>

  <!-- ==================== ROW 3: CPUs ==================== -->
  <rect x="40" y="300" width="536" height="58" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="324" font-family="monospace" font-size="24" fill="#303a36"><tspan x="56" dy="0">CPUs={{ v.ansible_facts.</tspan><tspan x="56" dy="26">processor_vcpus }}</tspan></text>

  <rect x="590" y="300" width="346" height="58" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="336" font-family="sans-serif" font-size="24" fill="#303a36">gathered fact</text>

  <rect x="950" y="300" width="610" height="58" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="336" font-family="sans-serif" font-size="24" fill="#303a36">-</text>

  <!-- ==================== ROW 4: Boards=1 (constant) ==================== -->
  <rect x="40" y="362" width="1520" height="42" rx="6" fill="#f0f5f1" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="391" font-family="monospace" font-size="24" fill="#303a36">Boards=1</text>

  <!-- ==================== ROW 5: SocketsPerBoard ==================== -->
  <rect x="40" y="408" width="536" height="58" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="432" font-family="monospace" font-size="24" fill="#303a36"><tspan x="56" dy="0">SocketsPerBoard={{ </tspan><tspan x="56" dy="26">v.sockets | default(2) }}</tspan></text>

  <rect x="590" y="408" width="346" height="58" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="444" font-family="sans-serif" font-size="24" fill="#303a36">host variable</text>

  <rect x="950" y="408" width="610" height="58" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="444" font-family="sans-serif" font-size="24" fill="#303a36">2</text>

  <!-- ==================== ROW 6: CoresPerSocket ==================== -->
  <rect x="40" y="470" width="536" height="84" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="495" font-family="monospace" font-size="24" fill="#303a36"><tspan x="56" dy="0">CoresPerSocket={{ </tspan><tspan x="56" dy="26">v.cores_per_socket | </tspan><tspan x="56" dy="26">default(48) }}</tspan></text>

  <rect x="590" y="470" width="346" height="84" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="519" font-family="sans-serif" font-size="24" fill="#303a36">host variable</text>

  <rect x="950" y="470" width="610" height="84" rx="6" fill="#fcfdfc" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="519" font-family="sans-serif" font-size="24" fill="#303a36">48</text>

  <!-- ==================== ROW 7: ThreadsPerCore=1 (constant) ==================== -->
  <rect x="40" y="558" width="1520" height="42" rx="6" fill="#f0f5f1" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="587" font-family="monospace" font-size="24" fill="#303a36">ThreadsPerCore=1</text>

  <!-- ==================== ROW 8: RealMemory (KEY ORANGE HIGHLIGHT) ==================== -->
  <rect x="40" y="604" width="536" height="120" rx="8" fill="#fff9f4" stroke="#db8129" stroke-width="2.5"/>
  <text x="56" y="652" font-family="monospace" font-size="24" font-weight="bold" fill="#db8129"><tspan x="56" dy="0">RealMemory={{ (v.ansible_facts.</tspan><tspan x="56" dy="28">memtotal_mb * 0.95) | int }}</tspan></text>

  <rect x="590" y="604" width="346" height="120" rx="8" fill="#fff9f4" stroke="#db8129" stroke-width="1.5"/>
  <text x="606" y="669" font-family="sans-serif" font-size="24" fill="#303a36">gathered fact</text>

  <rect x="950" y="604" width="610" height="120" rx="8" fill="#fff9f4" stroke="#db8129" stroke-width="1.5"/>
  <text x="966" y="634" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="966" dy="0">leave memory unused: the operating </tspan><tspan x="966" dy="26">system and the Slurm daemon need </tspan><tspan x="966" dy="26">room too, so the scheduler never </tspan><tspan x="966" dy="26">promises every last byte to a job</tspan></text>

  <!-- ==================== ROW 9: Gres ==================== -->
  <rect x="40" y="728" width="536" height="84" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="753" font-family="monospace" font-size="24" fill="#303a36"><tspan x="56" dy="0">Gres=gpu:{{ v.gpu_model | </tspan><tspan x="56" dy="26">default(h100) }}:</tspan><tspan x="56" dy="26">{{ v.gpu_count | default(8) }}</tspan></text>

  <rect x="590" y="728" width="346" height="84" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="606" y="777" font-family="sans-serif" font-size="24" fill="#303a36">host variables</text>

  <rect x="950" y="728" width="610" height="84" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.2"/>
  <text x="966" y="777" font-family="sans-serif" font-size="24" fill="#303a36">h100 and 8</text>

  <!-- ==================== ROW 10: State=UNKNOWN (constant) ==================== -->
  <rect x="40" y="816" width="1520" height="42" rx="6" fill="#f0f5f1" stroke="#207448" stroke-width="1.2"/>
  <text x="56" y="845" font-family="monospace" font-size="24" fill="#303a36">State=UNKNOWN</text>

  <!-- ==================== FOOTER LINE PANEL ==================== -->
  <rect x="40" y="872" width="1520" height="106" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g transform="translate(56, 897)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="2" width="36" height="18" rx="3"/>
    <line x1="8" y1="20" x2="8" y2="28"/>
    <line x1="32" y1="20" x2="32" y2="28"/>
    <line x1="2" y1="28" x2="38" y2="28"/>
    <circle cx="20" cy="11" r="3" fill="#207448"/>
  </g>
  <text x="114" y="904" font-family="monospace" font-size="24" fill="#303a36"><tspan x="114" dy="0">PartitionName=gpu Nodes={{ groups[gpu] | sort | join(,) }} </tspan><tspan x="114" dy="28">Default=YES MaxTime=INFINITE State=UP</tspan></text>
  <text x="114" y="964" font-family="sans-serif" font-size="24" fill="#207448">a partition is Slurm&apos;s name for a pool of nodes that a user submits jobs to</text>

  <!-- ==================== TIP STRIP PANEL ==================== -->
  <rect x="40" y="990" width="1520" height="102" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <g transform="translate(56, 1013)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 8 20 A 12 12 0 1 1 28 20 C 26 24 24 26 24 30 L 12 30 C 12 26 10 24 8 20 Z"/>
    <line x1="14" y1="34" x2="22" y2="34"/>
    <line x1="16" y1="38" x2="20" y2="38"/>
  </g>
  <text x="114" y="1022" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="114" dy="0">set v = hostvars[h] gives the long path a short name; </tspan><tspan x="114" dy="28">for large clusters compress the node list into Slurm hostlist syntax </tspan><tspan x="114" dy="28">such as gpu[001-032] with a custom filter or a precomputed variable</tspan></text>

  <!-- ==================== BOTTOM BAR ==================== -->
  <rect x="40" y="1106" width="1520" height="50" rx="8" fill="#207448"/>
  <text x="800" y="1139" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Defaults fill the gaps where data is missing</text>
</svg>'''

with open("candidate_test_node_line.svg", "w") as f:
    f.write(svg_content)

print("Saved candidate_test_node_line.svg successfully")
