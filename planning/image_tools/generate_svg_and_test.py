import re
import xml.etree.ElementTree as ET

def build_svg():
    title_text = "Import and install errors: symptom, likely cause, first fix"
    
    rows_data = [
        # Row 1
        (
            "ModuleNotFoundError: No module named x",
            ["ModuleNotFoundError:", "No module named x"],
            "wrong interpreter or venv, not installed, typo, wrong directory",
            ["wrong interpreter or venv,", "not installed, typo,", "wrong directory"],
            "which python, python -m pip show x, activate venv, print sys.path",
            ["which python, python -m pip", "show x, activate venv,", "print sys.path"],
            96, True
        ),
        # Row 2
        (
            "ImportError: cannot import name y from x",
            ["ImportError: cannot import", "name y from x"],
            "version mismatch, circular import or shadowing",
            ["version mismatch, circular", "import or shadowing"],
            "check x.__file__ and version, look for local x.py",
            ["check x.__file__ and version,", "look for local x.py"],
            68, False
        ),
        # Row 3
        (
            "AttributeError: module x has no attribute",
            ["AttributeError: module x", "has no attribute"],
            "shadowed module (random.py, requests.py) or old version",
            ["shadowed module (random.py,", "requests.py) or old version"],
            "rename file, remove __pycache__",
            ["rename file, remove __pycache__"],
            68, False
        ),
        # Row 4
        (
            "attempted relative import with no known parent package",
            ["attempted relative import", "with no known parent package"],
            "running a package file as a script",
            ["running a package file", "as a script"],
            "python -m pkg.module",
            ["python -m pkg.module"],
            68, False
        ),
        # Row 5
        (
            "externally-managed-environment",
            ["externally-managed-environment"],
            "PEP 668 on system Python",
            ["PEP 668 on system Python"],
            "venv, pipx, distribution package",
            ["venv, pipx, distribution package"],
            56, False
        ),
        # Row 6
        (
            "ResolutionImpossible",
            ["ResolutionImpossible"],
            "conflicting constraints",
            ["conflicting constraints"],
            "read the chain, relax pins, pip install -vv, separate environments",
            ["read the chain, relax pins, pip", "install -vv, separate environments"],
            68, False
        ),
        # Row 7
        (
            "Works in shell, fails in cron or systemd",
            ["Works in shell, fails", "in cron or systemd"],
            "different PATH, interpreter or env",
            ["different PATH, interpreter", "or env"],
            "absolute venv python path, Environment=, log sys.executable",
            ["absolute venv python path,", "Environment=, log sys.executable"],
            68, False
        ),
        # Row 8
        (
            "GLIBC_2.xx not found or illegal instruction",
            ["GLIBC_2.xx not found or", "illegal instruction"],
            "wheel built for newer glibc or CPU",
            ["wheel built for newer", "glibc or CPU"],
            "matching manylinux tag or container, build from source",
            ["matching manylinux tag or", "container, build from source"],
            68, False
        ),
        # Row 9
        (
            "CUDA driver version is insufficient",
            ["CUDA driver version is", "insufficient"],
            "wheel CUDA runtime newer than driver",
            ["wheel CUDA runtime", "newer than driver"],
            "upgrade driver or use cu118",
            ["upgrade driver or use cu118"],
            68, False
        ),
        # Row 10
        (
            "numpy.core.multiarray failed to import",
            ["numpy.core.multiarray", "failed to import"],
            "NumPy 1 and 2 mismatch",
            ["NumPy 1 and 2 mismatch"],
            "align versions, rebuild extensions",
            ["align versions, rebuild extensions"],
            68, False
        ),
        # Row 11
        (
            "Slow imports or startup",
            ["Slow imports or startup"],
            "heavy top-level imports, network filesystem",
            ["heavy top-level imports,", "network filesystem"],
            "-X importtime, lazy imports, local copy, container",
            ["-X importtime, lazy imports,", "local copy, container"],
            68, False
        ),
        # Row 12
        (
            "Different behaviour on two nodes",
            ["Different behaviour on", "two nodes"],
            "unpinned dependency drift",
            ["unpinned dependency drift"],
            "lockfile, hashes, image digests, pip freeze diff",
            ["lockfile, hashes, image digests,", "pip freeze diff"],
            68, False
        )
    ]

    strip_lines = [
        "pip debug --verbose, pipdeptree, pip index versions pkg,",
        "ldd on torch libraries, strace -f -e trace=openat python -c import x"
    ]
    bottom_bar_text = "Read the error line first, then find the matching row"

    col1_w = 480
    col2_w = 470
    col3_w = 570
    total_w = 1520
    table_x = 40
    table_y = 135

    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>Import and install errors: symptom, likely cause, first fix</title>')
    svg.append('  <desc>A three-column diagnostic matrix for Python import and install errors mapping symptoms to likely causes and first fixes, with deeper diagnostic tools.</desc>')
    svg.append('')
    svg.append('  <!-- Canvas Background -->')
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    svg.append('')
    svg.append('  <!-- Title: 48px bold (wrapped to avoid canvas overflow) -->')
    svg.append('  <text x="800" y="52" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Import and install errors:</tspan>')
    svg.append('    <tspan x="800" dy="52">symptom, likely cause, first fix</tspan>')
    svg.append('  </text>')
    svg.append('')

    # Table container
    total_table_h = sum(r[7] for r in rows_data)
    svg.append('  <!-- ==================== TABLE CONTAINER ==================== -->')
    svg.append(f'  <rect x="{table_x}" y="{table_y}" width="{total_w}" height="{total_table_h}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('')

    cur_y = table_y
    for idx, (f1, l1, f2, l2, f3, l3, rh, is_orange) in enumerate(rows_data, 1):
        bg = "#fff7f0" if is_orange else ("#ffffff" if idx % 2 == 1 else "#e8f1ea")
        svg.append(f'  <!-- Row {idx} Background -->')
        svg.append(f'  <rect x="{table_x}" y="{cur_y}" width="{total_w}" height="{rh}" fill="{bg}"/>')
        
        if is_orange:
            # Highlight most important row with orange accent bar
            svg.append(f'  <rect x="{table_x}" y="{cur_y}" width="8" height="{rh}" fill="#db8129"/>')
        
        if idx < len(rows_data):
            svg.append(f'  <line x1="{table_x}" y1="{cur_y + rh}" x2="{table_x + total_w}" y2="{cur_y + rh}" stroke="#207448" stroke-width="1" opacity="0.25"/>')

        # Vertically center text in row:
        # Col 1:
        n1 = len(l1)
        h1 = (n1 - 1) * 28 + 18
        y1 = cur_y + (rh - h1) / 2 + 18
        c1_color = "#db8129" if is_orange else "#207448"
        x1 = table_x + 24
        svg.append(f'  <text x="{x1}" y="{y1:.1f}" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="{c1_color}">')
        for j, line in enumerate(l1):
            dy = 0 if j == 0 else 28
            svg.append(f'    <tspan x="{x1}" dy="{dy}">{line}</tspan>')
        svg.append('  </text>')

        # Col 2:
        n2 = len(l2)
        h2 = (n2 - 1) * 28 + 18
        y2 = cur_y + (rh - h2) / 2 + 18
        x2 = table_x + col1_w + 24
        svg.append(f'  <text x="{x2}" y="{y2:.1f}" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">')
        for j, line in enumerate(l2):
            dy = 0 if j == 0 else 28
            svg.append(f'    <tspan x="{x2}" dy="{dy}">{line}</tspan>')
        svg.append('  </text>')

        # Col 3:
        n3 = len(l3)
        h3 = (n3 - 1) * 28 + 18
        y3 = cur_y + (rh - h3) / 2 + 18
        x3 = table_x + col1_w + col2_w + 24
        svg.append(f'  <text x="{x3}" y="{y3:.1f}" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
        for j, line in enumerate(l3):
            dy = 0 if j == 0 else 28
            svg.append(f'    <tspan x="{x3}" dy="{dy}">{line}</tspan>')
        svg.append('  </text>')
        svg.append('')

        cur_y += rh

    # Vertical column dividers
    div1_x = table_x + col1_w
    div2_x = div1_x + col2_w
    svg.append('  <!-- Vertical Column Dividers -->')
    svg.append(f'  <line x1="{div1_x}" y1="{table_y}" x2="{div1_x}" y2="{cur_y}" stroke="#207448" stroke-width="1.5" opacity="0.4"/>')
    svg.append(f'  <line x1="{div2_x}" y1="{table_y}" x2="{div2_x}" y2="{cur_y}" stroke="#207448" stroke-width="1.5" opacity="0.4"/>')
    svg.append('')

    # Deeper tools strip
    strip_y = cur_y + 18
    strip_h = 82
    svg.append('  <!-- ==================== DEEPER TOOLS STRIP ==================== -->')
    svg.append(f'  <rect x="{table_x}" y="{strip_y}" width="{total_w}" height="{strip_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Terminal/tools icon beside strip
    # Icon placed at x=60, y=strip_y + 13 (approx 56px, green stroke 4)
    # Wrench/terminal icon:
    svg.append(f'  <g transform="translate(60, {strip_y + 13})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="8" width="48" height="40" rx="6"/>')
    svg.append('    <polyline points="14,24 22,30 14,36"/>')
    svg.append('    <line x1="28" y1="36" x2="40" y2="36"/>')
    svg.append('  </g>')
    # Text start at x=135
    strip_text_x = 135
    svg.append(f'  <text x="{strip_text_x}" y="{strip_y + 35}" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg.append(f'    <tspan x="{strip_text_x}" dy="0">{strip_lines[0]}</tspan>')
    svg.append(f'    <tspan x="{strip_text_x}" dy="30">{strip_lines[1]}</tspan>')
    svg.append('  </text>')
    svg.append('')

    # Bottom bar
    bar_y = strip_y + strip_h + 18
    bar_h = 58
    svg.append('  <!-- ==================== BOTTOM BAR ==================== -->')
    svg.append(f'  <rect x="{table_x}" y="{bar_y}" width="{total_w}" height="{bar_h}" rx="10" fill="#207448"/>')
    svg.append(f'  <text x="800" y="{bar_y + 39}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#ffffff">{bottom_bar_text}</text>')
    svg.append('</svg>')

    return "\n".join(svg)

svg_content = build_svg()
with open("test_generated.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print("Saved test_generated.svg successfully!")
