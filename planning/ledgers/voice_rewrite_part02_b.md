# Voice rewrite ledger: Part 2, chapters 16-30 (agent B)

Method: each chapter rewritten in full (prose between the metadata table and the Checkpoint section). Code blocks, Mermaid blocks, data tables, front matter, metadata table, headings (wording and order), the Checkpoint section and the Sources section were carried over byte-for-byte by a merge script. Chapters 01-15 were not touched.

Gate results for all 15 files: rewrite_guard hard failures 0, new numbers 0, lost numbers 0, chain_gate 0.0 to 0.2 (limit 1.5), no exclamation marks in prose, checkpoint count unchanged.

Earlier corrections kept: 2.16 (Mermaid figures, RFC 8950 note, advertisement-interval softening, uSID "several"), 2.17 (merged SR/SD-WAN section, VXLAN overhead), 2.18 (about an hour, nines arithmetic), 2.19 (about 140 times, non-oversubscribed 1:1, SFC "still under development", thresholds-live-where section, credit-based flow control paragraph), 2.21 (RADIUS RFC wording, AI-cluster attack table, NO_PEER left as written), 2.29 (exercise set).

## Per chapter

| Ch | Guard | Notes |
|---|---|---|
| 2.16 | pass; code spans 1 new / 1 lost (wording of a spans-in-prose reference, no command changed) | Exercises 6 split into 10 single-situation items. DPF and distoptflood still rest on the gem book only (unresolved, as in rework_W6). |
| 2.17 | pass; no span changes | Exercises 6 split into 11. |
| 2.18 | pass; lost span `untested here` (residue removed) | Figure-description sentences in ToR/MoR/EoR and rail sections turned into plain layout prose, all counts kept. Book citations removed from exercises (lost number tokens 22, 25 only appear elsewhere). |
| 2.19 | pass; no span changes | Residue count 1 is the metadata-table cell "(untested here)" in the kept head; not edited because tables stay. Exercises with a/b nesting split into 12. |
| 2.20 | pass; lost spans are the bold italic names `Round Robin`, `Least Connections` and `untested here` in exercise text | Exercises split into 10. |
| 2.21 | pass | Exercises split into 11. |
| 2.22 | pass; residue 3 to 2 | Remaining 2 are in the kept metadata table. Exercises split into 9; book chapter citations removed. |
| 2.23 | pass | Exercises split into 9; "Networking and Kubernetes, chapter 2" removed. |
| 2.24 | pass; spans 4 new / 6 lost | Differences are the removal of `untested here` and prose wording around inline spans; no command or number changed. "The book's example" attribution removed. Exercises split into 12. |
| 2.25 | pass | Exercises split into 10; book citation removed. |
| 2.26 | pass | Exercises split into 10; "Systems Performance, chapter 15" removed. |
| 2.27 | pass; spans 2 new / 4 lost | `untested here` removed; other differences are re-flowed inline spans. Exercises split into 10. |
| 2.28 | pass | Exercises split into 11; book chapter citations removed. |
| 2.29 | pass | Exercises 10, book chapter citations removed (12, 13, 14, 26, 27 only appeared in those citations). |
| 2.30 | pass | Exercises split into 9; "chapter 24" citations removed. Case-study figures unchanged (SNAT about 60,000 ports in 2.30 versus about 64k in 2.23 are two different stated approximations, left as written). |

## Unresolved or not done

- Checkpoint questions and the Sources sections were not rewritten (kept verbatim, as the guard requires the count and structure unchanged). Residual book-style phrasing there, if any, is left for the reviewer.
- Metadata table cells with "(untested here)" in 2.19 and 2.22 are in the kept head.
- Needs source: none added. No new facts.
- No numbers were changed. The known 2.23 / 2.30 SNAT port wording (about 64k vs about 60,000) was not harmonised because it would change a number.
- Not run: language_audit, check_mermaid, npm run build (only rewrite_guard and chain_gate were requested).

## Deep pass 2 (coordinator message 2026-11-13)

Method: the earlier rewrite was kept as the base. A second pass adds opening situations and plain-words explanation after section headings (inserted with planning-free text, no new numbers, no new commands, no new facts). Scripts: scratchpad ins.py (anchor = heading or paragraph line, insertion after it), run.sh (restore base, merge, insert, guard, chain gate).

Gate results after pass 2 (all 15 files): rewrite_guard hard failures 0; new numbers 0; lost numbers 0; chain_gate 0.0 to 0.2. Code blocks, tables, Mermaid, checkpoint count and Sources untouched.

