# Voice rewrite, Part 7 chapters 7.13, 7.14, 7.15 (batch e)

Scope: docs/part-07-redfish-bmc/13-redfish-on-nvidia-dgx-and-hgx-bmc-gpu-baseboard-and-management.md, 14-fleet-scale-hardware-management-and-node-lifecycle-automation.md, 15-bmc-security-hardening-and-attestation.md. Uncommitted. planning/EXTERNAL_EDITS.md was not edited (per the run instruction). Files 01 to 12 in the same directory and Part 8 were not touched. Front matter, title, status row, checkpoint questions and answers, and the Sources and review notes sections were left exactly as on HEAD (checked by comparison).

## Gates

| Chapter | Words (wc) before to after | Guard (`rewrite_guard.py HEAD WORKTREE`) | Chain gate | Code-span and code-block check |
|---|---|---|---|---|
| 13 redfish on NVIDIA DGX and HGX | 6125 to 8578 (+40.0%) | 0 hard failures; new numbers 0; lost numbers 0; residue 23 to 16 (see unresolved) | 0.0 per 1000 words | all fenced blocks and Mermaid identical to HEAD; 5 "new" and 5 "lost" spans are the guard's backtick pairing artifact in Exercise 5 (the `6 x 5.5 kW = 33 kW` span itself is kept); no real span lost |
| 14 fleet-scale hardware management | 6368 to 8687 (+36.4%) | 0 hard failures; new numbers 0; lost numbers 0; residue 11 to 2 (only `Volume N` matches inside code spans) | 0.1 per 1000 words | all fenced blocks identical to HEAD; 2 "lost" spans (`bmc`, `mc`) are a pairing artifact, both `ipmitool bmc reset cold` and `ipmitool mc reset cold` are still present |
| 15 BMC security hardening and attestation | 6586 to 8484 (+28.8%) | 0 hard failures; new numbers 0; lost numbers 0; residue 16 to 9 (matches are code spans and locked headings) | 0.0 per 1000 words | all fenced blocks and Mermaid identical to HEAD; no span lost or added |

Mermaid: `node tools/check_mermaid.mjs part-07-redfish-bmc/1` ran (scoped to the Part 7 chapters 10 to 15), result "checked 7 diagrams, 0 failed". The Mermaid blocks in 13 to 15 were not edited.

`npm run build` was not run, because the run instruction said no npm build.

Honest status: each chapter keeps the status row word "untested" (13 also "not verified") and one plain sentence above its lab ("These steps were not run on a live ..." in the Exercises section of each chapter).

## What changed (all three)

