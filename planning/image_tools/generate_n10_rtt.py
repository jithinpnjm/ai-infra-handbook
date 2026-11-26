import re
import xml.etree.ElementTree as ET

def generate_perfect_svg():
    width = 1600
    height = 900
    
    # Palette
    bg = "#f5f8f5"
    text_color = "#303a36"
    main_green = "#207448"
    panel_bg = "#e8f1ea"
    card_bg = "#ffffff"
    orange = "#db8129"
    orange_tint = "#fdf5ee"
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    svg.append('  <title>Round trips: TCP plus TLS</title>')
    svg.append('  <desc>Round trips: TCP plus TLS</desc>')
    svg.append('  <defs>')
    svg.append(f'    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" orient="auto">')
    svg.append(f'      <path d="M 2 3 L 16 9 L 2 15 Z" fill="{orange}"/>')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="{width}" height="{height}" fill="{bg}"/>')
    
    # Title (48px bold)
    svg.append(f'  <text x="800" y="66" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="{text_color}">Round trips: TCP plus TLS</text>')
    
    # =========================================================================
    # TOP BAR: TCP + TLS 1.2 (y=115 to 300, h=185)
    # =========================================================================
    svg.append('  <!-- Top bar container: TCP + TLS 1.2 -->')
    svg.append(f'  <rect x="40" y="115" width="1520" height="185" rx="14" fill="{panel_bg}" stroke="{main_green}" stroke-width="2"/>')
    
    # Label panel on the left (x=60, y=135, w=330, h=145)
    svg.append(f'  <rect x="60" y="135" width="330" height="145" rx="10" fill="{card_bg}" stroke="{main_green}" stroke-width="2"/>')
    # Icon: Lock / Shield outline 56x56 at (75, 180)
    svg.append(f'  <g transform="translate(75, 178)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="18" width="44" height="34" rx="6"/>')
    svg.append('    <path d="M 14 18 V 10 A 12 12 0 0 1 38 10 V 18"/>')
    svg.append('    <circle cx="26" cy="35" r="4" fill="#207448"/>')
    svg.append('  </g>')
    # Label: TCP + TLS 1.2 (32px bold)
    svg.append(f'  <text x="142" y="220" font-family="sans-serif" font-size="32" font-weight="bold" fill="{main_green}">TCP + TLS 1.2</text>')
    
    # Blocks for Top Bar:
    # Block 1: TCP 1 RTT (x=410, w=360, h=145)
    svg.append(f'  <rect x="410" y="135" width="360" height="145" rx="10" fill="{card_bg}" stroke="{main_green}" stroke-width="2"/>')
    svg.append(f'  <g transform="translate(426, 178)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="14" cy="28" r="10"/>')
    svg.append('    <circle cx="42" cy="28" r="10"/>')
    svg.append('    <line x1="24" y1="28" x2="32" y2="28"/>')
    svg.append('  </g>')
    svg.append(f'  <text x="496" y="220" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">TCP 1 RTT</text>')
    
    # Block 2: TLS 2 RTT (x=790, w=750, h=145)
    svg.append(f'  <rect x="790" y="135" width="750" height="145" rx="10" fill="{card_bg}" stroke="{main_green}" stroke-width="2"/>')
    svg.append(f'  <g transform="translate(812, 178)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="28" cy="28" r="22"/>')
    svg.append('    <polyline points="28,14 28,28 38,28"/>')
    svg.append('  </g>')
    svg.append(f'  <text x="886" y="220" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">TLS 2 RTT</text>')
    
    # =========================================================================
    # BOTTOM BAR: TCP + TLS 1.3 (y=330 to 515, h=185)
    # =========================================================================
    svg.append('  <!-- Bottom bar container: TCP + TLS 1.3 -->')
    svg.append(f'  <rect x="40" y="330" width="1520" height="185" rx="14" fill="{panel_bg}" stroke="{main_green}" stroke-width="2"/>')
    
    # Label panel on the left (x=60, y=350, w=330, h=145)
    svg.append(f'  <rect x="60" y="350" width="330" height="145" rx="10" fill="{card_bg}" stroke="{main_green}" stroke-width="2"/>')
    # Icon: Shield with check outline 56x56 at (75, 395)
    svg.append(f'  <g transform="translate(75, 393)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M 26 4 L 46 12 V 26 C 46 40 26 48 26 48 C 26 48 6 40 6 26 V 12 Z"/>')
    svg.append('    <path d="M 16 26 L 23 33 L 36 18"/>')
    svg.append('  </g>')
    # Label: TCP + TLS 1.3 (32px bold)
    svg.append(f'  <text x="142" y="435" font-family="sans-serif" font-size="32" font-weight="bold" fill="{main_green}">TCP + TLS 1.3</text>')
    
    # Block 1: TCP 1 RTT (x=410, w=360, h=145)
    svg.append(f'  <rect x="410" y="350" width="360" height="145" rx="10" fill="{card_bg}" stroke="{main_green}" stroke-width="2"/>')
    svg.append(f'  <g transform="translate(426, 393)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="14" cy="28" r="10"/>')
    svg.append('    <circle cx="42" cy="28" r="10"/>')
    svg.append('    <line x1="24" y1="28" x2="32" y2="28"/>')
    svg.append('  </g>')
    svg.append(f'  <text x="496" y="435" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">TCP 1 RTT</text>')
    
    # Block 2: TLS 1 RTT (x=790, w=360, h=145) - green, shorter!
    svg.append(f'  <rect x="790" y="350" width="360" height="145" rx="10" fill="{card_bg}" stroke="{main_green}" stroke-width="2"/>')
    svg.append(f'  <g transform="translate(812, 393)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="28" cy="28" r="22"/>')
    svg.append('    <polyline points="28,14 28,28 38,28"/>')
    svg.append('  </g>')
    svg.append(f'  <text x="886" y="435" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">TLS 1 RTT</text>')
    
    # Saved round trip area: x=1170 to 1540 (w=370, h=145)
    svg.append(f'  <rect x="1170" y="350" width="370" height="145" rx="10" fill="{orange_tint}" stroke="{orange}" stroke-width="2" stroke-dasharray="8 6"/>')
    # Orange arrow showing the saved round trip
    svg.append(f'  <line x1="1200" y1="422" x2="1510" y2="422" stroke="{orange}" stroke-width="5" stroke-linecap="round" marker-end="url(#arrow-orange)"/>')
    
    # =========================================================================
    # SIDE NOTE: TLS 1.3 client sends its key share in the first message (y=545 to 685, h=140)
    # =========================================================================
    svg.append('  <!-- Side note -->')
    svg.append(f'  <rect x="40" y="545" width="1520" height="140" rx="14" fill="{card_bg}" stroke="{main_green}" stroke-width="2"/>')
    # Key / message icon 56x56 at (65, 587)
    svg.append(f'  <g transform="translate(65, 587)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="18" cy="28" r="12"/>')
    svg.append('    <line x1="30" y1="28" x2="52" y2="28"/>')
    svg.append('    <line x1="42" y1="28" x2="42" y2="38"/>')
    svg.append('    <line x1="48" y1="28" x2="48" y2="35"/>')
    svg.append('  </g>')
    # Side note text: 'TLS 1.3 client sends its key share in the first message' (26px)
    svg.append(f'  <text x="145" y="627" font-family="sans-serif" font-size="26" font-weight="bold" fill="{text_color}">TLS 1.3 client sends its key share in the first message</text>')
    
    # =========================================================================
    # FOOTER: Session tickets or PSKs let a returning client skip the full handshake (y=715 to 855, h=140)
    # =========================================================================
    svg.append('  <!-- Footer takeaway bar -->')
    svg.append(f'  <rect x="40" y="715" width="1520" height="140" rx="14" fill="{main_green}"/>')
    # Ticket / pass icon at (65, 757)
    svg.append('  <g transform="translate(65, 757)" stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="10" width="48" height="36" rx="6"/>')
    svg.append('    <line x1="16" y1="10" x2="16" y2="46" stroke-dasharray="4 4"/>')
    svg.append('    <circle cx="34" cy="28" r="6"/>')
    svg.append('  </g>')
    # Footer text: 'Session tickets or PSKs let a returning client skip the full handshake' (26px bold white)
    svg.append(f'  <text x="145" y="797" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Session tickets or PSKs let a returning client skip the full handshake</text>')
    
    svg.append('</svg>')
    return "\n".join(svg)

if __name__ == "__main__":
    content = generate_perfect_svg()
    with open("test_n10_rtt.svg", "w") as f:
        f.write(content)
    with open("/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook/docs/part-02-networking/img/n10-rtt.svg", "w") as f:
        f.write(content)
    print("Generated and written to docs/part-02-networking/img/n10-rtt.svg")
