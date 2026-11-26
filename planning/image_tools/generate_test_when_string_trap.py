#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def create_svg():
    bg = "#f5f8f5"
    text_color = "#303a36"
    main_green = "#207448"
    panel_bg = "#e8f1ea"
    orange = "#db8129"
    card_bg = "#ffffff"
    card_stroke = "#207448"
    
    # We will build the SVG string
    # Canvas dimensions: 1600 x 980
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 980" width="1600" height="980">')
    svg.append('  <title>The string false trap in when</title>')
    svg.append('  <desc>Visual explanation of the Ansible string false trap in when conditionals and how the bool filter safely converts it to a real boolean false.</desc>')
    svg.append('  <rect width="1600" height="980" fill="#f5f8f5"/>')
    svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">The string false trap in when</text>')

    # ==================== LANE ONE (TRAP LANE) ====================
    # x=40, y=95, w=740, h=740
    svg.append('  <g id="lane-one">')
    svg.append('    <rect x="40" y="95" width="740" height="740" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')

    # Card 1: run with -e flag=false (x=68, y=120, w=684, h=150)
    svg.append('    <rect x="68" y="120" width="684" height="150" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Terminal icon (56px) at (92, 167)
    svg.append('    <g transform="translate(92, 167)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="2" y="6" width="52" height="44" rx="6"/>')
    svg.append('      <line x1="2" y1="18" x2="54" y2="18"/>')
    svg.append('      <path d="M 14 28 L 22 34 L 14 40"/>')
    svg.append('      <line x1="28" y1="40" x2="40" y2="40"/>')
    svg.append('    </g>')
    svg.append('    <text x="175" y="204" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36">run with -e flag=false</text>')

    # Card 2: the value arrives as the string false (x=68, y=298, w=684, h=150)
    svg.append('    <rect x="68" y="298" width="684" height="150" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Document / String Quotes icon (56px) at (92, 345)
    svg.append('    <g transform="translate(92, 345)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="4" width="44" height="48" rx="6"/>')
    svg.append('      <path d="M 18 22 A 4 4 0 0 1 22 18 V 28"/>')
    svg.append('      <path d="M 34 22 A 4 4 0 0 1 38 18 V 28"/>')
    svg.append('      <line x1="16" y1="38" x2="40" y2="38"/>')
    svg.append('    </g>')
    svg.append('    <text x="175" y="362" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="175" dy="0">the value arrives as</tspan>')
    svg.append('      <tspan x="175" dy="38">the string false</tspan>')
    svg.append('    </text>')

    # Card 3: when: flag treats a non-empty string as true (x=68, y=476, w=684, h=150)
    svg.append('    <rect x="68" y="476" width="684" height="150" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Decision diamond icon (56px) at (92, 523)
    svg.append('    <g transform="translate(92, 523)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 4 L 52 28 L 28 52 L 4 28 Z"/>')
    svg.append('      <path d="M 20 28 L 26 34 L 38 20"/>')
    svg.append('    </g>')
    svg.append('    <text x="175" y="540" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="175" dy="0">when: flag treats a</tspan>')
    svg.append('      <tspan x="175" dy="38">non-empty string as true</tspan>')
    svg.append('    </text>')

    # Card 4: task runs when it should skip (x=68, y=654, w=684, h=150)
    svg.append('    <rect x="68" y="654" width="684" height="150" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Warning shield / alert gear icon (56px) at (92, 701)
    svg.append('    <g transform="translate(92, 701)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="22"/>')
    svg.append('      <line x1="28" y1="16" x2="28" y2="30"/>')
    svg.append('      <circle cx="28" cy="38" r="2" fill="#207448" stroke="none"/>')
    svg.append('    </g>')
    svg.append('    <text x="175" y="718" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="175" dy="0">task runs when it</tspan>')
    svg.append('      <tspan x="175" dy="38">should skip</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== LANE TWO (FIX LANE - ORANGE HIGHLIGHT) ====================
    # x=820, y=95, w=740, h=740
    svg.append('  <g id="lane-two">')
    svg.append('    <rect x="820" y="95" width="740" height="740" rx="16" fill="#fffaf5" stroke="#db8129" stroke-width="3"/>')

    # Card 1: fix with when: flag | bool (x=848, y=120, w=684, h=200)
    svg.append('    <rect x="848" y="120" width="684" height="200" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="2"/>')
    # Wrench / Tool filter icon (56px) at (872, 192) in orange
    svg.append('    <g transform="translate(872, 192)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 38 6 A 14 14 0 0 0 24 20 L 8 36 A 6 6 0 0 0 16 44 L 32 28 A 14 14 0 0 0 46 14 Z"/>')
    svg.append('      <circle cx="38" cy="14" r="3" fill="#db8129"/>')
    svg.append('    </g>')
    svg.append('    <text x="955" y="210" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="955" dy="0">fix with</tspan>')
    svg.append('      <tspan x="955" dy="38" font-family="monospace">when: flag | bool</tspan>')
    svg.append('    </text>')

    # Card 2: string false becomes boolean false (x=848, y=365, w=684, h=200)
    svg.append('    <rect x="848" y="365" width="684" height="200" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Transform / Conversion icon (56px) at (872, 437)
    svg.append('    <g transform="translate(872, 437)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="10" width="20" height="36" rx="4"/>')
    svg.append('      <rect x="32" y="10" width="20" height="36" rx="4"/>')
    svg.append('      <path d="M 24 24 L 30 28 L 24 32"/>')
    svg.append('    </g>')
    svg.append('    <text x="955" y="455" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="955" dy="0">string false becomes</tspan>')
    svg.append('      <tspan x="955" dy="38">boolean false</tspan>')
    svg.append('    </text>')

    # Card 3: task skips (x=848, y=610, w=684, h=194)
    svg.append('    <rect x="848" y="610" width="684" height="194" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Fast-forward / Skip icon (56px) at (872, 679)
    svg.append('    <g transform="translate(872, 679)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polygon points="10,14 28,28 10,42" fill="#e8f1ea"/>')
    svg.append('      <polygon points="28,14 46,28 28,42" fill="#e8f1ea"/>')
    svg.append('    </g>')
    svg.append('    <text x="955" y="718" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">task skips</text>')
    svg.append('  </g>')

    # ==================== FOOTER TAKEAWAY BAR ====================
    # x=40, y=865, w=1520, h=80
    svg.append('  <g id="footer-takeaway">')
    svg.append('    <rect x="40" y="865" width="1520" height="80" rx="12" fill="#207448"/>')
    # Small key / note icon (40px) at x=65, y=885
    svg.append('    <g transform="translate(68, 885)" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="16" cy="16" r="10"/>')
    svg.append('      <line x1="23" y1="23" x2="36" y2="36"/>')
    svg.append('      <line x1="31" y1="31" x2="36" y2="26"/>')
    svg.append('    </g>')
    svg.append('    <text x="800" y="915" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#ffffff">write the bare expression when: var, not when: &quot;{{ var }}&quot;</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return '\n'.join(svg)

with open("test_when_string_trap.svg", "w") as f:
    f.write(create_svg())
print("Wrote test_when_string_trap.svg")
