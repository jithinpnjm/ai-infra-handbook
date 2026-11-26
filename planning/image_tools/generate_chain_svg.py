import re
import xml.etree.ElementTree as ET
import subprocess
import pathlib

def build_svg():
    H = 950
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>A filter chain is a conveyor belt: each filter changes the value once</title>')
    svg.append('  <desc>Visual infographic explaining how a Jinja2 filter chain processes node records step by step like a conveyor belt, selecting nodes, extracting names, and joining them.</desc>')
    svg.append('  <defs>')
    # 18px proportional green arrowhead marker
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')

    # Main Canvas Title: 48px bold
    svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">A filter chain is a conveyor belt: </tspan>')
    svg.append('    <tspan x="800" dy="56">each filter changes the value once</tspan>')
    svg.append('  </text>')

    # =========================================================================
    # Conveyor Belt Assembly (Background structure)
    # Belt runs horizontally across the canvas: x=40..1560, y=565..605
    # =========================================================================
    svg.append('  <!-- Conveyor Belt Assembly -->')
    svg.append('  <g id="conveyor-belt">')
    # Belt bed
    svg.append('    <rect x="40" y="565" width="1520" height="40" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Belt rollers underneath
    for rx in range(80, 1530, 95):
        svg.append(f'    <circle cx="{rx}" cy="615" r="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
        svg.append(f'    <circle cx="{rx}" cy="615" r="4" fill="#207448" />')
    
    # Left & right end pulleys
    svg.append('    <circle cx="55" cy="585" r="22" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    svg.append('    <circle cx="55" cy="585" r="7" fill="#207448" />')
    svg.append('    <circle cx="1545" cy="585" r="22" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    svg.append('    <circle cx="1545" cy="585" r="7" fill="#207448" />')
    svg.append('  </g>')

    # =========================================================================
    # Stations 1, 2, 3 (Filter machines overhead)
    # y = 165 to 455 (height = 290)
    # =========================================================================
    
    # Station 1: x = 330, width = 295
    svg.append('  <!-- Station 1 -->')
    svg.append('  <g id="station-1">')
    svg.append('    <rect x="330" y="165" width="295" height="290" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    # Filter / funnel outline icon (56px) centered at cx = 477, y = 185..241
    svg.append('    <g transform="translate(449, 185)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polygon points="4,4 52,4 34,28 34,50 22,50 22,28" />')
    svg.append('      <line x1="12" y1="12" x2="44" y2="12" />')
    svg.append('    </g>')
    # Label: 'selectattr(gpus, ge, 8): keep nodes with 8 or more GPUs'
    svg.append('    <text x="477" y="280" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="477" dy="0" font-family="monospace">selectattr(</tspan><tspan x="477" dy="32" font-family="monospace">gpus, ge, 8): </tspan><tspan x="477" dy="34">keep nodes with </tspan><tspan x="477" dy="32">8 or more GPUs</tspan></text>')
    # Downward drop arrow into output payload (ends exactly at y=495)
    svg.append('    <line x1="477" y1="455" x2="477" y2="495" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />')
    svg.append('  </g>')

    # Station 2: x = 670, width = 295
    svg.append('  <!-- Station 2 -->')
    svg.append('  <g id="station-2">')
    svg.append('    <rect x="670" y="165" width="295" height="290" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    # Extract / tag outline icon (56px) centered at cx = 817, y = 185..241
    svg.append('    <g transform="translate(789, 185)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 6 24 L 24 6 L 48 6 L 48 30 L 30 48 Z" />')
    svg.append('      <circle cx="38" cy="16" r="4" fill="#207448" />')
    svg.append('    </g>')
    # Label: 'map(attribute=name): pull out the name of each node'
    svg.append('    <text x="817" y="280" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="817" dy="0" font-family="monospace">map(</tspan><tspan x="817" dy="32" font-family="monospace">attribute=name): </tspan><tspan x="817" dy="34">pull out the name </tspan><tspan x="817" dy="32">of each node</tspan></text>')
    # Downward drop arrow into output payload (ends exactly at y=495)
    svg.append('    <line x1="817" y1="455" x2="817" y2="495" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />')
    svg.append('  </g>')

    # Station 3: x = 1010, width = 295 (ORANGE OUTLINE!)
    svg.append('  <!-- Station 3 (Orange Outline) -->')
    svg.append('  <g id="station-3">')
    svg.append('    <rect x="1010" y="165" width="295" height="290" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
    # Glue / link outline icon (56px) centered at cx = 1157, y = 185..241
    svg.append('    <g transform="translate(1129, 185)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 18 28 A 12 12 0 0 1 30 16 L 38 16 A 12 12 0 0 1 50 28 A 12 12 0 0 1 38 40 L 30 40" />')
    svg.append('      <path d="M 38 28 A 12 12 0 0 1 26 40 L 18 40 A 12 12 0 0 1 6 28 A 12 12 0 0 1 18 16 L 26 16" />')
    svg.append('    </g>')
    # Label: 'join(,): glue the names with commas'
    svg.append('    <text x="1157" y="290" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="1157" dy="0" font-family="monospace">join(,): </tspan><tspan x="1157" dy="36">glue the names </tspan><tspan x="1157" dy="34">with commas</tspan></text>')
    # Downward drop arrow into output payload (ends exactly at y=495)
    svg.append('    <line x1="1157" y1="455" x2="1157" y2="495" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />')
    svg.append('  </g>')

    # =========================================================================
    # Conveyor Belt Items / Payloads (Sitting on belt at y = 495..565)
    # =========================================================================
    
    # 1. Input at far left: x = 40, y = 440, width = 245, height = 125
    svg.append('  <!-- Input Box -->')
    svg.append('  <g id="input-box">')
    svg.append('    <rect x="40" y="440" width="245" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # 3 rows inside input box
    svg.append('    <text x="162" y="475" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">gpu01 gpus 8</text>')
    svg.append('    <text x="162" y="512" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">gpu02 gpus 8</text>')
    svg.append('    <text x="162" y="549" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">login01 gpus 0</text>')
    # Conveyor flow arrow from Input to Station 1 output (ends exactly at x=352)
    svg.append('    <line x1="285" y1="530" x2="352" y2="530" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />')
    svg.append('  </g>')

    # 2. Output beneath Station 1: x = 352, y = 495, width = 250, height = 70
    svg.append('  <!-- Station 1 Output Payload -->')
    svg.append('  <g id="output-station-1">')
    svg.append('    <rect x="352" y="495" width="250" height="70" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="477" y="539" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">gpu01, gpu02</text>')
    # Flow arrow to Station 2 (ends exactly at x=692)
    svg.append('    <line x1="602" y1="530" x2="692" y2="530" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />')
    svg.append('  </g>')

    # 3. Output beneath Station 2: x = 692, y = 495, width = 250, height = 70
    svg.append('  <!-- Station 2 Output Payload -->')
    svg.append('  <g id="output-station-2">')
    svg.append('    <rect x="692" y="495" width="250" height="70" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="817" y="539" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">gpu01, gpu02</text>')
    # Flow arrow to Station 3 (ends exactly at x=1032)
    svg.append('    <line x1="942" y1="530" x2="1032" y2="530" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />')
    svg.append('  </g>')

    # 4. Output beneath Station 3: x = 1032, y = 495, width = 250, height = 70
    svg.append('  <!-- Station 3 Output Payload -->')
    svg.append('  <g id="output-station-3">')
    svg.append('    <rect x="1032" y="495" width="250" height="70" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1157" y="539" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">gpu01,gpu02</text>')
    # Flow arrow to final Output box (ends exactly at x=1350)
    svg.append('    <line x1="1282" y1="530" x2="1350" y2="530" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />')
    svg.append('  </g>')

    # 5. Output at far right: x = 1350, y = 475, width = 210, height = 90
    svg.append('  <!-- Output Box at Far Right -->')
    svg.append('  <g id="output-box-far-right">')
    svg.append('    <rect x="1350" y="475" width="210" height="90" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <text x="1455" y="530" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">gpu01,gpu02</text>')
    svg.append('  </g>')

    # =========================================================================
    # Grey Note Under The Belt: x=100..1500 (w=1400, h=90, y=685..775)
    # =========================================================================
    svg.append('  <!-- Grey Note Under Belt -->')
    svg.append('  <g id="grey-note">')
    svg.append('    <rect x="100" y="685" width="1400" height="90" rx="12" fill="#ffffff" stroke="#9aa8a0" stroke-width="2" />')
    # Info circle outline icon
    svg.append('    <g transform="translate(130, 708)" stroke="#7a8c82" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="22" cy="22" r="20" />')
    svg.append('      <line x1="22" y1="20" x2="22" y2="31" />')
    svg.append('      <circle cx="22" cy="13" r="1.5" fill="#7a8c82" />')
    svg.append('    </g>')
    # Text: 'If the first filter keeps nothing, later filters receive an empty list and the output is an empty string.'
    svg.append('    <text x="190" y="727" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="190" dy="0">If the first filter keeps nothing, later filters receive an empty list </tspan>')
    svg.append('      <tspan x="190" dy="32">and the output is an empty string.</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # =========================================================================
    # Caption / Takeaway Bar: x=40..1560 (w=1520, h=70, y=835..905)
    # =========================================================================
    svg.append('  <!-- Takeaway Bar -->')
    svg.append('  <g id="takeaway-bar">')
    svg.append('    <rect x="40" y="835" width="1520" height="70" rx="12" fill="#207448" />')
    svg.append('    <text x="800" y="879" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Read a filter chain left to right, one change at a time.</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return "\n".join(svg)

res = build_svg()
pathlib.Path("test_output.svg").write_text(res)
print("Updated test_output.svg successfully")
