import xml.etree.ElementTree as ET
import re
import pathlib

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1120" viewBox="0 0 1600 1120">
  <title>Four limits, four different fences</title>
  <desc>Rate limiting fences for AI inference: requests per second, tokens per second, concurrent streams, daily quota, token bucket mechanism, and incident analysis.</desc>

  <!-- Background -->
  <rect width="1600" height="1120" fill="#f5f8f5" />

  <!-- Diagram Title -->
  <text x="800" y="80" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle" font-family="sans-serif">Four limits, four different fences</text>

  <!-- 4 Fences in a row -->
  <!-- Fence 1: Requests per second -->
  <rect x="40" y="130" width="350" height="420" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Icon 1: Rate meter / Clock -->
  <circle cx="215" cy="182" r="24" stroke="#207448" stroke-width="4" fill="none" />
  <line x1="215" y1="182" x2="228" y2="170" stroke="#207448" stroke-width="4" stroke-linecap="round" />
  <line x1="215" y1="162" x2="215" y2="168" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="235" y1="182" x2="229" y2="182" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="215" y1="202" x2="215" y2="196" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="195" y1="182" x2="201" y2="182" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <text x="215" y="246" font-size="24" fill="#303a36" text-anchor="middle" font-family="sans-serif">
    <tspan x="215" dy="0" font-size="30" font-weight="bold">Requests</tspan>
    <tspan x="215" dy="36" font-size="30" font-weight="bold">per second:</tspan>
    <tspan x="215" dy="42">protects gateway,</tspan>
    <tspan x="215" dy="32">tokenizer, scheduler;</tspan>
    <tspan x="215" dy="40">unit requests;</tspan>
    <tspan x="215" dy="40">missing:</tspan>
    <tspan x="215" dy="32">connection floods</tspan>
  </text>

  <!-- Fence 2: Tokens per second -->
  <rect x="430" y="130" width="350" height="420" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Icon 2: GPU compute chip -->
  <rect x="587" y="164" width="36" height="36" rx="4" stroke="#207448" stroke-width="4" fill="none" />
  <rect x="597" y="174" width="16" height="16" rx="2" stroke="#207448" stroke-width="2" fill="none" />
  <line x1="595" y1="158" x2="595" y2="164" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="615" y1="158" x2="615" y2="164" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="595" y1="200" x2="595" y2="206" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="615" y1="200" x2="615" y2="206" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="581" y1="174" x2="587" y2="174" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="581" y1="190" x2="587" y2="190" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="623" y1="174" x2="629" y2="174" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="623" y1="190" x2="629" y2="190" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <text x="605" y="246" font-size="24" fill="#303a36" text-anchor="middle" font-family="sans-serif">
    <tspan x="605" dy="0" font-size="30" font-weight="bold">Tokens</tspan>
    <tspan x="605" dy="36" font-size="30" font-weight="bold">per second:</tspan>
    <tspan x="605" dy="38">protects GPU compute</tspan>
    <tspan x="605" dy="32">and KV cache;</tspan>
    <tspan x="605" dy="38">unit prompt plus</tspan>
    <tspan x="605" dy="32">output tokens;</tspan>
    <tspan x="605" dy="38">missing: one tenant</tspan>
    <tspan x="605" dy="32">starves the rest</tspan>
  </text>

  <!-- Fence 3: Concurrent streams -->
  <rect x="820" y="130" width="350" height="420" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Icon 3: Concurrent streams -->
  <path d="M 978 156 L 968 156 L 968 208 L 978 208" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" />
  <path d="M 1012 156 L 1022 156 L 1022 208 L 1012 208" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" />
  <path d="M 974 166 L 1016 166" stroke="#207448" stroke-width="4" stroke-linecap="round" />
  <circle cx="974" cy="166" r="3" fill="#207448" />
  <circle cx="1016" cy="166" r="3" fill="#207448" />
  <path d="M 974 182 L 1016 182" stroke="#207448" stroke-width="4" stroke-linecap="round" />
  <circle cx="974" cy="182" r="3" fill="#207448" />
  <circle cx="1016" cy="182" r="3" fill="#207448" />
  <path d="M 974 198 L 1016 198" stroke="#207448" stroke-width="4" stroke-linecap="round" />
  <circle cx="974" cy="198" r="3" fill="#207448" />
  <circle cx="1016" cy="198" r="3" fill="#207448" />
  <text x="995" y="246" font-size="24" fill="#303a36" text-anchor="middle" font-family="sans-serif">
    <tspan x="995" dy="0" font-size="30" font-weight="bold">Concurrent</tspan>
    <tspan x="995" dy="36" font-size="30" font-weight="bold">streams:</tspan>
    <tspan x="995" dy="38">protects open</tspan>
    <tspan x="995" dy="32">connections and</tspan>
    <tspan x="995" dy="32">decode slots;</tspan>
    <tspan x="995" dy="38">unit streams;</tspan>
    <tspan x="995" dy="38">missing: decode</tspan>
    <tspan x="995" dy="32">queues overrun</tspan>
  </text>

  <!-- Fence 4: Daily or monthly quota -->
  <rect x="1210" y="130" width="350" height="420" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Icon 4: Calendar / Ledger quota -->
  <rect x="1363" y="160" width="44" height="44" rx="6" stroke="#207448" stroke-width="4" fill="none" />
  <line x1="1363" y1="174" x2="1407" y2="174" stroke="#207448" stroke-width="3" />
  <line x1="1374" y1="154" x2="1374" y2="162" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="1396" y1="154" x2="1396" y2="162" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="1374" y1="186" x2="1380" y2="186" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="1390" y1="186" x2="1396" y2="186" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="1374" y1="196" x2="1380" y2="196" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="1390" y1="196" x2="1396" y2="196" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <text x="1385" y="246" font-size="24" fill="#303a36" text-anchor="middle" font-family="sans-serif">
    <tspan x="1385" dy="0" font-size="30" font-weight="bold">Daily or</tspan>
    <tspan x="1385" dy="36" font-size="30" font-weight="bold">monthly quota:</tspan>
    <tspan x="1385" dy="42">protects the bill</tspan>
    <tspan x="1385" dy="32">and the contract;</tspan>
    <tspan x="1385" dy="40">unit tokens;</tspan>
    <tspan x="1385" dy="40">missing:</tspan>
    <tspan x="1385" dy="32">surprise cost</tspan>
  </text>

  <!-- Mechanism strip: token bucket -->
  <rect x="40" y="595" width="1520" height="290" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Icon: Token bucket / Jar -->
  <path d="M 82 720 L 87 760 Q 88 768 100 768 Q 112 768 113 760 L 118 720 Z" stroke="#207448" stroke-width="4" fill="none" stroke-linejoin="round" />
  <ellipse cx="100" cy="720" rx="18" ry="6" stroke="#207448" stroke-width="4" fill="none" />
  <path d="M 85 738 Q 100 744 115 738" stroke="#207448" stroke-width="3" fill="none" />
  <circle cx="100" cy="750" r="4" fill="#207448" />
  <text x="150" y="642" font-size="24" fill="#303a36" font-family="sans-serif">
    <tspan x="150" dy="0">token bucket: a jar that starts full, is spent per request, refills slowly,</tspan>
    <tspan x="150" dy="38">and allows bursts up to bucket size; charge prompt tokens plus max output</tspan>
    <tspan x="150" dy="38">tokens at admission, refund the unused at the end; reject at once what can</tspan>
    <tspan x="150" dy="38">never fit; a refused request must not burn a request slot; distributed</tspan>
    <tspan x="150" dy="38">choice: shared store such as Redis is exact but adds a hop and a</tspan>
    <tspan x="150" dy="38">dependency, local buckets are fast and slightly loose</tspan>
  </text>

  <!-- Incident callout -->
  <rect x="40" y="930" width="1520" height="150" rx="12" fill="#e8f1ea" stroke="#db8129" stroke-width="3" />
  <!-- Icon: Alert triangle in orange -->
  <path d="M 100 975 L 126 1025 L 74 1025 Z" stroke="#db8129" stroke-width="4" fill="none" stroke-linejoin="round" />
  <line x1="100" y1="988" x2="100" y2="1008" stroke="#db8129" stroke-width="4" stroke-linecap="round" />
  <circle cx="100" cy="1016" r="2.5" fill="#db8129" />
  <text x="150" y="990" font-size="24" fill="#303a36" font-family="sans-serif">
    <tspan x="150" dy="0">ten requests with 8,000 prompt tokens and a large max output made every</tspan>
    <tspan x="150" dy="42">other tenant TTFT double while a requests-per-minute limit saw nothing wrong</tspan>
  </text>
</svg>'''

with open("planning/image_tools/candidate_fences.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print("Saved candidate_fences.svg successfully!")
