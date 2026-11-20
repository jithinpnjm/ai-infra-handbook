import xml.etree.ElementTree as ET
import re, subprocess, pathlib

# Let's define the SVG template and test
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>Why become breaks SSH agent forwarding for git</title>
  <desc>Visual infographic explaining why become: true breaks SSH agent forwarding for git tasks on a target host while become: false works, due to sudo dropping SSH_AUTH_SOCK in a clean environment.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 1 2 L 16 9 L 1 16 Z" fill="#207448" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 1 2 L 16 9 L 1 16 Z" fill="#db8129" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1080" fill="#f5f8f5"/>

  <!-- Main Diagram Title -->
  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Why become breaks SSH agent forwarding for git</text>

  <!-- ==================== LEFT COLUMN: LAPTOP (Your login session) ==================== -->
  <g id="laptop-box">
    <!-- Outer Laptop Container spanning both paths -->
    <rect x="50" y="115" width="240" height="745" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- Laptop Outline Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(142, 145)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="28" rx="3"/>
      <path d="M 2 40 L 54 40"/>
      <line x1="22" y1="44" x2="34" y2="44" stroke-width="3"/>
    </g>

    <!-- Box Title: Your login session -->
    <text x="170" y="240" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="170" dy="0">Your login</tspan>
      <tspan x="170" dy="38">session</tspan>
    </text>

    <!-- Card: ssh-add -L with Key Icon -->
    <g transform="translate(68, 330)">
      <rect x="0" y="0" width="204" height="185" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Key Icon (56x56 outline, green stroke 4) -->
      <g transform="translate(74, 20)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="20" cy="20" r="12"/>
        <line x1="28" y1="28" x2="48" y2="48"/>
        <line x1="42" y1="42" x2="48" y2="36"/>
        <line x1="36" y1="36" x2="42" y2="30"/>
      </g>
      <!-- Label: ssh-add -L -->
      <text x="102" y="145" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">ssh-add -L</text>
    </g>

    <!-- Card: Agent socket SSH_AUTH_SOCK -->
    <g transform="translate(68, 555)">
      <rect x="0" y="0" width="204" height="185" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Socket Outline Icon (56x56 outline, green stroke 4) -->
      <g transform="translate(74, 22)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="10" width="44" height="36" rx="8"/>
        <line x1="18" y1="22" x2="18" y2="34"/>
        <line x1="38" y1="22" x2="38" y2="34"/>
        <circle cx="28" cy="28" r="4" fill="#207448"/>
      </g>
      <!-- Label: SSH_AUTH_SOCK -->
      <text x="102" y="145" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">SSH_AUTH_SOCK</text>
    </g>
  </g>

  <!-- ==================== FORWARDED AGENT ARROW (SHARED TRUNK & BRANCHES) ==================== -->
  <g id="forward-agent-arrow">
    <!-- Arrow label: ForwardAgent=yes positioned with ample clearance -->
    <text x="427" y="450" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">ForwardAgent=yes</text>

    <!-- Trunk from Laptop box -->
    <line x1="290" y1="485" x2="427" y2="485" stroke="#207448" stroke-width="4"/>

    <!-- Branch to Top Row Target -->
    <path d="M 427 485 H 480 V 270 H 547" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

    <!-- Branch to Bottom Row Target -->
    <path d="M 427 485 H 480 V 675 H 547" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>
  </g>

  <!-- ==================== TOP ROW: A PATH THAT WORKS ==================== -->
  <g id="top-row">
    <!-- Top Lane Background Panel -->
    <rect x="525" y="115" width="1025" height="310" rx="16" fill="#ffffff" stroke="#ccd9d0" stroke-width="2"/>

    <!-- Station 1: Target box titled Target with become: false -->
    <g id="top-target-box" transform="translate(565, 145)">
      <rect x="0" y="0" width="400" height="250" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

      <!-- Server Outline Icon (56x56) -->
      <g transform="translate(30, 25)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="48" height="44" rx="4"/>
        <line x1="4" y1="20" x2="52" y2="20" stroke-width="3"/>
        <line x1="4" y1="36" x2="52" y2="36" stroke-width="3"/>
        <circle cx="12" cy="13" r="2.5" fill="#207448"/>
        <circle cx="12" cy="28" r="2.5" fill="#207448"/>
        <circle cx="12" cy="44" r="2.5" fill="#207448"/>
      </g>

      <!-- Title: Target -->
      <text x="105" y="64" font-family="sans-serif" font-size="34" font-weight="bold" fill="#303a36">Target</text>

      <!-- Task sub-card: become: false -->
      <g transform="translate(30, 105)">
        <rect x="0" y="0" width="340" height="115" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
        <text x="170" y="68" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#207448">become: false</text>
      </g>
    </g>

    <!-- Arrow between Target and clone works -->
    <line x1="965" y1="270" x2="1082" y2="270" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

    <!-- Station 2: Result box with tick and the note the clone works -->
    <g id="top-result-box" transform="translate(1100, 145)">
      <rect x="0" y="0" width="410" height="250" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

      <!-- Tick outline icon (56x56 outline, green stroke 4) -->
      <g transform="translate(177, 40)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="24"/>
        <polyline points="16,28 24,36 40,20"/>
      </g>

      <!-- Note: the clone works -->
      <text x="205" y="175" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">the clone works</text>
    </g>
  </g>

  <!-- ==================== BOTTOM ROW: THE FAILING PATH ==================== -->
  <g id="bottom-row">
    <!-- Bottom Lane Background Panel -->
    <rect x="525" y="475" width="1025" height="425" rx="16" fill="#ffffff" stroke="#ccd9d0" stroke-width="2"/>

    <!-- Box 1: Target box running git task with become: true -->
    <g id="bottom-target-box" transform="translate(555, 510)">
      <rect x="0" y="0" width="180" height="310" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

      <!-- Server Outline Icon (56x56) -->
      <g transform="translate(62, 35)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="48" height="44" rx="4"/>
        <line x1="4" y1="20" x2="52" y2="20" stroke-width="3"/>
        <line x1="4" y1="36" x2="52" y2="36" stroke-width="3"/>
        <circle cx="12" cy="13" r="2.5" fill="#207448"/>
        <circle cx="12" cy="28" r="2.5" fill="#207448"/>
        <circle cx="12" cy="44" r="2.5" fill="#207448"/>
      </g>

      <!-- Monospace label: become: true (wrapped onto 2 lines with ample padding) -->
      <g transform="translate(18, 130)">
        <rect x="0" y="0" width="144" height="135" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
        <text x="72" y="60" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">
          <tspan x="72" dy="0">become:</tspan>
          <tspan x="72" dy="38">true</tspan>
        </text>
      </g>
    </g>

    <!-- Arrow 1 -> 2 -->
    <line x1="735" y1="665" x2="762" y2="665" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

    <!-- Box 2: Intermediate box (Orange highlight on sudo box, the step that drops the variable) -->
    <g id="sudo-box" transform="translate(780, 510)">
      <rect x="0" y="0" width="335" height="310" rx="14" fill="#fff9f2" stroke="#db8129" stroke-width="3.5"/>

      <!-- Shield / Clean Environment Outline Icon (56x56 outline, orange stroke 4) -->
      <g transform="translate(139, 25)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 28 6 L 50 14 V 28 C 50 42 28 50 28 50 C 28 50 6 42 6 28 V 14 Z"/>
        <line x1="18" y1="28" x2="38" y2="28"/>
        <line x1="28" y1="18" x2="28" y2="38"/>
      </g>

      <!-- Title: sudo starts a clean environment -->
      <text x="167" y="122" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
        <tspan x="167" dy="0">sudo starts a</tspan>
        <tspan x="167" dy="36">clean environment</tspan>
      </text>

      <!-- Note: SSH_AUTH_SOCK is dropped unless env_keep keeps it -->
      <g transform="translate(16, 185)">
        <rect x="0" y="0" width="303" height="105" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="2"/>
        <text x="151" y="32" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
          <tspan x="151" dy="0" font-family="monospace" font-weight="bold" fill="#db8129">SSH_AUTH_SOCK</tspan>
          <tspan font-family="sans-serif"> is dropped</tspan>
          <tspan x="151" dy="34" font-family="sans-serif">unless </tspan>
          <tspan font-family="monospace" font-weight="bold" fill="#207448">env_keep</tspan>
          <tspan font-family="sans-serif"> keeps it</tspan>
        </text>
      </g>
    </g>

    <!-- Arrow 2 -> 3 -->
    <line x1="1115" y1="665" x2="1142" y2="665" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

    <!-- Box 3: git has no agent to ask -->
    <g id="no-agent-box" transform="translate(1160, 510)">
      <rect x="0" y="0" width="170" height="310" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

      <!-- Question / Disconnected socket outline icon (56x56) -->
      <g transform="translate(57, 35)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="24"/>
        <path d="M 20 20 C 20 12 36 12 36 22 C 36 28 28 28 28 35"/>
        <circle cx="28" cy="43" r="2.5" fill="#207448"/>
      </g>

      <!-- Note: git has no agent to ask -->
      <g transform="translate(15, 130)">
        <rect x="0" y="0" width="140" height="150" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
        <text x="70" y="48" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
          <tspan x="70" dy="0">git has</tspan>
          <tspan x="70" dy="34">no agent</tspan>
          <tspan x="70" dy="34">to ask</tspan>
        </text>
      </g>
    </g>

    <!-- Arrow 3 -> 4 (leading to result box) -->
    <line x1="1330" y1="665" x2="1357" y2="665" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

    <!-- Box 4: Result box labelled Permission denied (publickey) -->
    <g id="permission-denied-box" transform="translate(1375, 510)">
      <rect x="0" y="0" width="160" height="310" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

      <!-- Lock / Denied outline icon (56x56 outline) -->
      <g transform="translate(52, 35)" stroke="#303a36" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="8" y="22" width="40" height="28" rx="5"/>
        <path d="M 16 22 V 14 C 16 7 40 7 40 14 V 22"/>
        <circle cx="28" cy="33" r="3" fill="#303a36"/>
        <line x1="28" y1="36" x2="28" y2="43" stroke-width="3"/>
      </g>

      <!-- Label: Permission denied (publickey) -->
      <g transform="translate(12, 130)">
        <rect x="0" y="0" width="136" height="150" rx="10" fill="#ffffff" stroke="#303a36" stroke-width="2"/>
        <text x="68" y="44" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
          <tspan x="68" dy="0">Permission</tspan>
          <tspan x="68" dy="34">denied</tspan>
          <tspan x="68" dy="34" font-size="24">(publickey)</tspan>
        </text>
      </g>
    </g>

    <!-- Small label at bottom of lower row: the key was fine, the environment was not -->
    <text x="1037" y="870" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">the key was fine, the environment was not</text>
  </g>

  <!-- ==================== GREEN TAKEAWAY BAR AT BOTTOM ==================== -->
  <g id="takeaway-bar" transform="translate(50, 930)">
    <rect width="1500" height="110" rx="16" fill="#207448"/>
    <!-- Key Takeaway Checkmark / Star Icon -->
    <g transform="translate(35, 27)" stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="24"/>
      <path d="M 18 28 L 25 35 L 38 21"/>
    </g>
    <text x="800" y="48" text-anchor="middle" font-family="sans-serif" font-size="25" fill="#ffffff">
      <tspan x="800" dy="0">Check 3 is about privilege, and it is the one that catches most people,</tspan>
      <tspan x="800" dy="36">so make sure the git task does not set <tspan font-family="monospace" font-weight="bold">become: true</tspan>.</tspan>
    </text>
  </g>
</svg>'''

pathlib.Path('test_candidate.svg').write_text(svg)
print('Saved test_candidate.svg')
