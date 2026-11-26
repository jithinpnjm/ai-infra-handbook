import os
import re
from playwright.sync_api import sync_playwright

def test_config(title_y1, title_y2, host_y, host_h,
                hdr_y, hdr_h,
                l1_y, l1_h, l1_tspan_ys,
                l2_y, l2_h, l2_tspan_ys,
                l3_y, l3_h, l3_tspan_ys,
                ftr_y, ftr_h, ftr_tspan_ys,
                bar_y, bar_h, bar_text_y):
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Three paths from a container: to a neighbour, to the Internet, and from outside to a published port</title>
  <desc>Technical infographic illustrating the three container networking paths: c1 to c2 over a bridge, c1 to the Internet with NAT masquerading, and inbound traffic to a published port with DNAT.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129"/>
    </marker>
    <filter id="shadow" x="-2%" y="-4%" width="104%" height="108%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.05"/>
    </filter>
  </defs>

  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <text id="title-1" x="800" y="{title_y1}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Three paths from a container: to a neighbour,</text>
  <text id="title-2" x="800" y="{title_y2}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">to the Internet, and to a published port</text>

  <!-- HOST -->
  <rect id="box-host" x="40" y="{host_y}" width="1520" height="{host_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" stroke-dasharray="10 8" filter="url(#shadow)"/>

  <!-- HOST HEADER -->
  <rect id="box-host-header" x="56" y="{hdr_y}" width="1488" height="{hdr_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>

  <g transform="translate(70, {hdr_y + 9})">
    <g stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="6" width="52" height="18" rx="3"/>
      <rect x="2" y="30" width="52" height="18" rx="3"/>
      <circle cx="12" cy="15" r="2" fill="#207448"/>
      <circle cx="20" cy="15" r="2" fill="#207448"/>
      <circle cx="12" cy="39" r="2" fill="#207448"/>
      <circle cx="20" cy="39" r="2" fill="#207448"/>
      <line x1="36" y1="15" x2="48" y2="15"/>
      <line x1="36" y1="39" x2="48" y2="39"/>
    </g>
    <rect x="66" y="6" width="82" height="44" rx="6" fill="#207448"/>
    <text x="107" y="37" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">host</text>
  </g>

  <g transform="translate(246, {hdr_y + 8})">
    <rect x="0" y="0" width="290" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <g transform="translate(10, 6)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="40" height="42" rx="4"/>
      <line x1="2" y1="14" x2="42" y2="14"/>
      <circle cx="9" cy="8" r="2" fill="#207448"/>
      <circle cx="17" cy="8" r="2" fill="#207448"/>
    </g>
    <text x="68" y="38" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">c1 (10.10.0.11)</text>
  </g>

  <g transform="translate(552, {hdr_y + 8})">
    <rect x="0" y="0" width="314" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <g transform="translate(10, 6)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="8" width="40" height="30" rx="4"/>
      <line x1="12" y1="18" x2="12" y2="28"/>
      <line x1="22" y1="18" x2="22" y2="28"/>
      <line x1="32" y1="18" x2="32" y2="28"/>
    </g>
    <text x="68" y="38" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">br0 (10.10.0.1/24)</text>
  </g>

  <g transform="translate(882, {hdr_y + 8})">
    <rect x="0" y="0" width="290" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <g transform="translate(10, 6)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="40" height="42" rx="4"/>
      <line x1="2" y1="14" x2="42" y2="14"/>
      <circle cx="9" cy="8" r="2" fill="#207448"/>
      <circle cx="17" cy="8" r="2" fill="#207448"/>
    </g>
    <text x="68" y="38" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">c2 (10.10.0.12)</text>
  </g>

  <g transform="translate(1188, {hdr_y + 8})">
    <rect x="0" y="0" width="340" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <g transform="translate(12, 6)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="40" height="34" rx="3"/>
      <line x1="8" y1="38" x2="8" y2="44"/>
      <line x1="16" y1="38" x2="16" y2="44"/>
      <line x1="24" y1="38" x2="24" y2="44"/>
      <line x1="32" y1="38" x2="32" y2="44"/>
      <circle cx="12" cy="16" r="3" fill="#207448"/>
    </g>
    <text x="70" y="38" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">uplink NIC</text>
  </g>

  <!-- LANE 1 -->
  <g id="lane-1">
    <rect id="box-lane-1" x="56" y="{l1_y}" width="1488" height="{l1_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <circle cx="96" cy="{l1_y + 36}" r="24" fill="#207448"/>
    <text x="96" y="{l1_y + 45}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <g transform="translate(136, {l1_y + 8})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="14" cy="28" r="8"/>
      <circle cx="42" cy="28" r="8"/>
      <path d="M 22 28 L 34 28"/>
    </g>
    <text id="l1-title" x="208" y="{l1_y + 46}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">c1 to c2 on the same bridge</text>
    <line x1="680" y1="{l1_y + 36}" x2="1520" y2="{l1_y + 36}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>
    <text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="84" y="{l1_tspan_ys[0]}">c1's own stack routes the packet because both share a subnet, ARP finds c2,</tspan>
      <tspan x="84" y="{l1_tspan_ys[1]}">the packet leaves c1's eth0 (veth peer), enters the host-side veth, the bridge learns</tspan>
      <tspan x="84" y="{l1_tspan_ys[2]}">the MAC and forwards the frame to c2's veth and eth0</tspan>
      <tspan x="84" y="{l1_tspan_ys[3]}">br_netfilter and net.bridge.bridge-nf-call-iptables=1 let iptables see bridged traffic;</tspan>
      <tspan x="84" y="{l1_tspan_ys[4]}">Kubernetes requires it so kube-proxy rules apply</tspan>
    </text>
  </g>

  <!-- LANE 2 -->
  <g id="lane-2">
    <rect id="box-lane-2" x="56" y="{l2_y}" width="1488" height="{l2_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <circle cx="96" cy="{l2_y + 36}" r="24" fill="#207448"/>
    <text x="96" y="{l2_y + 45}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <g transform="translate(136, {l2_y + 8})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <ellipse cx="28" cy="28" rx="10" ry="22"/>
      <line x1="6" y1="28" x2="50" y2="28"/>
    </g>
    <text id="l2-title" x="208" y="{l2_y + 46}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">c1 to the Internet</text>
    <line x1="530" y1="{l2_y + 36}" x2="1520" y2="{l2_y + 36}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>
    <text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="84" y="{l2_tspan_ys[0]}">default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack,</tspan>
      <tspan x="84" y="{l2_tspan_ys[1]}">passes FORWARD then POSTROUTING masquerade, leaves through the NIC with the host's</tspan>
      <tspan x="84" y="{l2_tspan_ys[2]}">address; return traffic is un-NATed by conntrack and delivered back through the bridge;</tspan>
      <tspan x="84" y="{l2_tspan_ys[3]}">the outside world only talks to the host</tspan>
    </text>
    <text font-family="ui-monospace, monospace" font-size="24" fill="#303a36">
      <tspan x="84" y="{l2_tspan_ys[4]}">sysctl -w net.ipv4.ip_forward=1</tspan>
      <tspan x="620" y="{l2_tspan_ys[4]}">iptables -I FORWARD -i br0 -j ACCEPT</tspan>
      <tspan x="84" y="{l2_tspan_ys[5]}">iptables -t nat -A POSTROUTING -s 10.10.0.0/24 ! -o br0 -j MASQUERADE</tspan>
      <tspan x="84" y="{l2_tspan_ys[6]}">iptables -I FORWARD -o br0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT</tspan>
    </text>
  </g>

  <!-- LANE 3 -->
  <g id="lane-3">
    <rect id="box-lane-3" x="56" y="{l3_y}" width="1488" height="{l3_h}" rx="10" fill="#fdf8f3" stroke="#db8129" stroke-width="2.5"/>
    <circle cx="96" cy="{l3_y + 36}" r="24" fill="#db8129"/>
    <text x="96" y="{l3_y + 45}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <g transform="translate(136, {l3_y + 8})" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="4"/>
      <path d="M 18 28 L 38 28"/>
      <polyline points="26,20 18,28 26,36"/>
    </g>
    <text id="l3-title" x="208" y="{l3_y + 46}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#db8129">host:8080 to c1:80</text>
    <line x1="1520" y1="{l3_y + 36}" x2="520" y2="{l3_y + 36}" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)"/>
    <text font-family="ui-monospace, monospace" font-size="24" fill="#303a36">
      <tspan x="84" y="{l3_tspan_ys[0]}">iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.10.0.11:80</tspan>
      <tspan x="84" y="{l3_tspan_ys[1]}">iptables -t nat -A OUTPUT -p tcp -d 127.0.0.1 --dport 8080 -j DNAT ... for local clients</tspan>
    </text>
  </g>

  <!-- FOOTER -->
  <g id="footer-notes">
    <rect id="box-footer" x="40" y="{ftr_y}" width="1520" height="{ftr_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" filter="url(#shadow)"/>
    <text font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448" x="64" y="{ftr_tspan_ys[0]}">DNS inside: mkdir /etc/netns/c1 and write nameserver 1.1.1.1 to /etc/netns/c1/resolv.conf</text>
    <line x1="64" y1="{ftr_tspan_ys[0] + 16}" x2="1536" y2="{ftr_tspan_ys[0] + 16}" stroke="#207448" stroke-width="1.5" stroke-opacity="0.3"/>
    <text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="64" y="{ftr_tspan_ys[1]}">almost literally what the default bridge network does: docker0, a veth per container,</tspan>
      <tspan x="64" y="{ftr_tspan_ys[2]}">an IPAM address from a private pool, a default route via the bridge, masquerade,</tspan>
      <tspan x="64" y="{ftr_tspan_ys[3]}">DNAT for published ports, a bind-mounted /etc/resolv.conf</tspan>
    </text>
  </g>

  <!-- TAKEAWAY BAR -->
  <g id="bottom-bar">
    <rect id="box-takeaway" x="40" y="{bar_y}" width="1520" height="{bar_h}" rx="8" fill="#207448" filter="url(#shadow)"/>
    <text x="800" y="{bar_text_y}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">A container is only a namespace plus a cable</text>
  </g>
