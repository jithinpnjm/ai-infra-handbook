# Rework ledger W2 (Part 9: 9.5, 9.13, 9.11, 9.3)

## 9.5 GB200 and GB300 NVL72
Rewritten in one voice: why the rack (copper reach before optics power), tray anatomy, power and cooling section, crossbar math, GB200 vs GB300, new failure domains and partitions section, firmware, operations. Removed Corpus scope note, empty Concepts H2, all "In one minute" boxes, the "book itself" meta line.
- AC to DC in compute tray: fixed. Source: DGX GB300 SuperPOD RA (6 x 5.5 kW PSUs in shelf, DC connectors on tray rear). Busbar voltage 48-54 V removed (unsourced).
- "Fully liquid cooled": fixed to hybrid per RA p.5; NVIDIA product pages say fully liquid cooled; split unresolved (stated as not given).
- Power figures: 130 kW GB200 (ASP: 18x6+~20), 150 kW GB300 (1.2 MW / 8 racks, RA p.5). 120-130 range dropped.
- GB300 Grace memory 36x500 GB: fixed to 36x480 GB, 17 TB (nvidia.com GB300 NVL72 page, fetched 2026-11-12); fast memory 37.7 TB. code/part09/nvl72_rack.py and lab updated; lab 30/30 pass, check_code_files ok.
- Speedup: 30x attributed; 44x kept only as lab arithmetic.
- Failure domains: derived from wiring (inference, labelled); IMEX facts from BCM11 manual; NMX-M partition procedure and job behaviour on tray failure UNRESOLVED (stated as not covered).
- Gates: chain 0.2, 20 details, no language_audit warnings.

## 9.13 Capacity planning
Reframed for an SRE opening on "will we hit the power wall"; order: is fleet full, forecast + wall, levers, worked costs, PoC. Removed Solutions Architect framing, Volume/Lab refs, tip boxes, Concepts H2, Corpus note. All figures unchanged. Added cross-ref to 9.5 (130 kW rack vs 150 kW room). One audit warning remains (3.1% long sentences, was 1 warning before).

## 9.11 Facility deep dive
Removed leaks, tip boxes, Corpus note; fixed 120-150 kW to 130/150; 85/15 split relabelled as illustrative assumption (RA gives no percentage). Added section 5 (canonical NVL72 facility numbers: power, AC/DC, hybrid cooling, heat balance ~170 L/min, weight, pointers to 6.30/8.15/9.7/9.5). Audit warnings 3 before and after (parentheses come from Sources section).

## 9.3 HGX
Removed unsourced "15 percent discount" and "40 to 50 percent slower" (no source), "golden reference", Corpus note, tip boxes, Concepts H2. Audit warnings 1 -> 0.

## Neighbours
- 9.4 line ~226 and part-15 chapter 15.11 line ~376 still quote GB300 as ~18 TB LPDDR5X / 38.7 TB: should become 17 TB / ~37.7 TB.
- 9.7, 9.8, 8.15 should link to 9.11 section 5 for the shared rack numbers and use 130/150 kW.
