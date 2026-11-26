import re
import xml.etree.ElementTree as ET
import subprocess
import os

def build_svg():
    # Colors
    bg = "#f5f8f5"
    text_color = "#303a36"
    main_green = "#207448"
    light_green = "#e8f1ea"
    orange = "#db8129"
    white = "#ffffff"
    
    # Layout constants
    W = 1600
    H = 1200
    
    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    lines.append('  <title>Common mistakes in errors, files and subprocesses, grouped</title>')
    lines.append('  <desc>A grouped table of common mistakes and fixes across exceptions, files, subprocess, global state, re-runs, signals, and untrusted input.</desc>')
    lines.append(f'  <rect width="{W}" height="{H}" fill="{bg}"/>')
    
    # Title (2 lines)
    lines.append('  <!-- ==================== TITLE ==================== -->')
    lines.append(f'  <text x="800" y="44" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="{text_color}">')
    lines.append('    <tspan x="800" dy="0">Common mistakes in errors, files</tspan>')
    lines.append('    <tspan x="800" dy="52">and subprocesses, grouped</tspan>')
    lines.append('  </text>')
    
    # Table Column Headers
    header_y = 100
    header_h = 44
    area_w = 270
    mistake_w = 715
    fix_w = 505
    col_gap = 15
    
    area_x = 40
    mistake_x = area_x + area_w + col_gap # 325
    fix_x = mistake_x + mistake_w + col_gap # 1055
    
    lines.append('  <!-- ==================== TABLE HEADERS ==================== -->')
    lines.append(f'  <rect x="{area_x}" y="{header_y}" width="{area_w}" height="{header_h}" rx="6" fill="{main_green}"/>')
    lines.append(f'  <text x="{area_x + area_w//2}" y="{header_y + 32}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{white}">Area</text>')
    
    lines.append(f'  <rect x="{mistake_x}" y="{header_y}" width="{mistake_w}" height="{header_h}" rx="6" fill="{main_green}"/>')
    lines.append(f'  <text x="{mistake_x + mistake_w//2}" y="{header_y + 32}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{white}">Mistake</text>')
    
    lines.append(f'  <rect x="{fix_x}" y="{header_y}" width="{fix_w}" height="{header_h}" rx="6" fill="{main_green}"/>')
    lines.append(f'  <text x="{fix_x + fix_w//2}" y="{header_y + 32}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{white}">Fix</text>')
    
    # Rows definition: Total heights = 104+130+178+104+104+78+104 = 802px.
    # 6 gaps of 6px = 36px. Total table rows = 838px.
    # Starts at 150, ends at 988.
    rows_data = [
        {
            "id": "exceptions",
            "area_title": ["Exceptions"],
            "rh": 104,
            "mistake_lines": [
                "bare except and except Exception: pass;",
                "catching too much around too much code",
                "loses tracebacks and hides bugs"
            ],
            "fix_lines": [
                "catch the narrowest exception,",
                "log once at the top"
            ],
            "orange": False
        },
        {
            "id": "files",
            "area_title": ["Files"],
            "rh": 130,
            "mistake_lines": [
                "writing in place leads to partial writes;",
                "declaring success before an fsync;",
                "exists-then-create checks leave gaps; no",
                "explicit encoding; mixing bytes and str"
            ],
            "fix_lines": [
                "atomic replace, fsync, attempt",
                "then handle, encoding=utf-8"
            ],
            "orange": False
        },
        {
            "id": "subprocess",
            "area_title": ["Subprocess"],
            "rh": 178,
            "mistake_lines": [
                "shell=True with interpolated input; missing",
                "timeouts; ignored return codes; parsing",
                "human-formatted output; secrets in command",
                "lines; capturing huge output in memory; pipe",
                "deadlocks; unreaped children; os.system,",
                "os.popen and the deprecated commands module"
            ],
            "fix_lines": [
                "argument list, timeout, check,",
                "machine-readable output,",
                "communicate, wait"
            ],
            "orange": False
        },
        {
            "id": "global_state",
            "area_title": ["Global", "state"],
            "rh": 104,
            "mistake_lines": [
                "mutating os.environ or os.chdir inside a",
                "library affects every caller; assuming the",
                "current directory"
            ],
            "fix_lines": [
                "copy the environment for the",
                "child, pass explicit paths"
            ],
            "orange": True
        },
        {
            "id": "reruns",
            "area_title": ["Re-runs"],
            "rh": 104,
            "mistake_lines": [
                "scripts unsafe to re-run"
            ],
            "fix_lines": [
                "dry-run mode, a lock against",
                "overlapping runs, UTC timestamps",
                "rather than naive ones"
            ],
            "orange": False
        },
        {
            "id": "signals",
            "area_title": ["Signals"],
            "rh": 78,
            "mistake_lines": [
                "heavy work in signal handlers;",
                "ignoring SIGTERM in containers"
            ],
            "fix_lines": [
                "set a flag, finish and exit"
            ],
            "orange": False
        },
        {
            "id": "untrusted_input",
            "area_title": ["Untrusted", "input"],
            "rh": 104,
            "mistake_lines": [
                "extracting tar or zip archives without",
                "validating paths; yaml.load or pickle on",
                "data from the network"
            ],
            "fix_lines": [
                "validate member paths,",
                "filter=data, safe_load"
            ],
            "orange": False
        }
    ]
    
    # Helper to draw area icons
    def draw_icon(row_id, ix, iy):
        res = []
        if row_id == "exceptions":
            # Alert triangle
            res.append(f'    <polygon points="{ix+22},{iy+4} {ix+42},{iy+38} {ix+2},{iy+38}" fill="none" stroke="{main_green}" stroke-width="3.5" stroke-linejoin="round"/>')
            res.append(f'    <line x1="{ix+22}" y1="{iy+16}" x2="{ix+22}" y2="{iy+26}" stroke="{main_green}" stroke-width="3.5" stroke-linecap="round"/>')
            res.append(f'    <circle cx="{ix+22}" cy="{iy+32}" r="2" fill="{main_green}"/>')
        elif row_id == "files":
            # Document outline with folded corner
            res.append(f'    <path d="M {ix+8} {iy+4} L {ix+28} {iy+4} L {ix+38} {iy+14} L {ix+38} {iy+40} L {ix+8} {iy+40} Z" fill="none" stroke="{main_green}" stroke-width="3.5" stroke-linejoin="round"/>')
            res.append(f'    <path d="M {ix+28} {iy+4} L {ix+28} {iy+14} L {ix+38} {iy+14}" fill="none" stroke="{main_green}" stroke-width="3" stroke-linejoin="round"/>')
            res.append(f'    <line x1="{ix+14}" y1="{iy+22}" x2="{ix+32}" y2="{iy+22}" stroke="{main_green}" stroke-width="3" stroke-linecap="round"/>')
            res.append(f'    <line x1="{ix+14}" y1="{iy+30}" x2="{ix+28}" y2="{iy+30}" stroke="{main_green}" stroke-width="3" stroke-linecap="round"/>')
        elif row_id == "subprocess":
            # Terminal / prompt window
            res.append(f'    <rect x="{ix+2}" y="{iy+6}" width="40" height="32" rx="4" fill="none" stroke="{main_green}" stroke-width="3.5"/>')
            res.append(f'    <polyline points="{ix+8},{iy+16} {ix+14},{iy+22} {ix+8},{iy+28}" fill="none" stroke="{main_green}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
            res.append(f'    <line x1="{ix+18}" y1="{iy+28}" x2="{ix+28}" y2="{iy+28}" stroke="{main_green}" stroke-width="3.5" stroke-linecap="round"/>')
        elif row_id == "global_state":
            # Globe with latitude/longitude
            res.append(f'    <circle cx="{ix+22}" cy="{iy+22}" r="18" fill="none" stroke="{main_green}" stroke-width="3.5"/>')
            res.append(f'    <ellipse cx="{ix+22}" cy="{iy+22}" rx="8" ry="18" fill="none" stroke="{main_green}" stroke-width="3"/>')
            res.append(f'    <line x1="{ix+4}" y1="{iy+22}" x2="{ix+40}" y2="{iy+22}" stroke="{main_green}" stroke-width="3"/>')
        elif row_id == "reruns":
            # Refresh / repeat circular loop
            res.append(f'    <path d="M {ix+22} {iy+6} A 16 16 0 1 1 {ix+8} {iy+24}" fill="none" stroke="{main_green}" stroke-width="3.5" stroke-linecap="round"/>')
            res.append(f'    <polygon points="{ix+22},{iy+1} {ix+22},{iy+12} {ix+30},{iy+6}" fill="{main_green}"/>')
        elif row_id == "signals":
            # Broadcast / signal antenna
            res.append(f'    <line x1="{ix+22}" y1="{iy+18}" x2="{ix+22}" y2="{iy+40}" stroke="{main_green}" stroke-width="3.5" stroke-linecap="round"/>')
            res.append(f'    <circle cx="{ix+22}" cy="{iy+14}" r="4" fill="{main_green}"/>')
            res.append(f'    <path d="M {ix+12} {iy+8} A 14 14 0 0 1 {ix+32} {iy+8}" fill="none" stroke="{main_green}" stroke-width="3" stroke-linecap="round"/>')
            res.append(f'    <path d="M {ix+6} {iy+2} A 22 22 0 0 1 {ix+38} {iy+2}" fill="none" stroke="{main_green}" stroke-width="3" stroke-linecap="round"/>')
        elif row_id == "untrusted_input":
            # Shield with padlock
            res.append(f'    <path d="M {ix+22} {iy+4} L {ix+38} {iy+10} C {ix+38} {iy+28} {ix+22} {iy+38} {ix+22} {iy+38} C {ix+22} {iy+38} {ix+6} {iy+28} {ix+6} {iy+10} Z" fill="none" stroke="{main_green}" stroke-width="3.5" stroke-linejoin="round"/>')
            res.append(f'    <line x1="{ix+22}" y1="{iy+14}" x2="{ix+22}" y2="{iy+24}" stroke="{main_green}" stroke-width="3.5" stroke-linecap="round"/>')
            res.append(f'    <circle cx="{ix+22}" cy="{iy+29}" r="2" fill="{main_green}"/>')
        return "\n".join(res)
    
    cur_y = 150
    row_gap = 6
    
    lines.append('  <!-- ==================== TABLE ROWS ==================== -->')
    for r in rows_data:
        rh = r["rh"]
        is_orange = r["orange"]
        row_id = r["id"]
        
        # 1. Area Box
        lines.append(f'  <!-- Row: {r["id"]} -->')
        lines.append(f'  <rect x="{area_x}" y="{cur_y}" width="{area_w}" height="{rh}" rx="8" fill="{light_green}" stroke="{main_green}" stroke-width="2"/>')
        
        # Icon
        icon_x = area_x + 14
        icon_y = cur_y + (rh - 44) // 2
        lines.append(draw_icon(row_id, icon_x, icon_y))
        
        # Area title text
        titles = r["area_title"]
        if len(titles) == 1:
            title_y = cur_y + (rh // 2) + 10
            lines.append(f'  <text x="{area_x + 68}" y="{title_y}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">{titles[0]}</text>')
        else:
            title_y = cur_y + (rh // 2) - 6
            lines.append(f'  <text x="{area_x + 68}" y="{title_y}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">')
            lines.append(f'    <tspan x="{area_x + 68}" dy="0">{titles[0]}</tspan>')
            lines.append(f'    <tspan x="{area_x + 68}" dy="32">{titles[1]}</tspan>')
            lines.append('  </text>')
            
        # 2. Mistake Box
        m_lines = r["mistake_lines"]
        if is_orange:
            # Highlighted orange box for the single most important item
            lines.append(f'  <rect x="{mistake_x}" y="{cur_y}" width="{mistake_w}" height="{rh}" rx="8" fill="#fff8f2" stroke="{orange}" stroke-width="3"/>')
        else:
            lines.append(f'  <rect x="{mistake_x}" y="{cur_y}" width="{mistake_w}" height="{rh}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="1.5"/>')
            
        if len(m_lines) == 1:
            m_start_y = cur_y + (rh // 2) + 8
            lines.append(f'  <text x="{mistake_x + 20}" y="{m_start_y}" font-family="monospace" font-size="24" fill="{text_color}">{m_lines[0]}</text>')
        else:
            m_start_y = cur_y + 34
            lines.append(f'  <text x="{mistake_x + 20}" y="{m_start_y}" font-family="monospace" font-size="24" fill="{text_color}">')
            for idx, ml in enumerate(m_lines):
                dy = 0 if idx == 0 else 25
                lines.append(f'    <tspan x="{mistake_x + 20}" dy="{dy}">{ml}</tspan>')
            lines.append('  </text>')
            
        # 3. Fix Box
        f_lines = r["fix_lines"]
        lines.append(f'  <rect x="{fix_x}" y="{cur_y}" width="{fix_w}" height="{rh}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="1.5"/>')
        
        if len(f_lines) == 1:
            f_start_y = cur_y + (rh // 2) + 8
            lines.append(f'  <text x="{fix_x + 20}" y="{f_start_y}" font-family="sans-serif" font-size="24" fill="{text_color}">{f_lines[0]}</text>')
        else:
            f_start_y = cur_y + 34
            lines.append(f'  <text x="{fix_x + 20}" y="{f_start_y}" font-family="sans-serif" font-size="24" fill="{text_color}">')
            for idx, fl in enumerate(f_lines):
                dy = 0 if idx == 0 else 25
                lines.append(f'    <tspan x="{fix_x + 20}" dy="{dy}">{fl}</tspan>')
            lines.append('  </text>')
            
        cur_y += rh + row_gap
        
    # Stories Strip
    stories_y = cur_y + 6
    stories_h = 76
    lines.append('  <!-- ==================== STORIES STRIP ==================== -->')
    lines.append(f'  <rect x="{area_x}" y="{stories_y}" width="{W - 80}" height="{stories_h}" rx="8" fill="{light_green}" stroke="{main_green}" stroke-width="2"/>')
    story_l1 = "a cleanup script runs twice because its lock was checked before it was taken,"
    story_l2 = "and the second run deletes the checkpoint the first one was writing"
    lines.append(f'  <text x="{W//2}" y="{stories_y + 32}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{text_color}">')
    lines.append(f'    <tspan x="{W//2}" dy="0">{story_l1}</tspan>')
    lines.append(f'    <tspan x="{W//2}" dy="28">{story_l2}</tspan>')
    lines.append('  </text>')
    
    # Bottom bar
    bottom_y = stories_y + stories_h + 12
    bottom_h = 50
    lines.append('  <!-- ==================== BOTTOM BAR ==================== -->')
    lines.append(f'  <rect x="{area_x}" y="{bottom_y}" width="{W - 80}" height="{bottom_h}" rx="8" fill="{main_green}"/>')
    bottom_text = "A second attempt after a failure should be boring"
    lines.append(f'  <text x="{W//2}" y="{bottom_y + 34}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="{white}">{bottom_text}</text>')
    
    lines.append('</svg>')
    return "\n".join(lines)

svg_str = build_svg()
with open("test_mistakes.svg", "w") as f:
    f.write(svg_str)
print("SVG written to test_mistakes.svg")
