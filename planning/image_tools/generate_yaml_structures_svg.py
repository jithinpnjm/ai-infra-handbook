#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def build_perfect_svg():
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    lines.append('  <title>The three YAML structures, read through the cluster example</title>')
    lines.append('  <desc>Visual infographic explaining the three YAML data structures—scalars, sequences, and mappings—using an annotated cluster manifest alongside syntax rules, JSON equivalents, and parser behaviors.</desc>')
    lines.append('')
    lines.append('  <!-- Background Canvas -->')
    lines.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    lines.append('')
    lines.append('  <!-- ==================== TITLE (48px bold) ==================== -->')
    lines.append('  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    lines.append('    <tspan x="800" dy="0">The three YAML structures, </tspan>')
    lines.append('    <tspan x="800" dy="54">read through the cluster example</tspan>')
    lines.append('  </text>')
    lines.append('')
    lines.append('  <!-- ==================== LEFT COLUMN: ANNOTATED FILE ==================== -->')
    lines.append('  <!-- Outer Container (x=40, y=140, w=780, h=920) -->')
    lines.append('  <rect x="40" y="140" width="780" height="920" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    lines.append('')
    lines.append('  <!-- File / Document Outline Icon (56x56 px, stroke 4, green) -->')
    lines.append('  <g transform="translate(68, 148)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <path d="M 10 4 L 36 4 L 48 16 L 48 50 L 10 50 Z M 36 4 L 36 16 L 48 16" fill="#ffffff"/>')
    lines.append('    <line x1="18" y1="26" x2="40" y2="26"/>')
    lines.append('    <line x1="18" y1="34" x2="34" y2="34"/>')
    lines.append('    <line x1="18" y1="42" x2="38" y2="42"/>')
    lines.append('  </g>')
    lines.append('')
    lines.append('  <!-- Inner Code Canvas (x=64, y=208, w=732, h=832) -->')
    lines.append('  <rect x="64" y="208" width="732" height="832" rx="10" fill="#ffffff" stroke="#cfded2" stroke-width="1.5"/>')
    lines.append('')
    lines.append('  <!-- Code Gutter / Margin Indicator Line -->')
    lines.append('  <line x1="86" y1="208" x2="86" y2="1040" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('')
    lines.append('  <!-- Visual Structure Guides / Indentation Rails -->')
    lines.append('  <line x1="108" y1="345" x2="108" y2="980" stroke="#e8f1ea" stroke-width="2" stroke-dasharray="4 4"/>')
    lines.append('  <line x1="132" y1="540" x2="132" y2="680" stroke="#e8f1ea" stroke-width="2" stroke-dasharray="4 4"/>')
    lines.append('')
    lines.append('  <!-- YAML Code Lines -->')

    left_items = [
        ("---", 258, 90, "#f5f8f5", True),
        ("cluster:", 322, 90, "#e8f1ea", False),
        ("name: ai-prod-1", 386, 114, "#ffffff", False),
        ("racks: [r1, r2, r3]", 450, 114, "#ffffff", False),
        ("nodes:", 514, 114, "#e8f1ea", False),
        ("name: gpu01, gpus: 8, tags: [h100, nvlink]", 578, 138, "#ffffff", False),
        ("name: gpu02, gpus: 8, tags: - h100", 642, 138, "#ffffff", False),
        ("motd: |", 706, 114, "#ffffff", False),
        ("description: >", 770, 114, "#ffffff", False),
        ("enabled: true", 834, 114, "#ffffff", False),
        ("contact: null", 898, 114, "#ffffff", False),
        ("...", 962, 90, "#f5f8f5", True)
    ]

    for text_val, y_pos, x_indent, bg_col, is_dashed in left_items:
        char_w = len(text_val) * 24 * 0.62
        rect_x = x_indent - 18
        rect_w = int(char_w + 36)
        dash_attr = ' stroke-dasharray="4 3"' if is_dashed else ''
        lines.append(f'  <rect x="{rect_x}" y="{y_pos - 34}" width="{rect_w}" height="52" rx="6" fill="{bg_col}" stroke="#cfded2" stroke-width="1"{dash_attr}/>')
        escaped_val = text_val.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        lines.append(f'  <text x="{x_indent}" y="{y_pos}" font-family="monospace" font-size="24" fill="#303a36">{escaped_val}</text>')

    lines.append('')
    lines.append('  <!-- ==================== RIGHT COLUMN: TABLE & NOTES ==================== -->')
    lines.append('  <!-- ==================== TOP RIGHT: STRUCTURE TABLE ==================== -->')
    lines.append('  <rect x="860" y="140" width="700" height="420" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    lines.append('')
    lines.append('  <!-- Table Icon (56x56 px, stroke 4, green) -->')
    lines.append('  <g transform="translate(884, 148)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="4" y="6" width="48" height="42" rx="6" fill="#ffffff"/>')
    lines.append('    <line x1="4" y1="20" x2="52" y2="20"/>')
    lines.append('    <line x1="20" y1="6" x2="20" y2="48"/>')
    lines.append('    <line x1="36" y1="6" x2="36" y2="48"/>')
    lines.append('  </g>')
    lines.append('')
    lines.append('  <!-- Table Column Headers Bar (28px bold) -->')
    lines.append('  <rect x="880" y="198" width="660" height="56" rx="6" fill="#207448"/>')
    lines.append('  <text x="898" y="236" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Structure</text>')
    lines.append('  <text x="1070" y="236" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Syntax</text>')
    lines.append('  <text x="1270" y="236" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">JSON or Python</text>')
    lines.append('')

    # Table Row 1: Scalar
    lines.append('  <!-- Row 1: Scalar -->')
    lines.append('  <rect x="880" y="264" width="660" height="84" rx="8" fill="#ffffff" stroke="#cfded2" stroke-width="1.5"/>')
    lines.append('  <text x="898" y="296" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="898" dy="0" font-weight="bold" fill="#207448">Scalar: </tspan>')
    lines.append('    <tspan font-family="monospace">42, 3.14, true, null, hello, </tspan>')
    lines.append('    <tspan x="898" dy="34">&quot;quoted&quot; / number, bool, null, string</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Table Row 2: Sequence
    lines.append('  <!-- Row 2: Sequence -->')
    lines.append('  <rect x="880" y="356" width="660" height="84" rx="8" fill="#ffffff" stroke="#cfded2" stroke-width="1.5"/>')
    lines.append('  <text x="898" y="388" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="898" dy="0" font-weight="bold" fill="#207448">Sequence: </tspan>')
    lines.append('    <tspan font-family="monospace">- item per line, or [a, b] </tspan>')
    lines.append('    <tspan x="898" dy="34" fill="#606c66">/ array or list</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Table Row 3: Mapping
    lines.append('  <!-- Row 3: Mapping -->')
    lines.append('  <rect x="880" y="448" width="660" height="84" rx="8" fill="#ffffff" stroke="#cfded2" stroke-width="1.5"/>')
    lines.append('  <text x="898" y="480" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="898" dy="0" font-weight="bold" fill="#207448">Mapping: </tspan>')
    lines.append('    <tspan font-family="monospace">key: value pairs, or </tspan>')
    lines.append('    <tspan x="898" dy="34">{a: 1, b: 2} / object or dict</tspan>')
    lines.append('  </text>')
    lines.append('')

    # ==================== BOTTOM RIGHT: NOTES PANEL ====================
    lines.append('  <!-- ==================== BOTTOM RIGHT: NOTES PANEL ==================== -->')
    lines.append('  <rect x="860" y="600" width="700" height="460" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    lines.append('')
    lines.append('  <!-- Notes Gear / Filing Tray Icon (56x56 px, stroke 4, green) -->')
    lines.append('  <g transform="translate(884, 608)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="6" y="16" width="44" height="30" rx="6" fill="#ffffff"/>')
    lines.append('    <path d="M 6 28 L 22 28 L 26 34 L 38 34 L 42 28 L 50 28"/>')
    lines.append('    <line x1="16" y1="8" x2="40" y2="8"/>')
    lines.append('    <line x1="20" y1="12" x2="36" y2="12"/>')
    lines.append('  </g>')
    lines.append('')

    # Note 1: ORANGE HIGHLIGHT (the single most important item)
    lines.append('  <!-- Note 1 (orange highlight: the single most important item) -->')
    lines.append('  <rect x="880" y="664" width="660" height="140" rx="8" fill="#fff9f2" stroke="#db8129" stroke-width="2.5"/>')
    lines.append('  <text x="898" y="696" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="898" dy="0">a parser turns each value into a typed </tspan>')
    lines.append('    <tspan x="898" dy="28">object before any tool reads it: the </tspan>')
    lines.append('    <tspan x="898" dy="28">clerk at a counter files each word as </tspan>')
    lines.append('    <tspan x="898" dy="28">number, true or false, or text</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Note 2: JSON is valid YAML 1.2
    lines.append('  <!-- Note 2: JSON is valid YAML 1.2 -->')
    lines.append('  <rect x="880" y="816" width="660" height="80" rx="8" fill="#ffffff" stroke="#cfded2" stroke-width="1.5"/>')
    lines.append('  <text x="898" y="848" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="898" dy="0">JSON is valid YAML 1.2, so {&quot;a&quot;: 1} </tspan>')
    lines.append('    <tspan x="898" dy="30">works anywhere YAML does</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Note 3: Indentation
    lines.append('  <!-- Note 3: Indentation rules -->')
    lines.append('  <rect x="880" y="908" width="660" height="132" rx="8" fill="#ffffff" stroke="#cfded2" stroke-width="1.5"/>')
    lines.append('  <text x="898" y="938" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="898" dy="0">indentation tells the parser where each </tspan>')
    lines.append('    <tspan x="898" dy="28">item ends, brackets do the same for short </tspan>')
    lines.append('    <tspan x="898" dy="28">lists; pick the form a reviewer reads </tspan>')
    lines.append('    <tspan x="898" dy="28">fastest and keep it consistent in each file</tspan>')
    lines.append('  </text>')
    lines.append('')

    # ==================== BOTTOM TAKEAWAY BAR ====================
    lines.append('  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->')
    lines.append('  <rect x="40" y="1100" width="1520" height="60" rx="10" fill="#207448"/>')
    lines.append('  <text x="800" y="1140" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Read the file the way the parser reads it</text>')
    lines.append('')
    lines.append('</svg>')

    return '\n'.join(lines)

if __name__ == '__main__':
    svg_code = build_perfect_svg()
    with open('test_yaml_structures.svg', 'w') as f:
        f.write(svg_code)
    print("Regenerated test_yaml_structures.svg")