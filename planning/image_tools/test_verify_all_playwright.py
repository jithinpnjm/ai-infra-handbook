import re
import asyncio
from playwright.async_api import async_playwright
import pathlib
import xml.etree.ElementTree as ET

# Generate the candidate SVG
svg_text = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>The Kubernetes Service path: seven checks in order</title>
  <desc>A vertical ladder of seven numbered rungs from top to bottom showing diagnostic checks for a failing Kubernetes Service.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background Canvas -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="85" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">When a Service fails, confirm in order</text>

  <!-- Down the left side a thin arrow labelled read top to bottom -->
  <line x1="50" y1="136" x2="50" y2="1065" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
  <text x="68" y="580" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="68" dy="0">read</tspan>
    <tspan x="68" dy="28">top to</tspan>
    <tspan x="68" dy="28">bottom</tspan>
  </text>

  <!-- ==================== RUNG 1: Pod ==================== -->
  <g id="rung-1">
    <rect x="175" y="136" width="975" height="94" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 1 -->
    <circle cx="215" cy="183" r="24" fill="#207448" />
    <text x="215" y="191" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
    <!-- Pod Outline Icon (56x56) -->
    <g transform="translate(250, 155)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="28,6 50,18 50,42 28,54 6,42 6,18" />
      <line x1="28" y1="6" x2="28" y2="30" />
      <line x1="6" y1="18" x2="28" y2="30" />
      <line x1="50" y1="18" x2="28" y2="30" />
      <line x1="28" y1="30" x2="28" y2="54" />
    </g>
    <!-- Text -->
    <text x="325" y="178" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Pod</text>
    <text x="325" y="208" font-family="monospace" font-size="24" fill="#303a36">call the pod IP and pod port directly from another pod</text>
  </g>

  <!-- ==================== RIGHT SIDE: Small Box Note ==================== -->
  <g id="small-box">
    <rect x="1190" y="136" width="370" height="94" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1215" y="176" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1215" dy="0">the first failing rung</tspan>
      <tspan x="1215" dy="28">is where to look</tspan>
    </text>
  </g>

  <!-- ==================== RUNG 2: Service ==================== -->
  <g id="rung-2">
    <rect x="175" y="270" width="1385" height="94" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 2 -->
    <circle cx="215" cy="317" r="24" fill="#207448" />
    <text x="215" y="325" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
    <!-- Service Gear Outline Icon (56x56) -->
    <g transform="translate(250, 289)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="12" />
      <path d="M 28 6 L 28 12 M 28 44 L 28 50 M 6 28 L 12 28 M 44 28 L 50 28 M 12 12 L 17 17 M 39 39 L 44 44 M 12 44 L 17 39 M 39 17 L 44 12" stroke-width="4" />
    </g>
    <!-- Text -->
    <text x="325" y="312" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Service</text>
    <text x="325" y="342" font-family="monospace" font-size="24" fill="#303a36">the Service exists, otherwise lookup fails with Name or service not known</text>
  </g>

  <!-- ==================== RUNG 3: DNS ==================== -->
  <g id="rung-3">
    <rect x="175" y="404" width="1385" height="94" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 3 -->
    <circle cx="215" cy="451" r="24" fill="#207448" />
    <text x="215" y="459" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
    <!-- DNS Globe Outline Icon (56x56) -->
    <g transform="translate(250, 423)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <ellipse cx="28" cy="28" rx="10" ry="22" />
      <line x1="6" y1="28" x2="50" y2="28" />
    </g>
    <!-- Text -->
    <text x="325" y="446" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">DNS</text>
    <text x="325" y="476" font-family="monospace" font-size="24" fill="#303a36">short, namespaced and full names resolve</text>
  </g>

  <!-- ==================== RUNG 4: Endpoints ==================== -->
  <g id="rung-4">
    <rect x="175" y="538" width="765" height="122" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 4 -->
    <circle cx="215" cy="599" r="24" fill="#207448" />
    <text x="215" y="607" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
    <!-- Endpoints Nodes Outline Icon (56x56) -->
    <g transform="translate(250, 571)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="16" r="6" />
      <circle cx="40" cy="16" r="6" />
      <circle cx="28" cy="42" r="6" />
      <line x1="16" y1="16" x2="28" y2="42" />
      <line x1="40" y1="16" x2="28" y2="42" />
      <line x1="16" y1="16" x2="40" y2="16" />
    </g>
    <!-- Text -->
    <text x="325" y="580" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Endpoints</text>
    <text x="325" y="610" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="325" dy="0">kubectl get endpointslices</tspan>
      <tspan x="325" dy="28">-l kubernetes.io/service-name=hostnames</tspan>
    </text>
  </g>

  <!-- ==================== ORANGE CALLOUT BESIDE RUNG 4 ==================== -->
  <!-- Single most important item highlighted in orange #db8129 -->
  <g id="orange-callout">
    <rect x="980" y="538" width="580" height="122" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3" />
    <text x="1010" y="580" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1010" dy="0" font-weight="bold" fill="#db8129">ENDPOINTS shows none means</tspan>
      <tspan x="1010" dy="28">the Service selector does not</tspan>
      <tspan x="1010" dy="28">match pod labels</tspan>
    </text>
  </g>

  <!-- ==================== RUNG 5: Ports ==================== -->
  <g id="rung-5">
    <rect x="175" y="701" width="1385" height="94" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 5 -->
    <circle cx="215" cy="748" r="24" fill="#207448" />
    <text x="215" y="756" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>
    <!-- Ports Plug Outline Icon (56x56) -->
    <g transform="translate(250, 720)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="36" height="36" rx="6" />
      <path d="M 18 10 L 18 24 L 24 24 L 24 38 L 32 38 L 32 24 L 38 24 L 38 10" />
    </g>
    <!-- Text -->
    <text x="325" y="743" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Ports</text>
    <text x="325" y="773" font-family="monospace" font-size="24" fill="#303a36">Service port listed, targetPort correct, named port matched</text>
  </g>

  <!-- ==================== RUNG 6: kube-proxy rules ==================== -->
  <g id="rung-6">
    <rect x="175" y="836" width="1385" height="94" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 6 -->
    <circle cx="215" cy="883" r="24" fill="#207448" />
    <text x="215" y="891" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">6</text>
    <!-- Shield / Rules Outline Icon (56x56) -->
    <g transform="translate(250, 855)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 L 48 28 C 48 40 28 50 28 50 C 28 50 8 40 8 28 L 8 14 Z" />
      <line x1="18" y1="26" x2="38" y2="26" />
      <line x1="28" y1="18" x2="28" y2="36" />
    </g>
    <!-- Text -->
    <text x="325" y="878" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">kube-proxy rules</text>
    <text x="325" y="908" font-family="monospace" font-size="24" fill="#303a36">iptables-save grep hostnames, or ipvsadm -ln</text>
  </g>

  <!-- ==================== RUNG 7: Conntrack ==================== -->
  <g id="rung-7">
    <rect x="175" y="971" width="1385" height="94" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 7 -->
    <circle cx="215" cy="1018" r="24" fill="#207448" />
    <text x="215" y="1026" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">7</text>
    <!-- Conntrack Table Outline Icon (56x56) -->
    <g transform="translate(250, 990)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="6" />
      <line x1="8" y1="20" x2="48" y2="20" />
      <line x1="8" y1="32" x2="48" y2="32" />
      <circle cx="15" cy="14" r="2" fill="#207448" />
      <circle cx="15" cy="26" r="2" fill="#207448" />
      <circle cx="15" cy="38" r="2" fill="#207448" />
    </g>
    <!-- Text -->
    <text x="325" y="1013" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Conntrack</text>
    <text x="325" y="1043" font-family="monospace" font-size="24" fill="#303a36">table usage, since iptables Service load balancing depends on connection tracking</text>
  </g>

  <!-- ==================== TAKEAWAY BAR ==================== -->
  <rect x="40" y="1105" width="1520" height="55" rx="12" fill="#207448" />
  <text x="800" y="1141" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Pod, Service, DNS, endpoints, ports, kube-proxy rules, then conntrack</text>
