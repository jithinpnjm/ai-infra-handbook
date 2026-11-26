import os
from playwright.sync_api import sync_playwright

def build_svg():
    H = 1200
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">
  <title>Why a script works in the shell but fails under cron or systemd</title>
  <desc>Technical infographic comparing environment activation in an interactive shell versus cron, systemd, or CI runners, showing the absolute path fix and diagnostic check commands.</desc>

  <!-- Background Canvas -->
  <rect width="1600" height="{H}" fill="#f5f8f5" />

  <!-- Diagram Title (48px bold, two lines) -->
  <text x="800" y="88" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Why a script works in the shell </tspan>
    <tspan x="800" dy="54">but fails under cron or systemd</tspan>
  </text>

  <!-- ==================== LANE 1: YOUR SHELL ==================== -->
  <g id="lane-shell">
    <!-- Lane Container (width=740, height=292, x=40..780, y=184..476) -->
    <rect x="40" y="184" width="740" height="292" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <rect x="40" y="184" width="740" height="58" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />

    <!-- Terminal Outline Icon (56px) -->
    <g transform="translate(62, 185)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="6" width="52" height="40" rx="7" />
      <polyline points="14,19 24,26 14,33" />
      <line x1="28" y1="33" x2="42" y2="33" />
    </g>

    <!-- Lane 1 Header -->
    <text x="135" y="224" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">Your shell</text>

    <!-- Step 1 Card: source .venv/bin/activate ... (h=82, y=248..330) -->
    <rect x="58" y="248" width="704" height="82" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="76" y="293" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">
      <tspan x="76" dy="0">source .venv/bin/activate puts .venv/bin </tspan>
      <tspan x="76" dy="28" font-family="system-ui, -apple-system, sans-serif">at the front of PATH and sets VIRTUAL_ENV</tspan>
    </text>

    <!-- Step 2 Card: python resolves to the venv interpreter (h=60, y=338..398) -->
    <rect x="58" y="338" width="704" height="60" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="76" y="377" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">python resolves to the venv interpreter</text>

    <!-- Step 3 Card: import works (h=60, y=406..466) -->
    <rect x="58" y="406" width="704" height="60" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="76" y="445" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#207448">import works</text>
  </g>

  <!-- ==================== LANE 2: CRON, SYSTEMD OR CI (orange) ==================== -->
  <g id="lane-daemon">
    <!-- Lane Container (width=740, height=292, x=820..1560, y=184..476) -->
    <rect x="820" y="184" width="740" height="292" rx="14" fill="#fff9f3" stroke="#db8129" stroke-width="2.5" />
    <rect x="820" y="184" width="740" height="58" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="2.5" />

    <!-- Timer / Service Cog Outline Icon (56px) in orange -->
    <g transform="translate(842, 185)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="26" r="20" />
      <polyline points="28,14 28,26 37,26" />
    </g>

    <!-- Lane 2 Header -->
    <text x="915" y="224" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#db8129">cron, systemd or CI</text>

    <!-- Step 1 Card: no activation, a different PATH (h=60, y=248..308) -->
    <rect x="838" y="248" width="704" height="60" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="1.5" />
    <text x="856" y="287" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">no activation, a different PATH</text>

    <!-- Step 2 Card: bare python3 resolves to the system interpreter (h=82, y=316..398) -->
    <rect x="838" y="316" width="704" height="82" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="1.5" />
    <text x="856" y="361" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="856" dy="0"><tspan font-family="ui-monospace, monospace">bare python3</tspan> resolves to the </tspan>
      <tspan x="856" dy="28">system interpreter</tspan>
    </text>

    <!-- Step 3 Card: ModuleNotFoundError: No module named x (h=60, y=406..466) -->
    <rect x="838" y="406" width="704" height="60" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="1.5" />
    <text x="856" y="445" font-family="ui-monospace, monospace" font-size="24" fill="#db8129">ModuleNotFoundError: No module named x</text>
  </g>

  <!-- ==================== FIX BOX ==================== -->
  <g id="fix-box">
    <!-- Fix Box Container (width=1520, height=140, x=40..1560, y=516..656) -->
    <rect x="40" y="516" width="1520" height="140" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />

    <!-- Wrench / Tool Outline Icon (56px) -->
    <g transform="translate(62, 558)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 38 8 A 14 14 0 0 0 20 23 L 6 37 A 4 4 0 0 0 10 41 L 15 46 A 4 4 0 0 0 19 42 L 33 28 A 14 14 0 0 0 48 10 Z" />
      <circle cx="37" cy="19" r="2.5" />
    </g>

    <text x="140" y="558" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="140" dy="0">call the interpreter by absolute path: <tspan font-family="ui-monospace, monospace">/path/to/.venv/bin/python -m pip install requests;</tspan> </tspan>
      <tspan x="140" dy="32"><tspan font-family="ui-monospace, monospace">systemd ExecStart=/opt/myops/.venv/bin/myops</tspan> with <tspan font-family="ui-monospace, monospace">Environment=PYTHONUNBUFFERED=1</tspan>, </tspan>
      <tspan x="140" dy="32">a dedicated user and ProtectSystem= hardening from chapter 1.15; log <tspan font-family="ui-monospace, monospace">sys.executable</tspan></tspan>
    </text>
  </g>

  <!-- ==================== CHECKS STRIP ==================== -->
  <g id="checks-strip">
    <!-- Checks Strip Container (width=1520, height=190, x=40..1560, y=696..886) -->
    <rect x="40" y="696" width="1520" height="190" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Search / Magnifying Glass Outline Icon (56px) -->
    <g transform="translate(62, 763)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="22" cy="22" r="16" />
      <line x1="34" y1="34" x2="50" y2="50" />
      <line x1="14" y1="22" x2="30" y2="22" />
    </g>

    <!-- Card 1: which python (x=136..676, y=704..784, w=540, h=80) -->
    <rect x="136" y="704" width="540" height="80" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="156" y="752" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">which python</text>

    <!-- Card 2: python -m pip show x (x=136..676, y=794..874, w=540, h=80) -->
    <rect x="136" y="794" width="540" height="80" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="156" y="842" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">python -m pip show x</text>

    <!-- Card 3: python -c "import sys; print(sys.prefix, sys.base_prefix)" (they differ inside a venv) (x=696..1540, y=704..788, w=844, h=84) -->
    <rect x="696" y="704" width="844" height="84" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="716" y="747" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">
      <tspan x="716" dy="0">python -c "import sys; print(sys.prefix, </tspan>
      <tspan x="716" dy="28">sys.base_prefix)" <tspan font-family="system-ui, -apple-system, sans-serif">(they differ inside a venv)</tspan></tspan>
    </text>

    <!-- Card 4: python -m site shows sys.path, user site and whether a venv is active (x=696..1540, y=794..878, w=844, h=84) -->
    <rect x="696" y="794" width="844" height="84" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="716" y="837" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="716" dy="0"><tspan font-family="ui-monospace, monospace">python -m site</tspan> shows <tspan font-family="ui-monospace, monospace">sys.path</tspan>, user site </tspan>
      <tspan x="716" dy="28">and whether a venv is active</tspan>
    </text>
  </g>

  <!-- ==================== RULES STRIP ==================== -->
  <g id="rules-strip">
    <!-- Rules Strip Container (width=1520, height=140, x=40..1560, y=926..1066) -->
    <rect x="40" y="926" width="1520" height="140" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />

    <!-- Shield Outline Icon (56px) -->
    <g transform="translate(62, 968)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 8 15 L 8 29 C 8 44 28 54 28 54 C 28 54 48 44 48 29 L 48 15 Z" />
      <circle cx="28" cy="27" r="4.5" />
      <line x1="28" y1="31.5" x2="28" y2="39" />
    </g>

    <text x="140" y="968" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="140" dy="0"><tspan font-family="ui-monospace, monospace">python -m pip</tspan>, not bare <tspan font-family="ui-monospace, monospace">pip</tspan>; one environment per project; recreate rather than repair; </tspan>
      <tspan x="140" dy="28">rebuild after upgrading the base Python since a venv borrows its interpreter; </tspan>
      <tspan x="140" dy="28">never sudo pip install: PEP 668 externally-managed-environment, use venv, </tspan>
      <tspan x="140" dy="28">pipx or distribution packages; <tspan font-family="ui-monospace, monospace">--system-site-packages</tspan> weakens isolation</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1102" width="1520" height="58" rx="10" fill="#207448" />
    <text x="800" y="1140" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Activation only changes the shell you are sitting in</text>
  </g>
