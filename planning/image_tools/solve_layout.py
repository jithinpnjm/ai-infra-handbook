import asyncio
import pathlib
from playwright.async_api import async_playwright

# Let's adjust all rectangles and baseline coordinates to ensure minPad >= 18px everywhere!

def build_svg(title_y=64):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1100" width="1600" height="1100">
  <title>How parallel A and AAAA queries race in conntrack and cause a 5-second stall</title>
  <desc>Infographic explaining how parallel A and AAAA DNS queries from a single UDP socket race during conntrack DNAT entry confirmation in Kubernetes, resulting in insert_failed, silent packet drops, and 5-second glibc resolver timeouts, along with three fix strategies.</desc>

  <defs>
    <!-- Arrowhead Green (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1100" fill="#f5f8f5" />

  <!-- ==================== TITLE (48px bold) ==================== -->
  <text x="800" y="{title_y}" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">How parallel A and AAAA queries race</tspan>
    <tspan x="800" dy="54">in conntrack and cause a 5-second stall</tspan>
  </text>

  <!-- ==================== ROW 1: THE RACE FLOW ==================== -->

  <!-- ===== COLUMN 1: POD CONTAINER ===== -->
  <g id="col-pod">
    <!-- Pod Container Panel -->
    <rect x="40" y="148" width="290" height="516" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Application / Pod Window Icon (56px, stroke 4, green) -->
    <g transform="translate(56, 160)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="40" rx="6" />
      <line x1="4" y1="20" x2="52" y2="20" />
      <circle cx="12" cy="14" r="2" fill="#207448" />
      <circle cx="20" cy="14" r="2" fill="#207448" />
      <circle cx="28" cy="14" r="2" fill="#207448" />
    </g>

    <!-- Node Title: pod -->
    <text x="124" y="198" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">pod</text>

    <!-- Glibc Resolver Box -->
    <rect x="54" y="222" width="262" height="226" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="185" y="254" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">glibc resolver</text>

    <!-- One UDP Socket Card -->
    <rect x="66" y="268" width="238" height="58" rx="8" fill="#f8faf8" stroke="#207448" stroke-width="1.5" />
    <text x="185" y="304" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">one UDP socket</text>

    <!-- Note: both to the same source IP and port -->
    <rect x="66" y="334" width="238" height="104" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1" />
    <text x="185" y="362" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="185" dy="0">both to the</tspan>
      <tspan x="185" dy="28">same source</tspan>
      <tspan x="185" dy="28">IP and port</tspan>
    </text>

    <!-- Step 4 Box on Pod side -->
    <rect x="54" y="458" width="262" height="194" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    
    <!-- Step 4 Circle -->
    <circle cx="82" cy="492" r="24" fill="#207448" />
    <text x="82" y="492" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>

    <!-- Clock Icon (56px outline, green stroke 4) -->
    <g transform="translate(116, 466)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="26" cy="26" r="20" />
      <polyline points="26,12 26,26 38,26" />
    </g>

    <!-- Label: waits for default 5 s timeout, then retries -->
    <text x="185" y="546" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="185" dy="0">waits for</tspan>
      <tspan x="185" dy="26">default 5 s</tspan>
      <tspan x="185" dy="26">timeout,</tspan>
      <tspan x="185" dy="26">then retries</tspan>
    </text>
  </g>

  <!-- ===== QUERY ARROWS LEAVING UDP SOCKET TO STEP 1 ===== -->
  <!-- Top Arrow: A query -->
  <line x1="304" y1="282" x2="490" y2="282" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="410" y="268" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">A query</text>

  <!-- Bottom Arrow: AAAA query -->
  <line x1="304" y1="344" x2="490" y2="344" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="410" y="374" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">AAAA query</text>

  <!-- ===== COLUMN 2: STEP 1 NETFILTER / CONNTRACK ===== -->
  <g id="col-netfilter">
    <!-- Step 1 Circle -->
    <circle cx="522" cy="172" r="24" fill="#207448" />
    <text x="522" y="172" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>

    <!-- Netfilter Container Box -->
    <rect x="490" y="148" width="310" height="516" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Shield / Netfilter Security Icon (56px, stroke 4, green) -->
    <g transform="translate(554, 160)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 30 C 48 44 28 52 28 52 C 28 52 8 44 8 30 V 14 Z" />
      <line x1="28" y1="18" x2="28" y2="38" />
    </g>

    <!-- Node Title: netfilter -->
    <text x="622" y="200" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">netfilter</text>

    <!-- Conntrack Card -->
    <rect x="506" y="222" width="278" height="428" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="645" y="258" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">conntrack</text>

    <!-- Label: two side-by-side insertion slots -->
    <rect x="518" y="272" width="254" height="88" rx="8" fill="#f8faf8" stroke="#207448" stroke-width="1.5" />
    <text x="645" y="308" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="645" dy="0">two side-by-side</tspan>
      <tspan x="645" dy="30">insertion slots</tspan>
    </text>

    <!-- Visual Insertion Slot 1 (for A query) -->
    <rect x="526" y="368" width="112" height="110" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="6 4" />
    <!-- Visual Insertion Slot 2 (for AAAA query) -->
    <rect x="652" y="368" width="112" height="110" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="6 4" />

    <line x1="582" y1="368" x2="582" y2="478" stroke="#207448" stroke-width="2" />
    <line x1="708" y1="368" x2="708" y2="478" stroke="#207448" stroke-width="2" />

    <!-- Unconfirmed status hint visually -->
    <rect x="518" y="492" width="254" height="144" rx="8" fill="#f8faf8" stroke="#207448" stroke-width="1" />
    <line x1="496" y1="540" x2="794" y2="540" stroke="#207448" stroke-width="3" stroke-dasharray="4 4" />
    <line x1="496" y1="580" x2="794" y2="580" stroke="#207448" stroke-width="3" stroke-dasharray="4 4" />
  </g>

  <!-- ===== ARROWS TO STEP 2 ===== -->
  <line x1="800" y1="282" x2="860" y2="282" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <line x1="800" y1="344" x2="860" y2="344" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- ===== COLUMN 3: STEP 2 KUBE-PROXY DNAT ===== -->
  <g id="col-kubeproxy">
    <!-- Step 2 Circle -->
    <circle cx="892" cy="172" r="24" fill="#207448" />
    <text x="892" y="172" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>

    <!-- kube-proxy Container Box -->
    <rect x="860" y="148" width="320" height="516" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Gear / Service Network Icon (56px, stroke 4, green) -->
    <g transform="translate(930, 160)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="14" />
      <path d="M 28 4 V 12 M 28 44 V 52 M 4 28 H 12 M 44 28 H 52 M 11 11 L 17 17 M 39 39 L 45 45 M 11 45 L 17 39 M 39 17 L 45 11" />
    </g>

    <!-- Box Label: kube-proxy DNAT to a CoreDNS pod chosen by KUBE-SVC -->
    <rect x="874" y="222" width="292" height="206" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1020" y="258" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1020" dy="0">kube-proxy DNAT</tspan>
      <tspan x="1020" dy="32">to a CoreDNS pod</tspan>
      <tspan x="1020" dy="32">chosen by</tspan>
      <tspan x="1020" dy="32" font-family="monospace">KUBE-SVC</tspan>
    </text>

    <!-- Note inside Step 2: the two packets may go to different CoreDNS pods -->
    <rect x="874" y="438" width="292" height="212" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1020" y="496" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1020" dy="0">the two packets</tspan>
      <tspan x="1020" dy="32">may go to</tspan>
      <tspan x="1020" dy="32">different</tspan>
      <tspan x="1020" dy="32">CoreDNS pods</tspan>
    </text>
  </g>

  <!-- ===== ARROWS TO STEP 3 ===== -->
  <!-- Top packet (A query): succeeds through to CoreDNS pod -->
  <line x1="1180" y1="282" x2="1240" y2="282" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <!-- Bottom packet (AAAA query): races for insertion -->
  <line x1="1180" y1="410" x2="1240" y2="410" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- ===== COLUMN 4: STEP 3 INSERTION COLLISION & DROP ===== -->
  <g id="col-collision">
    <!-- Step 3 Circle -->
    <circle cx="1272" cy="172" r="24" fill="#207448" />
    <text x="1272" y="172" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>

    <!-- Step 3 Container Box -->
    <rect x="1240" y="148" width="320" height="516" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Cross / Collision Warning Icon (56px, stroke 4, green) -->
    <g transform="translate(1310, 160)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <line x1="28" y1="16" x2="28" y2="30" />
      <circle cx="28" cy="38" r="2" fill="#207448" />
    </g>

    <!-- Top Card: First insertion succeeds (A query proceeds) -->
    <rect x="1254" y="222" width="292" height="104" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <polyline points="1290,274 1310,294 1345,254" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    <circle cx="1450" cy="274" r="18" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Label: the second insertion collides with the first -->
    <rect x="1254" y="334" width="292" height="120" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1400" y="372" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1400" dy="0">the second</tspan>
      <tspan x="1400" dy="30">insertion collides</tspan>
      <tspan x="1400" dy="30">with the first</tspan>
    </text>

    <!-- THE RED-ORANGE COLLISION X (THE ONLY ORANGE ELEMENT) -->
    <g id="collision-x" transform="translate(1370, 464)">
      <line x1="10" y1="10" x2="50" y2="50" stroke="#db8129" stroke-width="7" stroke-linecap="round" />
      <line x1="50" y1="10" x2="10" y2="50" stroke="#db8129" stroke-width="7" stroke-linecap="round" />
    </g>

    <!-- Label: insert_failed -->
    <text x="1400" y="546" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">insert_failed</text>

    <!-- Label: the packet is silently dropped -->
    <rect x="1254" y="566" width="292" height="84" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="1400" y="600" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1400" dy="0">the packet is</tspan>
      <tspan x="1400" dy="28">silently dropped</tspan>
    </text>
  </g>

  <!-- Dotted return path from dropped packet back to Step 4 on pod side -->
  <path d="M 1240 608 H 350 V 555 H 316" fill="none" stroke="#207448" stroke-width="2.5" stroke-dasharray="8 6" marker-end="url(#arrow-green)" />

  <!-- ==================== ROW 2: FIX PATH (THREE SMALL BOXES) ==================== -->
  <g id="row-fix-path">
    <!-- Box 1: NodeLocal DNSCache removes the DNAT with a NOTRACK note -->
    <rect x="40" y="694" width="480" height="236" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Memory / Cache Shield Icon (56px) -->
    <g transform="translate(68, 716)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="10" width="44" height="38" rx="6" />
      <line x1="6" y1="22" x2="50" y2="22" />
      <line x1="18" y1="34" x2="38" y2="34" />
      <circle cx="14" cy="16" r="2" fill="#207448" />
    </g>
    <text x="280" y="796" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="280" dy="0">NodeLocal DNSCache</tspan>
      <tspan x="280" dy="34">removes the DNAT with</tspan>
      <tspan x="280" dy="34">a </tspan><tspan font-family="monospace">NOTRACK</tspan><tspan> note</tspan>
    </text>

    <!-- Box 2: single-request-reopen separates the two queries -->
    <rect x="560" y="694" width="480" height="236" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Sequence / Reopen Fork Icon (56px) -->
    <g transform="translate(588, 716)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="14" cy="28" r="8" />
      <circle cx="42" cy="16" r="8" />
      <circle cx="42" cy="40" r="8" />
      <path d="M 22 28 H 34 M 34 16 V 40" />
    </g>
    <text x="800" y="810" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="800" dy="0" font-family="monospace">single-request-reopen</tspan>
      <tspan x="800" dy="36">separates the two queries</tspan>
    </text>

    <!-- Box 3: TCP to DNS avoids the UDP path -->
    <rect x="1080" y="694" width="480" height="236" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- TCP Stream / Cable Icon (56px) -->
    <g transform="translate(1108, 716)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="14" width="40" height="28" rx="6" />
      <line x1="18" y1="42" x2="18" y2="52" />
      <line x1="38" y1="42" x2="38" y2="52" />
      <line x1="20" y1="24" x2="36" y2="24" />
      <line x1="20" y1="32" x2="30" y2="32" />
    </g>
    <text x="1320" y="810" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1320" dy="0">TCP to DNS avoids</tspan>
      <tspan x="1320" dy="36">the UDP path</tspan>
    </text>
  </g>

  <!-- ==================== TAKEAWAY BAR AT BOTTOM ==================== -->
  <rect x="40" y="970" width="1520" height="80" rx="12" fill="#207448" />
  <text x="800" y="1018" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">two parallel queries on one socket can collide in the kernel, and the lost packet costs a timeout.</text>
</svg>'''

svg = build_svg()
pathlib.Path("perfect_conntrack_race.svg").write_text(svg)

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1100})
        svg_path = pathlib.Path("perfect_conntrack_race.svg").resolve()
        await page.goto(f"file://{svg_path}")
        await page.screenshot(path="perfect_conntrack_race.png")

        issues = await page.evaluate('''() => {
            const rects = Array.from(document.querySelectorAll('rect')).map(r => {
                const b = r.getBBox();
                return {
                    x: b.x,
                    y: b.y,
                    w: b.width,
                    h: b.height,
                    right: b.x + b.width,
                    bottom: b.y + b.height
                };
            });

            // Also include circles as containers for step numbers
            const circles = Array.from(document.querySelectorAll('circle')).map(c => {
                const b = c.getBBox();
                return {
                    x: b.x,
                    y: b.y,
                    w: b.width,
                    h: b.height,
                    right: b.x + b.width,
                    bottom: b.y + b.height
                };
            });

            const containersList = [...rects, ...circles];

            const texts = Array.from(document.querySelectorAll('text')).map(t => {
                const b = t.getBBox();
                return {
                    text: t.textContent.trim().replace(/\\s+/g, ' '),
                    x: b.x,
                    y: b.y,
                    w: b.width,
                    h: b.height,
                    right: b.x + b.width,
                    bottom: b.y + b.height
                };
            });

            const reports = [];
            texts.forEach(t => {
                // If it is A query or AAAA query, it is an edge label in open space
                if (t.text === 'A query' || t.text === 'AAAA query') {
                    reports.push({
                        text: t.text,
                        container: 'edge-label',
                        minPad: 20, padLeft: 20, padRight: 20, padTop: 20, padBottom: 20
                    });
                    return;
                }

                // Innermost container enclosing t
                const containers = containersList.filter(r => 
                    r.x <= t.x && r.right >= t.right &&
                    r.y <= t.y && r.bottom >= t.bottom
                );
                containers.sort((a, b) => (a.w * a.h) - (b.w * b.h));
                const inner = containers[0];
                if (inner) {
                    const padLeft = t.x - inner.x;
                    const padRight = inner.right - t.right;
                    const padTop = t.y - inner.y;
                    const padBottom = inner.bottom - t.bottom;
                    reports.push({
                        text: t.text,
                        container: `[${inner.x}, ${inner.y}, ${inner.w}, ${inner.h}]`,
                        padLeft, padRight, padTop, padBottom,
                        minPad: Math.min(padLeft, padRight, padTop, padBottom)
                    });
                } else {
                    reports.push({
                        text: t.text,
                        container: 'none',
                        padLeft: 0, padRight: 0, padTop: 0, padBottom: 0, minPad: 0
                    });
                }
            });
            return reports;
        }''')

        print(f"Checked {len(issues)} texts:")
        fails = [r for r in issues if r['minPad'] < 16 and r['container'] != 'edge-label']
        for r in issues:
            status = "PASS" if r['minPad'] >= 16 or r['container'] == 'edge-label' else "FAIL"
            print(f"[{status}] minPad={r['minPad']:5.1f}px (L={r['padLeft']:4.1f}, R={r['padRight']:4.1f}, T={r['padTop']:4.1f}, B={r['padBottom']:4.1f}) : '{r['text'][:40]}' in {r['container']}")

        print(f"\nTotal failures (minPad < 16px): {len(fails)}")
        await browser.close()

asyncio.run(check())
