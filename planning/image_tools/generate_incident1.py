#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from test_p3_2026 import audit_svg_string

def build_svg():
    # Dimensions: 1600 x 1200
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>Incident 1: from symptoms to the one lost routing setting</title>')
    svg.append('  <desc>Incident 1: from symptoms to the one lost routing setting</desc>')
    
    # Background
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')

    # Title: 48px bold
    svg.append('  <text x="800" y="68" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Incident 1: from symptoms to the one lost routing setting</text>')

    # =========================================================================
    # LEFT EVIDENCE COLUMN
    # Container: x=40, y=110, width=500, height=890
    # =========================================================================
    svg.append('  <!-- Left Evidence Column -->')
    svg.append('  <g id="left-evidence-column">')
    svg.append('    <rect x="40" y="110" width="500" height="890" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    
    # Evidence Column Header Icon (Clipboard / Checklist outline, 56px, stroke 4)
    # Centered at x=290, y=125
    svg.append('    <g transform="translate(262, 125)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="12" width="40" height="42" rx="4" />')
    svg.append('      <path d="M 20 12 V 8 C 20 6 22 4 24 4 H 32 C 34 4 36 6 36 8 V 12" />')
    svg.append('      <line x1="18" y1="24" x2="38" y2="24" />')
    svg.append('      <line x1="18" y1="34" x2="38" y2="34" />')
    svg.append('      <line x1="18" y1="44" x2="30" y2="44" />')
    svg.append('    </g>')

    # 5 White Cards inside Left Column
    # Width = 460, x = 60
    # Card 1: y = 195, height = 205
    svg.append('    <!-- Card 1: TTFT / Latency -->')
    svg.append('    <rect x="60" y="195" width="460" height="205" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="80" y="230" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="80" dy="0">p99 TTFT 4.1 s against</tspan>')
    svg.append('      <tspan x="80" dy="30">normal 0.6 s; p50 0.9 s</tspan>')
    svg.append('      <tspan x="80" dy="30">against 0.5 s; inter-token</tspan>')
    svg.append('      <tspan x="80" dy="30">latency flat at about 25 ms</tspan>')
    svg.append('      <tspan x="80" dy="30">(decode is fine, so the</tspan>')
    svg.append('      <tspan x="80" dy="30">problem is prefill or queue)</tspan>')
    svg.append('    </text>')

    # Card 2: y = 416, height = 145
    svg.append('    <!-- Card 2: Waiting Queue -->')
    svg.append('    <rect x="60" y="416" width="460" height="145" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="80" y="452" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="80" dy="0">waiting queue per replica</tspan>')
    svg.append('      <tspan x="80" dy="30">about 2 to about 30 at 13:55;</tspan>')
    svg.append('      <tspan x="80" dy="30">running requests at the</tspan>')
    svg.append('      <tspan x="80" dy="30">batch cap</tspan>')
    svg.append('    </text>')

    # Card 3: y = 577, height = 115
    svg.append('    <!-- Card 3: KV Usage -->')
    svg.append('    <rect x="60" y="577" width="460" height="115" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="80" y="612" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="80" dy="0">KV usage about 0.45, no</tspan>')
    svg.append('      <tspan x="80" dy="30">preemption, no OOM</tspan>')
    svg.append('      <tspan x="80" dy="30">(not memory)</tspan>')
    svg.append('    </text>')

    # Card 4: y = 708, height = 135
    svg.append('    <!-- Card 4: Prompts and Replicas -->')
    svg.append('    <rect x="60" y="708" width="460" height="135" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="80" y="742" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="80" dy="0">prompts unchanged, all 12</tspan>')
    svg.append('      <tspan x="80" dy="30">replicas look the same, no</tspan>')
    svg.append('      <tspan x="80" dy="30">errors, no restarts (not</tspan>')
    svg.append('      <tspan x="80" dy="30">traffic, not one bad pod)</tspan>')
    svg.append('    </text>')

    # Card 5: y = 859, height = 130
    svg.append('    <!-- Card 5: Deploy -->')
    svg.append('    <rect x="60" y="859" width="460" height="130" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="80" y="893" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="80" dy="0">deploy finished 13:50 moved</tspan>')
    svg.append('      <tspan x="80" dy="30">router and engine image to</tspan>')
    svg.append('      <tspan x="80" dy="30">all 12 replicas in ten</tspan>')
    svg.append('      <tspan x="80" dy="30">minutes, no canary</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # =========================================================================
    # CENTER KEY SIGNAL
    # Container: x=580, y=110, width=460, height=890
    # Uses orange #db8129 stroke for single most important item!
    # =========================================================================
    svg.append('  <!-- Center Key Signal -->')
    svg.append('  <g id="center-key-signal">')
    svg.append('    <rect x="580" y="110" width="460" height="890" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
    
    # Key Signal Icon: Pulse / Activity / Gauge (56px, stroke 4)
    # Centered at x=810, y=180
    svg.append('    <g transform="translate(782, 170)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="24" />')
    svg.append('      <polyline points="12,30 20,30 25,18 31,38 36,26 40,30 46,30" />')
    svg.append('    </g>')

    # Key Signal Text
    svg.append('    <text x="604" y="320" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="604" dy="0">vllm:prefix_cache_hits /</tspan>')
    svg.append('      <tspan x="604" dy="38">vllm:prefix_cache_queries</tspan>')
    svg.append('      <tspan x="604" dy="38">fell from about 0.55 to</tspan>')
    svg.append('      <tspan x="604" dy="38">about 0.03 at 13:52; the</tspan>')
    svg.append('      <tspan x="604" dy="38">chat product sends the</tspan>')
    svg.append('      <tspan x="604" dy="38">same 3,000-token system</tspan>')
    svg.append('      <tspan x="604" dy="38">prompt on every request;</tspan>')
    svg.append('      <tspan x="604" dy="38">GPU utilisation 70 to 95</tspan>')
    svg.append('      <tspan x="604" dy="38">percent, extra work is</tspan>')
    svg.append('      <tspan x="604" dy="38">prefill</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # =========================================================================
    # RIGHT COLUMN: CONCLUSION & FIX
    # Conclusion: x=1080, y=110, width=480, height=425
    # Fix: x=1080, y=575, width=480, height=425
    # =========================================================================
    svg.append('  <!-- Right Column: Conclusion -->')
    svg.append('  <g id="right-conclusion">')
    svg.append('    <rect x="1080" y="110" width="480" height="425" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    
    # Conclusion Icon: Network Routing Fork (56px, stroke 4)
    # Centered at x=1320, y=145
    svg.append('    <g transform="translate(1292, 140)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="16" cy="28" r="6" />')
    svg.append('      <circle cx="44" cy="14" r="6" />')
    svg.append('      <circle cx="44" cy="42" r="6" />')
    svg.append('      <path d="M 22 28 H 30 C 34 28 36 14 40 14" />')
    svg.append('      <path d="M 22 28 H 30 C 34 28 36 42 40 42" />')
    svg.append('    </g>')

    # Conclusion Text
    svg.append('    <text x="1104" y="250" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1104" dy="0">diff: new router config</tspan>')
    svg.append('      <tspan x="1104" dy="38">lost the prefix-hash</tspan>')
    svg.append('      <tspan x="1104" dy="38">routing setting, requests</tspan>')
    svg.append('      <tspan x="1104" dy="38">with the same prefix are</tspan>')
    svg.append('      <tspan x="1104" dy="38">spread by round robin</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Fix Card
    svg.append('  <!-- Right Column: Fix -->')
    svg.append('  <g id="fix-card">')
    svg.append('    <rect x="1080" y="575" width="480" height="425" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    
    # Fix Icon: Terminal / Undo Wrench (56px, stroke 4)
    # Centered at x=1320, y=615
    svg.append('    <g transform="translate(1292, 605)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="8" width="44" height="40" rx="6" />')
    svg.append('      <path d="M 16 22 L 24 28 L 16 34" />')
    svg.append('      <line x1="28" y1="34" x2="38" y2="34" />')
    svg.append('    </g>')

    # Fix Text
    svg.append('    <text x="1104" y="725" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1104" dy="0">kubectl rollout undo</tspan>')
    svg.append('      <tspan x="1104" dy="38">deployment, watch TTFT and</tspan>')
    svg.append('      <tspan x="1104" dy="38">hit rate recover, then diff</tspan>')
    svg.append('      <tspan x="1104" dy="38">the values file</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # =========================================================================
    # BOTTOM STRIP: STRONG NOTE
    # Container: x=40, y=1040, width=1520, height=120
    # =========================================================================
    svg.append('  <!-- Bottom Strip: Strong Note -->')
    svg.append('  <g id="strong-note">')
    svg.append('    <rect x="40" y="1040" width="1520" height="120" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    
    # Shield / Alert Icon (56px, stroke 4)
    svg.append('    <g transform="translate(68, 1072)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 10 14 L 10 30 C 10 44 28 52 28 52 C 28 52 46 44 46 30 L 46 14 Z" />')
    svg.append('      <line x1="28" y1="20" x2="28" y2="32" />')
    svg.append('      <circle cx="28" cy="40" r="2.5" fill="#207448" />')
    svg.append('    </g>')

    # Strong Note Text
    svg.append('    <text x="145" y="1092" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="145" dy="0">new replicas start with an empty prefix cache, so scaling out is no fix;</tspan>')
    svg.append('      <tspan x="145" dy="34">restarting every replica empties every cache at once</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == "__main__":
    s = build_svg()
    audit_svg_string(s)
    with open("candidate_incident1.svg", "w") as f:
        f.write(s)
    print("candidate_incident1.svg written successfully!")
