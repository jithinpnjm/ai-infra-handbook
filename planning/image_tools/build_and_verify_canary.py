import re
import pathlib
import xml.etree.ElementTree as ET
import subprocess

# Let's write the complete generator for x14-canary-ladder.svg

def build_svg():
    H = 1200
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>The canary ladder moves traffic up in steps, and each step must pass its gates</title>')
    svg.append('  <desc>Visual infographic explaining the canary traffic staircase, latency and quality gates, promote, hold, and rollback decisions.</desc>')
    svg.append('  <defs>')
    # 18px proportional green arrowhead marker
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    # 18px proportional orange arrowhead marker
    svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
    
    # Title: 48px bold (wrapped on 2 lines)
    svg.append('  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">The canary ladder moves traffic up in steps, </tspan>')
    svg.append('    <tspan x="800" dy="56">and each step must pass its gates</tspan>')
    svg.append('  </text>')

    # ==================== GATE GROUPS ROW ====================
    # Latency gates box: x=40..770 (w=730, h=120, y=145..265)
    svg.append('  <g id="latency-gates">')
    svg.append('    <rect x="40" y="145" width="730" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Outline icon: clock / timer (56x56, stroke 4, green)
    svg.append('    <g transform="translate(65, 177)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="24" />')
    svg.append('      <polyline points="28,14 28,28 40,28" />')
    svg.append('    </g>')
    # Title: Latency gates
    svg.append('    <text x="140" y="185" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Latency gates</text>')
    # Description: canary TTFT p99 and ITL p99 against baseline, ratio limit
    svg.append('    <text x="140" y="222" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="140" dy="0">canary TTFT p99 and ITL p99 </tspan>')
    svg.append('      <tspan x="140" dy="30">against baseline, ratio limit</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Quality gates box: x=830..1560 (w=730, h=120, y=145..265)
    svg.append('  <g id="quality-gates">')
    svg.append('    <rect x="830" y="145" width="730" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Outline icon: shield / security (56x56, stroke 4, green)
    svg.append('    <g transform="translate(855, 177)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 48 14 C 48 34 28 48 28 48 C 28 48 8 34 8 14 Z" />')
    svg.append('      <polyline points="20,26 26,32 36,20" />')
    svg.append('    </g>')
    # Title: Quality gates
    svg.append('    <text x="930" y="185" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Quality gates</text>')
    # Description: eval score, finish_reason length share, error rate
    svg.append('    <text x="930" y="222" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="930" dy="0">eval score, finish_reason length share, </tspan>')
    svg.append('      <tspan x="930" dy="30">error rate</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== STAIRCASE (STEPS & GATE DIAMONDS) ====================
    # 6 steps rising from left to right.
    # Dimensions:
    # W_step = 158
    # W_dia = 106
    # G = 8 px
    # Total width = 6 * 158 + 5 * 106 + 10 * 8 = 948 + 530 + 80 = 1558 px!
    # Margin left = 41 px, right = 41 px -> 41 + 1558 = 1599 px (fits inside 1600!).
    # Wait, let's make W_step = 156, W_dia = 104, G = 7 px:
    # Total = 6 * 156 + 5 * 104 + 10 * 7 = 936 + 520 + 70 = 1526 px!
    # Margin left = 37, right = 37.
    # Wait! "Leave at least 40 px outside margin."
    # If Margin left = 40, Margin right = 40: Usable = 1520 px!
    # Let's tune:
    # 6 * 156 = 936
    # 5 * 102 = 510
    # 10 * G = 1520 - 936 - 510 = 74 px -> G = 7.4 px!
    # Wait! Can "gates" fit in 102 px diamond?
    # 5 chars * 24 * 0.6 = 72 px. 72 + 30 = 102 px (15px padding each side).
    # Wait! We need AT LEAST 16 px padding!
    # 72 + 32 = 104 px!
    # Let's check!
    return '\n'.join(svg) + '\n</svg>'

print("Test complete")