- Every section keeps its heading and opens with a situation (a GPU server with a failing fan, a purchase quote, a 2 a.m. node failure, a fleet of 128 new nodes, a bricked BMC with fans at 100 percent, a security review asking for Secure Boot, an alert on a Monday morning).
- The "Prerequisites and outcomes" paragraphs (all three) were rewritten as plain paragraphs. Chapter 15 had a bullet list of "you should be able to" outcomes; it is now a paragraph. No "you should be able to" or "you will be able to" lines remain in any of the three.
- Exercises keep their counts (13: 6, 14: 6, 15: 6) and their commands and numbers. Long multi-part exercises were split into one question or instruction per sentence. Nested (a)(b) labels in 13 Exercise 6 were replaced with "In the first case / In the second case". 14 Exercise 1 and 15 Exercise 1 were split the same way.
- Interview angles keep their counts (13: 5, 14: 5, 15: 5) and their text. Each section got a short intro sentence.
- Checklists keep their counts (14 bring-up: 8 steps; 15 BMC checklist: 11 items). Each item keeps its command and value.
- First-person and lab-residue wording removed from body text: "my lab", "my mock", "my profile", "my rf_bios.py", "my own 30-day lab certificate", "I tested", "I ran", "I fixed", "I relaxed", "I learned", "I read only", "I believe", "I did not check", "I did not run", "I did not test", "I have not measured", "I have not verified", "I wrote", "I did none of steps 2 to 4", "I only retell", "which I ran", "Correction to my notes" (now "Correction to the notes"), "The user's HGX notes" (now "The NVIDIA-DevOps notes"), "volume 10 chapter 1" and "volume 10, chapter 1" (now "the NVIDIA-DevOps notes on the bare-metal and BMC lifecycle"), "volume 18" (now "the NVIDIA-DevOps security notes"), "Figure 1" (now "the diagram in section 2"), "Let us go one level deeper". Replaced with "the lab", "the practice mock", "the notes", or plain statements.
- Honest "not verified" and "untested" wording appears once per chapter in body (status row plus one lab sentence), plus the locked Sources lines.
- Exclamation marks: none added. Raw `<` or `{` outside code: none added. Semicolon chains: chain gate 0.0 or 0.1 on all three.
- No new vendor facts were added. No new numbers were added (guard: new numbers 0 on all three). A few sentences were tightened so that no hypothetical number crept in (for example "ten identical nodes", "two minutes", "1,024 GPUs", "a dozen fixes", "weeks").
- Invented attributions: none added. The only sources named in body are the ones the original named (NVIDIA-DevOps notes, BCM 11 Administrator Manual, DMTF, Redfish schema guide, DGX GB300 SuperPOD reference architecture, Supercomputers for Linux SysAdmins chapter 10 in 15, chapter references).
- Gem book title: "Supercomputers for Linux SysAdmins" is written in full (not abbreviated) in 15.
- Lab-run claims in the body now say "the lab" or "the practice mock" and do not claim live-hardware runs.

## Needs source (general explanations added, not from the original text)

These are plain-language definitions or explanations that I added. They are standard background, but none is cited in the chapter's Sources. A reviewer should check them.

