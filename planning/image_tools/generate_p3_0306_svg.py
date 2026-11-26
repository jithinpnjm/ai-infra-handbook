import xml.etree.ElementTree as ET
import re

title_text = "From symptom to likely cause, with the first tool to use"
desc_text = "A three-column diagnostic ladder mapping seventeen concurrency symptoms to their likely causes and remedies."

# Table dimensions
col1_w = 460
col2_w = 420
col3_w = 640
assert col1_w + col2_w + col3_w == 1520

c1_x = 40 + 20
c2_x = 40 + col1_w + 20
c3_x = 40 + col1_w + col2_w + 20

# 17 rows definition
# Each entry: (c1_lines, c2_lines, c3_lines, row_height)
# Using whitespace in tspans so direct "".join(elem.itertext()).strip() produces EXACT strings.
rows_data = [
    # Row 1
    (
        [("Tasks stall, timeouts ", 0), ("everywhere, slow callback ", 24), ("warnings", 24)],
        [("blocking the event loop", 0)],
        [("async APIs or to_thread", 0)],
        78
    ),
    # Row 2
    (
        [("Work never happens; ", 0), ("was never awaited warning", 24)],
        [("un-awaited coroutine", 0)],
        [("await or create_task", 0)],
        54
    ),
    # Row 3
    (
        [("Task exception was ", 0), ("never retrieved", 24)],
        [("dropped task reference", 0)],
        [("keep references, await or add ", 0), ("done callbacks", 24)],
        54
    ),
    # Row 4
    (
        [("Cannot cancel or shut down", 0)],
        [("swallowed CancelledError", 0)],
        [("re-raise it, no bare except", 0)],
        44
    ),
    # Row 5
    (
        [("Hangs after network blips", 0)],
        [("missing timeouts", 0)],
        [("wait_for or timeout on every await; ", 0), ("client timeout=", 24)],
        54
    ),
    # Row 6
    (
        [("OOM, too many open files, ", 0), ("target overload", 24)],
        [("unbounded fan-out", 0)],
        [("semaphores, bounded queues, ", 0), ("islice feeding", 24)],
        54
    ),
    # Row 7
    (
        [("Rare wrong results", 0)],
        [("thread-unsafe shared state", 0)],
        [("locks, queues, thread-local, ", 0), ("immutable data", 24)],
        54
    ),
    # Row 8
    (
        [("Everything idle forever", 0)],
        [("deadlock", 0)],
        [("lock ordering, timeouts; ", 0), ("faulthandler.dump_traceback_later(60); ", 24), ("py-spy dump", 24)],
        78
    ),
    # Row 9
    (
        [("Hangs in children, ", 0), ("CUDA errors", 24)],
        [("fork with threads, ", 0), ("CUDA or locks", 24)],
        [("spawn or forkserver", 0)],
        54
    ),
    # Row 10
    (
        [("Can't pickle local object", 0)],
        [("pickle errors", 0)],
        [("top-level functions", 0)],
        44
    ),
    # Row 11
    (
        [("Memory growth in pools", 0)],
        [("worker leaks", 0)],
        [("maxtasksperchild, tracemalloc", 0)],
        44
    ),
    # Row 12
    (
        [("Defunct processes, ", 0), ("leftover workers", 24)],
        [("zombies or orphans", 0)],
        [("wait(), context managers, ", 0), ("process groups, supervisors", 24)],
        54
    ),
    # Row 13
    (
        [("CPU throttling, slow runs", 0)],
        [("oversubscription", 0)],
        [("match cgroup limits, ", 0), ("OMP_NUM_THREADS=1", 24)],
        54
    ),
    # Row 14
    (
        [("Target collapse", 0)],
        [("thundering herd or ", 0), ("retry storm", 24)],
        [("jittered backoff, limits, ", 0), ("circuit breakers", 24)],
        54
    ),
    # Row 15
    (
        [("Silent partial results", 0)],
        [("lost exceptions in threads", 0)],
        [("futures, threading.excepthook", 0)],
        44
    ),
    # Row 16
    (
        [("ValueError: signal only ", 0), ("works in main thread", 24)],
        [("signal in a non-main ", 0), ("thread", 24)],
        [("install handlers in the main thread ", 0), ("or loop.add_signal_handler", 24)],
        54
    ),
    # Row 17
    (
        [("RuntimeError", 0)],
        [("asyncio.run() inside a ", 0), ("running loop (Jupyter)", 24)],
        [("await instead; nest_asyncio only ", 0), ("for notebooks", 24)],
        54
    )
]

total_table_h = sum(r[3] for r in rows_data)
print(f"Total table height: {total_table_h}")

table_y = 104
habits_y = 1046
habits_h = 58
bar_y = 1118
bar_h = 64
total_h = 1200
print(f"Habits Y: {habits_y}, Bar Y: {bar_y}, Bar bottom: {bar_y + bar_h}")
assert bar_y + bar_h <= 1200

# Build SVG lines
lines = []
lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
lines.append(f'  <title>{title_text}</title>')
lines.append(f'  <desc>{desc_text}</desc>')
lines.append('  <!-- Background -->')
lines.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
lines.append('')

# Title (wrapped on 2 lines with tspan)
lines.append('  <!-- Title: 48px bold -->')
lines.append('  <text x="800" y="46" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36"><tspan x="800" dy="0">From symptom to likely cause, </tspan><tspan x="800" dy="50">with the first tool to use</tspan></text>')
lines.append('')

