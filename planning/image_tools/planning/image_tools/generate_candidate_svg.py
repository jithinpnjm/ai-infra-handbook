#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import asyncio
from playwright.async_api import async_playwright

def generate_perfect_svg():
    # Title
    t_line1 = "The 60-second checklist for a GPU node: "
    t_line2 = "eight read-only additions"
    
    # Title: y=44, dy=40
    title_y = 44
    title_dy = 40
    
    # Header: y=109, h=56
    hdr_y = 109
    hdr_h = 56
    
    gap = 3.5
    
    rows_data = [
        {
            "num": "11",
            "h": 128,
            "cmd_lines": ["nvidia-smi"],
            "desc_lines": [
                "all GPUs present, driver and CUDA versions, ",
                "memory, processes, power draw versus cap, ",
                "temperature, throttle reasons ",
                "(nvidia-smi -q -d PERFORMANCE)"
            ],
            "is_orange": False,
            "layer_type": "gpu_chip"
        },
        {
            "num": "12",
            "h": 104,
            "cmd_lines": ["nvidia-smi dmon ", "-s pucvmet -d 1"],
            "desc_lines": [
                "per-GPU power, utilisation (sm, mem, enc/dec), ",
                "clocks, memory, PCIe and NVLink throughput, ",
                "ECC counters per second"
            ],
            "is_orange": False,
            "layer_type": "telemetry"
        },
        {
            "num": "13",
            "h": 88,
            "cmd_lines": ["nvidia-smi topo -m and ", "nvidia-smi nvlink -s"],
            "desc_lines": [
                "topology matrix (NV#, PIX, PXB, PHB, SYS, NODE), ",
                "NVLink active links"
            ],
            "is_orange": False,
            "layer_type": "nvlink"
        },
        {
            "num": "14",
            "h": 104,
            "cmd_lines": ["dcgmi dmon -e ... or ", "dcgmi diag -r 1"],
            "desc_lines": [
                "SM activity and occupancy, tensor-pipe activity, ",
                "DRAM activity, NVLink and PCIe throughput; ",
                "quick health test"
            ],
            "is_orange": False,
            "layer_type": "tensor"
        },
        {
            "num": "15",
            "h": 104,
            "cmd_lines": ["journalctl -k | grep ", '-iE "NVRM|Xid|nvidia"'],
            "desc_lines": [
                "GPU errors: Xid 79 fallen off the bus, ",
                "48 63 64 94 95 ECC and retired pages, ",
                "74 NVLink errors"
            ],
            "is_orange": True,
            "layer_type": "xid"
        },
        {
            "num": "16",
            "h": 104,
            "cmd_lines": ["ibstat, ibv_devinfo, ", "rdma link, perfquery or ", "ethtool -S"],
            "desc_lines": [
                "link state and rate, error counters"
            ],
            "is_orange": False,
            "layer_type": "network"
        },
        {
            "num": "17",
            "h": 88,
            "cmd_lines": ["cat /proc/pressure/", "{cpu,memory,io}"],
            "desc_lines": [
                "PSI: tasks stalled on each resource"
            ],
            "is_orange": False,
            "layer_type": "psi"
        },
        {
            "num": "18",
            "h": 104,
            "cmd_lines": [
                "numastat, lstopo, cat ",
                "/proc/cmdline, sysctl -a ",
                "diff versus baseline"
            ],
            "desc_lines": [
                "placement and drift"
            ],
            "is_orange": False,
            "layer_type": "numa"
        }
    ]
    
    cur_y = hdr_y + hdr_h + gap
    for r in rows_data:
        r["y"] = cur_y
        cur_y += r["h"] + gap
        
    last_row_end = cur_y - gap
    footer_y = last_row_end + gap
    footer_h = 80
    
    bbar_y = footer_y + footer_h + gap
    bbar_h = 56
    
    # Helper to generate icons
    def generate_icon(layer_type, cx, cy, is_orange):
        color = "#db8129" if is_orange else "#207448"
        x = cx - 28
        y = cy - 28
        out = []
        if layer_type == "gpu_chip":
            out.append(f'<g transform="translate({x}, {y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            out.append('  <rect x="10" y="10" width="36" height="36" rx="4"/>')
            out.append('  <rect x="20" y="20" width="16" height="16" fill="none"/>')
            out.append('  <line x1="18" y1="2" x2="18" y2="10"/><line x1="28" y1="2" x2="28" y2="10"/><line x1="38" y1="2" x2="38" y2="10"/>')
            out.append('  <line x1="18" y1="46" x2="18" y2="54"/><line x1="28" y1="46" x2="28" y2="54"/><line x1="38" y1="46" x2="38" y2="54"/>')
            out.append('  <line x1="2" y1="18" x2="10" y2="18"/><line x1="2" y1="28" x2="10" y2="28"/><line x1="2" y1="38" x2="10" y2="38"/>')
            out.append('  <line x1="46" y1="18" x2="54" y2="18"/><line x1="46" y1="28" x2="54" y2="28"/><line x1="46" y1="38" x2="54" y2="38"/>')
            out.append('</g>')
        elif layer_type == "telemetry":
            out.append(f'<g transform="translate({x}, {y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            out.append('  <circle cx="28" cy="28" r="22"/>')
            out.append('  <line x1="28" y1="28" x2="40" y2="16"/>')
            out.append(f'  <circle cx="28" cy="28" r="3" fill="{color}"/>')
            out.append('  <line x1="14" y1="28" x2="10" y2="28"/><line x1="28" y1="14" x2="28" y2="10"/><line x1="42" y1="28" x2="46" y2="28"/>')
            out.append('</g>')
        elif layer_type == "nvlink":
            out.append(f'<g transform="translate({x}, {y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            out.append('  <circle cx="12" cy="12" r="6"/>')
            out.append('  <circle cx="44" cy="12" r="6"/>')
            out.append('  <circle cx="12" cy="44" r="6"/>')
            out.append('  <circle cx="44" cy="44" r="6"/>')
            out.append('  <line x1="18" y1="12" x2="38" y2="12"/><line x1="18" y1="44" x2="38" y2="44"/>')
            out.append('  <line x1="12" y1="18" x2="12" y2="38"/><line x1="44" y1="18" x2="44" y2="38"/>')
            out.append('  <line x1="16" y1="16" x2="40" y2="40"/><line x1="40" y1="16" x2="16" y2="40"/>')
            out.append('</g>')
        elif layer_type == "tensor":
            out.append(f'<g transform="translate({x}, {y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            out.append('  <rect x="6" y="6" width="18" height="18" rx="3"/>')
            out.append('  <rect x="32" y="6" width="18" height="18" rx="3"/>')
            out.append('  <rect x="6" y="32" width="18" height="18" rx="3"/>')
            out.append('  <rect x="32" y="32" width="18" height="18" rx="3"/>')
            out.append('  <line x1="15" y1="24" x2="15" y2="32"/><line x1="41" y1="24" x2="41" y2="32"/>')
            out.append('  <line x1="24" y1="15" x2="32" y2="15"/><line x1="24" y1="41" x2="32" y2="41"/>')
            out.append('</g>')
        elif layer_type == "xid":
            out.append(f'<g transform="translate({x}, {y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            out.append('  <path d="M 28 6 L 50 48 L 6 48 Z"/>')
            out.append('  <line x1="28" y1="20" x2="28" y2="32"/>')
            out.append(f'  <circle cx="28" cy="40" r="2.5" fill="{color}"/>')
            out.append('</g>')
        elif layer_type == "network":
            out.append(f'<g transform="translate({x}, {y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            out.append('  <rect x="8" y="12" width="40" height="32" rx="4"/>')
            out.append('  <rect x="16" y="20" width="10" height="16" rx="2"/>')
            out.append('  <rect x="30" y="20" width="10" height="16" rx="2"/>')
            out.append('  <line x1="20" y1="44" x2="20" y2="52"/><line x1="36" y1="44" x2="36" y2="52"/>')
            out.append('</g>')
        elif layer_type == "psi":
            out.append(f'<g transform="translate({x}, {y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            out.append('  <path d="M 10 38 A 20 20 0 1 1 46 38"/>')
            out.append('  <line x1="28" y1="28" x2="38" y2="18"/>')
            out.append(f'  <circle cx="28" cy="28" r="3" fill="{color}"/>')
            out.append('  <line x1="8" y1="46" x2="48" y2="46"/>')
            out.append('</g>')
        elif layer_type == "numa":
            out.append(f'<g transform="translate({x}, {y})" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            out.append('  <rect x="6" y="8" width="18" height="20" rx="3"/>')
            out.append('  <rect x="32" y="8" width="18" height="20" rx="3"/>')
            out.append('  <line x1="15" y1="28" x2="15" y2="42"/>')
            out.append('  <line x1="41" y1="28" x2="41" y2="42"/>')
            out.append('  <line x1="10" y1="42" x2="46" y2="42"/>')
            out.append('  <rect x="18" y="42" width="20" height="10" rx="2"/>')
            out.append('</g>')
        return "\n".join(out)

    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>The 60-second checklist for a GPU node: eight read-only additions</title>')
    svg.append('  <desc>Eight read-only GPU checks extending the host checklist to cover GPUs, topology, Xid errors, fabric counters and pressure.</desc>')
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    
    # Title
    svg.append('  <!-- ==================== TITLE ==================== -->')
    svg.append(f'  <text x="800" y="{title_y}" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append(f'    <tspan x="800" dy="0">{t_line1}</tspan>')
    svg.append(f'    <tspan x="800" dy="{title_dy}">{t_line2}</tspan>')
    svg.append('  </text>')
    
    # Table Header
    svg.append('  <!-- ==================== TABLE HEADERS ==================== -->')
    svg.append('  <g id="header-col1">')
    svg.append(f'    <rect x="40" y="{hdr_y}" width="480" height="{hdr_h}" rx="6" fill="#207448"/>')
    svg.append(f'    <text x="280" y="{hdr_y + 40}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Command</text>')
    svg.append('  </g>')
    svg.append('  <g id="header-col2">')
    svg.append(f'    <rect x="535" y="{hdr_y}" width="730" height="{hdr_h}" rx="6" fill="#207448"/>')
    svg.append(f'    <text x="900" y="{hdr_y + 40}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">What to check</text>')
    svg.append('  </g>')
    svg.append('  <g id="header-col3">')
    svg.append(f'    <rect x="1280" y="{hdr_y}" width="280" height="{hdr_h}" rx="6" fill="#207448"/>')
    svg.append(f'    <text x="1420" y="{hdr_y + 40}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Reads which layer</text>')
    svg.append('  </g>')
    
    # Rows
    for r in rows_data:
        num = r["num"]
        y = r["y"]
        h = r["h"]
        is_orange = r["is_orange"]
        border_color = "#db8129" if is_orange else "#207448"
        fill_color = "#fffaf5" if is_orange else "#ffffff"
        circle_color = "#db8129" if is_orange else "#207448"
        stroke_w = "2.5" if is_orange else "1.2"
        
        svg.append(f'  <!-- ==================== ROW {num} ==================== -->')
        svg.append(f'  <g id="row-{num}">')
        
        # Col 1 (Command)
        svg.append(f'    <rect x="40" y="{y}" width="480" height="{h}" rx="6" fill="{fill_color}" stroke="{border_color}" stroke-width="{stroke_w}"/>')
        # Number circle centered vertically
        cy = y + h / 2.0
        svg.append(f'    <circle cx="74" cy="{cy}" r="24" fill="{circle_color}"/>')
        svg.append(f'    <text x="74" y="{cy}" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">{num}</text>')
        
        # Command text
        cmd_lines = r["cmd_lines"]
        if len(cmd_lines) == 1:
            cmd_y = y + h / 2.0 + 8
            svg.append(f'    <text x="114" y="{cmd_y}" font-family="monospace" font-size="24" fill="#303a36"><tspan x="114" dy="0">{cmd_lines[0]}</tspan></text>')
        elif len(cmd_lines) == 2:
            cmd_y = y + 40
            svg.append(f'    <text x="114" y="{cmd_y}" font-family="monospace" font-size="24" fill="#303a36"><tspan x="114" dy="0">{cmd_lines[0]}</tspan><tspan x="114" dy="24">{cmd_lines[1]}</tspan></text>')
        elif len(cmd_lines) == 3:
            cmd_y = y + 40
            svg.append(f'    <text x="114" y="{cmd_y}" font-family="monospace" font-size="24" fill="#303a36"><tspan x="114" dy="0">{cmd_lines[0]}</tspan><tspan x="114" dy="24">{cmd_lines[1]}</tspan><tspan x="114" dy="24">{cmd_lines[2]}</tspan></text>')
            
        # Col 2 (What to check)
        svg.append(f'    <rect x="535" y="{y}" width="730" height="{h}" rx="6" fill="{fill_color}" stroke="{border_color}" stroke-width="{stroke_w}"/>')
        desc_lines = r["desc_lines"]
        if len(desc_lines) == 1:
            desc_y = y + h / 2.0 + 8
            desc_t = desc_lines[0]
            svg.append(f'    <text x="555" y="{desc_y}" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="555" dy="0">{desc_t}</tspan></text>')
        else:
            desc_y = y + 40
            tspans = "".join([f'<tspan x="555" dy="{0 if i==0 else 24}">{line}</tspan>' for i, line in enumerate(desc_lines)])
            svg.append(f'    <text x="555" y="{desc_y}" font-family="sans-serif" font-size="24" fill="#303a36">{tspans}</text>')
            
        # Col 3 (Reads which layer)
        svg.append(f'    <rect x="1280" y="{y}" width="280" height="{h}" rx="6" fill="{fill_color}" stroke="{border_color}" stroke-width="{stroke_w}"/>')
        icon_cx = 1280 + 280 / 2.0
        icon_cy = y + h / 2.0
        svg.append(generate_icon(r["layer_type"], icon_cx, icon_cy, is_orange))
        
        svg.append('  </g>')
        
    # Footer Panel
    svg.append('  <!-- ==================== FOOTER PANEL ==================== -->')
    svg.append('  <g id="footer-panel">')
    svg.append(f'    <rect x="40" y="{footer_y}" width="1520" height="{footer_h}" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    svg.append(f'    <text x="800" y="{footer_y + 40}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="800" dy="0">All of them are read-only; option names vary by driver and DCGM version, </tspan>')
    svg.append('      <tspan x="800" dy="24">so check the flags on your own system</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # Bottom bar
    svg.append('  <!-- ==================== BOTTOM BAR ==================== -->')
    svg.append('  <g id="bottom-bar">')
    svg.append(f'    <rect x="40" y="{bbar_y}" width="1520" height="{bbar_h}" rx="8" fill="#207448"/>')
    svg.append(f'    <text x="800" y="{bbar_y + 40}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Add these to the host checklist when you are on a GPU node</text>')
    svg.append('  </g>')
    
    svg.append('</svg>')
    
    content = "\n".join(svg) + "\n"
    with open("candidate_gpu_checklist.svg", "w") as f:
        f.write(content)
    print(f"Generated candidate_gpu_checklist.svg (hdr_y={hdr_y}, bbar end={bbar_y + bbar_h})")

if __name__ == "__main__":
    generate_perfect_svg()
