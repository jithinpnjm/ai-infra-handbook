#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys

def build_svg():
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    lines.append('  <title>Link up is not link healthy: which counter points at which suspect</title>')
    lines.append('  <desc>Diagnostic mapping between network counters, commands, and physical or configuration suspects</desc>')
    lines.append('  <defs>')
    lines.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    lines.append('    </marker>')
    lines.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    lines.append('    </marker>')
    lines.append('  </defs>')
    lines.append('')
    lines.append('  <!-- Canvas Background -->')
    lines.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    lines.append('')
    lines.append('  <!-- Title: 48px bold -->')
    lines.append('  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    lines.append('    <tspan x="800" dy="0">Link up is not link healthy: </tspan>')
    lines.append('    <tspan x="800" dy="54">which counter points at which suspect</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Left Strip Container
    lines.append('  <!-- ==================== LEFT STRIP: COMMANDS ==================== -->')
    lines.append('  <rect x="40" y="137" width="430" height="832" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('')

    # Command 1
    # 'ip -s link show eth0; cat /sys/class/net/eth0/carrier_changes'
    lines.append('  <!-- Command 1 -->')
    lines.append('  <rect x="55" y="153" width="400" height="120" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <text x="73" y="194" font-family="monospace" font-size="24" fill="#303a36"><tspan x="73" dy="0">ip -s link show eth0; </tspan><tspan x="73" dy="28">cat /sys/class/net/</tspan><tspan x="73" dy="28">eth0/carrier_changes</tspan></text>')
    lines.append('')

    # Command 2
    # 'ethtool -S eth0 | egrep crc|fcs|err|drop|pause|pfc'
    lines.append('  <!-- Command 2 -->')
    lines.append('  <rect x="55" y="289" width="400" height="120" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <text x="73" y="330" font-family="monospace" font-size="24" fill="#303a36"><tspan x="73" dy="0">ethtool -S eth0 | </tspan><tspan x="73" dy="28">egrep crc|fcs|err|</tspan><tspan x="73" dy="28">drop|pause|pfc</tspan></text>')
    lines.append('')

    # Command 3
    # 'ethtool --show-fec eth0'
    lines.append('  <!-- Command 3 -->')
    lines.append('  <rect x="55" y="425" width="400" height="120" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <text x="73" y="493" font-family="monospace" font-size="24" fill="#303a36">ethtool --show-fec eth0</text>')
    lines.append('')

    # Command 4
    # 'ethtool -m eth0 (DOM: temperature, Tx/Rx optical power)'
    lines.append('  <!-- Command 4 -->')
    lines.append('  <rect x="55" y="561" width="400" height="120" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <text x="73" y="602" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="73" dy="0">ethtool -m eth0 </tspan>')
    lines.append('    <tspan x="73" dy="28">(DOM: temperature, </tspan>')
    lines.append('    <tspan x="73" dy="28">Tx/Rx optical power)</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Command 5
    # 'dmesg -T | egrep -i link'
    lines.append('  <!-- Command 5 -->')
    lines.append('  <rect x="55" y="697" width="400" height="120" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <text x="73" y="765" font-family="monospace" font-size="24" fill="#303a36">dmesg -T | egrep -i link</text>')
    lines.append('')

    # Command 6
    # 'lldpcli show neighbors (which switch and port is at the far end)'
    lines.append('  <!-- Command 6 -->')
    lines.append('  <rect x="55" y="833" width="400" height="120" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <text x="73" y="874" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="73" dy="0">lldpcli show neighbors </tspan>')
    lines.append('    <tspan x="73" dy="28">(which switch and port </tspan>')
    lines.append('    <tspan x="73" dy="28">is at the far end)</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Column 1 (Counters) and Column 2 (Suspects)
    # Rows:
    # y = [140, 310, 480, 650, 820], height = 146
    # col1: x = 500, width = 450
    # col2: x = 1010, width = 550
    # arrow: line from (950, y+73) to (1010, y+73)

    # ROW 1
    lines.append('  <!-- ==================== ROW 1 ==================== -->')
    # Counter 1: 'rising carrier_changes'
    lines.append('  <rect x="500" y="140" width="450" height="146" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('  <g transform="translate(518, 188)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <path d="M 4 25 L 14 25 L 20 8 L 30 42 L 36 25 L 46 25" />')
    lines.append('  </g>')
    lines.append('  <text x="584" y="200" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="584" dy="0">rising </tspan>')
    lines.append('    <tspan x="584" dy="36">carrier_changes</tspan>')
    lines.append('  </text>')
    # Arrow 1
    lines.append('  <line x1="950" y1="213" x2="1010" y2="213" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')
    # Suspect 1: 'link flapping: cable, optic, transceiver seating, switch port, power'
    lines.append('  <rect x="1010" y="140" width="550" height="146" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('  <g transform="translate(1028, 188)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="12" y="10" width="26" height="20" rx="3" />')
    lines.append('    <path d="M 18 10 L 18 4 L 32 4 L 32 10" />')
    lines.append('    <line x1="25" y1="30" x2="25" y2="44" />')
    lines.append('    <line x1="18" y1="30" x2="18" y2="38" />')
    lines.append('    <line x1="32" y1="30" x2="32" y2="38" />')
    lines.append('  </g>')
    lines.append('  <text x="1094" y="186" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="1094" dy="0">link flapping: cable, optic, </tspan>')
    lines.append('    <tspan x="1094" dy="30">transceiver seating, </tspan>')
    lines.append('    <tspan x="1094" dy="30">switch port, power</tspan>')
    lines.append('  </text>')
    lines.append('')

    # ROW 2
    lines.append('  <!-- ==================== ROW 2 ==================== -->')
    # Counter 2: 'non-zero rx_crc_errors or uncorrected FEC'
    lines.append('  <rect x="500" y="310" width="450" height="146" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('  <g transform="translate(518, 358)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <path d="M 8 10 L 25 4 L 42 10 C 42 30 25 44 25 44 C 25 44 8 30 8 10 Z" />')
    lines.append('    <line x1="25" y1="14" x2="25" y2="26" />')
    lines.append('    <circle cx="25" cy="33" r="2.5" fill="#207448" />')
    lines.append('  </g>')
    lines.append('  <text x="584" y="358" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="584" dy="0">non-zero </tspan>')
    lines.append('    <tspan x="584" dy="34">rx_crc_errors or </tspan>')
    lines.append('    <tspan x="584" dy="34">uncorrected FEC</tspan>')
    lines.append('  </text>')
    # Arrow 2
    lines.append('  <line x1="950" y1="383" x2="1010" y2="383" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')
    # Suspect 2: 'marginal signal: dirty or failing optic, bad DAC, bent fibre'
    lines.append('  <rect x="1010" y="310" width="550" height="146" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('  <g transform="translate(1028, 358)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <path d="M 6 12 C 28 12 22 38 44 38" />')
    lines.append('    <circle cx="25" cy="25" r="7" stroke-dasharray="3,3" />')
    lines.append('  </g>')
    lines.append('  <text x="1094" y="356" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="1094" dy="0">marginal signal: dirty or </tspan>')
    lines.append('    <tspan x="1094" dy="30">failing optic, bad DAC, </tspan>')
    lines.append('    <tspan x="1094" dy="30">bent fibre</tspan>')
    lines.append('  </text>')
    lines.append('')

    # ROW 3
    lines.append('  <!-- ==================== ROW 3 ==================== -->')
    # Counter 3: 'rx_discards and rx_out_of_buffer'
    lines.append('  <rect x="500" y="480" width="450" height="146" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('  <g transform="translate(518, 528)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="6" y="14" width="38" height="26" rx="4" />')
    lines.append('    <line x1="16" y1="14" x2="16" y2="40" />')
    lines.append('    <line x1="26" y1="14" x2="26" y2="40" />')
    lines.append('    <line x1="36" y1="14" x2="36" y2="40" />')
    lines.append('  </g>')
    lines.append('  <text x="584" y="540" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="584" dy="0">rx_discards and </tspan>')
    lines.append('    <tspan x="584" dy="36">rx_out_of_buffer</tspan>')
    lines.append('  </text>')
    # Arrow 3
    lines.append('  <line x1="950" y1="553" x2="1010" y2="553" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')
    # Suspect 3: 'host cannot drain traffic fast enough, or switch or NIC buffers overflow'
    lines.append('  <rect x="1010" y="480" width="550" height="146" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('  <g transform="translate(1028, 528)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="12" y="12" width="26" height="26" rx="4" />')
    lines.append('    <rect x="19" y="19" width="12" height="12" rx="2" fill="#207448" />')
    lines.append('    <line x1="18" y1="6" x2="18" y2="12" /><line x1="25" y1="6" x2="25" y2="12" /><line x1="32" y1="6" x2="32" y2="12" />')
    lines.append('    <line x1="18" y1="38" x2="18" y2="44" /><line x1="25" y1="38" x2="25" y2="44" /><line x1="32" y1="38" x2="32" y2="44" />')
    lines.append('    <line x1="6" y1="18" x2="12" y2="18" /><line x1="6" y1="25" x2="12" y2="25" /><line x1="6" y1="32" x2="12" y2="32" />')
    lines.append('    <line x1="38" y1="18" x2="44" y2="18" /><line x1="38" y1="25" x2="44" y2="25" /><line x1="38" y1="32" x2="44" y2="32" />')
    lines.append('  </g>')
    lines.append('  <text x="1094" y="526" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="1094" dy="0">host cannot drain traffic </tspan>')
    lines.append('    <tspan x="1094" dy="30">fast enough, or switch or </tspan>')
    lines.append('    <tspan x="1094" dy="30">NIC buffers overflow</tspan>')
    lines.append('  </text>')
    lines.append('')

    # ROW 4
    lines.append('  <!-- ==================== ROW 4 ==================== -->')
    # Counter 4: 'rx_pause and tx_pause'
    lines.append('  <rect x="500" y="650" width="450" height="146" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('  <g transform="translate(518, 698)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <circle cx="25" cy="25" r="20" />')
    lines.append('    <line x1="20" y1="16" x2="20" y2="34" />')
    lines.append('    <line x1="30" y1="16" x2="30" y2="34" />')
    lines.append('  </g>')
    lines.append('  <text x="584" y="710" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="584" dy="0">rx_pause and </tspan>')
    lines.append('    <tspan x="584" dy="36">tx_pause</tspan>')
    lines.append('  </text>')
    # Arrow 4
    lines.append('  <line x1="950" y1="723" x2="1010" y2="723" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')
    # Suspect 4: 'flow control is active'
    lines.append('  <rect x="1010" y="650" width="550" height="146" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('  <g transform="translate(1028, 698)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <line x1="6" y1="25" x2="44" y2="25" />')
    lines.append('    <polygon points="12,17 22,25 12,33" fill="#207448" />')
    lines.append('    <polygon points="38,17 28,25 38,33" fill="#207448" />')
    lines.append('  </g>')
    lines.append('  <text x="1094" y="732" font-family="sans-serif" font-size="24" fill="#303a36">flow control is active</text>')
    lines.append('')

    # ROW 5 (Orange highlight!)
    lines.append('  <!-- ==================== ROW 5: ORANGE HIGHLIGHT ==================== -->')
    # Counter 5: 'NIC at the wrong speed, a 400G NIC at 100G'
    lines.append('  <rect x="500" y="820" width="450" height="146" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2.5" />')
    lines.append('  <g transform="translate(518, 868)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <path d="M 8 36 A 20 20 0 1 1 42 36" />')
    lines.append('    <line x1="25" y1="25" x2="15" y2="17" />')
    lines.append('    <circle cx="25" cy="25" r="3.5" fill="#db8129" />')
    lines.append('  </g>')
    lines.append('  <text x="584" y="868" font-family="sans-serif" font-size="30" font-weight="bold" fill="#db8129">')
    lines.append('    <tspan x="584" dy="0">NIC at the wrong </tspan>')
    lines.append('    <tspan x="584" dy="34">speed, a 400G NIC </tspan>')
    lines.append('    <tspan x="584" dy="34">at 100G</tspan>')
    lines.append('  </text>')
    # Arrow 5 (Orange!)
    lines.append('  <line x1="950" y1="893" x2="1010" y2="893" stroke="#db8129" stroke-width="3" marker-end="url(#arrow-orange)" />')
    # Suspect 5: 'cable, optic, lane problem, or switch configuration'
    lines.append('  <rect x="1010" y="820" width="550" height="146" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2.5" />')
    lines.append('  <g transform="translate(1028, 868)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="8" y="14" width="34" height="22" rx="3" />')
    lines.append('    <circle cx="16" cy="25" r="2.5" fill="#db8129" />')
    lines.append('    <circle cx="25" cy="25" r="2.5" fill="#db8129" />')
    lines.append('    <circle cx="34" cy="25" r="2.5" fill="#db8129" />')
    lines.append('    <line x1="12" y1="8" x2="38" y2="8" stroke-dasharray="4,3" />')
    lines.append('  </g>')
    lines.append('  <text x="1094" y="882" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="1094" dy="0">cable, optic, lane problem, </tspan>')
    lines.append('    <tspan x="1094" dy="32">or switch configuration</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Footer note
    # 'At 25G and above FEC corrects many errors before the CRC sees them; a frame with a bad FCS is dropped silently and not retransmitted at this layer'
    lines.append('  <!-- ==================== FOOTER NOTE ==================== -->')
    lines.append('  <rect x="40" y="1000" width="1520" height="102" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('  <text x="800" y="1042" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="800" dy="0">At 25G and above FEC corrects many errors before the CRC sees them; </tspan>')
    lines.append('    <tspan x="800" dy="34">a frame with a bad FCS is dropped silently and not retransmitted at this layer</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Bottom bar (Takeaway bar)
    # 'A link can be up and still be losing bits'
    lines.append('  <!-- ==================== BOTTOM BAR ==================== -->')
    lines.append('  <rect x="40" y="1115" width="1520" height="70" rx="10" fill="#207448" />')
    lines.append('  <text x="800" y="1160" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">A link can be up and still be losing bits</text>')
    lines.append('</svg>')

    return '\n'.join(lines)

if __name__ == '__main__':
    svg_content = build_svg()
    with open('planning/image_tools/generated_link_health.svg', 'w') as f:
        f.write(svg_content)
    print("SVG generated successfully at planning/image_tools/generated_link_health.svg")
