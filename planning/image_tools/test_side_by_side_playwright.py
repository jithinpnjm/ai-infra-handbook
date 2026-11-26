import asyncio
from playwright.async_api import async_playwright
import xml.etree.ElementTree as ET
import re, pathlib

def build_svg():
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    lines.append('  <title>Toy router simulation: policies and the bound sweep</title>')
    lines.append('  <desc>Comparison of routing policies and backlog bound sweep showing hit rate, latency percentiles, and load imbalance.</desc>')
    lines.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    lines.append('')
    
    # Title (48px bold)
    lines.append('  <!-- ==================== TITLE ==================== -->')
    lines.append('  <text x="800" y="54" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Toy router simulation: policies and the bound sweep</text>')
    lines.append('')
    
    # Subtitle Pill
    # y = 72..136 (h = 64)
    lines.append('  <!-- ==================== SUBTITLE PILL ==================== -->')
    lines.append('  <rect x="450" y="72" width="700" height="64" rx="32" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    lines.append('  <text x="800" y="112" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">toy numbers chosen to show the mechanism</text>')
    lines.append('')
    
    # Setup Container (Node 1)
    # y = 176..270 (h = 94)
    lines.append('  <!-- ==================== SETUP CONTAINER ==================== -->')
    lines.append('  <rect x="50" y="176" width="1500" height="94" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Gear Icon at x = 75, y = 195 (56x56)
    lines.append('  <g transform="translate(75, 195)" stroke="#207448" stroke-width="4" fill="none">')
    lines.append('    <circle cx="28" cy="28" r="12"/>')
    lines.append('    <path d="M 28 4 L 28 10 M 28 46 L 28 52 M 4 28 L 10 28 M 46 28 L 52 28 M 11 11 L 15 15 M 41 41 L 45 45 M 11 45 L 15 41 M 41 11 L 45 15"/>')
    lines.append('  </g>')
    # Setup Text (2 lines)
    lines.append('  <text x="155" y="215" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="155" dy="0">Setup: eight replicas, forty prefixes, one hot prefix with 40 percent of traffic,</tspan>')
    lines.append('    <tspan x="155" dy="33">cache of six prefixes per replica, hit costs 0.10 s and miss 0.50 s</tspan>')
    lines.append('  </text>')
    lines.append('')
    
    # ==================== TABLE 1: LEFT PANEL ====================
    # x = 50..775 (w = 725), y = 312..932 (h = 620)
    lines.append('  <!-- ==================== TABLE 1: POLICIES ==================== -->')
    lines.append('  <rect x="50" y="312" width="725" height="620" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    
    # Header card inside T1: x = 70..755 (w = 685), y = 328..424 (h = 96)
    lines.append('  <rect x="70" y="328" width="685" height="96" rx="10" fill="#e8f1ea"/>')
    # Chip Icon at x = 85, y = 348 (56x56)
    lines.append('  <g transform="translate(85, 348)" stroke="#207448" stroke-width="4" fill="none">')
    lines.append('    <rect x="10" y="10" width="36" height="36" rx="6"/>')
    lines.append('    <line x1="18" y1="4" x2="18" y2="10"/><line x1="28" y1="4" x2="28" y2="10"/><line x1="38" y1="4" x2="38" y2="10"/>')
    lines.append('    <line x1="18" y1="46" x2="18" y2="52"/><line x1="28" y1="46" x2="28" y2="52"/><line x1="38" y1="46" x2="38" y2="52"/>')
    lines.append('    <line x1="4" y1="18" x2="10" y2="18"/><line x1="4" y1="28" x2="10" y2="28"/><line x1="4" y1="38" x2="10" y2="38"/>')
    lines.append('    <line x1="46" y1="18" x2="52" y2="18"/><line x1="46" y1="28" x2="52" y2="28"/><line x1="46" y1="38" x2="52" y2="38"/>')
    lines.append('  </g>')
    # Header text (30px bold, 2 lines)
    lines.append('  <text x="160" y="366" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="160" dy="0">Table 1 policy:</tspan>')
    lines.append('    <tspan x="160" dy="35" font-size="24">hit rate, p50 s, p99 s, max over mean load</tspan>')
    lines.append('  </text>')

    # T1 Rows: 4 rows of 110px each
    # Row 1: y = 438..548 (h = 110)
    # Row 2: y = 560..670 (h = 110)
    # Row 3: y = 682..792 (h = 110)
    # Row 4: y = 804..914 (h = 110)
    
    # T1 Row 1: round_robin
    lines.append('  <rect x="70" y="438" width="685" height="110" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="90" y="478" font-family="monospace" font-size="24" fill="#303a36">round_robin 0.46, 0.50, 2.33, 1.00</text>')
    lines.append('  <rect x="90" y="504" width="138" height="24" rx="4" fill="#207448"/>')
    lines.append('  <rect x="240" y="504" width="163" height="24" rx="4" fill="#c2dac7"/>')
    lines.append('  <rect x="415" y="504" width="70" height="24" rx="4" fill="#207448"/>')

    # T1 Row 2: least_loaded
    lines.append('  <rect x="70" y="560" width="685" height="110" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="90" y="600" font-family="monospace" font-size="24" fill="#303a36">least_loaded 0.46, 0.50, 1.22, 1.16</text>')
    lines.append('  <rect x="90" y="626" width="138" height="24" rx="4" fill="#207448"/>')
    lines.append('  <rect x="240" y="626" width="85" height="24" rx="4" fill="#c2dac7"/>')
    lines.append('  <rect x="337" y="626" width="81" height="24" rx="4" fill="#207448"/>')

    # T1 Row 3: cache_only
    lines.append('  <rect x="70" y="682" width="685" height="110" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="90" y="722" font-family="monospace" font-size="24" fill="#303a36">cache_only 0.98, 0.16, 4.39, 3.80</text>')
    lines.append('  <rect x="90" y="748" width="294" height="24" rx="4" fill="#207448"/>')
    lines.append('  <rect x="396" y="748" width="219" height="24" rx="4" fill="#c2dac7"/>')

    # T1 Row 4: cache_bounded
    lines.append('  <rect x="70" y="804" width="685" height="110" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="90" y="844" font-family="monospace" font-size="24" fill="#303a36">cache_bounded 0.95, 0.10, 0.50, 2.13</text>')
    lines.append('  <rect x="90" y="870" width="285" height="24" rx="4" fill="#207448"/>')
    lines.append('  <rect x="387" y="870" width="35" height="24" rx="4" fill="#207448"/>')
    lines.append('  <rect x="434" y="870" width="149" height="24" rx="4" fill="#207448"/>')
    lines.append('')
    
    # ==================== TABLE 2: RIGHT PANEL ====================
    # x = 825..1550 (w = 725), y = 312..932 (h = 620)
    lines.append('  <!-- ==================== TABLE 2: BOUND SWEEP ==================== -->')
    lines.append('  <rect x="825" y="312" width="725" height="620" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')

    # Header card inside T2: x = 845..1530 (w = 685), y = 328..424 (h = 96)
    lines.append('  <rect x="845" y="328" width="685" height="96" rx="10" fill="#e8f1ea"/>')
    # Clock Icon at x = 860, y = 348 (56x56)
    lines.append('  <g transform="translate(860, 348)" stroke="#207448" stroke-width="4" fill="none">')
    lines.append('    <circle cx="28" cy="28" r="22"/>')
    lines.append('    <polyline points="28,14 28,28 38,28"/>')
    lines.append('  </g>')
    # Header text (30px bold, 2 lines)
    lines.append('  <text x="935" y="366" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="935" dy="0">Table 2 bound in seconds</tspan>')
    lines.append('    <tspan x="935" dy="35" font-size="24">of backlog</tspan>')
    lines.append('  </text>')

    # T2 Rows: 5 rows
    # Row 1: y = 434..526 (h = 92)
    # Row 2: y = 534..618 (h = 84)
    # Row 3: y = 626..710 (h = 84) (ORANGE highlighted sweet spot!)
    # Row 4: y = 718..802 (h = 84)
    # Row 5: y = 810..902 (h = 92)

    # T2 Row 1: 0.0 (2 lines of text)
    lines.append('  <rect x="845" y="434" width="685" height="92" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="865" y="471" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="865" dy="0">0.0: hit 0.57, p50 0.22,</tspan>')
    lines.append('    <tspan x="865" dy="33">p99 0.99, max/mean 1.22</tspan>')
    lines.append('  </text>')
    lines.append('  <rect x="1275" y="454" width="114" height="22" rx="4" fill="#207448"/>')
    lines.append('  <rect x="1400" y="454" width="69" height="22" rx="4" fill="#c2dac7"/>')
    lines.append('  <rect x="1478" y="454" width="35" height="22" rx="4" fill="#207448"/>')

    # T2 Row 2: 0.1 (1 line of text!)
    lines.append('  <rect x="845" y="534" width="685" height="84" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="865" y="574" font-family="monospace" font-size="24" fill="#303a36">0.1: 0.89, 0.10, 0.52, 1.56</text>')
    lines.append('  <rect x="1275" y="563" width="178" height="22" rx="4" fill="#207448"/>')
    lines.append('  <rect x="1460" y="563" width="36" height="22" rx="4" fill="#c2dac7"/>')

    # T2 Row 3: 0.5 (Single ORANGE highlight for optimal bound!)
    lines.append('  <rect x="845" y="626" width="685" height="84" rx="10" fill="#f5f8f5" stroke="#db8129" stroke-width="3"/>')
    lines.append('  <text x="865" y="666" font-family="monospace" font-size="24" fill="#303a36">0.5: 0.95, 0.10, 0.50, 2.13</text>')
    lines.append('  <rect x="1275" y="655" width="190" height="22" rx="4" fill="#207448"/>')
    lines.append('  <rect x="1472" y="655" width="35" height="22" rx="4" fill="#207448"/>')

    # T2 Row 4: 2.0 (1 line of text!)
    lines.append('  <rect x="845" y="718" width="685" height="84" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="865" y="758" font-family="monospace" font-size="24" fill="#303a36">2.0: 0.98, 0.11, 1.68, 3.39</text>')
    lines.append('  <rect x="1275" y="747" width="196" height="22" rx="4" fill="#207448"/>')
    lines.append('  <rect x="1478" y="747" width="35" height="22" rx="4" fill="#c2dac7"/>')

    # T2 Row 5: 100 (cache-only) (1 line of text!)
    lines.append('  <rect x="845" y="810" width="685" height="92" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="865" y="851" font-family="monospace" font-size="24" fill="#303a36">100 (cache-only): 0.98, 0.16, 4.39, 3.80</text>')
    lines.append('  <rect x="865" y="868" width="294" height="22" rx="4" fill="#207448"/>')
    lines.append('  <rect x="1170" y="868" width="263" height="22" rx="4" fill="#c2dac7"/>')
    lines.append('')

    # Takeaway Bar (Node 4)
    # y = 975..1150 (h = 175)
    lines.append('  <!-- ==================== TAKEAWAY BAR ==================== -->')
    lines.append('  <rect x="50" y="975" width="1500" height="175" rx="14" fill="#207448"/>')
    lines.append('  <text x="800" y="1022" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">')
    lines.append('    <tspan x="800" dy="0">cache-only wins hit rate and loses the tail because</tspan>')
    lines.append('    <tspan x="800" dy="34">one replica carries 3.8 times the average load; least-loaded keeps load flat</tspan>')
    lines.append('    <tspan x="800" dy="34">but wastes the cache; sweep the bound against p99, not hit rate;</tspan>')
    lines.append('    <tspan x="800" dy="34">zero bound behaves like least-loaded, a huge bound like cache-only</tspan>')
    lines.append('  </text>')
    lines.append('</svg>')

    return "\n".join(lines)

svg_str = build_svg()
with open("test_side_by_side_playwright.svg", "w") as f:
    f.write(svg_str)
print("Saved test_side_by_side_playwright.svg")

async def measure_all():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1600, "height": 1200})
        await page.goto("file://" + str(pathlib.Path("test_side_by_side_playwright.svg").resolve()))
        data = await page.evaluate('''() => {
            const results = [];
            for (const t of document.querySelectorAll("text")) {
                const b = t.getBBox();
                results.push({
                    text: t.textContent.trim().replace(/\\s+/g, " "),
                    x: b.x, y: b.y, w: b.width, h: b.height,
                    r: b.x + b.width, bot: b.y + b.height
                });
            }
            return results;
        }''')
        await b.close()
        return data

results = asyncio.run(measure_all())
print(f"Total measured: {len(results)}")
for i, r in enumerate(results, 1):
    txt = r['text'][:35]
    print(f"{i:2d}. {txt:35s} | x={r['x']:6.1f}..{r['r']:6.1f} (w={r['w']:5.1f}) | y={r['y']:6.1f}..{r['bot']:6.1f} (h={r['h']:4.1f})")
