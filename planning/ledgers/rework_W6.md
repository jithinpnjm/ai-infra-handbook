# Rework ledger W6 (chapters 2.14, 2.16, 2.17, 2.21, 2.32)

Gates run on all five: chain_gate under 1.5, summary counts unchanged (20 each), no exclamation marks, language_audit no rows, no LaTeX. Code blocks unchanged (no code/ edits). 2.32 was already partly edited by an earlier worker; its subnet sizing text was kept.

## 2.14
Changed: RIP, EIGRP and the Spanning Tree section compressed to two short sections and renumbered; EIGRP formula moved to a text block; book citations removed from exercises 1-2 and checkpoint 1; "six parameters" question reworded (it listed seven); inline "untested" tags replaced by status sentences.
Watch-list: no rows for this chapter in Opus section 6. Spot-checked timers (OSPF MaxAge 3600, refresh 1800; IS-IS lifetime 1200; EIGRP hello 5/hold 15) against RFCs 2328, 1195, 7868: already correct.

## 2.16
Changed: all four figure-transcription sections (5.1, 6.1, 6.2, 9.1, which cited Figure 8-15 to 8-30 and "the book") replaced by Mermaid diagrams and plain prose; book chapter references removed from exercises and checkpoints; unfinished lab step 4 sentence fixed; "64 switches of 800G" corrected to 64-port 800G switches.
Verdicts: advertisement-interval 0 claim softened (platform default varies; RFC 4271 suggests 30 s) = fixed; "turn off bgp bestpath compare-routerid" removed, could not source = removed; uSID "up to six" softened to "several" = fixed; RFC 8950 obsoletes 5549, capability code 5, RFC 9350/9502/9692 numbers = already correct.
Unresolved: DPF and distoptflood drafts and the 2,500-node figure rest on the gem book only.

## 2.17
Changed: segment routing and SD-WAN sections merged into one short section with a Mermaid diamond example (book A-K example and label stack removed); sections renumbered; "platypus" aside deleted; VXLAN overhead cell simplified; book chapter citations removed; uSID count softened.
Verdicts: VXLAN 50 bytes, GRE 24, WireGuard 60/80, EVPN route types, RFC 9136 = already correct.

## 2.21
Changed: section 9 (dated How Linux Works vulnerability text, Why Linux draws attackers, Security resources, book recommendations) replaced by an AI-cluster attack-path table with controls; SSH "falls short" paragraph rewritten without book names; book citations removed from checkpoints and exercises; RADIUS RFC fixed to 2865 and 2866 = fixed.
Verdicts: RTBH 65535:666, TACACS+ TCP 49, P_Key membership bit = already correct.
Unresolved: NO_PEER naming (RFC 3765 calls it NOPEER); kept as the source wrote it.

## 2.32
Changed: AWS and Azure primer replaced with a three-cloud mapping table; "1500 on HA VPN? verify" residue removed; MTU facts fixed against Google docs (default 1,460, range 1,300 to 8,896, HA VPN no jumbo); GPU VM text corrected and extended with A3 High, A3 Mega, A3 Ultra and A4 bandwidth and NIC counts (fetched 2026-11-12); book citations removed.
Unresolved: Interconnect attachment MTU values and exact Cloud VPN payload MTU left to vendor docs.

## Neighbouring chapters
2.14 refers to 2.16 for RIFT: correct. 2.17 and 2.16 both explain SRv6 SIDs, overlap acceptable. 2.21 section 7 SSH is long; could be trimmed later.
