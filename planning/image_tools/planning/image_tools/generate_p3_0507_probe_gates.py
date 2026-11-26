#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, subprocess, pathlib

def build_svg():
    W = 1600
    H = 1060
    
    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    lines.append('  <title>Three probes for a slow model server</title>')
    lines.append('  <desc>A timeline for vllm-llama showing the startup probe protecting model weights download and CUDA graph capture before readiness gates traffic and liveness handles deadlocks.</desc>')
    lines.append('')
    lines.append('  <defs>')
    lines.append('    <!-- Orange arrowhead (18px) for the single transition arrow -->')
    lines.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    lines.append('    </marker>')
    lines.append('  </defs>')
    lines.append('')
    lines.append(f'  <!-- Background -->')
    lines.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')
    lines.append('')
    lines.append('  <!-- Title: 48px bold -->')
    lines.append('  <text x="800" y="56" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Three probes for a slow model server</text>')
    lines.append('')
    lines.append('  <!-- Context Header Card: Timeline for vllm-llama -->')
    lines.append('  <rect x="50" y="85" width="1500" height="70" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('  <g transform="translate(75, 92)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <!-- Window / container application icon (56x56) -->')
    lines.append('    <rect x="4" y="8" width="48" height="40" rx="6" />')
    lines.append('    <line x1="4" y1="20" x2="52" y2="20" />')
    lines.append('    <circle cx="12" cy="14" r="2" fill="#207448" />')
    lines.append('    <circle cx="20" cy="14" r="2" fill="#207448" />')
    lines.append('    <line x1="14" y1="32" x2="26" y2="32" />')
    lines.append('    <line x1="14" y1="40" x2="38" y2="40" />')
    lines.append('  </g>')
    lines.append('  <text x="160" y="130" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Timeline for vllm-llama</text>')
    lines.append('')
    
    # Left Panel: Segment 1 (Startup Phase)
    # x = 50, y = 175, width = 710, height = 760
    lines.append('  <!-- ==================== LEFT PANEL: SEGMENT 1 (STARTUP PHASE) ==================== -->')
    lines.append('  <rect x="50" y="175" width="710" height="760" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('')
    
    # Card 1: Left note (during loading the server downloads or maps weights and captures CUDA graphs)
    # x = 75, y = 195, width = 660, height = 150
    lines.append('  <!-- Left Note Card: Model loading mechanics -->')
    lines.append('  <rect x="75" y="195" width="660" height="150" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('  <g transform="translate(95, 242)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <!-- Chip / hardware GPU memory icon (56x56) -->')
    lines.append('    <rect x="10" y="10" width="36" height="36" rx="6" />')
    lines.append('    <circle cx="28" cy="28" r="7" />')
    lines.append('    <line x1="18" y1="2" x2="18" y2="10" />')
    lines.append('    <line x1="28" y1="2" x2="28" y2="10" />')
    lines.append('    <line x1="38" y1="2" x2="38" y2="10" />')
    lines.append('    <line x1="18" y1="46" x2="18" y2="54" />')
    lines.append('    <line x1="28" y1="46" x2="28" y2="54" />')
    lines.append('    <line x1="38" y1="46" x2="38" y2="54" />')
    lines.append('    <line x1="2" y1="18" x2="10" y2="18" />')
    lines.append('    <line x1="2" y1="28" x2="10" y2="28" />')
    lines.append('    <line x1="2" y1="38" x2="10" y2="38" />')
    lines.append('    <line x1="46" y1="18" x2="54" y2="18" />')
    lines.append('    <line x1="46" y1="28" x2="54" y2="28" />')
    lines.append('    <line x1="46" y1="38" x2="54" y2="38" />')
    lines.append('  </g>')
    lines.append('  <text x="175" y="244" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">')
    lines.append('    <tspan x="175" dy="0">during loading the server </tspan>')
    lines.append('    <tspan x="175" dy="36">downloads or maps weights and </tspan>')
    lines.append('    <tspan x="175" dy="36">captures CUDA graphs</tspan>')
    lines.append('  </text>')
    lines.append('')
    
    # Card 2: Segment 1 (startupProbe)
    # x = 75, y = 365, width = 660, height = 295
    lines.append('  <!-- Segment 1 Prober Card: startupProbe configuration -->')
    lines.append('  <rect x="75" y="365" width="660" height="295" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    lines.append('  <g transform="translate(95, 485)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <!-- Clock / timer prober icon (56x56) -->')
    lines.append('    <circle cx="28" cy="28" r="22" />')
    lines.append('    <polyline points="28,14 28,28 38,28" />')
    lines.append('    <path d="M 22 2 L 34 2" />')
    lines.append('  </g>')
    lines.append('  <text x="175" y="425" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">')
    lines.append('    <tspan x="175" dy="0">startupProbe: periodSeconds 10, </tspan>')
    lines.append('    <tspan x="175" dy="38">failureThreshold 180, up to 30 </tspan>')
    lines.append('    <tspan x="175" dy="38">minutes; liveness and readiness </tspan>')
    lines.append('    <tspan x="175" dy="38">are disabled until it succeeds </tspan>')
    lines.append('    <tspan x="175" dy="38">once</tspan>')
    lines.append('  </text>')
    lines.append('')
    
    # Card 3: Red cross failure note
    # x = 75, y = 680, width = 660, height = 230
    lines.append('  <!-- Failure Note: Red cross failure scenario -->')
    lines.append('  <rect x="75" y="680" width="660" height="230" rx="12" fill="#fff5f5" stroke="#c53030" stroke-width="2" />')
    lines.append('  <g transform="translate(95, 767)">')
    lines.append('    <!-- Red cross outline badge (56x56) -->')
    lines.append('    <circle cx="28" cy="28" r="22" fill="#fee2e2" stroke="#c53030" stroke-width="3" />')
    lines.append('    <line x1="18" y1="18" x2="38" y2="38" stroke="#c53030" stroke-width="4" stroke-linecap="round" />')
    lines.append('    <line x1="38" y1="18" x2="18" y2="38" stroke="#c53030" stroke-width="4" stroke-linecap="round" />')
    lines.append('  </g>')
    lines.append('  <text x="175" y="750" font-family="sans-serif" font-size="26" font-weight="bold" fill="#991b1b">')
    lines.append('    <tspan x="175" dy="0">liveness with no startup probe </tspan>')
    lines.append('    <tspan x="175" dy="38">on a slow starter creates a </tspan>')
    lines.append('    <tspan x="175" dy="38">restart loop</tspan>')
    lines.append('  </text>')
    lines.append('')
    
    # Transition Arrow: from Segment 1 card (x=735, y=512) to Segment 2 container (x=840, y=512)
    # The single orange highlight in the infographic!
    lines.append('  <!-- Single Transition Arrow: Segment 1 success unlocks Segment 2 (Orange) -->')
    lines.append('  <line x1="735" y1="512" x2="840" y2="512" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />')
    lines.append('')
    
    # Right Panel: Segment 2 (after success: two stacked lanes)
    # x = 840, y = 175, width = 710, height = 760
    lines.append('  <!-- ==================== RIGHT PANEL: SEGMENT 2 (TWO STACKED LANES) ==================== -->')
    lines.append('  <rect x="840" y="175" width="710" height="760" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('')
    
    # Lane 1 (top): readinessProbe
    # x = 865, y = 210, width = 660, height = 320
    lines.append('  <!-- Stacked Lane 1: readinessProbe configuration -->')
    lines.append('  <rect x="865" y="210" width="660" height="320" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    lines.append('  <g transform="translate(885, 342)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <!-- Gate / network endpoints icon (56x56) -->')
    lines.append('    <rect x="6" y="10" width="44" height="36" rx="6" />')
    lines.append('    <line x1="16" y1="20" x2="40" y2="20" />')
    lines.append('    <line x1="16" y1="28" x2="34" y2="28" />')
    lines.append('    <circle cx="20" cy="38" r="2" fill="#207448" />')
    lines.append('    <circle cx="28" cy="38" r="2" fill="#207448" />')
    lines.append('    <circle cx="36" cy="38" r="2" fill="#207448" />')
    lines.append('  </g>')
    lines.append('  <text x="965" y="280" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">')
    lines.append('    <tspan x="965" dy="0">readinessProbe periodSeconds 5: </tspan>')
    lines.append('    <tspan x="965" dy="38">on failure the pod IP leaves the </tspan>')
    lines.append('    <tspan x="965" dy="38">EndpointSlices, container is NOT </tspan>')
    lines.append('    <tspan x="965" dy="38">restarted</tspan>')
    lines.append('  </text>')
    lines.append('')
    
    # Lane 2 (bottom): livenessProbe
    # x = 865, y = 560, width = 660, height = 320
    lines.append('  <!-- Stacked Lane 2: livenessProbe configuration -->')
    lines.append('  <rect x="865" y="560" width="660" height="320" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    lines.append('  <g transform="translate(885, 692)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <!-- Shield / watchdog health heartbeat icon (56x56) -->')
    lines.append('    <path d="M 28 6 L 46 14 L 46 28 C 46 40 28 50 28 50 C 28 50 10 40 10 28 L 10 14 Z" />')
    lines.append('    <polyline points="20,28 25,33 36,22" />')
    lines.append('  </g>')
    lines.append('  <text x="965" y="630" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">')
    lines.append('    <tspan x="965" dy="0">livenessProbe periodSeconds 20, </tspan>')
    lines.append('    <tspan x="965" dy="38">failureThreshold 6: restarts </tspan>')
    lines.append('    <tspan x="965" dy="38">only after 2 full minutes of no </tspan>')
    lines.append('    <tspan x="965" dy="38">response</tspan>')
    lines.append('  </text>')
    lines.append('')
    
    # Footer Takeaway Bar:
    # x = 50, y = 960, width = 1500, height = 70
    lines.append('  <!-- ==================== FOOTER TAKEAWAY BAR ==================== -->')
    lines.append('  <rect x="50" y="960" width="1500" height="70" rx="14" fill="#207448" />')
    lines.append('  <text x="800" y="1004" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Never tie liveness to dependencies</text>')
    lines.append('</svg>')
    
    return "\n".join(lines)

if __name__ == "__main__":
    svg = build_svg()
    pathlib.Path("probe_gates_candidate.svg").write_text(svg)
    print("SVG generated successfully.")