</svg>'''

with open("perfect_service_path.svg", "w") as f:
    f.write(svg_text)

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        await page.goto(f'file://{pathlib.Path("perfect_service_path.svg").resolve()}')
        
        # 1. Check all text bounding boxes inside canvas with 40px margin
        texts = await page.query_selector_all('text')
        print(f"Total text elements: {len(texts)}")
        for i, t in enumerate(texts, 1):
            box = await t.bounding_box()
            content = ' '.join((await t.text_content()).split())
            print(f"{i:2d}. x={box['x']:6.1f}, y={box['y']:6.1f}, w={box['width']:6.1f}, h={box['height']:6.1f} | '{content[:38]}'")
            assert box['x'] >= 40.0, f"Left overflow: {box['x']} < 40"
            assert box['x'] + box['width'] <= 1560.0, f"Right overflow: {box['x'] + box['width']} > 1560"
            assert box['y'] >= 40.0, f"Top overflow: {box['y']} < 40"
            assert box['y'] + box['height'] <= 1160.0, f"Bottom overflow: {box['y'] + box['height']} > 1160"
            
        print("\nAll text elements within canvas margins >= 40px!")
        
        # 2. Check each card's rendered text paddings
        checks = [
            ("Rung 1", "#rung-1", 2, 3),
            ("Rung 2", "#rung-2", 2, 3),
            ("Rung 3", "#rung-3", 2, 3),
            ("Rung 4", "#rung-4", 2, 3),
            ("Rung 5", "#rung-5", 2, 3),
            ("Rung 6", "#rung-6", 2, 3),
            ("Rung 7", "#rung-7", 2, 3),
        ]
        
        for name, sel, t_idx, c_idx in checks:
            r_box = await (await page.query_selector(f"{sel} rect")).bounding_box()
            t_box = await (await page.query_selector(f"{sel} text:nth-of-type({t_idx})")).bounding_box()
            c_box = await (await page.query_selector(f"{sel} text:nth-of-type({c_idx})")).bounding_box()
            
            pad_l = min(t_box['x'], c_box['x']) - r_box['x']
            pad_r = (r_box['x'] + r_box['width']) - max(t_box['x'] + t_box['width'], c_box['x'] + c_box['width'])
            pad_t = t_box['y'] - r_box['y']
            pad_b = (r_box['y'] + r_box['height']) - (c_box['y'] + c_box['height'])
            
            print(f"{name:8s} | pad_l={pad_l:5.1f}, pad_r={pad_r:5.1f}, pad_t={pad_t:5.1f}, pad_b={pad_b:5.1f}")
            assert min(pad_l, pad_r, pad_t, pad_b) >= 16.0, f"{name} failed padding >= 16.0!"

        # Small Box:
        sb_r = await (await page.query_selector("#small-box rect")).bounding_box()
        sb_t = await (await page.query_selector("#small-box text")).bounding_box()
        pad_sb_l = sb_t['x'] - sb_r['x']
        pad_sb_r = (sb_r['x'] + sb_r['width']) - (sb_t['x'] + sb_t['width'])
        pad_sb_t = sb_t['y'] - sb_r['y']
        pad_sb_b = (sb_r['y'] + sb_r['height']) - (sb_t['y'] + sb_t['height'])
        print(f"Small Box | pad_l={pad_sb_l:5.1f}, pad_r={pad_sb_r:5.1f}, pad_t={pad_sb_t:5.1f}, pad_b={pad_sb_b:5.1f}")
        assert min(pad_sb_l, pad_sb_r, pad_sb_t, pad_sb_b) >= 16.0

        # Orange Callout:
        oc_r = await (await page.query_selector("#orange-callout rect")).bounding_box()
        oc_t = await (await page.query_selector("#orange-callout text")).bounding_box()
        pad_oc_l = oc_t['x'] - oc_r['x']
        pad_oc_r = (oc_r['x'] + oc_r['width']) - (oc_t['x'] + oc_t['width'])
        pad_oc_t = oc_t['y'] - oc_r['y']
        pad_oc_b = (oc_r['y'] + oc_r['height']) - (oc_t['y'] + oc_t['height'])
        print(f"Callout   | pad_l={pad_oc_l:5.1f}, pad_r={pad_oc_r:5.1f}, pad_t={pad_oc_t:5.1f}, pad_b={pad_oc_b:5.1f}")
        assert min(pad_oc_l, pad_oc_r, pad_oc_t, pad_oc_b) >= 16.0

        await browser.close()
        print("\nALL PLAYWRIGHT AUDITS PASSED PERFECTLY!")

asyncio.run(check())
