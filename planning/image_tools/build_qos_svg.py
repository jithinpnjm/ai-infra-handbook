#!/usr/bin/env python3
import re
import xml.etree.ElementTree as ET

def build_svg():
    width = 1600
    height = 1200
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    svg.append('  <title>How the three QoS classes are derived and what they change</title>')
    svg.append('  <desc>Visual explanation of how Kubernetes derives Guaranteed, Burstable, and BestEffort QoS classes from container resource requests and limits, and what they change including OOM scores, cgroups, and eviction behavior.</desc>')
    
    # Background
    svg.append(f'  <rect width="{width}" height="{height}" fill="#f5f8f5"/>')
    
    # 1. Title (48px bold, wrapped on 2 lines with >= 40px top margin)
    svg.append('  <text text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" y="88">How the three QoS classes are derived</tspan>')
    svg.append('    <tspan x="800" y="142">and what they change</tspan>')
    svg.append('  </text>')
    
    # 2. Header note (x=50, y=175, w=1500, h=100)
    # Label: "QoS is derived by the API server, never set by a field; check with kubectl get pod -o jsonpath={.status.qosClass}"
    svg.append('  <g id="header-note">')
    svg.append('    <rect x="50" y="175" width="1500" height="100" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Terminal / info icon
    svg.append('    <g transform="translate(75, 197)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="48" height="42" rx="6"/>')
    svg.append('      <line x1="4" y1="18" x2="52" y2="18" stroke-width="3"/>')
    svg.append('      <polyline points="14,28 22,35 14,42" stroke-width="3"/>')
    svg.append('      <line x1="26" y1="42" x2="38" y2="42" stroke-width="3"/>')
    svg.append('    </g>')
    # Header note text (pad_t: 217 - 24 - 175 = 18px, pad_b: 275 - 251 = 24px)
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="145" y="217">QoS is derived by the API server, never set by a field; check with </tspan>')
    svg.append('      <tspan x="145" y="251" font-family="monospace">kubectl get pod -o jsonpath={.status.qosClass}</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ================= THREE COLUMNS =================
    # Columns layout:
    # Col 1: x = 50,  w = 470
    # Col 2: x = 565, w = 470
    # Col 3: x = 1080, w = 470
    # Column cards: y = 315, h = 715 (ends at y = 1030)
    
    # Row vertical alignments:
    # Column Title & Icon: y = 330 to 430
    # Row 1 (Rule): y = 445, h = 130 (ends 575)
    # Row 2 (oom_score_adj): y = 595, h = 95 (ends 690)
    # Row 3 (cgroup): y = 710, h = 95 (ends 805)
    # Row 4 (Behavior / Eviction): y = 825, h = 185 (ends 1010)
    
    # ----- COLUMN 1: Guaranteed -----
    # Single orange highlight #db8129 on Guaranteed card outline!
    svg.append('  <g id="col-guaranteed">')
    svg.append('    <rect x="50" y="315" width="470" height="715" rx="16" fill="#e8f1ea" stroke="#db8129" stroke-width="3"/>')
    
    # Shield icon (about 56px, stroke 4)
    svg.append('    <g transform="translate(110, 341)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M28 6 L50 14 V28 C50 42 28 52 28 52 C28 52 6 42 6 28 V14 Z"/>')
    svg.append('      <polyline points="18,28 25,35 38,20"/>')
    svg.append('    </g>')
    # Column 1 Title: Guaranteed (32px bold)
    svg.append('    <text x="185" y="380" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Guaranteed</text>')
    
    # Col 1 Item 1: Rule (x=75, y=445, w=420, h=130)
    # "every container sets CPU and memory requests equal to limits"
    # pad_t: 485 - 24 - 445 = 16px, pad_b: 575 - 549 = 26px
    svg.append('    <rect x="75" y="445" width="420" height="130" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="95" y="485">every container sets CPU</tspan>')
    svg.append('      <tspan x="95" y="517">and memory requests</tspan>')
    svg.append('      <tspan x="95" y="549">equal to limits</tspan>')
    svg.append('    </text>')
    
    # Col 1 Item 2: oom_score_adj (x=75, y=595, w=420, h=95)
    # "oom_score_adj -997"
    # pad_t: 653 - 24 - 595 = 34px, pad_b: 690 - 653 = 37px
    svg.append('    <rect x="75" y="595" width="420" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="285" y="653" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">oom_score_adj -997</text>')
    
    # Col 1 Item 3: cgroup (x=75, y=710, w=420, h=95)
    # "cgroup kubepods.slice/guaranteed"
    # pad_t: 750 - 24 - 710 = 16px, pad_b: 805 - 784 = 21px
    svg.append('    <rect x="75" y="710" width="420" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="95" y="750">cgroup</tspan>')
    svg.append('      <tspan x="95" y="784">kubepods.slice/guaranteed</tspan>')
    svg.append('    </text>')
    
    # Col 1 Item 4: Effect / behavior (x=75, y=825, w=420, h=185)
    # "evicted last; required for CPU Manager static policy exclusive cores and Topology Manager alignment"
    # pad_t: 865 - 24 - 825 = 16px, pad_b: 1010 - 985 = 25px
    svg.append('    <rect x="75" y="825" width="420" height="185" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="95" y="865">evicted last; required</tspan>')
    svg.append('      <tspan x="95" y="895">for CPU Manager static</tspan>')
    svg.append('      <tspan x="95" y="925">policy exclusive cores</tspan>')
    svg.append('      <tspan x="95" y="955">and Topology Manager</tspan>')
    svg.append('      <tspan x="95" y="985">alignment</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ----- COLUMN 2: Burstable -----
    svg.append('  <g id="col-burstable">')
    svg.append('    <rect x="565" y="315" width="470" height="715" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    
    # Sliders / scale icon (about 56px, stroke 4)
    svg.append('    <g transform="translate(635, 341)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <line x1="8" y1="16" x2="48" y2="16"/>')
    svg.append('      <circle cx="22" cy="16" r="6" fill="#e8f1ea"/>')
    svg.append('      <line x1="8" y1="32" x2="48" y2="32"/>')
    svg.append('      <circle cx="36" cy="32" r="6" fill="#e8f1ea"/>')
    svg.append('      <line x1="8" y1="48" x2="48" y2="48"/>')
    svg.append('      <circle cx="18" cy="48" r="6" fill="#e8f1ea"/>')
    svg.append('    </g>')
    # Column 2 Title: Burstable (32px bold)
    svg.append('    <text x="710" y="380" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Burstable</text>')
    
    # Col 2 Item 1: Rule (x=590, y=445, w=420, h=130)
    # "some requests or limits set, but not Guaranteed rules"
    # pad_t: 485 - 24 - 445 = 16px, pad_b: 575 - 549 = 26px
    svg.append('    <rect x="590" y="445" width="420" height="130" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="610" y="485">some requests or</tspan>')
    svg.append('      <tspan x="610" y="517">limits set, but not</tspan>')
    svg.append('      <tspan x="610" y="549">Guaranteed rules</tspan>')
    svg.append('    </text>')
    
    # Col 2 Item 2: oom_score_adj (x=590, y=595, w=420, h=95)
    # "oom_score_adj scaled between 2 and 999"
    # pad_t: 637 - 24 - 595 = 18px, pad_b: 690 - 671 = 19px
    svg.append('    <rect x="590" y="595" width="420" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="610" y="637" font-family="monospace">oom_score_adj</tspan>')
    svg.append('      <tspan x="610" y="671">scaled between 2 and 999</tspan>')
    svg.append('    </text>')
    
    # Col 2 Item 3: cgroup (x=590, y=710, w=420, h=95)
    # "cgroup kubepods.slice/burstable"
    # pad_t: 750 - 24 - 710 = 16px, pad_b: 805 - 784 = 21px
    svg.append('    <rect x="590" y="710" width="420" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="610" y="750">cgroup</tspan>')
    svg.append('      <tspan x="610" y="784">kubepods.slice/burstable</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ----- COLUMN 3: BestEffort -----
    svg.append('  <g id="col-besteffort">')
    svg.append('    <rect x="1080" y="315" width="470" height="715" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    
    # Dashed circle icon (about 56px, stroke 4)
    svg.append('    <g transform="translate(1135, 341)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="22" stroke-dasharray="6 6"/>')
    svg.append('      <line x1="28" y1="16" x2="28" y2="28"/>')
    svg.append('      <circle cx="28" cy="38" r="2.5" fill="#207448"/>')
    svg.append('    </g>')
    # Column 3 Title: BestEffort (32px bold)
    svg.append('    <text x="1210" y="380" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">BestEffort</text>')
    
    # Col 3 Item 1: Rule (x=1105, y=445, w=420, h=130)
    # "no requests or limits at all"
    # pad_t: 501 - 24 - 445 = 32px, pad_b: 575 - 535 = 40px
    svg.append('    <rect x="1105" y="445" width="420" height="130" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1125" y="501">no requests or</tspan>')
    svg.append('      <tspan x="1125" y="535">limits at all</tspan>')
    svg.append('    </text>')
    
    # Col 3 Item 2: oom_score_adj (x=1105, y=595, w=420, h=95)
    # "oom_score_adj 1000"
    # pad_t: 653 - 24 - 595 = 34px, pad_b: 690 - 653 = 37px
    svg.append('    <rect x="1105" y="595" width="420" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="1315" y="653" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">oom_score_adj 1000</text>')
    
    # Col 3 Item 3: cgroup (x=1105, y=710, w=420, h=95)
    # "cgroup kubepods.slice/besteffort"
    # pad_t: 750 - 24 - 710 = 16px, pad_b: 805 - 784 = 21px
    svg.append('    <rect x="1105" y="710" width="420" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1125" y="750">cgroup</tspan>')
    svg.append('      <tspan x="1125" y="784">kubepods.slice/besteffort</tspan>')
    svg.append('    </text>')
    
    # Col 3 Item 4: Effect / behavior (x=1105, y=825, w=420, h=185)
    # "first to be killed or evicted under pressure"
    # pad_t: 905 - 24 - 825 = 56px, pad_b: 1010 - 939 = 71px
    svg.append('    <rect x="1105" y="825" width="420" height="185" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1125" y="905">first to be killed or</tspan>')
    svg.append('      <tspan x="1125" y="939">evicted under pressure</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ================= FOOTER =================
    # Footer: x = 50, y = 1070, w = 1500, h = 90
    # Label: "GPU extended resources must be whole integers and requests equal limits (no overcommit); setting only limits defaults requests to the same value"
    # pad_t: 1106 - 24 - 1070 = 12px -> let's make h = 100, y = 1060!
    # With y = 1060, h = 100: pad_t = 1102 - 24 - 1060 = 18px, pad_b = 1160 - 1136 = 24px!
    svg.append('  <g id="footer-bar">')
    svg.append('    <rect x="50" y="1060" width="1500" height="100" rx="14" fill="#207448"/>')
    # Chip / GPU icon inside footer
    svg.append('    <g transform="translate(75, 1082)" fill="none" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="10" y="10" width="36" height="36" rx="5"/>')
    svg.append('      <rect x="18" y="18" width="20" height="20" rx="3" fill="#207448"/>')
    svg.append('      <line x1="18" y1="4" x2="18" y2="10"/>')
    svg.append('      <line x1="28" y1="4" x2="28" y2="10"/>')
    svg.append('      <line x1="38" y1="4" x2="38" y2="10"/>')
    svg.append('      <line x1="18" y1="46" x2="18" y2="52"/>')
    svg.append('      <line x1="28" y1="46" x2="28" y2="52"/>')
    svg.append('      <line x1="38" y1="46" x2="38" y2="52"/>')
    svg.append('      <line x1="4" y1="18" x2="10" y2="18"/>')
    svg.append('      <line x1="4" y1="28" x2="10" y2="28"/>')
    svg.append('      <line x1="4" y1="38" x2="10" y2="38"/>')
    svg.append('      <line x1="46" y1="18" x2="52" y2="18"/>')
    svg.append('      <line x1="46" y1="28" x2="52" y2="28"/>')
    svg.append('      <line x1="46" y1="38" x2="52" y2="38"/>')
    svg.append('    </g>')
    # Footer text
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#ffffff">')
    svg.append('      <tspan x="145" y="1102">GPU extended resources must be whole integers and requests equal limits (no overcommit);</tspan>')
    svg.append('      <tspan x="145" y="1136">setting only limits defaults requests to the same value</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == '__main__':
    content = build_svg()
    with open('candidate_qos.svg', 'w') as f:
        f.write(content)
    print("Generated candidate_qos.svg successfully.")
