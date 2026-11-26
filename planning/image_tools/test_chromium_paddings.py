import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright
import pathlib

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>The sawtooth and the cut streams need two separate fixes</title>
  <desc>Visual infographic explaining why autoscaler flapping and undrained scale-down require two distinct fixes: lengthening the stabilization window and deploying the connection draining stack.</desc>

  <!-- Background -->
  <rect width="1600" height="1080" fill="#f5f8f5" />

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">The sawtooth and the cut streams need two separate fixes</text>

  <!-- ==================== SETUP STRIP ==================== -->
  <g id="setup-strip">
    <rect x="40" y="105" width="1520" height="165" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Clock / Pulse Timer Icon (56x56, stroke 4, green) -->
    <g transform="translate(68, 160)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" fill="#ffffff" />
      <polyline points="28,14 28,28 38,28" />
      <path d="M 46 10 L 52 16" />
      <path d="M 10 10 L 4 16" />
    </g>
    <text x="156" y="145" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="156" dy="0">short burst every six minutes;</tspan>
      <tspan x="156" dy="33">autoscaler removes replicas after each burst</tspan>
      <tspan x="156" dy="33">and adds them back a few minutes later;</tspan>
      <tspan x="156" dy="33">users report streams that stop halfway</tspan>
    </text>
  </g>

  <!-- ==================== TWO PROBLEM BOXES (LEFT COLUMN) ==================== -->
  <!-- Problem 1: Flapping wastes cold starts -->
  <g id="problem-1">
    <rect x="40" y="310" width="740" height="265" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Sawtooth / Activity Flapping Icon (56x56, stroke 4, green) -->
    <g transform="translate(68, 330)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="44" rx="8" fill="#e8f1ea" />
      <polyline points="12,34 20,18 28,34 36,18 44,34" />
    </g>
    <text x="156" y="354" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="156" dy="0" font-weight="bold">flapping wastes cold starts:</tspan>
      <tspan x="156" dy="33">in-flight policy with no window</tspan>
      <tspan x="156" dy="33">starts 130 replicas in an hour</tspan>
      <tspan x="156" dy="33">and reverses direction 19 times;</tspan>
      <tspan x="156" dy="33">with a 300 s window it starts 13</tspan>
      <tspan x="156" dy="33">and reverses once</tspan>
    </text>
  </g>

  <!-- Problem 2: Scale-down without a drain cuts streams -->
  <g id="problem-2">
    <rect x="40" y="615" width="740" height="265" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Severed Stream Icon (56x56, stroke 4, green) -->
    <g transform="translate(68, 635)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="44" rx="8" fill="#e8f1ea" />
      <path d="M 14 20 L 24 28 L 14 36" />
      <line x1="28" y1="16" x2="28" y2="40" stroke-dasharray="4 4" />
      <path d="M 42 20 L 32 28 L 42 36" />
    </g>
    <text x="156" y="665" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="156" dy="0" font-weight="bold">scale-down without a drain</tspan>
      <tspan x="156" dy="36">cuts streams: waiting-queue</tspan>
      <tspan x="156" dy="36">policy with no drain</tspan>
      <tspan x="156" dy="36">cut 168 streams</tspan>
    </text>
  </g>

  <!-- ==================== FIX COLUMN (RIGHT COLUMN) ==================== -->
  <!-- Highlighted in orange as the single most important item containing the two separate fixes -->
  <g id="fix-column">
    <rect x="820" y="310" width="740" height="570" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3.5" />
    <!-- Shield / Protection Solution Icon (56x56, stroke 4, green) -->
    <g transform="translate(850, 335)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 28 C 48 42 28 50 28 50 C 28 50 8 42 8 28 V 14 Z" fill="#e8f1ea" />
      <polyline points="20,27 26,33 36,21" />
    </g>
    <text x="936" y="357" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="936" dy="0" font-weight="bold">lengthen the window beyond the</tspan>
      <tspan x="936" dy="36">cold start and slow the scale-down</tspan>
      <tspan x="936" dy="36">(removes most cold starts);</tspan>
      <tspan x="936" dy="50" font-weight="bold">then add the drain stack</tspan>
      <tspan x="936" dy="36">from section 7: grace period,</tspan>
      <tspan x="936" dy="36">preStop pause, engine drain,</tspan>
      <tspan x="936" dy="36">PodDisruptionBudget</tspan>
    </text>
  </g>

  <!-- ==================== FOOTER TAKEAWAY ==================== -->
  <g id="footer-takeaway">
    <rect x="40" y="920" width="1520" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Info / Guardrail Icon (56x56, stroke 4, green) -->
    <g transform="translate(68, 952)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" fill="#ffffff" />
      <line x1="28" y1="24" x2="28" y2="38" />
      <circle cx="28" cy="17" r="2" fill="#207448" />
    </g>
    <text x="156" y="965" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="156" dy="0">fixing only flapping leaves users on a removed pod unprotected;</tspan>
      <tspan x="156" dy="36">fixing only the drain keeps the waste; all counts are simulator output</tspan>
    </text>
  </g>
