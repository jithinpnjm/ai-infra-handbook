# Voice rewrite, Part 9 chapters 9.7 to 9.9 (run c)

Scope: `docs/part-09-nvidia-systems/07-dgx-b200-superpod-data-center-design-power-cooling-cabling-and-layout.md`, `08-gb300-superpod-reference-architecture.md`, `09-compute-storage-in-band-and-out-of-band-networks-in-a-superpod.md`. Front matter, headings, tables, code blocks, Mermaid, checkpoints (20 each) and the Sources and review notes are unchanged (the locked tail was spliced from HEAD). EXTERNAL_EDITS.md not edited, per instruction.

## Word counts (whole file, `wc -w`)

| File | Before | After | Growth |
|---|---|---|---|
| 07 DGX B200 SuperPOD data center design | 6931 | 9648 | +39.2% |
| 08 GB300 SuperPOD reference architecture | 6839 | 9493 | +38.8% |
| 09 Compute, storage, in-band and OOB networks | 7629 | 9716 | +27.4% |

Body only (before the Checkpoint questions): 07 5013 to about 7730, 08 4941 to about 7575, 09 about 5711 to about 7798.

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three. New numbers: 0 on all three (07 "4.1" and "80" and 08 "6.1" were reworded to remove them). Lost numbers: 0. Lost code spans: 0.
- `python3 tools/restore/chain_gate.py <file>`: 07 = 0.2, 08 = 0.1, 09 = 0.0 (target <= 0.2 met).
- Span check (inline backtick spans, HEAD vs worktree, code blocks excluded): `{}` on all three. One span lost in the first pass of 07 (`< 90%` in Exercise 4) was restored.
- Structural check on all three: code blocks identical (8, 9, 9), table rows identical (63, 72, 57), headings identical, checkpoints 20 / 20 / 20, exercises 6 / 6 / 6, no exclamation marks, no raw `<` or `{` outside code.
- Mermaid: `node tools/check_mermaid.mjs` = checked 776 diagrams, 0 failed. Mermaid blocks byte-identical to HEAD.
- `npm run build`: not run (the task said no npm build).
- Honest status: one "not run" or "not verified" sentence in each body (07 Commands: "were not run against a live vendor rPDU"; 08 Lab: "have not been run against live switches, PDUs or storage arrays"; 09 Commands: "have not been run on live SuperPOD switches or nodes"). The locked Sources tail also says "Not verified on live hardware" in each.

## What changed in every chapter

