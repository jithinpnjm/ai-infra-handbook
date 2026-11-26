svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Three things a runtime must do to give a container a GPU</title>
  <desc>Three things a runtime must do to give a container a GPU: make device nodes exist in mount namespace, allow devices in devices cgroup, and mount driver user-space libraries from host.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Main Title (48px bold) -->
  <text x="800" y="60" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Three things a runtime must do</tspan>
    <tspan x="800" dy="50">to give a container a GPU</tspan>
  </text>

  <!-- Top Strip -->
  <rect x="40" y="152" width="1520" height="54" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="800" y="187" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">Namespaces and cgroups know nothing about GPUs, so the GPU layer supplies the pieces</text>

  <!-- ==================== THREE COLUMNS ==================== -->

  <!-- Column 1: Mount namespace -->
  <g id="col-1">
    <rect x="40" y="232" width="480" height="544" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

    <!-- Step 1 Number Circle -->
    <circle cx="85" cy="268" r="24" fill="#207448"/>
    <text x="85" y="277" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>

    <!-- Storage / Device Outline Icon (56px, stroke 4, #207448) -->
    <g transform="translate(424, 242)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="6"/>
      <line x1="16" y1="20" x2="26" y2="20"/>
      <line x1="16" y1="28" x2="36" y2="28"/>
      <circle cx="36" cy="20" r="2" fill="#207448"/>
    </g>

    <!-- Column 1 Title (30px bold) -->
    <text x="265" y="296" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="265" dy="0">Make the device </tspan>
      <tspan x="265" dy="32">nodes exist in the </tspan>
      <tspan x="265" dy="32">container's mount </tspan>
      <tspan x="265" dy="32">namespace</tspan>
    </text>

    <!-- Column 1 Item 1: by bind mount or mknod -->
    <rect x="60" y="415" width="440" height="50" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="280" y="448" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">by bind mount or mknod</text>

    <!-- Column 1 Item 2: device nodes list -->
    <rect x="60" y="475" width="440" height="152" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="280" y="503" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="280" dy="0">/dev/nvidia0..N, </tspan>
      <tspan x="280" dy="25">/dev/nvidiactl, </tspan>
      <tspan x="280" dy="25">/dev/nvidia-uvm, </tspan>
      <tspan x="280" dy="25">/dev/nvidia-uvm-tools, </tspan>
      <tspan x="280" dy="25">/dev/nvidia-modeset</tspan>
    </text>

    <!-- Column 1 Item 3: MIG node -->
    <rect x="60" y="637" width="440" height="50" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="280" y="670" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">/dev/nvidia-caps/*</text>

    <!-- Column 1 Item 4: check command -->
    <rect x="60" y="697" width="440" height="65" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="280" y="725" text-anchor="middle" font-size="24" fill="#303a36">
      <tspan x="280" dy="0" font-family="monospace">ls -l /dev/nvidia* </tspan>
      <tspan x="280" dy="26" font-family="sans-serif">inside the container</tspan>
    </text>
  </g>

  <!-- Column 2: Devices cgroup -->
  <g id="col-2">
    <rect x="560" y="232" width="480" height="544" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

    <!-- Step 2 Number Circle -->
    <circle cx="605" cy="268" r="24" fill="#207448"/>
    <text x="605" y="277" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>

    <!-- Shield / Cgroups Outline Icon (56px, stroke 4, #207448) -->
    <g transform="translate(954, 242)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 28 C 48 40 28 50 28 50 C 28 50 8 40 8 28 V 14 Z"/>
      <path d="M 20 26 L 26 32 L 36 20"/>
    </g>

    <!-- Column 2 Title (30px bold) -->
    <text x="800" y="332" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="800" dy="0">Allow those devices in </tspan>
      <tspan x="800" dy="40">the devices cgroup</tspan>
    </text>

    <!-- Column 2 Check Card -->
    <rect x="580" y="475" width="440" height="135" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="800" y="534" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="800" dy="0">runtime class, CDI spec, </tspan>
      <tspan x="800" dy="36">cgroup driver match</tspan>
    </text>
  </g>

  <!-- Column 3: Driver user-space libraries -->
  <g id="col-3">
    <rect x="1080" y="232" width="480" height="544" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

    <!-- Step 3 Number Circle -->
    <circle cx="1125" cy="268" r="24" fill="#207448"/>
    <text x="1125" y="277" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>

    <!-- Library / Layers Outline Icon (56px, stroke 4, #207448) -->
    <g transform="translate(1480, 242)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="10" width="40" height="10" rx="2"/>
      <rect x="8" y="24" width="40" height="10" rx="2"/>
      <rect x="8" y="38" width="40" height="10" rx="2"/>
    </g>

    <!-- Column 3 Title (30px bold) -->
    <text x="1312" y="296" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="1312" dy="0">Mount the driver </tspan>
      <tspan x="1312" dy="32">user-space libraries </tspan>
      <tspan x="1312" dy="32">and binaries from </tspan>
      <tspan x="1312" dy="32">the host</tspan>
    </text>

    <!-- Column 3 Orange Content Card (The Single Most Important Item) -->
    <rect x="1100" y="415" width="440" height="160" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="3"/>
    <text x="1320" y="456" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1320" dy="0">libcuda.so, NVML, </tspan>
      <tspan x="1320" dy="30">nvidia-smi must match </tspan>
      <tspan x="1320" dy="30">the host kernel driver </tspan>
      <tspan x="1320" dy="30">version</tspan>
    </text>

    <!-- Column 3 Note Card -->
    <rect x="1100" y="591" width="440" height="160" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="1320" y="632" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1320" dy="0">the CUDA toolkit libraries </tspan>
      <tspan x="1320" dy="30">can live in the image, </tspan>
      <tspan x="1320" dy="30">but the driver library </tspan>
      <tspan x="1320" dy="30">cannot</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM PANEL (Automation) ==================== -->
  <rect x="40" y="802" width="1520" height="114" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="800" y="838" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="800" dy="0">Automation: NVIDIA Container Toolkit (nvidia-container-runtime, nvidia-ctk, libnvidia-container); </tspan>
    <tspan x="800" dy="28">historically an OCI prestart hook, now prefers CDI, a declarative spec file listing device nodes, </tspan>
    <tspan x="800" dy="28">mounts and environment variables, created with nvidia-ctk cdi generate</tspan>
  </text>

  <!-- ==================== SYMPTOM STRIP ==================== -->
  <rect x="40" y="942" width="740" height="136" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="410" y="977" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="410" dy="0">nvidia-smi fails with driver/library version </tspan>
    <tspan x="410" dy="26">mismatch: the container has its own libcuda </tspan>
    <tspan x="410" dy="26">not matching the host driver, or the toolkit </tspan>
    <tspan x="410" dy="26">hook is missing</tspan>
  </text>

  <rect x="820" y="942" width="740" height="136" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="1190" y="990" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1190" dy="0">GPU visible on the host but not in the </tspan>
    <tspan x="1190" dy="30">container: nodes missing, devices cgroup </tspan>
    <tspan x="1190" dy="30">denies, or runtime not configured</tspan>
  </text>

  <!-- ==================== BOTTOM BAR ==================== -->
  <rect x="40" y="1104" width="1520" height="56" rx="10" fill="#207448"/>
  <text x="800" y="1140" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Do not bake driver libraries into images; let the toolkit inject them from the host</text>
</svg>"""

with open("candidate_three_things.svg", "w") as f:
    f.write(svg_content)

print("Saved candidate_three_things.svg")