| Ch | Words before pass 2 | Words after | Insertions | Notes |
|---|---|---|---|---|
| 2.16 | 12889 | 13754 | 8 | Situations for the stamp/passport ASN argument, the flap cascade, the spine black hole, the convergence test. |
| 2.17 | 8302 | 9606 | 3 | Parcel analogy for encapsulation hashing, EVPN live-migration story, Friday overlay flap. |
| 2.18 | 12169 | 12965 | 5 | Office-tower analogy, morning-after spine failure, rack-flap story, napkin-sketch exercise. |
| 2.19 | 9623 | 10531 | 3 | Home streaming example for QoS, PFC chain-of-cars, congestion flowchart story. |
| 2.20 | 9142 | 9833 | 3 | Single busy server, backend that answers checks but times out, inference replica imbalance. |
| 2.21 | 9748 | 10625 | 3 | Locked-office threat model, first SSH login trust prompt, 3 a.m. OODA alert. |
| 2.22 | 9964 | 10449 | 3 | Lost interface mid-training, sockets as conversation handles, the hundred-numbers meeting. |
| 2.23 | 8349 | 8945 | 4 | Remote firewall lockout, night-time conntrack exhaustion, NAT changes apply to new flows only, packet vanishing story. |
| 2.24 | 9191 | 9935 | 4 | Two front doors for policy routing, large-download MTU hang, 100G link at 25G, six-settings Monday. |
| 2.25 | 7888 | 8344 | 3 | Hand-built container network, GPU job on the overlay, pod A cannot reach pod B. |
| 2.26 | 8864 | 9156 | 3 | Capture as a camera, sorting office sampling, intermittent reset. |
| 2.27 | 5934 | 6594 | 3 | Lab 1 opening, lab 3 as a safe copy, lab 6 failure during a busy hour. |
| 2.28 | 9711 | 10317 | 3 | Column-shift script bug, typed MTU rejected mid-rollout, controller down for an hour. |
| 2.29 | 9238 | 9602 | 3 | Thirty leaves by hand, single typo to every switch, three places to run automation. |
| 2.30 | 8717 | 9031 | 1 | Half-split opening only. |

Honest status: this pass is partial. Growth is 3 to 20 percent, not the Kimi-scale expansion the coordinator asked for. Chapter 2.30 received only one insertion. Still needed: more step-by-step walkthroughs, worked mini-examples and "why" paragraphs inside the body sections of 2.18 and 2.23 to 2.30, and a second opening situation for most H2 sections. No commit was made.

Unresolved (carried from pass 1): the RINA and OSI wording in 2.30 is kept from the source; the 2.23 and 2.30 case-study numbers were not re-verified against a primary source.

## Deep pass 3 (body expansion, chapters 2.18, 2.23, 2.24, 2.25)

Method: insertions after body headings and numbered prose lines, in files scratchpad 18/23/24/25 .ins2.md (ins.py now merges all ins*.md files). Each insertion adds a lived situation or a step-by-step walkthrough of existing content. No new numbers, commands or facts. Code blocks, tables, Mermaid, checkpoints and Sources untouched.

Gate results: rewrite_guard 0 hard failures; new numbers 0 (one incidental "101" in 2.24 was reworded to a word and the chapter rebuilt); chain_gate passes.

| Ch | Words before pass 3 | Words after | Insertions added |
|---|---|---|---|
| 2.18 | 12965 | 14559 | 15 new (topologies, leaf-spine, sizing walkthrough, five-stage, ROD, rail-only, RUD, cable layout, scheduled cells, dragonfly, multi-planar, NIC spraying, resilience, measures, common mistakes) |
| 2.23 | 8945 | 9898 | 11 new (iptables checkpoints, nftables, gateway ruleset, conntrack states, inspecting, UDP/DNS race, container hosts, firewall strategies, rule order, performance, mistakes) |
| 2.24 | 9935 | 11076 | 14 new (asymmetric routing walkthrough, persistence, fwmark, VRF, bonding, rings, RSS path, offloads, budget, pacing, beyond kernel, scenarios, mistakes, interview) |
| 2.25 | 8344 | 9295 | 12 new (veth, Docker model, CNI life cycle, plugin choices, cross-node walk, service path, NCCL interface, overlay costs, topology alignment, debugging, mistakes, interview) |

Honest status: pass 3 adds lived situations and walkthroughs at most body headings, but these are still insertions. Some sections (for example the lab and exercise blocks, and several short H3 headings in 2.23 and 2.25) received none. Growth is about 10 to 20 percent, so this is not yet the full Part 1 body rewrite. No commit was made.
