import xml.etree.ElementTree as ET
import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>One blocking call freezes every task, and how to route work off the loop</title>
  <desc>Visual infographic explaining how one synchronous blocking call freezes the entire single-threaded asyncio event loop, causing all concurrent tasks to stall and timeouts to fire, and detailing how to route blocking and CPU-bound work off the loop using to_thread, ProcessPoolExecutor, or native async libraries, alongside debug mode diagnostics.</desc>

  <defs>
    <!-- Arrowhead Green (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- ==================== 1. TITLE (48px bold) ==================== -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" y="52">One blocking call freezes every task,</tspan>
    <tspan x="800" y="102">and how to route work off the loop</tspan>
  </text>

  <!-- ==================== 2. TOP LANE: EVENT LOOP THREAD ==================== -->
  <g id="top-lane">
    <!-- Container panel for top lane -->
    <rect x="40" y="124" width="1520" height="224" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Event Loop Thread visual timeline / lane track -->
    <path d="M 120 182 H 1520" stroke="#207448" stroke-width="3" stroke-dasharray="8 6" />

    <!-- Event Loop Cycle Icon (56px outline, green stroke 4) -->
    <g transform="translate(56, 154)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" stroke-dasharray="45 15" />
      <polyline points="28,6 36,12 28,18" fill="#207448" />
      <circle cx="28" cy="28" r="7" />
    </g>

    <!-- Task A visual card (slot on thread) -->
    <g id="task-a-slot">
      <rect x="135" y="146" width="160" height="72" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Task A Glyph: Coroutine window icon (stroke 3.5) -->
      <g transform="translate(150, 158)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="38" height="34" rx="4" />
        <line x1="4" y1="16" x2="42" y2="16" />
        <circle cx="12" cy="11" r="1.5" fill="#207448" />
        <circle cx="18" cy="11" r="1.5" fill="#207448" />
        <polyline points="14,24 20,29 14,34" />
      </g>
      <!-- Task A glyph letter shape (vector path, not text) -->
      <path d="M 230 196 L 242 166 L 254 196 M 234 188 L 250 188" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
    </g>

    <!-- Task B: The Single Orange Element (calls blocking function) -->
    <g id="task-b-slot">
      <rect x="320" y="146" width="940" height="72" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="3" />
      <!-- Pause / blocking halt icon (56px, orange stroke 4) -->
      <g transform="translate(336, 154)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="48" height="44" rx="8" />
        <line x1="22" y1="18" x2="22" y2="38" />
        <line x1="34" y1="18" x2="34" y2="38" />
      </g>
      <!-- Single Quoted Label 1 -->
      <text x="412" y="191" font-family="monospace" font-size="24" font-weight="bold" fill="#db8129">time.sleep, requests.get, subprocess.run or heavy CPU</text>
    </g>

    <!-- Task C visual card (slot on thread) -->
    <g id="task-c-slot">
      <rect x="1285" y="146" width="245" height="72" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Task C Glyph: Clock / Wait timer icon -->
      <g transform="translate(1305, 158)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="24" cy="24" r="18" />
        <polyline points="24,12 24,24 33,24" />
      </g>
      <!-- Task C glyph letter shape (vector path, not text) -->
      <path d="M 1445 171 C 1435 167 1415 173 1415 182 C 1415 192 1435 197 1445 192" stroke="#207448" stroke-width="3.5" stroke-linecap="round" fill="none" />
    </g>

    <!-- Stall Warning Banner (consequence across the entire thread) -->
    <g id="stall-warning-box">
      <rect x="60" y="236" width="1480" height="92" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Alert / Fire / Warning Outline Icon (56px, green stroke 4) -->
      <g transform="translate(80, 254)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="28,6 52,48 4,48" />
        <line x1="28" y1="20" x2="28" y2="34" />
        <circle cx="28" cy="41" r="2" fill="#207448" />
      </g>
      <!-- Single Quoted Label 2 -->
      <text x="160" y="273" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">
        <tspan x="160" y="273">a task is never paused except at an await, </tspan>
        <tspan x="160" y="307">so all other tasks stall; timeouts fire everywhere</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== 3. BOTTOM ROUTING TABLE (ROWS 1, 2, 3) ==================== -->
  <!-- Row 1: blocking function -> await asyncio.to_thread... -->
  <g id="routing-row-1">
    <!-- Left Box: blocking function -->
    <rect x="40" y="378" width="500" height="84" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Stop / Barrier Outline Icon (56px) -->
    <g transform="translate(56, 392)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <line x1="12" y1="12" x2="44" y2="44" />
    </g>
    <!-- Single Quoted Label 3 -->
    <text x="135" y="431" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">blocking function</text>

    <!-- Arrow 1: Horizontal orthogonal arrow to right box -->
    <line x1="540" y1="420" x2="618" y2="420" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

    <!-- Right Box: await asyncio.to_thread... -->
    <rect x="620" y="378" width="940" height="84" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Thread / Fiber Outline Icon (56px) -->
    <g transform="translate(636, 392)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="10" width="40" height="36" rx="6" />
      <line x1="8" y1="22" x2="48" y2="22" />
      <line x1="8" y1="34" x2="48" y2="34" />
      <circle cx="16" cy="16" r="2" fill="#207448" />
    </g>
    <!-- Single Quoted Label 4 -->
    <text x="710" y="414" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="710" y="414">await asyncio.to_thread(blocking_fn, args) (3.9) </tspan>
      <tspan x="710" y="446">or loop.run_in_executor(executor, fn, *args)</tspan>
    </text>
  </g>

  <!-- Row 2: CPU-bound function -> run_in_executor with a ProcessPoolExecutor -->
  <g id="routing-row-2">
    <!-- Left Box: CPU-bound function -->
    <rect x="40" y="482" width="500" height="84" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- CPU Chip Outline Icon (56px) -->
    <g transform="translate(56, 496)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="36" height="36" rx="4" />
      <rect x="19" y="19" width="18" height="18" rx="2" />
      <line x1="18" y1="4" x2="18" y2="10" />
      <line x1="28" y1="4" x2="28" y2="10" />
      <line x1="38" y1="4" x2="38" y2="10" />
      <line x1="18" y1="46" x2="18" y2="52" />
      <line x1="28" y1="46" x2="28" y2="52" />
      <line x1="38" y1="46" x2="38" y2="52" />
      <line x1="4" y1="18" x2="10" y2="18" />
      <line x1="4" y1="28" x2="10" y2="28" />
      <line x1="4" y1="38" x2="10" y2="38" />
      <line x1="46" y1="18" x2="52" y2="18" />
      <line x1="46" y1="28" x2="52" y2="28" />
      <line x1="46" y1="38" x2="52" y2="38" />
    </g>
    <!-- Single Quoted Label 5 -->
    <text x="135" y="535" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">CPU-bound function</text>

    <!-- Arrow 2: Horizontal orthogonal arrow to right box -->
    <line x1="540" y1="524" x2="618" y2="524" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

    <!-- Right Box: run_in_executor with a ProcessPoolExecutor -->
    <rect x="620" y="482" width="940" height="84" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Multi-Process Cluster Outline Icon (56px) -->
    <g transform="translate(636, 496)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="20" height="20" rx="3" />
      <rect x="30" y="6" width="20" height="20" rx="3" />
      <rect x="6" y="30" width="20" height="20" rx="3" />
      <rect x="30" y="30" width="20" height="20" rx="3" />
    </g>
    <!-- Single Quoted Label 6 -->
    <text x="710" y="534" font-family="monospace" font-size="25" fill="#303a36">run_in_executor with a ProcessPoolExecutor</text>
  </g>

  <!-- Row 3: sync libraries requests, paramiko, boto3 -> wrap with to_thread -->
  <g id="routing-row-3">
    <!-- Left Box: sync libraries requests, paramiko, boto3 -->
    <rect x="40" y="586" width="500" height="84" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Package / Sync Library Outline Icon (56px) -->
    <g transform="translate(56, 600)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 50 17 L 28 28 L 6 17 Z" />
      <polyline points="6,17 6,39 28,50 50,39 50,17" />
      <line x1="28" y1="28" x2="28" y2="50" />
    </g>
    <!-- Single Quoted Label 7 -->
    <text x="135" y="622" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="135" y="622">sync libraries </tspan>
      <tspan x="135" y="654">requests, paramiko, boto3</tspan>
    </text>

    <!-- Arrow 3: Horizontal orthogonal arrow to right box -->
    <line x1="540" y1="628" x2="618" y2="628" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

    <!-- Right Box: wrap with to_thread -->
    <rect x="620" y="586" width="940" height="84" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Wrapper Bracket Outline Icon (56px) -->
    <g transform="translate(636, 600)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 18 10 L 8 10 L 8 46 L 18 46" />
      <path d="M 38 10 L 48 10 L 48 46 L 38 46" />
      <circle cx="28" cy="28" r="8" />
    </g>
    <!-- Single Quoted Label 8 -->
    <text x="710" y="638" font-family="monospace" font-size="26" fill="#303a36">wrap with to_thread</text>
  </g>

  <!-- ==================== 4. ASYNC LIBRARIES & SIDE NOTE ==================== -->
  <g id="async-and-side-note">
    <!-- Async Libraries Panel (Row 4 of routing options) -->
    <g id="async-libraries-panel">
      <rect x="40" y="694" width="920" height="176" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Async Network / Lightning Outline Icon (56px) -->
      <g transform="translate(58, 754)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="32,6 12,30 26,30 20,50 44,24 28,24" />
      </g>
      <!-- Single Quoted Label 9 -->
      <text x="130" y="732" font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="130" y="732">async libraries: aiohttp, httpx, asyncssh, </tspan>
        <tspan x="130" y="768">aiofiles (uses threads under the hood), asyncpg, </tspan>
        <tspan x="130" y="804">redis.asyncio, aiokafka, kubernetes_asyncio, </tspan>
        <tspan x="130" y="840">aioboto3, aiobotocore, grpc.aio</tspan>
      </text>
    </g>

    <!-- Side Note: uvloop -->
    <g id="side-note-panel">
      <rect x="1000" y="694" width="560" height="176" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- Speedometer / Fast Loop Outline Icon (56px) -->
      <g transform="translate(1020, 754)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 8 42 A 22 22 0 1 1 48 42" />
        <line x1="28" y1="28" x2="40" y2="18" />
        <circle cx="28" cy="28" r="4" fill="#207448" />
      </g>
      <!-- Single Quoted Label 11 -->
      <text x="1100" y="766" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">
        <tspan x="1100" y="766">uvloop: faster drop-in loop </tspan>
        <tspan x="1100" y="804">on Linux and macOS</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== 5. DEBUG STRIP ==================== -->
  <g id="debug-strip">
    <rect x="40" y="894" width="1520" height="196" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Diagnostic / Terminal Inspect Outline Icon (56px) -->
    <g transform="translate(62, 964)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="42" rx="6" />
      <circle cx="28" cy="24" r="10" />
      <line x1="35" y1="31" x2="44" y2="40" />
    </g>
    <!-- Single Quoted Label 10 -->
    <text x="135" y="934" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="135" y="934">asyncio.run(main(), debug=True) or PYTHONASYNCIODEBUG=1 logs callbacks longer than 100 ms </tspan>
      <tspan x="135" y="974">(loop.slow_callback_duration), coroutines never awaited and tasks destroyed while pending; </tspan>
      <tspan x="135" y="1014">asyncio.all_tasks() and task.print_stack() show where tasks are stuck; </tspan>
      <tspan x="135" y="1054">py-spy dump --pid when the loop itself is blocked</tspan>
    </text>
  </g>

  <!-- ==================== 6. BOTTOM TAKEAWAY BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1114" width="1520" height="62" rx="10" fill="#207448" />
    <!-- Shield / Safety Check Outline Icon (white) -->
    <g transform="translate(605, 1123)" stroke="#ffffff" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 22 4 L 6 10 V 22 C 6 34 22 42 22 42 C 22 42 38 34 38 22 V 10 Z" />
      <polyline points="14,22 20,28 30,16" />
    </g>
    <!-- Single Quoted Label 12 -->
    <text x="800" y="1155" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Keep the loop free</text>
  </g>
</svg>'''

with open("candidate_blocking_loop_fix.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

print("Saved candidate_blocking_loop_fix.svg successfully!")
