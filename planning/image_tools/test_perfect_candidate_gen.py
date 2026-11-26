#!/usr/bin/env python3
import pathlib
import re
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

def generate_svg():
    svg_parts = []
    svg_parts.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg_parts.append('  <title>DNSSEC chain of trust, and the other DNS security controls</title>')
    svg_parts.append('  <desc>Visual infographic explaining the DNSSEC authentication chain from root trust anchor to the answer, validating resolver behavior, and a table of DNS threats and controls.</desc>')
    svg_parts.append('  <defs>')
    svg_parts.append('    <marker id="arrow-green" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse">')
    svg_parts.append('      <path d="M 1 2 L 11 6 L 1 10 z" fill="#207448" />')
    svg_parts.append('    </marker>')
    svg_parts.append('    <marker id="arrow-orange" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse">')
    svg_parts.append('      <path d="M 1 2 L 11 6 L 1 10 z" fill="#db8129" />')
    svg_parts.append('    </marker>')
    svg_parts.append('  </defs>')
    svg_parts.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    
    # Title (48px bold)
    svg_parts.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">DNSSEC chain of trust, and the other DNS security controls</text>')
    
    # Left panel (x=40, y=95, w=740, h=970)
    svg_parts.append('  <rect x="40" y="95" width="740" height="970" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Left Chain Nodes:
    # x = 65, w = 395 (x: 65 .. 460)
    chain_nodes = [
        {
            "id": "node1", "label": "Root trust anchor", "fs": 30, "bold": True,
            "x": 65, "y": 115, "w": 395, "h": 72, "base_y": 160,
            "lines": [("Root trust anchor", 0)], "icon": "anchor"
        },
        {
            "id": "node2", "label": "DS record in the root for com", "fs": 24, "bold": False,
            "x": 65, "y": 207, "w": 395, "h": 96, "base_y": 248,
            "lines": [("DS record in the root", 0), ("for com", 30)], "icon": "hash"
        },
        {
            "id": "node3", "label": "com zone DNSKEY", "fs": 30, "bold": True,
            "x": 65, "y": 323, "w": 395, "h": 72, "base_y": 368,
            "lines": [("com zone DNSKEY", 0)], "icon": "key"
        },
        {
            "id": "node4", "label": "DS record for example.com published by the parent", "fs": 24, "bold": False,
            "x": 65, "y": 415, "w": 395, "h": 126, "base_y": 455,
            "lines": [("DS record for", 0), ("example.com published", 30), ("by the parent", 30)], "icon": "hash"
        },
        {
            "id": "node5", "label": "example.com zone DNSKEY", "fs": 30, "bold": True,
            "x": 65, "y": 561, "w": 395, "h": 108, "base_y": 606,
            "lines": [("example.com zone", 0), ("DNSKEY", 38)], "icon": "key"
        },
        {
            "id": "node6", "label": "RRSIG over each RRset", "fs": 24, "bold": False,
            "x": 65, "y": 689, "w": 395, "h": 68, "base_y": 730,
            "lines": [("RRSIG over each RRset", 0)], "icon": "sig"
        },
        {
            "id": "node7", "label": "the answer", "fs": 30, "bold": True,
            "x": 65, "y": 777, "w": 395, "h": 72, "base_y": 822,
            "lines": [("the answer", 0)], "icon": "doc"
        }
    ]
    
    for nd in chain_nodes:
        x, y, w, h = nd["x"], nd["y"], nd["w"], nd["h"]
        fs, bold = nd["fs"], nd["bold"]
        weight = "bold" if bold else "normal"
        svg_parts.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
        
        # Icon (size 34x34) at x=78
        iy = y + (h - 34)//2
        svg_parts.append(f'  <g transform="translate(78, {iy})">')
        if nd["icon"] == "anchor":
            svg_parts.append('    <circle cx="17" cy="8" r="5" fill="none" stroke="#207448" stroke-width="2.5" />')
            svg_parts.append('    <line x1="17" y1="13" x2="17" y2="28" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
            svg_parts.append('    <line x1="9" y1="17" x2="25" y2="17" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
            svg_parts.append('    <path d="M 5 22 C 8 32, 26 32, 29 22" fill="none" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
        elif nd["icon"] == "hash":
            svg_parts.append('    <line x1="12" y1="5" x2="9" y2="29" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
            svg_parts.append('    <line x1="22" y1="5" x2="19" y2="29" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
            svg_parts.append('    <line x1="5" y1="12" x2="27" y2="12" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
            svg_parts.append('    <line x1="4" y1="22" x2="26" y2="22" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
        elif nd["icon"] == "key":
            svg_parts.append('    <circle cx="12" cy="14" r="7" fill="none" stroke="#207448" stroke-width="2.5" />')
            svg_parts.append('    <line x1="18" y1="18" x2="29" y2="27" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
            svg_parts.append('    <line x1="24" y1="23" x2="27" y2="20" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
            svg_parts.append('    <line x1="27" y1="25" x2="30" y2="22" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
        elif nd["icon"] == "sig":
            svg_parts.append('    <circle cx="17" cy="15" r="10" fill="none" stroke="#207448" stroke-width="2.5" />')
            svg_parts.append('    <path d="M 12 25 L 14 31 L 17 28 L 20 31 L 22 25" fill="none" stroke="#207448" stroke-width="2" stroke-linejoin="round" />')
            svg_parts.append('    <path d="M 12 15 L 16 19 L 23 11" fill="none" stroke="#207448" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />')
        elif nd["icon"] == "doc":
            svg_parts.append('    <rect x="5" y="3" width="24" height="28" rx="3" fill="none" stroke="#207448" stroke-width="2.5" />')
            svg_parts.append('    <path d="M 10 15 L 15 20 L 24 10" fill="none" stroke="#207448" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />')
        svg_parts.append('  </g>')
        
        # Text
        by = nd["base_y"]
        svg_parts.append(f'  <text x="124" y="{by}" font-family="sans-serif" font-size="{fs}" font-weight="{weight}" fill="#303a36">')
        for l_idx, (line_str, dy) in enumerate(nd["lines"]):
            svg_parts.append(f'    <tspan x="124" dy="{dy}">{line_str}</tspan>')
        svg_parts.append('  </text>')

    # 6 arrows between chain nodes (straight vertical)
    for i in range(len(chain_nodes) - 1):
        y1 = chain_nodes[i]["y"] + chain_nodes[i]["h"]
        y2 = chain_nodes[i+1]["y"]
        svg_parts.append(f'  <line x1="260" y1="{y1}" x2="260" y2="{y2}" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')

    # Validating resolver side elements
    # Container / area: x = 485 to 755 (w = 270)
    # Inspection bus alongside chain links at x = 472
    svg_parts.append('  <!-- Validating resolver side inspection bus -->')
    svg_parts.append('  <path d="M 460 197 L 472 197 M 460 313 L 472 313 M 460 405 L 472 405 M 460 551 L 472 551 M 460 679 L 472 679 M 460 767 L 472 767" stroke="#207448" stroke-width="2" />')
    svg_parts.append('  <line x1="472" y1="197" x2="472" y2="767" stroke="#207448" stroke-width="2" />')
    
    # SERVFAIL on failure box (orange): x=485, y=435, w=270, h=92
    # Arrow from bus at y=481 to x=485 (orange)
    svg_parts.append('  <path d="M 472 481 L 483 481" stroke="#db8129" stroke-width="3" marker-end="url(#arrow-orange)" />')
    svg_parts.append('  <g stroke="currentColor" color="#db8129">')
    svg_parts.append('    <rect x="485" y="435" width="270" height="92" rx="12" fill="#fff7f0" stroke-width="3" />')
    svg_parts.append('    <g transform="translate(502, 464)" fill="none" stroke-width="2.5">')
    svg_parts.append('      <path d="M 17 3 L 32 29 L 2 29 Z" stroke-linejoin="round" />')
    svg_parts.append('      <line x1="17" y1="13" x2="17" y2="20" stroke-linecap="round" />')
    svg_parts.append('      <circle cx="17" cy="24" r="1.5" fill="currentColor" stroke="none" />')
    svg_parts.append('    </g>')
    svg_parts.append('  </g>')
    svg_parts.append('  <text x="548" y="473" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">')
    svg_parts.append('    <tspan x="548" dy="0">SERVFAIL on</tspan>')
    svg_parts.append('    <tspan x="548" dy="28">failure</tspan>')
    svg_parts.append('  </text>')
    
    # ad flag on verified answers box (green): x=485, y=745, w=270, h=92
    # Arrow from bus at y=767 to x=485 (green)
    svg_parts.append('  <path d="M 472 767 L 483 767" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')
    svg_parts.append('  <rect x="485" y="745" width="270" height="92" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg_parts.append('  <g transform="translate(502, 774)">')
    svg_parts.append('    <path d="M 17 3 L 30 8 L 30 18 C 30 25 17 30 17 30 C 17 30 4 25 4 18 L 4 8 Z" fill="none" stroke="#207448" stroke-width="2.5" stroke-linejoin="round" />')
    svg_parts.append('    <path d="M 10 16 L 15 20 L 24 11" fill="none" stroke="#207448" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />')
    svg_parts.append('  </g>')
    svg_parts.append('  <text x="548" y="783" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
    svg_parts.append('    <tspan x="548" dy="0">ad flag on</tspan>')
    svg_parts.append('    <tspan x="548" dy="28">verified answers</tspan>')
    svg_parts.append('  </text>')

    # Note at bottom of left panel:
    # x = 65, y = 872, w = 690, h = 176
    svg_parts.append('  <rect x="65" y="872" width="690" height="176" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg_parts.append('  <g transform="translate(85, 940)">')
    svg_parts.append('    <circle cx="18" cy="18" r="14" fill="none" stroke="#207448" stroke-width="2.5" />')
    svg_parts.append('    <line x1="18" y1="16" x2="18" y2="25" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
    svg_parts.append('    <circle cx="18" cy="11" r="2" fill="#207448" />')
    svg_parts.append('  </g>')
    svg_parts.append('  <text x="135" y="910" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg_parts.append('    <tspan x="135" dy="0">DNSSEC does not encrypt anything;</tspan>')
    svg_parts.append('    <tspan x="135" dy="26">expired signatures or DS and key mismatches</tspan>')
    svg_parts.append('    <tspan x="135" dy="26">during a rollover cause outages for validating</tspan>')
    svg_parts.append('    <tspan x="135" dy="26">users; automate signing and rollovers</tspan>')
    svg_parts.append('  </text>')

    # Right panel: Table 'Threat to control'
    # x = 820, y = 95, w = 740, h = 970
    svg_parts.append('  <rect x="820" y="95" width="740" height="970" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Table Title: 'Threat to control'
    svg_parts.append('  <g transform="translate(845, 112)">')
    svg_parts.append('    <rect x="0" y="0" width="40" height="40" rx="6" fill="none" stroke="#207448" stroke-width="2.5" />')
    svg_parts.append('    <line x1="0" y1="14" x2="40" y2="14" stroke="#207448" stroke-width="2" />')
    svg_parts.append('    <line x1="14" y1="14" x2="14" y2="40" stroke="#207448" stroke-width="2" />')
    svg_parts.append('  </g>')
    svg_parts.append('  <text x="898" y="142" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Threat to control</text>')
    
    # Table rows:
    # 7 rows + optional
    # Threat rect: x = 845, w = 252
    # Control rect: x = 1107, w = 428 (ends at 1535)
    table_data = [
        (
            ["Forged answers,", "cache poisoning"], 24, True,
            ["DNSSEC, source-port and", "query-ID randomisation"], 24, False,
            88
        ),
        (
            ["Open resolvers,", "amplification", "DDoS"], 24, True,
            ["restrict recursion to your own", "networks, rate-limit responses"], 24, False,
            114
        ),
        (
            ["DNS tunnelling", "exfiltrating data"], 24, True,
            ["monitor volume, long labels", "and TXT records"], 24, False,
            88
        ),
        (
            ["Dangling CNAMEs"], 24, True,
            ["subdomain takeover,", "clean up records"], 24, False,
            88
        ),
        (
            ["DNS rebinding"], 24, True,
            ["filter private answers"], 24, False,
            64
        ),
        (
            ["Zone data"], 24, True,
            [
                "restrict AXFR to secondaries and",
                "authenticate with TSIG; keep",
                "authoritative and recursive roles",
                "on separate servers"
            ], 24, False,
            140
        ),
        (
            ["Untrusted", "network hop"], 24, True,
            [
                "DoT over TCP/853 and DoH over",
                "HTTPS encrypt the stub to resolver",
                "hop; mostly unnecessary inside",
                "a data centre"
            ], 24, False,
            140
        )
    ]
    
    cur_ry = 160
    gap_r = 8
    for t_lines, t_fs, t_bold, c_lines, c_fs, c_bold, rh in table_data:
        # Threat box: x=845, w=252
        svg_parts.append(f'  <rect x="845" y="{cur_ry}" width="252" height="{rh}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
        # Control box: x=1107, w=428
        svg_parts.append(f'  <rect x="1107" y="{cur_ry}" width="428" height="{rh}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
        
        # Threat text
        if len(t_lines) == 1:
            t_base_y = cur_ry + 41 + (rh - 64)//2
        else:
            t_base_y = cur_ry + 37 + (rh - (37 + (len(t_lines)-1)*26 + 18))//2
        t_weight = "bold" if t_bold else "normal"
        svg_parts.append(f'  <text x="865" y="{t_base_y}" font-family="sans-serif" font-size="{t_fs}" font-weight="{t_weight}" fill="#303a36">')
        for l_idx, line_s in enumerate(t_lines):
            dy = 0 if l_idx == 0 else 26
            svg_parts.append(f'    <tspan x="865" dy="{dy}">{line_s}</tspan>')
        svg_parts.append('  </text>')
        
        # Control text
        if len(c_lines) == 1:
            c_base_y = cur_ry + 41 + (rh - 64)//2
        else:
            c_base_y = cur_ry + 37 + (rh - (37 + (len(c_lines)-1)*26 + 18))//2
        c_weight = "bold" if c_bold else "normal"
        svg_parts.append(f'  <text x="1125" y="{c_base_y}" font-family="sans-serif" font-size="{c_fs}" font-weight="{c_weight}" fill="#303a36">')
        for l_idx, line_s in enumerate(c_lines):
            dy = 0 if l_idx == 0 else 26
            svg_parts.append(f'    <tspan x="1125" dy="{dy}">{line_s}</tspan>')
        svg_parts.append('  </text>')
        
        cur_ry += rh + gap_r

    # Optional row: 'RPZ response policy zones or provider threat-blocking'
    # Full-width card: x=845, w=690, h=88
    svg_parts.append(f'  <rect x="845" y="{cur_ry}" width="690" height="{88}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" stroke-dasharray="6 4" />')
    svg_parts.append(f'  <g transform="translate(865, {cur_ry + 27})">')
    svg_parts.append('    <path d="M 17 3 L 30 8 L 30 18 C 30 25 17 30 17 30 C 17 30 4 25 4 18 L 4 8 Z" fill="none" stroke="#207448" stroke-width="2.5" />')
    svg_parts.append('  </g>')
    svg_parts.append(f'  <text x="915" y="{cur_ry + 39}" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg_parts.append(f'    <tspan x="915" dy="0">RPZ response policy zones or</tspan>')
    svg_parts.append(f'    <tspan x="915" dy="26">provider threat-blocking</tspan>')
    svg_parts.append('  </text>')

    # Bottom takeaway bar: 'Restrict who can use each resolver before you open it to a network'
    # x=40, y=1100, w=1520, h=62
    svg_parts.append('  <rect x="40" y="1100" width="1520" height="62" rx="10" fill="#207448" />')
    svg_parts.append('  <text x="800" y="1139" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Restrict who can use each resolver before you open it to a network</text>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)

svg_text = generate_svg()
pathlib.Path("test_candidate_refined.svg").write_text(svg_text)
print("Updated test_candidate_refined.svg")
