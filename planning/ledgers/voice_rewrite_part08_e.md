# Voice rewrite ledger: Part 8, chapters 8.13 to 8.16 (run e)

Scope: `docs/part-08-bcm/13-day-2-operations-updates-scaling-hardware-replacement-disaster-recover.md`, `14-air-gapped-installation-and-upgrades.md`, `15-bcm-in-an-ai-factory-dgx-superpod-integration.md`, `16-mission-control-dgx-cloud-and-autonomous-recovery-concepts.md`. Front matter, headings (text and order), tables, Mermaid, code blocks, the checkpoint questions (20 each) and Sources and review notes are unchanged from HEAD. The checkpoint and Sources tail was spliced byte-for-byte from HEAD. `EXTERNAL_EDITS.md` was not edited (per instruction).

## Words (wc, whole file)

| File | Before | After | Growth |
|---|---|---|---|
| 8.13 | 6410 | 8956 | +39.7 percent |
| 8.14 | 6166 | 8070 | +30.9 percent |
| 8.15 | 6223 | 8702 | +39.8 percent |
| 8.16 | 9357 | 12060 | +28.9 percent |

## Gates (run after the last edit)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all four.
  - 8.13: new numbers 0, lost numbers 0. One new span (`cmsh`-style command names in prose, plus `pdsh`, `pexec`, `gdb`, `prejob`, `rsync`, `.ko`, `all_reduce_perf`, `ok`) is a typed or on-screen name; the exact span check shows no lost spans.
  - 8.14: new numbers 0, lost numbers 0. New span `docker ps` (typed command).
  - 8.15: new numbers 0, lost numbers 0. Guard reports lost 3 and new 1 (`/16` in the walkthrough). This is the guard's pairing artifact; the exact check below shows no lost spans. `/16` is the original `bmcnet` prefix, now in a restored span.
  - 8.16: new numbers 0, lost numbers 0. New span `openssl verify` (typed command). Guard "lost" entries are pairing artifacts; the exact check shows none lost.
- Exact span check (set and count, fenced blocks removed, `git show HEAD:<file>` against worktree): lost `{}` on all four. Two spans were lost in the first pass of 8.15 and 8.16 and were restored before the final run.
- `python3 tools/restore/chain_gate.py <file>`: 8.13 0.3, 8.14 0.4, 8.15 0.3, 8.16 0.7. All are at or under the 1.5 limit. 8.16 is above the 0.2 target because of the locked Sources and checkpoint text.
- `node tools/check_mermaid.mjs`: "checked 776 diagrams, 0 failed".
- `npm run build`: not run (the lead said no npm build).
- Fenced code blocks, Mermaid blocks and all table rows: identical to HEAD (checked line by line).
- Headings: identical text and order to HEAD.

## Honest status

- Each chapter keeps the status row (locked table, "cluster commands **untested** on live BCM" or the SuperPOD variant).
- One plain sentence above the exercises or lab in each chapter: "These steps were not run on a live cluster, so treat them as practice." (8.13, 8.14, 8.15). In 8.16 the section 5 intro says the cluster commands were not run on a live cluster. Remaining "not run" hits are inside code blocks, which are unchanged.

## Residue and voice fixes

- Outcomes lists ("you should be able to", "you will be able to", "By the end of the chapter") in all four rewritten as plain paragraphs. Headings kept.
- First-person residue removed from body text: "I read their headings" and "I did not read every procedure" (8.16 section 4 intro, now a scope sentence); "I did not cover InfiniBand setup" (8.15 section 2); "my own products" and "my own derivation" (8.15); "our BCM manual corpus" (8.16 section 2.1); "the manual says" phrasing kept only where the original cited the manual.
- "Table 7 in Section 7" (8.13 section 10.2) became "the table in section 7 of this chapter".
- Bold: at most one bold per section in prose. Table cells keep their original bold.
- Semicolon chains: only in code and locked text. Prose has none over three clauses.
- Section openers: every body section now opens with a situation (a 3 a.m. change, a day before a cut-off, a training job that slows, an on-call engineer). Openers that are scenarios written for teaching are invented, not reported incidents.
- Exercises: same counts (8.13: 6, 8.14: 6, 8.15: 6, 8.16: 6). Multi-part asks split into one question per sentence. Commands, versions and numbers unchanged. Where a sentence held more than two numbers (8.15 exercise 3), it was split so each sentence has at most two.
- Interview angles: same five bullets per chapter (bold question text replaced with quoted questions). Explanations added around the answers.
- Removed an unsupported claim in 8.16 section 4 that a failed Topograph query "fails quietly". Replaced with a plain statement that Topograph has nothing to authenticate with.
- Removed unsupported claims added during the pass: that a network rule "cannot be changed later" (8.15 section 3.1), and that built-in MySQL system schemas are excluded "because the server rebuilds them" (8.16 section 2.3).