- Opening situations: every top-level section now opens with a scene (a crew with cooling on order, an electrician's rack, an on-call engineer, a storage lead). Subsections 2.1, 2.2, 3.1, 3.2, 4.1, 4.2 and 5.1 and 5.2 in 09 and 2.1, 2.2, 3.2 and 4.2 in 08 gained a situation sentence before the existing text.
- Prerequisites and outcomes: the "you will be able to" lists were replaced with a plain paragraph of what the chapter walks through. The bold "Prerequisites:" and "Outcomes:" labels were removed.
- Bold: at most one bold idea per section. The bold lead-ins in 09 section 2.1 (two of three), section 3.2 (four numbered items) and section 4.2 (three bullets) were removed. Bold in table cells is untouched.
- Bullets and numbered items: question-and-answer form where the item is a rule (09 section 5 and 3.2; 08 exercises not changed).
- Exercises: same count in each chapter (6). Multi-part exercises were split into short single-question sentences. Commands and facts unchanged. In 07, Exercise 4 keeps `< 90%` as a code span.
- Lab: "This chapter's self-checking Python model" became "The Python model in ..." in all three. The four-suite and PASS-line explanations were expanded. The expected-output blocks are byte-identical.
- Residue removed from body prose: "this chapter's own" in 07 section 2.2 and 5.1 and in 08 section 3.1 and 4.1 (replaced by "a derivation made for this lesson" or "a reconstruction for this lesson"), "the chapter's own explanation" (08 4.1), "the source does not say" (07 2.2, replaced by "the reference does not say"), "as proven in Chapter 9.8" (09 3.2, replaced by "as shown in chapter 9.8"), "(untested here)" (09 Commands).
- Facts unchanged: all numbers, units, part numbers, port counts, tray counts, GPU counts, power kW and MW, CFM values, dB values, altitude and temperature limits, cable limits and the GB300 memory figure (288 GB HBM3e) are exactly as in HEAD. Explanations only explain what a number means.
- Gem book titles: unchanged. No abbreviations introduced. The body of 09 does not attribute claims to *AI Data Center Network Design and Technologies*; that attribution lives only in the locked Sources table.

## Needs source (general explanations added in prose; facts stay exact, a reviewer should check these)

07 DGX B200 SuperPOD data center design:
- PDU defined as the metered rack power strip. Splitting cords across PDUs described as good practice for ordinary servers.
- "Nearly all of the power a server draws leaves the chassis as heat."
- Three-phase power described as three offset conductors that deliver more power than single-phase at the same wire size.
- Derating described as not loading a breaker to its full rating for long periods.
- Power factor described as the share of apparent power that does useful work.
- Stranded capacity and the reason a third node is not counted: the "whole nodes must split evenly" reading is marked as a guess in the text.
- ASHRAE described as the professional body that publishes IT environment classes; dew point defined as the condensation temperature.
- MERV expanded as Minimum Efficiency Reporting Value; ISO 14644-1 described as the particle-count standard for cleanrooms.
- "Hardware is best unboxed outside the cold aisle" (original text said it was "why", now a recommendation; needs source).
- CFD, plenum, anemometer, backpressure, throttling, and CRAC (computer room air conditioner) defined.
- UPS described as the battery-backed unit; STS described as a device that moves load between sources.
- N+1 described as one extra supply as a spare.
- Bend radius, DAC expansion (direct attach copper), passive DAC described as no active electronics, AOC described as optics built in.
- Hop latency; link flap; patch panel attenuation as a reason to avoid patch panels (original claim, explanation only).
- REST API, locking receptacles, metering, Redfish as a standard web interface, `-k` flag described as skipping certificate checks, `jq` described as a JSON formatter.
- Commissioning described as the stage before power-on.

08 GB300 SuperPOD reference architecture:
- Reference architecture described as a design the vendor has worked out and tested.
- Two-layer fabric described as leaf and spine layers with no third tier.
- NVLink described as the in-rack GPU link and InfiniBand as the between-rack link; synchronous collective workload described.
- Thermal design power described as the heat and power budget used for planning.
- Tier 3, TIA-942-B Rated 3, EN 50600 Class 3 described as three published data center standards.
- Bill of materials and NIC defined; ASIC and NVSwitch ASIC defined; BMC described as a small management computer that works when the main system is off.
- Superchip described as a CPU and GPU packaged together; RAID 0 described as striping with no redundancy.
- BlueField-3 described as a DPU with its own processor.
- SHARP described as combining partial results inside the switch.
- Magnum IO, NCCL, Slurm, Mission Control's relation to Base Command Manager (BCM) explained in one line each.
- Rank described as one process per GPU in a distributed job; telemetry and correlation described.
- Grace aarch64 and GPUDirect Storage described in one line each.
- "1:3 blocking is acceptable for compute traffic, which is bursty" (the reason is ours, not the reference's; needs source).
- Run:ai tenant quota described as a per-group GPU limit; Kubernetes described as the system that manages containers across machines.
- DR1 described as a short-reach single-mode optic standard; VLAN, Layer-2 reachability, BACnet and Modbus described as building-control protocols that often lack authentication.
- Route filtering and firewall policy explained as limits on announced routes and inbound traffic.
- Storage RAID, reconciliation loop, PXE, NOC and SOC expanded.
- Host-Based Networking described as moving routing decisions onto the DPU (roadmap text in the original; mechanism is our wording).
- The 1-SU spine count (4) is a derived value, marked in the table cell (table is locked; see unresolved).

09 Compute, storage, in-band and out-of-band networks:
- Heartbeat, tensor, NCCL (the NVIDIA collective library), IPMI and Redfish as management interfaces, NVOS as the switch operating system.
- Rail defined as the set of NICs in the same position across servers; NIC defined; NVSwitch defined as the chip that connects GPUs inside a server.
- Rail-only and rail-unified trade-offs described as fewer switches versus blast radius; deterministic path forwarding described as fixed paths.
- Clos described as a multi-stage fabric where every leaf reaches every spine; three-stage Clos as the two-tier leaf-spine fabric.
- Oversubscription described as the ratio of host-facing to uplink capacity; head-of-line blocking described in one sentence.
- Active optical cable reach described as the rated distance limit.
- Ephemeral port, five-tuple, entropy (header variety), flowlet (short burst inside a flow), ECMP (equal-cost multipath), in-cast, microburst described in one line each.
- Random Early Detection described as early marking before a queue fills; Queue Pair described as the RDMA endpoint pair.
- Lossless described as pause instead of drop; PFC watchdog described as a timer on a stuck queue.
- VLAN, subnet, LACP (bonding protocol), buffer headroom, ingress endpoint, border uplink, eBGP described as the external routing protocol.
- PXE described as a network boot method; control-plane services described as the programs that run the cluster.
- VXLAN described as wrapping one virtual network inside another; VTEP described as the tunnel endpoint; broadcast domain described as devices that hear each other's broadcasts.
- Heartbeat and "ping answers only shows one port is alive" (explanation of the failure mode).
- Cumulus Linux described as the switch operating system on the Spectrum-4 switches; BGP peering state described as whether routing sessions are up.
- "Bonding would mix the two kinds of traffic on the same path" (explanation).

## Unresolved

1. Locked table cells still carry drafting residue because tables are fixed by the rule and were not edited: 07 section 2.1 table cell "the deck's FAQ"; 08 section 3.2 table cell "(chapter's own value; the reference architecture table starts at 2 units)".
2. Locked Sources and review notes (all three) still say "My own choices and inferences", "Run here", "Not verified on live hardware", and "the book" or "the deck" as attribution. These are outside the body and were kept as instructed.
3. 08: the GB300 memory figure (288 GB HBM3e) was not changed, per instruction. It is an open factual issue.
4. 09 is at +27.4%, close to the +25% floor. It is inside the band, but a reviewer could add one more worked example if the owner wants margin.
5. 07 Exercises: the original exercise 1 asked for "two rows" and a hand calculation; kept as two sentences. No command or fact changed.
6. `npm run build` not run (task said no npm build). `node tools/check_mermaid.mjs` run: 776 diagrams, 0 failed.
7. Subsection openers in 09 section 2.2 and 4.1 use the original situation or a short "Picture..." sentence. Reviewer may prefer a stronger scene in 09 section 3.1 and 5.2, which are short scenes.