</svg>"""
    return svg

# Let's find working parameters!
# Title:
title_y1 = 86
title_y2 = 140
host_y = 158

# Header:
hdr_y = 170
hdr_h = 76

# Lane 1:
l1_y = 258
l1_h = 222
l1_tspan_ys = [338, 366, 394, 422, 450]

# Lane 2:
l2_y = 492
l2_h = 280
l2_tspan_ys = [572, 598, 624, 650, 680, 708, 736]

# Lane 3:
l3_y = 784
l3_h = 138
l3_tspan_ys = [862, 892]

host_h = 776 # host ends at 158 + 776 = 934

# Footer:
ftr_y = 946
ftr_h = 144
ftr_tspan_ys = [985, 1025, 1049, 1073]
ftr_h = 148

# Takeaway bar:
bar_y = 1098
bar_h = 60
bar_text_y = 1137

svg_code = test_config(title_y1, title_y2, host_y, host_h,
                       hdr_y, hdr_h,
                       l1_y, l1_h, l1_tspan_ys,
                       l2_y, l2_h, l2_tspan_ys,
                       l3_y, l3_h, l3_tspan_ys,
                       ftr_y, ftr_h, ftr_tspan_ys,
                       bar_y, bar_h, bar_text_y)

with open("test_opt.svg", "w") as f:
    f.write(svg_code)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f"file://{os.path.abspath('test_opt.svg')}")
    
    issues = page.evaluate("""() => {
        const issues = [];
        
        // Canvas bounds check
        const texts = Array.from(document.querySelectorAll('text, tspan'));
        texts.forEach(el => {
            const r = el.getBoundingClientRect();
            const txt = el.textContent.trim();
            if (!txt) return;
            if (r.left < 39.5) issues.push(`Left margin violation: '${txt.slice(0,25)}' left=${r.left.toFixed(1)}`);
            if (r.right > 1560.5) issues.push(`Right margin violation: '${txt.slice(0,25)}' right=${r.right.toFixed(1)}`);
            if (r.top < 39.5) issues.push(`Top margin violation: '${txt.slice(0,25)}' top=${r.top.toFixed(1)}`);
            if (r.bottom > 1160.5) issues.push(`Bottom margin violation: '${txt.slice(0,25)}' bottom=${r.bottom.toFixed(1)}`);
        });

        // Rect paddings
        const checks = [
            { rect: '#box-lane-1', text: '#lane-1 text', name: 'Lane 1' },
            { rect: '#box-lane-2', text: '#lane-2 text', name: 'Lane 2' },
            { rect: '#box-lane-3', text: '#lane-3 text', name: 'Lane 3' },
            { rect: '#box-footer', text: '#footer-notes text', name: 'Footer' },
            { rect: '#box-takeaway', text: '#bottom-bar text', name: 'Takeaway' }
        ];

        checks.forEach(c => {
            const rEl = document.querySelector(c.rect);
            const tEls = Array.from(document.querySelectorAll(c.text));
            if (!rEl) return;
            const rb = rEl.getBoundingClientRect();
            tEls.forEach(t => {
                const tb = t.getBoundingClientRect();
                const pl = tb.left - rb.left;
                const pr = rb.right - tb.right;
                const pt = tb.top - rb.top;
                const pb = rb.bottom - tb.bottom;
                if (pl < 15.5) issues.push(`${c.name} left pad violation: ${pl.toFixed(1)} < 16 for '${t.textContent.slice(0,20)}'`);
                if (pr < 15.5) issues.push(`${c.name} right pad violation: ${pr.toFixed(1)} < 16 for '${t.textContent.slice(0,20)}'`);
                if (pt < 15.5) issues.push(`${c.name} top pad violation: ${pt.toFixed(1)} < 16 for '${t.textContent.slice(0,20)}'`);
                if (pb < 15.5) issues.push(`${c.name} bottom pad violation: ${pb.toFixed(1)} < 16 for '${t.textContent.slice(0,20)}'`);
            });
        });

        return issues;
    }""")
    
    print("Optimization results:")
    for iss in issues:
        print(" -", iss)
    print(f"Total issues: {len(issues)}")