## Headings kept on purpose (unresolved, owner to decide)

- 8.13 "## 7. Disaster recovery: an outline (my assembly)" and "## 10. Change runbooks (my assembly)": first-person label kept because the rulebook keeps headings unchanged. Suggest renaming to "(assembled for this handbook)" in a later pass.
- 8.15 "## 6. How I would use this in practice": same reason. Suggest "## 6. Using this in practice".

## Needs source (general explanations added; no new vendor facts)

These are general definitions and reasoning around the manual's facts. Check them against a reference before publication.

8.13:
- RPM and DEB as the package formats of Red Hat-style and Debian-style systems; what a GPG signature does; what a tar file is; what a `gdb` trace is; what a repository metadata index is; what a chroot is; what autofs is; what fencing and quorum mean; what a burn-in is.
- Btrfs subvolume and snapshot as a concept; what a MAC address is for PXE recognition; what genders groups are; what pdsh does (parallel SSH); what a rotating backup set means in practice.
- Descriptions of Keycloak (login service) and Harbor (container image store) in the bundle list.
- Reasons added: why a power surge matters when many nodes start at once; why `close` and `drain` differ; why a dead passive head should not run tools.

8.14:
- NGC as NVIDIA's catalogue; SAN and CA as terms; TLS as the encryption layer; NTP as the time protocol; Skopeo as a copy tool; Helm 3 versus 4 behaviour expectation; CRD; data diode and DMZ; provenance; supply-chain framing.
- initrd, loop mount and bind mount descriptions; DOCA OFED as the driver stack; GPUDirect RDMA and GDS descriptions; all_reduce_perf as a benchmark; `kubelet` and systemd roles; static pod; uncordon; Slurm accounting as the job record.
- Reasons added: why the packages must be present before the image build; why the registry name must match what nodes use; why the wizard refuses to run on a passive head.

8.15:
- Thermal design power; Uptime Tier 3 as a concept (concurrent maintainability); liquid cooling efficiency as a general claim; NVLink as NVIDIA's GPU link; power shelf as a conversion unit; BMC and BlueField and DPU descriptions; BGP, eBGP and single-mode fibre; MQTT; Redfish as a standard web interface; ZTP; UFM and NetQ as fabric tools; Magnum IO; PDU, UPS, STS definitions; N+1 meaning; derating, power factor, line-to-neutral; CFM; ASHRAE as the publisher of data center air standards; MERV; ISO 14644-1 as a cleanliness standard; rear door heat exchangers and in-row coolers as device types.
- VLAN and VXLAN; spine; RoCE and RDMA; parallel filesystem; checkpoint and heartbeat; rail-aligned; IMEX as a concept; direct-to-chip cooling; bond; BMS; /16 as address space size.
- Reasons added: why networks are separated; why rounding up matters for SUs; why stranded power matters; why the out-of-band network is kept apart; why a reference needs checking.

8.16:
- Operational technology; NFS tier; nonuser profile meaning; X509 tokens as permissions; CMDaemon as the management daemon; EOL; DCGM as GPU monitoring; NCCL and collectives; sharded checkpoint; Dynamic Resource Allocation as a Kubernetes mechanism; MetalLB as an address-handing component; OIDC and the API server; Kourier as the Run:ai ingress component; IAM and EC2 descriptions; BMS; VXLAN spine.
- Reasons added: why a profile edit can stop recovery silently; why the failover check must be per service; why checkpoint interval is a cost decision; why topology data matters for collective traffic; why multiplexers protect the wizard; why a prerequisite check beats a late abort.

## Unresolved

- Heading residue: "(my assembly)" in 8.13 (two headings) and "How I would use this in practice" in 8.15. Kept because headings are locked by the rulebook (see above).
- 8.14 section 5 says "the documented order ... has 13 steps" and lists nine numbered items. This is from the original text and was kept as is. Needs a check against the lab `STEPS` list.
- 8.15 and 8.16 are vendor-heavy. Every product claim in them is original. Only general explanations were added (see Needs source).
- 8.16 chain gate 0.7 is from the locked Sources and checkpoint text. Body prose has no semicolon chains.
- Some original statements from the manuals are kept with their attribution (for example "the manual says"). They are not re-verified.
- Words: all four are within +25 to +40 percent (8.14 +30.9, 8.16 +28.9, 8.13 +39.7, 8.15 +39.8).
