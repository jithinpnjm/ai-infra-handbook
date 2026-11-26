import xml.etree.ElementTree as ET
import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1100" width="1600" height="1100">
  <title>gather versus TaskGroup when one task fails</title>
  <desc>Visual comparison between asyncio.gather and asyncio.TaskGroup when one task raises an exception, showing unhandled orphan tasks versus structured cancellation and ExceptionGroup handling.</desc>

  <!-- Background -->
  <rect width="1600" height="1100" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">gather versus TaskGroup when one task fails</text>

  <!-- ==================== LANE 1: gather ==================== -->
  <g id="lane-gather">
    <!-- Outer Container -->
    <rect x="40" y="95" width="1520" height="280" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Lane 1 Icon: Async Fan-out (56px) -->
    <g transform="translate(65, 110)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="14" cy="28" r="8" fill="#e8f1ea" />
      <path d="M 22 28 L 36 14" />
      <path d="M 22 28 L 38 28" />
      <path d="M 22 28 L 36 42" />
      <circle cx="44" cy="14" r="6" fill="#207448" />
      <circle cx="46" cy="28" r="6" fill="#207448" />
      <circle cx="44" cy="42" r="6" fill="#207448" />
    </g>

    <!-- Lane 1 Title -->
    <text x="145" y="148" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">gather(*aws, return_exceptions=False)</text>

    <!-- Three Tasks Visual Container (Left Side) -->
    <rect x="65" y="175" width="600" height="180" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />

    <!-- Task 1 Track: Runs to completion -->
    <rect x="85" y="195" width="560" height="34" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <rect x="85" y="195" width="560" height="34" rx="6" fill="#207448" fill-opacity="0.35" />

    <!-- Task 2 Track: Fails midway -->
    <rect x="85" y="248" width="560" height="34" rx="6" fill="#fdf4f4" stroke="#303a36" stroke-width="1.5" stroke-dasharray="4,4" />
    <rect x="85" y="248" width="220" height="34" rx="6" fill="#207448" fill-opacity="0.35" stroke="#207448" stroke-width="2" />
    <!-- Failure Octagon / Cross at x=305 -->
    <g transform="translate(305, 247)" stroke="#c53030" stroke-width="3.5" fill="#fdf4f4" stroke-linecap="round">
      <polygon points="12,2 24,2 34,12 34,24 24,34 12,34 2,24 2,12" fill="#ffffff" stroke="#c53030" stroke-width="2.5" />
      <line x1="11" y1="11" x2="25" y2="25" />
      <line x1="25" y1="11" x2="11" y2="25" />
    </g>

    <!-- Task 3 Track: Keeps running in background (orphan) -->
    <rect x="85" y="301" width="560" height="34" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <rect x="85" y="301" width="560" height="34" rx="6" fill="#207448" fill-opacity="0.35" />

    <!-- Explanation Card 1: Exception propagates, others run -->
    <rect x="690" y="175" width="845" height="85" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1112" y="210" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1112" dy="0">first exception propagates, </tspan>
      <tspan x="1112" dy="30">the other tasks keep running</tspan>
    </text>

    <!-- Explanation Card 2: return_exceptions=True behavior -->
    <rect x="690" y="270" width="845" height="85" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1112" y="305" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1112" dy="0">with &apos;return_exceptions=True&apos; exceptions are </tspan>
      <tspan x="1112" dy="30">collected in the results list alongside values</tspan>
    </text>
  </g>

  <!-- ==================== LANE 2: TaskGroup (Orange) ==================== -->
  <g id="lane-taskgroup">
    <!-- Outer Container (Orange Accent) -->
    <rect x="40" y="395" width="1520" height="360" rx="16" fill="#fffaf5" stroke="#db8129" stroke-width="3" />

    <!-- Lane 2 Icon: Structured Boundary Shield (56px) -->
    <g transform="translate(65, 410)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 C 48 34 28 48 28 48 C 28 48 8 34 8 14 Z" />
      <path d="M 18 26 L 25 33 L 38 18" />
    </g>

    <!-- Lane 2 Title -->
    <text x="145" y="448" font-family="monospace" font-size="30" font-weight="bold" fill="#303a36">async with asyncio.TaskGroup() as tg: tg.create_task(poll(n, results))</text>

    <!-- Three Tasks Visual Container (Left Side) -->
    <rect x="65" y="475" width="600" height="260" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="2" />

    <!-- Task 1 Track: Cancelled on sibling failure -->
    <rect x="85" y="495" width="220" height="34" rx="6" fill="#db8129" fill-opacity="0.3" stroke="#db8129" stroke-width="2" />
    <rect x="305" y="495" width="230" height="34" rx="6" fill="#f5f8f5" stroke="#707a75" stroke-width="1.5" stroke-dasharray="6,4" />
    <!-- Slash / cancellation mark on task 1 -->
    <line x1="315" y1="503" x2="331" y2="521" stroke="#707a75" stroke-width="3" stroke-linecap="round" />

    <!-- Task 2 Track: Fails -->
    <rect x="85" y="550" width="220" height="34" rx="6" fill="#db8129" fill-opacity="0.3" stroke="#db8129" stroke-width="2" />
    <g transform="translate(305, 549)" stroke="#c53030" stroke-width="3.5" fill="#fdf4f4" stroke-linecap="round">
      <polygon points="12,2 24,2 34,12 34,24 24,34 12,34 2,24 2,12" fill="#ffffff" stroke="#c53030" stroke-width="2.5" />
      <line x1="11" y1="11" x2="25" y2="25" />
      <line x1="25" y1="11" x2="11" y2="25" />
    </g>

    <!-- Task 3 Track: Cancelled on sibling failure -->
    <rect x="85" y="605" width="220" height="34" rx="6" fill="#db8129" fill-opacity="0.3" stroke="#db8129" stroke-width="2" />
    <rect x="305" y="605" width="230" height="34" rx="6" fill="#f5f8f5" stroke="#707a75" stroke-width="1.5" stroke-dasharray="6,4" />
    <!-- Slash / cancellation mark on task 3 -->
    <line x1="315" y1="613" x2="331" y2="631" stroke="#707a75" stroke-width="3" stroke-linecap="round" />

    <!-- Exit Barrier (All tasks awaited on exit) -->
    <line x1="535" y1="485" x2="535" y2="650" stroke="#db8129" stroke-width="3.5" stroke-linecap="round" />
    <circle cx="535" cy="658" r="5" fill="#db8129" />

    <!-- Explanation Card 1: Awaited on exit -->
    <rect x="690" y="475" width="845" height="70" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1112" y="519" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">tasks started in the group are awaited on exit</text>

    <!-- Explanation Card 2: Cancelled & ExceptionGroup -->
    <rect x="690" y="555" width="845" height="75" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1112" y="588" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1112" dy="0">if one fails the others are cancelled </tspan>
      <tspan x="1112" dy="30">and an ExceptionGroup is raised</tspan>
    </text>

    <!-- Handling Sub-card A: except* clause -->
    <rect x="690" y="640" width="560" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="712" y="670" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="712" dy="0">except* TimeoutError as eg:</tspan>
      <tspan x="712" dy="28">  log.error(timeouts: ..., </tspan>
      <tspan x="712" dy="28">  [str(e) for e in eg.exceptions])</tspan>
    </text>

    <!-- Handling Sub-card B: return results -->
    <rect x="1270" y="640" width="265" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1402" y="696" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">return results</text>
  </g>

  <!-- ==================== STRIP 1: create_task ==================== -->
  <g id="strip-create-task">
    <rect x="40" y="775" width="1520" height="85" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Gear / Task Icon (56px) -->
    <g transform="translate(65, 789)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="10" />
      <path d="M 28 6 L 28 12 M 28 44 L 28 50 M 6 28 L 12 28 M 44 28 L 50 28 M 12 12 L 17 17 M 39 39 L 44 44 M 12 44 L 17 39 M 39 17 L 44 12" />
    </g>
    <text x="145" y="813" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="145" dy="0">asyncio.create_task(coro) schedules concurrently; keep a reference because the loop holds </tspan>
      <tspan x="145" dy="28">only weak references and a dropped task can be garbage collected mid-flight</tspan>
    </text>
  </g>

  <!-- ==================== STRIP 2: await ==================== -->
  <g id="strip-await">
    <rect x="40" y="880" width="1520" height="85" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Clock / Suspend Icon (56px) -->
    <g transform="translate(65, 894)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="28,14 28,28 38,28" />
    </g>
    <text x="145" y="918" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="145" dy="0">await suspends the caller until the awaited coroutine, future or task completes; only inside </tspan>
      <tspan x="145" dy="28">async def; calling an async def returns a coroutine object that has not run yet</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="40" y="985" width="1520" height="65" rx="12" fill="#207448" />
    <text x="800" y="1027" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">A TaskGroup leaves no orphan task behind</text>
  </g>
</svg>'''

with open("candidate_test.svg", "w") as f:
    f.write(svg_content)

print("Saved candidate_test.svg")
