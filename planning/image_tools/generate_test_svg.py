import xml.etree.ElementTree as ET
import re

def generate_svg():
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">')
    lines.append('  <title>GPUs sit idle in the timeline: seven questions, each answered by a measurement</title>')
    lines.append('  <desc>A GPU timeline showing an idle gap above seven starvation questions with short checks and causes, alongside outcome metrics.</desc>')
    lines.append('')
    lines.append('  <!-- Background -->')
    lines.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    lines.append('')
    lines.append('  <!-- Main Title (48px bold) -->')
    lines.append('  <text x="800" y="75" font-size="48" font-weight="bold" fill="#303a36" font-family="sans-serif" text-anchor="middle">')
    lines.append('    <tspan x="800" dy="0">GPUs sit idle in the timeline:</tspan>')
    lines.append('    <tspan x="800" dy="54">seven questions, each answered by a measurement</tspan>')
    lines.append('  </text>')
    lines.append('')
    lines.append('  <!-- Top Panel: GPU Timeline -->')
    lines.append('  <rect x="40" y="150" width="1520" height="95" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('  <!-- Busy GPU compute blocks -->')
    lines.append('  <rect x="60" y="168" width="100" height="58" rx="6" fill="#207448" />')
    lines.append('  <rect x="175" y="168" width="110" height="58" rx="6" fill="#207448" />')
    lines.append('  <!-- Idle gap bubble -->')
    lines.append('  <rect x="305" y="168" width="990" height="58" rx="6" fill="#f5f8f5" stroke="#207448" stroke-width="2" stroke-dasharray="8,6" />')
    lines.append('  <text x="800" y="205" font-size="24" font-weight="bold" fill="#303a36" font-family="sans-serif" text-anchor="middle">idle gap (bubble): time between kernels or collectives</text>')
    lines.append('  <!-- Resumed compute blocks -->')
    lines.append('  <rect x="1315" y="168" width="105" height="58" rx="6" fill="#207448" />')
    lines.append('  <rect x="1435" y="168" width="105" height="58" rx="6" fill="#207448" />')
    lines.append('')
    lines.append('  <!-- Seven Question Rows -->')
    
    rows_data = [
        {
            "num": "1",
            "lines": [
                "Is the data loader the bottleneck? Empty queue, busy",
                "workers, a busy iostat, a slow network filesystem"
            ],
            "icon": "storage"
        },
        {
            "num": "2",
            "lines": [
                "Is the CPU the limiter? Single-thread Python launch overhead,",
                "torch ops launching tiny kernels"
            ],
            "fix": "fix: CUDA graphs or compile",
            "fix_x": 670,
            "icon": "cpu"
        },
        {
            "num": "3",
            "lines": [
                "Is host memory pinned, is the PCIe link at x16, is",
                "the NUMA placement right?"
            ],
            "icon": "pcie"
        },
        {
            "num": "4",
            "lines": [
                "Is communication exposed, meaning not overlapped",
                "with compute?"
            ],
            "icon": "network"
        },
        {
            "num": "5",
            "lines": [
                "Is a straggler rank late: thermal throttle, bad",
                "link, noisy neighbour?"
            ],
            "orange": True,
            "icon": "timer"
        },
        {
            "num": "6",
            "lines": [
                "Is the checkpoint blocking the step?"
            ],
            "icon": "checkpoint"
        },
        {
            "num": "7",
            "lines": [
                "Is GPU-Util high while SM activity is low? Many",
                "small kernels"
            ],
            "icon": "gpu"
        }
    ]

    y_start = 260
    row_h = 114
    gap = 10
    
    for i, r in enumerate(rows_data):
        by = y_start + i * (row_h + gap)
        cy = by + 57
        is_orange = r.get("orange", False)
        border_color = "#db8129" if is_orange else "#207448"
        border_width = "3" if is_orange else "2"
        badge_fill = "#db8129" if is_orange else "#207448"
        icon_stroke = "#db8129" if is_orange else "#207448"

        lines.append(f'  <!-- Row {r["num"]} -->')
        lines.append(f'  <rect x="40" y="{by}" width="1040" height="{row_h}" rx="8" fill="#e8f1ea" stroke="{border_color}" stroke-width="{border_width}" />')
        
        # Step number circle (r=24)
        lines.append(f'  <circle cx="74" cy="{cy}" r="24" fill="{badge_fill}" />')
        lines.append(f'  <text x="74" y="{cy + 8}" font-size="24" font-weight="bold" fill="#ffffff" font-family="sans-serif" text-anchor="middle">{r["num"]}</text>')

        # Icon outline (56px)
        lines.append(f'  <g stroke="{icon_stroke}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
        if r["icon"] == "storage":
            lines.append(f'    <ellipse cx="136" cy="{by+40}" rx="18" ry="6" />')
            lines.append(f'    <path d="M 118,{by+40} v 22 c 0,4 8,6 18,6 c 10,0 18,-2 18,-6 v -22" />')
            lines.append(f'    <path d="M 118,{by+51} c 0,4 8,6 18,6 c 10,0 18,-2 18,-6" />')
        elif r["icon"] == "cpu":
            lines.append(f'    <rect x="120" y="{by+41}" width="32" height="32" rx="4" />')
            lines.append(f'    <rect x="127" y="{by+48}" width="18" height="18" rx="2" />')
            lines.append(f'    <line x1="126" y1="{by+35}" x2="126" y2="{by+41}" /><line x1="136" y1="{by+35}" x2="136" y2="{by+41}" /><line x1="146" y1="{by+35}" x2="146" y2="{by+41}" />')
            lines.append(f'    <line x1="126" y1="{by+73}" x2="126" y2="{by+79}" /><line x1="136" y1="{by+73}" x2="136" y2="{by+79}" /><line x1="146" y1="{by+73}" x2="146" y2="{by+79}" />')
            lines.append(f'    <line x1="114" y1="{by+47}" x2="120" y2="{by+47}" /><line x1="114" y1="{by+57}" x2="120" y2="{by+57}" /><line x1="114" y1="{by+67}" x2="120" y2="{by+67}" />')
            lines.append(f'    <line x1="152" y1="{by+47}" x2="158" y2="{by+47}" /><line x1="152" y1="{by+57}" x2="158" y2="{by+57}" /><line x1="152" y1="{by+67}" x2="158" y2="{by+67}" />')
        elif r["icon"] == "pcie":
            lines.append(f'    <rect x="115" y="{by+43}" width="42" height="26" rx="3" />')
            lines.append(f'    <path d="M 120,{by+69} v 6 M 125,{by+69} v 6 M 130,{by+69} v 6 M 138,{by+69} v 6 M 143,{by+69} v 6 M 148,{by+69} v 6" />')
            lines.append(f'    <rect x="120" y="{by+48}" width="8" height="12" rx="1" /><rect x="132" y="{by+48}" width="8" height="12" rx="1" /><rect x="144" y="{by+48}" width="8" height="12" rx="1" />')
        elif r["icon"] == "network":
            lines.append(f'    <circle cx="124" cy="{by+44}" r="5" /><circle cx="148" cy="{by+44}" r="5" /><circle cx="136" cy="{by+70}" r="5" />')
            lines.append(f'    <line x1="129" y1="{by+44}" x2="143" y2="{by+44}" /><line x1="126" y1="{by+48}" x2="134" y2="{by+66}" /><line x1="146" y1="{by+48}" x2="138" y2="{by+66}" />')
        elif r["icon"] == "timer":
            lines.append(f'    <circle cx="136" cy="{by+57}" r="19" />')
            lines.append(f'    <polyline points="136,{by+45} 136,{by+57} 145,{by+57}" />')
            lines.append(f'    <line x1="136" y1="{by+38}" x2="136" y2="{by+41}" /><line x1="155" y1="{by+57}" x2="152" y2="{by+57}" />')
        elif r["icon"] == "checkpoint":
            lines.append(f'    <rect x="118" y="{by+39}" width="36" height="36" rx="3" />')
            lines.append(f'    <rect x="125" y="{by+39}" width="22" height="13" rx="1" />')
            lines.append(f'    <rect x="125" y="{by+58}" width="22" height="17" rx="1" />')
        elif r["icon"] == "gpu":
            lines.append(f'    <rect x="117" y="{by+38}" width="38" height="38" rx="3" />')
            lines.append(f'    <rect x="122" y="{by+43}" width="11" height="11" rx="1" fill="#207448" fill-opacity="0.2" />')
            lines.append(f'    <rect x="139" y="{by+43}" width="11" height="11" rx="1" fill="#207448" fill-opacity="0.2" />')
            lines.append(f'    <rect x="122" y="{by+60}" width="11" height="11" rx="1" fill="#207448" fill-opacity="0.2" />')
            lines.append(f'    <rect x="139" y="{by+60}" width="11" height="11" rx="1" fill="#207448" fill-opacity="0.2" />')
        lines.append('  </g>')

        # Text lines
        if len(r["lines"]) == 1:
            lines.append(f'  <text x="180" y="{by+65}" font-size="24" fill="#303a36" font-family="sans-serif">{r["lines"][0]}</text>')
        else:
            lines.append(f'  <text x="180" y="{by+48}" font-size="24" fill="#303a36" font-family="sans-serif">')
            lines.append(f'    <tspan x="180" dy="0">{r["lines"][0]}</tspan>')
            lines.append(f'    <tspan x="180" dy="34">{r["lines"][1]}</tspan>')
            lines.append('  </text>')

        # Fix text for Row 2
        if "fix" in r:
            lines.append(f'  <text x="{r["fix_x"]}" y="{by+82}" font-size="24" font-weight="bold" fill="#207448" font-family="sans-serif">{r["fix"]}</text>')

    lines.append('')
    lines.append('  <!-- Right Strip: Outcome metrics to read first -->')
    lines.append('  <rect x="1110" y="260" width="450" height="858" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Header
    lines.append('  <text x="1134" y="308" font-size="30" font-weight="bold" fill="#207448" font-family="sans-serif">')
    lines.append('    <tspan x="1134" dy="0">Outcome metrics</tspan>')
    lines.append('    <tspan x="1134" dy="36">to read first</tspan>')
    lines.append('  </text>')

    strip_metrics = [
        {
            "lines": [
                "throughput (tokens/s or",
                "samples/s per GPU and",
                "aggregate)"
            ]
        },
        {
            "lines": [
                "step time breakdown: data",
                "wait, H2D, forward,",
                "backward, exposed",
                "communication, optimizer,",
                "checkpoint"
            ]
        },
        {
            "lines": ["MFU"]
        },
        {
            "lines": [
                "scaling efficiency =",
                "throughput(N) / (N x",
                "throughput(1))"
            ]
        },
        {
            "lines": [
                "goodput = GPU-hours of",
                "useful work / GPU-hours",
                "paid, excluding restarts,",
                "failures, checkpoint",
                "stalls, stragglers and",
                "idle waiting"
            ]
        },
        {
            "lines": [
                "cost: USD per million",
                "tokens or per training run"
            ]
        }
    ]

    curr_y = 398
    for sm in strip_metrics:
        lines.append(f'  <text x="1134" y="{curr_y}" font-size="24" fill="#303a36" font-family="sans-serif">')
        for idx, l in enumerate(sm["lines"]):
            dy = "0" if idx == 0 else "28"
            lines.append(f'    <tspan x="1134" dy="{dy}">{l}</tspan>')
        lines.append('  </text>')
        curr_y += len(sm["lines"]) * 28 + 14

    lines.append('')
    lines.append('  <!-- Bottom Takeaway Bar -->')
    lines.append('  <rect x="40" y="1128" width="1520" height="58" rx="8" fill="#207448" />')
    lines.append('  <text x="800" y="1168" font-size="24" font-weight="bold" fill="#ffffff" font-family="sans-serif" text-anchor="middle">Answer each question with a measurement rather than an opinion</text>')
    lines.append('</svg>')

    return "\n".join(lines)

svg_content = generate_svg()
with open("test_candidate_gpu_starvation.svg", "w") as f:
    f.write(svg_content)
print("Generated test_candidate_gpu_starvation.svg successfully!")
