# Voice audit report 3 (part-02-networking, part-16-mlops-llmops)

Strict grading. Overall: Part 16 prose is plainer and more story-led than Part 2. Part 2 has many term-stack paragraphs, backticks on ordinary words, and numbered lab lists packed with code spans. No 5s given.

| file | grade | main problem (one phrase) |
|---|---|---|
| part-02/01-what-happens-when-you-curl-a-url | 3 | term-dense reference text; "Step 1: ... Step 2:" fragments |
| part-02/02-how-networks-work-layers | 4 | minor stiffness ("Stretch makes this concrete") |
| part-02/03-ethernet-and-l2-frames | 3 | counter and cause lists stacked; numbers stacked |
| part-02/04-ip-addressing-subnetting | 4 | formula-ish sentences, otherwise clear worked example |
| part-02/05-routing-on-a-host | 4 | stock "fixes below apply"; one dense paragraph |
| part-02/06-tcp-in-depth | 3 | lab questions are code-span and number dumps |
| part-02/07-udp-icmp-and-diagnostic-tools | 4 | tool-name lists, symptom list in one sentence |
| part-02/08-dns-in-depth | 3 | option and file-name stacks; backticks on ordinary words |
| part-02/09-dhcp-nat-and-pat | 3 | mistake lists as run-on sentences; tool dump |
| part-02/10-http-tls-and-pki-basics | 3 | name dumps (CAs, tools); clipped "Expiry is the next group" |
| part-02/11-vlans-trunking-and-spanning-tree | 3 | very long single-paragraph L2 vs L3 explanation |
| part-02/12-link-aggregation-lacp-and-mlag | 4 | good concrete opening; slight terseness |
| part-02/13-ip-routing-static-dynamic | 3 | 150-word paragraph on proactive learning, safeguard stack |
| part-02/14-ospf-and-is-is | 3 | "too/that" openings with no referent (RIP unnamed) |
| part-02/15-bgp-fundamentals | 4 | OPEN-message field list is dense |
| part-02/16-bgp-in-the-data-center | 3 | verification paragraph is a command checklist |
| part-02/17-overlays-vxlan-and-evpn | 3 | abstract "must do three things"; acronym stacking |
| part-02/18-data-center-topologies | 3 | stray meta line "The source describes this as about an hour" |
| part-02/19-queuing-qos-ecn-pfc-and-dcb | 3 | parameter-list dumps |
| part-02/20-load-balancing-l4-l7 | 3 | question list, tool-name lists |
| part-02/21-network-security-firewalls | 3 | generic advice; "two main types of vulnerability" reads like source residue |
| part-02/22-linux-networking-inspecting-state | 3 | tool list and number run in one paragraph |
| part-02/23-linux-networking-netfilter | 4 | clear, concrete; mild redundancy |
| part-02/24-linux-networking-policy-routing | 3 | dense tuning terms (qdisc, DMA, zerocopy) |
| part-02/25-linux-networking-namespaces | 4 | good definitions; plain |
| part-02/26-packet-capture-from-scratch | 3 | Wireshark menu paragraph is one giant list sentence |
| part-02/27-lab-build-network-topologies | 3 | lab steps with inline commands and chained actions |
| part-02/28-network-automation-fundamentals | 3 | format-name lists; abstract CAP/subsidiarity talk |
| part-02/29-network-automation-in-practice | 2 | abstract claims, list dumps, "you have not looked hard enough" |
| part-02/30-network-troubleshooting-method | 4 | clear method; slightly repetitive |
| part-02/31-network-monitoring-and-telemetry | 3 | metric-name dump paragraph |
| part-02/32-cloud-networking-vpc | 3 | numbered security item is a stacked term list |
| part-16/01-mlops-foundations-and-lifecycle | 3 | "untested" lab note, numbered items same shape |
| part-16/02-data-versioning-and-experiment-tracking | 3 | list-heavy; repeated "Both get..." shapes |
| part-16/03-data-pipelines-and-feature-stores | 3 | book-chapter citations in place of explanation |
| part-16/04-pipeline-orchestration | 4 | good scenario openings |
| part-16/05-distributed-compute-for-ml | 4 | concrete; minor jargon (gang-schedules) |
| part-16/06-model-registry-ci-cd-and-gitops | 4 | good "auditor asks" opening; "The diagram shows" is flat |
| part-16/07-model-serving-platforms | 3 | leaked draft-history note ("Earlier drafts ... wrong") |
| part-16/08-llmops-rag-vector-databases-agents | 3 | clipped cross-reference sentences; "Fix:" fragment |
| part-16/09-llm-evaluation-and-guardrails | 3 | six exercises with the same "Solution sketch" shape |
| part-16/10-monitoring-drift-and-continual-learning | 3 | repeated exercise template; mixed tense ("You build") |
| part-16/11-cloud-mlops-platforms | 4 | readable comparison prose |
| part-16/12-nvidia-enterprise-stack | 4 | concrete product-team story |
| part-16/13-governance-privacy-and-compliance | 4 | good erasure scenario |
| part-16/14-platform-design-multi-tenant | 4 | clear two-teams picture |
| part-16/15-lab-end-to-end-mlops-on-gke | 4 | plain; code-intro sentences repeat shape |

