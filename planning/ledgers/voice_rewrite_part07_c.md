# Voice rewrite, Part 7 chapters 7.7, 7.8, 7.9 (batch c)

Scope: docs/part-07-redfish-bmc/07-systems-chassis-and-managers-the-core-resource-model.md, 08-power-thermal-sensors-and-environment.md, 09-storage-network-adapters-and-pcie-devices.md. Uncommitted. planning/EXTERNAL_EDITS.md was not edited (per the run instruction). Files 01 to 06 and 10 to 12 in the same directory were modified by another session and were not touched.

No mid-run disk changes were seen on 07, 08 or 09. The on-disk state matched HEAD before the rewrite.

## Gates

| Chapter | Words (wc) before to after | Guard (`rewrite_guard.py HEAD WORKTREE`) | Chain gate | Code-span set check |
|---|---|---|---|---|
| 07 systems, chassis, managers | 6005 to 7884 (+31.3%) | 0 hard failures; guard count 5789 to 7668; new numbers 0; lost numbers 0; residue 3 to 0; guard reports "lost 1" (pairing artifact) | 0.0 per 1000 words | no lost spans (Counter difference empty) |
| 08 power, thermal, sensors | 6161 to 7859 (+27.5%) | 0 hard failures; guard count 5932 to 7630; new numbers 1 (`8.4`, a section cross-reference, not a fact); lost numbers 0; residue 5 to 0 | 0.0 per 1000 words | no lost spans |
| 09 storage, network, PCIe | 6609 to 8697 (+31.6%) | 0 hard failures; guard count 6275 to 8363; new numbers 0; lost numbers 0; residue 0 to 0; guard reports "lost 4" (pairing artifact) | 0.0 per 1000 words | no lost spans |

Checkpoint count: 20 in each chapter, same `<details><summary>` form. Code blocks, Mermaid blocks, front matter, headings, data tables (lookup tables and the top status table) and the Sources and review notes section were left as they were on HEAD.

Not run, per the run instruction: `node tools/check_mermaid.mjs` and `npm run build` (the instruction said no npm build or full Mermaid). Mermaid blocks were not edited, so they are unchanged from HEAD.

## What changed (all three)
- Each section keeps its heading and opens with a situation (a GPU running hot during a training job, a fan that stops, a PCIe link that trains down quietly, a drive that is about to fail).
- The "Prerequisites and outcomes" bullets (07, 08, 09) were rewritten as a plain paragraph. No "you should be able to" lines remain. 08 keeps the `Status`, `Health` and thresholds split in that paragraph because the original listed it there.
- Interview angles and exercises keep their counts and commands. Exercises were split into one question per sentence. 07 keeps 6 exercises, 08 keeps 6, 09 keeps 6. 09 Interview angles keep 4 and 07 keeps 4. 08 keeps 5, as the original did.
- The "Lab" paragraphs in each chapter now include a plain sentence saying the steps were not run on a live BMC (07 link-check paragraph, 08 lab paragraph in section 5, 09 "The lab" section).
- First-person residue removed from reader text: "I ran it", "my mock", "my lab", "I fixed", "I could not check", "I could not confirm", "I carry that scenario", "the schema version I read", "I did not use those three", "I set", "I removed", "my reader", "I give them as the notes state them", "the user's notes" (rewritten as "the NVIDIA-DevOps notes", which the original Sources section already names), "I have not checked". Replaced with plain teacher voice or "the practice mock" and "not checked here". The 09 body had one "I" ("the size I expect"), changed to "you expect".
- Lines like "Drafted" status and the status row keep the word "untested" once (the status row), as the gate requires.
- Exclamation marks: none added. Raw `<` or `{` in prose: none added. Semicolon chains: chain gate 0.0 on all three.
- Invented attributions: none added. Body still names only the sources the original named (DMTF, the Redfish schema guide, BCM 11 manual, NVIDIA-DevOps notes). No "the book says", no "Volume N" in body.
- Exercise and lab commands are unchanged. Numbers in exercises and lab outputs are unchanged.

## Needs source (general explanations added, not from the original text)

