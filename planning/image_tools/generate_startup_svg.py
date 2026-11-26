#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import subprocess

def build_svg():
    svg_parts = []
    svg_parts.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1180" width="1600" height="1180">')
    svg_parts.append('  <title>Which startup stage produced this error message</title>')
    svg_parts.append('  <desc>Visual infographic mapping Linux startup errors to six execution pipeline stages with diagnostics.</desc>')
    
    # Marker definitions
    svg_parts.append('  <defs>')
    svg_parts.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg_parts.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg_parts.append('    </marker>')
    svg_parts.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg_parts.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    svg_parts.append('    </marker>')
    svg_parts.append('  </defs>')

    # Background
    svg_parts.append('  <!-- Canvas Background -->')
    svg_parts.append('  <rect width="1600" height="1180" fill="#f5f8f5" />')

    # Title (48px bold)
    svg_parts.append('  <!-- Title -->')
    svg_parts.append('  <text x="800" y="56" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Which startup stage produced this error message</text>')

    # =========================================================================
    # ROW 1: PIPELINE OF SIX STAGE BOXES (y = 96 to 346, height = 250)
    # Box 1: x=40,   w=180, right=220
    # Box 2: x=244,  w=236, right=480
    # Box 3: x=504,  w=190, right=694
    # Box 4: x=720,  w=236, right=956
    # Box 5: x=982,  w=250, right=1232
    # Box 6: x=1264, w=296, right=1560
    # =========================================================================

    # --- STAGE 1: shell fork and execve ---
    svg_parts.append('  <!-- Stage 1 -->')
    svg_parts.append('  <g id="stage-1">')
    svg_parts.append('    <rect x="40" y="96" width="180" height="250" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Number circle 1 (cx=70, cy=126, r=20)
    svg_parts.append('    <circle cx="70" cy="126" r="20" fill="#207448" />')
    svg_parts.append('    <text x="70" y="134" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>')
    # Outline icon: Terminal prompt (56x40)
    svg_parts.append('    <g transform="translate(132, 106)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_parts.append('      <rect x="0" y="0" width="56" height="40" rx="6" />')
    svg_parts.append('      <line x1="0" y1="12" x2="56" y2="12" stroke-width="2.5" />')
    svg_parts.append('      <polyline points="10,22 18,27 10,32" stroke-width="3" />')
    svg_parts.append('      <line x1="24" y1="32" x2="38" y2="32" stroke-width="3" />')
    svg_parts.append('    </g>')
    # Label: shell fork and execve
    svg_parts.append('    <text font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="130" y="210">shell fork </tspan>')
    svg_parts.append('      <tspan x="130" dy="32">and execve</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # Arrow Stage 1 -> Stage 2
    svg_parts.append('  <line x1="220" y1="221" x2="244" y2="221" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')

    # --- STAGE 2: kernel checks the file and picks a format handler ---
    svg_parts.append('  <!-- Stage 2 -->')
    svg_parts.append('  <g id="stage-2">')
    svg_parts.append('    <rect x="244" y="96" width="236" height="250" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Number circle 2
    svg_parts.append('    <circle cx="274" cy="126" r="20" fill="#207448" />')
    svg_parts.append('    <text x="274" y="134" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>')
    # Outline icon: Kernel shield inspection (46x50)
    svg_parts.append('    <g transform="translate(404, 103)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_parts.append('      <path d="M 6 6 H 42 V 26 C 42 38 24 46 24 46 C 24 46 6 38 6 26 Z" />')
    svg_parts.append('      <polyline points="15,24 21,30 33,18" stroke-width="3" />')
    svg_parts.append('    </g>')
    # Label: kernel checks the file and picks a format handler
    svg_parts.append('    <text font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="362" y="180">kernel checks </tspan>')
    svg_parts.append('      <tspan x="362" dy="30">the file and </tspan>')
    svg_parts.append('      <tspan x="362" dy="30">picks a </tspan>')
    svg_parts.append('      <tspan x="362" dy="30">format handler</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # Arrow Stage 2 -> Stage 3
    svg_parts.append('  <line x1="480" y1="221" x2="504" y2="221" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')

    # --- STAGE 3: ELF loader maps LOAD segments, builds the stack ---
    svg_parts.append('  <!-- Stage 3 -->')
    svg_parts.append('  <g id="stage-3">')
    svg_parts.append('    <rect x="504" y="96" width="190" height="250" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Number circle 3
    svg_parts.append('    <circle cx="534" cy="126" r="20" fill="#207448" />')
    svg_parts.append('    <text x="534" y="134" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>')
    # Outline icon: Stack memory layers (46x46)
    svg_parts.append('    <g transform="translate(628, 105)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_parts.append('      <rect x="4" y="6" width="40" height="10" rx="3" />')
    svg_parts.append('      <rect x="4" y="20" width="40" height="10" rx="3" />')
    svg_parts.append('      <rect x="4" y="34" width="40" height="10" rx="3" />')
    svg_parts.append('    </g>')
    # Label: ELF loader maps LOAD segments, builds the stack
    svg_parts.append('    <text font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="599" y="170">ELF loader </tspan>')
    svg_parts.append('      <tspan x="599" dy="28">maps LOAD </tspan>')
    svg_parts.append('      <tspan x="599" dy="28">segments, </tspan>')
    svg_parts.append('      <tspan x="599" dy="28">builds the </tspan>')
    svg_parts.append('      <tspan x="599" dy="28">stack</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # Arrow Stage 3 -> Stage 4
    svg_parts.append('  <line x1="694" y1="221" x2="720" y2="221" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')

    # --- STAGE 4: PT_INTERP: kernel maps ld.so, execution starts in the dynamic linker ---
    svg_parts.append('  <!-- Stage 4 -->')
    svg_parts.append('  <g id="stage-4">')
    svg_parts.append('    <rect x="720" y="96" width="236" height="250" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Number circle 4
    svg_parts.append('    <circle cx="750" cy="126" r="20" fill="#207448" />')
    svg_parts.append('    <text x="750" y="134" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>')
    # Outline icon: Linker interlocking link (48x46)
    svg_parts.append('    <g transform="translate(884, 105)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_parts.append('      <rect x="6" y="8" width="22" height="14" rx="4" />')
    svg_parts.append('      <rect x="18" y="24" width="22" height="14" rx="4" />')
    svg_parts.append('      <line x1="18" y1="18" x2="28" y2="28" stroke-width="3" />')
    svg_parts.append('    </g>')
    # Label: PT_INTERP: kernel maps ld.so, execution starts in the dynamic linker
    svg_parts.append('    <text font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="838" y="166">PT_INTERP: </tspan>')
    svg_parts.append('      <tspan x="838" dy="26">kernel maps </tspan>')
    svg_parts.append('      <tspan x="838" dy="26">ld.so, </tspan>')
    svg_parts.append('      <tspan x="838" dy="26">execution </tspan>')
    svg_parts.append('      <tspan x="838" dy="26">starts in the </tspan>')
    svg_parts.append('      <tspan x="838" dy="26">dynamic linker</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # Arrow Stage 4 -> Stage 5
    svg_parts.append('  <line x1="956" y1="221" x2="982" y2="221" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')

    # --- STAGE 5: ld.so loads DT_NEEDED libraries, relocates, runs constructors ---
    svg_parts.append('  <!-- Stage 5 (Orange Column Highlight) -->')
    svg_parts.append('  <g id="stage-5">')
    svg_parts.append('    <rect x="982" y="96" width="250" height="250" rx="14" fill="#fff5ea" stroke="#db8129" stroke-width="3" />')
    # Number circle 5 (Orange)
    svg_parts.append('    <circle cx="1014" cy="126" r="20" fill="#db8129" />')
    svg_parts.append('    <text x="1014" y="134" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>')
    # Outline icon: Library books / DSO (48x48, orange)
    svg_parts.append('    <g transform="translate(1160, 105)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_parts.append('      <rect x="6" y="6" width="10" height="34" rx="2" />')
    svg_parts.append('      <rect x="20" y="6" width="10" height="34" rx="2" />')
    svg_parts.append('      <path d="M 34 10 L 42 38" />')
    svg_parts.append('    </g>')
    # Label: ld.so loads DT_NEEDED libraries, relocates, runs constructors
    svg_parts.append('    <text font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="1107" y="172">ld.so loads </tspan>')
    svg_parts.append('      <tspan x="1107" dy="28">DT_NEEDED </tspan>')
    svg_parts.append('      <tspan x="1107" dy="28">libraries, </tspan>')
    svg_parts.append('      <tspan x="1107" dy="28">relocates, runs </tspan>')
    svg_parts.append('      <tspan x="1107" dy="28">constructors</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # Arrow Stage 5 -> Stage 6
    svg_parts.append('  <line x1="1232" y1="221" x2="1264" y2="221" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')

    # --- STAGE 6: _start, __libc_start_main, main ---
    svg_parts.append('  <!-- Stage 6 -->')
    svg_parts.append('  <g id="stage-6">')
    svg_parts.append('    <rect x="1264" y="96" width="296" height="250" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Number circle 6
    svg_parts.append('    <circle cx="1296" cy="126" r="20" fill="#207448" />')
    svg_parts.append('    <text x="1296" y="134" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">6</text>')
    # Outline icon: CPU / application execution (48x48)
    svg_parts.append('    <g transform="translate(1488, 105)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_parts.append('      <rect x="8" y="8" width="32" height="32" rx="4" />')
    svg_parts.append('      <polygon points="20,18 32,24 20,30" fill="#207448" stroke="none" />')
    svg_parts.append('    </g>')
    # Label: _start, __libc_start_main, main
    svg_parts.append('    <text font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="1412" y="196">_start, </tspan>')
    svg_parts.append('      <tspan x="1412" dy="34">__libc_start_main, </tspan>')
    svg_parts.append('      <tspan x="1412" dy="34">main</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # =========================================================================
    # TRANSITION ARROWS FROM PIPELINE TO MATCHING COLUMNS
    # =========================================================================
    # Bracket connecting Stage 1 (center 130) and Stage 2 (center 362) to Column 1 (center 220)
    svg_parts.append('  <!-- Transition Bracket connecting Stage 1 and Stage 2 to Column 1 -->')
    svg_parts.append('  <path d="M 130 346 V 366 H 362 V 346" fill="none" stroke="#207448" stroke-width="3" />')
    svg_parts.append('  <line x1="220" y1="366" x2="220" y2="390" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')

    # From Stage 4 (center x=838) down to Column 2 (center x=610)
    svg_parts.append('  <!-- Transition Arrow to Column 2 -->')
    svg_parts.append('  <path d="M 838 346 V 368 H 610 V 390" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')

    # From Stage 5 (x=1000) straight down to Column 3 (x=1000) (Orange)
    svg_parts.append('  <!-- Transition Arrow to Column 3 (Orange) -->')
    svg_parts.append('  <line x1="1000" y1="346" x2="1000" y2="390" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />')

    # From Stage 6 (x=1390) straight down to Column 4 (x=1390)
    svg_parts.append('  <!-- Transition Arrow to Column 4 -->')
    svg_parts.append('  <line x1="1390" y1="346" x2="1390" y2="390" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')

    # =========================================================================
    # ROW 2: FOUR MATCHING COLUMNS FOR ERROR MESSAGES & FIRST CHECKS
    # Column 1 (Stage 1/2): x=40,   w=360, right=400
    # Column 2 (Stage 4):   x=440,  w=340, right=780
    # Column 3 (Stage 5):   x=820,  w=360, right=1180 (Orange)
    # Column 4 (Stage 6):   x=1220, w=340, right=1560
    # Outer container y = 390 to 1140 (height = 750)
    # =========================================================================

    # -------------------------------------------------------------------------
    # COLUMN 1: Stage 1/2
    # -------------------------------------------------------------------------
    svg_parts.append('  <!-- Column 1 (Stage 1/2) -->')
    svg_parts.append('  <g id="column-1">')
    svg_parts.append('    <rect x="40" y="390" width="360" height="740" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')

    # Card 1.1: Exec format error (wrong CPU architecture such as x86-64 on aarch64, or a script without shebang)
    svg_parts.append('    <rect x="58" y="414" width="324" height="216" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg_parts.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="220" y="448">Exec format error </tspan>')
    svg_parts.append('      <tspan x="220" dy="30">(wrong CPU </tspan>')
    svg_parts.append('      <tspan x="220" dy="30">architecture such </tspan>')
    svg_parts.append('      <tspan x="220" dy="30">as x86-64 on </tspan>')
    svg_parts.append('      <tspan x="220" dy="30">aarch64, or a script </tspan>')
    svg_parts.append('      <tspan x="220" dy="30">without shebang)</tspan>')
    svg_parts.append('    </text>')

    # Card 1.2: exit 126 found but not executable
    svg_parts.append('    <rect x="58" y="650" width="324" height="92" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg_parts.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="220" y="690">exit 126 found but </tspan>')
    svg_parts.append('      <tspan x="220" dy="32">not executable</tspan>')
    svg_parts.append('    </text>')

    # Card 1.3: exit 127 not found
    svg_parts.append('    <rect x="58" y="762" width="324" height="68" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg_parts.append('    <text x="220" y="805" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">exit 127 not found</text>')

    # Downward connector to first check
    svg_parts.append('    <line x1="220" y1="850" x2="220" y2="990" stroke="#207448" stroke-width="2.5" stroke-dasharray="6 4" marker-end="url(#arrow-green)" />')

    # First Check 1: file and readelf -h
    svg_parts.append('    <rect x="58" y="990" width="324" height="116" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg_parts.append('    <text x="220" y="1056" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">file and readelf -h</text>')
    svg_parts.append('  </g>')

    # -------------------------------------------------------------------------
    # COLUMN 2: Stage 4
    # -------------------------------------------------------------------------
    svg_parts.append('  <!-- Column 2 (Stage 4) -->')
    svg_parts.append('  <g id="column-2">')
    svg_parts.append('    <rect x="440" y="390" width="340" height="740" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')

    # Card 2.1: bad ELF interpreter / not found for a file that exists (glibc binary on Alpine musl: /lib64/ld-linux-x86-64.so.2 missing)
    svg_parts.append('    <rect x="456" y="414" width="308" height="340" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg_parts.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="610" y="450">bad ELF </tspan>')
    svg_parts.append('      <tspan x="610" dy="30">interpreter / </tspan>')
    svg_parts.append('      <tspan x="610" dy="30">not found for </tspan>')
    svg_parts.append('      <tspan x="610" dy="30">a file that exists </tspan>')
    svg_parts.append('      <tspan x="610" dy="30">(glibc binary on </tspan>')
    svg_parts.append('      <tspan x="610" dy="30">Alpine musl: </tspan>')
    svg_parts.append('      <tspan x="610" dy="30" font-family="monospace">/lib64/ld-linux-</tspan><tspan x="610" dy="30" font-family="monospace">x86-64.so.2 </tspan>')
    svg_parts.append('      <tspan x="610" dy="30">missing)</tspan>')
    svg_parts.append('    </text>')

    # Downward connector to first check
    svg_parts.append('    <line x1="610" y1="800" x2="610" y2="990" stroke="#207448" stroke-width="2.5" stroke-dasharray="6 4" marker-end="url(#arrow-green)" />')

    # First Check 2: readelf -l | grep interpreter
    svg_parts.append('    <rect x="456" y="990" width="308" height="116" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg_parts.append('    <text font-family="monospace" font-size="24" font-weight="bold" fill="#207448" text-anchor="middle">')
    svg_parts.append('      <tspan x="610" y="1042">readelf -l | </tspan>')
    svg_parts.append('      <tspan x="610" dy="32">grep interpreter</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # -------------------------------------------------------------------------
    # COLUMN 3: Stage 5 (ORANGE HIGHLIGHT COLUMN)
    # -------------------------------------------------------------------------
    svg_parts.append('  <!-- Column 3 (Stage 5 - Orange Highlight) -->')
    svg_parts.append('  <g id="column-3">')
    svg_parts.append('    <rect x="820" y="390" width="360" height="740" rx="16" fill="#fff5ea" stroke="#db8129" stroke-width="3" />')

    # Card 3.1: libcuda.so.1: cannot open shared object file
    svg_parts.append('    <rect x="838" y="414" width="324" height="114" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2" />')
    svg_parts.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="1000" y="446">libcuda.so.1: cannot </tspan>')
    svg_parts.append('      <tspan x="1000" dy="30">open shared </tspan>')
    svg_parts.append('      <tspan x="1000" dy="30">object file</tspan>')
    svg_parts.append('    </text>')

    # Card 3.2: error while loading shared libraries: libnccl.so.2
    svg_parts.append('    <rect x="838" y="542" width="324" height="114" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2" />')
    svg_parts.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="1000" y="574">error while loading </tspan>')
    svg_parts.append('      <tspan x="1000" dy="30">shared libraries: </tspan>')
    svg_parts.append('      <tspan x="1000" dy="30" font-family="monospace">libnccl.so.2</tspan>')
    svg_parts.append('    </text>')

    # Card 3.3: version GLIBC_2.34 not found
    svg_parts.append('    <rect x="838" y="670" width="324" height="110" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2" />')
    svg_parts.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="1000" y="702">version </tspan>')
    svg_parts.append('      <tspan x="1000" dy="30">GLIBC_2.34 </tspan>')
    svg_parts.append('      <tspan x="1000" dy="30">not found</tspan>')
    svg_parts.append('    </text>')

    # Card 3.4: version GLIBCXX_3.4.30 not found
    svg_parts.append('    <rect x="838" y="794" width="324" height="110" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2" />')
    svg_parts.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="1000" y="826">version </tspan>')
    svg_parts.append('      <tspan x="1000" dy="30">GLIBCXX_3.4.30 </tspan>')
    svg_parts.append('      <tspan x="1000" dy="30">not found</tspan>')
    svg_parts.append('    </text>')

    # Downward connector to first check (Orange)
    svg_parts.append('    <line x1="1000" y1="918" x2="1000" y2="990" stroke="#db8129" stroke-width="2.5" stroke-dasharray="6 4" marker-end="url(#arrow-orange)" />')

    # First Check 3: ldd, ldconfig -p, LD_DEBUG=libs
    svg_parts.append('    <rect x="838" y="990" width="324" height="116" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2.5" />')
    svg_parts.append('    <text font-family="monospace" font-size="24" font-weight="bold" fill="#db8129" text-anchor="middle">')
    svg_parts.append('      <tspan x="1000" y="1042">ldd, ldconfig -p, </tspan>')
    svg_parts.append('      <tspan x="1000" dy="32">LD_DEBUG=libs</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # -------------------------------------------------------------------------
    # COLUMN 4: Stage 6 and after
    # -------------------------------------------------------------------------
    svg_parts.append('  <!-- Column 4 (Stage 6 and after) -->')
    svg_parts.append('  <g id="column-4">')
    svg_parts.append('    <rect x="1220" y="390" width="340" height="740" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')

    # Card 4.1: CUDA error: no kernel image is available for execution on the device
    svg_parts.append('    <rect x="1236" y="414" width="308" height="196" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg_parts.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="1390" y="448">CUDA error: no </tspan>')
    svg_parts.append('      <tspan x="1390" dy="30">kernel image is </tspan>')
    svg_parts.append('      <tspan x="1390" dy="30">available for </tspan>')
    svg_parts.append('      <tspan x="1390" dy="30">execution on </tspan>')
    svg_parts.append('      <tspan x="1390" dy="30">the device</tspan>')
    svg_parts.append('    </text>')

    # Card 4.2: Illegal instruction (SIGILL, exit 132)
    svg_parts.append('    <rect x="1236" y="626" width="308" height="136" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg_parts.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg_parts.append('      <tspan x="1390" y="666">Illegal </tspan>')
    svg_parts.append('      <tspan x="1390" dy="30">instruction </tspan>')
    svg_parts.append('      <tspan x="1390" dy="30">(SIGILL, exit 132)</tspan>')
    svg_parts.append('    </text>')

    # Card 4.3: segfault exit 139
    svg_parts.append('    <rect x="1236" y="776" width="308" height="68" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg_parts.append('    <text x="1390" y="818" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">segfault exit 139</text>')

    # Downward connector to first check
    svg_parts.append('    <line x1="1390" y1="864" x2="1390" y2="990" stroke="#207448" stroke-width="2.5" stroke-dasharray="6 4" marker-end="url(#arrow-green)" />')

    # First Check 4: strace -f for the last failed call
    svg_parts.append('    <rect x="1236" y="990" width="308" height="116" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg_parts.append('    <text font-family="monospace" font-size="24" font-weight="bold" fill="#207448" text-anchor="middle">')
    svg_parts.append('      <tspan x="1390" y="1042">strace -f for the </tspan>')
    svg_parts.append('      <tspan x="1390" dy="32">last failed call</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)

if __name__ == '__main__':
    content = build_svg()
    with open('output_candidate.svg', 'w') as f:
        f.write(content)
    print("Candidate SVG generated successfully!")
    
    # Render with Chrome
    subprocess.run([
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '--headless=new',
        '--disable-gpu',
        '--hide-scrollbars',
        '--window-size=1600,1180',
        '--screenshot=rendered_output.png',
        'output_candidate.svg'
    ], check=True)
    print("Re-rendered rendered_output.png successfully!")