## Worst 15 files, one example each

1. **29-network-automation-in-practice.** "If you have not found the trade-off yet, you have not looked hard enough." Human: drop the slogan; give one concrete example, such as a bad template pushed to 200 switches at once.
2. **31-network-monitoring-and-telemetry.** Paragraph lists about 20 `node_*` metric names in a row. Human: name the three metrics you check first and why, and move the rest to a table.
3. **18-data-center-topologies.** "The source describes this as about an hour." Human: delete this leftover editing note; state the figure once.
4. **13-ip-routing.** "Proactive learning does the opposite." Human: open with a failure ("one dropped update causes a loop"), then split the safeguards into short paragraphs or a table.
5. **16-07-model-serving.** "Earlier drafts of this section had the canary field layout wrong." Human: remove draft history; say only "the layout above matches the KServe repository".
6. **14-ospf-and-is-is.** "Choosing a route is simple too, and you can check it by hand." Human: name RIP and say "In RIP, each router..." so the paragraph stands alone.
7. **06-tcp-in-depth.** Exercise 3 stacks `compute_jacobson_rto_ms()`, `SRTT`, `RTTVAR`, `RFC 2018` and `200 ms` in one item. Human: one task per item, with numbers in a small table.
8. **32-cloud-networking.** "Security in the cloud has several parts." Human: pick the one risk a reader will hit first, such as traffic leaving over the public Internet, and explain it.
9. **16-09-llm-evaluation.** "The system prompt is the most effective jailbreak defence you have." Suspicious: overstated, and classifiers and filters are usually seen as stronger. Human: "A system prompt helps, but a determined user can talk around it."
10. **16-10-monitoring-drift.** "You build a Grafana dashboard that shows drift score per feature, prediction drift per class..." Human: imperative voice, two metrics named, the rest pointed to a table.
11. **03-ethernet-and-l2-frames.** Counter paragraph chains `carrier_changes`, `rx_crc_errors`, `rx_discards` and `rx_pause`. Human: take one symptom, a flapping link, and walk through the one counter that proves it.
12. **26-packet-capture.** Wireshark paragraph runs about 170 words through menus, `SSLKEYLOGFILE` and coloring rules. Human: split into short steps, one task each.
13. **19-queuing-qos-ecn-pfc.** NIC parameters paragraph lists about ten settings in one sentence. Human: say why misconfigured NIC parameters hurt, give one example, and tabulate the rest.
14. **21-network-security.** "There are two main types of vulnerability: direct attacks and cleartext password sniffing." Reads like source residue and is too broad. Human: begin with a concrete incident, such as an exposed admin port.
15. **08-dns-in-depth.** "`/etc/resolv.conf` holds `nameserver` lines, of which up to 3 are used." Human: start with a pod that cannot resolve a name, then explain the file; put options in a table.

## Other flags

Suspicious claims, note only:
- 02-32: "`/20` node subnet plus `/14` pod range gives 1,024 maximum nodes and 4,096 Services." The numbers do not obviously follow from those two ranges; check against the GKE docs.
- 02-18: "The source describes this as about an hour" contradicts 52.6 min. Check the source figure.
- 16-09: system-prompt-as-best-jailbreak-defence claim (above).
- 02-23: the `sleep 60 && nft flush ruleset &` safety timer opens the host firewall completely when it fires. Worth a caveat.
- 02-27: GRE/IPIP hash-policy claim is plausible but needs lab verification.

Semicolon chain: 16-11 ("...managed services; you do not operate a GKE cluster...").

Parenthesis stacking: 02-06 lab items, 02-08, 02-26 (`Edit → Preferences...`), 02-27.

Backticks on ordinary words or protocol names: 02-06 (`CUBIC`, `ECN`, `QUIC`, `SACK`), 02-26 (`tcpdump`), 02-25 (`ADD`, `DEL`).

Undefined acronyms at first use: PBR (02-02), NLRI (02-13), CSNP and PSNP (02-13), VOQ (02-18), IFA (02-31), RACK and CUBIC (02-06), FIB (02-01), CNM (02-25).
