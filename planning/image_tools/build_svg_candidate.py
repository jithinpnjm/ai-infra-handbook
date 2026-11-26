import pathlib
import re
import subprocess
import xml.etree.ElementTree as ET

def generate_svg():
    W = 1600
    H = 1180

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>The two queues behind listen(): where a busy server drops connections</title>')
    svg.append('  <desc>Visual explanation of the SYN queue and Accept queue in Linux TCP listen(), packet flow, failure callouts, and fixes.</desc>')
    
    # Defs: arrow marker
    svg.append('  <defs>')
    svg.append('    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">')
    svg.append('      <path d="M 0 1 L 10 5 L 0 9 z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')

    # Background
    svg.append(f'  <rect x="0" y="0" width="{W}" height="{H}" fill="#f5f8f5" />')

    # Title (48px bold)
    title_text = "The two queues behind listen(): where a busy server drops connections"
    svg.append(f'  <text x="50" y="70" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">{title_text}</text>')

    # Bottom bar (25px bold)
    bar_y = 1080
    bar_h = 60
    svg.append(f'  <rect x="50" y="{bar_y}" width="1500" height="{bar_h}" rx="10" fill="#207448" />')
    svg.append(f'  <text x="800" y="{bar_y + 38}" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#ffffff">Check ListenOverflows before you change any setting</text>')

    return "\n".join(svg) + "\n</svg>"

svg_data = generate_svg()
pathlib.Path("test_candidate.svg").write_text(svg_data)
print("Initial draft written.")