# Table container
lines.append('  <!-- ==================== TABLE CONTAINER ==================== -->')
lines.append(f'  <rect x="40" y="{table_y}" width="1520" height="{total_table_h}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
lines.append('')

cur_y = table_y
for idx, (c1_parts, c2_parts, c3_parts, rh) in enumerate(rows_data, 1):
    bg = "#ffffff" if (idx % 2 == 1) else "#e8f1ea"
    lines.append(f'  <!-- Row {idx} -->')
    lines.append(f'  <rect x="40" y="{cur_y}" width="1520" height="{rh}" fill="{bg}"/>')
    if idx < len(rows_data):
        lines.append(f'  <line x1="40" y1="{cur_y + rh}" x2="1560" y2="{cur_y + rh}" stroke="#207448" stroke-width="1" opacity="0.25"/>')
    
    # Text vertical centering
    # For 1 line:
    # 44px -> baseline at cur_y + 30 (top pad = 12, bot pad = 10)
    # For 2 lines:
    # 54px -> line 1 at cur_y + 24, line 2 at cur_y + 48 (dy=24)
    # For 3 lines:
    # 78px -> line 1 at cur_y + 24, line 2 at cur_y + 48, line 3 at cur_y + 72 (dy=24)
    
    def get_first_y(num_lines, r_height):
        if num_lines == 1:
            return cur_y + (r_height / 2.0) + 8.0
        elif num_lines == 2:
            return cur_y + (r_height / 2.0) - 4.0
        else: # 3 lines
            return cur_y + (r_height / 2.0) - 15.0

    # Col 1 Text
    y1 = get_first_y(len(c1_parts), rh)
    if len(c1_parts) == 1:
        lines.append(f'  <text x="{c1_x}" y="{y1:.1f}" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">{c1_parts[0][0]}</text>')
    else:
        tspans_str = "".join([f'<tspan x="{c1_x}" dy="{dy}">{txt}</tspan>' for txt, dy in c1_parts])
        lines.append(f'  <text x="{c1_x}" y="{y1:.1f}" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">{tspans_str}</text>')

    # Col 2 Text
    y2 = get_first_y(len(c2_parts), rh)
    if len(c2_parts) == 1:
        lines.append(f'  <text x="{c2_x}" y="{y2:.1f}" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">{c2_parts[0][0]}</text>')
    else:
        tspans_str = "".join([f'<tspan x="{c2_x}" dy="{dy}">{txt}</tspan>' for txt, dy in c2_parts])
        lines.append(f'  <text x="{c2_x}" y="{y2:.1f}" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">{tspans_str}</text>')

    # Col 3 Text
    y3 = get_first_y(len(c3_parts), rh)
    if len(c3_parts) == 1:
        lines.append(f'  <text x="{c3_x}" y="{y3:.1f}" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">{c3_parts[0][0]}</text>')
    else:
        tspans_str = "".join([f'<tspan x="{c3_x}" dy="{dy}">{txt}</tspan>' for txt, dy in c3_parts])
        lines.append(f'  <text x="{c3_x}" y="{y3:.1f}" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">{tspans_str}</text>')

    cur_y += rh

# Vertical column divider lines
lines.append('  <!-- Column Dividers -->')
lines.append(f'  <line x1="{40 + col1_w}" y1="{table_y}" x2="{40 + col1_w}" y2="{table_y + total_table_h}" stroke="#207448" stroke-width="1.5" opacity="0.35"/>')
lines.append(f'  <line x1="{40 + col1_w + col2_w}" y1="{table_y}" x2="{40 + col1_w + col2_w}" y2="{table_y + total_table_h}" stroke="#207448" stroke-width="1.5" opacity="0.35"/>')
lines.append('')

# Orange habits strip
lines.append('  <!-- ==================== ORANGE HABITS HIGHLIGHT STRIP ==================== -->')
lines.append(f'  <rect x="40" y="{habits_y}" width="1520" height="{habits_h}" rx="8" fill="#fff7f0" stroke="#db8129" stroke-width="2.5"/>')
# Icon on habits strip: Lock/shield with clock (safety & limits)
lines.append(f'  <g transform="translate(68, {habits_y + 11})" stroke="#db8129" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
lines.append('    <circle cx="18" cy="18" r="14"/>')
lines.append('    <polyline points="18,10 18,18 24,18"/>')
lines.append('  </g>')
lines.append(f'  <g transform="translate(1480, {habits_y + 11})" stroke="#db8129" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
lines.append('    <rect x="4" y="4" width="28" height="28" rx="5"/>')
lines.append('    <line x1="4" y1="18" x2="32" y2="18"/>')
lines.append('    <line x1="18" y1="4" x2="18" y2="32"/>')
lines.append('  </g>')
lines.append(f'  <text x="800" y="1081" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="#db8129">a timeout on every wait, a bound on every queue and pool</text>')
lines.append('')

# Bottom bar
lines.append('  <!-- ==================== TAKEAWAY BOTTOM BAR ==================== -->')
lines.append(f'  <rect x="40" y="{bar_y}" width="1520" height="{bar_h}" rx="8" fill="#207448"/>')
lines.append(f'  <text x="800" y="1157" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Start from the symptom you see</text>')
lines.append('</svg>')

svg_content = "\n".join(lines)
with open("p3-0306-symptom-ladder.svg", "w") as f:
    f.write(svg_content)

print("Saved to p3-0306-symptom-ladder.svg successfully!")
