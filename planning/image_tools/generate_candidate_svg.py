# Generator and strict validator for candidate_cfg_order.svg

svg_template = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Which ansible.cfg wins: the search order and the precedence of settings</title>
  <desc>Visual infographic explaining the search order of ansible.cfg files (first found wins, never merged) and the precedence of configuration settings from flags down to defaults.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title (48px bold, top margin >= 40px) -->
  <text font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">
    <tspan x="800" y="68">Which ansible.cfg wins: </tspan>
    <tspan x="800" y="112">the search order and the precedence of settings</tspan>
  </text>

  <!-- ==================== LADDER 1: Which file is read (x=40..780, y=158..615, w=740, h=457) ==================== -->
  <g id="ladder-1">
    <rect x="40" y="158" width="740" height="457" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    
    <!-- Ladder 1 Header text (30px bold) -->
    <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="64" y="194">Which file is read </tspan>
      <tspan x="64" y="226">(first found wins, never merged)</tspan>
    </text>

    <!-- Step 1 Card: ANSIBLE_CONFIG environment variable (x=56..764, y=255..315, w=708, h=60) -->
    <rect x="56" y="255" width="708" height="60" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="88" cy="285" r="24" fill="#207448" />
    <text x="88" y="294" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <!-- Outline icon: Terminal prompt window (38px) -->
    <g transform="translate(124, 266)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="40" height="34" rx="5" />
      <path d="M 9 13 L 17 19 L 9 25" />
      <line x1="21" y1="25" x2="31" y2="25" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="180" y="292" font-family="monospace" font-weight="bold">ANSIBLE_CONFIG </tspan>
      <tspan x="382" y="292" font-family="sans-serif">environment variable</tspan>
    </text>

    <!-- Step 2 Card: ./ansible.cfg (x=56..764, y=321..473, w=708, h=152) -->
    <rect x="56" y="321" width="708" height="152" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="88" cy="359" r="24" fill="#207448" />
    <text x="88" y="368" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <!-- Outline icon: Security folder with lock (38px) -->
    <g transform="translate(124, 340)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 3 11 L 15 11 L 20 16 L 37 16 A 3 3 0 0 1 40 19 L 40 35 A 3 3 0 0 1 37 38 L 3 38 A 3 3 0 0 1 0 35 L 0 14 A 3 3 0 0 1 3 11 Z" />
      <rect x="16" y="22" width="13" height="11" rx="2" fill="#e8f1ea" />
      <path d="M 19 22 V 17 C 19 15 26 15 26 17 V 22" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="180" y="353" font-family="monospace" font-weight="bold">./ansible.cfg </tspan>
      <tspan x="180" y="379" font-family="sans-serif">in the current directory </tspan>
      <tspan x="72" y="415">(honoured only if it is not world-writable: a </tspan>
      <tspan x="72" y="443">folder any user can change cannot be trusted)</tspan>
    </text>

    <!-- Step 3 Card: ~/.ansible.cfg (x=56..764, y=479..539, w=708, h=60) -->
    <rect x="56" y="479" width="708" height="60" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="88" cy="509" r="24" fill="#207448" />
    <text x="88" y="518" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <!-- Outline icon: Home house (38px) -->
    <g transform="translate(124, 490)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 5 20 L 21 5 L 37 20 V 36 A 2 2 0 0 1 35 38 H 7 A 2 2 0 0 1 5 36 Z" />
      <path d="M 16 38 V 23 H 26 V 38" />
    </g>
    <text x="180" y="516" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">~/.ansible.cfg</text>

    <!-- Step 4 Card: /etc/ansible/ansible.cfg (x=56..764, y=545..605, w=708, h=60) -->
    <rect x="56" y="545" width="708" height="60" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="88" cy="575" r="24" fill="#207448" />
    <text x="88" y="584" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <!-- Outline icon: System server rack cylinder (38px) -->
    <g transform="translate(124, 556)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="34" height="30" rx="3" />
      <line x1="4" y1="14" x2="38" y2="14" />
      <line x1="4" y1="24" x2="38" y2="24" />
      <circle cx="31" cy="9" r="1.5" fill="#207448" />
      <circle cx="31" cy="19" r="1.5" fill="#207448" />
      <circle cx="31" cy="29" r="1.5" fill="#207448" />
    </g>
    <text x="180" y="582" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">/etc/ansible/ansible.cfg</text>
  </g>

  <!-- ==================== LADDER 2: Which value wins (x=820..1560, y=158..615, w=740, h=457) ==================== -->
  <g id="ladder-2">
    <rect x="820" y="158" width="740" height="457" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    
    <!-- Ladder 2 Header text (30px bold) -->
    <text x="844" y="210" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Which value wins</text>

    <!-- Step 1 Card: command-line flags (x=836..1544, y=255..337, w=708, h=82) -->
    <rect x="836" y="255" width="708" height="82" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="868" cy="296" r="24" fill="#207448" />
    <text x="868" y="305" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <!-- Outline icon: Flag post (42px) -->
    <g transform="translate(904, 275)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="10" y1="4" x2="10" y2="38" />
      <polygon points="10,6 36,13 10,21" fill="#e8f1ea" />
      <line x1="5" y1="38" x2="15" y2="38" />
    </g>
    <text x="960" y="306" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">command-line flags</text>

    <!-- Step 2 Card: environment variables (x=836..1544, y=344..426, w=708, h=82) -->
    <rect x="836" y="344" width="708" height="82" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="868" cy="385" r="24" fill="#207448" />
    <text x="868" y="394" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <!-- Outline icon: Variable braces (42px) -->
    <g transform="translate(904, 364)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 13 6 C 6 6 6 19 2 21 C 6 23 6 36 13 36" />
      <path d="M 29 6 C 36 6 36 19 40 21 C 36 23 36 36 29 36" />
      <line x1="17" y1="21" x2="25" y2="21" />
    </g>
    <text x="960" y="395" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">environment variables</text>

    <!-- Step 3 Card: config file (x=836..1544, y=433..515, w=708, h=82) -->
    <rect x="836" y="433" width="708" height="82" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="868" cy="474" r="24" fill="#207448" />
    <text x="868" y="483" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <!-- Outline icon: Config document (42px) -->
    <g transform="translate(904, 453)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 8 5 L 26 5 L 36 15 L 36 37 A 2 2 0 0 1 34 39 L 10 39 A 2 2 0 0 1 8 37 Z" />
      <polyline points="26,5 26,15 36,15" />
      <line x1="15" y1="24" x2="29" y2="24" />
      <line x1="15" y1="31" x2="25" y2="31" />
    </g>
    <text x="960" y="484" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">config file</text>

    <!-- Step 4 Card: defaults (x=836..1544, y=522..604, w=708, h=82) -->
    <rect x="836" y="522" width="708" height="82" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="868" cy="563" r="24" fill="#207448" />
    <text x="868" y="572" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <!-- Outline icon: Foundation building block (42px) -->
    <g transform="translate(904, 542)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="5" y="16" width="34" height="20" rx="3" />
      <line x1="5" y1="26" x2="39" y2="26" />
      <line x1="22" y1="26" x2="22" y2="36" />
      <path d="M 15 16 V 6 L 29 6 V 16" />
    </g>
    <text x="960" y="573" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">defaults</text>
  </g>

  <!-- ==================== COMMANDS STRIP (x=40..1560, y=655..771, w=1520, h=116) ==================== -->
  <g id="commands-strip">
    <rect x="40" y="655" width="1520" height="116" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Outline icon: Terminal prompt window (44px) -->
    <g transform="translate(64, 691)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="3" width="44" height="38" rx="5" />
      <path d="M 11 15 L 20 22 L 11 29" />
      <line x1="24" y1="29" x2="36" y2="29" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="136" y="687"><tspan font-family="monospace" font-weight="bold">ansible-config dump --only-changed</tspan> shows only what you changed; </tspan>
      <tspan x="136" y="715"><tspan font-family="monospace" font-weight="bold">ansible-config list</tspan> shows every setting with its default; </tspan>
      <tspan x="136" y="743"><tspan font-family="monospace" font-weight="bold">ansible --version</tspan> shows the config file in use</tspan>
    </text>
  </g>

  <!-- ==================== SURPRISE STORY (orange) (x=40..1560, y=811..899, w=1520, h=88) ==================== -->
  <g id="surprise-story">
    <rect x="40" y="811" width="1520" height="88" rx="12" fill="#fffaf5" stroke="#db8129" stroke-width="2.5" />
    <!-- Outline icon in orange: Alert / warning triangle (44px) -->
    <g transform="translate(64, 833)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="24,3 45,40 3,40" />
      <line x1="24" y1="16" x2="24" y2="27" />
      <circle cx="24" cy="34" r="1.5" fill="#db8129" stroke="none" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="136" y="847">an engineer runs Ansible from a folder they did not expect, </tspan>
      <tspan x="136" y="875">and the tool quietly picks up a different config file</tspan>
    </text>
  </g>

  <!-- ==================== RULES STRIP (x=40..1560, y=939..1055, w=1520, h=116) ==================== -->
  <g id="rules-strip">
    <rect x="40" y="939" width="1520" height="116" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Outline icon: Shield best practice rules (44px) -->
    <g transform="translate(64, 975)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 24 3 L 43 11 V 24 C 43 35 24 43 24 43 C 24 43 5 35 5 24 V 11 Z" />
      <polyline points="16,24 22,30 33,17" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="136" y="971">keep a project-level <tspan font-family="monospace" font-weight="bold">ansible.cfg</tspan> in the repo root; </tspan>
      <tspan x="136" y="999">keep secrets and personal paths out of it because it is committed; </tspan>
      <tspan x="136" y="1027">editing <tspan font-family="monospace" font-weight="bold">/etc/ansible</tspan> changes behaviour between laptops and CI and is invisible to Git</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR (x=40..1560, y=1095..1155, w=1520, h=60) ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1095" width="1520" height="60" rx="10" fill="#207448" />
    <text x="800" y="1132" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Knowing the search order turns a surprise into a quick check</text>
  </g>
</svg>'''

with open("candidate_cfg_order.svg", "w") as f:
    f.write(svg_template)
print("Updated candidate_cfg_order.svg successfully!")
