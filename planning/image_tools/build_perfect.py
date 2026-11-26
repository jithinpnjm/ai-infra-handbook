import xml.etree.ElementTree as ET
import re

def build_perfect_svg():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1190" width="1600" height="1190">
  <title>Where a variable can be defined, from the desk note to the front door</title>
  <desc>A reach ladder from narrow to wide illustrating where Ansible variables can be defined, from local task variables to global extra vars, with placement rules and the NCCL debug scenario.</desc>

  <!-- Background -->
  <rect width="1600" height="1190" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Where a variable can be defined, from the desk note to the front door</text>

  <!-- ==================== LADDER SECTION: NARROW TO WIDE ==================== -->
  <!-- Ladder background container -->
  <rect x="40" y="80" width="1520" height="696" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

  <!-- Vertical ladder rails -->
  <line x1="50" y1="92" x2="50" y2="764" stroke="#207448" stroke-width="4" stroke-opacity="0.35" />
  <line x1="1550" y1="92" x2="1550" y2="764" stroke="#207448" stroke-width="4" stroke-opacity="0.35" />

  <!-- RUNG 1: task vars (narrowest reach, 1 task) -->
  <g id="rung-1">
    <rect x="64" y="92" width="1472" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
    <!-- Reach indicator bar at bottom of card (120px) -->
    <rect x="64" y="144" width="120" height="6" rx="3" fill="#207448" />
    <!-- Icon 1: Task clipboard with single checkmark (56px) -->
    <g transform="translate(78, 93)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="12" y="10" width="32" height="40" rx="4" />
      <path d="M 20 10 V 6 C 20 4.5 21.5 4 23 4 H 33 C 34.5 4 36 4.5 36 6 V 10" />
      <polyline points="20,28 26,34 36,22" />
    </g>
    <text x="148" y="129" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan font-weight="bold" fill="#207448">task vars: </tspan>only that one task, gone when it ends (extra: 1)
    </text>
  </g>

  <!-- RUNG 2: set_fact and register -->
  <g id="rung-2">
    <rect x="64" y="158" width="1472" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
    <!-- Reach indicator bar (250px) -->
    <rect x="64" y="210" width="250" height="6" rx="3" fill="#207448" />
    <!-- Icon 2: Task gear / fact generator (56px) -->
    <g transform="translate(78, 159)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="10" />
      <path d="M 28 8 V 14 M 28 42 V 48 M 8 28 H 14 M 42 28 H 48 M 14 14 L 18 18 M 38 38 L 42 42 M 14 42 L 18 38 M 38 18 L 42 14" />
    </g>
    <text x="148" y="195" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan font-weight="bold" fill="#207448">set_fact and register: </tspan>created by tasks
    </text>
  </g>

  <!-- RUNG 3: include_vars -->
  <g id="rung-3">
    <rect x="64" y="224" width="1472" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
    <!-- Reach indicator bar (380px) -->
    <rect x="64" y="276" width="380" height="6" rx="3" fill="#207448" />
    <!-- Icon 3: Folder with incoming data / import (56px) -->
    <g transform="translate(78, 225)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 14 C 6 11 8 9 11 9 H 22 L 28 15 H 45 C 48 15 50 17 50 20 V 43 C 50 46 48 48 45 48 H 11 C 8 48 6 46 6 43 Z" />
      <line x1="28" y1="24" x2="28" y2="38" />
      <polyline points="22,32 28,38 34,32" />
    </g>
    <text x="148" y="261" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan font-weight="bold" fill="#207448">include_vars: </tspan>loads a file or directory into host variables during the run
    </text>
  </g>

  <!-- RUNG 4: play vars -->
  <g id="rung-4">
    <rect x="64" y="290" width="1472" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
    <!-- Reach indicator bar (520px) -->
    <rect x="64" y="342" width="520" height="6" rx="3" fill="#207448" />
    <!-- Icon 4: Play script / document block (56px) -->
    <g transform="translate(78, 291)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="6" width="36" height="44" rx="4" />
      <polygon points="24,18 36,26 24,34" fill="#207448" stroke="none" />
      <line x1="18" y1="40" x2="38" y2="40" />
    </g>
    <text x="148" y="327" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan font-weight="bold" fill="#207448">play vars: </tspan>vars block, belongs to the play, stops when the play ends
    </text>
  </g>

  <!-- RUNG 5: vars_files (multi-line) -->
  <g id="rung-5">
    <rect x="64" y="356" width="1472" height="114" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
    <!-- Reach indicator bar (700px) -->
    <rect x="64" y="464" width="700" height="6" rx="3" fill="#207448" />
    <!-- Icon 5: Multiple template files stack (56px) -->
    <g transform="translate(78, 385)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 16 10 H 42 C 45 10 47 12 47 15 V 45" />
      <rect x="9" y="16" width="32" height="36" rx="4" />
      <line x1="16" y1="26" x2="34" y2="26" />
      <line x1="16" y1="34" x2="28" y2="34" />
      <line x1="16" y1="42" x2="32" y2="42" />
    </g>
    <text x="148" y="388" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="148" dy="0"><tspan font-weight="bold" fill="#207448">vars_files: </tspan>loads files at the start of the play; </tspan>
      <tspan x="148" dy="28">the file name can itself be a template, <tspan font-family="monospace">vars/{{ ansible_facts[os_family] | lower }}.yml</tspan>, </tspan>
      <tspan x="148" dy="28">so Debian and RedHat hosts load different files with no if statement</tspan>
    </text>
  </g>

  <!-- RUNG 6: vars_prompt (orange highlight) -->
  <g id="rung-6">
    <rect x="64" y="478" width="1472" height="88" rx="8" fill="#fff7f0" stroke="#db8129" stroke-width="2.5" />
    <!-- Reach indicator bar (880px) in orange -->
    <rect x="64" y="560" width="880" height="6" rx="3" fill="#db8129" />
    <!-- Icon 6: User prompt / alert dialog (56px) in orange -->
    <g transform="translate(78, 494)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 8 10 C 8 7 10 5 13 5 H 43 C 46 5 48 7 48 10 V 34 C 48 37 46 39 43 39 H 24 L 14 47 V 39 H 13 C 10 39 8 37 8 34 Z" />
      <line x1="28" y1="14" x2="28" y2="24" stroke-width="4" />
      <circle cx="28" cy="31" r="2" fill="#db8129" stroke="none" />
    </g>
    <text x="148" y="513" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="148" dy="0"><tspan font-weight="bold" fill="#db8129">vars_prompt: </tspan>asks a person at run time: avoid in automation, it stops the run and waits </tspan>
      <tspan x="148" dy="30">(private: false, name reason, prompt Maintenance reason)</tspan>
    </text>
  </g>

  <!-- RUNG 7: lookup results and lookup(env, ...) -->
  <g id="rung-7">
    <rect x="64" y="574" width="1472" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
    <!-- Reach indicator bar (1080px) -->
    <rect x="64" y="626" width="1080" height="6" rx="3" fill="#207448" />
    <!-- Icon 7: Magnifying glass / search lookup (56px) -->
    <g transform="translate(78, 575)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="24" cy="24" r="14" />
      <line x1="34" y1="34" x2="48" y2="48" stroke-width="4.5" />
    </g>
    <text x="148" y="611" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan font-weight="bold" fill="#207448">lookup results and lookup(env, ...)</tspan>
    </text>
  </g>

  <!-- RUNG 8: inventory, group_vars, host_vars and roles -->
  <g id="rung-8">
    <rect x="64" y="640" width="1472" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8" />
    <!-- Reach indicator bar (1280px) -->
    <rect x="64" y="692" width="1280" height="6" rx="3" fill="#207448" />
    <!-- Icon 8: Network cluster / rack hierarchy (56px) -->
    <g transform="translate(78, 641)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="14" y="6" width="28" height="12" rx="3" />
      <rect x="4" y="34" width="20" height="12" rx="3" />
      <rect x="32" y="34" width="20" height="12" rx="3" />
      <line x1="28" y1="18" x2="28" y2="26" />
      <line x1="14" y1="26" x2="42" y2="26" />
      <line x1="14" y1="26" x2="14" y2="34" />
      <line x1="42" y1="26" x2="42" y2="34" />
    </g>
    <text x="148" y="677" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan font-weight="bold" fill="#207448">inventory, group_vars, host_vars (4.5) and role defaults/ and vars/ (4.11)</tspan>
    </text>
  </g>

  <!-- RUNG 9: extra vars -e (widest reach, front door) -->
  <g id="rung-9">
    <rect x="64" y="706" width="1472" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Reach indicator bar (1472px full card width) -->
    <rect x="64" y="758" width="1472" height="6" rx="3" fill="#207448" />
    <!-- Icon 9: Terminal prompt / CLI extra vars (56px) -->
    <g transform="translate(78, 707)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="38" rx="5" />
      <polyline points="14,20 22,27 14,34" />
      <line x1="26" y1="34" x2="38" y2="34" stroke-width="4" />
    </g>
    <text x="148" y="743" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan font-weight="bold" fill="#207448">extra vars -e: </tspan>key=value, a JSON-style string such as {"k": [1,2]}, or @file.yml
    </text>
  </g>

  <!-- ==================== PLACEMENT RULE PANEL ==================== -->
  <g id="placement-rule-panel">
    <rect x="40" y="792" width="1520" height="144" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Balance / compass outline icon (56px) -->
    <g transform="translate(68, 836)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="28" y1="6" x2="28" y2="48" stroke-width="4" />
      <line x1="10" y1="16" x2="46" y2="16" stroke-width="4" />
      <path d="M 10 16 L 4 32 H 16 Z" />
      <path d="M 46 16 L 40 32 H 52 Z" />
      <line x1="18" y1="48" x2="38" y2="48" stroke-width="4" />
    </g>
    <text x="148" y="828" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="148" dy="0"><tspan font-weight="bold" fill="#207448">put a value where the people who own it will look: </tspan></tspan>
      <tspan x="148" dy="28">a cluster-wide default in group_vars/all, a rack's special case in the group for that rack, </tspan>
      <tspan x="148" dy="28">a one-off test on the command line where it vanishes when the run ends; </tspan>
      <tspan x="148" dy="28">which one wins when two disagree is in 4.5</tspan>
    </text>
  </g>

  <!-- ==================== STORY STRIP ==================== -->
  <g id="story-strip">
    <rect x="40" y="952" width="1520" height="126" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Clock / disk warning incident icon (56px) -->
    <g transform="translate(68, 987)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="20" />
      <polyline points="28,14 28,28 38,28" stroke-width="4" />
      <circle cx="42" cy="14" r="7" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
      <line x1="42" y1="11" x2="42" y2="15" stroke-width="2.5" />
      <circle cx="42" cy="18" r="0.8" fill="#207448" />
    </g>
    <text x="148" y="992" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="148" dy="0"><tspan font-weight="bold" fill="#207448">late Tuesday: </tspan>raising the NCCL debug level for the second cluster </tspan>
      <tspan x="148" dy="32">also turned on verbose logging on the first, filling its disk: </tspan>
      <tspan x="148" dy="32">the setting was written in a place that reached further than you thought</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1094" width="1520" height="66" rx="12" fill="#207448" />
    <text x="800" y="1136" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">The place you choose decides how far the value reaches</text>
  </g>
</svg>"""
    return svg

svg_data = build_perfect_svg()
with open("final_candidate_test.svg", "w") as f:
    f.write(svg_data)
print("Built and saved final_candidate_test.svg")
