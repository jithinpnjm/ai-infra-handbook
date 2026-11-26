import re
import xml.etree.ElementTree as ET

def build_svg():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Which ansible.cfg wins: the search order and the precedence of settings</title>
  <desc>Visual infographic explaining the search order of ansible.cfg files (first found wins, never merged) and the precedence of configuration settings from flags down to defaults.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">
    <tspan x="800" y="56">Which ansible.cfg wins: </tspan>
    <tspan x="800" y="108">the search order and the precedence of settings</tspan>
  </text>

  <!-- ==================== LADDER 1: Which file is read (x=40..780, y=145..650) ==================== -->
  <g id="ladder-1">
    <rect x="40" y="145" width="740" height="505" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Header bar -->
    <path d="M 40 161 A 16 16 0 0 1 56 145 L 764 145 A 16 16 0 0 1 780 161 L 780 225 L 40 225 Z" fill="#e8f1ea" />
    <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="60" y="180">Which file is read </tspan>
      <tspan x="60" y="214">(first found wins, never merged)</tspan>
    </text>

    <!-- Step 1 Card: ANSIBLE_CONFIG -->
    <rect x="60" y="235" width="700" height="75" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="94" cy="272" r="24" fill="#207448" />
    <text x="94" y="281" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <!-- Outline icon: Terminal env variable prompt (50px) -->
    <g transform="translate(130, 248)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="4" width="48" height="42" rx="6" />
      <path d="M 12 18 L 22 25 L 12 32" />
      <line x1="26" y1="32" x2="39" y2="32" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="264" font-family="monospace" font-weight="bold">ANSIBLE_CONFIG </tspan>
      <tspan x="202" y="294" font-family="sans-serif">environment variable</tspan>
    </text>

    <!-- Step 2 Card: ./ansible.cfg (with world-writable warning) -->
    <rect x="60" y="320" width="700" height="180" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="94" cy="358" r="24" fill="#207448" />
    <text x="94" y="367" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <!-- Outline icon: Folder with security lock (50px) -->
    <g transform="translate(130, 334)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 4 14 L 18 14 L 24 20 L 46 20 A 4 4 0 0 1 50 24 L 50 44 A 4 4 0 0 1 46 48 L 4 48 A 4 4 0 0 1 0 44 L 0 18 A 4 4 0 0 1 4 14 Z" />
      <rect x="20" y="28" width="16" height="14" rx="2" fill="#e8f1ea" />
      <path d="M 24 28 V 22 C 24 19 32 19 32 22 V 28" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="350" font-family="monospace" font-weight="bold">./ansible.cfg </tspan>
      <tspan x="202" y="378" font-family="sans-serif">in the current directory </tspan>
      <tspan x="76" y="414">(honoured only if it is not world-writable: </tspan>
      <tspan x="76" y="444">a folder any user can change </tspan>
      <tspan x="76" y="474">cannot be trusted)</tspan>
    </text>

    <!-- Step 3 Card: ~/.ansible.cfg -->
    <rect x="60" y="510" width="700" height="58" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="94" cy="539" r="24" fill="#207448" />
    <text x="94" y="548" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <!-- Outline icon: Home directory user house (48px) -->
    <g transform="translate(130, 515)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 24 L 26 6 L 46 24 V 44 A 2 2 0 0 1 44 46 H 8 A 2 2 0 0 1 6 44 Z" />
      <path d="M 20 46 V 28 H 32 V 46" />
    </g>
    <text x="202" y="547" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">~/.ansible.cfg</text>

    <!-- Step 4 Card: /etc/ansible/ansible.cfg -->
    <rect x="60" y="578" width="700" height="58" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="94" cy="607" r="24" fill="#207448" />
    <text x="94" y="616" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <!-- Outline icon: System server / storage cylinder (48px) -->
    <g transform="translate(130, 583)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="40" height="36" rx="4" />
      <line x1="6" y1="18" x2="46" y2="18" />
      <line x1="6" y1="30" x2="46" y2="30" />
      <circle cx="36" cy="12" r="2" fill="#207448" />
      <circle cx="36" cy="24" r="2" fill="#207448" />
      <circle cx="36" cy="36" r="2" fill="#207448" />
    </g>
    <text x="202" y="615" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">/etc/ansible/ansible.cfg</text>
  </g>

  <!-- ==================== LADDER 2: Which value wins (x=820..1560, y=145..650) ==================== -->
  <g id="ladder-2">
    <rect x="820" y="145" width="740" height="505" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Header bar -->
    <path d="M 820 161 A 16 16 0 0 1 836 145 L 1544 145 A 16 16 0 0 1 1560 161 L 1560 225 L 820 225 Z" fill="#e8f1ea" />
    <text x="840" y="197" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Which value wins</text>

    <!-- Step 1 Card: command-line flags -->
    <rect x="840" y="235" width="700" height="88" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="874" cy="279" r="24" fill="#207448" />
    <text x="874" y="288" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <!-- Outline icon: Flag on post (50px) -->
    <g transform="translate(910, 254)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="12" y1="6" x2="12" y2="44" />
      <polygon points="12,8 42,16 12,25" fill="#e8f1ea" />
      <line x1="6" y1="44" x2="18" y2="44" />
    </g>
    <text x="984" y="287" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">command-line flags</text>

    <!-- Step 2 Card: environment variables -->
    <rect x="840" y="339" width="700" height="88" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="874" cy="383" r="24" fill="#207448" />
    <text x="874" y="392" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <!-- Outline icon: Shell braces / variable symbol (50px) -->
    <g transform="translate(910, 358)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 16 8 C 8 8 8 22 2 25 C 8 28 8 42 16 42" />
      <path d="M 36 8 C 44 8 44 22 50 25 C 44 28 44 42 36 42" />
      <line x1="21" y1="25" x2="31" y2="25" />
    </g>
    <text x="984" y="391" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">environment variables</text>

    <!-- Step 3 Card: config file -->
    <rect x="840" y="443" width="700" height="88" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="874" cy="487" r="24" fill="#207448" />
    <text x="874" y="496" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <!-- Outline icon: Config file document with gear (50px) -->
    <g transform="translate(910, 462)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 6 L 32 6 L 44 18 L 44 44 A 2 2 0 0 1 42 46 L 12 46 A 2 2 0 0 1 10 44 Z" />
      <polyline points="32,6 32,18 44,18" />
      <line x1="18" y1="28" x2="36" y2="28" />
      <line x1="18" y1="36" x2="30" y2="36" />
    </g>
    <text x="984" y="495" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">config file</text>

    <!-- Step 4 Card: defaults -->
    <rect x="840" y="547" width="700" height="88" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="874" cy="591" r="24" fill="#207448" />
    <text x="874" y="600" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <!-- Outline icon: Defaults / factory foundation blocks (50px) -->
    <g transform="translate(910, 566)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="20" width="40" height="24" rx="3" />
      <line x1="6" y1="32" x2="46" y2="32" />
      <line x1="26" y1="32" x2="26" y2="44" />
      <path d="M 18 20 V 8 L 34 8 V 20" />
    </g>
    <text x="984" y="599" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">defaults</text>
  </g>

  <!-- ==================== COMMANDS STRIP (x=40..1560, y=690..786, h=96) ==================== -->
  <g id="commands-strip">
    <rect x="40" y="690" width="1520" height="96" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Outline icon: Terminal prompt window (50px) -->
    <g transform="translate(60, 713)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="4" width="48" height="42" rx="6" />
      <path d="M 12 16 L 22 24 L 12 32" />
      <line x1="26" y1="32" x2="39" y2="32" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="136" y="719"><tspan font-family="monospace" font-weight="bold">ansible-config dump --only-changed</tspan> shows only what you changed; </tspan>
      <tspan x="136" y="749"><tspan font-family="monospace" font-weight="bold">ansible-config list</tspan> shows every setting with its default; </tspan>
      <tspan x="136" y="779"><tspan font-family="monospace" font-weight="bold">ansible --version</tspan> shows the config file in use</tspan>
    </text>
  </g>

  <!-- ==================== SURPRISE STORY (orange) (x=40..1560, y=826..902, h=76) ==================== -->
  <g id="surprise-story">
    <rect x="40" y="826" width="1520" height="76" rx="12" fill="#fffaf5" stroke="#db8129" stroke-width="2.5" />
    <!-- Outline icon in orange: Alert / warning triangle (50px) -->
    <g transform="translate(60, 839)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="26,4 48,44 4,44" />
      <line x1="26" y1="18" x2="26" y2="30" />
      <circle cx="26" cy="38" r="2" fill="#db8129" stroke="none" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="136" y="855">an engineer runs Ansible from a folder they did not expect, </tspan>
      <tspan x="136" y="887">and the tool quietly picks up a different config file</tspan>
    </text>
  </g>

  <!-- ==================== RULES STRIP (x=40..1560, y=942..1038, h=96) ==================== -->
  <g id="rules-strip">
    <rect x="40" y="942" width="1520" height="96" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Outline icon: Shield / best practice rules (50px) -->
    <g transform="translate(60, 965)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 26 4 L 46 12 V 26 C 46 38 26 46 26 46 C 26 46 6 38 6 26 V 12 Z" />
      <polyline points="18,26 24,32 36,18" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="136" y="971">keep a project-level <tspan font-family="monospace" font-weight="bold">ansible.cfg</tspan> in the repo root; </tspan>
      <tspan x="136" y="1001">keep secrets and personal paths out of it because it is committed; </tspan>
      <tspan x="136" y="1031">editing <tspan font-family="monospace" font-weight="bold">/etc/ansible</tspan> changes behaviour between laptops and CI and is invisible to Git</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR (x=40..1560, y=1078..1130, h=52) ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1078" width="1520" height="52" rx="10" fill="#207448" />
    <text x="800" y="1112" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Knowing the search order turns a surprise into a quick check</text>
  </g>
</svg>'''
    return svg

svg_content = build_svg()
with open("candidate_cfg_order.svg", "w") as f:
    f.write(svg_content)

print("Saved updated candidate_cfg_order.svg")
