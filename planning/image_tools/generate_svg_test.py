import re
import xml.etree.ElementTree as ET

# Generate the SVG string
svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Sequence types on two axes, and what a list really costs</title>
  <desc>A 2 by 2 grid classifying Python sequence types across container versus flat and mutable versus immutable axes, alongside memory and performance costs for lists, arrays, deques, memoryviews, and sorting.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Title -->
  <text x="800" y="58" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Sequence types on two axes, and what a list really costs</text>

  <!-- LEFT PANEL: 2 by 2 Grid -->
  <g id="grid-container">
    <rect x="40" y="95" width="670" height="1010" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

    <!-- Grid Header Icon (56x56 outline 2x2 grid icon) -->
    <g transform="translate(65, 115)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="48" height="48" rx="8"/>
      <line x1="28" y1="4" x2="28" y2="52"/>
      <line x1="4" y1="28" x2="52" y2="28"/>
    </g>

    <!-- Column Headers -->
    <!-- Column 1: mutable -->
    <rect x="65" y="190" width="295" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="212" y="226" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">mutable</text>

    <!-- Column 2: immutable -->
    <rect x="385" y="190" width="300" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="535" y="226" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">immutable</text>

    <!-- ROW 1: container (holds references to objects stored elsewhere) -->
    <rect x="65" y="260" width="620" height="92" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="375" y="296" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="375" dy="0" font-size="30" font-weight="bold" fill="#207448">container</tspan>
      <tspan x="375" dy="34" font-size="24">(holds references to objects stored elsewhere)</tspan>
    </text>

    <!-- Cell (1,1): container & mutable -> list, collections.deque -->
    <rect x="65" y="368" width="295" height="230" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="212" y="435" text-anchor="middle" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="212" dy="0">list,</tspan>
      <tspan x="212" dy="34">collections.deque</tspan>
    </text>
    <!-- Visual schematic: pointer array to heap objects -->
    <g transform="translate(100, 500)" stroke="#207448" stroke-width="2" fill="none">
      <rect x="0" y="0" width="225" height="34" rx="4" fill="#f5f8f5"/>
      <line x1="56" y1="0" x2="56" y2="34"/>
      <line x1="112" y1="0" x2="112" y2="34"/>
      <line x1="168" y1="0" x2="168" y2="34"/>
      <!-- Pointers down to objects -->
      <circle cx="28" cy="17" r="4" fill="#207448"/>
      <circle cx="84" cy="17" r="4" fill="#207448"/>
      <circle cx="140" cy="17" r="4" fill="#207448"/>
      <circle cx="196" cy="17" r="4" fill="#207448"/>
      <path d="M 28 21 L 28 55 L 40 55" stroke-linecap="round"/>
      <path d="M 84 21 L 84 55 L 96 55" stroke-linecap="round"/>
      <rect x="40" y="45" width="40" height="20" rx="3" fill="#e8f1ea"/>
      <rect x="96" y="45" width="40" height="20" rx="3" fill="#e8f1ea"/>
    </g>

    <!-- Cell (1,2): container & immutable -> tuple -->
    <rect x="385" y="368" width="300" height="230" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="535" y="450" text-anchor="middle" font-family="ui-monospace, monospace" font-size="30" font-weight="bold" fill="#207448">tuple</text>
    <!-- Visual schematic: fixed pointer array to objects -->
    <g transform="translate(422, 500)" stroke="#207448" stroke-width="2" fill="none">
      <rect x="0" y="0" width="225" height="34" rx="4" fill="#f5f8f5"/>
      <line x1="75" y1="0" x2="75" y2="34"/>
      <line x1="150" y1="0" x2="150" y2="34"/>
      <circle cx="37" cy="17" r="4" fill="#207448"/>
      <circle cx="112" cy="17" r="4" fill="#207448"/>
      <circle cx="187" cy="17" r="4" fill="#207448"/>
      <path d="M 37 21 L 37 55 L 50 55" stroke-linecap="round"/>
      <path d="M 112 21 L 112 55 L 125 55" stroke-linecap="round"/>
      <rect x="50" y="45" width="42" height="20" rx="3" fill="#e8f1ea"/>
      <rect x="125" y="45" width="42" height="20" rx="3" fill="#e8f1ea"/>
    </g>

    <!-- ROW 2: flat (values of one type side by side in memory) -->
    <rect x="65" y="618" width="620" height="92" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="375" y="654" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="375" dy="0" font-size="30" font-weight="bold" fill="#207448">flat</tspan>
      <tspan x="375" dy="34" font-size="24">(values of one type side by side in memory)</tspan>
    </text>

    <!-- Cell (2,1): flat & mutable -> bytearray, array.array -->
    <rect x="65" y="726" width="295" height="230" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="212" y="795" text-anchor="middle" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="212" dy="0">bytearray,</tspan>
      <tspan x="212" dy="34">array.array</tspan>
    </text>
    <!-- Visual schematic: contiguous contiguous raw bytes in memory -->
    <g transform="translate(100, 860)" stroke="#207448" stroke-width="2" fill="none">
      <rect x="0" y="0" width="225" height="34" rx="4" fill="#e8f1ea"/>
      <line x1="37" y1="0" x2="37" y2="34"/>
      <line x1="75" y1="0" x2="75" y2="34"/>
      <line x1="112" y1="0" x2="112" y2="34"/>
      <line x1="150" y1="0" x2="150" y2="34"/>
      <line x1="187" y1="0" x2="187" y2="34"/>
      <rect x="0" y="46" width="225" height="22" rx="3" fill="#f5f8f5"/>
      <line x1="56" y1="46" x2="56" y2="68"/>
      <line x1="112" y1="46" x2="112" y2="68"/>
      <line x1="168" y1="46" x2="168" y2="68"/>
    </g>

    <!-- Cell (2,2): flat & immutable -> str, bytes -->
    <rect x="385" y="726" width="300" height="230" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="535" y="810" text-anchor="middle" font-family="ui-monospace, monospace" font-size="28" font-weight="bold" fill="#207448">str, bytes</text>
    <!-- Visual schematic: contiguous contiguous packed characters / bytes -->
    <g transform="translate(422, 860)" stroke="#207448" stroke-width="2" fill="none">
      <rect x="0" y="0" width="225" height="34" rx="4" fill="#e8f1ea"/>
      <line x1="37" y1="0" x2="37" y2="34"/>
      <line x1="75" y1="0" x2="75" y2="34"/>
      <line x1="112" y1="0" x2="112" y2="34"/>
      <line x1="150" y1="0" x2="150" y2="34"/>
      <line x1="187" y1="0" x2="187" y2="34"/>
      <rect x="0" y="46" width="225" height="22" rx="3" fill="#f5f8f5"/>
      <line x1="45" y1="46" x2="45" y2="68"/>
      <line x1="90" y1="46" x2="90" y2="68"/>
      <line x1="135" y1="46" x2="135" y2="68"/>
      <line x1="180" y1="46" x2="180" y2="68"/>
    </g>

    <!-- Flat view visual representation (memoryview window over buffer) -->
    <g transform="translate(65, 970)">
      <rect x="0" y="0" width="620" height="110" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" stroke-dasharray="6 4"/>
      <!-- Sliced memory buffer and window lens -->
      <g transform="translate(25, 20)" stroke="#207448" stroke-width="2" fill="none">
        <rect x="0" y="15" width="570" height="36" rx="4" fill="#f5f8f5"/>
        <line x1="57" y1="15" x2="57" y2="51"/>
        <line x1="114" y1="15" x2="114" y2="51"/>
        <line x1="171" y1="15" x2="171" y2="51"/>
        <line x1="228" y1="15" x2="228" y2="51"/>
        <line x1="285" y1="15" x2="285" y2="51"/>
        <line x1="342" y1="15" x2="342" y2="51"/>
        <line x1="399" y1="15" x2="399" y2="51"/>
        <line x1="456" y1="15" x2="456" y2="51"/>
        <line x1="513" y1="15" x2="513" y2="51"/>
        <!-- Window overlay [100:200] -->
        <rect x="171" y="9" width="171" height="48" rx="6" fill="#207448" fill-opacity="0.15" stroke="#207448" stroke-width="3"/>
        <path d="M 155 33 L 171 33 M 342 33 L 358 33" stroke-linecap="round"/>
      </g>
    </g>
  </g>

  <!-- RIGHT PANEL: Costs -->
  <g id="costs-panel">
    <rect x="750" y="95" width="810" height="1010" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

    <!-- Costs Header Icon (56x56 outline gauge / scale icon) -->
    <g transform="translate(775, 115)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <path d="M 14 36 A 16 16 0 1 1 42 36"/>
      <line x1="28" y1="28" x2="38" y2="18"/>
      <circle cx="28" cy="28" r="3" fill="#207448"/>
    </g>

    <text x="850" y="153" font-family="system-ui, -apple-system, sans-serif" font-size="34" font-weight="bold" fill="#207448">Costs</text>

    <!-- Cost Item 1: pointer overhead for lists -->
    <rect x="770" y="185" width="770" height="98" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="790" y="217" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="790" dy="0">a list stores 8 byte pointers on a 64-bit system</tspan>
      <tspan x="790" dy="30">to separate objects: a list of one million floats</tspan>
      <tspan x="790" dy="30">costs about 32 MB before you count the objects</tspan>
    </text>

    <!-- Cost Item 2: array("f") vs list (ORANGE HIGHLIGHT - single most important item) -->
    <rect x="770" y="293" width="770" height="88" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="3"/>
    <text x="790" y="328" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="790" dy="0" font-family="ui-monospace, monospace" font-weight="bold" fill="#db8129">array("f") stores 4 bytes per float, a list stores</tspan>
      <tspan x="790" dy="32" font-family="ui-monospace, monospace" font-weight="bold" fill="#db8129">a float object of about 32 bytes per value</tspan>
    </text>

    <!-- Cost Item 3: memoryview zero-copy -->
    <rect x="770" y="391" width="770" height="88" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="790" y="426" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="790" dy="0" font-family="ui-monospace, monospace">memoryview(bytearray(1024))[100:200] is a</tspan>
      <tspan x="790" dy="32">zero-copy window for sockets, mmap and NumPy</tspan>
    </text>

    <!-- Cost Item 4: list insert/pop vs deque ring buffer -->
    <rect x="770" y="489" width="770" height="98" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="790" y="521" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="790" dy="0">list.insert(0, x) and list.pop(0) are O(n);</tspan>
      <tspan x="790" dy="30">deque has appendleft, popleft and maxlen=N ring buffer:</tspan>
      <tspan x="790" dy="30">deque(maxlen=1000) keeps the last 1000 samples</tspan>
    </text>

    <!-- Cost Item 5: Timsort details -->
    <rect x="770" y="597" width="770" height="175" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="790" y="627" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="790" dy="0">sort() sorts in place and returns None;</tspan>
      <tspan x="790" dy="30">sorted() returns a new list; Timsort is stable,</tspan>
      <tspan x="790" dy="30">O(n log n), O(n) best case on partly ordered data;</tspan>
      <tspan x="790" dy="30">use key= not a comparison function;</tspan>
      <tspan x="790" dy="30">tuple comparison is lexicographic</tspan>
    </text>

    <!-- Cost Item 6: bisect and heapq -->
    <rect x="770" y="782" width="770" height="98" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="790" y="814" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="790" dy="0">bisect.bisect_left and insort keep a list sorted;</tspan>
      <tspan x="790" dy="30">heapq.nlargest(5, items) gives top-k</tspan>
      <tspan x="790" dy="30">without a full sort</tspan>
    </text>

    <!-- Cost Item 7: x in list membership -->
    <rect x="770" y="890" width="770" height="88" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="790" y="925" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="790" dy="0">x in list is linear: convert to a set</tspan>
      <tspan x="790" dy="32">when testing membership many times</tspan>
    </text>

    <!-- Cost Item 8: shallow copies -->
    <rect x="770" y="988" width="770" height="88" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="790" y="1023" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="790" dy="0">copy.copy, slicing and list()</tspan>
      <tspan x="790" dy="32">each make a shallow copy</tspan>
    </text>
  </g>

  <!-- BOTTOM TAKEAWAY BAR -->
  <rect x="40" y="1125" width="1520" height="60" rx="10" fill="#207448"/>
  <text x="800" y="1163" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">The choice of sequence type affects both memory and speed</text>
</svg>"""

with open("output_test.svg", "w") as f:
    f.write(svg)
print("Wrote output_test.svg successfully!")
