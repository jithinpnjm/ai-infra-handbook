import xml.etree.ElementTree as ET
import re

def create_svg():
    W = 1600
    H = 1200
    
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    parts.append('  <title>Layering timeout, retry, breaker and bulkhead</title>')
    parts.append('  <desc>Visual explanation of layering timeout, retry, circuit breaker, and bulkhead patterns around a dependency call, with breaker states and recovery.</desc>')
    
    # defs
    parts.append('  <defs>')
    parts.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    parts.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    parts.append('    </marker>')
    parts.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    parts.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    parts.append('    </marker>')
    parts.append('  </defs>')
    
    # Background
    parts.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')
    
    # Main Title (48px bold)
    parts.append('  <text x="800" y="54" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Layering timeout, retry, breaker and bulkhead</text>')
    
    # ========================================================
    # LEFT COLUMN: NESTED BOXES (x=40, y=95, w=760, h=610)
    # Outside to inside: timeout -> retry -> circuit breaker -> bulkhead -> call to the dependency
    # ========================================================
    
    # 1. TIMEOUT (Outer box)
    # x=40, y=95, w=760, h=610
    parts.append('  <!-- 1. TIMEOUT (Outer Box) -->')
    parts.append('  <g id="box-timeout">')
    parts.append('    <rect x="40" y="95" width="760" height="610" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    parts.append('    <g transform="translate(65, 108)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <circle cx="24" cy="24" r="20" />')
    parts.append('      <polyline points="24,12 24,24 34,24" />')
    parts.append('    </g>')
    parts.append('    <text x="125" y="142" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">timeout</text>')
    parts.append('  </g>')
    
    # 2. RETRY (Inside timeout)
    # x=70, y=165, w=700, h=515
    parts.append('  <!-- 2. RETRY -->')
    parts.append('  <g id="box-retry">')
    parts.append('    <rect x="70" y="165" width="700" height="515" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    parts.append('    <g transform="translate(95, 178)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <path d="M 40 20 A 16 16 0 1 0 42 28" />')
    parts.append('      <polyline points="32,8 42,20 30,22" />')
    parts.append('    </g>')
    parts.append('    <text x="155" y="212" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">retry</text>')
    parts.append('  </g>')
    
    # 3. CIRCUIT BREAKER (Inside retry)
    # x=100, y=235, w=640, h=420
    parts.append('  <!-- 3. CIRCUIT BREAKER -->')
    parts.append('  <g id="box-circuit-breaker">')
    parts.append('    <rect x="100" y="235" width="640" height="420" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    parts.append('    <g transform="translate(125, 248)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <circle cx="10" cy="36" r="4" fill="#207448" />')
    parts.append('      <circle cx="38" cy="36" r="4" fill="#207448" />')
    parts.append('      <line x1="10" y1="32" x2="32" y2="14" />')
    parts.append('    </g>')
    parts.append('    <text x="185" y="282" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">circuit breaker</text>')
    parts.append('  </g>')
    
    # 4. BULKHEAD (Inside circuit breaker)
    # x=130, y=305, w=580, h=325
    parts.append('  <!-- 4. BULKHEAD -->')
    parts.append('  <g id="box-bulkhead">')
    parts.append('    <rect x="130" y="305" width="580" height="325" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    parts.append('    <g transform="translate(155, 318)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <path d="M 6 8 L 24 3 L 42 8 L 42 26 C 42 38 24 45 24 45 C 24 45 6 38 6 26 Z" />')
    parts.append('      <line x1="12" y1="18" x2="36" y2="18" />')
    parts.append('      <line x1="15" y1="28" x2="33" y2="28" />')
    parts.append('    </g>')
    parts.append('    <text x="215" y="352" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">bulkhead</text>')
    parts.append('  </g>')
    
    # 5. CALL TO THE DEPENDENCY (Innermost)
    # x=160, y=380, w=520, h=220
    parts.append('  <!-- 5. CALL TO THE DEPENDENCY -->')
    parts.append('  <g id="box-call">')
    parts.append('    <rect x="160" y="380" width="520" height="220" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" stroke-dasharray="6 4" />')
    parts.append('    <g transform="translate(396, 410)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <ellipse cx="24" cy="12" rx="20" ry="7" />')
    parts.append('      <path d="M 4 12 L 4 36 C 4 42 13 46 24 46 C 35 46 44 42 44 36 L 44 12" />')
    parts.append('      <path d="M 4 24 C 4 30 13 34 24 34 C 35 34 44 30 44 24" />')
    parts.append('    </g>')
    parts.append('    <text x="420" y="505" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">call to the dependency</text>')
    parts.append('  </g>')
    
    # ========================================================
    # RIGHT COLUMN: CONTEXT CARDS (x=840, y=95, w=720)
    # Spacing between left (800) and right (840) is exactly 40px!
    # ========================================================
    
    # Card 1: Reason (y=95, h=120)
    # 'when a dependency is down, retries make it worse because every caller keeps adding load'
    parts.append('  <!-- Reason Card -->')
    parts.append('  <g id="card-reason">')
    parts.append('    <rect x="840" y="95" width="720" height="120" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    parts.append('    <g transform="translate(865, 127)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <path d="M 24 4 L 46 44 L 2 44 Z" />')
    parts.append('      <line x1="24" y1="18" x2="24" y2="30" />')
    parts.append('      <circle cx="24" cy="37" r="1.5" fill="#207448" />')
    parts.append('    </g>')
    parts.append('    <text x="935" y="142" font-family="sans-serif" font-size="24" fill="#303a36">')
    parts.append('      <tspan x="935" dy="0">when a dependency is down, retries</tspan>')
    parts.append('      <tspan x="935" dy="32">make it worse because every caller</tspan>')
    parts.append('      <tspan x="935" dy="32">keeps adding load</tspan>')
    parts.append('    </text>')
    parts.append('  </g>')
    
    # Card 2: Bulkhead description (y=235, h=170)
    # 'limits how many calls run at once against one dependency, using a semaphore (a counter that caps simultaneous work), so one slow service cannot consume every thread'
    parts.append('  <!-- Bulkhead Description Card -->')
    parts.append('  <g id="card-bulkhead-desc">')
    parts.append('    <rect x="840" y="235" width="720" height="170" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    parts.append('    <g transform="translate(865, 290)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <line x1="8" y1="46" x2="8" y2="6" />')
    parts.append('      <circle cx="8" cy="6" r="3.5" fill="#207448" />')
    parts.append('      <line x1="8" y1="16" x2="40" y2="4" />')
    parts.append('      <line x1="8" y1="26" x2="36" y2="14" />')
    parts.append('    </g>')
    parts.append('    <text x="935" y="272" font-family="sans-serif" font-size="24" fill="#303a36">')
    parts.append('      <tspan x="935" dy="0">limits how many calls run at once</tspan>')
    parts.append('      <tspan x="935" dy="28">against one dependency, using a semaphore</tspan>')
    parts.append('      <tspan x="935" dy="28">(a counter that caps simultaneous work),</tspan>')
    parts.append('      <tspan x="935" dy="28">so one slow service cannot consume</tspan>')
    parts.append('      <tspan x="935" dy="28">every thread</tspan>')
    parts.append('    </text>')
    parts.append('  </g>')
    
    # Card 3: Message Example (y=425, h=130)
    # 'fleet API unavailable, breaker open for 30 s'
    # 'so the operator knows what happened'
    parts.append('  <!-- Message Example Card -->')
    parts.append('  <g id="card-message-example">')
    parts.append('    <rect x="840" y="425" width="720" height="130" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    parts.append('    <g transform="translate(865, 465)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <rect x="4" y="6" width="42" height="32" rx="6" />')
    parts.append('      <polyline points="6,10 25,24 44,10" />')
    parts.append('    </g>')
    parts.append('    <text x="935" y="462" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">')
    parts.append('      <tspan x="935" dy="0">fleet API unavailable,</tspan>')
    parts.append('      <tspan x="935" dy="30">breaker open for 30 s</tspan>')
    parts.append('    </text>')
    parts.append('    <text x="935" y="530" font-family="sans-serif" font-size="24" fill="#303a36">so the operator knows what happened</text>')
    parts.append('  </g>')
    
    # Row 4: Analogy (left) & Libraries (right) (y=575, h=130)
    # Analogy 'a fuse in a wall' (x=840, w=290)
    parts.append('  <!-- Analogy Card -->')
    parts.append('  <g id="card-analogy">')
    parts.append('    <rect x="840" y="575" width="290" height="130" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    parts.append('    <g transform="translate(965, 590)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <rect x="6" y="10" width="28" height="16" rx="4" />')
    parts.append('      <line x1="2" y1="18" x2="6" y2="18" />')
    parts.append('      <line x1="34" y1="18" x2="38" y2="18" />')
    parts.append('    </g>')
    parts.append('    <text x="985" y="655" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#207448">a fuse in a wall</text>')
    parts.append('  </g>')
    
    # Libraries 'pybreaker, circuitbreaker, or a class of about 30 lines' (x=1150, w=410)
    parts.append('  <!-- Libraries Card -->')
    parts.append('  <g id="card-libraries">')
    parts.append('    <rect x="1150" y="575" width="410" height="130" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    parts.append('    <g transform="translate(1170, 615)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <rect x="4" y="6" width="36" height="34" rx="6" />')
    parts.append('      <path d="M 12 18 L 18 23 L 12 28" />')
    parts.append('      <line x1="22" y1="28" x2="30" y2="28" />')
    parts.append('    </g>')
    parts.append('    <text x="1225" y="608" font-family="sans-serif" font-size="24" fill="#303a36">')
    parts.append('      <tspan x="1225" dy="0">pybreaker,</tspan>')
    parts.append('      <tspan x="1225" dy="26">circuitbreaker,</tspan>')
    parts.append('      <tspan x="1225" dy="26">or a class of</tspan>')
    parts.append('      <tspan x="1225" dy="26">about 30 lines</tspan>')
    parts.append('    </text>')
    parts.append('  </g>')
    
    # ========================================================
    # BOTTOM CONTAINER: BREAKER STATE STRIP (x=40, y=725, w=1520, h=360)
    # ========================================================
    parts.append('  <!-- ==================== BREAKER STATE STRIP ==================== -->')
    parts.append('  <g id="breaker-strip">')
    parts.append('    <rect x="40" y="725" width="1520" height="360" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    
    # State 1: CLOSED (x=65, y=745, w=440, h=195)
    # 'closed: calls pass; counts consecutive failures'
    parts.append('    <!-- State 1: CLOSED -->')
    parts.append('    <rect x="65" y="745" width="440" height="195" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    parts.append('    <g transform="translate(85, 755)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <circle cx="20" cy="20" r="18" />')
    parts.append('      <polyline points="12,20 18,26 28,14" />')
    parts.append('    </g>')
    parts.append('    <text x="85" y="825" font-family="sans-serif" font-size="24" fill="#303a36">')
    parts.append('      <tspan x="85" dy="0" font-size="28" font-weight="bold" fill="#207448">closed:</tspan>')
    parts.append('      <tspan x="85" dy="38">calls pass; counts</tspan>')
    parts.append('      <tspan x="85" dy="32">consecutive failures</tspan>')
    parts.append('    </text>')
    
    # Arrow 1: Closed -> Open (threshold exceeded)
    parts.append('    <!-- Arrow 1: Closed -> Open -->')
    parts.append('    <line x1="505" y1="842" x2="575" y2="842" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    
    # State 2: OPEN (Orange highlight) (x=575, y=745, w=450, h=195)
    # 'open after a threshold: calls fail fast without reaching the dependency'
    parts.append('    <!-- State 2: OPEN (Orange Highlight) -->')
    parts.append('    <rect x="575" y="745" width="450" height="195" rx="12" fill="#fff9f2" stroke="#db8129" stroke-width="3" />')
    parts.append('    <g transform="translate(595, 755)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <circle cx="20" cy="20" r="18" />')
    parts.append('      <line x1="12" y1="12" x2="28" y2="28" />')
    parts.append('      <line x1="28" y1="12" x2="12" y2="28" />')
    parts.append('    </g>')
    parts.append('    <text x="595" y="825" font-family="sans-serif" font-size="24" fill="#303a36">')
    parts.append('      <tspan x="595" dy="0" font-size="26" font-weight="bold" fill="#db8129">open after a threshold:</tspan>')
    parts.append('      <tspan x="595" dy="38">calls fail fast without</tspan>')
    parts.append('      <tspan x="595" dy="32">reaching the dependency</tspan>')
    parts.append('    </text>')
    
    # Arrow 2: Open -> Half-Open (cool-down)
    parts.append('    <!-- Arrow 2: Open -> Half-open -->')
    parts.append('    <line x1="1025" y1="842" x2="1095" y2="842" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    
    # State 3: HALF-OPEN (x=1095, y=745, w=440, h=195)
    # 'after a cool-down, half-open: one probe call passes'
    parts.append('    <!-- State 3: HALF-OPEN -->')
    parts.append('    <rect x="1095" y="745" width="440" height="195" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    parts.append('    <g transform="translate(1115, 755)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    parts.append('      <circle cx="20" cy="20" r="18" />')
    parts.append('      <path d="M 20 2 A 18 18 0 0 1 20 38 Z" fill="#207448" />')
    parts.append('    </g>')
    parts.append('    <text x="1115" y="825" font-family="sans-serif" font-size="24" fill="#303a36">')
    parts.append('      <tspan x="1115" dy="0" font-size="26" font-weight="bold" fill="#207448">after a cool-down,</tspan>')
    parts.append('      <tspan x="1115" dy="34" font-size="26" font-weight="bold" fill="#207448">half-open:</tspan>')
    parts.append('      <tspan x="1115" dy="36">one probe call passes</tspan>')
    parts.append('    </text>')
    
    # Outcome 1: probe succeeds: closed again (x=80, y=980, w=460, h=65)
    parts.append('    <!-- Probe Succeeds Box -->')
    parts.append('    <rect x="80" y="980" width="460" height="65" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    parts.append('    <text x="310" y="1021" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">probe succeeds: closed again</text>')
    
    # Outcome 2: probe fails: open again (x=600, y=980, w=400, h=65)
    parts.append('    <!-- Probe Fails Box -->')
    parts.append('    <rect x="600" y="980" width="400" height="65" rx="8" fill="#fff9f2" stroke="#db8129" stroke-width="2" />')
    parts.append('    <text x="800" y="1021" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">probe fails: open again</text>')
    
    # Return Arrows (non-overlapping, perfectly orthogonal)
    # Path for probe fails:
    # Leaves bottom of Half-open (x=1220, y=940), down to y=1012, left to right edge of probe fails box (x=1000, y=1012)
    # Then from left edge of probe fails box (x=600, y=1012), left to x=565, up to bottom of Open box (x=565, y=940)
    parts.append('    <!-- Return Path: probe fails -> Open -->')
    parts.append('    <path d="M 1220 940 L 1220 1012 L 1000 1012" fill="none" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />')
    parts.append('    <path d="M 600 1012 L 565 1012 L 565 948" fill="none" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />')
    
    # Path for probe succeeds:
    # Leaves bottom of Half-open (x=1400, y=940), down to y=1058 (below probe fails path!), left to x=310, then up to bottom of probe succeeds box (x=310, y=1045)
    # Then from left edge of probe succeeds box (x=80, y=1012), left to x=60, up to bottom of Closed box (x=60, y=940)
    parts.append('    <!-- Return Path: probe succeeds -> Closed -->')
    parts.append('    <path d="M 1400 940 L 1400 1058 L 310 1058 L 310 1045" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    parts.append('    <path d="M 80 1012 L 60 1012 L 60 948" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    
    parts.append('  </g>')
    
    # ========================================================
    # BOTTOM BAR (x=40, y=1115, w=1520, h=60)
    # ========================================================
    parts.append('  <!-- Bottom Takeaway Bar -->')
    parts.append('  <rect x="40" y="1115" width="1520" height="60" rx="10" fill="#207448" />')
    parts.append('  <text x="800" y="1153" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Fail fast with a clear message while the dependency recovers</text>')
    
    parts.append('</svg>')
    return '\n'.join(parts)

svg_code = create_svg()
with open("test_candidate_refined.svg", "w") as f:
    f.write(svg_code)

print("Saved test_candidate_refined.svg")
