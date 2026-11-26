#!/usr/bin/env python3
import re, subprocess, pathlib
import xml.etree.ElementTree as ET

def build_svg():
    H = 1200
    
    # Participant definitions
    # 5 lanes across 1600 width:
    # Margins: 50 px left and right.
    # 5 boxes of 260 px width, 4 gaps of 50 px.
    # Lane centers: U=180, C=490, DBD=800, D1=1110, D2=1420.
    
    centers = {
        "U": 180,
        "C": 490,
        "DBD": 800,
        "D1": 1110,
        "D2": 1420
    }
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>The life of a job</title>')
    svg.append('  <desc>Sequence diagram illustrating the lifecycle of a Slurm batch job from submission to completion across login node, controller, database daemon, and compute nodes.</desc>')
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-green-left" viewBox="0 0 18 18" refX="2" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 16 3 L 2 9 L 16 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5"/>')
    
    # Title
    svg.append('  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">The life of a job</text>')
    
    # Participant headers: y = 75 to 180 (height 105)
    headers = [
        {"id": "U", "x": 50, "cx": 180, "title": ["User on", "login node"], "icon": "user"},
        {"id": "C", "x": 360, "cx": 490, "title": ["slurmctld"], "icon": "gear"},
        {"id": "DBD", "x": 670, "cx": 800, "title": ["slurmdbd"], "icon": "db"},
        {"id": "D1", "x": 980, "cx": 1110, "title": ["slurmd on", "node A"], "icon": "chip"},
        {"id": "D2", "x": 1290, "cx": 1420, "title": ["slurmd on", "node B"], "icon": "chip"}
    ]
    
    for h in headers:
        bx = h["x"]
        bw = 260
        cx = h["cx"]
        svg.append(f'  <g id="header-{h["id"]}">')
        svg.append(f'    <rect x="{bx}" y="75" width="{bw}" height="105" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
        
        # Icon
        if h["icon"] == "user":
            svg.append(f'    <g transform="translate({cx - 95}, 90)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="0" y="0" width="46" height="34" rx="4"/>')
            svg.append('      <path d="M 23 34 v 10 M 11 44 h 24"/>')
            svg.append('      <path d="M 8 13 l 7 5 -7 5 M 22 23 h 12"/>')
            svg.append('    </g>')
        elif h["icon"] == "gear":
            svg.append(f'    <g transform="translate({cx - 85}, 85)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <circle cx="24" cy="24" r="11"/>')
            svg.append('      <path d="M 24 3 v 6 M 24 39 v 6 M 3 24 h 6 M 39 24 h 6 M 9 9 l 5 5 M 34 34 l 5 5 M 9 39 l 5 -5 M 34 9 l 5 -5"/>')
            svg.append('    </g>')
        elif h["icon"] == "db":
            svg.append(f'    <g transform="translate({cx - 85}, 84)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <ellipse cx="24" cy="10" rx="20" ry="7"/>')
            svg.append('      <path d="M 4 10 v 26 c 0 4 9 7 20 7 s 20 -3 20 -7 v -26"/>')
            svg.append('      <path d="M 4 23 c 0 4 9 7 20 7 s 20 -3 20 -7"/>')
            svg.append('    </g>')
        elif h["icon"] == "chip":
            svg.append(f'    <g transform="translate({cx - 95}, 85)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="6" y="6" width="34" height="34" rx="4"/>')
            svg.append('      <rect x="15" y="15" width="16" height="16" rx="2"/>')
            svg.append('      <path d="M 17 0 v 6 M 29 0 v 6 M 17 40 v 6 M 29 40 v 6 M 0 17 h 6 M 0 29 h 6 M 40 17 h 6 M 40 29 h 6"/>')
            svg.append('    </g>')
            
        # Title text
        lines = h["title"]
        if len(lines) == 1:
            svg.append(f'    <text x="{bx + 90}" y="140" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">{lines[0]}</text>')
        else:
            svg.append(f'    <text x="{bx + 90}" y="122" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
            svg.append(f'      <tspan x="{bx + 90}" dy="0">{lines[0]}</tspan>')
            svg.append(f'      <tspan x="{bx + 90}" dy="34">{lines[1]}</tspan>')
            svg.append('    </text>')
            
        svg.append('  </g>')

    # Lifelines
    for h in headers:
        cx = h["cx"]
        svg.append(f'  <line x1="{cx}" y1="180" x2="{cx}" y2="1175" stroke="#b8c9c0" stroke-width="3" stroke-dasharray="8 6"/>')
        
    return "\n".join(svg) + "\n</svg>"

pathlib.Path("test_headers.svg").write_text(build_svg())
print("Saved test_headers.svg")
