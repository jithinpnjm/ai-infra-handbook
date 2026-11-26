#!/usr/bin/env python3

def build_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>Reading a wheel filename and deciding between wheel and sdist</title>')
    svg.append('  <desc>Visual infographic explaining how to read a Python wheel filename, understand tag variants, and decide whether pip can install a pre-built wheel or must build from sdist.</desc>')
    
    # Defs: arrowheads
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="10" markerHeight="10" orient="auto-start-reverse">')
    svg.append('      <path d="M 1 2 L 10 6 L 1 10 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="10" markerHeight="10" orient="auto-start-reverse">')
    svg.append('      <path d="M 1 2 L 10 6 L 1 10 Z" fill="#db8129" />')
    svg.append('    </marker>')
    svg.append('  </defs>')

    # Background
    svg.append('  <!-- Canvas Background -->')
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')

    # Title (48px bold, wrapped onto two lines so it fits comfortably)
    svg.append('  <!-- Infographic Title -->')
    svg.append('  <text x="800" y="44" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Reading a wheel filename </tspan>')
    svg.append('    <tspan x="800" dy="50">and deciding between wheel and sdist</tspan>')
    svg.append('  </text>')

    # =========================================================================
    # SECTION 1: Wheel Filename Anatomy (y = 110 to 290, height = 180)
    # =========================================================================
    svg.append('  <!-- ==================== SECTION 1: FILENAME ANATOMY ==================== -->')
    svg.append('  <g id="section-anatomy">')
    svg.append('    <rect x="40" y="110" width="1520" height="180" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <rect x="40" y="110" width="1520" height="78" rx="16" fill="#e8f1ea" />')
    svg.append('    <line x1="40" y1="188" x2="1560" y2="188" stroke="#207448" stroke-width="1.5" />')

    # Icon: Wheel / Archive Outline (56x56) at x=60, y=120
    svg.append('    <g transform="translate(60, 120)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="24" />')
    svg.append('      <circle cx="28" cy="28" r="8" fill="#ffffff" />')
    svg.append('      <line x1="28" y1="4" x2="28" y2="20" />')
    svg.append('      <line x1="28" y1="36" x2="28" y2="52" />')
    svg.append('      <line x1="4" y1="28" x2="20" y2="28" />')
    svg.append('      <line x1="36" y1="28" x2="52" y2="28" />')
    svg.append('    </g>')

    # Format line (monospace 24px)
    svg.append('    <text x="800" y="150" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">name-version-pythontag-abitag-platformtag</text>')
    
    # Filename line (monospace 24px)
    svg.append('    <text x="800" y="178" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.whl</text>')

    # Five piece boxes (y = 192, height = 88)
    # Piece 1: numpy: name (x = 60, w = 190)
    svg.append('    <g id="piece-1">')
    svg.append('      <rect x="60" y="192" width="190" height="88" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('      <text x="155" y="232" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="155" dy="0" font-family="monospace" font-weight="bold" fill="#207448">numpy: </tspan>')
    svg.append('        <tspan x="155" dy="26">name</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Piece 2: 1.26.4: version (x = 265, w = 190)
    svg.append('    <g id="piece-2">')
    svg.append('      <rect x="265" y="192" width="190" height="88" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('      <text x="360" y="232" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="360" dy="0" font-family="monospace" font-weight="bold" fill="#207448">1.26.4: </tspan>')
    svg.append('        <tspan x="360" dy="26">version</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Piece 3: cp311: Python tag (CPython 3.11) (x = 470, w = 310)
    svg.append('    <g id="piece-3">')
    svg.append('      <rect x="470" y="192" width="310" height="88" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('      <text x="625" y="232" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="625" dy="0" font-weight="bold" fill="#207448">cp311: Python tag </tspan>')
    svg.append('        <tspan x="625" dy="26">(CPython 3.11)</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Piece 4: cp311: ABI tag (x = 795, w = 190)
    svg.append('    <g id="piece-4">')
    svg.append('      <rect x="795" y="192" width="190" height="88" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('      <text x="890" y="232" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="890" dy="0" font-family="monospace" font-weight="bold" fill="#207448">cp311: </tspan>')
    svg.append('        <tspan x="890" dy="26">ABI tag</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Piece 5: manylinux_2_17_x86_64: platform tag (x86_64 Linux, glibc-compatible) (x = 1000, w = 540)
    svg.append('    <g id="piece-5">')
    svg.append('      <rect x="1000" y="192" width="540" height="88" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('      <text x="1270" y="232" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="1270" dy="0" font-weight="bold" fill="#207448">manylinux_2_17_x86_64: platform tag </tspan>')
    svg.append('        <tspan x="1270" dy="26">(x86_64 Linux, glibc-compatible)</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')
    svg.append('  </g>')

    # =========================================================================
    # SECTION 2: Variants Strip (y = 330 to 595, height = 265)
    # =========================================================================
    svg.append('  <!-- ==================== SECTION 2: VARIANTS STRIP ==================== -->')
    svg.append('  <g id="section-variants">')
    svg.append('    <rect x="40" y="330" width="1520" height="265" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    
    # Icon: Architecture / Tags Outline (56x56) at x=56, y=434
    svg.append('    <g transform="translate(56, 434)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="8" width="40" height="40" rx="6" />')
    svg.append('      <path d="M 20 8 L 20 4 M 28 8 L 28 4 M 36 8 L 36 4" />')
    svg.append('      <path d="M 20 48 L 20 52 M 28 48 L 28 52 M 36 48 L 36 52" />')
    svg.append('      <path d="M 8 20 L 4 20 M 8 28 L 4 28 M 8 36 L 4 36" />')
    svg.append('      <path d="M 48 20 L 52 20 M 48 28 L 52 28 M 48 36 L 52 36" />')
    svg.append('    </g>')

    # 6 variants in 2 columns of 3 rows:
    # Col 1: x = 125, w = 700
    # Col 2: x = 845, w = 700
    # Row 1: y = 338, h = 84
    # Row 2: y = 428, h = 84
    # Row 3: y = 518, h = 84

    # Variant 1: py3-none-any: pure Python, installs anywhere
    svg.append('    <g id="var-1">')
    svg.append('      <rect x="125" y="338" width="700" height="84" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.2" />')
    svg.append('      <text x="475" y="378" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="475" dy="0" font-family="monospace" font-weight="bold" fill="#207448">py3-none-any: </tspan>')
    svg.append('        <tspan x="475" dy="22">pure Python, installs anywhere</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Variant 2: manylinux: runs on most Linux distributions with a compatible glibc
    svg.append('    <g id="var-2">')
    svg.append('      <rect x="845" y="338" width="700" height="84" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.2" />')
    svg.append('      <text x="1195" y="378" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="1195" dy="0" font-weight="bold" fill="#207448">manylinux: runs on most Linux distributions </tspan>')
    svg.append('        <tspan x="1195" dy="22">with a compatible glibc</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Variant 3: musllinux: Alpine, which uses musl instead
    svg.append('    <g id="var-3">')
    svg.append('      <rect x="125" y="428" width="700" height="84" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.2" />')
    svg.append('      <text x="475" y="468" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="475" dy="0" font-family="monospace" font-weight="bold" fill="#207448">musllinux: </tspan>')
    svg.append('        <tspan x="475" dy="22">Alpine, which uses musl instead</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Variant 4: abi3: the stable ABI
    svg.append('    <g id="var-4">')
    svg.append('      <rect x="845" y="428" width="700" height="84" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.2" />')
    svg.append('      <text x="1195" y="468" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="1195" dy="0" font-family="monospace" font-weight="bold" fill="#207448">abi3: </tspan>')
    svg.append('        <tspan x="1195" dy="22">the stable ABI</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Variant 5: +cu121: local version label (PEP 440) marking a CUDA build, used by PyTorch index wheels
    svg.append('    <g id="var-5">')
    svg.append('      <rect x="125" y="518" width="700" height="84" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.2" />')
    svg.append('      <text x="475" y="558" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="475" dy="0" font-weight="bold" fill="#207448">+cu121: local version label (PEP 440) marking </tspan>')
    svg.append('        <tspan x="475" dy="22">a CUDA build, used by PyTorch index wheels</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Variant 6: aarch64: Grace and other ARM hosts, some packages have no wheels
    svg.append('    <g id="var-6">')
    svg.append('      <rect x="845" y="518" width="700" height="84" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.2" />')
    svg.append('      <text x="1195" y="558" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="1195" dy="0" font-weight="bold" fill="#207448">aarch64: Grace and other ARM hosts, </tspan>')
    svg.append('        <tspan x="1195" dy="22">some packages have no wheels</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')
    svg.append('  </g>')

    # =========================================================================
    # SECTION 3: Decision Flow (y = 635 to 830, height = 195)
    # =========================================================================
    svg.append('  <!-- ==================== SECTION 3: DECISION FLOW ==================== -->')
    svg.append('  <g id="section-decision">')
    
    # Decision Question Box: pip finds a compatible wheel?
    # x = 40, y = 635, width = 450, height = 185
    svg.append('    <g id="box-decision">')
    svg.append('      <rect x="40" y="635" width="450" height="185" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    # Icon: Search / Filter (56x56) at x = 60, y = 700
    svg.append('      <g transform="translate(60, 700)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('        <circle cx="24" cy="24" r="16" />')
    svg.append('        <line x1="36" y1="36" x2="50" y2="50" />')
    svg.append('        <circle cx="24" cy="24" r="7" stroke-dasharray="4 3" />')
    svg.append('      </g>')
    svg.append('      <text x="280" y="715" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    svg.append('        <tspan x="280" dy="0">pip finds a </tspan>')
    svg.append('        <tspan x="280" dy="38">compatible wheel?</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Branch YES: unzip, no build step, fast
    # Target Box: x = 620, y = 635, width = 940, height = 70
    svg.append('    <g id="box-yes">')
    svg.append('      <rect x="620" y="635" width="940" height="70" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Icon: Fast unpack (56x56) at x = 640, y = 642
    svg.append('      <g transform="translate(640, 642)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('        <path d="M 8 16 L 24 16 L 28 24 L 48 24 L 48 48 L 8 48 Z" />')
    svg.append('        <path d="M 28 28 L 36 36 L 48 24" stroke="#207448" />')
    svg.append('      </g>')
    svg.append('      <text x="1100" y="679" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">unzip, no build step, fast</text>')
    svg.append('    </g>')

    # Arrow 1: YES (Green)
    # From x = 490, y = 670 to x = 620, y = 670
    svg.append('    <line x1="490" y1="670" x2="620" y2="670" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append('    <text x="555" y="658" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">yes</text>')

    # Branch NO (orange): builds from the sdist...
    # Target Box: x = 620, y = 716, width = 940, height = 114
    svg.append('    <g id="box-no">')
    svg.append('      <rect x="620" y="716" width="940" height="114" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="2.5" />')
    # Icon: Compiler / Slow build (56x56) at x = 640, y = 745 in ORANGE
    svg.append('      <g transform="translate(640, 745)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('        <rect x="6" y="8" width="44" height="40" rx="6" />')
    svg.append('        <path d="M 16 22 L 24 28 L 16 34" />')
    svg.append('        <line x1="28" y1="34" x2="38" y2="34" />')
    svg.append('      </g>')
    svg.append('      <text x="1100" y="756" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="1100" dy="0" font-weight="bold" fill="#db8129">builds from the sdist: needs compilers and headers; </tspan>')
    svg.append('        <tspan x="1100" dy="24">the usual reason an install takes 10 minutes or </tspan>')
    svg.append('        <tspan x="1100" dy="24">fails in a slim container</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Arrow 2: NO (Orange)
    # From x = 490, y = 773 to x = 620, y = 773
    svg.append('    <line x1="490" y1="773" x2="620" y2="773" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />')
    svg.append('    <text x="555" y="761" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">no</text>')
    svg.append('  </g>')

    # =========================================================================
    # SECTION 4: Tool Line & Early Check (y = 870 to 1055, height = 185)
    # =========================================================================
    svg.append('  <!-- ==================== SECTION 4: TOOL LINE & EARLY CHECK ==================== -->')
    svg.append('  <g id="section-tools">')
    svg.append('    <rect x="40" y="870" width="1520" height="185" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')

    # Tool 1: python -m build makes dist/myops-0.3.1.tar.gz (sdist) and dist/myops-0.3.1-py3-none-any.whl (wheel)
    # y = 878, height = 84
    svg.append('    <g id="tool-1">')
    svg.append('      <rect x="56" y="878" width="1488" height="84" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.2" />')
    svg.append('      <text x="800" y="918" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('        <tspan x="800" dy="0">python -m build makes dist/myops-0.3.1.tar.gz (sdist) </tspan>')
    svg.append('        <tspan x="800" dy="22">and dist/myops-0.3.1-py3-none-any.whl (wheel)</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Tool 2: python -m pip debug --verbose lists the supported tags
    # x = 56, y = 968, width = 734, height = 80
    svg.append('    <g id="tool-2">')
    svg.append('      <rect x="56" y="968" width="734" height="80" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.2" />')
    svg.append('      <text x="423" y="1008" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="423" dy="0" font-family="monospace" font-weight="bold" fill="#207448">python -m pip debug --verbose </tspan>')
    svg.append('        <tspan x="423" dy="22">lists the supported tags</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Tool 3: pip download --only-binary=:all: --platform manylinux2014_aarch64 ...
    # x = 810, y = 968, width = 734, height = 80
    svg.append('    <g id="tool-3">')
    svg.append('      <rect x="810" y="968" width="734" height="80" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.2" />')
    svg.append('      <text x="1177" y="1008" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('        <tspan x="1177" dy="0" fill="#207448">pip download --only-binary=:all: </tspan>')
    svg.append('        <tspan x="1177" dy="22">--platform manylinux2014_aarch64 ...</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')
    svg.append('  </g>')

    # =========================================================================
    # SECTION 5: Bottom Takeaway Bar (y = 1095 to 1160, height = 65)
    # =========================================================================
    svg.append('  <!-- ==================== SECTION 5: BOTTOM TAKEAWAY BAR ==================== -->')
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1095" width="1520" height="65" rx="12" fill="#207448" />')
    svg.append('    <text x="800" y="1137" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Check the tags of every wheel you plan to ship against the machines that will install it</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return "\n".join(svg)

if __name__ == "__main__":
    content = build_svg()
    with open("wheel_decision.svg", "w", encoding="utf-8") as f:
        f.write(content)
    print("Generated wheel_decision.svg successfully.")
