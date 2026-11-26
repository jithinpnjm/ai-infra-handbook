import xml.etree.ElementTree as ET
import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Paginated API into batches of 100: two generators in a row</title>
  <desc>A flow of pages and batches showing two generators in a row that consume a paginated API and yield batches of 100 with constant memory.</desc>

  <defs>
    <marker id="arrow" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 1 2 L 16 9 L 1 16 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="40" y="68" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36"><tspan x="40" dy="0">Paginated API into batches of 100:</tspan><tspan x="40" dy="58">two generators in a row</tspan></text>

  <!-- ==================== LEFT COLUMN: MAIN GENERATOR PIPELINE ==================== -->

  <!-- STEP 1: list_instances (fetch page, yield items) -->
  <g id="step-1">
    <rect x="40" y="160" width="960" height="240" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    
    <!-- Step Circle 1 -->
    <circle cx="78" cy="198" r="22" fill="#207448" />
    <text x="78" y="206" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>

    <!-- Icon: API window / database outline (56x40) -->
    <g transform="translate(116, 178)" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
      <rect x="0" y="0" width="48" height="38" rx="5" />
      <line x1="0" y1="12" x2="48" y2="12" stroke-width="2" />
      <circle cx="8" cy="6" r="2" fill="#207448" />
      <circle cx="16" cy="6" r="2" fill="#207448" />
      <line x1="10" y1="20" x2="38" y2="20" />
      <line x1="10" y1="28" x2="28" y2="28" />
    </g>

    <!-- Node Title -->
    <text x="180" y="206" font-family="monospace" font-size="30" font-weight="bold" fill="#303a36">list_instances(client, project)</text>

    <!-- Inner Code Box -->
    <rect x="64" y="234" width="912" height="150" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="84" y="262" font-family="monospace" font-size="24" fill="#303a36">token = None</text>

    <!-- Loop boundary indication -->
    <rect x="76" y="274" width="888" height="100" rx="6" fill="#f8faf8" stroke="#207448" stroke-width="1" stroke-dasharray="4,4" />
    <text x="88" y="300" font-family="monospace" font-size="24" fill="#303a36">client.list(project=project, page_token=token, page_size=500)</text>
    <text x="88" y="326" font-family="monospace" font-size="24" fill="#303a36">yield from resp[items]</text>
    <text x="88" y="352" font-family="monospace" font-size="24" fill="#303a36">token = resp.get(nextPageToken)</text>
    <text x="560" y="352" font-family="monospace" font-size="24" fill="#303a36">if not token: break</text>
  </g>

  <!-- Connection Arrow 1 (Step 1 -> Step 2) with label -->
  <g id="arrow-1">
    <path d="M 120 400 L 120 460" stroke="#207448" stroke-width="3" fill="none" marker-end="url(#arrow)" />
    <text x="160" y="438" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">items arrive one at a time, one page of 500 in memory</text>
  </g>

  <!-- STEP 2: Filter (generator expression) -->
  <g id="step-2">
    <rect x="40" y="465" width="960" height="145" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Step Circle 2 -->
    <circle cx="78" cy="503" r="22" fill="#207448" />
    <text x="78" y="511" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>

    <!-- Icon: Funnel filter (44x40) -->
    <g transform="translate(118, 483)" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="2,4 42,4 28,20 28,34 16,38 16,20" />
    </g>

    <!-- Code Line: running filter -->
    <text x="180" y="512" font-family="monospace" font-size="25" font-weight="bold" fill="#303a36"><tspan x="180" dy="0">running = (i for i in list_instances(c, p) </tspan><tspan x="180" dy="32">           if i[status] == RUNNING)</tspan></text>

    <!-- Note badge -->
    <rect x="690" y="548" width="286" height="42" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="833" y="577" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">with no list built</text>
  </g>

  <!-- Connection Arrow 2 (Step 2 -> Step 3) -->
  <g id="arrow-2">
    <path d="M 120 610 L 120 660" stroke="#207448" stroke-width="3" fill="none" marker-end="url(#arrow)" />
  </g>

  <!-- STEP 3: batched (generator yielding batches of n) - ORANGE HIGHLIGHT -->
  <g id="step-3">
    <rect x="40" y="665" width="960" height="195" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3" />

    <!-- Step Circle 3 (Orange) -->
    <circle cx="78" cy="705" r="22" fill="#db8129" />
    <text x="78" y="713" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>

    <!-- Icon: Batched chunks / grid (46x40) in Orange -->
    <g transform="translate(116, 685)" fill="none" stroke="#db8129" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
      <rect x="0" y="0" width="20" height="16" rx="3" />
      <rect x="26" y="0" width="20" height="16" rx="3" />
      <rect x="0" y="22" width="20" height="16" rx="3" />
      <rect x="26" y="22" width="20" height="16" rx="3" />
    </g>

    <!-- Node Title (Orange) -->
    <text x="180" y="713" font-family="monospace" font-size="30" font-weight="bold" fill="#db8129">batched(iterable, n)</text>

    <!-- Implementation Code -->
    <rect x="64" y="736" width="912" height="68" rx="8" fill="#fffaf5" stroke="#db8129" stroke-width="1.5" />
    <text x="80" y="777" font-family="monospace" font-size="24" fill="#303a36">it = iter(iterable); while batch := list(islice(it, n)): yield batch</text>

    <!-- Note on Python 3.12 batched -->
    <text x="80" y="836" font-family="sans-serif" font-size="24" fill="#303a36">Python 3.12 itertools.batched(iterable, n) yields tuples</text>
  </g>

  <!-- Connection Arrow 3 (Step 3 -> Step 4) -->
  <g id="arrow-3">
    <path d="M 120 860 L 120 910" stroke="#207448" stroke-width="3" fill="none" marker-end="url(#arrow)" />
  </g>

  <!-- STEP 4: Consumer (bulk delete in batches) -->
  <g id="step-4">
    <rect x="40" y="915" width="960" height="145" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Step Circle 4 -->
    <circle cx="78" cy="953" r="22" fill="#207448" />
    <text x="78" y="961" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>

    <!-- Icon: Trash / bulk delete (44x40) -->
    <g transform="translate(118, 933)" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 10 L 38 10 L 34 36 L 10 36 Z" />
      <line x1="2" y1="10" x2="42" y2="10" />
      <path d="M 16 10 L 16 4 L 28 4 L 28 10" />
      <line x1="17" y1="16" x2="17" y2="30" stroke-width="2" />
      <line x1="27" y1="16" x2="27" y2="30" stroke-width="2" />
    </g>

    <!-- Code Line: consumer loop -->
    <text x="180" y="955" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36"><tspan x="180" dy="0">for ids in batched(all_instance_ids, 100): </tspan><tspan x="180" dy="32">    client.bulk_delete(ids)</tspan></text>

    <!-- Note badge -->
    <rect x="520" y="1005" width="456" height="42" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="748" y="1034" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">matches the API limit of 100 per call</text>
  </g>

  <!-- ==================== RIGHT COLUMN: NGINX PIPELINE STRIP ==================== -->
  <g id="nginx-pipeline-panel">
    <rect x="1040" y="160" width="520" height="900" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Icon: Pipeline / connected links (48x44) -->
    <g transform="translate(1075, 185)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="0" y="8" width="14" height="24" rx="4" />
      <rect x="30" y="8" width="14" height="24" rx="4" />
      <line x1="14" y1="20" x2="30" y2="20" stroke-width="4" />
    </g>

    <!-- Subcard 1: Pipeline stages -->
    <rect x="1065" y="250" width="470" height="340" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    
    <text x="1085" y="300" font-family="monospace" font-size="24" fill="#303a36"><tspan x="1085" dy="0">files(root) to </tspan><tspan x="1085" dy="54">lines(paths) to </tspan><tspan x="1085" dy="54">parse(lines) to </tspan><tspan x="1085" dy="54">errors(records) to </tspan><tspan x="1085" dy="54">Counter(...).most_common(10)</tspan></text>

    <!-- Subcard 2: Memory & architecture explanation -->
    <rect x="1065" y="620" width="470" height="240" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />

    <text x="1088" y="675" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="1088" dy="0">one line in memory </tspan><tspan x="1088" dy="38">at any moment; each stage </tspan><tspan x="1088" dy="38">is its own function and </tspan><tspan x="1088" dy="38">can be tested alone</tspan></text>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="40" y="1090" width="1520" height="70" rx="12" fill="#207448" />
    <text x="800" y="1134" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Each stage pulls one item from the stage before it</text>
  </g>
</svg>
"""

with open("test_candidate_api_batches.svg", "w") as f:
    f.write(svg_content.strip())
print("Saved test_candidate_api_batches.svg")
