import xml.etree.ElementTree as ET
import re

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1120" width="1600" height="1120">
  <title>Where roles, import_role and include_role run in a play</title>
  <desc>Visual infographic explaining the execution lifecycle and placement of roles, import_role, and include_role across play sections.</desc>

  <defs>
    <marker id="arrow" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="14" markerHeight="14" orient="auto-start-reverse">
      <path d="M 1 2 L 10 6 L 1 10 z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="1600" height="1120" fill="#f5f8f5" />

  <!-- Title: 48px bold, wrapped onto two lines so it fits conservatively inside 1600px with generous margins -->
  <text x="800" y="72" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Where roles, import_role and include_role</tspan>
    <tspan x="800" dy="58">run in a play</tspan>
  </text>

  <!-- Timeline Bar with Markers above the sequence -->
  <line x1="120" y1="205" x2="1480" y2="205" stroke="#a3c9b3" stroke-width="4" stroke-linecap="round" />
  
  <!-- Marker 3 (milestone indicator) -->
  <circle cx="170" cy="205" r="9" fill="#207448" stroke="#ffffff" stroke-width="2.5" />

  <!-- Marker 1: Parse time for import_role -->
  <circle cx="575" cy="205" r="9" fill="#207448" stroke="#ffffff" stroke-width="2.5" />
  <line x1="575" y1="214" x2="575" y2="248" stroke="#207448" stroke-width="2" stroke-dasharray="4,4" />
  <text x="575" y="185" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">Parse time for import_role</text>

  <!-- Marker 2: Runtime for include_role -->
  <circle cx="1025" cy="205" r="9" fill="#207448" stroke="#ffffff" stroke-width="2.5" />
  <line x1="1025" y1="214" x2="1025" y2="248" stroke="#207448" stroke-width="2" stroke-dasharray="4,4" />
  <text x="1025" y="185" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">Runtime for include_role</text>

  <!-- ================= SECTION 1: pre_tasks ================= -->
  <g id="section-pre-tasks">
    <rect x="50" y="250" width="240" height="640" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    
    <!-- Step number circle 1 -->
    <circle cx="170" cy="300" r="24" fill="#207448" />
    <text x="170" y="300" text-anchor="middle" dominant-baseline="central" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>

    <!-- Outline icon: checklist (56px) -->
    <g transform="translate(142, 345)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="48" rx="6" />
      <path d="M18 6 V2 a2 2 0 0 1 2 -2 h16 a2 2 0 0 1 2 2 V6" />
      <path d="M15 28 L23 36 L41 18" />
      <line x1="16" y1="44" x2="40" y2="44" />
    </g>

    <!-- Title: pre_tasks -->
    <text x="170" y="445" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#303a36">pre_tasks</text>
  </g>

  <!-- Orthogonal Arrow 1: pre_tasks -> roles and tasks -->
  <line x1="290" y1="570" x2="340" y2="570" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />

  <!-- ================= SECTION 2: roles and tasks ================= -->
  <g id="section-roles-and-tasks">
    <rect x="340" y="250" width="920" height="640" rx="16" fill="#f2f7f3" stroke="#207448" stroke-width="3" />

    <!-- Step number circle 2 -->
    <circle cx="385" cy="292" r="24" fill="#207448" />
    <text x="385" y="292" text-anchor="middle" dominant-baseline="central" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>

    <!-- Header Icon: layers (56px) -->
    <g transform="translate(425, 268)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="44" height="10" rx="3" />
      <rect x="2" y="19" width="44" height="10" rx="3" />
      <rect x="2" y="34" width="44" height="10" rx="3" />
    </g>

    <!-- Title: roles and tasks -->
    <text x="490" y="302" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="#303a36">roles and tasks</text>

    <!-- SUB-ROW 1: roles: list (classic, runs before tasks) -->
    <g id="subrow-roles-list">
      <rect x="365" y="335" width="870" height="110" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      
      <!-- Outline icon: role cube (48px) -->
      <g transform="translate(390, 366)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linejoin="round">
        <path d="M24 4 L44 14 V34 L24 44 L4 34 V14 Z" />
        <path d="M24 4 V44 M4 14 L24 24 L44 14" />
      </g>

      <!-- Label: roles: -->
      <text x="460" y="401" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">roles:</text>

      <!-- Label: classic, runs before tasks -->
      <text x="600" y="401" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">classic, runs before tasks</text>
    </g>

    <!-- SUB-ROW 2: task flow -->
    <g id="subrow-task-flow">
      <rect x="365" y="465" width="870" height="405" rx="12" fill="#ffffff" stroke="#a3c9b3" stroke-width="2" />

      <!-- Card A: ansible.builtin.import_role -->
      <g id="card-import-role">
        <rect x="385" y="485" width="380" height="365" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="2.5" />
        
        <!-- Outline icon: static padlock (48px) -->
        <g transform="translate(410, 505)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="8" y="18" width="32" height="26" rx="4" />
          <path d="M14 18 V10 a10 10 0 0 1 20 0 V18" />
          <circle cx="24" cy="30" r="3" fill="#207448" stroke="none" />
        </g>

        <!-- Label: ansible.builtin.import_role -->
        <text x="410" y="585" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">
          <tspan x="410" dy="0">ansible.builtin.</tspan>
          <tspan x="410" dy="32">import_role</tspan>
        </text>

        <!-- Label: static, fixed at parse time -->
        <text x="410" y="685" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
          <tspan x="410" dy="0">static,</tspan>
          <tspan x="410" dy="32">fixed at parse time</tspan>
        </text>
      </g>

      <!-- Task flow arrow between import_role and include_role -->
      <line x1="765" y1="667" x2="815" y2="667" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />

      <!-- Card B: ansible.builtin.include_role (Orange highlight) -->
      <g id="card-include-role">
        <rect x="815" y="485" width="400" height="365" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="3.5" />

        <!-- Outline icon: loop icon (48px) in orange -->
        <g transform="translate(840, 505)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M38 16 A 18 18 0 1 1 12 34" />
          <polyline points="38,8 42,18 32,20" />
        </g>

        <!-- Label: ansible.builtin.include_role -->
        <text x="840" y="585" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">
          <tspan x="840" dy="0">ansible.builtin.</tspan>
          <tspan x="840" dy="32">include_role</tspan>
        </text>

        <!-- Label: dynamic, decided at runtime -->
        <text x="840" y="675" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
          <tspan x="840" dy="0">dynamic,</tspan>
          <tspan x="840" dy="30">decided at runtime</tspan>
        </text>

        <!-- Note: supports loop and tasks_from -->
        <text x="840" y="755" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
          <tspan x="840" dy="0">supports loop and</tspan>
          <tspan x="840" dy="30" font-family="monospace">tasks_from</tspan>
        </text>
      </g>
    </g>
  </g>

  <!-- Orthogonal Arrow 2: roles and tasks -> post_tasks -->
  <line x1="1260" y1="570" x2="1310" y2="570" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />

  <!-- ================= SECTION 3: post_tasks ================= -->
  <g id="section-post-tasks">
    <rect x="1310" y="250" width="240" height="640" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />

    <!-- Step number circle 3 -->
    <circle cx="1430" cy="300" r="24" fill="#207448" />
    <text x="1430" y="300" text-anchor="middle" dominant-baseline="central" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>

    <!-- Outline icon: flag (56px) -->
    <g transform="translate(1402, 345)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="12" y1="4" x2="12" y2="52" />
      <path d="M12 8 C24 0 32 16 44 8 V32 C32 40 24 24 12 32 Z" />
    </g>

    <!-- Title: post_tasks -->
    <text x="1430" y="445" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#303a36">post_tasks</text>
  </g>

  <!-- ================= NOTE-CHIP: Handlers flush between sections ================= -->
  <g id="note-handlers">
    <rect x="520" y="905" width="560" height="56" rx="28" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <text x="800" y="941" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">Handlers flush between sections.</text>
  </g>

  <!-- ================= TAKEAWAY BAR ================= -->
  <g id="takeaway-bar">
    <rect x="50" y="990" width="1500" height="85" rx="16" fill="#207448" />
    <text x="800" y="1043" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#ffffff">
      <tspan>Use </tspan>
      <tspan font-family="monospace">roles:</tspan>
      <tspan> for simple cases, and the other two for mid-task roles.</tspan>
    </text>
  </g>
</svg>'''

tree = ET.fromstring(svg_code)
print("SVG parsed successfully!")
