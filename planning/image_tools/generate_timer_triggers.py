import xml.etree.ElementTree as ET
import re

def build_svg():
    H = 1100
    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{H}" viewBox="0 0 1600 {H}">')
    lines.append('  <title>Timer triggers: calendar time versus time since an event</title>')
    lines.append('  <desc>An infographic comparing systemd calendar timers with OnCalendar syntax against monotonic timers counted from events such as boot or last activation, along with key options Persistent, RandomizedDelaySec, and AccuracySec.</desc>')
    
    # Background
    lines.append(f'  <rect x="0" y="0" width="1600" height="{H}" fill="#f5f8f5"/>')
    
    # Title (Label 1)
    lines.append('  <!-- Title -->')
    lines.append('  <text x="800" y="68" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="800" dy="0">Timer triggers: calendar time </tspan>')
    lines.append('    <tspan x="800" dy="54">versus time since an event</tspan>')
    lines.append('  </text>')

    # ==========================================
    # LEFT PANEL: Realtime (calendar): OnCalendar=
    # x=40, y=165, w=740, h=495
    # ==========================================
    lines.append('  <!-- Left Panel -->')
    lines.append('  <rect x="40" y="165" width="740" height="495" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    
    # Left Panel Icon (Calendar/Clock)
    lines.append('  <!-- Calendar Icon -->')
    lines.append('  <g transform="translate(65, 182)" stroke="#207448" stroke-width="3" fill="none">')
    lines.append('    <rect x="0" y="6" width="46" height="40" rx="6"/>')
    lines.append('    <line x1="12" y1="0" x2="12" y2="8"/>')
    lines.append('    <line x1="34" y1="0" x2="34" y2="8"/>')
    lines.append('    <line x1="0" y1="18" x2="46" y2="18"/>')
    lines.append('    <circle cx="15" cy="28" r="2.5" fill="#207448"/>')
    lines.append('    <circle cx="23" cy="28" r="2.5" fill="#207448"/>')
    lines.append('    <circle cx="31" cy="28" r="2.5" fill="#207448"/>')
    lines.append('  </g>')

    # Left Panel Title (Label 2)
    lines.append('  <text x="125" y="218" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Realtime (calendar): OnCalendar=</text>')

    # Sub-card 1: Chapter line & 3 parts (x=60, y=242, w=700, h=132)
    lines.append('  <rect x="60" y="242" width="700" height="132" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    
    # Chapter line (Label 3)
    lines.append('  <text x="80" y="274" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">OnCalendar=Sun *-*-* 03:00:00</text>')

    # Labelled parts: DayOfWeek (Label 4)
    lines.append('  <rect x="80" y="288" width="180" height="36" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="170" y="314" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">DayOfWeek</text>')

    # Labelled parts: Year-Month-Day (Label 5)
    lines.append('  <rect x="275" y="288" width="250" height="36" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="400" y="314" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">Year-Month-Day</text>')

    # Labelled parts: Hour:Minute:Second (Label 6)
    lines.append('  <rect x="80" y="330" width="310" height="36" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="235" y="356" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">Hour:Minute:Second</text>')

    # Syntax chips
    # Row 1: * wildcard (Label 7)
    lines.append('  <rect x="60" y="386" width="180" height="38" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="150" y="413" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">* wildcard</text>')

    # Row 1: Mon,Fri list (Label 8)
    lines.append('  <rect x="255" y="386" width="220" height="38" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="365" y="413" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">Mon,Fri list</text>')

    # Row 1: Mon..Fri range (Label 9)
    lines.append('  <rect x="490" y="386" width="250" height="38" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="615" y="413" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">Mon..Fri range</text>')

    # Row 2: *:0/15 every 15 minutes (Label 10)
    lines.append('  <rect x="60" y="434" width="380" height="38" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="250" y="461" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">*:0/15 every 15 minutes</text>')

    # Row 3: hourly daily weekly monthly yearly (Label 11)
    lines.append('  <rect x="60" y="482" width="540" height="38" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="330" y="509" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">hourly daily weekly monthly yearly</text>')

    # Test line box (x=60, y=530, w=700, h=118) (Label 12)
    lines.append('  <rect x="60" y="530" width="700" height="118" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="80" y="562" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="80" dy="0">systemd-analyze calendar "Mon..Fri 02:30" </tspan>')
    lines.append('    <tspan x="80" dy="32">prints the normalised form and next elapse </tspan>')
    lines.append('    <tspan x="80" dy="32">times; --iterations=5 shows more</tspan>')
    lines.append('  </text>')

    # ==========================================
    # RIGHT PANEL: Monotonic: counts from an event
    # x=820, y=165, w=740, h=495
    # ==========================================
    lines.append('  <!-- Right Panel -->')
    lines.append('  <rect x="820" y="165" width="740" height="495" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    
    # Right Panel Icon (Stopwatch/Timer)
    lines.append('  <!-- Stopwatch Icon -->')
    lines.append('  <g transform="translate(845, 180)" stroke="#207448" stroke-width="3" fill="none">')
    lines.append('    <circle cx="23" cy="27" r="20"/>')
    lines.append('    <line x1="23" y1="2" x2="23" y2="7"/>')
    lines.append('    <line x1="17" y1="2" x2="29" y2="2"/>')
    lines.append('    <line x1="23" y1="27" x2="23" y2="15"/>')
    lines.append('    <line x1="23" y1="27" x2="31" y2="27"/>')
    lines.append('  </g>')

    # Right Panel Title (Label 13)
    lines.append('  <text x="905" y="218" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Monotonic: counts from an event</text>')

    # Timeline card (x=840, y=242, w=700, h=276)
    lines.append('  <rect x="840" y="242" width="700" height="276" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    
    # Timeline Axis Line & tick marks (no arrow marker)
    lines.append('  <!-- Timeline Axis Line -->')
    lines.append('  <line x1="870" y1="335" x2="1510" y2="335" stroke="#207448" stroke-width="3"/>')
    lines.append('  <line x1="915" y1="320" x2="915" y2="350" stroke="#207448" stroke-width="3"/>')
    lines.append('  <circle cx="915" cy="335" r="7" fill="#207448"/>')
    lines.append('  <line x1="1100" y1="320" x2="1100" y2="350" stroke="#207448" stroke-width="3"/>')
    lines.append('  <circle cx="1100" cy="335" r="7" fill="#207448"/>')
    lines.append('  <line x1="1330" y1="320" x2="1330" y2="350" stroke="#207448" stroke-width="3"/>')
    lines.append('  <circle cx="1330" cy="335" r="7" fill="#207448"/>')
    lines.append('  <line x1="1480" y1="320" x2="1480" y2="350" stroke="#207448" stroke-width="3" stroke-dasharray="4 4"/>')

    # Event 1: boot (Label 14)
    lines.append('  <rect x="860" y="262" width="110" height="40" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="915" y="290" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">boot</text>')

    # Interval 1: OnBootSec= (Label 15)
    lines.append('  <rect x="915" y="360" width="180" height="42" rx="6" fill="#f5f8f5" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="1005" y="390" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">OnBootSec=</text>')

    # Event 2: unit last activated (Label 16)
    lines.append('  <rect x="970" y="262" width="310" height="40" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="1125" y="290" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">unit last activated</text>')

    # Interval 2: OnUnitActiveSec= (Label 17)
    lines.append('  <rect x="1115" y="360" width="270" height="42" rx="6" fill="#f5f8f5" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="1250" y="390" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">OnUnitActiveSec=</text>')

    # Repeating interval label: every N minutes since the last run (Label 18)
    lines.append('  <rect x="930" y="445" width="520" height="44" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="1190" y="475" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">every N minutes since the last run</text>')

    # Other keys listed (Label 19)
    # x=840, y=530, w=700, h=118
    lines.append('  <rect x="840" y="530" width="700" height="118" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append('  <text x="865" y="578" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="865" dy="0">OnStartupSec=, OnUnitInactiveSec=, </tspan>')
    lines.append('    <tspan x="865" dy="34">OnActiveSec=</tspan>')
    lines.append('  </text>')

    # ==========================================
    # BOTTOM ROW OF THREE OPTION CARDS
    # y = 680, h = 165
    # Card 1: x = 40, w = 490 (Orange highlight)
    # Card 2: x = 555, w = 490
    # Card 3: x = 1070, w = 490
    # ==========================================
    lines.append('  <!-- Three Option Cards -->')
    
    # Card 1 (Orange): Persistent=true (Label 20)
    lines.append('  <rect x="40" y="680" width="490" height="165" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2.5"/>')
    # Storage Icon inside Card 1
    lines.append('  <g transform="translate(60, 696)" stroke="#207448" stroke-width="2.5" fill="none">')
    lines.append('    <ellipse cx="16" cy="8" rx="14" ry="5"/>')
    lines.append('    <path d="M 2 8 v 12 c 0 3 6 5 14 5 s 14 -2 14 -5 v -12"/>')
    lines.append('    <path d="M 2 14 c 0 3 6 5 14 5 s 14 -2 14 -5"/>')
    lines.append('  </g>')
    lines.append('  <text x="60" y="750" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="60" dy="0">Persistent=true: remembers </tspan>')
    lines.append('    <tspan x="60" dy="32">the last run on disk and </tspan>')
    lines.append('    <tspan x="60" dy="32">runs a missed job at next start</tspan>')
    lines.append('  </text>')

    # Card 2: RandomizedDelaySec= (Label 21)
    lines.append('  <rect x="555" y="680" width="490" height="165" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Shuffle / Spread icon inside Card 2
    lines.append('  <g transform="translate(575, 696)" stroke="#207448" stroke-width="2.5" fill="none">')
    lines.append('    <path d="M 4 8 h 8 l 12 14 h 8"/>')
    lines.append('    <path d="M 4 22 h 8 l 4 -4.5"/>')
    lines.append('    <path d="M 24 10.5 l 4 -2.5 h 4"/>')
    lines.append('  </g>')
    lines.append('  <text x="575" y="765" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="575" dy="0">RandomizedDelaySec=: </tspan>')
    lines.append('    <tspan x="575" dy="34">spreads load across machines</tspan>')
    lines.append('  </text>')

    # Card 3: AccuracySec= (Label 22)
    lines.append('  <rect x="1070" y="680" width="490" height="165" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Target / Precision icon inside Card 3
    lines.append('  <g transform="translate(1090, 696)" stroke="#207448" stroke-width="2.5" fill="none">')
    lines.append('    <circle cx="16" cy="16" r="14"/>')
    lines.append('    <circle cx="16" cy="16" r="8"/>')
    lines.append('    <circle cx="16" cy="16" r="2" fill="#207448"/>')
    lines.append('  </g>')
    lines.append('  <text x="1090" y="750" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="1090" dy="0">AccuracySec= defaults to one </tspan>')
    lines.append('    <tspan x="1090" dy="32">minute so wake-ups combine; </tspan>')
    lines.append('    <tspan x="1090" dy="32">set 1s for precision</tspan>')
    lines.append('  </text>')

    # ==========================================
    # NOTE: Enable the timer, not the service (Label 23)
    # x = 40, y = 865, w = 1520, h = 95
    # ==========================================
    lines.append('  <!-- Note Card -->')
    lines.append('  <rect x="40" y="865" width="1520" height="95" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    # Terminal / prompt icon
    lines.append('  <g transform="translate(60, 882)" stroke="#207448" stroke-width="2.5" fill="none">')
    lines.append('    <rect x="0" y="0" width="34" height="26" rx="4"/>')
    lines.append('    <path d="M 6 8 l 6 5 l -6 5"/>')
    lines.append('    <line x1="16" y1="18" x2="26" y2="18"/>')
    lines.append('  </g>')
    lines.append('  <text x="110" y="904" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="110" dy="0">Enable the timer, not the service: systemctl enable --now fstrim-data.timer; </tspan>')
    lines.append('    <tspan x="110" dy="32">an overlapping oneshot trigger is skipped</tspan>')
    lines.append('  </text>')

    # ==========================================
    # BOTTOM BAR: Check the zone (Label 24)
    # x = 40, y = 980, w = 1520, h = 65
    # ==========================================
    lines.append('  <!-- Bottom Bar -->')
    lines.append('  <rect x="40" y="980" width="1520" height="65" rx="8" fill="#207448"/>')
    # Globe / Zone icon
    lines.append('  <g transform="translate(310, 995)" stroke="#ffffff" stroke-width="2.5" fill="none">')
    lines.append('    <circle cx="17" cy="17" r="14"/>')
    lines.append('    <line x1="3" y1="17" x2="31" y2="17"/>')
    lines.append('    <ellipse cx="17" cy="17" rx="7" ry="14"/>')
    lines.append('  </g>')
    lines.append('  <text x="800" y="1022" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Check the zone: add UTC or a zone name when it matters</text>')

    lines.append('</svg>')
    return "\n".join(lines)

svg_content = build_svg()
with open("test_timer_triggers.svg", "w") as f:
    f.write(svg_content)

print(f"Generated test_timer_triggers.svg ({len(svg_content)} bytes)")