13:
- BMC expanded as baseboard management controller (kept consistent with 7.7); BIOS expanded as basic input and output system; VBIOS as the GPU card firmware; VRM as voltage regulator module.
- Firmware bundle defined as a tested set of firmware versions shipped together.
- NVLink described as the high-speed GPU link and NVSwitch as the chip that connects several GPUs.
- DPU described as a network card with its own small operating system.
- DGX SuperPOD described as NVIDIA's reference design for a large cluster; OEM as original equipment manufacturer; HGX/DGX ownership framing is the original's.
- Analogy: several firmware owners each holding a key to one front door (no numbers).
- FRU, RMA (return under a return authorization), mezzanine connector, and "non-blocking mesh" meaning (every GPU pair at full speed at the same time).
- Fallback from NVLink to PCIe described as the slower standard bus.
- Heat in the copper grows with the square of the current (general electrical fact; I^2 R stays as the original wrote it).
- Power converters and "the tiny piece of silicon where computing happens" for the GPU die.
- Manifolds as pipes that spread coolant.
- UPI and Infinity Fabric described as CPU-to-CPU links; egress defined as traffic leaving the node; GPUDirect RDMA described as direct NIC access to GPU memory; "lossless" meaning no drops under load.
- Xid described as the family of error codes written by the NVIDIA driver; riser described as the card carrying a PCIe slot.
- Statement that the GPU tray has no network path of its own (inferred from the diagram in section 2, not from text).
- Statement that the GPUs never speak Redfish themselves; main BMC described as "the only door" and as a reception desk analogy.
- I2C and SMBus described as simple two-wire management buses.
- ERoT described as a root of trust that checks firmware from outside the main processor; CPLD and FPGA expanded and described as programmable logic.
- Retimer described as rebuilding a weak PCIe signal.
- 8U chassis and tray described.
- NVL72 defined as 72 GPUs in one NVLink domain (the number is from the original); N redundancy described as spare capacity so the shelf survives one dead supply.
- COMe and RJ45 described; BMC port described as out-of-band.
- Logical separation described as isolation by configuration, not separate cables.
- PDU defined as the power strip feeding the rack.
- VXLAN described as a virtual network tunnel; spine described as the core layer.
- NVSM and DCGM expanded (NVIDIA System Management, NVIDIA Data Center GPU Manager); in-band vs out-of-band defined.
- Timeline reasoning for fault investigation (which event came first).
- CDU expanded as coolant distribution unit; MQTT described as a lightweight messaging protocol; drain and power-down explained; fan curve defined; orchestration defined.
- cmsh described as BCM's command-line shell; wrapping NVSM described.
- Base Command Manager expanded as BCM (name only; the chapter's BCM facts come from the BCM manual).
- AC power cycle described as cutting and restoring mains power.
- Burn-in described; dcgmi diag, nvbandwidth and ib_write_bw each given a one-line purpose (NVIDIA GPU diagnostics, NVLink bandwidth, InfiniBand bandwidth).
- CA certificate described as a way for the BMC to prove its identity.

14:
- Node lifecycle and staging-tray analogy for Settings (no numbers).
- OnReset explained as "the next reset of the system".
- Annotation defined as extra information the BMC attaches to a resource.
- Idempotent defined as same end state after one or many runs.
- Enumeration defined as a fixed list of allowed words; registry explained as a menu analogy.
- The 400 versus 403 reading (bad request versus account not allowed).
- Naming difference: the lab uses `PowerProfile`, the notes use `OperatingPerformance` (both names are from the original text; the "same idea" claim is the explanation).
- Cautions: a forced Gen5 link that the device cannot sustain fails at boot acceptance; cores that never sleep draw more power and heat.
- Plan/apply two-stage explanation.
- Continuous network boot described as a reinstall loop with the installer rebuilding the disk each reboot (checkpoint 10 says the same in locked text).
- PXE and UefiHttp described as network boot methods over DHCP and HTTP; UEFI and Legacy described.
- D-T-B-I chain walk-in-order reasoning (a failure at an early letter hides later ones).
- DHCP reservation and HTTP boot versus TFTP described.
- Immutable baseline described as a new version gets a new name.
- Canary, gate and state-ledger/append-only described; JSON described as plain text structured data.
- CMDB expanded as configuration management database; smart hands described as on-site technician service.
- DAC cable described as direct-attach copper; a loose one can show as a degraded link.
- Gen2 x4 described as link far below rated speed.
- Day-0 described as the first day hardware is in place.
- 6.1 explanations: ACPI, C1E and C6 described as sleep states; barrier; doorbell; NUMA; pinned memory; rank; GT/s; TLP; TLP header as the fixed label; BAR; POST; IOMMU; SR-IOV.
- Scenario 1 explanations: all-reduce (every GPU shares results), throttling, AER, LnkSta, inlet temperature, healthy twin.
- Scenario 2: "1,024" heading total kept only in the heading; DGX eight-GPU fact follows from the heading; gate defined as a check a node must pass; "last line of defence".
- Scenario 3: bricked BMC definition; fans at full speed explained as the chassis playing safe; in-band definition; flash defined as the memory chip; AC drain described as cutting PDU power so standby power also goes off. The `bmc` versus `mc` alias question is left open in the text ("this chapter does not check that").
- Scenario 4: CUDA as NVIDIA's programming platform; SEL described; ECC described; DIMM described as a memory module; timeline reasoning (hardware event before crash points to cause).
- Scenario 5: Secure Boot as signature check before run; shim and bootloader defined; HTTPS boot explained as an authenticated channel; owner key enrolment explained.
- Scenario 2's "weeks" wording was removed to avoid an unsourced time claim.

15:
- VLAN, MFA, KVM, persistence, DMA and bastion defined in plain words.
- Thermal-threshold attack described as making cooling react too late (the original named the risk; the consequence wording is mine).
- Route defined as the path a packet takes; NTP described as the time protocol.
- IPMI described as an older management protocol with weak default protection.
- Secret manager described as a vault.
- Self-signed certificate analogy (an identity card printed by the device itself); CSR described as the public half of the request; refusal of a self-signed cert described as correct behaviour.
- Device Identity Certificate described as burned in at manufacturing (the notes' "immutable silicon fuses" phrase is the original's).
- Chain described as certificates each signed by the next.
- Nonce defined as a value used once; SlotId and MeasurementIndices explained as "which certificate" and "which measurements".
- Measurement register defined as a slot holding a running hash.
- Base64 described as a text encoding for binary data.
- RIM defined as the vendor's signed list of expected digests; digest defined as the hash result.
- Handshake defined as an agreed back-and-forth before data moves.
- PCR and TPM described (small security chip on the motherboard).
- Hash defined as a short fingerprint.
- SetupMode and UserMode explained as "no platform key enrolled, open to changes" and "platform key enrolled, rules enforced".
- Secure Boot databases: ResetKeys described as changing which keys are trusted (sensitive).
- Shim described as a small widely trusted bridge program; mokutil described as the tool that adds keys to the shim's trusted list.
- Confirm-after-reboot statement ("until you see that value after a reboot, the setting is only a request").
- Firmware described as running before and below the OS; BIOS-first explanation for why reinstall does not fix a bad BIOS.
- Root of trust defined as a chip whose own code is trusted by design; chain explained as each link checking the next.
- Change-managed tooling described as recorded and approved updates.
- Anti-rollback described as a hardware check that refuses older versions.
- Provenance defined.
- `sudo` described as run-one-task-with-root-powers.
- `-k` described as skipping verification; session token described as valid for whoever holds it.
- Lockout and per-purpose role explanations.
- Role mapping described (directory group to BMC role).
- ACL defined as a set of switch rules; cordon described as no new work lands on the node; volatile evidence defined as data lost on power loss.
- Forensic storage advice (store bundles where the node cannot write them) is general advice.
- Golden image defined as known-good rebuild version; SPI ROM described as the firmware flash chip; severity-1 explained as top priority.
- The "most likely answer is the boring one" in 8.2 is a reading of the notes' "nine times out of ten" statement (the number and claim are from the original).
- Checklist reason for changing default passwords before the BMC joins a shared network.

## Unresolved issues

1. Locked headings with residue, not changed (headings are locked by the run instruction):
   - 13: "### What happened on my mock" (first person in lab wording; the body under it was rewritten to "the practice mock").
   - 15: "## 7. Attestation: what it is, and what I did not do" (first person; body rewritten).
   - 13 and 15 heading residue is the only residue left outside Sources.
2. Sources and review notes sections are locked and still contain first-person and "not verified" wording (for example 13 "whether a real DGX passes my profile", 14 "I used my own lab names" and "which I did not run", 15 "which I only retell" and "my profile"). Owner decision: unlock those lines or keep them as the honest record.
3. Checkpoint questions and answers are locked. Some answers still contain claims that were not checked (for example 14 checkpoint 9's attribute names, 14 checkpoint 18's metric names and 15 checkpoint 13's key workflow). Left as on HEAD.
4. 13 is at +40.0% by wc, at the top of the 25 to 40 percent band. Trimming more would start cutting explanation that the rule wants. Left as is.
5. 15 is at +28.8%, inside the band but below the +30 aim. Adding a little more would be easy if the owner wants it.
6. 15 Layer 4: the sentence "Here is the full flow, as the lab runs it." comes right before the next paragraph and no flow block follows it in this section (the sequence diagram is in section 3). This wording is from the original; a reviewer may want to point to section 3 instead.
7. Guard "lost spans" in 13 (5) and 14 (2) are the guard's own backtick-pairing artifacts; the spans themselves are present. Confirmed by listing spans for each side.
8. Exercise 5 in 13 keeps the original wording's numbers, but the numbers are now spread over several short sentences, one or two per sentence. Commands and facts are unchanged.
9. The chain gate for 14 is 0.1 per 1000 words (target was 0.2 or lower; met).
10. The npm build was not run (run instruction). Mermaid parse check ran on Part 7 chapters 10 to 15 only (7 diagrams, 0 failed).
