# Part 2 deepening, chapters 16, 17, 19, 20, 21, 22 (agent E, 2026-11-13)

Scope: body sections only. Added lived situations, step-by-step "what actually happens" walkthroughs and worked examples built from numbers already in each chapter. Front matter, headings order, code blocks, Mermaid, tables, checkpoint blocks, Sources and the "untested" status row are unchanged. No commit.

Gate results (`python3 tools/rewrite_guard.py HEAD WORKTREE <file>`, `python3 tools/restore/chain_gate.py <file>`):

| Chapter | Words before | Words after | Growth | New numbers | Hard failures | Chain gate |
|---|---|---|---|---|---|---|
| 2.16 BGP in the data center | 13754 | 14856 | +8.0% | 0 | 0 | 0.0 |
| 2.17 Overlays, VXLAN, EVPN | 9606 | 10357 | +7.8% | 0 | 0 | 0.1 |
| 2.19 Queuing, QoS, ECN, PFC, DCB | 10531 | 11555 | +9.7% | 1 (0.10) | 0 | 0.0 |
| 2.20 Load balancing | 9833 | 10988 | +11.7% | 0 | 0 | 0.0 |
| 2.21 Network security | 10625 | 11820 | +11.2% | 0 | 0 | 0.0 |
| 2.22 Linux networking I | 10449 | 11492 | +10.0% | 1 (0.31, exact copy of the ss -ti sample) | 0 | 0.0 |

New number explained:
- 2.19 "0.10" in the DCQCN threshold walkthrough is derived, not new data: at 300 KB with Kmin 100 KB and Kmax 500 KB, marking is (300-100)/(500-100) x Pmax 0.20 = 0.10. This matches `evaluate_dcqcn_queue_action()` in code/part02/qos_ecn_pfc_dcqcn.py (frac x pmax, rounded to 3 places). Above Kmax the function returns 1.0, as the text says.
- 2.22 "0.31 ms" repeats `rtt:0.31/0.12` from the chapter's own ss -ti sample.

Changes made in reader text (no facts changed):
- 2.16: ADD-PATH, section 5 IGP, section 6 dragonfly (situation, valiant detour, 6.1 wiring), section 8 server routing (anycast health), section 9 traffic engineering (controller loop, oscillation and hysteresis), section 10 operations (opening situation, drain steps).
- 2.17: VXLAN frame walkthrough (VM A to VM B), EVPN pitfalls (lived situation and ECMP polarization example), RDMA-over-overlay situation, pod-call walkthrough under an overlay CNI, SR-MPLS diamond walkthrough (labels 103 and 104), common-mistakes MTU situation.
- 2.19: situation for PFC timeline, pause renewal, PFC storm and watchdog walkthrough, DCQCN threshold worked example (exercise 9 numbers), SFC/source-flow-control walkthrough, RoCE class mismatch situation, configuration chain reasoning, DCBX drift situation, design-order situation.
- 2.20: power-of-two-choices single request walkthrough, retry storm situation, drain situation, DSR one-request walkthrough, HAProxy gRPC timeouts situation and per-request path, Envoy xDS add-host walkthrough, PROXY protocol walkthrough, cloud idle-timeout situation, kube-proxy iptables probability chain, 502 troubleshooting walkthrough, pinning morning-after situation.
- 2.21: attacker path through four defence layers, VPN login steps, stateful firewall situation, backup-disk situation for encryption, SYN flood and SYN cookies walkthrough, two-vantage-point scan situation, route leak situation, rogue DHCP walkthrough, BMC handover situation, 3 a.m. OODA walkthrough, Jupyter exposure situation.
- 2.22: ip addr reading order, manual-fix-lost-on-reboot situation, ethtool dirty-optics walkthrough, counter-delta situation, latency split walkthrough, rwnd_limited situation, identical-node drift situation, bandwidth cap situation, 100G single-stream vs parallel walkthrough, top-down alert walkthrough, ss -ti line read as one story.

Facts flagged, NOT changed (need owner decision):
- 2.19 section 1 says a 64-byte packet waits about 140 times its serialization time behind a 9000-byte packet on 100 Mb/s (0.72 ms over 5.12 us, which is correct). Checkpoint 1 says the 64-byte packet takes "0.05 ms" and the wait is "14x". 0.05 ms is wrong (64 bytes at 100 Mb/s is 5.12 us), and 14x is 0.72 ms over 0.05 ms. Fix the checkpoint to match section 1.
- 2.21 checkpoint 14 says "seven classic Layer-2 LAN attacks". Exercise 4 and the section 11 table list six. Pick one count.
- 2.17 exercise 7 and checkpoint 12 are consistent with the code; no issue found.

Still thin after this pass (not yet walked through):
- 2.16: section 2 (unnumbered), section 3 (scope), section 7 (multi-tenancy levels 1 to 4), section 11 lab steps.
- 2.17: section 2 (encapsulation table prose), section 7 (complexity), section 5 SD-WAN paragraph.
- 2.20: section 2 (algorithm prose), section 3 active/passive prose, section 8 cloud prose, section 9 five-difference bullets.
- 2.21: section 9 (attack-path table prose), section 10 control plane lists, section 13 AI-cluster paragraphs (partly done).
- 2.22: section 3 persistence prose, section 5 counter tool table, section 8 bottom-up paragraph.
- Checkpoint answers, exercises and Sources were not changed (checkpoint count and form kept).

Other part-02 files in the worktree (15, 27, 28, 29) were not touched by this agent.
