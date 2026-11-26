#!/usr/bin/env python3

def generate_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>Start-up phases and the remedy that attacks each one</title>')
    svg.append('  <desc>Visual infographic explaining the six start-up phases of model serving and the remedy attacking each phase.</desc>')
    
    # Canvas Background
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    
    # Title (48px bold)
    svg.append('  <text x="800" y="56" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Start-up phases and the remedy that attacks each one</text>')
    
    # Row 1: y = 90, height = 430
    # Row 2: y = 560, height = 430
    # Footer: y = 1030, height = 125
    # Bottom margin = 1200 - 1155 = 45px >= 40px
    # Col 1: x = 40, width = 480
    # Col 2: x = 560, width = 480
    # Col 3: x = 1080, width = 480
    
    # ==================== BOX 1: Pull image ====================
    svg.append('  <!-- ==================== BOX 1: Pull image ==================== -->')
    svg.append('  <g id="box-1">')
    svg.append('    <rect x="40" y="90" width="480" height="430" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <circle cx="90" cy="138" r="24" fill="#207448" />')
    svg.append('    <text x="90" y="147" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>')
    # Icon 1: Package Download (56x56)
    svg.append('    <g transform="translate(440, 110)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="16" width="48" height="36" rx="4" />')
    svg.append('      <path d="M 28 4 L 28 32 M 18 22 L 28 32 L 38 22" />')
    svg.append('    </g>')
    # Inner remedy panel
    svg.append('    <rect x="56" y="260" width="448" height="245" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    # Text for Box 1
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg.append('      <tspan x="280" y="138" font-size="30" font-weight="bold" fill="#207448">Pull image </tspan>')
    svg.append('      <tspan x="280" y="168">(vLLM v0.32.0 amd64 </tspan>')
    svg.append('      <tspan x="280" y="196">image is about 9.2 GB on </tspan>')
    svg.append('      <tspan x="280" y="224">Docker Hub, not under 5 GB </tspan>')
    svg.append('      <tspan x="280" y="252">as the book says): </tspan>')
    svg.append('      <tspan x="280" y="320">pin the tag or digest and </tspan>')
    svg.append('      <tspan x="280" y="354">use <tspan font-family="monospace">IfNotPresent</tspan> so a node </tspan>')
    svg.append('      <tspan x="280" y="388">that has the image does not </tspan>')
    svg.append('      <tspan x="280" y="422">pull again; pre-pull</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== BOX 2: Fetch and mount model ====================
    svg.append('  <!-- ==================== BOX 2: Fetch and mount model ==================== -->')
    svg.append('  <g id="box-2">')
    svg.append('    <rect x="560" y="90" width="480" height="430" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <circle cx="610" cy="138" r="24" fill="#207448" />')
    svg.append('    <text x="610" y="147" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>')
    # Icon 2: Storage cylinder (56x56)
    svg.append('    <g transform="translate(960, 110)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 8 16 C 8 10 48 10 48 16 C 48 22 8 22 8 16 Z" />')
    svg.append('      <path d="M 8 16 L 8 40 C 8 46 48 46 48 40 L 48 16" />')
    svg.append('      <path d="M 8 28 C 8 34 48 34 48 28" />')
    svg.append('    </g>')
    # Inner remedy panel
    svg.append('    <rect x="576" y="260" width="448" height="245" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    # Text for Box 2
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg.append('      <tspan x="800" y="195" font-size="30" font-weight="bold" fill="#207448">Fetch and mount model: </tspan>')
    svg.append('      <tspan x="800" y="320">weights on a PVC, an OCI </tspan>')
    svg.append('      <tspan x="800" y="354">image or node-local NVMe </tspan>')
    svg.append('      <tspan x="800" y="388">instead of downloading from </tspan>')
    svg.append('      <tspan x="800" y="422">Hugging Face on every start</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== BOX 3: Start runtime ====================
    svg.append('  <!-- ==================== BOX 3: Start runtime ==================== -->')
    svg.append('  <g id="box-3">')
    svg.append('    <rect x="1080" y="90" width="480" height="430" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <circle cx="1130" cy="138" r="24" fill="#207448" />')
    svg.append('    <text x="1130" y="147" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>')
    # Icon 3: Service runtime gear (56x56)
    svg.append('    <g transform="translate(1480, 110)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="11" />')
    svg.append('      <path d="M 28 8 L 28 14 M 28 42 L 28 48 M 8 28 L 14 28 M 42 28 L 48 28 M 14 14 L 18 18 M 38 38 L 42 42 M 14 42 L 18 38 M 38 14 L 42 18" />')
    svg.append('    </g>')
    # Inner remedy panel
    svg.append('    <rect x="1096" y="260" width="448" height="245" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    # Text for Box 3
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg.append('      <tspan x="1320" y="195" font-size="30" font-weight="bold" fill="#207448">Start runtime: </tspan>')
    svg.append('      <tspan x="1320" y="354">a second or less </tspan>')
    svg.append('      <tspan x="1320" y="388">per the book</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== BOX 4: Load weights to GPU (Orange Highlight) ====================
    svg.append('  <!-- ==================== BOX 4: Load weights to GPU (Orange Highlight) ==================== -->')
    svg.append('  <g id="box-4">')
    svg.append('    <rect x="40" y="560" width="480" height="430" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
    svg.append('    <circle cx="90" cy="608" r="24" fill="#db8129" />')
    svg.append('    <text x="90" y="617" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>')
    # Icon 4: Accelerator Chip (56x56) in Orange
    svg.append('    <g transform="translate(440, 580)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="12" y="12" width="32" height="32" rx="4" />')
    svg.append('      <rect x="20" y="20" width="16" height="16" rx="2" fill="#e8f1ea" />')
    svg.append('      <line x1="18" y1="6" x2="18" y2="12" /><line x1="28" y1="6" x2="28" y2="12" /><line x1="38" y1="6" x2="38" y2="12" />')
    svg.append('      <line x1="18" y1="44" x2="18" y2="50" /><line x1="28" y1="44" x2="28" y2="50" /><line x1="38" y1="44" x2="38" y2="50" />')
    svg.append('      <line x1="6" y1="18" x2="12" y2="18" /><line x1="6" y1="28" x2="12" y2="28" /><line x1="6" y1="38" x2="12" y2="38" />')
    svg.append('      <line x1="44" y1="18" x2="50" y2="18" /><line x1="44" y1="28" x2="50" y2="28" /><line x1="44" y1="38" x2="50" y2="38" />')
    svg.append('    </g>')
    # Inner remedy panel with orange border
    svg.append('    <rect x="56" y="730" width="448" height="245" rx="12" fill="#e8f1ea" stroke="#db8129" stroke-width="1.5" />')
    # Text for Box 4
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg.append('      <tspan x="280" y="665" font-size="30" font-weight="bold" fill="#db8129">Load weights to GPU: </tspan>')
    svg.append('      <tspan x="280" y="775">bounded by I/O into GPU </tspan>')
    svg.append('      <tspan x="280" y="808">memory; faster loader such </tspan>')
    svg.append('      <tspan x="280" y="841">as Run:ai Model Streamer </tspan>')
    svg.append('      <tspan x="280" y="874">with <tspan font-family="monospace">--load-format</tspan> </tspan>')
    svg.append('      <tspan x="280" y="907" font-family="monospace">runai_streamer, </tspan>')
    svg.append('      <tspan x="280" y="940">no repackaging</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== BOX 5: Warm-up ====================
    svg.append('  <!-- ==================== BOX 5: Warm-up ==================== -->')
    svg.append('  <g id="box-5">')
    svg.append('    <rect x="560" y="560" width="480" height="430" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <circle cx="610" cy="608" r="24" fill="#207448" />')
    svg.append('    <text x="610" y="617" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>')
    # Icon 5: Timer clock (56x56)
    svg.append('    <g transform="translate(960, 580)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="22" />')
    svg.append('      <polyline points="28,14 28,28 38,28" />')
    svg.append('      <line x1="24" y1="2" x2="32" y2="2" />')
    svg.append('    </g>')
    # Inner remedy panel
    svg.append('    <rect x="576" y="730" width="448" height="245" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    # Text for Box 5
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg.append('      <tspan x="800" y="612" font-size="30" font-weight="bold" fill="#207448">Warm-up: </tspan>')
    svg.append('      <tspan x="800" y="640">allocate KV pool, profile, </tspan>')
    svg.append('      <tspan x="800" y="668">compile and capture </tspan>')
    svg.append('      <tspan x="800" y="696">CUDA graphs: </tspan>')
    svg.append('      <tspan x="800" y="756">reuse the </tspan>')
    svg.append('      <tspan x="800" y="784"><tspan font-family="monospace">torch.compile</tspan> cache </tspan>')
    svg.append('      <tspan x="800" y="812">under <tspan font-family="monospace">VLLM_CACHE_ROOT,</tspan> </tspan>')
    svg.append('      <tspan x="800" y="840">set <tspan font-family="monospace">VLLM_FORCE_AOT_LOAD=1</tspan> </tspan>')
    svg.append('      <tspan x="800" y="868">to fail loudly on a </tspan>')
    svg.append('      <tspan x="800" y="896">cache miss, pass </tspan>')
    svg.append('      <tspan x="800" y="924" font-family="monospace">--kv-cache-memory </tspan>')
    svg.append('      <tspan x="800" y="952">to skip profiling</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== BOX 6: API opens ====================
    svg.append('  <!-- ==================== BOX 6: API opens ==================== -->')
    svg.append('  <g id="box-6">')
    svg.append('    <rect x="1080" y="560" width="480" height="430" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <circle cx="1130" cy="608" r="24" fill="#207448" />')
    svg.append('    <text x="1130" y="617" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">6</text>')
    # Icon 6: Health Pulse (56x56)
    svg.append('    <g transform="translate(1480, 580)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="22" />')
    svg.append('      <polyline points="10,28 18,28 23,16 29,40 34,24 38,28 46,28" />')
    svg.append('    </g>')
    # Inner remedy panel
    svg.append('    <rect x="1096" y="730" width="448" height="245" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    # Text for Box 6
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg.append('      <tspan x="1320" y="665" font-size="30" font-weight="bold" fill="#207448">API opens: </tspan>')
    svg.append('      <tspan x="1320" y="855" font-family="monospace">/health 200</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== FOOTER ====================
    svg.append('  <!-- ==================== FOOTER ==================== -->')
    svg.append('  <g id="footer">')
    svg.append('    <rect x="40" y="1030" width="1520" height="125" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg.append('      <tspan x="800" y="1062">book says these together can cut scale-up from many minutes </tspan>')
    svg.append('      <tspan x="800" y="1090">to tens of seconds depending on model size; <tspan font-family="monospace">--enforce-eager</tspan> and </tspan>')
    svg.append('      <tspan x="800" y="1118"><tspan font-family="monospace">-O0</tspan> make boot fast but decode slower, use them in development only; </tspan>')
    svg.append('      <tspan x="800" y="1146">most time goes to model download and weight load; measure each phase on your own cluster</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return "\n".join(svg)

content = generate_svg()
with open("test_candidate_startup.svg", "w", encoding="utf-8") as f:
    f.write(content)
print("Saved updated test_candidate_startup.svg successfully.")
