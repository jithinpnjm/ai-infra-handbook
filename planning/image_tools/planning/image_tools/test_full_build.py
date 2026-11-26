import xml.etree.ElementTree as ET
import re

# Let's test the complete SVG generation with exact geometry

def generate_svg():
    W = 1600
    H = 1200
    BG = "#f5f8f5"
    TEXT = "#303a36"
    GREEN = "#207448"
    PANEL_BG = "#e8f1ea"
    ORANGE = "#db8129"
    WHITE = "#ffffff"

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>The GPU diagnostics CLI in four layers, with exit codes</title>')
    svg.append('  <desc>Visual infographic explaining the four layers of the GPU diagnostics CLI: cli.py, collect.py, parsers.py, rules.py, with models.py, exit codes, and test strip.</desc>')
    
    # Defs
    svg.append('  <defs>')
    # Marker
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')

    # 56px Outline Icons
    # Icon 1: Terminal / CLI
    svg.append('    <g id="icon-cli" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="48" height="44" rx="6" fill="#ffffff" />')
    svg.append('      <line x1="4" y1="18" x2="52" y2="18" />')
    svg.append('      <circle cx="11" cy="12" r="2" fill="#207448" />')
    svg.append('      <circle cx="17" cy="12" r="2" fill="#207448" />')
    svg.append('      <path d="M 14 28 L 22 34 L 14 40" />')
    svg.append('      <line x1="26" y1="40" x2="38" y2="40" />')
    svg.append('    </g>')

    # Icon 2: Collect / Host
    svg.append('    <g id="icon-collect" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="8" width="44" height="18" rx="4" fill="#ffffff" />')
    svg.append('      <rect x="6" y="30" width="44" height="18" rx="4" fill="#ffffff" />')
    svg.append('      <circle cx="14" cy="17" r="2.5" fill="#207448" />')
    svg.append('      <line x1="22" y1="17" x2="42" y2="17" />')
    svg.append('      <circle cx="14" cy="39" r="2.5" fill="#207448" />')
    svg.append('      <line x1="22" y1="39" x2="42" y2="39" />')
    svg.append('    </g>')

    # Icon 3: Parsers / Pure transformation
    svg.append('    <g id="icon-parser" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="6" width="44" height="44" rx="6" fill="#ffffff" />')
    svg.append('      <path d="M 18 18 L 12 28 L 18 38" />')
    svg.append('      <path d="M 38 18 L 44 28 L 38 38" />')
    svg.append('      <line x1="30" y1="16" x2="26" y2="40" />')
    svg.append('    </g>')

    # Icon 4: Rules / Evaluation shield
    svg.append('    <g id="icon-rules" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 48 14 L 48 28 C 48 40 28 50 28 50 C 28 50 8 40 8 28 L 8 14 Z" fill="#ffffff" />')
    svg.append('      <path d="M 20 28 L 26 34 L 38 20" />')
    svg.append('    </g>')

    # Icon 5: Models / Cube
    svg.append('    <g id="icon-models" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polygon points="28,6 50,18 50,42 28,52 6,42 6,18" fill="#ffffff" />')
    svg.append('      <line x1="28" y1="6" x2="28" y2="52" />')
    svg.append('      <line x1="6" y1="18" x2="28" y2="30" />')
    svg.append('      <line x1="50" y1="18" x2="28" y2="30" />')
    svg.append('    </g>')

    # Icon 6: Exit codes
    svg.append('    <g id="icon-exit" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="6" width="40" height="44" rx="5" fill="#ffffff" />')
    svg.append('      <line x1="16" y1="18" x2="38" y2="18" />')
    svg.append('      <line x1="16" y1="28" x2="38" y2="28" />')
    svg.append('      <line x1="16" y1="38" x2="32" y2="38" />')
    svg.append('    </g>')

    # Icon 7: Test strip
    svg.append('    <g id="icon-test" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 22 6 L 34 6" />')
    svg.append('      <line x1="28" y1="6" x2="28" y2="18" />')
    svg.append('      <path d="M 22 18 L 10 44 C 8 48 11 52 16 52 L 40 52 C 45 52 48 48 46 44 L 34 18 Z" fill="#ffffff" />')
    svg.append('      <line x1="16" y1="38" x2="40" y2="38" />')
    svg.append('    </g>')

    # Icon 8: Bottom bar
    svg.append('    <g id="icon-key" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="18" cy="28" r="12" fill="#ffffff" />')
    svg.append('      <circle cx="18" cy="28" r="4" fill="#207448" />')
    svg.append('      <line x1="30" y1="28" x2="50" y2="28" />')
    svg.append('      <line x1="42" y1="28" x2="42" y2="36" />')
    svg.append('      <line x1="48" y1="28" x2="48" y2="34" />')
    svg.append('    </g>')

    svg.append('  </defs>')

    # Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="{BG}" />')

    # Title
    svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">The GPU diagnostics CLI in four layers, </tspan>')
    svg.append('    <tspan x="800" dy="54">with exit codes</tspan>')
    svg.append('  </text>')

    return "\n".join(svg)

print("Generator skeleton ready")
