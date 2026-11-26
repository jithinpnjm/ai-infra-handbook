svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1050" width="1600" height="1050" style="background-color: #f5f8f5;">
  <title>Access architecture</title>
  <desc>Visual diagram of HPC access architecture showing paths from user laptop to bastion host, Open OnDemand portal, data transfer nodes, login nodes, Slurm controller, compute nodes, and parallel file system.</desc>

  <defs>
    <!-- Arrowhead markers -->
    <marker id="arrow-green" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="10" markerHeight="10" orient="auto-start-reverse">
      <path d="M 1 2 L 10 6 L 1 10 Z" fill="#207448" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="10" markerHeight="10" orient="auto-start-reverse">
      <path d="M 1 2 L 10 6 L 1 10 Z" fill="#db8129" />
    </marker>

    <!-- Shadow filter for clean flat depth -->
    <filter id="card-shadow" x="-4%" y="-4%" width="108%" height="108%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#207448" flood-opacity="0.08"/>
    </filter>
  </defs>

  <!-- Title -->
  <text x="800" y="65" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Access architecture</text>

  <!-- ==================== ARROWS & CONNECTIONS (drawn beneath nodes) ==================== -->

  <!-- 1. U to B: SSH 22 -->
  <line x1="260" y1="515" x2="360" y2="515" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>
  <text x="310" y="490" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="24" font-weight="bold" fill="#303a36">SSH 22</text>

  <!-- 2. U to P: HTTPS 443 -->
  <path d="M 150 430 V 210 H 440" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>
  <text x="295" y="190" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="24" font-weight="bold" fill="#303a36">HTTPS 443</text>

  <!-- 3. U to D: bulk data -->
  <path d="M 150 600 V 710 H 320 V 790" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>
  <text x="235" y="692" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">bulk data</text>

  <!-- 4. B to L -->
  <line x1="600" y1="515" x2="690" y2="515" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- 5. P to L -->
  <line x1="785" y1="280" x2="785" y2="420" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- 6. L to S -->
  <line x1="920" y1="515" x2="1020" y2="515" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- 7. S to C -->
  <line x1="1250" y1="515" x2="1330" y2="515" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- 8. P to C: reverse proxy to interactive app (Single orange highlight, dashed) -->
  <path d="M 870 210 H 1445 V 420" fill="none" stroke="#db8129" stroke-width="4" stroke-dasharray="8 6" marker-end="url(#arrow-orange)"/>
  <text x="1157" y="190" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#db8129">reverse proxy to interactive app</text>

  <!-- 9. D --- ST: undirected line -->
  <line x1="590" y1="887" x2="710" y2="887" stroke="#207448" stroke-width="4"/>

  <!-- 10. L --- ST: undirected line -->
  <line x1="845" y1="600" x2="845" y2="800" stroke="#207448" stroke-width="4"/>

  <!-- 11. C --- ST: undirected line -->
  <path d="M 1445 600 V 887 H 1250" fill="none" stroke="#207448" stroke-width="4"/>

  <!-- ==================== NODES ==================== -->

  <!-- Node U: User laptop -->
  <g transform="translate(40, 430)" filter="url(#card-shadow)">
    <rect width="220" height="170" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- Laptop Icon -->
    <g transform="translate(82, 20)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="10" width="40" height="26" rx="3"/>
      <path d="M4 42h48l-4-6H12z"/>
      <line x1="24" y1="42" x2="32" y2="42"/>
    </g>
    <text x="110" y="112" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="110" dy="0">User</tspan>
      <tspan x="110" dy="36">laptop</tspan>
    </text>
  </g>

  <!-- Node P: Open OnDemand portal -->
  <g transform="translate(450, 130)" filter="url(#card-shadow)">
    <rect width="420" height="150" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- Portal / Web Window Icon -->
    <g transform="translate(182, 16)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="4"/>
      <line x1="6" y1="20" x2="50" y2="20"/>
      <circle cx="14" cy="14" r="1.5" fill="#207448"/>
      <circle cx="20" cy="14" r="1.5" fill="#207448"/>
      <circle cx="26" cy="14" r="1.5" fill="#207448"/>
      <rect x="14" y="27" width="28" height="13" rx="2" stroke-dasharray="3 3"/>
    </g>
    <text x="210" y="114" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">Open OnDemand portal</text>
  </g>

  <!-- Node B: Bastion / jump host -->
  <g transform="translate(370, 430)" filter="url(#card-shadow)">
    <rect width="230" height="170" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- Security Shield Icon -->
    <g transform="translate(87, 20)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M28 8 L46 15 V28 C46 40 37 47 28 50 C19 47 10 40 10 28 V15 Z"/>
      <circle cx="28" cy="26" r="4"/>
      <path d="M28 30 V36"/>
    </g>
    <text x="115" y="112" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="115" dy="0">Bastion /</tspan>
      <tspan x="115" dy="36">jump host</tspan>
    </text>
  </g>

  <!-- Node L: Login nodes -->
  <g transform="translate(690, 430)" filter="url(#card-shadow)">
    <rect width="230" height="170" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- Terminal / Console Icon -->
    <g transform="translate(87, 20)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="4"/>
      <path d="M14 24 L22 30 L14 36"/>
      <line x1="26" y1="36" x2="38" y2="36"/>
    </g>
    <text x="115" y="112" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="115" dy="0">Login</tspan>
      <tspan x="115" dy="36">nodes</tspan>
    </text>
  </g>

  <!-- Node S: Slurm controller -->
  <g transform="translate(1020, 430)" filter="url(#card-shadow)">
    <rect width="230" height="170" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- Scheduler / Gear Icon -->
    <g transform="translate(87, 20)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="8"/>
      <path d="M28 6v6m0 32v6m-22-22h6m32 0h6m-7.6-14.4l-4.2 4.2m-22.8 22.8l-4.2 4.2m0-31.2l4.2 4.2m22.8 22.8l4.2 4.2"/>
    </g>
    <text x="115" y="112" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="115" dy="0">Slurm</tspan>
      <tspan x="115" dy="36">controller</tspan>
    </text>
  </g>

  <!-- Node C: Compute nodes -->
  <g transform="translate(1330, 430)" filter="url(#card-shadow)">
    <rect width="230" height="170" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- CPU / Chip Icon -->
    <g transform="translate(87, 20)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="14" y="14" width="28" height="28" rx="3"/>
      <circle cx="28" cy="28" r="5"/>
      <line x1="20" y1="6" x2="20" y2="14"/>
      <line x1="28" y1="6" x2="28" y2="14"/>
      <line x1="36" y1="6" x2="36" y2="14"/>
      <line x1="20" y1="42" x2="20" y2="50"/>
      <line x1="28" y1="42" x2="28" y2="50"/>
      <line x1="36" y1="42" x2="36" y2="50"/>
      <line x1="6" y1="20" x2="14" y2="20"/>
      <line x1="6" y1="28" x2="14" y2="28"/>
      <line x1="6" y1="36" x2="14" y2="36"/>
      <line x1="42" y1="20" x2="50" y2="20"/>
      <line x1="42" y1="28" x2="50" y2="28"/>
      <line x1="42" y1="36" x2="50" y2="36"/>
    </g>
    <text x="115" y="112" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="115" dy="0">Compute</tspan>
      <tspan x="115" dy="36">nodes</tspan>
    </text>
  </g>

  <!-- Node D: Data transfer nodes: Globus, rsync, rclone -->
  <g transform="translate(150, 800)" filter="url(#card-shadow)">
    <rect width="440" height="175" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- Transfer Sync Icon -->
    <g transform="translate(192, 16)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M10 20 H44 M34 10 L44 20 L34 30"/>
      <path d="M46 36 H12 M22 26 L12 36 L22 46"/>
    </g>
    <text x="220" y="114" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">Data transfer nodes:</text>
    <text x="220" y="152" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="24" font-weight="bold" fill="#303a36">Globus, rsync, rclone</text>
  </g>

  <!-- Node ST: Parallel file system -->
  <g transform="translate(710, 800)" filter="url(#card-shadow)">
    <rect width="540" height="175" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- Storage / Disk Cylinder Icon -->
    <g transform="translate(242, 16)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="20" ry="6"/>
      <path d="M8 14 V42 C8 48 48 48 48 42 V14"/>
      <path d="M8 28 C8 34 48 34 48 28"/>
    </g>
    <text x="270" y="126" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">Parallel file system</text>
  </g>
</svg>'''

with open('output.svg', 'w') as f:
    f.write(svg_code)

print("Saved output.svg successfully!")
