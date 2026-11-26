import xml.etree.ElementTree as ET
import re
import subprocess
import os

def create_svg():
    W = 1600
    H = 1040

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <title>Three rooms, one skill: the round has two shapes</title>
  <desc>Visual infographic explaining how the same technical project question appears across three interview rooms—team leader final hour, project deep dive, and hiring-manager conversation—and how to prepare for each.</desc>

  <!-- Background -->
  <rect width="{W}" height="{H}" fill="#f5f8f5"/>

  <!-- ==================== TITLE ==================== -->
  <text x="800" y="58" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Three rooms, one skill: the round has two shapes</text>

  <!-- ==================== TOP BANNER ==================== -->
  <g id="top-banner">
    <rect x="70" y="92" width="1460" height="56" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="800" y="128" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">The same question arrives in three rooms, and the skill underneath is the same</text>
  </g>

  <!-- ==================== THREE COLUMN CARD BACKGROUNDS ==================== -->
  <rect x="70" y="165" width="460" height="715" rx="16" fill="#ffffff"/>
  <rect x="570" y="165" width="460" height="715" rx="16" fill="#ffffff"/>
  <rect x="1070" y="165" width="460" height="715" rx="16" fill="#ffffff"/>

  <!-- ==================== EVIDENCE TAGS ==================== -->
  <!-- Col 1 Tag: [official] -->
  <g id="col1-tag">
    <rect x="210" y="182" width="180" height="42" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="300" y="211" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">[official]</text>
  </g>

  <!-- Col 2 Tag: [unverified] -->
  <g id="col2-tag">
    <rect x="695" y="182" width="210" height="42" rx="8" fill="#f5f8f5" stroke="#718079" stroke-width="2"/>
    <text x="800" y="211" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#5a6661">[unverified]</text>
  </g>

  <!-- Col 3 Tag: [unverified] -->
  <g id="col3-tag">
    <rect x="1195" y="182" width="210" height="42" rx="8" fill="#f5f8f5" stroke="#718079" stroke-width="2"/>
    <text x="1300" y="211" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#5a6661">[unverified]</text>
  </g>

  <!-- ==================== ICONS ==================== -->
  <!-- Col 1 Icon: Team Leader (Person with leadership collar/tie) -->
  <g transform="translate(272, 236)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="28" cy="16" r="11"/>
    <path d="M 10 48 C 10 36 18 32 28 32 C 38 32 46 36 46 48"/>
    <polyline points="24,34 28,42 32,34"/>
  </g>

  <!-- Col 2 Icon: Deep Dive (Magnifying glass inspection with layer slices) -->
  <g transform="translate(772, 236)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="24" cy="22" r="16"/>
    <line x1="36" y1="34" x2="48" y2="46"/>
    <line x1="16" y1="18" x2="32" y2="18"/>
    <line x1="14" y1="24" x2="34" y2="24"/>
    <line x1="18" y1="30" x2="30" y2="30"/>
  </g>

  <!-- Col 3 Icon: Hiring-manager conversation (Two dialogue speech bubbles) -->
  <g transform="translate(1272, 236)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 6 10 H 34 C 36 10 38 12 38 14 V 28 C 38 30 36 32 34 32 H 18 L 10 40 V 32 H 6 C 4 32 2 30 2 28 V 14 C 2 12 4 10 6 10 Z"/>
    <path d="M 42 20 H 50 C 52 20 54 22 54 24 V 36 C 54 38 52 40 50 40 H 46 V 48 L 38 40 H 32"/>
  </g>

  <!-- ==================== COLUMN HEADERS ==================== -->
  <!-- Col 1 Header: Final hour with a team leader -->
  <text x="300" y="322" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
    <tspan x="300" dy="0">Final hour with</tspan>
    <tspan x="300" dy="38">a team leader</tspan>
  </text>

  <!-- Col 2 Header: Project deep dive of up to 90 minutes -->
  <text x="800" y="322" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Project deep dive</tspan>
    <tspan x="800" dy="38">of up to 90 minutes</tspan>
  </text>

  <!-- Col 3 Header: Hiring-manager conversation -->
  <text x="1300" y="322" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
    <tspan x="1300" dy="0">Hiring-manager</tspan>
    <tspan x="1300" dy="38">conversation</tspan>
  </text>

  <!-- ==================== ROW 1 BANNER: What the source says ==================== -->
  <g id="source-row-banner">
    <rect x="70" y="395" width="1460" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="800" y="427" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">What the source says</text>
  </g>

  <!-- Col 1 Source Box -->
  <rect x="85" y="455" width="430" height="155" rx="10" fill="#f5f8f5" stroke="#c4d9cb" stroke-width="1.5"/>
  <text x="300" y="500" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="300" dy="0">Team, projects, services,</tspan>
    <tspan x="300" dy="34">possibly extra technical</tspan>
    <tspan x="300" dy="34">questions told in advance</tspan>
  </text>

  <!-- Col 2 Source Box -->
  <rect x="585" y="455" width="430" height="155" rx="10" fill="#f5f8f5" stroke="#c4d9cb" stroke-width="1.5"/>
  <text x="800" y="517" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="800" dy="0">A technical defence of</tspan>
    <tspan x="800" dy="34">one significant project</tspan>
  </text>

  <!-- Col 3 Source Box -->
  <rect x="1085" y="455" width="430" height="155" rx="10" fill="#f5f8f5" stroke="#c4d9cb" stroke-width="1.5"/>
  <text x="1300" y="517" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="1300" dy="0">Past projects, reasons for</tspan>
    <tspan x="1300" dy="34">key decisions, teamwork</tspan>
  </text>

  <!-- ==================== ROW 2 BANNER: What to prepare ==================== -->
  <g id="prepare-row-banner">
    <rect x="70" y="628" width="1460" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="800" y="660" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">What to prepare</text>
  </g>

  <!-- Col 1 Prepare Box -->
  <rect x="85" y="688" width="430" height="175" rx="10" fill="#f5f8f5" stroke="#c4d9cb" stroke-width="1.5"/>
  <text x="300" y="726" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="300" dy="0">A two-minute project story,</tspan>
    <tspan x="300" dy="32">questions for the</tspan>
    <tspan x="300" dy="32">team leader, the</tspan>
    <tspan x="300" dy="32">first-90-days answer</tspan>
  </text>

  <!-- Col 2 Prepare Box -->
  <rect x="585" y="688" width="430" height="175" rx="10" fill="#f5f8f5" stroke="#c4d9cb" stroke-width="1.5"/>
  <text x="800" y="742" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="800" dy="0">The full dossier,</tspan>
    <tspan x="800" dy="34">five levels of why, and</tspan>
    <tspan x="800" dy="34">a whiteboard sketch</tspan>
  </text>

  <!-- Col 3 Prepare Box -->
  <rect x="1085" y="688" width="430" height="175" rx="10" fill="#f5f8f5" stroke="#c4d9cb" stroke-width="1.5"/>
  <text x="1300" y="742" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="1300" dy="0">Decision stories with</tspan>
    <tspan x="1300" dy="34">alternatives, and</tspan>
    <tspan x="1300" dy="34">one teamwork story</tspan>
  </text>

  <!-- ==================== THREE COLUMN OUTLINES (ON TOP) ==================== -->
  <rect x="70" y="165" width="460" height="715" rx="16" fill="none" stroke="#207448" stroke-width="2.5"/>
  <!-- Column 2 Card: Orange outline as the deep dive that punishes breadth -->
  <rect x="570" y="165" width="460" height="715" rx="16" fill="none" stroke="#db8129" stroke-width="4"/>
  <rect x="1070" y="165" width="460" height="715" rx="16" fill="none" stroke="#207448" stroke-width="2.5"/>

  <!-- ==================== BOTTOM NOTE / TAKEAWAY BAR ==================== -->
  <g id="bottom-takeaway">
    <rect x="70" y="910" width="1460" height="76" rx="12" fill="#207448"/>
    <text x="800" y="956" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Would they trust you with a pager and a production fleet?</text>
  </g>
</svg>"""
    return svg

if __name__ == "__main__":
    s = create_svg()
    with open("candidate_round_shapes.svg", "w") as f:
        f.write(s)
    print("Saved candidate_round_shapes.svg")