</svg>"""
    return svg

with open("test_service_python.svg", "w") as f:
    f.write(build_svg())

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f"file://{os.path.abspath('test_service_python.svg')}")
    
    issues = page.evaluate("""() => {
        const issues = [];
        const texts = Array.from(document.querySelectorAll('text'));
        
        texts.forEach((el, idx) => {
            const r = el.getBoundingClientRect();
            const textContent = el.textContent.trim();
            if (r.left < 39.5) {
                issues.push(`Outside margin violation (left < 40): '${textContent.slice(0, 30)}' at left=${r.left.toFixed(1)}`);
            }
            if (r.right > 1560.5) {
                issues.push(`Outside margin violation (right > 1560): '${textContent.slice(0, 30)}' at right=${r.right.toFixed(1)}`);
            }
            if (r.top < 39.5) {
                issues.push(`Outside margin violation (top < 40): '${textContent.slice(0, 30)}' at top=${r.top.toFixed(1)}`);
            }
            if (r.bottom > 1160.5) {
                issues.push(`Outside margin violation (bottom > 1160): '${textContent.slice(0, 30)}' at bottom=${r.bottom.toFixed(1)}`);
            }
        });
        
        const checkCard = (cardSel, textSel, name) => {
            const card = document.querySelector(cardSel);
            const text = document.querySelector(textSel);
            if (!card || !text) return;
            const cr = card.getBoundingClientRect();
            const tr = text.getBoundingClientRect();
            
            const padL = tr.left - cr.left;
            const padR = cr.right - tr.right;
            const padT = tr.top - cr.top;
            const padB = cr.bottom - tr.bottom;
            
            if (padL < 15.5) issues.push(`${name} left padding ${padL.toFixed(1)} < 16`);
            if (padR < 15.5) issues.push(`${name} right padding ${padR.toFixed(1)} < 16`);
            if (padT < 15.5) issues.push(`${name} top padding ${padT.toFixed(1)} < 16`);
            if (padB < 15.5) issues.push(`${name} bottom padding ${padB.toFixed(1)} < 16`);
        };
        
        checkCard('#fix-box rect', '#fix-box text', 'Fix box');
        checkCard('#rules-strip rect', '#rules-strip text', 'Rules strip');
        checkCard('#bottom-bar rect', '#bottom-bar text', 'Bottom bar');
        
        const laneShellCards = Array.from(document.querySelectorAll('#lane-shell rect[width="704"]'));
        const laneShellTexts = Array.from(document.querySelectorAll('#lane-shell text')).filter(t => !t.textContent.includes('Your shell'));
        laneShellTexts.forEach((t, i) => {
            const c = laneShellCards[i];
            const cr = c.getBoundingClientRect();
            const tr = t.getBoundingClientRect();
            const padL = tr.left - cr.left;
            const padR = cr.right - tr.right;
            const padT = tr.top - cr.top;
            const padB = cr.bottom - tr.bottom;
            if (padL < 15.5) issues.push(`Lane Shell Card ${i+1} left padding ${padL.toFixed(1)} < 16`);
            if (padR < 15.5) issues.push(`Lane Shell Card ${i+1} right padding ${padR.toFixed(1)} < 16`);
            if (padT < 15.5) issues.push(`Lane Shell Card ${i+1} top padding ${padT.toFixed(1)} < 16`);
            if (padB < 15.5) issues.push(`Lane Shell Card ${i+1} bottom padding ${padB.toFixed(1)} < 16`);
        });

        const laneDaemonCards = Array.from(document.querySelectorAll('#lane-daemon rect[width="704"]'));
        const laneDaemonTexts = Array.from(document.querySelectorAll('#lane-daemon text')).filter(t => !t.textContent.includes('cron, systemd or CI'));
        laneDaemonTexts.forEach((t, i) => {
            const c = laneDaemonCards[i];
            const cr = c.getBoundingClientRect();
            const tr = t.getBoundingClientRect();
            const padL = tr.left - cr.left;
            const padR = cr.right - tr.right;
            const padT = tr.top - cr.top;
            const padB = cr.bottom - tr.bottom;
            if (padL < 15.5) issues.push(`Lane Daemon Card ${i+1} left padding ${padL.toFixed(1)} < 16`);
            if (padR < 15.5) issues.push(`Lane Daemon Card ${i+1} right padding ${padR.toFixed(1)} < 16`);
            if (padT < 15.5) issues.push(`Lane Daemon Card ${i+1} top padding ${padT.toFixed(1)} < 16`);
            if (padB < 15.5) issues.push(`Lane Daemon Card ${i+1} bottom padding ${padB.toFixed(1)} < 16`);
        });

        const checksCards = Array.from(document.querySelectorAll('#checks-strip rect[width="540"], #checks-strip rect[width="844"]'));
        const checksTexts = Array.from(document.querySelectorAll('#checks-strip text'));
        checksTexts.forEach((t, i) => {
            const c = checksCards[i];
            const cr = c.getBoundingClientRect();
            const tr = t.getBoundingClientRect();
            const padL = tr.left - cr.left;
            const padR = cr.right - tr.right;
            const padT = tr.top - cr.top;
            const padB = cr.bottom - tr.bottom;
            if (padL < 15.5) issues.push(`Checks Card ${i+1} left padding ${padL.toFixed(1)} < 16`);
            if (padR < 15.5) issues.push(`Checks Card ${i+1} right padding ${padR.toFixed(1)} < 16`);
            if (padT < 15.5) issues.push(`Checks Card ${i+1} top padding ${padT.toFixed(1)} < 16`);
            if (padB < 15.5) issues.push(`Checks Card ${i+1} bottom padding ${padB.toFixed(1)} < 16`);
        });

        return issues;
    }""")
    
    print(f"Browser Audit Issues ({len(issues)}):")
    for iss in issues:
        print("  -", iss)
    if not issues:
        print("[PASS] ZERO browser layout issues!")
    browser.close()
