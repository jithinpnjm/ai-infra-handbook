import xml.etree.ElementTree as ET
import re

def build_v4_svg():
    W = 1600
    H = 1200
    BG = "#f5f8f5"
    TEXT = "#303a36"
    GREEN = "#207448"
    PANEL_BG = "#e8f1ea"
    ORANGE = "#db8129"
    WHITE = "#ffffff"

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>The GPU diagnostics CLI in four layers, with exit codes</title>')
    svg.append('  <desc>Visual infographic explaining the four layers of the GPU diagnostics CLI: cli.py, collect.py, parsers.py, rules.py, with models.py, exit codes, and test strip.</desc>')
    
    # Defs: Markers and Icons
    svg.append('  <defs>')
    # Proportional arrow marker (about 18px)
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')

    # 56px Outline Icons (stroke="#207448" stroke-width="4" fill="none")
    # 1. CLI Icon
    svg.append('    <g id="icon-cli" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="48" height="44" rx="6" fill="#ffffff" />')
    svg.append('      <line x1="4" y1="18" x2="52" y2="18" />')
    svg.append('      <circle cx="11" cy="12" r="2" fill="#207448" />')
    svg.append('      <circle cx="17" cy="12" r="2" fill="#207448" />')
    svg.append('      <path d="M 14 28 L 22 34 L 14 40" />')
    svg.append('      <line x1="26" y1="40" x2="38" y2="40" />')
    svg.append('    </g>')

    # 2. Collect Icon
    svg.append('    <g id="icon-collect" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="8" width="44" height="18" rx="4" fill="#ffffff" />')
    svg.append('      <rect x="6" y="30" width="44" height="18" rx="4" fill="#ffffff" />')
    svg.append('      <circle cx="14" cy="17" r="2.5" fill="#207448" />')
    svg.append('      <line x1="22" y1="17" x2="42" y2="17" />')
    svg.append('      <circle cx="14" cy="39" r="2.5" fill="#207448" />')
    svg.append('      <line x1="22" y1="39" x2="42" y2="39" />')
    svg.append('    </g>')

    # 3. Parser Icon
    svg.append('    <g id="icon-parser" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="6" width="44" height="44" rx="6" fill="#ffffff" />')
    svg.append('      <path d="M 18 18 L 12 28 L 18 38" />')
    svg.append('      <path d="M 38 18 L 44 28 L 38 38" />')
    svg.append('      <line x1="30" y1="16" x2="26" y2="40" />')
    svg.append('    </g>')

    # 4. Rules Icon
    svg.append('    <g id="icon-rules" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 48 14 L 48 28 C 48 40 28 50 28 50 C 28 50 8 40 8 28 L 8 14 Z" fill="#ffffff" />')
    svg.append('      <path d="M 20 28 L 26 34 L 38 20" />')
    svg.append('    </g>')

    # 5. Models Icon
    svg.append('    <g id="icon-models" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polygon points="28,6 50,18 50,42 28,52 6,42 6,18" fill="#ffffff" />')
    svg.append('      <line x1="28" y1="6" x2="28" y2="52" />')
    svg.append('      <line x1="6" y1="18" x2="28" y2="30" />')
    svg.append('      <line x1="50" y1="18" x2="28" y2="30" />')
    svg.append('    </g>')

    # 6. Exit Codes Icon
    svg.append('    <g id="icon-exit" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="6" width="40" height="44" rx="5" fill="#ffffff" />')
    svg.append('      <line x1="16" y1="18" x2="38" y2="18" />')
    svg.append('      <line x1="16" y1="28" x2="38" y2="28" />')
    svg.append('      <line x1="16" y1="38" x2="32" y2="38" />')
    svg.append('    </g>')

    # 7. Test Strip Icon
    svg.append('    <g id="icon-test" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 22 6 L 34 6" />')
    svg.append('      <line x1="28" y1="6" x2="28" y2="18" />')
    svg.append('      <path d="M 22 18 L 10 44 C 8 48 11 52 16 52 L 40 52 C 45 52 48 48 46 44 L 34 18 Z" fill="#ffffff" />')
    svg.append('      <line x1="16" y1="38" x2="40" y2="38" />')
    svg.append('    </g>')

    # 8. Bottom Bar Icon
    svg.append('    <g id="icon-key" stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="18" cy="28" r="12" fill="#207448" />')
    svg.append('      <circle cx="18" cy="28" r="4" fill="#ffffff" />')
    svg.append('      <line x1="30" y1="28" x2="50" y2="28" />')
    svg.append('      <line x1="42" y1="28" x2="42" y2="36" />')
    svg.append('      <line x1="48" y1="28" x2="48" y2="34" />')
    svg.append('    </g>')

    svg.append('  </defs>')

    # Canvas Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="{BG}" />')

    # Title: 48px bold (centered)
    svg.append('  <text x="800" y="50" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">The GPU diagnostics CLI in four layers, </tspan>')
    svg.append('    <tspan x="800" dy="50">with exit codes</tspan>')
    svg.append('  </text>')

    # ================= LEFT COLUMN: LAYERED PIPELINE =================
    # Layer 1: cli.py
    # Box: x=40, y=132, w=1000, h=72
    svg.append('  <g id="layer-cli">')
    svg.append('    <rect x="40" y="132" width="1000" height="72" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <use href="#icon-cli" x="56" y="140" />')
    svg.append('    <text x="128" y="176" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan font-family="monospace">cli.py: </tspan>')
    svg.append('      <tspan>Click group, output formatting and exit codes</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Arrow 1: cli.py -> collect.py (gap: 204 to 244 = 40px)
    svg.append('  <line x1="540" y1="204" x2="540" y2="244" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')

    # Layer 2: collect.py
    # Box: x=40, y=244, w=1000, h=90
    svg.append('  <g id="layer-collect">')
    svg.append('    <rect x="40" y="244" width="1000" height="90" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <use href="#icon-collect" x="56" y="261" />')
    svg.append('    <text x="128" y="280" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="128" dy="0"><tspan font-family="monospace">collect.py: </tspan>per-host executor over SSH, an agent or Redfish, </tspan>')
    svg.append('      <tspan x="128" dy="30">with timeout and bounded concurrency</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Arrow 2: collect.py -> pure layers (gap: 334 to 374 = 40px)
    svg.append('  <line x1="540" y1="334" x2="540" y2="374" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')

    # Pure Layers Container (orange border #db8129)
    # Box: x=40, y=374, w=1000, h=490
    svg.append('  <g id="pure-layers-container">')
    svg.append('    <rect x="40" y="374" width="1000" height="490" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3" />')

    # Layer 3: parsers.py card
    # Box: x=56, y=390, w=968, h=264
    svg.append('    <rect x="56" y="390" width="968" height="264" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <use href="#icon-parser" x="72" y="406" />')
    # parsers.py text (4 wrapped lines)
    svg.append('    <text x="144" y="426" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="144" dy="0"><tspan font-family="monospace">parsers.py: </tspan>pure functions turning nvidia-smi CSV </tspan>')
    svg.append('      <tspan x="144" dy="26">and dcgmi output into frozen dataclasses </tspan>')
    svg.append('      <tspan x="144" dy="26">(a pure function answers from its inputs alone: </tspan>')
    svg.append('      <tspan x="144" dy="26">no network, no clock, no randomness)</tspan>')
    svg.append('    </text>')
    # Parser detail (5 wrapped monospace lines)
    svg.append('    <text x="144" y="536" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="144" dy="0">Gpu(index, name, temp_c, util_pct, </tspan>')
    svg.append('      <tspan x="144" dy="24">mem_used_mib, mem_total_mib, ecc_uncorrected); </tspan>')
    svg.append('      <tspan x="144" dy="24">_int maps empty, [N/A] and [Not Supported] to None; </tspan>')
    svg.append('      <tspan x="144" dy="24">a line without exactly 7 columns raises </tspan>')
    svg.append('      <tspan x="144" dy="24">ValueError unexpected nvidia-smi columns</tspan>')
    svg.append('    </text>')

    # Arrow 3: parsers.py -> rules.py (gap: 654 to 694 = 40px)
    svg.append('    <line x1="540" y1="654" x2="540" y2="694" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')

    # Layer 4: rules.py card
    # Box: x=56, y=694, w=968, h=154
    svg.append('    <rect x="56" y="694" width="968" height="154" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <use href="#icon-rules" x="72" y="708" />')
    # rules.py text
    svg.append('    <text x="144" y="732" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan font-family="monospace">rules.py: </tspan>')
    svg.append('      <tspan>evaluate(gpus, expected=8, max_temp=85)</tspan>')
    svg.append('    </text>')
    # Rules detail text (3 wrapped lines)
    svg.append('    <text x="144" y="766" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="144" dy="0">problems for: expected 8 GPUs but found a different count; </tspan>')
    svg.append('      <tspan x="144" dy="26">temp above 85; uncorrected ECC non-zero; </tspan>')
    svg.append('      <tspan x="144" dy="26">plus XID in a set of known codes</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ================= RIGHT COLUMN: AT THE SIDE =================
    # Side Node: models.py
    # Box: x=1080, y=132, w=480, h=96
    svg.append('  <g id="side-models">')
    svg.append('    <rect x="1080" y="132" width="480" height="96" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <use href="#icon-models" x="1096" y="152" />')
    svg.append('    <text x="1172" y="172" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="1172" dy="0"><tspan font-family="monospace">models.py: </tspan>dataclasses </tspan>')
    svg.append('      <tspan x="1172" dy="32">or pydantic models</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Exit Code Table Container (gap: 228 to 268 = 40px)
    # Box: x=1080, y=268, w=480, h=596
    svg.append('  <g id="exit-code-table">')
    svg.append('    <rect x="1080" y="268" width="480" height="596" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')

    # Card 0: 0 all GPUs healthy (y=288 to 400, h=112)
    svg.append('    <rect x="1100" y="288" width="440" height="112" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <use href="#icon-exit" x="1116" y="316" />')
    svg.append('    <text x="1188" y="354" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan font-family="monospace">0 </tspan>')
    svg.append('      <tspan>all GPUs healthy</tspan>')
    svg.append('    </text>')

    # Card 1: 1 usage or runtime failure (gap: 400 to 436 = 36px)
    svg.append('    <rect x="1100" y="436" width="440" height="112" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <use href="#icon-exit" x="1116" y="464" />')
    svg.append('    <text x="1188" y="482" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="1188" dy="0"><tspan font-family="monospace">1 </tspan>usage or </tspan>')
    svg.append('      <tspan x="1188" dy="32">runtime failure</tspan>')
    svg.append('    </text>')

    # Card 3: 3 any GPU unhealthy (gap: 548 to 584 = 36px)
    svg.append('    <rect x="1100" y="584" width="440" height="112" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <use href="#icon-exit" x="1116" y="612" />')
    svg.append('    <text x="1188" y="650" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan font-family="monospace">3 </tspan>')
    svg.append('      <tspan>any GPU unhealthy</tspan>')
    svg.append('    </text>')

    # Card 4: 4 partial collection failure (gap: 696 to 732 = 36px)
    svg.append('    <rect x="1100" y="732" width="440" height="112" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <use href="#icon-exit" x="1116" y="760" />')
    svg.append('    <text x="1188" y="778" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="1188" dy="0"><tspan font-family="monospace">4 </tspan>partial </tspan>')
    svg.append('      <tspan x="1188" dy="32">collection failure</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ================= FULL-WIDTH TEST STRIP =================
    # Gap: 864 to 904 = 40px
    # Box: x=40, y=904, w=1520, h=120
    svg.append('  <g id="test-strip">')
    svg.append('    <rect x="40" y="904" width="1520" height="120" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <use href="#icon-test" x="56" y="936" />')
    svg.append('    <text x="136" y="940" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="136" dy="0">canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, </tspan>')
    svg.append('      <tspan x="136" dy="30">empty output, missing GPU; then CliRunner with a stubbed executor </tspan>')
    svg.append('      <tspan x="136" dy="30">asserting exit codes and JSON shape</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ================= FULL-WIDTH BOTTOM BAR =================
    # Gap: 1024 to 1064 = 40px
    # Box: x=40, y=1064, w=1520, h=80
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1064" width="1520" height="80" rx="12" fill="#207448" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <use href="#icon-key" x="56" y="1076" />')
    svg.append('    <text x="800" y="1114" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">')
    svg.append('      Parser, rules, executor and CLI stay separate')
    svg.append('    </text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return "\n".join(svg)

if __name__ == "__main__":
    content = build_v4_svg()
    with open("planning/image_tools/candidate_gpu_cli_v4.svg", "w", encoding="utf-8") as f:
        f.write(content)
    print("Generated candidate_gpu_cli_v4.svg")
