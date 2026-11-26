import asyncio, pathlib, math
from playwright.async_api import async_playwright
import xml.etree.ElementTree as ET

def dist_to_diamond(px, py, cx, cy, rx, ry):
    dx = abs(px - cx)
    dy = abs(py - cy)
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    val = dx/rx + dy/ry
    return (1.0 - val) / scale

def generate_svg():
    W = 1600
    H = 1200
    
    # Layout geometry
    # Top title: y=74
    # Panels: y = 110 to 725 (h=615)
    # Left panel: x = 40 to 770 (w=730)
    # Right panel: x = 810 to 1560 (w=750)
    # Center of left panel = 405
    # Center trunk of right panel = 1035
    # Box c on right = 1265 to 1535 (w=270, h=180, y=365..545)
    
    # Guards container: y = 765 to 1045 (h=280)
    # x = 40 to 1560 (w=1520)
    
    # Takeaway bar: y = 1085 to 1155 (h=70)
    # x = 40 to 1560 (w=1520)
    
    parts = []
    parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <title>a &amp;&amp; b || c is not an if/else</title>
  <desc>Two side-by-side flow diagrams comparing if-then-else with the and-or construct, showing that c runs even though a succeeded when b fails.</desc>

  <defs>
    <!-- Green marker (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="{W}" height="{H}" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="74" text-anchor="middle" font-size="48" font-weight="bold" fill="#303a36"><tspan font-family="ui-monospace, monospace">a &amp;&amp; b || c</tspan><tspan font-family="system-ui, -apple-system, sans-serif"> is not an if/else</tspan></text>

  <!-- ========================================== -->
  <!-- LEFT PANEL: if a; then b; else c; fi       -->
  <!-- ========================================== -->
  <rect x="40" y="110" width="730" height="615" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  
  <!-- Left Header -->
  <text x="405" y="152" text-anchor="middle" font-family="ui-monospace, monospace" font-size="30" font-weight="bold" fill="#207448">if a; then b; else c; fi</text>

  <!-- Left Arrows (drawn behind nodes) -->
  <!-- 1. start -> diamond 'a succeeds?' -->
  <line x1="405" y1="210" x2="405" y2="238" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 2. diamond -> box 'b' (yes) -->
  <path d="M 155 310 L 155 365 L 220 365 L 220 408" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="145" y="348" text-anchor="end" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">yes</text>

  <!-- 3. diamond -> box 'c' (no) -->
  <path d="M 655 310 L 655 365 L 590 365 L 590 408" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="665" y="348" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">no</text>

  <!-- 4. box 'b' -> end -->
  <path d="M 220 520 L 220 670 L 313 670" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 5. box 'c' -> end -->
  <path d="M 590 520 L 590 670 L 497 670" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Left Nodes -->
  <!-- Node: start (center 405, 178, w=180, h=64) -->
  <g id="left-start">
    <rect x="315" y="146" width="180" height="64" rx="32" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <polygon points="338,168 338,188 354,178" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round" />
    <text x="418" y="187" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">start</text>
  </g>

  <!-- Node: diamond 'a succeeds?' (center 405, 310, rx=250, ry=72 -> w=500, h=144) -->
  <g id="left-diamond-a">
    <polygon points="405,238 655,310 405,382 155,310" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(295, 292)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="18" cy="18" r="15" />
      <path d="M 14 12 C 14 7, 22 7, 22 13 C 22 17, 18 17, 18 22" />
      <circle cx="18" cy="27" r="1.5" fill="#207448" />
    </g>
    <text x="438" y="320" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">a succeeds?</text>
  </g>

  <!-- Node: box 'b' (x=115, y=410, w=210, h=110) -->
  <g id="left-box-b">
    <rect x="115" y="410" width="210" height="110" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(135, 441)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="48" height="42" rx="6" />
      <line x1="2" y1="16" x2="50" y2="16" stroke-width="2.5" />
      <polyline points="12,26 20,33 12,40" stroke-width="3" />
      <line x1="24" y1="40" x2="38" y2="40" stroke-width="3" />
    </g>
    <text x="245" y="477" text-anchor="middle" font-family="ui-monospace, monospace" font-size="34" font-weight="bold" fill="#303a36">b</text>
  </g>

  <!-- Node: box 'c' (x=485, y=410, w=210, h=110) -->
  <g id="left-box-c">
    <rect x="485" y="410" width="210" height="110" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(505, 441)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="48" height="42" rx="6" />
      <line x1="2" y1="16" x2="50" y2="16" stroke-width="2.5" />
      <polyline points="12,26 20,33 12,40" stroke-width="3" />
      <line x1="24" y1="40" x2="38" y2="40" stroke-width="3" />
    </g>
    <text x="615" y="477" text-anchor="middle" font-family="ui-monospace, monospace" font-size="34" font-weight="bold" fill="#303a36">c</text>
  </g>

  <!-- Node: end (center 405, 670, w=180, h=64) -->
  <g id="left-end">
    <rect x="315" y="638" width="180" height="64" rx="32" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <circle cx="343" cy="670" r="13" fill="none" stroke="#207448" stroke-width="3.5" />
    <circle cx="343" cy="670" r="4.5" fill="#207448" />
    <text x="418" y="679" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">end</text>
  </g>

  <!-- ========================================== -->
  <!-- RIGHT PANEL: a && b || c                   -->
  <!-- ========================================== -->
  <rect x="810" y="110" width="750" height="615" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  
  <!-- Right Header -->
  <text x="1185" y="152" text-anchor="middle" font-family="ui-monospace, monospace" font-size="30" font-weight="bold" fill="#207448">a &amp;&amp; b || c</text>

  <!-- Right Arrows (drawn behind nodes) -->
  <!-- 1. start -> diamond 'a succeeds?' -->
  <line x1="1035" y1="210" x2="1035" y2="230" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 2. diamond 1 -> box 'b' (yes) -->
  <line x1="1035" y1="374" x2="1035" y2="390" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1052" y="386" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">yes</text>

  <!-- 3. box 'b' -> diamond 2 'b succeeded?' -->
  <line x1="1035" y1="462" x2="1035" y2="478" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 4. diamond 2 -> end (yes) -->
  <line x1="1035" y1="622" x2="1035" y2="638" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1052" y="632" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">yes</text>

  <!-- 5. diamond 1 -> box 'c' (labelled 'a failed') -->
  <!-- leaves diamond 1 right vertex (1275, 302) -> right to 1400, down to top of box c (1400, 368) -->
  <path d="M 1275 302 L 1400 302 L 1400 366" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1335" y="290" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">a failed</text>

  <!-- 6. diamond 2 -> box 'c' (labelled 'b failed') -->
  <!-- leaves diamond 2 right vertex (1275, 550) -> right to 1400, up to bottom of box c (1400, 552) -->
  <path d="M 1275 550 L 1400 550 L 1400 552" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1335" y="574" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">b failed</text>

  <!-- Right Nodes -->
  <!-- Node: start (center 1035, 178, w=180, h=64) -->
  <g id="right-start">
    <rect x="945" y="146" width="180" height="64" rx="32" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <polygon points="968,168 968,188 984,178" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round" />
    <text x="1048" y="187" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">start</text>
  </g>

  <!-- Node: diamond 1 'a succeeds?' (center 1035, 302, rx=240, ry=72 -> w=480, h=144) -->
  <g id="right-diamond-a">
    <polygon points="1035,230 1275,302 1035,374 795,302" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(920, 286)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="16" r="13" />
      <path d="M 13 11 C 13 6, 19 6, 19 12 C 19 15, 16 15, 16 19" />
      <circle cx="16" cy="24" r="1.5" fill="#207448" />
    </g>
    <text x="1065" y="312" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">a succeeds?</text>
  </g>

  <!-- Node: box 'b' (x=935, y=392, w=200, h=70) -->
  <g id="right-box-b">
    <rect x="935" y="392" width="200" height="70" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(955, 408)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="44" height="38" rx="5" />
      <line x1="2" y1="14" x2="46" y2="14" stroke-width="2.5" />
      <polyline points="10,23 17,29 10,35" stroke-width="2.5" />
      <line x1="21" y1="35" x2="33" y2="35" stroke-width="2.5" />
    </g>
    <text x="1055" y="439" text-anchor="middle" font-family="ui-monospace, monospace" font-size="34" font-weight="bold" fill="#303a36">b</text>
  </g>

  <!-- Node: diamond 2 'b succeeded?' (center 1035, 550, rx=240, ry=72 -> w=480, h=144) -->
  <g id="right-diamond-b">
    <polygon points="1035,478 1275,550 1035,622 795,550" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(905, 534)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="16" r="13" />
      <path d="M 13 11 C 13 6, 19 6, 19 12 C 19 15, 16 15, 16 19" />
      <circle cx="16" cy="24" r="1.5" fill="#207448" />
    </g>
    <text x="1060" y="560" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">b succeeded?</text>
  </g>

  <!-- Node: end (center 1035, 670, w=180, h=64) -->
  <g id="right-end">
    <rect x="945" y="638" width="180" height="64" rx="32" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <circle cx="973" cy="670" r="13" fill="none" stroke="#207448" stroke-width="3.5" />
    <circle cx="973" cy="670" r="4.5" fill="#207448" />
    <text x="1048" y="679" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">end</text>
  </g>

  <!-- Node: box 'c' (ORANGE OUTLINED) with 'c runs even though a succeeded' -->
  <!-- x=1265, y=368, w=275, h=182 -->
  <g id="right-box-c">
    <rect x="1265" y="368" width="275" height="182" rx="14" fill="#fff9f3" stroke="#db8129" stroke-width="3.5" />
    <!-- Warning outline icon in orange -->
    <g transform="translate(1283, 428)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="24,4 46,42 2,42" />
      <line x1="24" y1="17" x2="24" y2="29" stroke-width="3.5" />
      <line x1="24" y1="35" x2="24" y2="37" stroke-width="4" />
    </g>
    <!-- Label: 'c' -->
    <text x="1355" y="418" font-family="ui-monospace, monospace" font-size="34" font-weight="bold" fill="#303a36">c</text>
    <!-- Label: 'c runs even though a succeeded' -->
    <text x="1355" y="458" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#db8129">
      <tspan x="1355" dy="0">c runs even </tspan>
      <tspan x="1355" dy="28">though </tspan>
      <tspan x="1355" dy="28">a succeeded</tspan>
    </text>
  </g>

  <!-- ========================================== -->
  <!-- BELOW: LIST OF GOOD ONE-LINE GUARDS        -->
  <!-- ========================================== -->
  <rect x="40" y="765" width="1520" height="280" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />

  <!-- Guard 1: [ -d "$d" ] || mkdir -p "$d" -->
  <g id="guard-1">
    <rect x="60" y="776" width="1480" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(80, 792)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 3 6 L 11 6 L 15 11 L 26 11 A 2 2 0 0 1 28 13 L 28 24 A 2 2 0 0 1 26 26 L 3 26 A 2 2 0 0 1 1 24 L 1 8 A 2 2 0 0 1 3 6 Z" />
    </g>
    <text x="130" y="814" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">[ -d "$d" ] || mkdir -p "$d"</text>
  </g>

  <!-- Guard 2: command -v nvidia-smi >/dev/null || exit 0 -->
  <g id="guard-2">
    <rect x="60" y="844" width="1480" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(80, 860)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="5" y="5" width="20" height="20" rx="3" />
      <circle cx="15" cy="15" r="4" />
      <line x1="10" y1="1" x2="10" y2="5" />
      <line x1="20" y1="1" x2="20" y2="5" />
      <line x1="10" y1="25" x2="10" y2="29" />
      <line x1="20" y1="25" x2="20" y2="29" />
      <line x1="1" y1="10" x2="5" y2="10" />
      <line x1="1" y1="20" x2="5" y2="20" />
      <line x1="25" y1="10" x2="29" y2="10" />
      <line x1="25" y1="20" x2="29" y2="20" />
    </g>
    <text x="130" y="882" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">command -v nvidia-smi &gt;/dev/null || exit 0</text>
  </g>

  <!-- Guard 3: cd "$dir" || exit 1 -->
  <g id="guard-3">
    <rect x="60" y="912" width="1480" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(80, 928)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="5,21 15,8 25,21" />
      <line x1="15" y1="10" x2="15" y2="26" />
    </g>
    <text x="130" y="950" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">cd "$dir" || exit 1</text>
  </g>

  <!-- Guard 4: [ -z "$x" ] && {{ echo "empty" >&2; exit 1; }} -->
  <g id="guard-4">
    <rect x="60" y="980" width="1480" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(80, 996)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 15 3 L 26 7 C 26 19 15 26 15 26 C 15 26 4 19 4 7 Z" />
      <polyline points="10,14 13,17 20,10" />
    </g>
    <text x="130" y="1018" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">[ -z "$x" ] &amp;&amp; &#123; echo "empty" &gt;&amp;2; exit 1; &#125;</text>
  </g>

  <!-- ========================================== -->
  <!-- BOTTOM NOTE / TAKEAWAY BAR                 -->
  <!-- ========================================== -->
  <rect x="40" y="1085" width="1520" height="70" rx="14" fill="#207448" />
  <text x="800" y="1129" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">&amp;&amp; runs the next command only if the last one succeeded; || only if it failed</text>
</svg>''')
    return "".join(parts)

svg_str = generate_svg()
pathlib.Path("test_candidate_trap_perfect.svg").write_text(svg_str)
print("Saved test_candidate_trap_perfect.svg")

async def test():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={'width': 1600, 'height': 1200})
        await page.goto('file://' + str(pathlib.Path('test_candidate_trap_perfect.svg').resolve()))
        
        # 1. Margin audit
        margin_issues = await page.evaluate('''() => {
            const issues = [];
            const allElements = Array.from(document.querySelectorAll('text, rect, circle, path, polygon, line'));
            for (const el of allElements) {
                if (el.closest('defs')) continue;
                if (el.tagName.toLowerCase() === 'rect' && el.getAttribute('width') == '1600' && el.getAttribute('height') == '1200') {
                    continue; // background
                }
                const r = el.getBoundingClientRect();
                if (r.top < 39.5) {
                    issues.push(`Top margin violation (<40): ${el.tagName} at top=${r.top.toFixed(1)}, text='${(el.textContent||'').slice(0,30)}'`);
                }
                if (r.bottom > 1160.5) {
                    issues.push(`Bottom margin violation (>1160): ${el.tagName} at bottom=${r.bottom.toFixed(1)}`);
                }
                if (r.left < 39.5) {
                    issues.push(`Left margin violation (<40): ${el.tagName} at left=${r.left.toFixed(1)}`);
                }
                if (r.right > 1560.5) {
                    issues.push(`Right margin violation (>1560): ${el.tagName} at right=${r.right.toFixed(1)}`);
                }
            }
            return issues;
        }''')
        print("Margin issues:", margin_issues)
        
        # 2. Text paddings
        pad_data = await page.evaluate('''() => {
            const texts = [];
            for (const t of document.querySelectorAll("text")) {
                const b = t.getBBox();
                texts.push({
                    text: t.textContent.trim().replace(/\\s+/g, " "),
                    x: b.x, y: b.y, w: b.width, h: b.height, r: b.x + b.width, bot: b.y + b.height
                });
            }
            const rects = [];
            for (const r of document.querySelectorAll("rect")) {
                const b = r.getBBox();
                rects.push({
                    x: b.x, y: b.y, w: b.width, h: b.height, r: b.x + b.width, bot: b.y + b.height
                });
            }
            return { texts, rects };
        }''')
        
        print("\n--- Checking All Text Elements Against Containers ---")
        for t in pad_data["texts"]:
            containing = [r for r in pad_data["rects"] if r['x'] <= t['x'] and r['r'] >= t['r'] and r['y'] <= t['y'] and r['bot'] >= t['bot']]
            if containing:
                c = min(containing, key=lambda r: r['w'] * r['h'])
                pad_l = t['x'] - c['x']
                pad_r = c['r'] - t['r']
                pad_t = t['y'] - c['y']
                pad_b = c['bot'] - t['bot']
                min_pad = min(pad_l, pad_r, pad_t, pad_b)
                status = "PASS" if min_pad >= 16.0 else f"FAIL (min={min_pad:.1f}px)"
                print(f"Text '{t['text'][:35]:35s}': L={pad_l:4.1f}, R={pad_r:4.1f}, T={pad_t:4.1f}, B={pad_b:4.1f} -> {status}")

        # Check diamonds
        # Left diamond: cx=405, cy=310, rx=250, ry=72
        t_left_a = [t for t in pad_data["texts"] if t["text"] == "a succeeds?"][0]
        pts_la = [(t_left_a['x'], t_left_a['y']), (t_left_a['r'], t_left_a['y']), (t_left_a['x'], t_left_a['bot']), (t_left_a['r'], t_left_a['bot']),
                  (295, 292), (331, 292), (295, 328), (331, 328)]
        d_la = min(dist_to_diamond(px, py, 405, 310, 250, 72) for px, py in pts_la)
        print(f"\nLeft Diamond: min_dist = {d_la:.2f}px ({'PASS' if d_la>=16 else 'FAIL'})")

        # Right diamond 1: cx=1035, cy=302, rx=240, ry=72
        t_r1 = [t for t in pad_data["texts"] if t["text"] == "a succeeds?"][1]
        pts_r1 = [(t_r1['x'], t_r1['y']), (t_r1['r'], t_r1['y']), (t_r1['x'], t_r1['bot']), (t_r1['r'], t_r1['bot']),
                  (920, 286), (952, 286), (920, 318), (952, 318)]
        d_r1 = min(dist_to_diamond(px, py, 1035, 302, 240, 72) for px, py in pts_r1)
        print(f"Right Diamond 1: min_dist = {d_r1:.2f}px ({'PASS' if d_r1>=16 else 'FAIL'})")

        # Right diamond 2: cx=1035, cy=550, rx=240, ry=72
        t_r2 = [t for t in pad_data["texts"] if t["text"] == "b succeeded?"][0]
        pts_r2 = [(t_r2['x'], t_r2['y']), (t_r2['r'], t_r2['y']), (t_r2['x'], t_r2['bot']), (t_r2['r'], t_r2['bot']),
                  (905, 534), (937, 534), (905, 566), (937, 566)]
        d_r2 = min(dist_to_diamond(px, py, 1035, 550, 240, 72) for px, py in pts_r2)
        print(f"Right Diamond 2: min_dist = {d_r2:.2f}px ({'PASS' if d_r2>=16 else 'FAIL'})")

        await b.close()

asyncio.run(test())
