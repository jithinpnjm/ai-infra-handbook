#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def generate_svg():
    W = 1600
    H = 1100

    # Colors
    bg = "#f5f8f5"
    text_color = "#303a36"
    main_green = "#207448"
    panel_bg = "#e8f1ea"
    orange = "#db8129"
    card_bg = "#ffffff"
    card_stroke = "#207448"

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>Holding the driver and kernel so a routine upgrade cannot move them</title>')
    svg.append('  <desc>Infographic explaining how dpkg_selections holds the NVIDIA driver and kernel packages together on Debian-family hosts to prevent routine upgrades from breaking compatibility, comparing pinning options.</desc>')
    svg.append('')
    svg.append('  <!-- Canvas Background -->')
    svg.append(f'  <rect width="{W}" height="{H}" fill="{bg}" />')
    svg.append('')

    # Title: 48px bold
    svg.append('  <!-- Canvas Title (48px bold) -->')
    svg.append(f'  <text x="800" y="66" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="{text_color}">')
    svg.append('    <tspan x="800" dy="0" font-size="48">Holding the driver and kernel </tspan>')
    svg.append('    <tspan x="800" dy="56" font-size="48">so a routine upgrade cannot move them</tspan>')
    svg.append('  </text>')
    svg.append('')

    # Story Card (The Incident / Scenario) - ORANGE
    # y = 160, h = 110, w = 1520, x = 40
    svg.append('  <!-- ==================== STORY: THE INCIDENT (ORANGE HIGHLIGHT) ==================== -->')
    svg.append('  <g id="story-card">')
    svg.append(f'    <rect x="40" y="160" width="1520" height="110" rx="14" fill="#fffaf5" stroke="{orange}" stroke-width="3" />')
    # Incident / Alert Outline Icon (56px) at (65, 187)
    svg.append(f'    <g transform="translate(65, 187)" stroke="{orange}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polygon points="28,6 52,48 4,48" />')
    svg.append('      <line x1="28" y1="20" x2="28" y2="34" />')
    svg.append('      <circle cx="28" cy="41" r="2" fill="' + orange + '" />')
    svg.append('    </g>')
    # Story text: font-size 26 bold
    svg.append(f'    <text x="145" y="206" font-family="sans-serif" font-size="26" font-weight="bold" fill="{text_color}">')
    svg.append('      <tspan x="145" dy="0" font-size="26">a Tuesday morning when the package manager upgrades the kernel </tspan>')
    svg.append('      <tspan x="145" dy="38" font-size="26">on half the nodes and the NVIDIA driver no longer matches the new kernel</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Section 2: Fix Task and Notes Panel
    # y = 310, h = 330, w = 1520, x = 40
    svg.append('  <!-- ==================== FIX TASK AND NOTES PANEL ==================== -->')
    svg.append('  <g id="fix-task-panel">')
    svg.append(f'    <rect x="40" y="310" width="1520" height="330" rx="14" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')
    
    # Fix Task Card: x = 65, y = 335, w = 1470, h = 155
    svg.append(f'    <rect x="65" y="335" width="1470" height="155" rx="10" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    # Lock / Hold outline icon (56px) at (85, 385)
    svg.append(f'    <g transform="translate(85, 385)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="10" y="22" width="36" height="28" rx="5" />')
    svg.append('      <path d="M 18 22 V 14 A 10 10 0 0 1 38 14 V 22" />')
    svg.append('      <circle cx="28" cy="34" r="3" fill="' + main_green + '" />')
    svg.append('      <line x1="28" y1="37" x2="28" y2="43" />')
    svg.append('    </g>')
    # Fix Task Code Text: monospace font-size 24
    svg.append(f'    <text x="165" y="382" font-family="monospace" font-size="24" fill="{text_color}">')
    svg.append('      <tspan x="165" dy="0" font-size="24">dpkg_selections: name {{ item }}, selection hold, </tspan>')
    svg.append('      <tspan x="165" dy="36" font-size="24">loop [nvidia-driver-550, linux-image-generic], </tspan>')
    svg.append('      <tspan x="165" dy="36" font-size="24">when ansible_facts[os_family] == Debian</tspan>')
    svg.append('    </text>')

    # Note 1 Card: x = 65, y = 510, w = 920, h = 110
    svg.append(f'    <rect x="65" y="510" width="920" height="110" rx="10" fill="{card_bg}" stroke="{card_stroke}" stroke-width="1.5" />')
    # Shield / Filter outline icon (56px) at (85, 537)
    svg.append(f'    <g transform="translate(85, 537)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 48 14 V 28 C 48 40 28 50 28 50 C 28 50 8 40 8 28 V 14 Z" />')
    svg.append('      <polyline points="20,26 26,32 36,20" />')
    svg.append('    </g>')
    # Note 1 text: sans-serif font-size 24
    svg.append(f'    <text x="165" y="556" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append('      <tspan x="165" dy="0" font-size="24">when keeps the task away from RedHat-family hosts, </tspan>')
    svg.append('      <tspan x="165" dy="34" font-size="24">which need a different tool for the same job</tspan>')
    svg.append('    </text>')

    # Note 2 Card: x = 1025, y = 510, w = 510, h = 110
    svg.append(f'    <rect x="1025" y="510" width="510" height="110" rx="10" fill="{card_bg}" stroke="{card_stroke}" stroke-width="1.5" />')
    # Inspect / Magnifier outline icon (56px) at (1045, 537)
    svg.append(f'    <g transform="translate(1045, 537)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="24" cy="24" r="14" />')
    svg.append('      <line x1="34" y1="34" x2="48" y2="48" />')
    svg.append('      <line x1="16" y1="24" x2="32" y2="24" />')
    svg.append('      <line x1="24" y1="16" x2="24" y2="32" />')
    svg.append('    </g>')
    # Note 2 text: sans-serif font-size 24
    svg.append(f'    <text x="1125" y="556" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append('      <tspan x="1125" dy="0" font-size="24">package_facts inspects </tspan>')
    svg.append('      <tspan x="1125" dy="34" font-size="24">installed packages</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Section 3: Pinning Options Table
    # y = 680, h = 270, w = 1520, x = 40
    svg.append('  <!-- ==================== PINNING OPTIONS TABLE ==================== -->')
    svg.append('  <g id="pinning-options-table">')
    svg.append(f'    <rect x="40" y="680" width="1520" height="270" rx="14" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')

    # Row 1: selection: hold: package cannot be moved by a routine upgrade
    # y = 700, h = 70, w = 1470, x = 65
    svg.append(f'    <rect x="65" y="700" width="1470" height="70" rx="8" fill="{card_bg}" stroke="{card_stroke}" stroke-width="1.5" />')
    # Pin / Anchor outline icon (56px) at (85, 707)
    svg.append(f'    <g transform="translate(85, 707)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="18" r="8" />')
    svg.append('      <line x1="28" y1="26" x2="28" y2="48" />')
    svg.append('      <line x1="16" y1="36" x2="40" y2="36" />')
    svg.append('    </g>')
    svg.append(f'    <text x="165" y="743" font-family="sans-serif" font-size="25" fill="{text_color}">')
    svg.append(f'      <tspan font-family="monospace" font-weight="bold" fill="{main_green}" font-size="25">selection: hold:</tspan> package cannot be moved by a routine upgrade')
    svg.append('    </text>')

    # Row 2: pinned version with state present: name nvidia-driver-550=550.90.07-1
    # y = 780, h = 70, w = 1470, x = 65
    svg.append(f'    <rect x="65" y="780" width="1470" height="70" rx="8" fill="{card_bg}" stroke="{card_stroke}" stroke-width="1.5" />')
    # Tag / Version outline icon (56px) at (85, 787)
    svg.append(f'    <g transform="translate(85, 787)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 12 12 L 28 12 L 44 28 L 28 44 L 12 28 Z" />')
    svg.append('      <circle cx="20" cy="20" r="3" fill="' + main_green + '" />')
    svg.append('    </g>')
    svg.append(f'    <text x="165" y="823" font-family="sans-serif" font-size="25" fill="{text_color}">')
    svg.append(f'      pinned version with state present: <tspan font-family="monospace" font-weight="bold" fill="{main_green}" font-size="25">name nvidia-driver-550=550.90.07-1</tspan>')
    svg.append('    </text>')

    # Row 3: state: latest allows the upgrade
    # y = 860, h = 70, w = 1470, x = 65
    svg.append(f'    <rect x="65" y="860" width="1470" height="70" rx="8" fill="{card_bg}" stroke="{card_stroke}" stroke-width="1.5" />')
    # Upgrade / Cycle outline icon (56px) at (85, 867)
    svg.append(f'    <g transform="translate(85, 867)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 12 A 16 16 0 1 1 14 28" />')
    svg.append('      <polyline points="28,4 28,12 36,12" />')
    svg.append('      <line x1="28" y1="28" x2="28" y2="38" />')
    svg.append('      <polyline points="22,32 28,26 34,32" />')
    svg.append('    </g>')
    svg.append(f'    <text x="165" y="903" font-family="sans-serif" font-size="25" fill="{text_color}">')
    svg.append(f'      <tspan font-family="monospace" font-weight="bold" fill="{main_green}" font-size="25">state: latest</tspan> allows the upgrade')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Section 4: Bottom Bar (Takeaway)
    # y = 990, h = 60, w = 1520, x = 40
    svg.append('  <!-- ==================== BOTTOM BAR: TAKEAWAY ==================== -->')
    svg.append(f'  <rect x="40" y="990" width="1520" height="60" rx="10" fill="{main_green}" />')
    svg.append(f'  <text x="800" y="1028" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#ffffff">Hold the packages that must move together</text>')
    svg.append('</svg>')

    return '\n'.join(svg)

if __name__ == '__main__':
    with open('test_holding_driver.svg', 'w') as f:
        f.write(generate_svg())
    print('Generated test_holding_driver.svg successfully.')
