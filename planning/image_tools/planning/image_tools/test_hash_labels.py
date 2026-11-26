import re
import xml.etree.ElementTree as ET

expected_labels = [
    "When a backend leaves: modulo hashing versus consistent hashing",
    "Hash(key) mod N",
    "N backends",
    "a row of keys assigned",
    "one backend removed, N becomes N minus 1",
    "most keys remapped",
    "Consistent hashing (ring, rendezvous, jump hash)",
    "keys and backends mapped on a ring or score space",
    "one backend removed",
    "only the keys on that backend move",
    "about 1/N of keys",
    "Maglev hashing: a lookup table built from backend preference permutations; near-uniform load with minimal disruption; used by L4 LBs behind ECMP (Google Maglev, Meta Katran); table rebuild cost, small disruption on change",
    "Why it matters in three places",
    "cache locality and sticky sessions",
    "L4 tier behind ECMP: any node computes the same backend for the same 5-tuple without synchronised state",
    "LLM prefix cache: consistent hashing on a session ID or prompt-prefix hash, with bounded loads that spill to the next replica when one exceeds its share",
    "lab check: rendezvous (HRW) hashing moves about 1/N of keys; bounded-load spillover",
    "Hash affinity accepts uneven load, so plan for reshuffling"
]

print("Expected labels count:", len(expected_labels))
for i, l in enumerate(expected_labels, 1):
    print(f"{i:2d}. {l}")
