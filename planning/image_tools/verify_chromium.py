import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright
import pathlib

# Let's write the complete, updated SVG builder

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>The sawtooth and the cut streams need two separate fixes</title>
  <desc>Visual infographic explaining why autoscaler flapping and undrained scale-down require two distinct fixes: lengthening the stabilization window and deploying the connection draining stack.</desc>

  <!-- Background -->
  <rect width="1600" height="1080" fill="#f5f8f5" />

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">The sawtooth and the cut streams need two separate fixes</text>

  <!-- ==================== SETUP STRIP ==================== -->
  <g id="setup-strip">
    <rect x="40" y="105" width="1520" height="150" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Clock / Timer Icon (56x56, stroke 4, green) -->
    <g transform="translate(68, 152)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" fill="#ffffff" />
      <polyline points="28,14 28,28 38,28" />
      <path d="M 46 10 L 52 16" />
      <path d="M 10 10 L 4 16" />
    </g>
    <text x="156" y="148" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="156" dy="0">short burst every six minutes;</tspan>
      <tspan x="156" dy="35">autoscaler removes replicas after each burst</tspan>
      <tspan x="156" dy="35">and adds them back a few minutes later;</tspan>
      <tspan x="156" dy="35">users report streams that stop halfway</tspan>
    </text>
  </g>

  <!-- ==================== TWO PROBLEM BOXES (LEFT COLUMN) ==================== -->
  <!-- Problem 1: Flapping wastes cold starts -->
  <g id="problem-1">
    <rect x="40" y="295" width="740" height="260" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Sawtooth / Activity Flapping Icon (56x56, stroke 4, green) -->
    <g transform="translate(68, 320)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="44" rx="8" fill="#e8f1ea" />
      <polyline points="12,34 20,18 28,34 36,18 44,34" />
    </g>
    <text x="156" y="340" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="156" dy="0" font-weight="bold">flapping wastes cold starts:</tspan>
      <tspan x="156" dy="35">in-flight policy with no window starts 130</tspan>
      <tspan x="156" dy="35">replicas in an hour and reverses direction</tspan>
      <tspan x="156" dy="35">19 times; with a 300 s window it starts 13</tspan>
      <tspan x="156" dy="35">and reverses once</tspan>
    </text>
  </g>

  <!-- Problem 2: Scale-down without a drain cuts streams -->
  <g id="problem-2">
    <rect x="40" y="595" width="740" height="260" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Severed Stream Icon (56x56, stroke 4, green) -->
    <g transform="translate(68, 620)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="44" rx="8" fill="#e8f1ea" />
      <path d="M 14 20 L 24 28 L 14 36" />
      <line x1="28" y1="16" x2="28" y2="40" stroke-dasharray="4 4" />
      <path d="M 42 20 L 32 28 L 42 36" />
    </g>
    <text x="156" y="650" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="156" dy="0" font-weight="bold">scale-down without a drain cuts streams:</tspan>
      <tspan x="156" dy="36">waiting-queue policy with</tspan>
      <tspan x="156" dy="36">no drain cut 168 streams</tspan>
    </text>
  </g>

  <!-- ==================== FIX COLUMN (RIGHT COLUMN) ==================== -->
  <!-- Highlighted in orange as the single most important item containing the two separate fixes -->
  <g id="fix-column">
    <rect x="820" y="295" width="740" height="560" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3.5" />
    <!-- Shield / Protection Solution Icon (56x56, stroke 4, green) -->
    <g transform="translate(850, 325)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 28 C 48 42 28 50 28 50 C 28 50 8 42 8 28 V 14 Z" fill="#e8f1ea" />
      <polyline points="20,27 26,33 36,21" />
    </g>
    <text x="936" y="345" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="936" dy="0" font-weight="bold">lengthen the window beyond the</tspan>
      <tspan x="936" dy="36">cold start and slow the scale-down</tspan>
      <tspan x="936" dy="36">(removes most cold starts);</tspan>
      <tspan x="936" dy="48" font-weight="bold">then add the drain stack</tspan>
      <tspan x="936" dy="36">from section 7: grace period,</tspan>
      <tspan x="936" dy="36">preStop pause, engine drain,</tspan>
      <tspan x="936" dy="36">PodDisruptionBudget</tspan>
    </text>
  </g>

  <!-- ==================== FOOTER TAKEAWAY ==================== -->
  <g id="footer-takeaway">
    <rect x="40" y="895" width="1520" height="145" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Info / Guardrail Icon (56x56, stroke 4, green) -->
    <g transform="translate(68, 940)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" fill="#ffffff" />
      <line x1="28" y1="24" x2="28" y2="38" />
      <circle cx="28" cy="17" r="2" fill="#207448" />
    </g>
    <text x="156" y="955" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="156" dy="0">fixing only flapping leaves users on a removed pod unprotected;</tspan>
      <tspan x="156" dy="36">fixing only the drain keeps the waste; all counts are simulator output</tspan>
    </text>
  </g>
</svg>'''

pathlib.Path("test_sawtooth_v2.svg").write_text(svg_content)
print("Wrote test_sawtooth_v2.svg")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('file://' + str(pathlib.Path('test_sawtooth_v2.svg').resolve()))
    
    # Check bounding boxes of all text elements
    texts = page.evaluate('''() => {
        const textElems = Array.from(document.querySelectorAll('text'));
        return textElems.map(t => {
            const b = t.getBBox();
            return {
                text: t.textContent.replace(/\\s+/g, ' ').trim(),
                x: b.x,
                y: b.y,
                width: b.width,
                height: b.height,
                right: b.x + b.width,
                bottom: b.y + b.height
            };
        });
    }''')
    
    # Check rects
    rects = page.evaluate('''() => {
        const rectElems = Array.from(document.querySelectorAll('rect'));
        return rectElems.map(r => {
            const b = r.getBBox();
            return {
                id: r.parentElement.id || 'rect',
                x: b.x,
                y: b.y,
                width: b.width,
                height: b.height,
                right: b.x + b.width,
                bottom: b.y + b.height
            };
        });
    }''')
    
    browser.close()

print(f"\\nChromium measured {len(texts)} text elements:")
for i, t in enumerate(texts, 1):
    print(f"{i}. '{t['text'][:40]}...' x={t['x']:.1f}, right={t['right']:.1f}, y={t['y']:.1f}, bottom={t['bottom']:.1f}")

print(f"\\nChromium measured major rects:")
for r in rects:
    if r['width'] >= 100:
        print(f"  [{r['id']}] x={r['x']:.1f}, y={r['y']:.1f}, w={r['width']:.1f}, h={r['height']:.1f}, right={r['right']:.1f}, bottom={r['bottom']:.1f}")