</svg>'''

pathlib.Path("test_sawtooth_v3.svg").write_text(svg_content)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('file://' + str(pathlib.Path('test_sawtooth_v3.svg').resolve()))
    
    # Check boxes & paddings
    data = page.evaluate('''() => {
        const getB = sel => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const b = el.getBBox();
            return { x: b.x, y: b.y, width: b.width, height: b.height };
        };
        return {
            setup_rect: getB('#setup-strip rect'),
            setup_text: getB('#setup-strip text'),
            setup_icon: getB('#setup-strip g'),
            p1_rect: getB('#problem-1 rect'),
            p1_text: getB('#problem-1 text'),
            p1_icon: getB('#problem-1 g'),
            p2_rect: getB('#problem-2 rect'),
            p2_text: getB('#problem-2 text'),
            p2_icon: getB('#problem-2 g'),
            fix_rect: getB('#fix-column rect'),
            fix_text: getB('#fix-column text'),
            fix_icon: getB('#fix-column g'),
            footer_rect: getB('#footer-takeaway rect'),
            footer_text: getB('#footer-takeaway text'),
            footer_icon: getB('#footer-takeaway g'),
        };
    }''')
    browser.close()

for k in ['setup', 'p1', 'p2', 'fix', 'footer']:
    r = data[f'{k}_rect']
    t = data[f'{k}_text']
    ic = data[f'{k}_icon']
    
    top_p = t['y'] - r['y']
    bot_p = (r['y'] + r['height']) - (t['y'] + t['height'])
    left_p = t['x'] - r['x']
    right_p = (r['x'] + r['width']) - (t['x'] + t['width'])
    icon_p = t['x'] - (ic['x'] + ic['width'])
    
    print(f"=== {k.upper()} PADDINGS ===")
    print(f"  Top padding:    {top_p:5.1f} px  (>= 16)")
    print(f"  Bottom padding: {bot_p:5.1f} px  (>= 16)")
    print(f"  Left padding:   {left_p:5.1f} px  (>= 16)")
    print(f"  Right padding:  {right_p:5.1f} px  (>= 16)")
    print(f"  Icon to text:   {icon_p:5.1f} px  (>= 16)")
    
    assert top_p >= 16, f"[{k}] top_p {top_p} < 16"
    assert bot_p >= 16, f"[{k}] bot_p {bot_p} < 16"
    assert left_p >= 16, f"[{k}] left_p {left_p} < 16"
    assert right_p >= 16, f"[{k}] right_p {right_p} < 16"
    assert icon_p >= 16, f"[{k}] icon_p {icon_p} < 16"

print("\nALL CHROMIUM PADDINGS VERIFIED CLEANLY!")
