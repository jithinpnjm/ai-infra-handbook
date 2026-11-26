import xml.etree.ElementTree as ET
import re

def build_svg():
    svg = []
    H = 1060
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>Checking which variable value is used</title>')
    svg.append('  <desc>Checklist flow for identifying which variable value wins in Ansible, inspecting variable types, rendering templates offline, and debugging when conditions.</desc>')
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5"/>')
    svg.append('')
    svg.append('  <!-- Title (48px bold) -->')
    svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Checking which variable value is used</text>')
    svg.append('')
    
    # ROW 1: Box 1 and Box 2 (y = 110, h = 350)
    # Box 1: x = 40, y = 110, w = 740, h = 350
    svg.append('  <!-- ==================== BOX 1: which value is used ==================== -->')
    svg.append('  <g id="box-1">')
    svg.append('    <rect x="40" y="110" width="740" height="350" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Step Number Circle 1 (r=24)
    svg.append('    <circle cx="78" cy="148" r="24" fill="#207448"/>')
    svg.append('    <text x="78" y="157" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>')
    # Outline Icon: Stack / Layers (56x56) at x = 708
    svg.append('    <g transform="translate(708, 120)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 6 14 L 28 4 L 50 14 L 28 24 Z"/>')
    svg.append('      <path d="M 6 26 L 28 36 L 50 26"/>')
    svg.append('      <path d="M 6 38 L 28 48 L 50 38"/>')
    svg.append('    </g>')
    # Box 1 Title
    svg.append('    <text x="120" y="158" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">which value is used</text>')
    
    # Commands Row 1: ansible-inventory --host and debug var
    svg.append('    <rect x="60" y="196" width="410" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <text x="265" y="231" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">ansible-inventory --host</text>')
    svg.append('    <rect x="486" y="196" width="274" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <text x="623" y="231" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">debug var</text>')
    
    # Commands Row 2: -vvv and grep
    svg.append('    <rect x="60" y="260" width="338" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <text x="229" y="295" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">-vvv</text>')
    svg.append('    <rect x="414" y="260" width="346" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <text x="587" y="295" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">grep</text>')
    
    # Precedence Note Card
    svg.append('    <rect x="60" y="324" width="700" height="116" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <text x="410" y="360" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="410" dy="0">extra vars with -e sit at the top of the stack </tspan>')
    svg.append('      <tspan x="410" dy="34">and role vars/ also beats inventory</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # Box 2: x = 820, y = 110, w = 740, h = 350
    svg.append('  <!-- ==================== BOX 2: type ==================== -->')
    svg.append('  <g id="box-2">')
    svg.append('    <rect x="820" y="110" width="740" height="350" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Step Number Circle 2 (r=24)
    svg.append('    <circle cx="858" cy="148" r="24" fill="#207448"/>')
    svg.append('    <text x="858" y="157" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>')
    # Outline Icon: Data Types / Curly Brackets { } (56x56) at x = 1488
    svg.append('    <g transform="translate(1488, 120)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 18 8 C 12 8 8 14 8 20 C 8 26 4 28 2 28 C 4 28 8 30 8 36 C 8 42 12 48 18 48"/>')
    svg.append('      <path d="M 38 8 C 44 8 48 14 48 20 C 48 26 52 28 54 28 C 52 28 48 30 48 36 C 48 42 44 48 38 48"/>')
    svg.append('      <circle cx="28" cy="28" r="3" fill="#207448"/>')
    svg.append('    </g>')
    # Box 2 Title
    svg.append('    <text x="900" y="158" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">type</text>')
    
    # Box 2 Content Card
    svg.append('    <rect x="840" y="210" width="700" height="210" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <text x="1190" y="295" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1190" dy="0" font-family="monospace">var | type_debug </tspan>')
    svg.append('      <tspan x="1190" dy="44">shows str, int, bool, list, dict</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # ROW 2: Box 3 and Box 4 (y = 500, h = 350)
    # Box 3: x = 40, y = 500, w = 740, h = 350
    svg.append('  <!-- ==================== BOX 3: render template ==================== -->')
    svg.append('  <g id="box-3">')
    svg.append('    <rect x="40" y="500" width="740" height="350" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Step Number Circle 3 (r=24)
    svg.append('    <circle cx="78" cy="538" r="24" fill="#207448"/>')
    svg.append('    <text x="78" y="547" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>')
    # Outline Icon: Document / Template Sheet (56x56) at x = 708
    svg.append('    <g transform="translate(708, 510)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 8 6 L 36 6 L 48 18 L 48 50 L 8 50 Z"/>')
    svg.append('      <polyline points="36,6 36,18 48,18"/>')
    svg.append('      <line x1="16" y1="26" x2="32" y2="26"/>')
    svg.append('      <line x1="16" y1="34" x2="40" y2="34"/>')
    svg.append('      <line x1="16" y1="42" x2="28" y2="42"/>')
    svg.append('    </g>')
    # Box 3 Title
    svg.append('    <text x="120" y="548" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">render template</text>')
    
    # Command Card
    svg.append('    <rect x="60" y="586" width="700" height="114" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <text x="410" y="632" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="410" dy="0">ansible localhost -m template </tspan>')
    svg.append('      <tspan x="410" dy="36">with -e @vars.yml</tspan>')
    svg.append('    </text>')
    
    # Inspect Card
    svg.append('    <rect x="60" y="720" width="700" height="96" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <text x="410" y="776" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">inspect /tmp/out</text>')
    svg.append('  </g>')
    svg.append('')
    
    # Box 4: x = 820, y = 500, w = 740, h = 350
    svg.append('  <!-- ==================== BOX 4: condition ==================== -->')
    svg.append('  <g id="box-4">')
    svg.append('    <rect x="820" y="500" width="740" height="350" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Step Number Circle 4 (r=24)
    svg.append('    <circle cx="858" cy="538" r="24" fill="#207448"/>')
    svg.append('    <text x="858" y="547" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>')
    # Outline Icon: Decision Diamond / Filter (56x56) at x = 1488
    svg.append('    <g transform="translate(1488, 510)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 50 28 L 28 50 L 6 28 Z"/>')
    svg.append('      <circle cx="28" cy="28" r="4" fill="#207448"/>')
    svg.append('    </g>')
    # Box 4 Title
    svg.append('    <text x="900" y="548" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">condition</text>')
    
    # Debug msg Card
    svg.append('    <rect x="840" y="586" width="700" height="104" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <text x="1190" y="646" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">debug msg of the when expression</text>')
    
    # -vv false_condition Card
    svg.append('    <rect x="840" y="710" width="700" height="106" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <text x="1190" y="771" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">-vv false_condition</text>')
    svg.append('  </g>')
    svg.append('')
    
    # EXAMPLE STRIP: x = 40, y = 890, w = 1520, h = 120
    # Orange on the example strip (stroke="#db8129")
    svg.append('  <!-- ==================== EXAMPLE STRIP (Orange) ==================== -->')
    svg.append('  <g id="example-strip">')
    svg.append('    <rect x="40" y="890" width="1520" height="120" rx="14" fill="#fff9f5" stroke="#db8129" stroke-width="3"/>')
    # Warning / Info Icon (56x56) at x = 68
    svg.append('    <g transform="translate(68, 922)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 50 46 L 6 46 Z"/>')
    svg.append('      <line x1="28" y1="20" x2="28" y2="32"/>')
    svg.append('      <circle cx="28" cy="40" r="2" fill="#207448"/>')
    svg.append('    </g>')
    svg.append('    <text x="840" y="946" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="840" dy="0">gpu_count 8 from -e is a number, </tspan>')
    svg.append('      <tspan x="840" dy="36">from a CSV it is the text 8 and the when comparison fails</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('</svg>')
    
    return "\n".join(svg)

svg_content = build_svg()
with open("test_candidate_val.svg", "w") as f:
    f.write(svg_content)
print("Saved test_candidate_val.svg successfully.")
