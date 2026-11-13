# Voice rewrite, Part 4 chapters 16-21 (ledger)

## Status
- 4.16 (16-ansible-for-containers-cloud-and-network-devices.md): rewritten. Guard: 0 hard failures, words 7805 -> ~9760 (+25%). Chain gate passes. Lost numbers restored (study items 21-30). Removed "untested here" markers; body says commands not run on live hardware above the lab. Removed garbled "WISB == WIRI" fragment from Exercise 9 answer (Q10) as non-fact residue. NVUE code comment already reads "uses RFC 5549 (2.16)"; no "RFC 7938 style" wording found in part04 code.
- 4.17 (17-ansible-for-gpu-nodes-and-clusters.md): NOT rewritten. Read lines 1-605 only.
- 4.18, 4.19, 4.20, 4.21: NOT started.

## Open items
- 4.17 GPU tuning table: "When you need it" cells are short; plausibility check still to do (persistence, clocks, power, ECC/compute mode, MIG rows look plausible; flag B200 MIG profile list for source check).
- 4.17 Section 5 table says "PCIe link width and speed (x16 Gen5)"; check against sources.
- Ch16 Sources section references original study items 21-30 by number; keep.
