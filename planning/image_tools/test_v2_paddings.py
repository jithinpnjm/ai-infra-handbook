import pathlib
from playwright.sync_api import sync_playwright

def build_svg(H=1200):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">
  <title>Collection traps: shared inner lists, mutating while iterating, and slow membership</title>
  <desc>Visual infographic explaining Python collection traps: shared inner lists in nested lists, dict.fromkeys sharing one list, mutating collections while iterating, slow linear list membership, collection operation costs, hashable key rules, and type performance trade-offs.</desc>

  <!-- Background -->
  <rect width="1600" height="{H}" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="58" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Collection traps: shared inner lists,</tspan>
    <tspan x="800" dy="54">mutating while iterating, and slow membership</tspan>
  </text>

  <!-- ======================================================== -->
  <!-- TOP ROW: Panel 1 (left) and Panel 2 (right)              -->
  <!-- ======================================================== -->

  <!-- Panel 1: grid = [[0] * 3] * 3 -->
  <g id="panel-1">
    <rect x="40" y="145" width="740" height="225" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    
    <!-- Grid outline icon (56px, stroke 4) -->
    <g transform="translate(65, 158)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="46" height="46" rx="6" />
      <line x1="17" y1="2" x2="17" y2="48" stroke-width="3" />
      <line x1="33" y1="2" x2="33" y2="48" stroke-width="3" />
      <line x1="2" y1="17" x2="48" y2="17" stroke-width="3" />
      <line x1="2" y1="33" x2="48" y2="33" stroke-width="3" />
    </g>

    <!-- Title: grid = [[0] * 3] * 3 -->
    <text x="135" y="194" font-family="ui-monospace, monospace" font-size="30" font-weight="bold" fill="#303a36">grid = [[0] * 3] * 3</text>

    <!-- Problem card (orange #db8129 highlight - single most important item) -->
    <rect x="60" y="218" width="700" height="82" rx="10" fill="#fff9f3" stroke="#db8129" stroke-width="2.5" />
    <text x="80" y="250" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#db8129">
      <tspan x="80" dy="0">three references to the same inner list,</tspan>
      <tspan x="80" dy="28">so changing one row changes all</tspan>
    </text>

    <!-- Fix card -->
    <rect x="60" y="308" width="700" height="50" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="80" y="341" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448">[[0] * 3 for _ in range(3)]</text>
  </g>

  <!-- Panel 2: d = dict.fromkeys(keys, []) -->
  <g id="panel-2">
    <rect x="820" y="145" width="740" height="225" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Key outline icon (56px, stroke 4) -->
    <g transform="translate(845, 158)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="24" r="11" />
      <line x1="27" y1="24" x2="48" y2="24" />
      <line x1="38" y1="24" x2="38" y2="33" />
      <line x1="46" y1="24" x2="46" y2="33" />
    </g>

    <!-- Title: d = dict.fromkeys(keys, []) -->
    <text x="915" y="194" font-family="ui-monospace, monospace" font-size="30" font-weight="bold" fill="#303a36">d = dict.fromkeys(keys, [])</text>

    <!-- Problem card -->
    <rect x="840" y="218" width="700" height="50" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="860" y="251" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">one list shared across all keys</text>

    <!-- Fix card -->
    <rect x="840" y="276" width="700" height="82" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="860" y="308" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="860" dy="0">fix with a comprehension</tspan>
      <tspan x="860" dy="28">that makes a new list per key</tspan>
    </text>
  </g>

  <!-- ======================================================== -->
  <!-- BOTTOM ROW: Panel 3 (left) and Panel 4 (right)           -->
  <!-- ======================================================== -->

  <!-- Panel 3: for x in lst: lst.remove(x) -->
  <g id="panel-3">
    <rect x="40" y="395" width="740" height="260" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Loop/cycle outline icon (56px, stroke 4) -->
    <g transform="translate(65, 408)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 26 8 A 17 17 0 1 1 10 31" />
      <polyline points="26,2 26,10 34,10" />
      <line x1="20" y1="25" x2="32" y2="25" stroke-width="3" />
    </g>

    <!-- Title: for x in lst: lst.remove(x) -->
    <text x="135" y="444" font-family="ui-monospace, monospace" font-size="30" font-weight="bold" fill="#303a36">for x in lst: lst.remove(x)</text>

    <!-- Skips elements card -->
    <rect x="60" y="468" width="700" height="46" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="80" y="499" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">skips elements</text>

    <!-- Dict RuntimeError card -->
    <rect x="60" y="522" width="700" height="74" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="80" y="551" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="80" dy="0">mutating a dict's size during iteration</tspan>
      <tspan x="80" dy="26">raises RuntimeError</tspan>
    </text>

    <!-- Fix card -->
    <rect x="60" y="604" width="700" height="44" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="80" y="633" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">iterate over a copy or build a new collection</text>
  </g>

  <!-- Panel 4: x in list on large data -->
  <g id="panel-4">
    <rect x="820" y="395" width="740" height="260" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Search/gauge outline icon (56px, stroke 4) -->
    <g transform="translate(845, 408)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="20" cy="20" r="14" />
      <line x1="30" y1="30" x2="46" y2="46" />
      <polyline points="14,20 20,20 24,15" stroke-width="3" />
    </g>

    <!-- Title: x in list on large data -->
    <text x="915" y="444" font-family="ui-monospace, monospace" font-size="30" font-weight="bold" fill="#303a36">x in list on large data</text>

    <!-- Linear card -->
    <rect x="840" y="468" width="700" height="46" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="860" y="499" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">linear</text>

    <!-- Recommendation card -->
    <rect x="840" y="522" width="700" height="126" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="860" y="568" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="860" dy="0">use sets or dicts for repeated in checks;</tspan>
      <tspan x="860" dy="36">set and dict lookup O(1) average</tspan>
    </text>
  </g>

  <!-- ======================================================== -->
  <!-- COST TABLE: 6 collection types                           -->
  <!-- ======================================================== -->
  <g id="cost-table">
    <rect x="40" y="680" width="1520" height="280" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Table row 1: list -->
    <line x1="40" y1="726" x2="1560" y2="726" stroke="#c4d9c8" stroke-width="1.5" />
    <text x="65" y="714" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">list: index O(1), append amortised O(1), insert or delete at front O(n), in O(n)</text>

    <!-- Table row 2: tuple -->
    <line x1="40" y1="772" x2="1560" y2="772" stroke="#c4d9c8" stroke-width="1.5" />
    <text x="65" y="760" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">tuple: index O(1), hashable if elements are</text>

    <!-- Table row 3: dict -->
    <line x1="40" y1="818" x2="1560" y2="818" stroke="#c4d9c8" stroke-width="1.5" />
    <text x="65" y="806" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">dict: lookup and insert O(1) average, insertion-ordered since 3.7, keys must be hashable</text>

    <!-- Table row 4: set -->
    <line x1="40" y1="864" x2="1560" y2="864" stroke="#c4d9c8" stroke-width="1.5" />
    <text x="65" y="852" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">set: in O(1) average, empty is set()</text>

    <!-- Table row 5: frozenset -->
    <line x1="40" y1="910" x2="1560" y2="910" stroke="#c4d9c8" stroke-width="1.5" />
    <text x="65" y="898" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">frozenset: immutable set</text>

    <!-- Table row 6: deque -->
    <text x="65" y="944" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">deque: O(1) at both ends</text>
  </g>

  <!-- ======================================================== -->
  <!-- MINI RULE: Hashable keys                                 -->
  <!-- ======================================================== -->
  <g id="mini-rule">
    <rect x="40" y="985" width="1520" height="85" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Lock / shield outline icon (stroke 4) -->
    <g transform="translate(60, 1001)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="20" width="38" height="28" rx="6" />
      <path d="M 12 20 V 12 A 11 11 0 0 1 34 12 V 20" />
      <circle cx="23" cy="32" r="3" fill="#207448" />
    </g>

    <text x="125" y="1024" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="125" dy="0">dict keys must be hashable: strings, numbers, tuples of hashables,</tspan>
      <tspan x="125" dy="28">frozensets; lists and dicts cannot be keys</tspan>
    </text>
  </g>

  <!-- ======================================================== -->
  <!-- BOTTOM TAKEAWAY BAR                                      -->
  <!-- ======================================================== -->
  <g id="bottom-bar">
    <rect x="40" y="1095" width="1520" height="65" rx="14" fill="#207448" />
    <text x="800" y="1136" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="#ffffff">The type you pick sets how fast the script runs and which bugs it carries</text>
  </g>
</svg>'''

svg_code = build_svg()
pathlib.Path("test_collections_v2.svg").write_text(svg_code)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_viewport_size({'width': 1600, 'height': 1200})
    svg_path = pathlib.Path('test_collections_v2.svg').resolve()
    page.goto(f'file://{svg_path}')
    
    data = page.evaluate('''() => {
        const textElements = Array.from(document.querySelectorAll('text')).map(t => {
            const b = t.getBBox();
            return {
                text: t.textContent.replace(/\\s+/g, ' ').trim(),
                x: b.x,
                y: b.y,
                w: b.width,
                h: b.height,
                right: b.x + b.width,
                bottom: b.y + b.height
            };
        });
        const rectElements = Array.from(document.querySelectorAll('rect')).map(r => {
            const b = r.getBBox();
            return {
                x: b.x,
                y: b.y,
                w: b.width,
                h: b.height,
                right: b.x + b.width,
                bottom: b.y + b.height,
                fill: r.getAttribute('fill')
            };
        });
        return { textElements, rectElements };
    }''')
    browser.close()

texts = data['textElements']
rects = data['rectElements']

print("=== Padding Analysis V2 ===")
all_pass = True
for t in texts:
    containers = []
    for r in rects:
        if r['w'] >= 1590 and r['h'] >= 1190:
            continue # background
        if r['x'] <= t['x'] and r['right'] >= t['right'] and r['y'] <= t['y'] and r['bottom'] >= t['bottom']:
            containers.append(r)
    
    containers.sort(key=lambda r: r['w'] * r['h'])
    
    if containers:
        c = containers[0]
        pad_left = t['x'] - c['x']
        pad_right = c['right'] - t['right']
        pad_top = t['y'] - c['y']
        pad_bottom = c['bottom'] - t['bottom']
        min_pad = min(pad_left, pad_right, pad_top, pad_bottom)
        print(f"Text: '{t['text'][:32]}...'")
        print(f"   Paddings: left={pad_left:.1f}, right={pad_right:.1f}, top={pad_top:.1f}, bottom={pad_bottom:.1f} (min={min_pad:.1f})")
        if min_pad < 15.5:
            print(f"   --> FAILED min padding {min_pad:.1f} < 16px!")
            all_pass = False
    else:
        print(f"Text outside explicit rect: '{t['text'][:32]}...' (x={t['x']:.1f}, y={t['y']:.1f})")

if all_pass:
    print("\nSUCCESS: All text elements have >= 16px padding inside their boxes!")
