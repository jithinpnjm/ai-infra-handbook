#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

W = 1600
H = 1200

lines = []
lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
lines.append('  <title>Investigation commands from cheapest to most targeted</title>')
lines.append('  <desc>Visual ladder of Ansible investigation commands arranged from cheapest parse-only checks to targeted ad hoc commands, with a warning that start-at-task skips earlier set_fact tasks.</desc>')

# Background Canvas
lines.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')

# Title (48px bold, centered)
lines.append('  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Investigation commands from cheapest to most targeted</text>')

row_data = [
    {"type": "full",
     "cmd": "--syntax-check",
     "note": " (parse only, touches no host)",
     "icon": "parse"},
    {"type": "full",
     "cmd": "--list-tasks --list-tags --list-hosts",
     "note": "",
     "icon": "list"},
    {"type": "full",
     "cmd": "--check --diff --limit gpu001",
     "note": " (what would change)",
     "icon": "diff"},
    {"type": "full",
     "cmd": "--step",
     "note": " (confirm every task y/n/c)",
     "icon": "step"},
    {"type": "split",
     "cmd": "--start-at-task Install driver",
     "warn_l1": "it skips earlier set_fact so the driver ",
     "warn_l2": "task fails on an undefined variable",
     "icon": "start"},
    {"type": "full",
     "cmd": "-t config -l gpu001",
     "note": "",
     "icon": "tag"},
    {"type": "adhoc_setup",
     "prefix": "ad hoc ",
     "cmd": "setup with filter=ansible_default_ipv4",
     "icon": "setup"},
    {"type": "adhoc_cmd",
     "prefix": "ad hoc command ",
     "cmd": "which python3 with -vvv",
     "icon": "adhoc"}
]

def render_icon(icon_type, x, y, stroke_color="#207448"):
    if icon_type == "parse":
        # Document with checkmark (parse only)
        return f'''<g transform="translate({x}, {y})" stroke="{stroke_color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 8 4 L 30 4 L 42 16 L 42 44 L 8 44 Z" />
    <polyline points="30,4 30,16 42,16" />
    <polyline points="15,28 22,35 34,21" />
  </g>'''
    elif icon_type == "list":
        # Bullet list with lines
        return f'''<g transform="translate({x}, {y})" stroke="{stroke_color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="10" cy="12" r="2" fill="{stroke_color}" />
    <line x1="20" y1="12" x2="42" y2="12" />
    <circle cx="10" cy="24" r="2" fill="{stroke_color}" />
    <line x1="20" y1="24" x2="42" y2="24" />
    <circle cx="10" cy="36" r="2" fill="{stroke_color}" />
    <line x1="20" y1="36" x2="42" y2="36" />
  </g>'''
    elif icon_type == "diff":
        # Two overlapping sheets / diff
        return f'''<g transform="translate({x}, {y})" stroke="{stroke_color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="6" y="10" width="22" height="32" rx="3" />
    <path d="M 20 10 L 20 4 L 34 4 L 42 12 L 42 34 L 28 34" />
    <line x1="12" y1="20" x2="22" y2="20" />
    <line x1="12" y1="28" x2="22" y2="28" />
  </g>'''
    elif icon_type == "step":
        # Interactive step / question prompt
        return f'''<g transform="translate({x}, {y})" stroke="{stroke_color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="6" y="8" width="36" height="32" rx="4" />
    <polyline points="14,24 20,30 32,18" />
  </g>'''
    elif icon_type == "start":
        # Flag marker for start-at-task
        return f'''<g transform="translate({x}, {y})" stroke="{stroke_color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <line x1="10" y1="6" x2="10" y2="44" />
    <path d="M 10 8 L 38 18 L 10 28 Z" fill="#e8f1ea" />
  </g>'''
    elif icon_type == "tag":
        # Tag icon for -t config -l gpu001
        return f'''<g transform="translate({x}, {y})" stroke="{stroke_color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 8 24 L 24 8 L 40 8 L 40 24 L 24 40 Z" />
    <circle cx="32" cy="16" r="3" fill="{stroke_color}" />
  </g>'''
    elif icon_type == "setup":
        # Device / network probe for ad hoc setup
        return f'''<g transform="translate({x}, {y})" stroke="{stroke_color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="6" y="10" width="36" height="24" rx="3" />
    <line x1="14" y1="34" x2="14" y2="40" />
    <line x1="34" y1="34" x2="34" y2="40" />
    <line x1="6" y1="40" x2="42" y2="40" />
    <circle cx="16" cy="22" r="2" fill="{stroke_color}" />
    <circle cx="26" cy="22" r="2" fill="{stroke_color}" />
  </g>'''
    elif icon_type == "adhoc":
        # Terminal prompt >_ for ad hoc command
        return f'''<g transform="translate({x}, {y})" stroke="{stroke_color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="6" y="8" width="36" height="32" rx="4" />
    <polyline points="13,18 20,24 13,30" />
    <line x1="24" y1="30" x2="33" y2="30" />
  </g>'''
    elif icon_type == "warning":
        # Warning triangle
        return f'''<g transform="translate({x}, {y})" stroke="{stroke_color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="24,6 44,42 4,42" />
    <line x1="24" y1="18" x2="24" y2="28" />
    <circle cx="24" cy="35" r="2" fill="{stroke_color}" />
  </g>'''
    return ""