These are plain-language definitions or explanations I added. They are standard background, but they are not cited in the chapter's Sources. A reviewer should check them.

07:
- BMC expanded as baseboard management controller.
- UUID described as following RFC 4122 (the original named RFC 4122; the "standard format for unique identifiers" wording is mine).
- Replaceable and HotPluggable meanings (swap by a technician; swap with power on).
- Chassis nesting explained with a shipping-carton analogy (no numbers).
- Redundant managers explained as pairs that take over for each other.
- `ipmitool` described as the older command-line tool for the same job.
- Slurm drain explained as "finish current work, accept no new jobs".
- Two-way street analogy for links (no numbers).

08:
- ETag and `If-Match` explained as a version tag that stops a stale edit.
- Prometheus described as a time-series database.
- DwellTime and hysteresis explained (hysteresis as the fall-back gap before an alarm clears).
- ASHRAE described as the body that publishes data center air temperature ranges.
- TIM expanded as thermal interface material.
- Straggler defined as the one node that finishes late and holds back the job.
- CDU and loop explanations (facility loop, rack loop) are general.
- The Prometheus alert-rule suggestion (watch `redfish_sensor_ok` for `0`, filter absent sensors) is my own practical advice, not from a source.
- `ReportSequence` gap explained as a sign that a report was lost.
- MetricReport gathering "on the BMC's own schedule" and the telemetry path explanation are general.
- Fan-failure walkthrough (remaining fan speeds up, nearby sensors warm slowly) is a general explanation. Not measured in the labs.
- Power-supply redundancy walkthrough (survivor runs hotter and closer to its limit) is general.
- Dashboard summary vs `DataSourceUri` argument is an analogy.

09:
- SR-IOV expanded as single-root I/O virtualization and described.
- GT/s defined as giga-transfers per second.
- Lane defined as one pair of wires per direction.
- Retimer defined as a chip that rebuilds a weak signal.
- Differential pair defined as the two-wire signal path for one lane.
- DAC, PAM4, FEC, auto-negotiation, TX and RX polarity, SerDes lanes described in plain words.
- SXM described as a socket form factor on the baseboard.
- RoCEv2 and GPUDirect RDMA described briefly. HBM described as stacked memory next to the GPU die.
- GDS (GPUDirect Storage) and P2PDMA described briefly.
- The `D` state (uninterruptible sleep) described as waiting on hardware that stopped answering.
- Spare blocks, P/E endurance and SMART described.
- DHCP and PXE described as address and boot services.
- Diskless node described.
- ECC expanded as error-correcting code. OEM described as vendor extensions outside the standard.
- CXL (Compute Express Link) and JBOF described.
- Collective step described: every GPU waits for the slowest in each exchange.
- Fault-injection test described as "break it on purpose and check the tool notices".
- Day-0 and Day-2 described as the arrival moment and everything after production.
- Delta of counters described.
- "Gate" described as a point the node cannot pass until it checks.

## Unresolved issues

1. 09, Exercise 1 says to confirm that `12` / `15` checks pass, while the lab output block shows `15 passed, 0 failed`. This was in the original text. Numbers are locked, so the text was kept as written. The owner should decide which count is correct.
2. 09, section 6.5 table keeps the original `\|` escapes inside code spans. They are unchanged from HEAD. The MDX build was not run, so rendering was not checked.
3. 08 body still has one additional honest sentence ("The exact method has not been checked here.", and "That name could not be confirmed here."). Both are claim-boundary sentences in the original's spirit. Remove them if the owner wants only one honest status line per chapter.
4. Bold use: a few sections still have more than one bold label (for example 08 section 8.1 and 09 section 6.4 list items). Left as in the original, because bold labels are in the original lists and the rule says at most one bold idea per section.
5. Checkpoint questions and answers are unchanged from HEAD. Some answers may still contain claims that were not re-checked in this run (for example 08 checkpoint 11 on `LineInputStatus` values, and 09 checkpoint 18 on NCCL jobs). These were not in scope to change.
6. The 07 Sources note "Run here: `rf_model.py` (8 services)" and similar lines are locked by the rules and are left as they were.
