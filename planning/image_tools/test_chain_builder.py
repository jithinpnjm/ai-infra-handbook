import re
import xml.etree.ElementTree as ET
import subprocess
import pathlib

def build_svg():
    H = 1050
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>A filter chain is a conveyor belt: each filter changes the value once</title>')
    svg.append('  <desc>Visual infographic explaining how a Jinja2 filter chain processes node records step by step like a conveyor belt, selecting nodes, extracting names, and joining them.</desc>')
    svg.append('  <defs>')
    # Arrow marker
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')

    # Title: 48px bold
    svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">A filter chain is a conveyor belt: </tspan>')
    svg.append('    <tspan x="800" dy="56">each filter changes the value once</tspan>')
    svg.append('  </text>')

    return "\n".join(svg) + "\n</svg>"

print("Builder scaffold ready")
