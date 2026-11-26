#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def build_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>IPv4 and IPv6 headers side by side: what moved, what went away</title>')
    svg.append('  <desc>Visual comparison of IPv4 and IPv6 header fields side by side showing what moved, what went away, simplified hardware parsing, and flexible extension headers.</desc>')
    
    # Defs: arrowheads
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append('  <!-- Background -->')
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    
    # Main Diagram Title (48px bold, centered)
    svg.append('  <!-- Diagram Title -->')
    svg.append('  <text x="800" y="44" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">IPv4 and IPv6 headers side by side: </tspan>')
    svg.append('    <tspan x="800" dy="52">what moved, what went away</tspan>')
    svg.append('  </text>')
    
    # Geometry constants
    col_w = 620
    col1_x = 40
    col2_x = 940
    col_y = 104
    col_h = 1008
    
    card_w = 584
    card1_x = 58
    card2_x = 958
    hdr_h = 80
    
    # Row definitions (10 rows)
    rows_data = [
        # 0: Version
        {
            "id": "row-version",
            "h": 62,
            "card4": {
                "text": ["Version 4"],
                "icon": "chip-v4"
            },
            "card6": {
                "text": ["Version 4 bits"],
                "icon": "chip-v6"
            }
        },
        # 1: DSCP / Traffic Class (Arrow: DSCP+ECN to Traffic Class)
        {
            "id": "row-traffic-class",
            "h": 68,
            "arrow": "DSCP+ECN to Traffic Class",
            "card4": {
                "text": ["DSCP (6 bits) and ECN (2 bits)"],
                "icon": "sliders"
            },
            "card6": {
                "text": ["Traffic Class 8 bits = DSCP 6 +", "ECN 2"],
                "icon": "priority"
            }
        },
        # 2: IHL / Flow Label
        {
            "id": "row-ihl-flow",
            "h": 90,
            "card4": {
                "text": ["IHL: header length in 32-bit", "words, 5 means 20 bytes"],
                "icon": "ruler"
            },
            "card6": {
                "text": ["Flow Label 20 bits: helps routers", "keep a flow on one path when ECMP", "spreads traffic"],
                "icon": "flow-label"
            }
        },
        # 3: Total Length / Payload Length
        {
            "id": "row-length",
            "h": 62,
            "card4": {
                "text": ["Total Length up to 65,535"],
                "icon": "arrows-expand"
            },
            "card6": {
                "text": ["Payload Length 16"],
                "icon": "box-parcel"
            }
        },
        # 4: Fragmentation (Crossed out on IPv6 in orange)
        {
            "id": "row-fragmentation",
            "h": 120,
            "card4": {
                "text": [
                    "Identification, Flags (DF, MF),",
                    "Fragment Offset: fragmentation",
                    "lives in the base header; routers",
                    "may fragment unless DF is set"
                ],
                "icon": "scissors"
            },
            "card6": {
                "text": [
                    "no fragmentation fields in the",
                    "base header: only the source host",
                    "may fragment, through an extension",
                    "header; routers never do"
                ],
                "icon": "ban-orange",
                "crossed": True
            }
        },
        # 5: TTL / Hop Limit (Arrow: TTL to Hop Limit)
        {
            "id": "row-ttl-hop",
            "h": 90,
            "arrow": "TTL to Hop Limit",
            "card4": {
                "text": [
                    "TTL: drops by one per router, at 0",
                    "the router drops the packet and",
                    "sends ICMP Time Exceeded"
                ],
                "icon": "clock-timer"
            },
            "card6": {
                "text": [
                    "Hop Limit 8: plays the role of the",
                    "TTL"
                ],
                "icon": "hourglass"
            }
        },
        # 6: Protocol / Next Header (Arrow: Protocol to Next Header)
        {
            "id": "row-protocol-next",
            "h": 120,
            "arrow": "Protocol to Next Header",
            "card4": {
                "text": [
                    "Protocol: 6 TCP, 17 UDP, 1 ICMP,",
                    "47 GRE, 50 ESP, 89 OSPF"
                ],
                "icon": "ports-list"
            },
            "card6": {
                "text": [
                    "Next Header 8: extension headers",
                    "chained (hop-by-hop, routing,",
                    "fragment, destination options, AH,",
                    "ESP)"
                ],
                "icon": "chain-links"
            }
        },
        # 7: Checksum (Crossed out on IPv6 in orange)
        {
            "id": "row-checksum",
            "h": 68,
            "card4": {
                "text": [
                    "Header checksum: recomputed at",
                    "every hop because the TTL changes"
                ],
                "icon": "sigma-calc"
            },
            "card6": {
                "text": [
                    "no header checksum (link and",
                    "transport layers cover errors)"
                ],
                "icon": "shield-cross-orange",
                "crossed": True
            }
        },
        # 8: Addresses
        {
            "id": "row-addresses",
            "h": 68,
            "card4": {
                "text": [
                    "source and destination 32-bit",
                    "addresses"
                ],
                "icon": "address-pin"
            },
            "card6": {
                "text": [
                    "source and destination 128-bit",
                    "addresses"
                ],
                "icon": "globe-network"
            }
        },
        # 9: Options (IPv4 only)
        {
            "id": "row-options",
            "h": 60,
            "card4": {
                "text": ["options (rare)"],
                "icon": "cog-wrench"
            },
            "card6": None
        }
    ]
    
    def render_icon(icon_name, ix, iy):
        shapes = []
        if icon_name == "chip-v4":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <rect x="4" y="4" width="38" height="38" rx="6"/>')
            shapes.append('  <path d="M 23 12 v 18 M 15 24 h 16 M 15 16 l 8 -4"/>')
            shapes.append('</g>')
        elif icon_name == "chip-v6":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <rect x="4" y="4" width="38" height="38" rx="6"/>')
            shapes.append('  <circle cx="23" cy="27" r="7"/>')
            shapes.append('  <path d="M 27 13 c -4 -2 -11 3 -11 14"/>')
            shapes.append('</g>')
        elif icon_name == "sliders":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round">')
            shapes.append('  <line x1="6" y1="13" x2="40" y2="13"/><circle cx="18" cy="13" r="4" fill="#e8f1ea"/>')
            shapes.append('  <line x1="6" y1="26" x2="40" y2="26"/><circle cx="30" cy="26" r="4" fill="#e8f1ea"/>')
            shapes.append('  <line x1="6" y1="39" x2="40" y2="39"/><circle cx="14" cy="39" r="4" fill="#e8f1ea"/>')
            shapes.append('</g>')
        elif icon_name == "priority":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <path d="M 6 38 L 18 10 L 30 26 L 40 16"/>')
            shapes.append('  <polyline points="32,16 40,16 40,24"/>')
            shapes.append('</g>')
        elif icon_name == "ruler":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <rect x="4" y="10" width="38" height="26" rx="4"/>')
            shapes.append('  <line x1="13" y1="10" x2="13" y2="20"/>')
            shapes.append('  <line x1="23" y1="10" x2="23" y2="26"/>')
            shapes.append('  <line x1="33" y1="10" x2="33" y2="20"/>')
            shapes.append('</g>')
        elif icon_name == "flow-label":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <path d="M 6 14 C 18 14 20 32 38 32"/>')
            shapes.append('  <path d="M 6 32 C 18 32 20 14 38 14"/>')
            shapes.append('  <polyline points="32,10 38,14 32,18"/>')
            shapes.append('  <polyline points="32,28 38,32 32,36"/>')
            shapes.append('</g>')
        elif icon_name == "arrows-expand":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <line x1="6" y1="23" x2="40" y2="23"/>')
            shapes.append('  <polyline points="14,15 6,23 14,31"/>')
            shapes.append('  <polyline points="32,15 40,23 32,31"/>')
            shapes.append('</g>')
        elif icon_name == "box-parcel":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <rect x="6" y="8" width="34" height="30" rx="4"/>')
            shapes.append('  <line x1="6" y1="18" x2="40" y2="18"/>')
            shapes.append('  <line x1="23" y1="18" x2="23" y2="38"/>')
            shapes.append('</g>')
        elif icon_name == "scissors":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <circle cx="12" cy="14" r="6"/>')
            shapes.append('  <circle cx="12" cy="32" r="6"/>')
            shapes.append('  <line x1="17" y1="17" x2="38" y2="35"/>')
            shapes.append('  <line x1="17" y1="29" x2="38" y2="11"/>')
            shapes.append('</g>')
        elif icon_name == "ban-orange":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#db8129" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <circle cx="23" cy="23" r="18"/>')
            shapes.append('  <line x1="10" y1="10" x2="36" y2="36"/>')
            shapes.append('</g>')
        elif icon_name == "clock-timer":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <circle cx="23" cy="23" r="18"/>')
            shapes.append('  <polyline points="23,12 23,23 32,23"/>')
            shapes.append('</g>')
        elif icon_name == "hourglass":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <path d="M 8 6 H 38 L 27 23 L 38 40 H 8 L 19 23 Z"/>')
            shapes.append('</g>')
        elif icon_name == "ports-list":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <rect x="6" y="6" width="34" height="34" rx="4"/>')
            shapes.append('  <line x1="14" y1="15" x2="32" y2="15"/>')
            shapes.append('  <line x1="14" y1="23" x2="32" y2="23"/>')
            shapes.append('  <line x1="14" y1="31" x2="26" y2="31"/>')
            shapes.append('</g>')
        elif icon_name == "chain-links":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <rect x="6" y="14" width="20" height="18" rx="6"/>')
            shapes.append('  <rect x="20" y="14" width="20" height="18" rx="6"/>')
            shapes.append('</g>')
        elif icon_name == "sigma-calc":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <rect x="6" y="6" width="34" height="34" rx="5"/>')
            shapes.append('  <path d="M 31 14 H 16 L 24 23 L 16 32 H 31"/>')
            shapes.append('</g>')
        elif icon_name == "shield-cross-orange":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#db8129" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <path d="M 23 5 L 39 12 V 22 C 39 33 23 41 23 41 C 23 41 7 33 7 22 V 12 Z"/>')
            shapes.append('  <line x1="15" y1="18" x2="31" y2="28"/>')
            shapes.append('  <line x1="31" y1="18" x2="15" y2="28"/>')
            shapes.append('</g>')
        elif icon_name == "address-pin":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <path d="M 23 6 C 15 6 10 12 10 19 C 10 28 23 41 23 41 C 23 41 36 28 36 19 C 36 12 31 6 23 6 Z"/>')
            shapes.append('  <circle cx="23" cy="18" r="4"/>')
            shapes.append('</g>')
        elif icon_name == "globe-network":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <circle cx="23" cy="23" r="18"/>')
            shapes.append('  <ellipse cx="23" cy="23" rx="8" ry="18"/>')
            shapes.append('  <line x1="5" y1="23" x2="41" y2="23"/>')
            shapes.append('</g>')
        elif icon_name == "cog-wrench":
            shapes.append(f'<g transform="translate({ix}, {iy})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
            shapes.append('  <circle cx="23" cy="23" r="10"/>')
            shapes.append('  <path d="M 23 5 v 6 M 23 35 v 6 M 5 23 h 6 M 35 23 h 6 M 10 10 l 4 4 M 32 32 l 4 4 M 10 36 l 4 -4 M 32 10 l 4 4"/>')
            shapes.append('</g>')
        return "\n".join(shapes)

    # 1. Left Column (IPv4)
    svg.append('  <!-- ==================== LEFT COLUMN: IPv4 ==================== -->')
    svg.append('  <g id="col-ipv4">')
    svg.append(f'    <rect x="{col1_x}" y="{col_y}" width="{col_w}" height="{col_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    svg.append(f'    <rect x="{card1_x}" y="{col_y + 12}" width="{card_w}" height="{hdr_h}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append(f'    <g transform="translate({card1_x + 14}, {col_y + 28})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="2" y="4" width="42" height="12" rx="3"/>')
    svg.append('      <rect x="2" y="19" width="42" height="12" rx="3"/>')
    svg.append('      <rect x="2" y="34" width="42" height="8" rx="2" stroke-dasharray="4 3"/>')
    svg.append('    </g>')
    svg.append('    <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    svg.append(f'      <tspan x="{card1_x + 72}" y="{col_y + 47}">IPv4 header, </tspan>')
    svg.append(f'      <tspan x="{card1_x + 72}" y="{col_y + 79}">20 bytes minimum</tspan>')
    svg.append('    </text>')

    cur_y = col_y + 12 + hdr_h + 8
    gap_y = 8
    arrows_to_render = []

    for r in rows_data:
        rh = r["h"]
        c4 = r["card4"]
        svg.append(f'    <!-- Card: {r["id"]}-v4 -->')
        svg.append(f'    <rect x="{card1_x}" y="{cur_y}" width="{card_w}" height="{rh}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
        icon_y = cur_y + (rh - 46) / 2
        svg.append(render_icon(c4["icon"], card1_x + 14, icon_y))
        
        lines4 = c4["text"]
        n_lines4 = len(lines4)
        line_step = 26 if n_lines4 >= 4 else 28
        total_span = (n_lines4 - 1) * line_step + 19.2
        rem_pad = rh - total_span
        pad_top = max(16.5, rem_pad / 2)
        start_y4 = cur_y + pad_top + 19.2
        
        svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
        for idx, line in enumerate(lines4):
            sep = " " if idx < n_lines4 - 1 else ""
            line_y = start_y4 + idx * line_step
            svg.append(f'      <tspan x="{card1_x + 72}" y="{line_y:.1f}">{line}{sep}</tspan>')
        svg.append('    </text>')
        
        if "arrow" in r:
            arrow_y = cur_y + rh / 2
            arrows_to_render.append((r["arrow"], arrow_y))
            
        cur_y += rh + gap_y
    svg.append('  </g>')

    # 2. Right Column (IPv6)
    svg.append('  <!-- ==================== RIGHT COLUMN: IPv6 ==================== -->')
    svg.append('  <g id="col-ipv6">')
    svg.append(f'    <rect x="{col2_x}" y="{col_y}" width="{col_w}" height="{col_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    svg.append(f'    <rect x="{card2_x}" y="{col_y + 12}" width="{card_w}" height="{hdr_h}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append(f'    <g transform="translate({card2_x + 14}, {col_y + 28})" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="2" y="4" width="42" height="16" rx="3"/>')
    svg.append('      <rect x="2" y="24" width="42" height="16" rx="3"/>')
    svg.append('      <line x1="12" y1="12" x2="34" y2="12"/>')
    svg.append('      <line x1="12" y1="32" x2="34" y2="32"/>')
    svg.append('    </g>')
    svg.append('    <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    svg.append(f'      <tspan x="{card2_x + 72}" y="{col_y + 47}">IPv6 header, </tspan>')
    svg.append(f'      <tspan x="{card2_x + 72}" y="{col_y + 79}">40 bytes fixed</tspan>')
    svg.append('    </text>')

    cur_y = col_y + 12 + hdr_h + 8
    for r in rows_data:
        rh = r["h"]
        c6 = r["card6"]
        if c6:
            is_crossed = c6.get("crossed", False)
            bg_fill = "#fef8f2" if is_crossed else "#ffffff"
            stroke_col = "#db8129" if is_crossed else "#207448"
            stroke_w = "2.2" if is_crossed else "1.8"
            text_fill = "#db8129" if is_crossed else "#303a36"
            
            svg.append(f'    <!-- Card: {r["id"]}-v6 -->')
            svg.append(f'    <rect x="{card2_x}" y="{cur_y}" width="{card_w}" height="{rh}" rx="8" fill="{bg_fill}" stroke="{stroke_col}" stroke-width="{stroke_w}"/>')
            
            icon_y6 = cur_y + (rh - 46) / 2
            svg.append(render_icon(c6["icon"], card2_x + 14, icon_y6))
            
            lines6 = c6["text"]
            n_lines6 = len(lines6)
            line_step6 = 26 if n_lines6 >= 4 else 28
            total_span6 = (n_lines6 - 1) * line_step6 + 19.2
            rem_pad6 = rh - total_span6
            pad_top6 = max(16.5, rem_pad6 / 2)
            start_y6 = cur_y + pad_top6 + 19.2
            
            svg.append(f'    <text font-family="sans-serif" font-size="24" fill="{text_fill}">')
            for idx, line in enumerate(lines6):
                sep = " " if idx < n_lines6 - 1 else ""
                line_y = start_y6 + idx * line_step6
                svg.append(f'      <tspan x="{card2_x + 72}" y="{line_y:.1f}">{line}{sep}</tspan>')
            svg.append('    </text>')
            
            if is_crossed:
                for idx in range(n_lines6):
                    line_y = start_y6 + idx * line_step6
                    line_len = len(lines6[idx]) * 14.4
                    svg.append(f'    <line x1="{card2_x + 70}" y1="{line_y - 7:.1f}" x2="{card2_x + 72 + line_len:.1f}" y2="{line_y - 7:.1f}" stroke="#db8129" stroke-width="2.2" opacity="0.85"/>')
        
        cur_y += rh + gap_y
    svg.append('  </g>')

    # 3. Corridor Arrows
    svg.append('  <!-- ==================== ARROWS BETWEEN COLUMNS ==================== -->')
    svg.append('  <g id="corridor-arrows">')
    for label, ay in arrows_to_render:
        svg.append(f'    <!-- Arrow: {label} -->')
        svg.append(f'    <line x1="645" y1="{ay:.1f}" x2="955" y2="{ay:.1f}" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)"/>')
        
        if label == "DSCP+ECN to Traffic Class":
            svg.append(f'    <text x="800" y="{ay - 22:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
            svg.append(f'      <tspan x="800" dy="0">DSCP+ECN to </tspan>')
            svg.append(f'      <tspan x="800" dy="28">Traffic Class</tspan>')
            svg.append('    </text>')
        elif label == "Protocol to Next Header":
            svg.append(f'    <text x="800" y="{ay - 22:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
            svg.append(f'      <tspan x="800" dy="0">Protocol to </tspan>')
            svg.append(f'      <tspan x="800" dy="28">Next Header</tspan>')
            svg.append('    </text>')
        else: # "TTL to Hop Limit"
            svg.append(f'    <text x="800" y="{ay - 10:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">{label}</text>')
    svg.append('  </g>')

    # 4. Bottom Takeaway Bar
    bar_y = 1124
    bar_h = 56
    svg.append('  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->')
    svg.append('  <g id="bottom-bar">')
    svg.append(f'    <rect x="40" y="{bar_y}" width="1520" height="{bar_h}" rx="12" fill="#207448"/>')
    svg.append(f'    <g transform="translate(65, {bar_y + 8})" fill="none" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 20 4 L 36 10 V 20 C 36 30 20 38 20 38 C 20 38 4 30 4 20 V 10 Z"/>')
    svg.append('      <polyline points="12,19 18,25 28,15"/>')
    svg.append('    </g>')
    svg.append(f'    <text x="125" y="{bar_y + 36}" font-family="sans-serif" font-size="25" font-weight="bold" fill="#ffffff">A fixed header keeps hardware parsing simple, and extension headers keep the design flexible</text>')
    svg.append('  </g>')
    
    svg.append('</svg>')
    return "\n".join(svg)

code = build_svg()
with open("test_candidate_v4_v6.svg", "w") as f:
    f.write(code)

print("Updated test_candidate_v4_v6.svg with clean group nesting")
