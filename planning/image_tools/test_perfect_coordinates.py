from test_runner import test_svg_with_playwright

def generate_svg(p):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Which ansible.cfg wins: the search order and the precedence of settings</title>
  <desc>Visual infographic explaining the search order of ansible.cfg files (first found wins, never merged) and the precedence of configuration settings from flags down to defaults.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title (48px bold, top margin >= 40px) -->
  <text font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">
    <tspan x="800" y="{p['t_y1']}">Which ansible.cfg wins: </tspan>
    <tspan x="800" y="{p['t_y2']}">the search order and the precedence of settings</tspan>
  </text>

  <!-- ==================== LADDER 1: Which file is read (x=40..780, y={p['lad_y']}..{p['lad_y']+p['lad_h']}, w=740, h={p['lad_h']}) ==================== -->
  <g id="ladder-1">
    <rect x="40" y="{p['lad_y']}" width="740" height="{p['lad_h']}" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    
    <!-- Ladder 1 Header text (30px bold) -->
    <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="64" y="{p['lad_y'] + 36}">Which file is read </tspan>
      <tspan x="64" y="{p['lad_y'] + 68}">(first found wins, never merged)</tspan>
    </text>

    <!-- Step 1 Card: ANSIBLE_CONFIG environment variable (w=708, h={p['c1_h']}) -->
    <rect x="56" y="{p['c1_y']}" width="708" height="{p['c1_h']}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="88" cy="{p['c1_y'] + p['c1_h']//2}" r="24" fill="#207448" />
    <text x="88" y="{p['c1_y'] + p['c1_h']//2 + 9}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <!-- Outline icon: Terminal prompt window (36px) -->
    <g transform="translate(124, {p['c1_y'] + (p['c1_h']-32)//2})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="40" height="28" rx="5" />
      <path d="M 9 10 L 17 16 L 9 22" />
      <line x1="21" y1="22" x2="31" y2="22" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="180" y="{p['c1_y'] + p['c1_ty']}" font-family="monospace" font-weight="bold">ANSIBLE_CONFIG </tspan>
      <tspan x="382" y="{p['c1_y'] + p['c1_ty']}" font-family="sans-serif">environment variable</tspan>
    </text>

    <!-- Step 2 Card: ./ansible.cfg (w=708, h={p['c2_h']}) -->
    <rect x="56" y="{p['c2_y']}" width="708" height="{p['c2_h']}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="88" cy="{p['c2_y'] + 38}" r="24" fill="#207448" />
    <text x="88" y="{p['c2_y'] + 47}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <!-- Outline icon: Security folder with lock (34px) -->
    <g transform="translate(124, {p['c2_y'] + 21})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 3 10 L 14 10 L 19 15 L 35 15 A 3 3 0 0 1 38 18 L 38 33 A 3 3 0 0 1 35 36 L 3 36 A 3 3 0 0 1 0 33 L 0 13 A 3 3 0 0 1 3 10 Z" />
      <rect x="15" y="20" width="13" height="11" rx="2" fill="#e8f1ea" />
      <path d="M 18 20 V 15 C 18 13 25 13 25 15 V 20" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="180" y="{p['c2_y'] + p['c2_ty1']}" font-family="monospace" font-weight="bold">./ansible.cfg </tspan>
      <tspan x="180" y="{p['c2_y'] + p['c2_ty2']}" font-family="sans-serif">in the current directory </tspan>
      <tspan x="72" y="{p['c2_y'] + p['c2_ty3']}">(honoured only if it is not world-writable: a </tspan>
      <tspan x="72" y="{p['c2_y'] + p['c2_ty4']}">folder any user can change cannot be trusted)</tspan>
    </text>

    <!-- Step 3 Card: ~/.ansible.cfg (w=708, h={p['c3_h']}) -->
    <rect x="56" y="{p['c3_y']}" width="708" height="{p['c3_h']}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="88" cy="{p['c3_y'] + p['c3_h']//2}" r="24" fill="#207448" />
    <text x="88" y="{p['c3_y'] + p['c3_h']//2 + 9}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <!-- Outline icon: Home house (34px) -->
    <g transform="translate(124, {p['c3_y'] + (p['c3_h']-34)//2})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 5 18 L 19 5 L 33 18 V 32 A 2 2 0 0 1 31 34 H 7 A 2 2 0 0 1 5 32 Z" />
      <path d="M 14 34 V 20 H 24 V 34" />
    </g>
    <text x="180" y="{p['c3_y'] + p['c3_ty']}" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">~/.ansible.cfg</text>

    <!-- Step 4 Card: /etc/ansible/ansible.cfg (w=708, h={p['c4_h']}) -->
    <rect x="56" y="{p['c4_y']}" width="708" height="{p['c4_h']}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="88" cy="{p['c4_y'] + p['c4_h']//2}" r="24" fill="#207448" />
    <text x="88" y="{p['c4_y'] + p['c4_h']//2 + 9}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <!-- Outline icon: Server rack (30px) -->
    <g transform="translate(124, {p['c4_y'] + (p['c4_h']-28)//2})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="32" height="24" rx="3" />
      <line x1="3" y1="11" x2="35" y2="11" />
      <line x1="3" y1="19" x2="35" y2="19" />
      <circle cx="29" cy="7" r="1.5" fill="#207448" />
      <circle cx="29" cy="15" r="1.5" fill="#207448" />
      <circle cx="29" cy="23" r="1.5" fill="#207448" />
    </g>
    <text x="180" y="{p['c4_y'] + p['c4_ty']}" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">/etc/ansible/ansible.cfg</text>
  </g>

  <!-- ==================== LADDER 2: Which value wins (x=820..1560, y={p['lad_y']}..{p['lad_y']+p['lad_h']}, w=740, h={p['lad_h']}) ==================== -->
  <g id="ladder-2">
    <rect x="820" y="{p['lad_y']}" width="740" height="{p['lad_h']}" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    
    <!-- Ladder 2 Header text (30px bold) -->
    <text x="844" y="{p['lad_y'] + 52}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Which value wins</text>

    <!-- Step 1 Card: command-line flags (w=708, h={p['l2_h']}) -->
    <rect x="836" y="{p['l2_c1_y']}" width="708" height="{p['l2_h']}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="868" cy="{p['l2_c1_y'] + p['l2_h']//2}" r="24" fill="#207448" />
    <text x="868" y="{p['l2_c1_y'] + p['l2_h']//2 + 9}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <!-- Outline icon: Flag post (38px) -->
    <g transform="translate(904, {p['l2_c1_y'] + (p['l2_h']-36)//2})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="10" y1="4" x2="10" y2="34" />
      <polygon points="10,6 34,13 10,20" fill="#e8f1ea" />
      <line x1="5" y1="34" x2="15" y2="34" />
    </g>
    <text x="960" y="{p['l2_c1_y'] + p['l2_ty']}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">command-line flags</text>

    <!-- Step 2 Card: environment variables (w=708, h={p['l2_h']}) -->
    <rect x="836" y="{p['l2_c2_y']}" width="708" height="{p['l2_h']}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="868" cy="{p['l2_c2_y'] + p['l2_h']//2}" r="24" fill="#207448" />
    <text x="868" y="{p['l2_c2_y'] + p['l2_h']//2 + 9}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <!-- Outline icon: Variable braces (36px) -->
    <g transform="translate(904, {p['l2_c2_y'] + (p['l2_h']-34)//2})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 5 C 6 5 6 16 2 18 C 6 20 6 31 12 31" />
      <path d="M 26 5 C 32 5 32 16 36 18 C 32 20 32 31 26 31" />
      <line x1="16" y1="18" x2="22" y2="18" />
    </g>
    <text x="960" y="{p['l2_c2_y'] + p['l2_ty']}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">environment variables</text>

    <!-- Step 3 Card: config file (w=708, h={p['l2_h']}) -->
    <rect x="836" y="{p['l2_c3_y']}" width="708" height="{p['l2_h']}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="868" cy="{p['l2_c3_y'] + p['l2_h']//2}" r="24" fill="#207448" />
    <text x="868" y="{p['l2_c3_y'] + p['l2_h']//2 + 9}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <!-- Outline icon: Config document (36px) -->
    <g transform="translate(904, {p['l2_c3_y'] + (p['l2_h']-36)//2})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 8 5 L 24 5 L 34 15 L 34 34 A 2 2 0 0 1 32 36 L 10 36 A 2 2 0 0 1 8 34 Z" />
      <polyline points="24,5 24,15 34,15" />
      <line x1="14" y1="22" x2="28" y2="22" />
      <line x1="14" y1="28" x2="24" y2="28" />
    </g>
    <text x="960" y="{p['l2_c3_y'] + p['l2_ty']}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">config file</text>

    <!-- Step 4 Card: defaults (w=708, h={p['l2_h']}) -->
    <rect x="836" y="{p['l2_c4_y']}" width="708" height="{p['l2_h']}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <circle cx="868" cy="{p['l2_c4_y'] + p['l2_h']//2}" r="24" fill="#207448" />
    <text x="868" y="{p['l2_c4_y'] + p['l2_h']//2 + 9}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <!-- Outline icon: Foundation building block (36px) -->
    <g transform="translate(904, {p['l2_c4_y'] + (p['l2_h']-34)//2})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="5" y="15" width="32" height="17" rx="3" />
      <line x1="5" y1="23" x2="37" y2="23" />
      <line x1="21" y1="23" x2="21" y2="32" />
      <path d="M 14 15 V 6 L 28 6 V 15" />
    </g>
    <text x="960" y="{p['l2_c4_y'] + p['l2_ty']}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">defaults</text>
  </g>

  <!-- ==================== COMMANDS STRIP (x=40..1560, y={p['cmd_y']}..{p['cmd_y']+p['cmd_h']}, w=1520, h={p['cmd_h']}) ==================== -->
  <g id="commands-strip">
    <rect x="40" y="{p['cmd_y']}" width="1520" height="{p['cmd_h']}" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Outline icon: Terminal prompt window (40px) -->
    <g transform="translate(64, {p['cmd_y'] + (p['cmd_h']-36)//2})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="3" width="44" height="32" rx="5" />
      <path d="M 11 12 L 19 18 L 11 24" />
      <line x1="23" y1="24" x2="35" y2="24" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="136" y="{p['cmd_y'] + p['cmd_ty1']}"><tspan font-family="monospace" font-weight="bold">ansible-config dump --only-changed</tspan> shows only what you changed; </tspan>
      <tspan x="136" y="{p['cmd_y'] + p['cmd_ty2']}"><tspan font-family="monospace" font-weight="bold">ansible-config list</tspan> shows every setting with its default; </tspan>
      <tspan x="136" y="{p['cmd_y'] + p['cmd_ty3']}"><tspan font-family="monospace" font-weight="bold">ansible --version</tspan> shows the config file in use</tspan>
    </text>
  </g>

  <!-- ==================== SURPRISE STORY (orange) (x=40..1560, y={p['surp_y']}..{p['surp_y']+p['surp_h']}, w=1520, h={p['surp_h']}) ==================== -->
  <g id="surprise-story">
    <rect x="40" y="{p['surp_y']}" width="1520" height="{p['surp_h']}" rx="12" fill="#fffaf5" stroke="#db8129" stroke-width="2.5" />
    <!-- Outline icon in orange: Alert / warning triangle (40px) -->
    <g transform="translate(64, {p['surp_y'] + (p['surp_h']-36)//2})" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="22,3 42,35 2,35" />
      <line x1="22" y1="13" x2="22" y2="23" />
      <circle cx="22" cy="29" r="1.5" fill="#db8129" stroke="none" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="136" y="{p['surp_y'] + p['surp_ty1']}">an engineer runs Ansible from a folder they did not expect, </tspan>
      <tspan x="136" y="{p['surp_y'] + p['surp_ty2']}">and the tool quietly picks up a different config file</tspan>
    </text>
  </g>

  <!-- ==================== RULES STRIP (x=40..1560, y={p['rules_y']}..{p['rules_y']+p['rules_h']}, w=1520, h={p['rules_h']}) ==================== -->
  <g id="rules-strip">
    <rect x="40" y="{p['rules_y']}" width="1520" height="{p['rules_h']}" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Outline icon: Shield best practice rules (40px) -->
    <g transform="translate(64, {p['rules_y'] + (p['rules_h']-38)//2})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 22 3 L 39 10 V 21 C 39 31 22 37 22 37 C 22 37 5 31 5 21 V 10 Z" />
      <polyline points="15,21 20,26 30,14" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="136" y="{p['rules_y'] + p['rules_ty1']}">keep a project-level <tspan font-family="monospace" font-weight="bold">ansible.cfg</tspan> in the repo root; </tspan>
      <tspan x="136" y="{p['rules_y'] + p['rules_ty2']}">keep secrets and personal paths out of it because it is committed; </tspan>
      <tspan x="136" y="{p['rules_y'] + p['rules_ty3']}">editing <tspan font-family="monospace" font-weight="bold">/etc/ansible</tspan> changes behaviour between laptops and CI and is invisible to Git</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR (x=40..1560, y={p['bar_y']}..{p['bar_y']+p['bar_h']}, w=1520, h={p['bar_h']}) ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="{p['bar_y']}" width="1520" height="{p['bar_h']}" rx="10" fill="#207448" />
    <text x="800" y="{p['bar_y'] + p['bar_ty']}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Knowing the search order turns a surprise into a quick check</text>
  </g>
</svg>'''

p = {
    't_y1': 84,
    't_y2': 130,
    
    'lad_y': 172,
    'lad_h': 446, # 172..618
    
    # Ladder 1 Cards
    'c1_y': 260,
    'c1_h': 60,
    'c1_ty': 38,
    
    'c2_y': 326,
    'c2_h': 148,
    'c2_ty1': 35,
    'c2_ty2': 62,
    'c2_ty3': 95,
    'c2_ty4': 123,
    
    'c3_y': 480,
    'c3_h': 60,
    'c3_ty': 38,
    
    'c4_y': 546,
    'c4_h': 60,
    'c4_ty': 38,
    
    # Ladder 2 Cards
    'l2_h': 82,
    'l2_ty': 51,
    'l2_c1_y': 260,
    'l2_c2_y': 348,
    'l2_c3_y': 436,
    'l2_c4_y': 524,
    
    # Strips
    'cmd_y': 658, # gap = 658 - 618 = 40
    'cmd_h': 116,
    'cmd_ty1': 38,
    'cmd_ty2': 66,
    'cmd_ty3': 94,
    
    'surp_y': 814, # gap = 814 - 774 = 40
    'surp_h': 88,
    'surp_ty1': 38,
    'surp_ty2': 66,
    
    'rules_y': 942, # gap = 942 - 902 = 40
    'rules_h': 116,
    'rules_ty1': 38,
    'rules_ty2': 66,
    'rules_ty3': 94,
    
    'bar_y': 1098, # gap = 1098 - 1058 = 40
    'bar_h': 58,
    'bar_ty': 37, # bottom = 1098 + 58 = 1156 -> bottom margin = 44px >= 40px!
}

svg_str = generate_svg(p)
with open('candidate_cfg_order.svg', 'w') as f:
    f.write(svg_str)

issues = test_svg_with_playwright(svg_str)
print("=== PLAYWRIGHT RUN RESULTS ===")
if not issues:
    print("ALL TESTS PASSED! ZERO ISSUES!")
else:
    for iss in issues:
        print("ISSUE:", iss)