y_current = 112
box_h = 94
gap_y = 40

for idx, r in enumerate(row_data):
    if r["type"] == "full":
        # Full width box: x=50, w=1500, h=94
        lines.append(f'  <rect x="50" y="{y_current}" width="1500" height="{box_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
        lines.append(f'  {render_icon(r["icon"], 75, y_current + 23)}')
        y_text = y_current + 57
        if r["note"]:
            lines.append(f'  <text x="145" y="{y_text}" font-size="30" fill="#303a36"><tspan font-family="monospace" font-weight="bold">{r["cmd"]}</tspan><tspan font-family="sans-serif" font-weight="normal" font-size="24">{r["note"]}</tspan></text>')
        else:
            lines.append(f'  <text x="145" y="{y_text}" font-family="monospace" font-size="30" font-weight="bold" fill="#303a36">{r["cmd"]}</text>')
            
    elif r["type"] == "split":
        # Split row: Step 5 on left (w=730), Warning box on right (w=730)
        lines.append(f'  <rect x="50" y="{y_current}" width="730" height="{box_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
        lines.append(f'  {render_icon(r["icon"], 75, y_current + 23)}')
        y_text = y_current + 57
        lines.append(f'  <text x="145" y="{y_text}" font-family="monospace" font-size="30" font-weight="bold" fill="#303a36">{r["cmd"]}</text>')
        
        # Right box: Warning Box (Orange highlight)
        lines.append(f'  <rect x="820" y="{y_current}" width="730" height="{box_h}" rx="12" fill="#fffaf5" stroke="#db8129" stroke-width="2.5" />')
        lines.append(f'  {render_icon("warning", 840, y_current + 23, stroke_color="#db8129")}')
        y_warn = y_current + 39
        lines.append(f'  <text x="905" y="{y_warn}" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="905" dy="0">{r["warn_l1"]}</tspan><tspan x="905" dy="28">{r["warn_l2"]}</tspan></text>')

    elif r["type"] == "adhoc_setup":
        lines.append(f'  <rect x="50" y="{y_current}" width="1500" height="{box_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
        lines.append(f'  {render_icon(r["icon"], 75, y_current + 23)}')
        y_text = y_current + 57
        lines.append(f'  <text x="145" y="{y_text}" font-size="30" fill="#303a36"><tspan font-family="sans-serif" font-weight="bold">{r["prefix"]}</tspan><tspan font-family="monospace" font-weight="bold">{r["cmd"]}</tspan></text>')

    elif r["type"] == "adhoc_cmd":
        lines.append(f'  <rect x="50" y="{y_current}" width="1500" height="{box_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
        lines.append(f'  {render_icon(r["icon"], 75, y_current + 23)}')
        y_text = y_current + 57
        lines.append(f'  <text x="145" y="{y_text}" font-size="30" fill="#303a36"><tspan font-family="sans-serif" font-weight="bold">{r["prefix"]}</tspan><tspan font-family="monospace" font-weight="bold">{r["cmd"]}</tspan></text>')

    y_current += box_h + gap_y

lines.append('</svg>')

svg_content = "\n".join(lines)
with open("investigation_ladder.svg", "w") as f:
    f.write(svg_content)

print(f"Generated investigation_ladder.svg ({len(svg_content)} bytes)")
