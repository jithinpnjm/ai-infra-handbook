#!/usr/bin/env python3
import re
import xml.etree.ElementTree as ET

def generate_svg():
    W = 1600
    H = 1180
    
    # Palette constants
    bg_color = "#f5f8f5"
    text_color = "#303a36"
    main_green = "#207448"
    panel_bg = "#e8f1ea"
    accent_orange = "#db8129"
    card_bg = "#ffffff"
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>Drill 3: a liveness probe kills a slow load</title>')
    svg.append('  <desc>Visual explanation of slow model load killed by premature liveness probe versus protected by a 300-second startup probe window.</desc>')
    
    # Markers
    svg.append('  <defs>')
    svg.append('    <marker id="marker-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Canvas Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="{bg_color}" />')
    
    # Diagram Title (48px bold)
    svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Drill 3: a liveness probe kills a slow load</text>')
    
    # =========================================================================
    # LANE 1: what exists (y = 95 to 225, height 130)
    # =========================================================================
    svg.append('  <!-- Lane 1 Container: what exists -->')
    svg.append('  <rect x="50" y="95" width="1500" height="130" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Lane 1 Header Box (x=70, y=110, w=260, h=100)
    svg.append('  <rect x="70" y="110" width="260" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Storage / Weights Disc Stack Icon (56x56) at x=85, y=132
    svg.append('  <g transform="translate(85, 132)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <ellipse cx="28" cy="12" rx="22" ry="8" />')
    svg.append('    <path d="M 6 12 V 28 C 6 32 16 36 28 36 C 40 36 50 32 50 28 V 12" />')
    svg.append('    <path d="M 6 28 V 44 C 6 48 16 52 28 52 C 40 52 50 48 50 44 V 28" />')
    svg.append('  </g>')
    # Label 1: what exists (30px bold)
    svg.append('  <text x="155" y="168" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">what exists</text>')
    
    # Lane 1 Content Card (x=350, y=110, w=1180, h=100)
    svg.append('  <rect x="350" y="110" width="1180" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Visual timeline progress track (0 to 300s scale: 90s is 30% of 1100px track = 330px)
    svg.append('  <rect x="370" y="123" width="400" height="10" rx="5" fill="#207448" opacity="0.25" />')
    svg.append('  <rect x="370" y="123" width="248" height="10" rx="5" fill="#207448" />')
    # Label 2: weights load for about 90 seconds ('loading weights 62%' then nothing in the previous logs)
    svg.append('  <text x="370" y="156" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="370" dy="0">weights load for about 90 seconds</tspan>')
    svg.append('    <tspan x="370" dy="34">(&apos;loading weights 62%&apos; then nothing in the previous logs)</tspan>')
    svg.append('  </text>')
    
    # =========================================================================
    # LANE 2: broken probes (y = 265 to 535, height 270)
    # Gap from Lane 1: 265 - 225 = 40px
    # =========================================================================
    svg.append('  <!-- Lane 2 Container: broken probes -->')
    svg.append('  <rect x="50" y="265" width="1500" height="270" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Lane 2 Header Box (x=70, y=275, w=260, h=250)
    svg.append('  <rect x="70" y="275" width="260" height="250" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Pulse / Broken Heartbeat Icon (56x56) at x=172, y=300
    svg.append('  <g transform="translate(172, 300)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="28" cy="28" r="24" />')
    svg.append('    <path d="M 12 28 L 20 28 L 25 18 L 31 38 L 36 28 L 44 28" />')
    svg.append('  </g>')
    # Label 3: broken probes (30px bold, wrapped)
    svg.append('  <text x="200" y="395" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    svg.append('    <tspan x="200" dy="0">broken</tspan>')
    svg.append('    <tspan x="200" dy="38">probes</tspan>')
    svg.append('  </text>')
    
    # Lane 2 Top-Left: Config Card (x=350, y=275, w=690, h=125)
    svg.append('  <rect x="350" y="275" width="690" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Label 4: liveness initialDelaySeconds 5, periodSeconds 10, failureThreshold 1, no startup probe
    svg.append('  <text x="370" y="312" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="370" dy="0">liveness initialDelaySeconds 5,</tspan>')
    svg.append('    <tspan x="370" dy="31">periodSeconds 10, failureThreshold 1,</tspan>')
    svg.append('    <tspan x="370" dy="31">no startup probe</tspan>')
    svg.append('  </text>')
    
    # Lane 2 Top-Right: Impact Card (x=1060, y=275, w=470, h=125)
    svg.append('  <rect x="1060" y="275" width="470" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Label 6: restart count 40, one restart every four minutes
    svg.append('  <text x="1080" y="330" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1080" dy="0">restart count 40,</tspan>')
    svg.append('    <tspan x="1080" dy="34">one restart every four minutes</tspan>')
    svg.append('  </text>')
    
    # Lane 2 Bottom: Event Kill Sequence Card (Single orange highlight item!)
    svg.append('  <rect x="350" y="420" width="1180" height="100" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
    # Outline warning glyph inside event card (stroke orange)
    svg.append('  <path d="M 374 472 L 392 440 L 410 472 Z" fill="none" stroke="#db8129" stroke-width="3" stroke-linejoin="round" />')
    svg.append('  <line x1="392" y1="450" x2="392" y2="460" stroke="#db8129" stroke-width="3" stroke-linecap="round" />')
    svg.append('  <circle cx="392" cy="466" r="1.5" fill="#db8129" />')
    # Label 5: first check near 5 s fails, event 'Unhealthy: Liveness probe failed' three times then 'Killing: failed liveness probe, will be restarted'
    svg.append('  <text x="424" y="458" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="424" dy="0">first check near 5 s fails, event &apos;Unhealthy: Liveness probe failed&apos;</tspan>')
    svg.append('    <tspan x="424" dy="34">three times then &apos;Killing: failed liveness probe, will be restarted&apos;</tspan>')
    svg.append('  </text>')
    
    # Arrow inside Lane 2 from Config down to Kill Sequence
    svg.append('  <line x1="695" y1="400" x2="695" y2="418" stroke="#207448" stroke-width="3" marker-end="url(#marker-green)" />')
    
    # =========================================================================
    # LANE 3: fixed (y = 575 to 705, height 130)
    # Gap from Lane 2: 575 - 535 = 40px
    # =========================================================================
    svg.append('  <!-- Lane 3 Container: fixed -->')
    svg.append('  <rect x="50" y="575" width="1500" height="130" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Lane 3 Header Box (x=70, y=585, w=260, h=110)
    svg.append('  <rect x="70" y="585" width="260" height="110" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Shield with checkmark icon (56x56) at x=85, y=612
    svg.append('  <g transform="translate(85, 612)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M 28 6 L 48 14 V 28 C 48 42 28 52 28 52 C 28 52 8 42 8 28 V 14 Z" />')
    svg.append('    <polyline points="18,28 25,35 38,20" />')
    svg.append('  </g>')
    # Label 7: fixed (30px bold)
    svg.append('  <text x="165" y="650" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">fixed</text>')
    
    # Lane 3 Left Card: Startup probe window (x=350, y=585, w=680, h=110)
    svg.append('  <rect x="350" y="585" width="680" height="110" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Label 8: startup probe with failureThreshold 30 and period 10 gives a 300 second window
    svg.append('  <text x="370" y="626" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="370" dy="0">startup probe with failureThreshold 30 and</tspan>')
    svg.append('    <tspan x="370" dy="34">period 10 gives a 300 second window</tspan>')
    svg.append('  </text>')
    
    # Lane 3 Right Card: Liveness transition (x=1070, y=585, w=460, h=110)
    svg.append('  <rect x="1070" y="585" width="460" height="110" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Label 9: liveness only starts after the startup probe passes
    svg.append('  <text x="1090" y="626" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1090" dy="0">liveness only starts after</tspan>')
    svg.append('    <tspan x="1090" dy="34">the startup probe passes</tspan>')
    svg.append('  </text>')
    
    # Arrow in Lane 3 from Startup Probe window to Liveness
    svg.append('  <line x1="1030" y1="640" x2="1068" y2="640" stroke="#207448" stroke-width="3" marker-end="url(#marker-green)" />')
    
    # =========================================================================
    # RESTART DELAY STRIP (y = 745 to 825, height 80)
    # Gap from Lane 3: 745 - 705 = 40px
    # =========================================================================
    svg.append('  <!-- Restart Delay Strip -->')
    svg.append('  <rect x="50" y="745" width="1500" height="80" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Clock / Timer Icon (56x56) at x=75, y=757
    svg.append('  <g transform="translate(75, 757)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="28" cy="28" r="22" />')
    svg.append('    <polyline points="28,14 28,28 38,28" />')
    svg.append('    <path d="M 22 2 L 34 2" />')
    svg.append('  </g>')
    # Label 10: starts at 10 s, doubles, capped at 300 s, resets after ten clean minutes
    svg.append('  <text x="155" y="792" font-family="sans-serif" font-size="24" fill="#303a36">starts at 10 s, doubles, capped at 300 s, resets after ten clean minutes</text>')
    
    # =========================================================================
    # CONTRAST PANEL: OOM vs Probe Kill (y = 865 to 975, height 110)
    # Gap from Restart strip: 865 - 825 = 40px
    # =========================================================================
    svg.append('  <!-- Contrast Panel -->')
    svg.append('  <rect x="50" y="865" width="1500" height="110" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Terminal / Application Status Icon (56x56) at x=75, y=892
    svg.append('  <g transform="translate(75, 892)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="8" width="48" height="40" rx="6" />')
    svg.append('    <line x1="4" y1="20" x2="52" y2="20" />')
    svg.append('    <circle cx="12" cy="14" r="2" fill="#207448" />')
    svg.append('    <circle cx="20" cy="14" r="2" fill="#207448" />')
    svg.append('    <line x1="14" y1="32" x2="26" y2="32" />')
    svg.append('    <line x1="14" y1="40" x2="38" y2="40" />')
    svg.append('  </g>')
    # Label 11: OOM kill shows Last State Terminated, Reason OOMKilled, Exit Code 137; here Reason is Error and no OOMKilled
    svg.append('  <text x="155" y="910" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="155" dy="0">OOM kill shows Last State Terminated, Reason OOMKilled, Exit Code 137;</tspan>')
    svg.append('    <tspan x="155" dy="34">here Reason is Error and no OOMKilled</tspan>')
    svg.append('  </text>')
    
    # =========================================================================
    # PREVENTION TAKEAWAY BAR (y = 1015 to 1115, height 100)
    # Gap from Contrast panel: 1015 - 975 = 40px
    # Bottom margin: 1180 - 1115 = 65px (>= 40px)
    # =========================================================================
    svg.append('  <!-- Prevention Takeaway Bar -->')
    svg.append('  <rect x="50" y="1015" width="1500" height="100" rx="14" fill="#207448" />')
    # Label 12: liveness answers is this process stuck, not is it ready; slow starters get a startup probe sized to a measured load time
    svg.append('  <text x="800" y="1055" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">')
    svg.append('    <tspan x="800" dy="0">liveness answers is this process stuck, not is it ready;</tspan>')
    svg.append('    <tspan x="800" dy="34">slow starters get a startup probe sized to a measured load time</tspan>')
    svg.append('  </text>')
    
    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == "__main__":
    content = generate_svg()
    with open("candidate_drill3.svg", "w") as f:
        f.write(content)
    print("Generated candidate_drill3.svg successfully.")
