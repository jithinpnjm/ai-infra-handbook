#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def build_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>One app host through the application play</title>')
    svg.append('  <desc>Four stage columns showing pre_tasks, tasks, handlers, and post_tasks for an application deployment with zero downtime.</desc>')
    svg.append('')
    svg.append('  <defs>')
    svg.append('    <marker id="arrow" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse">')
    svg.append('      <path d="M 1 2 L 10 6 L 1 10 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse">')
    svg.append('      <path d="M 1 2 L 10 6 L 1 10 Z" fill="#db8129" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    svg.append('')
    svg.append('  <!-- Canvas Background -->')
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    svg.append('')
    svg.append('  <!-- Title -->')
    svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">One app host through the application play</text>')
    svg.append('')
    svg.append('  <!-- Subtitle Panel -->')
    svg.append('  <rect x="45" y="82" width="1510" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    svg.append('  <text x="800" y="114" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">one app host with serial one at a time and max_fail_percentage 0</text>')
    svg.append('')

    # Column dimensions:
    # Col 1: pre_tasks  x = 45,  w = 360
    # Col 2: tasks      x = 430, w = 425
    # Col 3: handlers   x = 880, w = 325
    # Col 4: post_tasks x = 1230, w = 325

    # 4 Stage Column Containers
    svg.append('  <!-- Column 1 Container: pre_tasks -->')
    svg.append('  <rect x="45" y="148" width="360" height="1022" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <rect x="45" y="148" width="360" height="54" rx="14" fill="#207448" />')
    svg.append('  <text x="225" y="186" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#ffffff">pre_tasks</text>')
    svg.append('')

    svg.append('  <!-- Column 2 Container: tasks -->')
    svg.append('  <rect x="430" y="148" width="425" height="1022" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <rect x="430" y="148" width="425" height="54" rx="14" fill="#207448" />')
    svg.append('  <text x="642" y="186" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#ffffff">tasks</text>')
    svg.append('')

    svg.append('  <!-- Column 3 Container: handlers -->')
    svg.append('  <rect x="880" y="148" width="325" height="1022" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <rect x="880" y="148" width="325" height="54" rx="14" fill="#207448" />')
    svg.append('  <text x="1042" y="186" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#ffffff">handlers</text>')
    svg.append('')

    svg.append('  <!-- Column 4 Container: post_tasks -->')
    svg.append('  <rect x="1230" y="148" width="325" height="1022" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <rect x="1230" y="148" width="325" height="54" rx="14" fill="#207448" />')
    svg.append('  <text x="1392" y="186" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#ffffff">post_tasks</text>')
    svg.append('')

    # ==================== COLUMN 1 ITEMS ====================
    # Card 1: assert app_version is a tag or commit SHA
    # x = 60, w = 330, y = 230, h = 170
    svg.append('  <!-- Col 1, Step 1: assert app_version -->')
    svg.append('  <g id="pretask-1">')
    svg.append('    <rect x="60" y="230" width="330" height="170" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    # Icon: shield / check
    svg.append('    <g transform="translate(203, 246)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 22 4 L 4 12 V 24 C 4 34 22 44 22 44 C 22 44 40 34 40 24 V 12 Z" />')
    svg.append('      <polyline points="14,24 20,30 30,18" />')
    svg.append('    </g>')
    svg.append('    <text x="225" y="322" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="225" dy="0">assert app_version</tspan>')
    svg.append('      <tspan x="225" dy="28">is a tag or</tspan>')
    svg.append('      <tspan x="225" dy="28">commit SHA</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Arrow down to Step 2
    svg.append('  <line x1="225" y1="400" x2="225" y2="440" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('')

    # Card 2: touch drain flag under /var/www/lb-drain delegated to the first web host
    # x = 60, w = 330, y = 445, h = 230
    svg.append('  <!-- Col 1, Step 2: touch drain flag -->')
    svg.append('  <g id="pretask-2">')
    svg.append('    <rect x="60" y="445" width="330" height="230" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    # Icon: gate / server switch
    svg.append('    <g transform="translate(203, 460)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="36" height="34" rx="4" />')
    svg.append('      <line x1="4" y1="23" x2="40" y2="23" />')
    svg.append('      <circle cx="12" cy="14" r="2" fill="#207448" />')
    svg.append('      <circle cx="12" cy="31" r="2" fill="#207448" />')
    svg.append('    </g>')
    svg.append('    <text x="225" y="530" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="225" dy="0" font-weight="bold">touch drain flag</tspan>')
    svg.append('      <tspan x="225" dy="28">under</tspan>')
    svg.append('      <tspan x="225" dy="28" font-family="monospace">/var/www/lb-drain</tspan>')
    svg.append('      <tspan x="225" dy="28">delegated to the</tspan>')
    svg.append('      <tspan x="225" dy="28">first web host</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Arrow down to Step 3
    svg.append('  <line x1="225" y1="675" x2="225" y2="715" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('')

    # Card 3: pause 5 seconds
    # x = 60, w = 330, y = 720, h = 120
    svg.append('  <!-- Col 1, Step 3: pause 5 seconds -->')
    svg.append('  <g id="pretask-3">')
    svg.append('    <rect x="60" y="720" width="330" height="120" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    # Icon: clock / timer
    svg.append('    <g transform="translate(203, 735)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="22" cy="22" r="18" />')
    svg.append('      <polyline points="22,12 22,22 30,22" />')
    svg.append('    </g>')
    svg.append('    <text x="225" y="805" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">pause 5 seconds</text>')
    svg.append('  </g>')
    svg.append('')

    # Arrow from pre_tasks step 3 to tasks step 1 (orthogonal, in the gap)
    svg.append('  <!-- Connection from pre_tasks to tasks -->')
    svg.append('  <path d="M 390 780 H 418 V 252 H 445" fill="none" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('')

    # ==================== COLUMN 2 ITEMS (tasks) ====================
    # x = 445, w = 395
    # Let's place the 11 tasks with cards:
    # 1. group and user: y = 220, h = 64
    # 2. directory skeleton: y = 296, h = 64
    # 3. git fetch pinned version: y = 372, h = 86
    # 4. venv from requirements.lock: y = 470, h = 86
    # 5. env file mode 0600: y = 568, h = 64
    # 6. alembic upgrade head run_once: y = 644, h = 86
    # 7. systemd unit: y = 742, h = 64
    # 8. switch current symlink: y = 818, h = 86
    # 9. meta flush_handlers: y = 916, h = 64
    # 10. uri readyz retries 20 delay 3: y = 992, h = 86 (ORANGE!)
    # 11. prune old releases: y = 1090, h = 64

    # Task 1: group and user
    svg.append('  <!-- Task 1: group and user -->')
    svg.append('  <g id="task-1">')
    svg.append('    <rect x="445" y="220" width="395" height="64" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <g transform="translate(460, 230)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="14" cy="14" r="8" />')
    svg.append('      <path d="M 4 36 C 4 26 24 26 24 36" />')
    svg.append('      <circle cx="28" cy="16" r="6" />')
    svg.append('      <path d="M 22 36 C 22 28 38 28 38 36" />')
    svg.append('    </g>')
    svg.append('    <text x="525" y="260" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">group and user</text>')
    svg.append('  </g>')
    svg.append('  <line x1="642" y1="284" x2="642" y2="294" stroke="#207448" stroke-width="2" marker-end="url(#arrow)" />')
    svg.append('')

    # Task 2: directory skeleton
    svg.append('  <!-- Task 2: directory skeleton -->')
    svg.append('  <g id="task-2">')
    svg.append('    <rect x="445" y="296" width="395" height="64" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <g transform="translate(460, 306)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 6 10 L 16 10 L 22 16 L 38 16 L 38 36 L 6 36 Z" />')
    svg.append('      <line x1="6" y1="18" x2="38" y2="18" />')
    svg.append('    </g>')
    svg.append('    <text x="525" y="336" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">directory skeleton</text>')
    svg.append('  </g>')
    svg.append('  <line x1="642" y1="360" x2="642" y2="370" stroke="#207448" stroke-width="2" marker-end="url(#arrow)" />')
    svg.append('')

    # Task 3: git fetch pinned version
    svg.append('  <!-- Task 3: git fetch pinned version -->')
    svg.append('  <g id="task-3">')
    svg.append('    <rect x="445" y="372" width="395" height="86" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <g transform="translate(460, 393)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="12" cy="12" r="5" />')
    svg.append('      <circle cx="12" cy="32" r="5" />')
    svg.append('      <circle cx="32" cy="18" r="5" />')
    svg.append('      <line x1="12" y1="17" x2="12" y2="27" />')
    svg.append('      <path d="M 12 27 C 12 18 32 25 32 23" />')
    svg.append('    </g>')
    svg.append('    <text x="525" y="411" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="525" dy="0" font-weight="bold">git fetch</tspan>')
    svg.append('      <tspan x="525" dy="28">pinned version</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('  <line x1="642" y1="458" x2="642" y2="468" stroke="#207448" stroke-width="2" marker-end="url(#arrow)" />')
    svg.append('')

    # Task 4: venv from requirements.lock
    svg.append('  <!-- Task 4: venv from requirements.lock -->')
    svg.append('  <g id="task-4">')
    svg.append('    <rect x="445" y="470" width="395" height="86" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <g transform="translate(460, 491)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="8" width="32" height="30" rx="3" />')
    svg.append('      <line x1="6" y1="18" x2="38" y2="18" />')
    svg.append('      <line x1="14" y1="26" x2="30" y2="26" />')
    svg.append('    </g>')
    svg.append('    <text x="525" y="509" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="525" dy="0">venv from</tspan>')
    svg.append('      <tspan x="525" dy="28" font-family="monospace">requirements.lock</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('  <line x1="642" y1="556" x2="642" y2="566" stroke="#207448" stroke-width="2" marker-end="url(#arrow)" />')
    svg.append('')

    # Task 5: env file mode 0600
    svg.append('  <!-- Task 5: env file mode 0600 -->')
    svg.append('  <g id="task-5">')
    svg.append('    <rect x="445" y="568" width="395" height="64" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <g transform="translate(460, 578)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="10" y="18" width="24" height="20" rx="3" />')
    svg.append('      <path d="M 16 18 V 10 C 16 6 28 6 28 10 V 18" />')
    svg.append('    </g>')
    svg.append('    <text x="525" y="608" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan font-family="sans-serif">env file mode </tspan>')
    svg.append('      <tspan font-family="monospace" font-weight="bold">0600</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('  <line x1="642" y1="632" x2="642" y2="642" stroke="#207448" stroke-width="2" marker-end="url(#arrow)" />')
    svg.append('')

    # Task 6: alembic upgrade head run_once
    svg.append('  <!-- Task 6: alembic upgrade head run_once -->')
    svg.append('  <g id="task-6">')
    svg.append('    <rect x="445" y="644" width="395" height="86" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <g transform="translate(460, 665)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <ellipse cx="22" cy="12" rx="16" ry="6" />')
    svg.append('      <path d="M 6 12 V 32 C 6 36 38 36 38 32 V 12" />')
    svg.append('      <path d="M 6 22 C 6 26 38 26 38 22" />')
    svg.append('    </g>')
    svg.append('    <text x="525" y="683" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="525" dy="0" font-family="monospace">alembic upgrade head</tspan>')
    svg.append('      <tspan x="525" dy="28" font-weight="bold">run_once</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('  <line x1="642" y1="730" x2="642" y2="740" stroke="#207448" stroke-width="2" marker-end="url(#arrow)" />')
    svg.append('')

    # Task 7: systemd unit
    svg.append('  <!-- Task 7: systemd unit -->')
    svg.append('  <g id="task-7">')
    svg.append('    <rect x="445" y="742" width="395" height="64" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <g transform="translate(460, 752)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="22" cy="22" r="8" />')
    svg.append('      <path d="M 22 6 V 10 M 22 34 V 38 M 6 22 H 10 M 34 22 H 38 M 11 11 L 14 14 M 30 30 L 33 33 M 11 33 L 14 30 M 30 14 L 33 11" />')
    svg.append('    </g>')
    svg.append('    <text x="525" y="782" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">systemd unit</text>')
    svg.append('  </g>')
    svg.append('  <line x1="642" y1="806" x2="642" y2="816" stroke="#207448" stroke-width="2" marker-end="url(#arrow)" />')
    svg.append('')

    # Task 8: switch current symlink
    svg.append('  <!-- Task 8: switch current symlink -->')
    svg.append('  <g id="task-8">')
    svg.append('    <rect x="445" y="818" width="395" height="86" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <g transform="translate(460, 839)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 12 28 A 10 10 0 1 1 26 34" />')
    svg.append('      <path d="M 32 16 A 10 10 0 1 1 18 10" />')
    svg.append('      <line x1="16" y1="28" x2="28" y2="16" />')
    svg.append('    </g>')
    svg.append('    <text x="525" y="857" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="525" dy="0">switch current</tspan>')
    svg.append('      <tspan x="525" dy="28">symlink</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('  <line x1="642" y1="904" x2="642" y2="914" stroke="#207448" stroke-width="2" marker-end="url(#arrow)" />')
    svg.append('')

    # Task 9: meta flush_handlers
    svg.append('  <!-- Task 9: meta flush_handlers -->')
    svg.append('  <g id="task-9">')
    svg.append('    <rect x="445" y="916" width="395" height="64" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <g transform="translate(460, 926)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polyline points="8,14 18,24 8,34" />')
    svg.append('      <polyline points="18,14 28,24 18,34" />')
    svg.append('      <line x1="34" y1="12" x2="34" y2="36" />')
    svg.append('    </g>')
    svg.append('    <text x="525" y="956" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">meta flush_handlers</text>')
    svg.append('  </g>')
    svg.append('')

    # Task 9 connects to Column 3 (handlers)
    svg.append('  <!-- Flush Handlers Trigger -->')
    svg.append('  <line x1="840" y1="948" x2="893" y2="948" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('')

    # ==================== COLUMN 3 ITEM (handlers) ====================
    # Card: restart fleetapp only when something changed
    # x = 895, w = 295, y = 880, h = 180
    svg.append('  <!-- Col 3: Handler Card -->')
    svg.append('  <g id="handler-card">')
    svg.append('    <rect x="895" y="880" width="295" height="180" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    # Icon: restart loop
    svg.append('    <g transform="translate(1020, 896)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 38 22 A 16 16 0 1 1 28 8" />')
    svg.append('      <polyline points="28,2 28,10 36,10" />')
    svg.append('    </g>')
    svg.append('    <text x="1042" y="976" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1042" dy="0" font-weight="bold">restart fleetapp</tspan>')
    svg.append('      <tspan x="1042" dy="28">only when</tspan>')
    svg.append('      <tspan x="1042" dy="28">something changed</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Arrow from handlers back to Task 10 (uri readyz)
    svg.append('  <!-- Handler completion back to uri readyz -->')
    svg.append('  <path d="M 895 1020 H 870 V 1035 H 842" fill="none" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('')

    # Task 10: uri readyz retries 20 delay 3 (ORANGE HIGHLIGHT GATE!)
    svg.append('  <!-- Task 10: uri readyz (Orange Gate) -->')
    svg.append('  <g id="task-10">')
    svg.append('    <rect x="445" y="992" width="395" height="86" rx="8" fill="#fff5eb" stroke="#db8129" stroke-width="3" />')
    svg.append('    <g transform="translate(460, 1013)" stroke="#db8129" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="22" cy="22" r="16" />')
    svg.append('      <polyline points="14,22 20,28 30,16" />')
    svg.append('    </g>')
    svg.append('    <text x="525" y="1031" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="525" dy="0" font-family="monospace" font-weight="bold" fill="#db8129">uri readyz</tspan>')
    svg.append('      <tspan x="525" dy="28" font-family="monospace">retries 20 delay 3</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('  <line x1="642" y1="1078" x2="642" y2="1088" stroke="#207448" stroke-width="2" marker-end="url(#arrow)" />')
    svg.append('')

    # Task 11: prune old releases
    svg.append('  <!-- Task 11: prune old releases -->')
    svg.append('  <g id="task-11">')
    svg.append('    <rect x="445" y="1090" width="395" height="64" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <g transform="translate(460, 1100)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polyline points="6,12 12,38 32,38 38,12" />')
    svg.append('      <line x1="4" y1="12" x2="40" y2="12" />')
    svg.append('      <line x1="16" y1="8" x2="28" y2="8" />')
    svg.append('    </g>')
    svg.append('    <text x="525" y="1130" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">prune old releases</text>')
    svg.append('  </g>')
    svg.append('')

    # Connection from prune old releases (Col 2) to post_tasks (Col 4)
    # Col 3 has empty space at y = 1122!
    svg.append('  <!-- Connection from tasks to post_tasks -->')
    svg.append('  <line x1="840" y1="1122" x2="1243" y2="1122" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('')

    # ==================== COLUMN 4 ITEMS (post_tasks) ====================
    # x = 1245, w = 295
    # Card 1: remove drain flag: y = 960, h = 110
    # Card 2: host back in rotation: y = 1100, h = 64
    # Wait, if arrow from Col 2 enters at y = 1122:
    # Let's arrange post_tasks cards so that the flow enters Card 1 first!
    # Where does the flow enter post_tasks?
    # Readyz passed -> prune old releases -> post_tasks: remove drain flag -> host back in rotation!
    # What if the arrow from Col 2 goes to remove drain flag:
    # Say remove drain flag is at y = 950, and host back in rotation is at y = 1080?
    # Then arrow from Col 2 at y = 1122 would enter below it?
    # NO! If arrow comes from prune old releases at y = 1122, it can enter remove drain flag if remove drain flag is at y = 1010,
    # OR what if the arrow comes from uri readyz gate directly (or prune) and enters remove drain flag!
    # Let's check:
    # If remove drain flag is at y = 990, h = 76.
    # host back in rotation is at y = 1085, h = 76.
    # Arrow from Box 11 (prune old releases at y = 1122) can go:
    # H 1220 V 1028 H 1245 -> enters remove drain flag at y = 1028!
    # Then from remove drain flag (bottom at y = 1066), arrow down to host back in rotation at y = 1085!
    # Zero crossings! Completely orthogonal!
    
    svg.append('  <!-- Col 4, Step 1: remove drain flag -->')
    svg.append('  <g id="posttask-1">')
    svg.append('    <rect x="1245" y="970" width="295" height="84" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    # Icon: checkmark on server / unflag
    svg.append('    <g transform="translate(1260, 988)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <line x1="8" y1="38" x2="8" y2="8" />')
    svg.append('      <path d="M 8 8 L 32 14 L 8 22 Z" />')
    svg.append('      <line x1="28" y1="28" x2="38" y2="38" />')
    svg.append('      <line x1="38" y1="28" x2="28" y2="38" />')
    svg.append('    </g>')
    svg.append('    <text x="1315" y="1021" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">remove drain flag</text>')
    svg.append('  </g>')
    svg.append('')

    # Arrow down to host back in rotation
    svg.append('  <line x1="1392" y1="1054" x2="1392" y2="1082" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('')

    svg.append('  <!-- Col 4, Step 2: host back in rotation -->')
    svg.append('  <g id="posttask-2">')
    svg.append('    <rect x="1245" y="1084" width="295" height="76" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    # Icon: rotation check
    svg.append('    <g transform="translate(1260, 1098)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 36 24 A 14 14 0 1 1 24 10" />')
    svg.append('      <polyline points="24,4 24,11 31,11" />')
    svg.append('      <polyline points="14,24 19,29 28,19" />')
    svg.append('    </g>')
    svg.append('    <text x="1315" y="1120" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1315" dy="0" font-weight="bold">host back</tspan>')
    svg.append('      <tspan x="1315" dy="26">in rotation</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    svg.append('</svg>')
    return "\n".join(svg)

with open("test_candidate.svg", "w") as f:
    f.write(build_svg())
print("Saved test_candidate.svg")
